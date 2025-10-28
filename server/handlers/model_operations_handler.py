"""
Model Operations Handler
Handles measure creation, deletion, and other model modification operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_upsert_measure(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a measure"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    dax_injector = connection_state.dax_injector
    if not dax_injector:
        return ErrorHandler.handle_manager_unavailable('dax_injector')

    table = args.get('table')
    measure = args.get('measure')
    expression = args.get('expression')

    if not table or not measure or not expression:
        return {
            'success': False,
            'error': 'table, measure, and expression parameters are required'
        }

    description = args.get('description')
    format_string = args.get('format')
    display_folder = args.get('display_folder')

    return dax_injector.upsert_measure(
        table_name=table,
        measure_name=measure,
        dax_expression=expression,
        description=description,
        format_string=format_string,
        display_folder=display_folder
    )

def handle_delete_measure(args: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a measure"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    dax_injector = connection_state.dax_injector
    if not dax_injector:
        return ErrorHandler.handle_manager_unavailable('dax_injector')

    table = args.get('table')
    measure = args.get('measure')

    if not table or not measure:
        return {
            'success': False,
            'error': 'table and measure parameters are required'
        }

    return dax_injector.delete_measure(
        table_name=table,
        measure_name=measure
    )

def handle_bulk_create_measures(args: Dict[str, Any]) -> Dict[str, Any]:
    """Bulk create multiple measures"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    bulk_ops = connection_state.bulk_operations
    if not bulk_ops:
        return ErrorHandler.handle_manager_unavailable('bulk_operations')

    measures = args.get('measures', [])
    if not measures:
        return {
            'success': False,
            'error': 'measures parameter required (array of measure definitions)'
        }

    return bulk_ops.bulk_create_measures(measures)

def handle_bulk_delete_measures(args: Dict[str, Any]) -> Dict[str, Any]:
    """Bulk delete multiple measures"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    bulk_ops = connection_state.bulk_operations
    if not bulk_ops:
        return ErrorHandler.handle_manager_unavailable('bulk_operations')

    measures = args.get('measures', [])
    if not measures:
        return {
            'success': False,
            'error': 'measures parameter required (array of {table, measure} objects)'
        }

    return bulk_ops.bulk_delete_measures(measures)

def handle_list_calculation_groups(args: Dict[str, Any]) -> Dict[str, Any]:
    """List calculation groups"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    calc_group_mgr = connection_state.calc_group_manager
    if not calc_group_mgr:
        return ErrorHandler.handle_manager_unavailable('calc_group_manager')

    return calc_group_mgr.list_calculation_groups()

