"""
Comparison Handler
Handles model comparison operations with workflow templates
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
            'instruction': 'Please open both Power BI models in separate Desktop instances',
            'workflow': {
                'name': 'Model Comparison',
                'status': 'insufficient_instances',
                'current_step': 0,
                'total_steps': 3,
                'note': 'At least 2 Power BI Desktop instances are required'
            }
        }

    # Add workflow template guidance
    inst_list = instances.get('instances', [])
    return {
        'success': True,
        'message': 'Ready for comparison',
        'instances': inst_list,
        'instruction': 'Please identify OLD and NEW models, then use compare_pbi_models with their ports',
        'workflow': {
            'name': 'Model Comparison',
            'current_step': 1,
            'total_steps': 3,
            'steps': [
                {
                    'step': 1,
                    'status': 'completed',
                    'description': 'Detect models',
                    'result': f'Found {len(inst_list)} models'
                },
                {
                    'step': 2,
                    'status': 'awaiting_user_input',
                    'description': 'User identifies OLD vs NEW models',
                    'prompt': 'Which model is the OLD version and which is NEW?',
                    'instances': [
                        {
                            'index': i,
                            'port': inst.get('port'),
                            'name': inst.get('model_name', 'Unknown'),
                            'file_path': inst.get('file_path', 'Unknown')
                        }
                        for i, inst in enumerate(inst_list)
                    ],
                    'required_input': 'old_port and new_port parameters'
                },
                {
                    'step': 3,
                    'status': 'pending',
                    'description': 'Compare models',
                    'next_tool': 'compare_pbi_models',
                    'next_action': 'Call compare_pbi_models with old_port and new_port'
                }
            ]
        },
        'next_action': {
            'tool': 'compare_pbi_models',
            'description': 'Compare the two models after identifying OLD/NEW',
            'required_params': ['old_port', 'new_port']
        }
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
            'error': 'old_port and new_port parameters are required',
            'workflow': {
                'name': 'Model Comparison',
                'current_step': 2,
                'status': 'missing_parameters',
                'error': 'Please provide both old_port and new_port',
                'hint': 'Use the port numbers from prepare_model_comparison output'
            }
        }

    # Use multi-instance manager to compare
    try:
        from core.operations.multi_instance_manager import MultiInstanceManager
        multi_mgr = MultiInstanceManager()

        result = multi_mgr.compare_models(old_port, new_port)

        # Add workflow completion status
        if result.get('success'):
            result['workflow'] = {
                'name': 'Model Comparison',
                'current_step': 3,
                'total_steps': 3,
                'status': 'completed',
                'summary': f'Compared models (old: {old_port}, new: {new_port})',
                'next_recommendations': [
                    {
                        'action': 'Document comparison results',
                        'tool': 'generate_model_documentation_word',
                        'description': 'Create a Word document with comparison findings'
                    }
                ]
            }

        return result

    except ImportError:
        return {
            'success': False,
            'error': 'MultiInstanceManager not available',
            'error_type': 'import_error',
            'workflow': {
                'name': 'Model Comparison',
                'current_step': 2,
                'status': 'error',
                'error': 'Comparison feature not available'
            }
        }
    except Exception as e:
        logger.error(f"Error comparing models: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error comparing models: {str(e)}',
            'workflow': {
                'name': 'Model Comparison',
                'current_step': 2,
                'status': 'error',
                'error': str(e)
            }
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
