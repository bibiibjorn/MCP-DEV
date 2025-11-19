"""
Unified table operations handler
Consolidates: list_tables, describe_table + new CRUD operations
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class TableOperationsHandler(BaseOperationsHandler):
    """Handles all table-related operations"""

    def __init__(self):
        super().__init__("table_operations")

        # Register all operations
        self.register_operation('list', self._list_tables)
        self.register_operation('describe', self._describe_table)
        self.register_operation('preview', self._preview_table)
        self.register_operation('create', self._create_table)
        self.register_operation('update', self._update_table)
        self.register_operation('delete', self._delete_table)
        self.register_operation('rename', self._rename_table)
        self.register_operation('refresh', self._refresh_table)

    def _list_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables in the model"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        result = qe.execute_info_query("TABLES")

        # Apply pagination if requested
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _describe_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive table description"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        # Support both 'table_name' and 'table' for backward compatibility
        table_name = args.get('table_name') or args.get('table')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name (or table) parameter is required for operation: describe'
            }

        # Apply default pagination limits (backward compatibility)
        from core.infrastructure.limits_manager import get_limits
        from server.middleware import apply_default_limits
        limits = get_limits()
        defaults = {
            'columns_page_size': limits.token.describe_table_columns_page_size,
            'measures_page_size': limits.token.describe_table_measures_page_size,
            'relationships_page_size': limits.token.describe_table_relationships_page_size
        }
        args = apply_default_limits(args, defaults)

        # Check if method exists
        if not hasattr(qe, 'describe_table'):
            return {
                'success': False,
                'error': 'describe_table method not implemented in query executor'
            }

        try:
            result = qe.describe_table(table_name, args)
            return result
        except Exception as e:
            logger.error(f"Error describing table '{table_name}': {e}", exc_info=True)
            return ErrorHandler.handle_unexpected_error('describe_table', e)

    def _preview_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Preview table data"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        agent_policy = connection_state.agent_policy
        if not agent_policy:
            return ErrorHandler.handle_manager_unavailable('agent_policy')

        # Support both 'table_name' and 'table' for backward compatibility
        table_name = args.get('table_name') or args.get('table')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name (or table) parameter is required for operation: preview'
            }

        max_rows = args.get('max_rows', 10)

        # Create EVALUATE query for table preview
        query = f'EVALUATE TOPN({max_rows}, \'{table_name}\')'

        result = agent_policy.safe_run_dax(
            connection_state=connection_state,
            query=query,
            mode='auto',
            max_rows=max_rows
        )

        return result

    def _create_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        table_crud = connection_state.table_crud_manager
        if not table_crud:
            return ErrorHandler.handle_manager_unavailable('table_crud_manager')

        return table_crud.create_table(
            table_name=args.get('table_name'),
            description=args.get('description'),
            expression=args.get('expression'),
            hidden=args.get('hidden', False)
        )

    def _update_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        table_crud = connection_state.table_crud_manager
        if not table_crud:
            return ErrorHandler.handle_manager_unavailable('table_crud_manager')

        return table_crud.update_table(
            table_name=args.get('table_name'),
            description=args.get('description'),
            expression=args.get('expression'),
            hidden=args.get('hidden'),
            new_name=args.get('new_name')
        )

    def _delete_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        table_crud = connection_state.table_crud_manager
        if not table_crud:
            return ErrorHandler.handle_manager_unavailable('table_crud_manager')

        table_name = args.get('table_name')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name parameter is required for operation: delete'
            }

        return table_crud.delete_table(table_name)

    def _rename_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        table_crud = connection_state.table_crud_manager
        if not table_crud:
            return ErrorHandler.handle_manager_unavailable('table_crud_manager')

        table_name = args.get('table_name')
        new_name = args.get('new_name')

        if not table_name or not new_name:
            return {
                'success': False,
                'error': 'table_name and new_name parameters are required for operation: rename'
            }

        return table_crud.rename_table(table_name, new_name)

    def _refresh_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh a table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        table_crud = connection_state.table_crud_manager
        if not table_crud:
            return ErrorHandler.handle_manager_unavailable('table_crud_manager')

        table_name = args.get('table_name')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name parameter is required for operation: refresh'
            }

        return table_crud.refresh_table(table_name)
