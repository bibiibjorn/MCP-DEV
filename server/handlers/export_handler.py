"""
Export Handler
Handles TMSL, TMDL, and schema export operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_export_tmsl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export TMSL definition"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    file_path = args.get('file_path')

    return model_exporter.export_tmsl(file_path)

def handle_export_tmdl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export TMDL definition"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    output_dir = args.get('output_dir')

    return model_exporter.export_tmdl(output_dir)

def handle_export_model_schema(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export model schema by section"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    section = args.get('section', 'all')
    output_path = args.get('output_path')

    return model_exporter.export_schema(section, output_path)

def register_export_handlers(registry):
    """Register all export handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="export_model_schema",
            description="Export model schema by section",
            handler=handle_export_model_schema,
            input_schema=TOOL_SCHEMAS.get('export_model_schema', {}),
            category="export",
            sort_order=34
        ),
        ToolDefinition(
            name="export_tmsl",
            description="Export TMSL definition",
            handler=handle_export_tmsl,
            input_schema=TOOL_SCHEMAS.get('export_tmsl', {}),
            category="export",
            sort_order=35
        ),
        ToolDefinition(
            name="export_tmdl",
            description="Export TMDL definition",
            handler=handle_export_tmdl,
            input_schema=TOOL_SCHEMAS.get('export_tmdl', {}),
            category="export",
            sort_order=36
        ),
    relationships, calculation groups, and RLS. Use preview_table_data and run_dax tools to fetch actual data and DAX expressions on demand.",
            handler=handle_analyze_model_for_ai,
            input_schema=TOOL_SCHEMAS.get('analyze_model_for_ai', {}),
            category="export",
            sort_order=33
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} export handlers")
