"""
Enhanced PBIP Analyzer - Comprehensive analysis including BPA, lineage, quality metrics.

This module provides advanced analysis capabilities for PBIP projects including:
- Best Practice Analysis (BPA) integration
- Column-level lineage and impact analysis
- Data type and cardinality analysis
- Relationship quality metrics
- DAX code quality metrics
- Calculation group analysis
- Perspective analysis
- Naming convention validation
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ColumnLineageAnalyzer:
    """Analyzes column-level lineage and impact across the model."""

    def __init__(self, model_data: Dict, dependencies: Dict, report_data: Optional[Dict] = None):
        """
        Initialize lineage analyzer.

        Args:
            model_data: Parsed model data
            dependencies: Dependency analysis results
            report_data: Optional report data for visual usage
        """
        self.model = model_data
        self.dependencies = dependencies
        self.report = report_data
        self.logger = logger

    def analyze_column_lineage(self) -> Dict[str, Any]:
        """
        Analyze column lineage from source to destination.

        Returns:
            Dictionary with lineage information for each column
        """
        lineage_map = {}

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for column in table.get("columns", []):
                column_name = column.get("name", "")
                column_key = f"{table_name}[{column_name}]"

                lineage_info = {
                    "table": table_name,
                    "column": column_name,
                    "data_type": column.get("data_type", "Unknown"),
                    "is_calculated": bool(column.get("expression", "")),
                    "source_expression": column.get("expression", ""),
                    "used_in_measures": self.dependencies.get("column_to_measure", {}).get(column_key, []),
                    "used_in_relationships": self._find_relationship_usage(table_name, column_name),
                    "used_in_visuals": self._find_visual_usage(column_key),
                    "upstream_columns": [],  # Columns this column depends on
                    "downstream_usage": {}   # Where this column is used
                }

                # Calculate usage score
                usage_count = (
                    len(lineage_info["used_in_measures"]) +
                    len(lineage_info["used_in_relationships"]) +
                    len(lineage_info["used_in_visuals"])
                )
                lineage_info["usage_score"] = usage_count
                lineage_info["is_orphan"] = column_key in self.dependencies.get("unused_columns", [])

                lineage_map[column_key] = lineage_info

        return lineage_map

    def _find_relationship_usage(self, table_name: str, column_name: str) -> List[Dict[str, str]]:
        """Find relationships that use this column."""
        relationships = []

        for rel in self.model.get("relationships", []):
            from_table = rel.get("from_table", rel.get("fromTable", ""))
            from_col = rel.get("from_column", rel.get("fromColumn", ""))
            to_table = rel.get("to_table", rel.get("toTable", ""))
            to_col = rel.get("to_column", rel.get("toColumn", ""))

            if (from_table == table_name and from_col == column_name):
                relationships.append({
                    "role": "from",
                    "to_table": to_table,
                    "to_column": to_col,
                    "cardinality": rel.get("cardinality", rel.get("multiplicity", ""))
                })
            elif (to_table == table_name and to_col == column_name):
                relationships.append({
                    "role": "to",
                    "from_table": from_table,
                    "from_column": from_col,
                    "cardinality": rel.get("cardinality", rel.get("multiplicity", ""))
                })

        return relationships

    def _find_visual_usage(self, column_key: str) -> List[Dict[str, str]]:
        """Find visuals that use this column."""
        if not self.report:
            return []

        visuals = []
        visual_deps = self.dependencies.get("visual_dependencies", {})

        for visual_key, deps in visual_deps.items():
            if column_key in deps.get("columns", []):
                visuals.append({
                    "visual_key": visual_key,
                    "visual_type": deps.get("visual_type", ""),
                    "page": deps.get("page", "")
                })

        return visuals

    def calculate_column_impact(self, column_key: str) -> Dict[str, Any]:
        """
        Calculate the impact of changing or removing a column.

        Args:
            column_key: Column identifier (Table[Column])

        Returns:
            Dictionary with impact analysis
        """
        lineage = self.analyze_column_lineage()

        if column_key not in lineage:
            return {"error": f"Column {column_key} not found"}

        col_info = lineage[column_key]

        return {
            "column": column_key,
            "direct_impact": {
                "measures": len(col_info["used_in_measures"]),
                "relationships": len(col_info["used_in_relationships"]),
                "visuals": len(col_info["used_in_visuals"])
            },
            "affected_objects": {
                "measures": col_info["used_in_measures"],
                "relationships": col_info["used_in_relationships"],
                "visuals": col_info["used_in_visuals"]
            },
            "risk_level": self._calculate_risk_level(col_info),
            "recommendations": self._generate_column_recommendations(col_info)
        }

    def _calculate_risk_level(self, col_info: Dict) -> str:
        """Calculate risk level for column changes."""
        usage_score = col_info["usage_score"]

        if usage_score == 0:
            return "LOW"  # Unused column
        elif usage_score <= 3:
            return "MEDIUM"
        elif usage_score <= 10:
            return "HIGH"
        else:
            return "CRITICAL"

    def _generate_column_recommendations(self, col_info: Dict) -> List[str]:
        """Generate recommendations for column usage."""
        recommendations = []

        if col_info["is_orphan"]:
            recommendations.append("This column appears to be unused and could be removed to reduce model size")

        if col_info["is_calculated"] and len(col_info["used_in_measures"]) == 0:
            recommendations.append("Consider moving this calculated column logic to a measure for better performance")

        if len(col_info["used_in_relationships"]) > 0 and col_info["is_calculated"]:
            recommendations.append("WARNING: Calculated columns in relationships can cause performance issues")

        return recommendations


class DataTypeCardinalityAnalyzer:
    """Analyzes data types and cardinality for optimization recommendations."""

    def __init__(self, model_data: Dict):
        """Initialize analyzer with model data."""
        self.model = model_data
        self.logger = logger

    def analyze_data_types(self) -> Dict[str, Any]:
        """
        Analyze data types for optimization opportunities.

        Returns:
            Dictionary with data type analysis results
        """
        type_issues = []
        type_summary = Counter()

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for column in table.get("columns", []):
                column_name = column.get("name", "")
                data_type = column.get("data_type", "String")

                type_summary[data_type] += 1

                # Check for inefficient data types
                issues = self._check_data_type_issues(table_name, column_name, data_type, column)
                type_issues.extend(issues)

        return {
            "type_summary": dict(type_summary),
            "type_issues": type_issues,
            "recommendations": self._generate_type_recommendations(type_issues)
        }

    def _check_data_type_issues(
        self,
        table_name: str,
        column_name: str,
        data_type: str,
        column: Dict
    ) -> List[Dict[str, Any]]:
        """Check for data type optimization opportunities."""
        issues = []

        # Int64 could be Int32
        if data_type == "Int64":
            issues.append({
                "severity": "INFO",
                "table": table_name,
                "column": column_name,
                "current_type": data_type,
                "issue": "Int64 columns use more memory than Int32",
                "recommendation": "Consider using Int32 if values fit within -2,147,483,648 to 2,147,483,647",
                "impact": "MEDIUM"
            })

        # Decimal should be Double for aggregations
        if data_type == "Decimal" and not column.get("expression"):
            issues.append({
                "severity": "WARNING",
                "table": table_name,
                "column": column_name,
                "current_type": data_type,
                "issue": "Decimal type can be slower for aggregations",
                "recommendation": "Use Double for numeric columns that will be aggregated",
                "impact": "MEDIUM"
            })

        # String length analysis (if format_string contains length hint)
        if data_type == "String":
            # Check for potential date/time strings
            if any(kw in column_name.lower() for kw in ["date", "time", "year", "month"]):
                issues.append({
                    "severity": "WARNING",
                    "table": table_name,
                    "column": column_name,
                    "current_type": data_type,
                    "issue": "Date/time data stored as string",
                    "recommendation": "Use DateTime or Int64 (YYYYMMDD) for better performance",
                    "impact": "HIGH"
                })

        return issues

    def _generate_type_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate summary recommendations from type issues."""
        recommendations = []

        high_impact = [i for i in issues if i.get("impact") == "HIGH"]
        if high_impact:
            recommendations.append(
                f"Found {len(high_impact)} high-impact data type issues that should be addressed"
            )

        int64_count = len([i for i in issues if i.get("current_type") == "Int64"])
        if int64_count > 5:
            recommendations.append(
                f"Consider reviewing {int64_count} Int64 columns for potential Int32 conversion"
            )

        return recommendations

    def analyze_cardinality(self) -> Dict[str, Any]:
        """
        Analyze column cardinality for performance insights.

        Note: This provides static analysis. Runtime cardinality requires Vertipaq Analyzer.

        Returns:
            Dictionary with cardinality analysis
        """
        cardinality_warnings = []

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for column in table.get("columns", []):
                column_name = column.get("name", "")
                data_type = column.get("data_type", "")

                # Heuristic warnings
                warnings = self._check_cardinality_heuristics(table_name, column_name, data_type, column)
                cardinality_warnings.extend(warnings)

        return {
            "cardinality_warnings": cardinality_warnings,
            "summary": {
                "total_warnings": len(cardinality_warnings),
                "high_cardinality_columns": len([w for w in cardinality_warnings if w.get("type") == "high"])
            }
        }

    def _check_cardinality_heuristics(
        self,
        table_name: str,
        column_name: str,
        data_type: str,
        column: Dict
    ) -> List[Dict[str, Any]]:
        """Check for potential high-cardinality issues using heuristics."""
        warnings = []

        # ID columns are often high cardinality
        if re.search(r'\b(id|key|guid|uuid)\b', column_name, re.IGNORECASE):
            warnings.append({
                "type": "high",
                "table": table_name,
                "column": column_name,
                "reason": "Column name suggests high cardinality (ID/Key)",
                "recommendation": "Mark as hidden if not used for filtering",
                "is_hidden": column.get("is_hidden", False)
            })

        # DateTime columns can be high cardinality
        if data_type == "DateTime":
            warnings.append({
                "type": "high",
                "table": table_name,
                "column": column_name,
                "reason": "DateTime columns have high cardinality",
                "recommendation": "Consider using separate Date and Time columns, or pre-aggregating data",
                "is_hidden": column.get("is_hidden", False)
            })

        return warnings


