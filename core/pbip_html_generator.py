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
            enhanced_results: Optional enhanced analysis results (lineage, quality metrics, etc.)

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

    <!-- Vue 3, D3.js, and Dagre for graph layouts -->
    <script src="https://cdn.jsdelivr.net/npm/vue@3.4.21/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
"""

    def _get_styles(self) -> str:
        """Get all CSS styles."""
        return f"""    <style>
        :root {{
            --primary: #5B7FFF;
            --primary-dark: #4A6BEE;
            --primary-light: #7D9AFF;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --bg-dark: #1e293b;
            --text-dark: #0f172a;
            --bg-light: #F5F7FF;
            --accent: #FF6B9D;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #F5F7FF 0%, #E8ECFF 100%);
        }}

        .dark-mode {{
            background: #0f172a;
            color: #e2e8f0;
        }}

        .dark-mode .bg-white {{
            background: #1e293b !important;
        }}

        .dark-mode .text-gray-900 {{
            color: #f1f5f9 !important;
        }}

        .dark-mode .text-gray-600,
        .dark-mode .text-gray-500 {{
            color: #cbd5e1 !important;
        }}

        .dark-mode .border-gray-200,
        .dark-mode .border-gray-300 {{
            border-color: #475569 !important;
        }}

        .dark-mode .bg-gray-50 {{
            background: #334155 !important;
        }}

        .dark-mode .bg-gray-100 {{
            background: #475569 !important;
        }}

        .list-item {{
            transition: all 0.15s ease;
        }}

        .list-item:hover {{
            background-color: #E8ECFF;
            transform: translateX(4px);
        }}

        .list-item.selected {{
            background: linear-gradient(90deg, #E8ECFF 0%, #D4DBFF 100%);
            border-left: 4px solid var(--primary);
            box-shadow: 0 2px 8px rgba(91, 127, 255, 0.15);
        }}

        .dark-mode .list-item:hover {{
            background-color: #334155 !important;
        }}

        .dark-mode .list-item.selected {{
            background-color: #1e40af !important;
        }}

        /* Grouped list items */
        .list-group-header {{
            background: linear-gradient(90deg, #5B7FFF 0%, #7D9AFF 100%);
            color: white;
            padding: 0.75rem 1rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 0.375rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s ease;
        }}

        .list-group-header:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(91, 127, 255, 0.3);
        }}

        .list-group-header .expand-icon {{
            transition: transform 0.2s ease;
        }}

        .list-group-header.collapsed .expand-icon {{
            transform: rotate(-90deg);
        }}

        .list-group-items {{
            margin-left: 1rem;
            border-left: 2px solid #E8ECFF;
            padding-left: 0.5rem;
        }}

        .dark-mode .list-group-items {{
            border-left-color: #475569;
        }}

        /* Visual type icons */
        .visual-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2rem;
            height: 2rem;
            border-radius: 0.375rem;
            font-size: 1.25rem;
            margin-right: 0.5rem;
        }}

        .visual-icon.slicer {{ background: #E8ECFF; }}
        .visual-icon.table {{ background: #D1FAE5; }}
        .visual-icon.card {{ background: #FEF3C7; }}
        .visual-icon.chart {{ background: #FFE4E6; }}
        .visual-icon.map {{ background: #E0E7FF; }}
        .visual-icon.matrix {{ background: #FCE7F3; }}

        /* Folder structure */
        .folder-item {{
            margin-bottom: 0.75rem;
        }}

        .folder-header {{
            background: #F1F5F9;
            padding: 0.5rem 0.75rem;
            border-radius: 0.375rem;
            font-weight: 600;
            color: #475569;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.15s ease;
        }}

        .folder-header:hover {{
            background: #E2E8F0;
        }}

        .dark-mode .folder-header {{
            background: #334155;
            color: #CBD5E1;
        }}

        .dark-mode .folder-header:hover {{
            background: #475569;
        }}

        .folder-content {{
            margin-left: 1rem;
            margin-top: 0.5rem;
            padding-left: 0.75rem;
            border-left: 2px solid #E2E8F0;
        }}

        .dark-mode .folder-content {{
            border-left-color: #475569;
        }}

        /* DAX Syntax Highlighting */
        .dax-keyword {{ color: #0066CC; font-weight: bold; }}
        .dax-function {{ color: #7C3AED; font-weight: 600; }}
        .dax-string {{ color: #059669; }}
        .dax-number {{ color: #DC2626; }}
        .dax-comment {{ color: #6B7280; font-style: italic; }}
        .dax-table {{ color: #2563EB; }}
        .dax-column {{ color: #EA580C; }}

        .dark-mode .dax-keyword {{ color: #60A5FA; }}
        .dark-mode .dax-function {{ color: #A78BFA; }}
        .dark-mode .dax-string {{ color: #34D399; }}
        .dark-mode .dax-number {{ color: #F87171; }}
        .dark-mode .dax-comment {{ color: #9CA3AF; }}
        .dark-mode .dax-table {{ color: #60A5FA; }}
        .dark-mode .dax-column {{ color: #FB923C; }}

        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .badge-primary {{ background: #E8ECFF; color: #4A6BEE; }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-gray {{ background: #f1f5f9; color: #475569; }}

        .scrollable {{
            max-height: calc(100vh - 250px);
            overflow-y: auto;
        }}

        .code-block {{
            background: #f5f5f5;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 0.875rem;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .dark-mode .code-block {{
            background: #0f172a;
            border: 1px solid #475569;
            color: #e2e8f0;
        }}

        .stat-card {{
            background: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }}

        .dark-mode .stat-card {{
            background: #1e293b;
            border: 1px solid #475569;
        }}

        .kpi-card {{
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .kpi-card h3 {{
            font-size: 0.875rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            opacity: 0.9;
        }}

        .kpi-card .value {{
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0;
        }}

        #graph-container {{
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            background: white;
            min-height: 600px;
            position: relative;
            overflow: hidden;
        }}

        #dependency-tree-container {{
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            background: white;
            max-height: 600px;
            overflow-y: auto;
        }}

        .graph-controls {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}

        .graph-control-btn {{
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            border: 2px solid #e2e8f0;
            background: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .graph-control-btn:hover {{
            border-color: var(--primary);
            background: #f0f4ff;
        }}

        .graph-control-btn.active {{
            border-color: var(--primary);
            background: var(--primary);
            color: white;
        }}

        .tree-node {{
            margin-left: 20px;
            border-left: 2px solid #e2e8f0;
            padding-left: 12px;
        }}

        .tree-node-header {{
            padding: 8px 12px;
            margin: 4px 0;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .tree-node-header:hover {{
            background: #f3f4f6;
        }}

        .tree-node-header.expanded {{
            background: #e8ecff;
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

        .relationship-link {{
            stroke: #94a3b8;
            stroke-width: 2px;
            fill: none;
        }}

        .relationship-link.active {{
            stroke: #10b981;
            stroke-width: 3px;
        }}

        .relationship-link.inactive {{
            stroke: #ef4444;
            stroke-width: 2px;
            stroke-dasharray: 5,5;
        }}

        .relationship-link.fact-to-dim {{
            stroke: #3b82f6;
        }}

        .relationship-link.dim-to-dim {{
            stroke: #8b5cf6;
        }}

        .graph-node {{
            cursor: pointer;
            transition: all 0.2s;
        }}

        .graph-node:hover circle {{
            stroke-width: 3px;
        }}

        .graph-node.fact-table circle {{
            fill: #3b82f6;
        }}

        .graph-node.dim-table circle {{
            fill: #10b981;
        }}

        .graph-node.other-table circle {{
            fill: #94a3b8;
        }}

        .graph-legend {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            font-size: 0.875rem;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid #1f2937;
        }}

        .dark-mode #graph-container,
        .dark-mode #dependency-tree-container {{
            background: #0f172a;
            border-color: #475569;
            min-height: 600px;
        }}

        .dark-mode #graph-container {{
            background: #1e293b;
            border-color: #475569;
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
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 10vh;
            z-index: 1000;
        }}

        .command-palette-content {{
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 600px;
            max-height: 70vh;
            overflow: hidden;
        }}

        .dark-mode .command-palette-content {{
            background: #1e293b;
        }}

        /* Highlight flash animation */
        @keyframes highlight-flash {{
            0%, 100% {{ background-color: transparent; }}
            50% {{ background-color: #fef3c7; }}
        }}

        .highlight-flash {{
            animation: highlight-flash 2s ease-in-out;
        }}

        /* v-cloak: Hide uncompiled Vue templates until Vue is ready */
        [v-cloak] {{
            display: none !important;
        }}
    </style>
"""

    def _get_body_content(self) -> str:
        """Get the Vue app container and HTML structure."""
        return f"""    <div id="app" v-cloak>
        <!-- Header -->
        <div class="shadow-sm border-b" style="background: linear-gradient(135deg, #5B7FFF 0%, #7D9AFF 100%); border: none;">
            <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center flex-wrap gap-4">
                    <div>
                        <h1 class="text-3xl font-bold text-white">{{{{ repositoryName }}}} - PBIP Analysis</h1>
                        <p class="text-sm mt-1 text-white opacity-90">
                            {{{{ statistics.total_tables }}}} tables ·
                            {{{{ statistics.total_measures }}}} measures ·
                            {{{{ statistics.total_relationships }}}} relationships
                            <span v-if="reportData"> · {{{{ statistics.total_pages }}}} pages · {{{{ statistics.total_visuals }}}} visuals</span>
                        </p>
                    </div>
                    <div class="flex items-center gap-2 flex-wrap">
                        <input
                            v-model="searchQuery"
                            type="text"
                            placeholder="Search... (press / to focus)"
                            class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-64"
                            @keydown.slash.prevent="$event.target.focus()"
                        />
                        <button
                            @click="exportToCSV"
                            class="px-3 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg transition text-sm"
                            title="Export to CSV"
                        >
                            📄 CSV
                        </button>
                        <button
                            @click="exportToJSON"
                            class="px-3 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition text-sm"
                            title="Export to JSON"
                        >
                            📦 JSON
                        </button>
                        <button
                            @click="showCommandPalette = true"
                            class="px-3 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition text-sm"
                            title="Command Palette (Ctrl/Cmd+K)"
                        >
                            ⌘
                        </button>
                        <button
                            @click="toggleDarkMode"
                            class="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg transition"
                            title="Toggle Dark Mode"
                        >
                            {{{{ darkMode ? '☀️' : '🌙' }}}}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
            <div class="border-b border-gray-200">
                <nav class="-mb-px flex space-x-8 overflow-x-auto">
                    <button
                        @click="activeTab = 'summary'"
                        :class="tabClass('summary')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        📊 Summary
                    </button>
                    <button
                        @click="activeTab = 'model'"
                        :class="tabClass('model')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        🗂️ Model ({{{{ modelData.tables?.length || 0 }}}})
                    </button>
                    <button
                        v-if="reportData"
                        @click="activeTab = 'report'"
                        :class="tabClass('report')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        📄 Report ({{{{ reportData.pages?.length || 0 }}}})
                    </button>
                    <button
                        @click="activeTab = 'dependencies'"
                        :class="tabClass('dependencies')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        🔀 Dependencies
                    </button>
                    <button
                        @click="activeTab = 'usage'"
                        :class="tabClass('usage')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        📈 Usage
                    </button>
                    <button
                        v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.bpa"
                        @click="activeTab = 'best-practices'"
                        :class="tabClass('best-practices')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        ✨ Best Practices ({{{{ bpaViolationsCount }}}})
                    </button>
                    <button
                        v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.data_types"
                        @click="activeTab = 'data-quality'"
                        :class="tabClass('data-quality')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        🔍 Data Quality ({{{{ dataQualityIssuesCount }}}})
                    </button>
                    <button
                        v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.dax_quality"
                        @click="activeTab = 'code-quality'"
                        :class="tabClass('code-quality')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        💎 Code Quality ({{{{ daxQualityIssuesCount }}}})
                    </button>
                    <button
                        v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.column_lineage"
                        @click="activeTab = 'lineage'"
                        :class="tabClass('lineage')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        🔗 Lineage ({{{{ Object.keys(columnLineage).length }}}})
                    </button>
                    <button
                        v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.perspectives && enhancedData.analyses.perspectives.has_perspectives"
                        @click="activeTab = 'perspectives'"
                        :class="tabClass('perspectives')"
                        class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition"
                    >
                        👁️ Perspectives ({{{{ perspectivesCount }}}})
                    </button>
                </nav>
            </div>
        </div>

        <!-- Content -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 pb-12">
            <!-- Summary Tab -->
            <div v-show="activeTab === 'summary'">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                    <div class="kpi-card">
                        <h3>Tables</h3>
                        <div class="value">{{{{ statistics.total_tables }}}}</div>
                    </div>
                    <div class="kpi-card">
                        <h3>Measures</h3>
                        <div class="value">{{{{ statistics.total_measures }}}}</div>
                    </div>
                    <div class="kpi-card">
                        <h3>Columns</h3>
                        <div class="value">{{{{ statistics.total_columns }}}}</div>
                    </div>
                    <div class="kpi-card">
                        <h3>Relationships</h3>
                        <div class="value">{{{{ statistics.total_relationships }}}}</div>
                    </div>
                </div>

                <!-- Model Information -->
                <div class="stat-card mb-6">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Model Information</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="font-semibold text-gray-700">Repository Path:</span>
                            <span class="text-gray-600 ml-2">{{{{ modelData.model_folder || 'Unknown' }}}}</span>
                        </div>
                        <div>
                            <span class="font-semibold text-gray-700">Model Type:</span>
                            <span class="text-gray-600 ml-2">Power BI Semantic Model (PBIP Format)</span>
                        </div>
                        <div>
                            <span class="font-semibold text-gray-700">Architecture:</span>
                            <span class="badge badge-primary ml-2">{{{{ modelArchitecture }}}}</span>
                        </div>
                        <div>
                            <span class="font-semibold text-gray-700">Expressions:</span>
                            <span class="text-gray-600 ml-2">{{{{ modelData.expressions?.length || 0 }}}} M/Power Query expressions</span>
                        </div>
                    </div>
                </div>

                <!-- Key Insights -->
                <div class="stat-card mb-6">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">📊 Key Insights</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <h3 class="text-sm font-semibold text-gray-600 mb-2">Table Distribution</h3>
                            <p class="text-sm text-gray-700">
                                <strong>{{{{ tableDistribution.fact }}}}%</strong> fact ·
                                <strong>{{{{ tableDistribution.dimension }}}}%</strong> dimension
                            </p>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-gray-600 mb-2">Model Density</h3>
                            <p class="text-sm text-gray-700">
                                Avg <strong>{{{{ avgColumnsPerTable }}}}</strong> columns/table<br>
                                Avg <strong>{{{{ avgMeasuresPerTable }}}}</strong> measures/table
                            </p>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-gray-600 mb-2">Measure Coverage</h3>
                            <p class="text-sm text-gray-700">
                                <strong>{{{{ measureToColumnRatio }}}}:1</strong> measure/column ratio<br>
                                <strong>{{{{ measuresUsedPct }}}}%</strong> measures in use
                            </p>
                        </div>
                        <div>
                            <h3 class="text-sm font-semibold text-gray-600 mb-2">Data Quality</h3>
                            <p class="text-sm text-gray-700">
                                <strong>{{{{ columnsUsedPct }}}}%</strong> columns referenced<br>
                                <strong>{{{{ statistics.total_relationships }}}}</strong> active relationships
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Issues & Recommendations -->
                <div v-if="issues.length > 0" class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6 rounded">
                    <h3 class="text-lg font-semibold text-yellow-800 mb-2">⚠️ Attention Required</h3>
                    <ul class="list-disc list-inside space-y-1 text-sm text-yellow-700">
                        <li v-for="issue in issues" :key="issue">{{{{ issue }}}}</li>
                    </ul>
                </div>

                <div v-if="recommendations.length > 0" class="bg-green-50 border-l-4 border-green-400 p-4 mb-6 rounded">
                    <h3 class="text-lg font-semibold text-green-800 mb-2">💡 Recommendations</h3>
                    <ul class="list-disc list-inside space-y-1 text-sm text-green-700">
                        <li v-for="rec in recommendations" :key="rec">{{{{ rec }}}}</li>
                    </ul>
                </div>

                <!-- Model Health -->
                <div class="stat-card">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">🏥 Model Health Summary</h2>
                    <p class="text-gray-700 mb-4">{{{{ healthSummary }}}}</p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="bg-gray-50 p-4 rounded">
                            <strong>Unused Objects:</strong> {{{{ statistics.unused_measures }}}} measures, {{{{ statistics.unused_columns }}}} columns
                        </div>
                        <div class="bg-gray-50 p-4 rounded">
                            <strong>Model Complexity:</strong> {{{{ modelComplexity }}}}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Model Tab -->
            <div v-show="activeTab === 'model'">
                <!-- Model Sub-Tabs -->
                <div class="mb-6 border-b border-gray-200">
                    <nav class="-mb-px flex space-x-8">
                        <button
                            @click="modelSubTab = 'tables'"
                            :class="[
                                'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition',
                                modelSubTab === 'tables' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            ]"
                        >
                            📊 Tables
                        </button>
                        <button
                            @click="modelSubTab = 'measures'"
                            :class="[
                                'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition',
                                modelSubTab === 'measures' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            ]"
                        >
                            📐 Measures
                        </button>
                        <button
                            @click="modelSubTab = 'relationships'"
                            :class="[
                                'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition',
                                modelSubTab === 'relationships' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            ]"
                        >
                            🔗 Relationships
                        </button>
                    </nav>
                </div>

                <!-- Tables View -->
                <div v-show="modelSubTab === 'tables'" class="grid grid-cols-12 gap-6">
                    <!-- Left Sidebar: Tables List -->
                    <div class="col-span-12 md:col-span-4">
                        <div class="stat-card">
                            <h3 class="text-xl font-bold text-gray-900 mb-4">Tables ({{{{ filteredTables.length }}}})</h3>
                            <input
                                v-model="modelSearchQuery"
                                type="search"
                                placeholder="Search tables..."
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
                            />
                            <div class="scrollable space-y-2">
                                <div
                                    v-for="table in filteredTables"
                                    :key="table.name"
                                    @click="selectedTable = table"
                                    :class="['list-item border-l-4 p-3 cursor-pointer rounded', selectedTable?.name === table.name ? 'selected' : 'border-gray-300']"
                                >
                                    <div class="flex items-center gap-2 mb-1">
                                        <div class="font-semibold text-gray-900">{{{{ table.name }}}}</div>
                                    </div>
                                    <div class="text-sm text-gray-600">
                                        {{{{ table.columns?.length || 0 }}}} columns · {{{{ table.measures?.length || 0 }}}} measures
                                    </div>
                                    <div class="flex gap-1 mt-1">
                                        <span :class="['badge text-xs', getTableType(table.name) === 'DIMENSION' ? 'badge-success' : getTableType(table.name) === 'FACT' ? 'badge-danger' : 'badge-gray']">
                                            {{{{ getTableType(table.name).toLowerCase() }}}}
                                        </span>
                                        <span :class="['badge text-xs', getComplexityBadge(table)]">
                                            {{{{ getTableComplexity(table).replace('Complexity: ', '').toLowerCase() }}}}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Panel: Table Details -->
                    <div class="col-span-12 md:col-span-8">
                        <div v-if="selectedTable" class="stat-card">
                            <div class="flex justify-between items-start mb-4">
                                <div>
                                    <h2 class="text-2xl font-bold text-gray-900">{{{{ selectedTable.name }}}}</h2>
                                    <div class="flex gap-2 mt-2">
                                        <span :class="['badge', selectedTable.name.toLowerCase().startsWith('f ') ? 'badge-danger' : selectedTable.name.toLowerCase().startsWith('d ') ? 'badge-primary' : 'badge-gray']">
                                            {{{{ getTableType(selectedTable.name) }}}}
                                        </span>
                                        <span :class="['badge', getComplexityBadge(selectedTable)]">
                                            {{{{ getTableComplexity(selectedTable) }}}}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <!-- Table Statistics -->
                            <div class="grid grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded">
                                <div>
                                    <div class="text-sm text-gray-600">Columns</div>
                                    <div class="text-2xl font-bold text-gray-900">{{{{ selectedTable.columns?.length || 0 }}}}</div>
                                </div>
                                <div>
                                    <div class="text-sm text-gray-600">Measures</div>
                                    <div class="text-2xl font-bold text-gray-900">{{{{ selectedTable.measures?.length || 0 }}}}</div>
                                </div>
                                <div>
                                    <div class="text-sm text-gray-600">Relationships</div>
                                    <div class="text-2xl font-bold text-gray-900">{{{{ getTableRelationshipCount(selectedTable.name) }}}}</div>
                                </div>
                                <div>
                                    <div class="text-sm text-gray-600">Usage</div>
                                    <div class="text-2xl font-bold text-gray-900">{{{{ getTableUsageCount(selectedTable.name) }}}}</div>
                                </div>
                            </div>

                            <div class="mb-6">
                                <div class="flex gap-2 mb-4 flex-wrap">
                                    <button
                                        @click="modelDetailTab = 'columns'"
                                        :class="['px-4 py-2 rounded-lg font-medium transition text-sm', modelDetailTab === 'columns' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700']"
                                    >
                                        Columns ({{{{ selectedTable.columns?.length || 0 }}}})
                                    </button>
                                    <button
                                        @click="modelDetailTab = 'measures'"
                                        :class="['px-4 py-2 rounded-lg font-medium transition text-sm', modelDetailTab === 'measures' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700']"
                                    >
                                        Measures ({{{{ selectedTable.measures?.length || 0 }}}})
                                    </button>
                                    <button
                                        @click="modelDetailTab = 'relationships'"
                                        :class="['px-4 py-2 rounded-lg font-medium transition text-sm', modelDetailTab === 'relationships' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700']"
                                    >
                                        Relationships ({{{{ getTableRelationshipCount(selectedTable.name) }}}})
                                    </button>
                                    <button
                                        @click="modelDetailTab = 'usage'"
                                        :class="['px-4 py-2 rounded-lg font-medium transition text-sm', modelDetailTab === 'usage' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700']"
                                    >
                                        Usage ({{{{ getTableUsageCount(selectedTable.name) }}}})
                                    </button>
                                </div>

                                <!-- Columns -->
                                <div v-show="modelDetailTab === 'columns'">
                                    <div v-if="selectedTable.columns?.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div v-for="col in selectedTable.columns" :key="col.name" class="border border-gray-200 rounded p-3">
                                            <div class="font-semibold text-gray-900 mb-1 flex items-center gap-2">
                                                <span>{{{{ col.name }}}}</span>
                                                <span v-if="isColumnInRelationship(selectedTable.name, col.name)" class="badge badge-info flex items-center gap-1">
                                                    <svg class="lucide-key-round w-3 h-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z"></path><circle cx="16.5" cy="7.5" r=".5"></circle></svg>
                                                    Key
                                                </span>
                                                <span v-if="col.is_hidden" class="badge badge-warning flex items-center gap-1">
                                                    <svg class="lucide-eye-off w-3 h-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path><line x1="2" x2="22" y1="2" y2="22"></line></svg>
                                                    Hidden
                                                </span>
                                            </div>
                                            <div class="text-sm text-gray-600">
                                                <span class="badge badge-gray">{{{{ col.data_type }}}}</span>
                                            </div>
                                            <div class="text-xs text-gray-500 mt-1">
                                                Source: {{{{ col.source_column || '-' }}}}
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="text-gray-500 italic">No columns in this table</div>
                                </div>

                                <!-- Measures -->
                                <div v-show="modelDetailTab === 'measures'">
                                    <div v-if="selectedTable.measures?.length > 0" class="space-y-4">
                                        <div v-for="measure in selectedTable.measures" :key="measure.name" class="border border-gray-200 rounded p-4" :data-measure="measure.name">
                                            <div class="flex items-center justify-between gap-2 mb-2">
                                                <div class="flex items-center gap-2">
                                                    <div class="font-semibold text-gray-900">{{{{ measure.name }}}}</div>
                                                    <span class="badge badge-primary text-xs">m Measure</span>
                                                    <span v-if="measure.display_folder" class="badge badge-warning text-xs">📁 {{{{ measure.display_folder }}}}</span>
                                                    <span v-if="measure.is_hidden" class="badge badge-gray text-xs">Hidden</span>
                                                </div>
                                                <button
                                                    v-if="measure.expression"
                                                    @click="toggleMeasureExpansion(measure.name)"
                                                    class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                                >
                                                    {{{{ expandedMeasures[measure.name] ? 'Hide DAX' : 'Show DAX' }}}}
                                                </button>
                                            </div>
                                            <div v-if="measure.expression && expandedMeasures[measure.name]" class="code-block mt-2" v-html="highlightDAX(measure.expression)"></div>
                                        </div>
                                    </div>
                                    <div v-else class="text-gray-500 italic">No measures in this table</div>
                                </div>

                                <!-- Relationships -->
                                <div v-show="modelDetailTab === 'relationships'">
                                    <div v-if="getTableRelationships(selectedTable.name).length > 0">
                                        <div class="mb-4">
                                            <h4 class="font-semibold text-gray-900 mb-2">Incoming ({{{{ getTableRelationships(selectedTable.name).filter(r => r.to_table === selectedTable.name).length }}}})</h4>
                                            <div class="space-y-2">
                                                <div v-for="rel in getTableRelationships(selectedTable.name).filter(r => r.to_table === selectedTable.name)" :key="rel.name" class="border border-gray-200 rounded p-3 bg-green-50">
                                                    <div class="flex items-center justify-between mb-1">
                                                        <span class="font-semibold text-sm">{{{{ rel.from_table }}}}</span>
                                                        <span class="badge badge-success text-xs">Active</span>
                                                    </div>
                                                    <div class="text-sm text-gray-600">
                                                        [{{{{ rel.from_column_name }}}}] → [{{{{ rel.to_column_name }}}}]
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div>
                                            <h4 class="font-semibold text-gray-900 mb-2">Outgoing ({{{{ getTableRelationships(selectedTable.name).filter(r => r.from_table === selectedTable.name).length }}}})</h4>
                                            <div class="space-y-2">
                                                <div v-for="rel in getTableRelationships(selectedTable.name).filter(r => r.from_table === selectedTable.name)" :key="rel.name" class="border border-gray-200 rounded p-3 bg-blue-50">
                                                    <div class="flex items-center justify-between mb-1">
                                                        <span class="font-semibold text-sm">{{{{ rel.to_table }}}}</span>
                                                        <span class="badge badge-success text-xs">Active</span>
                                                    </div>
                                                    <div class="text-sm text-gray-600">
                                                        [{{{{ rel.from_column_name }}}}] → [{{{{ rel.to_column_name }}}}]
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="text-gray-500 italic">No relationships for this table</div>
                                </div>

                                <!-- Usage -->
                                <div v-show="modelDetailTab === 'usage'">
                                    <h3 class="font-semibold text-gray-900 mb-3">Column Usage by Page</h3>
                                    <div v-if="selectedTable.columns?.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div v-for="col in selectedTable.columns" :key="col.name" class="border border-gray-200 rounded">
                                            <div class="font-semibold text-gray-900 p-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                                                <span>{{{{ col.name }}}}</span>
                                                <span class="badge badge-gray text-xs">{{{{ getColumnVisualUsage(selectedTable.name, col.name).length }}}} visual(s)</span>
                                            </div>
                                            <div class="p-3 space-y-3">
                                                <!-- Measure Usage -->
                                                <div v-if="getColumnUsedByMeasures(selectedTable.name, col.name).length > 0">
                                                    <div class="font-medium text-gray-700 text-sm mb-2 flex items-center gap-1">
                                                        <span>📐</span>
                                                        <span>Used in Measures</span>
                                                    </div>
                                                    <div class="space-y-1 ml-5">
                                                        <div v-for="measure in getColumnUsedByMeasures(selectedTable.name, col.name)" :key="measure" class="text-xs p-2 bg-blue-50 border border-blue-200 rounded flex items-center gap-2">
                                                            <span class="badge badge-primary" style="font-size: 10px; padding: 2px 6px;">Measure</span>
                                                            <span class="text-gray-700">{{{{ measure }}}}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- Field Parameter Usage -->
                                                <div v-if="getColumnFieldParams(selectedTable.name, col.name).length > 0">
                                                    <div class="font-medium text-gray-700 text-sm mb-2 flex items-center gap-1">
                                                        <span>📊</span>
                                                        <span>Used in Field Parameters</span>
                                                    </div>
                                                    <div class="space-y-1 ml-5">
                                                        <div v-for="fp in getColumnFieldParams(selectedTable.name, col.name)" :key="fp" class="text-xs p-2 bg-green-50 border border-green-200 rounded flex items-center gap-2">
                                                            <span class="badge badge-success" style="font-size: 10px; padding: 2px 6px;">Field Param</span>
                                                            <span class="text-gray-700">{{{{ fp }}}}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- Visual Usage -->
                                                <div v-if="getColumnVisualUsage(selectedTable.name, col.name).length > 0">
                                                    <div class="font-medium text-gray-700 text-sm mb-2 flex items-center gap-1">
                                                        <span>📈</span>
                                                        <span>Used in Visuals</span>
                                                    </div>
                                                    <div class="space-y-2">
                                                        <div v-for="(visuals, pageName) in groupColumnUsageByPage(selectedTable.name, col.name)" :key="pageName" class="border border-gray-100 rounded p-2">
                                                            <div class="font-medium text-gray-800 text-sm mb-1 flex items-center gap-1">
                                                                <span>📄</span>
                                                                <span>{{{{ pageName }}}}</span>
                                                                <span class="text-xs text-gray-500">({{{{ visuals.length }}}})</span>
                                                            </div>
                                                            <div class="space-y-1 ml-5">
                                                                <div v-for="usage in visuals" :key="usage.visualId" class="text-xs text-gray-600 flex items-center gap-2">
                                                                    <span class="badge badge-primary" style="font-size: 10px; padding: 2px 6px;">{{{{ usage.visualType }}}}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- No Usage Message -->
                                                <div v-if="getColumnVisualUsage(selectedTable.name, col.name).length === 0 && getColumnFieldParams(selectedTable.name, col.name).length === 0 && getColumnUsedByMeasures(selectedTable.name, col.name).length === 0" class="text-xs text-gray-500 italic">
                                                    Not used in any measures, visuals, or field parameters
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else class="text-gray-500 italic">No columns in this table</div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="stat-card">
                            <p class="text-gray-500 italic">Select a table from the left to view details</p>
                        </div>
                    </div>
                </div>

                <!-- Measures View -->
                <div v-show="modelSubTab === 'measures'">
                    <div class="stat-card">
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">All Measures by Folder</h2>
                        <div class="grid grid-cols-12 gap-4" style="height: 600px;">
                            <!-- Left: Folder list -->
                            <div class="col-span-4 overflow-y-auto border-r pr-4">
                                <input
                                    v-model="measuresSearchQuery"
                                    type="search"
                                    placeholder="Search measures..."
                                    class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
                                />
                                <div v-for="(folder, folderName) in measuresByFolder" :key="folderName" class="mb-2">
                                    <div class="folder-header cursor-pointer" @click="toggleFolder(folderName)">
                                        <div>
                                            <span class="mr-2">📁</span>
                                            <strong>{{{{ folderName || 'No Folder' }}}}</strong>
                                            <span class="ml-2 text-sm opacity-75">({{{{ folder.length }}}})</span>
                                        </div>
                                        <span class="expand-icon">▼</span>
                                    </div>
                                    <div v-show="!collapsedFolders[folderName]" class="ml-6 mt-2 space-y-1">
                                        <div
                                            v-for="measure in folder"
                                            :key="measure.key"
                                            @click="selectedMeasure = measure"
                                            :class="['p-2 rounded cursor-pointer hover:bg-blue-50', selectedMeasure?.key === measure.key ? 'bg-blue-100 font-semibold' : '']"
                                        >
                                            <div class="text-sm">{{{{ measure.name }}}}</div>
                                            <div class="text-xs text-gray-500">{{{{ measure.table }}}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Right: DAX viewer -->
                            <div class="col-span-8 overflow-y-auto">
                                <div v-if="selectedMeasure">
                                    <div class="mb-4">
                                        <h3 class="text-xl font-bold text-gray-900 mb-2">{{{{ selectedMeasure.name }}}}</h3>
                                        <div class="flex gap-2 mb-2">
                                            <span class="badge badge-primary">{{{{ selectedMeasure.table }}}}</span>
                                            <span v-if="selectedMeasure.is_hidden" class="badge badge-warning">Hidden</span>
                                            <span v-if="selectedMeasure.displayFolder" class="badge badge-gray">{{{{ selectedMeasure.displayFolder }}}}</span>
                                        </div>
                                    </div>
                                    <div class="code-block" v-if="selectedMeasure.expression" v-html="highlightDAX(selectedMeasure.expression)"></div>
                                </div>
                                <div v-else class="text-center text-gray-500 mt-20">
                                    <p>Select a measure from the left to view its DAX code</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Relationships View -->
                <div v-show="modelSubTab === 'relationships'">
                    <div class="stat-card">
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">Relationships ({{{{ sortedRelationships.length }}}})</h2>

                        <!-- Graph Layout Controls -->
                        <div class="graph-controls">
                            <button
                                @click="relationshipGraphLayout = 'list'"
                                :class="['graph-control-btn', relationshipGraphLayout === 'list' ? 'active' : '']"
                            >
                                📋 List View
                            </button>
                            <button
                                @click="relationshipGraphLayout = 'tree'"
                                :class="['graph-control-btn', relationshipGraphLayout === 'tree' ? 'active' : '']"
                            >
                                🌳 Hierarchical Tree
                            </button>
                            <button
                                @click="relationshipGraphLayout = 'force'"
                                :class="['graph-control-btn', relationshipGraphLayout === 'force' ? 'active' : '']"
                            >
                                🔗 Force-Directed
                            </button>
                        </div>

                        <!-- Legend -->
                        <div v-if="relationshipGraphLayout !== 'list' && sortedRelationships.length > 0" class="graph-legend">
                            <div class="legend-item">
                                <div class="legend-color" style="background: #3b82f6;"></div>
                                <span>Fact Tables</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: #10b981;"></div>
                                <span>Dimension Tables</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: #94a3b8;"></div>
                                <span>Other Tables</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: none; border: 2px solid #10b981;"></div>
                                <span>Active</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: none; border: 2px dashed #ef4444;"></div>
                                <span>Inactive</span>
                            </div>
                        </div>

                        <!-- Graph Container -->
                        <div v-if="relationshipGraphLayout !== 'list' && sortedRelationships.length > 0">
                            <div id="graph-container"></div>
                        </div>

                        <!-- List View -->
                        <div v-if="relationshipGraphLayout === 'list' && sortedRelationships.length > 0" class="space-y-4">
                            <!-- Group by Type -->
                            <div class="mb-4">
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Fact-to-Dimension Relationships</h3>
                                <div class="space-y-2">
                                    <div v-for="(rel, idx) in factToDimRelationships" :key="'f2d-' + idx" class="border border-blue-200 rounded p-3 bg-blue-50">
                                        <div class="flex items-center justify-between mb-2">
                                            <div class="font-semibold text-gray-900">
                                                {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                            </div>
                                            <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                                {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                            </span>
                                        </div>
                                        <div class="text-sm text-gray-600">
                                            <div><strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]</div>
                                            <div><strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]</div>
                                            <div class="mt-2">
                                                <span class="badge badge-primary mr-2">{{{{ formatCardinality(rel) }}}}</span>
                                                <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="factToDimRelationships.length === 0" class="text-gray-500 italic text-sm">No fact-to-dimension relationships</div>
                            </div>

                            <div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Dimension-to-Dimension Relationships</h3>
                                <div class="space-y-2">
                                    <div v-for="(rel, idx) in dimToDimRelationships" :key="'d2d-' + idx" class="border border-purple-200 rounded p-3 bg-purple-50">
                                        <div class="flex items-center justify-between mb-2">
                                            <div class="font-semibold text-gray-900">
                                                {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                            </div>
                                            <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                                {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                            </span>
                                        </div>
                                        <div class="text-sm text-gray-600">
                                            <div><strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]</div>
                                            <div><strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]</div>
                                            <div class="mt-2">
                                                <span class="badge badge-primary mr-2">{{{{ formatCardinality(rel) }}}}</span>
                                                <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="dimToDimRelationships.length === 0" class="text-gray-500 italic text-sm">No dimension-to-dimension relationships</div>
                            </div>

                            <div>
                                <h3 class="text-lg font-semibold text-gray-900 mb-2">Other Relationships</h3>
                                <div class="space-y-2">
                                    <div v-for="(rel, idx) in otherRelationships" :key="'other-' + idx" class="border border-gray-200 rounded p-3 bg-gray-50">
                                        <div class="flex items-center justify-between mb-2">
                                            <div class="font-semibold text-gray-900">
                                                {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                            </div>
                                            <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                                {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                            </span>
                                        </div>
                                        <div class="text-sm text-gray-600">
                                            <div><strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]</div>
                                            <div><strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]</div>
                                            <div class="mt-2">
                                                <span class="badge badge-primary mr-2">{{{{ formatCardinality(rel) }}}}</span>
                                                <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="otherRelationships.length === 0" class="text-gray-500 italic text-sm">No other relationships</div>
                            </div>
                        </div>

                        <div v-else-if="sortedRelationships.length === 0" class="text-gray-500 italic">No relationships found in model</div>
                    </div>
                </div>
            </div>

            <!-- Report Tab -->
            <div v-show="activeTab === 'report'" v-if="reportData">
                <div class="grid grid-cols-12 gap-6">
                    <!-- Left Sidebar: Pages List -->
                    <div class="col-span-12 md:col-span-3">
                        <div class="stat-card">
                            <h3 class="text-xl font-bold text-gray-900 mb-4">Pages ({{{{ reportData.pages?.length || 0 }}}})</h3>
                            <div class="space-y-2">
                                <div
                                    v-for="(page, idx) in sortedPages"
                                    :key="idx"
                                    @click="selectedPage = page"
                                    :class="['list-item border-l-4 p-3 cursor-pointer rounded', selectedPage === page ? 'selected' : 'border-gray-300']"
                                >
                                    <div class="font-semibold text-gray-900">{{{{ page.display_name || page.name }}}}</div>
                                    <div class="text-sm text-gray-600">
                                        {{{{ getVisibleVisualCount(page.visuals) }}}} visuals
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Panel: Page Details -->
                    <div class="col-span-12 md:col-span-9">
                        <div v-if="selectedPage" class="stat-card">
                            <h2 class="text-2xl font-bold text-gray-900 mb-4">{{{{ selectedPage.display_name || selectedPage.name }}}}</h2>

                            <!-- Page Filters -->
                            <div v-if="selectedPage.filters?.length > 0" class="bg-blue-50 p-4 rounded mb-4">
                                <h3 class="font-semibold text-gray-900 mb-2">Page Filters</h3>
                                <div class="flex flex-wrap gap-2">
                                    <span v-for="(filter, idx) in selectedPage.filters" :key="idx" class="badge badge-primary">
                                        {{{{ filter.field?.table }}}}[{{{{ filter.field?.name }}}}]
                                    </span>
                                </div>
                            </div>

                            <!-- Visuals Grouped by Type -->
                            <div class="space-y-4">
                                <div v-for="(group, visualType) in visualsByType(selectedPage.visuals)" :key="visualType">
                                    <div class="list-group-header" :class="{{collapsed: collapsedVisualGroups[visualType]}}" @click="toggleVisualGroup(visualType)">
                                        <div class="flex items-center">
                                            <span :class="getVisualIcon(visualType)" v-html="getVisualEmoji(visualType)"></span>
                                            <strong class="ml-2">{{{{ visualType }}}}</strong>
                                            <span class="ml-2 text-sm opacity-90">({{{{ group.length }}}})</span>
                                        </div>
                                        <span class="expand-icon">▼</span>
                                    </div>
                                    <div v-show="!collapsedVisualGroups[visualType]" class="list-group-items space-y-3 mt-2">
                                        <div v-for="(visual, idx) in group" :key="idx" class="border border-gray-200 rounded p-4 bg-white">
                                            <div class="flex justify-between items-center mb-3">
                                                <div class="font-semibold text-gray-900">
                                                    {{{{ visual.visual_name || visual.title || `${{visualType}} ${{idx + 1}}` }}}}
                                                </div>
                                                <div class="text-xs text-gray-500">{{{{ visual.id?.substring(0, 8) }}}}...</div>
                                            </div>

                                            <!-- Measures -->
                                            <div v-if="visual.fields?.measures?.length > 0" class="mb-2">
                                                <div class="text-sm font-semibold text-gray-700 mb-1">Measures ({{{{ visual.fields.measures.length }}}})</div>
                                                <div class="flex flex-wrap gap-2">
                                                    <span v-for="(m, midx) in visual.fields.measures" :key="midx" class="badge badge-success">
                                                        {{{{ m.table }}}}[{{{{ m.measure }}}}]
                                                    </span>
                                                </div>
                                            </div>

                                            <!-- Columns -->
                                            <div v-if="visual.fields?.columns?.length > 0">
                                                <div class="text-sm font-semibold text-gray-700 mb-1">Columns ({{{{ visual.fields.columns.length }}}})</div>
                                                <div class="flex flex-wrap gap-2">
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
                        <div v-else class="stat-card">
                            <p class="text-gray-500 italic">Select a page from the left to view visuals</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dependencies Tab -->
            <div v-show="activeTab === 'dependencies'">
                <!-- Dependency Sub-Tabs -->
                <div class="mb-6 border-b border-gray-200">
                    <nav class="-mb-px flex space-x-8">
                        <button
                            @click="dependencySubTab = 'measures'"
                            :class="[
                                'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition',
                                dependencySubTab === 'measures' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            ]"
                        >
                            📐 Measures
                        </button>
                        <button
                            @click="dependencySubTab = 'columns'"
                            :class="[
                                'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition',
                                dependencySubTab === 'columns' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            ]"
                        >
                            📊 Columns
                        </button>
                    </nav>
                </div>

                <!-- Measures Dependencies -->
                <div v-show="dependencySubTab === 'measures'" class="grid grid-cols-12 gap-6">
                    <!-- Left: Search & Select -->
                    <div class="col-span-12 md:col-span-4">
                        <div class="stat-card">
                            <h3 class="text-xl font-bold text-gray-900 mb-4">Select Measure</h3>
                            <input
                                v-model="dependencySearchQuery"
                                type="search"
                                placeholder="Search measures..."
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
                            />

                            <div class="scrollable space-y-2">
                                <div v-for="(folder, folderName) in measuresForDependencyByFolder" :key="folderName" class="mb-3">
                                    <div class="folder-header text-xs" @click="toggleDependencyFolder(folderName)">
                                        <div>
                                            <span class="mr-1">📁</span>
                                            <strong>{{{{ folderName || 'No Folder' }}}}</strong>
                                            <span class="ml-1 opacity-75">({{{{ folder.length }}}})</span>
                                        </div>
                                        <span class="expand-icon text-xs">▼</span>
                                    </div>
                                    <div v-show="!collapsedDependencyFolders[folderName]" class="mt-1 space-y-1">
                                        <div
                                            v-for="measure in folder"
                                            :key="measure.key"
                                            @click="selectDependencyObject(measure.key)"
                                            :class="['list-item border-l-4 p-2 cursor-pointer rounded text-sm', selectedDependencyKey === measure.key ? 'selected' : 'border-gray-300']"
                                        >
                                            <div class="font-semibold text-gray-900">{{{{ measure.name }}}}</div>
                                            <div class="text-xs text-gray-600">{{{{ measure.table }}}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Dependency Details -->
                    <div class="col-span-12 md:col-span-8">
                        <div v-if="selectedDependencyKey" class="stat-card">
                            <h2 class="text-2xl font-bold text-gray-900 mb-4">{{{{ selectedDependencyKey }}}}</h2>

                            <!-- Depends On -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Depends On ({{{{ currentDependencyDetails.dependsOn.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.dependsOn.length > 0" class="space-y-2">
                                    <div v-for="dep in currentDependencyDetails.dependsOn" :key="dep" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                        <span class="badge badge-primary">Measure</span>
                                        <span class="text-sm text-gray-700">{{{{ dep }}}}</span>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">No dependencies</div>
                            </div>

                            <!-- Used By -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used By ({{{{ currentDependencyDetails.usedBy.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.usedBy.length > 0" class="space-y-3">
                                    <div v-for="(measures, folderName) in groupMeasuresByFolder(currentDependencyDetails.usedBy)" :key="folderName" class="border border-gray-200 rounded">
                                        <div class="folder-header cursor-pointer" :class="{{collapsed: collapsedUsedByFolders[folderName]}}" @click="toggleUsedByFolder(folderName)">
                                            <div class="flex items-center gap-2">
                                                <span>📁</span>
                                                <span class="font-semibold">{{{{ folderName }}}}</span>
                                                <span class="text-sm text-gray-500">({{{{ measures.length }}}})</span>
                                            </div>
                                            <span class="expand-icon">▼</span>
                                        </div>
                                        <div v-show="!collapsedUsedByFolders[folderName]" class="folder-content space-y-1 p-3">
                                            <div v-for="measure in measures" :key="measure" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                                <span class="badge badge-success">Measure</span>
                                                <span class="text-sm text-gray-700">{{{{ measure }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used by other measures</div>
                            </div>

                            <!-- Used In Visuals -->
                            <div v-if="reportData">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used In Visuals ({{{{ currentDependencyDetails.visualUsage.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.visualUsage.length > 0" class="space-y-3">
                                    <div v-for="(visuals, pageName) in groupVisualUsageByPage(currentDependencyDetails.visualUsage)" :key="pageName" class="border border-gray-200 rounded p-3">
                                        <div class="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                                            <span>📄</span>
                                            <span>{{{{ pageName }}}}</span>
                                            <span class="text-sm text-gray-500">({{{{ visuals.length }}}})</span>
                                        </div>
                                        <div class="space-y-1 ml-6">
                                            <div v-for="usage in visuals" :key="usage.visualId" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                                <span class="badge badge-warning">{{{{ usage.visualType }}}}</span>
                                                <span class="text-sm text-gray-700">{{{{ usage.visualName || 'Unnamed Visual' }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used in any visuals</div>
                            </div>
                        </div>
                        <div v-else class="stat-card">
                            <p class="text-gray-500 italic">Select a measure from the left to view dependencies</p>
                        </div>
                    </div>
                </div>

                <!-- Columns Dependencies -->
                <div v-show="dependencySubTab === 'columns'" class="grid grid-cols-12 gap-6">
                    <!-- Left: Search & Select -->
                    <div class="col-span-12 md:col-span-4">
                        <div class="stat-card">
                            <h3 class="text-xl font-bold text-gray-900 mb-4">Select Column</h3>
                            <input
                                v-model="columnSearchQuery"
                                type="search"
                                placeholder="Search columns..."
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
                            />

                            <div class="scrollable">
                                <div v-for="(columns, tableName) in filteredColumnsForDependency" :key="tableName" class="folder-item">
                                    <div class="folder-header" @click="toggleDependencyFolder(tableName)">
                                        <div>
                                            <span class="mr-2">📊</span>
                                            <strong>{{{{ tableName }}}}</strong>
                                            <span class="ml-2 text-sm opacity-75">({{{{ columns.length }}}})</span>
                                        </div>
                                        <span class="expand-icon">▼</span>
                                    </div>
                                    <div v-show="!collapsedDependencyFolders[tableName]" class="folder-content space-y-2">
                                        <div
                                            v-for="column in columns"
                                            :key="column.key"
                                            @click="selectColumnDependency(column.key)"
                                            :class="['list-item border-l-4 p-3 cursor-pointer rounded', selectedColumnKey === column.key ? 'selected' : 'border-gray-300']"
                                        >
                                            <div class="font-semibold text-gray-900">{{{{ column.name }}}}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right: Column Dependency Details -->
                    <div class="col-span-12 md:col-span-8">
                        <div v-if="selectedColumnKey" class="stat-card">
                            <h2 class="text-2xl font-bold text-gray-900 mb-4">{{{{ selectedColumnKey }}}}</h2>

                            <!-- Used By Field Parameters -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used By Field Parameters ({{{{ currentColumnDependencies.usedByFieldParams.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.usedByFieldParams.length > 0" class="space-y-2">
                                    <div v-for="fieldParam in currentColumnDependencies.usedByFieldParams" :key="fieldParam" class="flex items-center gap-2 p-2 bg-green-50 rounded border border-green-200">
                                        <span class="badge badge-success">Field Parameter</span>
                                        <span class="text-sm text-gray-700">{{{{ fieldParam }}}}</span>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used by any field parameters</div>
                            </div>

                            <!-- Used By Measures -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used By Measures ({{{{ currentColumnDependencies.usedByMeasures.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.usedByMeasures.length > 0" class="space-y-3">
                                    <div v-for="(measures, folderName) in groupMeasuresByFolder(currentColumnDependencies.usedByMeasures)" :key="folderName" class="border border-gray-200 rounded p-3">
                                        <div class="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                                            <span>📁</span>
                                            <span>{{{{ folderName }}}}</span>
                                            <span class="text-sm text-gray-500">({{{{ measures.length }}}})</span>
                                        </div>
                                        <div class="space-y-1 ml-6">
                                            <div v-for="measure in measures" :key="measure" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                                <span class="badge badge-success">Measure</span>
                                                <span class="text-sm text-gray-700">{{{{ measure }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used by any measures</div>
                            </div>

                            <!-- Used In Visuals -->
                            <div v-if="reportData">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used In Visuals ({{{{ currentColumnDependencies.visualUsage.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.visualUsage.length > 0" class="space-y-3">
                                    <div v-for="(visuals, pageName) in groupVisualUsageByPage(currentColumnDependencies.visualUsage)" :key="pageName" class="border border-gray-200 rounded p-3">
                                        <div class="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                                            <span>📄</span>
                                            <span>{{{{ pageName }}}}</span>
                                            <span class="text-sm text-gray-500">({{{{ visuals.length }}}})</span>
                                        </div>
                                        <div class="space-y-1 ml-6">
                                            <div v-for="usage in visuals" :key="usage.visualId" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                                <span class="badge badge-warning">{{{{ usage.visualType }}}}</span>
                                                <span class="text-sm text-gray-700">{{{{ usage.visualName || 'Unnamed Visual' }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used in any visuals</div>
                            </div>
                        </div>
                        <div v-else class="stat-card">
                            <p class="text-gray-500 italic">Select a column from the left to view usage</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Usage Tab -->
            <div v-show="activeTab === 'usage'" class="space-y-6">
                <!-- Field Parameters Section (Full Width) -->
                <div class="stat-card">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Field Parameters</h2>
                    <div v-if="fieldParametersList.length > 0" class="bg-blue-50 p-4 rounded mb-4">
                        <strong>Info:</strong> Found {{{{ fieldParametersList.length }}}} field parameter(s) in the model.
                    </div>
                    <div v-if="fieldParametersList.length > 0" class="space-y-4">
                        <div v-for="fp in fieldParametersList" :key="fp.name" class="border border-blue-200 rounded p-4 bg-white">
                            <div class="flex items-center gap-2 mb-3">
                                <span class="badge badge-success text-base">{{{{ fp.name }}}}</span>
                                <span class="text-sm text-gray-500">{{{{ fp.table }}}}</span>
                            </div>
                            <div v-if="fp.columns && fp.columns.length > 0">
                                <h4 class="font-semibold text-gray-700 mb-2">Referenced Columns ({{{{ fp.columns.length }}}}):</h4>
                                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                    <div v-for="col in fp.columns" :key="col" class="text-sm p-2 bg-gray-50 rounded border border-gray-200">
                                        {{{{ col }}}}
                                    </div>
                                </div>
                            </div>
                            <div v-else class="text-gray-500 italic text-sm">No columns referenced</div>
                        </div>
                    </div>
                    <div v-else class="text-gray-500 italic">No field parameters found in the model.</div>
                </div>

                <!-- Unused Measures and Columns Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="stat-card">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-2xl font-bold text-gray-900">Unused Measures</h2>
                            <div v-if="dependencies.unused_measures?.length > 0" class="flex gap-2">
                                <button @click="expandAllUnusedMeasures" class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">Expand All</button>
                                <button @click="collapseAllUnusedMeasures" class="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600">Collapse All</button>
                            </div>
                        </div>
                        <div v-if="dependencies.unused_measures?.length > 0" class="bg-yellow-50 p-4 rounded mb-4">
                            <strong>Warning:</strong> Found {{{{ dependencies.unused_measures.length }}}} measures not used anywhere.
                        </div>
                        <div v-if="dependencies.unused_measures?.length > 0" class="space-y-4 max-h-96 overflow-y-auto">
                            <!-- Grouped by folder -->
                            <div v-for="(measures, folderName) in unusedMeasuresByFolder" :key="folderName">
                                <div class="list-group-header" :class="{{collapsed: collapsedUnusedMeasureFolders[folderName]}}" @click="toggleUnusedMeasureFolder(folderName)">
                                    <div>
                                        <strong>{{{{ folderName }}}}</strong>
                                        <span class="ml-2 text-sm opacity-75">({{{{ measures.length }}}})</span>
                                    </div>
                                    <span class="expand-icon">▼</span>
                                </div>
                                <div v-show="!collapsedUnusedMeasureFolders[folderName]" class="folder-content space-y-2 mt-2">
                                    <div v-for="measure in measures" :key="measure" class="p-2 border border-gray-200 rounded text-sm bg-white">
                                        {{{{ measure }}}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="text-green-600 font-semibold">✓ All measures are in use!</div>
                    </div>

                    <div class="stat-card">
                        <div class="flex items-center justify-between mb-4">
                            <h2 class="text-2xl font-bold text-gray-900">Unused Columns</h2>
                            <div v-if="dependencies.unused_columns?.length > 0" class="flex gap-2">
                                <button @click="expandAllUnusedColumns" class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">Expand All</button>
                                <button @click="collapseAllUnusedColumns" class="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600">Collapse All</button>
                            </div>
                        </div>
                        <div v-if="dependencies.unused_columns?.length > 0" class="bg-yellow-50 p-4 rounded mb-4">
                            <strong>Warning:</strong> Found {{{{ dependencies.unused_columns.length }}}} columns not used anywhere.
                        </div>
                        <div v-if="dependencies.unused_columns?.length > 0" class="space-y-4 max-h-96 overflow-y-auto">
                            <!-- Grouped by table -->
                            <div v-for="(columns, tableName) in unusedColumnsByTable" :key="tableName">
                                <div class="list-group-header" :class="{{collapsed: collapsedUnusedColumnTables[tableName]}}" @click="toggleUnusedColumnTable(tableName)">
                                    <div>
                                        <strong>{{{{ tableName }}}}</strong>
                                        <span class="ml-2 text-sm opacity-75">({{{{ columns.length }}}})</span>
                                    </div>
                                    <span class="expand-icon">▼</span>
                                </div>
                                <div v-show="!collapsedUnusedColumnTables[tableName]" class="folder-content space-y-2 mt-2">
                                    <div v-for="column in columns" :key="column" class="p-2 border border-gray-200 rounded text-sm bg-white">
                                        {{{{ column }}}}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="text-green-600 font-semibold">✓ All columns are in use!</div>
                    </div>
                </div>
            </div>

            <!-- Best Practices Tab -->
            <div v-show="activeTab === 'best-practices'" v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.bpa">
                <div class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">Best Practice Analysis</h1>
                    <p class="text-gray-600">Analysis based on Microsoft Power BI Best Practices</p>
                </div>

                <!-- BPA Summary Cards -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                    <div class="kpi-card">
                        <h3>Total Violations</h3>
                        <p class="text-4xl font-bold text-gray-900">{{{{ bpaTotalViolations }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Errors</h3>
                        <p class="text-4xl font-bold text-red-600">{{{{ bpaErrorCount }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Warnings</h3>
                        <p class="text-4xl font-bold text-yellow-600">{{{{ bpaWarningCount }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Info</h3>
                        <p class="text-4xl font-bold text-blue-600">{{{{ bpaInfoCount }}}}</p>
                    </div>
                </div>

                <!-- Category Breakdown -->
                <div class="stat-card mb-6">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Violations by Category</h2>
                    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                        <div v-for="(count, category) in bpaCategoryBreakdown" :key="category" class="p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-600 mb-1">{{{{ category }}}}</div>
                            <div class="text-2xl font-bold">{{{{ count }}}}</div>
                        </div>
                    </div>
                </div>

                <!-- Violations by Object Type -->
                <div class="stat-card">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-2xl font-bold text-gray-900">Violations by Object Type</h2>
                        <div class="flex gap-2">
                            <select v-model="bpaSeverityFilter" class="px-3 py-1 text-sm border border-gray-300 rounded">
                                <option value="all">All Severities</option>
                                <option value="ERROR">Errors</option>
                                <option value="WARNING">Warnings</option>
                                <option value="INFO">Info</option>
                            </select>
                            <select v-model="bpaCategoryFilter" class="px-3 py-1 text-sm border border-gray-300 rounded">
                                <option value="all">All Categories</option>
                                <option v-for="category in bpaCategories" :key="category" :value="category">{{{{ category }}}}</option>
                            </select>
                        </div>
                    </div>

                    <!-- Group by Object Type, then by Category (with Maintenance last) -->
                    <div v-for="objectType in bpaObjectTypes" :key="objectType" class="mb-4">
                        <div
                            @click="toggleBpaObjectGroup(objectType)"
                            class="flex items-center justify-between p-3 bg-gray-100 hover:bg-gray-200 cursor-pointer rounded-t"
                        >
                            <div class="flex items-center gap-2">
                                <svg class="w-5 h-5 transition-transform" :class="{{'rotate-90': !collapsedBpaObjectGroups[objectType]}}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                </svg>
                                <span class="font-semibold text-lg text-gray-900">
                                    {{{{ objectType }}}} ({{{{ bpaViolationsByObjectType[objectType].length }}}})
                                </span>
                            </div>
                        </div>

                        <div v-show="!collapsedBpaObjectGroups[objectType]" class="border border-gray-200 border-t-0 rounded-b">
                            <!-- Violations grouped by category within this object type -->
                            <div v-for="category in bpaOrderedCategories" :key="category">
                                <template v-if="bpaViolationsByObjectAndCategory[objectType] && bpaViolationsByObjectAndCategory[objectType][category]">
                                    <div class="bg-gray-50 px-4 py-2 border-b border-gray-200">
                                        <span class="font-medium text-gray-700">{{{{ category }}}} ({{{{ bpaViolationsByObjectAndCategory[objectType][category].length }}}})</span>
                                    </div>
                                    <div class="overflow-x-auto">
                                        <table class="min-w-full divide-y divide-gray-200">
                                            <thead class="bg-gray-50">
                                                <tr>
                                                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                                                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Rule</th>
                                                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Object</th>
                                                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                                                </tr>
                                            </thead>
                                            <tbody class="bg-white divide-y divide-gray-200">
                                                <tr v-for="violation in bpaViolationsByObjectAndCategory[objectType][category]" :key="violation.rule_id + violation.object_name" class="hover:bg-gray-50">
                                                    <td class="px-4 py-2 whitespace-nowrap">
                                                        <span :class="bpaSeverityClass(violation.severity)" class="px-2 py-1 text-xs font-semibold rounded">
                                                            {{{{ violation.severity }}}}
                                                        </span>
                                                    </td>
                                                    <td class="px-4 py-2 text-sm text-gray-900">{{{{ violation.rule_name }}}}</td>
                                                    <td class="px-4 py-2 text-sm">
                                                        <div class="font-medium text-gray-900">{{{{ violation.object_name }}}}</div>
                                                        <div v-if="violation.table_name" class="text-xs text-gray-500">Table: {{{{ violation.table_name }}}}</div>
                                                    </td>
                                                    <td class="px-4 py-2 text-sm text-gray-600">
                                                        <div>{{{{ violation.description }}}}</div>
                                                        <div v-if="violation.details" class="mt-1 text-xs text-gray-500">{{{{ violation.details }}}}</div>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>

                    <div v-if="filteredBpaViolations.length === 0" class="text-center py-8 text-gray-500">
                        No violations found matching your filters
                    </div>
                </div>

                <!-- Naming Conventions Section -->
                <div v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.naming_conventions" class="stat-card mt-6">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Naming Convention Violations</h2>

                    <div v-if="namingViolationsCount === 0" class="text-center py-8">
                        <div class="text-6xl mb-4">✅</div>
                        <h3 class="text-xl font-semibold text-green-700 mb-2">All naming conventions followed!</h3>
                        <p class="text-gray-600">No violations found</p>
                    </div>

                    <div v-else>
                        <!-- Naming Summary -->
                        <div class="grid grid-cols-3 gap-4 mb-6">
                            <div class="text-center p-4 bg-red-50 rounded">
                                <p class="text-sm text-gray-600 mb-1">Total Violations</p>
                                <p class="text-3xl font-bold text-red-600">{{{{ namingViolationsCount }}}}</p>
                            </div>
                            <div class="text-center p-4 bg-yellow-50 rounded">
                                <p class="text-sm text-gray-600 mb-1">Warnings</p>
                                <p class="text-3xl font-bold text-yellow-600">{{{{ namingSummary.by_severity?.WARNING || 0 }}}}</p>
                            </div>
                            <div class="text-center p-4 bg-blue-50 rounded">
                                <p class="text-sm text-gray-600 mb-1">Info</p>
                                <p class="text-3xl font-bold text-blue-600">{{{{ namingSummary.by_severity?.INFO || 0 }}}}</p>
                            </div>
                        </div>

                        <!-- Filters -->
                        <div class="flex gap-2 mb-4">
                            <select v-model="namingSeverityFilter" class="px-3 py-2 text-sm border border-gray-300 rounded">
                                <option value="all">All Severities</option>
                                <option value="WARNING">Warnings</option>
                                <option value="INFO">Info</option>
                            </select>
                            <select v-model="namingTypeFilter" class="px-3 py-2 text-sm border border-gray-300 rounded">
                                <option value="all">All Types</option>
                                <option value="missing_prefix">Missing Prefix</option>
                                <option value="contains_spaces">Contains Spaces</option>
                                <option value="name_too_long">Name Too Long</option>
                                <option value="special_characters">Special Characters</option>
                            </select>
                        </div>

                        <!-- Violations Table -->
                        <div class="overflow-x-auto max-h-[400px] overflow-y-auto">
                            <table class="min-w-full divide-y divide-gray-200">
                                <thead class="bg-gray-50 sticky top-0">
                                    <tr>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Object Type</th>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Table</th>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Object</th>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Issue</th>
                                        <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Name</th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
                                    <tr v-for="(violation, idx) in filteredNamingViolations" :key="idx" class="hover:bg-gray-50">
                                        <td class="px-4 py-3 whitespace-nowrap">
                                            <span :class="severityBadgeClass(violation.severity)" class="px-2 py-1 text-xs font-semibold rounded">
                                                {{{{ violation.severity }}}}
                                            </span>
                                        </td>
                                        <td class="px-4 py-3 text-sm text-gray-600">{{{{ violation.type }}}}</td>
                                        <td class="px-4 py-3 text-sm text-gray-700">{{{{ violation.object_type }}}}</td>
                                        <td class="px-4 py-3 text-sm font-medium text-gray-900">{{{{ violation.table }}}}</td>
                                        <td class="px-4 py-3 text-sm text-gray-900">{{{{ violation.object }}}}</td>
                                        <td class="px-4 py-3 text-sm text-gray-600">{{{{ violation.issue }}}}</td>
                                        <td class="px-4 py-3 text-sm font-mono text-gray-700">{{{{ violation.current_name }}}}</td>
                                    </tr>
                                </tbody>
                            </table>
                            <div v-if="filteredNamingViolations.length === 0" class="text-center py-8 text-gray-500">
                                No violations match your filters
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Data Quality Tab -->
            <div v-show="activeTab === 'data-quality'" v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.data_types">
                <div class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">Data Quality Analysis</h1>
                    <p class="text-gray-600">Data type optimization and cardinality warnings</p>
                </div>

                <!-- Data Type Summary -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div class="stat-card">
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">Data Type Distribution</h2>
                        <div class="space-y-2">
                            <div v-for="(count, type) in dataTypeSummary" :key="type" class="flex justify-between items-center p-2 bg-gray-50 rounded">
                                <span class="font-medium">{{{{ type }}}}</span>
                                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">{{{{ count }}}}</span>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">Quality Metrics</h2>
                        <div class="space-y-4">
                            <div class="kpi-card">
                                <h3>Data Type Issues</h3>
                                <p class="text-4xl font-bold text-yellow-600">{{{{ dataTypeIssues.length }}}}</p>
                            </div>
                            <div class="kpi-card">
                                <h3>High-Impact Issues</h3>
                                <p class="text-4xl font-bold text-red-600">{{{{ dataTypeHighImpactCount }}}}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Data Type Issues Table -->
                <div class="stat-card mb-6">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-2xl font-bold text-gray-900">Data Type Optimization Opportunities</h2>
                        <select v-model="dataTypeImpactFilter" class="px-3 py-1 text-sm border border-gray-300 rounded">
                            <option value="all">All Impact Levels</option>
                            <option value="HIGH">High Impact</option>
                            <option value="MEDIUM">Medium Impact</option>
                            <option value="LOW">Low Impact</option>
                        </select>
                    </div>
                    <div class="overflow-x-auto max-h-[500px] overflow-y-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Table</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Column</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Current Type</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Issue</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Impact</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                <tr v-for="issue in filteredDataTypeIssues" :key="issue.table + issue.column" class="hover:bg-gray-50">
                                    <td class="px-4 py-3 text-sm font-medium text-gray-900">{{{{ issue.table }}}}</td>
                                    <td class="px-4 py-3 text-sm text-gray-900">{{{{ issue.column }}}}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <code class="px-2 py-1 bg-gray-100 rounded text-xs">{{{{ issue.current_type }}}}</code>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-gray-600">{{{{ issue.issue }}}}</td>
                                    <td class="px-4 py-3 text-sm text-blue-600">{{{{ issue.recommendation }}}}</td>
                                    <td class="px-4 py-3 whitespace-nowrap">
                                        <span :class="impactBadgeClass(issue.impact)" class="px-2 py-1 text-xs font-semibold rounded">
                                            {{{{ issue.impact }}}}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div v-if="filteredDataTypeIssues.length === 0" class="text-center py-8 text-gray-500">
                            No data type issues found
                        </div>
                    </div>
                </div>

                <!-- Cardinality Warnings -->
                <div class="stat-card" v-if="cardinalityWarnings.length > 0">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">High Cardinality Warnings</h2>
                    <div class="bg-yellow-50 p-4 rounded mb-4">
                        <strong>Note:</strong> High cardinality columns can impact performance and memory usage. Consider hiding or pre-aggregating these columns.
                    </div>
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Table</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Column</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Is Hidden</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                <tr v-for="warning in cardinalityWarnings" :key="warning.table + warning.column" class="hover:bg-gray-50">
                                    <td class="px-4 py-3 text-sm font-medium text-gray-900">{{{{ warning.table }}}}</td>
                                    <td class="px-4 py-3 text-sm text-gray-900">{{{{ warning.column }}}}</td>
                                    <td class="px-4 py-3 text-sm text-gray-600">{{{{ warning.reason }}}}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <span :class="warning.is_hidden ? 'text-green-600' : 'text-red-600'" class="font-semibold">
                                            {{{{ warning.is_hidden ? '✓ Yes' : '✗ No' }}}}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-blue-600">{{{{ warning.recommendation }}}}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Code Quality Tab -->
            <div v-show="activeTab === 'code-quality'" v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.dax_quality">
                <div class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">DAX Code Quality Analysis</h1>
                    <p class="text-gray-600">Complexity metrics and anti-pattern detection</p>
                </div>

                <!-- DAX Quality Summary -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                    <div class="kpi-card">
                        <h3>Total Measures</h3>
                        <p class="text-4xl font-bold text-gray-900">{{{{ daxSummary.total_measures || 0 }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Avg Complexity</h3>
                        <p class="text-4xl font-bold text-blue-600">{{{{ daxSummary.avg_complexity || 0 }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>High Complexity</h3>
                        <p class="text-4xl font-bold text-red-600">{{{{ daxSummary.high_complexity_measures || 0 }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Total Issues</h3>
                        <p class="text-4xl font-bold text-yellow-600">{{{{ daxQualityIssues.length }}}}</p>
                    </div>
                </div>

                <!-- DAX Quality Issues Table -->
                <div class="stat-card">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-2xl font-bold text-gray-900">Code Quality Issues</h2>
                        <div class="flex gap-2">
                            <select v-model="daxSeverityFilter" class="px-3 py-1 text-sm border border-gray-300 rounded">
                                <option value="all">All Severities</option>
                                <option value="WARNING">Warnings</option>
                                <option value="INFO">Info</option>
                            </select>
                            <select v-model="daxTypeFilter" class="px-3 py-1 text-sm border border-gray-300 rounded">
                                <option value="all">All Types</option>
                                <option value="high_complexity">High Complexity</option>
                                <option value="deep_nesting">Deep Nesting</option>
                                <option value="excessive_calculate">Excessive CALCULATE</option>
                                <option value="no_variables">No Variables</option>
                                <option value="sumx_filter">SUMX(FILTER) Pattern</option>
                            </select>
                        </div>
                    </div>
                    <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100" @click="sortDaxQuality('type')">
                                        Type
                                        <span v-if="daxQualitySortBy === 'type'">{{{{ daxQualitySortDesc ? '▼' : '▲' }}}}</span>
                                    </th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100" @click="sortDaxQuality('table')">
                                        Table
                                        <span v-if="daxQualitySortBy === 'table'">{{{{ daxQualitySortDesc ? '▼' : '▲' }}}}</span>
                                    </th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100" @click="sortDaxQuality('measure')">
                                        Measure
                                        <span v-if="daxQualitySortBy === 'measure'">{{{{ daxQualitySortDesc ? '▼' : '▲' }}}}</span>
                                    </th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Issue</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recommendation</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100" @click="sortDaxQuality('complexity')">
                                        Complexity
                                        <span v-if="daxQualitySortBy === 'complexity'">{{{{ daxQualitySortDesc ? '▼' : '▲' }}}}</span>
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                <tr v-for="(issue, idx) in sortedDaxQualityIssues" :key="idx" class="hover:bg-gray-50">
                                    <td class="px-4 py-3 whitespace-nowrap">
                                        <span :class="severityBadgeClass(issue.severity)" class="px-2 py-1 text-xs font-semibold rounded">
                                            {{{{ issue.severity }}}}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-gray-600">{{{{ issue.type }}}}</td>
                                    <td class="px-4 py-3 text-sm font-medium text-gray-900">{{{{ issue.table }}}}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <button
                                            @click="jumpToMeasureInModel(issue.table, issue.measure)"
                                            class="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                                            title="Go to measure in Model tab"
                                        >
                                            {{{{ issue.measure }}}}
                                        </button>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-gray-600">{{{{ issue.issue }}}}</td>
                                    <td class="px-4 py-3 text-sm text-blue-600">{{{{ issue.recommendation }}}}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <span v-if="issue.complexity_score" :class="complexityBadgeClass(issue.complexity_score)" class="px-2 py-1 text-xs font-semibold rounded">
                                            {{{{ issue.complexity_score }}}}
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div v-if="sortedDaxQualityIssues.length === 0" class="text-center py-8 text-gray-500">
                            No code quality issues found
                        </div>
                    </div>
                </div>
            </div>

            <!-- Column Lineage Tab -->
            <div v-show="activeTab === 'lineage'" v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.column_lineage">
                <div class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">Column Lineage & Impact Analysis</h1>
                    <p class="text-gray-600">Track column usage and impact across the model</p>
                </div>

                <!-- Lineage Summary -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                    <div class="kpi-card">
                        <h3>Total Columns</h3>
                        <p class="text-4xl font-bold text-gray-900">{{{{ Object.keys(columnLineage).length }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Orphan Columns</h3>
                        <p class="text-4xl font-bold text-red-600">{{{{ orphanColumnsCount }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>Calculated Columns</h3>
                        <p class="text-4xl font-bold text-blue-600">{{{{ calculatedColumnsCount }}}}</p>
                    </div>
                    <div class="kpi-card">
                        <h3>High Usage</h3>
                        <p class="text-4xl font-bold text-green-600">{{{{ highUsageColumnsCount }}}}</p>
                    </div>
                </div>

                <!-- Search and Filter -->
                <div class="stat-card mb-6">
                    <div class="flex items-center gap-4">
                        <input
                            v-model="lineageSearchQuery"
                            type="text"
                            placeholder="Search columns..."
                            class="flex-1 px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        <select v-model="lineageUsageFilter" class="px-3 py-2 border border-gray-300 rounded">
                            <option value="all">All Columns</option>
                            <option value="orphan">Orphan Only</option>
                            <option value="calculated">Calculated Only</option>
                            <option value="high-usage">High Usage (3+)</option>
                        </select>
                    </div>
                </div>

                <!-- Column Lineage Table -->
                <div class="stat-card">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Column Impact Analysis</h2>
                    <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Table</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Column</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Data Type</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">In Measures</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">In Relationships</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">In Visuals</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usage Score</th>
                                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                <tr v-for="(lineage, colKey) in filteredColumnLineage" :key="colKey" class="hover:bg-gray-50">
                                    <td class="px-4 py-3 text-sm font-medium text-gray-900">{{{{ lineage.table }}}}</td>
                                    <td class="px-4 py-3 text-sm text-gray-900">{{{{ lineage.column }}}}</td>
                                    <td class="px-4 py-3 text-sm">
                                        <span v-if="lineage.is_calculated" class="px-2 py-1 text-xs font-semibold rounded bg-purple-100 text-purple-800">
                                            Calculated
                                        </span>
                                        <span v-else class="px-2 py-1 text-xs font-semibold rounded bg-gray-100 text-gray-800">
                                            Physical
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-gray-600 font-mono">{{{{ lineage.data_type }}}}</td>
                                    <td class="px-4 py-3 text-sm text-center">
                                        <span class="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
                                            {{{{ lineage.used_in_measures?.length || 0 }}}}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-center">
                                        <span class="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                                            {{{{ lineage.used_in_relationships?.length || 0 }}}}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-center">
                                        <span class="px-2 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800">
                                            {{{{ lineage.used_in_visuals?.length || 0 }}}}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-sm text-center">
                                        <span :class="usageScoreBadgeClass(lineage.usage_score)" class="px-2 py-1 text-xs font-semibold rounded">
                                            {{{{ lineage.usage_score }}}}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 whitespace-nowrap">
                                        <span v-if="lineage.is_orphan" class="px-2 py-1 text-xs font-semibold rounded bg-red-100 text-red-800">
                                            Orphan
                                        </span>
                                        <span v-else class="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                                            In Use
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div v-if="Object.keys(filteredColumnLineage).length === 0" class="text-center py-8 text-gray-500">
                            No columns match the current filter
                        </div>
                    </div>
                </div>
            </div>

            <!-- Perspectives Tab -->
            <div v-show="activeTab === 'perspectives'" v-if="enhancedData && enhancedData.analyses && enhancedData.analyses.perspectives">
                <div class="mb-6">
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">Perspectives Analysis</h1>
                    <p class="text-gray-600">Object visibility and perspective usage</p>
                </div>

                <div v-if="!perspectivesData.has_perspectives" class="stat-card">
                    <div class="text-center py-12">
                        <div class="text-6xl mb-4">👁️</div>
                        <h3 class="text-xl font-semibold text-gray-700 mb-2">No Perspectives Defined</h3>
                        <p class="text-gray-600">{{{{ perspectivesData.message }}}}</p>
                    </div>
                </div>

                <div v-else>
                    <!-- Perspectives Summary -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div class="kpi-card">
                            <h3>Total Perspectives</h3>
                            <p class="text-4xl font-bold text-gray-900">{{{{ perspectivesCount }}}}</p>
                        </div>
                        <div class="kpi-card">
                            <h3>Unused Perspectives</h3>
                            <p class="text-4xl font-bold text-yellow-600">{{{{ perspectivesData.unused_perspectives?.length || 0 }}}}</p>
                        </div>
                        <div class="kpi-card">
                            <h3>Active Perspectives</h3>
                            <p class="text-4xl font-bold text-green-600">{{{{ perspectivesCount - (perspectivesData.unused_perspectives?.length || 0) }}}}</p>
                        </div>
                    </div>

                    <!-- Perspectives Details -->
                    <div class="stat-card">
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">Perspective Details</h2>
                        <div class="space-y-4">
                            <div v-for="perspective in perspectivesData.perspectives" :key="perspective.name" class="border border-gray-200 rounded-lg p-4">
                                <div class="flex items-center justify-between mb-3">
                                    <h3 class="text-lg font-semibold text-gray-900">{{{{ perspective.name }}}}</h3>
                                    <span v-if="perspective.total_objects === 0" class="px-3 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800">
                                        UNUSED
                                    </span>
                                    <span v-else class="px-3 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                                        ACTIVE
                                    </span>
                                </div>
                                <div class="grid grid-cols-4 gap-4 text-sm">
                                    <div class="text-center p-3 bg-blue-50 rounded">
                                        <p class="text-gray-600 mb-1">Tables</p>
                                        <p class="text-2xl font-bold text-blue-600">{{{{ perspective.table_count }}}}</p>
                                    </div>
                                    <div class="text-center p-3 bg-green-50 rounded">
                                        <p class="text-gray-600 mb-1">Columns</p>
                                        <p class="text-2xl font-bold text-green-600">{{{{ perspective.column_count }}}}</p>
                                    </div>
                                    <div class="text-center p-3 bg-purple-50 rounded">
                                        <p class="text-gray-600 mb-1">Measures</p>
                                        <p class="text-2xl font-bold text-purple-600">{{{{ perspective.measure_count }}}}</p>
                                    </div>
                                    <div class="text-center p-3 bg-gray-50 rounded">
                                        <p class="text-gray-600 mb-1">Total Objects</p>
                                        <p class="text-2xl font-bold text-gray-900">{{{{ perspective.total_objects }}}}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Command Palette -->
        <div v-if="showCommandPalette" v-cloak class="command-palette" @click.self="showCommandPalette = false">
            <div class="command-palette-content">
                <div class="p-4 border-b border-gray-200">
                    <input
                        v-model="commandQuery"
                        type="text"
                        placeholder="Type a command..."
                        class="w-full px-4 py-2 border-0 focus:ring-0 text-lg"
                        @keydown.esc="showCommandPalette = false"
                        ref="commandInput"
                    />
                </div>
                <div class="p-2 max-h-96 overflow-y-auto">
                    <div
                        v-for="cmd in filteredCommands"
                        :key="cmd.name"
                        @click="executeCommand(cmd)"
                        class="p-3 hover:bg-gray-100 cursor-pointer rounded transition"
                    >
                        <div class="font-semibold text-gray-900">{{{{ cmd.name }}}}</div>
                        <div class="text-sm text-gray-600">{{{{ cmd.description }}}}</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""

    def _get_vue_app_script(self, data_json_str: str) -> str:
        """Get the Vue 3 application JavaScript."""
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

                    // Dependencies tab
                    selectedDependencyKey: null,
                    dependencySearchQuery: '',
                    dependencySubTab: 'measures',
                    selectedColumnKey: null,
                    columnSearchQuery: '',
                    collapsedDependencyFolders: {{}},
                    collapsedUsedByFolders: {{}},

                    // Enhanced analysis tabs
                    bpaSeverityFilter: 'all',
                    bpaCategoryFilter: 'all',
                    collapsedBpaObjectGroups: {{}},
                    dataTypeImpactFilter: 'all',
                    daxSeverityFilter: 'all',
                    daxTypeFilter: 'all',
                    daxQualitySortBy: 'complexity',
                    daxQualitySortDesc: true,

                    // Naming conventions
                    namingSeverityFilter: 'all',
                    namingTypeFilter: 'all',

                    // Column lineage
                    lineageSearchQuery: '',
                    lineageUsageFilter: 'all',

                    commands: [
                        {{ name: 'Go to Summary', description: 'View summary and insights', action: () => this.activeTab = 'summary' }},
                        {{ name: 'Go to Model', description: 'Explore model tables', action: () => this.activeTab = 'model' }},
                        {{ name: 'Go to Report', description: 'View report visuals', action: () => this.activeTab = 'report' }},
                        {{ name: 'Go to Dependencies', description: 'Analyze dependencies', action: () => this.activeTab = 'dependencies' }},
                        {{ name: 'Go to Usage', description: 'View unused objects', action: () => this.activeTab = 'usage' }},
                        {{ name: 'Go to Best Practices', description: 'View BPA violations', action: () => this.activeTab = 'best-practices' }},
                        {{ name: 'Go to Data Quality', description: 'View data type and cardinality analysis', action: () => this.activeTab = 'data-quality' }},
                        {{ name: 'Go to Code Quality', description: 'View DAX quality metrics', action: () => this.activeTab = 'code-quality' }},
                        {{ name: 'Export to CSV', description: 'Export model data to CSV', action: () => this.exportToCSV() }},
                        {{ name: 'Export to JSON', description: 'Export all data to JSON', action: () => this.exportToJSON() }},
                        {{ name: 'Toggle Dark Mode', description: 'Switch light/dark theme', action: () => this.toggleDarkMode() }}
                    ]
                }};
            }},

            computed: {{
                statistics() {{
                    const summary = this.dependencies.summary || {{}};

                    // Calculate actual visible visual count (excluding filtered types)
                    let visibleVisualCount = 0;
                    if (this.reportData && this.reportData.pages) {{
                        this.reportData.pages.forEach(page => {{
                            visibleVisualCount += this.getVisibleVisualCount(page.visuals || []);
                        }});
                    }}

                    return {{
                        total_tables: summary.total_tables || 0,
                        total_measures: summary.total_measures || 0,
                        total_columns: summary.total_columns || 0,
                        total_relationships: summary.total_relationships || 0,
                        total_pages: summary.total_pages || 0,
                        total_visuals: visibleVisualCount || summary.total_visuals || 0,
                        unused_measures: summary.unused_measures || 0,
                        unused_columns: summary.unused_columns || 0
                    }};
                }},

                modelArchitecture() {{
                    const tables = this.modelData.tables || [];
                    const factTables = tables.filter(t => t.name.toLowerCase().startsWith('f ')).length;
                    const dimTables = tables.filter(t => t.name.toLowerCase().startsWith('d ')).length;
                    return factTables > 0 && dimTables > 0 ? 'Star Schema' : 'Custom';
                }},

                tableDistribution() {{
                    const tables = this.modelData.tables || [];
                    const total = tables.length || 1;
                    const fact = tables.filter(t => t.name.toLowerCase().startsWith('f ')).length;
                    const dimension = tables.filter(t => t.name.toLowerCase().startsWith('d ')).length;
                    return {{
                        fact: ((fact / total) * 100).toFixed(1),
                        dimension: ((dimension / total) * 100).toFixed(1)
                    }};
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
                        return {{ usedByMeasures: [], usedByFieldParams: [], visualUsage: [] }};
                    }}

                    const deps = this.dependencies;
                    const key = this.selectedColumnKey;

                    const usedByMeasures = deps.column_to_measure?.[key] || [];
                    const usedByFieldParams = deps.column_to_field_params?.[key] || [];
                    const visualUsage = this.findColumnInVisuals(key);

                    return {{ usedByMeasures, usedByFieldParams, visualUsage }};
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

                fieldParametersList() {{
                    const fieldParams = [];
                    const fieldParamMap = this.dependencies.field_param_to_columns || {{}};

                    // Iterate through field parameters and build the list
                    Object.keys(fieldParamMap).forEach(fpKey => {{
                        const columns = fieldParamMap[fpKey] || [];

                        // Parse the field parameter key to get table and name
                        // Format is typically: TableName[FieldParamName]
                        const match = fpKey.match(/^(.+?)\[(.+?)\]$/);
                        if (match) {{
                            fieldParams.push({{
                                name: match[2],
                                table: match[1],
                                fullName: fpKey,
                                columns: columns
                            }});
                        }} else {{
                            // Fallback if format doesn't match
                            fieldParams.push({{
                                name: fpKey,
                                table: '',
                                fullName: fpKey,
                                columns: columns
                            }});
                        }}
                    }});

                    // Sort by table name, then by field parameter name
                    return fieldParams.sort((a, b) => {{
                        if (a.table !== b.table) {{
                            return a.table.localeCompare(b.table);
                        }}
                        return a.name.localeCompare(b.name);
                    }});
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

                cardinalityWarnings() {{
                    return this.enhancedData?.analyses?.cardinality?.cardinality_warnings || [];
                }},

                filteredDataTypeIssues() {{
                    return this.dataTypeIssues.filter(issue => {{
                        return this.dataTypeImpactFilter === 'all' || issue.impact === this.dataTypeImpactFilter;
                    }});
                }},

                // Enhanced Analysis - DAX Quality
                daxQualityIssues() {{
                    return this.enhancedData?.analyses?.dax_quality?.quality_issues || [];
                }},

                daxQualityIssuesCount() {{
                    return this.daxQualityIssues.length;
                }},

                daxSummary() {{
                    return this.enhancedData?.analyses?.dax_quality?.summary || {{}};
                }},

                filteredDaxQualityIssues() {{
                    return this.daxQualityIssues.filter(issue => {{
                        const severityMatch = this.daxSeverityFilter === 'all' || issue.severity === this.daxSeverityFilter;
                        const typeMatch = this.daxTypeFilter === 'all' || issue.type === this.daxTypeFilter;
                        return severityMatch && typeMatch;
                    }});
                }},

                sortedDaxQualityIssues() {{
                    const issues = [...this.filteredDaxQualityIssues];
                    const sortBy = this.daxQualitySortBy;
                    const desc = this.daxQualitySortDesc;

                    issues.sort((a, b) => {{
                        let aVal, bVal;

                        if (sortBy === 'complexity') {{
                            aVal = a.complexity_score || 0;
                            bVal = b.complexity_score || 0;
                            return desc ? bVal - aVal : aVal - bVal;
                        }} else if (sortBy === 'type') {{
                            aVal = a.type || '';
                            bVal = b.type || '';
                        }} else if (sortBy === 'table') {{
                            aVal = a.table || '';
                            bVal = b.table || '';
                        }} else if (sortBy === 'measure') {{
                            aVal = a.measure || '';
                            bVal = b.measure || '';
                        }}

                        if (typeof aVal === 'string') {{
                            return desc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
                        }}
                        return 0;
                    }});

                    return issues;
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

                // Column Lineage
                columnLineage() {{
                    return this.enhancedData?.analyses?.column_lineage || {{}};
                }},

                filteredColumnLineage() {{
                    const allColumns = this.columnLineage;
                    const query = this.lineageSearchQuery.toLowerCase();

                    return Object.fromEntries(
                        Object.entries(allColumns).filter(([key, lineage]) => {{
                            // Search filter
                            const searchMatch = !query ||
                                lineage.table.toLowerCase().includes(query) ||
                                lineage.column.toLowerCase().includes(query);

                            // Usage filter
                            let usageMatch = true;
                            if (this.lineageUsageFilter === 'orphan') {{
                                usageMatch = lineage.is_orphan;
                            }} else if (this.lineageUsageFilter === 'calculated') {{
                                usageMatch = lineage.is_calculated;
                            }} else if (this.lineageUsageFilter === 'high-usage') {{
                                usageMatch = lineage.usage_score >= 3;
                            }}

                            return searchMatch && usageMatch;
                        }})
                    );
                }},

                orphanColumnsCount() {{
                    return Object.values(this.columnLineage).filter(l => l.is_orphan).length;
                }},

                calculatedColumnsCount() {{
                    return Object.values(this.columnLineage).filter(l => l.is_calculated).length;
                }},

                highUsageColumnsCount() {{
                    return Object.values(this.columnLineage).filter(l => l.usage_score >= 3).length;
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
                    if (severity === 'ERROR') return 'bg-red-100 text-red-800';
                    if (severity === 'WARNING') return 'bg-yellow-100 text-yellow-800';
                    if (severity === 'INFO') return 'bg-blue-100 text-blue-800';
                    return 'bg-gray-100 text-gray-800';
                }},

                severityBadgeClass(severity) {{
                    if (severity === 'ERROR') return 'bg-red-100 text-red-800';
                    if (severity === 'WARNING') return 'bg-yellow-100 text-yellow-800';
                    if (severity === 'INFO') return 'bg-blue-100 text-blue-800';
                    return 'bg-gray-100 text-gray-800';
                }},

                impactBadgeClass(impact) {{
                    if (impact === 'HIGH') return 'bg-red-100 text-red-800';
                    if (impact === 'MEDIUM') return 'bg-yellow-100 text-yellow-800';
                    if (impact === 'LOW') return 'bg-green-100 text-green-800';
                    return 'bg-gray-100 text-gray-800';
                }},

                complexityBadgeClass(score) {{
                    if (score > 20) return 'bg-red-100 text-red-800';
                    if (score > 15) return 'bg-orange-100 text-orange-800';
                    if (score > 10) return 'bg-yellow-100 text-yellow-800';
                    return 'bg-green-100 text-green-800';
                }},

                usageScoreBadgeClass(score) {{
                    if (score === 0) return 'bg-red-100 text-red-800';
                    if (score <= 2) return 'bg-yellow-100 text-yellow-800';
                    if (score <= 5) return 'bg-blue-100 text-blue-800';
                    return 'bg-green-100 text-green-800';
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

                toggleBpaObjectGroup(objectType) {{
                    this.collapsedBpaObjectGroups[objectType] = !this.collapsedBpaObjectGroups[objectType];
                }},

                sortDaxQuality(column) {{
                    if (this.daxQualitySortBy === column) {{
                        this.daxQualitySortDesc = !this.daxQualitySortDesc;
                    }} else {{
                        this.daxQualitySortBy = column;
                        this.daxQualitySortDesc = column === 'complexity'; // Default descending for complexity
                    }}
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
                        const match = colRef.match(/['\"]([^'\"]+)['\"]\.['\"]*([^'\"]+)['\"]*$/);
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
                        const match = measureName.match(/^(.+?)\[(.+?)\]$/);
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
                }}
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
                Object.keys(this.measuresByFolder).forEach(folderName => {{
                    this.collapsedFolders[folderName] = true;
                }});

                // Collapse dependency folders (columns grouped by table)
                Object.keys(this.filteredColumnsForDependency).forEach(tableName => {{
                    this.collapsedDependencyFolders[tableName] = true;
                }});

                // Collapse visual type groups
                if (this.reportData && this.reportData.pages) {{
                    this.reportData.pages.forEach(page => {{
                        const visualGroups = this.visualsByType(page.visuals || []);
                        Object.keys(visualGroups).forEach(visualType => {{
                            this.collapsedVisualGroups[visualType] = true;
                        }});
                    }});
                }}

                // Start with unused measure folders expanded (set to false)
                Object.keys(this.unusedMeasuresByFolder).forEach(folderName => {{
                    this.collapsedUnusedMeasureFolders[folderName] = false;
                }});

                // Start with unused column tables expanded (set to false)
                Object.keys(this.unusedColumnsByTable).forEach(tableName => {{
                    this.collapsedUnusedColumnTables[tableName] = false;
                }});

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
            }}
        }}).mount('#app');
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


        return html_content
