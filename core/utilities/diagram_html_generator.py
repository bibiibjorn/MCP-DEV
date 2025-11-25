"""
Professional HTML generator for dependency diagrams.
Creates interactive, beautifully styled Mermaid diagrams that open in browser.
"""

import os
import logging
import webbrowser
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_dependency_html(
    mermaid_code: str,
    measure_table: str,
    measure_name: str,
    metadata: Dict[str, Any] = None,
    auto_open: bool = True,
    referenced_measures: list = None,
    referenced_columns: list = None,
    used_by_measures: list = None
) -> Optional[str]:
    """
    Generate a professional HTML page with interactive Mermaid diagram.

    Args:
        mermaid_code: The Mermaid diagram code
        measure_table: Table containing the measure
        measure_name: Name of the measure
        metadata: Additional metadata (direction, depth, node_count, edge_count)
        auto_open: Whether to open the HTML in browser
        referenced_measures: List of (table, measure) tuples this measure depends on
        referenced_columns: List of (table, column) tuples this measure uses
        used_by_measures: List of {'table': ..., 'measure': ...} dicts of measures using this one
    """
    if not mermaid_code:
        return None

    metadata = metadata or {}
    direction = metadata.get('direction', 'bidirectional')
    depth = metadata.get('depth', 3)
    node_count = metadata.get('node_count', 0)
    edge_count = metadata.get('edge_count', 0)
    upstream_count = metadata.get('upstream_count', 0)
    downstream_count = metadata.get('downstream_count', 0)

    # Normalize data structures
    referenced_measures = referenced_measures or []
    referenced_columns = referenced_columns or []
    used_by_measures = used_by_measures or []

    # Generate JSON data for JavaScript
    import json
    ref_measures_json = json.dumps([{'table': t, 'name': m} for t, m in referenced_measures])
    ref_columns_json = json.dumps([{'table': t, 'name': c} for t, c in referenced_columns])
    used_by_json = json.dumps(used_by_measures)

    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{measure_name} - Dependency Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent: #6366f1;
            --accent-light: #818cf8;
            --accent-glow: rgba(99, 102, 241, 0.4);
            --success: #10b981;
            --warning: #f59e0b;
            --bg-dark: #09090b;
            --bg-card: rgba(24, 24, 27, 0.8);
            --bg-elevated: rgba(39, 39, 42, 0.6);
            --border: rgba(63, 63, 70, 0.5);
            --border-light: rgba(82, 82, 91, 0.3);
            --text: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
            overflow-x: hidden;
        }}

        /* Animated background */
        .bg-pattern {{
            position: fixed;
            inset: 0;
            z-index: -1;
            background:
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.15), transparent),
                radial-gradient(ellipse 60% 40% at 80% 100%, rgba(139, 92, 246, 0.1), transparent),
                radial-gradient(ellipse 40% 30% at 10% 60%, rgba(79, 172, 254, 0.08), transparent);
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
        }}

        /* Header Section */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 2rem;
            gap: 2rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .brand-icon {{
            width: 56px;
            height: 56px;
            background: var(--gradient-1);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
            animation: float 3s ease-in-out infinite;
        }}

        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-4px); }}
        }}

        .brand-text h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #a1a1aa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .brand-text span {{
            font-size: 0.875rem;
            color: var(--text-muted);
            font-weight: 400;
        }}

        .timestamp {{
            padding: 0.625rem 1rem;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 12px;
            font-size: 0.8125rem;
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
            backdrop-filter: blur(12px);
        }}

        /* Hero Card */
        .hero-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }}

        .hero-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent-light), transparent);
        }}

        .hero-label {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--accent-light);
            margin-bottom: 1rem;
        }}

        .hero-label::before {{
            content: '';
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            animation: pulse 2s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.5; transform: scale(1.2); }}
        }}

        .hero-title {{
            font-size: 2.5rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }}

        .hero-title .table-name {{
            color: var(--accent-light);
        }}

        .hero-title .measure-name {{
            color: var(--text);
        }}

        .hero-subtitle {{
            color: var(--text-muted);
            font-size: 1rem;
        }}

        /* Stats Row */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .stat-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .stat-card::after {{
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, transparent 40%, rgba(99, 102, 241, 0.05));
            opacity: 0;
            transition: opacity 0.3s;
        }}

        .stat-card:hover {{
            transform: translateY(-4px);
            border-color: var(--accent);
            box-shadow: 0 20px 40px -20px var(--accent-glow);
        }}

        .stat-card:hover::after {{
            opacity: 1;
        }}

        .stat-value {{
            font-size: 2.25rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }}

        .stat-card:nth-child(2) .stat-value {{
            background: var(--gradient-3);
            -webkit-background-clip: text;
            background-clip: text;
        }}

        .stat-card:nth-child(3) .stat-value {{
            background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
            -webkit-background-clip: text;
            background-clip: text;
        }}

        .stat-card:nth-child(4) .stat-value {{
            background: var(--gradient-2);
            -webkit-background-clip: text;
            background-clip: text;
        }}

        .stat-label {{
            font-size: 0.8125rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
            font-weight: 500;
        }}

        /* Diagram Container */
        .diagram-wrapper {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 24px;
            overflow: hidden;
            position: relative;
        }}

        .diagram-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
            background: var(--bg-elevated);
        }}

        .diagram-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
            font-size: 1rem;
        }}

        .diagram-title-icon {{
            width: 32px;
            height: 32px;
            background: var(--gradient-1);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }}

        .toolbar {{
            display: flex;
            gap: 0.5rem;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.625rem 1rem;
            font-size: 0.8125rem;
            font-weight: 500;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            font-family: inherit;
        }}

        .btn-ghost {{
            background: transparent;
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}

        .btn-ghost:hover {{
            background: var(--bg-elevated);
            color: var(--text);
            border-color: var(--border-light);
        }}

        .btn-primary {{
            background: var(--accent);
            color: white;
            box-shadow: 0 4px 12px var(--accent-glow);
        }}

        .btn-primary:hover {{
            background: var(--accent-light);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px var(--accent-glow);
        }}

        .diagram-content {{
            padding: 2rem;
            min-height: 800px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            background:
                radial-gradient(ellipse at center, rgba(99, 102, 241, 0.03), transparent 70%),
                linear-gradient(180deg, transparent, rgba(0,0,0,0.2));
            overflow: auto;
        }}

        .mermaid {{
            width: 100%;
            min-width: 1200px;
        }}

        .mermaid svg {{
            width: 100% !important;
            min-width: 1200px;
            height: auto !important;
            min-height: 600px;
            transition: transform 0.3s ease;
        }}

        /* Legend */
        .legend {{
            display: flex;
            justify-content: center;
            gap: 2.5rem;
            padding: 1.25rem;
            border-top: 1px solid var(--border);
            background: var(--bg-elevated);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.625rem;
            font-size: 0.8125rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 4px;
        }}

        .legend-measure {{ background: linear-gradient(135deg, #e1f5fe, #b3e5fc); border: 2px solid #01579b; }}
        .legend-column {{ background: linear-gradient(135deg, #f3e5f5, #e1bee7); border: 2px solid #7b1fa2; }}
        .legend-table {{ background: linear-gradient(135deg, #fff3e0, #ffe0b2); border: 2px solid #e65100; }}
        .legend-upstream {{ background: linear-gradient(135deg, #4CAF50, #81C784); border: 2px solid #388E3C; }}
        .legend-downstream {{ background: linear-gradient(135deg, #FF9800, #FFB74D); border: 2px solid #F57C00; }}
        .legend-root {{ background: linear-gradient(135deg, #2196F3, #64B5F6); border: 2px solid #1565C0; }}

        /* Dependency Panels */
        .panels-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .panel {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }}

        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.25rem;
            background: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
        }}

        .panel-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
            font-size: 0.9375rem;
        }}

        .panel-icon {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
        }}

        .panel-icon.upstream {{
            background: linear-gradient(135deg, #10b981, #34d399);
        }}

        .panel-icon.downstream {{
            background: linear-gradient(135deg, #f59e0b, #fbbf24);
        }}

        .panel-count {{
            background: var(--accent);
            color: white;
            font-size: 0.75rem;
            padding: 0.25rem 0.625rem;
            border-radius: 999px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .panel-search {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
        }}

        .search-input {{
            width: 100%;
            padding: 0.625rem 1rem;
            padding-left: 2.5rem;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text);
            font-size: 0.8125rem;
            font-family: inherit;
            transition: all 0.2s;
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }}

        .search-input::placeholder {{
            color: var(--text-muted);
        }}

        .search-wrapper {{
            position: relative;
        }}

        .search-wrapper::before {{
            content: '🔍';
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.875rem;
            pointer-events: none;
        }}

        .panel-content {{
            max-height: 400px;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }}

        .panel-content::-webkit-scrollbar {{
            width: 6px;
        }}

        .panel-content::-webkit-scrollbar-track {{
            background: transparent;
        }}

        .panel-content::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 3px;
        }}

        .panel-content::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}

        .table-group {{
            border-bottom: 1px solid var(--border);
        }}

        .table-group:last-child {{
            border-bottom: none;
        }}

        .table-group-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background: rgba(99, 102, 241, 0.05);
            cursor: pointer;
            transition: background 0.2s;
        }}

        .table-group-header:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}

        .table-group-name {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            color: var(--accent-light);
        }}

        .table-group-name::before {{
            content: '📁';
            font-size: 0.75rem;
        }}

        .table-group-count {{
            font-size: 0.75rem;
            color: var(--text-muted);
            background: var(--bg-elevated);
            padding: 0.125rem 0.5rem;
            border-radius: 999px;
        }}

        .table-group-items {{
            padding: 0.25rem 0;
        }}

        .table-group.collapsed .table-group-items {{
            display: none;
        }}

        .table-group-header .chevron {{
            transition: transform 0.2s;
            font-size: 0.75rem;
        }}

        .table-group.collapsed .chevron {{
            transform: rotate(-90deg);
        }}

        .item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem 0.5rem 2rem;
            font-size: 0.8125rem;
            color: var(--text-secondary);
            transition: all 0.2s;
        }}

        .item:hover {{
            background: var(--bg-elevated);
            color: var(--text);
        }}

        .item-icon {{
            font-size: 0.625rem;
            color: var(--accent);
        }}

        .item-name {{
            font-family: 'JetBrains Mono', monospace;
        }}

        .item.measure .item-icon {{ color: #01579b; }}
        .item.column .item-icon {{ color: #7b1fa2; }}

        .empty-state {{
            padding: 2rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        .empty-state-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            opacity: 0.5;
        }}

        .no-results {{
            padding: 1.5rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.8125rem;
            display: none;
        }}

        /* Responsive panels */
        @media (max-width: 1100px) {{
            .panels-container {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.8125rem;
        }}

        .footer strong {{
            color: var(--text-secondary);
        }}

        /* Responsive */
        @media (max-width: 900px) {{
            .stats-row {{ grid-template-columns: repeat(2, 1fr); }}
            .header {{ flex-direction: column; }}
            .hero-title {{ font-size: 1.75rem; }}
        }}

        @media (max-width: 600px) {{
            .container {{ padding: 1rem; }}
            .stats-row {{ grid-template-columns: 1fr; }}
            .toolbar {{ flex-wrap: wrap; }}
            .legend {{ flex-direction: column; align-items: center; gap: 1rem; }}
        }}
    </style>
</head>
<body>
    <div class="bg-pattern"></div>

    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="brand">
                <div class="brand-icon">📊</div>
                <div class="brand-text">
                    <h1>Dependency Analysis</h1>
                    <span>Power BI Model Explorer</span>
                </div>
            </div>
            <div class="timestamp">{timestamp}</div>
        </header>

        <!-- Hero Card -->
        <div class="hero-card">
            <div class="hero-label">Analyzing Measure</div>
            <h2 class="hero-title">
                <span class="table-name">{measure_table}</span><span class="measure-name">[{measure_name}]</span>
            </h2>
            <p class="hero-subtitle">Visualizing {direction} dependencies up to {depth} levels deep</p>
        </div>

        <!-- Stats -->
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">{len(referenced_measures) + len(referenced_columns)}</div>
                <div class="stat-label">Dependencies (Upstream)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(used_by_measures)}</div>
                <div class="stat-label">Used By (Downstream)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{node_count}</div>
                <div class="stat-label">Total Nodes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{edge_count}</div>
                <div class="stat-label">Connections</div>
            </div>
        </div>

        <!-- Dependency Panels -->
        <div class="panels-container">
            <!-- Dependencies Panel (Upstream - what this measure uses) -->
            <div class="panel" id="dependencies-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <div class="panel-icon upstream">⬆️</div>
                        <span>Dependencies (Upstream)</span>
                    </div>
                    <div class="panel-count" id="deps-count">{len(referenced_measures) + len(referenced_columns)}</div>
                </div>
                <div class="panel-search">
                    <div class="search-wrapper">
                        <input type="text" class="search-input" id="deps-search" placeholder="Filter dependencies..." oninput="filterPanel('deps')">
                    </div>
                </div>
                <div class="panel-content" id="deps-content">
                    <!-- Content populated by JavaScript -->
                </div>
                <div class="no-results" id="deps-no-results">No matching items found</div>
            </div>

            <!-- Used By Panel (Downstream - what uses this measure) -->
            <div class="panel" id="used-by-panel">
                <div class="panel-header">
                    <div class="panel-title">
                        <div class="panel-icon downstream">⬇️</div>
                        <span>Used By (Downstream)</span>
                    </div>
                    <div class="panel-count" id="used-by-count">{len(used_by_measures)}</div>
                </div>
                <div class="panel-search">
                    <div class="search-wrapper">
                        <input type="text" class="search-input" id="used-by-search" placeholder="Filter measures..." oninput="filterPanel('used-by')">
                    </div>
                </div>
                <div class="panel-content" id="used-by-content">
                    <!-- Content populated by JavaScript -->
                </div>
                <div class="no-results" id="used-by-no-results">No matching items found</div>
            </div>
        </div>

        <!-- Diagram -->
        <div class="diagram-wrapper">
            <div class="diagram-header">
                <div class="diagram-title">
                    <div class="diagram-title-icon">🔗</div>
                    <span>Dependency Flow</span>
                </div>
                <div class="toolbar">
                    <button class="btn btn-ghost" onclick="zoomIn()">🔍+ Zoom In</button>
                    <button class="btn btn-ghost" onclick="zoomOut()">🔍- Zoom Out</button>
                    <button class="btn btn-ghost" onclick="resetZoom()">↺ Reset</button>
                    <button class="btn btn-primary" onclick="downloadSVG()">💾 Download SVG</button>
                </div>
            </div>
            <div class="diagram-content" id="diagram-content">
                <pre class="mermaid" id="mermaid-diagram">
{mermaid_code}
                </pre>
            </div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-dot legend-root"></div>
                    <span>Target Measure</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot legend-upstream"></div>
                    <span>Dependencies (Upstream)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot legend-downstream"></div>
                    <span>Used By (Downstream)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot legend-column"></div>
                    <span>Columns</span>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            Generated by <strong>MCP-PowerBi-Finvision</strong>
        </footer>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#6366f1',
                primaryTextColor: '#fafafa',
                primaryBorderColor: '#818cf8',
                lineColor: '#64748b',
                secondaryColor: '#18181b',
                tertiaryColor: '#27272a',
                background: '#09090b',
                mainBkg: '#18181b',
                nodeBorder: '#818cf8',
                clusterBkg: 'rgba(99, 102, 241, 0.15)',
                clusterBorder: '#6366f1',
                titleColor: '#fafafa',
                edgeLabelBackground: '#18181b',
                nodeTextColor: '#fafafa',
                fontSize: '16px',
                fontFamily: 'Inter, sans-serif'
            }},
            flowchart: {{
                htmlLabels: true,
                curve: 'basis',
                nodeSpacing: 80,
                rankSpacing: 120,
                padding: 30,
                useMaxWidth: false,
                defaultRenderer: 'dagre-wrapper',
                wrappingWidth: 200
            }},
            securityLevel: 'loose'
        }});

        // Force re-render with larger size after initial load
        setTimeout(() => {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                svg.style.minWidth = '1200px';
                svg.style.minHeight = '600px';
            }}
        }}, 500);

        let currentZoom = 1;
        const zoomStep = 0.15;

        function zoomIn() {{
            currentZoom = Math.min(3, currentZoom + zoomStep);
            applyZoom();
        }}

        function zoomOut() {{
            currentZoom = Math.max(0.3, currentZoom - zoomStep);
            applyZoom();
        }}

        function resetZoom() {{
            currentZoom = 1;
            applyZoom();
        }}

        function applyZoom() {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                svg.style.transform = `scale(${{currentZoom}})`;
                svg.style.transformOrigin = 'center center';
            }}
        }}

        function downloadSVG() {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = '{measure_table}_{measure_name}_dependencies.svg';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
        }}

        // Panel data
        const referencedMeasures = {ref_measures_json};
        const referencedColumns = {ref_columns_json};
        const usedByMeasures = {used_by_json};

        // Group items by table
        function groupByTable(items, nameKey = 'name') {{
            const groups = {{}};
            items.forEach(item => {{
                const table = item.table || 'Unknown';
                if (!groups[table]) {{
                    groups[table] = [];
                }}
                groups[table].push(item[nameKey] || item.measure || item.name);
            }});
            return groups;
        }}

        // Render panel content
        function renderPanelContent(containerId, groups, itemType = 'measure') {{
            const container = document.getElementById(containerId);
            if (!container) return;

            const tables = Object.keys(groups).sort();
            if (tables.length === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">${{itemType === 'measure' ? '📊' : '📁'}}</div>
                        <div>No ${{itemType === 'measure' ? 'measures' : 'columns'}} found</div>
                    </div>
                `;
                return;
            }}

            let html = '';
            tables.forEach(table => {{
                const items = groups[table].sort();
                html += `
                    <div class="table-group" data-table="${{table.toLowerCase()}}">
                        <div class="table-group-header" onclick="toggleGroup(this)">
                            <span class="table-group-name">${{table}}</span>
                            <div style="display: flex; align-items: center; gap: 0.5rem;">
                                <span class="table-group-count">${{items.length}}</span>
                                <span class="chevron">▼</span>
                            </div>
                        </div>
                        <div class="table-group-items">
                            ${{items.map(name => `
                                <div class="item ${{itemType}}" data-name="${{name.toLowerCase()}}" data-table="${{table.toLowerCase()}}">
                                    <span class="item-icon">●</span>
                                    <span class="item-name">${{name}}</span>
                                </div>
                            `).join('')}}
                        </div>
                    </div>
                `;
            }});

            container.innerHTML = html;
        }}

        // Toggle table group collapse
        function toggleGroup(header) {{
            const group = header.closest('.table-group');
            if (group) {{
                group.classList.toggle('collapsed');
            }}
        }}

        // Filter panel content
        function filterPanel(panelType) {{
            const searchInput = document.getElementById(`${{panelType}}-search`);
            const container = document.getElementById(`${{panelType}}-content`);
            const noResults = document.getElementById(`${{panelType}}-no-results`);

            if (!searchInput || !container) return;

            const filter = searchInput.value.toLowerCase().trim();
            const groups = container.querySelectorAll('.table-group');
            let hasVisibleItems = false;

            groups.forEach(group => {{
                const items = group.querySelectorAll('.item');
                let groupHasVisible = false;

                items.forEach(item => {{
                    const name = item.dataset.name || '';
                    const table = item.dataset.table || '';
                    const matches = !filter || name.includes(filter) || table.includes(filter);
                    item.style.display = matches ? 'flex' : 'none';
                    if (matches) {{
                        groupHasVisible = true;
                        hasVisibleItems = true;
                    }}
                }});

                // Show/hide group based on matching items
                group.style.display = groupHasVisible ? 'block' : 'none';

                // Auto-expand groups when filtering
                if (filter && groupHasVisible) {{
                    group.classList.remove('collapsed');
                }}
            }});

            // Show no results message
            if (noResults) {{
                noResults.style.display = hasVisibleItems ? 'none' : 'block';
            }}

            // Update visible count
            updateVisibleCount(panelType, hasVisibleItems ? countVisibleItems(container) : 0);
        }}

        // Count visible items
        function countVisibleItems(container) {{
            return container.querySelectorAll('.item[style*="display: flex"], .item:not([style*="display"])').length;
        }}

        // Update count badge
        function updateVisibleCount(panelType, count) {{
            const countEl = document.getElementById(`${{panelType}}-count`);
            if (countEl) {{
                const original = panelType === 'deps'
                    ? referencedMeasures.length + referencedColumns.length
                    : usedByMeasures.length;
                countEl.textContent = count < original ? `${{count}}/${{original}}` : original;
            }}
        }}

        // Initialize panels on load
        document.addEventListener('DOMContentLoaded', function() {{
            // Combine measures and columns for dependencies panel
            const depsGroups = {{}};

            // Add measures
            referencedMeasures.forEach(item => {{
                const table = item.table || 'Unknown';
                if (!depsGroups[table]) depsGroups[table] = {{ measures: [], columns: [] }};
                depsGroups[table].measures.push(item.name);
            }});

            // Add columns
            referencedColumns.forEach(item => {{
                const table = item.table || 'Unknown';
                if (!depsGroups[table]) depsGroups[table] = {{ measures: [], columns: [] }};
                depsGroups[table].columns.push(item.name);
            }});

            // Render dependencies panel with both measures and columns
            const depsContainer = document.getElementById('deps-content');
            if (depsContainer) {{
                const tables = Object.keys(depsGroups).sort();
                if (tables.length === 0) {{
                    depsContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📊</div>
                            <div>No dependencies found</div>
                            <div style="font-size: 0.75rem; margin-top: 0.25rem;">This measure doesn't reference any other measures or columns</div>
                        </div>
                    `;
                }} else {{
                    let html = '';
                    tables.forEach(table => {{
                        const data = depsGroups[table];
                        const items = [
                            ...data.measures.map(m => ({{ name: m, type: 'measure' }})),
                            ...data.columns.map(c => ({{ name: c, type: 'column' }}))
                        ].sort((a, b) => a.name.localeCompare(b.name));

                        html += `
                            <div class="table-group" data-table="${{table.toLowerCase()}}">
                                <div class="table-group-header" onclick="toggleGroup(this)">
                                    <span class="table-group-name">${{table}}</span>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <span class="table-group-count">${{items.length}}</span>
                                        <span class="chevron">▼</span>
                                    </div>
                                </div>
                                <div class="table-group-items">
                                    ${{items.map(item => `
                                        <div class="item ${{item.type}}" data-name="${{item.name.toLowerCase()}}" data-table="${{table.toLowerCase()}}">
                                            <span class="item-icon">${{item.type === 'measure' ? '●' : '◇'}}</span>
                                            <span class="item-name">${{item.name}}</span>
                                            <span style="color: var(--text-muted); font-size: 0.6875rem; margin-left: auto;">${{item.type}}</span>
                                        </div>
                                    `).join('')}}
                                </div>
                            </div>
                        `;
                    }});
                    depsContainer.innerHTML = html;
                }}
            }}

            // Render used-by panel
            const usedByGroups = groupByTable(usedByMeasures, 'measure');
            const usedByContainer = document.getElementById('used-by-content');
            if (usedByContainer) {{
                const tables = Object.keys(usedByGroups).sort();
                if (tables.length === 0) {{
                    usedByContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📭</div>
                            <div>No measures use this measure</div>
                            <div style="font-size: 0.75rem; margin-top: 0.25rem;">This measure is not referenced by any other measures</div>
                        </div>
                    `;
                }} else {{
                    let html = '';
                    tables.forEach(table => {{
                        const items = usedByGroups[table].sort();
                        html += `
                            <div class="table-group" data-table="${{table.toLowerCase()}}">
                                <div class="table-group-header" onclick="toggleGroup(this)">
                                    <span class="table-group-name">${{table}}</span>
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <span class="table-group-count">${{items.length}}</span>
                                        <span class="chevron">▼</span>
                                    </div>
                                </div>
                                <div class="table-group-items">
                                    ${{items.map(name => `
                                        <div class="item measure" data-name="${{name.toLowerCase()}}" data-table="${{table.toLowerCase()}}">
                                            <span class="item-icon">●</span>
                                            <span class="item-name">${{name}}</span>
                                        </div>
                                    `).join('')}}
                                </div>
                            </div>
                        `;
                    }});
                    usedByContainer.innerHTML = html;
                }}
            }}
        }});
    </script>
</body>
</html>'''

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        exports_dir = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "exports")
        os.makedirs(exports_dir, exist_ok=True)

        html_path = os.path.join(exports_dir, "dependency_diagram.html")

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Generated dependency diagram HTML: {html_path}")

        if auto_open:
            webbrowser.open(f'file:///{html_path.replace(os.sep, "/")}')

        return html_path

    except Exception as e:
        logger.error(f"Failed to generate HTML diagram: {e}")
        return None
