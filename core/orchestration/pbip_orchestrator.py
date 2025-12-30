"""PBIP analysis orchestration."""
import logging
import os
from typing import Any, Dict, Optional, List
from .base_orchestrator import BaseOrchestrator

logger = logging.getLogger(__name__)

class PbipOrchestrator(BaseOrchestrator):
    """Handles PBIP repository analysis workflows."""

    def analyze_pbip_repository_enhanced(
        self,
        repo_path: str,
        output_path: str = "exports/pbip_analysis",
        exclude_folders: Optional[List[str]] = None,
        bpa_rules_path: Optional[str] = "config/bpa_rules_comprehensive.json",
        enable_enhanced: bool = True
    ) -> Dict[str, Any]:
        """Perform comprehensive PBIP repository analysis with enhanced features."""
        try:
            from core.pbip.pbip_project_scanner import PbipProjectScanner
            from core.pbip.pbip_model_analyzer import TmdlModelAnalyzer
            from core.pbip.pbip_report_analyzer import PbirReportAnalyzer
            from core.pbip.pbip_dependency_engine import PbipDependencyEngine
            from core.pbip.pbip_html_generator import PbipHtmlGenerator
            from core.pbip.pbip_enhanced_analyzer import EnhancedPbipAnalyzer

            logger.info(f"Starting PBIP analysis: {repo_path}")

            # Step 1: Scan repository
            scanner = PbipProjectScanner()
            projects = scanner.scan_repository(repo_path, exclude_folders or [])

            semantic_models = projects.get("semantic_models", [])
            reports = projects.get("reports", [])

            if not semantic_models:
                return {
                    "success": False,
                    "error": "No semantic models found in repository",
                    "error_type": "no_models"
                }

            # Step 2: Analyze semantic model (first one)
            model = semantic_models[0]
            model_folder = model.get("model_folder")

            if not model_folder:
                return {
                    "success": False,
                    "error": "No model folder found",
                    "error_type": "invalid_model"
                }

            analyzer = TmdlModelAnalyzer()
            model_data = analyzer.analyze_model(model_folder)

            # Step 3: Analyze report (if available)
            report_data = None
            if reports:
                report = reports[0]
                report_folder = report.get("report_folder")
                if report_folder:
                    report_analyzer = PbirReportAnalyzer()
                    report_data = report_analyzer.analyze_report(report_folder)

            # Step 4: Dependency analysis
            dep_engine = PbipDependencyEngine(model_data, report_data)
            dependencies = dep_engine.analyze_all_dependencies()

            # Step 5: Enhanced analysis (if enabled)
            enhanced_results = None
            if enable_enhanced:
                logger.info("Running enhanced analysis...")
                enhanced_analyzer = EnhancedPbipAnalyzer(model_data, report_data, dependencies)
                enhanced_results = enhanced_analyzer.run_full_analysis(bpa_rules_path)

                logger.info(
                    f"Enhanced analysis complete: "
                    f"{len(enhanced_results.get('analyses', {}).get('column_lineage', {}))} columns tracked, "
                    f"{enhanced_results.get('analyses', {}).get('dax_quality', {}).get('summary', {}).get('total_issues', 0)} DAX issues found"
                )

            # Step 6: Generate HTML report
            generator = PbipHtmlGenerator()
            html_path = generator.generate_full_report(
                model_data,
                report_data,
                dependencies,
                output_path,
                os.path.basename(repo_path),
                enhanced_results=enhanced_results
            )

            # Build summary
            summary = {
                "success": True,
                "repository": repo_path,
                "html_report": html_path,
                "statistics": {
                    "tables": len(model_data.get("tables", [])),
                    "measures": sum(len(t.get("measures", [])) for t in model_data.get("tables", [])),
                    "columns": sum(len(t.get("columns", [])) for t in model_data.get("tables", [])),
                    "relationships": len(model_data.get("relationships", [])),
                    "pages": len(report_data.get("pages", [])) if report_data else 0,
                    "visuals": sum(len(p.get("visuals", [])) for p in report_data.get("pages", [])) if report_data else 0,
                    "unused_measures": dependencies.get("summary", {}).get("unused_measures", 0),
                    "unused_columns": dependencies.get("summary", {}).get("unused_columns", 0)
                }
            }

            # Add enhanced statistics if available
            if enhanced_results:
                summary["enhanced_statistics"] = {
                    "column_lineage_tracked": len(enhanced_results.get("analyses", {}).get("column_lineage", {})),
                    "data_type_issues": len(enhanced_results.get("analyses", {}).get("data_types", {}).get("type_issues", [])),
                    "cardinality_warnings": len(enhanced_results.get("analyses", {}).get("cardinality", {}).get("cardinality_warnings", [])),
                    "relationship_issues": len(enhanced_results.get("analyses", {}).get("relationships", {}).get("issues", [])),
                    "dax_quality_issues": len(enhanced_results.get("analyses", {}).get("dax_quality", {}).get("quality_issues", [])),
                    "naming_violations": len(enhanced_results.get("analyses", {}).get("naming_conventions", {}).get("violations", [])),
                    "high_complexity_measures": enhanced_results.get("analyses", {}).get("dax_quality", {}).get("summary", {}).get("high_complexity_measures", 0)
                }

                # Add BPA statistics if available
                if enhanced_results.get("analyses", {}).get("bpa"):
                    bpa_summary = enhanced_results["analyses"]["bpa"].get("summary", {})
                    summary["enhanced_statistics"]["bpa_violations"] = bpa_summary.get("total", 0)
                    summary["enhanced_statistics"]["bpa_errors"] = bpa_summary.get("by_severity", {}).get("ERROR", 0)
                    summary["enhanced_statistics"]["bpa_warnings"] = bpa_summary.get("by_severity", {}).get("WARNING", 0)

            return summary

        except Exception as e:
            logger.error(f"PBIP analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "analysis_error"
            }

    def analyze_aggregation(
        self,
        pbip_path: str,
        output_format: str = "summary",
        output_path: Optional[str] = None,
        page_filter: Optional[str] = None,
        include_visual_details: bool = True,
        estimate_row_savings: bool = True,
        base_table_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze aggregation table usage across visuals and pages.

        Args:
            pbip_path: Path to PBIP project folder
            output_format: Output format (summary, detailed, html, json)
            output_path: Optional output path for HTML/JSON reports
            page_filter: Analyze only pages matching this name
            include_visual_details: Include detailed per-visual analysis
            estimate_row_savings: Calculate estimated row savings
            base_table_rows: Actual row count of base fact table

        Returns:
            Analysis result with aggregation tables, measures, and visual usage
        """
        try:
            from core.aggregation import (
                AggregationAnalyzer,
                AggregationReportBuilder,
                RowSavingsEstimator,
            )
            from pathlib import Path
            from datetime import datetime

            path = Path(pbip_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {pbip_path}",
                }

            logger.info(f"Starting aggregation analysis for {pbip_path}")
            analyzer = AggregationAnalyzer(str(path))
            result = analyzer.analyze(
                include_report=True,
                base_table_rows=base_table_rows,
            )

            # Calculate row savings if requested
            row_savings = None
            if estimate_row_savings and result.report_summary:
                base_rows = base_table_rows or 10_000_000
                estimator = RowSavingsEstimator(
                    result.aggregation_tables,
                    base_table_name=result.base_fact_tables[0] if result.base_fact_tables else "Base Table",
                    base_table_rows=base_rows,
                )
                row_savings = estimator.estimate_savings(result.report_summary)

            # Build report
            report_builder = AggregationReportBuilder(result)
            if row_savings:
                report_builder.set_row_savings(row_savings)

            # Filter pages if requested
            if page_filter and result.report_summary:
                filtered_pages = [
                    p for p in result.report_summary.pages
                    if page_filter.lower() in p.page_name.lower()
                ]
                result.report_summary.pages = filtered_pages

            # Generate output based on format
            if output_format == "html":
                if output_path:
                    saved_path = report_builder.save_html_report(output_path)
                else:
                    export_dir = Path(pbip_path).parent / "exports" / "aggregation_analysis"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    model_name = result.model_name.replace(" ", "_")
                    output_file = export_dir / f"{model_name}_Aggregation_{timestamp}.html"
                    saved_path = report_builder.save_html_report(str(output_file))

                return {
                    "success": True,
                    "format": "html",
                    "output_path": saved_path,
                    "summary": self._build_agg_summary(result, row_savings),
                }

            elif output_format == "json":
                json_data = report_builder.build_json_export()
                if output_path:
                    saved_path = report_builder.save_json_export(output_path)
                    return {
                        "success": True,
                        "format": "json",
                        "output_path": saved_path,
                        "data": json_data if include_visual_details else self._strip_agg_visual_details(json_data),
                    }
                return {
                    "success": True,
                    "format": "json",
                    "data": json_data if include_visual_details else self._strip_agg_visual_details(json_data),
                }

            elif output_format == "detailed":
                return {
                    "success": True,
                    "format": "detailed",
                    "report": report_builder.build_detailed_text(),
                }

            else:  # summary
                return {
                    "success": True,
                    "format": "summary",
                    "report": report_builder.build_summary_text(),
                }

        except Exception as e:
            logger.error(f"Aggregation analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "aggregation_error"
            }

    def _build_agg_summary(self, result, row_savings) -> Dict[str, Any]:
        """Build a brief summary for aggregation analysis."""
        summary = {
            "model_name": result.model_name,
            "aggregation_tables": len(result.aggregation_tables),
            "agg_aware_measures": len(result.agg_aware_measures),
            "agg_level_measures": len(result.agg_level_measures),
        }
        if result.report_summary:
            rs = result.report_summary
            summary["report"] = {
                "pages": rs.total_pages,
                "visuals_analyzed": rs.visuals_analyzed,
                "optimization_score": rs.optimization_score,
                "level_breakdown": rs.agg_level_breakdown,
            }
        if row_savings:
            summary["row_savings"] = {
                "total_saved": row_savings.total_rows_saved,
                "savings_percentage": row_savings.overall_savings_percentage,
            }
        return summary

    def _strip_agg_visual_details(self, json_data: Dict) -> Dict:
        """Strip detailed visual information from JSON output."""
        if "report_summary" in json_data and "pages" in json_data["report_summary"]:
            for page in json_data["report_summary"]["pages"]:
                page["visuals"] = [
                    {
                        "visual_id": v["visual_id"],
                        "visual_type": v["visual_type"],
                        "agg_level": v["agg_level"],
                        "agg_table": v["agg_table"],
                    }
                    for v in page.get("visuals", [])
                ]
        return json_data

    def get_column_lineage(
        self,
        repo_path: str,
        column_key: str,
        exclude_folders: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get detailed lineage information for a specific column."""
        try:
            from core.pbip.pbip_project_scanner import PbipProjectScanner
            from core.pbip.pbip_model_analyzer import TmdlModelAnalyzer
            from core.pbip.pbip_report_analyzer import PbirReportAnalyzer
            from core.pbip.pbip_dependency_engine import PbipDependencyEngine
            from core.pbip.pbip_enhanced_analyzer import EnhancedPbipAnalyzer

            # Analyze model
            scanner = PbipProjectScanner()
            projects = scanner.scan_repository(repo_path, exclude_folders or [])

            if not projects.get("semantic_models"):
                return {"success": False, "error": "No semantic models found"}

            model = projects["semantic_models"][0]
            analyzer = TmdlModelAnalyzer()
            model_data = analyzer.analyze_model(model["model_folder"])

            # Analyze report if available
            report_data = None
            if projects.get("reports"):
                report = projects["reports"][0]
                if report.get("report_folder"):
                    report_analyzer = PbirReportAnalyzer()
                    report_data = report_analyzer.analyze_report(report["report_folder"])

            # Build dependencies
            dep_engine = PbipDependencyEngine(model_data, report_data)
            dependencies = dep_engine.analyze_all_dependencies()

            # Get lineage
            enhanced_analyzer = EnhancedPbipAnalyzer(model_data, report_data, dependencies)
            lineage = enhanced_analyzer.lineage_analyzer.analyze_column_lineage()

            if column_key not in lineage:
                return {
                    "success": False,
                    "error": f"Column not found: {column_key}",
                    "available_columns": list(lineage.keys())[:10]
                }

            # Get impact analysis
            impact = enhanced_analyzer.lineage_analyzer.calculate_column_impact(column_key)

            return {
                "success": True,
                "column": column_key,
                "lineage": lineage[column_key],
                "impact_analysis": impact
            }

        except Exception as e:
            logger.error(f"Column lineage analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "lineage_error"
            }
