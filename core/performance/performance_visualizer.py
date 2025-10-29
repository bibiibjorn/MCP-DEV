"""
Performance Visualization Generator.

This module generates interactive HTML visualizations for query performance analysis,
including waterfall charts, query plan trees, and comparison charts.
"""

import logging
from typing import Any, Dict, List
import json

logger = logging.getLogger(__name__)


class PerformanceVisualizer:
    """
    Generator for interactive HTML performance visualizations.

    Creates standalone HTML files with embedded D3.js or Chart.js visualizations.
    """

    def __init__(self):
        """Initialize performance visualizer."""
        self.d3_version = "7.8.5"  # D3.js version to use

    def generate_waterfall_chart(
        self,
        analysis_result: Dict[str, Any],
        title: str = "Query Performance Breakdown",
    ) -> str:
        """
        Generate HTML waterfall chart for SE/FE timing breakdown.

        Args:
            analysis_result: Result from PerformanceAnalyzerV2.analyze_query_detailed()
            title: Chart title

        Returns:
            HTML string with embedded waterfall chart
        """
        summary = analysis_result.get("summary", {})
        runs = analysis_result.get("runs", [])

        se_ms = summary.get("avg_se_ms", 0.0)
        fe_ms = summary.get("avg_fe_ms", 0.0)
        total_ms = summary.get("avg_execution_ms", 0.0)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v{self.d3_version}.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            padding: 15px;
            background: #f9f9f9;
            border-left: 4px solid #4CAF50;
            border-radius: 4px;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
        .chart {{
            margin: 30px 0;
        }}
        .se-bar {{
            fill: #2196F3;
        }}
        .fe-bar {{
            fill: #FF9800;
        }}
        .total-bar {{
            fill: #4CAF50;
        }}
        .axis text {{
            font-size: 12px;
        }}
        .bar-label {{
            font-size: 14px;
            font-weight: 500;
            fill: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .cold-cache {{
            background: #e3f2fd;
        }}
        .warm-cache {{
            background: #fff3e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="summary">
            <div class="metric">
                <div class="metric-label">Total Time</div>
                <div class="metric-value">{total_ms:.2f} ms</div>
            </div>
            <div class="metric">
                <div class="metric-label">Storage Engine</div>
                <div class="metric-value">{se_ms:.2f} ms ({summary.get('se_percent', 0):.1f}%)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Formula Engine</div>
                <div class="metric-value">{fe_ms:.2f} ms ({summary.get('fe_percent', 0):.1f}%)</div>
            </div>
        </div>

        <div class="chart" id="waterfall"></div>

        <h2>Execution Runs</h2>
        <table>
            <thead>
                <tr>
                    <th>Run</th>
                    <th>Cache State</th>
                    <th>Total (ms)</th>
                    <th>SE (ms)</th>
                    <th>FE (ms)</th>
                    <th>Rows</th>
                </tr>
            </thead>
            <tbody>
"""

        # Add run data to table
        for run in runs:
            cache_class = "cold-cache" if run.get("cache_state") == "cold" else "warm-cache"
            html += f"""
                <tr class="{cache_class}">
                    <td>{run.get('run', 0)}</td>
                    <td>{run.get('cache_state', 'unknown')}</td>
                    <td>{run.get('execution_time_ms', 0):.2f}</td>
                    <td>{run.get('storage_engine_ms', 0):.2f}</td>
                    <td>{run.get('formula_engine_ms', 0):.2f}</td>
                    <td>{run.get('row_count', 0):,}</td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>
    </div>

    <script>
        // Waterfall chart data
        const data = [
            {{ label: 'Storage Engine', value: {se_ms}, color: '#2196F3' }},
            {{ label: 'Formula Engine', value: {fe_ms}, color: '#FF9800' }}
        ];

        // Chart dimensions
        const margin = {{ top: 20, right: 30, bottom: 40, left: 120 }};
        const width = 800 - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select('#waterfall')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

        // Scales
        const x = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.value)])
            .range([0, width]);

        const y = d3.scaleBand()
            .domain(data.map(d => d.label))
            .range([0, height])
            .padding(0.2);

        // Bars
        svg.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', 0)
            .attr('y', d => y(d.label))
            .attr('width', d => x(d.value))
            .attr('height', y.bandwidth())
            .attr('fill', d => d.color);

        // Bar labels
        svg.selectAll('.bar-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.value) - 10)
            .attr('y', d => y(d.label) + y.bandwidth() / 2)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'end')
            .text(d => d.value.toFixed(2) + ' ms');

        // Axes
        svg.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0,${{height}})`)
            .call(d3.axisBottom(x).ticks(5).tickFormat(d => d + ' ms'));

        svg.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y));
    </script>
</body>
</html>
"""
        return html

    def generate_comparison_chart(
        self,
        comparison_result: Dict[str, Any],
        title: str = "Performance Comparison",
    ) -> str:
        """
        Generate HTML comparison chart for before/after analysis.

        Args:
            comparison_result: Result from PerformanceAnalyzerV2.compare_query_performance()
            title: Chart title

        Returns:
            HTML string with embedded comparison chart
        """
        before_summary = comparison_result.get("before", {}).get("summary", {})
        after_summary = comparison_result.get("after", {}).get("summary", {})
        improvement = comparison_result.get("improvement", {})

        before_total = before_summary.get("avg_execution_ms", 0.0)
        after_total = after_summary.get("avg_execution_ms", 0.0)
        improvement_percent = improvement.get("total_percent", 0.0)
        verdict = improvement.get("verdict", "Unknown")

        verdict_color = "#4CAF50" if improvement_percent > 0 else "#f44336"

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v{self.d3_version}.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .verdict {{
            background: {verdict_color};
            color: white;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
            text-align: center;
        }}
        .verdict-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .verdict-details {{
            font-size: 1.2em;
        }}
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin: 30px 0;
        }}
        .metric-box {{
            padding: 20px;
            background: #f9f9f9;
            border-radius: 4px;
        }}
        .metric-box h3 {{
            margin-top: 0;
            color: #666;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .chart {{
            margin: 30px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="verdict">
            <div class="verdict-title">{verdict}</div>
            <div class="verdict-details">
                {"Improvement" if improvement_percent > 0 else "Regression"}: {abs(improvement_percent):.1f}%
                ({improvement.get('total_ms', 0):.2f} ms faster)
            </div>
        </div>

        <div class="comparison">
            <div class="metric-box">
                <h3>Before Optimization</h3>
                <div class="metric-value">{before_total:.2f} ms</div>
                <div style="margin-top: 10px;">
                    SE: {before_summary.get('avg_se_ms', 0):.2f} ms<br>
                    FE: {before_summary.get('avg_fe_ms', 0):.2f} ms
                </div>
            </div>
            <div class="metric-box">
                <h3>After Optimization</h3>
                <div class="metric-value">{after_total:.2f} ms</div>
                <div style="margin-top: 10px;">
                    SE: {after_summary.get('avg_se_ms', 0):.2f} ms<br>
                    FE: {after_summary.get('avg_fe_ms', 0):.2f} ms
                </div>
            </div>
        </div>

        <div class="chart" id="comparison"></div>
    </div>

    <script>
        // Comparison data
        const data = [
            {{
                category: 'Before',
                total: {before_total},
                se: {before_summary.get('avg_se_ms', 0)},
                fe: {before_summary.get('avg_fe_ms', 0)}
            }},
            {{
                category: 'After',
                total: {after_total},
                se: {after_summary.get('avg_se_ms', 0)},
                fe: {after_summary.get('avg_fe_ms', 0)}
            }}
        ];

        // Chart dimensions
        const margin = {{ top: 20, right: 30, bottom: 40, left: 60 }};
        const width = 600 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select('#comparison')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

        // Scales
        const x0 = d3.scaleBand()
            .domain(data.map(d => d.category))
            .range([0, width])
            .padding(0.2);

        const x1 = d3.scaleBand()
            .domain(['se', 'fe'])
            .range([0, x0.bandwidth()])
            .padding(0.05);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.total)])
            .nice()
            .range([height, 0]);

        const color = d3.scaleOrdinal()
            .domain(['se', 'fe'])
            .range(['#2196F3', '#FF9800']);

        // Bars
        svg.selectAll('.category')
            .data(data)
            .enter()
            .append('g')
            .attr('class', 'category')
            .attr('transform', d => `translate(${{x0(d.category)}},0)`)
            .selectAll('rect')
            .data(d => [{{ key: 'se', value: d.se }}, {{ key: 'fe', value: d.fe }}])
            .enter()
            .append('rect')
            .attr('x', d => x1(d.key))
            .attr('y', d => y(d.value))
            .attr('width', x1.bandwidth())
            .attr('height', d => height - y(d.value))
            .attr('fill', d => color(d.key));

        // Axes
        svg.append('g')
            .attr('transform', `translate(0,${{height}})`)
            .call(d3.axisBottom(x0));

        svg.append('g')
            .call(d3.axisLeft(y).tickFormat(d => d + ' ms'));

        // Legend
        const legend = svg.append('g')
            .attr('transform', `translate(${{width - 100}}, 0)`);

        legend.append('rect')
            .attr('width', 20)
            .attr('height', 20)
            .attr('fill', '#2196F3');
        legend.append('text')
            .attr('x', 25)
            .attr('y', 15)
            .text('SE');

        legend.append('rect')
            .attr('y', 30)
            .attr('width', 20)
            .attr('height', 20)
            .attr('fill', '#FF9800');
        legend.append('text')
            .attr('x', 25)
            .attr('y', 45)
            .text('FE');
    </script>
</body>
</html>
"""
        return html

    def generate_batch_profiling_report(
        self,
        batch_result: Dict[str, Any],
        title: str = "Batch Query Profiling Report",
    ) -> str:
        """
        Generate HTML report for batch profiling results.

        Args:
            batch_result: Result from PerformanceAnalyzerV2.batch_profile_queries()
            title: Report title

        Returns:
            HTML string with embedded batch profiling report
        """
        queries = batch_result.get("queries", [])
        comparative = batch_result.get("comparative_analysis", {})
        bottlenecks = comparative.get("top_bottlenecks", [])

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v{self.d3_version}.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .bottleneck {{
            background: #ffebee;
            border-left: 4px solid #f44336;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .bottleneck-rank {{
            font-weight: bold;
            color: #f44336;
        }}
        .chart {{
            margin: 30px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <h2>Top Performance Bottlenecks</h2>
"""

        # Add bottleneck cards
        for bottleneck in bottlenecks[:5]:
            html += f"""
        <div class="bottleneck">
            <span class="bottleneck-rank">#{bottleneck.get('rank', 0)}</span> -
            <strong>{bottleneck.get('query_name', 'Unknown')}</strong>
            <div style="margin-top: 10px;">
                Total: {bottleneck.get('total_ms', 0):.2f} ms |
                SE: {bottleneck.get('se_ms', 0):.2f} ms |
                FE: {bottleneck.get('fe_ms', 0):.2f} ms |
                Primary Bottleneck: {bottleneck.get('primary_bottleneck', 'Unknown')}
            </div>
        </div>
"""

        html += """
        <div class="chart" id="chart"></div>

        <h2>All Queries</h2>
        <table>
            <thead>
                <tr>
                    <th>Query Name</th>
                    <th>Total (ms)</th>
                    <th>SE (ms)</th>
                    <th>FE (ms)</th>
                    <th>SE %</th>
                    <th>FE %</th>
                </tr>
            </thead>
            <tbody>
"""

        # Add query rows
        for query in queries:
            summary = query.get("summary", {})
            html += f"""
                <tr>
                    <td>{query.get('query_name', 'Unknown')}</td>
                    <td>{summary.get('avg_execution_ms', 0):.2f}</td>
                    <td>{summary.get('avg_se_ms', 0):.2f}</td>
                    <td>{summary.get('avg_fe_ms', 0):.2f}</td>
                    <td>{summary.get('se_percent', 0):.1f}%</td>
                    <td>{summary.get('fe_percent', 0):.1f}%</td>
                </tr>
"""

        # Prepare chart data
        chart_data = []
        for query in queries:
            summary = query.get("summary", {})
            chart_data.append({
                "name": query.get("query_name", "Unknown"),
                "total": summary.get("avg_execution_ms", 0),
                "se": summary.get("avg_se_ms", 0),
                "fe": summary.get("avg_fe_ms", 0),
            })

        chart_data_json = json.dumps(chart_data)

        html += f"""
            </tbody>
        </table>
    </div>

    <script>
        // Chart data
        const data = {chart_data_json};

        // Chart dimensions
        const margin = {{ top: 20, right: 30, bottom: 100, left: 60 }};
        const width = 1200 - margin.left - margin.right;
        const height = 400 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select('#chart')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${{margin.left}},${{margin.top}})`);

        // Scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.name))
            .range([0, width])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.total)])
            .nice()
            .range([height, 0]);

        // Bars
        svg.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('y', d => y(d.total))
            .attr('width', x.bandwidth())
            .attr('height', d => height - y(d.total))
            .attr('fill', '#4CAF50');

        // Axes
        svg.append('g')
            .attr('transform', `translate(0,${{height}})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('transform', 'rotate(-45)')
            .style('text-anchor', 'end');

        svg.append('g')
            .call(d3.axisLeft(y).tickFormat(d => d + ' ms'));

        // Y-axis label
        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0 - margin.left)
            .attr('x', 0 - (height / 2))
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .text('Execution Time (ms)');
    </script>
</body>
</html>
"""
        return html

    def export_visualization(self, html_content: str, output_path: str) -> bool:
        """
        Export HTML visualization to file.

        Args:
            html_content: HTML content to export
            output_path: Path to output file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Visualization exported to {output_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to export visualization: {exc}")
            return False
