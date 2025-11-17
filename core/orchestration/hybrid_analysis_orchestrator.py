"""
Hybrid Analysis Orchestrator - Guides MCP agents on using hybrid analysis tools

Provides policy guidance for:
- When to use hybrid analysis vs live connection
- How to export and analyze models
- Interpreting BI expert insights
- Following up on recommendations
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class HybridAnalysisOrchestrator:
    """Orchestrator for hybrid analysis operations"""

    def __init__(self, config):
        self.config = config

    @staticmethod
    def get_usage_guidance() -> Dict[str, Any]:
        """
        Get guidance on when and how to use hybrid analysis

        Returns:
            Usage guidance dictionary
        """
        return {
            "when_to_use": {
                "offline_analysis": [
                    "Model is in Git repository as PBIP",
                    "Need to analyze model without opening Power BI Desktop",
                    "Want to review TMDL changes from version control",
                    "Performing code review of DAX measures"
                ],
                "combined_analysis": [
                    "Need both schema (TMDL) and runtime data (row counts, sample data)",
                    "Validating data quality alongside model structure",
                    "Comprehensive model documentation",
                    "Performance analysis with actual data distribution"
                ],
                "vs_live_connection": {
                    "use_hybrid_when": [
                        "Model not currently open in Power BI Desktop",
                        "PBIP available in Git/file system",
                        "Need reproducible analysis (exported package)",
                        "Analyzing multiple model versions"
                    ],
                    "use_live_when": [
                        "Model is open in Power BI Desktop",
                        "Need real-time DMV queries",
                        "Running performance traces",
                        "Modifying model objects"
                    ]
                }
            },
            "workflow": {
                "step_1_export": {
                    "tool": "export_hybrid_analysis",
                    "when": "Once per analysis session or when model changes",
                    "parameters": {
                        "pbip_folder_path": "Required - path to .SemanticModel folder",
                        "include_sample_data": "true for full analysis, false for TMDL-only",
                        "connection_string": "Optional - auto-detects if Power BI is open"
                    }
                },
                "step_2_analyze": {
                    "tool": "analyze_hybrid_model",
                    "operations": {
                        "read_metadata": "Start here - get expert overview and health score",
                        "find_objects": "List measures, tables, or other objects with filters",
                        "get_object_definition": "Deep dive into specific measure DAX or table structure",
                        "analyze_dependencies": "Understand measure dependencies and impact",
                        "get_sample_data": "Preview data (requires sample_data in export)"
                    }
                },
                "step_3_action": {
                    "follow_recommendations": "Act on expert_analysis.recommendations",
                    "review_flagged_items": "Check insights with severity='warning'",
                    "optimize_measures": "Review measures flagged for complexity or best practices",
                    "validate_relationships": "Verify relationship patterns align with star schema"
                }
            },
            "best_practices": [
                "Always start with 'read_metadata' for model overview",
                "Review expert_analysis health_score and insights",
                "Follow sample_data_guidance - only request when beneficial",
                "Use TMDL parsing for accurate measure DAX (not JSON catalog)",
                "Check relationship patterns for star schema compliance",
                "Monitor measure complexity and apply best practices",
                "Use display folders for measure organization (if many measures)",
                "Document measures with descriptions",
                "Avoid excessive bidirectional or many-to-many relationships"
            ]
        }

    @staticmethod
    def interpret_health_score(score: int) -> Dict[str, Any]:
        """
        Interpret model health score and provide guidance

        Args:
            score: Health score 0-100

        Returns:
            Interpretation and next steps
        """
        if score >= 80:
            return {
                "rating": "EXCELLENT",
                "interpretation": "Model follows best practices with strong architecture",
                "next_steps": [
                    "Review any remaining recommendations for minor improvements",
                    "Monitor performance metrics if available",
                    "Document any custom patterns for team reference"
                ]
            }
        elif score >= 60:
            return {
                "rating": "GOOD",
                "interpretation": "Model is functional with some optimization opportunities",
                "next_steps": [
                    "Review insights with severity='warning'",
                    "Address high-priority recommendations first",
                    "Consider refactoring flagged measures",
                    "Validate relationship patterns"
                ]
            }
        elif score >= 40:
            return {
                "rating": "NEEDS IMPROVEMENT",
                "interpretation": "Model has several issues requiring attention",
                "next_steps": [
                    "Focus on high-priority recommendations immediately",
                    "Review all warnings and insights",
                    "Check for disconnected tables (relationship issues)",
                    "Analyze measure complexity and refactor as needed",
                    "Validate star schema adherence"
                ]
            }
        else:
            return {
                "rating": "CRITICAL",
                "interpretation": "Model has significant structural or design issues",
                "next_steps": [
                    "Review architecture_assessment for fundamental issues",
                    "Address relationship problems first (disconnected tables, many-to-many)",
                    "Add measures if none exist",
                    "Consider model redesign if star schema is not followed",
                    "Engage senior BI architect for review"
                ]
            }

    @staticmethod
    def guide_measure_analysis(complexity: str, best_practices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide guidance on measure analysis results

        Args:
            complexity: Measure complexity level
            best_practices: List of best practice checks

        Returns:
            Guidance for the measure
        """
        guidance = {
            "priority": "low",
            "actions": []
        }

        # Check complexity
        if complexity == "High":
            guidance["priority"] = "high"
            guidance["actions"].append({
                "action": "refactor_for_complexity",
                "reason": "High complexity measures are harder to maintain and may have performance issues",
                "recommendation": "Break into multiple measures or use variables to improve readability"
            })
        elif complexity == "Medium":
            guidance["priority"] = "medium"
            guidance["actions"].append({
                "action": "review_structure",
                "reason": "Medium complexity is acceptable but review for optimization opportunities",
                "recommendation": "Ensure proper use of variables and consider if logic can be simplified"
            })

        # Check best practices
        warnings = [bp for bp in best_practices if bp.get("status") == "warning"]
        if warnings:
            for warning in warnings:
                guidance["actions"].append({
                    "action": "address_best_practice",
                    "practice": warning.get("practice"),
                    "message": warning.get("message")
                })

        return guidance

    @staticmethod
    def recommend_next_operation(current_operation: str, result: Dict[str, Any]) -> Optional[str]:
        """
        Recommend the next operation based on current analysis

        Args:
            current_operation: The operation just performed
            result: Result from the operation

        Returns:
            Recommended next operation or None
        """
        if current_operation == "read_metadata":
            # Check if there are recommendations to follow up on
            expert_analysis = result.get("data", {}).get("expert_analysis", {})
            recommendations = expert_analysis.get("recommendations", [])

            if recommendations:
                # High priority recommendations suggest deeper analysis
                high_priority = [r for r in recommendations if r.get("priority") == "high"]
                if high_priority:
                    return {
                        "operation": "find_objects",
                        "reason": "High-priority recommendations found, review affected objects",
                        "parameters": {
                            "object_type": "measures" if "measure" in str(high_priority) else "tables"
                        }
                    }

            # Check health score
            health_score = expert_analysis.get("health_score", 0)
            if health_score < 60:
                return {
                    "operation": "find_objects",
                    "reason": "Low health score, review model objects for issues",
                    "parameters": {"object_type": "tables"}
                }

        elif current_operation == "find_objects":
            # Suggest diving into specific objects
            objects = result.get("objects", [])
            if objects and len(objects) > 0:
                first_object = objects[0]
                return {
                    "operation": "get_object_definition",
                    "reason": "Review detailed definition of identified objects",
                    "parameters": {
                        "object_name": first_object.get("name"),
                        "object_type": "measure" if "measure" in str(result.get("object_type", "")) else "table"
                    }
                }

        elif current_operation == "get_object_definition":
            # Check if expert analysis suggests sample data
            guidance = result.get("data", {}).get("_sample_data_guidance", {})
            if guidance.get("sample_data_recommended"):
                return {
                    "operation": "get_sample_data",
                    "reason": guidance.get("reason"),
                    "benefits": guidance.get("benefits", [])
                }

            # Otherwise suggest dependency analysis
            return {
                "operation": "analyze_dependencies",
                "reason": "Understand what this object depends on and what depends on it"
            }

        return None

    @staticmethod
    def format_expert_insights_for_agent(analysis: Dict[str, Any]) -> str:
        """
        Format expert analysis for MCP agent consumption

        Args:
            analysis: Expert analysis dictionary

        Returns:
            Formatted string for agent
        """
        output = []

        # Summary
        if "summary" in analysis:
            output.append(f"EXPERT SUMMARY: {analysis['summary']}")
            output.append("")

        # Health Score
        health_score = analysis.get("health_score", 0)
        output.append(f"Model Health Score: {health_score}/100")

        interpretation = HybridAnalysisOrchestrator.interpret_health_score(health_score)
        output.append(f"Rating: {interpretation['rating']}")
        output.append(f"Assessment: {interpretation['interpretation']}")
        output.append("")

        # Architecture
        arch = analysis.get("architecture_assessment", {})
        if arch:
            output.append("ARCHITECTURE:")
            output.append(f"  Complexity: {arch.get('complexity')} - {arch.get('complexity_note')}")
            if "star_schema_quality" in arch:
                output.append(f"  Star Schema: {arch.get('star_schema_quality')} - {arch.get('schema_note')}")
            output.append(f"  Tables: {arch.get('table_count')} ({arch.get('estimated_fact_tables')} fact, {arch.get('estimated_dimension_tables')} dimension)")
            output.append(f"  Measures: {arch.get('measure_count')}")
            output.append(f"  Relationships: {arch.get('relationship_count')}")
            output.append("")

        # Insights
        insights = analysis.get("insights", [])
        if insights:
            output.append("KEY INSIGHTS:")
            for insight in insights:
                severity = insight.get("severity", "info").upper()
                msg = insight.get("message", '')
                output.append(f"  [{severity}] {msg}")
            output.append("")

        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            output.append("RECOMMENDATIONS:")
            for rec in recommendations:
                priority = rec.get("priority", 'low').upper()
                category = rec.get("category", 'general')
                msg = rec.get("recommendation", '')
                output.append(f"  [{priority}] {category}: {msg}")
            output.append("")

        # Next Steps
        output.append("SUGGESTED NEXT STEPS:")
        for step in interpretation.get("next_steps", []):
            output.append(f"  - {step}")

        return "\n".join(output)
