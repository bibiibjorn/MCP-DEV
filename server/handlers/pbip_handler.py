"""
PBIP Handler
Handles offline PBIP repository analysis
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_analyze_pbip_repository(args: Dict[str, Any]) -> Dict[str, Any]:
    """Offline PBIP repository analysis"""
    # This tool doesn't require active connection
    pbip_path = args.get('pbip_path')

    if not pbip_path:
        return {
            'success': False,
            'error': 'pbip_path parameter is required - must be a path to a .pbip project folder'
        }

    try:
        from core.pbip.pbip_enhanced_analyzer import EnhancedPbipAnalyzer

        # EnhancedPbipAnalyzer expects model_data, dependencies, and optional report_data
        # We need to parse the PBIP first
        from core.pbip.pbip_project_scanner import PbipProjectScanner
        from core.pbip.pbip_model_analyzer import TmdlModelAnalyzer
        from core.pbip.pbip_dependency_engine import PbipDependencyEngine

        # Step 1: Validate and scan the PBIP project
        from pathlib import Path

        pbip_path_obj = Path(pbip_path)
        if not pbip_path_obj.exists():
            return {
                'success': False,
                'error': f'PBIP path does not exist: {pbip_path}'
            }

        scanner = PbipProjectScanner()

        # Determine if it's a single .pbip file or a directory
        if pbip_path_obj.is_file() and pbip_path_obj.suffix == '.pbip':
            # Single PBIP file - use its parent directory
            repo_path = str(pbip_path_obj.parent)
        else:
            # Directory containing PBIP files
            repo_path = str(pbip_path_obj)

        project_info = scanner.scan_repository(repo_path)

        if not project_info or (not project_info.get('semantic_models') and not project_info.get('reports')):
            return {
                'success': False,
                'error': f"No PBIP projects found in: {repo_path}"
            }

        # Step 2: Parse model data from the first semantic model found
        semantic_models = project_info.get('semantic_models', [])
        if not semantic_models:
            return {
                'success': False,
                'error': 'No semantic models found in PBIP project'
            }

        # Use the first semantic model
        model_folder = semantic_models[0].get('model_folder')
        if not model_folder:
            return {
                'success': False,
                'error': 'Semantic model folder not found'
            }

        # Verify definition path exists
        definition_path = semantic_models[0].get('definition_path')
        if not definition_path:
            return {
                'success': False,
                'error': 'Semantic model definition path not found'
            }

        model_analyzer = TmdlModelAnalyzer()
        model_data = model_analyzer.analyze_model(model_folder)

        # Step 3: Parse report data if available
        report_data = None
        reports_list = project_info.get('reports', [])
        if reports_list and len(reports_list) > 0:
            # Use the first report found
            report_info = reports_list[0]
            report_folder = report_info.get('report_folder')
            if report_folder:
                from core.pbip.pbip_report_analyzer import PbirReportAnalyzer
                report_analyzer = PbirReportAnalyzer()
                try:
                    report_data = report_analyzer.analyze_report(report_folder)
                    logger.info(f"Parsed report: {len(report_data.get('pages', []))} pages")
                except Exception as e:
                    logger.warning(f"Failed to parse report: {e}")
                    report_data = None

        # Step 4: Analyze dependencies
        dep_engine = PbipDependencyEngine(model_data)
        dependencies = dep_engine.analyze_all_dependencies()

        # Step 5: Run enhanced analysis
        analyzer = EnhancedPbipAnalyzer(
            model_data=model_data,
            dependencies=dependencies,
            report_data=report_data
        )

        result = analyzer.run_full_analysis()

        # Step 6: Generate HTML report
        from core.pbip.pbip_html_generator import PbipHtmlGenerator
        import os
        from pathlib import Path

        # Determine output path - use exports folder in MCP server directory by default
        # Get the MCP server root directory (parent of the server folder)
        server_root = Path(__file__).parent.parent.parent
        default_exports_path = server_root / 'exports'

        # Create exports folder if it doesn't exist
        default_exports_path.mkdir(exist_ok=True)

        # Use user-provided path or default to MCP server exports folder
        output_path = args.get('output_path', str(default_exports_path))

        # If user provided a relative path, make it relative to server root
        if not os.path.isabs(output_path):
            output_path = str(server_root / output_path)

        # Get repository name from the path
        repo_name = os.path.basename(repo_path) if repo_path else "PBIP_Repository"

        logger.info(f"Saving HTML report to: {output_path}")

        html_generator = PbipHtmlGenerator()
        try:
            html_file_path = html_generator.generate_full_report(
                model_data=model_data,
                report_data=report_data,
                dependencies=dependencies,
                output_path=output_path,
                repository_name=repo_name,
                enhanced_results=result
            )

            return {
                'success': True,
                'html_report': html_file_path,
                'message': f'HTML report generated: {html_file_path}'
            }
        except Exception as html_error:
            logger.error(f"HTML generation failed: {html_error}", exc_info=True)
            return {
                'success': False,
                'error': f'HTML generation failed: {str(html_error)}'
            }

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'error': f'Required analyzer not available: {str(ie)}. This is an internal error.',
            'error_type': 'import_error'
        }
    except FileNotFoundError as fnf:
        return {
            'success': False,
            'error': f'PBIP path not found or invalid: {str(fnf)}'
        }
    except Exception as e:
        logger.error(f"Error analyzing PBIP: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error analyzing PBIP: {str(e)}'
        }

def register_pbip_handlers(registry):
    """Register all PBIP handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="analyze_pbip_repository",
            description="Offline PBIP repository analysis with HTML report export",
            handler=handle_analyze_pbip_repository,
            input_schema=TOOL_SCHEMAS.get('analyze_pbip_repository', {}),
            category="pbip",
            sort_order=43
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} PBIP handlers")
