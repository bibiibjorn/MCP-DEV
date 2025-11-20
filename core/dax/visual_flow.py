"""
Visual Context Flow Diagram Generator

Generates ASCII and HTML visualizations of DAX context flow
Similar to SQLBI's visual explanations
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FlowStep:
    """Represents a step in the context flow"""
    step_number: int
    description: str
    filter_context: List[str]
    row_context: Optional[str]
    transition_type: Optional[str]  # None, "row_to_filter", "filter_to_row"


class VisualFlowDiagramGenerator:
    """
    Generate visual diagrams of DAX context flow

    Creates both ASCII and HTML visualizations showing:
    - Filter context progression
    - Row context activation/deactivation
    - Context transitions
    - CALCULATE modifications
    """

    def __init__(self):
        """Initialize diagram generator"""
        pass

    def generate_ascii_diagram(self, context_analysis) -> str:
        """
        Generate ASCII diagram of context flow

        Args:
            context_analysis: ContextFlowExplanation from DaxContextAnalyzer

        Returns:
            ASCII diagram string
        """
        try:
            lines = []

            # Header
            lines.append("=" * 80)
            lines.append("  DAX CONTEXT FLOW DIAGRAM")
            lines.append("=" * 80)
            lines.append("")

            # Legend
            lines.append("Legend:")
            lines.append("  [F] = Filter Context")
            lines.append("  [R] = Row Context")
            lines.append("  --> = Context Transition")
            lines.append("  ~~> = Measure Reference (Implicit CALCULATE)")
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

            if not context_analysis.transitions:
                lines.append("No context transitions detected.")
                lines.append("")
                lines.append("[F] Initial Filter Context (from report/slicer)")
                lines.append("     |")
                lines.append("     v")
                lines.append("[Result] Simple calculation, no context changes")
                return "\n".join(lines)

            # Build flow diagram
            current_state = "filter"  # Start in filter context
            step_num = 0

            lines.append("[F] Initial Filter Context")
            lines.append("     |  (Inherited from report visuals and slicers)")
            lines.append("     v")

            for transition in context_analysis.transitions:
                step_num += 1

                if transition.type.value == "explicit_calculate":
                    lines.append(f"     | ")
                    lines.append(f"[{step_num}]  CALCULATE detected")
                    lines.append("     |  --> Context Transition: Row → Filter (if row context exists)")
                    lines.append("     |      Modifies filter context with new filters")
                    lines.append("     v")
                    lines.append("[F] Modified Filter Context")
                    current_state = "filter"

                elif transition.type.value == "iterator":
                    lines.append(f"     | ")
                    lines.append(f"[{step_num}]  {transition.function} (Iterator)")
                    lines.append("     |  Creates Row Context")
                    lines.append("     v")
                    lines.append(f"[R] Row Context Active - Iterating over rows")
                    lines.append("     |  (Each row evaluated separately)")
                    current_state = "row"

                    # Check if there are measure references inside
                    if transition.performance_impact.value != "low":
                        lines.append("     |")
                        lines.append("     | ⚠️  WARNING: Measure references inside iterator")
                        lines.append("     |     Each measure reference causes context transition")
                        lines.append("     |     This happens for EVERY ROW!")
                        lines.append("     |")
                        lines.append("     +---> For each row:")
                        lines.append("     |       [R] Row Context")
                        lines.append("     |         ~~> Implicit CALCULATE (measure ref)")
                        lines.append("     |       [F] Transition to Filter Context")
                        lines.append("     |         (Evaluate measure)")
                        lines.append("     |       [Result] Back to Row Context")
                        lines.append("     |     Loop repeats...")

                    lines.append("     v")

                elif transition.type.value == "implicit_measure":
                    lines.append(f"     | ")
                    lines.append(f"[{step_num}]  Measure Reference: {transition.measure_name or 'Unknown'}")

                    if current_state == "row":
                        lines.append("     |  ~~> Implicit CALCULATE (in row context)")
                        lines.append("     |      Row → Filter transition")
                        lines.append("     v")
                        lines.append("[F] Filter Context (from current row)")
                        lines.append("     |  (Evaluate measure)")
                        lines.append("     v")
                        lines.append("[R] Return to Row Context")
                    else:
                        lines.append("     |  ~~> Implicit CALCULATE")
                        lines.append("     |      Already in filter context - uses current filters")
                        lines.append("     v")
                        lines.append("[F] Filter Context (unchanged)")

                lines.append("")

            # Final result
            lines.append("     |")
            lines.append("     v")
            lines.append("[RESULT] Final calculation result")
            lines.append("")
            lines.append("=" * 80)

            # Add summary
            lines.append("SUMMARY:")
            lines.append(f"  Total transitions: {len(context_analysis.transitions)}")
            lines.append(f"  Complexity score: {context_analysis.complexity_score}/100")
            lines.append(f"  Max nesting level: {context_analysis.max_nesting_level}")

            if context_analysis.warnings:
                lines.append("")
                lines.append("WARNINGS:")
                for warning in context_analysis.warnings:
                    lines.append(f"  ⚠️  {warning.message}")

            lines.append("=" * 80)

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error generating ASCII diagram: {e}", exc_info=True)
            return f"Error generating diagram: {str(e)}"

    def generate_html_diagram(self, context_analysis) -> str:
        """
        Generate HTML diagram of context flow

        Args:
            context_analysis: ContextFlowExplanation from DaxContextAnalyzer

        Returns:
            HTML string
        """
        try:
            html_parts = []

            # CSS styles
            html_parts.append("""
