"""
DAX Context Analyzer - Context transition detection and analysis

Detects and explains:
- Explicit CALCULATE/CALCULATETABLE context transitions
- Implicit context transitions from measure references
- Iterator function context transitions
- Performance impact assessment
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """Type of context transition"""
    EXPLICIT_CALCULATE = "explicit_calculate"
    IMPLICIT_MEASURE = "implicit_measure"
    ITERATOR = "iterator"
    CALCULATETABLE = "calculatetable"


class PerformanceImpact(Enum):
    """Performance impact level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ContextTransition:
    """Represents a detected context transition"""
    location: int  # Character position in DAX
    line: int  # Line number
    column: int  # Column position
    type: TransitionType
    function: str  # Function causing transition (CALCULATE, SUMX, etc.)
    measure_name: Optional[str] = None
    row_context_vars: List[str] = field(default_factory=list)
    filter_context_before: List[str] = field(default_factory=list)
    filter_context_after: List[str] = field(default_factory=list)
    performance_impact: PerformanceImpact = PerformanceImpact.LOW
    explanation: str = ""
    nested_level: int = 0


@dataclass
class PerformanceWarning:
    """Performance warning for context transitions"""
    location: int
    severity: str  # "warning", "error"
    message: str
    suggestion: str


@dataclass
class ContextFlowExplanation:
    """Complete explanation of context flow in DAX expression"""
    transitions: List[ContextTransition]
    warnings: List[PerformanceWarning]
    summary: str
    complexity_score: int  # 0-100
    max_nesting_level: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "transitions": [
                {
                    "location": t.location,
                    "line": t.line,
                    "column": t.column,
                    "type": t.type.value,
                    "function": t.function,
                    "measure_name": t.measure_name,
                    "performance_impact": t.performance_impact.value,
                    "explanation": t.explanation,
                    "nested_level": t.nested_level,
                }
                for t in self.transitions
            ],
            "warnings": [
                {
                    "location": w.location,
                    "severity": w.severity,
                    "message": w.message,
                    "suggestion": w.suggestion,
                }
                for w in self.warnings
            ],
            "summary": self.summary,
            "complexity_score": self.complexity_score,
            "max_nesting_level": self.max_nesting_level,
        }


