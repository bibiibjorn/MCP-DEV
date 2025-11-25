"""
Pagination helpers for consistent pagination handling across operations.

These helpers consolidate duplicate pagination logic patterns.
Reduces ~80 lines of duplicated code.
"""
from typing import Any, Dict, List, Optional


def apply_default_page_size(args: Dict[str, Any], default_size: Optional[int] = None) -> Dict[str, Any]:
    """
    Apply default page size if not specified in args.

    Args:
        args: The arguments dictionary (modified in place)
        default_size: Override default size. If None, uses limits_manager default.

    Returns:
        The args dict with page_size set if it was missing

    Usage:
        args = apply_default_page_size(args)
        # or with explicit default
        args = apply_default_page_size(args, default_size=50)
    """
    if 'page_size' not in args or args['page_size'] is None:
        if default_size is not None:
            args['page_size'] = default_size
        else:
            from core.infrastructure.limits_manager import get_limits
            limits = get_limits()
            args['page_size'] = limits.query.default_page_size
    return args


def apply_pagination(result: Dict[str, Any], args: Dict[str, Any], rows_key: str = 'rows') -> Dict[str, Any]:
    """
    Apply pagination to a result dictionary.

    Args:
        result: The result dictionary containing data to paginate
        args: The arguments dictionary containing page_size and next_token
        rows_key: The key in result that contains the list to paginate

    Returns:
        The result with pagination applied

    Usage:
        result = qe.execute_info_query("MEASURES")
        result = apply_pagination(result, args)
    """
    page_size = args.get('page_size')
    next_token = args.get('next_token')

    if page_size or next_token:
        from server.middleware import paginate
        result = paginate(result, page_size, next_token, [rows_key])

    return result


def apply_pagination_with_defaults(
    result: Dict[str, Any],
    args: Dict[str, Any],
    rows_key: str = 'rows',
    default_page_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Apply default page size and pagination in one call.

    This is the most common pattern - combines apply_default_page_size and apply_pagination.

    Args:
        result: The result dictionary containing data to paginate
        args: The arguments dictionary (page_size will be set if missing)
        rows_key: The key in result that contains the list to paginate
        default_page_size: Override default size. If None, uses limits_manager default.

    Returns:
        The result with pagination applied

    Usage:
        result = qe.execute_info_query("MEASURES")
        result = apply_pagination_with_defaults(result, args)
    """
    # Apply default page size
    apply_default_page_size(args, default_page_size)

    # Apply pagination
    return apply_pagination(result, args, rows_key)


def apply_describe_table_defaults(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply default pagination limits for describe_table operation.

    This sets column, measure, and relationship page sizes based on token limits.

    Args:
        args: The arguments dictionary (modified in place)

    Returns:
        The args dict with describe table defaults applied

    Usage:
        args = apply_describe_table_defaults(args)
        result = qe.describe_table(table_name, args)
    """
    from core.infrastructure.limits_manager import get_limits
    from server.middleware import apply_default_limits

    limits = get_limits()
    defaults = {
        'columns_page_size': limits.token.describe_table_columns_page_size,
        'measures_page_size': limits.token.describe_table_measures_page_size,
        'relationships_page_size': limits.token.describe_table_relationships_page_size
    }
    return apply_default_limits(args, defaults)


def get_page_size_with_default(args: Dict[str, Any], default: Optional[int] = None) -> int:
    """
    Get page size from args, using default if not specified.

    Args:
        args: The arguments dictionary
        default: Default page size. If None, uses limits_manager default.

    Returns:
        Page size value

    Usage:
        page_size = get_page_size_with_default(args)
    """
    page_size = args.get('page_size')
    if page_size is not None:
        return page_size

    if default is not None:
        return default

    from core.infrastructure.limits_manager import get_limits
    limits = get_limits()
    return limits.query.default_page_size


def paginate_list(
    items: List[Any],
    page_size: Optional[int] = None,
    next_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Paginate a list directly (not wrapped in a result dict).

    Args:
        items: The list to paginate
        page_size: Number of items per page
        next_token: Continuation token (format: "offset_number")

    Returns:
        Dict with 'items', 'total_count', 'has_more', and optionally 'next_token'

    Usage:
        result = paginate_list(all_items, page_size=50, next_token="100")
    """
    total = len(items)

    # Parse offset from token
    offset = 0
    if next_token:
        try:
            offset = int(next_token)
        except ValueError:
            offset = 0

    # Apply pagination
    if page_size is not None and page_size > 0:
        end = offset + page_size
        page_items = items[offset:end]
        has_more = end < total
        new_token = str(end) if has_more else None
    else:
        page_items = items
        has_more = False
        new_token = None

    result = {
        'items': page_items,
        'total_count': total,
        'has_more': has_more
    }

    if new_token:
        result['next_token'] = new_token

    return result


def wrap_with_pagination_metadata(
    result: Dict[str, Any],
    args: Dict[str, Any],
    rows_key: str = 'rows'
) -> Dict[str, Any]:
    """
    Add pagination metadata to result without modifying data.

    Useful when pagination was already applied but metadata needs to be added.

    Args:
        result: The result dictionary
        args: The arguments dictionary with pagination params
        rows_key: The key containing the paginated data

    Returns:
        Result with pagination metadata added

    Usage:
        result = wrap_with_pagination_metadata(result, args)
    """
    if not result.get('success'):
        return result

    items = result.get(rows_key, [])
    page_size = args.get('page_size')
    next_token = args.get('next_token')

    result['pagination'] = {
        'page_size': page_size,
        'current_count': len(items),
        'has_more': result.get('has_more', False)
    }

    if next_token:
        result['pagination']['continued_from'] = next_token

    return result
