"""
PBIP HTML Generator (Vue 3 Version) - Generates interactive HTML dashboard for PBIP analysis.

This module creates a comprehensive, interactive HTML dashboard with Vue 3,
D3.js visualizations, searchable tables, and dependency graphs.
"""

import html
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class PbipHtmlGenerator:
    """Generates interactive HTML dashboard for PBIP analysis using Vue 3."""

    def __init__(self):
        """Initialize the HTML generator."""
        self.logger = logger

    def generate_full_report(
        self,
        model_data: Dict[str, Any],
        report_data: Optional[Dict[str, Any]],
        dependencies: Dict[str, Any],
        output_path: str,
        repository_name: str = "PBIP Repository",
        enhanced_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            model_data: Parsed model data
            report_data: Optional parsed report data
            dependencies: Dependency analysis results
            output_path: Output directory path
            repository_name: Name of the repository
            enhanced_results: Optional enhanced analysis results (BPA, perspectives, etc.)

        Returns:
            Path to generated HTML file

        Raises:
            IOError: If unable to write output file
        """
        # Convert to absolute path for MCP compatibility
        abs_output_path = os.path.abspath(output_path)
        self.logger.info(f"Generating Vue 3 HTML report to {abs_output_path}")

        # Create output directory
        os.makedirs(abs_output_path, exist_ok=True)

        # Generate HTML content
        html_content = self._build_html_document(
            model_data,
            report_data,
            dependencies,
            repository_name,
            enhanced_results
        )

        # Generate filename from repository name and timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean repository name for filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in repository_name)
        safe_name = safe_name.replace(' ', '_').strip('_')

        # Create meaningful filename
        filename = f"{safe_name}_PBIP_Analysis_{timestamp}.html"
        html_file = os.path.join(abs_output_path, filename)

        try:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"Vue 3 HTML report generated: {html_file}")
            return html_file

        except Exception as e:
            self.logger.error(f"Failed to write HTML report: {e}")
            raise IOError(f"Failed to write HTML report: {e}")

    def _build_html_document(
        self,
        model_data: Dict,
        report_data: Optional[Dict],
        dependencies: Dict,
        repo_name: str,
        enhanced_results: Optional[Dict] = None
    ) -> str:
        """Build complete HTML document with Vue 3."""
        # Prepare data for JavaScript
        data_json = {
            "model": model_data,
            "report": report_data,
            "dependencies": dependencies,
            "enhanced": enhanced_results,
            "generated": datetime.now().isoformat(),
            "repository_name": repo_name
        }

        # Serialize to JSON string
        data_json_str = json.dumps(data_json, indent=2, ensure_ascii=False)

        # Build complete HTML
        html_content = self._get_vue3_template(data_json_str, repo_name)

        return html_content


    def _get_head_section(self, escaped_repo_name: str) -> str:
        """Get HTML head with meta tags and CDN imports."""
        return f"""    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_repo_name} - PBIP Analysis</title>

    <!-- Google Fonts: Fraunces (display), DM Sans (body), IBM Plex Mono (code) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

    <!-- Vue 3, D3.js, and Dagre for graph layouts -->
    <script src="https://cdn.jsdelivr.net/npm/vue@3.4.21/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
