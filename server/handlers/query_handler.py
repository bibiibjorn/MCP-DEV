"""
Query Handler
Handles DAX query execution, validation, and data preview
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_run_dax(args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute DAX query with auto limits"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    query = args.get('query')
    if not query:
        return {'success': False, 'error': 'query parameter required'}

    top_n = args.get('top_n', 100)
    mode = args.get('mode', 'auto')

    result = agent_policy.safe_run_dax(
        connection_state=connection_state,
        query=query,
        mode=mode,
        max_rows=top_n
    )

    return result

def handle_get_data_sources(args: Dict[str, Any]) -> Dict[str, Any]:
    """List data sources with fallback to TOM"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    # Use INFO query to get data sources
    result = qe.execute_info_query("DATASOURCES")
    return result

def handle_get_m_expressions(args: Dict[str, Any]) -> Dict[str, Any]:
    """List M/Power Query expressions"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    limit = args.get('limit')

    # Use INFO query to get partitions which contain M expressions
    result = qe.execute_info_query("PARTITIONS")

    if result.get('success') and limit:
        rows = result.get('rows', [])
        result['rows'] = rows[:limit]

    return result

def register_query_handlers(registry):
    """Register all query execution handlers"""
    tools = [
        ToolDefinition(
            name="04_Run_DAX",
            description="Execute DAX query with auto limits",
            handler=handle_run_dax,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "DAX query to execute (EVALUATE statement)"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Limit number of rows returned (default: 100)",
                        "default": 100
                    },
                    "mode": {
                        "type": "string",
                        "description": "Execution mode: 'auto' (smart choice), 'analyze' or 'profile' (with timing analysis), 'simple' (preview only)",
                        "enum": ["auto", "analyze", "profile", "simple"],
                        "default": "auto"
                    }
                },
                "required": ["query"]
            },
            category="query",
            sort_order=40  # 04 = Query & Search
        ),
        ToolDefinition(
            name="04_Get_Data_Sources",
            description="List data sources with fallback to TOM",
            handler=handle_get_data_sources,
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            category="query",
            sort_order=41  # 04 = Query & Search
        ),
        ToolDefinition(
            name="04_Get_M_Expressions",
            description="List M/Power Query expressions",
            handler=handle_get_m_expressions,
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max expressions to return"
                    }
                },
                "required": []
            },
            category="query",
            sort_order=42  # 04 = Query & Search
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} query handlers")
