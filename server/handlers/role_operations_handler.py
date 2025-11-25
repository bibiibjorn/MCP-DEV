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
        description=(
            "Unified RLS/OLS role operations handler supporting ALL CRUD operations.\n"
            "\n"
            "━━━ READ OPERATIONS ━━━\n"
            "• list: List all security roles → operation='list'\n"
            "  Example: {'operation': 'list'}\n"
            "\n"
            "RLS = Row-Level Security (filter data rows)\n"
            "OLS = Object-Level Security (hide objects)\n"
            "\n"
            "Note: Additional CRUD operations (create, update, delete, rename) will be available when implemented.\n"
            "USE ALL OPERATIONS AS NEEDED when they become available!"
        ),
        handler=handle_role_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list"],
                    "description": (
                        "Operation to perform:\n"
                        "• 'list' - List all security roles (RLS/OLS)\n"
                        "Note: Additional operations (create, update, delete, rename, create_permission, etc.) will be available when implemented."
                    )
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
            "required": ["operation"],
            "examples": [
                {
                    "_description": "List all security roles (RLS/OLS)",
                    "operation": "list"
                }
            ]
        },
        category="model_operations",
        sort_order=17
    )

    registry.register(tool)
    logger.info("Registered role_operations handler")
