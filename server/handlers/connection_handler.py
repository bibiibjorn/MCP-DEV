"""
Connection Handler
Simplified - just the 2 essential connection tools
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_detect_powerbi_desktop(args: Dict[str, Any]) -> Dict[str, Any]:
    """Detect running Power BI Desktop instances"""
    try:
        connection_manager = connection_state.connection_manager
        if not connection_manager:
            return ErrorHandler.handle_manager_unavailable('connection_manager')

        instances = connection_manager.detect_instances()
        return {
            'success': True,
            'instances': instances,
            'count': len(instances)
        }
    except Exception as e:
        logger.error(f"Error detecting instances: {e}", exc_info=True)
        return ErrorHandler.handle_unexpected_error('detect_powerbi_desktop', e)

def handle_connect_to_powerbi(args: Dict[str, Any]) -> Dict[str, Any]:
    """Connect to Power BI Desktop instance"""
    try:
        connection_manager = connection_state.connection_manager
        if not connection_manager:
            return ErrorHandler.handle_manager_unavailable('connection_manager')

        model_index = args.get('model_index', 0)

        # Auto-detect if not connected
        instances = connection_manager.detect_instances()
        if not instances:
            return {
                'success': False,
                'error': 'No Power BI Desktop instances detected',
                'error_type': 'no_instances'
            }

        # Connect
        result = connection_manager.connect(model_index)
        if result.get('success'):
            # Initialize managers
            connection_state.set_connection_manager(connection_manager)
            init_result = connection_state.initialize_managers()

            # Check if initialization succeeded
            if not init_result.get('success'):
                # Connection succeeded but manager initialization failed
                logger.error(f"Manager initialization failed: {init_result.get('error')}")
                return {
                    'success': False,
                    'error': 'Connected to Power BI but failed to initialize service managers',
                    'error_type': 'initialization_failed',
                    'connection_info': result,
                    'initialization_error': init_result,
                    'suggestions': [
                        'Check the detailed error in initialization_error.error_details',
                        'Verify all required .NET assemblies are available',
                        'Try restarting Claude Desktop to reset the MCP server',
                        'Check MCP server logs for more information'
                    ]
                }

            # Add initialization status to successful result
            result['managers_initialized'] = True
            result['query_executor_available'] = init_result.get('query_executor_available', False)

        return result

    except Exception as e:
        logger.error(f"Error connecting: {e}", exc_info=True)
        return ErrorHandler.handle_unexpected_error('connect_to_powerbi', e)

def handle_reinitialize_managers(args: Dict[str, Any]) -> Dict[str, Any]:
    """Reinitialize service managers (useful for recovery from initialization errors)"""
    try:
        if not connection_state.is_connected():
            return {
                'success': False,
                'error': 'Not connected to Power BI Desktop',
                'error_type': 'not_connected',
                'suggestions': [
                    'Run detect_powerbi_desktop to find instances',
                    'Run connect_to_powerbi to establish connection'
                ]
            }

        force_reinit = args.get('force', True)
        logger.info(f"Reinitializing managers (force={force_reinit})...")

        init_result = connection_state.initialize_managers(force_reinit=force_reinit)

        if init_result.get('success'):
            return {
                'success': True,
                'message': 'Managers reinitialized successfully',
                'query_executor_available': connection_state.query_executor is not None,
                'managers_status': connection_state.get_status()['managers']
            }
        else:
            return init_result

    except Exception as e:
        logger.error(f"Error reinitializing managers: {e}", exc_info=True)
        return ErrorHandler.handle_unexpected_error('reinitialize_managers', e)

def handle_check_connection_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Check current connection and manager initialization status"""
    try:
        status = connection_state.get_status()

        # Add more diagnostic information
        status['recommendations'] = []

        if not status['connected']:
            status['recommendations'].append('Not connected. Run detect_powerbi_desktop and connect_to_powerbi')
        elif not status['managers_initialized']:
            status['recommendations'].append('Connected but managers not initialized. Try reinitialize_managers tool')
        elif not status['managers']['query_executor']:
            status['recommendations'].append('Query executor not available. Run reinitialize_managers with force=true')
        else:
            status['recommendations'].append('All systems operational')

        status['success'] = True
        return status

    except Exception as e:
        logger.error(f"Error checking status: {e}", exc_info=True)
        return ErrorHandler.handle_unexpected_error('check_connection_status', e)

def register_connection_handlers(registry):
    """Register connection handlers"""
    tools = [
        ToolDefinition(
            name="detect_powerbi_desktop",
            description="Detect running Power BI Desktop instances",
            handler=handle_detect_powerbi_desktop,
            input_schema={"type": "object", "properties": {}, "required": []},
            category="connection",
            sort_order=0
        ),
        ToolDefinition(
            name="connect_to_powerbi",
            description="Connect to Power BI Desktop (auto-detect or specify model_index)",
            handler=handle_connect_to_powerbi,
            input_schema={
                "type": "object",
                "properties": {
                    "model_index": {"type": "integer", "description": "Index of the model to connect to (default: 0)"}
                },
                "required": []
            },
            category="connection",
            sort_order=1
        ),
        ToolDefinition(
            name="check_connection_status",
            description="Check current connection status and manager initialization state",
            handler=handle_check_connection_status,
            input_schema={"type": "object", "properties": {}, "required": []},
            category="connection",
            sort_order=2
        ),
        ToolDefinition(
            name="reinitialize_managers",
            description="Reinitialize service managers (useful for recovery from initialization errors)",
            handler=handle_reinitialize_managers,
            input_schema={
                "type": "object",
                "properties": {
                    "force": {"type": "boolean", "description": "Force reinitialization even if already initialized (default: true)"}
                },
                "required": []
            },
            category="connection",
            sort_order=3
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} connection handlers")
