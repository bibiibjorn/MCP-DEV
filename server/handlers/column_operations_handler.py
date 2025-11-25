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
            "Unified column operations handler supporting ALL CRUD operations.\n"
            "\n"
            "━━━ READ OPERATIONS ━━━\n"
            "• list: List columns (all/data/calculated) → operation='list'\n"
            "  Optional: table_name, column_type ('all'/'data'/'calculated')\n"
            "  Example: {'operation': 'list', 'table_name': 'Sales', 'column_type': 'calculated'}\n"
            "\n"
            "• get: Get column details → operation='get', table_name=X, column_name=Y\n"
            "  Example: {'operation': 'get', 'table_name': 'Sales', 'column_name': 'Amount'}\n"
            "\n"
            "• statistics: Get column stats (distinct/total/blank counts) → operation='statistics', table_name=X, column_name=Y\n"
            "  Example: {'operation': 'statistics', 'table_name': 'Sales', 'column_name': 'CustomerID'}\n"
            "\n"
            "• distribution: Get top N values → operation='distribution', table_name=X, column_name=Y, top_n=N\n"
            "  Example: {'operation': 'distribution', 'table_name': 'Sales', 'column_name': 'Country', 'top_n': 10}\n"
            "\n"
            "━━━ CREATE OPERATION ━━━\n"
            "• create: Create new column → operation='create', table_name=X, column_name=Y\n"
            "  Required: table_name, column_name\n"
            "  Optional: data_type, expression (for calculated), description, hidden, display_folder, format_string, source_column\n"
            "  Example (data column): {'operation': 'create', 'table_name': 'Sales', 'column_name': 'NewColumn', 'data_type': 'String'}\n"
            "  Example (calculated): {'operation': 'create', 'table_name': 'Sales', 'column_name': 'TotalAmount', 'expression': '[Quantity] * [Price]'}\n"
            "\n"
            "━━━ UPDATE OPERATION ━━━\n"
            "• update: Update existing column → operation='update', table_name=X, column_name=Y\n"
            "  Required: table_name, column_name\n"
            "  Optional: expression, description, hidden, display_folder, format_string, new_name\n"
            "  Example: {'operation': 'update', 'table_name': 'Sales', 'column_name': 'Amount', 'format_string': '$#,0.00', 'description': 'Updated'}\n"
            "\n"
            "━━━ DELETE OPERATION ━━━\n"
            "• delete: Delete column → operation='delete', table_name=X, column_name=Y\n"
            "  Required: table_name, column_name\n"
            "  Example: {'operation': 'delete', 'table_name': 'Sales', 'column_name': 'OldColumn'}\n"
            "\n"
            "━━━ RENAME OPERATION ━━━\n"
            "• rename: Rename column → operation='rename', table_name=X, column_name=Y, new_name=Z\n"
            "  Required: table_name, column_name, new_name\n"
            "  Example: {'operation': 'rename', 'table_name': 'Sales', 'column_name': 'Amt', 'new_name': 'Amount'}\n"
            "\n"
            "USE ALL OPERATIONS AS NEEDED - don't skip CREATE/UPDATE/DELETE/RENAME!"
        ),
        handler=handle_column_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "statistics", "distribution", "get", "create", "update", "delete", "rename"],
                    "description": (
                        "Operation to perform (MUST USE ALL OPERATIONS - don't skip CRUD!):\n"
                        "• 'list' - List columns with optional filters\n"
                        "• 'get' - Get detailed column metadata\n"
                        "• 'statistics' - Get column stats (distinct/total/blank counts)\n"
                        "• 'distribution' - Get top N values with counts\n"
                        "• 'create' - CREATE new column (requires: table_name, column_name; optional: data_type, expression, description, hidden, display_folder, format_string, source_column)\n"
                        "• 'update' - UPDATE column properties (requires: table_name, column_name; optional: expression, description, hidden, display_folder, format_string, new_name)\n"
                        "• 'delete' - DELETE column (requires: table_name, column_name)\n"
                        "• 'rename' - RENAME column (requires: table_name, column_name, new_name)"
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
            "required": ["operation"],
            "examples": [
                {
                    "_description": "List all columns in the model",
                    "operation": "list"
                },
                {
                    "_description": "List columns in a specific table",
                    "operation": "list",
                    "table_name": "Sales"
                },
                {
                    "_description": "List only calculated columns",
                    "operation": "list",
                    "column_type": "calculated"
                },
                {
                    "_description": "Get column details",
                    "operation": "get",
                    "table_name": "Sales",
                    "column_name": "Amount"
                },
                {
                    "_description": "Get column statistics (distinct, blanks, etc.)",
                    "operation": "statistics",
                    "table_name": "Customer",
                    "column_name": "CustomerID"
                },
                {
                    "_description": "Get value distribution (top 10 values)",
                    "operation": "distribution",
                    "table_name": "Sales",
                    "column_name": "Country",
                    "top_n": 10
                },
                {
                    "_description": "Create a calculated column",
                    "operation": "create",
                    "table_name": "Sales",
                    "column_name": "TotalAmount",
                    "expression": "[Quantity] * [UnitPrice]",
                    "format_string": "$#,0.00"
                },
                {
                    "_description": "Create a data column",
                    "operation": "create",
                    "table_name": "Customer",
                    "column_name": "Region",
                    "data_type": "String"
                },
                {
                    "_description": "Update column format string",
                    "operation": "update",
                    "table_name": "Sales",
                    "column_name": "Amount",
                    "format_string": "$#,0.00"
                },
                {
                    "_description": "Hide a column",
                    "operation": "update",
                    "table_name": "Sales",
                    "column_name": "InternalID",
                    "hidden": True
                },
                {
                    "_description": "Update calculated column expression",
                    "operation": "update",
                    "table_name": "Sales",
                    "column_name": "TotalAmount",
                    "expression": "[Quantity] * [UnitPrice] * (1 - [Discount])"
                },
                {
                    "_description": "Delete unused column",
                    "operation": "delete",
                    "table_name": "Sales",
                    "column_name": "OldColumn"
                },
                {
                    "_description": "Rename column",
                    "operation": "rename",
                    "table_name": "Customer",
                    "column_name": "CustID",
                    "new_name": "CustomerID"
                }
            ]
        },
        category="metadata",
        sort_order=11
    )

    registry.register(tool)
    logger.info("Registered column_operations handler")
