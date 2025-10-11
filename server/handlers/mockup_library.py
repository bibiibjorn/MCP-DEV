"""
Mockup library handlers

Tools:
- mockup_list_components: surface component metadata
- mockup_generate_html: compose HTML using base template and component snippets
- mockup_analyze_screenshots: process screenshots in assets/screenshots/incoming
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from validation.screenshot_analyzer import analyze_screenshot

BASE_TEMPLATE_PATH = Path("templates/base/dashboard_base.html")
BASE_STYLESHEET_PATH = Path("templates/base/dashboard_base.css")
DEFAULT_LOG_PATH = Path("docs/screenshot_analysis_log.md")
SCREENSHOT_INCOMING = Path("assets/screenshots/incoming")
SCREENSHOT_PROCESSED = Path("assets/screenshots/processed")


def _load_metadata(base_dir: Path) -> Dict[str, Any]:
    metadata_path = base_dir / "docs" / "component_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"component_metadata.json not found at {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _resolve_path(base_dir: Path, relative: Path) -> Path:
    candidate = (base_dir / relative).resolve()
    base_dir_resolved = base_dir.resolve()
    if not str(candidate).startswith(str(base_dir_resolved)):
        raise ValueError(f"Attempt to access path outside project root: {candidate}")
    return candidate


def _extract_component_snippet(path: Path, anchor: Optional[str]) -> str:
    content = path.read_text(encoding="utf-8")
    if not anchor:
        return content

    pattern = re.compile(r"<!--\s*component:\s*([a-z0-9_\-]+)\s*-->", re.IGNORECASE)
    matches = list(pattern.finditer(content))
    for index, match in enumerate(matches):
        name = match.group(1)
        if name.lower() == anchor.lower():
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            return content[start:end].strip()
    raise ValueError(f"Component anchor '{anchor}' not found in {path}")


def _component_markup(base_dir: Path, component_ref: str) -> str:
    path_str, _, anchor = component_ref.partition("#")
    resolved = _resolve_path(base_dir, Path(path_str))
    return _extract_component_snippet(resolved, anchor or None)


def _render_base_template(base_dir: Path, title: str, heading: str, subtitle: str,
                          navigation_html: str, controls_html: str, content_html: str) -> str:
    template_path = _resolve_path(base_dir, BASE_TEMPLATE_PATH)
    html = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{ title }}": title,
        "{{ heading }}": heading,
        "{{ subtitle }}": subtitle,
        "{{ navigation }}": navigation_html or "<!-- navigation -->",
        "{{ controls }}": controls_html or "<!-- controls -->",
        "{{ content }}": content_html or "<!-- content -->",
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    return html


def _build_component_markup(base_dir: Path, metadata: Dict[str, Any], component_ids: List[str]) -> str:
    fragments: List[str] = []
    for comp_id in component_ids:
        meta = next((c for c in metadata.get("components", []) if c["id"] == comp_id), None)
        if not meta:
            continue
        fragments.append(_component_markup(base_dir, meta["template"]))
    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip())


def _append_log(log_path: Path, entries: List[Dict[str, Any]]) -> None:
    log_exists = log_path.exists()
    with log_path.open("a", encoding="utf-8") as handle:
        if not log_exists:
            handle.write("# Screenshot Analysis Log\n\n")
        for entry in entries:
            handle.write(f"## {entry['timestamp']} - {entry['filename']}\n")
            handle.write(f"- Theme: {entry['analysis']['theme']}\n")
            dims = entry["analysis"]["dimensions"]
            handle.write(f"- Dimensions: {dims['width']}x{dims['height']}\n")
            palette_preview = ", ".join(entry["analysis"]["color_palette"][:5])
            handle.write(f"- Dominant palette: {palette_preview}\n")
            detected = entry["analysis"]["detected_components"]
            detected_text = ", ".join(f"{k}:{v}" for k, v in detected.items())
            handle.write(f"- Detected components: {detected_text or 'none'}\n")
            suggestions = entry["analysis"].get("suggested_components") or []
            handle.write(f"- Suggested additions: {', '.join(suggestions) or 'none'}\n")
            handle.write("\n")


def _slugify(text: str) -> str:
    safe = re.sub(r"[^a-z0-9_-]+", "-", text.lower())
    safe = re.sub(r"-+", "-", safe).strip("-")
    return safe or "item"


def _ensure_dir(path: Path) -> None:
    os.makedirs(path, exist_ok=True)


def _generate_component_html(component_id: str, component_type: str, analysis: Dict[str, Any]) -> str:
    timestamp_slug = component_id.replace("_", "-")
    palette = analysis.get("color_palette") or []
    primary = palette[0] if palette else "#3b82f6"
    secondary = palette[1] if len(palette) > 1 else "#22d3ee"
    background = palette[2] if len(palette) > 2 else "rgba(15,23,42,0.92)"
    theme = analysis.get("theme") or "mixed"
    detected = analysis.get("detected_components") or {}
    filename = f"{component_id}.html"
    anchor = f"auto-{component_type.replace('_', '-')}-{timestamp_slug}"

    if component_type == "kpi_cards":
        html = f"""<!-- component: {anchor} -->
