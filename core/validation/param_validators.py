"""
Parameter validators for consistent validation error handling.

These validators consolidate duplicate validation error response patterns.
Reduces ~60 lines of duplicated code.
"""
from typing import Any, Dict, List, Optional, Tuple, Union


def validate_required(value: Any, param_name: str, operation: str) -> Optional[Dict[str, Any]]:
    """
    Validate that a required parameter is provided.

    Args:
        value: The parameter value to validate
        param_name: Name of the parameter for error messages
        operation: Name of the operation for error messages

    Returns:
        Error dict if validation fails, None if valid

    Usage:
        if error := validate_required(table_name, 'table_name', 'describe'):
            return error
    """
    if not value:
        return {
            'success': False,
            'error': f'{param_name} is required for operation: {operation}'
        }
    return None


def validate_required_params(
    *params: Tuple[Any, str],
    operation: str
) -> Optional[Dict[str, Any]]:
    """
    Validate multiple required parameters at once.

    Args:
        *params: Variable number of (value, param_name) tuples
        operation: Name of the operation for error messages

    Returns:
        Error dict if any validation fails, None if all valid

    Usage:
        if error := validate_required_params(
            (table_name, 'table_name'),
            (column_name, 'column_name'),
            operation='statistics'
        ):
            return error
    """
    missing = []
    for value, param_name in params:
        if not value:
            missing.append(param_name)

    if missing:
        if len(missing) == 1:
            return {
                'success': False,
                'error': f'{missing[0]} is required for operation: {operation}'
            }
        else:
            params_str = ' and '.join(missing)
            return {
                'success': False,
                'error': f'{params_str} are required for operation: {operation}'
            }

    return None


def validate_any_of(
    *params: Tuple[Any, str],
    operation: str
) -> Optional[Dict[str, Any]]:
    """
    Validate that at least one of the parameters is provided.

    Args:
        *params: Variable number of (value, param_name) tuples
        operation: Name of the operation for error messages

    Returns:
        Error dict if none provided, None if at least one valid

    Usage:
        if error := validate_any_of(
            (expression, 'expression'),
            (description, 'description'),
            operation='update'
        ):
            return error
    """
    for value, _ in params:
        if value is not None:
            return None

    param_names = [name for _, name in params]
    params_str = ', '.join(param_names)
    return {
        'success': False,
        'error': f'At least one of {params_str} is required for operation: {operation}'
    }


