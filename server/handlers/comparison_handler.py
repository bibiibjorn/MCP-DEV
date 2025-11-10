"""
Comparison Handler
Handles model comparison operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_prepare_model_comparison(args: Dict[str, Any]) -> Dict[str, Any]:
    """STEP 1: Detect both models for comparison"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    connection_manager = connection_state.connection_manager
    if not connection_manager:
        return ErrorHandler.handle_manager_unavailable('connection_manager')

    # Detect all instances
    instances = connection_manager.detect_instances()

    if not instances or len(instances.get('instances', [])) < 2:
        return {
            'success': False,
            'error': 'Need at least 2 Power BI Desktop instances running for comparison',
            'detected_instances': len(instances.get('instances', [])),
            'instruction': 'Please open both Power BI models in separate Desktop instances'
        }

    return {
        'success': True,
        'message': 'Ready for comparison',
        'instances': instances.get('instances', []),
        'instruction': 'Please identify OLD and NEW models, then use compare_pbi_models with their ports'
    }

def handle_compare_pbi_models(args: Dict[str, Any]) -> Dict[str, Any]:
    """STEP 2: Compare models after user confirms OLD/NEW"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    connection_manager = connection_state.connection_manager
    if not connection_manager:
        return ErrorHandler.handle_manager_unavailable('connection_manager')

    old_port = args.get('old_port')
    new_port = args.get('new_port')

    if not old_port or not new_port:
        return {
            'success': False,
            'error': 'old_port and new_port parameters are required'
        }

    # Use multi-instance manager to compare
    try:
        from core.operations.multi_instance_manager import MultiInstanceManager
        multi_mgr = MultiInstanceManager()

        return multi_mgr.compare_models(old_port, new_port)

    except ImportError:
        return {
            'success': False,
            'error': 'MultiInstanceManager not available',
            'error_type': 'import_error'
        }
    except Exception as e:
        logger.error(f"Error comparing models: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error comparing models: {str(e)}'
        }

def register_comparison_handlers(registry):
    """Register all comparison handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="prepare_model_comparison",
            description="STEP 1: Detect both models for comparison",
            handler=handle_prepare_model_comparison,
            input_schema=TOOL_SCHEMAS.get('prepare_model_comparison', {}),
            category="comparison",
            sort_order=41
        ),
        ToolDefinition(
            name="compare_pbi_models",
            description="STEP 2: Compare models after user confirms OLD/NEW",
            handler=handle_compare_pbi_models,
            input_schema=TOOL_SCHEMAS.get('compare_pbi_models', {}),
            category="comparison",
            sort_order=42
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} comparison handlers")
