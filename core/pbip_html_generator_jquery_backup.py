"""
PBIP HTML Generator - Generates interactive HTML dashboard for PBIP analysis.

This module creates a comprehensive, interactive HTML dashboard with D3.js
visualizations, searchable tables, and dependency graphs.
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
    """Generates interactive HTML dashboard for PBIP analysis."""

    def __init__(self):
        """Initialize the HTML generator."""
        self.logger = logger

    def generate_full_report(
        self,
        model_data: Dict[str, Any],
        report_data: Optional[Dict[str, Any]],
        dependencies: Dict[str, Any],
        output_path: str,
        repository_name: str = "PBIP Repository"
    ) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            model_data: Parsed model data
            report_data: Optional parsed report data
            dependencies: Dependency analysis results
            output_path: Output directory path
            repository_name: Name of the repository

        Returns:
            Path to generated HTML file

        Raises:
            IOError: If unable to write output file
        """
        # Convert to absolute path for MCP compatibility
        abs_output_path = os.path.abspath(output_path)
        self.logger.info(f"Generating HTML report to {abs_output_path}")

        # Create output directory
        os.makedirs(abs_output_path, exist_ok=True)

        # Generate HTML content
        html_content = self._build_html_document(
            model_data,
            report_data,
            dependencies,
            repository_name
        )

        # Write to file
        html_file = os.path.join(abs_output_path, "index.html")
        try:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"HTML report generated: {html_file}")
            return html_file

        except Exception as e:
            self.logger.error(f"Failed to write HTML report: {e}")
            raise IOError(f"Failed to write HTML report: {e}")

    def _build_html_document(
        self,
        model_data: Dict,
        report_data: Optional[Dict],
        dependencies: Dict,
        repo_name: str
    ) -> str:
        """Build complete HTML document."""
        # Prepare data for JavaScript
        data_json = {
            "model": model_data,
            "report": report_data,
            "dependencies": dependencies,
            "generated": datetime.now().isoformat()
        }

        summary = dependencies.get("summary", {})

        # All tab panes must be in a single tab-content wrapper
        html_parts = [
            self._generate_html_head(repo_name),
            self._generate_nav_bar(repo_name),
            '<div class="container">',
            '<div class="tab-content mt-3">',  # Single tab-content wrapper
            self._generate_summary_section(summary, model_data, report_data),
            self._generate_model_section(model_data, dependencies),
        ]

        if report_data:
            html_parts.append(
                self._generate_report_section(report_data, dependencies)
            )

        html_parts.extend([
            self._generate_dependencies_section(dependencies),
            self._generate_usage_section(dependencies, model_data, report_data),
            '</div>',  # tab-content
            '</div>',  # container
            self._generate_javascript(data_json),
            '</body></html>'
        ])

        return '\n'.join(html_parts)

    def _generate_html_head(self, title: str) -> str:
        """Generate HTML head with libraries."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} - PBIP Analysis</title>

    <!-- External Libraries -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.18.0.min.js"></script>

    <!-- Styling -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">

    <style>
        :root {{
            --primary-color: #0078d4;
            --secondary-color: #106ebe;
            --success-color: #107c10;
            --warning-color: #ffb900;
            --danger-color: #d13438;
            --bg-light: #f3f2f1;
            --border-color: #edebe9;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-light);
            margin: 0;
            padding: 0;
        }}

        .navbar {{
            background-color: var(--primary-color);
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .navbar h1 {{
            color: white;
            margin: 0;
            font-size: 1.5rem;
        }}

        .nav-tabs {{
            margin-top: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}

        .nav-tabs .nav-link {{
            color: white;
            opacity: 0.8;
            border: none;
            border-bottom: 3px solid transparent;
        }}

        .nav-tabs .nav-link:hover {{
            opacity: 1;
            border-bottom-color: white;
        }}

        .nav-tabs .nav-link.active {{
            opacity: 1;
            background-color: transparent;
            border-bottom-color: white;
            color: white;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .section {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .section h2 {{
            color: var(--primary-color);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .kpi-card {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .kpi-card h3 {{
            font-size: 0.9rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            opacity: 0.9;
        }}

        .kpi-card .value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0;
        }}

        .kpi-card.warning {{
            background: linear-gradient(135deg, var(--warning-color), #f7a800);
        }}

        .kpi-card.success {{
            background: linear-gradient(135deg, var(--success-color), #0e8b0e);
        }}

        .tabs-container {{
            margin-top: 1.5rem;
        }}

        .tab-content {{
            padding: 1.5rem 0;
        }}

        .table-container {{
            overflow-x: auto;
        }}

        table.dataTable {{
            width: 100% !important;
            border-collapse: collapse;
        }}

        table.dataTable thead th {{
            background-color: var(--primary-color);
            color: white;
            font-weight: 600;
            padding: 12px;
            text-align: left;
        }}

        table.dataTable tbody tr:hover {{
            background-color: #f8f9fa;
        }}

        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }}

        .badge-primary {{
            background-color: var(--primary-color);
            color: white;
        }}

        .badge-success {{
            background-color: var(--success-color);
            color: white;
        }}

        .badge-warning {{
            background-color: var(--warning-color);
            color: #000;
        }}

        .badge-danger {{
            background-color: var(--danger-color);
            color: white;
        }}

        .chart-container {{
            height: 400px;
            margin: 1.5rem 0;
        }}

        .dependency-graph {{
            height: 600px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: #fafafa;
        }}

        .code-block {{
            background: #f5f5f5;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            overflow-x: auto;
            white-space: pre-wrap;
        }}

        .search-box {{
            width: 100%;
            padding: 0.75rem;
            border: 2px solid var(--border-color);
            border-radius: 4px;
            font-size: 1rem;
            margin-bottom: 1rem;
        }}

        .search-box:focus {{
            outline: none;
            border-color: var(--primary-color);
        }}

        .measure-item {{
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
        }}

        .measure-item h4 {{
            color: var(--primary-color);
            margin: 0 0 0.5rem 0;
        }}

        .measure-item .display-folder {{
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }}

        .measure-item .dax-preview {{
            background: #f5f5f5;
            padding: 0.5rem;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            max-height: 100px;
            overflow-y: auto;
        }}

        .usage-stats {{
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
        }}

        .usage-stats span {{
            font-size: 0.85rem;
            color: #666;
        }}

        .alert {{
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }}

        .alert-warning {{
            background-color: #fff4ce;
            border-left: 4px solid var(--warning-color);
        }}

        .alert-info {{
            background-color: #e6f4ff;
            border-left: 4px solid var(--primary-color);
        }}

        .visual-card {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
        }}

        .visual-card h4 {{
            margin: 0 0 0.5rem 0;
        }}

        .field-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }}

        .field-tag {{
            background: #e6f4ff;
            color: var(--primary-color);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
        }}

        .field-tag.measure {{
            background: #e6f7e6;
            color: var(--success-color);
        }}

        #dependency-graph svg {{
            width: 100%;
            height: 100%;
        }}

        .node {{
            cursor: pointer;
        }}

        .node circle {{
            fill: var(--primary-color);
            stroke: #fff;
            stroke-width: 2px;
        }}

        .node.measure circle {{
            fill: var(--success-color);
        }}

        .node.column circle {{
            fill: var(--warning-color);
        }}

        .node text {{
            font-size: 12px;
            fill: #333;
        }}

        .link {{
            fill: none;
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 1.5px;
        }}

        .link.dependency {{
            stroke: var(--primary-color);
        }}

        /* Expandable table styles */
        .table-expandable tbody tr {{
            cursor: pointer;
        }}

        .table-expandable tbody tr:hover {{
            background-color: #f0f8ff !important;
        }}

        .expand-icon {{
            width: 30px;
            text-align: center;
            color: var(--primary-color);
            font-weight: bold;
        }}

        .expand-toggle {{
            display: inline-block;
            transition: transform 0.3s ease;
        }}

        .expand-toggle.expanded {{
            transform: rotate(90deg);
        }}

        .table-details-row {{
            background-color: #f8f9fa !important;
        }}

        .table-details-content {{
            padding: 1.5rem;
            border-left: 4px solid var(--primary-color);
        }}

        .detail-section {{
            margin-bottom: 1.5rem;
        }}

        .detail-section h5 {{
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-size: 1.1rem;
        }}

        .columns-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }}

        .column-card {{
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 0.75rem;
        }}

        .column-card .column-name {{
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.25rem;
        }}

        .column-card .column-meta {{
            font-size: 0.85rem;
            color: #666;
        }}

        .metadata-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .metadata-table td {{
            padding: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .metadata-table td:first-child {{
            font-weight: 600;
            width: 200px;
        }}

        /* Dependency selector styles */
        .dependency-selector {{
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            height: 600px;
            overflow-y: auto;
        }}

        .dependency-selector h4 {{
            color: var(--primary-color);
            margin-bottom: 1rem;
        }}

        .dependency-selector h5 {{
            font-size: 0.9rem;
            color: #666;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }}

        .selector-list {{
            max-height: 300px;
            overflow-y: auto;
        }}

        .selector-item {{
            padding: 0.5rem;
            cursor: pointer;
            border-bottom: 1px solid var(--border-color);
            transition: background-color 0.2s;
        }}

        .selector-item:hover {{
            background-color: #f0f8ff;
        }}

        .selector-item.selected {{
            background-color: #e6f4ff;
            border-left: 3px solid var(--primary-color);
        }}

        .selector-item .item-name {{
            font-weight: 600;
            color: var(--primary-color);
        }}

        .selector-item .item-type {{
            font-size: 0.85rem;
            color: #666;
        }}

        .recent-list {{
            max-height: 150px;
            overflow-y: auto;
        }}

        .dependency-details-card {{
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
        }}

        .dependency-details-card h3 {{
            color: var(--primary-color);
            margin-bottom: 1rem;
        }}

        .dependency-section {{
            margin-bottom: 2rem;
        }}

        .dependency-section h5 {{
            color: var(--primary-color);
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }}

        .dependency-list {{
            list-style: none;
            padding: 0;
        }}

        .dependency-list li {{
            padding: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .dependency-list li:last-child {{
            border-bottom: none;
        }}

        .usage-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}

        .usage-badge.visual {{
            background-color: #e6f7e6;
            color: var(--success-color);
        }}

        .usage-badge.measure {{
            background-color: #e6f4ff;
            color: var(--primary-color);
        }}

        .usage-badge.column {{
            background-color: #fff4ce;
            color: #8b6914;
        }}

        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
        }}

        .btn-primary:hover {{
            background-color: var(--secondary-color);
        }}

        /* DAX and Code Display Styles */
        .dax-box {{
            margin-top: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #dee2e6;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}

        .dax-box pre {{
            margin: 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
            color: #333;
        }}

        .dax-expression {{
            margin-top: 10px;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid var(--primary-color);
            background: #f8f9fa;
        }}

        .dax-expression pre {{
            margin: 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .measures-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .measure-card {{
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 1rem;
            border-left: 4px solid var(--success-color);
        }}

        .measure-card .measure-name {{
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
            font-size: 1.05rem;
        }}

        .measure-card .measure-folder {{
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.75rem;
        }}

        .measure-card .dax-expression {{
            background: #f5f5f5;
            border-left-color: var(--success-color);
        }}

        .column-type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            background: #e9ecef;
            color: #495057;
        }}

        .column-type-badge.string {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .column-type-badge.number {{
            background: #d4edda;
            color: #155724;
        }}

        .column-type-badge.date {{
            background: #fff3cd;
            color: #856404;
        }}

        .table-metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 6px;
        }}

        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}

        .metadata-label {{
            font-size: 0.75rem;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.25rem;
        }}

        .metadata-value {{
            font-size: 1rem;
            font-weight: 600;
            color: #333;
        }}

        .type-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}

        .type-badge.dimension {{
            background: #e3f2fd;
            color: #1976d2;
        }}

        .type-badge.fact {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}

        .type-badge.slicer {{
            background: #fff3e0;
            color: #e65100;
        }}

        .type-badge.measure {{
            background: #e8f5e9;
            color: #2e7d32;
        }}

        .type-badge.lookup {{
            background: #fce4ec;
            color: #c2185b;
        }}

        /* Model Explorer Styles */
        .table-list-item {{
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #ccc;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .table-list-item:hover {{
            background: #e6f4ff;
            border-left-color: var(--primary-color);
            transform: translateX(2px);
        }}

        .table-list-item.active {{
            background: #e6f4ff;
            border-left-color: var(--primary-color);
            box-shadow: 0 2px 8px rgba(0, 120, 212, 0.2);
        }}

        .table-list-item[data-table-type="dimension"] {{
            border-left-color: #0078d4;
        }}

        .table-list-item[data-table-type="fact"] {{
            border-left-color: #7b1fa2;
        }}

        .table-list-item[data-table-type="measure"] {{
            border-left-color: #107c10;
        }}

        .table-list-item[data-table-type="slicer"] {{
            border-left-color: #e65100;
        }}

        .table-list-item[data-table-type="lookup"] {{
            border-left-color: #c2185b;
        }}

        .table-list-name {{
            font-weight: 600;
            color: #333;
            margin-bottom: 0.25rem;
            font-size: 0.95rem;
        }}

        .table-list-meta {{
            font-size: 0.8rem;
            color: #666;
        }}

        .table-detail-header {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}

        .table-detail-title {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .table-detail-title h2 {{
            margin: 0;
            color: var(--primary-color);
        }}

        .table-stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}

        .stat-card {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid var(--primary-color);
        }}

        .stat-card .stat-label {{
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.5rem;
        }}

        .stat-card .stat-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--primary-color);
        }}

        .detail-tabs {{
            margin-top: 2rem;
        }}

        .detail-tabs .nav-tabs {{
            border-bottom: 2px solid var(--border-color);
        }}

        .detail-tabs .nav-link {{
            color: #666;
            border: none;
            border-bottom: 3px solid transparent;
            padding: 0.75rem 1.5rem;
        }}

        .detail-tabs .nav-link:hover {{
            color: var(--primary-color);
            border-bottom-color: #ccc;
        }}

        .detail-tabs .nav-link.active {{
            color: var(--primary-color);
            border-bottom-color: var(--primary-color);
            background: transparent;
        }}
    </style>
</head>
<body>"""

    def _generate_nav_bar(self, title: str) -> str:
        """Generate navigation bar."""
        return f"""
<nav class="navbar">
    <h1>{html.escape(title)} - PBIP Analysis Dashboard</h1>
    <ul class="nav nav-tabs" id="mainTabs" role="tablist">
        <li class="nav-item" role="presentation">
            <button class="nav-link active" id="summary-tab" data-bs-toggle="tab"
                    data-bs-target="#summary" type="button" role="tab">Summary</button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="model-tab" data-bs-toggle="tab"
                    data-bs-target="#model" type="button" role="tab">Model</button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="report-tab" data-bs-toggle="tab"
                    data-bs-target="#report" type="button" role="tab">Report</button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="dependencies-tab" data-bs-toggle="tab"
                    data-bs-target="#dependencies" type="button" role="tab">Dependencies</button>
        </li>
        <li class="nav-item" role="presentation">
            <button class="nav-link" id="usage-tab" data-bs-toggle="tab"
                    data-bs-target="#usage" type="button" role="tab">Usage</button>
        </li>
    </ul>
</nav>"""

    def _generate_summary_section(
        self,
        summary: Dict,
        model_data: Dict,
        report_data: Optional[Dict]
    ) -> str:
        """Generate executive summary section."""
        total_tables = summary.get("total_tables", 0)
        total_measures = summary.get("total_measures", 0)
        total_columns = summary.get("total_columns", 0)
        total_relationships = summary.get("total_relationships", 0)
        unused_measures = summary.get("unused_measures", 0)
        unused_columns = summary.get("unused_columns", 0)

        total_pages = summary.get("total_pages", 0)
        total_visuals = summary.get("total_visuals", 0)

        # Calculate model statistics
        tables = model_data.get("tables", [])
        fact_tables = sum(1 for t in tables if t.get("name", "").lower().startswith(("f ", "'f ")))
        dim_tables = sum(1 for t in tables if t.get("name", "").lower().startswith(("d ", "'d ")))
        measure_tables = sum(1 for t in tables if t.get("name", "").lower().startswith(("m ", "'m ")))

        # Calculate usage percentages
        measures_used_pct = round((total_measures - unused_measures) / total_measures * 100, 1) if total_measures > 0 else 0
        columns_used_pct = round((total_columns - unused_columns) / total_columns * 100, 1) if total_columns > 0 else 0

        # Calculate additional insights
        avg_columns_per_table = round(total_columns / total_tables, 1) if total_tables > 0 else 0
        avg_measures_per_table = round(total_measures / total_tables, 1) if total_tables > 0 else 0
        measures_to_columns_ratio = round(total_measures / total_columns, 2) if total_columns > 0 else 0

        # Identify potential issues
        issues = []
        recommendations = []

        if unused_measures > total_measures * 0.2:
            issues.append(f"High number of unused measures ({unused_measures} measures, {round(unused_measures/total_measures*100, 1)}%)")
            recommendations.append("Review and remove unused measures to improve model maintainability")

        if unused_columns > total_columns * 0.3:
            issues.append(f"Significant unused columns detected ({unused_columns} columns, {round(unused_columns/total_columns*100, 1)}%)")
            recommendations.append("Consider removing unused columns to reduce model size and improve refresh performance")

        if total_measures > total_columns * 2:
            issues.append(f"Very high measure-to-column ratio ({measures_to_columns_ratio}:1)")
            recommendations.append("Review measure complexity and consider consolidating similar calculations")

        if fact_tables == 0 and dim_tables > 0:
            issues.append("No fact tables detected - model may be dimension-only")

        if total_relationships < (total_tables - 1) and total_tables > 1:
            issues.append("Low relationship count - some tables may be disconnected")
            recommendations.append("Review table relationships to ensure all tables are properly connected")

        html_content = f"""
<div class="tab-pane fade show active" id="summary" role="tabpanel">
    <div class="section">
        <h2>Model Overview</h2>

        <!-- Quick Stats Bar -->
        <div style="display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
            <div class="kpi-card" style="flex: 1; min-width: 150px;">
                <h3>Tables</h3>
                <div class="value">{total_tables}</div>
            </div>
            <div class="kpi-card" style="flex: 1; min-width: 150px;">
                <h3>Measures</h3>
                <div class="value">{total_measures}</div>
            </div>
            <div class="kpi-card" style="flex: 1; min-width: 150px;">
                <h3>Columns</h3>
                <div class="value">{total_columns}</div>
            </div>
            <div class="kpi-card" style="flex: 1; min-width: 150px;">
                <h3>Relationships</h3>
                <div class="value">{total_relationships}</div>
            </div>
        </div>

        <!-- Model Information -->
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid var(--primary-color); margin-bottom: 2rem;">
            <h3 style="margin-top: 0; color: var(--primary-color);">Model Information</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid var(--border-color);">
                    <td style="padding: 0.75rem 0; font-weight: 600; width: 200px;">Repository Path</td>
                    <td style="padding: 0.75rem 0;">{html.escape(model_data.get("model_folder", "Unknown"))}</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-color);">
                    <td style="padding: 0.75rem 0; font-weight: 600;">Model Type</td>
                    <td style="padding: 0.75rem 0;">Power BI Semantic Model (PBIP Format)</td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-color);">
                    <td style="padding: 0.75rem 0; font-weight: 600;">Architecture</td>
                    <td style="padding: 0.75rem 0;">
                        {'<span class="badge badge-primary">Star Schema</span>' if fact_tables > 0 and dim_tables > 0 else '<span class="badge badge-secondary">Custom</span>'}
                        <span style="margin-left: 1rem; color: #666;">{fact_tables} Fact · {dim_tables} Dimension · {measure_tables} Measure</span>
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid var(--border-color);">
                    <td style="padding: 0.75rem 0; font-weight: 600;">Expressions</td>
                    <td style="padding: 0.75rem 0;">{len(model_data.get("expressions", []))} M/Power Query expressions</td>
                </tr>
                {"<tr style='border-bottom: 1px solid var(--border-color);'><td style='padding: 0.75rem 0; font-weight: 600;'>Report Pages</td><td style='padding: 0.75rem 0;'>" + str(total_pages) + " pages with " + str(total_visuals) + " visuals</td></tr>" if report_data else ""}
            </table>
        </div>

        <!-- Key Insights -->
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #0078d4; margin-bottom: 2rem;">
            <h3 style="margin-top: 0; color: #0078d4;">📊 Key Insights</h3>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-top: 1rem;">
                <div>
                    <h4 style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">Table Distribution</h4>
                    <p style="margin: 0;">
                        {'<strong>' + str(round(fact_tables/total_tables*100, 1)) + '%</strong> fact tables, ' if fact_tables > 0 else ''}
                        <strong>{round(dim_tables/total_tables*100, 1)}%</strong> dimension tables
                        {', <strong>' + str(round(measure_tables/total_tables*100, 1)) + '%</strong> measure tables' if measure_tables > 0 else ''}
                    </p>
                </div>

                <div>
                    <h4 style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">Model Density</h4>
                    <p style="margin: 0;">
                        Average <strong>{avg_columns_per_table}</strong> columns per table<br>
                        Average <strong>{avg_measures_per_table}</strong> measures per table
                    </p>
                </div>

                <div>
                    <h4 style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">Measure Coverage</h4>
                    <p style="margin: 0;">
                        <strong>{measures_to_columns_ratio}:1</strong> measure-to-column ratio<br>
                        <strong>{measures_used_pct}%</strong> of measures are in use
                    </p>
                </div>

                <div>
                    <h4 style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">Data Quality</h4>
                    <p style="margin: 0;">
                        <strong>{columns_used_pct}%</strong> of columns are referenced<br>
                        <strong>{total_relationships}</strong> active relationships
                    </p>
                </div>
            </div>
        </div>

        <!-- Issues & Recommendations -->
        {"<div style='background: #fff3cd; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 2rem;'><h3 style='margin-top: 0; color: #856404;'>⚠️ Attention Required</h3><ul style='margin: 0; padding-left: 1.5rem;'>" + ''.join(f"<li style='margin-bottom: 0.5rem;'>{issue}</li>" for issue in issues) + "</ul></div>" if issues else ""}

        {"<div style='background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 2rem;'><h3 style='margin-top: 0; color: #28a745;'>💡 Recommendations</h3><ul style='margin: 0; padding-left: 1.5rem;'>" + ''.join(f"<li style='margin-bottom: 0.5rem;'>{rec}</li>" for rec in recommendations) + "</ul></div>" if recommendations else ""}

        <!-- Model Health Summary -->
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #17a2b8;">
            <h3 style="margin-top: 0; color: #17a2b8;">🏥 Model Health Summary</h3>
            <p style="margin-bottom: 1rem;">
                {
                    "This model appears well-structured with good measure and column utilization."
                    if len(issues) == 0
                    else f"This model has {len(issues)} area(s) that may benefit from optimization. Review the recommendations above."
                }
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                    <strong>Unused Objects:</strong> {unused_measures} measures, {unused_columns} columns
                </div>
                <div style="padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                    <strong>Model Complexity:</strong> {
                        'Low' if total_measures < 50 and total_columns < 100
                        else 'Medium' if total_measures < 200 and total_columns < 500
                        else 'High'
                    }
                </div>
            </div>
        </div>
    </div>
</div>"""

        return html_content

    def _generate_model_section(
        self,
        model_data: Dict,
        dependencies: Dict
    ) -> str:
        """Generate model inventory section with explorer-style layout."""
        tables = model_data.get("tables", [])

        html_content = """
<div class="tab-pane fade" id="model" role="tabpanel">
    <div class="section" style="padding: 0;">
        <div style="display: flex; height: calc(100vh - 200px); min-height: 600px;">
            <!-- Left Sidebar: Tables List -->
            <div style="width: 320px; border-right: 2px solid var(--border-color); overflow-y: auto; background: #fafafa; padding: 1rem;">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem; padding: 0 0.5rem;">Tables</h3>
                <div style="font-size: 0.9rem; color: #666; margin-bottom: 1rem; padding: 0 0.5rem;">{len(tables)} total</div>
                <input type="search" class="search-box" id="model-search" placeholder="Search tables..." style="margin-bottom: 1rem;">
                <div id="tables-list">"""

        # Generate table list items
        for idx, table in enumerate(tables):
            table_name = html.escape(table.get("name", ""))
            column_count = len(table.get("columns", []))
            measure_count = len(table.get("measures", []))
            is_hidden = table.get("is_hidden", False)

            # Determine table type
            table_type = "dimension"
            if table_name.lower().startswith(("f ", "'f ")):
                table_type = "fact"
            elif table_name.lower().startswith(("m ", "'m ")):
                table_type = "measure"
            elif table_name.lower().startswith(("s ", "'s ")):
                table_type = "slicer"
            elif table_name.lower().startswith(("l ", "'l ")):
                table_type = "lookup"

            active_class = "active" if idx == 0 else ""

            html_content += f"""
                    <div class="table-list-item {active_class}" data-table-index="{idx}" data-table-type="{table_type}">
                        <div class="table-list-name">{table_name}</div>
                        <div class="table-list-meta">
                            <span>{column_count} columns · {measure_count} measures</span>
                            {'<span class="badge badge-warning" style="font-size: 0.7rem; margin-left: 0.5rem;">Hidden</span>' if is_hidden else ''}
                        </div>
                    </div>"""

        html_content += """
                </div>
            </div>

            <!-- Right Panel: Table Details -->
            <div style="flex: 1; overflow-y: auto; background: white; padding: 2rem;" id="table-detail-panel">
                <div class="alert alert-info">
                    <strong>Tip:</strong> Select a table from the left to view its details.
                </div>
            </div>
        </div>
    </div>
</div>"""

        return html_content

    def _generate_report_section(
        self,
        report_data: Dict,
        dependencies: Dict
    ) -> str:
        """Generate report overview section with page sidebar and visual grouping."""
        pages = report_data.get("pages", [])

        # Build page list with IDs
        pages_with_data = []
        for idx, page in enumerate(pages):
            visuals = page.get("visuals", [])
            visuals_with_data = []
            for visual in visuals:
                fields = visual.get("fields", {})
                measures = fields.get("measures", [])
                columns = fields.get("columns", [])
                if measures or columns:
                    visuals_with_data.append((visual, measures, columns))

            if visuals_with_data:
                pages_with_data.append({
                    "index": idx,
                    "name": page.get("display_name", f"Page {idx+1}"),
                    "visuals": visuals_with_data,
                    "filters": page.get("filters", [])
                })

        html_content = """
<div class="tab-pane fade" id="report" role="tabpanel">
    <div style="display: flex; height: calc(100vh - 200px);">
        <!-- Left Sidebar: Page Selector -->
        <div style="width: 280px; border-right: 2px solid var(--border-color); overflow-y: auto; padding: 1rem;">
            <h3 style="margin-bottom: 1rem;">Pages</h3>
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 1rem;">
                {len_pages} pages with data
            </div>
            <div class="list-group">"""

        # Generate page list
        for page_info in pages_with_data:
            page_id = f"report-page-{page_info['index']}"
            page_name = html.escape(page_info['name'])
            visual_count = len(page_info['visuals'])
            filter_count = len(page_info['filters'])

            active_class = "active" if page_info['index'] == 0 else ""

            html_content += f"""
                <a href="#" class="list-group-item list-group-item-action {active_class}"
                   onclick="showReportPage('{page_id}'); return false;"
                   style="border-left: 3px solid {'var(--primary-color)' if active_class else 'transparent'}; margin-bottom: 0.5rem;">
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">{page_name}</div>
                    <div style="font-size: 0.75rem; color: #666;">
                        {visual_count} visuals · {filter_count} filters
                    </div>
                </a>"""

        html_content += """
            </div>
        </div>

        <!-- Right Panel: Page Content -->
        <div style="flex: 1; overflow-y: auto; padding: 1.5rem;">
            <div class="alert alert-info" style="margin-bottom: 1.5rem;">
                <strong>Tip:</strong> Select a page from the sidebar. Visuals with the same name are grouped together.
            </div>
            <div id="report-pages-content">"""

        # Generate each page content
        for page_info in pages_with_data:
            page_id = f"report-page-{page_info['index']}"
            page_name = html.escape(page_info['name'])
            display_style = "display: block;" if page_info['index'] == 0 else "display: none;"

            html_content += f"""
                <div id="{page_id}" class="report-page-content" style="{display_style}">
                    <h2 style="color: var(--primary-color); margin-bottom: 1rem;">{page_name}</h2>"""

            # Show page filters if any
            if page_info['filters']:
                html_content += """
                    <div style="margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 6px;">
                        <h5>Page Filters</h5>
                        <div class="field-list">"""
                for filt in page_info['filters']:
                    field = filt.get("field", {})
                    field_name = f"{field.get('table', '')}[{field.get('name', '')}]"
                    field_type = field.get("type", "Unknown")
                    badge_class = "measure" if field_type == "Measure" else "column"
                    html_content += f"""
                            <span class="field-tag {badge_class}">{html.escape(field_name)}</span>"""
                html_content += """
                        </div>
                    </div>"""

            # Group visuals by name (visual_type or visual name)
            visual_groups = {}
            for visual, measures, columns in page_info['visuals']:
                visual_type = visual.get("visual_type", "unknown")
                visual_name = visual.get("name", visual_type)
                group_key = visual_name if visual_name else visual_type

                if group_key not in visual_groups:
                    visual_groups[group_key] = []
                visual_groups[group_key].append((visual, measures, columns))

            # Display grouped visuals
            for group_name, group_visuals in visual_groups.items():
                group_name_display = html.escape(group_name)

                if len(group_visuals) > 1:
                    # Multiple visuals with same name - show as collapsible group
                    group_id = f"{page_id}-group-{hash(group_name) % 10000}"
                    html_content += f"""
                        <div style="margin-bottom: 1.5rem;">
                            <div style="background: #f0f4ff; padding: 0.75rem; border-radius: 6px; border-left: 4px solid var(--primary-color); cursor: pointer;"
                                 onclick="toggleVisualGroup('{group_id}')">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: var(--primary-color);">{group_name_display}</strong>
                                    <span class="badge badge-primary">{len(group_visuals)} instances</span>
                                </div>
                            </div>
                            <div id="{group_id}" style="margin-top: 0.5rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1rem;">"""

                    for visual, measures, columns in group_visuals:
                        html_content += self._render_visual_card(visual, measures, columns)

                    html_content += """
                            </div>
                        </div>"""
                else:
                    # Single visual
                    html_content += '<div style="margin-bottom: 1rem;">'
                    for visual, measures, columns in group_visuals:
                        html_content += self._render_visual_card(visual, measures, columns)
                    html_content += '</div>'

            html_content += """
                </div>"""

        html_content += """
            </div>
        </div>
    </div>
</div>

<script>
function showReportPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.report-page-content').forEach(page => {
        page.style.display = 'none';
    });

    // Show selected page
    document.getElementById(pageId).style.display = 'block';

    // Update active state in sidebar
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
        item.style.borderLeft = '3px solid transparent';
    });
    event.target.closest('.list-group-item').classList.add('active');
    event.target.closest('.list-group-item').style.borderLeft = '3px solid var(--primary-color)';
}

function toggleVisualGroup(groupId) {
    const group = document.getElementById(groupId);
    if (group.style.display === 'none' || group.style.display === '') {
        group.style.display = 'grid';
    } else {
        group.style.display = 'none';
    }
}
</script>"""

        return html_content.replace("{len_pages}", str(len(pages_with_data)))

    def _render_visual_card(
        self,
        visual: Dict,
        measures: List,
        columns: List
    ) -> str:
        """Render a single visual card."""
        visual_type = html.escape(visual.get("visual_type", "unknown"))
        visual_id = html.escape(visual.get("id", ""))

        card_html = f"""
            <div style="background: white; border: 1px solid var(--border-color); border-radius: 6px; padding: 1rem; border-left: 4px solid var(--primary-color);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <strong style="color: var(--primary-color);">{visual_type}</strong>
                    <span style="font-size: 0.75rem; color: #666;">{visual_id[:8]}...</span>
                </div>"""

        # Show measures
        if measures:
            card_html += f"""
                <div style="margin-bottom: 0.75rem;">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #666; margin-bottom: 0.5rem;">Measures ({len(measures)})</div>
                    <div class="field-list">"""
            for measure in measures:
                measure_name = f"{measure.get('table', '')}[{measure.get('measure', '')}]"
                card_html += f"""
                        <span class="field-tag measure">{html.escape(measure_name)}</span>"""
            card_html += """
                    </div>
                </div>"""

        # Show columns
        if columns:
            card_html += f"""
                <div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: #666; margin-bottom: 0.5rem;">Columns ({len(columns)})</div>
                    <div class="field-list">"""
            for column in columns:
                column_name = f"{column.get('table', '')}[{column.get('column', '')}]"
                card_html += f"""
                        <span class="field-tag">{html.escape(column_name)}</span>"""
            card_html += """
                    </div>
                </div>"""

        card_html += """
            </div>"""

        return card_html

    def _generate_dependencies_section(self, dependencies: Dict) -> str:
        """Generate dependencies visualization section with interactive viewer."""
        return """
<div class="tab-pane fade" id="dependencies" role="tabpanel">
    <div class="section">
        <h2>Dependency Analysis</h2>

        <div class="row">
            <!-- Left Panel: Search & Select -->
            <div class="col-md-4">
                <div class="dependency-selector">
                    <h4>Select Object to Analyze</h4>
                    <div class="mb-3">
                        <label class="form-label">Search Measures & Columns</label>
                        <input type="search" class="search-box" id="dependency-search"
                               placeholder="Type to search...">
                    </div>

                    <div class="dependency-lists">
                        <h5>Recent Selections</h5>
                        <div id="recent-selections" class="recent-list"></div>

                        <h5 class="mt-3">All Measures</h5>
                        <div id="measures-selector-list" class="selector-list"></div>
                    </div>
                </div>
            </div>

            <!-- Right Panel: Dependency Details -->
            <div class="col-md-8">
                <div id="dependency-details">
                    <div class="alert alert-info">
                        <strong>Instructions:</strong> Search or select a measure/column from the left panel to view its dependencies and usage.
                    </div>
                </div>
            </div>
        </div>

        <!-- Dependency Graph (collapsible) -->
        <div class="mt-4">
            <button class="btn btn-primary mb-3" type="button" id="show-graph-btn">
                Show Dependency Graph
            </button>
            <div id="graph-container" style="display: none;">
                <div class="alert alert-info">
                    <strong>Interactive Graph:</strong> Shows top 50 measure dependencies.
                    Green nodes are measures, orange nodes are columns. Drag nodes to rearrange.
                </div>
                <div id="dependency-graph" class="dependency-graph"></div>
            </div>
        </div>

        <!-- Statistics -->
        <div class="mt-4">
            <h3>Dependency Statistics</h3>
            <div id="dependency-stats"></div>
        </div>
    </div>
</div>"""

    def _generate_usage_section(
        self,
        dependencies: Dict,
        model_data: Dict,
        report_data: Optional[Dict]
    ) -> str:
        """Generate usage analysis section."""
        unused_measures = dependencies.get("unused_measures", [])
        unused_columns = dependencies.get("unused_columns", [])

        html_content = """
<div class="tab-pane fade" id="usage" role="tabpanel">
    <div class="section">
        <h2>Usage & Cross-Reference Analysis</h2>

        <div class="row">
            <div class="col-md-6">
                <h3>Unused Measures</h3>"""

        if unused_measures:
            html_content += f"""
                <div class="alert alert-warning">
                    <strong>Warning:</strong> Found {len(unused_measures)} measures not used in any visuals or other measures.
                </div>
                <ul>"""
            for measure in unused_measures[:20]:  # Limit display
                html_content += f"<li>{html.escape(measure)}</li>"
            if len(unused_measures) > 20:
                html_content += f"<li><em>... and {len(unused_measures) - 20} more</em></li>"
            html_content += "</ul>"
        else:
            html_content += '<p class="text-success">All measures are in use!</p>'

        html_content += """
            </div>
            <div class="col-md-6">
                <h3>Unused Columns</h3>"""

        if unused_columns:
            html_content += f"""
                <div class="alert alert-warning">
                    <strong>Warning:</strong> Found {len(unused_columns)} columns not used anywhere.
                </div>
                <ul>"""
            for column in unused_columns[:20]:  # Limit display
                html_content += f"<li>{html.escape(column)}</li>"
            if len(unused_columns) > 20:
                html_content += f"<li><em>... and {len(unused_columns) - 20} more</em></li>"
            html_content += "</ul>"
        else:
            html_content += '<p class="text-success">All columns are in use!</p>'

        html_content += """
            </div>
        </div>
    </div>
</div>"""

        return html_content

    def _generate_javascript(self, data_json: Dict) -> str:
        """Generate JavaScript for interactivity."""
        data_json_str = json.dumps(data_json, indent=2)

        return f"""
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
// Embedded data
const pbipData = {data_json_str};

$(document).ready(function() {{
    console.log("PBIP Dashboard initialized");
    console.log("Data:", pbipData);

    // Initialize model explorer
    initializeModelExplorer();

    // Render dependency stats
    renderDependencyStats();
}});

function initializeModelExplorer() {{
    // Handle table selection
    $('.table-list-item').on('click', function() {{
        // Update active state
        $('.table-list-item').removeClass('active');
        $(this).addClass('active');

        // Get table index
        const tableIndex = $(this).data('table-index');

        // Render table details
        renderTableDetails(tableIndex);
    }});

    // Initialize with first table
    if (pbipData.model.tables.length > 0) {{
        renderTableDetails(0);
    }}

    // Handle search
    $('#model-search').on('keyup', function() {{
        const searchTerm = $(this).val().toLowerCase();
        $('.table-list-item').each(function() {{
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(searchTerm));
        }});
    }});
}}

function renderTableDetails(tableIndex) {{
    const table = pbipData.model.tables[tableIndex];
    if (!table) return;

    const columns = table.columns || [];
    const measures = table.measures || [];
    const partitions = table.partitions || [];
    const relationships = pbipData.model.relationships || [];

    // Count relationships for this table
    const tableRelCount = relationships.filter(rel =>
        rel.from_table === table.name || rel.to_table === table.name
    ).length;

    // Calculate estimated rows (from partition info or default)
    const estimatedRows = 145; // TODO: Extract from partition if available

    // Determine table type and complexity
    let tableTypeLabel = "DIMENSION";
    let tableTypeBadgeClass = "dimension";
    let complexityLabel = "LOW";

    const tableName = table.name.toLowerCase();
    if (tableName.startsWith("f ") || tableName.startsWith("'f ")) {{
        tableTypeLabel = "FACT";
        tableTypeBadgeClass = "fact";
        complexityLabel = columns.length > 20 ? "HIGH" : "MEDIUM";
    }} else if (tableName.startsWith("m ") || tableName.startsWith("'m ")) {{
        tableTypeLabel = "MEASURE";
        tableTypeBadgeClass = "measure";
        complexityLabel = "LOW";
    }} else if (tableName.startsWith("s ") || tableName.startsWith("'s ")) {{
        tableTypeLabel = "SLICER";
        tableTypeBadgeClass = "slicer";
    }} else if (tableName.startsWith("l ") || tableName.startsWith("'l ")) {{
        tableTypeLabel = "LOOKUP";
        tableTypeBadgeClass = "lookup";
    }}

    // Build detail HTML
    let detailHtml = `
        <div class="table-detail-header">
            <div class="table-detail-title">
                <h2>${{table.name}}</h2>
                <span class="type-badge ${{tableTypeBadgeClass}}">${{tableTypeLabel}}</span>
                <span class="badge badge-success">Complexity: ${{complexityLabel}}</span>
            </div>

            <div class="table-stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Rows</div>
                    <div class="stat-value">${{estimatedRows}}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Columns</div>
                    <div class="stat-value">${{columns.length}}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Measures</div>
                    <div class="stat-value">${{measures.length}}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Relationships</div>
                    <div class="stat-value">${{tableRelCount}}</div>
                </div>
            </div>
        </div>

        <div class="detail-tabs">
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item">
                    <a class="nav-link active" data-bs-toggle="tab" href="#columns-tab-${{tableIndex}}">Columns (${{columns.length}})</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#measures-tab-${{tableIndex}}">Measures (${{measures.length}})</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#relationships-tab-${{tableIndex}}">Relationships (${{tableRelCount}})</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#usage-tab-${{tableIndex}}">Usage (1)</a>
                </li>
            </ul>

            <div class="tab-content" style="padding-top: 1.5rem;">
                <div class="tab-pane fade show active" id="columns-tab-${{tableIndex}}">
                    ${{renderColumnsTab(columns)}}
                </div>
                <div class="tab-pane fade" id="measures-tab-${{tableIndex}}">
                    ${{renderMeasuresTab(measures)}}
                </div>
                <div class="tab-pane fade" id="relationships-tab-${{tableIndex}}">
                    ${{renderRelationshipsTab(table.name, relationships)}}
                </div>
                <div class="tab-pane fade" id="usage-tab-${{tableIndex}}">
                    ${{renderUsageTab(table.name, columns, measures)}}
                </div>
            </div>
        </div>
    `;

    $('#table-detail-panel').html(detailHtml);
}}

function renderColumnsTab(columns) {{
    if (columns.length === 0) {{
        return '<p class="text-muted">No columns in this table.</p>';
    }}

    let html = '<div class="columns-grid">';
    columns.forEach(col => {{
        const dataType = col.data_type || 'unknown';
        const sourceColumn = col.source_column || '-';
        const displayFolder = col.display_folder || 'None';
        const isHidden = col.is_hidden ? '<span class="badge badge-warning">Hidden</span>' : '';
        const isKey = col.name.toLowerCase().includes('key') ? '<span class="usage-badge column">🔑 Key</span>' : '';

        // Determine type badge class
        let typeClass = '';
        const lowerType = dataType.toLowerCase();
        if (lowerType.includes('string') || lowerType.includes('text')) {{
            typeClass = 'string';
        }} else if (lowerType.includes('int') || lowerType.includes('double') || lowerType.includes('decimal')) {{
            typeClass = 'number';
        }} else if (lowerType.includes('date') || lowerType.includes('time')) {{
            typeClass = 'date';
        }}

        html += `
            <div class="column-card">
                <div class="column-name">${{col.name}} ${{isHidden}} ${{isKey}}</div>
                <div class="column-meta">
                    <span class="column-type-badge ${{typeClass}}">${{dataType}}</span><br>
                    <strong>Source:</strong> ${{sourceColumn}}<br>
                    <strong>Folder:</strong> ${{displayFolder}}
                </div>
            </div>
        `;
    }});
    html += '</div>';
    return html;
}}

function renderMeasuresTab(measures) {{
    if (measures.length === 0) {{
        return '<p class="text-muted">No measures in this table.</p>';
    }}

    let html = '<div class="measures-list">';
    measures.forEach(measure => {{
        const displayFolder = measure.display_folder || 'None';
        const expression = measure.expression || '';
        const escapedExpression = expression
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
        const isHidden = measure.is_hidden ? '<span class="badge badge-warning">Hidden</span>' : '';

        html += `
            <div class="measure-card">
                <div class="measure-name">${{measure.name}} ${{isHidden}}</div>
                <div class="measure-folder">
                    <strong>Display Folder:</strong> ${{displayFolder}}
                </div>
                <div class="dax-expression">
                    <pre>${{escapedExpression}}</pre>
                </div>
            </div>
        `;
    }});
    html += '</div>';
    return html;
}}

function renderRelationshipsTab(tableName, relationships) {{
    const tableRels = relationships.filter(rel =>
        rel.from_table === tableName || rel.to_table === tableName
    );

    if (tableRels.length === 0) {{
        return '<p class="text-muted">No relationships for this table.</p>';
    }}

    let html = '<div style="overflow-x: auto;"><table class="table" style="width: 100%;">';
    html += '<thead><tr><th>From</th><th>To</th><th>Active</th><th>Cross Filter</th></tr></thead><tbody>';

    tableRels.forEach(rel => {{
        const fromRef = `${{rel.from_table}}[${{rel.from_column_name}}]`;
        const toRef = `${{rel.to_table}}[${{rel.to_column_name}}]`;
        const isActive = rel.is_active !== false;
        const activeBadge = isActive ?
            '<span class="badge badge-success">Active</span>' :
            '<span class="badge badge-warning">Inactive</span>';
        const crossFilter = rel.cross_filtering_behavior || '';

        html += `
            <tr>
                <td>${{fromRef}}</td>
                <td>${{toRef}}</td>
                <td>${{activeBadge}}</td>
                <td>${{crossFilter}}</td>
            </tr>
        `;
    }});

    html += '</tbody></table></div>';
    return html;
}}

function renderUsageTab(tableName, columns, measures) {{
    const dependencies = pbipData.dependencies;
    const columnToMeasure = dependencies.column_to_measure || {{}};
    const visualDeps = dependencies.visual_dependencies || {{}};
    const measureToMeasureReverse = dependencies.measure_to_measure_reverse || {{}};
    const report = pbipData.report;

    let html = '<div class="usage-analysis">';
    html += '<h5>Column Usage Analysis</h5>';
    html += '<div style="margin-bottom: 2rem;">';

    const columnsWithUsage = [];

    // Analyze each column
    columns.forEach(col => {{
        const columnKey = `${{tableName}}[${{col.name}}]`;
        const usedInMeasures = columnToMeasure[columnKey] || [];

        // Find visual usage
        let visualUsageCount = 0;
        const visualPages = new Set();
        Object.values(visualDeps).forEach(vDep => {{
            const columns = vDep.columns || [];
            if (columns.includes(columnKey)) {{
                visualUsageCount++;
                visualPages.add(vDep.page);
            }}
        }});

        const totalUsage = usedInMeasures.length + visualUsageCount;
        if (totalUsage > 0) {{
            columnsWithUsage.push({{
                name: col.name,
                key: columnKey,
                usedInMeasures,
                visualUsageCount,
                visualPages: Array.from(visualPages),
                totalUsage
            }});
        }}
    }});

    if (columnsWithUsage.length === 0) {{
        html += '<p class="text-muted">No column usage found (columns may be unused).</p>';
    }} else {{
        // Sort by total usage descending
        columnsWithUsage.sort((a, b) => b.totalUsage - a.totalUsage);

        html += '<table class="table table-hover"><thead><tr>';
        html += '<th>Column</th><th>Used in Measures</th><th>Used in Visuals</th><th>Pages</th>';
        html += '</tr></thead><tbody>';

        columnsWithUsage.forEach(col => {{
            html += `<tr>`;
            html += `<td><strong>${{col.name}}</strong></td>`;
            html += `<td>${{col.usedInMeasures.length}}</td>`;
            html += `<td>${{col.visualUsageCount}}</td>`;
            html += `<td>${{col.visualPages.length > 0 ? col.visualPages.slice(0, 3).join(', ') : '-'}}</td>`;
            html += `</tr>`;
        }});

        html += '</tbody></table>';
    }}

    html += '</div>';

    // Measure Usage Analysis
    html += '<h5>Measure Usage Analysis</h5>';
    html += '<div>';

    const measuresWithUsage = [];

    measures.forEach(meas => {{
        const measureKey = `${{tableName}}[${{meas.name}}]`;
        const usedByMeasures = measureToMeasureReverse[measureKey] || [];

        // Find visual usage
        let visualUsageCount = 0;
        const visualPages = new Set();
        Object.values(visualDeps).forEach(vDep => {{
            const measures = vDep.measures || [];
            if (measures.includes(measureKey)) {{
                visualUsageCount++;
                visualPages.add(vDep.page);
            }}
        }});

        const totalUsage = usedByMeasures.length + visualUsageCount;
        measuresWithUsage.push({{
            name: meas.name,
            key: measureKey,
            usedByMeasures,
            visualUsageCount,
            visualPages: Array.from(visualPages),
            totalUsage
        }});
    }});

    if (measuresWithUsage.length === 0) {{
        html += '<p class="text-muted">No measures in this table.</p>';
    }} else {{
        // Sort by total usage descending
        measuresWithUsage.sort((a, b) => b.totalUsage - a.totalUsage);

        html += '<table class="table table-hover"><thead><tr>';
        html += '<th>Measure</th><th>Used by Measures</th><th>Used in Visuals</th><th>Pages</th>';
        html += '</tr></thead><tbody>';

        measuresWithUsage.forEach(meas => {{
            const usageClass = meas.totalUsage === 0 ? 'text-muted' : '';
            html += `<tr class="${{usageClass}}">`;
            html += `<td><strong>${{meas.name}}</strong></td>`;
            html += `<td>${{meas.usedByMeasures.length}}</td>`;
            html += `<td>${{meas.visualUsageCount}}</td>`;
            html += `<td>${{meas.visualPages.length > 0 ? meas.visualPages.slice(0, 3).join(', ') : '-'}}</td>`;
            html += `</tr>`;
        }});

        html += '</tbody></table>';
    }}

    html += '</div>';
    html += '</div>';

    return html;
}}

// Removed old formatTableDetails and renderMeasuresList functions (now integrated into model explorer)

function renderDependencyGraph() {{
    const dependencies = pbipData.dependencies;
    const measureToMeasure = dependencies.measure_to_measure;

    // Build nodes and links
    const nodes = {{}};
    const links = [];

    Object.keys(measureToMeasure).forEach(source => {{
        if (!nodes[source]) {{
            nodes[source] = {{ id: source, type: 'measure' }};
        }}

        (measureToMeasure[source] || []).forEach(target => {{
            if (!nodes[target]) {{
                nodes[target] = {{ id: target, type: 'measure' }};
            }}
            links.push({{ source: source, target: target }});
        }});
    }});

    const nodeArray = Object.values(nodes).slice(0, 50); // Limit for performance
    const linkArray = links.slice(0, 100);

    // Create force-directed graph
    const width = $('#dependency-graph').width();
    const height = 600;

    const svg = d3.select('#dependency-graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    const simulation = d3.forceSimulation(nodeArray)
        .force('link', d3.forceLink(linkArray).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg.append('g')
        .selectAll('line')
        .data(linkArray)
        .enter().append('line')
        .attr('class', 'link dependency')
        .attr('stroke-width', 2);

    const node = svg.append('g')
        .selectAll('g')
        .data(nodeArray)
        .enter().append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.append('circle')
        .attr('r', 8)
        .attr('class', d => d.type);

    node.append('text')
        .attr('dx', 12)
        .attr('dy', 4)
        .text(d => {{
            const parts = d.id.split('[');
            if (parts.length > 1) {{
                return parts[1].replace(']', '').substring(0, 20);
            }}
            return d.id.substring(0, 20);
        }});

    simulation.on('tick', () => {{
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
    }});

    function dragstarted(event, d) {{
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }}

    function dragged(event, d) {{
        d.fx = event.x;
        d.fy = event.y;
    }}

    function dragended(event, d) {{
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }}
}}

function renderDependencyStats() {{
    const dependencies = pbipData.dependencies;
    const measureToMeasure = dependencies.measure_to_measure;

    // Calculate stats
    const totalMeasures = Object.keys(measureToMeasure).length;
    const avgDeps = totalMeasures > 0
        ? Object.values(measureToMeasure).reduce((sum, deps) => sum + deps.length, 0) / totalMeasures
        : 0;

    const maxDeps = Math.max(...Object.values(measureToMeasure).map(d => d.length), 0);

    const statsHtml = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <h3>Measures with Dependencies</h3>
                <div class="value">${{totalMeasures}}</div>
            </div>
            <div class="kpi-card">
                <h3>Average Dependencies</h3>
                <div class="value">${{avgDeps.toFixed(1)}}</div>
            </div>
            <div class="kpi-card">
                <h3>Max Dependencies</h3>
                <div class="value">${{maxDeps}}</div>
            </div>
        </div>
    `;

    $('#dependency-stats').html(statsHtml);
}}

// Dependency Viewer Functions
let recentSelections = [];

function initializeDependencyViewer() {{
    // Populate measures selector list
    const measuresHtml = [];
    pbipData.model.tables.forEach(table => {{
        table.measures.forEach(measure => {{
            const measureKey = `${{table.name}}[${{measure.name}}]`;
            measuresHtml.push(`
                <div class="selector-item" data-object-key="${{measureKey}}" data-object-type="measure">
                    <div class="item-name">${{measure.name}}</div>
                    <div class="item-type">Measure in ${{table.name}}</div>
                </div>
            `);
        }});
    }});
    $('#measures-selector-list').html(measuresHtml.join(''));

    // Handle selector item click
    $(document).on('click', '.selector-item', function() {{
        $('.selector-item').removeClass('selected');
        $(this).addClass('selected');

        const objectKey = $(this).data('object-key');
        const objectType = $(this).data('object-type');

        showDependencyDetails(objectKey, objectType);
        addToRecentSelections(objectKey, objectType);
    }});

    // Handle dependency search
    $('#dependency-search').on('keyup', function() {{
        const searchTerm = $(this).val().toLowerCase();
        $('.selector-item').each(function() {{
            const text = $(this).text().toLowerCase();
            $(this).toggle(text.includes(searchTerm));
        }});
    }});
}}

function showDependencyDetails(objectKey, objectType) {{
    const dependencies = pbipData.dependencies;
    const report = pbipData.report;

    let detailsHtml = `<div class="dependency-details-card">`;
    detailsHtml += `<h3>${{objectKey}}</h3>`;
    detailsHtml += `<p class="text-muted">Type: ${{objectType}}</p>`;

    if (objectType === 'measure') {{
        // Show measure dependencies
        const dependsOn = dependencies.measure_to_measure[objectKey] || [];
        const usedBy = dependencies.measure_to_measure_reverse[objectKey] || [];
        const usedInColumns = dependencies.measure_to_column[objectKey] || [];

        // Find visuals using this measure
        const visualUsage = findMeasureInVisuals(objectKey, report);

        // Depends On section
        detailsHtml += `<div class="dependency-section">`;
        detailsHtml += `<h5>Depends On (${{dependsOn.length + usedInColumns.length}})</h5>`;
        if (dependsOn.length > 0 || usedInColumns.length > 0) {{
            detailsHtml += `<ul class="dependency-list">`;
            dependsOn.forEach(dep => {{
                detailsHtml += `<li><span class="usage-badge measure">Measure</span>${{dep}}</li>`;
            }});
            usedInColumns.forEach(col => {{
                detailsHtml += `<li><span class="usage-badge column">Column</span>${{col}}</li>`;
            }});
            detailsHtml += `</ul>`;
        }} else {{
            detailsHtml += `<p class="text-muted">This measure doesn't depend on other measures or columns.</p>`;
        }}
        detailsHtml += `</div>`;

        // Used By Measures section
        detailsHtml += `<div class="dependency-section">`;
        detailsHtml += `<h5>Used By Measures (${{usedBy.length}})</h5>`;
        if (usedBy.length > 0) {{
            detailsHtml += `<ul class="dependency-list">`;
            usedBy.forEach(user => {{
                detailsHtml += `<li><span class="usage-badge measure">Measure</span>${{user}}</li>`;
            }});
            detailsHtml += `</ul>`;
        }} else {{
            detailsHtml += `<p class="text-muted">No other measures use this measure.</p>`;
        }}
        detailsHtml += `</div>`;

        // Used In Visuals section
        detailsHtml += `<div class="dependency-section">`;
        detailsHtml += `<h5>Used In Visuals (${{visualUsage.length}})</h5>`;
        if (visualUsage.length > 0) {{
            detailsHtml += `<ul class="dependency-list">`;
            visualUsage.forEach(usage => {{
                detailsHtml += `<li>
                    <span class="usage-badge visual">Visual</span>
                    <strong>${{usage.pageName}}</strong> - ${{usage.visualType}}
                </li>`;
            }});
            detailsHtml += `</ul>`;
        }} else {{
            detailsHtml += `<p class="text-muted">This measure is not used in any visuals.</p>`;
        }}
        detailsHtml += `</div>`;
    }}

    detailsHtml += `</div>`;
    $('#dependency-details').html(detailsHtml);
}}

function findMeasureInVisuals(measureKey, report) {{
    if (!report || !report.pages) return [];

    const usage = [];
    const parts = measureKey.match(/(.+?)\[(.+?)\]/);
    if (!parts) return usage;

    const tableName = parts[1];
    const measureName = parts[2];

    report.pages.forEach(page => {{
        page.visuals.forEach(visual => {{
            const fields = visual.fields || {{}};
            const measures = fields.measures || [];

            measures.forEach(measure => {{
                if (measure.table === tableName && measure.measure === measureName) {{
                    usage.push({{
                        pageName: page.display_name || page.name,
                        visualType: visual.visual_type || 'Unknown',
                        visualId: visual.id
                    }});
                }}
            }});
        }});
    }});

    return usage;
}}

function addToRecentSelections(objectKey, objectType) {{
    // Remove if already in recent
    recentSelections = recentSelections.filter(item => item.key !== objectKey);

    // Add to front
    recentSelections.unshift({{ key: objectKey, type: objectType }});

    // Keep only last 5
    recentSelections = recentSelections.slice(0, 5);

    // Update UI
    const recentHtml = recentSelections.map(item => `
        <div class="selector-item" data-object-key="${{item.key}}" data-object-type="${{item.type}}">
            <div class="item-name">${{item.key}}</div>
        </div>
    `).join('');

    $('#recent-selections').html(recentHtml);
}}

// Initialize dependency viewer on page load
$(document).ready(function() {{
    initializeDependencyViewer();

    // Handle graph rendering on button click
    $('#show-graph-btn').on('click', function() {{
        const btn = $(this);
        const container = $('#graph-container');

        if (container.is(':visible')) {{
            container.slideUp();
            btn.text('Show Dependency Graph');
        }} else {{
            container.slideDown();
            btn.text('Hide Dependency Graph');

            // Render graph only once
            if ($('#dependency-graph svg').length === 0) {{
                renderDependencyGraph();
            }}
        }}
    }});
}});

// Search functionality
$('#measures-search').on('keyup', function() {{
    const searchTerm = $(this).val().toLowerCase();
    $('.measure-item').each(function() {{
        const text = $(this).text().toLowerCase();
        $(this).toggle(text.includes(searchTerm));
    }});
}});

</script>"""