def handle_create_calculation_group(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a calculation group"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    calc_group_mgr = connection_state.calc_group_manager
    if not calc_group_mgr:
        return ErrorHandler.handle_manager_unavailable('calc_group_manager')

    name = args.get('name')
    items = args.get('items', [])
    description = args.get('description')
    precedence = args.get('precedence')

    if not name:
        return {
            'success': False,
            'error': 'name parameter required'
        }

    # If no precedence specified, find next available precedence value
    if precedence is None:
        # Get existing calculation groups to find used precedence values
        existing_groups = calc_group_mgr.list_calculation_groups()
        if existing_groups.get('success'):
            used_precedences = set()
            for group in existing_groups.get('calculation_groups', []):
                used_precedences.add(group.get('precedence', 0))

            # Find first available precedence (starting from 0)
            precedence = 0
            while precedence in used_precedences:
                precedence += 1

            logger.info(f"Auto-assigned precedence {precedence} for calculation group '{name}'")
        else:
            # Fallback to 0 if we can't list existing groups
            precedence = 0
    else:
        # Validate that the specified precedence isn't already taken
        existing_groups = calc_group_mgr.list_calculation_groups()
        if existing_groups.get('success'):
            for group in existing_groups.get('calculation_groups', []):
                if group.get('precedence') == precedence:
                    used_precedences = [g.get('precedence', 0) for g in existing_groups.get('calculation_groups', [])]
                    available = [p for p in range(max(used_precedences) + 2) if p not in used_precedences]
                    return {
                        'success': False,
                        'error': f'Precedence {precedence} is already taken by calculation group "{group.get("name")}"',
                        'suggestion': f'Use one of these available precedence values: {available[:5]}'
                    }

    return calc_group_mgr.create_calculation_group(
        name=name,
        items=items,
        description=description,
        precedence=precedence
    )

def handle_delete_calculation_group(args: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a calculation group"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    calc_group_mgr = connection_state.calc_group_manager
    if not calc_group_mgr:
        return ErrorHandler.handle_manager_unavailable('calc_group_manager')

    name = args.get('name')
    if not name:
        return {
            'success': False,
            'error': 'name parameter required'
        }

    return calc_group_mgr.delete_calculation_group(name)

def handle_list_partitions(args: Dict[str, Any]) -> Dict[str, Any]:
    """List table partitions"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    partition_mgr = connection_state.partition_manager
    if not partition_mgr:
        return ErrorHandler.handle_manager_unavailable('partition_manager')

    table = args.get('table')
    return partition_mgr.list_table_partitions(table)

def handle_list_roles(args: Dict[str, Any]) -> Dict[str, Any]:
    """List RLS roles"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    rls_mgr = connection_state.rls_manager
    if not rls_mgr:
        return ErrorHandler.handle_manager_unavailable('rls_manager')

    return rls_mgr.list_roles()

def register_model_operations_handlers(registry):
    """Register all model operation handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="upsert_measure",
            description="Create or update a measure",
            handler=handle_upsert_measure,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name for the measure"},
                    "measure": {"type": "string", "description": "Measure name"},
                    "expression": {"type": "string", "description": "DAX expression for the measure"},
                    "description": {"type": "string", "description": "Optional description"},
                    "format": {"type": "string", "description": "Optional format string"},
                    "display_folder": {"type": "string", "description": "Optional display folder"}
                },
                "required": ["table", "measure", "expression"]
            },
            category="model_operations",
            sort_order=40
        ),
        ToolDefinition(
            name="delete_measure",
            description="Delete a measure",
            handler=handle_delete_measure,
            input_schema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"},
                    "measure": {"type": "string", "description": "Measure name to delete"}
                },
                "required": ["table", "measure"]
            },
            category="model_operations",
            sort_order=41
        ),
        ToolDefinition(
            name="bulk_create_measures",
            description="Bulk create multiple measures",
            handler=handle_bulk_create_measures,
            input_schema=TOOL_SCHEMAS.get('bulk_create_measures', {}),
            category="model_operations",
            sort_order=42
        ),
        ToolDefinition(
            name="bulk_delete_measures",
            description="Bulk delete multiple measures",
            handler=handle_bulk_delete_measures,
            input_schema=TOOL_SCHEMAS.get('bulk_delete_measures', {}),
            category="model_operations",
            sort_order=43
        ),
        ToolDefinition(
            name="list_calculation_groups",
            description="List calculation groups",
            handler=handle_list_calculation_groups,
            input_schema=TOOL_SCHEMAS.get('list_calculation_groups', {}),
            category="model_operations",
            sort_order=44
        ),
        ToolDefinition(
            name="create_calculation_group",
            description="Create a calculation group",
            handler=handle_create_calculation_group,
            input_schema=TOOL_SCHEMAS.get('create_calculation_group', {}),
            category="model_operations",
            sort_order=45
        ),
        ToolDefinition(
            name="delete_calculation_group",
            description="Delete a calculation group",
            handler=handle_delete_calculation_group,
            input_schema=TOOL_SCHEMAS.get('delete_calculation_group', {}),
            category="model_operations",
            sort_order=46
        ),
        ToolDefinition(
            name="list_partitions",
            description="List table partitions",
            handler=handle_list_partitions,
            input_schema=TOOL_SCHEMAS.get('list_partitions', {}),
            category="model_operations",
            sort_order=47
        ),
        ToolDefinition(
            name="list_roles",
            description="List RLS roles",
            handler=handle_list_roles,
            input_schema=TOOL_SCHEMAS.get('list_roles', {}),
            category="model_operations",
            sort_order=48
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} model operation handlers")