<div class="card span-3" data-component="{component_id}" style="background:{background};border-color:{secondary}33;">
    <div class="meta-label">Auto KPI</div>
    <div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:16px;">
        <div>
            <div style="font-size:34px;color:#f8fafc;font-weight:600;">{detected.get('kpi_cards', 1) * 12:,}</div>
            <div class="muted" style="margin-top:6px;">Generated {theme.title()} theme</div>
        </div>
        <span class="chip" style="color:{primary};border-color:{primary}44;background:{primary}14;">
            <i data-lucide="sparkles" aria-hidden="true"></i>
            Auto
        </span>
    </div>
    <footer class="muted" style="margin-top:18px;font-size:12px;">Palette hint: {', '.join(palette[:3])}</footer>
</div>
"""
    elif component_type == "tables":
        html = f"""<!-- component: {anchor} -->
<div class="card span-6" data-component="{component_id}" style="background:{background};border-color:{primary}33;">
    <header style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <div>
            <div class="meta-label">Auto Table</div>
            <h2 style="margin:6px 0 0;color:#f8fafc;font-size:18px;font-weight:600;">Generated Insights</h2>
        </div>
        <span class="chip" style="color:{primary};border-color:{primary}55;background:{primary}18;">Theme: {theme}</span>
    </header>
    <table class="table" role="table" aria-label="Auto generated table">
        <thead>
            <tr>
                <th scope="col">Segment</th>
                <th scope="col" style="text-align:right;">Value</th>
                <th scope="col" style="text-align:right;">Share</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Highlight</td>
                <td style="text-align:right;color:#f8fafc;font-weight:600;">{detected.get('charts', 0) + 1}x</td>
                <td style="text-align:right;color:{primary};font-weight:600;">42%</td>
            </tr>
            <tr>
                <td>Opportunity</td>
                <td style="text-align:right;color:#f8fafc;font-weight:600;">{detected.get('tables', 0) + 2}</td>
                <td style="text-align:right;color:{secondary};font-weight:600;">31%</td>
            </tr>
            <tr>
                <td>Watch</td>
                <td style="text-align:right;color:#f8fafc;font-weight:600;">3</td>
                <td style="text-align:right;color:#f59e0b;font-weight:600;">27%</td>
            </tr>
        </tbody>
    </table>
</div>
"""
    elif component_type == "charts":
        html = f"""<!-- component: {anchor} -->
<div class="card span-6" data-component="{component_id}">
    <header style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <div>
            <div class="meta-label">Auto Chart</div>
            <h2 style="margin:6px 0 0;color:#f8fafc;font-size:18px;font-weight:600;">Generated Pattern</h2>
        </div>
        <span class="chip" style="gap:6px;color:{primary};border-color:{primary}44;background:{primary}18;">
            <i data-lucide="line-chart" aria-hidden="true"></i>
            {theme.title()}
        </span>
    </header>
    <div class="chart-canvas" role="img" aria-label="Auto generated chart from screenshot analysis">
        <svg viewBox="0 0 640 280" style="position:absolute;inset:24px;">
            <defs>
                <linearGradient id="{component_id}-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="{primary}32" />
                    <stop offset="100%" stop-color="{primary}06" />
                </linearGradient>
            </defs>
            <path d="M0 220 L80 196 L160 168 L240 144 L320 118 L400 94 L480 82 L560 70 L640 60 L640 260 L0 260 Z" fill="url(#{component_id}-fill)" />
            <polyline points="0,220 80,196 160,168 240,144 320,118 400,94 480,82 560,70 640,60"
                stroke="{secondary}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="640" cy="60" r="8" fill="{secondary}" />
        </svg>
    </div>
