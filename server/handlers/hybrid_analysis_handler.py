"""
Hybrid Analysis MCP Tool Handlers

Provides MCP tool handlers for PBIP dependency analysis.
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from core.pbip.pbip_dependency_engine import PbipDependencyEngine
from core.pbip.pbip_model_analyzer import TmdlModelAnalyzer
from core.pbip.pbip_report_analyzer import PbirReportAnalyzer
from core.utilities.pbip_dependency_html_generator import generate_pbip_dependency_html
from server.registry import ToolDefinition
from server.tool_schemas import TOOL_SCHEMAS

logger = logging.getLogger(__name__)


def handle_generate_pbip_dependency_diagram(
    pbip_folder_path: str,
    auto_open: bool = True,
    output_path: Optional[str] = None,
    main_item: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an interactive HTML dependency diagram for a PBIP project.

    Analyzes the PBIP model and report (if available) to create a comprehensive
    dependency visualization showing:
    - Visuals and their field usage
    - Measures and their dependencies
    - Columns and which measures use them
    - Field Parameters and their column references

    Features a sidebar with ALL measures, columns, and field parameters.
    Click any item in the sidebar to view its dependencies.

    Args:
        pbip_folder_path: Path to .SemanticModel folder or parent folder containing one
        auto_open: Whether to automatically open the diagram in browser (default: True)
        output_path: Optional custom output path for the HTML file
        main_item: Optional specific item to select initially (e.g., 'Table[Measure]')

    Returns:
        Result dictionary with success status and diagram path
    """
    try:
        # Validate and auto-detect PBIP folder
        pbip_path = Path(pbip_folder_path)
        if not pbip_path.exists():
            return {
                'success': False,
                'error': f'PBIP folder not found: {pbip_folder_path}',
                'error_type': 'not_found'
            }

        # Auto-detect .SemanticModel folder if parent folder is provided
        if not pbip_path.name.endswith('.SemanticModel'):
            # Search for .SemanticModel folders
            semantic_folders = list(pbip_path.rglob('*.SemanticModel'))

            if len(semantic_folders) == 0:
                return {
                    'success': False,
                    'error': f'No .SemanticModel folder found in: {pbip_folder_path}',
                    'error_type': 'not_found',
                    'hint': 'Please provide the path to a .SemanticModel folder or a parent folder containing one'
                }
            elif len(semantic_folders) == 1:
                pbip_path = semantic_folders[0]
                logger.info(f"Auto-detected .SemanticModel folder: {pbip_path}")
            else:
                # Multiple .SemanticModel folders found
                folder_names = [str(f.relative_to(pbip_folder_path)) for f in semantic_folders]
                return {
                    'success': False,
                    'error': f'Multiple .SemanticModel folders found in: {pbip_folder_path}',
                    'error_type': 'multiple_found',
                    'found_folders': folder_names,
                    'hint': 'Please specify which .SemanticModel folder to use'
                }

        # Get model name
        model_name = pbip_path.stem.replace('.SemanticModel', '')

        logger.info(f"Generating PBIP dependency diagram for: {model_name}")
        logger.info(f"  - TMDL source: {pbip_path}")

        # Step 1: Parse TMDL model
        logger.info("  - Parsing TMDL model...")
        tmdl_analyzer = TmdlModelAnalyzer()
        model_data = tmdl_analyzer.analyze_model(str(pbip_path))

        # Step 2: Parse report data if PBIR exists
        # Search strategies:
        # 1. Same name with .Report extension (e.g., Model.SemanticModel -> Model.Report)
        # 2. Any .Report folder in the same parent directory
        report_data = None
        report_folder = None

        # Strategy 1: Exact name match
        report_folder_name = pbip_path.name.replace('.SemanticModel', '.Report')
        pbir_path = pbip_path.parent / report_folder_name / "definition.pbir"

        if pbir_path.exists():
            report_folder = pbip_path.parent / report_folder_name
        else:
            # Strategy 2: Search for any .Report folder in parent
            report_folders = list(pbip_path.parent.glob("*.Report"))
            if report_folders:
                # Use the first one found
                report_folder = report_folders[0]
                report_folder_name = report_folder.name
                logger.info(f"  - Found alternative report folder: {report_folder_name}")

        if report_folder:
            # Check for PBIR structure (definition/pages/) vs old structure (report.json)
            definition_path = report_folder / "definition"
            if definition_path.exists():
                logger.info(f"  - Parsing PBIR report from {report_folder_name}...")
                try:
                    report_analyzer = PbirReportAnalyzer()
                    report_data = report_analyzer.analyze_report(str(report_folder))
                    logger.info(f"    ✓ Found {len(report_data.get('pages', []))} pages")
                except Exception as e:
                    logger.warning(f"    ✗ Could not parse report: {e}")
                    report_data = None
            else:
                logger.info(f"  - Found {report_folder_name} but it uses old format (not PBIR), skipping visual analysis")
        else:
            logger.info(f"  - No report folder found, visual dependencies will be empty")

        # Step 3: Run dependency analysis
        logger.info("  - Analyzing dependencies...")
        engine = PbipDependencyEngine(model_data, report_data)
        dependency_data = engine.analyze_all_dependencies()

        logger.info(f"    ✓ Analyzed {dependency_data['summary']['total_measures']} measures, "
                   f"{dependency_data['summary']['total_columns']} columns")
        if report_data:
            logger.info(f"    ✓ Analyzed {dependency_data['summary'].get('total_visuals', 0)} visuals "
                       f"across {dependency_data['summary'].get('total_pages', 0)} pages")

        # Step 4: Generate HTML diagram
        logger.info("  - Generating interactive HTML diagram...")
        html_path = generate_pbip_dependency_html(
            dependency_data=dependency_data,
            model_name=model_name,
            auto_open=auto_open,
            output_path=output_path,
            main_item=main_item
        )

        if html_path:
            logger.info(f"  ✓ Diagram generated: {html_path}")
            return {
                'success': True,
                'message': f"✓ PBIP dependency diagram generated successfully",
                'diagram_path': html_path,
                'model_name': model_name,
                'initial_selection': main_item if main_item else 'First measure in model',
                'summary': {
                    'visuals': dependency_data['summary'].get('total_visuals', 0),
                    'pages': dependency_data['summary'].get('total_pages', 0),
                    'measures': dependency_data['summary']['total_measures'],
                    'columns': dependency_data['summary']['total_columns'],
                    'field_parameters': len(dependency_data.get('column_to_field_params', {})),
                    'unused_measures': dependency_data['summary']['unused_measures'],
                    'unused_columns': dependency_data['summary']['unused_columns']
                },
                'features': [
                    'Left sidebar with ALL measures, columns, and field parameters',
                    'Click any item in sidebar to view its dependencies in tables',
                    'Search/filter items by name',
                    'Items grouped by table with expand/collapse',
                    'Clean table-based upstream & downstream dependency view',
                    'Model overview with statistics',
                    'Auto-opens in browser' if auto_open else 'Saved to file'
                ]
            }
        else:
            return {
                'success': False,
                'error': 'Failed to generate HTML diagram',
                'error_type': 'generation_error'
            }

    except Exception as e:
        logger.error(f"Error generating PBIP dependency diagram: {str(e)}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': f"Diagram generation failed: {str(e)}",
            'error_type': 'generation_error',
            'context': {
                'pbip_folder_path': pbip_folder_path
            }
        }


def register_hybrid_analysis_handlers(registry):
    """Register hybrid analysis tool handlers"""

    # Simple wrapper to handle arguments dict
    def make_handler(func):
        def wrapper(args):
            return func(**args)
        return wrapper

    registry.register(ToolDefinition(
        name='07_PBIP_Dependency_Analysis',
        description='[PBIP Analysis] Generate interactive HTML dependency analysis for PBIP project. Features a sidebar with ALL measures, columns, and field parameters - click any item to view its upstream and downstream dependencies in clean tables. Shows model overview with statistics. Auto-opens in browser.',
        handler=make_handler(handle_generate_pbip_dependency_diagram),
        input_schema=TOOL_SCHEMAS['pbip_dependency_analysis'],
        category='pbip',
        sort_order=72  # 07 = PBIP Analysis
    ))

    logger.info("Registered 1 hybrid analysis handler")
