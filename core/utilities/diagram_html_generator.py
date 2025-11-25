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

    # Helper to create Mermaid-compatible node IDs (must match dependency_analyzer.py)
    import re
    def sanitize_node_id(name: str) -> str:
        result = name.replace("[", "_").replace("]", "").replace(" ", "_")
        result = result.replace("-", "_").replace("/", "_").replace("\\", "_")
        result = result.replace("(", "_").replace(")", "_").replace("%", "pct")
        result = result.replace("&", "and").replace("'", "").replace('"', "")
        result = result.replace(".", "_").replace(",", "_").replace(":", "_")
        result = result.replace("+", "plus").replace("*", "x").replace("=", "eq")
        result = result.replace("<", "lt").replace(">", "gt").replace("!", "not")
        result = result.replace("#", "num").replace("@", "at").replace("$", "dollar")
        result = re.sub(r'[^a-zA-Z0-9_]', '', result)
        result = re.sub(r'_+', '_', result)
        if result and not result[0].isalpha():
            result = 'n_' + result
        return result.strip('_') or 'node'

    # Extract ALL node IDs from the mermaid code (includes transitive dependencies)
    # This ensures we catch all levels of dependencies, not just direct ones
    upstream_node_ids = []
    downstream_node_ids = []
    root_node_id = sanitize_node_id(f"{measure_table}[{measure_name}]")

    # Parse mermaid code to find all nodes in Dependencies vs Dependents subgraphs
    in_upstream_section = False
    in_downstream_section = False

    for line in mermaid_code.split('\n'):
        line_stripped = line.strip()

        # Track which subgraph we're in
        if 'subgraph Dependencies' in line:
            in_upstream_section = True
            in_downstream_section = False
        elif 'subgraph Dependents' in line:
            in_downstream_section = True
            in_upstream_section = False
        elif line_stripped == 'end':
            in_upstream_section = False
            in_downstream_section = False

        # Extract node IDs from node definitions (lines with [...] or ["..."])
        if '[' in line and (':::' in line or ']' in line):
            # Extract the node ID (part before the [)
            parts = line_stripped.split('[')
            if parts:
                node_id = parts[0].strip()
                if node_id and node_id != 'subgraph':
                    if in_upstream_section:
                        upstream_node_ids.append(node_id)
                    elif in_downstream_section:
                        downstream_node_ids.append(node_id)

    # Also add direct dependencies as fallback
    for tbl, name in referenced_measures:
        node_key = f"{tbl}[{name}]"
        node_id = sanitize_node_id(node_key)
        if node_id not in upstream_node_ids:
            upstream_node_ids.append(node_id)
    for tbl, name in referenced_columns:
        node_key = f"{tbl}[{name}]"
        node_id = sanitize_node_id(node_key)
        if node_id not in upstream_node_ids:
            upstream_node_ids.append(node_id)

    for item in used_by_measures:
        tbl = item.get('table', '')
        name = item.get('measure', '')
        if tbl and name:
            node_key = f"{tbl}[{name}]"
            node_id = sanitize_node_id(node_key)
            if node_id not in downstream_node_ids:
                downstream_node_ids.append(node_id)

    # Generate JSON data for JavaScript
    import json
    ref_measures_json = json.dumps([{'table': t, 'name': m} for t, m in referenced_measures])
    ref_columns_json = json.dumps([{'table': t, 'name': c} for t, c in referenced_columns])
    used_by_json = json.dumps(used_by_measures)
    upstream_ids_json = json.dumps(upstream_node_ids)
    downstream_ids_json = json.dumps(downstream_node_ids)
    root_id_json = json.dumps(root_node_id)

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

        .filter-group {{
            display: flex;
            gap: 0.25rem;
            background: var(--bg-dark);
            padding: 0.25rem;
            border-radius: 10px;
            border: 1px solid var(--border);
        }}

        .btn-filter {{
            background: transparent;
            color: var(--text-muted);
            border: none;
            padding: 0.5rem 0.875rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.2s;
        }}

        .btn-filter:hover {{
            color: var(--text);
            background: var(--bg-elevated);
        }}

        .btn-filter.active {{
            background: var(--accent);
            color: white;
            box-shadow: 0 2px 8px var(--accent-glow);
        }}

        .toolbar-divider {{
            width: 1px;
            background: var(--border);
            margin: 0 0.5rem;
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

        /* Node click highlight styles */
        .mermaid svg g.node {{
            cursor: pointer;
            transition: opacity 0.3s ease, filter 0.3s ease;
        }}

        .mermaid svg g.node:hover {{
            filter: brightness(1.2);
        }}

        .mermaid svg.flow-highlight-active g.node {{
            opacity: 0.2;
        }}

        .mermaid svg.flow-highlight-active g.node.flow-highlighted {{
            opacity: 1;
            filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.8));
        }}

        .mermaid svg.flow-highlight-active g.node.flow-selected {{
            opacity: 1;
            filter: drop-shadow(0 0 12px rgba(255, 255, 255, 0.9));
        }}

        .mermaid svg.flow-highlight-active g.edgePath {{
            opacity: 0.1;
        }}

        .mermaid svg.flow-highlight-active g.edgePath.flow-highlighted {{
            opacity: 1;
        }}

        .mermaid svg.flow-highlight-active g.edgePath.flow-highlighted path {{
            stroke-width: 3px !important;
            stroke: #6366f1 !important;
        }}

        .mermaid svg.flow-highlight-active g.cluster {{
            opacity: 0.3;
        }}

        .mermaid svg.flow-highlight-active g.cluster.flow-highlighted {{
            opacity: 1;
        }}

        /* Click hint tooltip */
        .click-hint {{
            position: absolute;
            bottom: 1rem;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(99, 102, 241, 0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 500;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 10;
        }}

        .click-hint.visible {{
            opacity: 1;
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
                <div class="stat-label">Diagram Elements</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{edge_count}</div>
                <div class="stat-label">Relationships</div>
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
                    <div class="filter-group">
                        <button class="btn btn-filter active" id="filter-all" onclick="setFilter('all')">All</button>
                        <button class="btn btn-filter" id="filter-upstream" onclick="setFilter('upstream')">⬆ Upstream</button>
                        <button class="btn btn-filter" id="filter-downstream" onclick="setFilter('downstream')">⬇ Downstream</button>
                    </div>
                    <div class="toolbar-divider"></div>
                    <button class="btn btn-ghost" id="clear-selection-btn" onclick="clearFlowHighlight()" style="display: none;">✕ Clear Selection</button>
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
                <div class="click-hint" id="click-hint">Click any node to highlight its complete flow. Click again or press Escape to clear.</div>
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
            // Also reset viewBox to original if filter is 'all'
            if (currentFilter === 'all') {{
                const svg = document.querySelector('.mermaid svg');
                if (svg && svg.dataset.originalViewBox) {{
                    svg.setAttribute('viewBox', svg.dataset.originalViewBox);
                }}
            }}
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

        // Node ID lists for filtering (pre-computed to match Mermaid IDs)
        const upstreamNodeIds = {upstream_ids_json};
        const downstreamNodeIds = {downstream_ids_json};
        const rootNodeId = {root_id_json};

        // Filter functionality for upstream/downstream view
        let currentFilter = 'all';

        function setFilter(filter) {{
            currentFilter = filter;

            // Update button states
            document.querySelectorAll('.btn-filter').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`filter-${{filter}}`).classList.add('active');

            // Get SVG elements
            const svg = document.querySelector('.mermaid svg');
            if (!svg) return;

            const allNodes = svg.querySelectorAll('g.node');
            const allEdges = svg.querySelectorAll('g.edgePath');
            const allClusters = svg.querySelectorAll('g.cluster');

            // Helper to check if node ID matches any in a list
            function nodeMatchesList(nodeId, idList) {{
                // Mermaid prefixes node IDs with 'flowchart-' and adds suffixes
                // Check if any of our IDs are contained in the node ID
                return idList.some(id => nodeId.includes(id));
            }}

            // Apply visibility to nodes
            allNodes.forEach(node => {{
                const nodeId = node.id || '';
                const isUpstream = nodeMatchesList(nodeId, upstreamNodeIds);
                const isDownstream = nodeMatchesList(nodeId, downstreamNodeIds);
                const isRoot = nodeId.includes(rootNodeId);

                if (filter === 'all') {{
                    node.style.display = '';
                    node.style.opacity = '1';
                }} else if (filter === 'upstream') {{
                    node.style.display = (isUpstream || isRoot) ? '' : 'none';
                    node.style.opacity = (isUpstream || isRoot) ? '1' : '0';
                }} else if (filter === 'downstream') {{
                    node.style.display = (isDownstream || isRoot) ? '' : 'none';
                    node.style.opacity = (isDownstream || isRoot) ? '1' : '0';
                }}
            }});

            // Apply visibility to clusters (subgraph boxes)
            allClusters.forEach(cluster => {{
                const texts = cluster.querySelectorAll('text, .nodeLabel, span');
                let clusterLabel = '';
                texts.forEach(t => {{ clusterLabel += ' ' + (t.textContent || ''); }});
                clusterLabel = clusterLabel.toLowerCase();

                const isUpstreamCluster = clusterLabel.includes('dependencies') && !clusterLabel.includes('dependents');
                const isDownstreamCluster = clusterLabel.includes('dependents');

                if (filter === 'all') {{
                    cluster.style.display = '';
                    cluster.style.opacity = '1';
                }} else if (filter === 'upstream') {{
                    cluster.style.display = isDownstreamCluster ? 'none' : '';
                    cluster.style.opacity = isDownstreamCluster ? '0' : '1';
                }} else if (filter === 'downstream') {{
                    cluster.style.display = isUpstreamCluster ? 'none' : '';
                    cluster.style.opacity = isUpstreamCluster ? '0' : '1';
                }}
            }});

            // Build a map of visible node IDs for edge filtering
            const visibleNodeIds = new Set();
            allNodes.forEach(node => {{
                if (node.style.display !== 'none') {{
                    visibleNodeIds.add(node.id);
                }}
            }});

            // Apply visibility to edges - hide if either endpoint is hidden
            allEdges.forEach(edge => {{
                let shouldShow = filter === 'all';

                if (filter !== 'all') {{
                    // Check the edge's marker-end and marker-start to find connected nodes
                    // Mermaid edges have class like 'LS-nodeId' and 'LE-nodeId' for start/end
                    const classList = Array.from(edge.classList || []);
                    let startNodeId = '';
                    let endNodeId = '';

                    classList.forEach(cls => {{
                        if (cls.startsWith('LS-')) startNodeId = cls.substring(3);
                        if (cls.startsWith('LE-')) endNodeId = cls.substring(3);
                    }});

                    // Also check data attributes
                    const edgeStart = edge.getAttribute('data-start') || startNodeId;
                    const edgeEnd = edge.getAttribute('data-end') || endNodeId;

                    // Find actual connected nodes by checking which nodes have matching IDs
                    let startsFromVisible = false;
                    let endsAtVisible = false;

                    allNodes.forEach(node => {{
                        const nodeId = node.id || '';
                        const isVisible = node.style.display !== 'none';

                        // Check if this node matches the edge endpoints
                        if (edgeStart && nodeId.includes(edgeStart)) {{
                            startsFromVisible = isVisible;
                        }}
                        if (edgeEnd && nodeId.includes(edgeEnd)) {{
                            endsAtVisible = isVisible;
                        }}
                    }});

                    // Show edge only if both connected nodes are visible
                    // If we couldn't determine endpoints, use ID-based matching as fallback
                    if (edgeStart || edgeEnd) {{
                        shouldShow = startsFromVisible && endsAtVisible;
                    }} else {{
                        // Fallback: check edge ID against node IDs
                        const edgeId = edge.id || '';
                        if (filter === 'upstream') {{
                            const connectsToDownstream = downstreamNodeIds.some(id => edgeId.includes(id));
                            shouldShow = !connectsToDownstream;
                        }} else if (filter === 'downstream') {{
                            const connectsToUpstream = upstreamNodeIds.some(id => edgeId.includes(id));
                            shouldShow = !connectsToUpstream;
                        }}
                    }}
                }}

                edge.style.display = shouldShow ? '' : 'none';
                edge.style.opacity = shouldShow ? '1' : '0';

                // Also hide the edge path itself
                const path = edge.querySelector('path');
                if (path) {{
                    path.style.display = shouldShow ? '' : 'none';
                    path.style.opacity = shouldShow ? '1' : '0';
                }}
            }});

            // Hide all edge-related elements based on the full element markup
            const hiddenNodeIds = filter === 'upstream' ? downstreamNodeIds :
                                  filter === 'downstream' ? upstreamNodeIds : [];

            // Helper to check if an element references any hidden node
            function referencesHiddenNode(element) {{
                if (hiddenNodeIds.length === 0) return false;
                const html = element.outerHTML || '';
                return hiddenNodeIds.some(id => html.includes(id));
            }}

            // Hide standalone paths
            svg.querySelectorAll('path').forEach(path => {{
                if (path.closest('g.edgePath')) return; // Already handled above

                if (filter === 'all') {{
                    path.style.display = '';
                    path.style.opacity = '1';
                }} else {{
                    const shouldHide = referencesHiddenNode(path);
                    path.style.display = shouldHide ? 'none' : '';
                    path.style.opacity = shouldHide ? '0' : '1';
                }}
            }});

            // Hide edge labels
            svg.querySelectorAll('g.edgeLabel').forEach(label => {{
                if (filter === 'all') {{
                    label.style.display = '';
                    label.style.opacity = '1';
                }} else {{
                    const shouldHide = referencesHiddenNode(label);
                    label.style.display = shouldHide ? 'none' : '';
                    label.style.opacity = shouldHide ? '0' : '1';
                }}
            }});

            // Alternative: hide edges by checking marker references
            svg.querySelectorAll('[marker-end], [marker-start]').forEach(el => {{
                if (el.closest('g.edgePath')) return; // Already handled

                if (filter === 'all') {{
                    el.style.display = '';
                    el.style.opacity = '1';
                }} else {{
                    const shouldHide = referencesHiddenNode(el);
                    el.style.display = shouldHide ? 'none' : '';
                    el.style.opacity = shouldHide ? '0' : '1';
                }}
            }});

            // Update panel visibility
            const depsPanel = document.getElementById('dependencies-panel');
            const usedByPanel = document.getElementById('used-by-panel');

            if (depsPanel && usedByPanel) {{
                if (filter === 'upstream') {{
                    depsPanel.style.display = '';
                    usedByPanel.style.display = 'none';
                }} else if (filter === 'downstream') {{
                    depsPanel.style.display = 'none';
                    usedByPanel.style.display = '';
                }} else {{
                    depsPanel.style.display = '';
                    usedByPanel.style.display = '';
                }}
            }}

            // Adjust SVG viewBox to crop to visible content only
            setTimeout(() => {{
                // Store original viewBox if not already stored
                if (!svg.dataset.originalViewBox) {{
                    svg.dataset.originalViewBox = svg.getAttribute('viewBox') || '';
                }}

                if (filter === 'all') {{
                    // Reset to original viewBox
                    if (svg.dataset.originalViewBox) {{
                        svg.setAttribute('viewBox', svg.dataset.originalViewBox);
                    }}
                }} else {{
                    // Calculate bounding box of all visible elements
                    let minX = Infinity, minY = Infinity;
                    let maxX = -Infinity, maxY = -Infinity;

                    // Get bounds of visible nodes
                    allNodes.forEach(node => {{
                        if (node.style.display !== 'none') {{
                            try {{
                                const bbox = node.getBBox();
                                minX = Math.min(minX, bbox.x);
                                minY = Math.min(minY, bbox.y);
                                maxX = Math.max(maxX, bbox.x + bbox.width);
                                maxY = Math.max(maxY, bbox.y + bbox.height);
                            }} catch (e) {{ /* ignore */ }}
                        }}
                    }});

                    // Get bounds of visible clusters
                    allClusters.forEach(cluster => {{
                        if (cluster.style.display !== 'none') {{
                            try {{
                                const bbox = cluster.getBBox();
                                minX = Math.min(minX, bbox.x);
                                minY = Math.min(minY, bbox.y);
                                maxX = Math.max(maxX, bbox.x + bbox.width);
                                maxY = Math.max(maxY, bbox.y + bbox.height);
                            }} catch (e) {{ /* ignore */ }}
                        }}
                    }});

                    // Get bounds of visible edges
                    allEdges.forEach(edge => {{
                        if (edge.style.display !== 'none') {{
                            try {{
                                const bbox = edge.getBBox();
                                minX = Math.min(minX, bbox.x);
                                minY = Math.min(minY, bbox.y);
                                maxX = Math.max(maxX, bbox.x + bbox.width);
                                maxY = Math.max(maxY, bbox.y + bbox.height);
                            }} catch (e) {{ /* ignore */ }}
                        }}
                    }});

                    // Only update viewBox if we found visible elements
                    if (minX !== Infinity && minY !== Infinity) {{
                        // Add padding around the visible area
                        const padding = 50;
                        const newX = minX - padding;
                        const newY = minY - padding;
                        const newWidth = (maxX - minX) + (padding * 2);
                        const newHeight = (maxY - minY) + (padding * 2);

                        svg.setAttribute('viewBox', `${{newX}} ${{newY}} ${{newWidth}} ${{newHeight}}`);
                    }}
                }}

                // Scroll diagram container to top
                const diagramContent = document.getElementById('diagram-content');
                if (diagramContent) {{
                    diagramContent.scrollTop = 0;
                    diagramContent.scrollLeft = 0;
                }}
            }}, 150);
        }}

        // ═══════════════════════════════════════════════════════════════════════
        // CLICK-TO-HIGHLIGHT FLOW FUNCTIONALITY
        // ═══════════════════════════════════════════════════════════════════════

        let flowHighlightActive = false;
        let selectedNodeId = null;
        let edgeGraph = {{ incoming: {{}}, outgoing: {{}} }}; // Node relationships

        // Build edge graph after Mermaid renders
        function buildEdgeGraph() {{
            const svg = document.querySelector('.mermaid svg');
            if (!svg) return;

            edgeGraph = {{ incoming: {{}}, outgoing: {{}} }};

            // Parse edges from edgePath elements
            svg.querySelectorAll('g.edgePath').forEach(edge => {{
                const classList = Array.from(edge.classList || []);
                let startNode = '';
                let endNode = '';

                // Mermaid uses LS-nodeId and LE-nodeId classes
                classList.forEach(cls => {{
                    if (cls.startsWith('LS-')) startNode = cls.substring(3);
                    if (cls.startsWith('LE-')) endNode = cls.substring(3);
                }});

                if (startNode && endNode) {{
                    // outgoing: startNode -> endNode (startNode is used BY endNode)
                    if (!edgeGraph.outgoing[startNode]) edgeGraph.outgoing[startNode] = [];
                    edgeGraph.outgoing[startNode].push(endNode);

                    // incoming: endNode <- startNode (endNode USES startNode)
                    if (!edgeGraph.incoming[endNode]) edgeGraph.incoming[endNode] = [];
                    edgeGraph.incoming[endNode].push(startNode);
                }}
            }});

            console.log('Edge graph built:', Object.keys(edgeGraph.outgoing).length, 'source nodes');
        }}

        // Find all upstream nodes (what the node depends on - recursively)
        function findUpstream(nodeId, visited = new Set()) {{
            if (visited.has(nodeId)) return visited;
            visited.add(nodeId);

            const incoming = edgeGraph.incoming[nodeId] || [];
            incoming.forEach(srcId => {{
                findUpstream(srcId, visited);
            }});

            return visited;
        }}

        // Find all downstream nodes (what uses this node - recursively)
        function findDownstream(nodeId, visited = new Set()) {{
            if (visited.has(nodeId)) return visited;
            visited.add(nodeId);

            const outgoing = edgeGraph.outgoing[nodeId] || [];
            outgoing.forEach(tgtId => {{
                findDownstream(tgtId, visited);
            }});

            return visited;
        }}

        // Highlight the complete flow for a node
        function highlightNodeFlow(nodeId) {{
            const svg = document.querySelector('.mermaid svg');
            if (!svg) return;

            // Find all connected nodes
            const upstreamNodes = findUpstream(nodeId, new Set());
            const downstreamNodes = findDownstream(nodeId, new Set());
            const allFlowNodes = new Set([...upstreamNodes, ...downstreamNodes]);

            // Activate highlight mode
            svg.classList.add('flow-highlight-active');
            flowHighlightActive = true;
            selectedNodeId = nodeId;

            // Show clear button
            document.getElementById('clear-selection-btn').style.display = '';

            // Highlight nodes
            svg.querySelectorAll('g.node').forEach(node => {{
                node.classList.remove('flow-highlighted', 'flow-selected');

                // Check if this node is in the flow
                const nId = node.id || '';
                let isInFlow = false;

                allFlowNodes.forEach(flowId => {{
                    if (nId.includes(flowId) || flowId.includes(nId.replace('flowchart-', '').split('-')[0])) {{
                        isInFlow = true;
                    }}
                }});

                // Also check by extracting the base node ID from mermaid's format
                const baseId = nId.replace('flowchart-', '').split('-')[0];
                if (allFlowNodes.has(baseId)) {{
                    isInFlow = true;
                }}

                if (isInFlow) {{
                    node.classList.add('flow-highlighted');
                }}

                // Mark the selected node specially
                if (nId.includes(nodeId) || nodeId.includes(baseId)) {{
                    node.classList.add('flow-selected');
                }}
            }});

            // Highlight edges that connect flow nodes
            svg.querySelectorAll('g.edgePath').forEach(edge => {{
                edge.classList.remove('flow-highlighted');

                const classList = Array.from(edge.classList || []);
                let startNode = '';
                let endNode = '';

                classList.forEach(cls => {{
                    if (cls.startsWith('LS-')) startNode = cls.substring(3);
                    if (cls.startsWith('LE-')) endNode = cls.substring(3);
                }});

                // Edge is in flow if both endpoints are in flow
                const startInFlow = allFlowNodes.has(startNode);
                const endInFlow = allFlowNodes.has(endNode);

                if (startInFlow && endInFlow) {{
                    edge.classList.add('flow-highlighted');
                }}
            }});

            // Highlight clusters containing flow nodes
            svg.querySelectorAll('g.cluster').forEach(cluster => {{
                cluster.classList.remove('flow-highlighted');

                // Check if cluster contains any highlighted nodes
                const hasFlowNode = cluster.querySelector('g.node.flow-highlighted');
                if (hasFlowNode) {{
                    cluster.classList.add('flow-highlighted');
                }}
            }});
        }}

        // Clear all flow highlighting
        function clearFlowHighlight() {{
            const svg = document.querySelector('.mermaid svg');
            if (!svg) return;

            svg.classList.remove('flow-highlight-active');
            flowHighlightActive = false;
            selectedNodeId = null;

            // Hide clear button
            document.getElementById('clear-selection-btn').style.display = 'none';

            // Remove all highlight classes
            svg.querySelectorAll('.flow-highlighted, .flow-selected').forEach(el => {{
                el.classList.remove('flow-highlighted', 'flow-selected');
            }});
        }}

        // Extract clean node ID from Mermaid's internal ID format
        function extractNodeId(mermaidId) {{
            // Mermaid uses format like "flowchart-NodeName-123"
            if (!mermaidId) return '';
            const parts = mermaidId.replace('flowchart-', '').split('-');
            // Remove the trailing number suffix
            if (parts.length > 1 && /^\d+$/.test(parts[parts.length - 1])) {{
                parts.pop();
            }}
            return parts.join('-');
        }}

        // Initialize click handlers after Mermaid renders
        function initializeClickHandlers() {{
            const svg = document.querySelector('.mermaid svg');
            if (!svg) {{
                setTimeout(initializeClickHandlers, 500);
                return;
            }}

            // Build the edge graph
            buildEdgeGraph();

            // Show hint briefly
            const hint = document.getElementById('click-hint');
            if (hint) {{
                hint.classList.add('visible');
                setTimeout(() => hint.classList.remove('visible'), 4000);
            }}

            // Add click handlers to nodes
            svg.querySelectorAll('g.node').forEach(node => {{
                node.addEventListener('click', (e) => {{
                    e.stopPropagation();

                    const nodeId = extractNodeId(node.id);

                    if (flowHighlightActive && selectedNodeId === nodeId) {{
                        // Clicking same node again clears highlight
                        clearFlowHighlight();
                    }} else {{
                        // Highlight the clicked node's flow
                        clearFlowHighlight(); // Clear previous
                        highlightNodeFlow(nodeId);
                    }}
                }});
            }});

            // Click on SVG background clears highlight
            svg.addEventListener('click', (e) => {{
                if (e.target === svg || e.target.tagName === 'svg') {{
                    clearFlowHighlight();
                }}
            }});

            // Escape key clears highlight
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'Escape' && flowHighlightActive) {{
                    clearFlowHighlight();
                }}
            }});

            console.log('Click handlers initialized');
        }}

        // Initialize after Mermaid renders (with delay)
        setTimeout(initializeClickHandlers, 1000);

        // ═══════════════════════════════════════════════════════════════════════
        // PANEL DATA
        // ═══════════════════════════════════════════════════════════════════════

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

            // Render used-by panel with display folder support
            const usedByContainer = document.getElementById('used-by-content');
            if (usedByContainer) {{
                if (usedByMeasures.length === 0) {{
                    usedByContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">📭</div>
                            <div>No measures use this measure</div>
                            <div style="font-size: 0.75rem; margin-top: 0.25rem;">This measure is not referenced by any other measures</div>
                        </div>
                    `;
                }} else {{
                    // Group by table
                    const usedByByTable = {{}};
                    usedByMeasures.forEach(item => {{
                        const table = item.table || 'Unknown';
                        if (!usedByByTable[table]) usedByByTable[table] = [];
                        usedByByTable[table].push({{
                            name: item.measure,
                            displayFolder: item.display_folder || ''
                        }});
                    }});

                    let html = '';
                    Object.keys(usedByByTable).sort().forEach(table => {{
                        const items = usedByByTable[table].sort((a, b) => a.name.localeCompare(b.name));
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
                                        <div class="item measure" data-name="${{item.name.toLowerCase()}}" data-table="${{table.toLowerCase()}}">
                                            <span class="item-icon">●</span>
                                            <div style="display: flex; flex-direction: column; gap: 0.125rem; flex: 1;">
                                                <span class="item-name">${{item.name}}</span>
                                                ${{item.displayFolder ? `<span style="color: var(--text-muted); font-size: 0.625rem;">📁 ${{item.displayFolder}}</span>` : ''}}
                                            </div>
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