</div>
"""
    else:  # sidebars or others default to navigation card
        html = f"""<!-- component: {anchor} -->
<aside class="card span-3" data-component="{component_id}" style="background:{background};border-color:{secondary}33;min-height:340px;padding:24px;">
    <div class="meta-label">Auto Sidebar</div>
    <nav aria-label="Generated navigation" style="margin-top:18px;display:flex;flex-direction:column;gap:10px;">
        <a class="chip" style="color:{primary};border-color:{primary}55;background:{primary}18;" href="#">
            <i data-lucide="star" aria-hidden="true"></i>
            Highlight
        </a>
        <a class="chip" style="color:#f8fafc;border-color:rgba(148,163,184,0.18);" href="#">
            <i data-lucide="layers" aria-hidden="true"></i>
            Layout ({detected.get('tables', 0)} tables)
        </a>
        <a class="chip" style="color:#f8fafc;border-color:rgba(148,163,184,0.18);" href="#">
            <i data-lucide="monitor" aria-hidden="true"></i>
            {theme.title()} Theme
        </a>
    </nav>
</aside>
"""
    return html, anchor, filename, primary, secondary


def _auto_update_library(
    base_dir: Path,
    metadata: Dict[str, Any],
    metadata_path: Path,
    analysis_entries: List[Dict[str, Any]],
    component_catalog_path: Path,
    guardrails_path: Path,
) -> List[str]:
    generated_ids: List[str] = []
    auto_dir = _resolve_path(base_dir, Path("templates/components/auto_generated"))
    _ensure_dir(auto_dir)

    now = datetime.utcnow()
    if not component_catalog_path.exists():
        component_catalog_path.write_text("# Component Catalog\n\n", encoding="utf-8")
    if not guardrails_path.exists():
        guardrails_path.write_text("# Component Library\n\n", encoding="utf-8")
    meta_components = metadata.setdefault("components", [])

    for entry in analysis_entries:
        analysis = entry["analysis"]
        filename = entry["filename"]
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        category_map = {
            "kpi_cards": "kpi_cards",
            "tables": "data_tables",
            "charts": "chart_visuals",
            "sidebars": "navigation",
        }
        for component_type, count in analysis.get("detected_components", {}).items():
            if count <= 0:
                continue
            component_id = f"auto_{component_type}_{stamp}"
            if any(c.get("id") == component_id for c in meta_components):
                continue
            html, anchor, html_filename, primary, secondary = _generate_component_html(component_id, component_type, analysis)
            target_path = auto_dir / html_filename
            target_path.write_text(html, encoding="utf-8")

            component_entry = {
                "id": component_id,
                "name": f"Auto {component_type.replace('_', ' ').title()} ({now.strftime('%Y-%m-%d %H:%M UTC')})",
                "category": category_map.get(component_type, "layout_patterns"),
                "template": f"templates/components/auto_generated/{html_filename}#{anchor}",
                "description": f"Auto-generated from screenshot {filename}.",
                "data_shape": "auto",
                "supports_dark_mode": True,
                "recommended_span": 6 if component_type in {"charts", "tables"} else 3 if component_type == "sidebars" else 4,
                "css_tokens": ["auto-generated", "mockup"],
                "guardrails": [
                    "Review auto-generated component before production use",
                    "Adjust palette to match design system"
                ],
            }
            meta_components.append(component_entry)
            generated_ids.append(component_id)

            # Append to catalog
            catalog_entry = [
                f"### Auto Component — {component_entry['name']}",
                f"- Component ID: `{component_id}`",
                f"- Template: `{component_entry['template']}`",
                f"- Generated from: `{filename}`",
                f"- Theme: {analysis.get('theme', 'unknown')}  | Palette: {', '.join(analysis.get('color_palette', [])[:4])}",
                ""
            ]
            with component_catalog_path.open("a", encoding="utf-8") as cat:
                cat.write("\n" + "\n".join(catalog_entry))

            # Append to guardrails component library
            guardrail_entry = [
                f"- **{component_entry['name']}** (`{component_id}`) — auto-generated from `{filename}`. Review before client delivery.",
            ]
            with guardrails_path.open("a", encoding="utf-8") as guardrail_doc:
                guardrail_doc.write("\n" + guardrail_entry[0] + "\n")

    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return generated_ids


def create_mockup_library_handlers(base_dir: Path) -> Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]:
    base_dir = base_dir.resolve()

    def list_mockup_components(arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            metadata = _load_metadata(base_dir)
            category_filter = arguments.get("category")
            components = metadata.get("components", [])
            if category_filter:
                components = [c for c in components if c.get("category") == category_filter]
            return {
                "success": True,
                "count": len(components),
                "components": components,
                "groups": metadata.get("component_groups"),
                "base_template": str(BASE_TEMPLATE_PATH),
                "base_stylesheet": str(BASE_STYLESHEET_PATH),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def generate_mockup_html(arguments: Dict[str, Any]) -> Dict[str, Any]:
        components = arguments.get("components") or []
        if not isinstance(components, list) or not components:
            return {"success": False, "error": "components array is required", "error_type": "invalid_input"}

        title = str(arguments.get("title") or "Power BI Dashboard")
        heading = str(arguments.get("heading") or "Executive Overview")
        subtitle = str(arguments.get("subtitle") or "Auto-generated with MCP mockup library")

        try:
            metadata = _load_metadata(base_dir)
            navigation_ids: List[str] = []
            control_ids: List[str] = []
            content_ids: List[str] = []

            for comp_id in components:
                meta = next((c for c in metadata.get("components", []) if c["id"] == comp_id), None)
                if not meta:
                    raise ValueError(f"Component '{comp_id}' not found in metadata.")
                category = meta.get("category")
                if category == "navigation":
                    navigation_ids.append(comp_id)
                elif category == "interactive_controls":
                    control_ids.append(comp_id)
                else:
                    content_ids.append(comp_id)

            navigation_html = _build_component_markup(base_dir, metadata, navigation_ids)
            controls_html = _build_component_markup(base_dir, metadata, control_ids)
            content_html = _build_component_markup(base_dir, metadata, content_ids)
            html = _render_base_template(base_dir, title, heading, subtitle, navigation_html, controls_html, content_html)
            return {
                "success": True,
                "html": html,
                "components_used": {
                    "navigation": navigation_ids,
                    "controls": control_ids,
                    "content": content_ids,
                },
                "metadata_version": metadata.get("version"),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def analyze_mockup_screenshots(arguments: Dict[str, Any]) -> Dict[str, Any]:
        folder_arg = arguments.get("folder")
        folder = Path(folder_arg) if folder_arg else SCREENSHOT_INCOMING
        incoming_dir = _resolve_path(base_dir, folder)
        processed_dir = _resolve_path(base_dir, SCREENSHOT_PROCESSED)
        metadata = _load_metadata(base_dir)
        metadata_path = _resolve_path(base_dir, Path("docs/component_metadata.json"))
        log_path = _resolve_path(base_dir, arguments.get("log_path") and Path(arguments["log_path"]) or DEFAULT_LOG_PATH)
        auto_update = bool(arguments.get("auto_update_library"))
        component_catalog_path = _resolve_path(base_dir, Path("docs/component_catalog.md"))
        guardrails_path = _resolve_path(base_dir, Path("guardrails/component_library_v1.0.md"))

        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(incoming_dir, exist_ok=True)

        images = sorted([p for p in incoming_dir.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
        if not images:
            return {"success": True, "processed": 0, "message": f"No screenshots found in {incoming_dir}."}

        entries: List[Dict[str, Any]] = []
        for image_path in images:
            analysis = analyze_screenshot(image_path, metadata_path)
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            entries.append({
                "filename": image_path.name,
                "timestamp": timestamp,
                "analysis": analysis,
            })
            target_name = f"{image_path.stem}_{int(time.time())}{image_path.suffix.lower()}"
            shutil.move(str(image_path), str(processed_dir / target_name))

        _append_log(log_path, entries)
        generated_components: List[str] = []
        if auto_update:
            generated_components = _auto_update_library(
                base_dir,
                metadata,
                metadata_path,
                entries,
                component_catalog_path,
                guardrails_path,
            )
        return {
            "success": True,
            "processed": len(entries),
            "log_path": str(log_path),
            "entries": entries,
            "metadata_version": metadata.get("version"),
            "auto_generated_components": generated_components,
        }

    return {
        "mockup_list_components": list_mockup_components,
        "mockup_generate_html": generate_mockup_html,
        "mockup_analyze_screenshots": analyze_mockup_screenshots,
    }
