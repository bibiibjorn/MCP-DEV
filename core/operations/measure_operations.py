"""
Unified measure operations handler
Consolidates: list_measures, get_measure_details, upsert_measure, delete_measure
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

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
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')

        result = qe.execute_info_query("MEASURES", table_name=table_name, exclude_columns=['Expression'])

        # Apply pagination
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _get_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed measure information including DAX formula"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')

        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'table_name and measure_name are required for operation: get'
            }

        result = qe.get_measure_details_with_fallback(table_name, measure_name)
        return result

    def _create_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new measure"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        dax_injector = connection_state.dax_injector
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')
        expression = args.get('expression')

        if not table_name or not measure_name or not expression:
            return {
                'success': False,
                'error': 'table_name, measure_name, and expression are required for operation: create'
            }

        return dax_injector.upsert_measure(
            table_name=table_name,
            measure_name=measure_name,
            dax_expression=expression,
            description=args.get('description'),
            format_string=args.get('format_string'),
            display_folder=args.get('display_folder')
        )

    def _update_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing measure"""
        # Same implementation as create (upsert_measure handles both)
        return self._create_measure(args)

    def _delete_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a measure"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        dax_injector = connection_state.dax_injector
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')

        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'table_name and measure_name are required for operation: delete'
            }

        return dax_injector.delete_measure(
            table_name=table_name,
            measure_name=measure_name
        )


    def _rename_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a measure"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        dax_injector = connection_state.dax_injector
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')

        table_name = args.get('table_name')
        measure_name = args.get('measure_name')
        new_name = args.get('new_name')

        if not table_name or not measure_name or not new_name:
            return {
                'success': False,
                'error': 'table_name, measure_name, and new_name are required for operation: rename'
            }

        return dax_injector.rename_measure(table_name, measure_name, new_name)

    def _move_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Move a measure between tables"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        dax_injector = connection_state.dax_injector
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')

        source_table = args.get('source_table') or args.get('table_name')
        measure_name = args.get('measure_name')
        target_table = args.get('target_table')

        if not source_table or not measure_name or not target_table:
            return {
                'success': False,
                'error': 'source_table (or table_name), measure_name, and target_table are required for operation: move'
            }

        return dax_injector.move_measure(source_table, measure_name, target_table)

