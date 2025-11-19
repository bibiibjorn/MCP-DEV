"""
Unified relationship operations handler
Extends: list_relationships + new CRUD operations
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class RelationshipOperationsHandler(BaseOperationsHandler):
    """Handles all relationship-related operations"""

    def __init__(self):
        super().__init__("relationship_operations")

        # Register all operations
        self.register_operation('list', self._list_relationships)
        self.register_operation('get', self._get_relationship)
        self.register_operation('find', self._find_relationships)
        self.register_operation('create', self._create_relationship)
        self.register_operation('update', self._update_relationship)
        self.register_operation('delete', self._delete_relationship)
        self.register_operation('activate', self._activate_relationship)
        self.register_operation('deactivate', self._deactivate_relationship)

    def _list_relationships(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List relationships with optional active_only filter"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        active_only = args.get('active_only', False)

        # Use INFO query to get relationships
        result = qe.execute_info_query("RELATIONSHIPS")

        if result.get('success') and active_only:
            rows = result.get('rows', [])
            # Filter for active relationships only
            active_rows = [r for r in rows if r.get('IsActive') or r.get('[IsActive]')]
            result['rows'] = active_rows

        # Apply pagination
        page_size = args.get('page_size')
        next_token = args.get('next_token')
        if page_size or next_token:
            from server.middleware import paginate
            result = paginate(result, page_size, next_token, ['rows'])

        return result

    def _get_relationship(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get single relationship details"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        relationship_name = args.get('relationship_name')
        if not relationship_name:
            return {
                'success': False,
                'error': 'relationship_name parameter is required for operation: get'
            }

        # Get all relationships and filter
        result = qe.execute_info_query("RELATIONSHIPS")

        if result.get('success'):
            rows = result.get('rows', [])
            matching = [r for r in rows if r.get('Name') == relationship_name or r.get('[Name]') == relationship_name]

            if matching:
                return {
                    'success': True,
                    'relationship': matching[0]
                }
            else:
                return {
                    'success': False,
                    'error': f'Relationship not found: {relationship_name}'
                }

        return result

    def _find_relationships(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find relationships for a specific table"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        table_name = args.get('table_name')
        if not table_name:
            return {
                'success': False,
                'error': 'table_name parameter is required for operation: find'
            }

        # Get all relationships
        result = qe.execute_info_query("RELATIONSHIPS")

        if result.get('success'):
            rows = result.get('rows', [])
            # Filter for relationships involving this table
            matching = [r for r in rows if
                       r.get('FromTable') == table_name or r.get('[FromTable]') == table_name or
                       r.get('ToTable') == table_name or r.get('[ToTable]') == table_name]

            return {
                'success': True,
                'table_name': table_name,
                'relationship_count': len(matching),
                'relationships': matching
            }

        return result


    def _create_relationship(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new relationship"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        rel_crud = connection_state.relationship_crud_manager
        if not rel_crud:
            return ErrorHandler.handle_manager_unavailable('relationship_crud_manager')

        from_table = args.get('from_table')
        from_column = args.get('from_column')
        to_table = args.get('to_table')
        to_column = args.get('to_column')

        if not all([from_table, from_column, to_table, to_column]):
            return {
                'success': False,
                'error': 'from_table, from_column, to_table, and to_column are required for operation: create'
            }

        return rel_crud.create_relationship(
            from_table=from_table,
            from_column=from_column,
            to_table=to_table,
            to_column=to_column,
            name=args.get('name'),
            from_cardinality=args.get('from_cardinality', 'Many'),
            to_cardinality=args.get('to_cardinality', 'One'),
            cross_filtering_behavior=args.get('cross_filtering_behavior', 'OneDirection'),
            is_active=args.get('is_active', True)
        )

    def _update_relationship(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing relationship"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        rel_crud = connection_state.relationship_crud_manager
        if not rel_crud:
            return ErrorHandler.handle_manager_unavailable('relationship_crud_manager')

        relationship_name = args.get('relationship_name')
        if not relationship_name:
            return {
                'success': False,
                'error': 'relationship_name is required for operation: update'
            }

        return rel_crud.update_relationship(
            relationship_name=relationship_name,
            cross_filtering_behavior=args.get('cross_filtering_behavior'),
            is_active=args.get('is_active'),
            new_name=args.get('new_name')
        )

    def _delete_relationship(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a relationship"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        rel_crud = connection_state.relationship_crud_manager
        if not rel_crud:
            return ErrorHandler.handle_manager_unavailable('relationship_crud_manager')

        relationship_name = args.get('relationship_name')
        if not relationship_name:
            return {
                'success': False,
                'error': 'relationship_name is required for operation: delete'
            }

        return rel_crud.delete_relationship(relationship_name)

    def _activate_relationship(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Activate a relationship"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        rel_crud = connection_state.relationship_crud_manager
        if not rel_crud:
            return ErrorHandler.handle_manager_unavailable('relationship_crud_manager')

        relationship_name = args.get('relationship_name')
        if not relationship_name:
            return {
                'success': False,
                'error': 'relationship_name is required for operation: activate'
            }

        return rel_crud.activate_relationship(relationship_name)

    def _deactivate_relationship(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate a relationship"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        rel_crud = connection_state.relationship_crud_manager
        if not rel_crud:
            return ErrorHandler.handle_manager_unavailable('relationship_crud_manager')

        relationship_name = args.get('relationship_name')
        if not relationship_name:
            return {
                'success': False,
                'error': 'relationship_name is required for operation: deactivate'
            }

        return rel_crud.deactivate_relationship(relationship_name)

