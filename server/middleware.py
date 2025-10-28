"""
Server Middleware Utilities
Pagination, truncation, formatting helpers
"""
from typing import Any, Dict, List, Optional, Tuple
import json

def paginate(result: Any, page_size: Optional[int], next_token: Optional[str], list_keys: List[str]) -> Any:
    """
    Paginate result arrays with continuation tokens

    Args:
        result: Result dict containing arrays to paginate
        page_size: Items per page (must be between 1 and 10000)
        next_token: Continuation token
        list_keys: Keys in result dict that contain lists to paginate

    Returns:
        Result with paginated data and next_token if more data available
    """
    if not isinstance(result, dict) or not result.get('success'):
        return result

    if page_size is None or page_size <= 0:
        return result

    # Validate page_size bounds
    MAX_PAGE_SIZE = 10000
    if page_size > MAX_PAGE_SIZE:
        return {
            'success': False,
            'error': f'page_size exceeds maximum allowed value of {MAX_PAGE_SIZE}',
            'error_type': 'ValidationError'
        }

    # Parse token (format: "key:offset")
    start_offset = 0
    target_key = None
    if next_token:
        try:
            parts = next_token.split(':', 1)
            if len(parts) == 2:
                target_key, offset_str = parts
                start_offset = int(offset_str)
                # Validate offset is non-negative and reasonable
                if start_offset < 0 or start_offset > 1000000:
                    return {
                        'success': False,
                        'error': 'Invalid next_token: offset out of valid range',
                        'error_type': 'ValidationError'
                    }
        except (ValueError, AttributeError) as e:
            return {
                'success': False,
                'error': f'Invalid next_token format: {str(e)}',
                'error_type': 'ValidationError'
            }

    # Apply pagination to each list key
    new_token = None
    for key in list_keys:
        if key not in result:
            continue

        arr = result.get(key, [])
        if not isinstance(arr, list):
            continue

        # Skip if this isn't the target key (when continuing pagination)
        if target_key and key != target_key:
            continue

        # Paginate
        paginated, token = paginate_section(arr, page_size, start_offset)
        result[key] = paginated

        if token is not None:
            new_token = f"{key}:{token}"
            break

    # Add pagination metadata
    if new_token:
        result['next_token'] = new_token
        result['has_more'] = True
    else:
        result.pop('next_token', None)
        result['has_more'] = False

    return result

def paginate_section(arr: Any, size: Optional[Any], offset: int = 0) -> Tuple[list, Optional[str]]:
    """
    Paginate a single array section

    Returns:
        (paginated_array, next_offset_or_none)
    """
    if not isinstance(arr, list):
        return arr, None

    if size is None or size <= 0:
        return arr, None

    try:
        size = int(size)
        offset = int(offset)
    except (ValueError, TypeError):
        return arr, None

    end = offset + size
    paginated = arr[offset:end]

    next_token = str(end) if end < len(arr) else None
    return paginated, next_token

def schema_sample(rows: List[dict], sample_size: int) -> dict:
    """
    Sample a subset of rows with count metadata

    Args:
        rows: List of row dictionaries
        sample_size: Max rows to include

    Returns:
        Dict with 'sample' and 'total_count'
    """
    if not isinstance(rows, list):
        return {'sample': [], 'total_count': 0}

    total = len(rows)
    sample = rows[:sample_size] if sample_size > 0 else []

    return {
        'sample': sample,
        'total_count': total,
        'is_sample': total > sample_size
    }

def truncate_if_needed(result: dict, max_tokens: int = 15000) -> dict:
    """
    Truncate large results to prevent token overflow

    Args:
        result: Result dictionary
        max_tokens: Approximate max tokens (rough estimate: 4 chars = 1 token)

    Returns:
        Possibly truncated result with metadata
    """
    if not isinstance(result, dict):
        return result

    try:
        # Rough token estimation
        json_str = json.dumps(result)
        estimated_tokens = len(json_str) // 4

        if estimated_tokens <= max_tokens:
            return result

        # Need to truncate - try to preserve important data
        truncated = dict(result)
        truncated['_truncated'] = True
        truncated['_original_size_estimate'] = estimated_tokens

        # Truncate arrays
        for key in ['rows', 'measures', 'columns', 'tables', 'relationships']:
            if key in truncated and isinstance(truncated[key], list):
                original_len = len(truncated[key])
                # Keep first 100 items
                truncated[key] = truncated[key][:100]
                truncated[f'_{key}_truncated_from'] = original_len

        # Truncate long strings
        for key, value in list(truncated.items()):
            if isinstance(value, str) and len(value) > 5000:
                truncated[key] = value[:5000] + "... [truncated]"

        return truncated

    except Exception:
        return result

def truncate_expression(expression: str, max_length: int = 500) -> str:
    """
    Truncate long expressions with ellipsis

    Args:
        expression: DAX or M expression
        max_length: Maximum length

    Returns:
        Truncated expression
    """
    if not isinstance(expression, str):
        return str(expression)

    if len(expression) <= max_length:
        return expression

    return expression[:max_length] + "... [truncated]"

def apply_default_limits(arguments: dict, defaults: dict) -> dict:
    """
    Apply default values to missing arguments

    Args:
        arguments: Tool arguments
        defaults: Default values dict

    Returns:
        Arguments with defaults applied
    """
    args = dict(arguments)
    for key, default_value in defaults.items():
        if key not in args or args[key] is None:
            args[key] = default_value
    return args

def add_note(result: Any, note: str) -> Any:
    """Add a note to result metadata"""
    if not isinstance(result, dict):
        return result

    if 'notes' not in result:
        result['notes'] = []
    elif not isinstance(result['notes'], list):
        result['notes'] = [result['notes']]

    result['notes'].append(note)
    return result

def note_truncated(result: Any, limit: int) -> Any:
    """Add truncation note"""
    return add_note(result, f"Results truncated to {limit} items for performance")

def note_tom_fallback(result: Any) -> Any:
    """Add TOM fallback note"""
    return add_note(result, "Retrieved via TOM/AMO fallback (DMV query blocked)")

def note_client_filter(result: Any, table: str) -> Any:
    """Add client-side filter note"""
    return add_note(result, f"Server filter failed; applied client-side filter for table '{table}'")

def dax_quote_table(name: str) -> str:
    """Quote table name for DAX"""
    return f"'{name.replace(chr(39), chr(39) + chr(39))}'"

def dax_quote_column(name: str) -> str:
    """Quote column name for DAX"""
    return f"[{name}]"

def attach_port_if_connected(result: Any) -> Any:
    """Attach current connection port to result"""
    if not isinstance(result, dict):
        return result

    try:
        from core.infrastructure.connection_state import connection_state
        if connection_state.is_connected():
            result['connection_port'] = connection_state.current_port
    except Exception:
        pass

    return result
