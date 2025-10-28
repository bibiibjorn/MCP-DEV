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
        from core.model.dependency_analyzer import DependencyAnalyzer

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
        model_path = semantic_models[0].get('definition_path')
        if not model_path:
            return {
                'success': False,
                'error': 'Semantic model definition path not found'
            }

        model_analyzer = TmdlModelAnalyzer(model_path)
        model_data = model_analyzer.parse_model()

        # Step 3: Analyze dependencies
        dep_analyzer = DependencyAnalyzer()
        dependencies = dep_analyzer.analyze_all(model_data)

        # Step 4: Run enhanced analysis
        analyzer = EnhancedPbipAnalyzer(
            model_data=model_data,
            dependencies=dependencies,
            report_data=project_info.get('reports', [])
        )

        result = analyzer.analyze_full()

        return {
            'success': True,
            'analysis': result,
            'project_info': {
                'semantic_models_count': len(semantic_models),
                'reports_count': len(project_info.get('reports', []))
            }
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
            description="Offline PBIP repository analysis",
            handler=handle_analyze_pbip_repository,
            input_schema=TOOL_SCHEMAS.get('analyze_pbip_repository', {}),
            category="pbip",
            sort_order=80
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} PBIP handlers")
