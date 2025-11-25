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
        description=(
            "Unified table operations handler supporting ALL CRUD operations.\n"
            "\n"
            "━━━ READ OPERATIONS ━━━\n"
            "• list: List all tables with counts → operation='list'\n"
            "  Example: {'operation': 'list'}\n"
            "\n"
            "• describe: Get table details (columns, measures, relationships) → operation='describe', table_name=X\n"
            "  Example: {'operation': 'describe', 'table_name': 'Sales'}\n"
            "\n"
            "• preview: Show sample data (simple) → operation='preview', table_name=X, max_rows=N\n"
            "  Example: {'operation': 'preview', 'table_name': 'Sales', 'max_rows': 10}\n"
            "\n"
            "• sample_data: Get sample data (enhanced) → operation='sample_data', table_name=X\n"
            "  Supports column selection, ordering, and pagination.\n"
            "  Example: {'operation': 'sample_data', 'table_name': 'Sales', 'max_rows': 20}\n"
            "  Example with columns: {'operation': 'sample_data', 'table_name': 'Sales', 'columns': ['CustomerName', 'Amount']}\n"
            "  Example with ordering: {'operation': 'sample_data', 'table_name': 'Sales', 'order_by': 'Amount', 'order_direction': 'desc'}\n"
            "\n"
            "━━━ CREATE OPERATION ━━━\n"
            "• create: Create new table → operation='create', table_name=X\n"
            "  Required: table_name\n"
            "  Optional: description, expression (for calculated table), hidden\n"
            "  Example: {'operation': 'create', 'table_name': 'NewTable', 'description': 'My new table'}\n"
            "  Example (calculated): {'operation': 'create', 'table_name': 'TopCustomers', 'expression': 'TOPN(100, Customer, [Revenue], DESC)'}\n"
            "\n"
            "━━━ UPDATE OPERATION ━━━\n"
            "• update: Update existing table → operation='update', table_name=X\n"
            "  Required: table_name\n"
            "  Optional: description, expression, hidden, new_name\n"
            "  Example: {'operation': 'update', 'table_name': 'Sales', 'description': 'Updated description', 'hidden': true}\n"
            "\n"
            "━━━ DELETE OPERATION ━━━\n"
            "• delete: Delete table → operation='delete', table_name=X\n"
            "  Required: table_name\n"
            "  Example: {'operation': 'delete', 'table_name': 'OldTable'}\n"
            "\n"
            "━━━ RENAME OPERATION ━━━\n"
            "• rename: Rename table → operation='rename', table_name=X, new_name=Y\n"
            "  Required: table_name, new_name\n"
            "  Example: {'operation': 'rename', 'table_name': 'Sales', 'new_name': 'SalesData'}\n"
            "\n"
            "━━━ REFRESH OPERATION ━━━\n"
            "• refresh: Refresh table data → operation='refresh', table_name=X\n"
            "  Required: table_name\n"
            "  Example: {'operation': 'refresh', 'table_name': 'Sales'}\n"
            "\n"
            "USE ALL OPERATIONS AS NEEDED - don't skip CREATE/UPDATE/DELETE/RENAME!"
        ),
        handler=handle_table_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "describe", "preview", "sample_data", "create", "update", "delete", "rename", "refresh"],
                    "description": (
                        "Operation to perform (MUST USE ALL OPERATIONS - don't skip CRUD!):\n"
                        "• 'list' - List all tables\n"
                        "• 'describe' - Get table details with columns/measures/relationships\n"
                        "• 'preview' - Show sample data rows (simple)\n"
                        "• 'sample_data' - Get sample data (enhanced: column selection, ordering)\n"
                        "• 'create' - CREATE new table (requires: table_name; optional: description, expression, hidden)\n"
                        "• 'update' - UPDATE table properties (requires: table_name; optional: description, expression, hidden, new_name)\n"
                        "• 'delete' - DELETE table (requires: table_name)\n"
                        "• 'rename' - RENAME table (requires: table_name, new_name)\n"
                        "• 'refresh' - REFRESH table data (requires: table_name)"
                    )
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (required for: describe, preview, sample_data, create, update, delete, rename, refresh)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New table name (required for: rename operation)"
                },
                "description": {
                    "type": "string",
                    "description": "Table description (optional for: create, update)"
                },
                "expression": {
                    "type": "string",
                    "description": "DAX expression for calculated table (optional for: create, update). Example: 'TOPN(100, Customer, [Revenue], DESC)'"
                },
                "hidden": {
                    "type": "boolean",
                    "description": "Hide table from client tools (optional for: create, update)"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to return (default: 10, max: 1000, for preview/sample_data operations)",
                    "default": 10
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of column names to include in sample_data (optional, default: all columns)"
                },
                "order_by": {
                    "type": "string",
                    "description": "Column name to order by (for sample_data operation)"
                },
                "order_direction": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "Order direction: 'asc' or 'desc' (default: 'asc', for sample_data operation)",
                    "default": "asc"
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
        sort_order=10
    )

    registry.register(tool)
    logger.info("Registered table_operations handler")
