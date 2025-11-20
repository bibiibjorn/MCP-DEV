"""
Measure Operations Handler
Unified handler for all measure operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.measure_operations import MeasureOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_measure_ops_handler = MeasureOperationsHandler()

def handle_measure_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified measure operations"""
    return _measure_ops_handler.execute(args)

def register_measure_operations_handler(registry):
    """Register measure operations handler"""

    tool = ToolDefinition(
        name="measure_operations",
        description=(
            "Unified measure operations handler supporting ALL CRUD operations.\n"
            "\n"
            "━━━ READ OPERATIONS ━━━\n"
            "• list: List measure names (optional table filter) → operation='list'\n"
            "  NOTE: Returns NAMES only, NO DAX expressions\n"
            "  Example: {'operation': 'list', 'table_name': 'Sales'}\n"
            "\n"
            "• get: Get measure details WITH DAX expression → operation='get', table_name=X, measure_name=Y\n"
            "  Returns: Full metadata INCLUDING DAX expression - USE THIS to see formulas!\n"
            "  Example: {'operation': 'get', 'table_name': 'Sales', 'measure_name': 'Total Revenue'}\n"
            "\n"
            "━━━ CREATE OPERATION ━━━\n"
            "• create: Create new measure → operation='create', table_name=X, measure_name=Y, expression=DAX\n"
            "  Required: table_name, measure_name, expression\n"
            "  Optional: description, format_string, display_folder\n"
            "  Example: {'operation': 'create', 'table_name': 'Sales', 'measure_name': 'Total Revenue', 'expression': 'SUM(Sales[Amount])', 'format_string': '$#,0'}\n"
            "\n"
            "━━━ UPDATE OPERATION ━━━\n"
            "• update: Update existing measure → operation='update', table_name=X, measure_name=Y\n"
            "  Required: table_name, measure_name\n"
            "  Optional: expression, description, format_string, display_folder\n"
            "  Example: {'operation': 'update', 'table_name': 'Sales', 'measure_name': 'Total Revenue', 'expression': 'SUMX(Sales, [Quantity] * [Price])'}\n"
            "\n"
            "━━━ DELETE OPERATION ━━━\n"
            "• delete: Delete measure → operation='delete', table_name=X, measure_name=Y\n"
            "  Required: table_name, measure_name\n"
            "  Example: {'operation': 'delete', 'table_name': 'Sales', 'measure_name': 'Old Measure'}\n"
            "\n"
            "━━━ RENAME OPERATION ━━━\n"
            "• rename: Rename measure → operation='rename', table_name=X, measure_name=Y, new_name=Z\n"
            "  Required: table_name, measure_name, new_name\n"
            "  Example: {'operation': 'rename', 'table_name': 'Sales', 'measure_name': 'Rev', 'new_name': 'Revenue'}\n"
            "\n"
            "━━━ MOVE OPERATION ━━━\n"
            "• move: Move measure to different table → operation='move', table_name=X, measure_name=Y, new_table=Z\n"
            "  Required: table_name, measure_name, new_table\n"
            "  Example: {'operation': 'move', 'table_name': 'Sales', 'measure_name': 'Total Revenue', 'new_table': 'Measures'}\n"
            "\n"
            "USE ALL OPERATIONS AS NEEDED - don't skip CREATE/UPDATE/DELETE/RENAME/MOVE!"
        ),
        handler=handle_measure_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete", "rename", "move"],
                    "description": (
                        "Operation to perform (MUST USE ALL OPERATIONS - don't skip CRUD!):\n"
                        "• 'list' - List measure names (returns NAMES only, no DAX)\n"
                        "• 'get' - Get measure details WITH DAX expression\n"
                        "• 'create' - CREATE new measure (requires: table_name, measure_name, expression; optional: description, format_string, display_folder)\n"
                        "• 'update' - UPDATE measure properties (requires: table_name, measure_name; optional: expression, description, format_string, display_folder)\n"
                        "• 'delete' - DELETE measure (requires: table_name, measure_name)\n"
                        "• 'rename' - RENAME measure (requires: table_name, measure_name, new_name)\n"
                        "• 'move' - MOVE measure to different table (requires: table_name, measure_name, new_table)"
                    )
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (optional for list, required for other operations)"
                },
                "measure_name": {
                    "type": "string",
                    "description": "Measure name (required for: get, update, delete, rename, move)"
                },
                "expression": {
                    "type": "string",
                    "description": "DAX expression (required for: create, update)"
                },
                "description": {
                    "type": "string",
                    "description": "Measure description (optional for: create, update)"
                },
                "format_string": {
                    "type": "string",
                    "description": "Format string (optional for: create, update)"
                },
                "display_folder": {
                    "type": "string",
                    "description": "Display folder (optional for: create, update)"
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
        sort_order=4
    )

    registry.register(tool)
    logger.info("Registered measure_operations handler")