class DaxContextAnalyzer:
    """
    DAX Context Analyzer

    Detects and analyzes context transitions in DAX expressions:
    - CALCULATE and CALCULATETABLE (explicit transitions)
    - Measure references (implicit transitions)
    - Iterator functions with measure calls (transition in each iteration)
    """

    # Iterator functions that create row context
    ITERATOR_FUNCTIONS = {
        "SUMX", "AVERAGEX", "MINX", "MAXX", "COUNTX",
        "FILTER", "ADDCOLUMNS", "SELECTCOLUMNS",
        "RANKX", "CONCATENATEX", "PRODUCTX",
        "STDEVX.S", "STDEVX.P", "VARX.S", "VARX.P",
    }

    # Functions that cause explicit context transition
    CALCULATE_FUNCTIONS = {"CALCULATE", "CALCULATETABLE"}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize context analyzer

        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        self.max_expression_length = self.config.get("max_expression_length", 50000)
        self.nested_calculate_limit = self.config.get("nested_calculate_limit", 10)

    def analyze_context_transitions(
        self,
        dax_expression: str,
        measure_name: Optional[str] = None,
        reference_index: Optional[Dict[str, Any]] = None,
    ) -> ContextFlowExplanation:
        """
        Analyze DAX expression for context transitions

        Args:
            dax_expression: DAX measure expression
            measure_name: Optional measure name for context
            reference_index: Optional index of all measures for dependency analysis

        Returns:
            ContextFlowExplanation with all detected transitions
        """
        try:
            if len(dax_expression) > self.max_expression_length:
                logger.warning(
                    f"DAX expression exceeds max length ({len(dax_expression)} > {self.max_expression_length})"
                )

            transitions: List[ContextTransition] = []
            warnings: List[PerformanceWarning] = []

            # Normalize expression (remove comments)
            normalized = self._normalize_dax(dax_expression)

            # Detect explicit CALCULATE transitions
            calc_transitions = self._detect_calculate_transitions(normalized)
            transitions.extend(calc_transitions)

            # Detect implicit measure call transitions
            measure_transitions = self._detect_implicit_measure_transitions(
                normalized, reference_index
            )
            transitions.extend(measure_transitions)

            # Detect iterator transitions
            iterator_transitions = self._detect_iterator_transitions(
                normalized, reference_index
            )
            transitions.extend(iterator_transitions)

            # Sort by location
            transitions.sort(key=lambda t: t.location)

            # Calculate nesting levels
            self._calculate_nesting_levels(transitions)

            # Detect performance issues
            warnings.extend(self._detect_performance_issues(transitions))

            # Calculate complexity score
            complexity = self._calculate_complexity_score(transitions)

            # Generate summary
            summary = self._generate_summary(transitions, warnings)

            max_nesting = max((t.nested_level for t in transitions), default=0)

            logger.info(
                f"Context analysis complete: {len(transitions)} transitions, "
                f"{len(warnings)} warnings, complexity={complexity}"
            )

            return ContextFlowExplanation(
                transitions=transitions,
                warnings=warnings,
                summary=summary,
                complexity_score=complexity,
                max_nesting_level=max_nesting,
            )

        except Exception as e:
            logger.error(f"Error analyzing context transitions: {e}", exc_info=True)
            return ContextFlowExplanation(
                transitions=[],
                warnings=[
                    PerformanceWarning(
                        location=0,
                        severity="error",
                        message=f"Analysis failed: {str(e)}",
                        suggestion="Check DAX syntax and try again"
                    )
                ],
                summary="Analysis failed",
                complexity_score=0,
                max_nesting_level=0,
            )

    def _normalize_dax(self, dax: str) -> str:
        """Normalize DAX expression (remove comments, extra whitespace)"""
        # Remove single-line comments
        dax = re.sub(r"//.*?$", "", dax, flags=re.MULTILINE)

        # Remove multi-line comments
        dax = re.sub(r"/\*.*?\*/", "", dax, flags=re.DOTALL)

        return dax

    def _detect_calculate_transitions(self, dax: str) -> List[ContextTransition]:
        """Detect explicit CALCULATE/CALCULATETABLE transitions"""
        transitions = []

        for func_name in self.CALCULATE_FUNCTIONS:
            # Find all occurrences of CALCULATE/CALCULATETABLE
            pattern = rf"\b{func_name}\s*\("

            for match in re.finditer(pattern, dax, re.IGNORECASE):
                location = match.start()
                line, column = self._get_line_column(dax, location)

                transition = ContextTransition(
                    location=location,
                    line=line,
                    column=column,
                    type=TransitionType.EXPLICIT_CALCULATE if func_name == "CALCULATE" else TransitionType.CALCULATETABLE,
                    function=func_name,
                    explanation=f"{func_name} creates a new filter context by transitioning from row context (if any) to filter context. Any existing filter context is modified by the filter arguments.",
                    performance_impact=PerformanceImpact.LOW,
                )

                transitions.append(transition)

        return transitions

    def _detect_implicit_measure_transitions(
        self,
        dax: str,
        reference_index: Optional[Dict[str, Any]],
    ) -> List[ContextTransition]:
        """Detect implicit context transitions from measure references"""
        transitions = []

        # Pattern to match measure references: [MeasureName]
        measure_pattern = r"\[([^\]]+)\]"

        for match in re.finditer(measure_pattern, dax):
            measure_name = match.group(1)
            location = match.start()
            line, column = self._get_line_column(dax, location)

            # Check if this is likely a measure (not a column reference)
            # Heuristic: measures are typically referenced alone, not with table prefix
            context_before = dax[max(0, location - 10):location]
            if "'" not in context_before and "[" not in context_before:
                # Likely a measure reference
                transition = ContextTransition(
                    location=location,
                    line=line,
                    column=column,
                    type=TransitionType.IMPLICIT_MEASURE,
                    function="MEASURE_REFERENCE",
                    measure_name=measure_name,
                    explanation=f"Implicit CALCULATE wrapper around measure [{measure_name}]. If in row context, this causes context transition to filter context.",
                    performance_impact=PerformanceImpact.LOW,
                )

                transitions.append(transition)

        return transitions

    def _detect_iterator_transitions(
        self,
        dax: str,
        reference_index: Optional[Dict[str, Any]],
    ) -> List[ContextTransition]:
        """Detect context transitions in iterator functions"""
        transitions = []

        for func_name in self.ITERATOR_FUNCTIONS:
            pattern = rf"\b{func_name}\s*\("

            for match in re.finditer(pattern, dax, re.IGNORECASE):
                location = match.start()
                line, column = self._get_line_column(dax, location)

                # Check if iterator contains measure references
                # Extract iterator body (simplified - doesn't handle nested functions perfectly)
                start = match.end()
                body = self._extract_function_body(dax, start)

                has_measure_refs = bool(re.search(r"\[[^\]]+\]", body))

                if has_measure_refs:
                    transition = ContextTransition(
                        location=location,
                        line=line,
                        column=column,
                        type=TransitionType.ITERATOR,
                        function=func_name,
                        explanation=f"{func_name} creates row context. Measure references inside the iterator cause context transition in EACH iteration, potentially impacting performance.",
                        performance_impact=PerformanceImpact.MEDIUM,
                    )

                    transitions.append(transition)

        return transitions

    def _extract_function_body(self, dax: str, start: int) -> str:
        """Extract function body (simplified parenthesis matching)"""
        depth = 1
        end = start

        while end < len(dax) and depth > 0:
            if dax[end] == "(":
                depth += 1
            elif dax[end] == ")":
                depth -= 1
            end += 1

        return dax[start:end - 1]

    def _calculate_nesting_levels(self, transitions: List[ContextTransition]) -> None:
        """Calculate nesting level for each transition"""
        # Simplified: count CALCULATE nesting by counting open CALCULATEs before each transition
        for i, transition in enumerate(transitions):
            # Count CALCULATE functions before this that haven't closed
            nesting = 0
            for j in range(i):
                if transitions[j].type in {TransitionType.EXPLICIT_CALCULATE, TransitionType.CALCULATETABLE}:
                    nesting += 1

            transition.nested_level = nesting

    def _detect_performance_issues(
        self,
        transitions: List[ContextTransition]
    ) -> List[PerformanceWarning]:
        """Detect performance issues from context transitions"""
        warnings = []

        # Check for excessive nesting
        max_nesting = max((t.nested_level for t in transitions), default=0)
        if max_nesting > self.nested_calculate_limit:
            warnings.append(
                PerformanceWarning(
                    location=0,
                    severity="warning",
                    message=f"Excessive CALCULATE nesting detected (depth: {max_nesting})",
                    suggestion="Consider refactoring into intermediate variables or measures"
                )
            )

        # Check for iterator + measure combinations
        iterator_with_measures = [
            t for t in transitions
            if t.type == TransitionType.ITERATOR and t.performance_impact == PerformanceImpact.MEDIUM
        ]

        if len(iterator_with_measures) > 5:
            warnings.append(
                PerformanceWarning(
                    location=0,
                    severity="warning",
                    message=f"Multiple iterators with measure references ({len(iterator_with_measures)} detected)",
                    suggestion="Each measure reference in an iterator causes context transition per row. Consider pre-calculating values or using variables."
                )
            )

        return warnings

    def _calculate_complexity_score(self, transitions: List[ContextTransition]) -> int:
        """Calculate complexity score (0-100)"""
        if not transitions:
            return 0

        # Factors:
        # - Number of transitions (5 points each)
        # - Nesting depth (10 points per level)
        # - Iterator transitions (extra 5 points each)

        score = len(transitions) * 5

        max_nesting = max((t.nested_level for t in transitions), default=0)
        score += max_nesting * 10

        iterator_count = sum(1 for t in transitions if t.type == TransitionType.ITERATOR)
        score += iterator_count * 5

        return min(score, 100)

    def _generate_summary(
        self,
        transitions: List[ContextTransition],
        warnings: List[PerformanceWarning]
    ) -> str:
        """Generate human-readable summary"""
        if not transitions:
            return "No context transitions detected. This measure uses simple aggregations without context modifications."

        explicit = sum(1 for t in transitions if t.type == TransitionType.EXPLICIT_CALCULATE)
        implicit = sum(1 for t in transitions if t.type == TransitionType.IMPLICIT_MEASURE)
        iterators = sum(1 for t in transitions if t.type == TransitionType.ITERATOR)

        summary_parts = [
            f"Detected {len(transitions)} context transition(s):"
        ]

        if explicit > 0:
            summary_parts.append(f"  • {explicit} explicit CALCULATE/CALCULATETABLE")

        if implicit > 0:
            summary_parts.append(f"  • {implicit} implicit measure references")

        if iterators > 0:
            summary_parts.append(f"  • {iterators} iterator functions with measure calls")

        if warnings:
            summary_parts.append(f"\n⚠️ {len(warnings)} performance warning(s) detected")

        return "\n".join(summary_parts)

    def _get_line_column(self, text: str, position: int) -> Tuple[int, int]:
        """Get line and column number from character position"""
        lines = text[:position].split("\n")
        line = len(lines)
        column = len(lines[-1]) + 1
        return line, column

    def detect_dax_anti_patterns(self, dax_expression: str) -> Dict[str, Any]:
        """
        Detect common DAX anti-patterns using pattern matching

        Args:
            dax_expression: DAX expression to analyze

        Returns:
            Dictionary with detected patterns and recommendations
        """
        try:
            from core.research.dax_research import DaxResearchProvider

            research_provider = DaxResearchProvider()
            results = research_provider.get_optimization_guidance(
                query=dax_expression,
                performance_data=None  # No performance data needed for pattern detection
            )

            # Extract pattern-based information
            pattern_matches = results.get('pattern_matches', {})
            articles = results.get('articles', [])

            # Get pattern-based recommendations
            all_recommendations = results.get('recommendations', [])
            pattern_recommendations = all_recommendations

            return {
                'success': True,
                'patterns_detected': len(pattern_matches),
                'pattern_matches': pattern_matches,
                'articles': articles,
                'recommendations': pattern_recommendations
            }

        except ImportError:
            logger.warning("DaxResearchProvider not available for anti-pattern detection")
            return {
                'success': False,
                'error': 'Pattern detection not available'
            }
        except Exception as e:
            logger.error(f"Error detecting anti-patterns: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def detect_summarize_patterns(self, dax_expression: str) -> Dict[str, Any]:
        """
        Detect SUMMARIZE vs SUMMARIZECOLUMNS usage

        Returns suggestions to upgrade to SUMMARIZECOLUMNS for better performance
        """
        summarize_pattern = r'\bSUMMARIZE\s*\('
        summarize_matches = list(re.finditer(summarize_pattern, dax_expression, re.IGNORECASE))

        if not summarize_matches:
            return {
                'has_summarize': False,
                'recommendation': None
            }

        return {
            'has_summarize': True,
            'occurrences': len(summarize_matches),
            'severity': 'medium',
            'recommendation': (
                f"Found {len(summarize_matches)} SUMMARIZE function(s). "
                "SUMMARIZECOLUMNS is newer and more optimized (2-10x faster). "
                "Consider converting SUMMARIZE to SUMMARIZECOLUMNS for better performance."
            ),
            'example_conversion': """
-- BEFORE (SUMMARIZE):
SUMMARIZE(
    Sales,
    Sales[ProductID],
    "Total", SUM(Sales[Amount])
)

-- AFTER (SUMMARIZECOLUMNS):
SUMMARIZECOLUMNS(
    Sales[ProductID],
    "Total", [Total Sales]
)
"""
        }

    def explain_context_flow(self, dax_expression: str) -> str:
        """
        Generate step-by-step explanation of context flow

        Args:
            dax_expression: DAX expression

        Returns:
            Human-readable explanation
        """
        analysis = self.analyze_context_transitions(dax_expression)

        explanation_parts = [analysis.summary, ""]

        if analysis.transitions:
            explanation_parts.append("Context Flow Details:")
            explanation_parts.append("=" * 50)

            for i, transition in enumerate(analysis.transitions, 1):
                explanation_parts.append(
                    f"\n{i}. Line {transition.line}, Col {transition.column}:"
                )
                explanation_parts.append(f"   Function: {transition.function}")
                explanation_parts.append(f"   Type: {transition.type.value}")
                explanation_parts.append(f"   {transition.explanation}")

                if transition.performance_impact != PerformanceImpact.LOW:
                    explanation_parts.append(
                        f"   ⚠️ Performance Impact: {transition.performance_impact.value.upper()}"
                    )

        if analysis.warnings:
            explanation_parts.append("\nPerformance Warnings:")
            explanation_parts.append("=" * 50)

            for warning in analysis.warnings:
                explanation_parts.append(f"\n⚠️ {warning.message}")
                explanation_parts.append(f"   💡 Suggestion: {warning.suggestion}")

        return "\n".join(explanation_parts)
