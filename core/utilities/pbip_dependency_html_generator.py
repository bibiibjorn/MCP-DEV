"""
PBIP Dependency HTML Generator
Creates interactive, comprehensive dependency diagrams for PBIP projects.
Includes Visuals, Measures, Columns, and Field Parameters with filtering.
"""

import os
import logging
import webbrowser
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def sanitize_node_id(name: str, prefix: str = "N") -> str:
    """Convert name to valid Mermaid node ID (alphanumeric and underscores only)"""
    clean = name.replace("[", "_").replace("]", "").replace(" ", "_")
    clean = clean.replace("-", "_").replace("/", "_").replace("\\", "_")
    clean = clean.replace("(", "_").replace(")", "_").replace("%", "pct")
    clean = clean.replace("&", "and").replace("'", "").replace('"', "")
    clean = clean.replace(".", "_").replace(",", "_").replace(":", "_")
    clean = clean.replace("+", "plus").replace("*", "x").replace("=", "eq")
    clean = clean.replace("<", "lt").replace(">", "gt").replace("!", "not")
    clean = clean.replace("#", "num").replace("@", "at").replace("$", "dollar")
    # Remove any remaining non-alphanumeric chars except underscore
    clean = re.sub(r'[^a-zA-Z0-9_]', '', clean)
    # Collapse multiple underscores
    clean = re.sub(r'_+', '_', clean)
    clean = clean.strip("_")
    return f"{prefix}_{clean}" if clean else f"{prefix}_node"


