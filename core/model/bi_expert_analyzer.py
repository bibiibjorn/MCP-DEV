"""
BI Expert Analyzer - Provides expert-level analysis and insights for Power BI models

This module acts as a BI expert, providing intelligent insights about:
- Model architecture and design patterns
- Relationship quality and star schema adherence
- Measure complexity and best practices
- Data model optimization opportunities
- Performance concerns
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BIExpertAnalyzer:
    """Provides expert-level BI analysis and insights"""

    @staticmethod
    def analyze_model_overview(metadata: Dict[str, Any], relationships: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Provide expert analysis of model overview

        Args:
            metadata: Model metadata
            relationships: List of relationships (optional)

        Returns:
            Expert analysis with insights and recommendations
        """
        analysis = {
            "summary": "",
            "architecture_assessment": {},
            "insights": [],
            "recommendations": [],
            "health_score": 0
        }

        # Extract statistics
        stats = metadata.get("statistics", {})
        tables = stats.get("tables", {})
        measures_info = stats.get("measures", {})
        relationships_info = stats.get("relationships", {})
        row_counts = metadata.get("row_counts", {})

        table_count = tables.get("total", 0)
        measure_count = measures_info.get("total", 0)
        relationship_count = relationships_info.get("total", 0)

        # Calculate total rows
        total_rows = 0
        fact_tables = []
        dim_tables = []
        if isinstance(row_counts, dict):
            for table_name, row_count in row_counts.items():
                if isinstance(row_count, (int, float)):
                    total_rows += row_count
                    # Heuristic: tables with >100k rows are likely fact tables
                    if row_count > 100000:
                        fact_tables.append({"name": table_name, "rows": row_count})
                    else:
                        dim_tables.append({"name": table_name, "rows": row_count})

        # Architecture Assessment
        if table_count > 0:
            # Assess model complexity
            if table_count <= 5:
                complexity = "Simple"
                complexity_note = "Small model, easy to maintain"
            elif table_count <= 15:
                complexity = "Moderate"
                complexity_note = "Well-sized model, manageable complexity"
            elif table_count <= 30:
                complexity = "Complex"
                complexity_note = "Large model, requires careful organization"
            else:
                complexity = "Very Complex"
                complexity_note = "Enterprise-scale model, consider modularization"

            analysis["architecture_assessment"] = {
                "complexity": complexity,
                "complexity_note": complexity_note,
                "table_count": table_count,
                "measure_count": measure_count,
                "relationship_count": relationship_count,
                "total_rows": total_rows,
                "estimated_fact_tables": len(fact_tables),
                "estimated_dimension_tables": len(dim_tables)
            }

            # Star Schema Assessment
            if len(fact_tables) > 0 and len(dim_tables) > 0:
                ratio = len(dim_tables) / max(len(fact_tables), 1)
                if 2 <= ratio <= 10:
                    schema_quality = "Good"
                    schema_note = "Healthy fact-to-dimension ratio, likely follows star schema pattern"
                elif ratio > 10:
                    schema_quality = "Review Needed"
                    schema_note = "High dimension-to-fact ratio, may indicate over-normalization"
                else:
                    schema_quality = "Review Needed"
                    schema_note = "Low dimension-to-fact ratio, may need more dimensional modeling"

                analysis["architecture_assessment"]["star_schema_quality"] = schema_quality
                analysis["architecture_assessment"]["schema_note"] = schema_note

        # Generate insights
        if measure_count > 0 and table_count > 0:
            measures_per_table = measure_count / table_count
            if measures_per_table > 10:
                analysis["insights"].append({
                    "type": "measure_organization",
                    "severity": "info",
                    "message": f"High measure density ({measures_per_table:.1f} measures per table). Consider using display folders for better organization."
                })

        if relationship_count > 0 and table_count > 1:
            rels_per_table = relationship_count / table_count
            if rels_per_table < 0.5:
                analysis["insights"].append({
                    "type": "relationships",
                    "severity": "warning",
                    "message": "Low relationship count relative to tables. Some tables may be disconnected from the model."
                })
            elif rels_per_table > 3:
                analysis["insights"].append({
                    "type": "relationships",
                    "severity": "info",
                    "message": "High relationship density suggests a well-connected model, but verify no circular dependencies exist."
                })

        if total_rows > 10000000:
            analysis["insights"].append({
                "type": "performance",
                "severity": "info",
                "message": f"Large dataset ({total_rows:,} total rows). Consider implementing aggregations or incremental refresh for optimal performance."
            })

        # Generate recommendations
        if len(fact_tables) > 5:
            analysis["recommendations"].append({
                "priority": "medium",
                "category": "performance",
                "recommendation": f"Model has {len(fact_tables)} large tables. Review if aggregations are needed for high-cardinality fact tables."
            })

        if measure_count == 0:
            analysis["recommendations"].append({
                "priority": "high",
                "category": "measures",
                "recommendation": "No measures detected. Add DAX measures for analytical insights rather than relying on implicit measures."
            })
        elif measure_count < 5:
            analysis["recommendations"].append({
                "priority": "low",
                "category": "measures",
                "recommendation": "Few measures defined. Consider creating more measures to encapsulate business logic."
            })

        # Calculate health score (0-100)
        health_score = 70  # Start with baseline

        # Positive factors
        if relationship_count > 0:
            health_score += 10
        if measure_count >= 5:
            health_score += 10
        if len(fact_tables) > 0 and len(dim_tables) > 0:
            health_score += 10

        # Negative factors
        if relationship_count == 0 and table_count > 1:
            health_score -= 20
        if measure_count == 0:
            health_score -= 15

        analysis["health_score"] = max(0, min(100, health_score))

        # Generate summary
        analysis["summary"] = BIExpertAnalyzer._generate_model_summary(
            table_count, measure_count, relationship_count, total_rows,
            len(fact_tables), len(dim_tables), health_score
        )

        return analysis

    @staticmethod
    def analyze_measure(measure_def: Dict[str, Any], include_dax_analysis: bool = True) -> Dict[str, Any]:
        """
        Provide expert analysis of a measure

        Args:
            measure_def: Measure definition with DAX expression
            include_dax_analysis: Whether to include DAX pattern analysis

        Returns:
            Expert analysis of the measure
        """
        analysis = {
            "measure_name": measure_def.get("name"),
            "insights": [],
            "complexity_assessment": {},
            "best_practices": [],
            "suggestions": []
        }

        expression = measure_def.get("expression", "")
        description = measure_def.get("description")

        # Complexity Analysis
        if expression:
            line_count = expression.count('\n') + 1
            char_count = len(expression)
            has_variables = 'VAR ' in expression.upper()
            has_iterator = any(func in expression.upper() for func in ['SUMX', 'AVERAGEX', 'FILTER', 'CALCULATE'])
            has_time_intelligence = any(func in expression.upper() for func in ['SAMEPERIODLASTYEAR', 'DATEADD', 'TOTALYTD', 'DATESYTD'])

            if line_count > 20:
                complexity = "High"
            elif line_count > 10:
                complexity = "Medium"
            else:
                complexity = "Low"

            analysis["complexity_assessment"] = {
                "complexity": complexity,
                "line_count": line_count,
                "character_count": char_count,
                "uses_variables": has_variables,
                "uses_iterators": has_iterator,
                "uses_time_intelligence": has_time_intelligence
            }

            # Best Practices Check
            if not has_variables and line_count > 5:
                analysis["best_practices"].append({
                    "status": "warning",
                    "practice": "Variable Usage",
                    "message": "Consider using VAR to improve readability and performance for complex calculations"
                })

            if not description:
                analysis["best_practices"].append({
                    "status": "warning",
                    "practice": "Documentation",
                    "message": "Add a description to document the measure's purpose and business logic"
                })
            else:
                analysis["best_practices"].append({
                    "status": "good",
                    "practice": "Documentation",
                    "message": "Measure has a description"
                })

            # Insights
            if has_iterator:
                analysis["insights"].append({
                    "type": "performance",
                    "message": "Uses iterator functions (X functions). Monitor performance on large datasets."
                })

            if has_time_intelligence:
                analysis["insights"].append({
                    "type": "functionality",
                    "message": "Implements time intelligence. Ensure your model has a proper date table."
                })

        # Format String Check
        format_string = measure_def.get("formatString")
        if format_string:
            analysis["insights"].append({
                "type": "formatting",
                "message": f"Has format string: {format_string}"
            })
        else:
            analysis["suggestions"].append({
                "priority": "low",
                "suggestion": "Add a format string for consistent number formatting"
            })

        return analysis

    @staticmethod
    def analyze_relationships(relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide expert analysis of relationships

        Args:
            relationships: List of relationship definitions

        Returns:
            Expert analysis of relationships
        """
        analysis = {
            "summary": "",
            "insights": [],
            "relationship_patterns": {},
            "recommendations": []
        }

        if not relationships:
            analysis["summary"] = "No relationships found in the model"
            analysis["recommendations"].append({
                "priority": "high",
                "message": "Define relationships between tables to enable cross-table analysis"
            })
            return analysis

        # Analyze relationship patterns
        one_to_many = 0
        many_to_one = 0
        one_to_one = 0
        many_to_many = 0
        inactive_count = 0
        bidirectional_count = 0

        for rel in relationships:
            from_card = rel.get("fromCardinality", "")
            to_card = rel.get("toCardinality", "")
            is_active = rel.get("isActive", True)
            cross_filter = rel.get("crossFilteringBehavior", "")

            # Count cardinalities
            if from_card == "one" and to_card == "many":
                one_to_many += 1
            elif from_card == "many" and to_card == "one":
                many_to_one += 1
            elif from_card == "one" and to_card == "one":
                one_to_one += 1
            elif from_card == "many" and to_card == "many":
                many_to_many += 1

            if not is_active:
                inactive_count += 1

            if cross_filter == "bothDirections":
                bidirectional_count += 1

        analysis["relationship_patterns"] = {
            "total": len(relationships),
            "one_to_many": one_to_many,
            "many_to_one": many_to_one,
            "one_to_one": one_to_one,
            "many_to_many": many_to_many,
            "inactive": inactive_count,
            "bidirectional": bidirectional_count
        }

        # Generate insights
        if one_to_many + many_to_one > 0:
            percentage = ((one_to_many + many_to_one) / len(relationships)) * 100
            analysis["insights"].append({
                "type": "star_schema",
                "severity": "good" if percentage > 80 else "info",
                "message": f"{percentage:.0f}% of relationships follow star schema pattern (one-to-many)"
            })

        if many_to_many > 0:
            analysis["insights"].append({
                "type": "many_to_many",
                "severity": "warning",
                "message": f"{many_to_many} many-to-many relationship(s) detected. These can impact performance and may indicate modeling issues."
            })

        if bidirectional_count > 0:
            analysis["insights"].append({
                "type": "bidirectional_filter",
                "severity": "warning",
                "message": f"{bidirectional_count} bidirectional relationship(s). Use sparingly as they can cause ambiguity and performance issues."
            })

        if inactive_count > 0:
            analysis["insights"].append({
                "type": "inactive_relationships",
                "severity": "info",
                "message": f"{inactive_count} inactive relationship(s). These are typically used with USERELATIONSHIP in DAX."
            })

        # Recommendations
        if many_to_many > len(relationships) * 0.2:
            analysis["recommendations"].append({
                "priority": "high",
                "category": "modeling",
                "message": "High proportion of many-to-many relationships. Consider introducing bridge tables to simplify the model."
            })

        if bidirectional_count > 2:
            analysis["recommendations"].append({
                "priority": "medium",
                "category": "performance",
                "message": "Multiple bidirectional relationships detected. Review if all are necessary, as they can cause circular dependencies."
            })

        # Generate summary
        analysis["summary"] = f"Model has {len(relationships)} relationships: {one_to_many + many_to_one} star schema patterns, "
        analysis["summary"] += f"{many_to_many} many-to-many, {inactive_count} inactive"

        return analysis

    @staticmethod
    def should_request_sample_data(operation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if sample data should be requested for the analysis

        Args:
            operation: The operation being performed
            context: Analysis context

        Returns:
            Guidance on whether sample data is needed
        """
        guidance = {
            "sample_data_recommended": False,
            "reason": "",
            "benefits": []
        }

        # Operations that benefit from sample data
        if operation in ["analyze_column", "profile_data", "validate_data_quality"]:
            guidance["sample_data_recommended"] = True
            guidance["reason"] = "Sample data required for this type of analysis"
            guidance["benefits"] = [
                "Validate data types and formats",
                "Identify data quality issues",
                "Analyze value distributions"
            ]

        elif operation == "get_object_definition" and context.get("object_type") == "table":
            guidance["sample_data_recommended"] = True
            guidance["reason"] = "Sample data helps understand table content"
            guidance["benefits"] = [
                "Preview actual data values",
                "Verify column contents match expectations",
                "Identify potential data issues"
            ]

        return guidance

    @staticmethod
    def _generate_model_summary(table_count: int, measure_count: int, relationship_count: int,
                               total_rows: int, fact_tables: int, dim_tables: int, health_score: int) -> str:
        """Generate a concise model summary"""
        summary = f"This Power BI model contains {table_count} tables ({fact_tables} fact, {dim_tables} dimension), "
        summary += f"{measure_count} measures, and {relationship_count} relationships. "
        summary += f"Total dataset size: {total_rows:,} rows. "

        if health_score >= 80:
            summary += "Overall health: GOOD - Model follows best practices. "
        elif health_score >= 60:
            summary += "Overall health: FAIR - Some optimization opportunities exist. "
        else:
            summary += "Overall health: NEEDS ATTENTION - Several issues require review. "

        return summary
