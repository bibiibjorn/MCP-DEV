"""
PBIP Dependency HTML Generator
Creates interactive, comprehensive dependency diagrams for PBIP projects.
Includes sidebar navigation for all Measures, Columns, and Field Parameters.
Supports selecting any item to view its dependencies.
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
    output_path: Optional[str] = None,
    main_item: Optional[str] = None,
    main_item_type: Optional[str] = None
) -> Optional[str]:
    """
    Generate a professional HTML page with interactive PBIP dependency diagram.

    Features a left sidebar with all measures, columns, and field parameters.
    Clicking any item in the sidebar switches the diagram to show that item's dependencies.

    Args:
        dependency_data: Output from PbipDependencyEngine.analyze_all_dependencies()
        model_name: Name of the model for display
        auto_open: Whether to open the HTML in browser
        output_path: Optional custom output path
        main_item: Optional specific item to select initially (e.g., "Table[Measure]")
        main_item_type: Type of main_item ("measure", "column", "field_parameter")

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
    summary = dependency_data.get('summary', {})

    # Build comprehensive node lists
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

    # Collect visuals
    for visual_key in visual_dependencies.keys():
        all_visuals.add(visual_key)

    # Collect field parameters
    for fp_list in column_to_field_params.values():
        all_field_params.update(fp_list)

    # Pre-compute dependencies for EACH item
    # This will be embedded as JSON in the HTML for client-side switching
    item_dependencies = {}

    def extract_table_and_name(key: str) -> Tuple[str, str]:
        """Extract table and name from a key in Table[Name] format."""
        if '[' in key and ']' in key:
            bracket_idx = key.index('[')
            table = key[:bracket_idx].strip()
            name = key[bracket_idx + 1:].rstrip(']').strip()
            if not table and name:
                return ("Unresolved", name)
            return (table if table else "Unresolved", name if name else key)
        return ("Unresolved", key)

    # Build dependencies for each MEASURE
    for measure_key in sorted(all_measures):
        table, name = extract_table_and_name(measure_key)
        node_id = sanitize_node_id(measure_key, "M")

        # Upstream: what this measure depends on (columns and measures)
        upstream_measures = measure_to_measure.get(measure_key, [])
        upstream_columns = measure_to_column.get(measure_key, [])

        # Downstream: what depends on this measure
        downstream_measures = measure_to_measure_reverse.get(measure_key, [])
        downstream_visuals = []
        for visual_key, visual_deps in visual_dependencies.items():
            if measure_key in visual_deps.get('measures', []):
                downstream_visuals.append({
                    'key': visual_key,
                    'page': visual_deps.get('page', ''),
                    'visual_type': visual_deps.get('visual_type', '')
                })

        item_dependencies[measure_key] = {
            'key': measure_key,
            'nodeId': node_id,
            'type': 'measure',
            'table': table,
            'name': name,
            'upstream': {
                'measures': upstream_measures,
                'columns': upstream_columns
            },
            'downstream': {
                'measures': downstream_measures,
                'visuals': downstream_visuals
            }
        }

    # Build dependencies for each COLUMN
    for column_key in sorted(all_columns):
        table, name = extract_table_and_name(column_key)
        node_id = sanitize_node_id(column_key, "C")

        # Downstream: what uses this column
        downstream_measures = column_to_measure.get(column_key, [])
        downstream_field_params = column_to_field_params.get(column_key, [])
        downstream_visuals = []
        for visual_key, visual_deps in visual_dependencies.items():
            if column_key in visual_deps.get('columns', []):
                downstream_visuals.append({
                    'key': visual_key,
                    'page': visual_deps.get('page', ''),
                    'visual_type': visual_deps.get('visual_type', '')
                })

        item_dependencies[column_key] = {
            'key': column_key,
            'nodeId': node_id,
            'type': 'column',
            'table': table,
            'name': name,
            'upstream': {
                'measures': [],
                'columns': []
            },
            'downstream': {
                'measures': downstream_measures,
                'visuals': downstream_visuals,
                'fieldParams': downstream_field_params
            }
        }

    # Build dependencies for each FIELD PARAMETER
    for fp_name in sorted(all_field_params):
        node_id = sanitize_node_id(fp_name, "FP")

        # Upstream: columns referenced by this field parameter
        upstream_columns = []
        for column_key, fp_list in column_to_field_params.items():
            if fp_name in fp_list:
                upstream_columns.append(column_key)

        item_dependencies[fp_name] = {
            'key': fp_name,
            'nodeId': node_id,
            'type': 'field_parameter',
            'table': fp_name,
            'name': fp_name,
            'upstream': {
                'measures': [],
                'columns': upstream_columns
            },
            'downstream': {
                'measures': [],
                'visuals': []
            }
        }

    # Build grouped data for sidebar
    measures_by_table = {}
    for measure_key in sorted(all_measures):
        table, name = extract_table_and_name(measure_key)
        if table not in measures_by_table:
            measures_by_table[table] = []
        measures_by_table[table].append({
            'name': name,
            'key': measure_key,
            'nodeId': sanitize_node_id(measure_key, "M")
        })

    columns_by_table = {}
    for column_key in sorted(all_columns):
        table, name = extract_table_and_name(column_key)
        if table not in columns_by_table:
            columns_by_table[table] = []
        columns_by_table[table].append({
            'name': name,
            'key': column_key,
            'nodeId': sanitize_node_id(column_key, "C")
        })

    field_params_list = []
    for fp_name in sorted(all_field_params):
        field_params_list.append({
            'name': fp_name,
            'key': fp_name,
            'nodeId': sanitize_node_id(fp_name, "FP")
        })

    # Determine initial selection
    initial_item = None
    if main_item and main_item in item_dependencies:
        initial_item = main_item
    elif all_measures:
        # Default to first measure
        initial_item = sorted(all_measures)[0]
    elif all_columns:
        initial_item = sorted(all_columns)[0]
    elif all_field_params:
        initial_item = sorted(all_field_params)[0]

    # Prepare JSON data for JavaScript
    item_dependencies_json = json.dumps(item_dependencies)
    measures_by_table_json = json.dumps(measures_by_table)
    columns_by_table_json = json.dumps(columns_by_table)
    field_params_json = json.dumps(field_params_list)
    initial_item_json = json.dumps(initial_item)

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
            --bg-dark: #0a0a0f;
            --bg-sidebar: #0d0d14;
            --bg-card: rgba(24, 24, 27, 0.8);
            --bg-elevated: rgba(39, 39, 42, 0.6);
            --bg-hover: rgba(99, 102, 241, 0.1);
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
            overflow: hidden;
        }}

        .app-container {{
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}

        /* Left Sidebar - Model Browser */
        .sidebar {{
            width: 320px;
            min-width: 320px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .sidebar-header {{
            padding: 1.25rem;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(99, 102, 241, 0.08) 0%, transparent 100%);
        }}

        .sidebar-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.5rem;
        }}

        .sidebar-title-icon {{
            font-size: 1.25rem;
        }}

        .sidebar-subtitle {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .sidebar-search {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
        }}

        .search-input {{
            width: 100%;
            padding: 0.5rem 0.75rem;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-size: 0.8125rem;
            font-family: inherit;
        }}

        .search-input::placeholder {{
            color: var(--text-muted);
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }}

        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: var(--border) transparent;
        }}

        .sidebar-content::-webkit-scrollbar {{
            width: 6px;
        }}

        .sidebar-content::-webkit-scrollbar-track {{
            background: transparent;
        }}

        .sidebar-content::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 3px;
        }}

        /* Category Panels */
        .category-panel {{
            border-bottom: 1px solid var(--border);
        }}

        .category-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.875rem 1rem;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }}

        .category-header:hover {{
            background: var(--bg-hover);
        }}

        .category-title {{
            display: flex;
            align-items: center;
            gap: 0.625rem;
        }}

        .category-icon {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
        }}

        .category-icon.measure {{
            background: linear-gradient(135deg, #2196F3, #1976D2);
        }}

        .category-icon.column {{
            background: linear-gradient(135deg, #9C27B0, #7B1FA2);
        }}

        .category-icon.fieldparam {{
            background: linear-gradient(135deg, #4CAF50, #388E3C);
        }}

        .category-name {{
            font-size: 0.875rem;
            font-weight: 600;
        }}

        .category-badge {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .category-count {{
            background: var(--accent);
            color: white;
            font-size: 0.6875rem;
            padding: 0.125rem 0.5rem;
            border-radius: 999px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .category-chevron {{
            color: var(--text-muted);
            font-size: 0.75rem;
            transition: transform 0.2s;
        }}

        .category-panel.collapsed .category-chevron {{
            transform: rotate(-90deg);
        }}

        .category-content {{
            display: block;
        }}

        .category-panel.collapsed .category-content {{
            display: none;
        }}

        /* Table Groups */
        .table-group {{
            border-top: 1px solid var(--border-light);
        }}

        .table-group-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 1rem 0.5rem 1.25rem;
            cursor: pointer;
            background: rgba(99, 102, 241, 0.03);
            transition: background 0.2s;
        }}

        .table-group-header:hover {{
            background: rgba(99, 102, 241, 0.08);
        }}

        .table-group-name {{
            font-size: 0.75rem;
            color: var(--accent-light);
            font-weight: 500;
        }}

        .table-group-count {{
            font-size: 0.625rem;
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

        /* Items */
        .item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.375rem 1rem 0.375rem 2rem;
            cursor: pointer;
            transition: all 0.15s;
        }}

        .item:hover {{
            background: var(--bg-hover);
        }}

        .item.selected {{
            background: var(--accent);
            color: white;
        }}

        .item.selected .item-name {{
            color: white;
        }}

        .item-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            flex-shrink: 0;
        }}

        .item.measure .item-dot {{
            background: var(--measure-color);
        }}

        .item.column .item-dot {{
            background: var(--column-color);
        }}

        .item.fieldparam .item-dot {{
            background: var(--fieldparam-color);
        }}

        .item.selected .item-dot {{
            background: white;
        }}

        .item-name {{
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Main Content Area */
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background: var(--bg-dark);
        }}

        .main-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-card);
        }}

        .main-title {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}

        .main-title h1 {{
            font-size: 1.125rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #a1a1aa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .main-title span {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .toolbar {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
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

        .timestamp {{
            font-size: 0.6875rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }}

        /* Diagram Area */
        .diagram-area {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .selected-item-info {{
            padding: 1rem 1.5rem;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
        }}

        .selected-item-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 12px;
        }}

        .selected-item-type {{
            font-size: 0.625rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.125rem 0.5rem;
            border-radius: 4px;
            font-weight: 600;
        }}

        .selected-item-type.measure {{
            background: var(--measure-color);
            color: white;
        }}

        .selected-item-type.column {{
            background: var(--column-color);
            color: white;
        }}

        .selected-item-type.field_parameter {{
            background: var(--fieldparam-color);
            color: white;
        }}

        .selected-item-name {{
            font-size: 0.875rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .dependency-stats {{
            display: flex;
            gap: 1.5rem;
            margin-top: 0.75rem;
        }}

        .dep-stat {{
            display: flex;
            align-items: center;
            gap: 0.375rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .dep-stat-value {{
            font-weight: 600;
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
        }}

        .diagram-container {{
            flex: 1;
            overflow: auto;
            padding: 1.5rem;
            background:
                radial-gradient(ellipse at center, rgba(99, 102, 241, 0.03), transparent 70%),
                linear-gradient(180deg, transparent, rgba(0,0,0,0.2));
        }}

        .mermaid {{
            display: flex;
            justify-content: center;
        }}

        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}

        .no-diagram {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-muted);
            text-align: center;
        }}

        .no-diagram-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}

        .no-diagram-text {{
            font-size: 0.875rem;
        }}

        /* Legend */
        .legend {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            padding: 1rem;
            border-top: 1px solid var(--border);
            background: var(--bg-card);
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}

        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 4px;
        }}

        .legend-dot.measure {{
            background: var(--measure-color);
        }}

        .legend-dot.column {{
            background: var(--column-color);
        }}

        .legend-dot.fieldparam {{
            background: var(--fieldparam-color);
        }}

        .legend-dot.visual {{
            background: var(--visual-color);
        }}

        .legend-dot.selected {{
            background: #00ffff;
        }}

        /* Responsive */
        @media (max-width: 900px) {{
            .sidebar {{
                width: 280px;
                min-width: 280px;
            }}
        }}

        @media (max-width: 700px) {{
            .app-container {{
                flex-direction: column;
            }}
            .sidebar {{
                width: 100%;
                max-height: 40vh;
            }}
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Left Sidebar -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">
                    <span class="sidebar-title-icon">📊</span>
                    <span>{model_name}</span>
                </div>
                <div class="sidebar-subtitle">Model Browser - Click to view dependencies</div>
            </div>

            <div class="sidebar-search">
                <input type="text" class="search-input" id="search-input" placeholder="Search measures, columns...">
            </div>

            <div class="sidebar-content" id="sidebar-content">
                <!-- Measures Panel -->
                <div class="category-panel" id="panel-measures">
                    <div class="category-header" onclick="toggleCategory('measures')">
                        <div class="category-title">
                            <div class="category-icon measure">📐</div>
                            <span class="category-name">Measures</span>
                        </div>
                        <div class="category-badge">
                            <span class="category-count" id="count-measures">{len(all_measures)}</span>
                            <span class="category-chevron">▼</span>
                        </div>
                    </div>
                    <div class="category-content" id="content-measures">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <!-- Columns Panel -->
                <div class="category-panel collapsed" id="panel-columns">
                    <div class="category-header" onclick="toggleCategory('columns')">
                        <div class="category-title">
                            <div class="category-icon column">📋</div>
                            <span class="category-name">Columns</span>
                        </div>
                        <div class="category-badge">
                            <span class="category-count" id="count-columns">{len(all_columns)}</span>
                            <span class="category-chevron">▼</span>
                        </div>
                    </div>
                    <div class="category-content" id="content-columns">
                        <!-- Populated by JS -->
                    </div>
                </div>

                <!-- Field Parameters Panel -->
                <div class="category-panel" id="panel-fieldparams">
                    <div class="category-header" onclick="toggleCategory('fieldparams')">
                        <div class="category-title">
                            <div class="category-icon fieldparam">🎛️</div>
                            <span class="category-name">Field Parameters</span>
                        </div>
                        <div class="category-badge">
                            <span class="category-count" id="count-fieldparams">{len(all_field_params)}</span>
                            <span class="category-chevron">▼</span>
                        </div>
                    </div>
                    <div class="category-content" id="content-fieldparams">
                        <!-- Populated by JS -->
                    </div>
                </div>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <header class="main-header">
                <div class="main-title">
                    <h1>PBIP Dependency Analysis</h1>
                    <span class="timestamp">Generated: {timestamp}</span>
                </div>
                <div class="toolbar">
                    <button class="btn btn-ghost" onclick="zoomIn()">🔍+ Zoom</button>
                    <button class="btn btn-ghost" onclick="zoomOut()">🔍- Zoom</button>
                    <button class="btn btn-ghost" onclick="resetZoom()">↺ Reset</button>
                    <button class="btn btn-primary" onclick="downloadSVG()">💾 Download SVG</button>
                </div>
            </header>

            <div class="diagram-area">
                <div class="selected-item-info" id="selected-item-info">
                    <div class="selected-item-badge">
                        <span class="selected-item-type" id="selected-type">MEASURE</span>
                        <span class="selected-item-name" id="selected-name">Select an item</span>
                    </div>
                    <div class="dependency-stats" id="dependency-stats">
                        <div class="dep-stat">
                            <span>Upstream:</span>
                            <span class="dep-stat-value" id="stat-upstream">0</span>
                        </div>
                        <div class="dep-stat">
                            <span>Downstream:</span>
                            <span class="dep-stat-value" id="stat-downstream">0</span>
                        </div>
                    </div>
                </div>

                <div class="diagram-container" id="diagram-container">
                    <div class="mermaid" id="mermaid-diagram"></div>
                </div>

                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-dot selected"></div>
                        <span>Selected Item</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot measure"></div>
                        <span>Measure</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot column"></div>
                        <span>Column</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot fieldparam"></div>
                        <span>Field Parameter</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot visual"></div>
                        <span>Visual</span>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // Data from Python
        const itemDependencies = {item_dependencies_json};
        const measuresByTable = {measures_by_table_json};
        const columnsByTable = {columns_by_table_json};
        const fieldParamsList = {field_params_json};
        const initialItem = {initial_item_json};

        // State
        let currentSelectedItem = null;
        let currentZoom = 1;

        // Mermaid configuration
        mermaid.initialize({{
            startOnLoad: false,
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
                nodeSpacing: 50,
                rankSpacing: 70,
                padding: 15,
                useMaxWidth: true
            }},
            securityLevel: 'loose'
        }});

        // Sanitize node ID for Mermaid
        function sanitizeNodeId(name, prefix = 'N') {{
            let clean = name.replace(/[\\[\\]]/g, '_').replace(/\\s/g, '_');
            clean = clean.replace(/[-\\/\\\\()%&'".,:\\+\\*=<>!#@$]/g, '_');
            clean = clean.replace(/_+/g, '_').replace(/^_|_$/g, '');
            return prefix + '_' + (clean || 'node');
        }}

        // Generate Mermaid diagram for selected item
        function generateDiagramForItem(itemKey) {{
            const item = itemDependencies[itemKey];
            if (!item) {{
                return 'flowchart LR\\n    nodata[No data available]';
            }}

            const lines = ['flowchart LR'];
            lines.push('');

            const rootId = sanitizeNodeId(item.key, item.type === 'measure' ? 'M' : item.type === 'column' ? 'C' : 'FP');
            const rootLabel = item.name.replace(/"/g, '\\"');

            // Root node (selected item)
            lines.push(`    ${{rootId}}["<b>${{rootLabel}}</b>"]:::selected`);
            lines.push('');

            const addedNodes = new Set([rootId]);
            const edges = [];

            // Add upstream nodes (what this item depends on)
            const upstream = item.upstream || {{}};

            // Upstream measures
            const upstreamMeasures = upstream.measures || [];
            if (upstreamMeasures.length > 0) {{
                lines.push('    subgraph Upstream_Measures["Upstream Measures"]');
                lines.push('    direction TB');
                upstreamMeasures.slice(0, 20).forEach(mKey => {{
                    const mItem = itemDependencies[mKey];
                    if (mItem) {{
                        const nodeId = sanitizeNodeId(mKey, 'UM');
                        const label = mItem.name.replace(/"/g, '\\"');
                        lines.push(`        ${{nodeId}}["${{label}}"]:::measure`);
                        addedNodes.add(nodeId);
                        edges.push({{ from: nodeId, to: rootId }});
                    }}
                }});
                if (upstreamMeasures.length > 20) {{
                    lines.push(`        UM_more["... +${{upstreamMeasures.length - 20}} more"]:::measure`);
                }}
                lines.push('    end');
                lines.push('');
            }}

            // Upstream columns
            const upstreamColumns = upstream.columns || [];
            if (upstreamColumns.length > 0) {{
                lines.push('    subgraph Upstream_Columns["Upstream Columns"]');
                lines.push('    direction TB');
                upstreamColumns.slice(0, 15).forEach(cKey => {{
                    const cItem = itemDependencies[cKey];
                    if (cItem) {{
                        const nodeId = sanitizeNodeId(cKey, 'UC');
                        const label = cItem.name.replace(/"/g, '\\"');
                        lines.push(`        ${{nodeId}}["${{label}}"]:::column`);
                        addedNodes.add(nodeId);
                        edges.push({{ from: nodeId, to: rootId }});
                    }}
                }});
                if (upstreamColumns.length > 15) {{
                    lines.push(`        UC_more["... +${{upstreamColumns.length - 15}} more"]:::column`);
                }}
                lines.push('    end');
                lines.push('');
            }}

            // Add downstream nodes (what depends on this item)
            const downstream = item.downstream || {{}};

            // Downstream measures
            const downstreamMeasures = downstream.measures || [];
            if (downstreamMeasures.length > 0) {{
                lines.push('    subgraph Downstream_Measures["Downstream Measures"]');
                lines.push('    direction TB');
                downstreamMeasures.slice(0, 20).forEach(mKey => {{
                    const mItem = itemDependencies[mKey];
                    if (mItem) {{
                        const nodeId = sanitizeNodeId(mKey, 'DM');
                        const label = mItem.name.replace(/"/g, '\\"');
                        lines.push(`        ${{nodeId}}["${{label}}"]:::measure`);
                        addedNodes.add(nodeId);
                        edges.push({{ from: rootId, to: nodeId }});
                    }}
                }});
                if (downstreamMeasures.length > 20) {{
                    lines.push(`        DM_more["... +${{downstreamMeasures.length - 20}} more"]:::measure`);
                }}
                lines.push('    end');
                lines.push('');
            }}

            // Downstream field parameters (for columns)
            const downstreamFieldParams = downstream.fieldParams || [];
            if (downstreamFieldParams.length > 0) {{
                lines.push('    subgraph Downstream_FieldParams["Field Parameters"]');
                lines.push('    direction TB');
                downstreamFieldParams.forEach(fpName => {{
                    const nodeId = sanitizeNodeId(fpName, 'DFP');
                    const label = fpName.replace(/"/g, '\\"');
                    lines.push(`        ${{nodeId}}["${{label}}"]:::fieldparam`);
                    addedNodes.add(nodeId);
                    edges.push({{ from: rootId, to: nodeId }});
                }});
                lines.push('    end');
                lines.push('');
            }}

            // Downstream visuals
            const downstreamVisuals = downstream.visuals || [];
            if (downstreamVisuals.length > 0) {{
                lines.push('    subgraph Downstream_Visuals["Visuals Using This"]');
                lines.push('    direction TB');
                downstreamVisuals.slice(0, 10).forEach((v, idx) => {{
                    const nodeId = `DV_${{idx}}`;
                    const label = `${{v.visual_type || 'Visual'}}\\n(${{v.page || 'Unknown Page'}})`.replace(/"/g, '\\"');
                    lines.push(`        ${{nodeId}}["${{label}}"]:::visual`);
                    addedNodes.add(nodeId);
                    edges.push({{ from: rootId, to: nodeId }});
                }});
                if (downstreamVisuals.length > 10) {{
                    lines.push(`        DV_more["... +${{downstreamVisuals.length - 10}} more visuals"]:::visual`);
                }}
                lines.push('    end');
                lines.push('');
            }}

            // Add edges
            edges.forEach(edge => {{
                lines.push(`    ${{edge.from}} --> ${{edge.to}}`);
            }});

            // Styling
            lines.push('');
            lines.push('    %% Styling');
            lines.push('    classDef selected fill:#00ffff,stroke:#00cccc,color:#000,stroke-width:3px');
            lines.push('    classDef measure fill:#2196F3,stroke:#1565C0,color:#fff,stroke-width:2px');
            lines.push('    classDef column fill:#9C27B0,stroke:#7B1FA2,color:#fff,stroke-width:2px');
            lines.push('    classDef fieldparam fill:#4CAF50,stroke:#388E3C,color:#fff,stroke-width:2px');
            lines.push('    classDef visual fill:#FF9800,stroke:#F57C00,color:#fff,stroke-width:2px');

            return lines.join('\\n');
        }}

        // Select an item and render its diagram
        async function selectItem(itemKey) {{
            // Update selection state
            currentSelectedItem = itemKey;

            // Update sidebar selection
            document.querySelectorAll('.item.selected').forEach(el => el.classList.remove('selected'));
            const itemEl = document.querySelector(`.item[data-key="${{CSS.escape(itemKey)}}"]`);
            if (itemEl) {{
                itemEl.classList.add('selected');
            }}

            // Get item data
            const item = itemDependencies[itemKey];
            if (!item) {{
                console.error('Item not found:', itemKey);
                return;
            }}

            // Update info panel
            document.getElementById('selected-type').textContent = item.type.toUpperCase().replace('_', ' ');
            document.getElementById('selected-type').className = 'selected-item-type ' + item.type;
            document.getElementById('selected-name').textContent = item.key;

            // Calculate stats
            const upstream = item.upstream || {{}};
            const downstream = item.downstream || {{}};
            const upstreamCount = (upstream.measures?.length || 0) + (upstream.columns?.length || 0);
            const downstreamCount = (downstream.measures?.length || 0) +
                                    (downstream.visuals?.length || 0) +
                                    (downstream.fieldParams?.length || 0);

            document.getElementById('stat-upstream').textContent = upstreamCount;
            document.getElementById('stat-downstream').textContent = downstreamCount;

            // Generate and render diagram
            const diagramCode = generateDiagramForItem(itemKey);
            const diagramContainer = document.getElementById('mermaid-diagram');

            try {{
                // Clear previous diagram
                diagramContainer.innerHTML = '';
                diagramContainer.removeAttribute('data-processed');

                // Generate unique ID for this render
                const id = 'mermaid-' + Date.now();

                // Render new diagram
                const {{ svg }} = await mermaid.render(id, diagramCode);
                diagramContainer.innerHTML = svg;

                // Reset zoom when switching items
                currentZoom = 1;
                applyZoom();
            }} catch (err) {{
                console.error('Mermaid render error:', err);
                diagramContainer.innerHTML = `<div class="no-diagram">
                    <div class="no-diagram-icon">⚠️</div>
                    <div class="no-diagram-text">Error rendering diagram</div>
                </div>`;
            }}
        }}

        // Toggle category panel
        function toggleCategory(category) {{
            const panel = document.getElementById('panel-' + category);
            if (panel) {{
                panel.classList.toggle('collapsed');
            }}
        }}

        // Toggle table group
        function toggleTableGroup(element) {{
            const group = element.closest('.table-group');
            if (group) {{
                group.classList.toggle('collapsed');
            }}
        }}

        // Populate sidebar
        function populateSidebar() {{
            // Measures
            const measuresContent = document.getElementById('content-measures');
            let measuresHtml = '';
            for (const [table, measures] of Object.entries(measuresByTable).sort()) {{
                measuresHtml += `
                    <div class="table-group">
                        <div class="table-group-header" onclick="toggleTableGroup(this)">
                            <span class="table-group-name">📁 ${{table}}</span>
                            <span class="table-group-count">${{measures.length}}</span>
                        </div>
                        <div class="table-group-items">
                            ${{measures.map(m => `
                                <div class="item measure" data-key="${{m.key}}" onclick="selectItem('${{m.key.replace(/'/g, "\\\\'")}}')" title="${{m.key}}">
                                    <span class="item-dot"></span>
                                    <span class="item-name">${{m.name}}</span>
                                </div>
                            `).join('')}}
                        </div>
                    </div>
                `;
            }}
            measuresContent.innerHTML = measuresHtml || '<div style="padding: 1rem; color: var(--text-muted); font-size: 0.75rem;">No measures found</div>';

            // Columns
            const columnsContent = document.getElementById('content-columns');
            let columnsHtml = '';
            for (const [table, columns] of Object.entries(columnsByTable).sort()) {{
                columnsHtml += `
                    <div class="table-group collapsed">
                        <div class="table-group-header" onclick="toggleTableGroup(this)">
                            <span class="table-group-name">📁 ${{table}}</span>
                            <span class="table-group-count">${{columns.length}}</span>
                        </div>
                        <div class="table-group-items">
                            ${{columns.map(c => `
                                <div class="item column" data-key="${{c.key}}" onclick="selectItem('${{c.key.replace(/'/g, "\\\\'")}}')" title="${{c.key}}">
                                    <span class="item-dot"></span>
                                    <span class="item-name">${{c.name}}</span>
                                </div>
                            `).join('')}}
                        </div>
                    </div>
                `;
            }}
            columnsContent.innerHTML = columnsHtml || '<div style="padding: 1rem; color: var(--text-muted); font-size: 0.75rem;">No columns found</div>';

            // Field Parameters
            const fpContent = document.getElementById('content-fieldparams');
            if (fieldParamsList.length > 0) {{
                fpContent.innerHTML = `
                    <div class="table-group-items">
                        ${{fieldParamsList.map(fp => `
                            <div class="item fieldparam" data-key="${{fp.key}}" onclick="selectItem('${{fp.key.replace(/'/g, "\\\\'")}}')" title="${{fp.key}}">
                                <span class="item-dot"></span>
                                <span class="item-name">${{fp.name}}</span>
                            </div>
                        `).join('')}}
                    </div>
                `;
            }} else {{
                fpContent.innerHTML = '<div style="padding: 1rem; color: var(--text-muted); font-size: 0.75rem;">No field parameters found</div>';
            }}
        }}

        // Search functionality
        function setupSearch() {{
            const searchInput = document.getElementById('search-input');
            searchInput.addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase();
                document.querySelectorAll('.item').forEach(item => {{
                    const name = item.querySelector('.item-name')?.textContent?.toLowerCase() || '';
                    const key = item.dataset.key?.toLowerCase() || '';
                    const matches = name.includes(query) || key.includes(query);
                    item.style.display = matches ? '' : 'none';
                }});

                // Expand all table groups when searching
                if (query) {{
                    document.querySelectorAll('.table-group').forEach(g => g.classList.remove('collapsed'));
                    document.querySelectorAll('.category-panel').forEach(p => p.classList.remove('collapsed'));
                }}
            }});
        }}

        // Zoom functions
        function zoomIn() {{
            currentZoom = Math.min(3, currentZoom + 0.2);
            applyZoom();
        }}

        function zoomOut() {{
            currentZoom = Math.max(0.3, currentZoom - 0.2);
            applyZoom();
        }}

        function resetZoom() {{
            currentZoom = 1;
            applyZoom();
        }}

        function applyZoom() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (svg) {{
                svg.style.transform = `scale(${{currentZoom}})`;
                svg.style.transformOrigin = 'center top';
            }}
        }}

        // Download SVG
        function downloadSVG() {{
            const svg = document.querySelector('#mermaid-diagram svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const blob = new Blob([svgData], {{ type: 'image/svg+xml' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const itemName = currentSelectedItem ? currentSelectedItem.replace(/[\\[\\]]/g, '_') : 'diagram';
                a.download = `${{itemName}}_dependencies.svg`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            populateSidebar();
            setupSearch();

            // Select initial item
            if (initialItem) {{
                selectItem(initialItem);
            }} else {{
                // Show empty state
                document.getElementById('mermaid-diagram').innerHTML = `
                    <div class="no-diagram">
                        <div class="no-diagram-icon">📊</div>
                        <div class="no-diagram-text">Select an item from the sidebar to view its dependencies</div>
                    </div>
                `;
            }}
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