class RelationshipQualityAnalyzer:
    """Analyzes relationship quality and detects issues."""

    def __init__(self, model_data: Dict):
        """Initialize with model data."""
        self.model = model_data
        self.logger = logger

    def analyze_relationships(self) -> Dict[str, Any]:
        """
        Analyze all relationships for quality and issues.

        Returns:
            Dictionary with relationship analysis
        """
        relationship_issues = []
        relationship_metrics = {
            "total": 0,
            "one_to_many": 0,
            "many_to_one": 0,
            "one_to_one": 0,
            "many_to_many": 0,
            "bi_directional": 0,
            "inactive": 0,
            "issues_found": 0
        }

        for rel in self.model.get("relationships", []):
            relationship_metrics["total"] += 1

            # Count by cardinality
            cardinality = rel.get("cardinality", rel.get("multiplicity", ""))
            if "OneToMany" in cardinality or "1:*" in cardinality:
                relationship_metrics["one_to_many"] += 1
            elif "ManyToOne" in cardinality or "*:1" in cardinality:
                relationship_metrics["many_to_one"] += 1
            elif "OneToOne" in cardinality or "1:1" in cardinality:
                relationship_metrics["one_to_one"] += 1
            elif "ManyToMany" in cardinality or "*:*" in cardinality:
                relationship_metrics["many_to_many"] += 1

            # Check for bi-directional
            cross_filter = rel.get("cross_filter_behavior", rel.get("crossFilteringBehavior", ""))
            if "BothDirections" in cross_filter or "both" in cross_filter.lower():
                relationship_metrics["bi_directional"] += 1

            # Check for inactive
            if not rel.get("is_active", rel.get("isActive", True)):
                relationship_metrics["inactive"] += 1

            # Analyze issues
            issues = self._check_relationship_issues(rel)
            relationship_issues.extend(issues)

        relationship_metrics["issues_found"] = len(relationship_issues)

        return {
            "metrics": relationship_metrics,
            "issues": relationship_issues,
            "recommendations": self._generate_relationship_recommendations(relationship_issues, relationship_metrics)
        }

    def _check_relationship_issues(self, rel: Dict) -> List[Dict[str, Any]]:
        """Check a single relationship for issues."""
        issues = []

        from_table = rel.get("from_table", rel.get("fromTable", ""))
        to_table = rel.get("to_table", rel.get("toTable", ""))
        cardinality = rel.get("cardinality", rel.get("multiplicity", ""))
        cross_filter = rel.get("cross_filter_behavior", rel.get("crossFilteringBehavior", ""))

        # Many-to-many warning
        if "ManyToMany" in cardinality or "*:*" in cardinality:
            issues.append({
                "severity": "ERROR",
                "type": "many_to_many",
                "from_table": from_table,
                "to_table": to_table,
                "issue": "Many-to-many relationship detected",
                "recommendation": "Use a bridge table to resolve many-to-many relationships",
                "impact": "HIGH"
            })

        # Bi-directional filtering warning
        if "BothDirections" in cross_filter or "both" in cross_filter.lower():
            issues.append({
                "severity": "WARNING",
                "type": "bi_directional",
                "from_table": from_table,
                "to_table": to_table,
                "issue": "Bi-directional cross-filtering enabled",
                "recommendation": "Avoid bi-directional filtering unless necessary; can cause performance issues and ambiguity",
                "impact": "MEDIUM"
            })

        # Circular dependency check (simple heuristic)
        if from_table == to_table:
            issues.append({
                "severity": "ERROR",
                "type": "self_reference",
                "from_table": from_table,
                "to_table": to_table,
                "issue": "Self-referencing relationship",
                "recommendation": "Review model design; self-references require careful handling",
                "impact": "HIGH"
            })

        return issues

    def _generate_relationship_recommendations(
        self,
        issues: List[Dict],
        metrics: Dict
    ) -> List[str]:
        """Generate relationship recommendations."""
        recommendations = []

        if metrics["many_to_many"] > 0:
            recommendations.append(
                f"Found {metrics['many_to_many']} many-to-many relationships. "
                "Consider using bridge tables for better performance."
            )

        if metrics["bi_directional"] > metrics["total"] * 0.3:  # More than 30%
            recommendations.append(
                f"{metrics['bi_directional']} relationships use bi-directional filtering. "
                "This can impact performance and query clarity."
            )

        if metrics["inactive"] > 0:
            recommendations.append(
                f"Found {metrics['inactive']} inactive relationships. "
                "Review if these are needed or should be removed."
            )

        return recommendations


