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
        self.logger.info(f"Generating Vue 3 HTML report to {abs_output_path}")

        # Create output directory
        os.makedirs(abs_output_path, exist_ok=True)

        # Generate HTML content
        html_content = self._build_html_document(
            model_data,
            report_data,
            dependencies,
            repository_name
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
        repo_name: str
    ) -> str:
        """Build complete HTML document with Vue 3."""
        # Prepare data for JavaScript
        data_json = {
            "model": model_data,
            "report": report_data,
            "dependencies": dependencies,
            "generated": datetime.now().isoformat(),
            "repository_name": repo_name
        }

        # Serialize to JSON string
        data_json_str = json.dumps(data_json, indent=2, ensure_ascii=False)

        # Build complete HTML
        html_content = self._get_vue3_template(data_json_str, repo_name)

        return html_content

    def _get_vue3_template(self, data_json_str: str, repo_name: str) -> str:
        """Get the complete Vue 3 HTML template."""
        escaped_repo_name = html.escape(repo_name)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_repo_name} - PBIP Analysis</title>

    <!-- Vue 3 and D3.js -->
    <script src="https://cdn.jsdelivr.net/npm/vue@3.4.21/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>

    <style>
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
        }}

        .dark-mode #graph-container {{
            background: #1e293b;
            border-color: #475569;
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
    </style>
