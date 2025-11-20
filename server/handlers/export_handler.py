"""
Export Handler
Handles TMDL and schema export operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_get_live_model_schema(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get live model schema (inline, without DAX expressions)"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    include_hidden = args.get('include_hidden', True)

    return model_exporter.export_compact_schema(include_hidden=include_hidden)

def register_export_handlers(registry):
    """Register all export handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tool = ToolDefinition(
        name="get_live_model_schema",
        description="Get live model schema (inline, lightweight, without DAX expressions)",
        handler=handle_get_live_model_schema,
        input_schema=TOOL_SCHEMAS.get('get_live_model_schema', {}),
        category="export",
        sort_order=60
    )

    registry.register(tool)
    logger.info("Registered get_live_model_schema handler")