class DaxCodeQualityAnalyzer:
    """Analyzes DAX code quality metrics."""

    def __init__(self, model_data: Dict):
        """Initialize with model data."""
        self.model = model_data
        self.logger = logger

    def analyze_dax_quality(self) -> Dict[str, Any]:
        """
        Analyze DAX code quality across all measures.

        Returns:
            Dictionary with DAX quality metrics
        """
        quality_issues = []
        complexity_scores = []

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for measure in table.get("measures", []):
                measure_name = measure.get("name", "")
                expression = measure.get("expression", "")

                if not expression:
                    continue

                # Calculate metrics
                metrics = self._calculate_dax_metrics(expression)
                complexity_scores.append(metrics["complexity_score"])

                # Check for issues
                issues = self._check_dax_issues(table_name, measure_name, expression, metrics)
                quality_issues.extend(issues)

        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0

        return {
            "quality_issues": quality_issues,
            "summary": {
                "total_measures": len(complexity_scores),
                "avg_complexity": round(avg_complexity, 2),
                "high_complexity_measures": len([s for s in complexity_scores if s > 15]),
                "total_issues": len(quality_issues)
            }
        }

    def _calculate_dax_metrics(self, expression: str) -> Dict[str, Any]:
        """Calculate DAX complexity metrics."""
        # Cyclomatic complexity (simplified)
        complexity_score = 1  # Base complexity
        complexity_score += expression.upper().count("IF(")
        complexity_score += expression.upper().count("SWITCH(")
        complexity_score += expression.upper().count("AND(")
        complexity_score += expression.upper().count("OR(")

        # Nesting depth
        max_nesting = self._calculate_max_nesting(expression)

        # Function count
        function_count = len(re.findall(r'\b[A-Z][A-Z0-9_]*\s*\(', expression))

        # Variable usage
        variable_count = expression.upper().count("VAR ")

        # Length
        expression_length = len(expression)

        # Calculate score
        total_score = (
            complexity_score +
            (max_nesting * 2) +
            (function_count * 0.5) +
            (expression_length / 100)
        )

        return {
            "complexity_score": round(total_score, 2),
            "max_nesting": max_nesting,
            "function_count": function_count,
            "variable_count": variable_count,
            "expression_length": expression_length,
            "has_variables": variable_count > 0
        }

    def _calculate_max_nesting(self, expression: str) -> int:
        """Calculate maximum parenthesis nesting depth."""
        max_depth = 0
        current_depth = 0

        for char in expression:
            if char == '(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ')':
                current_depth -= 1

        return max_depth

    def _check_dax_issues(
        self,
        table_name: str,
        measure_name: str,
        expression: str,
        metrics: Dict
    ) -> List[Dict[str, Any]]:
        """Check for DAX anti-patterns and issues."""
        issues = []

        # High complexity
        if metrics["complexity_score"] > 15:
            issues.append({
                "severity": "WARNING",
                "type": "high_complexity",
                "table": table_name,
                "measure": measure_name,
                "issue": f"High complexity score: {metrics['complexity_score']}",
                "recommendation": "Consider breaking this measure into smaller, reusable measures",
                "complexity_score": metrics["complexity_score"]
            })

        # Deep nesting
        if metrics["max_nesting"] > 5:
            issues.append({
                "severity": "WARNING",
                "type": "deep_nesting",
                "table": table_name,
                "measure": measure_name,
                "issue": f"Deep nesting level: {metrics['max_nesting']}",
                "recommendation": "Use variables to flatten nested expressions"
            })

        # CALCULATE anti-pattern
        if expression.upper().count("CALCULATE") > 3:
            issues.append({
                "severity": "INFO",
                "type": "excessive_calculate",
                "table": table_name,
                "measure": measure_name,
                "issue": "Multiple CALCULATE functions detected",
                "recommendation": "Review if calculations can be simplified or combined"
            })

        # No variables in complex measure
        if metrics["complexity_score"] > 10 and not metrics["has_variables"]:
            issues.append({
                "severity": "INFO",
                "type": "no_variables",
                "table": table_name,
                "measure": measure_name,
                "issue": "Complex measure without variables",
                "recommendation": "Use VAR to improve readability and potentially performance"
            })

        # SUMX with FILTER (potential performance issue)
        if re.search(r'SUMX\s*\(\s*FILTER', expression, re.IGNORECASE):
            issues.append({
                "severity": "WARNING",
                "type": "sumx_filter",
                "table": table_name,
                "measure": measure_name,
                "issue": "SUMX(FILTER(...)) pattern detected",
                "recommendation": "Consider using CALCULATE with filters for better performance"
            })

        return issues


