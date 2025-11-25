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
    auto_open: bool = True
) -> Optional[str]:
    """
    Generate a professional HTML page with interactive Mermaid diagram.
    """
    if not mermaid_code:
        return None

    metadata = metadata or {}
    direction = metadata.get('direction', 'upstream')
    depth = metadata.get('depth', 3)
    node_count = metadata.get('node_count', 0)
    edge_count = metadata.get('edge_count', 0)

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
                <div class="stat-value">{node_count}</div>
                <div class="stat-label">Total Nodes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{edge_count}</div>
                <div class="stat-label">Connections</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{depth}</div>
                <div class="stat-label">Depth Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{direction.title()}</div>
                <div class="stat-label">Direction</div>
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
                    <div class="legend-dot legend-measure"></div>
                    <span>Measures</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot legend-column"></div>
                    <span>Columns</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot legend-table"></div>
                    <span>Table Groups</span>
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