def generate_pbip_dependency_html(
    dependency_data: Dict[str, Any],
    model_name: str = "Power BI Model",
    auto_open: bool = True,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Generate a professional HTML page with interactive PBIP dependency diagram.

    Args:
        dependency_data: Output from PbipDependencyEngine.analyze_all_dependencies()
        model_name: Name of the model for display
        auto_open: Whether to open the HTML in browser
        output_path: Optional custom output path

    Returns:
        Path to generated HTML file or None if failed
    """
    if not dependency_data:
        logger.error("No dependency data provided")
        return None

    # Extract data from dependency engine output
    measure_to_measure = dependency_data.get('measure_to_measure', {})
    measure_to_measure_reverse = dependency_data.get('measure_to_measure_reverse', {})
    measure_to_column = dependency_data.get('measure_to_column', {})
    column_to_measure = dependency_data.get('column_to_measure', {})
    column_to_field_params = dependency_data.get('column_to_field_params', {})
    visual_dependencies = dependency_data.get('visual_dependencies', {})
    page_dependencies = dependency_data.get('page_dependencies', {})
    summary = dependency_data.get('summary', {})

    # Build comprehensive node and edge lists
    nodes = []  # {'id': str, 'label': str, 'type': str, 'table': str, 'page': str}
    edges = []  # {'source': str, 'target': str, 'type': str}

    # Track all unique entities
    all_measures: Set[str] = set()
    all_columns: Set[str] = set()
    all_visuals: Set[str] = set()
    all_field_params: Set[str] = set()

    # Collect all measures
    for measure_key in measure_to_measure.keys():
        all_measures.add(measure_key)
    for measure_key in measure_to_measure_reverse.keys():
        all_measures.add(measure_key)
    for measure_key in measure_to_column.keys():
        all_measures.add(measure_key)
    for measure_list in column_to_measure.values():
        all_measures.update(measure_list)

    # Collect all columns
    for column_key in column_to_measure.keys():
        all_columns.add(column_key)
    for column_list in measure_to_column.values():
        all_columns.update(column_list)
    for column_key in column_to_field_params.keys():
        all_columns.add(column_key)

    # Collect visuals and their dependencies
    for visual_key, visual_deps in visual_dependencies.items():
        all_visuals.add(visual_key)
        all_measures.update(visual_deps.get('measures', []))
        all_columns.update(visual_deps.get('columns', []))

    # Collect field parameters
    for fp_list in column_to_field_params.values():
        all_field_params.update(fp_list)

    # Build nodes list with sanitized IDs
    node_id_map = {}  # original_key -> sanitized_id

    # Add measure nodes
    for measure_key in sorted(all_measures):
        node_id = sanitize_node_id(measure_key, "M")
        node_id_map[measure_key] = node_id
        table = measure_key.split('[')[0] if '[' in measure_key else ''
        name = measure_key.split('[')[1].rstrip(']') if '[' in measure_key else measure_key
        nodes.append({
            'id': node_id,
            'key': measure_key,
            'label': name,
            'type': 'measure',
            'table': table,
            'page': ''
        })

    # Add column nodes
    for column_key in sorted(all_columns):
        node_id = sanitize_node_id(column_key, "C")
        node_id_map[column_key] = node_id
        table = column_key.split('[')[0] if '[' in column_key else ''
        name = column_key.split('[')[1].rstrip(']') if '[' in column_key else column_key
        nodes.append({
            'id': node_id,
            'key': column_key,
            'label': name,
            'type': 'column',
            'table': table,
            'page': ''
        })

    # Add visual nodes
    for visual_key in sorted(all_visuals):
        node_id = sanitize_node_id(visual_key, "V")
        node_id_map[visual_key] = node_id
        visual_deps = visual_dependencies.get(visual_key, {})
        page = visual_deps.get('page', '')
        visual_type = visual_deps.get('visual_type', 'unknown')
        nodes.append({
            'id': node_id,
            'key': visual_key,
            'label': f"{visual_type}",
            'type': 'visual',
            'table': '',
            'page': page,
            'visual_type': visual_type
        })

    # Add field parameter nodes
    for fp_name in sorted(all_field_params):
        node_id = sanitize_node_id(fp_name, "FP")
        node_id_map[fp_name] = node_id
        nodes.append({
            'id': node_id,
            'key': fp_name,
            'label': fp_name,
            'type': 'field_parameter',
            'table': fp_name,
            'page': ''
        })

    # Build edges
    # Measure -> Measure dependencies
    for measure_key, deps in measure_to_measure.items():
        source_id = node_id_map.get(measure_key)
        if source_id:
            for dep_key in deps:
                target_id = node_id_map.get(dep_key)
                if target_id:
                    edges.append({
                        'source': target_id,  # Dependency points TO the measure that uses it
                        'target': source_id,
                        'type': 'measure_to_measure'
                    })

    # Measure -> Column dependencies
    for measure_key, cols in measure_to_column.items():
        source_id = node_id_map.get(measure_key)
        if source_id:
            for col_key in cols:
                target_id = node_id_map.get(col_key)
                if target_id:
                    edges.append({
                        'source': target_id,  # Column points TO measure that uses it
                        'target': source_id,
                        'type': 'column_to_measure'
                    })

    # Visual -> Measure/Column dependencies
    for visual_key, visual_deps in visual_dependencies.items():
        visual_id = node_id_map.get(visual_key)
        if visual_id:
            for measure_key in visual_deps.get('measures', []):
                measure_id = node_id_map.get(measure_key)
                if measure_id:
                    edges.append({
                        'source': measure_id,
                        'target': visual_id,
                        'type': 'measure_to_visual'
                    })
            for column_key in visual_deps.get('columns', []):
                column_id = node_id_map.get(column_key)
                if column_id:
                    edges.append({
                        'source': column_id,
                        'target': visual_id,
                        'type': 'column_to_visual'
                    })

    # Field Parameter -> Column dependencies
    for column_key, fp_list in column_to_field_params.items():
        column_id = node_id_map.get(column_key)
        if column_id:
            for fp_name in fp_list:
                fp_id = node_id_map.get(fp_name)
                if fp_id:
                    edges.append({
                        'source': column_id,
                        'target': fp_id,
                        'type': 'column_to_field_param'
                    })

    # Generate Mermaid diagram
    mermaid_lines = ["flowchart LR"]
    mermaid_lines.append("")
    mermaid_lines.append("    %% PBIP Comprehensive Dependency Diagram")
    mermaid_lines.append("")

    # Group nodes by type into subgraphs
    # Visuals subgraph
    visual_nodes = [n for n in nodes if n['type'] == 'visual']
    if visual_nodes:
        # Group by page
        pages = {}
        for node in visual_nodes:
            page = node['page'] or 'Unknown Page'
            if page not in pages:
                pages[page] = []
            pages[page].append(node)

        mermaid_lines.append("    subgraph Visuals[\"Visuals\"]")
        mermaid_lines.append("    direction TB")
        for page_name, page_nodes in sorted(pages.items()):
            safe_page_id = sanitize_node_id(page_name, "PG")
            mermaid_lines.append(f"        subgraph {safe_page_id}[\"{page_name}\"]")
            for node in page_nodes:
                mermaid_lines.append(f'            {node["id"]}["{node["label"]}"]:::visual')
            mermaid_lines.append("        end")
        mermaid_lines.append("    end")
        mermaid_lines.append("")

    # Measures subgraph
    measure_nodes = [n for n in nodes if n['type'] == 'measure']
    if measure_nodes:
        # Group by table
        tables = {}
        for node in measure_nodes:
            table = node['table'] or 'Unknown'
            if table not in tables:
                tables[table] = []
            tables[table].append(node)

        mermaid_lines.append("    subgraph Measures[\"Measures\"]")
        mermaid_lines.append("    direction TB")
        for table_name, table_nodes in sorted(tables.items()):
            safe_table_id = sanitize_node_id(table_name, "TM")
            mermaid_lines.append(f"        subgraph {safe_table_id}[\"{table_name}\"]")
            for node in table_nodes[:20]:  # Limit per table to avoid huge diagrams
                mermaid_lines.append(f'            {node["id"]}["{node["label"]}"]:::measure')
            if len(table_nodes) > 20:
                mermaid_lines.append(f'            {safe_table_id}_more["... +{len(table_nodes) - 20} more"]:::measure')
            mermaid_lines.append("        end")
        mermaid_lines.append("    end")
        mermaid_lines.append("")

    # Columns subgraph
    column_nodes = [n for n in nodes if n['type'] == 'column']
    if column_nodes:
        # Group by table
        tables = {}
        for node in column_nodes:
            table = node['table'] or 'Unknown'
            if table not in tables:
                tables[table] = []
            tables[table].append(node)

        mermaid_lines.append("    subgraph Columns[\"Columns\"]")
        mermaid_lines.append("    direction TB")
        for table_name, table_nodes in sorted(tables.items()):
            safe_table_id = sanitize_node_id(table_name, "TC")
            mermaid_lines.append(f"        subgraph {safe_table_id}[\"{table_name}\"]")
            for node in table_nodes[:15]:  # Limit per table
                mermaid_lines.append(f'            {node["id"]}["{node["label"]}"]:::column')
            if len(table_nodes) > 15:
                mermaid_lines.append(f'            {safe_table_id}_more["... +{len(table_nodes) - 15} more"]:::column')
            mermaid_lines.append("        end")
        mermaid_lines.append("    end")
        mermaid_lines.append("")

    # Field Parameters subgraph
    fp_nodes = [n for n in nodes if n['type'] == 'field_parameter']
    if fp_nodes:
        mermaid_lines.append("    subgraph FieldParams[\"Field Parameters\"]")
        mermaid_lines.append("    direction TB")
        for node in fp_nodes:
            mermaid_lines.append(f'        {node["id"]}["{node["label"]}"]:::fieldparam')
        mermaid_lines.append("    end")
        mermaid_lines.append("")

    # Add edges (limit to prevent huge diagrams)
    edge_count = 0
    max_edges = 200
    for edge in edges:
        if edge_count >= max_edges:
            mermaid_lines.append(f"    %% ... and {len(edges) - max_edges} more edges")
            break
        mermaid_lines.append(f"    {edge['source']} --> {edge['target']}")
        edge_count += 1

    # Add styles
    mermaid_lines.append("")
    mermaid_lines.append("    %% Styling")
    mermaid_lines.append("    classDef visual fill:#FF9800,stroke:#F57C00,color:#fff,stroke-width:2px")
    mermaid_lines.append("    classDef measure fill:#2196F3,stroke:#1565C0,color:#fff,stroke-width:2px")
    mermaid_lines.append("    classDef column fill:#9C27B0,stroke:#7B1FA2,color:#fff,stroke-width:2px")
    mermaid_lines.append("    classDef fieldparam fill:#4CAF50,stroke:#388E3C,color:#fff,stroke-width:2px")

    mermaid_code = "\n".join(mermaid_lines)

    # Prepare JSON data for JavaScript
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    summary_json = json.dumps(summary)

    # Prepare category lists for filtering
    measure_ids = json.dumps([n['id'] for n in nodes if n['type'] == 'measure'])
    column_ids = json.dumps([n['id'] for n in nodes if n['type'] == 'column'])
    visual_ids = json.dumps([n['id'] for n in nodes if n['type'] == 'visual'])
    field_param_ids = json.dumps([n['id'] for n in nodes if n['type'] == 'field_parameter'])

    # Prepare grouped data for panels
    measures_by_table = {}
    for node in nodes:
        if node['type'] == 'measure':
            table = node['table'] or 'Unknown'
            if table not in measures_by_table:
                measures_by_table[table] = []
            measures_by_table[table].append({'name': node['label'], 'key': node['key']})

    columns_by_table = {}
    for node in nodes:
        if node['type'] == 'column':
            table = node['table'] or 'Unknown'
            if table not in columns_by_table:
                columns_by_table[table] = []
            columns_by_table[table].append({'name': node['label'], 'key': node['key']})

    visuals_by_page = {}
    for node in nodes:
        if node['type'] == 'visual':
            page = node['page'] or 'Unknown'
            if page not in visuals_by_page:
                visuals_by_page[page] = []
            visuals_by_page[page].append({
                'name': node['label'],
                'key': node['key'],
                'visual_type': node.get('visual_type', '')
            })

    field_params_list = [{'name': n['label'], 'key': n['key']} for n in nodes if n['type'] == 'field_parameter']

    measures_by_table_json = json.dumps(measures_by_table)
    columns_by_table_json = json.dumps(columns_by_table)
    visuals_by_page_json = json.dumps(visuals_by_page)
    field_params_json = json.dumps(field_params_list)

    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} - PBIP Dependency Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --accent: #6366f1;
            --accent-light: #818cf8;
            --accent-glow: rgba(99, 102, 241, 0.4);
            --visual-color: #FF9800;
            --measure-color: #2196F3;
            --column-color: #9C27B0;
            --fieldparam-color: #4CAF50;
            --bg-dark: #09090b;
            --bg-card: rgba(24, 24, 27, 0.8);
            --bg-elevated: rgba(39, 39, 42, 0.6);
            --border: rgba(63, 63, 70, 0.5);
            --border-light: rgba(82, 82, 91, 0.3);
            --text: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
            overflow-x: hidden;
        }}

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
            max-width: 1800px;
            margin: 0 auto;
            padding: 2rem;
            position: relative;
        }}

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
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
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
        }}

        .timestamp {{
            padding: 0.625rem 1rem;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 12px;
            font-size: 0.8125rem;
            color: var(--text-secondary);
            font-family: 'JetBrains Mono', monospace;
        }}

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

        .hero-title {{
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }}

        .hero-subtitle {{
            color: var(--text-muted);
            font-size: 1rem;
        }}

        /* Stats Row */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}

        .stat-card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }}

        .stat-card:hover {{
            transform: translateY(-4px);
            border-color: var(--accent);
            box-shadow: 0 20px 40px -20px var(--accent-glow);
        }}

        .stat-card.active {{
            border-color: var(--accent);
            box-shadow: 0 0 20px var(--accent-glow);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.2;
        }}

        .stat-card.visual .stat-value {{ color: var(--visual-color); }}
        .stat-card.measure .stat-value {{ color: var(--measure-color); }}
        .stat-card.column .stat-value {{ color: var(--column-color); }}
        .stat-card.fieldparam .stat-value {{ color: var(--fieldparam-color); }}
        .stat-card.all .stat-value {{ color: var(--accent-light); }}

        .stat-label {{
            font-size: 0.8125rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
            font-weight: 500;
        }}

        /* Filter Section */
        .filter-section {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .filter-label {{
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.875rem;
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
            padding: 0.5rem 1rem;
            font-size: 0.8125rem;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.2s;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
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

        .btn-filter .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}

        .btn-filter.visual .dot {{ background: var(--visual-color); }}
        .btn-filter.measure .dot {{ background: var(--measure-color); }}
        .btn-filter.column .dot {{ background: var(--column-color); }}
        .btn-filter.fieldparam .dot {{ background: var(--fieldparam-color); }}

        /* Main Content Grid */
        .content-grid {{
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 1.5rem;
        }}

        /* Sidebar Panels */
        .sidebar {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
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
            cursor: pointer;
        }}

        .panel-header:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}

        .panel-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
            font-size: 0.875rem;
        }}

        .panel-icon {{
            width: 24px;
            height: 24px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
        }}

        .panel-icon.visual {{ background: var(--visual-color); }}
        .panel-icon.measure {{ background: var(--measure-color); }}
        .panel-icon.column {{ background: var(--column-color); }}
        .panel-icon.fieldparam {{ background: var(--fieldparam-color); }}

        .panel-count {{
            background: var(--accent);
            color: white;
            font-size: 0.6875rem;
            padding: 0.125rem 0.5rem;
            border-radius: 999px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .panel-content {{
            max-height: 250px;
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

        .panel.collapsed .panel-content {{
            display: none;
        }}

        .panel-header .chevron {{
            transition: transform 0.2s;
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .panel.collapsed .chevron {{
            transform: rotate(-90deg);
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
            padding: 0.625rem 1rem;
            background: rgba(99, 102, 241, 0.05);
            cursor: pointer;
            transition: background 0.2s;
            font-size: 0.8125rem;
        }}

        .table-group-header:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}

        .table-group-name {{
            color: var(--accent-light);
            font-weight: 500;
        }}

        .table-group-count {{
            font-size: 0.6875rem;
            color: var(--text-muted);
            background: var(--bg-elevated);
            padding: 0.125rem 0.375rem;
            border-radius: 999px;
        }}

        .table-group-items {{
            padding: 0.25rem 0;
        }}

        .table-group.collapsed .table-group-items {{
            display: none;
        }}

        .item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 1rem 0.375rem 1.5rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
            transition: all 0.2s;
            cursor: pointer;
        }}

        .item:hover {{
            background: var(--bg-elevated);
            color: var(--text);
        }}

        .item-icon {{
            font-size: 0.5rem;
        }}

        .item.visual .item-icon {{ color: var(--visual-color); }}
        .item.measure .item-icon {{ color: var(--measure-color); }}
        .item.column .item-icon {{ color: var(--column-color); }}
        .item.fieldparam .item-icon {{ color: var(--fieldparam-color); }}

        .item-name {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.6875rem;
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
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            background: var(--bg-elevated);
        }}

        .diagram-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 600;
        }}

        .toolbar {{
            display: flex;
            gap: 0.5rem;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.875rem;
            font-size: 0.75rem;
            font-weight: 500;
            border-radius: 8px;
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
        }}

        .btn-primary {{
            background: var(--accent);
            color: white;
            box-shadow: 0 4px 12px var(--accent-glow);
        }}

        .btn-primary:hover {{
            background: var(--accent-light);
        }}

        .diagram-content {{
            padding: 2rem;
            min-height: 600px;
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
            min-width: 1000px;
        }}

        .mermaid svg {{
            width: 100% !important;
            height: auto !important;
            min-height: 500px;
        }}

        /* Node hover and click styles */
        .mermaid svg g.node {{
            cursor: pointer;
            transition: opacity 0.3s ease, filter 0.3s ease;
        }}

        .mermaid svg g.node:hover {{
            filter: brightness(1.2);
        }}

        .mermaid svg.filter-active g.node {{
            opacity: 0.15;
        }}

        .mermaid svg.filter-active g.node.node-visible {{
            opacity: 1;
        }}

        .mermaid svg.filter-active g.edgePath {{
            opacity: 0.1;
        }}

        .mermaid svg.filter-active g.edgePath.edge-visible {{
            opacity: 1;
        }}

        .mermaid svg.filter-active g.cluster {{
            opacity: 0.3;
        }}

        .mermaid svg.filter-active g.cluster.cluster-visible {{
            opacity: 1;
        }}

        /* Selection mode styles - when a node is clicked */
        .mermaid svg.selection-active g.node {{
            opacity: 0.2;
        }}

        .mermaid svg.selection-active g.node.node-selected {{
            opacity: 1;
            filter: brightness(1.3) drop-shadow(0 0 8px rgba(0, 255, 255, 0.8));
        }}

        .mermaid svg.selection-active g.node.node-connected {{
            opacity: 1;
        }}

        .mermaid svg.selection-active g.edgePath {{
            opacity: 0;
        }}

        .mermaid svg.selection-active g.edgePath.edge-selected {{
            opacity: 1;
        }}

        .mermaid svg.selection-active g.edgePath.edge-selected path {{
            stroke: #00ffff !important;
            stroke-width: 3px !important;
        }}

        .mermaid svg.selection-active g.edgePath.edge-selected marker path {{
            fill: #00ffff !important;
            stroke: #00ffff !important;
        }}

        .mermaid svg.selection-active g.cluster {{
            opacity: 0.3;
        }}

        .mermaid svg.selection-active g.cluster.cluster-has-selection {{
            opacity: 1;
        }}

        /* Legend */
        .legend {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            padding: 1rem;
            border-top: 1px solid var(--border);
            background: var(--bg-elevated);
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8125rem;
            color: var(--text-secondary);
        }}

        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 4px;
        }}

        .legend-dot.visual {{ background: var(--visual-color); }}
        .legend-dot.measure {{ background: var(--measure-color); }}
        .legend-dot.column {{ background: var(--column-color); }}
        .legend-dot.fieldparam {{ background: var(--fieldparam-color); }}

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
        @media (max-width: 1200px) {{
            .content-grid {{
                grid-template-columns: 1fr;
            }}
            .sidebar {{
                flex-direction: row;
                flex-wrap: wrap;
            }}
            .panel {{
                flex: 1;
                min-width: 250px;
            }}
        }}

        @media (max-width: 900px) {{
            .stats-row {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}

        @media (max-width: 600px) {{
            .stats-row {{
                grid-template-columns: repeat(2, 1fr);
            }}
            .filter-section {{
                flex-direction: column;
                align-items: stretch;
            }}
        }}
    </style>
</head>
<body>
    <div class="bg-pattern"></div>

    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="brand">
                <div class="brand-icon">🔗</div>
                <div class="brand-text">
                    <h1>PBIP Dependency Analysis</h1>
                    <span>Comprehensive Model Explorer</span>
                </div>
            </div>
            <div class="timestamp">{timestamp}</div>
        </header>

        <!-- Hero Card -->
        <div class="hero-card">
            <div class="hero-label">Analyzing Model</div>
            <h2 class="hero-title">{model_name}</h2>
            <p class="hero-subtitle">Visualizing dependencies across Visuals, Measures, Columns, and Field Parameters</p>
        </div>

        <!-- Stats Row (clickable filters) -->
        <div class="stats-row">
            <div class="stat-card all active" onclick="setFilter('all')">
                <div class="stat-value">{len(nodes)}</div>
                <div class="stat-label">All Objects</div>
            </div>
            <div class="stat-card visual" onclick="setFilter('visual')">
                <div class="stat-value">{len(visual_nodes)}</div>
                <div class="stat-label">Visuals</div>
            </div>
            <div class="stat-card measure" onclick="setFilter('measure')">
                <div class="stat-value">{len(measure_nodes)}</div>
                <div class="stat-label">Measures</div>
            </div>
            <div class="stat-card column" onclick="setFilter('column')">
                <div class="stat-value">{len(column_nodes)}</div>
                <div class="stat-label">Columns</div>
            </div>
            <div class="stat-card fieldparam" onclick="setFilter('field_parameter')">
                <div class="stat-value">{len(fp_nodes)}</div>
                <div class="stat-label">Field Params</div>
            </div>
        </div>

        <!-- Filter Section -->
        <div class="filter-section">
            <span class="filter-label">Filter by Type:</span>
            <div class="filter-group">
                <button class="btn-filter active" id="filter-all" onclick="setFilter('all')">All</button>
                <button class="btn-filter visual" id="filter-visual" onclick="setFilter('visual')">
                    <span class="dot"></span> Visuals
                </button>
                <button class="btn-filter measure" id="filter-measure" onclick="setFilter('measure')">
                    <span class="dot"></span> Measures
                </button>
                <button class="btn-filter column" id="filter-column" onclick="setFilter('column')">
                    <span class="dot"></span> Columns
                </button>
                <button class="btn-filter fieldparam" id="filter-field_parameter" onclick="setFilter('field_parameter')">
                    <span class="dot"></span> Field Params
                </button>
            </div>
            <span class="filter-label" style="margin-left: auto;">Showing: <span id="visible-count">{len(nodes)}</span> objects</span>
        </div>

        <!-- Main Content -->
        <div class="content-grid">
            <!-- Sidebar -->
            <div class="sidebar">
                <!-- Visuals Panel -->
                <div class="panel" id="panel-visuals">
                    <div class="panel-header" onclick="togglePanel('visuals')">
                        <div class="panel-title">
                            <div class="panel-icon visual">📊</div>
                            <span>Visuals</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span class="panel-count">{len(visual_nodes)}</span>
                            <span class="chevron">▼</span>
                        </div>
                    </div>
                    <div class="panel-content" id="content-visuals">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <!-- Measures Panel -->
                <div class="panel" id="panel-measures">
                    <div class="panel-header" onclick="togglePanel('measures')">
                        <div class="panel-title">
                            <div class="panel-icon measure">📐</div>
                            <span>Measures</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span class="panel-count">{len(measure_nodes)}</span>
                            <span class="chevron">▼</span>
                        </div>
                    </div>
                    <div class="panel-content" id="content-measures">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <!-- Columns Panel -->
                <div class="panel collapsed" id="panel-columns">
                    <div class="panel-header" onclick="togglePanel('columns')">
                        <div class="panel-title">
                            <div class="panel-icon column">📋</div>
                            <span>Columns</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span class="panel-count">{len(column_nodes)}</span>
                            <span class="chevron">▼</span>
                        </div>
                    </div>
                    <div class="panel-content" id="content-columns">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <!-- Field Parameters Panel -->
                <div class="panel" id="panel-fieldparams">
                    <div class="panel-header" onclick="togglePanel('fieldparams')">
                        <div class="panel-title">
                            <div class="panel-icon fieldparam">🎛️</div>
                            <span>Field Parameters</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span class="panel-count">{len(fp_nodes)}</span>
                            <span class="chevron">▼</span>
                        </div>
                    </div>
                    <div class="panel-content" id="content-fieldparams">
                        <!-- Populated by JS -->
                    </div>
                </div>
            </div>

            <!-- Diagram -->
            <div class="diagram-wrapper">
                <div class="diagram-header">
                    <div class="diagram-title">
                        <span>🔗</span>
                        <span>Dependency Graph</span>
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
                        <div class="legend-dot visual"></div>
                        <span>Visuals ({len(visual_nodes)})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot measure"></div>
                        <span>Measures ({len(measure_nodes)})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot column"></div>
                        <span>Columns ({len(column_nodes)})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot fieldparam"></div>
                        <span>Field Parameters ({len(fp_nodes)})</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            Generated by <strong>MCP-PowerBi-Finvision</strong> - PBIP Dependency Analysis
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
                fontSize: '14px',
                fontFamily: 'Inter, sans-serif'
            }},
            flowchart: {{
                htmlLabels: true,
                curve: 'basis',
                nodeSpacing: 60,
                rankSpacing: 80,
                padding: 20,
                useMaxWidth: false
            }},
            securityLevel: 'loose'
        }});

        // Data from Python
        const allNodes = {nodes_json};
        const allEdges = {edges_json};
        const measureIds = {measure_ids};
        const columnIds = {column_ids};
        const visualIds = {visual_ids};
        const fieldParamIds = {field_param_ids};

        const measuresByTable = {measures_by_table_json};
        const columnsByTable = {columns_by_table_json};
        const visualsByPage = {visuals_by_page_json};
        const fieldParamsList = {field_params_json};

        // Node type to IDs mapping
        const typeToIds = {{
            'all': allNodes.map(n => n.id),
            'visual': visualIds,
            'measure': measureIds,
            'column': columnIds,
            'field_parameter': fieldParamIds
        }};

        // Zoom functionality
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
            resetViewBox();
            clearSelection();
        }}

        function applyZoom() {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                svg.style.transform = `scale(${{currentZoom}})`;
                svg.style.transformOrigin = 'top center';
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
                a.download = '{model_name.replace(" ", "_")}_dependencies.svg';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
        }}

        // Filter functionality
        let currentFilter = 'all';

        function setFilter(filterType) {{
            currentFilter = filterType;
            console.log('Setting filter to:', filterType);

            // Update button states
            document.querySelectorAll('.btn-filter').forEach(btn => btn.classList.remove('active'));
            const filterBtn = document.getElementById(`filter-${{filterType}}`);
            if (filterBtn) filterBtn.classList.add('active');

            // Update stat card states
            document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
            const statCard = document.querySelector(`.stat-card.${{filterType === 'field_parameter' ? 'fieldparam' : filterType}}`);
            if (statCard) statCard.classList.add('active');

            // Get visible node IDs based on filter
            const visibleIds = new Set(typeToIds[filterType] || typeToIds['all']);

            // If filtering to a specific type, also show connected nodes
            if (filterType !== 'all') {{
                // Find all edges connected to visible nodes and add their endpoints
                allEdges.forEach(edge => {{
                    const sourceVisible = visibleIds.has(edge.source);
                    const targetVisible = visibleIds.has(edge.target);
                    // Keep edge visible if either endpoint matches the filter
                    // Don't auto-expand to show all connected nodes (keeps filter clean)
                }});
            }}

            // Apply to SVG
            const svg = document.querySelector('.mermaid svg');
            if (!svg) {{
                console.error('SVG not found');
                return;
            }}

            if (filterType === 'all') {{
                svg.classList.remove('filter-active');
                svg.classList.remove('selection-active');
                clearSelection();
                resetViewBox();
                // Show all nodes - reset everything
                svg.querySelectorAll('g.node').forEach(node => {{
                    node.classList.remove('node-visible', 'node-hidden', 'node-selected', 'node-connected');
                    node.style.display = '';
                    node.style.visibility = 'visible';
                    node.style.opacity = '1';
                }});
                svg.querySelectorAll('g.edgePath').forEach(edge => {{
                    edge.classList.remove('edge-visible', 'edge-hidden', 'edge-selected');
                    edge.style.display = '';
                    edge.style.visibility = 'visible';
                    edge.style.opacity = '1';
                    const paths = edge.querySelectorAll('path');
                    paths.forEach(pathEl => {{
                        pathEl.style.stroke = '';
                        pathEl.style.strokeWidth = '';
                    }});
                }});
                svg.querySelectorAll('g.cluster').forEach(cluster => {{
                    cluster.classList.remove('cluster-visible', 'cluster-has-selection');
                    cluster.style.display = '';
                    cluster.style.visibility = 'visible';
                    cluster.style.opacity = '1';
                }});
            }} else {{
                svg.classList.add('filter-active');
                svg.classList.remove('selection-active');

                // FIRST: Show ALL elements to calculate viewBox properly
                svg.querySelectorAll('g.node, g.edgePath, g.cluster').forEach(el => {{
                    el.style.display = '';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                    el.classList.remove('node-visible', 'node-hidden', 'node-selected', 'node-connected');
                    el.classList.remove('edge-visible', 'edge-hidden', 'edge-selected');
                    el.classList.remove('cluster-visible', 'cluster-has-selection');
                }});
                resetViewBox();

                // Find nodes to show and calculate viewBox
                const nodesToShow = [];
                const visibleMermaidIds = new Set();
                svg.querySelectorAll('g.node').forEach(node => {{
                    const mermaidId = node.id || '';
                    const nodeId = extractNodeId(mermaidId);
                    if (visibleIds.has(nodeId)) {{
                        nodesToShow.push(node);
                        visibleMermaidIds.add(nodeId);
                    }}
                }});

                // Calculate viewBox BEFORE hiding
                const viewBoxData = calculateBoundsForNodes(svg, nodesToShow);

                // NOW hide non-matching nodes with display:none
                svg.querySelectorAll('g.node').forEach(node => {{
                    const mermaidId = node.id || '';
                    const nodeId = extractNodeId(mermaidId);
                    const isVisible = visibleIds.has(nodeId);

                    if (isVisible) {{
                        node.classList.add('node-visible');
                        node.style.display = '';
                        node.style.visibility = 'visible';
                        node.style.opacity = '1';
                    }} else {{
                        node.classList.add('node-hidden');
                        node.style.display = 'none';
                    }}
                }});

                // Hide edges where endpoints are not both visible
                svg.querySelectorAll('g.edgePath').forEach(edge => {{
                    const classList = Array.from(edge.classList || []);
                    let startId = '';
                    let endId = '';

                    classList.forEach(cls => {{
                        if (cls.startsWith('LS-')) startId = cls.substring(3);
                        if (cls.startsWith('LE-')) endId = cls.substring(3);
                    }});

                    const shouldShow = visibleMermaidIds.has(startId) && visibleMermaidIds.has(endId);
                    if (shouldShow) {{
                        edge.classList.add('edge-visible');
                        edge.style.display = '';
                        edge.style.visibility = 'visible';
                        edge.style.opacity = '1';
                    }} else {{
                        edge.classList.add('edge-hidden');
                        edge.style.display = 'none';
                    }}
                }});

                // Hide clusters without visible nodes
                svg.querySelectorAll('g.cluster').forEach(cluster => {{
                    const hasVisibleNode = cluster.querySelector('g.node.node-visible');
                    if (hasVisibleNode) {{
                        cluster.classList.add('cluster-visible');
                        cluster.style.display = '';
                        cluster.style.visibility = 'visible';
                        cluster.style.opacity = '1';
                    }} else {{
                        cluster.style.display = 'none';
                    }}
                }});

                // Apply pre-calculated viewBox
                if (viewBoxData) {{
                    svg.setAttribute('viewBox', viewBoxData);
                    console.log('Filter viewBox applied:', viewBoxData);
                }}
            }}

            // Update visible count
            document.getElementById('visible-count').textContent = visibleIds.size;
        }}

        // REMOVED OLD FILTER CODE - replaced above
                        edge.classList.remove('edge-visible');
                    }}
                }});

                // Show clusters that contain visible nodes
                svg.querySelectorAll('g.cluster').forEach(cluster => {{
                    const hasVisibleNode = cluster.querySelector('g.node.node-visible');
                    if (hasVisibleNode) {{
                        cluster.classList.add('cluster-visible');
                    }} else {{
                        cluster.classList.remove('cluster-visible');
                    }}
                }});
            }}

            // Update visible count
            document.getElementById('visible-count').textContent = visibleIds.size;

            // Adjust viewBox to focus on visible nodes (fix blank space)
            if (filterType !== 'all') {{
                setTimeout(() => {{
                    focusOnVisibleNodes(svg, 'g.node.node-visible');
                }}, 100);
            }}
        }}

        // Node selection functionality
        let selectedNodeId = null;
        let nodeIdToMermaidId = {{}};  // Map our IDs to Mermaid SVG element IDs

        function extractNodeId(mermaidId) {{
            // Handle formats like "flowchart-M_some_measure-123" or just "M_some_measure"
            const match = mermaidId.match(/flowchart-(.+)-\\d+$/);
            return match ? match[1] : mermaidId;
        }}

        function buildNodeIdMap() {{
            const svg = document.querySelector('.mermaid svg');
            if (!svg) return;

            nodeIdToMermaidId = {{}};
            svg.querySelectorAll('g.node').forEach(node => {{
                const mermaidId = node.id || '';
                const nodeId = extractNodeId(mermaidId);
                nodeIdToMermaidId[nodeId] = mermaidId;
            }});
            console.log('Built node ID map with', Object.keys(nodeIdToMermaidId).length, 'entries');
        }}

        function clearSelection() {{
            console.log('Clearing selection');
            selectedNodeId = null;
            const svg = document.querySelector('.mermaid svg');
            if (!svg) return;

            svg.classList.remove('selection-active');

            // Show ALL nodes and edges - reset everything including display
            svg.querySelectorAll('g.node').forEach(node => {{
                node.classList.remove('node-selected', 'node-connected', 'node-hidden', 'node-visible');
                node.style.display = '';
                node.style.visibility = 'visible';
                node.style.opacity = '1';
            }});
            svg.querySelectorAll('g.edgePath').forEach(edge => {{
                edge.classList.remove('edge-selected', 'edge-hidden', 'edge-visible');
                edge.style.display = '';
                edge.style.visibility = 'visible';
                edge.style.opacity = '1';
                const paths = edge.querySelectorAll('path');
                paths.forEach(pathEl => {{
                    pathEl.style.stroke = '';
                    pathEl.style.strokeWidth = '';
                }});
            }});
            svg.querySelectorAll('g.cluster').forEach(cluster => {{
                cluster.classList.remove('cluster-has-selection', 'cluster-visible');
                cluster.style.display = '';
                cluster.style.visibility = 'visible';
                cluster.style.opacity = '1';
            }});

            // Reset viewBox to original
            resetViewBox();
        }}

        function selectNode(nodeId) {{
            console.log('selectNode called with:', nodeId);
            const svg = document.querySelector('.mermaid svg');
            if (!svg) {{
                console.error('SVG not found');
                return;
            }}

            // If clicking the same node while selected, deselect (toggle off)
            if (selectedNodeId === nodeId) {{
                clearSelection();
                return;
            }}

            // FIRST: Show ALL elements temporarily to calculate viewBox properly
            svg.querySelectorAll('g.node, g.edgePath, g.cluster').forEach(el => {{
                el.style.display = '';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
            }});

            // Reset viewBox to original
            resetViewBox();

            selectedNodeId = nodeId;
            svg.classList.add('selection-active');
            svg.classList.remove('filter-active');

            // Find ALL connected nodes (direct connections only)
            const connectedNodeIds = new Set();
            connectedNodeIds.add(nodeId);

            allEdges.forEach(edge => {{
                if (edge.source === nodeId || edge.target === nodeId) {{
                    connectedNodeIds.add(edge.source);
                    connectedNodeIds.add(edge.target);
                }}
            }});

            console.log('Selected node:', nodeId);
            console.log('Connected nodes:', Array.from(connectedNodeIds));

            // Calculate viewBox BEFORE hiding elements (so we get proper dimensions)
            const nodesToShow = [];
            svg.querySelectorAll('g.node').forEach(node => {{
                const mermaidId = node.id || '';
                const nId = extractNodeId(mermaidId);
                if (nId === nodeId || connectedNodeIds.has(nId)) {{
                    nodesToShow.push(node);
                }}
            }});

            // Calculate bounding box of nodes to show
            const viewBoxData = calculateBoundsForNodes(svg, nodesToShow);

            // NOW hide all non-related nodes
            svg.querySelectorAll('g.node').forEach(node => {{
                const mermaidId = node.id || '';
                const nId = extractNodeId(mermaidId);
                node.classList.remove('node-selected', 'node-connected', 'node-hidden', 'node-visible');

                if (nId === nodeId) {{
                    node.classList.add('node-selected');
                    node.style.display = '';
                    node.style.visibility = 'visible';
                    node.style.opacity = '1';
                }} else if (connectedNodeIds.has(nId)) {{
                    node.classList.add('node-connected');
                    node.style.display = '';
                    node.style.visibility = 'visible';
                    node.style.opacity = '1';
                }} else {{
                    node.classList.add('node-hidden');
                    node.style.display = 'none';
                }}
            }});

            // Hide all non-related edges
            svg.querySelectorAll('g.edgePath').forEach(edge => {{
                const classList = Array.from(edge.classList || []);
                let startId = '';
                let endId = '';

                classList.forEach(cls => {{
                    if (cls.startsWith('LS-')) startId = cls.substring(3);
                    if (cls.startsWith('LE-')) endId = cls.substring(3);
                }});

                edge.classList.remove('edge-selected', 'edge-hidden', 'edge-visible');
                const isDirectlyConnected = (startId === nodeId || endId === nodeId);

                if (isDirectlyConnected) {{
                    edge.classList.add('edge-selected');
                    edge.style.display = '';
                    edge.style.visibility = 'visible';
                    edge.style.opacity = '1';
                    const paths = edge.querySelectorAll('path');
                    paths.forEach(pathEl => {{
                        pathEl.style.stroke = '#00ffff';
                        pathEl.style.strokeWidth = '3px';
                    }});
                }} else {{
                    edge.classList.add('edge-hidden');
                    edge.style.display = 'none';
                }}
            }});

            // Hide clusters without selected nodes
            svg.querySelectorAll('g.cluster').forEach(cluster => {{
                const hasSelectedNode = cluster.querySelector('g.node.node-selected, g.node.node-connected');
                cluster.classList.remove('cluster-has-selection', 'cluster-visible');

                if (hasSelectedNode) {{
                    cluster.classList.add('cluster-has-selection');
                    cluster.style.display = '';
                    cluster.style.visibility = 'visible';
                    cluster.style.opacity = '1';
                }} else {{
                    cluster.style.display = 'none';
                }}
            }});

            // Apply pre-calculated viewBox
            if (viewBoxData) {{
                svg.setAttribute('viewBox', viewBoxData);
                console.log('Applied viewBox:', viewBoxData);
            }}
        }}

        function calculateBoundsForNodes(svg, nodes) {{
            if (!nodes || nodes.length === 0) return null;

            const svgCTM = svg.getScreenCTM();
            if (!svgCTM) return null;
            const svgCTMInverse = svgCTM.inverse();

            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

            nodes.forEach(node => {{
                try {{
                    const rect = node.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return;

                    const topLeft = svg.createSVGPoint();
                    topLeft.x = rect.left;
                    topLeft.y = rect.top;
                    const svgTopLeft = topLeft.matrixTransform(svgCTMInverse);

                    const bottomRight = svg.createSVGPoint();
                    bottomRight.x = rect.right;
                    bottomRight.y = rect.bottom;
                    const svgBottomRight = bottomRight.matrixTransform(svgCTMInverse);

                    minX = Math.min(minX, svgTopLeft.x);
                    minY = Math.min(minY, svgTopLeft.y);
                    maxX = Math.max(maxX, svgBottomRight.x);
                    maxY = Math.max(maxY, svgBottomRight.y);
                }} catch (e) {{
                    console.warn('Error calculating bounds:', e);
                }}
            }});

            if (minX === Infinity) return null;

            const padding = 50;
            minX -= padding;
            minY -= padding;
            maxX += padding;
            maxY += padding;

            const width = Math.max(maxX - minX, 300);
            const height = Math.max(maxY - minY, 200);

            return `${{minX}} ${{minY}} ${{width}} ${{height}}`;
        }}

        function focusOnVisibleNodes(svg, selector) {{
            // Get visible nodes based on selector (default for selection mode)
            const nodeSelector = selector || 'g.node.node-selected, g.node.node-connected';
            const visibleNodes = svg.querySelectorAll(nodeSelector);
            if (visibleNodes.length === 0) {{
                console.log('No visible nodes found for selector:', nodeSelector);
                return;
            }}

            console.log('Focusing on', visibleNodes.length, 'visible nodes');

            // Store original viewBox if not stored
            const viewBox = svg.viewBox.baseVal;
            if (!svg.dataset.originalViewBox) {{
                svg.dataset.originalViewBox = `${{viewBox.x}} ${{viewBox.y}} ${{viewBox.width}} ${{viewBox.height}}`;
            }}

            // Use getScreenCTM to properly convert coordinates
            const svgCTM = svg.getScreenCTM();
            if (!svgCTM) {{
                console.warn('Could not get SVG CTM');
                return;
            }}
            const svgCTMInverse = svgCTM.inverse();

            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

            visibleNodes.forEach(node => {{
                try {{
                    // Get the bounding client rect (screen coordinates)
                    const rect = node.getBoundingClientRect();

                    // Convert screen coordinates to SVG coordinates
                    const topLeft = svg.createSVGPoint();
                    topLeft.x = rect.left;
                    topLeft.y = rect.top;
                    const svgTopLeft = topLeft.matrixTransform(svgCTMInverse);

                    const bottomRight = svg.createSVGPoint();
                    bottomRight.x = rect.right;
                    bottomRight.y = rect.bottom;
                    const svgBottomRight = bottomRight.matrixTransform(svgCTMInverse);

                    minX = Math.min(minX, svgTopLeft.x);
                    minY = Math.min(minY, svgTopLeft.y);
                    maxX = Math.max(maxX, svgBottomRight.x);
                    maxY = Math.max(maxY, svgBottomRight.y);

                    console.log('Node bounds:', svgTopLeft.x, svgTopLeft.y, svgBottomRight.x, svgBottomRight.y);
                }} catch (e) {{
                    console.warn('Error calculating node bounds:', e);
                }}
            }});

            if (minX !== Infinity && maxX > minX && maxY > minY) {{
                // Add padding
                const padding = 60;
                minX -= padding;
                minY -= padding;
                maxX += padding;
                maxY += padding;

                const width = Math.max(maxX - minX, 300);
                const height = Math.max(maxY - minY, 200);

                // Set new viewBox to focus on visible content
                const newViewBox = `${{minX}} ${{minY}} ${{width}} ${{height}}`;
                console.log('Setting viewBox to:', newViewBox);
                svg.setAttribute('viewBox', newViewBox);
            }} else {{
                console.warn('Could not calculate valid bounds');
            }}
        }}

        function resetViewBox() {{
            const svg = document.querySelector('.mermaid svg');
            if (svg && svg.dataset.originalViewBox) {{
                console.log('Resetting viewBox to:', svg.dataset.originalViewBox);
                svg.setAttribute('viewBox', svg.dataset.originalViewBox);
            }}
        }}

        function setupNodeClickHandlers() {{
            const svg = document.querySelector('.mermaid svg');
            if (!svg) {{
                console.error('SVG not found for click handlers');
                return;
            }}

            console.log('Setting up click handlers');

            // Build node ID mapping
            buildNodeIdMap();

            // Store original viewBox
            const viewBox = svg.viewBox.baseVal;
            if (!svg.dataset.originalViewBox) {{
                svg.dataset.originalViewBox = `${{viewBox.x}} ${{viewBox.y}} ${{viewBox.width}} ${{viewBox.height}}`;
                console.log('Stored original viewBox:', svg.dataset.originalViewBox);
            }}

            // Set cursor style on all nodes
            const nodes = svg.querySelectorAll('g.node');
            console.log('Found', nodes.length, 'nodes');
            console.log('Available node IDs:', Object.keys(nodeIdToMermaidId).slice(0, 5), '...');
            console.log('Sample edges:', allEdges.slice(0, 3));

            nodes.forEach(node => {{
                node.style.cursor = 'pointer';
            }});

            // Use event delegation on SVG - this survives DOM changes
            svg.addEventListener('click', function(e) {{
                // Find if we clicked on a node
                const nodeElement = e.target.closest('g.node');

                if (nodeElement) {{
                    e.preventDefault();
                    e.stopPropagation();
                    const mermaidId = nodeElement.id || '';
                    const nodeId = extractNodeId(mermaidId);
                    console.log('=== NODE CLICKED ===');
                    console.log('Mermaid ID:', mermaidId);
                    console.log('Extracted ID:', nodeId);
                    selectNode(nodeId);
                }}
            }}, true);

            // Add click handler to diagram background to clear selection
            const diagramContent = document.getElementById('diagram-content');
            if (diagramContent) {{
                diagramContent.addEventListener('click', function(e) {{
                    // Only clear if NOT clicking on a node
                    const clickedNode = e.target.closest('g.node');
                    if (!clickedNode && !e.target.closest('g.edgePath')) {{
                        console.log('Background click - clearing selection');
                        clearSelection();
                    }}
                }});
            }}

            console.log('Click handlers setup complete');
        }}

        // Panel toggle
        function togglePanel(panelName) {{
            const panel = document.getElementById(`panel-${{panelName}}`);
            if (panel) {{
                panel.classList.toggle('collapsed');
            }}
        }}

        // Populate panels
        function populatePanels() {{
            // Visuals panel
            const visualsContent = document.getElementById('content-visuals');
            if (visualsContent) {{
                let html = '';
                for (const [page, visuals] of Object.entries(visualsByPage).sort()) {{
                    html += `
                        <div class="table-group">
                            <div class="table-group-header" onclick="this.parentElement.classList.toggle('collapsed')">
                                <span class="table-group-name">📄 ${{page}}</span>
                                <span class="table-group-count">${{visuals.length}}</span>
                            </div>
                            <div class="table-group-items">
                                ${{visuals.map(v => `
                                    <div class="item visual">
                                        <span class="item-icon">●</span>
                                        <span class="item-name">${{v.visual_type || v.name}}</span>
                                    </div>
                                `).join('')}}
                            </div>
                        </div>
                    `;
                }}
                visualsContent.innerHTML = html || '<div style="padding: 1rem; color: var(--text-muted);">No visuals found</div>';
            }}

            // Measures panel
            const measuresContent = document.getElementById('content-measures');
            if (measuresContent) {{
                let html = '';
                for (const [table, measures] of Object.entries(measuresByTable).sort()) {{
                    html += `
                        <div class="table-group">
                            <div class="table-group-header" onclick="this.parentElement.classList.toggle('collapsed')">
                                <span class="table-group-name">📁 ${{table}}</span>
                                <span class="table-group-count">${{measures.length}}</span>
                            </div>
                            <div class="table-group-items">
                                ${{measures.slice(0, 20).map(m => `
                                    <div class="item measure">
                                        <span class="item-icon">●</span>
                                        <span class="item-name">${{m.name}}</span>
                                    </div>
                                `).join('')}}
                                ${{measures.length > 20 ? `<div class="item measure"><span class="item-icon">...</span><span class="item-name">+${{measures.length - 20}} more</span></div>` : ''}}
                            </div>
                        </div>
                    `;
                }}
                measuresContent.innerHTML = html || '<div style="padding: 1rem; color: var(--text-muted);">No measures found</div>';
            }}

            // Columns panel
            const columnsContent = document.getElementById('content-columns');
            if (columnsContent) {{
                let html = '';
                for (const [table, columns] of Object.entries(columnsByTable).sort()) {{
                    html += `
                        <div class="table-group collapsed">
                            <div class="table-group-header" onclick="this.parentElement.classList.toggle('collapsed')">
                                <span class="table-group-name">📁 ${{table}}</span>
                                <span class="table-group-count">${{columns.length}}</span>
                            </div>
                            <div class="table-group-items">
                                ${{columns.slice(0, 15).map(c => `
                                    <div class="item column">
                                        <span class="item-icon">●</span>
                                        <span class="item-name">${{c.name}}</span>
                                    </div>
                                `).join('')}}
                                ${{columns.length > 15 ? `<div class="item column"><span class="item-icon">...</span><span class="item-name">+${{columns.length - 15}} more</span></div>` : ''}}
                            </div>
                        </div>
                    `;
                }}
                columnsContent.innerHTML = html || '<div style="padding: 1rem; color: var(--text-muted);">No columns found</div>';
            }}

            // Field Parameters panel
            const fpContent = document.getElementById('content-fieldparams');
            if (fpContent) {{
                if (fieldParamsList.length > 0) {{
                    fpContent.innerHTML = fieldParamsList.map(fp => `
                        <div class="item fieldparam">
                            <span class="item-icon">●</span>
                            <span class="item-name">${{fp.name}}</span>
                        </div>
                    `).join('');
                }} else {{
                    fpContent.innerHTML = '<div style="padding: 1rem; color: var(--text-muted);">No field parameters found</div>';
                }}
            }}
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            populatePanels();
            // Force SVG resize and setup click handlers after Mermaid renders
            setTimeout(() => {{
                const svg = document.querySelector('.mermaid svg');
                if (svg) {{
                    svg.style.minWidth = '1000px';
                    svg.style.minHeight = '500px';
                    // Store original viewBox for later reset
                    svg.dataset.originalViewBox = svg.getAttribute('viewBox') || '';
                    setupNodeClickHandlers();
                }}
            }}, 1000);
        }});
    </script>
</body>
</html>'''

    try:
        # Determine output path
        if output_path:
            html_path = output_path
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            exports_dir = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "exports")
            os.makedirs(exports_dir, exist_ok=True)
            html_path = os.path.join(exports_dir, "pbip_dependency_diagram.html")

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Generated PBIP dependency diagram HTML: {html_path}")

        if auto_open:
            webbrowser.open(f'file:///{html_path.replace(os.sep, "/")}')

        return html_path

    except Exception as e:
        logger.error(f"Failed to generate PBIP dependency HTML: {e}")
        return None
