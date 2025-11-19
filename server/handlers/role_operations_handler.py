"""
Role Operations Handler
Unified handler for all RLS/OLS role operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.role_operations import RoleOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_role_ops_handler = RoleOperationsHandler()

def handle_role_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified role operations"""
    return _role_ops_handler.execute(args)

def register_role_operations_handler(registry):
    """Register role operations handler"""

    tool = ToolDefinition(
        name="role_operations",
        description="Unified RLS/OLS operations: list roles, and CRUD for roles and table permissions",
        handler=handle_role_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list"],  # Add more as implemented: create, update, delete, rename, create_permission, etc.
                    "description": "Operation to perform on roles"
                },
                "role_name": {
                    "type": "string",
                    "description": "Role name (required for most operations)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New role name (required for: rename)"
                },
                "definition": {
                    "type": "object",
                    "description": "Role definition (required for: create, update)"
                },
                "permission": {
                    "type": "object",
                    "description": "Permission definition (required for: create_permission, update_permission)",
                    "properties": {
                        "table_name": {"type": "string"},
                        "filter_expression": {"type": "string"}
                    }
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (required for: delete_permission, test_role)"
                }
            },
            "required": ["operation"]
        },
        category="model_operations",
        sort_order=26
    )

    registry.register(tool)
    logger.info("Registered role_operations handler")