"""

    def _get_styles(self) -> str:
        """Get all CSS styles for Warm Terracotta design."""
        return f"""    <style>
        /* === WARM TERRACOTTA DESIGN SYSTEM === */
        :root {{
            /* Primary Warm Palette */
            --terracotta: #C4A484;
            --terracotta-dark: #A67B5B;
            --clay: #E8DDD3;
            --sand: #F5F1EB;
            --cream: #FAF8F5;
            --white: #FFFFFF;

            /* Earth Tones */
            --sienna: #9C6644;
            --umber: #6B4423;
            --olive: #606C38;
            --sage: #8B9D77;

            /* Text Colors */
            --ink: #2D2418;
            --charcoal: #4A4238;
            --stone: #7A7267;
            --pebble: #A9A196;

            /* Accent Colors */
            --coral: #E07A5F;
            --rust: #BC6C25;
            --ocean: #457B9D;

            /* Status Colors */
            --success: #606C38;
            --warning: #BC6C25;
            --danger: #9B2C2C;
            --info: #457B9D;

            /* Spacing */
            --space-xs: 4px;
            --space-sm: 8px;
            --space-md: 16px;
            --space-lg: 24px;
            --space-xl: 32px;
            --space-2xl: 48px;

            /* Border Radius */
            --radius-sm: 8px;
            --radius-md: 16px;
            --radius-lg: 24px;
            --radius-full: 9999px;

            /* Sidebar */
            --sidebar-width: 280px;
        }}

        *, *::before, *::after {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--cream);
            color: var(--ink);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }}

        /* Subtle texture overlay */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            opacity: 0.02;
            pointer-events: none;
            z-index: -1;
        }}

        /* === DARK MODE === */
        .dark-mode {{
            --cream: #1a1614;
            --sand: #252220;
            --clay: #332e2a;
            --white: #2d2825;
            --ink: #f5f1eb;
            --charcoal: #e8ddd3;
            --stone: #a9a196;
            --pebble: #7a7267;
            --terracotta: #d4b494;
            --sienna: #bc8664;
        }}

        .dark-mode body {{
            background: var(--cream);
        }}

        /* === LAYOUT === */
        .app-layout {{
            display: flex;
            min-height: 100vh;
        }}

        /* === SIDEBAR === */
        .sidebar {{
            width: var(--sidebar-width);
            background: var(--white);
            border-right: 1px solid var(--clay);
            display: flex;
            flex-direction: column;
            position: fixed;
            top: 0;
            left: 0;
            bottom: 0;
            z-index: 100;
            transition: transform 0.3s ease;
        }}

        .sidebar__header {{
            padding: var(--space-lg);
            border-bottom: 1px solid var(--clay);
        }}

        .sidebar__brand {{
            display: flex;
            align-items: center;
            gap: var(--space-md);
        }}

        .sidebar__logo {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--terracotta) 0%, var(--sienna) 100%);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(156, 102, 68, 0.2);
            flex-shrink: 0;
        }}

        .sidebar__logo svg {{
            width: 22px;
            height: 22px;
            color: var(--white);
        }}

        .sidebar__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 16px;
            font-weight: 600;
            color: var(--ink);
            line-height: 1.3;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}

        .sidebar__subtitle {{
            font-size: 12px;
            color: var(--stone);
            margin-top: 2px;
        }}

        .sidebar__nav {{
            flex: 1;
            overflow-y: auto;
            padding: var(--space-md);
        }}

        .nav-section {{
            margin-bottom: var(--space-lg);
        }}

        .nav-section__title {{
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--pebble);
            padding: var(--space-sm) var(--space-md);
            margin-bottom: var(--space-xs);
        }}

        .nav-item {{
            display: flex;
            align-items: center;
            gap: var(--space-md);
            padding: var(--space-md) var(--space-md);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
            font-family: inherit;
            font-size: 14px;
            color: var(--charcoal);
        }}

        .nav-item:hover {{
            background: var(--sand);
            color: var(--ink);
        }}

        .nav-item.active {{
            background: rgba(196, 164, 132, 0.15);
            color: var(--sienna);
            font-weight: 600;
        }}

        .nav-item.active::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 24px;
            background: var(--terracotta);
            border-radius: 0 3px 3px 0;
        }}

        .nav-item__icon {{
            width: 20px;
            height: 20px;
            color: var(--stone);
            flex-shrink: 0;
        }}

        .nav-item.active .nav-item__icon {{
            color: var(--sienna);
        }}

        .nav-item__text {{
            flex: 1;
        }}

        .nav-item__badge {{
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            background: var(--sand);
            border-radius: var(--radius-full);
            color: var(--stone);
        }}

        .nav-item.active .nav-item__badge {{
            background: rgba(196, 164, 132, 0.3);
            color: var(--sienna);
        }}

        .nav-subitems {{
            margin-left: 36px;
            padding-left: var(--space-md);
            border-left: 2px solid var(--clay);
            margin-top: var(--space-xs);
        }}

        .nav-subitem {{
            display: block;
            padding: var(--space-sm) var(--space-md);
            font-size: 13px;
            color: var(--stone);
            cursor: pointer;
            border-radius: var(--radius-sm);
            transition: all 0.15s ease;
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
        }}

        .nav-subitem:hover {{
            color: var(--charcoal);
            background: var(--sand);
        }}

        .nav-subitem.active {{
            color: var(--sienna);
            font-weight: 600;
        }}

        .sidebar__footer {{
            padding: var(--space-md);
            border-top: 1px solid var(--clay);
            display: flex;
            gap: var(--space-sm);
        }}

        /* === MAIN CONTENT === */
        .main-wrapper {{
            flex: 1;
            margin-left: var(--sidebar-width);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        /* === HEADER === */
        .header {{
            padding: var(--space-lg) var(--space-2xl);
            background: var(--white);
            border-bottom: 1px solid var(--clay);
            position: sticky;
            top: 0;
            z-index: 50;
        }}

        .header__inner {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: var(--space-lg);
        }}

        .header__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
        }}

        .header__actions {{
            display: flex;
            align-items: center;
            gap: var(--space-md);
        }}

        .search-box {{
            position: relative;
        }}

        .search-box__input {{
            width: 280px;
            padding: var(--space-md) var(--space-lg);
            padding-left: 44px;
            background: var(--sand);
            border: 2px solid transparent;
            border-radius: var(--radius-full);
            font-family: inherit;
            font-size: 14px;
            transition: all 0.3s ease;
        }}

        .search-box__input:focus {{
            outline: none;
            border-color: var(--terracotta);
            background: var(--white);
            box-shadow: 0 4px 20px rgba(196, 164, 132, 0.15);
        }}

        .search-box__icon {{
            position: absolute;
            left: var(--space-lg);
            top: 50%;
            transform: translateY(-50%);
            color: var(--stone);
            width: 18px;
            height: 18px;
        }}

        .btn-icon {{
            width: 44px;
            height: 44px;
            border-radius: var(--radius-md);
            border: none;
            background: var(--sand);
            color: var(--charcoal);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}

        .btn-icon:hover {{
            background: var(--clay);
            transform: translateY(-2px);
        }}

        .btn-icon svg {{
            width: 20px;
            height: 20px;
        }}

        /* === MAIN CONTENT AREA === */
        .main-content {{
            flex: 1;
            padding: var(--space-2xl);
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }}

        /* === HERO SECTION === */
        .hero {{
            display: grid;
            grid-template-columns: 1fr 360px;
            gap: var(--space-2xl);
            margin-bottom: var(--space-2xl);
        }}

        .hero__content {{
            padding-right: var(--space-xl);
        }}

        .hero__eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: var(--space-sm);
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--sienna);
            margin-bottom: var(--space-lg);
        }}

        .hero__eyebrow::before {{
            content: '';
            width: 24px;
            height: 2px;
            background: var(--terracotta);
            border-radius: 1px;
        }}

        .hero__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 42px;
            font-weight: 600;
            line-height: 1.15;
            letter-spacing: -0.02em;
            color: var(--ink);
            margin-bottom: var(--space-md);
        }}

        .hero__description {{
            font-size: 16px;
            line-height: 1.7;
            color: var(--stone);
            max-width: 520px;
        }}

        .hero__stats {{
            display: flex;
            gap: var(--space-xl);
            margin-top: var(--space-2xl);
            padding-top: var(--space-xl);
            border-top: 1px solid var(--clay);
        }}

        .hero-stat {{
            text-align: left;
        }}

        .hero-stat__value {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 36px;
            font-weight: 700;
            color: var(--ink);
            line-height: 1;
        }}

        .hero-stat__label {{
            font-size: 13px;
            color: var(--stone);
            margin-top: var(--space-xs);
        }}

        /* === FEATURE CARD === */
        .feature-card {{
            background: linear-gradient(135deg, var(--terracotta) 0%, var(--sienna) 100%);
            border-radius: var(--radius-lg);
            padding: var(--space-xl);
            color: var(--white);
            position: relative;
            overflow: hidden;
        }}

        .feature-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -30%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 50%);
            pointer-events: none;
        }}

        .feature-card__label {{
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 0.8;
            margin-bottom: var(--space-md);
        }}

        .feature-card__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 22px;
            font-weight: 600;
            margin-bottom: var(--space-md);
        }}

        .feature-card__value {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 56px;
            font-weight: 700;
            line-height: 1;
            margin-bottom: var(--space-md);
        }}

        .feature-card__meta {{
            font-size: 14px;
            opacity: 0.9;
        }}

        /* === METRICS GRID === */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--space-lg);
            margin-bottom: var(--space-2xl);
        }}

        .metric-card {{
            background: var(--white);
            border-radius: var(--radius-md);
            padding: var(--space-xl);
            border: 1px solid var(--clay);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--clay);
            transition: background 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(45, 36, 24, 0.08);
        }}

        .metric-card:hover::before {{
            background: var(--terracotta);
        }}

        .metric-card--coral::before {{ background: var(--coral); }}
        .metric-card--sage::before {{ background: var(--sage); }}
        .metric-card--ocean::before {{ background: var(--ocean); }}
        .metric-card--rust::before {{ background: var(--rust); }}

        .metric-card__icon {{
            width: 48px;
            height: 48px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: var(--space-lg);
        }}

        .metric-card--coral .metric-card__icon {{ background: rgba(224, 122, 95, 0.1); color: var(--coral); }}
        .metric-card--sage .metric-card__icon {{ background: rgba(139, 157, 119, 0.1); color: var(--sage); }}
        .metric-card--ocean .metric-card__icon {{ background: rgba(69, 123, 157, 0.1); color: var(--ocean); }}
        .metric-card--rust .metric-card__icon {{ background: rgba(188, 108, 37, 0.1); color: var(--rust); }}

        .metric-card__value {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 32px;
            font-weight: 700;
            color: var(--ink);
            line-height: 1;
            margin-bottom: var(--space-sm);
        }}

        .metric-card__label {{
            font-size: 14px;
            color: var(--stone);
        }}

        /* Additional metric card color variants */
        .metric-card--terracotta::before {{ background: var(--terracotta); }}
        .metric-card--sienna::before {{ background: var(--sienna); }}
        .metric-card--terracotta .metric-card__icon {{ background: rgba(196, 164, 132, 0.15); color: var(--terracotta-dark); }}
        .metric-card--sienna .metric-card__icon {{ background: rgba(156, 102, 68, 0.15); color: var(--sienna); }}

        .metric-card__icon svg {{
            width: 24px;
            height: 24px;
        }}

        /* === HERO SECTION === */
        .hero-section {{
            background: linear-gradient(135deg, var(--white) 0%, var(--sand) 100%);
            border-radius: var(--radius-lg);
            padding: var(--space-2xl);
            margin-bottom: var(--space-2xl);
            border: 1px solid var(--clay);
            text-align: center;
        }}

        .hero-section__eyebrow {{
            display: inline-block;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--sienna);
            padding: var(--space-sm) var(--space-lg);
            background: rgba(196, 164, 132, 0.15);
            border-radius: var(--radius-full);
            margin-bottom: var(--space-lg);
        }}

        .hero-section__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 36px;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: var(--space-md);
            line-height: 1.2;
        }}

        .hero-section__subtitle {{
            font-size: 16px;
            color: var(--stone);
            max-width: 600px;
            margin: 0 auto;
        }}

        /* === INFO GRID === */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--space-lg);
        }}

        .info-item {{
            display: flex;
            flex-direction: column;
            gap: var(--space-xs);
        }}

        .info-item__label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--stone);
        }}

        .info-item__value {{
            font-size: 15px;
            color: var(--ink);
        }}

        /* === INSIGHTS GRID === */
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--space-lg);
        }}

        .insight-card {{
            display: flex;
            gap: var(--space-lg);
            padding: var(--space-lg);
            background: var(--sand);
            border-radius: var(--radius-md);
            transition: all 0.2s ease;
        }}

        .insight-card:hover {{
            background: var(--clay);
            transform: translateY(-2px);
        }}

        .insight-card__icon {{
            width: 48px;
            height: 48px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .insight-card__icon svg {{
            width: 24px;
            height: 24px;
        }}

        .insight-card__icon--terracotta {{ background: rgba(196, 164, 132, 0.2); color: var(--terracotta-dark); }}
        .insight-card__icon--sienna {{ background: rgba(156, 102, 68, 0.2); color: var(--sienna); }}
        .insight-card__icon--sage {{ background: rgba(139, 157, 119, 0.2); color: var(--olive); }}
        .insight-card__icon--ocean {{ background: rgba(69, 123, 157, 0.2); color: var(--ocean); }}

        .insight-card__content {{
            flex: 1;
        }}

        .insight-card__title {{
            font-size: 13px;
            font-weight: 600;
            color: var(--stone);
            margin-bottom: var(--space-xs);
        }}

        .insight-card__value {{
            font-size: 15px;
            color: var(--ink);
            font-weight: 500;
        }}

        /* === ALERTS === */
        .alert {{
            display: flex;
            gap: var(--space-lg);
            padding: var(--space-lg);
            border-radius: var(--radius-md);
            margin-bottom: var(--space-lg);
            border-left: 4px solid;
        }}

        .alert--warning {{
            background: rgba(188, 108, 37, 0.08);
            border-left-color: var(--warning);
        }}

        .alert--success {{
            background: rgba(96, 108, 56, 0.08);
            border-left-color: var(--success);
        }}

        .alert--danger {{
            background: rgba(155, 44, 44, 0.08);
            border-left-color: var(--danger);
        }}

        .alert--info {{
            background: rgba(69, 123, 157, 0.08);
            border-left-color: var(--info);
        }}

        .alert__icon {{
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }}

        .alert__icon svg {{
            width: 24px;
            height: 24px;
        }}

        .alert--warning .alert__icon {{ color: var(--warning); }}
        .alert--success .alert__icon {{ color: var(--success); }}
        .alert--danger .alert__icon {{ color: var(--danger); }}
        .alert--info .alert__icon {{ color: var(--info); }}

        /* === UNUSED SUMMARY TEXTAREA === */
        .unused-summary-container {{
            margin-top: var(--space-md);
        }}

        .unused-summary-textarea {{
            width: 100%;
            min-height: 400px;
            max-height: 600px;
            padding: var(--space-md);
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.6;
            background: var(--cream);
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            resize: vertical;
            color: var(--ink);
        }}

        .unused-summary-textarea:focus {{
            outline: none;
            border-color: var(--terracotta);
            box-shadow: 0 0 0 3px rgba(188, 108, 37, 0.1);
        }}

        .success-state {{
            text-align: center;
            padding: var(--space-lg);
            color: var(--success);
            font-weight: 500;
        }}

        .success-state--large {{
            padding: var(--space-xl);
        }}

        .success-state__icon {{
            font-size: 48px;
            margin-bottom: var(--space-md);
        }}

        .success-state__title {{
            color: var(--success);
            margin-bottom: var(--space-sm);
        }}

        .success-state__text {{
            color: var(--stone);
            font-weight: normal;
        }}

        /* === USAGE MATRIX === */
        .usage-filter-select {{
            padding: var(--space-xs) var(--space-sm);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            background: var(--cream);
            color: var(--ink);
            font-size: 13px;
            cursor: pointer;
        }}

        .usage-filter-select:focus {{
            outline: none;
            border-color: var(--terracotta);
        }}

        .usage-matrix-section {{
            margin-bottom: var(--space-xl);
        }}

        .usage-matrix-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-md);
        }}

        .usage-matrix-title {{
            margin: 0;
            color: var(--ink);
            font-size: 16px;
            font-weight: 600;
        }}

        .usage-matrix-actions {{
            display: flex;
            gap: var(--space-xs);
        }}

        .usage-matrix-container {{
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
        }}

        /* Collapsible Groups */
        .collapsible-group {{
            border-bottom: 1px solid var(--sand);
        }}

        .collapsible-group:last-child {{
            border-bottom: none;
        }}

        .collapsible-header {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-sm) var(--space-md);
            background: var(--clay);
            cursor: pointer;
            user-select: none;
            transition: background 0.2s ease;
        }}

        .collapsible-header:hover {{
            background: var(--sand);
        }}

        .collapsible-header.collapsed {{
            background: var(--cream);
        }}

        .collapsible-icon {{
            font-size: 10px;
            color: var(--stone);
            width: 12px;
            text-align: center;
        }}

        .collapsible-title {{
            font-weight: 600;
            color: var(--ink);
            flex: 1;
        }}

        .collapsible-count {{
            color: var(--stone);
            font-size: 12px;
        }}

        .collapsible-stats {{
            display: flex;
            gap: var(--space-sm);
            font-size: 11px;
        }}

        .collapsible-stats .stat-used {{
            color: var(--pine);
        }}

        .collapsible-stats .stat-unused {{
            color: var(--rust);
        }}

        .collapsible-content {{
            background: var(--cream);
        }}

        .collapsible-content .usage-matrix-table {{
            margin: 0;
        }}

        .collapsible-content .usage-matrix-table thead {{
            background: var(--sand);
        }}

        .usage-matrix-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        .usage-matrix-table thead {{
            position: sticky;
            top: 0;
            background: var(--clay);
            z-index: 1;
        }}

        .usage-matrix-table th {{
            padding: var(--space-sm) var(--space-md);
            text-align: left;
            font-weight: 600;
            color: var(--ink);
            border-bottom: 2px solid var(--stone);
        }}

        .usage-matrix-table td {{
            padding: var(--space-sm) var(--space-md);
            border-bottom: 1px solid var(--sand);
        }}

        .usage-matrix-table tbody tr:hover {{
            background: var(--sand);
        }}

        .usage-matrix-table tbody tr.unused-row {{
            background: rgba(155, 44, 44, 0.05);
        }}

        .usage-matrix-table tbody tr.unused-row:hover {{
            background: rgba(155, 44, 44, 0.1);
        }}

        .status-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: var(--radius-sm);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-badge--used {{
            background: rgba(96, 108, 56, 0.15);
            color: var(--success);
        }}

        .status-badge--unused {{
            background: rgba(155, 44, 44, 0.15);
            color: var(--danger);
        }}

        .alert__content {{
            flex: 1;
        }}

        .alert__title {{
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-sm);
        }}

        .alert__list {{
            list-style: disc;
            list-style-position: inside;
            font-size: 14px;
            color: var(--charcoal);
        }}

        .alert__list li {{
            margin-bottom: var(--space-xs);
        }}

        /* === ENHANCED FEATURE CARD === */
        .feature-card__header {{
            display: flex;
            gap: var(--space-lg);
            align-items: flex-start;
            margin-bottom: var(--space-xl);
            position: relative;
            z-index: 1;
        }}

        .feature-card__icon {{
            width: 56px;
            height: 56px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .feature-card__icon svg {{
            width: 28px;
            height: 28px;
        }}

        .feature-card__titles {{
            flex: 1;
        }}

        .feature-card__subtitle {{
            font-size: 14px;
            opacity: 0.9;
            line-height: 1.5;
        }}

        .feature-card__body {{
            position: relative;
            z-index: 1;
        }}

        /* === HEALTH STATS === */
        .health-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--space-lg);
        }}

        .health-stat {{
            background: rgba(255, 255, 255, 0.15);
            padding: var(--space-lg);
            border-radius: var(--radius-md);
        }}

        .health-stat__label {{
            font-size: 13px;
            opacity: 0.85;
            margin-bottom: var(--space-xs);
        }}

        .health-stat__value {{
            font-size: 16px;
            font-weight: 600;
        }}

        /* === CARD BODY === */
        .card__body {{
            padding-top: var(--space-md);
        }}

        /* === TAB CONTENT === */
        .tab-content {{
            animation: fadeIn 0.3s ease;
        }}

        .tab-content > * + * {{
            margin-top: var(--space-xl);
        }}

        .tab-content .tab-header {{
            margin-bottom: var(--space-lg);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* === TWO COLUMN GRID === */
        .two-column-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--space-xl);
        }}

        /* === METRICS STACK === */
        .metrics-stack {{
            display: flex;
            flex-direction: column;
            gap: var(--space-md);
        }}

        .metrics-stack .metric-card {{
            margin: 0;
        }}

        /* === BADGE VARIANTS === */
        .badge-terracotta {{ background: rgba(196, 164, 132, 0.2); color: var(--sienna); }}

        /* === CONTENT SUB-TABS === */
        .subtabs {{
            display: flex;
            gap: var(--space-sm);
            margin-bottom: var(--space-xl);
            padding-bottom: var(--space-md);
            border-bottom: 1px solid var(--clay);
        }}

        .subtab {{
            padding: var(--space-md) var(--space-lg);
            font-size: 14px;
            font-weight: 500;
            color: var(--stone);
            background: transparent;
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .subtab:hover {{
            background: var(--sand);
            color: var(--charcoal);
        }}

        .subtab.active {{
            background: rgba(196, 164, 132, 0.15);
            color: var(--sienna);
            font-weight: 600;
        }}

        .subtab__icon {{
            width: 16px;
            height: 16px;
        }}

        /* === CONTENT PANELS === */
        .panel-grid {{
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: var(--space-xl);
        }}

        .panel {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            overflow: hidden;
            min-width: 0;
        }}

        .panel__header {{
            padding: var(--space-lg);
            border-bottom: 1px solid var(--clay);
            background: var(--sand);
        }}

        .panel__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-sm);
        }}

        .panel__search {{
            width: 100%;
            padding: var(--space-md);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            font-family: inherit;
            font-size: 14px;
            transition: all 0.2s ease;
        }}

        .panel__search:focus {{
            outline: none;
            border-color: var(--terracotta);
            box-shadow: 0 0 0 3px rgba(196, 164, 132, 0.15);
        }}

        .panel__body {{
            padding: var(--space-md);
            max-height: 600px;
            overflow-y: auto;
        }}

        /* === TABLE ITEM === */
        .table-item {{
            padding: var(--space-md);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
            border-left: 3px solid transparent;
            margin-bottom: var(--space-sm);
        }}

        .table-item:hover {{
            background: var(--sand);
        }}

        .table-item.active {{
            background: rgba(196, 164, 132, 0.12);
            border-left-color: var(--terracotta);
        }}

        .table-item__name {{
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-xs);
        }}

        .table-item__meta {{
            font-size: 13px;
            color: var(--stone);
            margin-bottom: var(--space-sm);
        }}

        .table-item__badges {{
            display: flex;
            gap: var(--space-xs);
            flex-wrap: wrap;
        }}

        /* === DETAIL PANEL === */
        .detail-header {{
            padding: var(--space-xl);
            border-bottom: 1px solid var(--clay);
            background: linear-gradient(135deg, var(--white) 0%, var(--sand) 100%);
        }}

        .detail-header__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-sm);
        }}

        .detail-header__badges {{
            display: flex;
            gap: var(--space-sm);
            margin-top: var(--space-md);
        }}

        .detail-stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--space-md);
            padding: var(--space-lg);
            background: var(--sand);
            border-bottom: 1px solid var(--clay);
        }}

        .detail-stat {{
            text-align: center;
        }}

        .detail-stat__value {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 28px;
            font-weight: 700;
            color: var(--ink);
            line-height: 1;
        }}

        .detail-stat__label {{
            font-size: 12px;
            color: var(--stone);
            margin-top: var(--space-xs);
        }}

        .detail-body {{
            padding: var(--space-lg);
        }}

        /* === DETAIL SUB-TABS === */
        .detail-tabs {{
            display: flex;
            gap: var(--space-sm);
            margin-bottom: var(--space-lg);
            flex-wrap: wrap;
        }}

        .detail-tab {{
            padding: var(--space-sm) var(--space-lg);
            font-size: 13px;
            font-weight: 600;
            color: var(--stone);
            background: var(--sand);
            border: none;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .detail-tab:hover {{
            background: var(--clay);
            color: var(--charcoal);
        }}

        .detail-tab.active {{
            background: var(--terracotta);
            color: var(--white);
        }}

        /* === COLUMN CARD === */
        .column-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            padding: var(--space-md);
            transition: all 0.15s ease;
        }}

        .column-card:hover {{
            border-color: var(--terracotta);
        }}

        .column-card__header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-sm);
        }}

        .column-card__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .column-card__badges {{
            display: flex;
            gap: var(--space-xs);
        }}

        .column-card__type {{
            font-size: 12px;
            color: var(--stone);
        }}

        .column-card__source {{
            font-size: 11px;
            color: var(--pebble);
            margin-top: var(--space-xs);
        }}

        /* === MEASURE CARD === */
        .measure-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            padding: var(--space-lg);
            margin-bottom: var(--space-md);
            transition: all 0.2s ease;
        }}

        .measure-card:hover {{
            border-color: var(--terracotta);
            box-shadow: 0 4px 16px rgba(45, 36, 24, 0.08);
        }}

        .measure-card__header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-md);
        }}

        .measure-card__title {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .measure-card__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .measure-card__toggle {{
            background: transparent;
            border: none;
            color: var(--sienna);
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            transition: color 0.2s;
        }}

        .measure-card__toggle:hover {{
            color: var(--terracotta-dark);
        }}

        /* === RELATIONSHIP CARD === */
        .relationship-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            padding: var(--space-md);
            margin-bottom: var(--space-sm);
        }}

        .relationship-card--incoming {{
            border-left: 3px solid var(--sage);
        }}

        .relationship-card--outgoing {{
            border-left: 3px solid var(--ocean);
        }}

        .relationship-card__header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-xs);
        }}

        .relationship-card__table {{
            font-weight: 600;
            color: var(--ink);
        }}

        .relationship-card__detail {{
            font-size: 13px;
            color: var(--stone);
        }}

        .relationship-card__columns {{
            font-size: 13px;
            color: var(--stone);
        }}

        .relationship-card__details {{
            font-size: 13px;
            color: var(--charcoal);
            line-height: 1.6;
        }}

        .relationship-card__badges {{
            display: flex;
            gap: var(--space-sm);
            margin-top: var(--space-sm);
        }}

        .relationship-card--fact-dim {{
            border-left: 3px solid var(--ocean);
            background: rgba(69, 123, 157, 0.05);
        }}

        .relationship-card--dim-dim {{
            border-left: 3px solid var(--coral);
            background: rgba(224, 122, 95, 0.05);
        }}

        .relationship-card--other {{
            border-left: 3px solid var(--stone);
            background: var(--sand);
        }}

        /* === COLUMNS GRID === */
        .columns-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: var(--space-md);
        }}

        /* === MEASURES LIST === */
        .measures-list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-md);
        }}

        .measure-card__info {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            flex-wrap: wrap;
        }}

        /* === RELATIONSHIP SECTIONS === */
        .relationships-section {{
            display: flex;
            flex-direction: column;
            gap: var(--space-xl);
        }}

        .relationship-group {{
            margin-bottom: var(--space-lg);
        }}

        .relationship-group__title {{
            font-size: 15px;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: var(--space-md);
        }}

        .relationship-list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
        }}

        .relationships-view {{
            display: flex;
            flex-direction: column;
            gap: var(--space-xl);
        }}

        .relationship-type-group {{
            margin-bottom: var(--space-lg);
        }}

        .relationship-type-group__title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-md);
            padding-bottom: var(--space-sm);
            border-bottom: 2px solid var(--clay);
        }}

        /* === USAGE STYLES === */
        .usage-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-lg);
        }}

        .usage-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: var(--space-md);
        }}

        .usage-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            overflow: hidden;
        }}

        .usage-card__header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-md);
            background: var(--sand);
            border-bottom: 1px solid var(--clay);
        }}

        .usage-card__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .usage-card__body {{
            padding: var(--space-md);
        }}

        .usage-section {{
            margin-bottom: var(--space-md);
        }}

        .usage-section__title {{
            display: flex;
            align-items: center;
            gap: var(--space-xs);
            font-weight: 600;
            font-size: 13px;
            color: var(--charcoal);
            margin-bottom: var(--space-sm);
        }}

        .usage-items {{
            display: flex;
            flex-direction: column;
            gap: var(--space-xs);
            margin-left: var(--space-lg);
        }}

        .usage-item {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            font-size: 12px;
            padding: var(--space-xs) var(--space-sm);
            background: var(--cream);
            border-radius: var(--radius-sm);
            color: var(--charcoal);
        }}

        .usage-item--measure {{
            background: rgba(69, 123, 157, 0.1);
        }}

        .usage-item--field-param {{
            background: rgba(139, 157, 119, 0.1);
        }}

        .usage-pages {{
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
        }}

        .usage-page {{
            padding: var(--space-sm);
            background: var(--cream);
            border-radius: var(--radius-sm);
        }}

        .usage-page__header {{
            display: flex;
            align-items: center;
            gap: var(--space-xs);
            font-weight: 500;
            font-size: 13px;
            color: var(--charcoal);
            margin-bottom: var(--space-xs);
        }}

        .usage-page__count {{
            font-size: 11px;
            color: var(--stone);
        }}

        .usage-empty {{
            font-size: 12px;
            color: var(--stone);
            font-style: italic;
        }}

        /* === DETAIL CONTENT === */
        .detail-tabs-container {{
            margin-top: var(--space-lg);
            padding: 0 var(--space-lg);
        }}

        .detail-content {{
            padding-top: var(--space-md);
            padding: var(--space-md);
            overflow: auto;
            max-height: 600px;
        }}

        /* === FOLDER/MEASURE BROWSER === */
        .folder-group {{
            margin-bottom: var(--space-sm);
        }}

        .folder-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-sm) var(--space-md);
            background: var(--sand);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .folder-header:hover {{
            background: var(--clay);
        }}

        .folder-header__info {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .folder-header__icon {{
            font-size: 14px;
        }}

        .folder-header__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .folder-header__count {{
            font-size: 12px;
            color: var(--stone);
        }}

        .folder-header__toggle {{
            font-size: 10px;
            color: var(--stone);
            transition: transform 0.2s ease;
        }}

        .folder-content {{
            margin-left: var(--space-lg);
            margin-top: var(--space-xs);
        }}

        .measure-item {{
            padding: var(--space-sm) var(--space-md);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .measure-item:hover {{
            background: var(--clay);
        }}

        .measure-item.active {{
            background: var(--terracotta);
            color: var(--white);
        }}

        .measure-item__name {{
            font-size: 13px;
            font-weight: 500;
        }}

        .measure-item__table {{
            font-size: 11px;
            color: var(--stone);
        }}

        .measure-item.active .measure-item__table {{
            color: rgba(255, 255, 255, 0.8);
        }}

        /* === MEASURE DETAIL === */
        .measure-detail {{
            padding: var(--space-lg);
        }}

        .measure-detail__header {{
            margin-bottom: var(--space-lg);
        }}

        .measure-detail__name {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 24px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-sm);
        }}

        .measure-detail__badges {{
            display: flex;
            gap: var(--space-sm);
            flex-wrap: wrap;
        }}

        /* === PANEL GRID FOR MEASURES === */
        .panel-grid--measures {{
            height: 600px;
        }}

        /* === SEARCH INPUT === */
        .search-input {{
            width: 100%;
            padding: var(--space-sm) var(--space-md);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            margin-bottom: var(--space-md);
            font-size: 14px;
            background: var(--white);
            transition: all 0.2s ease;
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--terracotta);
            box-shadow: 0 0 0 3px rgba(196, 164, 132, 0.2);
        }}

        /* === EMPTY STATE MODIFIERS === */
        .empty-state--centered {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 200px;
        }}

        .empty-state--small {{
            padding: var(--space-md);
            font-size: 13px;
        }}

        /* === BTN LINK === */
        .btn-link {{
            background: transparent;
            border: none;
            color: var(--sienna);
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: color 0.2s;
        }}

        .btn-link:hover {{
            color: var(--terracotta-dark);
        }}

        /* === BADGE MODIFIER === */
        .badge--small {{
            font-size: 10px;
            padding: 2px 6px;
        }}

        /* === PAGE LIST (Report Tab) === */
        .page-list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
        }}

        .page-item {{
            padding: var(--space-md);
            border-left: 3px solid var(--clay);
            background: var(--white);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .page-item:hover {{
            border-left-color: var(--terracotta);
            background: var(--sand);
        }}

        .page-item.active {{
            border-left-color: var(--terracotta);
            background: var(--cream);
        }}

        .page-item__name {{
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-xs);
        }}

        .page-item__count {{
            font-size: 12px;
            color: var(--stone);
        }}

        /* === FILTERS SECTION === */
        .filters-section {{
            background: rgba(69, 123, 157, 0.1);
            padding: var(--space-lg);
            border-radius: var(--radius-md);
            margin-bottom: var(--space-lg);
        }}

        .filters-section__title {{
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-sm);
        }}

        .filters-section__badges {{
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-sm);
        }}

        /* === VISUAL GROUPS === */
        .visual-groups {{
            display: flex;
            flex-direction: column;
            gap: var(--space-lg);
        }}

        .visual-group {{
            margin-bottom: var(--space-md);
        }}

        .visual-group__header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-md);
            background: var(--sand);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .visual-group__header:hover {{
            background: var(--clay);
        }}

        .visual-group__header.collapsed .visual-group__toggle {{
            transform: rotate(-90deg);
        }}

        .visual-group__info {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .visual-group__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .visual-group__count {{
            font-size: 12px;
            color: var(--stone);
        }}

        .visual-group__toggle {{
            font-size: 10px;
            color: var(--stone);
            transition: transform 0.2s ease;
        }}

        .visual-group__items {{
            display: flex;
            flex-direction: column;
            gap: var(--space-md);
            margin-top: var(--space-md);
            padding-left: var(--space-md);
        }}

        /* === VISUAL CARD === */
        .visual-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            padding: var(--space-lg);
            transition: all 0.15s ease;
        }}

        .visual-card:hover {{
            border-color: var(--terracotta);
        }}

        .visual-card__header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-md);
        }}

        .visual-card__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .visual-card__id {{
            font-size: 11px;
            color: var(--pebble);
            font-family: 'IBM Plex Mono', monospace;
        }}

        .visual-card__section {{
            margin-bottom: var(--space-sm);
        }}

        .visual-card__section-title {{
            font-size: 12px;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: var(--space-xs);
        }}

        .visual-card__badges {{
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-xs);
        }}

        /* === DEPENDENCY SUB-TABS === */
        .dependency-tabs {{
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-lg);
            padding-bottom: var(--space-md);
            border-bottom: 1px solid var(--clay);
            margin-bottom: var(--space-xl);
        }}

        .dependency-tab {{
            padding: var(--space-sm) 0;
            border: none;
            background: transparent;
            font-size: 14px;
            font-weight: 500;
            color: var(--stone);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
        }}

        .dependency-tab:hover {{
            color: var(--charcoal);
        }}

        .dependency-tab.active {{
            color: var(--sienna);
            border-bottom-color: var(--terracotta);
        }}

        /* === DEPENDENCY LIST ITEM === */
        .dep-list-item {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-sm) var(--space-md);
            background: var(--sand);
            border-radius: var(--radius-sm);
            font-size: 13px;
            color: var(--charcoal);
        }}

        /* === DEPENDENCY SECTION === */
        .dependency-section {{
            margin-bottom: var(--space-xl);
        }}

        .dependency-section__title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-md);
        }}

        .dependency-list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
        }}

        .dependency-groups {{
            display: flex;
            flex-direction: column;
            gap: var(--space-md);
        }}

        /* === DATA TABLE === */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .data-table th {{
            text-align: left;
            padding: var(--space-sm) var(--space-md);
            background: var(--sand);
            font-size: 12px;
            font-weight: 600;
            color: var(--charcoal);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 2px solid var(--clay);
        }}

        .data-table td {{
            padding: var(--space-sm) var(--space-md);
            font-size: 13px;
            color: var(--charcoal);
            border-bottom: 1px solid var(--cream);
        }}

        .data-table tr:hover td {{
            background: var(--cream);
        }}

        /* === CHAIN CARD === */
        .chain-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            padding: var(--space-lg);
            margin-bottom: var(--space-md);
        }}

        .chain-card:hover {{
            border-color: var(--terracotta);
        }}

        .chain-card__header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-md);
        }}

        .chain-card__title {{
            font-weight: 600;
            color: var(--ink);
        }}

        .chain-card__depth {{
            font-size: 12px;
            color: var(--stone);
        }}

        .chain-card__measures {{
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-xs);
        }}

        /* === TABLE CONTAINER === */
        .table-container {{
            width: 100%;
            overflow-x: auto;
        }}

        .table-container--scrollable {{
            max-height: 600px;
            overflow-y: auto;
        }}

        /* === SCROLLABLE CONTAINER === */
        .scrollable {{
            max-height: 500px;
            overflow-y: auto;
            padding-right: var(--space-sm);
        }}

        .scrollable::-webkit-scrollbar {{
            width: 6px;
        }}

        .scrollable::-webkit-scrollbar-track {{
            background: var(--sand);
            border-radius: 3px;
        }}

        .scrollable::-webkit-scrollbar-thumb {{
            background: var(--clay);
            border-radius: 3px;
        }}

        .scrollable::-webkit-scrollbar-thumb:hover {{
            background: var(--terracotta);
        }}

        /* === EMPTY STATE === */
        .empty-state {{
            text-align: center;
            padding: var(--space-2xl);
            color: var(--stone);
        }}

        .empty-state__icon {{
            font-size: 48px;
            margin-bottom: var(--space-lg);
        }}

        .empty-state__text {{
            font-size: 15px;
        }}

        /* Legacy KPI Card (for compatibility) */
        .kpi-card {{
            background: var(--white);
            border: 1px solid var(--clay);
            padding: var(--space-xl);
            border-radius: var(--radius-md);
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--terracotta);
        }}

        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(45, 36, 24, 0.08);
        }}

        .kpi-card h3 {{
            font-size: 13px;
            font-weight: 600;
            margin: 0 0 var(--space-sm) 0;
            color: var(--stone);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .kpi-card .value {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 36px;
            font-weight: 700;
            color: var(--ink);
            margin: 0;
        }}

        /* === SECTION STYLES === */
        .section {{
            margin-bottom: var(--space-2xl);
        }}

        .section__header {{
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            margin-bottom: var(--space-xl);
        }}

        .section__title-group {{
            display: flex;
            flex-direction: column;
            gap: var(--space-xs);
        }}

        .section__eyebrow {{
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--sienna);
        }}

        .section__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 28px;
            font-weight: 600;
            color: var(--ink);
        }}

        /* === CARDS === */
        .card {{
            background: var(--white);
            border-radius: var(--radius-md);
            border: 1px solid var(--clay);
            padding: var(--space-xl);
            transition: all 0.3s ease;
        }}

        .card:hover {{
            border-color: var(--terracotta);
            box-shadow: 0 8px 32px rgba(196, 164, 132, 0.15);
        }}

        .card__header {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: var(--space-md);
        }}

        .card__title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
        }}

        /* Legacy stat-card (for compatibility) */
        .stat-card {{
            background: var(--white);
            border-radius: var(--radius-md);
            padding: var(--space-xl);
            border: 1px solid var(--clay);
        }}

        /* === TABLES === */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .data-table thead {{
            background: var(--sand);
            position: sticky;
            top: 0;
        }}

        .data-table th {{
            padding: var(--space-md) var(--space-lg);
            text-align: left;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--stone);
            border-bottom: 1px solid var(--clay);
        }}

        .data-table td {{
            padding: var(--space-md) var(--space-lg);
            font-size: 14px;
            color: var(--charcoal);
            border-bottom: 1px solid var(--clay);
        }}

        .data-table tbody tr {{
            transition: background 0.15s ease;
        }}

        .data-table tbody tr:hover {{
            background: var(--sand);
        }}

        /* === BADGES === */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: var(--radius-full);
            font-size: 12px;
            font-weight: 600;
        }}

        .badge-primary {{ background: rgba(196, 164, 132, 0.15); color: var(--sienna); }}
        .badge-success {{ background: rgba(96, 108, 56, 0.15); color: var(--olive); }}
        .badge-danger {{ background: rgba(155, 44, 44, 0.15); color: var(--danger); }}
        .badge-warning {{ background: rgba(188, 108, 37, 0.15); color: var(--rust); }}
        .badge-info {{ background: rgba(69, 123, 157, 0.15); color: var(--ocean); }}
        .badge-gray {{ background: var(--sand); color: var(--stone); }}

        .badge--dimension {{
            background: rgba(139, 157, 119, 0.15);
            color: var(--olive);
        }}

        .badge--fact {{
            background: rgba(69, 123, 157, 0.15);
            color: var(--ocean);
        }}

        /* === BUTTONS === */
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-md) var(--space-xl);
            font-family: inherit;
            font-size: 14px;
            font-weight: 600;
            border-radius: var(--radius-full);
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn--outline {{
            background: transparent;
            border: 2px solid var(--clay);
            color: var(--charcoal);
        }}

        .btn--outline:hover {{
            border-color: var(--terracotta);
            color: var(--sienna);
        }}

        .btn--primary {{
            background: var(--ink);
            border: 2px solid var(--ink);
            color: var(--white);
        }}

        .btn--primary:hover {{
            background: var(--charcoal);
            border-color: var(--charcoal);
        }}

        /* === LIST ITEMS === */
        .list-item {{
            padding: var(--space-md);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .list-item:hover {{
            background: var(--sand);
            transform: translateX(4px);
        }}

        .list-item.selected {{
            background: rgba(196, 164, 132, 0.15);
            border-left: 3px solid var(--terracotta);
        }}

        /* === FOLDER STRUCTURE === */
        .folder-item {{
            margin-bottom: var(--space-md);
        }}

        .folder-header {{
            background: var(--sand);
            padding: var(--space-md) var(--space-lg);
            border-radius: var(--radius-sm);
            font-weight: 600;
            color: var(--charcoal);
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.15s ease;
        }}

        .folder-header:hover {{
            background: var(--clay);
        }}

        .folder-content {{
            margin-left: var(--space-lg);
            margin-top: var(--space-sm);
            padding-left: var(--space-lg);
            border-left: 2px solid var(--clay);
        }}

        /* === LIST GROUP === */
        .list-group-header {{
            background: linear-gradient(90deg, var(--terracotta) 0%, var(--sienna) 100%);
            color: white;
            padding: var(--space-md) var(--space-lg);
            font-weight: 600;
            cursor: pointer;
            border-radius: var(--radius-sm);
            margin-bottom: var(--space-sm);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }}

        .list-group-header:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(196, 164, 132, 0.3);
        }}

        .list-group-header .expand-icon {{
            transition: transform 0.2s ease;
        }}

        .list-group-header.collapsed .expand-icon {{
            transform: rotate(-90deg);
        }}

        .list-group-items {{
            margin-left: var(--space-lg);
            border-left: 2px solid var(--clay);
            padding-left: var(--space-md);
        }}

        /* === CODE BLOCK === */
        .code-block {{
            background: var(--sand);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            padding: var(--space-lg);
            font-family: 'IBM Plex Mono', 'Monaco', monospace;
            font-size: 13px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: var(--charcoal);
        }}

        /* === DAX SYNTAX HIGHLIGHTING === */
        .dax-keyword {{ color: var(--ocean); font-weight: bold; }}
        .dax-function {{ color: var(--sienna); font-weight: 600; }}
        .dax-string {{ color: var(--olive); }}
        .dax-number {{ color: var(--coral); }}
        .dax-comment {{ color: var(--pebble); font-style: italic; }}
        .dax-table {{ color: var(--ocean); }}
        .dax-column {{ color: var(--rust); }}

        .dark-mode .dax-keyword {{ color: #7eb8d6; }}
        .dark-mode .dax-function {{ color: #d4b494; }}
        .dark-mode .dax-string {{ color: #a8c686; }}
        .dark-mode .dax-number {{ color: #e9a07a; }}
        .dark-mode .dax-comment {{ color: #7a7267; }}
        .dark-mode .dax-table {{ color: #7eb8d6; }}
        .dark-mode .dax-column {{ color: #d4a056; }}

        /* === VISUAL ICONS === */
        .visual-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: var(--radius-sm);
            font-size: 16px;
            margin-right: var(--space-sm);
        }}

        .visual-icon.slicer {{ background: rgba(196, 164, 132, 0.15); }}
        .visual-icon.table {{ background: rgba(139, 157, 119, 0.15); }}
        .visual-icon.card {{ background: rgba(188, 108, 37, 0.15); }}
        .visual-icon.chart {{ background: rgba(224, 122, 95, 0.15); }}
        .visual-icon.map {{ background: rgba(69, 123, 157, 0.15); }}
        .visual-icon.matrix {{ background: rgba(156, 102, 68, 0.15); }}

        /* === GRAPH CONTAINER === */
        #graph-container {{
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            background: var(--white);
            min-height: 600px;
            position: relative;
            overflow: hidden;
        }}

        #dependency-tree-container {{
            border: 1px solid var(--clay);
            border-radius: var(--radius-md);
            background: var(--white);
            max-height: 600px;
            overflow-y: auto;
        }}

        .graph-controls {{
            display: flex;
            gap: var(--space-sm);
            margin-bottom: var(--space-lg);
            flex-wrap: wrap;
        }}

        .graph-control-btn {{
            padding: var(--space-sm) var(--space-lg);
            border-radius: var(--radius-sm);
            border: 2px solid var(--clay);
            background: var(--white);
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.2s;
        }}

        .graph-control-btn:hover {{
            border-color: var(--terracotta);
            background: rgba(196, 164, 132, 0.1);
        }}

        .graph-control-btn.active {{
            border-color: var(--terracotta);
            background: var(--terracotta);
            color: var(--white);
        }}

        /* === TREE NODE === */
        .tree-node {{
            margin-left: 20px;
            border-left: 2px solid var(--clay);
            padding-left: 12px;
        }}

        .tree-node-header {{
            padding: var(--space-sm) var(--space-md);
            margin: var(--space-xs) 0;
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .tree-node-header:hover {{
            background: var(--sand);
        }}

        .tree-node-header.expanded {{
            background: rgba(196, 164, 132, 0.15);
            font-weight: 600;
        }}

        .tree-expand-icon {{
            transition: transform 0.2s;
            display: inline-block;
            width: 16px;
            text-align: center;
        }}

        .tree-expand-icon.expanded {{
            transform: rotate(90deg);
        }}

        /* === RELATIONSHIP LINKS === */
        .relationship-link {{
            stroke: var(--pebble);
            stroke-width: 2px;
            fill: none;
        }}

        .relationship-link.active {{
            stroke: var(--sage);
            stroke-width: 3px;
        }}

        .relationship-link.inactive {{
            stroke: var(--coral);
            stroke-width: 2px;
            stroke-dasharray: 5,5;
        }}

        .relationship-link.fact-to-dim {{
            stroke: var(--ocean);
        }}

        .relationship-link.dim-to-dim {{
            stroke: var(--sienna);
        }}

        .graph-node {{
            cursor: pointer;
            transition: all 0.2s;
        }}

        .graph-node:hover circle {{
            stroke-width: 3px;
        }}

        .graph-node.fact-table circle {{
            fill: var(--ocean);
        }}

        .graph-node.dim-table circle {{
            fill: var(--sage);
        }}

        .graph-node.other-table circle {{
            fill: var(--pebble);
        }}

        .graph-legend {{
            display: flex;
            gap: var(--space-lg);
            margin-bottom: var(--space-lg);
            flex-wrap: wrap;
            font-size: 14px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: var(--radius-sm);
            border: 2px solid var(--ink);
        }}

        .dark-mode #graph-container,
        .dark-mode #dependency-tree-container {{
            background: var(--white);
            border-color: var(--clay);
            min-height: 600px;
        }}

        /* Vue.js cloak - hide uncompiled templates */
        [v-cloak] {{
            display: none !important;
        }}

        /* Command Palette */
        .command-palette {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(45, 36, 24, 0.5);
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 10vh;
            z-index: 1000;
        }}

        .command-palette-content {{
            background: var(--white);
            border-radius: var(--radius-lg);
            box-shadow: 0 20px 50px rgba(45, 36, 24, 0.2);
            width: 90%;
            max-width: 600px;
            max-height: 70vh;
            overflow: hidden;
            border: 1px solid var(--clay);
        }}

        .dark-mode .command-palette-content {{
            background: var(--white);
        }}

        /* Highlight flash animation */
        @keyframes highlight-flash {{
            0%, 100% {{ background-color: transparent; }}
            50% {{ background-color: rgba(196, 164, 132, 0.3); }}
        }}

        .highlight-flash {{
            animation: highlight-flash 2s ease-in-out;
        }}

        /* === SCROLLABLE === */
        .scrollable {{
            max-height: calc(100vh - 200px);
            overflow-y: auto;
        }}

        /* === ANIMATIONS === */
        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(24px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .animate-slide {{
            animation: slideUp 0.6s ease forwards;
        }}

        .animate-slide:nth-child(1) {{ animation-delay: 0ms; }}
        .animate-slide:nth-child(2) {{ animation-delay: 100ms; }}
        .animate-slide:nth-child(3) {{ animation-delay: 200ms; }}
        .animate-slide:nth-child(4) {{ animation-delay: 300ms; }}

        /* === ADDITIONAL BADGE VARIANTS === */
        .badge--ocean {{ background: rgba(69, 123, 157, 0.15); color: var(--ocean); }}
        .badge--sage {{ background: rgba(139, 157, 119, 0.15); color: var(--sage); }}
        .badge--terracotta {{ background: rgba(196, 164, 132, 0.2); color: var(--sienna); }}
        .badge--purple {{ background: rgba(147, 112, 219, 0.15); color: #7c3aed; }}
        .badge--neutral {{ background: var(--sand); color: var(--stone); }}

        /* === STATUS BADGES === */
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: var(--radius-full);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .status-badge--success {{
            background: rgba(96, 108, 56, 0.15);
            color: var(--olive);
        }}

        .status-badge--warning {{
            background: rgba(188, 108, 37, 0.15);
            color: var(--rust);
        }}

        .status-badge--error {{
            background: rgba(155, 44, 44, 0.15);
            color: var(--danger);
        }}

        /* === USAGE SCORE BADGE === */
        .usage-score-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: var(--radius-full);
            font-size: 12px;
            font-weight: 700;
        }}

        /* === CELL MODIFIERS === */
        .cell--bold {{
            font-weight: 600;
            color: var(--ink);
        }}

        .cell--mono {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 12px;
            color: var(--stone);
        }}

        .cell--center {{
            text-align: center;
        }}

        /* === METRICS GRID VARIANTS === */
        .metrics-grid--3 {{
            grid-template-columns: repeat(3, 1fr);
        }}

        .metrics-grid--2 {{
            grid-template-columns: repeat(2, 1fr);
        }}

        /* === PERSPECTIVE STYLES === */
        .perspective-list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-lg);
        }}

        .perspective-item {{
            background: var(--sand);
            border-radius: var(--radius-md);
            padding: var(--space-lg);
            transition: all 0.2s ease;
        }}

        .perspective-item:hover {{
            background: var(--clay);
        }}

        .perspective-item__header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-md);
        }}

        .perspective-item__name {{
            font-size: 16px;
            font-weight: 600;
            color: var(--ink);
        }}

        .perspective-item__stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: var(--space-md);
        }}

        .perspective-stat {{
            text-align: center;
            padding: var(--space-md);
            border-radius: var(--radius-sm);
            background: var(--white);
        }}

        .perspective-stat--ocean {{ background: rgba(69, 123, 157, 0.1); }}
        .perspective-stat--sage {{ background: rgba(139, 157, 119, 0.1); }}
        .perspective-stat--purple {{ background: rgba(147, 112, 219, 0.1); }}
        .perspective-stat--neutral {{ background: var(--sand); }}

        .perspective-stat__label {{
            display: block;
            font-size: 12px;
            color: var(--stone);
            margin-bottom: var(--space-xs);
        }}

        .perspective-stat__value {{
            display: block;
            font-family: 'Fraunces', Georgia, serif;
            font-size: 24px;
            font-weight: 700;
            color: var(--ink);
        }}

        .perspective-stat--ocean .perspective-stat__value {{ color: var(--ocean); }}
        .perspective-stat--sage .perspective-stat__value {{ color: var(--olive); }}
        .perspective-stat--purple .perspective-stat__value {{ color: #7c3aed; }}

        /* === COMMAND PALETTE STYLES === */
        .command-palette__content {{
            background: var(--white);
            border-radius: var(--radius-lg);
            box-shadow: 0 25px 50px -12px rgba(45, 36, 24, 0.25);
            overflow: hidden;
            max-width: 600px;
            width: 100%;
        }}

        .command-palette__input-wrapper {{
            padding: var(--space-lg);
            border-bottom: 1px solid var(--clay);
        }}

        .command-palette__input {{
            width: 100%;
            padding: var(--space-md);
            border: none;
            background: transparent;
            font-family: inherit;
            font-size: 16px;
            color: var(--ink);
        }}

        .command-palette__input:focus {{
            outline: none;
        }}

        .command-palette__input::placeholder {{
            color: var(--pebble);
        }}

        .command-palette__results {{
            max-height: 400px;
            overflow-y: auto;
            padding: var(--space-sm);
        }}

        .command-palette__item {{
            padding: var(--space-md) var(--space-lg);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: background 0.15s ease;
        }}

        .command-palette__item:hover {{
            background: var(--sand);
        }}

        .command-palette__item-name {{
            font-weight: 600;
            color: var(--ink);
            margin-bottom: var(--space-xs);
        }}

        .command-palette__item-desc {{
            font-size: 13px;
            color: var(--stone);
        }}

        /* === PANEL LAYOUT === */
        .panel-left {{
            min-width: 0;
        }}

        .panel-right {{
            min-width: 0;
        }}

        /* === CHAIN MEASURE ITEM === */
        .chain-measure-item {{
            padding: var(--space-md);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
            border-left: 3px solid transparent;
            margin-bottom: var(--space-sm);
            background: var(--white);
        }}

        .chain-measure-item:hover {{
            background: var(--sand);
            border-left-color: var(--clay);
        }}

        .chain-measure-item.active {{
            background: rgba(196, 164, 132, 0.15);
            border-left-color: var(--terracotta);
            box-shadow: 0 2px 8px rgba(196, 164, 132, 0.2);
        }}

        .chain-measure-item__name {{
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 2px;
        }}

        .chain-measure-item__table {{
            font-size: 12px;
            color: var(--stone);
            margin-bottom: var(--space-sm);
        }}

        .chain-measure-item__badges {{
            display: flex;
            flex-wrap: wrap;
            gap: var(--space-xs);
        }}

        /* === VISUAL SELECT ITEM === */
        .visual-select-item {{
            padding: var(--space-md);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s ease;
            border-left: 3px solid transparent;
            margin-bottom: var(--space-sm);
            background: var(--white);
            border: 1px solid var(--clay);
        }}

        .visual-select-item:hover {{
            background: var(--sand);
            border-left-color: var(--terracotta);
        }}

        .visual-select-item.active {{
            background: rgba(196, 164, 132, 0.15);
            border-left-color: var(--terracotta);
            border-color: var(--terracotta);
            box-shadow: 0 2px 8px rgba(196, 164, 132, 0.2);
        }}

        .visual-select-item__name {{
            font-weight: 600;
            color: var(--ink);
            margin-top: var(--space-sm);
            margin-bottom: 2px;
        }}

        .visual-select-item__meta {{
            font-size: 12px;
            color: var(--stone);
        }}

        /* === CHAIN SELECTED MEASURE === */
        .chain-selected-measure {{
            text-align: center;
            padding: var(--space-lg);
            background: linear-gradient(135deg, rgba(196, 164, 132, 0.15) 0%, rgba(156, 102, 68, 0.1) 100%);
            border-radius: var(--radius-md);
            margin-bottom: var(--space-xl);
            border: 2px solid var(--terracotta);
        }}

        .chain-selected-measure__label {{
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--sienna);
            margin-bottom: var(--space-sm);
        }}

        .chain-selected-measure__name {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 14px;
            font-weight: 600;
            color: var(--ink);
            word-break: break-all;
        }}

        /* === CHAIN SECTIONS === */
        .chain-sections {{
            display: flex;
            flex-direction: column;
            gap: var(--space-lg);
        }}

        .chain-section {{
            background: var(--sand);
            border-radius: var(--radius-sm);
            padding: var(--space-lg);
        }}

        .chain-section__header {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            margin-bottom: var(--space-md);
            padding-bottom: var(--space-sm);
            border-bottom: 1px solid var(--clay);
        }}

        .chain-section__header--upward {{
            color: var(--ocean);
        }}

        .chain-section__header--downward {{
            color: var(--olive);
        }}

        .chain-section__header--muted {{
            color: var(--stone);
        }}

        .chain-section__title {{
            font-weight: 600;
            font-size: 13px;
        }}

        .chain-section__count {{
            font-size: 12px;
            color: var(--stone);
        }}

        /* === CHAIN TREE === */
        .chain-tree {{
            padding-left: var(--space-md);
            border-left: 2px solid var(--clay);
        }}

        .chain-tree--nested {{
            margin-left: var(--space-lg);
            margin-top: var(--space-sm);
        }}

        .chain-tree--upward {{
            border-left-color: var(--ocean);
        }}

        .chain-node {{
            margin-bottom: var(--space-sm);
        }}

        .chain-node__item {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            padding: var(--space-sm) var(--space-md);
            background: var(--white);
            border-radius: var(--radius-sm);
            transition: background 0.15s ease;
        }}

        .chain-node__item:hover {{
            background: var(--clay);
        }}

        .chain-node__item--level1 {{
            border-left: 3px solid var(--ocean);
        }}

        .chain-node__item--level2 {{
            border-left: 3px solid rgba(69, 123, 157, 0.6);
        }}

        .chain-node__item--level3 {{
            border-left: 3px solid rgba(69, 123, 157, 0.3);
        }}

        .chain-node__arrow {{
            color: var(--stone);
            font-size: 12px;
        }}

        .chain-node__name {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 13px;
            color: var(--ink);
        }}

        .chain-node__more {{
            font-size: 12px;
            color: var(--stone);
            font-style: italic;
            padding-left: var(--space-xl);
            margin-top: var(--space-xs);
        }}

        /* === CHAIN DIVIDER === */
        .chain-divider {{
            height: 1px;
            background: var(--clay);
            margin: var(--space-md) 0;
        }}

        /* === CHAIN DEPS GRID === */
        .chain-deps-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: var(--space-sm);
        }}

        .chain-dep-item {{
            padding: var(--space-sm) var(--space-md);
            background: var(--white);
            border-radius: var(--radius-sm);
            border-left: 3px solid var(--olive);
            font-family: 'IBM Plex Mono', monospace;
            font-size: 13px;
            color: var(--ink);
        }}

        /* === CHAIN BASE MEASURE === */
        .chain-base-measure {{
            text-align: center;
            padding: var(--space-lg);
            background: rgba(96, 108, 56, 0.1);
            border-radius: var(--radius-sm);
            border: 1px dashed var(--olive);
        }}

        .chain-base-measure__icon {{
            font-size: 14px;
            font-weight: 600;
            color: var(--olive);
            margin-bottom: var(--space-xs);
        }}

        .chain-base-measure__text {{
            font-size: 13px;
            color: var(--stone);
        }}

        .chain-empty {{
            padding: var(--space-md);
            text-align: center;
            color: var(--stone);
            font-style: italic;
        }}

        /* === VISUAL TRACE === */
        .visual-trace-header {{
            padding: var(--space-lg);
            background: linear-gradient(135deg, var(--sand) 0%, var(--clay) 100%);
            border-radius: var(--radius-md);
            margin-bottom: var(--space-xl);
        }}

        .visual-trace-header__name {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--ink);
            display: block;
            margin-top: var(--space-sm);
        }}

        .visual-trace-header__page {{
            font-size: 13px;
            color: var(--stone);
            margin-top: var(--space-xs);
        }}

        .trace-sections {{
            display: flex;
            flex-direction: column;
            gap: var(--space-lg);
        }}

        .trace-section {{
            background: var(--sand);
            border-radius: var(--radius-sm);
            padding: var(--space-lg);
        }}

        .trace-section__header {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            margin-bottom: var(--space-md);
            padding-bottom: var(--space-sm);
            border-bottom: 1px solid var(--clay);
        }}

        .trace-section__header--visual {{
            color: var(--sienna);
        }}

        .trace-section__title {{
            font-weight: 600;
            font-size: 13px;
        }}

        .trace-section__count {{
            font-size: 12px;
            color: var(--stone);
        }}

        .trace-tree {{
            display: flex;
            flex-direction: column;
            gap: var(--space-md);
        }}

        .trace-measure {{
            padding: var(--space-md);
            background: var(--white);
            border-radius: var(--radius-sm);
            border-left: 3px solid var(--terracotta);
        }}

        .trace-measure__name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .trace-measure__table {{
            font-size: 12px;
            color: var(--stone);
        }}

        .trace-deps {{
            margin-top: var(--space-md);
            padding-top: var(--space-md);
            border-top: 1px dashed var(--clay);
        }}

        .trace-deps__header {{
            font-size: 12px;
            font-weight: 600;
            color: var(--stone);
            margin-bottom: var(--space-sm);
        }}

        .trace-deps__list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
            padding-left: var(--space-md);
        }}

        .trace-dep {{
            padding: var(--space-sm);
            background: var(--sand);
            border-radius: var(--radius-sm);
            border-left: 2px solid var(--ocean);
        }}

        .trace-dep__name {{
            font-size: 13px;
            font-weight: 500;
            color: var(--ink);
        }}

        .trace-dep__table {{
            font-size: 11px;
            color: var(--stone);
        }}

        .trace-base-deps {{
            margin-top: var(--space-sm);
            padding-left: var(--space-md);
        }}

        .trace-base-measure {{
            padding: var(--space-xs) var(--space-sm);
            background: rgba(96, 108, 56, 0.1);
            border-radius: var(--radius-sm);
            font-size: 12px;
            color: var(--olive);
            margin-top: var(--space-xs);
        }}

        .trace-summary {{
            margin-top: var(--space-xl);
            padding: var(--space-lg);
            background: var(--sand);
            border-radius: var(--radius-sm);
        }}

        /* === FORM STYLES === */
        .form-group {{
            margin-bottom: var(--space-lg);
        }}

        .form-label {{
            display: block;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--stone);
            margin-bottom: var(--space-sm);
        }}

        .form-select {{
            width: 100%;
            padding: var(--space-md);
            border: 1px solid var(--clay);
            border-radius: var(--radius-sm);
            font-family: inherit;
            font-size: 14px;
            background: var(--white);
            color: var(--ink);
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .form-select:focus {{
            outline: none;
            border-color: var(--terracotta);
            box-shadow: 0 0 0 3px rgba(196, 164, 132, 0.15);
        }}

        /* === DISTRIBUTION LIST (for Data Quality) === */
        .distribution-list {{
            display: flex;
            flex-direction: column;
            gap: var(--space-sm);
        }}

        .distribution-item {{
            display: flex;
            align-items: center;
            gap: var(--space-md);
            padding: var(--space-sm) var(--space-md);
            background: var(--white);
            border-radius: var(--radius-sm);
        }}

        .distribution-item__type {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 13px;
            font-weight: 600;
            color: var(--ink);
            min-width: 120px;
        }}

        .distribution-item__bar {{
            flex: 1;
            height: 8px;
            background: var(--clay);
            border-radius: var(--radius-full);
            overflow: hidden;
        }}

        .distribution-item__fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--terracotta) 0%, var(--sienna) 100%);
            border-radius: var(--radius-full);
            transition: width 0.3s ease;
        }}

        .distribution-item__count {{
            font-size: 13px;
            font-weight: 600;
            color: var(--charcoal);
            min-width: 50px;
            text-align: right;
        }}

        .distribution-item__percent {{
            font-size: 12px;
            color: var(--stone);
            min-width: 45px;
            text-align: right;
        }}

        /* === GROUP HEADER (Code Quality collapsible groups) === */
        .group-header {{
            cursor: pointer;
            background: var(--sand);
        }}

        .group-header:hover {{
            background: var(--clay);
        }}

        .group-header td {{
            padding: var(--space-md) !important;
        }}

        .group-header__content {{
            display: flex;
            align-items: center;
            gap: var(--space-sm);
        }}

        .group-header__icon {{
            font-size: 12px;
            color: var(--charcoal);
            width: 16px;
        }}

        .group-header__title {{
            font-weight: 600;
            color: var(--ink);
            text-transform: capitalize;
        }}

        .group-header__count {{
            font-size: 13px;
            color: var(--stone);
            margin-left: auto;
        }}

        /* === CELL MODIFIERS === */
        .cell--bold {{
            font-weight: 600;
            color: var(--ink);
        }}

        .cell--mono {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 13px;
        }}

        .cell--center {{
            text-align: center;
        }}

        .cell-primary {{
            font-weight: 600;
            color: var(--charcoal);
        }}

        .cell-link {{
            color: var(--terracotta-dark);
            text-decoration: none;
            cursor: pointer;
            background: none;
            border: none;
            padding: 0;
            font-size: inherit;
            font-family: inherit;
        }}

        .cell-link:hover {{
            color: var(--sienna);
            text-decoration: underline;
        }}

        /* === SEVERITY & COMPLEXITY BADGES === */
        .severity-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: var(--radius-full);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .severity-badge--warning {{
            background: rgba(224, 122, 95, 0.15);
            color: var(--coral);
        }}

        .severity-badge--info {{
            background: rgba(69, 123, 157, 0.15);
            color: var(--ocean);
        }}

        .severity-badge--error {{
            background: rgba(188, 108, 37, 0.15);
            color: var(--rust);
        }}

        .complexity-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: var(--radius-full);
            font-size: 12px;
            font-weight: 600;
        }}

        .complexity-badge--low {{
            background: rgba(139, 157, 119, 0.2);
            color: var(--sage);
        }}

        .complexity-badge--medium {{
            background: rgba(196, 164, 132, 0.2);
            color: var(--terracotta-dark);
        }}

        .complexity-badge--high {{
            background: rgba(224, 122, 95, 0.2);
            color: var(--coral);
        }}

        .complexity-badge--very-high {{
            background: rgba(188, 108, 37, 0.2);
            color: var(--rust);
        }}

        /* === USAGE SCORE BADGE === */
        .usage-score-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: var(--radius-full);
            font-size: 12px;
            font-weight: 600;
        }}

        .usage-score-badge--none {{
            background: var(--clay);
            color: var(--stone);
        }}

        .usage-score-badge--low {{
            background: rgba(139, 157, 119, 0.2);
            color: var(--sage);
        }}

        .usage-score-badge--medium {{
            background: rgba(69, 123, 157, 0.2);
            color: var(--ocean);
        }}

        .usage-score-badge--high {{
            background: rgba(196, 164, 132, 0.3);
            color: var(--sienna);
        }}

        .card__badge {{
            background: var(--clay);
            color: var(--stone);
            padding: 4px 12px;
            border-radius: var(--radius-full);
            font-size: 12px;
            font-weight: 500;
        }}

        .data-table--hover tbody tr:hover {{
            background: rgba(196, 164, 132, 0.08);
        }}

        .data-row {{
            transition: background 0.15s ease;
        }}

        /* === EMPTY STATE === */
        .empty-state {{
            text-align: center;
            padding: var(--space-2xl);
            color: var(--stone);
        }}

        .empty-state--compact {{
            padding: var(--space-lg);
        }}

        .empty-state__icon {{
            font-size: 48px;
            margin-bottom: var(--space-md);
        }}

        .empty-state__title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: var(--space-sm);
        }}

        .empty-state__text {{
            font-size: 14px;
            color: var(--stone);
        }}

        /* === FILTER ROW === */
        .filter-row {{
            display: flex;
            gap: var(--space-md);
            align-items: center;
        }}

        .search-input--full {{
            flex: 1;
        }}

        /* === RESPONSIVE === */
        @media (max-width: 1200px) {{
            .hero {{
                grid-template-columns: 1fr;
            }}

            .metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        @media (max-width: 768px) {{
            :root {{
                --sidebar-width: 0px;
            }}

            .sidebar {{
                transform: translateX(-100%);
            }}

            .sidebar.open {{
                transform: translateX(0);
            }}

            .main-wrapper {{
                margin-left: 0;
            }}

            .hero__title {{
                font-size: 28px;
            }}

            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
"""

    def _get_body_content(self) -> str:
        """Get HTML body content with Vue 3 template."""
        return f"""<div id="app" v-cloak :class="{{ 'dark-mode': darkMode }}">
        <div class="app-layout">
            <!-- Sidebar Navigation -->
            <aside class="sidebar">
                <div class="sidebar__header">
                    <div class="sidebar__brand">
                        <div class="sidebar__logo">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                                <line x1="12" y1="22.08" x2="12" y2="12"/>
                            </svg>
                        </div>
                        <div>
                            <h1 class="sidebar__title">{{{{ repositoryName }}}}</h1>
                            <p class="sidebar__subtitle">PBIP Analysis</p>
                        </div>
                    </div>
                </div>

                <nav class="sidebar__nav">
                    <div class="nav-section">
                        <div class="nav-section__title">Overview</div>
                        <button
                            @click="activeTab = 'summary'"
                            :class="['nav-item', {{ active: activeTab === 'summary' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="7" height="7"/>
                                <rect x="14" y="3" width="7" height="7"/>
                                <rect x="14" y="14" width="7" height="7"/>
                                <rect x="3" y="14" width="7" height="7"/>
                            </svg>
                            <span class="nav-item__text">Summary</span>
                        </button>
                    </div>

                    <div class="nav-section">
                        <div class="nav-section__title">Model</div>
                        <button
                            @click="activeTab = 'model'"
                            :class="['nav-item', {{ active: activeTab === 'model' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                            </svg>
                            <span class="nav-item__text">Model</span>
                            <span class="nav-item__badge">{{{{ modelData.tables?.length || 0 }}}}</span>
                        </button>
                        <div v-show="activeTab === 'model'" class="nav-subitems">
                            <button @click="modelSubTab = 'tables'" :class="['nav-subitem', {{ active: modelSubTab === 'tables' }}]">Tables</button>
                            <button @click="modelSubTab = 'measures'" :class="['nav-subitem', {{ active: modelSubTab === 'measures' }}]">Measures</button>
                            <button @click="modelSubTab = 'relationships'" :class="['nav-subitem', {{ active: modelSubTab === 'relationships' }}]">Relationships</button>
                        </div>

                        <button
                            v-if="reportData"
                            @click="activeTab = 'report'"
                            :class="['nav-item', {{ active: activeTab === 'report' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14 2 14 8 20 8"/>
                            </svg>
                            <span class="nav-item__text">Report</span>
                            <span class="nav-item__badge">{{{{ reportData.pages?.length || 0 }}}}</span>
                        </button>
                    </div>

                    <div class="nav-section">
                        <div class="nav-section__title">Analysis</div>
                        <button
                            @click="activeTab = 'dependencies'"
                            :class="['nav-item', {{ active: activeTab === 'dependencies' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="18" cy="5" r="3"/>
                                <circle cx="6" cy="12" r="3"/>
                                <circle cx="18" cy="19" r="3"/>
                                <path d="m8.59 13.51 6.83 3.98M15.41 6.51l-6.82 3.98"/>
                            </svg>
                            <span class="nav-item__text">Dependencies</span>
                        </button>
                        <div v-show="activeTab === 'dependencies'" class="nav-subitems">
                            <button @click="dependencySubTab = 'measures'" :class="['nav-subitem', {{ active: dependencySubTab === 'measures' }}]">Measures</button>
                            <button @click="dependencySubTab = 'columns'" :class="['nav-subitem', {{ active: dependencySubTab === 'columns' }}]">Columns</button>
                            <button @click="dependencySubTab = 'chains'" :class="['nav-subitem', {{ active: dependencySubTab === 'chains' }}]">Chains</button>
                            <button @click="dependencySubTab = 'visuals'" :class="['nav-subitem', {{ active: dependencySubTab === 'visuals' }}]">Visuals</button>
                        </div>

                        <button
                            @click="activeTab = 'usage'"
                            :class="['nav-item', {{ active: activeTab === 'usage' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 3v18h18"/>
                                <path d="M18 17V9"/>
                                <path d="M13 17V5"/>
                                <path d="M8 17v-3"/>
                            </svg>
                            <span class="nav-item__text">Usage</span>
                        </button>
                    </div>

                    <div class="nav-section" v-if="enhancedData?.analyses">
                        <div class="nav-section__title">Quality</div>
                        <button
                            v-if="enhancedData?.analyses?.bpa"
                            @click="activeTab = 'best-practices'"
                            :class="['nav-item', {{ active: activeTab === 'best-practices' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
                                <path d="m9 12 2 2 4-4"/>
                            </svg>
                            <span class="nav-item__text">Best Practices</span>
                            <span class="nav-item__badge">{{{{ bpaViolationsCount }}}}</span>
                        </button>

                        <button
                            v-if="enhancedData?.analyses?.data_types"
                            @click="activeTab = 'data-quality'"
                            :class="['nav-item', {{ active: activeTab === 'data-quality' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"/>
                                <path d="m21 21-4.35-4.35"/>
                            </svg>
                            <span class="nav-item__text">Data Quality</span>
                            <span class="nav-item__badge">{{{{ dataQualityIssuesCount }}}}</span>
                        </button>

                        <button
                            v-if="enhancedData?.analyses?.perspectives?.has_perspectives"
                            @click="activeTab = 'perspectives'"
                            :class="['nav-item', {{ active: activeTab === 'perspectives' }}]"
                        >
                            <svg class="nav-item__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                            </svg>
                            <span class="nav-item__text">Perspectives</span>
                            <span class="nav-item__badge">{{{{ perspectivesCount }}}}</span>
                        </button>
                    </div>
                </nav>

                <div class="sidebar__footer">
                    <button @click="toggleDarkMode" class="btn-icon" title="Toggle Dark Mode">
                        <svg v-if="!darkMode" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                        </svg>
                        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="5"/>
                            <line x1="12" y1="1" x2="12" y2="3"/>
                            <line x1="12" y1="21" x2="12" y2="23"/>
                            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                            <line x1="1" y1="12" x2="3" y2="12"/>
                            <line x1="21" y1="12" x2="23" y2="12"/>
                            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                        </svg>
                    </button>
                    <button @click="showCommandPalette = true" class="btn-icon" title="Command Palette (Ctrl/Cmd+K)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3z"/>
                        </svg>
                    </button>
                </div>
            </aside>

            <!-- Main Content Wrapper -->
            <div class="main-wrapper">
                <!-- Header -->
                <header class="header">
                    <div class="header__inner">
                        <h2 class="header__title">
                            <span v-if="activeTab === 'summary'">Dashboard Overview</span>
                            <span v-else-if="activeTab === 'model'">Model Explorer</span>
                            <span v-else-if="activeTab === 'report'">Report Analysis</span>
                            <span v-else-if="activeTab === 'dependencies'">Dependency Analysis</span>
                            <span v-else-if="activeTab === 'usage'">Usage Analytics</span>
                            <span v-else-if="activeTab === 'best-practices'">Best Practices</span>
                            <span v-else-if="activeTab === 'data-quality'">Data Quality</span>
                            <span v-else-if="activeTab === 'perspectives'">Perspectives</span>
                        </h2>
                        <div class="header__actions">
                            <div class="search-box">
                                <svg class="search-box__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="8"/>
                                    <path d="m21 21-4.35-4.35"/>
                                </svg>
                                <input
                                    v-model="searchQuery"
                                    type="text"
                                    placeholder="Search tables, measures..."
                                    class="search-box__input"
                                    @keydown.slash.prevent="$event.target.focus()"
                                />
                            </div>
                            <button @click="exportToCSV" class="btn-icon" title="Export CSV">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                    <polyline points="7 10 12 15 17 10"/>
                                    <line x1="12" y1="15" x2="12" y2="3"/>
                                </svg>
                            </button>
                            <button @click="exportToJSON" class="btn-icon" title="Export JSON">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                    <polyline points="10 9 9 9 8 9"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </header>

                <!-- Main Content -->
                <main class="main-content">
            <!-- Summary Tab -->
            <div v-show="activeTab === 'summary'" class="tab-content">
                <!-- Hero Section -->
                <div class="hero-section">
                    <div class="hero-section__eyebrow">PBIP Analysis Report</div>
                    <h1 class="hero-section__title">{{{{ repositoryName }}}}</h1>
                    <p class="hero-section__subtitle">Comprehensive model analysis with {{{{ statistics.total_tables }}}} tables and {{{{ statistics.total_measures }}}} measures</p>
                </div>

                <!-- KPI Metrics Grid -->
                <div class="metrics-grid">
                    <div class="metric-card metric-card--terracotta">
                        <div class="metric-card__icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 3h18v18H3zM21 9H3M9 21V9"/>
                            </svg>
                        </div>
                        <div class="metric-card__value">{{{{ statistics.total_tables }}}}</div>
                        <div class="metric-card__label">Tables</div>
                    </div>
                    <div class="metric-card metric-card--sienna">
                        <div class="metric-card__icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
                                <line x1="4" y1="22" x2="4" y2="15"/>
                            </svg>
                        </div>
                        <div class="metric-card__value">{{{{ statistics.total_measures }}}}</div>
                        <div class="metric-card__label">Measures</div>
                    </div>
                    <div class="metric-card metric-card--sage">
                        <div class="metric-card__icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                            </svg>
                        </div>
                        <div class="metric-card__value">{{{{ statistics.total_columns }}}}</div>
                        <div class="metric-card__label">Columns</div>
                    </div>
                    <div class="metric-card metric-card--ocean">
                        <div class="metric-card__icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="18" cy="5" r="3"/>
                                <circle cx="6" cy="12" r="3"/>
                                <circle cx="18" cy="19" r="3"/>
                                <path d="m8.59 13.51 6.83 3.98M15.41 6.51l-6.82 3.98"/>
                            </svg>
                        </div>
                        <div class="metric-card__value">{{{{ statistics.total_relationships }}}}</div>
                        <div class="metric-card__label">Relationships</div>
                    </div>
                </div>

                <!-- Model Information Card -->
                <div class="card">
                    <div class="card__header">
                        <h2 class="card__title">Model Information</h2>
                    </div>
                    <div class="card__body">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-item__label">Repository Path</span>
                                <span class="info-item__value">{{{{ modelData.model_folder || 'Unknown' }}}}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item__label">Model Type</span>
                                <span class="info-item__value">Power BI Semantic Model (PBIP Format)</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item__label">Architecture</span>
                                <span class="badge badge-terracotta">{{{{ modelArchitecture }}}}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-item__label">Expressions</span>
                                <span class="info-item__value">{{{{ modelData.expressions?.length || 0 }}}} M/Power Query expressions</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Key Insights -->
                <div class="card">
                    <div class="card__header">
                        <h2 class="card__title">Key Insights</h2>
                    </div>
                    <div class="card__body">
                        <div class="insights-grid">
                            <div class="insight-card">
                                <div class="insight-card__icon insight-card__icon--terracotta">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                                    </svg>
                                </div>
                                <div class="insight-card__content">
                                    <h3 class="insight-card__title">Table Distribution</h3>
                                    <p class="insight-card__value">{{{{ tableDistribution.fact }}}}% fact · {{{{ tableDistribution.dimension }}}}% dimension</p>
                                </div>
                            </div>
                            <div class="insight-card">
                                <div class="insight-card__icon insight-card__icon--sienna">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                        <line x1="3" y1="9" x2="21" y2="9"/>
                                        <line x1="9" y1="21" x2="9" y2="9"/>
                                    </svg>
                                </div>
                                <div class="insight-card__content">
                                    <h3 class="insight-card__title">Model Density</h3>
                                    <p class="insight-card__value">{{{{ avgColumnsPerTable }}}} cols/table · {{{{ avgMeasuresPerTable }}}} measures/table</p>
                                </div>
                            </div>
                            <div class="insight-card">
                                <div class="insight-card__icon insight-card__icon--sage">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M3 3v18h18"/>
                                        <path d="M18 17V9"/>
                                        <path d="M13 17V5"/>
                                        <path d="M8 17v-3"/>
                                    </svg>
                                </div>
                                <div class="insight-card__content">
                                    <h3 class="insight-card__title">Measure Coverage</h3>
                                    <p class="insight-card__value">{{{{ measureToColumnRatio }}}}:1 ratio · {{{{ measuresUsedPct }}}}% in use</p>
                                </div>
                            </div>
                            <div class="insight-card">
                                <div class="insight-card__icon insight-card__icon--ocean">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/>
                                        <path d="m9 12 2 2 4-4"/>
                                    </svg>
                                </div>
                                <div class="insight-card__content">
                                    <h3 class="insight-card__title">Data Quality</h3>
                                    <p class="insight-card__value">{{{{ columnsUsedPct }}}}% columns referenced · {{{{ statistics.total_relationships }}}} relationships</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Issues & Recommendations -->
                <div v-if="issues.length > 0" class="alert alert--warning">
                    <div class="alert__icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                    </div>
                    <div class="alert__content">
                        <h3 class="alert__title">Attention Required</h3>
                        <ul class="alert__list">
                            <li v-for="issue in issues" :key="issue">{{{{ issue }}}}</li>
                        </ul>
                    </div>
                </div>

                <div v-if="recommendations.length > 0" class="alert alert--success">
                    <div class="alert__icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                            <line x1="9" y1="9" x2="9.01" y2="9"/>
                            <line x1="15" y1="9" x2="15.01" y2="9"/>
                        </svg>
                    </div>
                    <div class="alert__content">
                        <h3 class="alert__title">Recommendations</h3>
                        <ul class="alert__list">
                            <li v-for="rec in recommendations" :key="rec">{{{{ rec }}}}</li>
                        </ul>
                    </div>
                </div>

                <!-- Model Health Summary -->
                <div class="feature-card">
                    <div class="feature-card__header">
                        <div class="feature-card__icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                            </svg>
                        </div>
                        <div class="feature-card__titles">
                            <h2 class="feature-card__title">Model Health Summary</h2>
                            <p class="feature-card__subtitle">{{{{ healthSummary }}}}</p>
                        </div>
                    </div>
                    <div class="feature-card__body">
                        <div class="health-stats">
                            <div class="health-stat">
                                <div class="health-stat__label">Unused Objects</div>
                                <div class="health-stat__value">{{{{ statistics.unused_measures }}}} measures · {{{{ statistics.unused_columns }}}} columns</div>
                            </div>
                            <div class="health-stat">
                                <div class="health-stat__label">Model Complexity</div>
                                <div class="health-stat__value">{{{{ modelComplexity }}}}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Model Tab -->
            <div v-show="activeTab === 'model'" class="tab-content">
                <!-- Model Sub-Tabs -->
                <div class="subtabs">
                    <button
                        @click="modelSubTab = 'tables'"
                        :class="['subtab', modelSubTab === 'tables' ? 'active' : '']"
                    >
                        <svg class="subtab__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 3h18v18H3zM21 9H3M9 21V9"/>
                        </svg>
                        Tables
                    </button>
                    <button
                        @click="modelSubTab = 'measures'"
                        :class="['subtab', modelSubTab === 'measures' ? 'active' : '']"
                    >
                        <svg class="subtab__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
                            <line x1="4" y1="22" x2="4" y2="15"/>
                        </svg>
                        Measures
                    </button>
                    <button
                        @click="modelSubTab = 'relationships'"
                        :class="['subtab', modelSubTab === 'relationships' ? 'active' : '']"
                    >
                        <svg class="subtab__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="18" cy="5" r="3"/>
                            <circle cx="6" cy="12" r="3"/>
                            <circle cx="18" cy="19" r="3"/>
                            <path d="m8.59 13.51 6.83 3.98M15.41 6.51l-6.82 3.98"/>
                        </svg>
                        Relationships
                    </button>
                </div>

                <!-- Tables View -->
                <div v-show="modelSubTab === 'tables'" class="panel-grid">
                    <!-- Left Panel: Tables List -->
                    <div class="panel">
                        <div class="panel__header">
                            <h3 class="panel__title">Tables ({{{{ filteredTables.length }}}})</h3>
                            <input
                                v-model="modelSearchQuery"
                                type="search"
                                placeholder="Search tables..."
                                class="panel__search"
                            />
                        </div>
                        <div class="panel__body">
                            <div
                                v-for="table in filteredTables"
                                :key="table.name"
                                @click="selectedTable = table"
                                :class="['table-item', selectedTable?.name === table.name ? 'active' : '']"
                            >
                                <div class="table-item__name">{{{{ table.name }}}}</div>
                                <div class="table-item__meta">
                                    {{{{ table.columns?.length || 0 }}}} columns · {{{{ table.measures?.length || 0 }}}} measures
                                </div>
                                <div class="table-item__badges">
                                    <span :class="['badge', getTableType(table.name) === 'DIMENSION' ? 'badge-success' : getTableType(table.name) === 'FACT' ? 'badge-info' : 'badge-gray']">
                                        {{{{ getTableType(table.name).toLowerCase() }}}}
                                    </span>
                                    <span :class="['badge', getComplexityBadge(table)]">
                                        {{{{ getTableComplexity(table).replace('Complexity: ', '').toLowerCase() }}}}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Panel: Table Details -->
                    <div class="panel">
                        <div v-if="selectedTable">
                            <div class="detail-header">
                                <h2 class="detail-header__title">{{{{ selectedTable.name }}}}</h2>
                                <div class="detail-header__badges">
                                    <span :class="['badge', selectedTable.name.toLowerCase().startsWith('f ') ? 'badge-info' : selectedTable.name.toLowerCase().startsWith('d ') ? 'badge-success' : 'badge-gray']">
                                        {{{{ getTableType(selectedTable.name) }}}}
                                    </span>
                                    <span :class="['badge', getComplexityBadge(selectedTable)]">
                                        {{{{ getTableComplexity(selectedTable) }}}}
                                    </span>
                                </div>
                            </div>

                            <!-- Table Statistics -->
                            <div class="detail-stats">
                                <div class="detail-stat">
                                    <div class="detail-stat__value">{{{{ selectedTable.columns?.length || 0 }}}}</div>
                                    <div class="detail-stat__label">Columns</div>
                                </div>
                                <div class="detail-stat">
                                    <div class="detail-stat__value">{{{{ selectedTable.measures?.length || 0 }}}}</div>
                                    <div class="detail-stat__label">Measures</div>
                                </div>
                                <div class="detail-stat">
                                    <div class="detail-stat__value">{{{{ getTableRelationshipCount(selectedTable.name) }}}}</div>
                                    <div class="detail-stat__label">Relationships</div>
                                </div>
                                <div class="detail-stat">
                                    <div class="detail-stat__value">{{{{ getTableUsageCount(selectedTable.name) }}}}</div>
                                    <div class="detail-stat__label">Usage</div>
                                </div>
                            </div>

                            <div class="detail-tabs-container">
                                <div class="detail-tabs">
                                    <button
                                        @click="modelDetailTab = 'columns'"
                                        :class="['detail-tab', modelDetailTab === 'columns' ? 'active' : '']"
                                    >
                                        Columns ({{{{ selectedTable.columns?.length || 0 }}}})
                                    </button>
                                    <button
                                        @click="modelDetailTab = 'measures'"
                                        :class="['detail-tab', modelDetailTab === 'measures' ? 'active' : '']"
                                    >
                                        Measures ({{{{ selectedTable.measures?.length || 0 }}}})
                                    </button>
                                    <button
                                        @click="modelDetailTab = 'relationships'"
                                        :class="['detail-tab', modelDetailTab === 'relationships' ? 'active' : '']"
                                    >
                                        Relationships ({{{{ getTableRelationshipCount(selectedTable.name) }}}})
                                    </button>
                                    <button
                                        @click="modelDetailTab = 'usage'"
                                        :class="['detail-tab', modelDetailTab === 'usage' ? 'active' : '']"
                                    >
                                        Usage ({{{{ getTableUsageCount(selectedTable.name) }}}})
                                    </button>
                                </div>

                                <!-- Columns -->
                                <div v-show="modelDetailTab === 'columns'" class="detail-content">
                                    <div v-if="selectedTable.columns?.length > 0" class="columns-grid">
                                        <div v-for="col in selectedTable.columns" :key="col.name" class="column-card">
                                            <div class="column-card__header">
                                                <span class="column-card__name">{{{{ col.name }}}}</span>
                                                <span v-if="isColumnInRelationship(selectedTable.name, col.name)" class="badge badge-info">
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"></path><circle cx="16.5" cy="7.5" r=".5"></circle></svg>
                                                    Key
                                                </span>
                                                <span v-if="col.is_hidden" class="badge badge-warning">
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path><line x1="2" x2="22" y1="2" y2="22"></line></svg>
                                                    Hidden
                                                </span>
                                            </div>
                                            <div class="column-card__type">
                                                <span class="badge badge-gray">{{{{ col.data_type }}}}</span>
                                            </div>
                                            <div class="column-card__source">
                                                Source: {{{{ col.source_column || '-' }}}}
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="empty-state">No columns in this table</div>
                                </div>

                                <!-- Measures -->
                                <div v-show="modelDetailTab === 'measures'" class="detail-content">
                                    <div v-if="selectedTable.measures?.length > 0" class="measures-list">
                                        <div v-for="measure in selectedTable.measures" :key="measure.name" class="measure-card" :data-measure="measure.name">
                                            <div class="measure-card__header">
                                                <div class="measure-card__info">
                                                    <div class="measure-card__name">{{{{ measure.name }}}}</div>
                                                    <span class="badge badge-primary">m Measure</span>
                                                    <span v-if="measure.display_folder" class="badge badge-warning">📁 {{{{ measure.display_folder }}}}</span>
                                                    <span v-if="measure.is_hidden" class="badge badge-gray">Hidden</span>
                                                </div>
                                                <button
                                                    v-if="measure.expression"
                                                    @click="toggleMeasureExpansion(measure.name)"
                                                    class="btn-link"
                                                >
                                                    {{{{ expandedMeasures[measure.name] ? 'Hide DAX' : 'Show DAX' }}}}
                                                </button>
                                            </div>
                                            <div v-if="measure.expression && expandedMeasures[measure.name]" class="code-block" v-html="highlightDAX(measure.expression)"></div>
                                        </div>
                                    </div>
                                    <div v-else class="empty-state">No measures in this table</div>
                                </div>

                                <!-- Relationships -->
                                <div v-show="modelDetailTab === 'relationships'" class="detail-content">
                                    <div v-if="getTableRelationships(selectedTable.name).length > 0" class="relationships-section">
                                        <div class="relationship-group">
                                            <h4 class="relationship-group__title">Incoming ({{{{ getTableRelationships(selectedTable.name).filter(r => r.to_table === selectedTable.name).length }}}})</h4>
                                            <div class="relationship-list">
                                                <div v-for="rel in getTableRelationships(selectedTable.name).filter(r => r.to_table === selectedTable.name)" :key="rel.name" class="relationship-card relationship-card--incoming">
                                                    <div class="relationship-card__header">
                                                        <span class="relationship-card__table">{{{{ rel.from_table }}}}</span>
                                                        <span class="badge badge-success">Active</span>
                                                    </div>
                                                    <div class="relationship-card__columns">
                                                        [{{{{ rel.from_column_name }}}}] → [{{{{ rel.to_column_name }}}}]
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="relationship-group">
                                            <h4 class="relationship-group__title">Outgoing ({{{{ getTableRelationships(selectedTable.name).filter(r => r.from_table === selectedTable.name).length }}}})</h4>
                                            <div class="relationship-list">
                                                <div v-for="rel in getTableRelationships(selectedTable.name).filter(r => r.from_table === selectedTable.name)" :key="rel.name" class="relationship-card relationship-card--outgoing">
                                                    <div class="relationship-card__header">
                                                        <span class="relationship-card__table">{{{{ rel.to_table }}}}</span>
                                                        <span class="badge badge-success">Active</span>
                                                    </div>
                                                    <div class="relationship-card__columns">
                                                        [{{{{ rel.from_column_name }}}}] → [{{{{ rel.to_column_name }}}}]
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="empty-state">No relationships for this table</div>
                                </div>

                                <!-- Usage -->
                                <div v-show="modelDetailTab === 'usage'" class="detail-content">
                                    <h3 class="usage-title">Column Usage by Page</h3>
                                    <div v-if="selectedTable.columns?.length > 0" class="usage-grid">
                                        <div v-for="col in selectedTable.columns" :key="col.name" class="usage-card">
                                            <div class="usage-card__header">
                                                <span class="usage-card__name">{{{{ col.name }}}}</span>
                                                <span class="badge badge-gray">{{{{ getColumnVisualUsage(selectedTable.name, col.name).length }}}} visual(s)</span>
                                            </div>
                                            <div class="usage-card__body">
                                                <!-- Measure Usage -->
                                                <div v-if="getColumnUsedByMeasures(selectedTable.name, col.name).length > 0" class="usage-section">
                                                    <div class="usage-section__title">
                                                        <span>📐</span>
                                                        <span>Used in Measures</span>
                                                    </div>
                                                    <div class="usage-items">
                                                        <div v-for="measure in getColumnUsedByMeasures(selectedTable.name, col.name)" :key="measure" class="usage-item usage-item--measure">
                                                            <span class="badge badge-primary badge--small">Measure</span>
                                                            <span>{{{{ measure }}}}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- Field Parameter Usage -->
                                                <div v-if="getColumnFieldParams(selectedTable.name, col.name).length > 0" class="usage-section">
                                                    <div class="usage-section__title">
                                                        <span>📊</span>
                                                        <span>Used in Field Parameters</span>
                                                    </div>
                                                    <div class="usage-items">
                                                        <div v-for="fp in getColumnFieldParams(selectedTable.name, col.name)" :key="fp" class="usage-item usage-item--field-param">
                                                            <span class="badge badge-success badge--small">Field Param</span>
                                                            <span>{{{{ fp }}}}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- Visual Usage -->
                                                <div v-if="getColumnVisualUsage(selectedTable.name, col.name).length > 0" class="usage-section">
                                                    <div class="usage-section__title">
                                                        <span>📈</span>
                                                        <span>Used in Visuals</span>
                                                    </div>
                                                    <div class="usage-pages">
                                                        <div v-for="(visuals, pageName) in groupColumnUsageByPage(selectedTable.name, col.name)" :key="pageName" class="usage-page">
                                                            <div class="usage-page__header">
                                                                <span>📄</span>
                                                                <span>{{{{ pageName }}}}</span>
                                                                <span class="usage-page__count">({{{{ visuals.length }}}})</span>
                                                            </div>
                                                            <div class="usage-items">
                                                                <div v-for="usage in visuals" :key="usage.visualId" class="usage-item">
                                                                    <span class="badge badge-primary badge--small">{{{{ usage.visualType }}}}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- Filter Pane Usage -->
                                                <div v-if="getColumnFilterUsage(selectedTable.name, col.name).length > 0" class="usage-section">
                                                    <div class="usage-section__title">
                                                        <span>🔽</span>
                                                        <span>Used in Filter Pane</span>
                                                    </div>
                                                    <div class="usage-pages">
                                                        <div v-for="(filters, pageName) in groupFilterUsageByPage(selectedTable.name, col.name)" :key="pageName" class="usage-page">
                                                            <div class="usage-page__header">
                                                                <span v-if="filters[0]?.filterLevel === 'report'">🌐</span>
                                                                <span v-else>📄</span>
                                                                <span>{{{{ pageName }}}}</span>
                                                            </div>
                                                            <div class="usage-items">
                                                                <div v-for="(filter, idx) in filters" :key="idx" class="usage-item">
                                                                    <span class="badge badge--small" :class="filter.filterLevel === 'report' ? 'badge-info' : 'badge-warning'">{{{{ filter.filterLevel === 'report' ? 'Report Filter' : 'Page Filter' }}}}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- No Usage Message -->
                                                <div v-if="getColumnVisualUsage(selectedTable.name, col.name).length === 0 && getColumnFieldParams(selectedTable.name, col.name).length === 0 && getColumnUsedByMeasures(selectedTable.name, col.name).length === 0 && getColumnFilterUsage(selectedTable.name, col.name).length === 0" class="usage-empty">
                                                    Not used in any measures, visuals, field parameters, or filters
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="empty-state">No columns in this table</div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="card">
                            <p class="empty-state">Select a table from the left to view details</p>
                        </div>
                    </div>
                </div>

                <!-- Measures View -->
                <div v-show="modelSubTab === 'measures'">
                    <div class="card">
                        <div class="card__header">
                            <h2 class="card__title">All Measures by Folder</h2>
                        </div>
                        <div class="panel-grid panel-grid--measures">
                            <!-- Left: Folder list -->
                            <div class="panel-left scrollable">
                                <input
                                    v-model="measuresSearchQuery"
                                    type="search"
                                    placeholder="Search measures..."
                                    class="search-input"
                                />
                                <div v-for="(folder, folderName) in measuresByFolder" :key="folderName" class="folder-group">
                                    <div class="folder-header" @click="toggleFolder(folderName)">
                                        <div class="folder-header__info">
                                            <span class="folder-header__icon">📁</span>
                                            <span class="folder-header__name">{{{{ folderName || 'No Folder' }}}}</span>
                                            <span class="folder-header__count">({{{{ folder.length }}}})</span>
                                        </div>
                                        <span class="folder-header__toggle">▼</span>
                                    </div>
                                    <div v-show="!collapsedFolders[folderName]" class="folder-content">
                                        <div
                                            v-for="measure in folder"
                                            :key="measure.key"
                                            @click="selectedMeasure = measure"
                                            :class="['measure-item', selectedMeasure?.key === measure.key ? 'active' : '']"
                                        >
                                            <div class="measure-item__name">{{{{ measure.name }}}}</div>
                                            <div class="measure-item__table">{{{{ measure.table }}}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Right: DAX viewer -->
                            <div class="panel-right scrollable">
                                <div v-if="selectedMeasure" class="measure-detail">
                                    <div class="measure-detail__header">
                                        <h3 class="measure-detail__name">{{{{ selectedMeasure.name }}}}</h3>
                                        <div class="measure-detail__badges">
                                            <span class="badge badge-primary">{{{{ selectedMeasure.table }}}}</span>
                                            <span v-if="selectedMeasure.is_hidden" class="badge badge-warning">Hidden</span>
                                            <span v-if="selectedMeasure.displayFolder" class="badge badge-gray">{{{{ selectedMeasure.displayFolder }}}}</span>
                                        </div>
                                    </div>
                                    <div class="code-block" v-if="selectedMeasure.expression" v-html="highlightDAX(selectedMeasure.expression)"></div>
                                </div>
                                <div v-else class="empty-state empty-state--centered">
                                    <p>Select a measure from the left to view its DAX code</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Relationships View -->
                <div v-show="modelSubTab === 'relationships'">
                    <div class="card">
                        <div class="card__header">
                            <h2 class="card__title">Relationships ({{{{ sortedRelationships.length }}}})</h2>
                        </div>

                        <!-- List View -->
                        <div v-if="sortedRelationships.length > 0" class="relationships-view">
                            <!-- Group by Type -->
                            <div class="relationship-type-group">
                                <h3 class="relationship-type-group__title">Fact-to-Dimension Relationships</h3>
                                <div class="relationship-list">
                                    <div v-for="(rel, idx) in factToDimRelationships" :key="'f2d-' + idx" class="relationship-card relationship-card--fact-dim">
                                        <div class="relationship-card__header">
                                            <div class="relationship-card__table">
                                                {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                            </div>
                                            <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                                {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                            </span>
                                        </div>
                                        <div class="relationship-card__details">
                                            <div><strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]</div>
                                            <div><strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]</div>
                                            <div class="relationship-card__badges">
                                                <span class="badge badge-primary">{{{{ formatCardinality(rel) }}}}</span>
                                                <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="factToDimRelationships.length === 0" class="empty-state empty-state--small">No fact-to-dimension relationships</div>
                            </div>

                            <div class="relationship-type-group">
                                <h3 class="relationship-type-group__title">Dimension-to-Dimension Relationships</h3>
                                <div class="relationship-list">
                                    <div v-for="(rel, idx) in dimToDimRelationships" :key="'d2d-' + idx" class="relationship-card relationship-card--dim-dim">
                                        <div class="relationship-card__header">
                                            <div class="relationship-card__table">
                                                {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                            </div>
                                            <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                                {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                            </span>
                                        </div>
                                        <div class="relationship-card__details">
                                            <div><strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]</div>
                                            <div><strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]</div>
                                            <div class="relationship-card__badges">
                                                <span class="badge badge-primary">{{{{ formatCardinality(rel) }}}}</span>
                                                <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="dimToDimRelationships.length === 0" class="empty-state empty-state--small">No dimension-to-dimension relationships</div>
                            </div>

                            <div class="relationship-type-group">
                                <h3 class="relationship-type-group__title">Other Relationships</h3>
                                <div class="relationship-list">
                                    <div v-for="(rel, idx) in otherRelationships" :key="'other-' + idx" class="relationship-card relationship-card--other">
                                        <div class="relationship-card__header">
                                            <div class="relationship-card__table">
                                                {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                            </div>
                                            <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                                {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                            </span>
                                        </div>
                                        <div class="relationship-card__details">
                                            <div><strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]</div>
                                            <div><strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]</div>
                                            <div class="relationship-card__badges">
                                                <span class="badge badge-primary">{{{{ formatCardinality(rel) }}}}</span>
                                                <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="otherRelationships.length === 0" class="empty-state empty-state--small">No other relationships</div>
                            </div>
                        </div>

                        <div v-else class="empty-state">No relationships found in model</div>
                    </div>
                </div>
            </div>

            <!-- Report Tab -->
            <div v-show="activeTab === 'report'" class="tab-content">
                <div class="panel-grid">
                    <!-- Left Sidebar: Pages List -->
                    <div class="panel-left">
                        <div class="card">
                            <div class="card__header">
                                <h3 class="card__title">Pages ({{{{ reportData.pages?.length || 0 }}}})</h3>
                            </div>
                            <div class="page-list scrollable">
                                <div
                                    v-for="(page, idx) in sortedPages"
                                    :key="idx"
                                    @click="selectedPage = page"
                                    :class="['page-item', selectedPage === page ? 'active' : '']"
                                >
                                    <div class="page-item__name">{{{{ page.display_name || page.name }}}}</div>
                                    <div class="page-item__count">
                                        {{{{ getVisibleVisualCount(page.visuals) }}}} visuals
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Panel: Page Details -->
                    <div class="panel-right">
                        <div v-if="selectedPage" class="card">
                            <div class="card__header">
                                <h2 class="card__title">{{{{ selectedPage.display_name || selectedPage.name }}}}</h2>
                            </div>

                            <!-- Page Filters -->
                            <div v-if="selectedPage.filters?.length > 0" class="filters-section">
                                <h3 class="filters-section__title">Page Filters</h3>
                                <div class="filters-section__badges">
                                    <span v-for="(filter, idx) in selectedPage.filters" :key="idx" class="badge badge-primary">
                                        {{{{ filter.field?.table }}}}[{{{{ filter.field?.name }}}}]
                                    </span>
                                </div>
                            </div>

                            <!-- Visuals Grouped by Type -->
                            <div class="visual-groups">
                                <div v-for="(group, visualType) in visualsByType(selectedPage.visuals)" :key="visualType" class="visual-group">
                                    <div class="visual-group__header" :class="{{collapsed: collapsedVisualGroups[visualType]}}" @click="toggleVisualGroup(visualType)">
                                        <div class="visual-group__info">
                                            <span :class="getVisualIcon(visualType)" v-html="getVisualEmoji(visualType)"></span>
                                            <span class="visual-group__name">{{{{ visualType }}}}</span>
                                            <span class="visual-group__count">({{{{ group.length }}}})</span>
                                        </div>
                                        <span class="visual-group__toggle">▼</span>
                                    </div>
                                    <div v-show="!collapsedVisualGroups[visualType]" class="visual-group__items">
                                        <div v-for="(visual, idx) in group" :key="idx" class="visual-card">
                                            <div class="visual-card__header">
                                                <div class="visual-card__name">
                                                    {{{{ visual.visual_name || visual.title || `${{visualType}} ${{idx + 1}}` }}}}
                                                </div>
                                                <div class="visual-card__id">{{{{ visual.id?.substring(0, 8) }}}}...</div>
                                            </div>

                                            <!-- Measures -->
                                            <div v-if="visual.fields?.measures?.length > 0" class="visual-card__section">
                                                <div class="visual-card__section-title">Measures ({{{{ visual.fields.measures.length }}}})</div>
                                                <div class="visual-card__badges">
                                                    <span v-for="(m, midx) in visual.fields.measures" :key="midx" class="badge badge-success">
                                                        {{{{ m.table }}}}[{{{{ m.measure }}}}]
                                                    </span>
                                                </div>
                                            </div>

                                            <!-- Columns -->
                                            <div v-if="visual.fields?.columns?.length > 0" class="visual-card__section">
                                                <div class="visual-card__section-title">Columns ({{{{ visual.fields.columns.length }}}})</div>
                                                <div class="visual-card__badges">
                                                    <span v-for="(c, cidx) in visual.fields.columns" :key="cidx" class="badge badge-primary">
                                                        {{{{ c.table }}}}[{{{{ c.column }}}}]
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="card">
                            <p class="empty-state">Select a page from the left to view visuals</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dependencies Tab -->
            <div v-show="activeTab === 'dependencies'">
                <!-- Dependency Sub-Tabs -->
                <div class="dependency-tabs">
                    <button
                        @click="dependencySubTab = 'measures'"
                        :class="['dependency-tab', dependencySubTab === 'measures' ? 'active' : '']"
                    >
                        📐 Measures
                    </button>
                    <button
                        @click="dependencySubTab = 'columns'"
                        :class="['dependency-tab', dependencySubTab === 'columns' ? 'active' : '']"
                    >
                        📊 Columns
                    </button>
                    <button
                        @click="dependencySubTab = 'chains'"
                        :class="['dependency-tab', dependencySubTab === 'chains' ? 'active' : '']"
                    >
                        🔗 Measure Chains
                    </button>
                    <button
                        @click="dependencySubTab = 'visuals'"
                        :class="['dependency-tab', dependencySubTab === 'visuals' ? 'active' : '']"
                    >
                        📈 Visuals
                    </button>
                </div>

                <!-- Measures Dependencies -->
                <div v-show="dependencySubTab === 'measures'" class="panel-grid">
                    <!-- Left: Search & Select -->
                    <div class="panel-left">
                        <div class="card">
                            <div class="card__header">
                                <h3 class="card__title">Select Measure</h3>
                            </div>
                            <input
                                v-model="dependencySearchQuery"
                                type="search"
                                placeholder="Search measures..."
                                class="search-input"
                            />

                            <div class="scrollable">
                                <div v-for="(folder, folderName) in measuresForDependencyByFolder" :key="folderName" class="folder-group">
                                    <div class="folder-header" @click="toggleDependencyFolder(folderName)">
                                        <div class="folder-header__info">
                                            <span class="folder-header__icon">📁</span>
                                            <span class="folder-header__name">{{{{ folderName || 'No Folder' }}}}</span>
                                            <span class="folder-header__count">({{{{ folder.length }}}})</span>
                                        </div>
                                        <span class="folder-header__toggle">▼</span>
                                    </div>
                                    <div v-show="!collapsedDependencyFolders[folderName]" class="folder-content">
                                        <div
                                            v-for="measure in folder"
                                            :key="measure.key"
                                            @click="selectDependencyObject(measure.key)"
                                            :class="['measure-item', selectedDependencyKey === measure.key ? 'active' : '']"
                                        >
                                            <div class="measure-item__name">{{{{ measure.name }}}}</div>
                                            <div class="measure-item__table">{{{{ measure.table }}}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Dependency Details -->
                    <div class="panel-right">
                        <div v-if="selectedDependencyKey" class="card">
                            <div class="card__header">
                                <h2 class="card__title">{{{{ selectedDependencyKey }}}}</h2>
                            </div>

                            <!-- Depends On -->
                            <div class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Depends On ({{{{ currentDependencyDetails.dependsOn.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.dependsOn.length > 0" class="dependency-list">
                                    <div v-for="dep in currentDependencyDetails.dependsOn" :key="dep" class="dep-list-item">
                                        <span class="badge badge-primary">Measure</span>
                                        <span>{{{{ dep }}}}</span>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">No dependencies</div>
                            </div>

                            <!-- Used By -->
                            <div class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Used By ({{{{ currentDependencyDetails.usedBy.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.usedBy.length > 0" class="dependency-groups">
                                    <div v-for="(measures, folderName) in groupMeasuresByFolder(currentDependencyDetails.usedBy)" :key="folderName" class="folder-group">
                                        <div class="folder-header" :class="{{collapsed: collapsedUsedByFolders[folderName]}}" @click="toggleUsedByFolder(folderName)">
                                            <div class="folder-header__info">
                                                <span>📁</span>
                                                <span class="folder-header__name">{{{{ folderName }}}}</span>
                                                <span class="folder-header__count">({{{{ measures.length }}}})</span>
                                            </div>
                                            <span class="folder-header__toggle">▼</span>
                                        </div>
                                        <div v-show="!collapsedUsedByFolders[folderName]" class="folder-content">
                                            <div v-for="measure in measures" :key="measure" class="dep-list-item">
                                                <span class="badge badge-success">Measure</span>
                                                <span>{{{{ measure }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">Not used by other measures</div>
                            </div>

                            <!-- Used In Visuals -->
                            <div v-if="reportData" class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Used In Visuals ({{{{ currentDependencyDetails.visualUsage.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.visualUsage.length > 0" class="usage-pages">
                                    <div v-for="(visuals, pageName) in groupVisualUsageByPage(currentDependencyDetails.visualUsage)" :key="pageName" class="usage-page">
                                        <div class="usage-page__header">
                                            <span>📄</span>
                                            <span>{{{{ pageName }}}}</span>
                                            <span class="usage-page__count">({{{{ visuals.length }}}})</span>
                                        </div>
                                        <div class="usage-items">
                                            <div v-for="usage in visuals" :key="usage.visualId" class="usage-item">
                                                <span class="badge badge-warning">{{{{ usage.visualType }}}}</span>
                                                <span>{{{{ usage.visualName || 'Unnamed Visual' }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">Not used in any visuals</div>
                            </div>
                        </div>
                        <div v-else class="card">
                            <p class="empty-state">Select a measure from the left to view dependencies</p>
                        </div>
                    </div>
                </div>

                <!-- Columns Dependencies -->
                <div v-show="dependencySubTab === 'columns'" class="panel-grid">
                    <!-- Left: Search & Select -->
                    <div class="panel-left">
                        <div class="card">
                            <div class="card__header">
                                <h3 class="card__title">Select Column</h3>
                            </div>
                            <input
                                v-model="columnSearchQuery"
                                type="search"
                                placeholder="Search columns..."
                                class="search-input"
                            />

                            <div class="scrollable">
                                <div v-for="(columns, tableName) in filteredColumnsForDependency" :key="tableName" class="folder-group">
                                    <div class="folder-header" @click="toggleDependencyFolder(tableName)">
                                        <div class="folder-header__info">
                                            <span class="folder-header__icon">📊</span>
                                            <span class="folder-header__name">{{{{ tableName }}}}</span>
                                            <span class="folder-header__count">({{{{ columns.length }}}})</span>
                                        </div>
                                        <span class="folder-header__toggle">▼</span>
                                    </div>
                                    <div v-show="!collapsedDependencyFolders[tableName]" class="folder-content">
                                        <div
                                            v-for="column in columns"
                                            :key="column.key"
                                            @click="selectColumnDependency(column.key)"
                                            :class="['measure-item', selectedColumnKey === column.key ? 'active' : '']"
                                        >
                                            <div class="measure-item__name">{{{{ column.name }}}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Column Dependency Details -->
                    <div class="panel-right">
                        <div v-if="selectedColumnKey" class="card">
                            <div class="card__header">
                                <h2 class="card__title">{{{{ selectedColumnKey }}}}</h2>
                            </div>

                            <!-- Used By Field Parameters -->
                            <div class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Used By Field Parameters ({{{{ currentColumnDependencies.usedByFieldParams.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.usedByFieldParams.length > 0" class="dependency-list">
                                    <div v-for="fieldParam in currentColumnDependencies.usedByFieldParams" :key="fieldParam" class="dep-list-item usage-item--field-param">
                                        <span class="badge badge-success">Field Parameter</span>
                                        <span>{{{{ fieldParam }}}}</span>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">Not used by any field parameters</div>
                            </div>

                            <!-- Used By Measures -->
                            <div class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Used By Measures ({{{{ currentColumnDependencies.usedByMeasures.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.usedByMeasures.length > 0" class="dependency-groups">
                                    <div v-for="(measures, folderName) in groupMeasuresByFolder(currentColumnDependencies.usedByMeasures)" :key="folderName" class="usage-page">
                                        <div class="usage-page__header">
                                            <span>📁</span>
                                            <span>{{{{ folderName }}}}</span>
                                            <span class="usage-page__count">({{{{ measures.length }}}})</span>
                                        </div>
                                        <div class="usage-items">
                                            <div v-for="measure in measures" :key="measure" class="dep-list-item">
                                                <span class="badge badge-success">Measure</span>
                                                <span>{{{{ measure }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">Not used by any measures</div>
                            </div>

                            <!-- Used In Visuals -->
                            <div v-if="reportData" class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Used In Visuals ({{{{ currentColumnDependencies.visualUsage.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.visualUsage.length > 0" class="usage-pages">
                                    <div v-for="(visuals, pageName) in groupVisualUsageByPage(currentColumnDependencies.visualUsage)" :key="pageName" class="usage-page">
                                        <div class="usage-page__header">
                                            <span>📄</span>
                                            <span>{{{{ pageName }}}}</span>
                                            <span class="usage-page__count">({{{{ visuals.length }}}})</span>
                                        </div>
                                        <div class="usage-items">
                                            <div v-for="usage in visuals" :key="usage.visualId" class="usage-item">
                                                <span class="badge badge-warning">{{{{ usage.visualType }}}}</span>
                                                <span>{{{{ usage.visualName || 'Unnamed Visual' }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">Not used in any visuals</div>
                            </div>

                            <!-- Used In Filter Pane -->
                            <div v-if="reportData" class="dependency-section">
                                <h3 class="dependency-section__title">
                                    Used In Filter Pane ({{{{ currentColumnDependencies.filterUsage?.length || 0 }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.filterUsage?.length > 0" class="usage-pages">
                                    <div v-for="(filters, pageName) in groupFilterUsageByPageForKey(currentColumnDependencies.filterUsage)" :key="pageName" class="usage-page">
                                        <div class="usage-page__header">
                                            <span v-if="filters[0]?.filterLevel === 'report'">🌐</span>
                                            <span v-else>📄</span>
                                            <span>{{{{ pageName }}}}</span>
                                        </div>
                                        <div class="usage-items">
                                            <div v-for="(filter, idx) in filters" :key="idx" class="usage-item">
                                                <span class="badge" :class="filter.filterLevel === 'report' ? 'badge-info' : 'badge-warning'">{{{{ filter.filterLevel === 'report' ? 'Report Filter' : 'Page Filter' }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-state empty-state--small">Not used in any filters</div>
                            </div>
                        </div>
                        <div v-else class="card">
                            <p class="empty-state">Select a column from the left to view usage</p>
                        </div>
                    </div>
                </div>

                <!-- Measure Chains Tab -->
                <div v-show="dependencySubTab === 'chains'" class="panel-grid">
                    <!-- Left: Measure List with Folders -->
                    <div class="panel-left">
                        <div class="card">
                            <div class="card__header">
                                <h3 class="card__title">Select Measure</h3>
                            </div>
                            <input
                                v-model="chainSearchQuery"
                                type="search"
                                placeholder="Search measures..."
                                class="search-input"
                            />
                            <div class="scrollable">
                                <!-- Folder-based structure -->
                                <div v-for="(measures, folderName) in filteredChainMeasuresByFolder" :key="folderName" class="folder-group">
                                    <div class="folder-header" :class="{{collapsed: collapsedChainFolders[folderName]}}" @click="toggleChainFolder(folderName)">
                                        <div class="folder-header__info">
                                            <span class="folder-header__name">{{{{ folderName }}}}</span>
                                            <span class="folder-header__count">({{{{ measures.length }}}})</span>
                                        </div>
                                        <span class="folder-header__toggle">▼</span>
                                    </div>
                                    <div v-show="!collapsedChainFolders[folderName]" class="folder-content">
                                        <div v-for="measure in measures" :key="measure.fullName"
                                            @click="selectedChainMeasure = measure.fullName"
                                            :class="['chain-measure-item', selectedChainMeasure === measure.fullName ? 'active' : '']"
                                        >
                                            <div class="chain-measure-item__name">{{{{ measure.name }}}}</div>
                                            <div class="chain-measure-item__table">{{{{ measure.table }}}}</div>
                                            <div class="chain-measure-item__badges">
                                                <span v-if="measure.isBase" class="badge badge-success badge--small">Base</span>
                                                <span v-if="measure.chainDepth > 0" class="badge badge-primary badge--small">Chain: {{{{ measure.chainDepth }}}}</span>
                                                <span v-if="measure.usedByCount > 0" class="badge badge-info badge--small">Used by {{{{ measure.usedByCount }}}}</span>
                                                <span v-if="measure.usedInVisuals" class="badge badge-warning badge--small">{{{{ measure.visualCount }}}} visual(s)</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Chain Visualization -->
                    <div class="panel-right">
                        <div v-if="selectedChainMeasure" class="card">
                            <div class="card__header">
                                <h3 class="card__title">Complete Measure Chain</h3>
                            </div>
                            <div class="card__body">
                                <!-- Selected Measure - Center -->
                                <div class="chain-selected-measure">
                                    <div class="chain-selected-measure__label">SELECTED MEASURE</div>
                                    <div class="chain-selected-measure__name">{{{{ selectedChainMeasure }}}}</div>
                                </div>

                                <div class="chain-sections">
                                    <!-- UPWARD: Used By (What uses this measure) - HIERARCHICAL -->
                                    <div v-if="currentChain.usedByChain && currentChain.usedByChain.length > 0" class="chain-section">
                                        <div class="chain-section__header chain-section__header--upward">
                                            <span class="chain-section__title">⬆️ USED BY CHAIN</span>
                                            <span class="chain-section__count">({{{{ currentChain.usedByCount }}}} total measure(s) in chain)</span>
                                        </div>

                                        <!-- Recursive Used By Tree -->
                                        <div class="chain-tree chain-tree--upward">
                                            <div v-for="(item, idx) in currentChain.usedByChain" :key="idx" class="chain-node">
                                                <div class="chain-node__item chain-node__item--level1">
                                                    <span class="chain-node__arrow">→</span>
                                                    <span class="chain-node__name">{{{{ item.measure }}}}</span>
                                                </div>

                                                <!-- Nested Used By (recursive) -->
                                                <div v-if="item.usedBy && item.usedBy.length > 0" class="chain-tree chain-tree--nested">
                                                    <div v-for="(child, cidx) in item.usedBy" :key="cidx" class="chain-node">
                                                        <div class="chain-node__item chain-node__item--level2">
                                                            <span class="chain-node__arrow">⇒</span>
                                                            <span class="chain-node__name">{{{{ child.measure }}}}</span>
                                                        </div>

                                                        <!-- Level 3 -->
                                                        <div v-if="child.usedBy && child.usedBy.length > 0" class="chain-tree chain-tree--nested">
                                                            <div v-for="(grandchild, gidx) in child.usedBy" :key="gidx" class="chain-node">
                                                                <div class="chain-node__item chain-node__item--level3">
                                                                    <span class="chain-node__arrow">⇛</span>
                                                                    <span class="chain-node__name">{{{{ grandchild.measure }}}}</span>
                                                                </div>

                                                                <!-- Level 4+ indicator -->
                                                                <div v-if="grandchild.usedBy && grandchild.usedBy.length > 0" class="chain-node__more">
                                                                    ... and {{{{ grandchild.usedBy.length }}}} more level(s)
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="chain-section">
                                        <div class="chain-section__header chain-section__header--muted">
                                            <span class="chain-section__title">⬆️ USED BY</span>
                                        </div>
                                        <div class="chain-empty">No other measures depend on this measure</div>
                                    </div>

                                    <div class="chain-divider"></div>

                                    <!-- DOWNWARD: Dependencies (What this measure uses) -->
                                    <div v-if="currentChain.dependencies && currentChain.dependencies.length > 0" class="chain-section">
                                        <div class="chain-section__header chain-section__header--downward">
                                            <span class="chain-section__title">⬇️ DEPENDS ON</span>
                                            <span class="chain-section__count">(This measure uses {{{{ currentChain.dependencies.length }}}} measure(s))</span>
                                        </div>
                                        <div class="chain-deps-grid">
                                            <div v-for="dep in currentChain.dependencies" :key="dep" class="chain-dep-item">
                                                {{{{ dep }}}}
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="chain-section">
                                        <div class="chain-section__header chain-section__header--downward">
                                            <span class="chain-section__title">⬇️ DEPENDS ON</span>
                                        </div>
                                        <div class="chain-base-measure">
                                            <div class="chain-base-measure__icon">🟢 BASE MEASURE</div>
                                            <div class="chain-base-measure__text">This measure doesn't depend on any other measures</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="card">
                            <div class="card__body">
                                <p class="empty-state">Select a measure from the left to view its complete dependency chain</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Visuals Tab -->
                <div v-show="dependencySubTab === 'visuals'" class="panel-grid">
                    <!-- Left: Page & Visual Selection -->
                    <div class="panel-left">
                        <div class="card">
                            <div class="card__header">
                                <h3 class="card__title">Select Page & Visual</h3>
                            </div>
                            <div class="card__body">
                                <!-- Page Selection -->
                                <div class="form-group">
                                    <label class="form-label">Page</label>
                                    <select v-model="selectedVisualPage" class="form-select" @change="selectedVisualId = null">
                                        <option :value="null">-- Select a page --</option>
                                        <option v-for="page in visualAnalysisPages" :key="page.name" :value="page.name">
                                            {{{{ page.name }}}} ({{{{ page.visualCount }}}} visuals)
                                        </option>
                                    </select>
                                </div>

                                <!-- Visual Selection -->
                                <div v-if="selectedVisualPage" class="form-group">
                                    <label class="form-label">Visual</label>
                                    <div class="scrollable">
                                        <div v-for="visual in visualsOnSelectedPage" :key="visual.visualId"
                                            @click="selectedVisualId = visual.visualId"
                                            :class="['visual-select-item', selectedVisualId === visual.visualId ? 'active' : '']"
                                        >
                                            <span class="badge badge-primary badge--small">{{{{ visual.visualType }}}}</span>
                                            <div class="visual-select-item__name">{{{{ visual.visualName || 'Unnamed Visual' }}}}</div>
                                            <div class="visual-select-item__meta">{{{{ visual.measureCount }}}} measure(s)</div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="empty-state">Select a page to view its visuals</div>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Measure Backward Trace -->
                    <div class="panel-right">
                        <div v-if="selectedVisualId && currentVisualAnalysis" class="card">
                            <div class="card__header">
                                <h3 class="card__title">Visual Measure Trace</h3>
                            </div>
                            <div class="card__body">
                                <div class="visual-trace-header">
                                    <span class="badge badge-primary">{{{{ currentVisualAnalysis.visualType }}}}</span>
                                    <span class="visual-trace-header__name">{{{{ currentVisualAnalysis.visualName || 'Unnamed Visual' }}}}</span>
                                    <div class="visual-trace-header__page">Page: {{{{ selectedVisualPage }}}}</div>
                                </div>

                                <!-- Backward Trace -->
                                <div class="trace-sections">
                                    <!-- Top-Level Measures (Used Directly in Visual) -->
                                    <div v-if="currentVisualAnalysis.topMeasures && currentVisualAnalysis.topMeasures.length > 0" class="trace-section">
                                        <div class="trace-section__header trace-section__header--visual">
                                            <span class="trace-section__title">📊 Measures Used in Visual</span>
                                            <span class="trace-section__count">({{{{ currentVisualAnalysis.topMeasures.length }}}})</span>
                                        </div>
                                        <div class="trace-tree trace-tree--visual">
                                            <div v-for="measure in currentVisualAnalysis.topMeasures" :key="measure.fullName" class="trace-measure">
                                                <div class="trace-measure__name">{{{{ measure.name }}}}</div>
                                                <div class="trace-measure__table">{{{{ measure.table }}}}</div>

                                                <!-- Show Dependencies -->
                                                <div v-if="measure.dependencies && measure.dependencies.length > 0" class="trace-deps">
                                                    <div class="trace-deps__header">⬇️ Depends on:</div>
                                                    <div class="trace-deps__list">
                                                        <div v-for="dep in measure.dependencies" :key="dep.fullName" class="trace-dep">
                                                            <div class="trace-dep__name">{{{{ dep.name }}}}</div>
                                                            <div class="trace-dep__table">{{{{ dep.table }}}}</div>

                                                            <!-- Nested Dependencies (Base Measures) -->
                                                            <div v-if="dep.dependencies && dep.dependencies.length > 0" class="trace-base-deps">
                                                                <div class="trace-deps__header">⬇️ Base:</div>
                                                                <div v-for="baseDep in dep.dependencies" :key="baseDep.fullName" class="trace-base-measure">
                                                                    <div class="trace-base-measure__name">{{{{ baseDep.name }}}}</div>
                                                                    <div class="trace-base-measure__table">{{{{ baseDep.table }}}}</div>
                                                                    <span class="badge badge-success badge--tiny">Base Measure</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- Base Measure Indicator -->
                                                <div v-else class="trace-measure__base">
                                                    <span class="badge badge-success badge--small">🟢 Base Measure</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Summary -->
                                    <div v-if="currentVisualAnalysis.summary" class="trace-summary">
                                        <h4 class="trace-summary__title">📋 Summary</h4>
                                        <div class="trace-summary__grid">
                                            <div class="trace-summary__item">
                                                <div class="trace-summary__label">Total Measures</div>
                                                <div class="trace-summary__value">{{{{ currentVisualAnalysis.summary.totalMeasures }}}}</div>
                                            </div>
                                            <div class="trace-summary__item">
                                                <div class="trace-summary__label">Direct Dependencies</div>
                                                <div class="trace-summary__value">{{{{ currentVisualAnalysis.summary.directDeps }}}}</div>
                                            </div>
                                            <div class="trace-summary__item">
                                                <div class="trace-summary__label">Base Measures</div>
                                                <div class="trace-summary__value">{{{{ currentVisualAnalysis.summary.baseMeasures }}}}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="card">
                            <div class="card__body">
                                <p class="empty-state">Select a page and visual from the left to trace measure dependencies</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Measure Info Modal -->
                <div v-if="showMeasureModal" class="modal-overlay" @click.self="closeMeasureModal">
                    <div class="modal">
                        <div class="modal__header">
                            <div>
                                <h2 class="modal__title">{{{{ selectedMeasureForModal?.name }}}}</h2>
                                <p class="modal__subtitle">table: {{{{ selectedMeasureForModal?.table }}}}</p>
                            </div>
                            <button @click="closeMeasureModal" class="modal__close">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>

                        <div class="modal__body">
                            <!-- Expression -->
                            <div v-if="selectedMeasureForModal?.expression" class="modal-section">
                                <h3 class="modal-section__title">Expression:</h3>
                                <div class="code-block">{{{{ selectedMeasureForModal.expression }}}}</div>
                            </div>

                            <!-- References -->
                            <div v-if="selectedMeasureForModal?.references && selectedMeasureForModal.references.length > 0" class="modal-section">
                                <h3 class="modal-section__title">References:</h3>
                                <div class="ref-list">
                                    <div v-for="ref in selectedMeasureForModal.references" :key="ref" class="ref-item ref-item--uses">
                                        {{{{ ref }}}}
                                    </div>
                                </div>
                            </div>

                            <!-- Referenced By -->
                            <div v-if="selectedMeasureForModal?.referencedBy && selectedMeasureForModal.referencedBy.length > 0" class="modal-section">
                                <h3 class="modal-section__title">Referenced By:</h3>
                                <div class="ref-list">
                                    <div v-for="ref in selectedMeasureForModal.referencedBy" :key="ref" class="ref-item ref-item--usedby">
                                        {{{{ ref }}}}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Usage Tab -->
            <div v-show="activeTab === 'usage'" class="tab-content">
                <!-- Field Parameters Section (Full Width) -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">Field Parameters</h3>
                        <div v-if="fieldParametersList.length > 0" class="card__actions">
                            <button @click="expandAllFieldParams" class="btn btn--small btn--primary">Expand All</button>
                            <button @click="collapseAllFieldParams" class="btn btn--small btn--secondary">Collapse All</button>
                        </div>
                    </div>
                    <div class="card__body">
                        <div v-if="fieldParametersList.length > 0" class="alert alert--info">
                            <strong>Info:</strong> Found {{{{ fieldParametersList.length }}}} field parameter(s) in the model.
                        </div>
                        <div v-if="fieldParametersList.length > 0" class="scrollable field-params-list">
                            <div v-for="fp in fieldParametersList" :key="fp.name" class="folder-group">
                                <div class="folder-header" :class="{{collapsed: collapsedFieldParams[fp.name]}}" @click="toggleFieldParam(fp.name)">
                                    <div class="folder-header__info">
                                        <span class="badge badge-success">{{{{ fp.name }}}}</span>
                                        <span class="field-param-card__table">{{{{ fp.table }}}}</span>
                                        <span class="folder-header__count">({{{{ fp.columns?.length || 0 }}}} columns)</span>
                                    </div>
                                    <span class="folder-header__icon">▼</span>
                                </div>
                                <div v-show="!collapsedFieldParams[fp.name]" class="folder-content">
                                    <div v-if="fp.columns && fp.columns.length > 0" class="columns-tag-grid">
                                        <div v-for="col in fp.columns" :key="col" class="column-tag">{{{{ col }}}}</div>
                                    </div>
                                    <div v-else class="empty-state empty-state--small">No columns referenced</div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="empty-state">No field parameters found in the model.</div>
                    </div>
                </div>

                <!-- Unused Measures and Columns Grid -->
                <div class="two-column-grid">
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">Unused Measures</h3>
                            <div v-if="dependencies.unused_measures?.length > 0" class="card__actions">
                                <button @click="expandAllUnusedMeasures" class="btn btn--small btn--primary">Expand All</button>
                                <button @click="collapseAllUnusedMeasures" class="btn btn--small btn--secondary">Collapse All</button>
                            </div>
                        </div>
                        <div class="card__body">
                            <div v-if="dependencies.unused_measures?.length > 0" class="alert alert--warning">
                                <strong>Warning:</strong> Found {{{{ dependencies.unused_measures.length }}}} measures not used anywhere.
                            </div>
                            <div v-if="dependencies.unused_measures?.length > 0" class="scrollable">
                                <!-- Grouped by folder -->
                                <div v-for="(measures, folderName) in unusedMeasuresByFolder" :key="folderName" class="folder-group">
                                    <div class="folder-header" :class="{{collapsed: collapsedUnusedMeasureFolders[folderName]}}" @click="toggleUnusedMeasureFolder(folderName)">
                                        <div class="folder-header__info">
                                            <strong>{{{{ folderName }}}}</strong>
                                            <span class="folder-header__count">({{{{ measures.length }}}})</span>
                                        </div>
                                        <span class="folder-header__icon">▼</span>
                                    </div>
                                    <div v-show="!collapsedUnusedMeasureFolders[folderName]" class="folder-content">
                                        <div v-for="measure in measures" :key="measure" class="unused-item">{{{{ measure }}}}</div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="success-state">✓ All measures are in use!</div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">Unused Columns</h3>
                            <div v-if="dependencies.unused_columns?.length > 0" class="card__actions">
                                <button @click="expandAllUnusedColumns" class="btn btn--small btn--primary">Expand All</button>
                                <button @click="collapseAllUnusedColumns" class="btn btn--small btn--secondary">Collapse All</button>
                            </div>
                        </div>
                        <div class="card__body">
                            <div v-if="dependencies.unused_columns?.length > 0" class="alert alert--warning">
                                <strong>Warning:</strong> Found {{{{ dependencies.unused_columns.length }}}} columns not used anywhere.
                            </div>
                            <div v-if="dependencies.unused_columns?.length > 0" class="scrollable">
                                <!-- Grouped by table -->
                                <div v-for="(columns, tableName) in unusedColumnsByTable" :key="tableName" class="folder-group">
                                    <div class="folder-header" :class="{{collapsed: collapsedUnusedColumnTables[tableName]}}" @click="toggleUnusedColumnTable(tableName)">
                                        <div class="folder-header__info">
                                            <strong>{{{{ tableName }}}}</strong>
                                            <span class="folder-header__count">({{{{ columns.length }}}})</span>
                                        </div>
                                        <span class="folder-header__icon">▼</span>
                                    </div>
                                    <div v-show="!collapsedUnusedColumnTables[tableName]" class="folder-content">
                                        <div v-for="column in columns" :key="column" class="unused-item">{{{{ column }}}}</div>
                                    </div>
                                </div>
                            </div>
                            <div v-else class="success-state">✓ All columns are in use!</div>
                        </div>
                    </div>
                </div>

                <!-- Complete Usage Matrix -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">Complete Usage Matrix</h3>
                        <div class="card__actions">
                            <select v-model="usageMatrixFilter" class="usage-filter-select">
                                <option value="all">Show All</option>
                                <option value="used">Used Only</option>
                                <option value="unused">Unused Only</option>
                            </select>
                            <button @click="copyUsageMatrix" class="btn btn--small btn--primary">Copy to Clipboard</button>
                        </div>
                    </div>
                    <div class="card__body">
                        <!-- Measures Matrix - Grouped by Display Folder -->
                        <div class="usage-matrix-section">
                            <div class="usage-matrix-header">
                                <h4 class="usage-matrix-title">Measures ({{{{ filteredMeasuresMatrix.length }}}})</h4>
                                <div class="usage-matrix-actions">
                                    <button @click="expandAllMeasureFolders" class="btn btn--small btn--secondary">Expand All</button>
                                    <button @click="collapseAllMeasureFolders" class="btn btn--small btn--secondary">Collapse All</button>
                                </div>
                            </div>
                            <div class="usage-matrix-container">
                                <div v-for="(measures, folderName) in filteredMeasuresGroupedByFolder" :key="folderName" class="collapsible-group">
                                    <div class="collapsible-header" :class="{{collapsed: collapsedMeasureFolders[folderName]}}" @click="toggleMeasureFolder(folderName)">
                                        <span class="collapsible-icon">{{{{ collapsedMeasureFolders[folderName] ? '▶' : '▼' }}}}</span>
                                        <span class="collapsible-title">{{{{ folderName || 'No Folder' }}}}</span>
                                        <span class="collapsible-count">({{{{ measures.length }}}})</span>
                                        <span class="collapsible-stats">
                                            <span class="stat-used">{{{{ measures.filter(m => m.isUsed).length }}}} used</span>
                                            <span class="stat-unused">{{{{ measures.filter(m => !m.isUsed).length }}}} unused</span>
                                        </span>
                                    </div>
                                    <div v-show="!collapsedMeasureFolders[folderName]" class="collapsible-content">
                                        <table class="usage-matrix-table">
                                            <thead>
                                                <tr>
                                                    <th>Table</th>
                                                    <th>Measure Name</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="item in measures" :key="item.fullName" :class="{{'unused-row': !item.isUsed}}">
                                                    <td>{{{{ item.table }}}}</td>
                                                    <td>{{{{ item.name }}}}</td>
                                                    <td>
                                                        <span :class="['status-badge', item.isUsed ? 'status-badge--used' : 'status-badge--unused']">
                                                            {{{{ item.isUsed ? 'Used' : 'Unused' }}}}
                                                        </span>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Columns Matrix - Grouped by Table -->
                        <div class="usage-matrix-section">
                            <div class="usage-matrix-header">
                                <h4 class="usage-matrix-title">Columns ({{{{ filteredColumnsMatrix.length }}}})</h4>
                                <div class="usage-matrix-actions">
                                    <button @click="expandAllColumnTables" class="btn btn--small btn--secondary">Expand All</button>
                                    <button @click="collapseAllColumnTables" class="btn btn--small btn--secondary">Collapse All</button>
                                </div>
                            </div>
                            <div class="usage-matrix-container">
                                <div v-for="(columns, tableName) in filteredColumnsGroupedByTable" :key="tableName" class="collapsible-group">
                                    <div class="collapsible-header" :class="{{collapsed: collapsedColumnTables[tableName]}}" @click="toggleColumnTable(tableName)">
                                        <span class="collapsible-icon">{{{{ collapsedColumnTables[tableName] ? '▶' : '▼' }}}}</span>
                                        <span class="collapsible-title">{{{{ tableName }}}}</span>
                                        <span class="collapsible-count">({{{{ columns.length }}}})</span>
                                        <span class="collapsible-stats">
                                            <span class="stat-used">{{{{ columns.filter(c => c.isUsed).length }}}} used</span>
                                            <span class="stat-unused">{{{{ columns.filter(c => !c.isUsed).length }}}} unused</span>
                                        </span>
                                    </div>
                                    <div v-show="!collapsedColumnTables[tableName]" class="collapsible-content">
                                        <table class="usage-matrix-table">
                                            <thead>
                                                <tr>
                                                    <th>Column Name</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="item in columns" :key="item.fullName" :class="{{'unused-row': !item.isUsed}}">
                                                    <td>{{{{ item.name }}}}</td>
                                                    <td>
                                                        <span :class="['status-badge', item.isUsed ? 'status-badge--used' : 'status-badge--unused']">
                                                            {{{{ item.isUsed ? 'Used' : 'Unused' }}}}
                                                        </span>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Best Practices Tab -->
            <div v-show="activeTab === 'best-practices'" class="tab-content">
                <div class="tab-header">
                    <h1 class="tab-header__title">Best Practice Analysis</h1>
                    <p class="tab-header__subtitle">Analysis based on Microsoft Power BI Best Practices</p>
                </div>

                <!-- BPA Summary Cards -->
                <div class="metrics-grid metrics-grid--4">
                    <div class="metric-card">
                        <div class="metric-card__label">Total Violations</div>
                        <div class="metric-card__value">{{{{ bpaTotalViolations }}}}</div>
                    </div>
                    <div class="metric-card metric-card--coral">
                        <div class="metric-card__label">Errors</div>
                        <div class="metric-card__value">{{{{ bpaErrorCount }}}}</div>
                    </div>
                    <div class="metric-card metric-card--rust">
                        <div class="metric-card__label">Warnings</div>
                        <div class="metric-card__value">{{{{ bpaWarningCount }}}}</div>
                    </div>
                    <div class="metric-card metric-card--ocean">
                        <div class="metric-card__label">Info</div>
                        <div class="metric-card__value">{{{{ bpaInfoCount }}}}</div>
                    </div>
                </div>

                <!-- Category Breakdown -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">Violations by Category</h3>
                    </div>
                    <div class="card__body">
                        <div class="category-breakdown">
                            <div v-for="(count, category) in bpaCategoryBreakdown" :key="category" class="category-item">
                                <div class="category-item__name">{{{{ category }}}}</div>
                                <div class="category-item__count">{{{{ count }}}}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Violations by Object Type -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">Violations by Object Type</h3>
                        <div class="card__filters">
                            <select v-model="bpaSeverityFilter" class="form-select form-select--small">
                                <option value="all">All Severities</option>
                                <option value="ERROR">Errors</option>
                                <option value="WARNING">Warnings</option>
                                <option value="INFO">Info</option>
                            </select>
                            <select v-model="bpaCategoryFilter" class="form-select form-select--small">
                                <option value="all">All Categories</option>
                                <option v-for="category in bpaCategories" :key="category" :value="category">{{{{ category }}}}</option>
                            </select>
                        </div>
                    </div>
                    <div class="card__body">
                        <!-- Group by Object Type, then by Category (with Maintenance last) -->
                        <div v-for="objectType in bpaObjectTypes" :key="objectType" class="accordion-group">
                            <div @click="toggleBpaObjectGroup(objectType)" class="accordion-header">
                                <div class="accordion-header__left">
                                    <svg class="accordion-header__icon" :class="{{expanded: !collapsedBpaObjectGroups[objectType]}}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                    </svg>
                                    <span class="accordion-header__title">{{{{ objectType }}}} ({{{{ bpaViolationsByObjectType[objectType].length }}}})</span>
                                </div>
                            </div>

                            <div v-show="!collapsedBpaObjectGroups[objectType]" class="accordion-content">
                                <!-- Violations grouped by category within this object type -->
                                <div v-for="category in bpaOrderedCategories" :key="category">
                                    <template v-if="bpaViolationsByObjectAndCategory[objectType] && bpaViolationsByObjectAndCategory[objectType][category]">
                                        <div @click="toggleBpaCategory(objectType, category)" class="accordion-subheader">
                                            <svg class="accordion-subheader__icon" :class="{{expanded: !collapsedBpaCategories[`${{objectType}}|${{category}}`]}}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                            </svg>
                                            <span>{{{{ category }}}} ({{{{ bpaViolationsByObjectAndCategory[objectType][category].length }}}})</span>
                                        </div>
                                        <div v-show="!collapsedBpaCategories[`${{objectType}}|${{category}}`]" class="table-container">
                                            <table class="data-table">
                                                <thead>
                                                    <tr>
                                                        <th>Severity</th>
                                                        <th>Rule</th>
                                                        <th>Object</th>
                                                        <th>Description</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr v-for="violation in bpaViolationsByObjectAndCategory[objectType][category]" :key="violation.rule_id + violation.object_name">
                                                        <td><span :class="bpaSeverityClass(violation.severity)" class="severity-badge">{{{{ violation.severity }}}}</span></td>
                                                        <td>{{{{ violation.rule_name }}}}</td>
                                                        <td>
                                                            <div class="cell-primary">{{{{ violation.object_name }}}}</div>
                                                            <div v-if="violation.table_name" class="cell-secondary">Table: {{{{ violation.table_name }}}}</div>
                                                        </td>
                                                        <td>
                                                            <div>{{{{ violation.description }}}}</div>
                                                            <div v-if="violation.details" class="cell-secondary">{{{{ violation.details }}}}</div>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </template>
                                </div>
                            </div>
                        </div>

                        <div v-if="filteredBpaViolations.length === 0" class="empty-state">No violations found matching your filters</div>
                    </div>
                </div>

                <!-- Naming Conventions Section -->
                <div v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.naming_conventions" class="card">
                    <div class="card__header">
                        <h3 class="card__title">Naming Convention Violations</h3>
                    </div>
                    <div class="card__body">
                        <div v-if="namingViolationsCount === 0" class="success-state success-state--large">
                            <div class="success-state__icon">✅</div>
                            <h3 class="success-state__title">All naming conventions followed!</h3>
                            <p class="success-state__text">No violations found</p>
                        </div>

                        <div v-else>
                            <!-- Naming Summary -->
                            <div class="metrics-grid metrics-grid--3">
                                <div class="metric-card metric-card--coral">
                                    <div class="metric-card__label">Total Violations</div>
                                    <div class="metric-card__value">{{{{ namingViolationsCount }}}}</div>
                                </div>
                                <div class="metric-card metric-card--rust">
                                    <div class="metric-card__label">Warnings</div>
                                    <div class="metric-card__value">{{{{ namingSummary.by_severity?.WARNING || 0 }}}}</div>
                                </div>
                                <div class="metric-card metric-card--ocean">
                                    <div class="metric-card__label">Info</div>
                                    <div class="metric-card__value">{{{{ namingSummary.by_severity?.INFO || 0 }}}}</div>
                                </div>
                            </div>

                            <!-- Filters -->
                            <div class="filter-row">
                                <select v-model="namingSeverityFilter" class="form-select form-select--small">
                                    <option value="all">All Severities</option>
                                    <option value="WARNING">Warnings</option>
                                    <option value="INFO">Info</option>
                                </select>
                                <select v-model="namingTypeFilter" class="form-select form-select--small">
                                    <option value="all">All Types</option>
                                    <option value="missing_prefix">Missing Prefix</option>
                                    <option value="contains_spaces">Contains Spaces</option>
                                    <option value="name_too_long">Name Too Long</option>
                                    <option value="special_characters">Special Characters</option>
                                </select>
                            </div>

                            <!-- Violations Table -->
                            <div class="table-container table-container--scrollable">
                                <table class="data-table">
                                    <thead>
                                        <tr>
                                            <th>Severity</th>
                                            <th>Type</th>
                                            <th>Object Type</th>
                                            <th>Table</th>
                                            <th>Object</th>
                                            <th>Issue</th>
                                            <th>Current Name</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr v-for="(violation, idx) in filteredNamingViolations" :key="idx">
                                            <td><span :class="severityBadgeClass(violation.severity)" class="severity-badge">{{{{ violation.severity }}}}</span></td>
                                            <td>{{{{ violation.type }}}}</td>
                                            <td>{{{{ violation.object_type }}}}</td>
                                            <td class="cell-primary">{{{{ violation.table }}}}</td>
                                            <td>{{{{ violation.object }}}}</td>
                                            <td>{{{{ violation.issue }}}}</td>
                                            <td class="cell-mono">{{{{ violation.current_name }}}}</td>
                                        </tr>
                                    </tbody>
                                </table>
                            <div v-if="filteredNamingViolations.length === 0" class="empty-state">No violations match your filters</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Data Quality Tab -->
            <div v-show="activeTab === 'data-quality'" class="tab-content">
                <div class="tab-header">
                    <h1 class="tab-header__title">Data Quality Analysis</h1>
                    <p class="tab-header__subtitle">Data type optimization and cardinality warnings</p>
                </div>

                <!-- Data Type Summary -->
                <div class="two-column-grid">
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">Data Type Distribution</h3>
                        </div>
                        <div class="card__body">
                            <div class="distribution-list">
                                <div v-for="(count, type) in dataTypeSummary" :key="type" class="distribution-item">
                                    <span class="distribution-item__type">{{{{ type }}}}</span>
                                    <div class="distribution-item__bar">
                                        <div class="distribution-item__fill" :style="{{ width: (count / totalDataTypeCount * 100) + '%' }}"></div>
                                    </div>
                                    <span class="distribution-item__count">{{{{ count }}}}</span>
                                    <span class="distribution-item__percent">{{{{ Math.round(count / totalDataTypeCount * 100) }}}}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card__header">
                            <h3 class="card__title">Quality Metrics</h3>
                        </div>
                        <div class="card__body">
                            <div class="metrics-stack">
                                <div class="metric-card metric-card--rust">
                                    <div class="metric-card__label">Data Type Issues</div>
                                    <div class="metric-card__value">{{{{ dataTypeIssues.length }}}}</div>
                                </div>
                                <div class="metric-card metric-card--coral">
                                    <div class="metric-card__label">High-Impact Issues</div>
                                    <div class="metric-card__value">{{{{ dataTypeHighImpactCount }}}}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Data Type Issues Table -->
                <div class="card">
                    <div class="card__header">
                        <h3 class="card__title">Data Type Optimization Opportunities</h3>
                        <select v-model="dataTypeImpactFilter" class="form-select form-select--small">
                            <option value="all">All Impact Levels</option>
                            <option value="HIGH">High Impact</option>
                            <option value="MEDIUM">Medium Impact</option>
                            <option value="LOW">Low Impact</option>
                        </select>
                    </div>
                    <div class="card__body">
                        <div class="table-container table-container--scrollable">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Table</th>
                                        <th>Column</th>
                                        <th>Current Type</th>
                                        <th>Issue</th>
                                        <th>Recommendation</th>
                                        <th>Impact</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="issue in filteredDataTypeIssues" :key="issue.table + issue.column">
                                        <td class="cell-primary">{{{{ issue.table }}}}</td>
                                        <td>{{{{ issue.column }}}}</td>
                                        <td><code class="code-inline">{{{{ issue.current_type }}}}</code></td>
                                        <td>{{{{ issue.issue }}}}</td>
                                        <td class="cell-link">{{{{ issue.recommendation }}}}</td>
                                        <td><span :class="impactBadgeClass(issue.impact)" class="impact-badge">{{{{ issue.impact }}}}</span></td>
                                    </tr>
                                </tbody>
                            </table>
                            <div v-if="filteredDataTypeIssues.length === 0" class="empty-state">No data type issues found</div>
                        </div>
                    </div>
                </div>

                <!-- Cardinality Warnings -->
                <div class="card" v-if="cardinalityWarnings.length > 0">
                    <div class="card__header">
                        <h3 class="card__title">High Cardinality Warnings</h3>
                    </div>
                    <div class="card__body">
                        <div class="alert alert--warning">
                            <strong>Note:</strong> High cardinality columns can impact performance and memory usage. Consider hiding or pre-aggregating these columns.
                        </div>
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Table</th>
                                        <th>Column</th>
                                        <th>Reason</th>
                                        <th>Is Hidden</th>
                                        <th>Recommendation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="warning in cardinalityWarnings" :key="warning.table + warning.column">
                                        <td class="cell-primary">{{{{ warning.table }}}}</td>
                                        <td>{{{{ warning.column }}}}</td>
                                        <td>{{{{ warning.reason }}}}</td>
                                        <td><span :class="warning.is_hidden ? 'status-success' : 'status-error'">{{{{ warning.is_hidden ? '✓ Yes' : '✗ No' }}}}</span></td>
                                        <td class="cell-link">{{{{ warning.recommendation }}}}</td>
                                    </tr>
                                </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Perspectives Tab -->
            <div v-show="activeTab === 'perspectives'" class="tab-content">
                <div class="tab-header">
                    <h1 class="tab-header__title">Perspectives Analysis</h1>
                    <p class="tab-header__subtitle">Object visibility and perspective usage</p>
                </div>

                <div v-if="!perspectivesData.has_perspectives" class="card">
                    <div class="card__body">
                        <div class="empty-state">
                            <div class="empty-state__icon">👁️</div>
                            <h3 class="empty-state__title">No Perspectives Defined</h3>
                            <p class="empty-state__text">{{{{ perspectivesData.message }}}}</p>
                        </div>
                    </div>
                </div>

                <div v-else>
                    <!-- Perspectives Summary -->
                    <div class="metrics-grid metrics-grid--3">
                        <div class="metric-card metric-card--ocean">
                            <div class="metric-card__label">Total Perspectives</div>
                            <div class="metric-card__value">{{{{ perspectivesCount }}}}</div>
                        </div>
                        <div class="metric-card metric-card--rust">
                            <div class="metric-card__label">Unused Perspectives</div>
                            <div class="metric-card__value">{{{{ perspectivesData.unused_perspectives?.length || 0 }}}}</div>
                        </div>
                        <div class="metric-card metric-card--sage">
                            <div class="metric-card__label">Active Perspectives</div>
                            <div class="metric-card__value">{{{{ perspectivesCount - (perspectivesData.unused_perspectives?.length || 0) }}}}</div>
                        </div>
                    </div>

                    <!-- Perspectives Details -->
                    <div class="card">
                        <div class="card__header">
                            <h2 class="card__title">Perspective Details</h2>
                        </div>
                        <div class="card__body">
                            <div class="perspective-list">
                                <div v-for="perspective in perspectivesData.perspectives" :key="perspective.name" class="perspective-item">
                                    <div class="perspective-item__header">
                                        <h3 class="perspective-item__name">{{{{ perspective.name }}}}</h3>
                                        <span v-if="perspective.total_objects === 0" class="status-badge status-badge--warning">UNUSED</span>
                                        <span v-else class="status-badge status-badge--success">ACTIVE</span>
                                    </div>
                                    <div class="perspective-item__stats">
                                        <div class="perspective-stat perspective-stat--ocean">
                                            <span class="perspective-stat__label">Tables</span>
                                            <span class="perspective-stat__value">{{{{ perspective.table_count }}}}</span>
                                        </div>
                                        <div class="perspective-stat perspective-stat--sage">
                                            <span class="perspective-stat__label">Columns</span>
                                            <span class="perspective-stat__value">{{{{ perspective.column_count }}}}</span>
                                        </div>
                                        <div class="perspective-stat perspective-stat--purple">
                                            <span class="perspective-stat__label">Measures</span>
                                            <span class="perspective-stat__value">{{{{ perspective.measure_count }}}}</span>
                                        </div>
                                        <div class="perspective-stat perspective-stat--neutral">
                                            <span class="perspective-stat__label">Total</span>
                                            <span class="perspective-stat__value">{{{{ perspective.total_objects }}}}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
                </main>
            </div>
        </div>

        <!-- Command Palette -->
        <div v-if="showCommandPalette" v-cloak class="command-palette" @click.self="showCommandPalette = false">
            <div class="command-palette__content">
                <div class="command-palette__input-wrapper">
                    <input
                        v-model="commandQuery"
                        type="text"
                        placeholder="Type a command..."
                        class="command-palette__input"
                        @keydown.esc="showCommandPalette = false"
                        ref="commandInput"
                    />
                </div>
                <div class="command-palette__results">
                    <div
                        v-for="cmd in filteredCommands"
                        :key="cmd.name"
                        @click="executeCommand(cmd)"
                        class="command-palette__item"
                    >
                        <div class="command-palette__item-name">{{{{ cmd.name }}}}</div>
                        <div class="command-palette__item-desc">{{{{ cmd.description }}}}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""

    def _get_vue_app_script(self, data_json_str: str) -> str:
        """Get Vue 3 app script."""
        return f"""    <script>
        const {{ createApp }} = Vue;

        const pbipData = {data_json_str};

        createApp({{
            data() {{
                return {{
                    modelData: pbipData.model || {{}},
                    reportData: pbipData.report || null,
                    dependencies: pbipData.dependencies || {{}},
                    enhancedData: pbipData.enhanced || null,
                    repositoryName: pbipData.repository_name || 'PBIP Repository',

                    activeTab: 'summary',
                    searchQuery: '',
                    darkMode: false,
                    showCommandPalette: false,
                    commandQuery: '',

                    // Model tab
                    selectedTable: null,
                    selectedMeasure: null,
                    modelDetailTab: 'columns',
                    modelSearchQuery: '',
                    modelSubTab: 'tables',
                    measuresSearchQuery: '',
                    collapsedFolders: {{}},
                    expandedMeasures: {{}},

                    // Relationship Graph
                    relationshipGraphLayout: 'list',  // 'tree', 'dagre', 'force', 'list'
                    expandedDependencyNodes: {{}},

                    // Report tab
                    selectedPage: null,
                    collapsedVisualGroups: {{}},

                    // Usage tab
                    collapsedUnusedMeasureFolders: {{}},
                    collapsedUnusedColumnTables: {{}},
                    collapsedFieldParams: {{}},
                    usageMatrixFilter: 'all',
                    collapsedMeasureFolders: {{}},
                    collapsedColumnTables: {{}},

                    // Dependencies tab
                    selectedDependencyKey: null,
                    dependencySearchQuery: '',
                    dependencySubTab: 'measures',
                    selectedColumnKey: null,
                    columnSearchQuery: '',
                    collapsedDependencyFolders: {{}},
                    collapsedUsedByFolders: {{}},

                    // Measure Chains tab
                    selectedChainMeasure: null,
                    chainSearchQuery: '',
                    collapsedChainFolders: {{}},

                    // Visuals tab
                    selectedVisualPage: null,
                    selectedVisualId: null,

                    // Measure Dependency Graph
                    graphSearchQuery: '',
                    graphFilterMode: 'all',
                    graphShowDisconnected: true,
                    graphStats: {{
                        totalMeasures: 0,
                        visibleMeasures: 0,
                        totalDependencies: 0,
                        maxDepth: 0
                    }},
                    showMeasureModal: false,
                    selectedMeasureForModal: null,
                    highlightedMeasures: new Set(),

                    // Enhanced analysis tabs
                    bpaSeverityFilter: 'all',
                    bpaCategoryFilter: 'all',
                    collapsedBpaObjectGroups: {{}},
                    collapsedBpaCategories: {{}},
                    dataTypeImpactFilter: 'all',

                    // Naming conventions
                    namingSeverityFilter: 'all',
                    namingTypeFilter: 'all',

                    commands: [
                        {{ name: 'Go to Summary', description: 'View summary and insights', action: () => this.activeTab = 'summary' }},
                        {{ name: 'Go to Model', description: 'Explore model tables', action: () => this.activeTab = 'model' }},
                        {{ name: 'Go to Report', description: 'View report visuals', action: () => this.activeTab = 'report' }},
                        {{ name: 'Go to Dependencies', description: 'Analyze dependencies', action: () => this.activeTab = 'dependencies' }},
                        {{ name: 'Go to Usage', description: 'View unused objects', action: () => this.activeTab = 'usage' }},
                        {{ name: 'Go to Best Practices', description: 'View BPA violations', action: () => this.activeTab = 'best-practices' }},
                        {{ name: 'Go to Data Quality', description: 'View data type and cardinality analysis', action: () => this.activeTab = 'data-quality' }},
                        {{ name: 'Export to CSV', description: 'Export model data to CSV', action: () => this.exportToCSV() }},
                        {{ name: 'Export to JSON', description: 'Export all data to JSON', action: () => this.exportToJSON() }},
                        {{ name: 'Toggle Dark Mode', description: 'Switch light/dark theme', action: () => this.toggleDarkMode() }}
                    ],

                    // Performance: Cache expensive calculations
                    _cachedVisibleVisualCount: null,
                    _cachedStatistics: null,
                    _cachedModelArchitecture: null,
                    _cachedTableDistribution: null,
                    _cachedAllMeasures: null,
                    _cachedAllColumns: null
                }};
            }},

            computed: {{
                statistics() {{
                    // Return cached statistics if available
                    if (this._cachedStatistics) {{
                        return this._cachedStatistics;
                    }}

                    const summary = this.dependencies.summary || {{}};

                    // Use cached visual count or calculate once
                    if (this._cachedVisibleVisualCount === null && this.reportData && this.reportData.pages) {{
                        this._cachedVisibleVisualCount = 0;
                        this.reportData.pages.forEach(page => {{
                            this._cachedVisibleVisualCount += this.getVisibleVisualCount(page.visuals || []);
                        }});
                    }}

                    this._cachedStatistics = {{
                        total_tables: summary.total_tables || 0,
                        total_measures: summary.total_measures || 0,
                        total_columns: summary.total_columns || 0,
                        total_relationships: summary.total_relationships || 0,
                        total_pages: summary.total_pages || 0,
                        total_visuals: this._cachedVisibleVisualCount || summary.total_visuals || 0,
                        unused_measures: summary.unused_measures || 0,
                        unused_columns: summary.unused_columns || 0
                    }};

                    return this._cachedStatistics;
                }},

                modelArchitecture() {{
                    if (this._cachedModelArchitecture) {{
                        return this._cachedModelArchitecture;
                    }}
                    const tables = this.modelData.tables || [];
                    const factTables = tables.filter(t => t.name.toLowerCase().startsWith('f ')).length;
                    const dimTables = tables.filter(t => t.name.toLowerCase().startsWith('d ')).length;
                    this._cachedModelArchitecture = factTables > 0 && dimTables > 0 ? 'Star Schema' : 'Custom';
                    return this._cachedModelArchitecture;
                }},

                tableDistribution() {{
                    if (this._cachedTableDistribution) {{
                        return this._cachedTableDistribution;
                    }}
                    const tables = this.modelData.tables || [];
                    const total = tables.length || 1;
                    const fact = tables.filter(t => t.name.toLowerCase().startsWith('f ')).length;
                    const dimension = tables.filter(t => t.name.toLowerCase().startsWith('d ')).length;
                    this._cachedTableDistribution = {{
                        fact: ((fact / total) * 100).toFixed(1),
                        dimension: ((dimension / total) * 100).toFixed(1)
                    }};
                    return this._cachedTableDistribution;
                }},

                avgColumnsPerTable() {{
                    const total = this.statistics.total_columns;
                    const tables = this.statistics.total_tables || 1;
                    return (total / tables).toFixed(1);
                }},

                avgMeasuresPerTable() {{
                    const total = this.statistics.total_measures;
                    const tables = this.statistics.total_tables || 1;
                    return (total / tables).toFixed(1);
                }},

                measureToColumnRatio() {{
                    const measures = this.statistics.total_measures;
                    const columns = this.statistics.total_columns || 1;
                    return (measures / columns).toFixed(2);
                }},

                measuresUsedPct() {{
                    const total = this.statistics.total_measures;
                    const unused = this.statistics.unused_measures;
                    if (total === 0) return 0;
                    return (((total - unused) / total) * 100).toFixed(1);
                }},

                columnsUsedPct() {{
                    const total = this.statistics.total_columns;
                    const unused = this.statistics.unused_columns;
                    if (total === 0) return 0;
                    return (((total - unused) / total) * 100).toFixed(1);
                }},

                issues() {{
                    const issues = [];
                    const stats = this.statistics;

                    if (stats.unused_measures > stats.total_measures * 0.2) {{
                        issues.push(`High number of unused measures (${{stats.unused_measures}} measures, ${{(stats.unused_measures/stats.total_measures*100).toFixed(1)}}%)`);
                    }}

                    if (stats.unused_columns > stats.total_columns * 0.3) {{
                        issues.push(`Significant unused columns detected (${{stats.unused_columns}} columns, ${{(stats.unused_columns/stats.total_columns*100).toFixed(1)}}%)`);
                    }}

                    if (stats.total_measures > stats.total_columns * 2) {{
                        issues.push(`Very high measure-to-column ratio (${{this.measureToColumnRatio}}:1)`);
                    }}

                    return issues;
                }},

                recommendations() {{
                    const recs = [];
                    const stats = this.statistics;

                    if (stats.unused_measures > stats.total_measures * 0.2) {{
                        recs.push('Review and remove unused measures to improve model maintainability');
                    }}

                    if (stats.unused_columns > stats.total_columns * 0.3) {{
                        recs.push('Consider removing unused columns to reduce model size and improve refresh performance');
                    }}

                    if (stats.total_measures > stats.total_columns * 2) {{
                        recs.push('Review measure complexity and consider consolidating similar calculations');
                    }}

                    return recs;
                }},

                healthSummary() {{
                    return this.issues.length === 0
                        ? 'This model appears well-structured with good measure and column utilization.'
                        : `This model has ${{this.issues.length}} area(s) that may benefit from optimization. Review the recommendations above.`;
                }},

                modelComplexity() {{
                    const measures = this.statistics.total_measures;
                    const columns = this.statistics.total_columns;

                    if (measures < 50 && columns < 100) return 'Low';
                    if (measures < 200 && columns < 500) return 'Medium';
                    return 'High';
                }},

                filteredTables() {{
                    const tables = this.modelData.tables || [];
                    const query = this.modelSearchQuery.toLowerCase();

                    if (!query) return tables;

                    return tables.filter(t =>
                        t.name.toLowerCase().includes(query)
                    );
                }},

                filteredMeasuresForDependency() {{
                    const measures = [];
                    const tables = this.modelData.tables || [];
                    const query = this.dependencySearchQuery.toLowerCase();

                    tables.forEach(table => {{
                        (table.measures || []).forEach(measure => {{
                            const key = `${{table.name}}[${{measure.name}}]`;
                            if (!query || measure.name.toLowerCase().includes(query) || table.name.toLowerCase().includes(query)) {{
                                measures.push({{
                                    key: key,
                                    name: measure.name,
                                    table: table.name
                                }});
                            }}
                        }});
                    }});

                    return measures;
                }},

                currentDependencyDetails() {{
                    if (!this.selectedDependencyKey) {{
                        return {{ dependsOn: [], usedBy: [], visualUsage: [] }};
                    }}

                    const deps = this.dependencies;
                    const key = this.selectedDependencyKey;

                    const dependsOn = deps.measure_to_measure?.[key] || [];
                    const usedBy = deps.measure_to_measure_reverse?.[key] || [];
                    const visualUsage = this.findMeasureInVisuals(key);

                    return {{ dependsOn, usedBy, visualUsage }};
                }},

                measuresByFolder() {{
                    const folders = {{}};
                    const tables = this.modelData.tables || [];
                    const query = this.measuresSearchQuery.toLowerCase();

                    tables.forEach(table => {{
                        (table.measures || []).forEach(measure => {{
                            if (!query || measure.name.toLowerCase().includes(query)) {{
                                const folder = measure.display_folder || 'No Folder';
                                if (!folders[folder]) {{
                                    folders[folder] = [];
                                }}
                                folders[folder].push({{
                                    key: `${{table.name}}[${{measure.name}}]`,
                                    name: measure.name,
                                    table: table.name,
                                    expression: measure.expression,
                                    is_hidden: measure.is_hidden,
                                    display_folder: measure.display_folder
                                }});
                            }}
                        }});
                    }});

                    // Sort folders alphabetically
                    const sortedFolders = {{}};
                    Object.keys(folders).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sortedFolders[key] = folders[key];
                    }});

                    return sortedFolders;
                }},

                measuresForDependencyByFolder() {{
                    const folders = {{}};
                    const tables = this.modelData.tables || [];
                    const query = this.dependencySearchQuery.toLowerCase();

                    tables.forEach(table => {{
                        (table.measures || []).forEach(measure => {{
                            if (!query || measure.name.toLowerCase().includes(query) || table.name.toLowerCase().includes(query)) {{
                                const folder = measure.display_folder || 'No Folder';
                                if (!folders[folder]) {{
                                    folders[folder] = [];
                                }}
                                folders[folder].push({{
                                    key: `${{table.name}}[${{measure.name}}]`,
                                    name: measure.name,
                                    table: table.name,
                                    display_folder: measure.display_folder
                                }});
                            }}
                        }});
                    }});

                    // Sort folders alphabetically
                    const sortedFolders = {{}};
                    Object.keys(folders).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sortedFolders[key] = folders[key];
                    }});

                    return sortedFolders;
                }},

                sortedRelationships() {{
                    const rels = this.modelData.relationships || [];
                    return [...rels].sort((a, b) => {{
                        const aFrom = a.from_table || '';
                        const bFrom = b.from_table || '';
                        if (aFrom !== bFrom) return aFrom.localeCompare(bFrom);
                        return (a.to_table || '').localeCompare(b.to_table || '');
                    }});
                }},

                // Group relationships by schema pattern
                factToDimRelationships() {{
                    return this.sortedRelationships.filter(rel => {{
                        const from = (rel.from_table || '').toLowerCase();
                        const to = (rel.to_table || '').toLowerCase();
                        const isFactFrom = from.startsWith('f ') || from.startsWith('fact');
                        const isDimTo = to.startsWith('d ') || to.startsWith('dim');
                        return isFactFrom && isDimTo;
                    }});
                }},

                dimToDimRelationships() {{
                    return this.sortedRelationships.filter(rel => {{
                        const from = (rel.from_table || '').toLowerCase();
                        const to = (rel.to_table || '').toLowerCase();
                        const isDimFrom = from.startsWith('d ') || from.startsWith('dim');
                        const isDimTo = to.startsWith('d ') || to.startsWith('dim');
                        return isDimFrom && isDimTo;
                    }});
                }},

                otherRelationships() {{
                    const factToDim = new Set(this.factToDimRelationships.map(r => `${{r.from_table}}-${{r.to_table}}`));
                    const dimToDim = new Set(this.dimToDimRelationships.map(r => `${{r.from_table}}-${{r.to_table}}`));

                    return this.sortedRelationships.filter(rel => {{
                        const key = `${{rel.from_table}}-${{rel.to_table}}`;
                        return !factToDim.has(key) && !dimToDim.has(key);
                    }});
                }},

                filteredColumnsForDependency() {{
                    const columnsByTable = {{}};
                    const tables = this.modelData.tables || [];
                    const query = this.columnSearchQuery.toLowerCase();

                    tables.forEach(table => {{
                        const matchingColumns = [];
                        (table.columns || []).forEach(column => {{
                            const key = `${{table.name}}[${{column.name}}]`;
                            if (!query || column.name.toLowerCase().includes(query) || table.name.toLowerCase().includes(query)) {{
                                matchingColumns.push({{
                                    key: key,
                                    name: column.name,
                                    table: table.name
                                }});
                            }}
                        }});

                        if (matchingColumns.length > 0) {{
                            columnsByTable[table.name] = matchingColumns;
                        }}
                    }});

                    return columnsByTable;
                }},

                currentColumnDependencies() {{
                    if (!this.selectedColumnKey) {{
                        return {{ usedByMeasures: [], usedByFieldParams: [], visualUsage: [], filterUsage: [] }};
                    }}

                    const deps = this.dependencies;
                    const key = this.selectedColumnKey;

                    const usedByMeasures = deps.column_to_measure?.[key] || [];
                    const usedByFieldParams = deps.column_to_field_params?.[key] || [];
                    const visualUsage = this.findColumnInVisuals(key);
                    const filterUsage = this.findColumnInFilters(key);

                    return {{ usedByMeasures, usedByFieldParams, visualUsage, filterUsage }};
                }},

                filteredCommands() {{
                    const query = this.commandQuery.toLowerCase();
                    if (!query) return this.commands;

                    return this.commands.filter(cmd =>
                        cmd.name.toLowerCase().includes(query) ||
                        cmd.description.toLowerCase().includes(query)
                    );
                }},

                unusedMeasuresByFolder() {{
                    const folders = {{}};
                    const tables = this.modelData.tables || [];
                    const unusedSet = new Set(this.dependencies.unused_measures || []);

                    tables.forEach(table => {{
                        (table.measures || []).forEach(measure => {{
                            const fullName = `${{table.name}}[${{measure.name}}]`;
                            if (unusedSet.has(fullName)) {{
                                const folder = measure.display_folder || 'No Folder';
                                if (!folders[folder]) {{
                                    folders[folder] = [];
                                }}
                                folders[folder].push(fullName);
                            }}
                        }});
                    }});

                    // Sort folders alphabetically
                    const sortedFolders = {{}};
                    Object.keys(folders).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sortedFolders[key] = folders[key];
                    }});

                    return sortedFolders;
                }},

                unusedColumnsByTable() {{
                    const tables = {{}};
                    const unusedSet = new Set(this.dependencies.unused_columns || []);

                    (this.modelData.tables || []).forEach(table => {{
                        (table.columns || []).forEach(column => {{
                            const fullName = `${{table.name}}[${{column.name}}]`;
                            if (unusedSet.has(fullName)) {{
                                if (!tables[table.name]) {{
                                    tables[table.name] = [];
                                }}
                                tables[table.name].push(fullName);
                            }}
                        }});
                    }});

                    // Sort tables alphabetically
                    const sortedTables = {{}};
                    Object.keys(tables).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sortedTables[key] = tables[key];
                    }});

                    return sortedTables;
                }},

                allMeasuresMatrix() {{
                    const measures = [];
                    // Build case-insensitive set of unused measures
                    const unusedSet = new Set((this.dependencies.unused_measures || []).map(m => m.toLowerCase()));
                    const tables = this.modelData.tables || [];

                    tables.forEach(table => {{
                        (table.measures || []).forEach(measure => {{
                            const fullName = `${{table.name}}[${{measure.name}}]`;
                            const fullNameLower = fullName.toLowerCase();
                            measures.push({{
                                table: table.name,
                                name: measure.name,
                                fullName: fullName,
                                displayFolder: measure.display_folder || '',
                                isUsed: !unusedSet.has(fullNameLower)
                            }});
                        }});
                    }});

                    // Sort by display folder, then by name
                    return measures.sort((a, b) => {{
                        const folderCompare = (a.displayFolder || '').localeCompare(b.displayFolder || '');
                        if (folderCompare !== 0) return folderCompare;
                        return a.name.localeCompare(b.name);
                    }});
                }},

                filteredMeasuresMatrix() {{
                    const all = this.allMeasuresMatrix;
                    if (this.usageMatrixFilter === 'used') {{
                        return all.filter(m => m.isUsed);
                    }} else if (this.usageMatrixFilter === 'unused') {{
                        return all.filter(m => !m.isUsed);
                    }}
                    return all;
                }},

                filteredMeasuresGroupedByFolder() {{
                    const grouped = {{}};
                    this.filteredMeasuresMatrix.forEach(measure => {{
                        const folder = measure.displayFolder || 'No Folder';
                        if (!grouped[folder]) {{
                            grouped[folder] = [];
                        }}
                        grouped[folder].push(measure);
                    }});
                    // Sort folders
                    const sorted = {{}};
                    Object.keys(grouped).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sorted[key] = grouped[key];
                    }});
                    return sorted;
                }},

                allColumnsMatrix() {{
                    const columns = [];
                    // Build case-insensitive set of unused columns
                    const unusedSet = new Set((this.dependencies.unused_columns || []).map(c => c.toLowerCase()));
                    const tables = this.modelData.tables || [];

                    tables.forEach(table => {{
                        (table.columns || []).forEach(column => {{
                            const fullName = `${{table.name}}[${{column.name}}]`;
                            const fullNameLower = fullName.toLowerCase();
                            columns.push({{
                                table: table.name,
                                name: column.name,
                                fullName: fullName,
                                isUsed: !unusedSet.has(fullNameLower)
                            }});
                        }});
                    }});

                    // Sort by table, then by name
                    return columns.sort((a, b) => {{
                        const tableCompare = a.table.localeCompare(b.table);
                        if (tableCompare !== 0) return tableCompare;
                        return a.name.localeCompare(b.name);
                    }});
                }},

                filteredColumnsMatrix() {{
                    const all = this.allColumnsMatrix;
                    if (this.usageMatrixFilter === 'used') {{
                        return all.filter(c => c.isUsed);
                    }} else if (this.usageMatrixFilter === 'unused') {{
                        return all.filter(c => !c.isUsed);
                    }}
                    return all;
                }},

                filteredColumnsGroupedByTable() {{
                    const grouped = {{}};
                    this.filteredColumnsMatrix.forEach(column => {{
                        const table = column.table || 'Unknown Table';
                        if (!grouped[table]) {{
                            grouped[table] = [];
                        }}
                        grouped[table].push(column);
                    }});
                    // Sort tables
                    const sorted = {{}};
                    Object.keys(grouped).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sorted[key] = grouped[key];
                    }});
                    return sorted;
                }},

                fieldParametersList() {{
                    const fieldParams = [];

                    // Build field_param_to_columns from column_to_field_params (reverse mapping)
                    const columnToFieldParams = this.dependencies.column_to_field_params || {{}};
                    const fieldParamToColumns = {{}};

                    // Reverse the mapping: column -> [field params] to field_param -> [columns]
                    Object.entries(columnToFieldParams).forEach(([columnKey, fpTables]) => {{
                        (fpTables || []).forEach(fpTable => {{
                            if (!fieldParamToColumns[fpTable]) {{
                                fieldParamToColumns[fpTable] = [];
                            }}
                            if (!fieldParamToColumns[fpTable].includes(columnKey)) {{
                                fieldParamToColumns[fpTable].push(columnKey);
                            }}
                        }});
                    }});

                    // Now build the list from the reversed mapping
                    Object.keys(fieldParamToColumns).forEach(fpTable => {{
                        const columns = fieldParamToColumns[fpTable] || [];
                        fieldParams.push({{
                            name: fpTable,
                            table: fpTable,
                            fullName: fpTable,
                            columns: columns
                        }});
                    }});

                    // Sort by table name
                    return fieldParams.sort((a, b) => a.name.localeCompare(b.name));
                }},

                // Measure Chains - Get all measures with chain info
                allMeasuresWithChainInfo() {{
                    const measures = [];
                    const tables = this.modelData.tables || [];
                    const measureToMeasure = this.dependencies.measure_to_measure || {{}};

                    // Build reverse lookup: which measures USE this measure
                    const usedByMap = {{}};
                    Object.keys(measureToMeasure).forEach(measureName => {{
                        const deps = measureToMeasure[measureName];
                        deps.forEach(dep => {{
                            if (!usedByMap[dep]) usedByMap[dep] = [];
                            usedByMap[dep].push(measureName);
                        }});
                    }});

                    tables.forEach(table => {{
                        (table.measures || []).forEach(measure => {{
                            const fullName = `${{table.name}}[${{measure.name}}]`;
                            const deps = measureToMeasure[fullName] || [];
                            const usedBy = usedByMap[fullName] || [];

                            // Calculate chain depth
                            const chainDepth = this.calculateChainDepth(fullName, measureToMeasure, new Set());

                            // Check if used in visuals
                            const visualUsage = this.getMeasureVisualUsage(fullName);

                            measures.push({{
                                name: measure.name,
                                table: table.name,
                                fullName: fullName,
                                displayFolder: measure.display_folder || 'No Folder',
                                isBase: deps.length === 0,
                                chainDepth: chainDepth,
                                usedByCount: usedBy.length,
                                usedInVisuals: visualUsage.length > 0,
                                visualCount: visualUsage.length
                            }});
                        }});
                    }});

                    return measures;
                }},

                filteredChainMeasuresByFolder() {{
                    const query = this.chainSearchQuery.toLowerCase();
                    let filtered = this.allMeasuresWithChainInfo;

                    if (query) {{
                        filtered = filtered.filter(m =>
                            m.name.toLowerCase().includes(query) ||
                            m.table.toLowerCase().includes(query) ||
                            m.displayFolder.toLowerCase().includes(query)
                        );
                    }}

                    // Group by folder
                    const grouped = {{}};
                    filtered.forEach(measure => {{
                        const folder = measure.displayFolder;
                        if (!grouped[folder]) {{
                            grouped[folder] = [];
                        }}
                        grouped[folder].push(measure);
                    }});

                    // Sort folders and measures within folders
                    const sortedFolders = {{}};
                    Object.keys(grouped).sort((a, b) => a.localeCompare(b)).forEach(key => {{
                        sortedFolders[key] = grouped[key].sort((a, b) => a.name.localeCompare(b.name));
                    }});

                    return sortedFolders;
                }},

                filteredChainMeasures() {{
                    const query = this.chainSearchQuery.toLowerCase();
                    if (!query) return this.allMeasuresWithChainInfo;
                    return this.allMeasuresWithChainInfo.filter(m =>
                        m.name.toLowerCase().includes(query) ||
                        m.table.toLowerCase().includes(query)
                    );
                }},

                currentChain() {{
                    if (!this.selectedChainMeasure) return {{}};

                    const measureToMeasure = this.dependencies.measure_to_measure || {{}};
                    const visualUsage = this.getMeasureVisualUsage(this.selectedChainMeasure);

                    // Get dependencies (what this measure uses)
                    const dependencies = measureToMeasure[this.selectedChainMeasure] || [];

                    // Build complete UPWARD chain (who uses this measure, and who uses those, etc.)
                    const buildUsedByChain = (measureName, visited = new Set()) => {{
                        if (visited.has(measureName)) return []; // Prevent circular references
                        visited.add(measureName);

                        const directUsers = [];
                        Object.keys(measureToMeasure).forEach(otherMeasure => {{
                            const deps = measureToMeasure[otherMeasure];
                            if (deps.includes(measureName)) {{
                                // This measure uses our target measure
                                const childChain = buildUsedByChain(otherMeasure, new Set(visited));
                                directUsers.push({{
                                    measure: otherMeasure,
                                    usedBy: childChain
                                }});
                            }}
                        }});

                        return directUsers;
                    }};

                    const usedByChain = buildUsedByChain(this.selectedChainMeasure);

                    // Also get flat list for count
                    const getAllUsedBy = (chain) => {{
                        const all = [];
                        chain.forEach(item => {{
                            all.push(item.measure);
                            if (item.usedBy && item.usedBy.length > 0) {{
                                all.push(...getAllUsedBy(item.usedBy));
                            }}
                        }});
                        return all;
                    }};

                    const allUsedBy = getAllUsedBy(usedByChain);

                    return {{
                        dependencies: dependencies,
                        usedByChain: usedByChain,
                        usedByCount: allUsedBy.length,
                        visualUsage: visualUsage
                    }};
                }},

                // Visuals Analysis - Get pages with visuals
                visualAnalysisPages() {{
                    if (!this.reportData || !this.reportData.pages) return [];

                    return this.reportData.pages.map(page => ({{
                        name: page.name || page.display_name,
                        visualCount: (page.visuals || []).filter(v => {{
                            const type = v.visual_type || v.type;
                            return !this.isVisualTypeFiltered(type);
                        }}).length
                    }})).filter(p => p.visualCount > 0)
                      .sort((a, b) => a.name.localeCompare(b.name));
                }},

                visualsOnSelectedPage() {{
                    if (!this.selectedVisualPage || !this.reportData || !this.reportData.pages) return [];

                    const page = this.reportData.pages.find(p =>
                        (p.name || p.display_name) === this.selectedVisualPage
                    );

                    if (!page || !page.visuals) return [];

                    const visuals = [];
                    page.visuals.forEach((visual, idx) => {{
                        const type = visual.visual_type || visual.type || 'Unknown';
                        if (this.isVisualTypeFiltered(type)) return;

                        // Get visual ID and name with better fallbacks
                        const vId = visual.visualId || visual.visual_id || visual.id || `visual-${{idx}}`;
                        const vName = visual.name || visual.visual_name || visual.title || `Visual ${{idx + 1}}`;

                        // Count measures in this visual
                        let measureCount = 0;
                        const measureUsage = this.dependencies.measure_to_visual || {{}};

                        // Method 1: Use mapping
                        Object.keys(measureUsage).forEach(measureName => {{
                            const visualIds = measureUsage[measureName] || [];
                            if (visualIds.includes(vId)) {{
                                measureCount++;
                            }}
                        }});

                        // Method 2: If no measures found, search visual JSON
                        if (measureCount === 0) {{
                            const visualJson = JSON.stringify(visual);
                            (this.modelData.tables || []).forEach(table => {{
                                (table.measures || []).forEach(measure => {{
                                    if (visualJson.includes(measure.name)) {{
                                        measureCount++;
                                    }}
                                }});
                            }});
                        }}

                        visuals.push({{
                            visualId: vId,
                            visualType: type,
                            visualName: vName,
                            measureCount: measureCount
                        }});
                    }});

                    return visuals;
                }},

                currentVisualAnalysis() {{
                    if (!this.selectedVisualId || !this.selectedVisualPage) return null;

                    const page = this.reportData.pages.find(p =>
                        (p.name || p.display_name) === this.selectedVisualPage
                    );
                    if (!page) return null;

                    const visual = (page.visuals || []).find(v =>
                        (v.visualId || v.visual_id || v.id) === this.selectedVisualId
                    );
                    if (!visual) return null;

                    // Find which measures are used in this visual
                    const measureUsage = this.dependencies.measure_to_visual || {{}};
                    const measureToMeasure = this.dependencies.measure_to_measure || {{}};

                    let usedMeasures = [];

                    // Method 1: Use measure_to_visual mapping
                    Object.keys(measureUsage).forEach(measureName => {{
                        const visualIds = measureUsage[measureName] || [];
                        if (visualIds.includes(this.selectedVisualId)) {{
                            usedMeasures.push(measureName);
                        }}
                    }});

                    // Method 2: If no measures found, search visual JSON for measure references
                    if (usedMeasures.length === 0) {{
                        const visualJson = JSON.stringify(visual);
                        const allMeasures = [];

                        // Get all measures from model
                        (this.modelData.tables || []).forEach(table => {{
                            (table.measures || []).forEach(measure => {{
                                allMeasures.push({{
                                    name: measure.name,
                                    fullName: `${{table.name}}[${{measure.name}}]`
                                }});
                            }});
                        }});

                        // Check which measures appear in the visual JSON
                        allMeasures.forEach(m => {{
                            if (visualJson.includes(m.name)) {{
                                usedMeasures.push(m.fullName);
                            }}
                        }});
                    }}

                    // Analyze each measure's dependencies
                    const topMeasures = usedMeasures.map(measureName => {{
                        const match = measureName.match(/^(.+?)\\[(.+?)\\]$/);
                        if (!match) return null;

                        const [, table, name] = match;
                        const deps = measureToMeasure[measureName] || [];

                        return {{
                            name: name,
                            table: table,
                            fullName: measureName,
                            dependencies: deps.map(depName => {{
                                const depMatch = depName.match(/^(.+?)\\[(.+?)\\]$/);
                                if (!depMatch) return null;
                                const [, depTable, depMeasureName] = depMatch;
                                const depDeps = measureToMeasure[depName] || [];
                                return {{
                                    name: depMeasureName,
                                    table: depTable,
                                    fullName: depName,
                                    dependencies: depDeps.length > 0 ? depDeps.map(d => ({{
                                        fullName: d,
                                        name: d.match(/\\[([^\\]]+)\\]$/)?.[1] || d,
                                        table: d.match(/^(.+?)\\[/)?.[1] || ''
                                    }})) : []
                                }};
                            }}).filter(Boolean)
                        }};
                    }}).filter(Boolean);

                    const totalMeasures = topMeasures.length;
                    const directDeps = topMeasures.reduce((sum, m) => sum + m.dependencies.length, 0);
                    const baseMeasures = topMeasures.filter(m => m.dependencies.length === 0).length;

                    return {{
                        visualType: visual.visual_type || visual.type || 'Unknown',
                        visualName: visual.name || visual.visual_name || visual.title || 'Unnamed Visual',
                        topMeasures: topMeasures,
                        summary: {{
                            totalMeasures: totalMeasures,
                            directDeps: directDeps,
                            baseMeasures: baseMeasures
                        }}
                    }};
                }},

                // Enhanced Analysis - BPA
                bpaViolations() {{
                    return this.enhancedData?.analyses?.bpa?.violations || [];
                }},

                bpaViolationsCount() {{
                    return this.bpaViolations.length;
                }},

                bpaTotalViolations() {{
                    return this.bpaViolations.length;
                }},

                bpaErrorCount() {{
                    return this.bpaViolations.filter(v => v.severity === 'ERROR').length;
                }},

                bpaWarningCount() {{
                    return this.bpaViolations.filter(v => v.severity === 'WARNING').length;
                }},

                bpaInfoCount() {{
                    return this.bpaViolations.filter(v => v.severity === 'INFO').length;
                }},

                bpaCategoryBreakdown() {{
                    const counts = {{}};
                    this.bpaViolations.forEach(v => {{
                        counts[v.category] = (counts[v.category] || 0) + 1;
                    }});
                    return counts;
                }},

                bpaCategories() {{
                    return [...new Set(this.bpaViolations.map(v => v.category))];
                }},

                filteredBpaViolations() {{
                    return this.bpaViolations.filter(v => {{
                        const severityMatch = this.bpaSeverityFilter === 'all' || v.severity === this.bpaSeverityFilter;
                        const categoryMatch = this.bpaCategoryFilter === 'all' || v.category === this.bpaCategoryFilter;
                        return severityMatch && categoryMatch;
                    }});
                }},

                // Group violations by object type
                bpaObjectTypes() {{
                    const types = [...new Set(this.filteredBpaViolations.map(v => v.object_type || 'Unknown'))];
                    // Sort with common types first
                    const order = ['Measure', 'Column', 'Table', 'Relationship', 'Model', 'Unknown'];
                    return types.sort((a, b) => {{
                        const aIndex = order.indexOf(a);
                        const bIndex = order.indexOf(b);
                        if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
                        if (aIndex === -1) return 1;
                        if (bIndex === -1) return -1;
                        return aIndex - bIndex;
                    }});
                }},

                // Group violations by object type and category
                bpaViolationsByObjectType() {{
                    const groups = {{}};
                    this.filteredBpaViolations.forEach(v => {{
                        const type = v.object_type || 'Unknown';
                        if (!groups[type]) groups[type] = [];
                        groups[type].push(v);
                    }});
                    return groups;
                }},

                // Ordered categories with Maintenance last
                bpaOrderedCategories() {{
                    const categories = [...new Set(this.filteredBpaViolations.map(v => v.category))];
                    const maintenanceIndex = categories.indexOf('Maintenance');
                    if (maintenanceIndex > -1) {{
                        categories.splice(maintenanceIndex, 1);
                        categories.push('Maintenance');
                    }}
                    return categories;
                }},

                // Group violations by object type and category
                bpaViolationsByObjectAndCategory() {{
                    const groups = {{}};
                    this.filteredBpaViolations.forEach(v => {{
                        const type = v.object_type || 'Unknown';
                        const category = v.category;
                        if (!groups[type]) groups[type] = {{}};
                        if (!groups[type][category]) groups[type][category] = [];
                        groups[type][category].push(v);
                    }});
                    return groups;
                }},

                // Enhanced Analysis - Data Quality
                dataTypeIssues() {{
                    return this.enhancedData?.analyses?.data_types?.type_issues || [];
                }},

                dataQualityIssuesCount() {{
                    return this.dataTypeIssues.length + this.cardinalityWarnings.length;
                }},

                dataTypeHighImpactCount() {{
                    return this.dataTypeIssues.filter(i => i.impact === 'HIGH').length;
                }},

                dataTypeSummary() {{
                    const summary = this.enhancedData?.analyses?.data_types?.type_summary || {{}};
                    // Filter out empty or null type names
                    const filtered = {{}};
                    Object.keys(summary).forEach(key => {{
                        if (key && key.trim() !== '') {{
                            filtered[key] = summary[key];
                        }}
                    }});
                    return filtered;
                }},

                totalDataTypeCount() {{
                    return Object.values(this.dataTypeSummary).reduce((sum, count) => sum + count, 0) || 1;
                }},

                cardinalityWarnings() {{
                    return this.enhancedData?.analyses?.cardinality?.cardinality_warnings || [];
                }},

                filteredDataTypeIssues() {{
                    return this.dataTypeIssues.filter(issue => {{
                        return this.dataTypeImpactFilter === 'all' || issue.impact === this.dataTypeImpactFilter;
                    }});
                }},

                // Naming Conventions
                namingViolations() {{
                    return this.enhancedData?.analyses?.naming_conventions?.violations || [];
                }},

                namingViolationsCount() {{
                    return this.namingViolations.length;
                }},

                namingSummary() {{
                    return this.enhancedData?.analyses?.naming_conventions?.summary || {{}};
                }},

                filteredNamingViolations() {{
                    return this.namingViolations.filter(violation => {{
                        const severityMatch = this.namingSeverityFilter === 'all' || violation.severity === this.namingSeverityFilter;
                        const typeMatch = this.namingTypeFilter === 'all' || violation.type === this.namingTypeFilter;
                        return severityMatch && typeMatch;
                    }});
                }},

                // Perspectives
                perspectivesData() {{
                    return this.enhancedData?.analyses?.perspectives || {{ has_perspectives: false }};
                }},

                perspectivesCount() {{
                    return this.perspectivesData.perspective_count || 0;
                }},

                sortedPages() {{
                    if (!this.reportData || !this.reportData.pages) {{
                        return [];
                    }}
                    // Sort pages by display_name or ordinal
                    return [...this.reportData.pages].sort((a, b) => {{
                        const nameA = a.display_name || a.name || '';
                        const nameB = b.display_name || b.name || '';
                        return nameA.localeCompare(nameB);
                    }});
                }}
            }},

            watch: {{
                relationshipGraphLayout(newLayout) {{
                    if (newLayout !== 'list') {{
                        this.$nextTick(() => {{
                            this.renderRelationshipGraph();
                        }});
                    }}
                }},

                modelSubTab(newTab) {{
                    if (newTab === 'relationships' && this.relationshipGraphLayout !== 'list') {{
                        this.$nextTick(() => {{
                            this.renderRelationshipGraph();
                        }});
                    }}
                }}
            }},

            methods: {{
                tabClass(tab) {{
                    return this.activeTab === tab
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300';
                }},

                toggleDarkMode() {{
                    this.darkMode = !this.darkMode;
                    document.body.classList.toggle('dark-mode');
                }},

                exportToCSV() {{
                    const tables = this.modelData.tables || [];
                    let csv = 'Table,Type,Column/Measure,Data Type,Hidden\\n';

                    tables.forEach(table => {{
                        (table.columns || []).forEach(col => {{
                            csv += `"${{table.name}}",Column,"${{col.name}}","${{col.data_type}}",${{col.is_hidden}}\\n`;
                        }});
                        (table.measures || []).forEach(measure => {{
                            csv += `"${{table.name}}",Measure,"${{measure.name}}","-",${{measure.is_hidden}}\\n`;
                        }});
                    }});

                    const blob = new Blob([csv], {{ type: 'text/csv' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'pbip_model_export.csv';
                    a.click();
                }},

                exportToJSON() {{
                    const dataStr = JSON.stringify(pbipData, null, 2);
                    const blob = new Blob([dataStr], {{ type: 'application/json' }});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'pbip_full_export.json';
                    a.click();
                }},

                // Relationship Graph Rendering Methods
                // Add these methods to the Vue app's methods section
                
                renderRelationshipGraph() {{
                    const container = document.getElementById('graph-container');
                    if (!container) return;
                
                    // Clear previous graph
                    container.innerHTML = '';
                
                    const relationships = this.sortedRelationships;
                    if (!relationships || relationships.length === 0) return;
                
                    // Build node and link data
                    const tables = new Set();
                    relationships.forEach(rel => {{
                        tables.add(rel.from_table);
                        tables.add(rel.to_table);
                    }});
                
                    const nodes = Array.from(tables).map(name => ({{
                        id: name,
                        type: this.getTableType(name)
                    }}));
                
                    const links = relationships.map(rel => ({{
                        source: rel.from_table,
                        target: rel.to_table,
                        active: rel.is_active !== false,
                        from_column: rel.from_column,
                        to_column: rel.to_column,
                        cardinality: this.formatCardinality(rel),
                        direction: this.formatCrossFilterDirection(rel),
                        relType: this.getRelationshipType(rel)
                    }}));
                
                    // Render based on selected layout
                    if (this.relationshipGraphLayout === 'tree') {{
                        this.renderTreeLayout(container, nodes, links);
                    }} else if (this.relationshipGraphLayout === 'dagre') {{
                        this.renderDagreLayout(container, nodes, links);
                    }} else if (this.relationshipGraphLayout === 'force') {{
                        this.renderForceLayout(container, nodes, links);
                    }}
                }},
                
                getTableType(tableName) {{
                    const lower = tableName.toLowerCase();
                    if (lower.startsWith('f ') || lower.startsWith('fact')) return 'fact';
                    if (lower.startsWith('d ') || lower.startsWith('dim')) return 'dim';
                    return 'other';
                }},
                
                getRelationshipType(rel) {{
                    const fromType = this.getTableType(rel.from_table);
                    const toType = this.getTableType(rel.to_table);
                    if (fromType === 'fact' && toType === 'dim') return 'fact-to-dim';
                    if (fromType === 'dim' && toType === 'dim') return 'dim-to-dim';
                    return 'other';
                }},
                
                renderTreeLayout(container, nodes, links) {{
                    const width = container.clientWidth || 800;
                    const height = 600;
                
                    // Build hierarchy from relationships
                    const root = this.buildHierarchy(nodes, links);
                
                    const treeLayout = d3.tree()
                        .size([height - 100, width - 200])
                        .separation((a, b) => (a.parent === b.parent ? 1 : 1.5));
                
                    const hierarchy = d3.hierarchy(root);
                    const treeData = treeLayout(hierarchy);
                
                    const svg = d3.select(container)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height);
                
                    const g = svg.append('g')
                        .attr('transform', 'translate(100,50)');
                
                    // Links
                    g.selectAll('.link')
                        .data(treeData.links())
                        .join('path')
                        .attr('class', 'relationship-link')
                        .attr('d', d3.linkHorizontal()
                            .x(d => d.y)
                            .y(d => d.x))
                        .attr('stroke', '#94a3b8')
                        .attr('stroke-width', 2)
                        .attr('fill', 'none');
                
                    // Nodes
                    const node = g.selectAll('.node')
                        .data(treeData.descendants())
                        .join('g')
                        .attr('class', d => `graph-node ${{d.data.type}}-table`)
                        .attr('transform', d => `translate(${{d.y}},${{d.x}})`);
                
                    node.append('circle')
                        .attr('r', 8)
                        .attr('fill', d => {{
                            if (d.data.type === 'fact') return '#3b82f6';
                            if (d.data.type === 'dim') return '#10b981';
                            return '#94a3b8';
                        }})
                        .attr('stroke', '#1f2937')
                        .attr('stroke-width', 2);
                
                    node.append('text')
                        .attr('dy', -15)
                        .attr('text-anchor', 'middle')
                        .attr('fill', '#1f2937')
                        .style('font-size', '12px')
                        .style('font-weight', 'bold')
                        .text(d => d.data.name || d.data.id);
                }},
                
                buildHierarchy(nodes, links) {{
                    // Find root nodes (fact tables or tables with no incoming links)
                    const incoming = new Set();
                    links.forEach(l => incoming.add(l.target));
                
                    const roots = nodes.filter(n => !incoming.has(n.id) || n.type === 'fact');
                    if (roots.length === 0 && nodes.length > 0) roots.push(nodes[0]);
                
                    const buildTree = (nodeId, visited = new Set()) => {{
                        if (visited.has(nodeId)) return null;
                        visited.add(nodeId);
                
                        const node = nodes.find(n => n.id === nodeId);
                        const children = links
                            .filter(l => l.source === nodeId)
                            .map(l => buildTree(l.target, visited))
                            .filter(c => c !== null);
                
                        return {{
                            name: nodeId,
                            id: nodeId,
                            type: node?.type || 'other',
                            children: children.length > 0 ? children : null
                        }};
                    }};
                
                    if (roots.length === 1) {{
                        return buildTree(roots[0].id);
                    }} else {{
                        return {{
                            name: 'Model',
                            id: '__root__',
                            type: 'root',
                            children: roots.map(r => buildTree(r.id))
                        }};
                    }}
                }},
                
                renderDagreLayout(container, nodes, links) {{
                    const width = container.clientWidth || 800;
                    const height = 600;
                
                    // Create dagre graph
                    const g = new dagre.graphlib.Graph();
                    g.setGraph({{ rankdir: 'LR', nodesep: 70, ranksep: 100 }});
                    g.setDefaultEdgeLabel(() => ({{}}));
                
                    // Add nodes
                    nodes.forEach(node => {{
                        g.setNode(node.id, {{ label: node.id, width: 120, height: 40 }});
                    }});
                
                    // Add edges
                    links.forEach(link => {{
                        g.setEdge(link.source, link.target);
                    }});
                
                    // Compute layout
                    dagre.layout(g);
                
                    const svg = d3.select(container)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height);
                
                    const svgGroup = svg.append('g')
                        .attr('transform', 'translate(20,20)');
                
                    // Draw edges
                    g.edges().forEach(e => {{
                        const edge = g.edge(e);
                        const link = links.find(l => l.source === e.v && l.target === e.w);
                
                        svgGroup.append('path')
                            .attr('class', `relationship-link ${{link?.active ? 'active' : 'inactive'}} ${{link?.relType}}`)
                            .attr('d', () => {{
                                const points = edge.points;
                                return d3.line()
                                    .x(d => d.x)
                                    .y(d => d.y)
                                    (points);
                            }})
                            .attr('marker-end', 'url(#arrowhead)');
                    }});
                
                    // Define arrow marker
                    svg.append('defs').append('marker')
                        .attr('id', 'arrowhead')
                        .attr('viewBox', '-0 -5 10 10')
                        .attr('refX', 8)
                        .attr('refY', 0)
                        .attr('orient', 'auto')
                        .attr('markerWidth', 6)
                        .attr('markerHeight', 6)
                        .append('svg:path')
                        .attr('d', 'M 0,-5 L 10,0 L 0,5')
                        .attr('fill', '#94a3b8');
                
                    // Draw nodes
                    g.nodes().forEach(v => {{
                        const node = g.node(v);
                        const nodeData = nodes.find(n => n.id === v);
                
                        const nodeGroup = svgGroup.append('g')
                            .attr('class', `graph-node ${{nodeData.type}}-table`)
                            .attr('transform', `translate(${{node.x}},${{node.y}})`);
                
                        nodeGroup.append('rect')
                            .attr('x', -60)
                            .attr('y', -20)
                            .attr('width', 120)
                            .attr('height', 40)
                            .attr('rx', 5)
                            .attr('fill', () => {{
                                if (nodeData.type === 'fact') return '#3b82f6';
                                if (nodeData.type === 'dim') return '#10b981';
                                return '#94a3b8';
                            }})
                            .attr('stroke', '#1f2937')
                            .attr('stroke-width', 2);
                
                        nodeGroup.append('text')
                            .attr('text-anchor', 'middle')
                            .attr('dy', 5)
                            .attr('fill', 'white')
                            .style('font-size', '12px')
                            .style('font-weight', 'bold')
                            .text(node.label);
                    }});
                }},
                
                renderForceLayout(container, nodes, links) {{
                    const width = container.clientWidth || 800;
                    const height = 600;
                
                    // Convert links to use node objects
                    const nodeMap = new Map(nodes.map(n => [n.id, {{ ...n }}]));
                    const forceLinks = links.map(l => ({{
                        source: nodeMap.get(l.source),
                        target: nodeMap.get(l.target),
                        ...l
                    }}));
                
                    const svg = d3.select(container)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height);
                
                    const simulation = d3.forceSimulation(Array.from(nodeMap.values()))
                        .force('link', d3.forceLink(forceLinks).id(d => d.id).distance(100))
                        .force('charge', d3.forceManyBody().strength(-300))
                        .force('center', d3.forceCenter(width / 2, height / 2))
                        .force('collision', d3.forceCollide().radius(50));
                
                    // Links
                    const link = svg.append('g')
                        .selectAll('line')
                        .data(forceLinks)
                        .join('line')
                        .attr('class', d => `relationship-link ${{d.active ? 'active' : 'inactive'}} ${{d.relType}}`)
                        .attr('stroke-width', d => d.active ? 3 : 2);
                
                    // Nodes
                    const node = svg.append('g')
                        .selectAll('g')
                        .data(Array.from(nodeMap.values()))
                        .join('g')
                        .attr('class', d => `graph-node ${{d.type}}-table`)
                        .call(d3.drag()
                            .on('start', dragstarted)
                            .on('drag', dragged)
                            .on('end', dragended));
                
                    node.append('circle')
                        .attr('r', 20)
                        .attr('fill', d => {{
                            if (d.type === 'fact') return '#3b82f6';
                            if (d.type === 'dim') return '#10b981';
                            return '#94a3b8';
                        }})
                        .attr('stroke', '#1f2937')
                        .attr('stroke-width', 2);
                
                    node.append('text')
                        .attr('dy', -25)
                        .attr('text-anchor', 'middle')
                        .attr('fill', '#1f2937')
                        .style('font-size', '12px')
                        .style('font-weight', 'bold')
                        .text(d => d.id);
                
                    simulation.on('tick', () => {{
                        link
                            .attr('x1', d => d.source.x)
                            .attr('y1', d => d.source.y)
                            .attr('x2', d => d.target.x)
                            .attr('y2', d => d.target.y);
                
                        node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
                    }});
                
                    function dragstarted(event) {{
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        event.subject.fx = event.subject.x;
                        event.subject.fy = event.subject.y;
                    }}
                
                    function dragged(event) {{
                        event.subject.fx = event.x;
                        event.subject.fy = event.y;
                    }}
                
                    function dragended(event) {{
                        if (!event.active) simulation.alphaTarget(0);
                        event.subject.fx = null;
                        event.subject.fy = null;
                    }}
                }},

                // Relationship Graph Rendering Methods
                // Add these methods to the Vue app's methods section
                
                renderRelationshipGraph() {{
                    const container = document.getElementById('graph-container');
                    if (!container) return;
                
                    // Clear previous graph
                    container.innerHTML = '';
                
                    const relationships = this.sortedRelationships;
                    if (!relationships || relationships.length === 0) return;
                
                    // Build node and link data
                    const tables = new Set();
                    relationships.forEach(rel => {{
                        tables.add(rel.from_table);
                        tables.add(rel.to_table);
                    }});
                
                    const nodes = Array.from(tables).map(name => ({{
                        id: name,
                        type: this.getTableType(name)
                    }}));
                
                    const links = relationships.map(rel => ({{
                        source: rel.from_table,
                        target: rel.to_table,
                        active: rel.is_active !== false,
                        from_column: rel.from_column,
                        to_column: rel.to_column,
                        cardinality: this.formatCardinality(rel),
                        direction: this.formatCrossFilterDirection(rel),
                        relType: this.getRelationshipType(rel)
                    }}));
                
                    // Render based on selected layout
                    if (this.relationshipGraphLayout === 'tree') {{
                        this.renderTreeLayout(container, nodes, links);
                    }} else if (this.relationshipGraphLayout === 'dagre') {{
                        this.renderDagreLayout(container, nodes, links);
                    }} else if (this.relationshipGraphLayout === 'force') {{
                        this.renderForceLayout(container, nodes, links);
                    }}
                }},
                
                getTableType(tableName) {{
                    const lower = tableName.toLowerCase();
                    if (lower.startsWith('f ') || lower.startsWith('fact')) return 'fact';
                    if (lower.startsWith('d ') || lower.startsWith('dim')) return 'dim';
                    return 'other';
                }},
                
                getRelationshipType(rel) {{
                    const fromType = this.getTableType(rel.from_table);
                    const toType = this.getTableType(rel.to_table);
                    if (fromType === 'fact' && toType === 'dim') return 'fact-to-dim';
                    if (fromType === 'dim' && toType === 'dim') return 'dim-to-dim';
                    return 'other';
                }},
                
                renderTreeLayout(container, nodes, links) {{
                    const width = container.clientWidth || 800;
                    const height = 600;
                
                    // Build hierarchy from relationships
                    const root = this.buildHierarchy(nodes, links);
                
                    const treeLayout = d3.tree()
                        .size([height - 100, width - 200])
                        .separation((a, b) => (a.parent === b.parent ? 1 : 1.5));
                
                    const hierarchy = d3.hierarchy(root);
                    const treeData = treeLayout(hierarchy);
                
                    const svg = d3.select(container)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height);
                
                    const g = svg.append('g')
                        .attr('transform', 'translate(100,50)');
                
                    // Links
                    g.selectAll('.link')
                        .data(treeData.links())
                        .join('path')
                        .attr('class', 'relationship-link')
                        .attr('d', d3.linkHorizontal()
                            .x(d => d.y)
                            .y(d => d.x))
                        .attr('stroke', '#94a3b8')
                        .attr('stroke-width', 2)
                        .attr('fill', 'none');
                
                    // Nodes
                    const node = g.selectAll('.node')
                        .data(treeData.descendants())
                        .join('g')
                        .attr('class', d => `graph-node ${{d.data.type}}-table`)
                        .attr('transform', d => `translate(${{d.y}},${{d.x}})`);
                
                    node.append('circle')
                        .attr('r', 8)
                        .attr('fill', d => {{
                            if (d.data.type === 'fact') return '#3b82f6';
                            if (d.data.type === 'dim') return '#10b981';
                            return '#94a3b8';
                        }})
                        .attr('stroke', '#1f2937')
                        .attr('stroke-width', 2);
                
                    node.append('text')
                        .attr('dy', -15)
                        .attr('text-anchor', 'middle')
                        .attr('fill', '#1f2937')
                        .style('font-size', '12px')
                        .style('font-weight', 'bold')
                        .text(d => d.data.name || d.data.id);
                }},
                
                buildHierarchy(nodes, links) {{
                    // Find root nodes (fact tables or tables with no incoming links)
                    const incoming = new Set();
                    links.forEach(l => incoming.add(l.target));
                
                    const roots = nodes.filter(n => !incoming.has(n.id) || n.type === 'fact');
                    if (roots.length === 0 && nodes.length > 0) roots.push(nodes[0]);
                
                    const buildTree = (nodeId, visited = new Set()) => {{
                        if (visited.has(nodeId)) return null;
                        visited.add(nodeId);
                
                        const node = nodes.find(n => n.id === nodeId);
                        const children = links
                            .filter(l => l.source === nodeId)
                            .map(l => buildTree(l.target, visited))
                            .filter(c => c !== null);
                
                        return {{
                            name: nodeId,
                            id: nodeId,
                            type: node?.type || 'other',
                            children: children.length > 0 ? children : null
                        }};
                    }};
                
                    if (roots.length === 1) {{
                        return buildTree(roots[0].id);
                    }} else {{
                        return {{
                            name: 'Model',
                            id: '__root__',
                            type: 'root',
                            children: roots.map(r => buildTree(r.id))
                        }};
                    }}
                }},
                
                renderDagreLayout(container, nodes, links) {{
                    const width = container.clientWidth || 800;
                    const height = 600;
                
                    // Create dagre graph
                    const g = new dagre.graphlib.Graph();
                    g.setGraph({{ rankdir: 'LR', nodesep: 70, ranksep: 100 }});
                    g.setDefaultEdgeLabel(() => ({{}}));
                
                    // Add nodes
                    nodes.forEach(node => {{
                        g.setNode(node.id, {{ label: node.id, width: 120, height: 40 }});
                    }});
                
                    // Add edges
                    links.forEach(link => {{
                        g.setEdge(link.source, link.target);
                    }});
                
                    // Compute layout
                    dagre.layout(g);
                
                    const svg = d3.select(container)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height);
                
                    const svgGroup = svg.append('g')
                        .attr('transform', 'translate(20,20)');
                
                    // Draw edges
                    g.edges().forEach(e => {{
                        const edge = g.edge(e);
                        const link = links.find(l => l.source === e.v && l.target === e.w);
                
                        svgGroup.append('path')
                            .attr('class', `relationship-link ${{link?.active ? 'active' : 'inactive'}} ${{link?.relType}}`)
                            .attr('d', () => {{
                                const points = edge.points;
                                return d3.line()
                                    .x(d => d.x)
                                    .y(d => d.y)
                                    (points);
                            }})
                            .attr('marker-end', 'url(#arrowhead)');
                    }});
                
                    // Define arrow marker
                    svg.append('defs').append('marker')
                        .attr('id', 'arrowhead')
                        .attr('viewBox', '-0 -5 10 10')
                        .attr('refX', 8)
                        .attr('refY', 0)
                        .attr('orient', 'auto')
                        .attr('markerWidth', 6)
                        .attr('markerHeight', 6)
                        .append('svg:path')
                        .attr('d', 'M 0,-5 L 10,0 L 0,5')
                        .attr('fill', '#94a3b8');
                
                    // Draw nodes
                    g.nodes().forEach(v => {{
                        const node = g.node(v);
                        const nodeData = nodes.find(n => n.id === v);
                
                        const nodeGroup = svgGroup.append('g')
                            .attr('class', `graph-node ${{nodeData.type}}-table`)
                            .attr('transform', `translate(${{node.x}},${{node.y}})`);
                
                        nodeGroup.append('rect')
                            .attr('x', -60)
                            .attr('y', -20)
                            .attr('width', 120)
                            .attr('height', 40)
                            .attr('rx', 5)
                            .attr('fill', () => {{
                                if (nodeData.type === 'fact') return '#3b82f6';
                                if (nodeData.type === 'dim') return '#10b981';
                                return '#94a3b8';
                            }})
                            .attr('stroke', '#1f2937')
                            .attr('stroke-width', 2);
                
                        nodeGroup.append('text')
                            .attr('text-anchor', 'middle')
                            .attr('dy', 5)
                            .attr('fill', 'white')
                            .style('font-size', '12px')
                            .style('font-weight', 'bold')
                            .text(node.label);
                    }});
                }},
                
                renderForceLayout(container, nodes, links) {{
                    const width = container.clientWidth || 800;
                    const height = 600;
                
                    // Convert links to use node objects
                    const nodeMap = new Map(nodes.map(n => [n.id, {{ ...n }}]));
                    const forceLinks = links.map(l => ({{
                        source: nodeMap.get(l.source),
                        target: nodeMap.get(l.target),
                        ...l
                    }}));
                
                    const svg = d3.select(container)
                        .append('svg')
                        .attr('width', width)
                        .attr('height', height);
                
                    const simulation = d3.forceSimulation(Array.from(nodeMap.values()))
                        .force('link', d3.forceLink(forceLinks).id(d => d.id).distance(100))
                        .force('charge', d3.forceManyBody().strength(-300))
                        .force('center', d3.forceCenter(width / 2, height / 2))
                        .force('collision', d3.forceCollide().radius(50));
                
                    // Links
                    const link = svg.append('g')
                        .selectAll('line')
                        .data(forceLinks)
                        .join('line')
                        .attr('class', d => `relationship-link ${{d.active ? 'active' : 'inactive'}} ${{d.relType}}`)
                        .attr('stroke-width', d => d.active ? 3 : 2);
                
                    // Nodes
                    const node = svg.append('g')
                        .selectAll('g')
                        .data(Array.from(nodeMap.values()))
                        .join('g')
                        .attr('class', d => `graph-node ${{d.type}}-table`)
                        .call(d3.drag()
                            .on('start', dragstarted)
                            .on('drag', dragged)
                            .on('end', dragended));
                
                    node.append('circle')
                        .attr('r', 20)
                        .attr('fill', d => {{
                            if (d.type === 'fact') return '#3b82f6';
                            if (d.type === 'dim') return '#10b981';
                            return '#94a3b8';
                        }})
                        .attr('stroke', '#1f2937')
                        .attr('stroke-width', 2);
                
                    node.append('text')
                        .attr('dy', -25)
                        .attr('text-anchor', 'middle')
                        .attr('fill', '#1f2937')
                        .style('font-size', '12px')
                        .style('font-weight', 'bold')
                        .text(d => d.id);
                
                    simulation.on('tick', () => {{
                        link
                            .attr('x1', d => d.source.x)
                            .attr('y1', d => d.source.y)
                            .attr('x2', d => d.target.x)
                            .attr('y2', d => d.target.y);
                
                        node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
                    }});
                
                    function dragstarted(event) {{
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        event.subject.fx = event.subject.x;
                        event.subject.fy = event.subject.y;
                    }}
                
                    function dragged(event) {{
                        event.subject.fx = event.x;
                        event.subject.fy = event.y;
                    }}
                
                    function dragended(event) {{
                        if (!event.active) simulation.alphaTarget(0);
                        event.subject.fx = null;
                        event.subject.fy = null;
                    }}
                }},
                

                // Enhanced Analysis - Helper Methods
                bpaSeverityClass(severity) {{
                    if (severity === 'ERROR') return 'severity-badge--error';
                    if (severity === 'WARNING') return 'severity-badge--warning';
                    if (severity === 'INFO') return 'severity-badge--info';
                    return 'severity-badge--info';
                }},

                severityBadgeClass(severity) {{
                    if (severity === 'ERROR') return 'severity-badge--error';
                    if (severity === 'WARNING') return 'severity-badge--warning';
                    if (severity === 'INFO') return 'severity-badge--info';
                    return 'severity-badge--info';
                }},

                impactBadgeClass(impact) {{
                    if (impact === 'HIGH') return 'severity-badge--error';
                    if (impact === 'MEDIUM') return 'severity-badge--warning';
                    if (impact === 'LOW') return 'severity-badge--info';
                    return 'severity-badge--info';
                }},

                complexityBadgeClass(score) {{
                    if (score > 20) return 'complexity-badge--very-high';
                    if (score > 15) return 'complexity-badge--high';
                    if (score > 10) return 'complexity-badge--medium';
                    return 'complexity-badge--low';
                }},

                usageScoreBadgeClass(score) {{
                    if (score === 0) return 'usage-score-badge--none';
                    if (score <= 2) return 'usage-score-badge--low';
                    if (score <= 5) return 'usage-score-badge--medium';
                    return 'usage-score-badge--high';
                }},

                selectDependencyObject(key) {{
                    this.selectedDependencyKey = key;
                }},

                findMeasureInVisuals(measureKey) {{
                    if (!this.reportData || !this.reportData.pages) return [];

                    const usage = [];
                    const match = measureKey.match(/(.+?)\\[(.+?)\\]/);
                    if (!match) return usage;

                    const [, tableName, measureName] = match;

                    this.reportData.pages.forEach(page => {{
                        (page.visuals || []).forEach(visual => {{
                            const measures = visual.fields?.measures || [];
                            measures.forEach(m => {{
                                if (m.table === tableName && m.measure === measureName) {{
                                    const visualType = visual.visual_type || 'Unknown';
                                    const visualName = visual.visual_name || visual.title || visualType || 'Unnamed Visual';
                                    usage.push({{
                                        pageName: page.display_name || page.name,
                                        visualType: visualType,
                                        visualId: visual.id,
                                        visualName: visualName
                                    }});
                                }}
                            }});
                        }});
                    }});

                    return usage;
                }},

                findColumnInVisuals(columnKey) {{
                    if (!this.reportData || !this.reportData.pages) return [];

                    const usage = [];
                    const match = columnKey.match(/(.+?)\\[(.+?)\\]/);
                    if (!match) {{
                        console.log('No match for columnKey:', columnKey);
                        return usage;
                    }}

                    const [, tableName, columnName] = match;
                    console.log('Searching for column:', tableName, columnName);

                    this.reportData.pages.forEach(page => {{
                        (page.visuals || []).forEach(visual => {{
                            const columns = visual.fields?.columns || [];
                            columns.forEach(c => {{
                                if (c.table === tableName && c.column === columnName) {{
                                    const visualType = visual.visual_type || 'Unknown';
                                    const visualName = visual.visual_name || visual.title || visualType || 'Unnamed Visual';
                                    console.log('Found match in visual:', visualType, page.name);
                                    usage.push({{
                                        pageName: page.display_name || page.name,
                                        visualType: visualType,
                                        visualId: visual.id,
                                        visualName: visualName
                                    }});
                                }}
                            }});
                        }});
                    }});

                    console.log('Total usage found:', usage.length);
                    return usage;
                }},

                selectColumnDependency(key) {{
                    this.selectedColumnKey = key;
                }},

                toggleFolder(folderName) {{
                    this.collapsedFolders[folderName] = !this.collapsedFolders[folderName];
                }},

                toggleDependencyFolder(folderName) {{
                    this.collapsedDependencyFolders[folderName] = !this.collapsedDependencyFolders[folderName];
                }},

                toggleVisualGroup(visualType) {{
                    this.collapsedVisualGroups[visualType] = !this.collapsedVisualGroups[visualType];
                }},

                toggleMeasureExpansion(measureName) {{
                    this.expandedMeasures[measureName] = !this.expandedMeasures[measureName];
                }},

                toggleUnusedMeasureFolder(folderName) {{
                    this.collapsedUnusedMeasureFolders[folderName] = !this.collapsedUnusedMeasureFolders[folderName];
                }},

                toggleChainFolder(folderName) {{
                    this.collapsedChainFolders[folderName] = !this.collapsedChainFolders[folderName];
                }},

                toggleBpaObjectGroup(objectType) {{
                    this.collapsedBpaObjectGroups[objectType] = !this.collapsedBpaObjectGroups[objectType];
                }},

                toggleBpaCategory(objectType, category) {{
                    const key = `${{objectType}}|${{category}}`;
                    this.collapsedBpaCategories[key] = !this.collapsedBpaCategories[key];
                }},

                jumpToMeasureInModel(tableName, measureName) {{
                    // Switch to Model tab
                    this.activeTab = 'model';

                    // Wait for next tick to ensure DOM is updated
                    this.$nextTick(() => {{
                        // Select the table in the model view
                        const table = this.filteredTables.find(t => t.name === tableName);
                        if (table) {{
                            this.selectedTable = table;
                            this.modelDetailTab = 'measures'; // Switch to measures sub-tab

                            // Find the measure and expand it
                            this.$nextTick(() => {{
                                this.expandedMeasures[measureName] = true;

                                // Scroll to the measure
                                setTimeout(() => {{
                                    const measureElement = document.querySelector(`[data-measure="${{measureName}}"]`);
                                    if (measureElement) {{
                                        measureElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                        measureElement.classList.add('highlight-flash');
                                        setTimeout(() => measureElement.classList.remove('highlight-flash'), 2000);
                                    }}
                                }}, 100);
                            }});
                        }}
                    }});
                }},

                toggleUnusedColumnTable(tableName) {{
                    this.collapsedUnusedColumnTables[tableName] = !this.collapsedUnusedColumnTables[tableName];
                }},

                toggleFieldParam(fpName) {{
                    this.collapsedFieldParams[fpName] = !this.collapsedFieldParams[fpName];
                }},

                expandAllFieldParams() {{
                    this.fieldParametersList.forEach(fp => {{
                        this.collapsedFieldParams[fp.name] = false;
                    }});
                }},

                collapseAllFieldParams() {{
                    this.fieldParametersList.forEach(fp => {{
                        this.collapsedFieldParams[fp.name] = true;
                    }});
                }},

                toggleUsedByFolder(folderName) {{
                    this.collapsedUsedByFolders[folderName] = !this.collapsedUsedByFolders[folderName];
                }},

                expandAllUnusedMeasures() {{
                    Object.keys(this.unusedMeasuresByFolder).forEach(folderName => {{
                        this.collapsedUnusedMeasureFolders[folderName] = false;
                    }});
                }},

                collapseAllUnusedMeasures() {{
                    Object.keys(this.unusedMeasuresByFolder).forEach(folderName => {{
                        this.collapsedUnusedMeasureFolders[folderName] = true;
                    }});
                }},

                // Usage Matrix - Measures by Folder
                toggleMeasureFolder(folderName) {{
                    this.collapsedMeasureFolders[folderName] = !this.collapsedMeasureFolders[folderName];
                }},

                expandAllMeasureFolders() {{
                    Object.keys(this.filteredMeasuresGroupedByFolder).forEach(folderName => {{
                        this.collapsedMeasureFolders[folderName] = false;
                    }});
                }},

                collapseAllMeasureFolders() {{
                    Object.keys(this.filteredMeasuresGroupedByFolder).forEach(folderName => {{
                        this.collapsedMeasureFolders[folderName] = true;
                    }});
                }},

                // Usage Matrix - Columns by Table
                toggleColumnTable(tableName) {{
                    this.collapsedColumnTables[tableName] = !this.collapsedColumnTables[tableName];
                }},

                expandAllColumnTables() {{
                    Object.keys(this.filteredColumnsGroupedByTable).forEach(tableName => {{
                        this.collapsedColumnTables[tableName] = false;
                    }});
                }},

                collapseAllColumnTables() {{
                    Object.keys(this.filteredColumnsGroupedByTable).forEach(tableName => {{
                        this.collapsedColumnTables[tableName] = true;
                    }});
                }},

                copyUsageMatrix() {{
                    // Build tab-separated values for measures
                    const lines = [];

                    // Measures section
                    lines.push('MEASURES');
                    lines.push('Display Folder\\tTable\\tMeasure Name\\tStatus');
                    this.filteredMeasuresMatrix.forEach(m => {{
                        lines.push(`${{m.displayFolder || 'No Folder'}}\\t${{m.table}}\\t${{m.name}}\\t${{m.isUsed ? 'Used' : 'Unused'}}`);
                    }});

                    lines.push('');

                    // Columns section
                    lines.push('COLUMNS');
                    lines.push('Table\\tColumn Name\\tStatus');
                    this.filteredColumnsMatrix.forEach(c => {{
                        lines.push(`${{c.table}}\\t${{c.name}}\\t${{c.isUsed ? 'Used' : 'Unused'}}`);
                    }});

                    const text = lines.join('\\n');

                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(text).then(() => {{
                            alert('Copied to clipboard! You can paste this into Excel or a text editor.');
                        }}).catch(err => {{
                            console.error('Failed to copy: ', err);
                            this.fallbackCopy(text);
                        }});
                    }} else {{
                        this.fallbackCopy(text);
                    }}
                }},

                fallbackCopy(text) {{
                    // Fallback for older browsers
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    alert('Copied to clipboard!');
                }},

                expandAllUnusedColumns() {{
                    Object.keys(this.unusedColumnsByTable).forEach(tableName => {{
                        this.collapsedUnusedColumnTables[tableName] = false;
                    }});
                }},

                collapseAllUnusedColumns() {{
                    Object.keys(this.unusedColumnsByTable).forEach(tableName => {{
                        this.collapsedUnusedColumnTables[tableName] = true;
                    }});
                }},

                getTableType(tableName) {{
                    const name = (tableName || '').toLowerCase();
                    if (name.startsWith('f ')) return 'FACT';
                    if (name.startsWith('d ')) return 'DIMENSION';
                    return 'OTHER';
                }},

                getTableComplexity(table) {{
                    const cols = table.columns?.length || 0;
                    const meas = table.measures?.length || 0;
                    const total = cols + meas;
                    if (total < 10) return 'Complexity: LOW';
                    if (total < 50) return 'Complexity: MEDIUM';
                    return 'Complexity: HIGH';
                }},

                getComplexityBadge(table) {{
                    const cols = table.columns?.length || 0;
                    const meas = table.measures?.length || 0;
                    const total = cols + meas;
                    if (total < 10) return 'badge-success';
                    if (total < 50) return 'badge-warning';
                    return 'badge-danger';
                }},

                getTableRelationshipCount(tableName) {{
                    const rels = this.modelData.relationships || [];
                    return rels.filter(r => r.from_table === tableName || r.to_table === tableName).length;
                }},

                isColumnInRelationship(tableName, columnName) {{
                    const rels = this.modelData.relationships || [];

                    // Helper to extract column name from format like "'TableName'.'ColumnName'" or "'TableName'.ColumnName"
                    const extractColumnName = (colRef) => {{
                        if (!colRef) return '';
                        // Match patterns: 'Table'.'Column' or 'Table'.Column
                        const match = colRef.match(/['"]([^'"]+)['"]\\.['"]*([^'"]+)['"]*$/);
                        if (match) return match[2];
                        return colRef;
                    }};

                    return rels.some(r => {{
                        const fromCol = extractColumnName(r.from_column);
                        const toCol = extractColumnName(r.to_column);
                        return (r.from_table === tableName && fromCol === columnName) ||
                               (r.to_table === tableName && toCol === columnName);
                    }});
                }},

                getColumnFieldParams(tableName, columnName) {{
                    const columnKey = tableName + '[' + columnName + ']';
                    const fieldParams = this.dependencies.column_to_field_params || {{}};
                    return fieldParams[columnKey] || [];
                }},

                getColumnUsedByMeasures(tableName, columnName) {{
                    const columnKey = tableName + '[' + columnName + ']';
                    const columnToMeasure = this.dependencies.column_to_measure || {{}};
                    return columnToMeasure[columnKey] || [];
                }},

                getTableUsageCount(tableName) {{
                    if (!this.reportData || !this.reportData.pages) return 0;
                    let count = 0;
                    this.reportData.pages.forEach(page => {{
                        (page.visuals || []).forEach(visual => {{
                            const fields = visual.fields || {{}};
                            const measures = fields.measures || [];
                            const columns = fields.columns || [];
                            if (measures.some(m => m.table === tableName) || columns.some(c => c.table === tableName)) {{
                                count++;
                            }}
                        }});
                    }});
                    return count;
                }},

                formatCardinality(rel) {{
                    // Check different possible property names
                    const card = rel.cardinality || rel.from_cardinality || rel.to_cardinality;
                    if (!card) {{
                        // Try to infer from multiplicity properties
                        const from = rel.from_multiplicity || rel.fromCardinality;
                        const to = rel.to_multiplicity || rel.toCardinality;
                        if (from && to) return `${{from}}:${{to}}`;
                        return 'Many-to-One';  // Default assumption
                    }}
                    return card;
                }},

                formatCrossFilterDirection(rel) {{
                    const dir = rel.cross_filter_direction || rel.crossFilteringBehavior || rel.security_filtering_behavior;
                    if (!dir) return 'Single';
                    // Normalize the value
                    const dirStr = String(dir).toLowerCase();
                    if (dirStr.includes('both')) return 'Both';
                    if (dirStr.includes('one') || dirStr.includes('single')) return 'Single';
                    return dir;
                }},

                visualsByType(visuals) {{
                    const groups = {{}};
                    (visuals || []).forEach(visual => {{
                        const type = visual.visual_type || 'Unknown';
                        // Filter out unwanted visual types
                        if (type === 'Unknown' || type === 'shape' || type === 'image' || type === 'actionButton') {{
                            return; // Skip these types
                        }}
                        if (!groups[type]) {{
                            groups[type] = [];
                        }}
                        groups[type].push(visual);
                    }});
                    return groups;
                }},

                getVisibleVisualCount(visuals) {{
                    if (!visuals) return 0;
                    return visuals.filter(visual => {{
                        const type = visual.visual_type || 'Unknown';
                        return !(type === 'Unknown' || type === 'shape' || type === 'image' || type === 'actionButton');
                    }}).length;
                }},

                isVisualTypeFiltered(visualType) {{
                    const type = (visualType || 'Unknown').toLowerCase();
                    return type === 'unknown' ||
                           type === 'shape' ||
                           type === 'image' ||
                           type === 'actionbutton' ||
                           type === 'slicer' ||
                           type.includes('slicer') ||
                           type === 'bookmarknavigator' ||
                           type.includes('bookmark');
                }},

                groupVisualUsageByPage(visualUsage) {{
                    const grouped = {{}};
                    (visualUsage || []).forEach(usage => {{
                        const pageName = usage.pageName || 'Unknown Page';
                        if (!grouped[pageName]) {{
                            grouped[pageName] = [];
                        }}
                        grouped[pageName].push(usage);
                    }});
                    return grouped;
                }},

                groupMeasuresByFolder(measureNames) {{
                    const grouped = {{}};
                    (measureNames || []).forEach(measureName => {{
                        // Parse measure name: Table[Measure]
                        const match = measureName.match(/^(.+?)\\[(.+?)\\]$/);
                        if (!match) {{
                            const folder = 'No Folder';
                            if (!grouped[folder]) grouped[folder] = [];
                            grouped[folder].push(measureName);
                            return;
                        }}

                        const [, tableName, measureSimpleName] = match;

                        // Find the measure in model data to get its folder
                        let measureFolder = 'No Folder';
                        const table = (this.modelData.tables || []).find(t => t.name === tableName);
                        if (table) {{
                            const measure = (table.measures || []).find(m => m.name === measureSimpleName);
                            if (measure && measure.display_folder) {{
                                measureFolder = measure.display_folder;
                            }}
                        }}

                        if (!grouped[measureFolder]) {{
                            grouped[measureFolder] = [];
                        }}
                        grouped[measureFolder].push(measureName);
                    }});
                    return grouped;
                }},

                groupColumnUsageByPage(tableName, columnName) {{
                    const usage = this.getColumnVisualUsage(tableName, columnName);
                    const grouped = {{}};
                    usage.forEach(visual => {{
                        const pageName = visual.pageName || 'Unknown Page';
                        if (!grouped[pageName]) {{
                            grouped[pageName] = [];
                        }}
                        grouped[pageName].push(visual);
                    }});
                    return grouped;
                }},

                groupFilterUsageByPage(tableName, columnName) {{
                    const usage = this.getColumnFilterUsage(tableName, columnName);
                    const grouped = {{}};
                    usage.forEach(filter => {{
                        const pageName = filter.pageName || 'Unknown Page';
                        if (!grouped[pageName]) {{
                            grouped[pageName] = [];
                        }}
                        grouped[pageName].push(filter);
                    }});
                    return grouped;
                }},

                groupFilterUsageByPageForKey(filterUsage) {{
                    // Group filter usage array by page name for display
                    const grouped = {{}};
                    (filterUsage || []).forEach(filter => {{
                        const pageName = filter.pageName || 'Unknown Page';
                        if (!grouped[pageName]) {{
                            grouped[pageName] = [];
                        }}
                        grouped[pageName].push(filter);
                    }});
                    return grouped;
                }},

                // Helper for Measure Chains: Group visuals by page
                groupVisualsByPage(visualUsage) {{
                    const grouped = {{}};
                    visualUsage.forEach(visual => {{
                        const pageName = visual.pageName || 'Unknown Page';
                        if (!grouped[pageName]) {{
                            grouped[pageName] = [];
                        }}
                        grouped[pageName].push(visual);
                    }});
                    return grouped;
                }},

                // Calculate chain depth for a measure
                calculateChainDepth(measureName, measureToMeasure, visited) {{
                    if (visited.has(measureName)) return 0; // Circular dependency
                    visited.add(measureName);

                    const deps = measureToMeasure[measureName] || [];
                    if (deps.length === 0) return 0; // Base measure

                    let maxDepth = 0;
                    deps.forEach(dep => {{
                        const depth = this.calculateChainDepth(dep, measureToMeasure, new Set(visited));
                        maxDepth = Math.max(maxDepth, depth);
                    }});

                    return maxDepth + 1;
                }},

                // Build complete measure chain
                buildMeasureChain(measureName, measureToMeasure) {{
                    const deps = measureToMeasure[measureName] || [];

                    // If base measure
                    if (deps.length === 0) {{
                        return {{
                            baseMeasures: [measureName],
                            levels: [],
                            topMeasure: null
                        }};
                    }}

                    // Build dependency tree
                    const allBaseMeasures = new Set();
                    const levels = [];

                    const buildLevel = (measures, depth = 0) => {{
                        const levelMeasures = [];

                        measures.forEach(m => {{
                            const mDeps = measureToMeasure[m] || [];

                            if (mDeps.length === 0) {{
                                allBaseMeasures.add(m);
                            }} else {{
                                levelMeasures.push({{
                                    name: m,
                                    dependsOn: mDeps
                                }});
                            }}
                        }});

                        if (levelMeasures.length > 0) {{
                            levels.push({{ measures: levelMeasures }});

                            // Recursively build next level
                            const nextLevelMeasures = [];
                            levelMeasures.forEach(lm => {{
                                nextLevelMeasures.push(...lm.dependsOn);
                            }});

                            if (nextLevelMeasures.length > 0) {{
                                buildLevel(nextLevelMeasures, depth + 1);
                            }}
                        }}
                    }};

                    buildLevel(deps);

                    // Reverse levels to show base -> top
                    levels.reverse();

                    return {{
                        baseMeasures: Array.from(allBaseMeasures),
                        levels: levels,
                        topMeasure: {{
                            name: measureName,
                            dependsOn: deps
                        }}
                    }};
                }},

                // Get visual usage for a measure
                getMeasureVisualUsage(measureName) {{
                    if (!this.reportData || !this.reportData.pages) return [];

                    const usage = [];
                    const measureUsage = this.dependencies.measure_to_visual || {{}};

                    // Use pre-computed measure_to_visual mapping if available
                    const visualIds = measureUsage[measureName] || [];

                    if (visualIds.length > 0) {{
                        this.reportData.pages.forEach(page => {{
                            (page.visuals || []).forEach(visual => {{
                                const vId = visual.visualId || visual.visual_id;
                                if (visualIds.includes(vId)) {{
                                    const type = visual.visual_type || visual.type;
                                    if (!this.isVisualTypeFiltered(type)) {{
                                        usage.push({{
                                            pageName: page.name || page.display_name,
                                            visualId: vId,
                                            visualType: type,
                                            visualName: visual.name || visual.visual_name || 'Unnamed'
                                        }});
                                    }}
                                }}
                            }});
                        }});
                    }}

                    return usage;
                }},

                // Get all measures used in a visual
                getVisualMeasures(visual) {{
                    const measures = new Set();

                    const extractMeasures = (obj) => {{
                        if (!obj) return;

                        if (typeof obj === 'string') {{
                            // Match measure references like [MeasureName]
                            const matches = obj.match(/\\[([^\\]]+)\\]/g);
                            if (matches) {{
                                matches.forEach(m => measures.add(m));
                            }}
                        }} else if (Array.isArray(obj)) {{
                            obj.forEach(item => extractMeasures(item));
                        }} else if (typeof obj === 'object') {{
                            Object.values(obj).forEach(value => extractMeasures(value));
                        }}
                    }};

                    extractMeasures(visual);
                    return Array.from(measures);
                }},

                // Analyze measures in a visual (backward trace)
                analyzeVisualMeasures(visual) {{
                    const topMeasures = this.getVisualMeasures(visual);
                    const measureToMeasure = this.dependencies.measure_to_measure || {{}};

                    const analyzeMeasure = (measureName, depth = 0) => {{
                        const match = measureName.match(/^(.+?)\\[(.+?)\\]$/);
                        if (!match) return null;

                        const [, table, name] = match;
                        const deps = measureToMeasure[measureName] || [];

                        return {{
                            name: name,
                            table: table,
                            fullName: measureName,
                            dependencies: deps.length > 0 ? deps.map(d => analyzeMeasure(d, depth + 1)).filter(Boolean) : []
                        }};
                    }};

                    const analyzedMeasures = topMeasures.map(m => analyzeMeasure(m)).filter(Boolean);

                    // Count totals
                    const countMeasures = (measure) => {{
                        let count = 1;
                        if (measure.dependencies) {{
                            measure.dependencies.forEach(dep => {{
                                count += countMeasures(dep);
                            }});
                        }}
                        return count;
                    }};

                    const totalMeasures = analyzedMeasures.reduce((sum, m) => sum + countMeasures(m), 0);

                    const countDirectDeps = analyzedMeasures.reduce((sum, m) =>
                        sum + (m.dependencies ? m.dependencies.length : 0), 0);

                    const countBaseMeasures = (measure) => {{
                        if (!measure.dependencies || measure.dependencies.length === 0) return 1;
                        return measure.dependencies.reduce((sum, dep) => sum + countBaseMeasures(dep), 0);
                    }};

                    const baseMeasures = analyzedMeasures.reduce((sum, m) => sum + countBaseMeasures(m), 0);

                    return {{
                        topMeasures: analyzedMeasures,
                        summary: {{
                            totalMeasures: totalMeasures,
                            directDeps: countDirectDeps,
                            baseMeasures: baseMeasures
                        }}
                    }};
                }},

                getVisualIcon(visualType) {{
                    const type = (visualType || '').toLowerCase();
                    if (type.includes('slicer')) return 'visual-icon slicer';
                    if (type.includes('table') || type.includes('matrix')) return 'visual-icon table';
                    if (type.includes('card')) return 'visual-icon card';
                    if (type.includes('map') || type.includes('geo')) return 'visual-icon map';
                    return 'visual-icon chart';
                }},

                getVisualEmoji(visualType) {{
                    const type = (visualType || '').toLowerCase();
                    if (type.includes('slicer')) return '🎚️';
                    if (type.includes('table')) return '📊';
                    if (type.includes('matrix')) return '🔢';
                    if (type.includes('card')) return '🃏';
                    if (type.includes('map') || type.includes('geo')) return '🗺️';
                    if (type.includes('line')) return '📈';
                    if (type.includes('bar') || type.includes('column')) return '📊';
                    if (type.includes('pie') || type.includes('donut')) return '🥧';
                    return '📉';
                }},

                highlightDAX(expression) {{
                    if (!expression) return '';

                    // Basic DAX syntax highlighting
                    let highlighted = expression
                        .replace(/\\b(VAR|RETURN|IF|SWITCH|CALCULATE|FILTER|ALL|RELATED|SUMX|AVERAGEX|HASONEVALUE|VALUES|DISTINCT|COUNTROWS|DIVIDE|AND|OR|NOT|TRUE|FALSE)\\b/g,
                            '<span class="dax-keyword">$1</span>')
                        .replace(/\\b([A-Z][A-Z0-9_]*)\\s*\\(/g,
                            '<span class="dax-function">$1</span>(')
                        .replace(/'([^']*)'/g,
                            '<span class="dax-string">\\'$1\\'</span>')
                        .replace(/\\b([0-9]+\\.?[0-9]*)\\b/g,
                            '<span class="dax-number">$1</span>')
                        .replace(/--([^\\n]*)/g,
                            '<span class="dax-comment">--$1</span>')
                        .replace(/\\[([^\\]]+)\\]/g,
                            '<span class="dax-column">[$1]</span>');

                    return highlighted;
                }},

                executeCommand(cmd) {{
                    this.showCommandPalette = false;
                    this.commandQuery = '';
                    cmd.action();
                }},

                getTableRelationships(tableName) {{
                    const rels = this.modelData.relationships || [];
                    return rels.filter(r => r.from_table === tableName || r.to_table === tableName);
                }},

                getTableVisualUsage(tableName) {{
                    if (!this.reportData || !this.reportData.pages) return [];
                    const usage = [];
                    this.reportData.pages.forEach(page => {{
                        (page.visuals || []).forEach(visual => {{
                            const fields = visual.fields || {{}};
                            const measures = fields.measures || [];
                            const columns = fields.columns || [];
                            if (measures.some(m => m.table === tableName) || columns.some(c => c.table === tableName)) {{
                                const visualType = visual.visual_type || 'Unknown';
                                const visualName = visual.visual_name || visual.title || visualType || 'Unnamed Visual';
                                usage.push({{
                                    pageName: page.display_name || page.name,
                                    visualType: visualType,
                                    visualId: visual.id,
                                    visualName: visualName
                                }});
                            }}
                        }});
                    }});
                    return usage;
                }},

                getColumnVisualUsage(tableName, columnName) {{
                    if (!this.reportData || !this.reportData.pages) return [];
                    const usage = [];
                    this.reportData.pages.forEach(page => {{
                        (page.visuals || []).forEach(visual => {{
                            const fields = visual.fields || {{}};
                            const columns = fields.columns || [];
                            if (columns.some(c => c.table === tableName && c.column === columnName)) {{
                                const visualType = visual.visual_type || 'Unknown';
                                const visualName = visual.visual_name || visual.title || visualType || 'Unnamed Visual';
                                usage.push({{
                                    pageName: page.display_name || page.name,
                                    visualType: visualType,
                                    visualId: visual.id,
                                    visualName: visualName
                                }});
                            }}
                        }});
                    }});
                    return usage;
                }},

                getColumnFilterUsage(tableName, columnName) {{
                    // Get filter pane usage for a column (both page-level and report-level filters)
                    if (!this.reportData) return [];
                    const usage = [];

                    // Check report-level filters (filters on all pages)
                    const reportFilters = this.reportData.report?.filters || [];
                    reportFilters.forEach(filter => {{
                        const field = filter.field || {{}};
                        if (field.type === 'Column' && field.table === tableName && field.name === columnName) {{
                            usage.push({{
                                pageName: 'All Pages (Report Filter)',
                                filterLevel: 'report',
                                filterName: field.name,
                                filterType: 'Column'
                            }});
                        }}
                    }});

                    // Check page-level filters
                    (this.reportData.pages || []).forEach(page => {{
                        const pageFilters = page.filters || [];
                        pageFilters.forEach(filter => {{
                            const field = filter.field || {{}};
                            if (field.type === 'Column' && field.table === tableName && field.name === columnName) {{
                                usage.push({{
                                    pageName: page.display_name || page.name,
                                    filterLevel: 'page',
                                    filterName: field.name,
                                    filterType: 'Column'
                                }});
                            }}
                        }});
                    }});

                    return usage;
                }},

                findColumnInFilters(columnKey) {{
                    // Find all filter usages for a column key like "Table[Column]"
                    if (!this.reportData) return [];
                    const usage = [];
                    const match = columnKey.match(/(.+?)\\[(.+?)\\]/);
                    if (!match) return usage;

                    const [, tableName, columnName] = match;

                    // Check report-level filters
                    const reportFilters = this.reportData.report?.filters || [];
                    reportFilters.forEach(filter => {{
                        const field = filter.field || {{}};
                        if (field.type === 'Column' && field.table === tableName && field.name === columnName) {{
                            usage.push({{
                                pageName: 'All Pages (Report Filter)',
                                filterLevel: 'report',
                                filterName: field.name
                            }});
                        }}
                    }});

                    // Check page-level filters
                    (this.reportData.pages || []).forEach(page => {{
                        const pageFilters = page.filters || [];
                        pageFilters.forEach(filter => {{
                            const field = filter.field || {{}};
                            if (field.type === 'Column' && field.table === tableName && field.name === columnName) {{
                                usage.push({{
                                    pageName: page.display_name || page.name,
                                    filterLevel: 'page',
                                    filterName: field.name
                                }});
                            }}
                        }});
                    }});

                    return usage;
                }},

            }},

            mounted() {{

                // Set first table as selected
                if (this.modelData.tables && this.modelData.tables.length > 0) {{
                    this.selectedTable = this.modelData.tables[0];
                }}

                // Set first page as selected
                if (this.sortedPages && this.sortedPages.length > 0) {{
                    this.selectedPage = this.sortedPages[0];
                }}

                // Initialize all folders as collapsed
                // Collapse measure folders
                if (this.measuresByFolder && typeof this.measuresByFolder === 'object') {{
                    Object.keys(this.measuresByFolder).forEach(folderName => {{
                        this.collapsedFolders[folderName] = true;
                    }});
                }}

                // Collapse dependency folders (columns grouped by table)
                if (this.filteredColumnsForDependency && typeof this.filteredColumnsForDependency === 'object') {{
                    Object.keys(this.filteredColumnsForDependency).forEach(tableName => {{
                        this.collapsedDependencyFolders[tableName] = true;
                    }});
                }}

                // Collapse visual type groups
                if (this.reportData && this.reportData.pages) {{
                    this.reportData.pages.forEach(page => {{
                        const visualGroups = this.visualsByType(page.visuals || []);
                        if (visualGroups && typeof visualGroups === 'object') {{
                            Object.keys(visualGroups).forEach(visualType => {{
                                this.collapsedVisualGroups[visualType] = true;
                            }});
                        }}
                    }});
                }}

                // Start with unused measure folders expanded (set to false)
                if (this.unusedMeasuresByFolder && typeof this.unusedMeasuresByFolder === 'object') {{
                    Object.keys(this.unusedMeasuresByFolder).forEach(folderName => {{
                        this.collapsedUnusedMeasureFolders[folderName] = false;
                    }});
                }}

                // Start with unused column tables expanded (set to false)
                if (this.unusedColumnsByTable && typeof this.unusedColumnsByTable === 'object') {{
                    Object.keys(this.unusedColumnsByTable).forEach(tableName => {{
                        this.collapsedUnusedColumnTables[tableName] = false;
                    }});
                }}

                // Initialize usage matrix collapsed states - start with all folders/tables collapsed
                if (this.filteredMeasuresGroupedByFolder && typeof this.filteredMeasuresGroupedByFolder === 'object') {{
                    Object.keys(this.filteredMeasuresGroupedByFolder).forEach(folderName => {{
                        this.collapsedMeasureFolders[folderName] = true;
                    }});
                }}

                if (this.filteredColumnsGroupedByTable && typeof this.filteredColumnsGroupedByTable === 'object') {{
                    Object.keys(this.filteredColumnsGroupedByTable).forEach(tableName => {{
                        this.collapsedColumnTables[tableName] = true;
                    }});
                }}

                // Keyboard shortcuts
                document.addEventListener('keydown', (e) => {{
                    // Cmd/Ctrl + K for command palette
                    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{
                        e.preventDefault();
                        this.showCommandPalette = true;
                        this.$nextTick(() => {{
                            this.$refs.commandInput?.focus();
                        }});
                    }}

                    // Escape to close command palette
                    if (e.key === 'Escape' && this.showCommandPalette) {{
                        this.showCommandPalette = false;
                    }}

                    // / to focus search
                    if (e.key === '/' && !this.showCommandPalette) {{
                        e.preventDefault();
                        document.querySelector('input[placeholder*="Search"]')?.focus();
                    }}
                }});
            }}}}).mount('#app');
    </script>
"""

    def _get_vue3_template(self, data_json_str: str, repo_name: str) -> str:
        """Get the complete Vue 3 HTML template."""
        escaped_repo_name = html.escape(repo_name)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
{self._get_head_section(escaped_repo_name)}
{self._get_styles()}
</head>
{self._get_body_content()}
{self._get_vue_app_script(data_json_str)}
</html>"""
