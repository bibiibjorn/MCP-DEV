"""
PBIP Theme Compliance HTML Generator - Generates interactive HTML report for theme compliance.

Creates a professional, interactive HTML dashboard with:
- Compliance score visualization
- Color palette analysis
- Font usage breakdown
- Violation tracking
- Page-by-page compliance details
"""

import os
import json
import logging
import webbrowser
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_theme_compliance_html(
    analysis_data: Dict[str, Any],
    model_name: str = "Power BI Report",
    auto_open: bool = True,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Generate an interactive HTML report for theme compliance analysis.

    Args:
        analysis_data: Output from PbipThemeComplianceAnalyzer.analyze_theme_compliance()
        model_name: Name of the report for display
        auto_open: Whether to open the HTML in browser
        output_path: Optional custom output path

    Returns:
        Path to generated HTML file or None if failed
    """
    if not analysis_data:
        logger.error("No analysis data provided")
        return None

    summary = analysis_data.get("summary", {})
    theme = analysis_data.get("theme", {})
    pages = analysis_data.get("pages", [])
    color_analysis = analysis_data.get("color_analysis", {})
    font_analysis = analysis_data.get("font_analysis", {})
    visual_analysis = analysis_data.get("visual_analysis", {})
    violations = analysis_data.get("violations", [])

    # Prepare data for JavaScript
    js_data = {
        "modelName": model_name,
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "theme": theme,
        "themeSource": analysis_data.get("theme_source", "Unknown"),
        "pages": pages,
        "colorAnalysis": color_analysis,
        "fontAnalysis": font_analysis,
        "visualAnalysis": visual_analysis,
        "violations": violations,
        "complianceScore": analysis_data.get("compliance_score", 0)
    }

    html_content = _build_html_document(js_data, model_name)

    # Determine output path
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        html_file = output_path
    else:
        # Default to exports folder
        server_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        exports_dir = os.path.join(server_root, "exports", "theme_compliance")
        os.makedirs(exports_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in model_name)
        safe_name = safe_name.replace(' ', '_').strip('_')
        html_file = os.path.join(exports_dir, f"{safe_name}_Theme_Compliance_{timestamp}.html")

    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Theme compliance HTML generated: {html_file}")

        if auto_open:
            webbrowser.open(f'file://{os.path.abspath(html_file)}')

        return html_file

    except Exception as e:
        logger.error(f"Failed to write HTML report: {e}")
        return None


def _build_html_document(data: Dict[str, Any], model_name: str) -> str:
    """Build the complete HTML document."""
    data_json = json.dumps(data, indent=2, ensure_ascii=False)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} - Theme Compliance Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/vue@3.4.21/dist/vue.global.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --terracotta: #C4A484;
            --terracotta-dark: #A67B5B;
            --clay: #E8DDD3;
            --sand: #F5F1EB;
            --cream: #FAF8F5;
            --ink: #2D2418;
            --charcoal: #4A4238;
            --stone: #7A7267;
            --success: #606C38;
            --warning: #BC6C25;
            --danger: #9B2C2C;
            --info: #457B9D;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'DM Sans', sans-serif;
            background: var(--cream);
            color: var(--ink);
            line-height: 1.6;
        }}

        .header {{
            background: linear-gradient(135deg, var(--terracotta) 0%, var(--terracotta-dark) 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .card {{
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid var(--clay);
        }}

        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--ink);
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--clay);
        }}

        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
        }}

        .stat-card {{
            background: var(--sand);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--terracotta-dark);
        }}

        .stat-label {{
            font-size: 0.875rem;
            color: var(--stone);
            margin-top: 0.25rem;
        }}

        /* Compliance Score Circle */
        .score-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }}

        .score-circle {{
            width: 200px;
            height: 200px;
            border-radius: 50%;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}

        .score-circle svg {{
            position: absolute;
            transform: rotate(-90deg);
            width: 200px;
            height: 200px;
        }}

        .score-circle circle {{
            fill: none;
            stroke-width: 12;
        }}

        .score-circle .bg {{
            stroke: var(--clay);
        }}

        .score-circle .progress {{
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease;
        }}

        .score-value {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--ink);
            z-index: 1;
        }}

        .score-label {{
            font-size: 0.875rem;
            color: var(--stone);
            z-index: 1;
        }}

        .score-excellent {{ color: var(--success); }}
        .score-good {{ color: #7CB342; }}
        .score-warning {{ color: var(--warning); }}
        .score-poor {{ color: var(--danger); }}

        /* Color Swatches */
        .color-swatch {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            background: white;
            border: 1px solid var(--clay);
            border-radius: 8px;
            margin: 0.25rem;
        }}

        .color-box {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
            border: 1px solid rgba(0,0,0,0.1);
        }}

        .color-info {{
            font-size: 0.75rem;
            color: var(--charcoal);
        }}

        .color-count {{
            font-size: 0.75rem;
            color: var(--stone);
            background: var(--sand);
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
        }}

        /* Violations */
        .violation-card {{
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.75rem;
            border-left: 4px solid;
        }}

        .violation-warning {{
            background: #FFF8E1;
            border-color: var(--warning);
        }}

        .violation-info {{
            background: #E3F2FD;
            border-color: var(--info);
        }}

        .violation-badge {{
            display: inline-block;
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-warning {{
            background: #FFE0B2;
            color: #E65100;
        }}

        .badge-info {{
            background: #BBDEFB;
            color: #1565C0;
        }}

        /* Tabs */
        .tabs {{
            display: flex;
            border-bottom: 2px solid var(--clay);
            margin-bottom: 1.5rem;
            overflow-x: auto;
        }}

        .tab {{
            padding: 0.75rem 1.5rem;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 0.9rem;
            font-weight: 500;
            color: var(--stone);
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .tab:hover {{
            color: var(--terracotta-dark);
        }}

        .tab.active {{
            color: var(--terracotta-dark);
            border-bottom: 3px solid var(--terracotta);
            margin-bottom: -2px;
        }}

        /* Page Card */
        .page-card {{
            background: var(--sand);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}

        .page-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}

        .page-name {{
            font-weight: 600;
            color: var(--ink);
        }}

        .page-stats {{
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: var(--stone);
        }}

        /* Visual Type Pills */
        .visual-type-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid var(--clay);
            border-radius: 20px;
            margin: 0.25rem;
            font-size: 0.875rem;
        }}

        .visual-count {{
            background: var(--terracotta);
            color: white;
            padding: 0.125rem 0.5rem;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        /* Font Pills */
        .font-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: white;
            border: 1px solid var(--clay);
            border-radius: 8px;
            margin: 0.25rem;
        }}

        .font-name {{
            font-weight: 500;
        }}

        /* Filter Input */
        .filter-input {{
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--clay);
            border-radius: 8px;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        .filter-input:focus {{
            outline: none;
            border-color: var(--terracotta);
        }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--stone);
        }}

        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}

        /* Theme Info */
        .theme-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}

        .theme-detail {{
            padding: 1rem;
            background: var(--sand);
            border-radius: 8px;
        }}

        .theme-detail-label {{
            font-size: 0.75rem;
            color: var(--stone);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .theme-detail-value {{
            font-weight: 600;
            color: var(--ink);
            margin-top: 0.25rem;
        }}

        /* Palette Display */
        .palette-row {{
            display: flex;
            gap: 4px;
            margin-top: 0.5rem;
        }}

        .palette-color {{
            width: 32px;
            height: 32px;
            border-radius: 4px;
            border: 1px solid rgba(0,0,0,0.1);
        }}

        /* Compliance indicator */
        .compliance-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            font-size: 0.875rem;
        }}

        .compliance-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}

        .dot-compliant {{
            background: var(--success);
        }}

        .dot-violation {{
            background: var(--warning);
        }}
    </style>
</head>
<body>
    <div id="app">
        <header class="header">
            <div class="container">
                <h1 style="font-size: 1.75rem; font-weight: 700;">{{{{ modelName }}}} - Theme Compliance</h1>
                <p style="opacity: 0.9; margin-top: 0.5rem;">Generated: {{{{ formattedTimestamp }}}}</p>
            </div>
        </header>

        <main class="container">
            <!-- Compliance Score -->
            <div class="card">
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 2rem; align-items: center;">
                    <div class="score-container">
                        <div class="score-circle">
                            <svg viewBox="0 0 200 200">
                                <circle class="bg" cx="100" cy="100" r="88"></circle>
                                <circle class="progress"
                                        :style="scoreCircleStyle"
                                        cx="100" cy="100" r="88"></circle>
                            </svg>
                            <span class="score-value" :class="scoreClass">{{{{ complianceScore }}}}</span>
                            <span class="score-label">Compliance Score</span>
                        </div>
                    </div>
                    <div>
                        <h2 class="card-title" style="border: none; padding: 0; margin-bottom: 1rem;">
                            {{{{ scoreLabel }}}}
                        </h2>
                        <div class="stat-grid">
                            <div class="stat-card">
                                <div class="stat-value">{{{{ summary.total_visuals }}}}</div>
                                <div class="stat-label">Total Visuals</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value" :class="{{'score-excellent': summary.compliant_visuals === summary.total_visuals}}">
                                    {{{{ summary.compliant_visuals }}}}
                                </div>
                                <div class="stat-label">Compliant Visuals</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value" :class="{{'score-warning': summary.total_violations > 0}}">
                                    {{{{ summary.total_violations }}}}
                                </div>
                                <div class="stat-label">Violations</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">{{{{ summary.total_pages }}}}</div>
                                <div class="stat-label">Pages</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Theme Information -->
            <div class="card">
                <h2 class="card-title">Theme Information</h2>
                <div class="theme-info">
                    <div class="theme-detail">
                        <div class="theme-detail-label">Theme Name</div>
                        <div class="theme-detail-value">{{{{ theme?.name || 'Default' }}}}</div>
                    </div>
                    <div class="theme-detail">
                        <div class="theme-detail-label">Source</div>
                        <div class="theme-detail-value">{{{{ themeSource }}}}</div>
                    </div>
                    <div class="theme-detail">
                        <div class="theme-detail-label">Unique Colors Used</div>
                        <div class="theme-detail-value">{{{{ summary.unique_colors }}}}</div>
                    </div>
                    <div class="theme-detail">
                        <div class="theme-detail-label">Unique Fonts Used</div>
                        <div class="theme-detail-value">{{{{ summary.unique_fonts }}}}</div>
                    </div>
                </div>

                <!-- Theme Data Colors with Variations -->
                <div v-if="theme?.colors?.data_colors?.length > 0" style="margin-top: 1.5rem;">
                    <div style="font-size: 0.875rem; color: var(--stone); margin-bottom: 0.5rem;">Theme Data Colors</div>
                    <!-- Base colors row -->
                    <div class="palette-row">
                        <div v-for="(color, index) in theme.colors.data_colors.slice(0, 8)"
                             :key="'base-' + index"
                             class="palette-color"
                             :style="{{backgroundColor: color}}"
                             :title="color">
                        </div>
                    </div>
                    <!-- Tints and Shades rows (show variations) -->
                    <div v-for="(factor, rowIdx) in [0.6, 0.4, 0.2, -0.25, -0.5]" :key="'row-' + rowIdx" class="palette-row">
                        <div v-for="(color, colIdx) in theme.colors.data_colors.slice(0, 8)"
                             :key="'var-' + rowIdx + '-' + colIdx"
                             class="palette-color"
                             :style="{{backgroundColor: getColorVariation(color, factor)}}"
                             :title="getColorVariation(color, factor)">
                        </div>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--stone); margin-top: 0.5rem;">
                        Includes tints (60%, 40%, 20% lighter) and shades (25%, 50% darker) as valid theme colors
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="tabs">
                <button class="tab" :class="{{active: activeTab === 'overview'}}" @click="activeTab = 'overview'">
                    Overview
                </button>
                <button class="tab" :class="{{active: activeTab === 'colors'}}" @click="activeTab = 'colors'">
                    Colors ({{{{ colorAnalysis.total_unique_colors }}}})
                </button>
                <button class="tab" :class="{{active: activeTab === 'fonts'}}" @click="activeTab = 'fonts'">
                    Fonts ({{{{ fontAnalysis.total_unique_fonts }}}})
                </button>
                <button class="tab" :class="{{active: activeTab === 'violations'}}" @click="activeTab = 'violations'">
                    Violations ({{{{ violations.length }}}})
                </button>
                <button class="tab" :class="{{active: activeTab === 'pages'}}" @click="activeTab = 'pages'">
                    By Page
                </button>
            </div>

            <!-- Overview Tab -->
            <div v-if="activeTab === 'overview'" class="card">
                <h2 class="card-title">Visual Type Distribution</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                    <div v-for="(count, type) in visualAnalysis.visual_type_distribution"
                         :key="type"
                         class="visual-type-pill">
                        <span>{{{{ formatVisualType(type) }}}}</span>
                        <span class="visual-count">{{{{ count }}}}</span>
                    </div>
                </div>

                <div v-if="violations.length > 0" style="margin-top: 2rem;">
                    <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">
                        Recent Violations
                    </h3>
                    <div v-for="violation in violations.slice(0, 5)" :key="violation.visual_id + violation.value"
                         :class="'violation-card violation-' + violation.severity">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <span :class="'violation-badge badge-' + violation.severity">
                                    {{{{ violation.severity }}}}
                                </span>
                                <span style="margin-left: 0.5rem; font-weight: 500;">{{{{ violation.detail }}}}</span>
                            </div>
                            <span style="font-size: 0.75rem; color: var(--stone);">{{{{ violation.page }}}}</span>
                        </div>
                        <div style="font-size: 0.875rem; color: var(--stone); margin-top: 0.5rem;">
                            Visual: {{{{ violation.visual_type }}}} ({{{{ violation.visual_id }}}})
                        </div>
                    </div>
                    <div v-if="violations.length > 5" style="text-align: center; margin-top: 1rem;">
                        <button @click="activeTab = 'violations'"
                                style="color: var(--terracotta-dark); background: none; border: none; cursor: pointer; font-weight: 500;">
                            View all {{{{ violations.length }}}} violations →
                        </button>
                    </div>
                </div>
            </div>

            <!-- Colors Tab -->
            <div v-if="activeTab === 'colors'" class="card">
                <h2 class="card-title">Color Usage Analysis</h2>

                <div v-if="colorAnalysis.top_colors?.length > 0">
                    <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">Top Colors</h3>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div v-for="[color, count] in colorAnalysis.top_colors" :key="color" class="color-swatch">
                            <div class="color-box" :style="{{backgroundColor: color}}"></div>
                            <span class="color-info">{{{{ color }}}}</span>
                            <span class="color-count">{{{{ count }}}} uses</span>
                        </div>
                    </div>
                </div>

                <div v-if="Object.keys(colorAnalysis.color_usage || {{}}).length > 10" style="margin-top: 1.5rem;">
                    <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem;">All Colors</h3>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div v-for="(count, color) in colorAnalysis.color_usage" :key="color" class="color-swatch">
                            <div class="color-box" :style="{{backgroundColor: color}}"></div>
                            <span class="color-info">{{{{ color }}}}</span>
                            <span class="color-count">{{{{ count }}}}</span>
                        </div>
                    </div>
                </div>

                <div v-if="nonThemeColors.length > 0" style="margin-top: 1.5rem;">
                    <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: var(--warning);">
                        ⚠️ Colors Not in Theme ({{{{ nonThemeColors.length }}}} unique)
                    </h3>
                    <div style="display: flex; flex-wrap: wrap;">
                        <div v-for="v in nonThemeColors" :key="v.value" class="color-swatch" style="border-color: var(--warning);">
                            <div class="color-box" :style="{{backgroundColor: v.value}}"></div>
                            <span class="color-info">{{{{ v.value }}}}</span>
                            <span class="color-count" :title="v.visual_count + ' visuals'">{{{{ v.usage_count }}}} uses</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Fonts Tab -->
            <div v-if="activeTab === 'fonts'" class="card">
                <h2 class="card-title">Font Usage Analysis</h2>

                <div v-if="fontAnalysis.top_fonts?.length > 0">
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                        <div v-for="[font, count] in fontAnalysis.top_fonts" :key="font" class="font-pill">
                            <span class="font-name" :style="{{fontFamily: font}}">{{{{ font }}}}</span>
                            <span class="color-count">{{{{ count }}}} uses</span>
                        </div>
                    </div>
                </div>

                <div v-if="nonThemeFonts.length > 0" style="margin-top: 1.5rem;">
                    <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: var(--info);">
                        ℹ️ Fonts Not in Theme ({{{{ nonThemeFonts.length }}}} unique)
                    </h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                        <div v-for="v in nonThemeFonts" :key="v.value" class="font-pill" style="border-color: var(--info);">
                            <span class="font-name">{{{{ v.value }}}}</span>
                            <span class="color-count" :title="v.visual_count + ' visuals'">{{{{ v.usage_count }}}} uses</span>
                        </div>
                    </div>
                </div>

                <div v-if="fontAnalysis.total_unique_fonts === 0" class="empty-state">
                    <div class="empty-state-icon">🔤</div>
                    <p>No custom fonts detected</p>
                </div>
            </div>

            <!-- Violations Tab -->
            <div v-if="activeTab === 'violations'" class="card">
                <h2 class="card-title">All Violations</h2>

                <div v-if="violations.length === 0" class="empty-state">
                    <div class="empty-state-icon">✅</div>
                    <p>No violations found - great job!</p>
                </div>

                <div v-else>
                    <input type="text" v-model="violationSearch"
                           placeholder="Search violations..."
                           class="filter-input">

                    <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                        <button @click="violationFilter = 'all'"
                                :style="{{fontWeight: violationFilter === 'all' ? '600' : '400', color: violationFilter === 'all' ? 'var(--terracotta-dark)' : 'var(--stone)'}}"
                                style="background: none; border: none; cursor: pointer;">
                            All ({{{{ violations.length }}}})
                        </button>
                        <button @click="violationFilter = 'warning'"
                                :style="{{fontWeight: violationFilter === 'warning' ? '600' : '400', color: violationFilter === 'warning' ? 'var(--warning)' : 'var(--stone)'}}"
                                style="background: none; border: none; cursor: pointer;">
                            Warnings ({{{{ summary.warning_count }}}})
                        </button>
                        <button @click="violationFilter = 'info'"
                                :style="{{fontWeight: violationFilter === 'info' ? '600' : '400', color: violationFilter === 'info' ? 'var(--info)' : 'var(--stone)'}}"
                                style="background: none; border: none; cursor: pointer;">
                            Info ({{{{ summary.info_count }}}})
                        </button>
                    </div>

                    <div v-for="violation in filteredViolations" :key="violation.visual_id + violation.value + violation.type"
                         :class="'violation-card violation-' + violation.severity">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <span :class="'violation-badge badge-' + violation.severity">
                                    {{{{ violation.type.replace(/_/g, ' ') }}}}
                                </span>
                            </div>
                            <span style="font-size: 0.75rem; color: var(--stone);">{{{{ violation.page }}}}</span>
                        </div>
                        <div style="margin-top: 0.5rem; font-weight: 500;">{{{{ violation.detail }}}}</div>
                        <div style="font-size: 0.875rem; color: var(--stone); margin-top: 0.25rem;">
                            Visual: {{{{ violation.visual_type }}}} ({{{{ violation.visual_id }}}})
                            <span v-if="violation.usage_count > 1"> · {{{{ violation.usage_count }}}} occurrences</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pages Tab -->
            <div v-if="activeTab === 'pages'" class="card">
                <h2 class="card-title">Page-by-Page Analysis</h2>

                <div v-for="page in pages" :key="page.id" class="page-card">
                    <div class="page-header">
                        <div>
                            <span class="page-name">{{{{ page.display_name || page.id }}}}</span>
                            <div class="compliance-indicator" style="margin-top: 0.25rem;">
                                <span class="compliance-dot" :class="page.violations.length === 0 ? 'dot-compliant' : 'dot-violation'"></span>
                                <span>{{{{ page.violations.length === 0 ? 'Compliant' : page.violations.length + ' violations' }}}}</span>
                            </div>
                        </div>
                        <div class="page-stats">
                            <span>{{{{ page.visuals.length }}}} visuals</span>
                            <span>{{{{ Object.keys(page.color_usage).length }}}} colors</span>
                            <span>{{{{ Object.keys(page.font_usage).length }}}} fonts</span>
                        </div>
                    </div>

                    <div v-if="Object.keys(page.color_usage).length > 0" style="margin-top: 0.75rem;">
                        <div style="font-size: 0.75rem; color: var(--stone); margin-bottom: 0.25rem;">Colors used:</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                            <div v-for="(count, color) in page.color_usage"
                                 :key="color"
                                 :style="{{backgroundColor: color, width: '20px', height: '20px', borderRadius: '4px', border: '1px solid rgba(0,0,0,0.1)'}}"
                                 :title="color + ' (' + count + ' uses)'">
                            </div>
                        </div>
                    </div>

                    <div v-if="page.violations.length > 0" style="margin-top: 0.75rem;">
                        <div style="font-size: 0.75rem; color: var(--warning); margin-bottom: 0.25rem;">
                            Violations on this page:
                        </div>
                        <div style="font-size: 0.875rem; color: var(--stone);">
                            <span v-for="(v, i) in page.violations.slice(0, 3)" :key="i">
                                {{{{ v.detail }}}}{{{{ i < Math.min(page.violations.length, 3) - 1 ? ', ' : '' }}}}
                            </span>
                            <span v-if="page.violations.length > 3">
                                and {{{{ page.violations.length - 3 }}}} more...
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <footer style="text-align: center; padding: 2rem; color: var(--stone); font-size: 0.875rem;">
            Generated by MCP-PowerBi-Finvision Theme Compliance Analyzer
        </footer>
    </div>

    <script>
        const analysisData = {data_json};

        const {{ createApp }} = Vue;

        createApp({{
            data() {{
                return {{
                    modelName: analysisData.modelName,
                    timestamp: analysisData.timestamp,
                    summary: analysisData.summary || {{}},
                    theme: analysisData.theme || {{}},
                    themeSource: analysisData.themeSource || 'Unknown',
                    pages: analysisData.pages || [],
                    colorAnalysis: analysisData.colorAnalysis || {{}},
                    fontAnalysis: analysisData.fontAnalysis || {{}},
                    visualAnalysis: analysisData.visualAnalysis || {{}},
                    violations: analysisData.violations || [],
                    complianceScore: analysisData.complianceScore || 0,
                    activeTab: 'overview',
                    violationSearch: '',
                    violationFilter: 'all'
                }};
            }},
            computed: {{
                formattedTimestamp() {{
                    return new Date(this.timestamp).toLocaleString();
                }},
                scoreClass() {{
                    if (this.complianceScore >= 90) return 'score-excellent';
                    if (this.complianceScore >= 75) return 'score-good';
                    if (this.complianceScore >= 50) return 'score-warning';
                    return 'score-poor';
                }},
                scoreLabel() {{
                    if (this.complianceScore >= 90) return 'Excellent Theme Compliance';
                    if (this.complianceScore >= 75) return 'Good Theme Compliance';
                    if (this.complianceScore >= 50) return 'Needs Improvement';
                    return 'Poor Theme Compliance';
                }},
                scoreCircleStyle() {{
                    const circumference = 2 * Math.PI * 88;
                    const offset = circumference - (this.complianceScore / 100) * circumference;
                    let color = '#9B2C2C';
                    if (this.complianceScore >= 90) color = '#606C38';
                    else if (this.complianceScore >= 75) color = '#7CB342';
                    else if (this.complianceScore >= 50) color = '#BC6C25';
                    return {{
                        stroke: color,
                        strokeDasharray: circumference,
                        strokeDashoffset: offset
                    }};
                }},
                nonThemeColors() {{
                    // Consolidate violations by unique color value
                    const colorMap = {{}};
                    this.violations
                        .filter(v => v.type === 'non_theme_color')
                        .forEach(v => {{
                            const color = v.value.toUpperCase();
                            if (!colorMap[color]) {{
                                colorMap[color] = {{
                                    value: v.value,
                                    usage_count: 0,
                                    visual_count: 0
                                }};
                            }}
                            colorMap[color].usage_count += v.usage_count || 1;
                            colorMap[color].visual_count += 1;
                        }});
                    // Sort by usage count descending
                    return Object.values(colorMap).sort((a, b) => b.usage_count - a.usage_count);
                }},
                nonThemeFonts() {{
                    // Consolidate violations by unique font value
                    const fontMap = {{}};
                    this.violations
                        .filter(v => v.type === 'non_theme_font')
                        .forEach(v => {{
                            const font = v.value.toLowerCase();
                            if (!fontMap[font]) {{
                                fontMap[font] = {{
                                    value: v.value,
                                    usage_count: 0,
                                    visual_count: 0
                                }};
                            }}
                            fontMap[font].usage_count += v.usage_count || 1;
                            fontMap[font].visual_count += 1;
                        }});
                    // Sort by usage count descending
                    return Object.values(fontMap).sort((a, b) => b.usage_count - a.usage_count);
                }},
                filteredViolations() {{
                    let result = this.violations;

                    if (this.violationFilter !== 'all') {{
                        result = result.filter(v => v.severity === this.violationFilter);
                    }}

                    if (this.violationSearch) {{
                        const query = this.violationSearch.toLowerCase();
                        result = result.filter(v =>
                            v.detail.toLowerCase().includes(query) ||
                            v.page.toLowerCase().includes(query) ||
                            v.visual_type.toLowerCase().includes(query) ||
                            v.value.toLowerCase().includes(query)
                        );
                    }}

                    return result;
                }}
            }},
            methods: {{
                formatVisualType(type) {{
                    return type.replace(/([A-Z])/g, ' $1').trim();
                }},
                getColorVariation(hexColor, factor) {{
                    // Parse hex color
                    if (!hexColor || !hexColor.startsWith('#')) return hexColor;
                    const hex = hexColor.slice(1);
                    let r = parseInt(hex.substring(0, 2), 16);
                    let g = parseInt(hex.substring(2, 4), 16);
                    let b = parseInt(hex.substring(4, 6), 16);

                    if (factor > 0) {{
                        // Tint (lighter) - mix with white
                        r = Math.round(r + (255 - r) * factor);
                        g = Math.round(g + (255 - g) * factor);
                        b = Math.round(b + (255 - b) * factor);
                    }} else {{
                        // Shade (darker) - multiply
                        const f = 1 + factor; // factor is negative, so this reduces
                        r = Math.round(r * f);
                        g = Math.round(g * f);
                        b = Math.round(b * f);
                    }}

                    // Clamp and convert back to hex
                    r = Math.max(0, Math.min(255, r));
                    g = Math.max(0, Math.min(255, g));
                    b = Math.max(0, Math.min(255, b));
                    return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
                }}
            }}
        }}).mount('#app');
    </script>
</body>
</html>'''