class NamingConventionValidator:
    """Validates object naming conventions."""

    def __init__(self, model_data: Dict):
        """Initialize validator."""
        self.model = model_data
        self.logger = logger

    def validate_naming_conventions(self, rules: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Validate naming conventions against customizable rules.

        Args:
            rules: Optional dictionary of naming rules (e.g., {"measure_prefix": "m_"})

        Returns:
            Dictionary with validation results
        """
        # Default rules
        default_rules = {
            "measure_prefix": "",  # Empty = no required prefix
            "table_pascal_case": True,
            "column_pascal_case": True,
            "no_spaces": False,  # Allow spaces by default
            "max_length": 100
        }

        if rules:
            default_rules.update(rules)

        violations = []

        # Check table names
        for table in self.model.get("tables", []):
            table_name = table.get("name", "")
            table_violations = self._check_name_conventions(
                table_name,
                "Table",
                table_name,
                None,
                default_rules
            )
            violations.extend(table_violations)

            # Check columns
            for column in table.get("columns", []):
                column_name = column.get("name", "")
                col_violations = self._check_name_conventions(
                    column_name,
                    "Column",
                    table_name,
                    column_name,
                    default_rules
                )
                violations.extend(col_violations)

            # Check measures
            for measure in table.get("measures", []):
                measure_name = measure.get("name", "")
                measure_violations = self._check_name_conventions(
                    measure_name,
                    "Measure",
                    table_name,
                    measure_name,
                    default_rules,
                    prefix_rule=default_rules.get("measure_prefix")
                )
                violations.extend(measure_violations)

        return {
            "violations": violations,
            "summary": {
                "total_violations": len(violations),
                "by_type": self._count_by_type(violations),
                "by_severity": self._count_by_severity(violations)
            }
        }

    def _check_name_conventions(
        self,
        name: str,
        obj_type: str,
        table_name: str,
        obj_name: Optional[str],
        rules: Dict,
        prefix_rule: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Check a single name against conventions."""
        violations = []

        # Prefix check
        if prefix_rule and not name.startswith(prefix_rule):
            violations.append({
                "severity": "INFO",
                "type": "missing_prefix",
                "object_type": obj_type,
                "table": table_name,
                "object": obj_name or name,
                "issue": f"Missing prefix '{prefix_rule}'",
                "current_name": name
            })

        # Spaces check
        if rules.get("no_spaces") and ' ' in name:
            violations.append({
                "severity": "INFO",
                "type": "contains_spaces",
                "object_type": obj_type,
                "table": table_name,
                "object": obj_name or name,
                "issue": "Name contains spaces",
                "current_name": name
            })

        # Length check
        max_len = rules.get("max_length", 100)
        if len(name) > max_len:
            violations.append({
                "severity": "WARNING",
                "type": "name_too_long",
                "object_type": obj_type,
                "table": table_name,
                "object": obj_name or name,
                "issue": f"Name exceeds {max_len} characters ({len(name)})",
                "current_name": name
            })

        # Special characters check
        if re.search(r'[^\w\s\-_]', name):
            violations.append({
                "severity": "WARNING",
                "type": "special_characters",
                "object_type": obj_type,
                "table": table_name,
                "object": obj_name or name,
                "issue": "Name contains special characters",
                "current_name": name
            })

        return violations

    def _count_by_type(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by type."""
        counts = Counter(v["type"] for v in violations)
        return dict(counts)

    def _count_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """Count violations by severity."""
        counts = Counter(v["severity"] for v in violations)
        return dict(counts)


class PerspectiveAnalyzer:
    """Analyzes perspectives and object visibility."""

    def __init__(self, model_data: Dict):
        """Initialize analyzer."""
        self.model = model_data
        self.logger = logger

    def analyze_perspectives(self) -> Dict[str, Any]:
        """
        Analyze perspective usage and coverage.

        Returns:
            Dictionary with perspective analysis
        """
        perspectives = self.model.get("perspectives", [])

        if not perspectives:
            return {
                "has_perspectives": False,
                "message": "No perspectives defined in the model"
            }

        perspective_analysis = []

        for persp in perspectives:
            persp_name = persp.get("name", "")
            persp_items = persp.get("perspectiveTableReferences", [])

            # Count objects in perspective
            table_count = len(persp_items)
            column_count = sum(
                len(item.get("perspectiveColumnReferences", []))
                for item in persp_items
            )
            measure_count = sum(
                len(item.get("perspectiveMeasureReferences", []))
                for item in persp_items
            )

            perspective_analysis.append({
                "name": persp_name,
                "table_count": table_count,
                "column_count": column_count,
                "measure_count": measure_count,
                "total_objects": table_count + column_count + measure_count
            })

        # Check for unused perspectives (empty)
        unused_perspectives = [p for p in perspective_analysis if p["total_objects"] == 0]

        return {
            "has_perspectives": True,
            "perspective_count": len(perspectives),
            "perspectives": perspective_analysis,
            "unused_perspectives": unused_perspectives,
            "summary": {
                "total_perspectives": len(perspectives),
                "unused_count": len(unused_perspectives)
            }
        }


class EnhancedPbipAnalyzer:
    """
    Main enhanced analyzer that orchestrates all analysis components.
    """

    def __init__(self, model_data: Dict, report_data: Optional[Dict] = None, dependencies: Optional[Dict] = None):
        """
        Initialize enhanced analyzer.

        Args:
            model_data: Parsed model data
            report_data: Optional report data
            dependencies: Optional pre-computed dependencies
        """
        self.model = model_data
        self.report = report_data
        self.dependencies = dependencies or {}
        self.logger = logger

        # Initialize sub-analyzers
        self.lineage_analyzer = ColumnLineageAnalyzer(model_data, self.dependencies, report_data)
        self.type_analyzer = DataTypeCardinalityAnalyzer(model_data)
        self.relationship_analyzer = RelationshipQualityAnalyzer(model_data)
        self.dax_analyzer = DaxCodeQualityAnalyzer(model_data)
        self.naming_validator = NamingConventionValidator(model_data)
        self.perspective_analyzer = PerspectiveAnalyzer(model_data)

    def _filter_bpa_violations(self, violations: List) -> List:
        """
        Filter BPA violations to remove false positives for PBIP analysis.

        PBIP analysis works with TMDL metadata files only - NO data access.
        We filter out:
        1. Usage-based violations (unused columns/measures) - use dependency analysis instead
        2. Data-based violations (empty columns, cardinality) - PBIP has no data access
        """
        from .bpa_analyzer import BPAViolation

        unused_columns_set = set(self.dependencies.get("unused_columns", []))
        unused_measures_set = set(self.dependencies.get("unused_measures", []))

        # Rules that require runtime data access (INVALID for PBIP analysis)
        DATA_DEPENDENT_RULES = {
            "AVOID_COLUMNS_WITH_NO_DATA",  # Can't check if columns are empty without data
            "NO_EMPTY_PARTITIONS",  # Can't check row counts without data
            "REDUCE_HIGH_CARDINALITY",  # Cardinality requires Vertipaq/runtime stats
        }

        filtered = []
        for v in violations:
            # Skip data-dependent rules entirely for PBIP analysis
            if v.rule_id in DATA_DEPENDENT_RULES:
                continue

            # For "Remove unused columns" rule, verify it's actually unused
            if v.rule_id == "REMOVE_UNUSED_COLUMNS":
                # Build column key
                if v.table_name and v.object_name:
                    col_key = f"{v.table_name}[{v.object_name}]"
                    # Only include if actually in unused set
                    if col_key in unused_columns_set:
                        filtered.append(v)
                continue

            # For "Remove unused measures" rule, verify it's actually unused
            if v.rule_id == "REMOVE_UNUSED_MEASURES":
                # Build measure key
                if v.table_name and v.object_name:
                    meas_key = f"{v.table_name}[{v.object_name}]"
                    # Only include if actually in unused set
                    if meas_key in unused_measures_set:
                        filtered.append(v)
                continue

            # Keep all other violations
            filtered.append(v)

        return filtered

    def _calculate_violations_summary(self, violations: List) -> Dict[str, Any]:
        """
        Calculate summary statistics for filtered BPA violations.
        """
        from collections import defaultdict

        total = len(violations)
        by_severity = defaultdict(int)
        by_category = defaultdict(int)

        for v in violations:
            by_severity[v.severity.name] += 1
            by_category[v.category] += 1

        return {
            "total": total,
            "by_severity": dict(by_severity),
            "by_category": dict(by_category)
        }

    def _transform_pbip_to_tmsl(self, pbip_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform PBIP model structure to TMSL structure for BPA analyzer compatibility.

        PBIP uses Python-style snake_case keys, but BPA rules expect TMSL camelCase/PascalCase.
        This method creates a TMSL-compatible copy with usage information from dependencies.
        """
        tmsl_model = {"tables": []}

        # Transform tables
        for table in pbip_model.get("tables", []):
            table_name = table.get("name")
            tmsl_table = {
                "name": table_name,
                "Name": table_name,  # Both cases for compatibility
                "IsHidden": table.get("is_hidden", False),
                "isHidden": table.get("is_hidden", False),
                "columns": [],
                "measures": []
            }

            # Transform columns
            for col in table.get("columns", []):
                col_name = col.get("name")

                tmsl_col = {
                    "name": col_name,
                    "Name": col_name,
                    "dataType": col.get("data_type", ""),
                    "DataType": col.get("data_type", ""),
                    "sourceColumn": col.get("source_column", ""),
                    "SourceColumn": col.get("source_column", ""),
                    "IsHidden": col.get("is_hidden", False),
                    "isHidden": col.get("is_hidden", False),
                    "formatString": col.get("format_string", ""),
                    "FormatString": col.get("format_string", ""),
                    "dataCategory": col.get("data_category", ""),
                    "DataCategory": col.get("data_category", ""),
                    "displayFolder": col.get("display_folder", ""),
                    "DisplayFolder": col.get("display_folder", ""),
                    "description": col.get("description", ""),
                    "Description": col.get("description", ""),
                    "Expression": col.get("expression", "")  # For calculated columns
                }
                tmsl_table["columns"].append(tmsl_col)

            # Transform measures
            for meas in table.get("measures", []):
                tmsl_meas = {
                    "name": meas.get("name"),
                    "Name": meas.get("name"),
                    "expression": meas.get("expression", ""),
                    "Expression": meas.get("expression", ""),
                    "formatString": meas.get("format_string", ""),
                    "FormatString": meas.get("format_string", ""),
                    "isHidden": meas.get("is_hidden", False),
                    "IsHidden": meas.get("is_hidden", False),
                    "displayFolder": meas.get("display_folder", ""),
                    "DisplayFolder": meas.get("display_folder", ""),
                    "description": meas.get("description", ""),
                    "Description": meas.get("description", "")
                }
                tmsl_table["measures"].append(tmsl_meas)

            tmsl_model["tables"].append(tmsl_table)

        # Transform relationships
        tmsl_model["relationships"] = []
        for rel in pbip_model.get("relationships", []):
            tmsl_rel = {
                "name": rel.get("name"),
                "Name": rel.get("name"),
                "fromColumn": rel.get("from_column", ""),
                "FromColumn": rel.get("from_column", ""),
                "toColumn": rel.get("to_column", ""),
                "ToColumn": rel.get("to_column", ""),
                "crossFilteringBehavior": rel.get("cross_filtering_behavior", "oneDirection"),
                "CrossFilteringBehavior": rel.get("cross_filtering_behavior", "oneDirection"),
                "isActive": rel.get("is_active", True),
                "IsActive": rel.get("is_active", True),
                "securityFilteringBehavior": rel.get("security_filtering_behavior", "oneDirection"),
                "SecurityFilteringBehavior": rel.get("security_filtering_behavior", "oneDirection"),
                # Add cardinality/multiplicity based on cross filtering
                "Multiplicity": "OneToMany",  # Default, would need more logic to determine actual cardinality
                "multiplicity": "OneToMany"
            }
            tmsl_model["relationships"].append(tmsl_rel)

        return tmsl_model

    def run_full_analysis(self, bpa_rules_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run complete enhanced analysis.

        Args:
            bpa_rules_path: Optional path to BPA rules JSON file

        Returns:
            Dictionary with all analysis results
        """
        self.logger.info("Starting enhanced PBIP analysis")

        results = {
            "timestamp": datetime.now().isoformat(),
            "model_name": self.model.get("name", "Unknown"),
            "analyses": {}
        }

        # 1. Column Lineage & Impact Analysis
        self.logger.info("Analyzing column lineage...")
        results["analyses"]["column_lineage"] = self.lineage_analyzer.analyze_column_lineage()

        # 2. Data Type & Cardinality Analysis
        self.logger.info("Analyzing data types and cardinality...")
        results["analyses"]["data_types"] = self.type_analyzer.analyze_data_types()
        results["analyses"]["cardinality"] = self.type_analyzer.analyze_cardinality()

        # 3. Relationship Quality Metrics
        self.logger.info("Analyzing relationship quality...")
        results["analyses"]["relationships"] = self.relationship_analyzer.analyze_relationships()

        # 4. DAX Code Quality Metrics
        self.logger.info("Analyzing DAX code quality...")
        results["analyses"]["dax_quality"] = self.dax_analyzer.analyze_dax_quality()

        # 5. Naming Convention Validation
        self.logger.info("Validating naming conventions...")
        results["analyses"]["naming_conventions"] = self.naming_validator.validate_naming_conventions()

        # 6. Perspective Analysis
        self.logger.info("Analyzing perspectives...")
        results["analyses"]["perspectives"] = self.perspective_analyzer.analyze_perspectives()

        # 7. BPA Analysis (if rules provided)
        if bpa_rules_path:
            self.logger.info("Running Best Practice Analyzer...")
            try:
                from .bpa_analyzer import BPAAnalyzer
                bpa = BPAAnalyzer(bpa_rules_path)
                # Transform PBIP model structure to TMSL structure for BPA compatibility
                tmsl_model = self._transform_pbip_to_tmsl(self.model)
                violations = bpa.analyze_model(tmsl_model)

                # Filter violations to remove false positives based on dependency analysis
                filtered_violations = self._filter_bpa_violations(violations)

                # Recalculate summary based on filtered violations
                filtered_summary = self._calculate_violations_summary(filtered_violations)

                results["analyses"]["bpa"] = {
                    "violations": [
                        {
                            "rule_id": v.rule_id,
                            "rule_name": v.rule_name,
                            "category": v.category,
                            "severity": v.severity.name,
                            "description": v.description,
                            "object_type": v.object_type,
                            "object_name": v.object_name,
                            "table_name": v.table_name,
                            "details": v.details
                        }
                        for v in filtered_violations
                    ],
                    "summary": filtered_summary
                }
            except Exception as e:
                self.logger.error(f"BPA analysis failed: {e}")
                results["analyses"]["bpa"] = {"error": str(e)}

        self.logger.info("Enhanced analysis complete")

        return results