<style>
.context-flow {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    max-width: 800px;
    margin: 20px auto;
    padding: 20px;
    background: #f5f5f5;
    border-radius: 8px;
}

.flow-title {
    text-align: center;
    color: #333;
    margin-bottom: 20px;
    font-size: 24px;
    font-weight: bold;
}

.flow-step {
    background: white;
    margin: 15px 0;
    padding: 15px;
    border-left: 4px solid #2196F3;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.flow-step.filter-context {
    border-left-color: #2196F3;
}

.flow-step.row-context {
    border-left-color: #FF9800;
}

.flow-step.transition {
    border-left-color: #4CAF50;
    background: #E8F5E9;
}

.flow-step.warning {
    border-left-color: #F44336;
    background: #FFEBEE;
}

.step-number {
    display: inline-block;
    background: #2196F3;
    color: white;
    width: 30px;
    height: 30px;
    line-height: 30px;
    text-align: center;
    border-radius: 50%;
    margin-right: 10px;
    font-weight: bold;
}

.step-title {
    font-weight: bold;
    font-size: 16px;
    margin-bottom: 8px;
}

.step-description {
    color: #666;
    margin-left: 40px;
    line-height: 1.6;
}

.flow-arrow {
    text-align: center;
    color: #999;
    font-size: 24px;
    margin: 10px 0;
}

.summary-box {
    background: #E3F2FD;
    padding: 15px;
    border-radius: 4px;
    margin-top: 20px;
}

.summary-title {
    font-weight: bold;
    margin-bottom: 10px;
}

.warning-icon {
    color: #F44336;
    font-weight: bold;
}

.legend {
    background: white;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 20px;
    font-size: 14px;
}

.legend-item {
    margin: 5px 0;
}

