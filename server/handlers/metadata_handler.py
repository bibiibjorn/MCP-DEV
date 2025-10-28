"""
Metadata Handler
Handles listing and searching tables, columns, measures
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition, get_registry
from server.middleware import paginate, apply_default_limits
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.infrastructure.limits_manager import get_limits
from core.validation.constants import QueryLimits
from core.infrastructure.query_executor import COLUMN_TYPE_CALCULATED

logger = logging.getLogger(__name__)

def handle_list_tables(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all tables in the model"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    result = qe.execute_info_query("TABLES")
    return paginate(result, args.get('page_size'), args.get('next_token'), ['rows'])

def handle_list_columns(args: Dict[str, Any]) -> Dict[str, Any]:
    """List columns, optionally filtered by table"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    table = args.get("table")
    limits = get_limits()

    # Apply default page size
    if 'page_size' not in args or args['page_size'] is None:
        args['page_size'] = limits.query.default_page_size

    result = qe.execute_info_query("COLUMNS", table_name=table)
    return paginate(result, args.get('page_size'), args.get('next_token'), ['rows'])

def handle_list_measures(args: Dict[str, Any]) -> Dict[str, Any]:
    """List measures, optionally filtered by table"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    table = args.get("table")
    limits = get_limits()

    # Apply default page size
    if 'page_size' not in args or args['page_size'] is None:
        args['page_size'] = limits.query.default_page_size

    result = qe.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
    return paginate(result, args.get('page_size'), args.get('next_token'), ['rows'])

def handle_describe_table(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get comprehensive table description with columns, measures, relationships"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    limits = get_limits()

    # Apply default pagination limits
    defaults = {
        'columns_page_size': limits.token.describe_table_columns_page_size,
        'measures_page_size': limits.token.describe_table_measures_page_size,
        'relationships_page_size': limits.token.describe_table_relationships_page_size
    }
    args = apply_default_limits(args, defaults)

    table = args.get("table")
    if not table:
        return {'success': False, 'error': 'table parameter required'}

    # Check if method exists
    if not hasattr(qe, 'describe_table'):
        return {
            'success': False,
            'error': 'describe_table method not implemented in query executor',
            'error_type': 'not_implemented',
            'suggestion': 'This tool requires legacy implementation'
        }

    try:
        return qe.describe_table(table, args)
    except AttributeError as e:
        logger.error(f"AttributeError in describe_table: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Method error: {str(e)}',
            'error_type': 'method_not_found',
            'suggestion': 'This tool may need to be bridged to legacy implementation'
        }
    except Exception as e:
        logger.error(f"Error in describe_table: {e}", exc_info=True)
        return ErrorHandler.handle_unexpected_error('describe_table', e)

def handle_get_measure_details(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed measure information including DAX formula"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    table = args.get("table")
    measure = args.get("measure")

    if not table or not measure:
        return {'success': False, 'error': 'table and measure parameters required'}

    return qe.get_measure_details_with_fallback(table, measure)

def handle_search_string(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search in measure names and/or expressions"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    limits = get_limits()

    # Apply default page size
    if 'page_size' not in args or args['page_size'] is None:
        args['page_size'] = limits.query.default_page_size

    search_text = args.get('search_text', '')
    search_in_expression = args.get('search_in_expression', True)
    search_in_name = args.get('search_in_name', True)

    result = qe.search_measures_dax(search_text, search_in_expression, search_in_name)
    return paginate(result, args.get('page_size'), args.get('next_token'), ['rows'])

def handle_list_calculated_columns(args: Dict[str, Any]) -> Dict[str, Any]:
    """List calculated columns"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    limits = get_limits()
    table = args.get("table")

    # Apply default page size
    if 'page_size' not in args or args['page_size'] is None:
        args['page_size'] = limits.query.default_page_size

    filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
    result = qe.execute_info_query("COLUMNS", filter_expr=filter_expr, table_name=table)
    return paginate(result, args.get('page_size'), args.get('next_token'), ['rows'])

def handle_search_objects(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search across tables, columns, and measures"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    pattern = args.get("pattern", "*")
    types = args.get("types", ["tables", "columns", "measures"])

    result = qe.search_objects_dax(pattern, types)
    return paginate(result, args.get('page_size'), args.get('next_token'), ['rows', 'items'])

def register_metadata_handlers(registry):
    """Register all metadata-related handlers"""
    tools = [
        ToolDefinition(
            name="list_tables",
            description="List all tables in the model",
            handler=handle_list_tables,
            input_schema={
                "type": "object",
                "properties": {
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"}
                },
                "required": []
            },
            category="metadata",
            sort_order=2
        ),
        ToolDefinition(
            name="describe_table",
            description="Get comprehensive table description with columns, measures, relationships",
            handler=handle_describe_table,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "columns_page_size": {"type": "integer"},
                    "measures_page_size": {"type": "integer"},
                    "relationships_page_size": {"type": "integer"}
                },
                "required": ["table"]
            },
            category="metadata",
            sort_order=3
        ),
        ToolDefinition(
            name="list_columns",
            description="List columns, optionally filtered by table",
            handler=handle_list_columns,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"}
                },
                "required": []
            },
            category="metadata",
            sort_order=4
        ),
        ToolDefinition(
            name="list_measures",
            description="List measures, optionally filtered by table",
            handler=handle_list_measures,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"}
                },
                "required": []
            },
            category="metadata",
            sort_order=5
        ),
        ToolDefinition(
            name="get_measure_details",
            description="Get detailed measure information including DAX formula",
            handler=handle_get_measure_details,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "measure": {"type": "string"}
                },
                "required": ["table", "measure"]
            },
            category="metadata",
            sort_order=6
        ),
        ToolDefinition(
            name="list_calculated_columns",
            description="List calculated columns",
            handler=handle_list_calculated_columns,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string"},
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"}
                },
                "required": []
            },
            category="metadata",
            sort_order=7
        ),
        ToolDefinition(
            name="search_objects",
            description="Search across tables, columns, and measures",
            handler=handle_search_objects,
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["tables", "columns", "measures"]}
                    },
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"}
                },
                "required": []
            },
            category="metadata",
            sort_order=8
        ),
        ToolDefinition(
            name="search_string",
            description="Search in measure names and/or expressions",
            handler=handle_search_string,
            input_schema={
                "type": "object",
                "properties": {
                    "search_text": {"type": "string"},
                    "search_in_expression": {"type": "boolean"},
                    "search_in_name": {"type": "boolean"},
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"}
                },
                "required": ["search_text"]
            },
            category="metadata",
            sort_order=9
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} metadata handlers")
