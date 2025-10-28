"""
Dependencies Handler
Handles measure dependency analysis
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_analyze_measure_dependencies(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze measure dependencies tree"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    dependency_analyzer = connection_state.dependency_analyzer
    if not dependency_analyzer:
        return ErrorHandler.handle_manager_unavailable('dependency_analyzer')

    table = args.get('table')
    measure = args.get('measure')

    if not table or not measure:
        return {
            'success': False,
            'error': 'table and measure parameters are required'
        }

    return dependency_analyzer.analyze_dependencies(table, measure)

def handle_get_measure_impact(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get measure usage impact"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    dependency_analyzer = connection_state.dependency_analyzer
    if not dependency_analyzer:
        return ErrorHandler.handle_manager_unavailable('dependency_analyzer')

    table = args.get('table')
    measure = args.get('measure')

    if not table or not measure:
        return {
            'success': False,
            'error': 'table and measure parameters are required'
        }

    return dependency_analyzer.get_measure_impact(table, measure)

def register_dependencies_handlers(registry):
    """Register all dependency analysis handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="analyze_measure_dependencies",
            description="Analyze measure dependencies tree",
            handler=handle_analyze_measure_dependencies,
            input_schema=TOOL_SCHEMAS.get('analyze_measure_dependencies', {}),
            category="dependencies",
            sort_order=32
        ),
        ToolDefinition(
            name="get_measure_impact",
            description="Get measure usage impact",
            handler=handle_get_measure_impact,
            input_schema=TOOL_SCHEMAS.get('get_measure_impact', {}),
            category="dependencies",
            sort_order=33
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} dependency handlers")
