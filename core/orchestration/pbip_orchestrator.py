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