</head>
<body>
    <div id="app">
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
                                            <div class="font-semibold text-gray-900 mb-1">
                                                {{{{ col.name }}}}
                                                <span v-if="col.is_hidden" class="badge badge-warning ml-2">Hidden</span>
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
                                        <div v-for="measure in selectedTable.measures" :key="measure.name" class="border border-gray-200 rounded p-4">
                                            <div class="flex items-center gap-2 mb-2">
                                                <div class="font-semibold text-gray-900">{{{{ measure.name }}}}</div>
                                                <span class="badge badge-primary text-xs">m Measure</span>
                                                <span v-if="measure.display_folder" class="badge badge-warning text-xs">📁 {{{{ measure.display_folder }}}}</span>
                                                <span v-if="measure.is_hidden" class="badge badge-gray text-xs">Hidden</span>
                                            </div>
                                            <div class="code-block" v-if="measure.expression" v-html="highlightDAX(measure.expression)"></div>
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
                                    <div v-if="getTableVisualUsage(selectedTable.name).length > 0" class="space-y-2">
                                        <div v-for="usage in getTableVisualUsage(selectedTable.name)" :key="usage.visualId" class="border border-gray-200 rounded p-3">
                                            <div class="font-semibold text-sm text-gray-900">{{{{ usage.pageName }}}}</div>
                                            <div class="text-xs text-gray-600">{{{{ usage.visualType }}}} - {{{{ usage.visualId.substring(0, 8) }}}}...</div>
                                        </div>
                                    </div>
                                    <div v-else class="text-gray-500 italic">This table is not used in any visuals</div>
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
                        <input
                            v-model="measuresSearchQuery"
                            type="search"
                            placeholder="Search measures..."
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-blue-500"
                        />
                        <div class="scrollable">
                            <div v-for="(folder, folderName) in measuresByFolder" :key="folderName" class="folder-item">
                                <div class="folder-header" @click="toggleFolder(folderName)">
                                    <div>
                                        <span class="mr-2">📁</span>
                                        <strong>{{{{ folderName || 'No Folder' }}}}</strong>
                                        <span class="ml-2 text-sm opacity-75">({{{{ folder.length }}}})</span>
                                    </div>
                                    <span class="expand-icon">▼</span>
                                </div>
                                <div v-show="!collapsedFolders[folderName]" class="folder-content space-y-3">
                                    <div v-for="measure in folder" :key="measure.key" class="border border-gray-200 rounded p-4 bg-white">
                                        <div class="font-semibold text-gray-900 mb-1">
                                            {{{{ measure.name }}}}
                                            <span class="badge badge-primary ml-2">{{{{ measure.table }}}}</span>
                                            <span v-if="measure.is_hidden" class="badge badge-warning ml-2">Hidden</span>
                                        </div>
                                        <div class="code-block mt-2" v-if="measure.expression" v-html="highlightDAX(measure.expression)"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Relationships View -->
                <div v-show="modelSubTab === 'relationships'">
                    <div class="stat-card">
                        <h2 class="text-2xl font-bold text-gray-900 mb-4">Relationships ({{{{ sortedRelationships.length }}}})</h2>
                        <div v-if="sortedRelationships.length > 0" class="space-y-4">
                            <div v-for="(rel, idx) in sortedRelationships" :key="idx" class="border border-gray-200 rounded p-4 bg-gray-50">
                                <div class="flex items-center justify-between mb-2">
                                    <div class="font-semibold text-gray-900">
                                        {{{{ rel.from_table }}}} → {{{{ rel.to_table }}}}
                                    </div>
                                    <span :class="['badge', rel.is_active !== false ? 'badge-success' : 'badge-gray']">
                                        {{{{ rel.is_active !== false ? 'Active' : 'Inactive' }}}}
                                    </span>
                                </div>
                                <div class="text-sm text-gray-600">
                                    <div>
                                        <strong>From:</strong> {{{{ rel.from_table }}}}[{{{{ rel.from_column }}}}]
                                    </div>
                                    <div>
                                        <strong>To:</strong> {{{{ rel.to_table }}}}[{{{{ rel.to_column }}}}]
                                    </div>
                                    <div class="mt-2">
                                        <span class="badge badge-primary mr-2">{{{{ formatCardinality(rel) }}}}</span>
                                        <span class="badge badge-gray">{{{{ formatCrossFilterDirection(rel) }}}}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else class="text-gray-500 italic">No relationships found in model</div>
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
                                    v-for="(page, idx) in reportData.pages"
                                    :key="idx"
                                    @click="selectedPage = page"
                                    :class="['list-item border-l-4 p-3 cursor-pointer rounded', selectedPage === page ? 'selected' : 'border-gray-300']"
                                >
                                    <div class="font-semibold text-gray-900">{{{{ page.display_name || page.name }}}}</div>
                                    <div class="text-sm text-gray-600">
                                        {{{{ page.visuals?.length || 0 }}}} visuals
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
                                <div v-if="currentDependencyDetails.usedBy.length > 0" class="space-y-2">
                                    <div v-for="user in currentDependencyDetails.usedBy" :key="user" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                        <span class="badge badge-success">Measure</span>
                                        <span class="text-sm text-gray-700">{{{{ user }}}}</span>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used by other measures</div>
                            </div>

                            <!-- Used In Visuals -->
                            <div v-if="reportData">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used In Visuals ({{{{ currentDependencyDetails.visualUsage.length }}}})
                                </h3>
                                <div v-if="currentDependencyDetails.visualUsage.length > 0" class="space-y-2">
                                    <div v-for="usage in currentDependencyDetails.visualUsage" :key="usage.visualId" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                        <span class="badge badge-warning">Visual</span>
                                        <span class="text-sm text-gray-700">{{{{ usage.pageName }}}} - {{{{ usage.visualType }}}}</span>
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

                            <!-- Used By Measures -->
                            <div class="mb-6">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used By Measures ({{{{ currentColumnDependencies.usedByMeasures.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.usedByMeasures.length > 0" class="space-y-2">
                                    <div v-for="measure in currentColumnDependencies.usedByMeasures" :key="measure" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                        <span class="badge badge-success">Measure</span>
                                        <span class="text-sm text-gray-700">{{{{ measure }}}}</span>
                                    </div>
                                </div>
                                <div v-else class="text-gray-500 italic">Not used by any measures</div>
                            </div>

                            <!-- Used In Visuals -->
                            <div v-if="reportData">
                                <h3 class="text-lg font-semibold text-gray-900 mb-3">
                                    Used In Visuals ({{{{ currentColumnDependencies.visualUsage.length }}}})
                                </h3>
                                <div v-if="currentColumnDependencies.visualUsage.length > 0" class="space-y-2">
                                    <div v-for="usage in currentColumnDependencies.visualUsage" :key="usage.visualId" class="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                        <span class="badge badge-warning">Visual</span>
                                        <span class="text-sm text-gray-700">{{{{ usage.pageName }}}} - {{{{ usage.visualType }}}}</span>
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
            <div v-show="activeTab === 'usage'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="stat-card">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Unused Measures</h2>
                    <div v-if="dependencies.unused_measures?.length > 0" class="bg-yellow-50 p-4 rounded mb-4">
                        <strong>Warning:</strong> Found {{{{ dependencies.unused_measures.length }}}} measures not used anywhere.
                    </div>
                    <div v-if="dependencies.unused_measures?.length > 0" class="space-y-2 max-h-96 overflow-y-auto">
                        <div v-for="measure in dependencies.unused_measures.slice(0, 50)" :key="measure" class="p-2 border border-gray-200 rounded text-sm">
                            {{{{ measure }}}}
                        </div>
                        <div v-if="dependencies.unused_measures.length > 50" class="text-gray-500 italic text-sm">
                            ... and {{{{ dependencies.unused_measures.length - 50 }}}} more
                        </div>
                    </div>
                    <div v-else class="text-green-600 font-semibold">✓ All measures are in use!</div>
                </div>

                <div class="stat-card">
                    <h2 class="text-2xl font-bold text-gray-900 mb-4">Unused Columns</h2>
                    <div v-if="dependencies.unused_columns?.length > 0" class="bg-yellow-50 p-4 rounded mb-4">
                        <strong>Warning:</strong> Found {{{{ dependencies.unused_columns.length }}}} columns not used anywhere.
                    </div>
                    <div v-if="dependencies.unused_columns?.length > 0" class="space-y-2 max-h-96 overflow-y-auto">
                        <div v-for="column in dependencies.unused_columns.slice(0, 50)" :key="column" class="p-2 border border-gray-200 rounded text-sm">
                            {{{{ column }}}}
                        </div>
                        <div v-if="dependencies.unused_columns.length > 50" class="text-gray-500 italic text-sm">
                            ... and {{{{ dependencies.unused_columns.length - 50 }}}} more
                        </div>
                    </div>
                    <div v-else class="text-green-600 font-semibold">✓ All columns are in use!</div>
                </div>
            </div>
        </div>

        <!-- Command Palette -->
        <div v-if="showCommandPalette" class="command-palette" @click.self="showCommandPalette = false">
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

    <script>
        const {{ createApp }} = Vue;

        const pbipData = {data_json_str};

        createApp({{
            data() {{
                return {{
                    modelData: pbipData.model || {{}},
                    reportData: pbipData.report || null,
                    dependencies: pbipData.dependencies || {{}},
                    repositoryName: pbipData.repository_name || 'PBIP Repository',

                    activeTab: 'summary',
                    searchQuery: '',
                    darkMode: false,
                    showCommandPalette: false,
                    commandQuery: '',

                    // Model tab
                    selectedTable: null,
                    modelDetailTab: 'columns',
                    modelSearchQuery: '',
                    modelSubTab: 'tables',
                    measuresSearchQuery: '',
                    collapsedFolders: {{}},

                    // Report tab
                    selectedPage: null,
                    collapsedVisualGroups: {{}},

                    // Dependencies tab
                    selectedDependencyKey: null,
                    dependencySearchQuery: '',
                    dependencySubTab: 'measures',
                    selectedColumnKey: null,
                    columnSearchQuery: '',
                    collapsedDependencyFolders: {{}},

                    commands: [
                        {{ name: 'Go to Summary', description: 'View summary and insights', action: () => this.activeTab = 'summary' }},
                        {{ name: 'Go to Model', description: 'Explore model tables', action: () => this.activeTab = 'model' }},
                        {{ name: 'Go to Report', description: 'View report visuals', action: () => this.activeTab = 'report' }},
                        {{ name: 'Go to Dependencies', description: 'Analyze dependencies', action: () => this.activeTab = 'dependencies' }},
                        {{ name: 'Go to Usage', description: 'View unused objects', action: () => this.activeTab = 'usage' }},
                        {{ name: 'Export to CSV', description: 'Export model data to CSV', action: () => this.exportToCSV() }},
                        {{ name: 'Export to JSON', description: 'Export all data to JSON', action: () => this.exportToJSON() }},
                        {{ name: 'Toggle Dark Mode', description: 'Switch light/dark theme', action: () => this.toggleDarkMode() }}
                    ]
                }};
            }},

            computed: {{
                statistics() {{
                    const summary = this.dependencies.summary || {{}};
                    return {{
                        total_tables: summary.total_tables || 0,
                        total_measures: summary.total_measures || 0,
                        total_columns: summary.total_columns || 0,
                        total_relationships: summary.total_relationships || 0,
                        total_pages: summary.total_pages || 0,
                        total_visuals: summary.total_visuals || 0,
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
                        return {{ usedByMeasures: [], visualUsage: [] }};
                    }}

                    const deps = this.dependencies;
                    const key = this.selectedColumnKey;

                    const usedByMeasures = deps.column_to_measure?.[key] || [];
                    const visualUsage = this.findColumnInVisuals(key);

                    return {{ usedByMeasures, visualUsage }};
                }},

                filteredCommands() {{
                    const query = this.commandQuery.toLowerCase();
                    if (!query) return this.commands;

                    return this.commands.filter(cmd =>
                        cmd.name.toLowerCase().includes(query) ||
                        cmd.description.toLowerCase().includes(query)
                    );
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
                }},

                findColumnInVisuals(columnKey) {{
                    if (!this.reportData || !this.reportData.pages) return [];

                    const usage = [];
                    const match = columnKey.match(/(.+?)\\[(.+?)\\]/);
                    if (!match) return usage;

                    const [, tableName, columnName] = match;

                    this.reportData.pages.forEach(page => {{
                        (page.visuals || []).forEach(visual => {{
                            const columns = visual.fields?.columns || [];
                            columns.forEach(c => {{
                                if (c.table === tableName && c.column === columnName) {{
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
                        if (!groups[type]) {{
                            groups[type] = [];
                        }}
                        groups[type].push(visual);
                    }});
                    return groups;
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
                                usage.push({{
                                    pageName: page.display_name || page.name,
                                    visualType: visual.visual_type || 'Unknown',
                                    visualId: visual.id,
                                    visualName: visual.visual_name || 'Unnamed'
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
                if (this.reportData && this.reportData.pages && this.reportData.pages.length > 0) {{
                    this.selectedPage = this.reportData.pages[0];
                }}

                // Initialize all folders as collapsed
                // Collapse measure folders
                Object.keys(this.measuresByFolder).forEach(folderName => {{
                    this.$set(this.collapsedFolders, folderName, true);
                }});

                // Collapse dependency folders (columns grouped by table)
                Object.keys(this.filteredColumnsForDependency).forEach(tableName => {{
                    this.$set(this.collapsedDependencyFolders, tableName, true);
                }});

                // Collapse visual type groups
                if (this.reportData && this.reportData.pages) {{
                    this.reportData.pages.forEach(page => {{
                        const visualGroups = this.visualsByType(page.visuals || []);
                        Object.keys(visualGroups).forEach(visualType => {{
                            this.$set(this.collapsedVisualGroups, visualType, true);
                        }});
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
            }}
        }}).mount('#app');
    </script>
</body>
</html>'''

        return html_content