def validate_enum(
    value: Any,
    param_name: str,
    allowed_values: List[str],
    operation: str,
    case_sensitive: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Validate that a parameter value is from an allowed set.

    Args:
        value: The parameter value to validate
        param_name: Name of the parameter for error messages
        allowed_values: List of allowed values
        operation: Name of the operation for error messages
        case_sensitive: Whether to do case-sensitive comparison

    Returns:
        Error dict if validation fails, None if valid or value is None

    Usage:
        if error := validate_enum(column_type, 'column_type', ['all', 'data', 'calculated'], 'list'):
            return error
    """
    if value is None:
        return None

    check_value = value if case_sensitive else str(value).lower()
    check_allowed = allowed_values if case_sensitive else [v.lower() for v in allowed_values]

    if check_value not in check_allowed:
        return {
            'success': False,
            'error': f"Invalid {param_name} '{value}' for operation: {operation}. Allowed values: {', '.join(allowed_values)}"
        }

    return None


def validate_positive_int(
    value: Any,
    param_name: str,
    operation: str,
    max_value: Optional[int] = None,
    allow_none: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Validate that a parameter is a positive integer.

    Args:
        value: The parameter value to validate
        param_name: Name of the parameter for error messages
        operation: Name of the operation for error messages
        max_value: Optional maximum allowed value
        allow_none: Whether to allow None values

    Returns:
        Error dict if validation fails, None if valid

    Usage:
        if error := validate_positive_int(top_n, 'top_n', 'distribution', max_value=1000):
            return error
    """
    if value is None:
        if allow_none:
            return None
        else:
            return {
                'success': False,
                'error': f'{param_name} is required for operation: {operation}'
            }

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return {
            'success': False,
            'error': f'{param_name} must be an integer for operation: {operation}'
        }

    if int_value <= 0:
        return {
            'success': False,
            'error': f'{param_name} must be a positive integer for operation: {operation}'
        }

    if max_value is not None and int_value > max_value:
        return {
            'success': False,
            'error': f'{param_name} exceeds maximum value of {max_value} for operation: {operation}'
        }

    return None


def validate_table_and_item(
    table_name: Any,
    item_name: Any,
    item_param_name: str,
    operation: str
) -> Optional[Dict[str, Any]]:
    """
    Common validation: table_name and another required item.

    Args:
        table_name: The table name value
        item_name: The item name value (measure, column, etc.)
        item_param_name: Name of the item parameter
        operation: Name of the operation

    Returns:
        Error dict if validation fails, None if valid

    Usage:
        if error := validate_table_and_item(table_name, measure_name, 'measure_name', 'get'):
            return error
    """
    return validate_required_params(
        (table_name, 'table_name'),
        (item_name, item_param_name),
        operation=operation
    )


def validate_create_params(
    table_name: Any,
    item_name: Any,
    expression: Any,
    item_param_name: str,
    require_expression: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Common validation for create operations.

    Args:
        table_name: The table name value
        item_name: The item name value (measure, column, etc.)
        expression: The DAX expression value
        item_param_name: Name of the item parameter
        require_expression: Whether expression is required

    Returns:
        Error dict if validation fails, None if valid

    Usage:
        if error := validate_create_params(table_name, measure_name, expression, 'measure_name'):
            return error
    """
    if require_expression:
        return validate_required_params(
            (table_name, 'table_name'),
            (item_name, item_param_name),
            (expression, 'expression'),
            operation='create'
        )
    else:
        return validate_required_params(
            (table_name, 'table_name'),
            (item_name, item_param_name),
            operation='create'
        )


def validate_rename_params(
    table_name: Any,
    item_name: Any,
    new_name: Any,
    item_param_name: str
) -> Optional[Dict[str, Any]]:
    """
    Common validation for rename operations.

    Args:
        table_name: The table name value
        item_name: The item name value
        new_name: The new name value
        item_param_name: Name of the item parameter

    Returns:
        Error dict if validation fails, None if valid

    Usage:
        if error := validate_rename_params(table_name, measure_name, new_name, 'measure_name'):
            return error
    """
    return validate_required_params(
        (table_name, 'table_name'),
        (item_name, item_param_name),
        (new_name, 'new_name'),
        operation='rename'
    )


def validate_move_params(
    source_table: Any,
    item_name: Any,
    target_table: Any,
    item_param_name: str
) -> Optional[Dict[str, Any]]:
    """
    Common validation for move operations.

    Args:
        source_table: The source table name
        item_name: The item name value
        target_table: The target table name
        item_param_name: Name of the item parameter

    Returns:
        Error dict if validation fails, None if valid

    Usage:
        if error := validate_move_params(source_table, measure_name, target_table, 'measure_name'):
            return error
    """
    return validate_required_params(
        (source_table, 'source_table'),
        (item_name, item_param_name),
        (target_table, 'target_table'),
        operation='move'
    )


def validate_relationship_create_params(
    from_table: Any,
    from_column: Any,
    to_table: Any,
    to_column: Any
) -> Optional[Dict[str, Any]]:
    """
    Validation for relationship create operations.

    Returns:
        Error dict if validation fails, None if valid
    """
    return validate_required_params(
        (from_table, 'from_table'),
        (from_column, 'from_column'),
        (to_table, 'to_table'),
        (to_column, 'to_column'),
        operation='create'
    )


class ValidationBuilder:
    """
    Fluent builder for complex validation logic.

    Usage:
        error = ValidationBuilder(operation='create') \
            .require(table_name, 'table_name') \
            .require(measure_name, 'measure_name') \
            .require(expression, 'expression') \
            .enum(format_type, 'format_type', ['percent', 'currency', 'number']) \
            .positive_int(top_n, 'top_n', max_value=1000) \
            .validate()

        if error:
            return error
    """

    def __init__(self, operation: str):
        self.operation = operation
        self._errors: List[str] = []

    def require(self, value: Any, param_name: str) -> 'ValidationBuilder':
        """Add a required parameter validation."""
        if not value:
            self._errors.append(f'{param_name} is required')
        return self

    def require_any(self, *params: Tuple[Any, str]) -> 'ValidationBuilder':
        """Add validation that at least one parameter is provided."""
        for value, _ in params:
            if value is not None:
                return self

        param_names = [name for _, name in params]
        self._errors.append(f'At least one of {", ".join(param_names)} is required')
        return self

    def enum(self, value: Any, param_name: str, allowed: List[str], case_sensitive: bool = False) -> 'ValidationBuilder':
        """Add enum validation."""
        if value is not None:
            check_value = value if case_sensitive else str(value).lower()
            check_allowed = allowed if case_sensitive else [v.lower() for v in allowed]
            if check_value not in check_allowed:
                self._errors.append(f"Invalid {param_name} '{value}'. Allowed: {', '.join(allowed)}")
        return self

    def positive_int(self, value: Any, param_name: str, max_value: Optional[int] = None) -> 'ValidationBuilder':
        """Add positive integer validation."""
        if value is not None:
            try:
                int_value = int(value)
                if int_value <= 0:
                    self._errors.append(f'{param_name} must be positive')
                elif max_value and int_value > max_value:
                    self._errors.append(f'{param_name} exceeds maximum {max_value}')
            except (ValueError, TypeError):
                self._errors.append(f'{param_name} must be an integer')
        return self

    def validate(self) -> Optional[Dict[str, Any]]:
        """Execute validation and return error dict if any failures."""
        if not self._errors:
            return None

        if len(self._errors) == 1:
            return {
                'success': False,
                'error': f'{self._errors[0]} for operation: {self.operation}'
            }
        else:
            return {
                'success': False,
                'error': f'Validation errors for operation {self.operation}: {"; ".join(self._errors)}'
            }
