"""
Filter Context Visualizer - Generate visual diagrams of context flow

Supports:
- Text-based ASCII diagrams
- Mermaid diagrams for markdown
- Interactive HTML visualizations with D3.js
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .context_analyzer import ContextFlowExplanation, TransitionType

logger = logging.getLogger(__name__)


class FilterContextVisualizer:
    """
    Generate visual representations of filter context flow

    Output formats:
    - text: ASCII art diagram
    - mermaid: Mermaid flowchart syntax
    - html: Interactive D3.js visualization
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize visualizer

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.highlight_performance = self.config.get("highlight_performance_issues", True)
        self.include_legend = self.config.get("include_legend", True)

    def generate_text_diagram(
        self,
        context_analysis: ContextFlowExplanation
    ) -> str:
        """
        Generate text-based ASCII diagram

        Args:
            context_analysis: Context analysis result

        Returns:
            ASCII diagram as string
        """
        lines = []

        # Header
        lines.append("╔" + "═" * 60 + "╗")
        lines.append("║" + " DAX Context Flow Diagram".center(60) + "║")
        lines.append("╠" + "═" * 60 + "╣")

        # Initial context
        lines.append("║ Initial State: Filter Context                            ║")
        lines.append("╚" + "═" * 60 + "╝")

        # Process transitions
        for i, transition in enumerate(context_analysis.transitions, 1):
            lines.append("    │")
            lines.append("    ↓")

            # Transition box
            lines.append("┌" + "─" * 60 + "┐")

            trans_label = f"Transition {i}: {transition.function}"
            if self.highlight_performance and transition.performance_impact.value != "low":
                trans_label += f" ⚠️ {transition.performance_impact.value.upper()}"

            lines.append("│ " + trans_label.ljust(59) + "│")
            lines.append("│ " + f"Type: {transition.type.value}".ljust(59) + "│")

            if transition.measure_name:
                lines.append("│ " + f"Measure: [{transition.measure_name}]".ljust(59) + "│")

            lines.append("│ " + "─" * 59 + "│")

            # Wrap explanation
            explanation_lines = self._wrap_text(transition.explanation, 57)
            for exp_line in explanation_lines:
                lines.append("│ " + exp_line.ljust(59) + "│")

            lines.append("└" + "─" * 60 + "┘")

        # Final context
        lines.append("    │")
        lines.append("    ↓")
        lines.append("╔" + "═" * 60 + "╗")
        lines.append("║ Final Context: Modified Filter Context                   ║")
        lines.append("╚" + "═" * 60 + "╝")

        # Add legend
        if self.include_legend:
            lines.append("")
            lines.append("Legend:")
            lines.append("  ⚠️ MEDIUM/HIGH = Performance impact warning")
            lines.append("  Filter Context = Table-level filters applied")
            lines.append("  Row Context = Iteration over table rows")

        return "\n".join(lines)

    def generate_mermaid_diagram(
        self,
        context_analysis: ContextFlowExplanation
    ) -> str:
        """
        Generate Mermaid flowchart diagram

        Args:
            context_analysis: Context analysis result

        Returns:
            Mermaid diagram syntax
        """
        lines = ["```mermaid", "graph TD"]

        # Start node
        lines.append('    A["Initial Filter Context"]')

        # Generate nodes for each transition
        prev_node = "A"

        for i, transition in enumerate(context_analysis.transitions, 1):
            node_id = f"T{i}"

            # Node label
            label = f"{transition.function}"
            if transition.measure_name:
                label += f"<br/>[{transition.measure_name}]"

            # Style based on performance impact
            if self.highlight_performance and transition.performance_impact.value != "low":
                lines.append(f'    {node_id}["{label}"]:::warning')
            else:
                lines.append(f'    {node_id}["{label}"]')

            # Connect to previous node
            edge_label = transition.type.value.replace("_", " ").title()
            lines.append(f'    {prev_node} -->|{edge_label}| {node_id}')

            prev_node = node_id

        # End node
        lines.append(f'    {prev_node} --> Z["Modified Filter Context"]')

        # Add styling
        if self.highlight_performance:
            lines.append("    classDef warning fill:#ff9,stroke:#f66,stroke-width:2px")

        lines.append("```")

        return "\n".join(lines)

    def generate_html_visualization(
        self,
        context_analysis: ContextFlowExplanation,
        output_path: str
    ) -> str:
        """
        Generate interactive HTML visualization with D3.js

        Args:
            context_analysis: Context analysis result
            output_path: Path to save HTML file

        Returns:
            Path to generated HTML file
        """
        try:
            html_content = self._generate_html_content(context_analysis)

            # Write to file
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html_content, encoding="utf-8")

            logger.info(f"Generated HTML visualization: {output_path}")

            return str(path)

        except Exception as e:
            logger.error(f"Error generating HTML visualization: {e}", exc_info=True)
            raise

    def _generate_html_content(self, context_analysis: ContextFlowExplanation) -> str:
        """Generate HTML content with D3.js visualization"""

        # Prepare data for JavaScript
        transitions_json = str(context_analysis.to_dict()["transitions"])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DAX Context Flow Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #0078d4;
            padding-bottom: 10px;
        }}
        .summary {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            border-left: 4px solid #0078d4;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            flex: 1;
            background: #fff;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #ddd;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #0078d4;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        #visualization {{
            margin: 30px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            min-height: 400px;
        }}
        .node {{
            cursor: pointer;
        }}
        .node rect {{
            stroke: #333;
            stroke-width: 2px;
            fill: #fff;
        }}
        .node.calculate rect {{
            fill: #e3f2fd;
        }}
        .node.measure rect {{
            fill: #fff3e0;
        }}
        .node.iterator rect {{
            fill: #f3e5f5;
        }}
        .node.warning rect {{
            fill: #ffebee;
            stroke: #f44336;
        }}
        .node text {{
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            pointer-events: none;
        }}
        .link {{
            fill: none;
            stroke: #999;
            stroke-width: 2px;
        }}
        .arrow {{
            fill: #999;
        }}
        .tooltip {{
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 300px;
        }}
        .details {{
            margin-top: 30px;
        }}
        .transition-card {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        .transition-card h3 {{
            margin-top: 0;
            color: #0078d4;
        }}
        .impact-low {{ color: #4caf50; }}
        .impact-medium {{ color: #ff9800; }}
        .impact-high {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 DAX Context Flow Analysis</h1>

        <div class="summary">
            <strong>Summary:</strong><br>
            {context_analysis.summary.replace(chr(10), '<br>')}
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(context_analysis.transitions)}</div>
                <div class="stat-label">Transitions</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{context_analysis.complexity_score}</div>
                <div class="stat-label">Complexity Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{context_analysis.max_nesting_level}</div>
                <div class="stat-label">Max Nesting</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(context_analysis.warnings)}</div>
                <div class="stat-label">Warnings</div>
            </div>
        </div>

        <div id="visualization"></div>

        <div class="details">
            <h2>Transition Details</h2>
            {''.join([
                f'''<div class="transition-card">
                    <h3>Transition {i+1}: {t.function}</h3>
                    <p><strong>Type:</strong> {t.type.value}</p>
                    {f'<p><strong>Measure:</strong> [{t.measure_name}]</p>' if t.measure_name else ''}
                    <p><strong>Location:</strong> Line {t.line}, Column {t.column}</p>
                    <p><strong>Performance Impact:</strong> <span class="impact-{t.performance_impact.value}">{t.performance_impact.value.upper()}</span></p>
                    <p>{t.explanation}</p>
                </div>'''
                for i, t in enumerate(context_analysis.transitions)
            ])}
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const transitions = {transitions_json};

        // Create visualization
        const width = 1140;
        const height = Math.max(400, transitions.length * 80 + 100);

        const svg = d3.select("#visualization")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        // Create nodes data
        const nodes = [
            {{ id: 0, label: "Initial\\nFilter Context", type: "start", x: width/2, y: 50 }}
        ];

        transitions.forEach((t, i) => {{
            nodes.push({{
                id: i + 1,
                label: t.function + (t.measure_name ? `\\n[${{t.measure_name}}]` : ""),
                type: t.type,
                impact: t.performance_impact,
                explanation: t.explanation,
                x: width/2,
                y: 100 + (i + 1) * 80
            }});
        }});

        nodes.push({{
            id: nodes.length,
            label: "Modified\\nFilter Context",
            type: "end",
            x: width/2,
            y: 100 + (transitions.length + 1) * 80
        }});

        // Draw links
        const links = [];
        for (let i = 0; i < nodes.length - 1; i++) {{
            links.push({{ source: nodes[i], target: nodes[i + 1] }});
        }}

        svg.selectAll(".link")
            .data(links)
            .enter()
            .append("line")
            .attr("class", "link")
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y + 25)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y - 25)
            .attr("marker-end", "url(#arrow)");

        // Arrow marker
        svg.append("defs")
            .append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 8)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("class", "arrow");

        // Draw nodes
        const node = svg.selectAll(".node")
            .data(nodes)
            .enter()
            .append("g")
            .attr("class", d => `node ${{d.type}} ${{d.impact === 'high' || d.impact === 'medium' ? 'warning' : ''}}`)
            .attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);

        node.append("rect")
            .attr("x", -80)
            .attr("y", -25)
            .attr("width", 160)
            .attr("height", 50)
            .attr("rx", 4);

        node.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", ".35em")
            .each(function(d) {{
                const lines = d.label.split("\\n");
                const text = d3.select(this);
                lines.forEach((line, i) => {{
                    text.append("tspan")
                        .attr("x", 0)
                        .attr("dy", i === 0 ? 0 : "1.2em")
                        .text(line);
                }});
            }});

        // Tooltip
        const tooltip = d3.select("#tooltip");

        node.on("mouseover", function(event, d) {{
            if (d.explanation) {{
                tooltip
                    .style("left", event.pageX + 10 + "px")
                    .style("top", event.pageY - 10 + "px")
                    .style("opacity", 1)
                    .html(`<strong>${{d.label.replace("\\n", " ")}}</strong><br>${{d.explanation}}`);
            }}
        }})
        .on("mouseout", function() {{
            tooltip.style("opacity", 0);
        }});
    </script>
</body>
</html>
"""

        return html

    def _wrap_text(self, text: str, width: int) -> list:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines
