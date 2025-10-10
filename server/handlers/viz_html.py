"""
viz_html.py

HTML renderer for visualization mockups.

Converts VisualizationTools output into a single-page HTML dashboard using
Tailwind CSS (CDN) and Chart.js (CDN). Designed for quick, high-quality
mockups that are easy to open and share.

Tools exposed via create_viz_html_handlers:
- viz_render_html_mockup: Return HTML content as a string
- viz_export_html_mockup: Write HTML to disk and return the file path
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = None

from .visualization_tools import VisualizationTools


def _format_number(val: Any, fmt: Optional[str]) -> str:
    try:
        if val is None:
            return ""
        # Basic heuristics for currency/percent
        if isinstance(fmt, str):
            fl = fmt.lower()
            if any(sym in fl for sym in ["$", "Ôé¼", "┬ú"]) or "currency" in fl:
                try:
                    return f"{float(val):,.0f}"
                except Exception:
                    return str(val)
            if "%" in fl or "percent" in fl:
                try:
                    return f"{float(val):.2%}"
                except Exception:
                    return str(val)
        # Default: thousand separators, no decimals for large values
        if isinstance(val, (int, float)):
            if abs(val) >= 1000:
                return f"{val:,.0f}"
            return f"{val}"
        return str(val)
    except Exception:
        return str(val)


def _safe_id(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", title).strip("-")
    return s or "chart"


def _chart_js_block(canvas_id: str, chart: Dict[str, Any]) -> str:
    ctype = chart.get("chart_type") or chart.get("type") or "bar"
    data = chart.get("data") or []
    spec = chart.get("spec") or {}
    x = spec.get("x_field") or "x"
    y = spec.get("y_field") or "y"
    labels = [str(row.get(x, "")) for row in data]
    values = [row.get(y, 0) for row in data]
    cfg = {
        "type": "bar" if ctype == "bar" else ("line" if ctype in ["line", "area"] else "bar"),
        "data": {
            "labels": labels,
            "datasets": [{
                "label": chart.get("title", "Series"),
                "data": values,
                "borderColor": "#60A5FA",
                "backgroundColor": "rgba(96,165,250,0.3)",
                "tension": 0.3 if ctype in ["line", "area"] else 0,
                "fill": True if ctype == "area" else False
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {"legend": {"display": False}},
            "scales": {
                "y": {"ticks": {"color": "#CBD5E1"}},
                "x": {"ticks": {"color": "#CBD5E1"}}
            }
        }
    }
    return f"""
    <div class=\"h-60\">
      <canvas id=\"{canvas_id}\"></canvas>
    </div>
    <script>
      (function() {{
        const ctx = document.getElementById('{canvas_id}').getContext('2d');
        const cfg = {json.dumps(cfg)};
        new Chart(ctx, cfg);
      }})();
    </script>
    """


def _kpi_card_block(item: Dict[str, Any]) -> str:
    label = item.get("label") or item.get("measure") or "KPI"
    value = _format_number(item.get("value"), item.get("format"))
    return f"""
    <div class=\"rounded-xl bg-slate-800/70 border border-slate-700 p-4 shadow-sm\">
      <div class=\"text-slate-300 text-sm\">{label}</div>
      <div class=\"text-2xl font-semibold text-slate-50\">{value}</div>
    </div>
    """


def _financial_table_block(title: str, rows: List[Dict[str, Any]]) -> str:
    head = f"<div class=\"text-slate-200 font-semibold mb-2\">{title}</div>" if title else ""
    lines = []
    for r in rows[:20]:  # keep single-page
        li = r.get("line_item") or r.get("label") or ""
        val = _format_number(r.get("value"), r.get("format"))
        lines.append(f"<div class=\"flex justify-between py-1\"><span class=\"text-slate-300\">{li}</span><span class=\"text-slate-100\">{val}</span></div>")
    return f"""
    <div class=\"rounded-xl bg-slate-800/70 border border-slate-700 p-4 shadow-sm\">
      {head}
      <div class=\"divide-y divide-slate-700\">
        {''.join(lines)}
      </div>
    </div>
    """


def _table_block(title: str, rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    if not columns and rows:
        columns = list(rows[0].keys())[:6]
    head = f"<div class=\"text-slate-200 font-semibold mb-2\">{title}</div>" if title else ""
    thead = ''.join([f"<th class=\"px-2 py-1 text-left text-slate-300\">{c}</th>" for c in (columns or [])])
    body_rows = []
    for r in rows[:12]:
        tds = []
        for c in (columns or []):
            v = r.get(c)
            tds.append(f"<td class=\"px-2 py-1 text-slate-200\">{v}</td>")
        body_rows.append(f"<tr class=\"border-t border-slate-700\">{''.join(tds)}</tr>")
    return f"""
    <div class=\"rounded-xl bg-slate-800/70 border border-slate-700 p-4 shadow-sm\">
      {head}
      <div class=\"overflow-hidden\">
        <table class=\"w-full text-sm\">
          <thead><tr>{thead}</tr></thead>
          <tbody>{''.join(body_rows)}</tbody>
        </table>
      </div>
    </div>
    """


def _vega_spec(chart: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    chart_type = (chart.get('chart_type') or chart.get('type') or '').lower()
    if chart_type not in {'bar', 'line', 'area'}:
        return None
    data = chart.get('data') or []
    if not data:
        return None
    spec_hint = chart.get('spec') or {}
    x_field = spec_hint.get('x_field')
    y_field = spec_hint.get('y_field') or 'Value'
    if not x_field and data:
        x_field = next(iter(data[0].keys()), None)
    if not y_field and data:
        keys = list(data[0].keys())
        if len(keys) > 1:
            y_field = keys[1]
    encoding_x = {
        'field': x_field or 'Category',
        'type': 'temporal' if spec_hint.get('time_grain') or chart_type in {'line', 'area'} else 'ordinal'
    }
    encoding_y = {
        'field': y_field or 'Value',
        'type': 'quantitative'
    }
    if chart_type == 'bar':
        encoding_x['sort'] = '-y'
    mark = 'line' if chart_type == 'line' else ('area' if chart_type == 'area' else 'bar')
    spec = {
        '$schema': 'https://vega.github.io/schema/vega-lite/v5.json',
        'title': chart.get('title'),
        'data': {'values': data},
        'mark': {'type': mark, 'tooltip': True},
        'encoding': {
            'x': encoding_x,
            'y': encoding_y,
            'tooltip': [
                {'field': encoding_x['field']},
                {'field': encoding_y['field']}
            ]
        },
        'autosize': {'type': 'fit', 'contains': 'padding'},
        'width': 'container',
        'height': 280 if mark == 'line' else 240,
        'usermeta': {
            'source': 'MCP-PowerBi-Finvision',
            'chart_type': chart_type,
            'dimension_field': encoding_x['field'],
            'measure_field': encoding_y['field']
        }
    }
    return spec


def _vega_block(element_id: str, chart: Dict[str, Any], specs_out: List[Dict[str, Any]]) -> str:
    spec = _vega_spec(chart)
    if not spec:
        return f"<pre class=\"text-xs text-slate-300 bg-slate-900 p-3 rounded\">{json.dumps(chart, indent=2)}</pre>"
    specs_out.append({'title': chart.get('title'), 'spec': spec})
    return f"""
    <div class=\"h-64\" id=\"{element_id}\"></div>
    <script type=\"text/javascript\">
      vegaEmbed("#{element_id}", {json.dumps(spec)}, {{actions: false, renderer: "canvas"}}).catch(err => {{
        const el = document.getElementById("{element_id}");
        if (el) {{
          el.innerText = err;
        }}
      }});
    </script>
    """


def _render_sections(page_blueprint: Dict[str, Any], charts: List[Dict[str, Any]], library: str = 'chartjs', vega_specs: Optional[List[Dict[str, Any]]] = None) -> str:
    # Map chart titles to chart payloads for simple lookup
    by_title = {c.get('title'): c for c in charts}
    sections_html: List[str] = []
    for section in page_blueprint.get('sections', []):
        slot = section.get('slot', 'mid')
        titles = section.get('charts', [])
        # Layout: top => 3 cols, mid => 2 cols, bottom => 2 cols
        grid = 'grid-cols-3' if slot == 'top' else ('grid-cols-2' if slot in ('mid', 'bottom') else 'grid-cols-2')
        inner: List[str] = []
        for t in titles:
            chart = by_title.get(t)
            if not chart:
                continue
            ctype = chart.get('chart_type') or chart.get('type')
            if ctype == 'kpi_grid':
                cards = []
                for item in (chart.get('data') or [])[:6]:
                    cards.append(_kpi_card_block(item))
                inner.append(f"<div class=\"grid grid-cols-1 md:grid-cols-3 gap-3\">{''.join(cards)}</div>")
            elif ctype in ('kpi_card',):
                item = (chart.get('data') or [{}])[0]
                inner.append(_kpi_card_block(item))
            elif ctype in ('bar', 'line', 'area'):
                canvas_id = _safe_id(t) + "-canvas"
                if library == 'vega-lite' and vega_specs is not None:
                    inner.append(_vega_block(canvas_id, chart, vega_specs))
                else:
                    inner.append(_chart_js_block(canvas_id, chart))
            elif ctype in ('financial_table',):
                inner.append(_financial_table_block(chart.get('title', ''), chart.get('data') or []))
            elif ctype in ('table',):
                inner.append(_table_block(chart.get('title', ''), chart.get('data') or [], chart.get('spec', {}).get('columns')))
            else:
                # Fallback simple card with JSON
                inner.append(f"<pre class=\"text-xs text-slate-300 bg-slate-900 p-3 rounded\">{json.dumps(chart, indent=2)}</pre>")
        sections_html.append(f"<section class=\"grid {grid} gap-4\">{''.join(inner)}</section>")
    return ''.join(sections_html)


def _wrap_html(page_title: str, body: str, theme: str = 'dark', library: str = 'chartjs') -> str:
    dark_class = 'class="dark"' if theme == 'dark' else ''
    if library == 'vega-lite':
        library_scripts = (
            '<script src="https://cdn.jsdelivr.net/npm/vega@5"></script>'
            '<script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>'
            '<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>'
        )
    else:
        library_scripts = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
    return f"""
