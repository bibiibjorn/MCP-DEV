"""
Calculation Group Operations Handler
Unified handler for all calculation group operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.calculation_group_operations import CalculationGroupOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_calc_group_ops_handler = CalculationGroupOperationsHandler()

def handle_calculation_group_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified calculation group operations"""
    return _calc_group_ops_handler.execute(args)

def register_calculation_group_operations_handler(registry):
    """Register calculation group operations handler"""

    tool = ToolDefinition(
        name="calculation_group_operations",
        description="Unified calculation group operations: list, create, delete, list_items, and CRUD for groups and items",
        handler=handle_calculation_group_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "create", "delete", "list_items"],  # Add more as implemented
                    "description": "Operation to perform on calculation groups"
                },
                "group_name": {
                    "type": "string",
                    "description": "Calculation group name (required for most operations)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New group name (required for: rename)"
                },
                "items": {
                    "type": "array",
                    "description": "Calculation items (for create operation)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "expression": {"type": "string"},
                            "ordinal": {"type": "integer"}
                        }
                    }
                },
                "description": {
                    "type": "string",
                    "description": "Group description (optional for: create, update)"
                },
                "precedence": {
                    "type": "integer",
                    "description": "Precedence value (optional for: create - auto-assigned if not provided)"
                },
                "item_name": {
                    "type": "string",
                    "description": "Calculation item name (required for: update_item, delete_item)"
                },
                "item_order": {
                    "type": "array",
                    "description": "Array of item names in desired order (required for: reorder_items)",
                    "items": {"type": "string"}
                }
            },
            "required": ["operation"]
        },
        category="model_operations",
        sort_order=20
    )

    registry.register(tool)
    logger.info("Registered calculation_group_operations handler")
