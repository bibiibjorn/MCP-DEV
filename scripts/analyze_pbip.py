#!/usr/bin/env python3
"""
Standalone script to analyze PBIP repositories.

This script can be run independently of the MCP server to generate comprehensive
analysis reports for Power BI Project repositories.

Usage:
    python scripts/analyze_pbip.py <repo_path> [options]

Example:
    python scripts/analyze_pbip.py "C:/path/to/repo" --output "exports/analysis"
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.pbip.pbip_project_scanner import PbipProjectScanner
from core.pbip.pbip_model_analyzer import TmdlModelAnalyzer
from core.pbip.pbip_report_analyzer import PbirReportAnalyzer
from core.pbip.pbip_dependency_engine import PbipDependencyEngine
from core.pbip.pbip_html_generator import PbipHtmlGenerator
from core.pbip.pbip_enhanced_analyzer import EnhancedPbipAnalyzer


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def analyze_pbip_repository(
    repo_path: str,
    output_path: str,
    exclude_folders: list,
    verbose: bool = False,
    bpa_rules_path: str = None,
    enable_enhanced: bool = True
) -> dict:
    """
    Analyze a PBIP repository and generate comprehensive report.

    Args:
        repo_path: Path to the repository
        output_path: Output directory for reports (absolute or relative to MCP server root)
        exclude_folders: List of folders to exclude
        verbose: Enable verbose logging
        bpa_rules_path: Optional path to BPA rules JSON file
        enable_enhanced: Enable enhanced analysis features (lineage, quality metrics, etc.)

    Returns:
        Dictionary with analysis results

    Raises:
        FileNotFoundError: If repository path doesn't exist
        ValueError: If analysis fails
    """
    logger = logging.getLogger(__name__)

    # Ensure output path is resolved relative to MCP server directory
    if not os.path.isabs(output_path):
        # Get MCP server root directory (parent of scripts/)
        server_root = os.path.dirname(parent_dir)
        output_path = os.path.join(server_root, output_path)

    logger.info("=" * 70)
    logger.info("PBIP Repository Analyzer")
    logger.info("=" * 70)
    logger.info(f"Repository: {repo_path}")
    logger.info(f"Output: {output_path}")
    if exclude_folders:
        logger.info(f"Excluding: {', '.join(exclude_folders)}")
    logger.info("=" * 70)

    # Step 1: Scan repository
    logger.info("Step 1: Scanning repository...")
    scanner = PbipProjectScanner()
    projects = scanner.scan_repository(repo_path, exclude_folders)

    semantic_models = projects.get("semantic_models", [])
    reports = projects.get("reports", [])

    logger.info(f"Found {len(semantic_models)} semantic model(s)")
    logger.info(f"Found {len(reports)} report(s)")

    if not semantic_models:
        logger.warning("No semantic models found in repository!")
        return {
            "success": False,
            "error": "No semantic models found"
        }

    # Step 2: Analyze semantic models
    logger.info("\nStep 2: Analyzing semantic models...")
    model_results = {}

    for model in semantic_models:
        model_name = model["name"]
        model_folder = model.get("model_folder")

        if not model_folder:
            logger.warning(f"No model folder for {model_name}, skipping")
            continue

        logger.info(f"  Analyzing model: {model_name}")
        try:
            analyzer = TmdlModelAnalyzer()
            model_data = analyzer.analyze_model(model_folder)
            model_results[model_name] = model_data

            # Log summary
            table_count = len(model_data.get("tables", []))
            measure_count = sum(
                len(t.get("measures", []))
                for t in model_data.get("tables", [])
            )
            logger.info(f"    {table_count} tables, {measure_count} measures")

        except Exception as e:
            logger.error(f"  Failed to analyze model {model_name}: {e}")
            if verbose:
                raise

    # Step 3: Analyze reports
    logger.info("\nStep 3: Analyzing reports...")
    report_results = {}

    for report in reports:
        report_name = report["name"]
        report_folder = report.get("report_folder")

        if not report_folder:
            logger.warning(f"No report folder for {report_name}, skipping")
            continue

        logger.info(f"  Analyzing report: {report_name}")
        try:
            analyzer = PbirReportAnalyzer()
            report_data = analyzer.analyze_report(report_folder)
            report_results[report_name] = report_data

            # Log summary
            page_count = len(report_data.get("pages", []))
            visual_count = sum(
                len(p.get("visuals", []))
                for p in report_data.get("pages", [])
            )
            logger.info(f"    {page_count} pages, {visual_count} visuals")

        except Exception as e:
            logger.error(f"  Failed to analyze report {report_name}: {e}")
            if verbose:
                raise

    # Step 4: Dependency analysis
    logger.info("\nStep 4: Performing dependency analysis...")

    # For now, analyze the first model (can be extended for multi-model)
    primary_model_name = list(model_results.keys())[0] if model_results else None
    primary_report_name = list(report_results.keys())[0] if report_results else None

    if not primary_model_name:
        logger.error("No models were successfully analyzed")
        return {
            "success": False,
            "error": "Model analysis failed"
        }

    model_data = model_results[primary_model_name]
    report_data = report_results.get(primary_report_name) if primary_report_name else None

    try:
        dep_engine = PbipDependencyEngine(model_data, report_data)
        dependencies = dep_engine.analyze_all_dependencies()

        logger.info("  Dependency analysis complete")
        logger.info(f"    Measures with dependencies: {dependencies['summary']['measures_with_dependencies']}")
        logger.info(f"    Unused measures: {dependencies['summary']['unused_measures']}")
        logger.info(f"    Unused columns: {dependencies['summary']['unused_columns']}")

    except Exception as e:
        logger.error(f"  Dependency analysis failed: {e}")
        if verbose:
            raise
        dependencies = {}

    # Step 4.5: Enhanced analysis (if enabled)
    enhanced_results = None
    if enable_enhanced:
        logger.info("\nStep 4.5: Running enhanced analysis...")
        try:
            enhanced_analyzer = EnhancedPbipAnalyzer(model_data, report_data, dependencies)
            enhanced_results = enhanced_analyzer.run_full_analysis(bpa_rules_path)

            # Log summary
            logger.info("  Enhanced analysis complete")
            if "column_lineage" in enhanced_results.get("analyses", {}):
                lineage_count = len(enhanced_results["analyses"]["column_lineage"])
                logger.info(f"    Column lineage tracked: {lineage_count} columns")

            if "dax_quality" in enhanced_results.get("analyses", {}):
                dax_summary = enhanced_results["analyses"]["dax_quality"].get("summary", {})
                logger.info(f"    DAX quality: {dax_summary.get('high_complexity_measures', 0)} high-complexity measures")

            if "relationships" in enhanced_results.get("analyses", {}):
                rel_metrics = enhanced_results["analyses"]["relationships"].get("metrics", {})
                logger.info(f"    Relationships: {rel_metrics.get('issues_found', 0)} issues found")

        except Exception as e:
            logger.error(f"  Enhanced analysis failed: {e}")
            if verbose:
                raise
            enhanced_results = None

    # Step 5: Generate HTML report
    logger.info("\nStep 5: Generating HTML dashboard...")

    try:
        generator = PbipHtmlGenerator()
        html_path = generator.generate_full_report(
            model_data,
            report_data,
            dependencies,
            output_path,
            os.path.basename(repo_path),
            enhanced_results=enhanced_results
        )

        logger.info(f"  HTML report generated: {html_path}")

    except Exception as e:
        logger.error(f"  HTML generation failed: {e}")
        if verbose:
            raise
        html_path = None

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Analysis Complete!")
    logger.info("=" * 70)
    logger.info(f"Models analyzed: {len(model_results)}")
    logger.info(f"Reports analyzed: {len(report_results)}")
    if html_path:
        logger.info(f"HTML report: {html_path}")
    logger.info("=" * 70)

    return {
        "success": True,
        "models": model_results,
        "reports": report_results,
        "dependencies": dependencies,
        "enhanced_analysis": enhanced_results,
        "html_path": html_path
    }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Analyze PBIP repository and generate comprehensive report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python scripts/analyze_pbip.py "C:/path/to/repo"

  # Custom output path
  python scripts/analyze_pbip.py "C:/path/to/repo" --output "exports/my_analysis"

  # Exclude specific folders
  python scripts/analyze_pbip.py "C:/path/to/repo" --exclude "R0100-Old.Report" "Backup"

  # Verbose output
  python scripts/analyze_pbip.py "C:/path/to/repo" --verbose
        """
    )

    parser.add_argument(
        "repo_path",
        help="Path to PBIP repository root directory"
    )

    parser.add_argument(
        "--output",
        "-o",
        default="exports/pbip_analysis",
        help="Output directory for analysis reports (default: exports/pbip_analysis)"
    )

    parser.add_argument(
        "--exclude",
        "-e",
        nargs="+",
        default=[],
        help="Folders to exclude from analysis"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--bpa-rules",
        "-b",
        default="config/bpa_rules_comprehensive.json",
        help="Path to BPA rules JSON file (default: comprehensive rules)"
    )

    parser.add_argument(
        "--no-enhanced",
        action="store_true",
        help="Disable enhanced analysis features (use basic analysis only)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Validate repository path
    if not os.path.exists(args.repo_path):
        print(f"Error: Repository path does not exist: {args.repo_path}")
        sys.exit(1)

    if not os.path.isdir(args.repo_path):
        print(f"Error: Path is not a directory: {args.repo_path}")
        sys.exit(1)

    # Run analysis
    try:
        result = analyze_pbip_repository(
            args.repo_path,
            args.output,
            args.exclude,
            args.verbose,
            args.bpa_rules,
            not args.no_enhanced
        )

        if result.get("success"):
            print("\nSuccess! Analysis complete.")
            if result.get("html_path"):
                print(f"Open the report: {result['html_path']}")
            sys.exit(0)
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(130)

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=args.verbose)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