.legend-color {
    display: inline-block;
    width: 20px;
    height: 4px;
    margin-right: 8px;
    vertical-align: middle;
}
</style>
""")

            # Start HTML structure
            html_parts.append('<div class="context-flow">')
            html_parts.append('<div class="flow-title">📊 DAX Context Flow Diagram</div>')

            # Legend
            html_parts.append('<div class="legend">')
            html_parts.append('<div class="legend-item">')
            html_parts.append('<span class="legend-color" style="background: #2196F3;"></span>')
            html_parts.append('Filter Context')
            html_parts.append('</div>')
            html_parts.append('<div class="legend-item">')
            html_parts.append('<span class="legend-color" style="background: #FF9800;"></span>')
            html_parts.append('Row Context')
            html_parts.append('</div>')
            html_parts.append('<div class="legend-item">')
            html_parts.append('<span class="legend-color" style="background: #4CAF50;"></span>')
            html_parts.append('Context Transition')
            html_parts.append('</div>')
            html_parts.append('</div>')

            # Initial state
            html_parts.append('<div class="flow-step filter-context">')
            html_parts.append('<div class="step-title">Initial Filter Context</div>')
            html_parts.append('<div class="step-description">Inherited from report visuals, slicers, and page filters</div>')
            html_parts.append('</div>')

            if not context_analysis.transitions:
                html_parts.append('<div class="flow-arrow">↓</div>')
                html_parts.append('<div class="flow-step">')
                html_parts.append('<div class="step-title">Simple Calculation</div>')
                html_parts.append('<div class="step-description">No context transitions detected. Direct calculation using current filter context.</div>')
                html_parts.append('</div>')
            else:
                # Process transitions
                for i, transition in enumerate(context_analysis.transitions, 1):
                    html_parts.append('<div class="flow-arrow">↓</div>')

                    # Determine step class
                    if transition.type.value == "explicit_calculate":
                        step_class = "transition"
                        icon = "🔄"
                    elif transition.type.value == "iterator":
                        step_class = "row-context"
                        icon = "🔁"
                    elif transition.type.value == "implicit_measure":
                        step_class = "transition"
                        icon = "📏"
                    else:
                        step_class = "flow-step"
                        icon = "•"

                    # Add warning class if high impact
                    if transition.performance_impact.value in ["high", "critical"]:
                        step_class += " warning"

                    html_parts.append(f'<div class="flow-step {step_class}">')
                    html_parts.append(f'<span class="step-number">{i}</span>')
                    html_parts.append(f'<div class="step-title">{icon} {transition.function}</div>')
                    html_parts.append(f'<div class="step-description">')
                    html_parts.append(f'{transition.explanation}')

                    if transition.performance_impact.value in ["high", "critical"]:
                        html_parts.append(f'<br><span class="warning-icon">⚠️ Performance Impact: {transition.performance_impact.value.upper()}</span>')

                    html_parts.append('</div>')
                    html_parts.append('</div>')

            # Final result
            html_parts.append('<div class="flow-arrow">↓</div>')
            html_parts.append('<div class="flow-step filter-context">')
            html_parts.append('<div class="step-title">✅ Final Result</div>')
            html_parts.append('<div class="step-description">Calculation complete and returned to visual</div>')
            html_parts.append('</div>')

            # Summary
            html_parts.append('<div class="summary-box">')
            html_parts.append('<div class="summary-title">📈 Analysis Summary</div>')
            html_parts.append(f'<div>Total transitions: <strong>{len(context_analysis.transitions)}</strong></div>')
            html_parts.append(f'<div>Complexity score: <strong>{context_analysis.complexity_score}/100</strong></div>')
            html_parts.append(f'<div>Max nesting level: <strong>{context_analysis.max_nesting_level}</strong></div>')

            if context_analysis.warnings:
                html_parts.append('<div style="margin-top: 10px;">')
                html_parts.append('<div class="summary-title">⚠️ Warnings</div>')
                for warning in context_analysis.warnings:
                    html_parts.append(f'<div>• {warning.message}</div>')
                html_parts.append('</div>')

            html_parts.append('</div>')

            # Close main div
            html_parts.append('</div>')

            return "\n".join(html_parts)

        except Exception as e:
            logger.error(f"Error generating HTML diagram: {e}", exc_info=True)
            return f"<div>Error generating diagram: {str(e)}</div>"

    def generate_mermaid_diagram(self, context_analysis) -> str:
        """
        Generate Mermaid flowchart diagram

        Args:
            context_analysis: ContextFlowExplanation from DaxContextAnalyzer

        Returns:
            Mermaid diagram code
        """
        try:
            lines = ["```mermaid", "flowchart TD"]

            # Start node
            lines.append("    Start[Initial Filter Context] --> Eval")

            if not context_analysis.transitions:
                lines.append("    Eval[Simple Calculation] --> Result")
                lines.append("    Result[Final Result]")
            else:
                # Process transitions
                for i, transition in enumerate(context_analysis.transitions, 1):
                    node_id = f"T{i}"
                    next_id = f"T{i + 1}" if i < len(context_analysis.transitions) else "Result"

                    # Create node label
                    label = f"{transition.function}"

                    # Determine node style
                    if transition.type.value == "explicit_calculate":
                        node_def = f"    {node_id}[{label}<br/>Context Transition]"
                        style = ":::calculate"
                    elif transition.type.value == "iterator":
                        node_def = f"    {node_id}[/{label}<br/>Row Context\\]"
                        style = ":::iterator"
                    elif transition.type.value == "implicit_measure":
                        node_def = f"    {node_id}([{label}])"
                        style = ":::measure"
                    else:
                        node_def = f"    {node_id}[{label}]"
                        style = ""

                    lines.append(f"{node_def}{style}")

                    # Connect to next
                    prev_id = f"T{i - 1}" if i > 1 else "Start"
                    lines.append(f"    {prev_id} --> {node_id}")

                # Final result
                lines.append("    " + f"T{len(context_analysis.transitions)} --> Result")
                lines.append("    Result[Final Result]")

            # Add style definitions
            lines.append("")
            lines.append("    classDef calculate fill:#4CAF50,stroke:#333,color:#fff")
            lines.append("    classDef iterator fill:#FF9800,stroke:#333,color:#fff")
            lines.append("    classDef measure fill:#2196F3,stroke:#333,color:#fff")

            lines.append("```")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error generating Mermaid diagram: {e}", exc_info=True)
            return f"Error: {str(e)}"
