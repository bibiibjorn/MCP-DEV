"""
Table Operations Handler
Unified handler for all table operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.table_operations import TableOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_table_ops_handler = TableOperationsHandler()

def handle_table_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified table operations"""
    return _table_ops_handler.execute(args)

def register_table_operations_handler(registry):
    """Register table operations handler"""

    tool = ToolDefinition(
        name="table_operations",
        description="Unified table operations: list, describe, preview, and CRUD (create/update/delete/rename/refresh)",
        handler=handle_table_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "describe", "preview", "create", "update", "delete", "rename", "refresh"],
                    "description": "Operation to perform on tables"
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (required for: describe, preview, update, delete, rename, refresh)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New table name (required for: rename)"
                },
                "definition": {
                    "type": "object",
                    "description": "Table definition (required for: create, update)"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to preview (default: 10, for preview operation)",
                    "default": 10
                },
                "columns_page_size": {
                    "type": "integer",
                    "description": "Page size for columns in describe operation"
                },
                "measures_page_size": {
                    "type": "integer",
                    "description": "Page size for measures in describe operation"
                },
                "relationships_page_size": {
                    "type": "integer",
                    "description": "Page size for relationships in describe operation"
                },
                "page_size": {
                    "type": "integer",
                    "description": "Page size for list operation"
                },
                "next_token": {
                    "type": "string",
                    "description": "Pagination token for list operation"
                }
            },
            "required": ["operation"]
        },
        category="metadata",
        sort_order=2
    )

    registry.register(tool)
    logger.info("Registered table_operations handler")
