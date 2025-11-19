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
        description="Unified measure operations: list, get, create, update, delete, rename, move, and bulk operations",
        handler=handle_measure_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "get", "create", "update", "delete", "rename", "move"],
                    "description": "Operation to perform on measures"
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
