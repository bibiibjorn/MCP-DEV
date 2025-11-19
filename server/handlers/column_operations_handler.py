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
        description="Unified column operations: list (all/data/calculated), statistics, distribution, and CRUD",
        handler=handle_column_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "statistics", "distribution", "get", "create", "update", "delete", "rename"],
                    "description": "Operation to perform on columns"
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
                }
            },
            "required": ["operation"]
        },
        category="metadata",
        sort_order=3
    )

    registry.register(tool)
    logger.info("Registered column_operations handler")
