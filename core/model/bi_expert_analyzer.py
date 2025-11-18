"""
BI Expert Analyzer - Provides expert-level analysis and insights for Power BI models

This module acts as a BI expert, providing intelligent insights about:
- Model architecture and design patterns
- Relationship quality and star schema adherence
- Measure complexity and best practices
- Data model optimization opportunities
- Performance concerns
- Advanced DAX pattern analysis
- Context transition analysis
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# DAX Best Practice Categories
class DAXBestPracticeCategory:
    """Categories for DAX best practice violations"""
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    STANDARDS = "standards"


# Expert Insight Levels
class ExpertInsightLevel:
    """Levels of expert insights"""
    CRITICAL = "critical"      # Must fix - causes errors or severe performance issues
    HIGH = "high"              # Should fix - significant impact
    MEDIUM = "medium"          # Consider fixing - moderate impact
    LOW = "low"                # Nice to have - minor improvements
    INFO = "info"              # Informational only


class BIExpertAnalyzer:
    """Provides expert-level BI analysis and insights"""

    @staticmethod
    def analyze_model_overview(metadata: Dict[str, Any], relationships: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Provide comprehensive expert analysis of model overview with advanced insights

        Args:
            metadata: Model metadata
            relationships: List of relationships (optional)

        Returns:
            Expert analysis with insights, recommendations, and quality scoring
        """
        analysis = {
            "executive_summary": "",
            "architecture_assessment": {},
            "data_quality_indicators": {},
            "insights": [],
            "recommendations": [],
            "health_score": 0,
            "health_breakdown": {},
            "risk_factors": [],
            "strengths": []
        }

        # Extract statistics
        stats = metadata.get("statistics", {})
        tables = stats.get("tables", {})
        measures_info = stats.get("measures", {})
        relationships_info = stats.get("relationships", {})
        row_counts = metadata.get("row_counts", {})
        cardinality = metadata.get("cardinality", {})

        table_count = tables.get("total", 0)
        measure_count = measures_info.get("total", 0)
        relationship_count = relationships_info.get("total", 0)
        column_count = stats.get("columns", {}).get("total", 0)

        # Initialize health score components
        health_components = {
            "architecture": 0,        # max 30 points
            "relationships": 0,       # max 25 points
            "measures": 0,            # max 20 points
            "data_quality": 0,        # max 15 points
            "organization": 0         # max 10 points
        }

        # Analyze tables and classify as fact/dimension
        total_rows = 0
        fact_tables = []
        dim_tables = []
        small_tables = []  # Tables with < 100 rows (possible date/lookup tables)

        if isinstance(row_counts, dict):
            for table_name, row_count in row_counts.items():
                if isinstance(row_count, (int, float)):
                    total_rows += row_count

                    # Sophisticated classification
                    if row_count > 100000:
                        fact_tables.append({"name": table_name, "rows": row_count})
                    elif row_count < 100:
                        small_tables.append({"name": table_name, "rows": row_count})
                    else:
                        dim_tables.append({"name": table_name, "rows": row_count})

        # Sort tables by size for insights
        fact_tables.sort(key=lambda x: x["rows"], reverse=True)
        dim_tables.sort(key=lambda x: x["rows"], reverse=True)

        # === ARCHITECTURE ASSESSMENT ===
        if table_count > 0:
            # Assess model complexity with more nuance
            if table_count <= 5:
                complexity = "Simple"
                complexity_note = "Small model with minimal tables. Ideal for focused analytics scenarios."
                health_components["architecture"] = 30
            elif table_count <= 15:
                complexity = "Moderate"
                complexity_note = "Well-sized model with manageable complexity. Good balance for most business scenarios."
                health_components["architecture"] = 28
            elif table_count <= 30:
                complexity = "Complex"
                complexity_note = "Large model requiring disciplined organization. Consider display folders and clear naming conventions."
                health_components["architecture"] = 22
            else:
                complexity = "Very Complex"
                complexity_note = "Enterprise-scale model. Strongly consider composite models, calculation groups, or modularization."
                health_components["architecture"] = 15
                analysis["risk_factors"].append({
                    "risk": "Model Complexity",
                    "severity": ExpertInsightLevel.MEDIUM,
                    "description": f"{table_count} tables may impact maintainability and refresh performance",
                    "mitigation": "Consider splitting into multiple models or using composite models"
                })

            # Calculate column-to-table ratio for normalization insights
            columns_per_table = column_count / table_count if table_count > 0 else 0

            analysis["architecture_assessment"] = {
                "complexity": complexity,
                "complexity_note": complexity_note,
                "model_size": {
                    "tables": table_count,
                    "measures": measure_count,
                    "columns": column_count,
                    "relationships": relationship_count,
                    "total_rows": total_rows
                },
                "table_classification": {
                    "fact_tables": len(fact_tables),
                    "dimension_tables": len(dim_tables),
                    "small_lookup_tables": len(small_tables),
                    "largest_fact": fact_tables[0]["name"] if fact_tables else None,
                    "largest_fact_rows": fact_tables[0]["rows"] if fact_tables else 0
                },
                "architectural_metrics": {
                    "columns_per_table_avg": round(columns_per_table, 1),
                    "measures_per_table_avg": round(measure_count / table_count, 1) if table_count > 0 else 0,
                    "relationships_per_table_avg": round(relationship_count / table_count, 1) if table_count > 0 else 0
                }
            }

            # === STAR SCHEMA ASSESSMENT ===
            if len(fact_tables) > 0 and len(dim_tables) > 0:
                ratio = len(dim_tables) / max(len(fact_tables), 1)

                if 2 <= ratio <= 10:
                    schema_quality = "Excellent"
                    schema_note = "Healthy fact-to-dimension ratio indicating proper star schema design. This supports efficient queries and clear business logic."
                    health_components["architecture"] += 0  # Already scored well
                    analysis["strengths"].append({
                        "strength": "Star Schema Design",
                        "description": f"{len(fact_tables)} fact table(s) with {len(dim_tables)} dimensions demonstrates sound dimensional modeling"
                    })
                elif ratio > 10:
                    schema_quality = "Review Recommended"
                    schema_note = "High dimension-to-fact ratio may indicate over-normalization or snowflake schema. Consider consolidating dimension tables."
                    health_components["architecture"] -= 5
                    analysis["recommendations"].append({
                        "priority": ExpertInsightLevel.MEDIUM,
                        "category": "architecture",
                        "recommendation": f"Review {len(dim_tables)} dimension tables. Consider denormalizing snowflake dimensions for better query performance.",
                        "business_impact": "Snowflake schemas increase query complexity and may slow down reports"
                    })
                elif ratio < 2:
                    schema_quality = "Needs Improvement"
                    schema_note = "Low dimension-to-fact ratio suggests missing dimensional context. Consider adding dimension tables for better analysis."
                    health_components["architecture"] -= 8
                    analysis["risk_factors"].append({
                        "risk": "Insufficient Dimensional Modeling",
                        "severity": ExpertInsightLevel.HIGH,
                        "description": "Fact tables without sufficient dimensions limit analytical capabilities",
                        "mitigation": "Add dimension tables to enable slicing and dicing of fact data"
                    })
                else:
                    schema_quality = "Good"
                    schema_note = "Acceptable fact-to-dimension ratio with room for optimization"

                analysis["architecture_assessment"]["star_schema_assessment"] = {
                    "quality": schema_quality,
                    "assessment": schema_note,
                    "fact_to_dimension_ratio": round(ratio, 2),
                    "schema_pattern": "Star Schema" if ratio >= 2 else "Snowflake or Denormalized"
                }
            elif len(fact_tables) == 0 and len(dim_tables) > 0:
                analysis["risk_factors"].append({
                    "risk": "No Fact Tables Detected",
                    "severity": ExpertInsightLevel.CRITICAL,
                    "description": "Model appears to contain only dimension tables without measurable facts",
                    "mitigation": "Add fact tables containing business metrics and events to enable meaningful analysis"
                })
                health_components["architecture"] -= 15

        # === MEASURES & ORGANIZATION ASSESSMENT ===
        if measure_count == 0:
            health_components["measures"] = 0
            analysis["risk_factors"].append({
                "risk": "No Explicit Measures",
                "severity": ExpertInsightLevel.CRITICAL,
                "description": "Model has no DAX measures. Relying on implicit measures limits control and reusability.",
                "mitigation": "Create explicit measures for all key business metrics to ensure consistency and enable advanced calculations"
            })
            analysis["recommendations"].append({
                "priority": ExpertInsightLevel.HIGH,
                "category": "measures",
                "recommendation": "Create explicit DAX measures for all business metrics instead of using implicit measures.",
                "business_impact": "Explicit measures provide consistency, reusability, and enable advanced time intelligence and calculations"
            })
        elif measure_count < 5:
            health_components["measures"] = 10
            analysis["insights"].append({
                "level": ExpertInsightLevel.INFO,
                "category": "measures",
                "message": f"Model has {measure_count} measures. Consider creating additional measures to encapsulate common business logic.",
                "suggestion": "Well-designed models typically have 10-50 measures covering key business metrics"
            })
        elif measure_count <= 50:
            health_components["measures"] = 20
            analysis["strengths"].append({
                "strength": "Well-Balanced Measure Count",
                "description": f"{measure_count} measures provides good coverage without overwhelming users"
            })
        elif measure_count <= 100:
            health_components["measures"] = 18
            measures_per_table = measure_count / table_count
            analysis["insights"].append({
                "level": ExpertInsightLevel.MEDIUM,
                "category": "organization",
                "message": f"Large number of measures ({measure_count}). Use display folders to organize for easier discovery.",
                "suggestion": f"Average {measures_per_table:.1f} measures per table - ensure logical grouping with display folders"
            })
        else:
            health_components["measures"] = 15
            analysis["recommendations"].append({
                "priority": ExpertInsightLevel.MEDIUM,
                "category": "organization",
                "recommendation": f"Model has {measure_count} measures. Consider using calculation groups to reduce measure proliferation.",
                "business_impact": "Too many measures can overwhelm users and complicate maintenance"
            })

        # === RELATIONSHIPS ASSESSMENT ===
        if relationship_count == 0 and table_count > 1:
            health_components["relationships"] = 0
            analysis["risk_factors"].append({
                "risk": "No Relationships",
                "severity": ExpertInsightLevel.CRITICAL,
                "description": f"{table_count} tables with no relationships creates isolated islands of data",
                "mitigation": "Define relationships between fact and dimension tables to enable cross-table analysis"
            })
        elif relationship_count > 0 and table_count > 1:
            rels_per_table = relationship_count / table_count

            if rels_per_table >= 0.8:
                health_components["relationships"] = 25
                analysis["strengths"].append({
                    "strength": "Well-Connected Model",
                    "description": f"{relationship_count} relationships across {table_count} tables indicates good integration"
                })
            elif rels_per_table >= 0.5:
                health_components["relationships"] = 20
            elif rels_per_table >= 0.3:
                health_components["relationships"] = 12
                analysis["insights"].append({
                    "level": ExpertInsightLevel.MEDIUM,
                    "category": "relationships",
                    "message": f"Moderate relationship density ({rels_per_table:.2f} per table). Some tables may be disconnected.",
                    "suggestion": "Review if all tables participate in the model's relationship graph"
                })
            else:
                health_components["relationships"] = 5
                analysis["risk_factors"].append({
                    "risk": "Disconnected Tables",
                    "severity": ExpertInsightLevel.HIGH,
                    "description": f"Low relationship count ({relationship_count} for {table_count} tables) suggests isolated tables",
                    "mitigation": "Identify and connect orphaned tables or consider removing if not needed"
                })

        # === DATA QUALITY & PERFORMANCE INDICATORS ===
        if total_rows > 50000000:
            health_components["data_quality"] = 10
            analysis["insights"].append({
                "level": ExpertInsightLevel.HIGH,
                "category": "performance",
                "message": f"Very large dataset ({total_rows:,} rows). Performance optimization critical.",
                "suggestion": "Implement aggregations, incremental refresh, and consider partitioning large fact tables"
            })
            analysis["data_quality_indicators"] = {
                "dataset_size": "Very Large",
                "row_count": total_rows,
                "performance_considerations": [
                    "Implement incremental refresh to reduce refresh time",
                    "Create aggregation tables for commonly used summarizations",
                    "Consider user-defined aggregations for complex visuals",
                    "Use query folding where possible to push processing to source"
                ]
            }
        elif total_rows > 10000000:
            health_components["data_quality"] = 12
            analysis["insights"].append({
                "level": ExpertInsightLevel.MEDIUM,
                "category": "performance",
                "message": f"Large dataset ({total_rows:,} rows). Monitor refresh and query performance.",
                "suggestion": "Consider aggregations for frequently used report pages"
            })
            analysis["data_quality_indicators"] = {
                "dataset_size": "Large",
                "row_count": total_rows,
                "performance_considerations": [
                    "Monitor refresh duration and optimize M queries",
                    "Consider incremental refresh for fact tables",
                    "Review query folding in Power Query transformations"
                ]
            }
        else:
            health_components["data_quality"] = 15
            analysis["data_quality_indicators"] = {
                "dataset_size": "Manageable",
                "row_count": total_rows,
                "performance_considerations": ["Dataset size is within optimal range for good performance"]
            }

        # === LARGE FACT TABLE INSIGHTS ===
        if len(fact_tables) > 5:
            analysis["recommendations"].append({
                "priority": ExpertInsightLevel.MEDIUM,
                "category": "performance",
                "recommendation": f"{len(fact_tables)} large fact tables detected. Review aggregation strategy for high-cardinality tables.",
                "business_impact": "Multiple large fact tables can impact refresh time and memory usage"
            })

        if fact_tables and fact_tables[0]["rows"] > 20000000:
            analysis["insights"].append({
                "level": ExpertInsightLevel.HIGH,
                "category": "performance",
                "message": f"Largest fact table '{fact_tables[0]['name']}' has {fact_tables[0]['rows']:,} rows.",
                "suggestion": "This is a prime candidate for aggregations and incremental refresh"
            })

        # === ORGANIZATION SCORING ===
        # Score based on whether the model appears organized
        if measure_count > 20 or table_count > 10:
            # Assume organization needed for larger models
            health_components["organization"] = 8  # Assume moderate organization
        else:
            health_components["organization"] = 10

        # === CALCULATE FINAL HEALTH SCORE ===
        analysis["health_score"] = max(0, min(100, sum(health_components.values())))
        analysis["health_breakdown"] = health_components

        # === GENERATE EXECUTIVE SUMMARY ===
        analysis["executive_summary"] = BIExpertAnalyzer._generate_model_executive_summary(
            analysis["health_score"],
            table_count,
            measure_count,
            relationship_count,
            total_rows,
            len(fact_tables),
            len(dim_tables),
            len(analysis["risk_factors"]),
            len(analysis["strengths"])
        )

        return analysis

    @staticmethod
    def analyze_measure(measure_def: Dict[str, Any], include_dax_analysis: bool = True) -> Dict[str, Any]:
        """
        Provide expert-level analysis of a measure with advanced DAX intelligence

        Args:
            measure_def: Measure definition with DAX expression
            include_dax_analysis: Whether to include deep DAX pattern analysis

        Returns:
            Comprehensive expert analysis of the measure
        """
        analysis = {
            "measure_name": measure_def.get("name"),
            "executive_summary": "",
            "quality_score": 0,  # 0-100 overall quality score
            "insights": [],
            "complexity_assessment": {},
            "dax_analysis": {},
            "best_practices": [],
            "anti_patterns": [],
            "recommendations": [],
            "performance_assessment": {}
        }

        expression = measure_def.get("expression", "") or measure_def.get("dax_expression", "")
        description = measure_def.get("description")
        display_folder = measure_def.get("display_folder") or measure_def.get("displayFolder")
        format_string = measure_def.get("formatString") or measure_def.get("format_string")
        is_hidden = measure_def.get("isHidden") or measure_def.get("is_hidden", False)

        if not expression:
            analysis["executive_summary"] = "No DAX expression available for analysis"
            analysis["quality_score"] = 0
            return analysis

        # Initialize quality score components
        quality_components = {
            "documentation": 0,      # max 15 points
            "complexity": 0,         # max 25 points
            "best_practices": 0,     # max 30 points
            "performance": 0,        # max 20 points
            "maintainability": 0     # max 10 points
        }

        # === 1. ADVANCED COMPLEXITY ANALYSIS ===
        try:
            from core.dax.dax_validator import DaxValidator

            complexity_metrics = DaxValidator.analyze_complexity(expression)
            analysis["complexity_assessment"] = {
                "level": complexity_metrics.get("level", "Unknown"),
                "score": complexity_metrics.get("complexity_score", 0),
                "metrics": {
                    "function_count": complexity_metrics.get("function_count", 0),
                    "max_nesting_level": complexity_metrics.get("max_nesting_level", 0),
                    "filter_count": complexity_metrics.get("filter_count", 0),
                    "calculate_count": complexity_metrics.get("calculate_count", 0),
                    "expression_length": complexity_metrics.get("expression_length", 0),
                    "line_count": expression.count('\n') + 1
                },
                "expert_interpretation": BIExpertAnalyzer._interpret_complexity(complexity_metrics)
            }

            # Score complexity (max 25 points)
            complexity_level = complexity_metrics.get("level", "Unknown")
            if complexity_level == "Low":
                quality_components["complexity"] = 25
            elif complexity_level == "Medium":
                quality_components["complexity"] = 20
            elif complexity_level == "High":
                quality_components["complexity"] = 12
            else:  # Very High
                quality_components["complexity"] = 5
                analysis["insights"].append({
                    "level": ExpertInsightLevel.HIGH,
                    "category": "complexity",
                    "message": "Very high complexity detected. Consider refactoring into multiple measures or using calculation groups.",
                    "impact": "High complexity increases maintenance cost and potential for errors"
                })

        except Exception as e:
            logger.warning(f"DaxValidator analysis failed: {e}")
            analysis["complexity_assessment"] = {"level": "Unknown", "error": str(e)}

        # === 2. DAX PATTERN ANALYSIS & ANTI-PATTERNS ===
        try:
            from core.dax.dax_validator import DaxValidator

            warnings, recommendations = DaxValidator.analyze_patterns(expression)

            # Categorize anti-patterns
            for warning in warnings:
                severity = BIExpertAnalyzer._categorize_pattern_severity(warning)
                analysis["anti_patterns"].append({
                    "severity": severity,
                    "category": DAXBestPracticeCategory.PERFORMANCE,
                    "pattern": warning,
                    "impact": BIExpertAnalyzer._explain_anti_pattern_impact(warning)
                })

                # Reduce quality score for anti-patterns
                if severity == ExpertInsightLevel.CRITICAL:
                    quality_components["best_practices"] -= 10
                elif severity == ExpertInsightLevel.HIGH:
                    quality_components["best_practices"] -= 5

            # Add recommendations
            for rec in recommendations:
                analysis["recommendations"].append({
                    "priority": BIExpertAnalyzer._categorize_recommendation_priority(rec),
                    "category": BIExpertAnalyzer._categorize_recommendation(rec),
                    "recommendation": rec,
                    "benefit": BIExpertAnalyzer._explain_recommendation_benefit(rec)
                })

        except Exception as e:
            logger.warning(f"DAX pattern analysis failed: {e}")

        # === 3. CONTEXT TRANSITION ANALYSIS ===
        if include_dax_analysis:
            try:
                from core.dax.context_analyzer import DaxContextAnalyzer

                analyzer = DaxContextAnalyzer()
                context_flow = analyzer.analyze_context_transitions(
                    expression,
                    measure_name=measure_def.get("name")
                )

                analysis["dax_analysis"] = {
                    "context_transitions": {
                        "count": len(context_flow.transitions),
                        "max_nesting_level": context_flow.max_nesting_level,
                        "complexity_score": context_flow.complexity_score,
                        "transitions": context_flow.to_dict()["transitions"][:5],  # Top 5 for readability
                        "expert_summary": BIExpertAnalyzer._summarize_context_transitions(context_flow)
                    },
                    "performance_warnings": [
                        {
                            "severity": w.severity,
                            "message": w.message,
                            "suggestion": w.suggestion
                        }
                        for w in context_flow.warnings
                    ]
                }

                # Add insights for complex context transitions
                if context_flow.max_nesting_level > 3:
                    analysis["insights"].append({
                        "level": ExpertInsightLevel.MEDIUM,
                        "category": "complexity",
                        "message": f"Deep context nesting detected ({context_flow.max_nesting_level} levels). This can impact both performance and readability.",
                        "impact": "Nested context transitions create multiple evaluation contexts, increasing query complexity"
                    })

                # Performance scoring based on context transitions
                if context_flow.complexity_score <= 30:
                    quality_components["performance"] = 20
                elif context_flow.complexity_score <= 60:
                    quality_components["performance"] = 15
                else:
                    quality_components["performance"] = 8

            except Exception as e:
                logger.warning(f"Context transition analysis failed: {e}")
                analysis["dax_analysis"] = {"error": f"Context analysis unavailable: {str(e)}"}

        # === 4. BEST PRACTICES ASSESSMENT ===
        best_practice_checks = BIExpertAnalyzer._check_best_practices(
            expression, description, display_folder, format_string, is_hidden
        )

        quality_components["best_practices"] = 30  # Start with full points
        for check in best_practice_checks:
            analysis["best_practices"].append(check)
            if check["status"] == "fail":
                if check["severity"] == ExpertInsightLevel.HIGH:
                    quality_components["best_practices"] -= 8
                elif check["severity"] == ExpertInsightLevel.MEDIUM:
                    quality_components["best_practices"] -= 4
                elif check["severity"] == ExpertInsightLevel.LOW:
                    quality_components["best_practices"] -= 2

        # === 5. DOCUMENTATION & MAINTAINABILITY ===
        quality_components["documentation"] = BIExpertAnalyzer._score_documentation(
            description, display_folder, format_string
        )

        quality_components["maintainability"] = BIExpertAnalyzer._score_maintainability(
            expression, display_folder
        )

        # === 6. PERFORMANCE ASSESSMENT ===
        analysis["performance_assessment"] = BIExpertAnalyzer._assess_performance_characteristics(
            expression, analysis.get("complexity_assessment", {}), analysis.get("dax_analysis", {})
        )

        # === 7. CALCULATE FINAL QUALITY SCORE ===
        analysis["quality_score"] = max(0, min(100, sum(quality_components.values())))
        analysis["quality_breakdown"] = quality_components

        # === 8. GENERATE EXECUTIVE SUMMARY ===
        analysis["executive_summary"] = BIExpertAnalyzer._generate_measure_executive_summary(
            measure_def.get("name"),
            analysis["quality_score"],
            analysis["complexity_assessment"],
            len(analysis["anti_patterns"]),
            len(analysis["recommendations"])
        )

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

    # ===================================================================
    # HELPER METHODS FOR ADVANCED MEASURE ANALYSIS
    # ===================================================================

    @staticmethod
    def _interpret_complexity(complexity_metrics: Dict[str, Any]) -> str:
        """Provide expert interpretation of complexity metrics"""
        level = complexity_metrics.get("level", "Unknown")
        score = complexity_metrics.get("complexity_score", 0)
        nesting = complexity_metrics.get("max_nesting_level", 0)
        functions = complexity_metrics.get("function_count", 0)

        if level == "Low":
            return f"Simple measure with {functions} functions and {nesting} nesting levels. Easy to understand and maintain."
        elif level == "Medium":
            return f"Moderately complex measure with {functions} functions. Good balance of functionality and maintainability."
        elif level == "High":
            return f"Complex measure with {functions} functions and {nesting} nesting levels. Consider breaking into smaller measures or adding comments."
        else:  # Very High
            return f"Highly complex measure (score: {score}). Strong candidate for refactoring. Consider using calculation groups or splitting logic."

    @staticmethod
    def _categorize_pattern_severity(warning: str) -> str:
        """Categorize anti-pattern severity"""
        warning_lower = warning.lower()

        # Critical issues
        if "nested calculate" in warning_lower:
            return ExpertInsightLevel.CRITICAL

        # High severity
        if any(pattern in warning_lower for pattern in ["sumx with filter", "high number of calculate"]):
            return ExpertInsightLevel.HIGH

        return ExpertInsightLevel.MEDIUM

    @staticmethod
    def _explain_anti_pattern_impact(warning: str) -> str:
        """Explain the business/technical impact of anti-patterns"""
        warning_lower = warning.lower()

        impact_map = {
            "nested calculate": "Nested CALCULATE can produce unexpected results due to filter context overrides. This is a common source of incorrect calculations.",
            "sumx with filter": "SUMX(FILTER(...)) creates a row-by-row iteration over filtered results. Using CALCULATE with filter arguments is typically 2-5x faster.",
            "high number of calculate": "Excessive CALCULATE functions can indicate overly complex logic and may impact query performance. Consider consolidating filters.",
        }

        for pattern, impact in impact_map.items():
            if pattern in warning_lower:
                return impact

        return "This pattern may impact performance or produce unexpected results in certain scenarios."

    @staticmethod
    def _categorize_recommendation_priority(rec: str) -> str:
        """Categorize recommendation priority"""
        rec_lower = rec.lower()

        # High priority
        if any(keyword in rec_lower for keyword in ["divide(", "division-by-zero", "blank handling"]):
            return ExpertInsightLevel.HIGH

        # Medium priority
        if any(keyword in rec_lower for keyword in ["var", "summarizecolumns", "calculate with filters"]):
            return ExpertInsightLevel.MEDIUM

        return ExpertInsightLevel.LOW

    @staticmethod
    def _categorize_recommendation(rec: str) -> str:
        """Categorize recommendation by type"""
        rec_lower = rec.lower()

        if any(keyword in rec_lower for keyword in ["performance", "faster", "slow"]):
            return DAXBestPracticeCategory.PERFORMANCE
        elif any(keyword in rec_lower for keyword in ["divide", "blank", "error"]):
            return DAXBestPracticeCategory.CORRECTNESS
        elif any(keyword in rec_lower for keyword in ["var", "break", "simplify"]):
            return DAXBestPracticeCategory.MAINTAINABILITY
        elif any(keyword in rec_lower for keyword in ["format", "present"]):
            return DAXBestPracticeCategory.READABILITY

        return DAXBestPracticeCategory.STANDARDS

    @staticmethod
    def _explain_recommendation_benefit(rec: str) -> str:
        """Explain the benefit of following a recommendation"""
        rec_lower = rec.lower()

        benefit_map = {
            "divide": "DIVIDE() handles division by zero gracefully, returning BLANK instead of errors. This prevents report failures and improves user experience.",
            "var": "Variables improve performance by avoiding re-evaluation of expressions and make DAX more readable by naming intermediate results.",
            "summarizecolumns": "SUMMARIZECOLUMNS provides more predictable behavior and better performance for grouping operations compared to SUMMARIZE.",
            "calculate with filters": "CALCULATE with filter arguments provides more flexibility and clearer intent than basic aggregations.",
            "format": "FORMAT function ensures consistent number presentation across different locales and user settings.",
            "break": "Breaking long expressions into multiple measures improves maintainability, enables reusability, and simplifies debugging."
        }

        for pattern, benefit in benefit_map.items():
            if pattern in rec_lower:
                return benefit

        return "Following this recommendation will improve measure quality and maintainability."

    @staticmethod
    def _summarize_context_transitions(context_flow) -> str:
        """Create expert summary of context transitions"""
        if not context_flow.transitions:
            return "No context transitions detected. This is a simple aggregation measure."

        transition_count = len(context_flow.transitions)
        max_nesting = context_flow.max_nesting_level
        complexity_score = context_flow.complexity_score

        # Categorize complexity
        if complexity_score <= 20:
            complexity_assessment = "straightforward"
        elif complexity_score <= 50:
            complexity_assessment = "moderate"
        elif complexity_score <= 80:
            complexity_assessment = "complex"
        else:
            complexity_assessment = "highly complex"

        summary = f"This measure has {transition_count} context transition(s) with {max_nesting} nesting level(s). "
        summary += f"Context flow is {complexity_assessment} (score: {complexity_score}/100). "

        # Add specific guidance
        if max_nesting > 3:
            summary += "Deep nesting may impact both performance and code readability. "
        if complexity_score > 70:
            summary += "Consider refactoring to reduce context transition complexity."

        return summary

    @staticmethod
    def _check_best_practices(expression: str, description: Optional[str],
                              display_folder: Optional[str], format_string: Optional[str],
                              is_hidden: bool) -> List[Dict[str, Any]]:
        """Comprehensive best practice checks"""
        checks = []
        expr_upper = expression.upper()

        # Documentation check
        if not description:
            checks.append({
                "status": "fail",
                "severity": ExpertInsightLevel.MEDIUM,
                "practice": "Documentation",
                "category": DAXBestPracticeCategory.MAINTAINABILITY,
                "message": "Measure lacks a description. Always document business logic and purpose.",
                "recommendation": "Add a description explaining what this measure calculates and when to use it."
            })
        else:
            checks.append({
                "status": "pass",
                "severity": ExpertInsightLevel.INFO,
                "practice": "Documentation",
                "category": DAXBestPracticeCategory.MAINTAINABILITY,
                "message": "Measure is documented with a description."
            })

        # Format string check
        if not format_string:
            checks.append({
                "status": "fail",
                "severity": ExpertInsightLevel.LOW,
                "practice": "Formatting",
                "category": DAXBestPracticeCategory.STANDARDS,
                "message": "No format string defined. Users may see inconsistent number formatting.",
                "recommendation": "Add a format string (e.g., '#,##0', '0.00%', '$#,##0') for consistent presentation."
            })

        # Display folder organization
        if not display_folder and not is_hidden:
            checks.append({
                "status": "warning",
                "severity": ExpertInsightLevel.LOW,
                "practice": "Organization",
                "category": DAXBestPracticeCategory.MAINTAINABILITY,
                "message": "Measure not organized in a display folder. This can make large models harder to navigate.",
                "recommendation": "Organize measures into logical display folders (e.g., 'Sales', 'Finance', 'Time Intelligence')."
            })

        # Variable usage for complex measures
        line_count = expression.count('\n') + 1
        if 'VAR ' not in expr_upper and line_count > 3:
            # Check if expression has repeated patterns
            if expression.count('SUM(') > 1 or expression.count('CALCULATE(') > 1:
                checks.append({
                    "status": "fail",
                    "severity": ExpertInsightLevel.MEDIUM,
                    "practice": "Variable Usage",
                    "category": DAXBestPracticeCategory.PERFORMANCE,
                    "message": "Complex measure without variables. Repeated expressions are evaluated multiple times.",
                    "recommendation": "Use VAR to store repeated calculations and intermediate results."
                })

        # Iterator best practices
        if 'SUMX(' in expr_upper or 'AVERAGEX(' in expr_upper:
            if 'FILTER(' in expr_upper:
                checks.append({
                    "status": "warning",
                    "severity": ExpertInsightLevel.MEDIUM,
                    "practice": "Iterator Optimization",
                    "category": DAXBestPracticeCategory.PERFORMANCE,
                    "message": "Iterator function with FILTER may be optimizable.",
                    "recommendation": "Consider using CALCULATE with filter arguments instead of iterator + FILTER pattern."
                })

        # Error handling
        if '/' in expression and 'DIVIDE(' not in expr_upper:
            checks.append({
                "status": "fail",
                "severity": ExpertInsightLevel.HIGH,
                "practice": "Error Handling",
                "category": DAXBestPracticeCategory.CORRECTNESS,
                "message": "Division operator (/) used without error handling. Risk of division-by-zero errors.",
                "recommendation": "Replace '/' with DIVIDE(numerator, denominator, alternate_result) for safe division."
            })

        return checks

    @staticmethod
    def _score_documentation(description: Optional[str], display_folder: Optional[str],
                            format_string: Optional[str]) -> int:
        """Score documentation quality (0-15 points)"""
        score = 0

        if description:
            score += 8
            # Bonus for detailed descriptions
            if len(description) > 50:
                score += 2

        if display_folder:
            score += 3

        if format_string:
            score += 2

        return min(15, score)

    @staticmethod
    def _score_maintainability(expression: str, display_folder: Optional[str]) -> int:
        """Score maintainability (0-10 points)"""
        score = 10  # Start optimistic

        line_count = expression.count('\n') + 1

        # Penalize very long expressions
        if line_count > 50:
            score -= 4
        elif line_count > 30:
            score -= 2

        # Reward variable usage
        if 'VAR ' in expression.upper():
            score += 2

        # Penalize if not organized
        if not display_folder:
            score -= 2

        return max(0, min(10, score))

    @staticmethod
    def _assess_performance_characteristics(expression: str, complexity: Dict[str, Any],
                                           dax_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess performance characteristics of the measure"""
        assessment = {
            "estimated_performance_tier": "",
            "performance_factors": [],
            "optimization_opportunities": []
        }

        expr_upper = expression.upper()

        # Analyze performance factors
        has_iterators = any(func in expr_upper for func in ['SUMX', 'AVERAGEX', 'FILTER', 'ADDCOLUMNS'])
        has_calculate = 'CALCULATE' in expr_upper
        calculate_count = complexity.get("metrics", {}).get("calculate_count", 0)
        filter_count = complexity.get("metrics", {}).get("filter_count", 0)
        nesting_level = complexity.get("metrics", {}).get("max_nesting_level", 0)

        # Performance tier estimation
        performance_score = 100

        if has_iterators:
            performance_score -= 15
            assessment["performance_factors"].append({
                "factor": "Iterator Functions",
                "impact": "Medium",
                "description": "Iterator functions process row-by-row and can be slow on large tables"
            })

        if filter_count > 2:
            performance_score -= 10 * (filter_count - 2)
            assessment["performance_factors"].append({
                "factor": "Multiple FILTER Operations",
                "impact": "High",
                "description": f"{filter_count} FILTER operations detected. Each creates an intermediate table."
            })

        if calculate_count > 3:
            performance_score -= 5 * (calculate_count - 3)
            assessment["performance_factors"].append({
                "factor": "Multiple CALCULATE Calls",
                "impact": "Medium",
                "description": f"{calculate_count} CALCULATE operations may create redundant filter context changes"
            })

        if nesting_level > 4:
            performance_score -= 15
            assessment["performance_factors"].append({
                "factor": "Deep Nesting",
                "impact": "Medium to High",
                "description": f"Nesting level of {nesting_level} increases evaluation complexity"
            })

        # Context transitions impact
        context_data = dax_analysis.get("context_transitions", {})
        transition_count = context_data.get("count", 0)
        if transition_count > 5:
            performance_score -= 10
            assessment["performance_factors"].append({
                "factor": "Frequent Context Transitions",
                "impact": "Medium",
                "description": f"{transition_count} context transitions detected. Each transition has overhead."
            })

        # Determine tier
        if performance_score >= 80:
            assessment["estimated_performance_tier"] = "Excellent - Low overhead, fast execution expected"
        elif performance_score >= 60:
            assessment["estimated_performance_tier"] = "Good - Acceptable performance for most scenarios"
        elif performance_score >= 40:
            assessment["estimated_performance_tier"] = "Fair - May be slow on large datasets, test performance"
        else:
            assessment["estimated_performance_tier"] = "Poor - Likely performance issues, refactoring recommended"

        # Optimization opportunities
        if has_iterators and filter_count > 0:
            assessment["optimization_opportunities"].append({
                "opportunity": "Replace Iterator+FILTER with CALCULATE",
                "potential_gain": "2-5x faster execution",
                "complexity": "Medium"
            })

        if calculate_count > 3:
            assessment["optimization_opportunities"].append({
                "opportunity": "Consolidate CALCULATE operations",
                "potential_gain": "Reduced filter context overhead",
                "complexity": "Low"
            })

        if 'SUMMARIZE(' in expr_upper and 'SUMMARIZECOLUMNS(' not in expr_upper:
            assessment["optimization_opportunities"].append({
                "opportunity": "Use SUMMARIZECOLUMNS instead of SUMMARIZE",
                "potential_gain": "Better performance and clearer semantics",
                "complexity": "Low"
            })

        return assessment

    @staticmethod
    def _generate_measure_executive_summary(measure_name: str, quality_score: int,
                                           complexity: Dict[str, Any], anti_pattern_count: int,
                                           recommendation_count: int) -> str:
        """Generate executive summary for measure analysis"""
        complexity_level = complexity.get("level", "Unknown")

        # Quality assessment
        if quality_score >= 80:
            quality_assessment = "EXCELLENT"
            quality_note = "follows best practices"
        elif quality_score >= 60:
            quality_assessment = "GOOD"
            quality_note = "is well-structured with minor improvements possible"
        elif quality_score >= 40:
            quality_assessment = "FAIR"
            quality_note = "needs attention in several areas"
        else:
            quality_assessment = "NEEDS IMPROVEMENT"
            quality_note = "requires significant refactoring"

        summary = f"Measure '{measure_name}' scores {quality_score}/100 ({quality_assessment}) and {quality_note}. "
        summary += f"Complexity: {complexity_level}. "

        if anti_pattern_count > 0:
            summary += f"Found {anti_pattern_count} anti-pattern(s) that should be addressed. "

        if recommendation_count > 0:
            summary += f"{recommendation_count} optimization recommendation(s) available."
        else:
            summary += "No major optimizations identified."

        return summary

    @staticmethod
    def _generate_model_executive_summary(health_score: int, table_count: int, measure_count: int,
                                         relationship_count: int, total_rows: int, fact_tables: int,
                                         dim_tables: int, risk_count: int, strength_count: int) -> str:
        """Generate comprehensive executive summary for model analysis"""

        # Health assessment
        if health_score >= 85:
            health_grade = "EXCELLENT"
            health_interpretation = "This model demonstrates expert-level design following Power BI best practices"
        elif health_score >= 70:
            health_grade = "GOOD"
            health_interpretation = "This model is well-designed with minor opportunities for optimization"
        elif health_score >= 55:
            health_grade = "FAIR"
            health_interpretation = "This model is functional but has several areas requiring improvement"
        elif health_score >= 40:
            health_grade = "NEEDS IMPROVEMENT"
            health_interpretation = "This model has significant issues that should be addressed"
        else:
            health_grade = "CRITICAL"
            health_interpretation = "This model requires immediate attention to address fundamental design issues"

        # Build summary
        summary = f"HEALTH SCORE: {health_score}/100 ({health_grade}) - {health_interpretation}. "

        # Model composition
        summary += f"MODEL COMPOSITION: {table_count} tables ({fact_tables} fact, {dim_tables} dimension), "
        summary += f"{measure_count} DAX measures, {relationship_count} relationships, {total_rows:,} total rows. "

        # Key insights
        if strength_count > 0 and risk_count == 0:
            summary += f"ASSESSMENT: Model shows {strength_count} key strength(s) with no critical risks identified. "
        elif strength_count > 0 and risk_count > 0:
            summary += f"ASSESSMENT: Model shows {strength_count} strength(s) but has {risk_count} risk factor(s) requiring attention. "
        elif risk_count > 0:
            summary += f"ASSESSMENT: {risk_count} risk factor(s) identified that require remediation. "

        # Data scale assessment
        if total_rows > 50000000:
            summary += "DATA SCALE: Very large dataset requiring performance optimization strategies."
        elif total_rows > 10000000:
            summary += "DATA SCALE: Large dataset - monitor performance and consider optimization."
        else:
            summary += "DATA SCALE: Dataset size is within optimal range."

        return summary

    @staticmethod
    def _generate_model_summary(table_count: int, measure_count: int, relationship_count: int,
                               total_rows: int, fact_tables: int, dim_tables: int, health_score: int) -> str:
        """Generate a concise model summary (legacy method)"""
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
