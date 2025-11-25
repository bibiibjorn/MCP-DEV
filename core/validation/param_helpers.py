"""
Parameter extraction helpers for backward compatibility.

These helpers consolidate duplicate parameter aliasing patterns across operations.
Reduces ~50 lines of duplicated code.
"""
from typing import Any, Dict, List, Optional, Tuple


def get_table_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract table name from args with backward compatibility.

    Supports: 'table_name', 'table'

    Usage:
        table_name = get_table_name(args)
        if not table_name:
            return validation_error(...)
    """
    return args.get('table_name') or args.get('table')


def get_measure_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract measure name from args with backward compatibility.

    Supports: 'measure_name', 'measure'
    """
    return args.get('measure_name') or args.get('measure')


def get_column_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract column name from args with backward compatibility.

    Supports: 'column_name', 'column'
    """
    return args.get('column_name') or args.get('column')


def get_relationship_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract relationship name from args with backward compatibility.

    Supports: 'relationship_name', 'name'
    """
    return args.get('relationship_name') or args.get('name')


def get_group_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract calculation group name from args with backward compatibility.

    Supports: 'group_name', 'name'
    """
    return args.get('group_name') or args.get('name')


def get_role_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract role name from args with backward compatibility.

    Supports: 'role_name', 'name'
    """
    return args.get('role_name') or args.get('name')


def get_format_string(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract format string from args with backward compatibility.

    Supports: 'format_string', 'format'
    """
    return args.get('format_string') or args.get('format')


def get_source_table(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract source table for move operations with backward compatibility.

    Supports: 'source_table', 'table_name', 'table'
    """
    return args.get('source_table') or args.get('table_name') or args.get('table')


def get_target_table(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract target table for move operations with backward compatibility.

    Supports: 'target_table', 'new_table'
    """
    return args.get('target_table') or args.get('new_table')


def get_new_name(args: Dict[str, Any]) -> Optional[str]:
    """
    Extract new name for rename operations.

    Supports: 'new_name'
    """
    return args.get('new_name')


def extract_params(args: Dict[str, Any], *param_specs: Tuple[str, ...]) -> Tuple:
    """
    Extract multiple parameters with backward compatibility aliases.

    Args:
        args: The arguments dictionary
        *param_specs: Variable number of tuples, each containing alternative keys for one parameter
            First key in tuple is the primary name, rest are aliases

    Returns:
        Tuple of extracted values in the same order as param_specs

    Usage:
        table, measure = extract_params(args,
            ('table_name', 'table'),       # Returns args['table_name'] or args['table']
            ('measure_name', 'measure')    # Returns args['measure_name'] or args['measure']
        )

        # With three alternatives
        source = extract_params(args,
            ('source_table', 'table_name', 'table')
        )[0]
    """
    results = []
    for aliases in param_specs:
        value = None
        for key in aliases:
            value = args.get(key)
            if value is not None:
                break
        results.append(value)
    return tuple(results)


def extract_table_and_name(args: Dict[str, Any], name_key: str, name_aliases: List[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Common pattern: extract table name and another name (measure, column, etc.)

    Args:
        args: The arguments dictionary
        name_key: Primary key for the name parameter
        name_aliases: Alternative keys for the name parameter

    Returns:
        (table_name, item_name) tuple

    Usage:
        table, measure = extract_table_and_name(args, 'measure_name', ['measure'])
        table, column = extract_table_and_name(args, 'column_name', ['column'])
    """
    table_name = get_table_name(args)

    aliases = [name_key] + (name_aliases or [])
    item_name = None
    for key in aliases:
        item_name = args.get(key)
        if item_name is not None:
            break

    return (table_name, item_name)


def extract_crud_params(args: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """
    Extract common CRUD operation parameters.

    Args:
        args: The arguments dictionary
        entity_type: One of 'measure', 'column', 'table', 'relationship'

    Returns:
        Dictionary with normalized parameter names

    Usage:
        params = extract_crud_params(args, 'measure')
        # Returns: {'table_name': ..., 'name': ..., 'new_name': ..., 'expression': ...}
    """
    result = {
        'new_name': get_new_name(args),
        'expression': args.get('expression'),
        'description': args.get('description'),
        'hidden': args.get('hidden'),
        'display_folder': args.get('display_folder'),
        'format_string': get_format_string(args),
    }

    if entity_type == 'measure':
        result['table_name'] = get_table_name(args)
        result['name'] = get_measure_name(args)
    elif entity_type == 'column':
        result['table_name'] = get_table_name(args)
        result['name'] = get_column_name(args)
        result['data_type'] = args.get('data_type', 'String')
        result['source_column'] = args.get('source_column')
    elif entity_type == 'table':
        result['name'] = get_table_name(args)
    elif entity_type == 'relationship':
        result['name'] = get_relationship_name(args)
        result['from_table'] = args.get('from_table')
        result['from_column'] = args.get('from_column')
        result['to_table'] = args.get('to_table')
        result['to_column'] = args.get('to_column')
        result['is_active'] = args.get('is_active')
        result['cross_filtering_behavior'] = args.get('cross_filtering_behavior')
        result['from_cardinality'] = args.get('from_cardinality', 'Many')
        result['to_cardinality'] = args.get('to_cardinality', 'One')
    elif entity_type == 'calculation_group':
        result['name'] = get_group_name(args)
        result['items'] = args.get('items', [])
        result['precedence'] = args.get('precedence')

    return result


def get_pagination_params(args: Dict[str, Any]) -> Tuple[Optional[int], Optional[str]]:
    """
    Extract pagination parameters.

    Returns:
        (page_size, next_token) tuple
    """
    return (args.get('page_size'), args.get('next_token'))


def get_optional_int(args: Dict[str, Any], key: str, default: int) -> int:
    """
    Get an optional integer parameter with default.

    Args:
        args: The arguments dictionary
        key: Parameter key
        default: Default value if not present

    Returns:
        Integer value or default
    """
    value = args.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_optional_bool(args: Dict[str, Any], key: str, default: bool) -> bool:
    """
    Get an optional boolean parameter with default.

    Args:
        args: The arguments dictionary
        key: Parameter key
        default: Default value if not present

    Returns:
        Boolean value or default
    """
    value = args.get(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return bool(value)
