"""
Unified role operations handler
Extends: list_roles + new CRUD and permission operations
"""
from typing import Dict, Any
import logging
from .base_operations import BaseOperationsHandler
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class RoleOperationsHandler(BaseOperationsHandler):
    """Handles all RLS/OLS role-related operations"""

    def __init__(self):
        super().__init__("role_operations")

        # Register all operations
        self.register_operation('list', self._list_roles)
        # Future: create, update, delete, rename,
        # create_permission, update_permission, delete_permission, test_role

    def _list_roles(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List RLS roles"""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        rls_mgr = connection_state.rls_manager
        if not rls_mgr:
            return ErrorHandler.handle_manager_unavailable('rls_manager')

        return rls_mgr.list_roles()

    # Future methods: _create_role, _update_role, _delete_role, _rename_role,
    # _create_permission, _update_permission, _delete_permission, _test_role
