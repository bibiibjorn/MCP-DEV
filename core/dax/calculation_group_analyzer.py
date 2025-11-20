"""
Calculation Group Analyzer - Specialized analysis for calculation groups

Provides:
- Precedence conflict detection
- Performance impact assessment
- Design pattern validation
- Best practice recommendations
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CalculationGroup:
    """Represents a calculation group"""
    name: str
    precedence: int
    items: List[str]
    description: Optional[str] = None


@dataclass
class PrecedenceConflict:
    """Precedence conflict between calculation groups"""
    measure_name: str
    groups: List[Tuple[str, int]]  # (group_name, precedence)
    warning: str
    severity: str  # "info", "warning", "error"


@dataclass
class CalculationGroupIssue:
    """Issue found in calculation group usage"""
    issue_type: str
    severity: str
    message: str
    recommendation: str
    affected_groups: List[str]


class CalculationGroupAnalyzer:
    """
    Analyzer for Calculation Group usage and best practices

    Features:
    - Detect calculation group references in DAX
    - Check for precedence conflicts
    - Validate design patterns
    - Assess performance impact
    """

    # Best practice limits
    MAX_RECOMMENDED_GROUPS = 3
    MAX_ITEMS_PER_GROUP = 20

    def __init__(self, connection_state=None):
        """
        Initialize calculation group analyzer

        Args:
            connection_state: Optional connection state for querying model
        """
        self.connection_state = connection_state
        self._calc_groups: Dict[str, CalculationGroup] = {}
        self._groups_loaded = False

    def load_calculation_groups(self) -> bool:
        """
        Load calculation groups from model

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.connection_state or not self.connection_state.is_connected():
                logger.warning("Not connected - cannot load calculation groups")
                return False

            qe = self.connection_state.query_executor
            if not qe:
                logger.warning("Query executor not available")
                return False

            # Query DMVs for calculation groups
            dmv_query = """
            SELECT
                [Name],
                [Description],
                [Precedence]
            FROM $SYSTEM.TMSCHEMA_CALCULATION_GROUPS
            """

            result = qe.execute_dmv_query(dmv_query)

            if result.get('success') and result.get('data'):
                self._calc_groups.clear()

                for row in result['data']:
                    name = row.get('Name', '')
                    precedence = int(row.get('Precedence', 0))
                    description = row.get('Description')

                    # Query calculation items for this group
                    items_query = f"""
                    SELECT [Name]
                    FROM $SYSTEM.TMSCHEMA_CALCULATION_ITEMS
                    WHERE [CalculationGroupName] = '{name}'
                    """

                    items_result = qe.execute_dmv_query(items_query)
                    items = []

                    if items_result.get('success') and items_result.get('data'):
                        items = [item['Name'] for item in items_result['data']]

                    calc_group = CalculationGroup(
                        name=name,
                        precedence=precedence,
                        items=items,
                        description=description
                    )

                    self._calc_groups[name] = calc_group

                self._groups_loaded = True
                logger.info(f"Loaded {len(self._calc_groups)} calculation groups")
                return True
            else:
                logger.info("No calculation groups found in model")
                return False

        except Exception as e:
            logger.error(f"Error loading calculation groups: {e}", exc_info=True)
            return False

    def analyze_dax_with_calc_groups(
        self,
        dax_expression: str,
        measure_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze DAX expression for calculation group usage

        Args:
            dax_expression: DAX expression to analyze
            measure_name: Optional measure name for context

        Returns:
            Dictionary with analysis results
        """
        try:
            # Ensure groups are loaded
            if not self._groups_loaded:
                self.load_calculation_groups()

            # Detect calculation group references
            groups_detected = self._detect_calc_group_references(dax_expression)

            # Check for precedence conflicts
            conflicts = []
            if len(groups_detected) > 1 and measure_name:
                conflicts = self._check_precedence_conflicts(measure_name, groups_detected)

            # Assess performance impact
            performance_impact = self._assess_performance_impact(groups_detected)

            # Validate design patterns
            issues = self._validate_design_patterns(dax_expression, groups_detected)

            # Get recommendations
            recommendations = self._get_recommendations(
                groups_detected,
                conflicts,
                issues,
                performance_impact
            )

            return {
                "success": True,
                "groups_detected": [g.name for g in groups_detected],
                "group_count": len(groups_detected),
                "precedence_conflicts": [
                    {
                        "measure": c.measure_name,
                        "groups": [{"name": g[0], "precedence": g[1]} for g in c.groups],
                        "warning": c.warning,
                        "severity": c.severity
                    }
                    for c in conflicts
                ],
                "performance_impact": performance_impact,
                "issues": [
                    {
                        "type": i.issue_type,
                        "severity": i.severity,
                        "message": i.message,
                        "recommendation": i.recommendation,
                        "affected_groups": i.affected_groups
                    }
                    for i in issues
                ],
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Error analyzing calculation groups: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _detect_calc_group_references(self, dax: str) -> List[CalculationGroup]:
        """Detect calculation group references in DAX"""
        detected = []

        for group_name, group in self._calc_groups.items():
            # Check if any calculation item from this group is referenced
            for item in group.items:
                # Pattern: 'GroupName'[ItemName] or GroupName[ItemName]
                patterns = [
                    rf"'{re.escape(group_name)}'\s*\[\s*{re.escape(item)}\s*\]",
                    rf"\b{re.escape(group_name)}\s*\[\s*{re.escape(item)}\s*\]"
                ]

                for pattern in patterns:
                    if re.search(pattern, dax, re.IGNORECASE):
                        if group not in detected:
                            detected.append(group)
                        break

        return detected

    def _check_precedence_conflicts(
        self,
        measure_name: str,
        groups: List[CalculationGroup]
    ) -> List[PrecedenceConflict]:
        """Check for precedence conflicts"""
        conflicts = []

        if len(groups) <= 1:
            return conflicts

        # Sort by precedence
        sorted_groups = sorted(groups, key=lambda g: g.precedence)

        # Check for ambiguous precedence
        precedences = [g.precedence for g in groups]
        if len(set(precedences)) != len(precedences):
            # Duplicate precedences found
            conflicts.append(PrecedenceConflict(
                measure_name=measure_name,
                groups=[(g.name, g.precedence) for g in groups],
                warning="Duplicate precedence values detected! This may cause unpredictable behavior.",
                severity="error"
            ))
        else:
            # Just a warning about multiple groups
            conflicts.append(PrecedenceConflict(
                measure_name=measure_name,
                groups=[(g.name, g.precedence) for g in sorted_groups],
                warning=(
                    f"Multiple calculation groups applied to this measure. "
                    f"Execution order: {' → '.join(g.name for g in sorted_groups)} "
                    f"(based on precedence values). Verify this is intended."
                ),
                severity="warning"
            ))

        return conflicts

    def _assess_performance_impact(self, groups: List[CalculationGroup]) -> str:
        """Assess performance impact of calculation groups"""
        if not groups:
            return "none"

        total_items = sum(len(g.items) for g in groups)

        if len(groups) > self.MAX_RECOMMENDED_GROUPS:
            return "high"
        elif total_items > self.MAX_ITEMS_PER_GROUP:
            return "medium"
        elif len(groups) > 1:
            return "medium"
        else:
            return "low"

    def _validate_design_patterns(
        self,
        dax: str,
        groups: List[CalculationGroup]
    ) -> List[CalculationGroupIssue]:
        """Validate calculation group design patterns"""
        issues = []

        # Check 1: Too many calculation groups
        if len(groups) > self.MAX_RECOMMENDED_GROUPS:
            issues.append(CalculationGroupIssue(
                issue_type="too_many_groups",
                severity="warning",
                message=f"Using {len(groups)} calculation groups on a single measure",
                recommendation=(
                    "Consider consolidating calculation groups using SWITCH statements "
                    "for better performance and maintainability."
                ),
                affected_groups=[g.name for g in groups]
            ))

        # Check 2: Calculation group used inside iterator
        iterator_pattern = r'\b(SUMX|AVERAGEX|FILTER|ADDCOLUMNS)\s*\('
        if re.search(iterator_pattern, dax, re.IGNORECASE):
            for group in groups:
                # Check if calc group reference is inside iterator
                # This is a simplified check - would need full parsing for accuracy
                issues.append(CalculationGroupIssue(
                    issue_type="calc_group_in_iterator",
                    severity="warning",
                    message=f"Calculation group '{group.name}' may be used inside an iterator",
                    recommendation=(
                        "Using calculation groups inside iterators can cause performance issues. "
                        "Consider pre-calculating the value or restructuring the measure."
                    ),
                    affected_groups=[group.name]
                ))

        # Check 3: Nested calculation group references
        if len(groups) > 2:
            issues.append(CalculationGroupIssue(
                issue_type="complex_nesting",
                severity="info",
                message=f"Complex interaction between {len(groups)} calculation groups",
                recommendation=(
                    "Complex calculation group interactions can be difficult to debug. "
                    "Document the intended behavior and test thoroughly."
                ),
                affected_groups=[g.name for g in groups]
            ))

        # Check 4: SELECTEDMEASURE usage
        if "SELECTEDMEASURE" in dax.upper():
            issues.append(CalculationGroupIssue(
                issue_type="selectedmeasure_usage",
                severity="info",
                message="SELECTEDMEASURE() detected - calculation group pattern",
                recommendation=(
                    "Ensure SELECTEDMEASURE() is used correctly within calculation group items. "
                    "This function only works in calculation group context."
                ),
                affected_groups=[g.name for g in groups]
            ))

        return issues

    def _get_recommendations(
        self,
        groups: List[CalculationGroup],
        conflicts: List[PrecedenceConflict],
        issues: List[CalculationGroupIssue],
        performance_impact: str
    ) -> List[str]:
        """Get optimization recommendations"""
        recommendations = []

        # Performance recommendations
        if performance_impact == "high":
            recommendations.append(
                "High performance impact detected. Consider consolidating calculation groups "
                "using SWITCH for shared logic between calculation items."
            )

        # Precedence recommendations
        if conflicts:
            has_errors = any(c.severity == "error" for c in conflicts)
            if has_errors:
                recommendations.append(
                    "CRITICAL: Fix precedence conflicts immediately. Duplicate precedence values "
                    "will cause unpredictable behavior."
                )
            else:
                recommendations.append(
                    "Verify the execution order of multiple calculation groups matches your intent. "
                    "Document the expected behavior for future reference."
                )

        # Design pattern recommendations
        if len(groups) > 2:
            recommendations.append(
                "Consider using variables (VAR) to cache calculation group results when "
                "the same calculation group is referenced multiple times."
            )

        # General best practices
        if groups:
            recommendations.append(
                "Ensure the 'Discourage implicit measures' property is enabled in your model, "
                "as calculation items don't apply to implicit measures."
            )

            # Check if composite model warning is needed
            recommendations.append(
                "If using a composite model, ensure calculation groups are in the 'local' part "
                "while measures are in the 'remote' part for proper functionality."
            )

        return recommendations

    def get_all_calculation_groups(self) -> Dict[str, Any]:
        """Get information about all calculation groups in the model"""
        if not self._groups_loaded:
            self.load_calculation_groups()

        return {
            "success": True,
            "total_groups": len(self._calc_groups),
            "groups": [
                {
                    "name": g.name,
                    "precedence": g.precedence,
                    "item_count": len(g.items),
                    "items": g.items,
                    "description": g.description
                }
                for g in self._calc_groups.values()
            ],
            "has_precedence_issues": self._check_duplicate_precedence()
        }

    def _check_duplicate_precedence(self) -> bool:
        """Check if any calculation groups have duplicate precedence values"""
        precedences = [g.precedence for g in self._calc_groups.values()]
        return len(precedences) != len(set(precedences))

    def suggest_consolidation(self, groups: List[str]) -> Dict[str, Any]:
        """
        Suggest how to consolidate multiple calculation groups

        Args:
            groups: List of calculation group names to consolidate

        Returns:
            Consolidation suggestion with example code
        """
        if len(groups) < 2:
            return {
                "success": False,
                "message": "Need at least 2 groups to consolidate"
            }

        # Get the calculation groups
        calc_groups = [self._calc_groups.get(name) for name in groups if name in self._calc_groups]

        if not calc_groups:
            return {
                "success": False,
                "message": "Specified groups not found"
            }

        # Generate SWITCH-based consolidation example
        example_code = self._generate_consolidation_code(calc_groups)

        return {
            "success": True,
            "original_groups": [g.name for g in calc_groups],
            "total_items_before": sum(len(g.items) for g in calc_groups),
            "total_items_after": sum(len(g.items) for g in calc_groups),  # Same count, but consolidated
            "estimated_performance_gain": "10-30%",
            "example_code": example_code,
            "recommendation": (
                "Consolidate multiple calculation groups into a single group using SWITCH "
                "for better performance. This reduces evaluation overhead and simplifies "
                "precedence management."
            )
        }

    def _generate_consolidation_code(self, groups: List[CalculationGroup]) -> str:
        """Generate example code for consolidating calculation groups"""
        lines = [
            "-- Consolidated Calculation Group",
            "-- Combines: " + ", ".join(g.name for g in groups),
            "",
            "VAR SelectedItem = SELECTEDMEASURENAME()",
            "VAR Result = ",
            "    SWITCH(",
            "        TRUE(),"
        ]

        # Add cases for each group's items
        for group in groups:
            for item in group.items[:3]:  # Show first 3 items as examples
                lines.append(f'        SelectedItem = "{group.name} - {item}",')
                lines.append(f'            [YourCalculationFor_{item.replace(" ", "")}],')
                lines.append("")

        lines.extend([
            "        SELECTEDMEASURE()  // Default case",
            "    )",
            "RETURN Result",
            "",
            "-- NOTE: This is a template. Adapt the SWITCH logic to your specific calculations."
        ])

        return "\n".join(lines)