<!DOCTYPE html>
<html lang="en" {dark_class}>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{page_title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    {library_scripts}
    <style>
      html, body {{ height: 100%; }}
      body {{ margin: 0; }}
    </style>
  </head>
  <body class="bg-slate-900 text-slate-100 min-h-screen">
    <div class="max-w-[1400px] mx-auto p-6">
      <header class="mb-4">
        <h1 class="text-2xl font-semibold">{page_title}</h1>
      </header>
      <main class="grid gap-6">
        {body}
      </main>
    </div>
  </body>
</html>
"""


def render_dashboard_html(
    prepared: Dict[str, Any],
    page_title: Optional[str] = None,
    theme: str = 'dark',
    library: str = 'chartjs'
) -> Tuple[str, Dict[str, Any]]:
    charts = prepared.get('chart_recommendations', []) or []
    blueprint = prepared.get('page_blueprint') or {}
    title = page_title or prepared.get('request_type', 'Dashboard').replace('_', ' ').title()
    extras: Dict[str, Any] = {}
    vega_specs: Optional[List[Dict[str, Any]]] = [] if library == 'vega-lite' else None
    sections = _render_sections(blueprint, charts, library, vega_specs)
    if vega_specs is not None:
        extras['vega_specs'] = vega_specs
    html = _wrap_html(title, sections, theme, library)
    return html, extras


def create_viz_html_handlers(connection_state, config):
    viz_tools = VisualizationTools(connection_state, config)

    def _ensure_connected() -> Optional[Dict[str, Any]]:
        try:
            if connection_state and connection_state.is_connected():
                return None
        except Exception:
            pass
        return {
            'success': False,
            'error': 'Not connected to a Power BI Desktop model',
            'error_type': 'not_connected'
        }

    def viz_render_html_mockup(arguments: Dict[str, Any]) -> Dict[str, Any]:
        issue = _ensure_connected()
        if issue:
            return issue
        req_type = arguments.get('request_type', 'financial')
        opts = {
            'tables': arguments.get('tables'),
            'measures': arguments.get('measures'),
            'max_rows': int(arguments.get('max_rows', 100)),
            'sample_rows': int(arguments.get('sample_rows', 20))
        }
        prepared = viz_tools.prepare_dashboard_data(req_type, **opts)
        if not prepared.get('success'):
            return prepared
        library = str(arguments.get('library', 'chartjs') or 'chartjs').strip().lower()
        if library in {'chartly', 'chart.js'}:
            library = 'chartjs'
        if library in {'vega', 'vega-lite', 'vega_lite'}:
            library = 'vega-lite'
        html, extras = render_dashboard_html(prepared, arguments.get('page_title'), arguments.get('theme', 'dark'), library)
        response = {
            'success': True,
            'html': html,
            'layout': prepared.get('page_blueprint'),
            'guidance': prepared.get('guidance'),
            'library': library
        }
        response.update(extras)
        return response

    def viz_export_html_mockup(arguments: Dict[str, Any]) -> Dict[str, Any]:
        res = viz_render_html_mockup(arguments)
        if not res.get('success'):
            return res
        title = arguments.get('page_title') or 'Dashboard'
        safe = _safe_id(title)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_dir = arguments.get('output_dir') or os.path.join(os.path.dirname(__file__), '..', '..', 'exports', 'mockups')
        base_path = Path(base_dir).resolve()
        try:
            base_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        file_path = base_path / f"{ts}_{safe}.html"
        file_path.write_text(res.get('html') or '', encoding='utf-8')
        result = {
            'success': True,
            'output_file': str(file_path),
            'layout': res.get('layout'),
            'guidance': res.get('guidance'),
            'library': res.get('library')
        }
        specs = res.get('vega_specs') or []
        export_specs = arguments.get('export_specs_json')
        if res.get('library') == 'vega-lite' and (export_specs is True or export_specs is None):
            specs_path = file_path.with_suffix('.specs.json')
            try:
                specs_path.write_text(json.dumps(specs, indent=2), encoding='utf-8')
                result['specs_file'] = str(specs_path)
                if specs:
                    result['vega_specs'] = specs
            except Exception:
                result.setdefault('notes', []).append('Unable to write specs JSON file')
        elif export_specs:
            result.setdefault('notes', []).append('Specs JSON requested but only available with library=vega-lite')
        if specs:
            result.setdefault('vega_specs', specs)
        return result

    return {
        'viz_render_html_mockup': viz_render_html_mockup,
        'viz_export_html_mockup': viz_export_html_mockup,
    }
