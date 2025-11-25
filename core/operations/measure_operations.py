"""
Unified measure operations handler
Consolidates: list_measures, get_measure_details, upsert_measure, delete_measure

Refactored to use validation utilities for reduced code duplication.
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler

# Import validation utilities
from core.validation import (
    get_manager_or_error,
    get_table_name,
    get_measure_name,
    get_format_string,
    get_source_table,
    get_target_table,
    get_new_name,
    apply_pagination_with_defaults,
    validate_table_and_item,
    validate_create_params,
    validate_rename_params,
    validate_move_params,
)

logger = logging.getLogger(__name__)


class MeasureOperationsHandler(BaseOperationsHandler):
    """Handles all measure-related operations"""

    def __init__(self):
        super().__init__("measure_operations")

        # Register all operations
        self.register_operation('list', self._list_measures)
        self.register_operation('get', self._get_measure)
        self.register_operation('create', self._create_measure)
        self.register_operation('update', self._update_measure)
        self.register_operation('delete', self._delete_measure)
        self.register_operation('rename', self._rename_measure)
        self.register_operation('move', self._move_measure)

    def _list_measures(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List measures, optionally filtered by table"""
        # Get manager with connection check
        qe = get_manager_or_error('query_executor')
        if isinstance(qe, dict):  # Error response
            return qe

        # Extract parameters with backward compatibility
        table_name = get_table_name(args)

        result = qe.execute_info_query("MEASURES", table_name=table_name, exclude_columns=['Expression'])

        # Apply pagination with defaults
        return apply_pagination_with_defaults(result, args)

    def _get_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed measure information including DAX formula"""
        # Get manager with connection check
        qe = get_manager_or_error('query_executor')
        if isinstance(qe, dict):  # Error response
            return qe

        # Extract parameters with backward compatibility
        table_name = get_table_name(args)
        measure_name = get_measure_name(args)

        # Validate required parameters
        if error := validate_table_and_item(table_name, measure_name, 'measure_name', 'get'):
            return error

        result = qe.get_measure_details_with_fallback(table_name, measure_name)
        return result

    def _create_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new measure"""
        # Get manager with connection check
        dax_injector = get_manager_or_error('dax_injector')
        if isinstance(dax_injector, dict):  # Error response
            return dax_injector

        # Extract parameters with backward compatibility
        table_name = get_table_name(args)
        measure_name = get_measure_name(args)
        expression = args.get('expression')
        format_string = get_format_string(args)

        # Validate required parameters
        if error := validate_create_params(table_name, measure_name, expression, 'measure_name'):
            return error

        return dax_injector.upsert_measure(
            table_name=table_name,
            measure_name=measure_name,
            dax_expression=expression,
            description=args.get('description'),
            format_string=format_string,
            display_folder=args.get('display_folder')
        )

    def _update_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing measure"""
        # Same implementation as create (upsert_measure handles both)
        return self._create_measure(args)

    def _delete_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a measure"""
        # Get manager with connection check
        dax_injector = get_manager_or_error('dax_injector')
        if isinstance(dax_injector, dict):  # Error response
            return dax_injector

        # Extract parameters with backward compatibility
        table_name = get_table_name(args)
        measure_name = get_measure_name(args)

        # Validate required parameters
        if error := validate_table_and_item(table_name, measure_name, 'measure_name', 'delete'):
            return error

        return dax_injector.delete_measure(
            table_name=table_name,
            measure_name=measure_name
        )

    def _rename_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a measure"""
        # Get manager with connection check
        measure_crud = get_manager_or_error('measure_crud_manager')
        if isinstance(measure_crud, dict):  # Error response
            return measure_crud

        # Extract parameters with backward compatibility
        table_name = get_table_name(args)
        measure_name = get_measure_name(args)
        new_name = get_new_name(args)

        # Validate required parameters
        if error := validate_rename_params(table_name, measure_name, new_name, 'measure_name'):
            return error

        return measure_crud.rename_measure(table_name, measure_name, new_name)

    def _move_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Move measure to a different table"""
        # Get manager with connection check
        measure_crud = get_manager_or_error('measure_crud_manager')
        if isinstance(measure_crud, dict):  # Error response
            return measure_crud

        # Extract parameters with backward compatibility
        source_table = get_source_table(args)
        target_table = get_target_table(args)
        measure_name = get_measure_name(args)

        # Validate required parameters
        if error := validate_move_params(source_table, measure_name, target_table, 'measure_name'):
            return error

        return measure_crud.move_measure(source_table, measure_name, target_table)
