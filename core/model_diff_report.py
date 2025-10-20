"""
Model Diff Report Generator

Generates interactive HTML reports for Power BI model comparisons,
with side-by-side diff views, syntax highlighting, and filtering capabilities.
"""

import logging
import json
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ModelDiffReportGenerator:
    """
    Generates interactive HTML reports for model comparison results.

    Creates beautiful, searchable, filterable HTML reports with:
    - Summary dashboard with metrics
    - Side-by-side DAX comparison with syntax highlighting
    - Interactive filtering and searching
    - Export capabilities
    """

    def __init__(self, diff_result: Dict[str, Any]):
        """
        Initialize report generator.

        Args:
            diff_result: Diff result from ModelDiffer
        """
        self.diff = diff_result

    def generate_html_report(self, output_path: str) -> str:
        """
        Generate complete HTML report.

        Args:
            output_path: Path for output HTML file

        Returns:
            Path to generated HTML file
        """
        logger.info(f"Generating HTML diff report: {output_path}")

        html_content = self._build_html()

        # Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")
        return output_path

    def _build_html(self) -> str:
        """Build complete HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power BI Model Comparison - {self._escape(self.diff['summary']['model1_name'])} vs {self._escape(self.diff['summary']['model2_name'])}</title>
    {self._build_styles()}
    {self._build_scripts()}
</head>
<body>
    <div class="container">
        {self._build_header()}
        {self._build_summary_dashboard()}
        {self._build_filter_controls()}
        {self._build_measures_section()}
        {self._build_tables_section()}
        {self._build_relationships_section()}
        {self._build_roles_perspectives_section()}
        {self._build_footer()}
    </div>
</body>
</html>"""

    def _build_styles(self) -> str:
        """Build CSS styles."""
        return """
<style>
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: #f5f5f5;
        color: #333;
        line-height: 1.6;
    }

    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Header */
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .header h1 {
        font-size: 2.5em;
        margin-bottom: 10px;
    }

    .header .subtitle {
        font-size: 1.2em;
        opacity: 0.9;
    }

    .header .timestamp {
        font-size: 0.9em;
        opacity: 0.8;
        margin-top: 10px;
    }

    /* Summary Dashboard */
    .summary-dashboard {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }

    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    .metric-value {
        font-size: 3em;
        font-weight: bold;
        color: #667eea;
        display: block;
        margin-bottom: 5px;
    }

    .metric-label {
        font-size: 0.9em;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-value.added { color: #10b981; }
    .metric-value.removed { color: #ef4444; }
    .metric-value.modified { color: #f59e0b; }

    /* Filter Controls */
    .filter-controls {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 30px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .filter-controls h3 {
        margin-bottom: 15px;
        color: #333;
    }

    .filter-buttons {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    .filter-btn {
        padding: 8px 16px;
        border: 2px solid #667eea;
        background: white;
        color: #667eea;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9em;
        transition: all 0.2s;
    }

    .filter-btn:hover {
        background: #667eea;
        color: white;
    }

    .filter-btn.active {
        background: #667eea;
        color: white;
    }

    .expand-controls {
        display: flex;
        gap: 10px;
    }

    .expand-btn {
        padding: 8px 16px;
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.85em;
        font-weight: 500;
        transition: all 0.2s;
    }

    .expand-btn:hover {
        background: #e5e7eb;
        border-color: #9ca3af;
    }

    .table-badge {
        display: inline-block;
        background: #e0e7ff;
        color: #3730a3;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        margin-left: 8px;
        font-weight: normal;
    }

    .search-box {
        width: 100%;
        padding: 12px;
        border: 2px solid #e5e7eb;
        border-radius: 6px;
        font-size: 1em;
        margin-top: 15px;
    }

    .search-box:focus {
        outline: none;
        border-color: #667eea;
    }

    /* Section */
    .section {
        background: white;
        padding: 25px;
        border-radius: 8px;
        margin-bottom: 25px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 2px solid #e5e7eb;
    }

    .section-title {
        font-size: 1.8em;
        color: #333;
    }

    .section-count {
        background: #667eea;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9em;
    }

    /* Change Item */
    .change-item {
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        margin-bottom: 15px;
        overflow: hidden;
    }

    .change-item-header {
        background: #f9fafb;
        padding: 15px;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: background 0.2s;
    }

    .change-item-header:hover {
        background: #f3f4f6;
    }

    .change-type {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
        text-transform: uppercase;
        margin-right: 10px;
    }

    .change-type.added {
        background: #d1fae5;
        color: #065f46;
    }

    .change-type.removed {
        background: #fee2e2;
        color: #991b1b;
    }

    .change-type.modified {
        background: #fef3c7;
        color: #92400e;
    }

    .change-item-name {
        font-weight: 600;
        color: #333;
        font-size: 1.1em;
    }

    .expand-icon {
        font-size: 1.2em;
        color: #667eea;
        transition: transform 0.3s;
    }

    .change-item-header.expanded .expand-icon {
        transform: rotate(180deg);
    }

    .change-item-body {
        display: none;
        padding: 20px;
        background: white;
    }

    .change-item-body.visible {
        display: block;
    }

    /* Diff View */
    .diff-container {
        background: #1e1e1e;
        border-radius: 6px;
        overflow: hidden;
        margin: 15px 0;
    }

    .diff-header {
        background: #2d2d30;
        padding: 10px 15px;
        color: #ccc;
        font-size: 0.9em;
        font-weight: 600;
        border-bottom: 1px solid #3e3e42;
    }

    .diff-content {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0;
    }

    .diff-side {
        padding: 15px;
        overflow-x: auto;
    }

    .diff-side.before {
        border-right: 1px solid #3e3e42;
    }

    .diff-side-label {
        color: #858585;
        font-size: 0.85em;
        margin-bottom: 10px;
        font-weight: 600;
    }

    .code-block {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.9em;
        line-height: 1.5;
        color: #d4d4d4;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    .code-line {
        padding: 2px 0;
    }

    .code-line.added {
        background: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
    }

    .code-line.removed {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
    }

    /* Property Changes */
    .property-changes {
        margin: 15px 0;
    }

    .property-change {
        display: grid;
        grid-template-columns: 150px 1fr 1fr;
        gap: 15px;
        padding: 10px;
        background: #f9fafb;
        border-radius: 4px;
        margin-bottom: 8px;
        align-items: center;
    }

    .property-name {
        font-weight: 600;
        color: #667eea;
    }

    .property-value {
        font-family: 'Consolas', monospace;
        font-size: 0.9em;
        padding: 5px 10px;
        background: white;
        border-radius: 4px;
        border: 1px solid #e5e7eb;
    }

    .property-value.before {
        text-decoration: line-through;
        color: #dc2626;
    }

    .property-value.after {
        color: #059669;
    }

    /* Sub-changes */
    .sub-changes {
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
    }

    .sub-section-title {
        font-size: 1.2em;
        font-weight: 600;
        color: #333;
        margin-bottom: 15px;
    }

    .sub-change-list {
        margin-left: 20px;
    }

    .sub-change-item {
        padding: 10px;
        margin-bottom: 10px;
        border-left: 3px solid #667eea;
        background: #f9fafb;
        border-radius: 0 4px 4px 0;
    }

    /* Metadata Display */
    .metadata-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 15px;
        margin: 15px 0;
    }

    .metadata-item {
        background: #f9fafb;
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid #667eea;
    }

    .metadata-label {
        font-weight: 600;
        font-size: 0.85em;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }

    .metadata-value {
        font-size: 0.95em;
        color: #1f2937;
        word-wrap: break-word;
    }

    .metadata-value.empty {
        color: #9ca3af;
        font-style: italic;
    }

    .metadata-change {
        display: flex;
        gap: 10px;
        align-items: center;
        margin: 8px 0;
    }

    .metadata-before, .metadata-after {
        flex: 1;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.9em;
        font-family: 'Consolas', monospace;
    }

    .metadata-before {
        background: #fee2e2;
        color: #991b1b;
        text-decoration: line-through;
    }

    .metadata-after {
        background: #d1fae5;
        color: #065f46;
    }

    .metadata-arrow {
        font-size: 1.2em;
        color: #667eea;
        font-weight: bold;
    }

    /* Badges for metadata indicators */
    .metadata-badges {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin: 10px 0;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .badge-hidden {
        background: #fef3c7;
        color: #92400e;
    }

    .badge-key {
        background: #dbeafe;
        color: #1e40af;
    }

    .badge-calculated {
        background: #e0e7ff;
        color: #3730a3;
    }

    .badge-category {
        background: #f3e8ff;
        color: #6b21a8;
    }

    .badge-annotation {
        background: #d1fae5;
        color: #065f46;
    }

    /* Partition/M Expression Display */
    .m-expression-container {
        margin: 15px 0;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
    }

    .m-expression-header {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 10px 15px;
        font-size: 0.95em;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .m-expression-code {
        background: #f9fafb;
        padding: 15px;
        overflow-x: auto;
    }

    .m-code {
        margin: 0;
        padding: 0;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        color: #1f2937;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    /* Calculation Group/Items */
    .calc-group-container {
        margin: 20px 0;
        padding: 20px;
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 8px;
        border: 2px solid #f59e0b;
    }

    .calc-group-header {
        font-size: 1.1em;
        font-weight: 700;
        color: #92400e;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .calc-item-card {
        background: white;
        padding: 15px;
        margin: 10px 0;
        border-radius: 6px;
        border-left: 4px solid #f59e0b;
    }

    .calc-item-name {
        font-weight: 600;
        font-size: 1.05em;
        color: #92400e;
        margin-bottom: 10px;
    }

    /* Annotation Display */
    .annotation-list {
        margin: 15px 0;
        padding: 12px;
        background: #f0fdf4;
        border-radius: 6px;
        border-left: 3px solid #10b981;
    }

    .annotation-item {
        display: flex;
        justify-content: space-between;
        padding: 6px 0;
        border-bottom: 1px solid #d1fae5;
    }

    .annotation-item:last-child {
        border-bottom: none;
    }

    .annotation-name {
        font-weight: 600;
        color: #065f46;
        font-size: 0.9em;
    }

    .annotation-value {
        color: #047857;
        font-family: 'Consolas', monospace;
        font-size: 0.85em;
    }

    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 40px;
        color: #9ca3af;
    }

    .empty-state-icon {
        font-size: 3em;
        margin-bottom: 10px;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #9ca3af;
        font-size: 0.9em;
    }

    /* Utility Classes */
    .hidden {
        display: none !important;
    }

    .mb-10 { margin-bottom: 10px; }
    .mb-15 { margin-bottom: 15px; }
    .mb-20 { margin-bottom: 20px; }

    /* DAX Diff Styles */
    .dax-diff-container {
        margin: 20px 0;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
    }

    .dax-diff-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 20px;
        font-size: 1.1em;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .dax-icon {
        font-size: 1.3em;
    }

    .dax-diff-content {
        display: grid;
        grid-template-columns: 1fr 3px 1fr;
        gap: 0;
        background: #fafafa;
    }

    .dax-diff-side {
        padding: 15px;
        overflow: auto;
    }

    .dax-before {
        background: #fef2f2;
        border-right: 1px solid #fee2e2;
    }

    .dax-after {
        background: #f0fdf4;
        border-left: 1px solid #d1fae5;
    }

    .dax-diff-divider {
        background: linear-gradient(to bottom, #e5e7eb 0%, #9ca3af 50%, #e5e7eb 100%);
        width: 3px;
    }

    .dax-diff-label {
        font-weight: bold;
        font-size: 0.85em;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 12px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .dax-before .dax-diff-label {
        background: #fee2e2;
        color: #991b1b;
    }

    .dax-after .dax-diff-label {
        background: #d1fae5;
        color: #065f46;
    }

    .label-icon {
        font-size: 1.2em;
    }

    .dax-code-block {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 15px;
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
    }

    .dax-code {
        margin: 0;
        padding: 0;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        color: #1f2937;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    .dax-keyword {
        color: #0066cc;
        font-weight: bold;
    }

    .dax-string {
        color: #22863a;
    }

    .dax-number {
        color: #d73a49;
        font-weight: 500;
    }

    .dax-comment {
        color: #6a737d;
        font-style: italic;
    }

    .dax-empty {
        color: #9ca3af;
        font-style: italic;
    }

    /* Scrollbar styling for DAX blocks */
    .dax-code-block::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    .dax-code-block::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }

    .dax-code-block::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }

    .dax-code-block::-webkit-scrollbar-thumb:hover {
        background: #555;
    }

    /* Single DAX Display (for added/removed measures) */
    .dax-single-container {
        margin: 15px 0;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
    }

    .dax-single-added {
        border-color: #10b981;
        background: #f0fdf4;
    }

    .dax-single-removed {
        border-color: #ef4444;
        background: #fef2f2;
    }

    .dax-single-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 15px;
        font-size: 0.95em;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .dax-single-added .dax-single-header {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }

    .dax-single-removed .dax-single-header {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
</style>
"""

    def _build_scripts(self) -> str:
        """Build JavaScript for interactivity."""
        diff_json = json.dumps(self.diff)

        return f"""
<script>
    // Store diff data
    const diffData = {diff_json};

    // Initialize on load
    document.addEventListener('DOMContentLoaded', function() {{
        initializeFilters();
        initializeSearch();
        initializeExpandCollapse();
    }});

    // Filter functionality
    function initializeFilters() {{
        const filterButtons = document.querySelectorAll('.filter-btn');

        filterButtons.forEach(btn => {{
            btn.addEventListener('click', function() {{
                this.classList.toggle('active');
                applyFilters();
            }});
        }});
    }}

    function applyFilters() {{
        const activeFilters = Array.from(document.querySelectorAll('.filter-btn.active'))
            .map(btn => btn.dataset.filter);

        const changeItems = document.querySelectorAll('.change-item');

        changeItems.forEach(item => {{
            const changeType = item.dataset.changeType;

            if (activeFilters.length === 0 || activeFilters.includes(changeType)) {{
                item.classList.remove('hidden');
            }} else {{
                item.classList.add('hidden');
            }}
        }});

        updateCounts();
    }}

    // Search functionality
    function initializeSearch() {{
        const searchBox = document.querySelector('.search-box');

        if (searchBox) {{
            searchBox.addEventListener('input', function() {{
                const searchTerm = this.value.toLowerCase();
                const changeItems = document.querySelectorAll('.change-item');

                changeItems.forEach(item => {{
                    const text = item.textContent.toLowerCase();

                    if (text.includes(searchTerm)) {{
                        item.classList.remove('hidden');
                    }} else {{
                        item.classList.add('hidden');
                    }}
                }});

                updateCounts();
            }});
        }}
    }}

    // Expand/collapse functionality
    function initializeExpandCollapse() {{
        const headers = document.querySelectorAll('.change-item-header');

        headers.forEach(header => {{
            header.addEventListener('click', function() {{
                const body = this.nextElementSibling;

                this.classList.toggle('expanded');
                body.classList.toggle('visible');
            }});
        }});
    }}

    // Expand all items
    function expandAll() {{
        const headers = document.querySelectorAll('.change-item-header');
        const bodies = document.querySelectorAll('.change-item-body');

        headers.forEach(header => header.classList.add('expanded'));
        bodies.forEach(body => body.classList.add('visible'));
    }}

    // Collapse all items
    function collapseAll() {{
        const headers = document.querySelectorAll('.change-item-header');
        const bodies = document.querySelectorAll('.change-item-body');

        headers.forEach(header => header.classList.remove('expanded'));
        bodies.forEach(body => body.classList.remove('visible'));
    }}

    function updateCounts() {{
        const sections = document.querySelectorAll('.section');

        sections.forEach(section => {{
            const visibleItems = section.querySelectorAll('.change-item:not(.hidden)');
            const countBadge = section.querySelector('.section-count');

            if (countBadge) {{
                countBadge.textContent = visibleItems.length;
            }}
        }});
    }}

    // Export functionality
    function exportToJSON() {{
        const dataStr = JSON.stringify(diffData, null, 2);
        const dataBlob = new Blob([dataStr], {{ type: 'application/json' }});
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'model-diff-export.json';
        link.click();
    }}
</script>
"""

    def _build_header(self) -> str:
        """Build header section."""
        summary = self.diff['summary']

        return f"""
<div class="header">
    <h1>Power BI Model Comparison</h1>
    <div class="subtitle">
        {self._escape(summary['model1_name'])} → {self._escape(summary['model2_name'])}
    </div>
    <div class="timestamp">
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</div>
"""

    def _build_summary_dashboard(self) -> str:
        """Build summary metrics dashboard."""
        changes = self.diff['summary']['changes_by_category']

        total_changes = self.diff['summary']['total_changes']

        metrics = [
            ('Total Changes', total_changes, ''),
            ('Tables Added', changes.get('tables_added', 0), 'added'),
            ('Tables Removed', changes.get('tables_removed', 0), 'removed'),
            ('Tables Modified', changes.get('tables_modified', 0), 'modified'),
            ('Measures Added', changes.get('measures_added', 0), 'added'),
            ('Measures Removed', changes.get('measures_removed', 0), 'removed'),
            ('Measures Modified', changes.get('measures_modified', 0), 'modified'),
            ('Relationships Changed',
             changes.get('relationships_added', 0) +
             changes.get('relationships_removed', 0) +
             changes.get('relationships_modified', 0), 'modified')
        ]

        cards_html = ''.join([
            f"""
            <div class="metric-card">
                <span class="metric-value {css_class}">{value}</span>
                <span class="metric-label">{label}</span>
            </div>
            """
            for label, value, css_class in metrics
        ])

        return f"""
<div class="summary-dashboard">
    {cards_html}
</div>
"""

    def _build_filter_controls(self) -> str:
        """Build filter controls."""
        return """
<div class="filter-controls">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h3 style="margin: 0;">Filter Changes</h3>
        <div class="expand-controls">
            <button class="expand-btn" onclick="expandAll()" title="Expand all items">Expand All</button>
            <button class="expand-btn" onclick="collapseAll()" title="Collapse all items">Collapse All</button>
        </div>
    </div>
    <div class="filter-buttons">
        <button class="filter-btn active" data-filter="added">Added</button>
        <button class="filter-btn active" data-filter="removed">Removed</button>
        <button class="filter-btn active" data-filter="modified">Modified</button>
    </div>
    <input type="text" class="search-box" placeholder="Search tables, measures, columns...">
</div>
"""

    def _build_measures_section(self) -> str:
        """Build standalone measures comparison section."""
        measures_diff = self.diff.get('measures', {'modified': [], 'removed': [], 'added': []})

        total_changes = (
            len(measures_diff['modified']) +
            len(measures_diff['removed']) +
            len(measures_diff['added'])
        )

        if total_changes == 0:
            return self._build_empty_section('Measures', '📊')

        items_html = []

        # ORDER: Modified → Removed → Added

        # Modified measures
        for meas in measures_diff['modified']:
            items_html.append(self._build_measure_modified_item(meas))

        # Removed measures
        for meas in measures_diff['removed']:
            items_html.append(self._build_measure_removed_item(meas))

        # Added measures
        for meas in measures_diff['added']:
            items_html.append(self._build_measure_added_item(meas))

        return f"""
<div class="section" id="measures-section">
    <div class="section-header">
        <h2 class="section-title">📊 Measures</h2>
        <span class="section-count">{total_changes}</span>
    </div>
    {''.join(items_html)}
</div>
"""

    def _build_measure_modified_item(self, meas: Dict[str, Any]) -> str:
        """Build HTML for a modified measure."""
        meas_changes = meas.get('changes', {})
        table_name = meas.get('table', 'Unknown')

        # Build metadata change displays
        metadata_changes_html = []
        metadata_fields = ['description', 'is_hidden', 'data_category', 'display_folder', 'format_string']
        for field in metadata_fields:
            if field in meas_changes:
                metadata_changes_html.append(self._build_metadata_change_display(field, meas_changes[field]))

        # Annotation changes
        if 'annotations' in meas_changes:
            metadata_changes_html.append(self._build_annotation_changes_display(meas_changes['annotations']))

        # DAX expression diff
        dax_diff = ""
        if 'expression' in meas_changes:
            dax_diff = self._build_dax_diff(
                meas_changes['expression']['from'],
                meas_changes['expression']['to']
            )

        content_html = []
        if metadata_changes_html:
            content_html.append('<div class="metadata-grid">' + ''.join(metadata_changes_html) + '</div>')
        if dax_diff:
            content_html.append(dax_diff)
        if not content_html:
            content_html.append('<p>No significant changes detected</p>')

        return f"""
<div class="change-item" data-change-type="modified">
    <div class="change-item-header">
        <div>
            <span class="change-type modified">Modified</span>
            <strong>{self._escape(meas['name'])}</strong>
            <span class="table-badge">{self._escape(table_name)}</span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        {''.join(content_html)}
    </div>
</div>
"""

    def _build_measure_removed_item(self, meas: Dict[str, Any]) -> str:
        """Build HTML for a removed measure."""
        table_name = meas.get('table', 'Unknown')
        dax_display = self._build_single_dax_display(meas.get('expression'), 'removed')

        return f"""
<div class="change-item" data-change-type="removed">
    <div class="change-item-header">
        <div>
            <span class="change-type removed">Removed</span>
            <strong>{self._escape(meas['name'])}</strong>
            <span class="table-badge">{self._escape(table_name)}</span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        {dax_display}
    </div>
</div>
"""

    def _build_measure_added_item(self, meas: Dict[str, Any]) -> str:
        """Build HTML for an added measure."""
        table_name = meas.get('table', 'Unknown')
        dax_display = self._build_single_dax_display(meas.get('expression'), 'added')

        return f"""
<div class="change-item" data-change-type="added">
    <div class="change-item-header">
        <div>
            <span class="change-type added">Added</span>
            <strong>{self._escape(meas['name'])}</strong>
            <span class="table-badge">{self._escape(table_name)}</span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        {dax_display}
    </div>
</div>
"""

    def _build_tables_section(self) -> str:
        """Build tables comparison section."""
        tables_diff = self.diff['tables']

        total_changes = (
            len(tables_diff['added']) +
            len(tables_diff['removed']) +
            len(tables_diff['modified'])
        )

        if total_changes == 0:
            return self._build_empty_section('Tables', '📋')

        items_html = []

        # ORDER: Modified → Removed → Added

        # Modified tables
        for table in tables_diff['modified']:
            items_html.append(self._build_table_modified_item(table))

        # Removed tables
        for table in tables_diff['removed']:
            items_html.append(self._build_table_removed_item(table))

        # Added tables
        for table in tables_diff['added']:
            items_html.append(self._build_table_added_item(table))

        return f"""
<div class="section" id="tables-section">
    <div class="section-header">
        <h2 class="section-title">Tables</h2>
        <span class="section-count">{total_changes}</span>
    </div>
    {''.join(items_html)}
</div>
"""

    def _build_table_added_item(self, table: Dict[str, Any]) -> str:
        """Build HTML for an added table."""
        return f"""
<div class="change-item" data-change-type="added">
    <div class="change-item-header">
        <div>
            <span class="change-type added">Added</span>
            <span class="change-item-name">{self._escape(table['name'])}</span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        <p><strong>Columns:</strong> {table.get('columns_count', 0)}</p>
        <p><strong>Measures:</strong> {table.get('measures_count', 0)}</p>
        {f'<p><strong>Type:</strong> Calculation Group</p>' if table.get('is_calculation_group') else ''}
    </div>
</div>
"""

    def _build_table_removed_item(self, table: Dict[str, Any]) -> str:
        """Build HTML for a removed table."""
        return f"""
<div class="change-item" data-change-type="removed">
    <div class="change-item-header">
        <div>
            <span class="change-type removed">Removed</span>
            <span class="change-item-name">{self._escape(table['name'])}</span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        <p><strong>Columns:</strong> {table.get('columns_count', 0)}</p>
        <p><strong>Measures:</strong> {table.get('measures_count', 0)}</p>
    </div>
</div>
"""

    def _build_table_modified_item(self, table: Dict[str, Any]) -> str:
        """Build HTML for a modified table."""
        changes = table['changes']

        content_sections = []

        # Table-level metadata changes
        table_metadata_html = []

        # Description changes
        if 'description_changed' in changes:
            table_metadata_html.append(
                self._build_metadata_change_display('description', changes['description_changed'])
            )

        # Hidden status changes
        if 'is_hidden_changed' in changes:
            table_metadata_html.append(
                self._build_metadata_change_display('hidden', changes['is_hidden_changed'])
            )

        # Calculation group status changes
        if 'calculation_group_changed' in changes:
            table_metadata_html.append(
                self._build_metadata_change_display('calculation_group', changes['calculation_group_changed'])
            )

        # Annotation changes
        if 'annotations' in changes:
            table_metadata_html.append(self._build_annotation_changes_display(changes['annotations']))

        # Show table-level changes if any
        if table_metadata_html:
            content_sections.append(f"""
                <div style="margin-bottom: 20px; padding: 15px; background: #fef3c7; border-radius: 6px; border-left: 4px solid #f59e0b;">
                    <h5 style="color: #92400e; margin-bottom: 10px;">📋 Table Properties Changed</h5>
                    {''.join(table_metadata_html)}
                </div>
            """)

        # Calculation items changes (for calculation groups)
        if 'calculation_items' in changes:
            calc_items_diff = changes['calculation_items']
            calc_items_html = []

            # Added calculation items
            for item_name in calc_items_diff.get('added', []):
                calc_items_html.append(f'<li><span class="change-type added">Added</span> {self._escape(item_name)}</li>')

            # Removed calculation items
            for item_name in calc_items_diff.get('removed', []):
                calc_items_html.append(f'<li><span class="change-type removed">Removed</span> {self._escape(item_name)}</li>')

            # Modified calculation items
            for item in calc_items_diff.get('modified', []):
                item_name = item.get('name', 'Unknown')
                item_changes = item.get('changes', {})
                change_types = []
                if 'expression' in item_changes:
                    change_types.append('Expression')
                if 'format_string_definition' in item_changes:
                    change_types.append('Format String')
                if 'ordinal' in item_changes:
                    change_types.append('Ordinal')

                calc_items_html.append(
                    f'<li><span class="change-type modified">Modified</span> {self._escape(item_name)}: {", ".join(change_types)}</li>'
                )

            if calc_items_html:
                content_sections.append(f"""
                    <div class="calc-group-container">
                        <div class="calc-group-header">
                            🧮 Calculation Items Changed ({len(calc_items_html)})
                        </div>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            {''.join(calc_items_html)}
                        </ul>
                    </div>
                """)

        # Column changes
        if changes['columns']['added'] or changes['columns']['removed'] or changes['columns']['modified']:
            content_sections.append(self._build_columns_changes(changes['columns']))

        # Measure changes
        if changes['measures']['added'] or changes['measures']['removed'] or changes['measures']['modified']:
            content_sections.append(self._build_measures_changes(changes['measures']))

        # Hierarchy changes
        if changes.get('hierarchies', {}).get('added') or changes.get('hierarchies', {}).get('removed') or changes.get('hierarchies', {}).get('modified'):
            hierarchies_html = []
            hier_diff = changes['hierarchies']

            for hier_name in hier_diff.get('added', []):
                hierarchies_html.append(f'<li><span class="change-type added">Added</span> {self._escape(hier_name)}</li>')

            for hier_name in hier_diff.get('removed', []):
                hierarchies_html.append(f'<li><span class="change-type removed">Removed</span> {self._escape(hier_name)}</li>')

            for hier in hier_diff.get('modified', []):
                hier_name = hier.get('name', 'Unknown')
                hierarchies_html.append(f'<li><span class="change-type modified">Modified</span> {self._escape(hier_name)}</li>')

            if hierarchies_html:
                content_sections.append(f"""
                    <div class="sub-changes">
                        <h4 class="sub-section-title">Hierarchies ({len(hierarchies_html)} changes)</h4>
                        <ul style="margin-left: 20px;">
                            {''.join(hierarchies_html)}
                        </ul>
                    </div>
                """)

        # Partition changes (M expressions)
        if changes.get('partitions', {}).get('added') or changes.get('partitions', {}).get('removed') or changes.get('partitions', {}).get('modified'):
            partitions_html = []
            part_diff = changes['partitions']

            for part_name in part_diff.get('added', []):
                partitions_html.append(f'<li><span class="change-type added">Added</span> {self._escape(part_name)}</li>')

            for part_name in part_diff.get('removed', []):
                partitions_html.append(f'<li><span class="change-type removed">Removed</span> {self._escape(part_name)}</li>')

            for part in part_diff.get('modified', []):
                part_name = part.get('name', 'Unknown')
                part_changes = part.get('changes', {})

                if 'source' in part_changes:
                    m_diff_html = self._build_m_expression_display(
                        part_changes['source'].get('to', ''),
                        f"Partition: {part_name} - Modified M Expression"
                    )
                    partitions_html.append(f'<li><span class="change-type modified">Modified</span> {self._escape(part_name)}: M expression changed{m_diff_html}</li>')
                else:
                    partitions_html.append(f'<li><span class="change-type modified">Modified</span> {self._escape(part_name)}</li>')

            if partitions_html:
                content_sections.append(f"""
                    <div class="sub-changes">
                        <h4 class="sub-section-title">💚 Partitions/M Expressions ({len(partitions_html)} changes)</h4>
                        <ul style="margin-left: 20px; list-style: none;">
                            {''.join(partitions_html)}
                        </ul>
                    </div>
                """)

        return f"""
<div class="change-item" data-change-type="modified">
    <div class="change-item-header">
        <div>
            <span class="change-type modified">Modified</span>
            <span class="change-item-name">{self._escape(table['name'])}</span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        {''.join(content_sections) if content_sections else '<p>No changes detected</p>'}
    </div>
</div>
"""

    def _build_columns_changes(self, columns_diff: Dict[str, Any]) -> str:
        """Build HTML for column changes."""
        items = []

        # Added columns
        for col in columns_diff['added']:
            badges = self._build_metadata_badges(col, 'column')
            items.append(f"""
                <div class="sub-change-item">
                    <span class="change-type added">Added</span>
                    <strong>{self._escape(col['name'])}</strong>
                    {f" ({col['data_type']})" if col.get('data_type') else ''}
                    {badges}
                    {f'<p style="margin-top: 8px; font-size: 0.9em; color: #6b7280;"><strong>Description:</strong> {self._escape(col.get("description"))}</p>' if col.get('description') else ''}
                </div>
            """)

        # Removed columns
        for col in columns_diff['removed']:
            badges = self._build_metadata_badges(col, 'column')
            items.append(f"""
                <div class="sub-change-item">
                    <span class="change-type removed">Removed</span>
                    <strong>{self._escape(col['name'])}</strong>
                    {f" ({col['data_type']})" if col.get('data_type') else ''}
                    {badges}
                </div>
            """)

        # Modified columns
        for col in columns_diff['modified']:
            col_changes = col['changes']
            metadata_changes_html = []

            # Build metadata change displays
            metadata_fields = ['description', 'display_folder', 'format_string', 'data_category',
                             'summarize_by', 'sort_by_column']
            for field in metadata_fields:
                if field in col_changes:
                    metadata_changes_html.append(self._build_metadata_change_display(field, col_changes[field]))

            # Annotation changes
            if 'annotations' in col_changes:
                metadata_changes_html.append(self._build_annotation_changes_display(col_changes['annotations']))

            # Expression changes
            expression_html = ""
            if 'expression' in col_changes:
                expression_html = self._build_dax_diff(
                    col_changes['expression'].get('from', ''),
                    col_changes['expression'].get('to', '')
                )

            items.append(f"""
                <div class="sub-change-item">
                    <span class="change-type modified">Modified</span>
                    <strong>{self._escape(col['name'])}</strong>
                    {''.join(metadata_changes_html)}
                    {expression_html}
                </div>
            """)

        if not items:
            return ""

        return f"""
<div class="sub-changes">
    <h4 class="sub-section-title">Columns ({len(items)} changes)</h4>
    <div class="sub-change-list">
        {''.join(items)}
    </div>
</div>
"""

    def _build_measures_changes(self, measures_diff: Dict[str, Any]) -> str:
        """Build HTML for measure changes."""
        items = []

        # Added measures
        for meas in measures_diff['added']:
            badges = self._build_metadata_badges(meas, 'measure')
            items.append(f"""
                <div class="sub-change-item">
                    <span class="change-type added">Added</span>
                    <strong>{self._escape(meas['name'])}</strong>
                    {badges}
                    {f'<p style="margin-top: 8px; font-size: 0.9em; color: #6b7280;"><strong>Description:</strong> {self._escape(meas.get("description"))}</p>' if meas.get('description') else ''}
                    {self._build_single_dax_display(meas.get('expression'), 'added')}
                </div>
            """)

        # Removed measures
        for meas in measures_diff['removed']:
            badges = self._build_metadata_badges(meas, 'measure')
            items.append(f"""
                <div class="sub-change-item">
                    <span class="change-type removed">Removed</span>
                    <strong>{self._escape(meas['name'])}</strong>
                    {badges}
                    {self._build_single_dax_display(meas.get('expression'), 'removed')}
                </div>
            """)

        # Modified measures
        for meas in measures_diff['modified']:
            meas_changes = meas['changes']
            metadata_changes_html = []

            # Build metadata change displays
            metadata_fields = ['description', 'is_hidden', 'data_category', 'display_folder', 'format_string']
            for field in metadata_fields:
                if field in meas_changes:
                    metadata_changes_html.append(self._build_metadata_change_display(field, meas_changes[field]))

            # Annotation changes
            if 'annotations' in meas_changes:
                metadata_changes_html.append(self._build_annotation_changes_display(meas_changes['annotations']))

            # Expression diff
            expression_html = ""
            if 'expression' in meas_changes:
                expression_html = self._build_dax_diff(
                    meas_changes['expression']['from'],
                    meas_changes['expression']['to']
                )

            items.append(f"""
                <div class="sub-change-item">
                    <span class="change-type modified">Modified</span>
                    <strong>{self._escape(meas['name'])}</strong>
                    {''.join(metadata_changes_html)}
                    {expression_html}
                </div>
            """)

        if not items:
            return ""

        return f"""
<div class="sub-changes">
    <h4 class="sub-section-title">Measures ({len(items)} changes)</h4>
    <div class="sub-change-list">
        {''.join(items)}
    </div>
</div>
"""

    def _build_single_dax_display(self, expression: Optional[str], change_type: str) -> str:
        """Build a beautiful single DAX code display for added/removed measures."""
        if not expression:
            return '<div class="dax-empty" style="margin-top: 10px;">No expression</div>'

        highlighted = self._highlight_dax(expression)

        bg_class = 'dax-single-added' if change_type == 'added' else 'dax-single-removed'
        icon = '✨' if change_type == 'added' else '📝'

        return f"""
<div class="dax-single-container {bg_class}">
    <div class="dax-single-header">
        <span class="dax-icon">{icon}</span>
        <strong>DAX Expression</strong>
    </div>
    <div class="dax-code-block">
        <pre class="dax-code">{highlighted}</pre>
    </div>
</div>
"""

    def _build_measure_expression_preview(self, expression: Optional[str]) -> str:
        """Build a preview snippet of measure expression."""
        if not expression:
            return ""

        preview = expression[:100].replace('\n', ' ')
        if len(expression) > 100:
            preview += "..."

        return f'<div class="code-block" style="margin-top: 5px;">{self._escape(preview)}</div>'

    def _build_dax_diff(self, expr_before: str, expr_after: str) -> str:
        """Build side-by-side DAX diff with syntax highlighting."""
        before_highlighted = self._highlight_dax(expr_before or '')
        after_highlighted = self._highlight_dax(expr_after or '')

        return f"""
<div class="dax-diff-container">
    <div class="dax-diff-header">
        <span class="dax-icon">⚡</span>
        <strong>DAX Expression Comparison</strong>
    </div>
    <div class="dax-diff-content">
        <div class="dax-diff-side dax-before">
            <div class="dax-diff-label">
                <span class="label-icon">📝</span> BEFORE
            </div>
            <div class="dax-code-block">
                <pre class="dax-code">{before_highlighted}</pre>
            </div>
        </div>
        <div class="dax-diff-divider"></div>
        <div class="dax-diff-side dax-after">
            <div class="dax-diff-label">
                <span class="label-icon">✨</span> AFTER
            </div>
            <div class="dax-code-block">
                <pre class="dax-code">{after_highlighted}</pre>
            </div>
        </div>
    </div>
</div>
"""

    def _highlight_dax(self, dax_code: str) -> str:
        """Apply simple DAX syntax highlighting."""
        if not dax_code:
            return '<span class="dax-empty">No expression</span>'

        # Escape HTML first
        code = self._escape(dax_code)

        # DAX keywords
        keywords = [
            'CALCULATE', 'FILTER', 'ALL', 'ALLSELECTED', 'SUMX', 'AVERAGEX', 'MAXX', 'MINX',
            'COUNTROWS', 'DISTINCT', 'VALUES', 'RELATED', 'RELATEDTABLE', 'USERELATIONSHIP',
            'VAR', 'RETURN', 'IF', 'SWITCH', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE',
            'SUM', 'AVERAGE', 'COUNT', 'MIN', 'MAX', 'DIVIDE', 'FORMAT', 'SELECTEDVALUE',
            'HASONEVALUE', 'ISBLANK', 'BLANK', 'CONCATENATE', 'CONCATENATEX',
            'ADDCOLUMNS', 'SELECTCOLUMNS', 'SUMMARIZE', 'GROUPBY', 'RANKX', 'TOPN'
        ]

        # Highlight keywords
        for keyword in keywords:
            code = code.replace(keyword, f'<span class="dax-keyword">{keyword}</span>')

        # Highlight strings (simple regex pattern)
        import re
        # Use lambda functions to avoid backreference interpretation issues
        code = re.sub(r'&quot;([^&quot;]*)&quot;', lambda m: f'<span class="dax-string">"{m.group(1)}"</span>', code)

        # Highlight numbers
        code = re.sub(r'\b(\d+(?:\.\d+)?)\b', lambda m: f'<span class="dax-number">{m.group(1)}</span>', code)

        # Highlight comments
        code = re.sub(r'(//.*?)(\n|$)', lambda m: f'<span class="dax-comment">{m.group(1)}</span>{m.group(2)}', code)
        code = re.sub(r'(/\*.*?\*/)', lambda m: f'<span class="dax-comment">{m.group(1)}</span>', code, flags=re.DOTALL)

        return code

    def _build_relationships_section(self) -> str:
        """Build relationships comparison section."""
        rels_diff = self.diff['relationships']

        total_changes = (
            len(rels_diff['added']) +
            len(rels_diff['removed']) +
            len(rels_diff['modified'])
        )

        if total_changes == 0:
            return self._build_empty_section('Relationships', '🔗')

        items_html = []

        # Added relationships
        for rel in rels_diff['added']:
            items_html.append(self._build_relationship_item(rel, 'added'))

        # Removed relationships
        for rel in rels_diff['removed']:
            items_html.append(self._build_relationship_item(rel, 'removed'))

        # Modified relationships
        for rel in rels_diff['modified']:
            items_html.append(self._build_relationship_modified_item(rel))

        return f"""
<div class="section" id="relationships-section">
    <div class="section-header">
        <h2 class="section-title">Relationships</h2>
        <span class="section-count">{total_changes}</span>
    </div>
    {''.join(items_html)}
</div>
"""

    def _build_relationship_item(self, rel: Dict[str, Any], change_type: str) -> str:
        """Build HTML for a relationship."""
        return f"""
<div class="change-item" data-change-type="{change_type}">
    <div class="change-item-header">
        <div>
            <span class="change-type {change_type}">{change_type.capitalize()}</span>
            <span class="change-item-name">
                {self._escape(rel.get('from_column', ''))} ({rel.get('from_cardinality', '')}) →
                {self._escape(rel.get('to_column', ''))} ({rel.get('to_cardinality', '')})
            </span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        <p><strong>Cross-filtering:</strong> {rel.get('cross_filtering_behavior', 'N/A')}</p>
        <p><strong>Active:</strong> {rel.get('is_active', True)}</p>
    </div>
</div>
"""

    def _build_relationship_modified_item(self, rel: Dict[str, Any]) -> str:
        """Build HTML for a modified relationship."""
        changes_html = []

        for key, change in rel['changes'].items():
            if key == 'annotations':
                # Handle annotations specially
                changes_html.append(self._build_annotation_changes_display(change))
            else:
                # Regular property changes
                from_val = change.get('from')
                to_val = change.get('to')

                # Format the display name
                display_name = key.replace('_', ' ').title()

                # Special formatting for security and integrity settings
                if key == 'security_filtering_behavior':
                    display_name = '🔒 Security Filtering'
                elif key == 'cross_filtering_behavior':
                    display_name = '🔄 Cross Filtering'
                elif key == 'rely_on_referential_integrity':
                    display_name = '✓ Referential Integrity'
                    from_val = '✓ Yes' if from_val else '✗ No'
                    to_val = '✓ Yes' if to_val else '✗ No'

                changes_html.append(f"""
                    <div class="property-change">
                        <div class="property-name">{display_name}</div>
                        <div class="property-value before">{self._escape(str(from_val))}</div>
                        <div class="property-value after">{self._escape(str(to_val))}</div>
                    </div>
                """)

        return f"""
<div class="change-item" data-change-type="modified">
    <div class="change-item-header">
        <div>
            <span class="change-type modified">Modified</span>
            <span class="change-item-name">
                {self._escape(rel.get('from_column', ''))} → {self._escape(rel.get('to_column', ''))}
            </span>
        </div>
        <span class="expand-icon">▼</span>
    </div>
    <div class="change-item-body">
        <div class="property-changes">
            {''.join(changes_html)}
        </div>
    </div>
</div>
"""

    def _build_roles_perspectives_section(self) -> str:
        """Build roles and perspectives section."""
        roles_diff = self.diff['roles']
        persp_diff = self.diff['perspectives']

        roles_changes = len(roles_diff['added']) + len(roles_diff['removed'])
        persp_changes = len(persp_diff['added']) + len(persp_diff['removed'])

        if roles_changes == 0 and persp_changes == 0:
            return ""

        items_html = []

        # Roles
        if roles_changes > 0:
            for role in roles_diff['added']:
                items_html.append(f'<li><span class="change-type added">Added</span> Role: {self._escape(role)}</li>')
            for role in roles_diff['removed']:
                items_html.append(f'<li><span class="change-type removed">Removed</span> Role: {self._escape(role)}</li>')

        # Perspectives
        if persp_changes > 0:
            for persp in persp_diff['added']:
                items_html.append(f'<li><span class="change-type added">Added</span> Perspective: {self._escape(persp)}</li>')
            for persp in persp_diff['removed']:
                items_html.append(f'<li><span class="change-type removed">Removed</span> Perspective: {self._escape(persp)}</li>')

        return f"""
<div class="section">
    <div class="section-header">
        <h2 class="section-title">Roles & Perspectives</h2>
        <span class="section-count">{roles_changes + persp_changes}</span>
    </div>
    <ul class="sub-change-list">
        {''.join(items_html)}
    </ul>
</div>
"""

    def _build_empty_section(self, title: str, icon: str) -> str:
        """Build empty state section."""
        return f"""
<div class="section">
    <div class="section-header">
        <h2 class="section-title">{title}</h2>
        <span class="section-count">0</span>
    </div>
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <p>No changes detected</p>
    </div>
</div>
"""

    def _build_footer(self) -> str:
        """Build footer."""
        return """
<div class="footer">
    <p>Generated by MCP-PowerBi-Finvision Model Comparison Tool</p>
    <p>Powered by TMDL (Tabular Model Definition Language)</p>
</div>
"""

    def _escape(self, text: str) -> str:
        """Escape HTML special characters."""
        if text is None:
            return ""
        return html.escape(str(text))

    def _build_metadata_badges(self, item: Dict[str, Any], item_type: str = 'column') -> str:
        """Build metadata badges for an item (column, measure, etc.)."""
        badges = []

        if item.get('is_hidden'):
            badges.append('<span class="badge badge-hidden">🔒 Hidden</span>')

        if item.get('is_key'):
            badges.append('<span class="badge badge-key">🔑 Key</span>')

        if item.get('is_calculated'):
            badges.append('<span class="badge badge-calculated">📐 Calculated</span>')

        if item.get('data_category'):
            badges.append(f'<span class="badge badge-category">📂 {self._escape(item["data_category"])}</span>')

        if item.get('annotations'):
            badges.append(f'<span class="badge badge-annotation">📝 {len(item["annotations"])} Annotations</span>')

        if not badges:
            return ""

        return f'<div class="metadata-badges">{" ".join(badges)}</div>'

    def _build_metadata_change_display(self, field_name: str, change: Dict[str, Any]) -> str:
        """Build a visual display for a metadata field change."""
        from_val = change.get('from')
        to_val = change.get('to')

        # Format values for display
        from_display = self._escape(str(from_val)) if from_val not in (None, '') else '<em>empty</em>'
        to_display = self._escape(str(to_val)) if to_val not in (None, '') else '<em>empty</em>'

        return f"""
        <div class="metadata-change">
            <div class="metadata-label">{self._escape(field_name.replace('_', ' ').title())}</div>
            <div class="metadata-before">{from_display}</div>
            <div class="metadata-arrow">→</div>
            <div class="metadata-after">{to_display}</div>
        </div>
        """

    def _build_annotation_display(self, annotations: List[Dict[str, Any]]) -> str:
        """Build annotation display."""
        if not annotations:
            return ""

        items_html = []
        for annot in annotations:
            name = self._escape(annot.get('name', ''))
            value = self._escape(annot.get('value', ''))
            items_html.append(f"""
                <div class="annotation-item">
                    <span class="annotation-name">{name}</span>
                    <span class="annotation-value">{value}</span>
                </div>
            """)

        return f"""
        <div class="annotation-list">
            <div style="font-weight: 600; margin-bottom: 8px; color: #065f46;">
                📝 Annotations ({len(annotations)})
            </div>
            {''.join(items_html)}
        </div>
        """

    def _build_annotation_changes_display(self, annot_changes: Dict[str, Any]) -> str:
        """Build display for annotation changes."""
        if not annot_changes:
            return ""

        changes_html = []
        for annot_name, change in annot_changes.items():
            from_val = change.get('from')
            to_val = change.get('to')

            if from_val is None:
                # Annotation added
                changes_html.append(f"""
                    <div class="metadata-change">
                        <div class="metadata-label">{self._escape(annot_name)}</div>
                        <div class="metadata-before"><em>none</em></div>
                        <div class="metadata-arrow">→</div>
                        <div class="metadata-after">{self._escape(str(to_val))}</div>
                    </div>
                """)
            elif to_val is None:
                # Annotation removed
                changes_html.append(f"""
                    <div class="metadata-change">
                        <div class="metadata-label">{self._escape(annot_name)}</div>
                        <div class="metadata-before">{self._escape(str(from_val))}</div>
                        <div class="metadata-arrow">→</div>
                        <div class="metadata-after"><em>removed</em></div>
                    </div>
                """)
            else:
                # Annotation modified
                changes_html.append(f"""
                    <div class="metadata-change">
                        <div class="metadata-label">{self._escape(annot_name)}</div>
                        <div class="metadata-before">{self._escape(str(from_val))}</div>
                        <div class="metadata-arrow">→</div>
                        <div class="metadata-after">{self._escape(str(to_val))}</div>
                    </div>
                """)

        return f"""
        <div style="margin: 15px 0;">
            <h5 style="color: #065f46; margin-bottom: 10px;">📝 Annotation Changes</h5>
            {''.join(changes_html)}
        </div>
        """

    def _build_m_expression_display(self, m_code: str, title: str = "Power Query (M) Expression") -> str:
        """Build M expression display."""
        if not m_code:
            return ""

        return f"""
        <div class="m-expression-container">
            <div class="m-expression-header">
                <span>💚</span>
                <strong>{self._escape(title)}</strong>
            </div>
            <div class="m-expression-code">
                <pre class="m-code">{self._escape(m_code)}</pre>
            </div>
        </div>
        """

    def _build_calculation_group_display(self, calc_items: List[Dict[str, Any]]) -> str:
        """Build calculation group items display."""
        if not calc_items:
            return ""

        items_html = []
        for item in calc_items:
            expr_display = self._build_single_dax_display(item.get('expression'), 'added')

            items_html.append(f"""
                <div class="calc-item-card">
                    <div class="calc-item-name">🧮 {self._escape(item.get('name', 'Unknown'))}</div>
                    {expr_display}
                    {f'<p style="margin-top: 10px;"><strong>Ordinal:</strong> {item.get("ordinal")}</p>' if item.get('ordinal') is not None else ''}
                    {f'<p><strong>Description:</strong> {self._escape(item.get("description"))}</p>' if item.get('description') else ''}
                </div>
            """)

        return f"""
        <div class="calc-group-container">
            <div class="calc-group-header">
                🧮 Calculation Group Items ({len(calc_items)})
            </div>
            {''.join(items_html)}
        </div>
        """


def generate_diff_report(diff_result: Dict[str, Any], output_path: str) -> str:
    """
    Convenience function to generate diff report.

    Args:
        diff_result: Diff result from ModelDiffer
        output_path: Output path for HTML report

    Returns:
        Path to generated report
    """
    generator = ModelDiffReportGenerator(diff_result)
    return generator.generate_html_report(output_path)
