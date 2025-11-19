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
            "Unified measure operations handler. USE THIS WHEN:\n"
            "• User asks 'list measures' / 'show all measures' / 'what measures exist' → operation='list'\n"
            "• User asks 'list measures in table X' → operation='list' with table_name='X'\n"
            "• User asks 'get measure X' / 'show measure X details' / 'show me the DAX for measure X' / 'what's the formula for X' → operation='get' (requires table_name and measure_name) - THIS RETURNS THE DAX EXPRESSION\n"
            "• User asks 'create measure' / 'add measure' → operation='create' (requires table_name, measure_name, expression)\n"
            "• User asks 'update measure' / 'modify measure' → operation='update' (requires table_name, measure_name, expression)\n"
            "• User asks 'delete measure' / 'remove measure' → operation='delete' (requires table_name, measure_name)\n"
            "\n"
            "IMPORTANT:\n"
            "• operation='list' returns measure NAMES only (NO DAX expressions)\n"
            "• operation='get' returns FULL measure details INCLUDING the DAX expression\n"
            "• If user wants to see the DAX formula/expression, ALWAYS use operation='get'\n"
            "\n"
            "OPERATIONS:\n"
            "• list: Returns measure names (optionally filtered by table)\n"
            "• get: Returns full measure metadata INCLUDING DAX expression - USE THIS for 'show me measure X'\n"
            "• create/update: Create or modify measures with DAX expressions\n"
            "• delete/rename/move: Modify measure organization"
        ),
        handler=handle_measure_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete", "rename", "move"],
                    "description": (
                        "Operation to perform:\n"
                        "• 'list' - List measures (use when: 'show measures', 'list measures', 'what measures exist') - returns NAMES only\n"
                        "• 'get' - Get measure details WITH DAX (use when: 'show measure X', 'get measure X details', 'show me the DAX for X') - returns FULL details including DAX expression\n"
                        "• 'create' - Create measure (use when: 'create measure X', 'add measure')\n"
                        "• 'update' - Update measure (use when: 'update measure X', 'change measure X')\n"
                        "• 'delete' - Delete measure (use when: 'delete measure X', 'remove measure X')\n"
                        "• 'rename', 'move' - Reorganize measures"
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
