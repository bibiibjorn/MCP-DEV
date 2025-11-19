"""
Workflow Handler

Handles execution of pre-defined multi-step analysis workflows.
"""

from typing import Dict, Any
import logging
from core.infrastructure.connection_state import connection_state
from core.orchestration.workflow_templates import WorkflowExecutor, list_available_workflows, get_workflow_by_trigger
from server.tool_schemas import TOOL_SCHEMAS
from server.registry import ToolDefinition

logger = logging.getLogger(__name__)


def handle_execute_workflow(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a predefined workflow

    Args:
        args: {
            'workflow': str - Workflow name/ID to execute
            'inputs': dict - Input parameters for the workflow
            'context': dict - Optional additional context
        }

    Returns:
        Workflow execution results
    """
    try:
        workflow_name = args.get('workflow')
        inputs = args.get('inputs', {})
        context = args.get('context', {})

        if not workflow_name:
            return {
                'success': False,
                'error': 'Workflow name is required',
                'available_workflows': [w['workflow_id'] for w in list_available_workflows()]
            }

        # Create workflow executor
        executor = WorkflowExecutor(connection_state)

        # Execute workflow
        result = executor.execute_workflow(workflow_name, inputs, context)

        return result

    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Workflow execution failed: {str(e)}'
        }


def handle_list_workflows(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List all available workflows

    Args:
        args: Optional filters

    Returns:
        List of available workflows with metadata
    """
    try:
        workflows = list_available_workflows()

        return {
            'success': True,
            'workflows': workflows,
            'count': len(workflows)
        }

    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Failed to list workflows: {str(e)}'
        }


def handle_suggest_workflow(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest a workflow based on user request

    Args:
        args: {
            'request': str - User's natural language request
        }

    Returns:
        Suggested workflow or none
    """
    try:
        user_request = args.get('request', '')

        if not user_request:
            return {
                'success': False,
                'error': 'Request text is required'
            }

        # Try to find matching workflow
        workflow = get_workflow_by_trigger(user_request)

        if workflow:
            return {
                'success': True,
                'suggested_workflow': {
                    'workflow_id': workflow.workflow_id,
                    'name': workflow.name,
                    'description': workflow.description,
                    'required_inputs': [
                        param for param, schema in workflow.input_schema.items()
                        if schema.get('required', False)
                    ],
                    'expected_duration_seconds': workflow.expected_duration_seconds
                }
            }
        else:
            return {
                'success': True,
                'suggested_workflow': None,
                'message': 'No matching workflow found for this request'
            }

    except Exception as e:
        logger.error(f"Error suggesting workflow: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Failed to suggest workflow: {str(e)}'
        }


def handle_smart_request(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a natural language request with intelligent routing

    Args:
        args: {
            'request': str - User's natural language request
            'context': dict - Optional context (previously used tools, objects, etc.)
        }

    Returns:
        Execution results from the routed tool or workflow
    """
    try:
        from core.intelligence.tool_router import IntelligentToolRouter

        user_request = args.get('request', '')
        context = args.get('context', {})

        if not user_request:
            return {
                'success': False,
                'error': 'Request text is required'
            }

        # Route the request
        router = IntelligentToolRouter()
        routing = router.route_request(user_request, context)

        if routing.get('routing_strategy') == 'error':
            return {
                'success': False,
                'error': routing.get('error'),
                'explanation': routing.get('explanation')
            }

        # Execute based on routing strategy
        if routing.get('routing_strategy') == 'workflow':
            # Execute workflow
            workflow_name = routing['primary_action']['workflow']
            inputs = routing['primary_action']['inputs']

            executor = WorkflowExecutor(connection_state)
            result = executor.execute_workflow(workflow_name, inputs, context)

            result['routing_explanation'] = routing.get('explanation')
            return result

        elif routing.get('routing_strategy') == 'single_tool':
            # Execute single tool
            tool_name = routing['primary_action']['tool']
            inputs = routing['primary_action']['inputs']

            from server.registry import handler_registry
            handler = handler_registry.get_handler(tool_name)

            if handler:
                result = handler(inputs)
                result['routing_explanation'] = routing.get('explanation')
                return result
            else:
                return {
                    'success': False,
                    'error': f'Handler not found for tool: {tool_name}'
                }

        elif routing.get('routing_strategy') == 'multi_tool':
            # Execute multiple tools in sequence
            results = []

            # Execute primary action
            primary_tool = routing['primary_action']['tool']
            primary_inputs = routing['primary_action']['inputs']

            from server.registry import handler_registry
            handler = handler_registry.get_handler(primary_tool)

            if handler:
                primary_result = handler(primary_inputs)
                results.append({
                    'tool': primary_tool,
                    'result': primary_result
                })

            # Execute follow-up actions
            for action in routing.get('follow_up_actions', []):
                tool_name = action['tool']
                inputs = action['inputs']

                handler = handler_registry.get_handler(tool_name)
                if handler:
                    result = handler(inputs)
                    results.append({
                        'tool': tool_name,
                        'result': result
                    })

            return {
                'success': True,
                'routing_strategy': 'multi_tool',
                'routing_explanation': routing.get('explanation'),
                'results': results
            }

        else:
            return {
                'success': False,
                'error': f'Unknown routing strategy: {routing.get("routing_strategy")}'
            }

    except Exception as e:
        logger.error(f"Error handling smart request: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Smart request failed: {str(e)}'
        }


def register_workflow_handlers(registry):
    """Register all workflow and intelligence handlers"""

    # Workflow execution
    registry.register(ToolDefinition(
        name='execute_workflow',
        description='Execute a pre-defined multi-step analysis workflow (complete_measure_analysis, model_health_check, measure_impact_analysis, table_profiling, performance_investigation, relationship_validation)',
        handler=handle_execute_workflow,
        input_schema=TOOL_SCHEMAS['execute_workflow'],
        category='workflows',
        sort_order=140
    ))

    # List available workflows
    registry.register(ToolDefinition(
        name='list_workflows',
        description='List all available analysis workflows with their descriptions and requirements',
        handler=handle_list_workflows,
        input_schema=TOOL_SCHEMAS['list_workflows'],
        category='workflows',
        sort_order=141
    ))

    # Suggest workflow based on request
    registry.register(ToolDefinition(
        name='suggest_workflow',
        description='Suggest an appropriate workflow based on a natural language request',
        handler=handle_suggest_workflow,
        input_schema=TOOL_SCHEMAS['suggest_workflow'],
        category='workflows',
        sort_order=142
    ))

    # Smart request routing
    registry.register(ToolDefinition(
        name='smart_request',
        description='Handle a natural language request with intelligent routing to the best tool or workflow - automatically determines what to execute',
        handler=handle_smart_request,
        input_schema=TOOL_SCHEMAS['smart_request'],
        category='workflows',
        sort_order=143
    ))

    logger.info("Registered 4 workflow and intelligence handlers")
