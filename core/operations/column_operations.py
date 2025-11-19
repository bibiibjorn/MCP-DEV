"""
Unified column operations handler
Consolidates: list_columns, list_calculated_columns, get_column_value_distribution, get_column_summary
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.infrastructure.query_executor import COLUMN_TYPE_CALCULATED

logger = logging.getLogger(__name__)

class ColumnOperationsHandler(BaseOperationsHandler):
    """Handles all column-related operations"""

    def __init__(self):
        super().__init__("column_operations")

        # Register all operations
        self.register_operation('list', self._list_columns)
        self.register_operation('statistics', self._get_column_statistics)
        self.register_operation('distribution', self._get_column_distribution)
        self.register_operation('get', self._get_column)
        self.register_operation('create', self._create_column)
        self.register_operation('update', self._update_column)
        self.register_operation('delete', self._delete_column)
        self.register_operation('rename', self._rename_column)

    def _list_columns(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List columns, optionally filtered by table and type"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')
        column_type = args.get('column_type', 'all')  # 'all', 'data', 'calculated'

        # Build filter expression based on column_type
        filter_expr = None
        if column_type == 'calculated':
            filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
        elif column_type == 'data':
            filter_expr = f'[Type] <> {COLUMN_TYPE_CALCULATED}'
        # else: 'all' - no filter

        result = qe.execute_info_query("COLUMNS", table_name=table_name, filter_expr=filter_expr)

        # Apply pagination
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _get_column_statistics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get column summary statistics"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        agent_policy = connection_state.agent_policy
        if not agent_policy:
            return ErrorHandler.handle_manager_unavailable('agent_policy')

        table_name = args.get('table_name')
        column_name = args.get('column_name')

        if not table_name or not column_name:
            return {
                'success': False,
                'error': 'table_name and column_name are required for operation: statistics'
            }

        # Create DAX query to get column statistics
        query = f'''
        EVALUATE
        ROW(
            "DistinctCount", COUNTROWS(DISTINCT('{table_name}'[{column_name}])),
            "TotalCount", COUNTROWS('{table_name}'),
            "BlankCount", COUNTBLANK('{table_name}'[{column_name}])
        )
        '''

        return agent_policy.safe_run_dax(
            connection_state=connection_state,
            query=query,
            mode='auto'
        )

    def _get_column_distribution(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get column value distribution"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        agent_policy = connection_state.agent_policy
        if not agent_policy:
            return ErrorHandler.handle_manager_unavailable('agent_policy')

        table_name = args.get('table_name')
        column_name = args.get('column_name')

        if not table_name or not column_name:
            return {
                'success': False,
                'error': 'table_name and column_name are required for operation: distribution'
            }

        top_n = args.get('top_n', 10)

        # Create DAX query to get value distribution
        query = f'''
        EVALUATE
        TOPN(
            {top_n},
            SUMMARIZECOLUMNS(
                '{table_name}'[{column_name}],
                "Count", COUNTROWS('{table_name}')
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


    def _get_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed column information"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        column_crud = connection_state.column_crud_manager
        if not column_crud:
            return ErrorHandler.handle_manager_unavailable('column_crud_manager')

        table_name = args.get('table_name')
        column_name = args.get('column_name')

        if not table_name or not column_name:
            return {
                'success': False,
                'error': 'table_name and column_name are required for operation: get'
            }

        return column_crud.get_column(table_name, column_name)

    def _create_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new column"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        column_crud = connection_state.column_crud_manager
        if not column_crud:
            return ErrorHandler.handle_manager_unavailable('column_crud_manager')

        return column_crud.create_column(
            table_name=args.get('table_name'),
            column_name=args.get('column_name'),
            data_type=args.get('data_type', 'String'),
            expression=args.get('expression'),
            description=args.get('description'),
            hidden=args.get('hidden', False),
            display_folder=args.get('display_folder'),
            format_string=args.get('format_string'),
            source_column=args.get('source_column')
        )

    def _update_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing column"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        column_crud = connection_state.column_crud_manager
        if not column_crud:
            return ErrorHandler.handle_manager_unavailable('column_crud_manager')

        return column_crud.update_column(
            table_name=args.get('table_name'),
            column_name=args.get('column_name'),
            expression=args.get('expression'),
            description=args.get('description'),
            hidden=args.get('hidden'),
            display_folder=args.get('display_folder'),
            format_string=args.get('format_string'),
            new_name=args.get('new_name')
        )

    def _delete_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a column"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        column_crud = connection_state.column_crud_manager
        if not column_crud:
            return ErrorHandler.handle_manager_unavailable('column_crud_manager')

        table_name = args.get('table_name')
        column_name = args.get('column_name')

        if not table_name or not column_name:
            return {
                'success': False,
                'error': 'table_name and column_name are required for operation: delete'
            }

        return column_crud.delete_column(table_name, column_name)

    def _rename_column(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a column"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        column_crud = connection_state.column_crud_manager
        if not column_crud:
            return ErrorHandler.handle_manager_unavailable('column_crud_manager')

        table_name = args.get('table_name')
        column_name = args.get('column_name')
        new_name = args.get('new_name')

        if not table_name or not column_name or not new_name:
            return {
                'success': False,
                'error': 'table_name, column_name, and new_name are required for operation: rename'
            }

        return column_crud.rename_column(table_name, column_name, new_name)

