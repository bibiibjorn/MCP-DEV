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
            connection_state.initialize_managers()

            # PERFORMANCE: Pre-warm table mapping cache to eliminate first-request latency
            try:
                qe = connection_state.query_executor
                if qe and hasattr(qe, '_ensure_table_mappings'):
                    logger.info("Pre-warming table mapping cache...")
                    qe._ensure_table_mappings()
                    logger.info("Table mapping cache pre-warmed successfully")
            except Exception as cache_error:
                logger.warning(f"Failed to pre-warm cache (non-critical): {cache_error}")
                # Don't fail connection if cache pre-warming fails

        return result

    except Exception as e:
        logger.error(f"Error connecting: {e}", exc_info=True)
        return ErrorHandler.handle_unexpected_error('connect_to_powerbi', e)

def register_connection_handlers(registry):
    """Register connection handlers"""
    tools = [
        ToolDefinition(
            name="detect_powerbi_desktop",
            description="Detect running Power BI Desktop instances",
            handler=handle_detect_powerbi_desktop,
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
                "examples": [
                    {
                        "_description": "Detect all running Power BI Desktop instances"
                    }
                ]
            },
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
                "required": [],
                "examples": [
                    {
                        "_description": "Connect to first detected instance (default)"
                    },
                    {
                        "_description": "Connect to specific instance by index",
                        "model_index": 1
                    }
                ]
            },
            category="connection",
            sort_order=1
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} connection handlers")
