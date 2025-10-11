"""
html_guardrails.py

Lightweight helpers to guide and validate Claude-generated HTML mockups.

Tools exposed:
- help_html_mockup_guardrails: Return canonical guardrails text and checklist
- validate_html_mockup: Score an HTML string against guardrails and suggest fixes
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple


def _read_guardrails_text(base_dir: Optional[str]) -> str:
    """Read the canonical mockup/visualization guardrails.

    Canonical source: enhanced_pbi_mockup_guardrails.md at the repo root.
    """
    try:
        if base_dir:
            enhanced = os.path.join(base_dir, 'enhanced_pbi_mockup_guardrails.md')
            if os.path.exists(enhanced):
                with open(enhanced, 'r', encoding='utf-8') as f:
                    return f.read()
    except Exception:
        pass
    return (
        "Mockup guardrails not found. Expected enhanced_pbi_mockup_guardrails.md at repo root."
    )


def _detect_flag(html: str, patterns: List[str]) -> bool:
    return any(p.lower() in html.lower() for p in patterns)


def _compute_screen_bucket(width: Optional[int], height: Optional[int]) -> Dict[str, Any]:
    """Infer screen traits and recommended container width based on proposed guardrails.

    Buckets (width in px):
    - 3440+: max 3200, 3 columns
    - 2560–3439: max 2400
    - 1920–2559: max 1800
    - 1440–1919: max 1400
    - <1440: max 1200
    """
    try:
        w = int(width) if width is not None else None
    except Exception:
        w = None
    try:
        h = int(height) if height is not None else None
    except Exception:
        h = None

    is_ultrawide = False
    if w is not None and h is not None and h > 0:
        ratio = float(w) / float(h)
        # Mark ultrawide if extremely wide or >=3440
        is_ultrawide = (w >= 3440) or (ratio >= 2.3)
    elif w is not None:
        is_ultrawide = (w >= 3440)

    if w is None:
        # Unknown screen; fall back to a safe default (FHD)
        w = 1920

    if w >= 3440:
        rec = '3200px'
    elif w >= 2560:
        rec = '2400px'
    elif w >= 1920:
        rec = '1800px'
    elif w >= 1440:
        rec = '1400px'
    else:
        rec = '1200px'

    return {
        'width': w,
        'height': h,
        'is_ultrawide': is_ultrawide,
        'recommended_max_width': rec,
        'recommended_breakpoints': [1440, 1920, 2560, 3440]
    }


def _detect_os_screen_size() -> Tuple[Optional[int], Optional[int]]:
    """Best-effort local screen size detection.
    - Windows: use ctypes windll.user32
    - Others: return (None, None)
    Safe to call in non-interactive/server context; failures return None values.
    """
    try:
        import platform
        if platform.system() == 'Windows':
            import ctypes
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            user32.SetProcessDPIAware()  # avoid DPI scaling artifacts
            w = int(user32.GetSystemMetrics(0))
            h = int(user32.GetSystemMetrics(1))
            return w, h
    except Exception:
        pass
    return None, None


def _validate_html(
    html: str,
    expected_library: Optional[str],
    expected_theme: Optional[str],
    layout_mode: str = 'auto',  # 'auto' | 'centered' | 'full-width'
    screen_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    reasons: List[str] = []
    ok = True

    # Basic HTML and head/body presence
    if '<html' not in html.lower() or '<body' not in html.lower():
        ok = False
        reasons.append('Missing <html> or <body> tags')
    # Meta viewport for responsive (recommendation, not hard fail)
    if 'name="viewport"' not in html.lower():
        reasons.append('Missing meta viewport tag')

    # CSS baseline: Tailwind OR any stylesheet/style tag (recommendation, not hard fail)
    has_tailwind = ('cdn.tailwindcss.com' in html)
    has_stylesheet = ('<link' in html.lower() and 'rel="stylesheet"' in html.lower()) or ('<style' in html.lower())
    if not (has_tailwind or has_stylesheet):
        reasons.append('No CSS baseline detected (consider Tailwind CDN or a stylesheet)')

    # Container width heuristics: honor layout_mode
    has_container = ('max-w-' in html) or ('mx-auto' in html) or ('container' in html and 'mx-auto' in html)
    if layout_mode == 'centered':
        if not has_container:
            reasons.append('Expected centered container (max-w ~1400px with mx-auto)')
    elif layout_mode == 'full-width':
        # No requirement; allow full-bleed layout
        pass
    else:  # auto
        # Suggest a container only if content looks very wide with many long rows
        if (html.count('<tr') > 60) and not has_container:
            reasons.append('Consider a centered container to keep content readable on wide screens')

    # Screen-aware checks: if we know the screen, check for a nearby max-width hint
    if screen_info:
        rec = str(screen_info.get('recommended_max_width') or '')
        try:
            rec_px = int(rec.replace('px', '').strip()) if rec.endswith('px') else None
        except Exception:
            rec_px = None
        if rec_px is not None:
            # Look for Tailwind arbitrary max-w-[NNNNpx] or inline style using similar width
            tailwind_match = f"max-w-[{rec_px}px]" in html
            inline_match = bool(re.search(rf"max-width\s*:\s*{rec_px}px", html, flags=re.IGNORECASE))
            if not (tailwind_match or inline_match or layout_mode == 'full-width'):
                reasons.append(
                    f"Add responsive container near {rec_px}px and center it (e.g., <div class=\"max-w-[{rec_px}px] mx-auto\">)."
                )
            # Also accept clamped widths to avoid oversizing in panels (95% viewport)
            if 'max-width' in html.lower():
                # If inline style is present, suggest using Math.min with 95% viewport comment
                reasons.append('Ensure container width is clamped to ~95% of available viewport to prevent overflow in side panels')
    # Header/title
    if not re.search(r'<h1[^>]*>', html, flags=re.IGNORECASE):
        reasons.append('Missing page title <h1>')
    # Sections / layout presence: accept grid OR flex
    has_grid = _detect_flag(html, ['grid-cols-', 'grid '])
    has_flex = _detect_flag(html, ['flex ', 'flex-'])
    if not (has_grid or has_flex):
        reasons.append('Missing structured layout (use CSS grid or flex for sections)')
    # Chart library is optional; allow any rendering approach (SVGs, CSS-only, libraries, etc.)
    # If expected_library is provided, do a best-effort hint-only check without failing ok.
    lib = (expected_library or '').lower()
    if lib in {'vega-lite', 'vega_lite', 'vega'}:
        if ('vega-lite@' not in html) and ('vega-lite' not in html) and ('vegaEmbed' not in html):
            reasons.append('Hint: Vega-Lite expected but not detected (allowed).')
    elif lib in {'chartjs', 'chart.js'}:
        if ('cdn.jsdelivr.net/npm/chart.js' not in html) or (('new Chart(' not in html) and ('Chart(' not in html)):
            reasons.append('Hint: Chart.js expected but not detected (allowed).')

    # Theme hint
    if expected_theme:
        if expected_theme.lower() == 'dark' and 'class="dark"' not in html and 'bg-slate-9' not in html:
            reasons.append('Expected dark theme but dark mode hints missing (class="dark", dark palette)')

    # Visual count is not enforced; collect a soft metric only
    visuals = 0
    visuals += 1 if 'kpi' in html.lower() or 'KPI' in html else 0
    visuals += len(re.findall(r'<canvas ', html, flags=re.IGNORECASE))
    visuals += len(re.findall(r'vegaEmbed\(', html, flags=re.IGNORECASE))
    visuals += len(re.findall(r'<table ', html, flags=re.IGNORECASE))

    # Color palette heuristics: detect too many distinct hex colors
    # Exclude common neutrals and CSS variables; focus on literal hex usage
    hex_colors = set(c.lower() for c in re.findall(r'#[0-9a-fA-F]{6}', html))
    # Known neutrals to ignore in counting towards the palette limit
    neutral_whitelist = {
        '#ffffff', '#fffafa', '#fafafa', '#f8f9fa', '#f5f5f5', '#f0f0f0', '#ecf0f1',
        '#2c3e50', '#34495e', '#bdc3c7', '#e0e0e0', '#ecf0f1'
    }
    palette_count = len([c for c in hex_colors if c not in neutral_whitelist])
    # If there are more than 3 distinct non-neutral hex colors, suggest reducing
    if palette_count > 3:
        reasons.append('Too many distinct colors detected; prefer 1 primary + semantic accents')

    # One-page heuristic: look for very large inline content or excessive repeated rows
    if html.count('<tr') > 60:
        reasons.append('Too many table rows; may not fit on a single page')

    # Chart structure heuristics (SVG-first rules)
    has_svg = '<svg' in html.lower()
    css_height_bars = bool(re.search(r'style\s*=\s*"[^"]*height\s*:\s*\d+%\s*;?', html, flags=re.IGNORECASE))
    if css_height_bars and not has_svg:
        reasons.append('Charts appear to be CSS-based; prefer SVG with explicit coordinates and viewBox')
    if has_svg and 'viewbox' not in html.lower():
        reasons.append('SVG charts should include a viewBox for responsive scaling')
    # Combo chart hints: dashed polylines and circles for points
    if has_svg and ('polyline' in html.lower()) and ('stroke-dasharray' not in html.lower()):
        reasons.append('Combo lines should use dashed stroke for comparison series and include point markers')
    # Waterfall connectors
    if has_svg and ('waterfall' in html.lower()) and ('stroke-dasharray' not in html.lower()):
        reasons.append('Waterfall charts should include dashed connector lines between segments')

    return {
        'ok': ok,
        'reasons': reasons,
        'visuals_count': visuals,
        'signals': {
            'has_tailwind': has_tailwind,
            'has_stylesheet': has_stylesheet,
            'has_container': has_container,
            'has_grid': has_grid,
            'has_flex': has_flex,
            'has_viewport': ('name="viewport"' in html.lower()),
        }
    }


def _suggest_improvements(
    html: str,
    expected_library: Optional[str],
    layout_mode: str = 'auto',
    screen_info: Optional[Dict[str, Any]] = None
) -> List[str]:
    suggestions: List[str] = []
    if ('cdn.tailwindcss.com' not in html) and ('<style' not in html.lower()) and ('rel="stylesheet"' not in html.lower()):
        suggestions.append('Add a CSS baseline (Tailwind CDN or a stylesheet)')
    if layout_mode == 'centered':
        if ('max-w-' not in html) or ('mx-auto' not in html):
            suggestions.append('Wrap content in a centered container: <div class="max-w-[1400px] mx-auto p-6">...</div>')
    if not re.search(r'<h1[^>]*>', html, flags=re.IGNORECASE):
        suggestions.append('Add a page title <h1 class="text-2xl font-semibold">Title</h1>')
    if not (_detect_flag(html, ['grid-cols-', 'grid ']) or _detect_flag(html, ['flex ', 'flex-'])):
        suggestions.append('Use CSS grid or flex for sections (e.g., grid grid-cols-3 gap-4 or flex flex-col gap-4)')
    # Do not enforce any charting library; let the agent choose its preferred rendering.
    if html.count('<tr') > 60:
        suggestions.append('Reduce table rows to keep content within one page (e.g., 10–12 rows)')
    if 'name="viewport"' not in html.lower():
        suggestions.append('Add meta viewport for responsiveness: <meta name="viewport" content="width=device-width, initial-scale=1"/>')
    # Screen-aware sizing
    if screen_info:
        rec = screen_info.get('recommended_max_width')
        if rec and ('max-w-[' not in html) and ('max-width' not in html.lower()) and layout_mode != 'full-width':
            suggestions.append(f'Set container to about {rec} with margin:0 auto for your screen')
        # Encourage adding resize handler
        suggestions.append('Add a small JS optimizeLayout() that sets container max-width based on window.innerWidth and re-runs on resize')
    # Power BI specific suggestions (always on by default)
    if '<style' not in html.lower():
        suggestions.append('Inline a <style> block so the visual is self-contained in one HTML file')
    if '<script' not in html.lower():
        suggestions.append('Inline a <script> block for rendering logic (no build tools)')
    # Storage API usage hints
    if _detect_flag(html, ['localstorage', 'sessionstorage', 'indexeddb', 'document.cookie']):
        suggestions.append('Remove usage of localStorage/sessionStorage/IndexedDB/cookies (blocked in Power BI iframe)')
    # Financial formatting
    if 'intl.numberformat' not in html.lower():
        suggestions.append('Use Intl.NumberFormat for currency/percentages and large numbers')
    # Keyboard navigation and focus
    if ':focus' not in html:
        suggestions.append('Add visible focus styles and ensure Tab/Enter/Space keyboard interactions')
    # Loading/error states
    if not _detect_flag(html, ['loading', 'spinner', 'error']):
        suggestions.append('Provide loading overlays and friendly error states for slow/failed operations')
    # Color palette suggestions
    # If many literal colors, nudge towards monochromatic usage and semantic-only accents
    hex_colors = set(c.lower() for c in re.findall(r'#[0-9a-fA-F]{6}', html))
    neutral_whitelist = {
        '#ffffff', '#fffafa', '#fafafa', '#f8f9fa', '#f5f5f5', '#f0f0f0', '#ecf0f1',
        '#2c3e50', '#34495e', '#bdc3c7', '#e0e0e0', '#ecf0f1'
    }
    palette_count = len([c for c in hex_colors if c not in neutral_whitelist])
    if palette_count > 3:
        suggestions.append('Use a restricted palette: primary shades + semantic green/red only; avoid rainbow charts')
    return suggestions


def create_html_guardrail_handlers(connection_state, config):
    base_dir = None
    try:
        # src/.. parent directory
        import inspect
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    except Exception:
        pass

    def help_html_mockup_guardrails(arguments: Dict[str, Any]) -> Dict[str, Any]:
        text = _read_guardrails_text(base_dir)
        checklist = [
            'Call html: guardrails before drafting',
            'Generate first HTML draft (single file; inline CSS/JS; CDN deps)',
            'Call html: validate mockup with full HTML (layout_mode as needed)',
            'Iterate if suggestions/violations returned (1–2 rounds)',
            'Return final single-file HTML only'
        ]
        screen_width = arguments.get('screen_width')
        screen_height = arguments.get('screen_height')
        if screen_width is None or screen_height is None:
            # Attempt to auto-detect on this host (best-effort)
            auto_w, auto_h = _detect_os_screen_size()
            if screen_width is None:
                screen_width = auto_w
            if screen_height is None:
                screen_height = auto_h
        detect_ultrawide = bool(arguments.get('detect_ultrawide', True))
        screen_info = _compute_screen_bucket(screen_width, screen_height)
        # If caller prefers not to detect ultrawide, override flag
        if not detect_ultrawide:
            screen_info['is_ultrawide'] = False
        return {
            'success': True,
            'guardrails': text,
            'checklist': checklist,
            'user_screen_info': screen_info
        }

    def validate_html_mockup(arguments: Dict[str, Any]) -> Dict[str, Any]:
        html = arguments.get('html') or ''
        expected_library = arguments.get('expected_library')
        expected_theme = arguments.get('expected_theme')
        layout_mode = str(arguments.get('layout_mode') or 'auto').lower()
        if layout_mode not in {'auto', 'centered', 'full-width'}:
            layout_mode = 'auto'
        if not isinstance(html, str) or not html.strip():
            return {'success': False, 'error': 'html string is required', 'error_type': 'invalid_input'}
        # Screen parameters (optional)
        screen_width = arguments.get('screen_width')
        screen_height = arguments.get('screen_height')
        if screen_width is None or screen_height is None:
            auto_w, auto_h = _detect_os_screen_size()
            if screen_width is None:
                screen_width = auto_w
            if screen_height is None:
                screen_height = auto_h
        detect_ultrawide = bool(arguments.get('detect_ultrawide', True))
        screen_info = _compute_screen_bucket(screen_width, screen_height)
        if not detect_ultrawide:
            screen_info['is_ultrawide'] = False

        validation = _validate_html(html, expected_library, expected_theme, layout_mode, screen_info)
        suggestions = _suggest_improvements(html, expected_library, layout_mode, screen_info)
        # Library-agnostic; score using core signals
        sig = validation.get('signals', {})
        score = 0
        score += 1 if validation.get('ok') else 0
        score += 1 if (sig.get('has_tailwind') or sig.get('has_stylesheet')) else 0
        score += 1 if re.search(r'<h1[^>]*>', html, flags=re.IGNORECASE) else 0
        score += 1 if (sig.get('has_grid') or sig.get('has_flex')) else 0
        score += 1 if sig.get('has_viewport') else 0
        result: Dict[str, Any] = {
            'success': True,
            'ok': validation.get('ok'),
            'score': score,
            'reasons': validation.get('reasons'),
            'visuals_count': validation.get('visuals_count'),
            'suggestions': suggestions,
            'layout_mode': layout_mode,
            'profile': 'powerbi',
            'user_screen_info': screen_info
        }
        # Always apply Power BI style violations by default
        violations: List[str] = []
        # Single-file and CDN-only deps: flag local/relative imports
        for m in re.finditer(r'<link[^>]+href="([^"]+)"', html, flags=re.IGNORECASE):
            href = m.group(1)
            if not (href.startswith('http://') or href.startswith('https://') or href.startswith('//')):
                violations.append(f'External stylesheet not CDN-based: {href}')
        for m in re.finditer(r'<script[^>]+src="([^"]+)"', html, flags=re.IGNORECASE):
            src = m.group(1)
            if not (src.startswith('http://') or src.startswith('https://') or src.startswith('//')):
                violations.append(f'External script not CDN-based: {src}')
        # Storage APIs
        if _detect_flag(html, ['localstorage']):
            violations.append('Uses localStorage (disallowed)')
        if _detect_flag(html, ['sessionstorage']):
            violations.append('Uses sessionStorage (disallowed)')
        if _detect_flag(html, ['indexeddb']):
            violations.append('Uses IndexedDB (disallowed)')
        if _detect_flag(html, ['document.cookie']):
            violations.append('Uses document.cookie (disallowed)')
        # Large tables without virtualization
        if html.count('<tr') > 120:
            violations.append('Large table (>120 rows) with no virtualization/pagination detected')
        # Add violations list to result
        result['violations'] = violations
        # Optional: compare against palette if provided (screenshot_colors)
        try:
            palette = arguments.get('screenshot_colors') or []
            used = []
            for col in palette[:8]:
                c = str(col).lower()
                if c and c in html.lower():
                    used.append(col)
            if palette:
                result['palette_hint'] = {'palette_size': len(palette), 'used_in_html': used}
        except Exception:
            pass
        return result

    return {
        'help_html_mockup_guardrails': help_html_mockup_guardrails,
        'validate_html_mockup': validate_html_mockup,
    }
