"""
Query Handler
Handles DAX query execution, validation, and data preview
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.infrastructure.limits_manager import get_limits

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

    return agent_policy.safe_run_dax(
        connection_state=connection_state,
        query=query,
        mode=mode,
        max_rows=top_n
    )

def handle_preview_table_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """Preview table rows with EVALUATE"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    table = args.get('table')
    if not table:
        return {'success': False, 'error': 'table parameter required'}

    max_rows = args.get('max_rows', 10)

    # Create EVALUATE query for table preview
    query = f'EVALUATE TOPN({max_rows}, \'{table}\')'

    return agent_policy.safe_run_dax(
        connection_state=connection_state,
        query=query,
        mode='auto',
        max_rows=max_rows
    )

def handle_get_column_value_distribution(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get column value distribution (top N)"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    table = args.get('table')
    column = args.get('column')

    if not table or not column:
        return {'success': False, 'error': 'table and column parameters required'}

    top_n = args.get('top_n', 10)

    # Create DAX query to get value distribution
    query = f'''
    EVALUATE
    TOPN(
        {top_n},
        SUMMARIZECOLUMNS(
            '{table}'[{column}],
            "Count", COUNTROWS('{table}')
        ),
        [Count],
        DESC
    )
    '''

    return agent_policy.safe_run_dax(
        connection_state=connection_state,
        query=query,
        mode='auto',
        max_rows=top_n
    )

def handle_get_column_summary(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get column summary statistics"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    table = args.get('table')
    column = args.get('column')

    if not table or not column:
        return {'success': False, 'error': 'table and column parameters required'}

    # Create DAX query to get column statistics
    query = f'''
    EVALUATE
    ROW(
        "DistinctCount", COUNTROWS(DISTINCT('{table}'[{column}])),
        "TotalCount", COUNTROWS('{table}'),
        "BlankCount", COUNTBLANK('{table}'[{column}])
    )
    '''

    return agent_policy.safe_run_dax(
        connection_state=connection_state,
        query=query,
        mode='auto'
    )

def handle_validate_dax_query(args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate DAX syntax"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    query = args.get('query')
    if not query:
        return {'success': False, 'error': 'query parameter required'}

    try:
        # Try to execute query with LIMIT 0 to validate syntax
        test_query = f'{query}'
        if 'EVALUATE' not in test_query.upper():
            test_query = f'EVALUATE {test_query}'

        # Use query executor to validate - use validate_and_execute_dax method
        result = qe.validate_and_execute_dax(test_query, top_n=0)

        if result.get('success'):
            return {
                'success': True,
                'valid': True,
                'message': 'DAX query is valid'
            }
        else:
            return {
                'success': True,
                'valid': False,
                'error': result.get('error', 'Unknown validation error')
            }
    except Exception as e:
        return {
            'success': True,
            'valid': False,
            'error': str(e)
        }

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

def handle_list_relationships(args: Dict[str, Any]) -> Dict[str, Any]:
    """List relationships with optional active_only filter"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    active_only = args.get('active_only', False)

    # Use INFO query to get relationships
    result = qe.execute_info_query("RELATIONSHIPS")

    if result.get('success') and active_only:
        rows = result.get('rows', [])
        # Filter for active relationships only
        active_rows = [r for r in rows if r.get('IsActive') or r.get('[IsActive]')]
        result['rows'] = active_rows

    return result

def register_query_handlers(registry):
    """Register all query execution handlers"""
    tools = [
        ToolDefinition(
            name="preview_table_data",
            description="Preview table rows with EVALUATE",
            handler=handle_preview_table_data,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name to preview"
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": "Maximum rows to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["table"]
            },
            category="query",
            sort_order=20
        ),
        ToolDefinition(
            name="run_dax",
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
                        "description": "Execution mode: 'auto' (smart choice), 'analyze' or 'profile' (with SE/FE timing), 'simple' (preview only)",
                        "enum": ["auto", "analyze", "profile", "simple"],
                        "default": "auto"
                    }
                },
                "required": ["query"]
            },
            category="query",
            sort_order=21
        ),
        ToolDefinition(
            name="validate_dax_query",
            description="Validate DAX syntax",
            handler=handle_validate_dax_query,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "DAX query to validate"
                    }
                },
                "required": ["query"]
            },
            category="query",
            sort_order=22
        ),
        ToolDefinition(
            name="get_column_value_distribution",
            description="Get column value distribution (top N)",
            handler=handle_get_column_value_distribution,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    },
                    "column": {
                        "type": "string",
                        "description": "Column name"
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top values (default: 10)",
                        "default": 10
                    }
                },
                "required": ["table", "column"]
            },
            category="query",
            sort_order=23
        ),
        ToolDefinition(
            name="get_column_summary",
            description="Get column summary statistics",
            handler=handle_get_column_summary,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    },
                    "column": {
                        "type": "string",
                        "description": "Column name"
                    }
                },
                "required": ["table", "column"]
            },
            category="query",
            sort_order=24
        ),
        ToolDefinition(
            name="list_relationships",
            description="List relationships with optional active_only filter",
            handler=handle_list_relationships,
            input_schema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active relationships (default: false)",
                        "default": False
                    }
                },
                "required": []
            },
            category="query",
            sort_order=25
        ),
        ToolDefinition(
            name="get_data_sources",
            description="List data sources with fallback to TOM",
            handler=handle_get_data_sources,
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            category="query",
            sort_order=26
        ),
        ToolDefinition(
            name="get_m_expressions",
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
            sort_order=27
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} query handlers")
