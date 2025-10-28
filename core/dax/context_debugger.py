"""
DAX Context Debugger - Step-by-step context tracking

Provides:
- Step-through evaluation with context tracking
- Context inspection at breakpoints
- Performance profiling per step
- Optimization suggestions
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from .context_analyzer import DaxContextAnalyzer, ContextFlowExplanation

logger = logging.getLogger(__name__)


@dataclass
class EvaluationStep:
    """Represents a single evaluation step"""
    step_number: int
    code_fragment: str
    filter_context: Dict[str, List[Any]]
    row_context: Optional[Dict[str, Any]]
    intermediate_result: Optional[Any]
    explanation: str
    execution_time_ms: Optional[float] = None


@dataclass
class ContextExplanation:
    """Explanation of context at a specific position"""
    position: int
    line: int
    column: int
    filter_context: Dict[str, List[str]]
    row_context: Optional[Dict[str, Any]]
    in_transition: bool
    transition_type: Optional[str]
    explanation: str


@dataclass
class Optimization:
    """Optimization suggestion"""
    severity: str  # "info", "warning", "critical"
    category: str  # "performance", "readability", "correctness"
    message: str
    suggestion: str
    code_example: Optional[str] = None


class DaxContextDebugger:
    """
    Step-by-step DAX debugger with context tracking

    Features:
    - Step through DAX evaluation
    - Track filter and row context at each step
    - Performance profiling
    - Optimization suggestions
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize debugger

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.max_steps = self.config.get("max_steps", 100)
        self.analyzer = DaxContextAnalyzer(config)

    def step_through(
        self,
        dax_expression: str,
        breakpoints: Optional[List[int]] = None,
        sample_data: Optional[Dict[str, Any]] = None,
    ) -> List[EvaluationStep]:
        """
        Step through DAX evaluation with context tracking

        Args:
            dax_expression: DAX expression to debug
            breakpoints: Optional character positions for breakpoints
            sample_data: Optional sample data for evaluation

        Returns:
            List of evaluation steps
        """
        try:
            steps: List[EvaluationStep] = []

            # First, analyze context transitions
            analysis = self.analyzer.analyze_context_transitions(dax_expression)

            # Create steps from transitions
            for i, transition in enumerate(analysis.transitions):
                step = EvaluationStep(
                    step_number=i + 1,
                    code_fragment=self._extract_code_fragment(
                        dax_expression, transition.location
                    ),
                    filter_context=self._infer_filter_context(transition),
                    row_context=self._infer_row_context(transition),
                    intermediate_result=None,  # Would require actual execution
                    explanation=transition.explanation,
                    execution_time_ms=None,
                )

                steps.append(step)

                # Check if we've reached max steps
                if len(steps) >= self.max_steps:
                    logger.warning(f"Reached max steps limit: {self.max_steps}")
                    break

            logger.info(f"Generated {len(steps)} evaluation steps")

            return steps

        except Exception as e:
            logger.error(f"Error in step-through debugging: {e}", exc_info=True)
            return []

    def explain_context_at_position(
        self,
        dax_expression: str,
        position: int,
    ) -> ContextExplanation:
        """
        Explain context at a specific position in DAX expression

        Args:
            dax_expression: DAX expression
            position: Character position

        Returns:
            ContextExplanation for that position
        """
        try:
            # Analyze entire expression
            analysis = self.analyzer.analyze_context_transitions(dax_expression)

            # Find transitions before this position
            transitions_before = [
                t for t in analysis.transitions if t.location <= position
            ]

            # Get line/column
            lines = dax_expression[:position].split("\n")
            line = len(lines)
            column = len(lines[-1]) + 1

            # Determine if we're inside a transition
            in_transition = False
            transition_type = None

            for t in reversed(transitions_before):
                # Check if position is within this transition's scope
                # (simplified - would need proper parsing)
                if abs(t.location - position) < 50:
                    in_transition = True
                    transition_type = t.type.value
                    break

            # Build explanation
            if in_transition:
                explanation = f"Inside {transition_type} at line {line}. "
                if transitions_before:
                    last_transition = transitions_before[-1]
                    explanation += last_transition.explanation
                else:
                    explanation = f"At position {position}, line {line}."
            else:
                explanation = f"At position {position}, line {line}. "
                if transitions_before:
                    explanation += f"After {len(transitions_before)} context transition(s)."
                else:
                    explanation += "No context transitions detected before this point."

            return ContextExplanation(
                position=position,
                line=line,
                column=column,
                filter_context={},  # Would need runtime data
                row_context=None,
                in_transition=in_transition,
                transition_type=transition_type,
                explanation=explanation,
            )

        except Exception as e:
            logger.error(f"Error explaining context at position: {e}", exc_info=True)
            return ContextExplanation(
                position=position,
                line=0,
                column=0,
                filter_context={},
                row_context=None,
                in_transition=False,
                transition_type=None,
                explanation=f"Error: {str(e)}",
            )

    def suggest_optimizations(
        self,
        context_analysis: ContextFlowExplanation,
    ) -> List[Optimization]:
        """
        Suggest optimizations based on context analysis

        Args:
            context_analysis: Context analysis result

        Returns:
            List of optimization suggestions
        """
        optimizations: List[Optimization] = []

        try:
            # Check for excessive CALCULATE nesting
            if context_analysis.max_nesting_level > 3:
                optimizations.append(
                    Optimization(
                        severity="warning",
                        category="performance",
                        message=f"Excessive CALCULATE nesting ({context_analysis.max_nesting_level} levels)",
                        suggestion="Consider using variables (VAR) to store intermediate calculations and reduce nesting depth.",
                        code_example="""// Instead of:
CALCULATE(
    CALCULATE(
        CALCULATE([Measure], Filter1),
        Filter2
    ),
    Filter3
)

// Use:
VAR Step1 = CALCULATE([Measure], Filter1)
VAR Step2 = CALCULATE(Step1, Filter2)
RETURN CALCULATE(Step2, Filter3)"""
                    )
                )

            # Check for iterator + measure combinations
            iterator_transitions = [
                t for t in context_analysis.transitions
                if t.type.value == "iterator"
            ]

            if len(iterator_transitions) > 3:
                optimizations.append(
                    Optimization(
                        severity="warning",
                        category="performance",
                        message=f"Multiple iterators with measure references ({len(iterator_transitions)} detected)",
                        suggestion="Each measure reference in an iterator causes context transition per row. Consider pre-calculating values using variables or switching to iterators that work with columns.",
                        code_example="""// Instead of:
SUMX(Sales, [Total Sales] * [Tax Rate])

// Use:
SUMX(Sales, Sales[Amount] * Sales[TaxRate])

// Or use variables:
VAR TotalSales = [Total Sales]
VAR TaxRate = [Tax Rate]
RETURN SUMX(Sales, TotalSales * TaxRate)"""
                    )
                )

            # Check complexity score
            if context_analysis.complexity_score > 70:
                optimizations.append(
                    Optimization(
                        severity="critical",
                        category="readability",
                        message=f"High complexity score ({context_analysis.complexity_score}/100)",
                        suggestion="Consider breaking this measure into multiple simpler measures for better maintainability and performance.",
                        code_example=None
                    )
                )

            # Check for implicit measure references
            implicit_refs = [
                t for t in context_analysis.transitions
                if t.type.value == "implicit_measure"
            ]

            if len(implicit_refs) > 10:
                optimizations.append(
                    Optimization(
                        severity="info",
                        category="performance",
                        message=f"Many implicit measure references ({len(implicit_refs)})",
                        suggestion="While implicit CALCULATE is convenient, excessive use can impact performance. Consider whether all references need to be measures.",
                        code_example=None
                    )
                )

            # Add general best practices
            if context_analysis.transitions:
                optimizations.append(
                    Optimization(
                        severity="info",
                        category="correctness",
                        message="Context transition detected",
                        suggestion="Ensure that context transitions are intentional. Use DAX Studio or Tabular Editor to verify query plans and performance.",
                        code_example=None
                    )
                )

            logger.info(f"Generated {len(optimizations)} optimization suggestions")

        except Exception as e:
            logger.error(f"Error generating optimizations: {e}", exc_info=True)

        return optimizations

    def _extract_code_fragment(self, dax: str, position: int) -> str:
        """Extract code fragment around position"""
        start = max(0, position - 30)
        end = min(len(dax), position + 30)

        fragment = dax[start:end]

        # Add markers
        marker_pos = min(30, position - start)
        return fragment[:marker_pos] + " ▶ " + fragment[marker_pos:]

    def _infer_filter_context(self, transition) -> Dict[str, List[Any]]:
        """Infer filter context (simplified - would need runtime data)"""
        # This is a placeholder - actual implementation would need
        # to track filter modifications through CALCULATE arguments
        return {}

    def _infer_row_context(self, transition) -> Optional[Dict[str, Any]]:
        """Infer row context (simplified - would need runtime data)"""
        if transition.type.value == "iterator":
            return {"type": "iterator", "function": transition.function}
        return None

    def generate_debug_report(
        self,
        dax_expression: str,
        include_profiling: bool = True,
        include_optimization: bool = True,
    ) -> str:
        """
        Generate comprehensive debug report

        Args:
            dax_expression: DAX expression to analyze
            include_profiling: Include performance profiling
            include_optimization: Include optimization suggestions

        Returns:
            Formatted debug report
        """
        lines = []

        lines.append("=" * 70)
        lines.append("DAX CONTEXT DEBUG REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Context analysis
        analysis = self.analyzer.analyze_context_transitions(dax_expression)

        lines.append("CONTEXT ANALYSIS")
        lines.append("-" * 70)
        lines.append(analysis.summary)
        lines.append("")
        lines.append(f"Complexity Score: {analysis.complexity_score}/100")
        lines.append(f"Max Nesting Level: {analysis.max_nesting_level}")
        lines.append("")

        # Transitions
        if analysis.transitions:
            lines.append("CONTEXT TRANSITIONS")
            lines.append("-" * 70)

            for i, t in enumerate(analysis.transitions, 1):
                lines.append(f"{i}. {t.function} (Line {t.line}, Col {t.column})")
                lines.append(f"   Type: {t.type.value}")
                lines.append(f"   Impact: {t.performance_impact.value}")
                lines.append(f"   {t.explanation}")
                lines.append("")

        # Warnings
        if analysis.warnings:
            lines.append("PERFORMANCE WARNINGS")
            lines.append("-" * 70)

            for w in analysis.warnings:
                lines.append(f"⚠️  {w.message}")
                lines.append(f"   💡 {w.suggestion}")
                lines.append("")

        # Optimizations
        if include_optimization:
            optimizations = self.suggest_optimizations(analysis)

            if optimizations:
                lines.append("OPTIMIZATION SUGGESTIONS")
                lines.append("-" * 70)

                for opt in optimizations:
                    icon = "🔴" if opt.severity == "critical" else "🟡" if opt.severity == "warning" else "🔵"
                    lines.append(f"{icon} [{opt.category.upper()}] {opt.message}")
                    lines.append(f"   💡 {opt.suggestion}")

                    if opt.code_example:
                        lines.append("   Example:")
                        for line in opt.code_example.split("\n"):
                            lines.append(f"      {line}")

                    lines.append("")

        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)
