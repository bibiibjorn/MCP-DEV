"""
Column Operations Handler
Unified handler for all column operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.column_operations import ColumnOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_column_ops_handler = ColumnOperationsHandler()

def handle_column_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified column operations"""
    return _column_ops_handler.execute(args)

def register_column_operations_handler(registry):
    """Register column operations handler"""

    tool = ToolDefinition(
        name="column_operations",
        description=(
            "Unified column operations handler. USE THIS WHEN:\n"
            "• User asks 'list columns' / 'show columns in table X' / 'what columns exist' → operation='list'\n"
            "• User asks 'list calculated columns' / 'show calculated columns' → operation='list' with column_type='calculated'\n"
            "• User asks 'column statistics' / 'stats for column X' / 'distinct count for column X' → operation='statistics' (requires table_name and column_name)\n"
            "• User asks 'top values in column X' / 'value distribution for column X' → operation='distribution' (requires table_name and column_name)\n"
            "• User asks 'get column details for X' → operation='get' (requires table_name and column_name)\n"
            "\n"
            "OPERATIONS:\n"
            "• list: Returns column list (all columns, data columns only, or calculated columns only)\n"
            "• statistics: Returns distinct count, total count, blank count for a column\n"
            "• distribution: Returns top N values with counts for a column\n"
            "• get: Returns detailed column metadata\n"
            "• create/update/delete/rename: Modify column structure"
        ),
        handler=handle_column_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "statistics", "distribution", "get", "create", "update", "delete", "rename"],
                    "description": (
                        "Operation to perform:\n"
                        "• 'list' - List columns (use when: 'show columns', 'list columns in table X', 'what columns exist')\n"
                        "• 'statistics' - Get column stats (use when: 'column stats for X', 'distinct count for column X')\n"
                        "• 'distribution' - Get top values (use when: 'top values in column X', 'value distribution for X')\n"
                        "• 'get' - Get column details (use when: 'show column X details', 'get column X')\n"
                        "• 'create', 'update', 'delete', 'rename' - Modify columns"
                    )
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (optional for list, required for other operations)"
                },
                "column_name": {
                    "type": "string",
                    "description": "Column name (required for: statistics, distribution, get, update, delete, rename)"
                },
                "column_type": {
                    "type": "string",
                    "enum": ["all", "data", "calculated"],
                    "description": "Filter by column type (for list operation)",
                    "default": "all"
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top values for distribution (default: 10)",
                    "default": 10
                },
                "page_size": {
                    "type": "integer",
                    "description": "Page size for list operation"
                },
                "next_token": {
                    "type": "string",
                    "description": "Pagination token for list operation"
                },
                "data_type": {
                    "type": "string",
                    "enum": ["String", "Int64", "Double", "Decimal", "Boolean", "DateTime", "Binary", "Variant"],
                    "description": "Data type for column (required for: create)",
                    "default": "String"
                },
                "expression": {
                    "type": "string",
                    "description": "DAX expression for calculated column (optional for: create, update). If provided, creates a calculated column instead of a data column."
                },
                "description": {
                    "type": "string",
                    "description": "Column description (optional for: create, update)"
                },
                "hidden": {
                    "type": "boolean",
                    "description": "Whether to hide the column (optional for: create, update)"
                },
                "display_folder": {
                    "type": "string",
                    "description": "Display folder path (optional for: create, update)"
                },
                "format_string": {
                    "type": "string",
                    "description": "Format string like '#,0' or '$#,0.00' (optional for: create, update)"
                },
                "source_column": {
                    "type": "string",
                    "description": "Source column name for data columns (optional for: create)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New column name (required for: rename, optional for: update)"
                }
            },
            "required": ["operation"]
        },
        category="metadata",
        sort_order=3
    )

    registry.register(tool)
    logger.info("Registered column_operations handler")
