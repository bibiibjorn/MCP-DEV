"""
Relationship Operations Handler
Unified handler for all relationship operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.operations.relationship_operations import RelationshipOperationsHandler

logger = logging.getLogger(__name__)

# Create singleton instance
_relationship_ops_handler = RelationshipOperationsHandler()

def handle_relationship_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified relationship operations"""
    return _relationship_ops_handler.execute(args)

def register_relationship_operations_handler(registry):
    """Register relationship operations handler"""

    tool = ToolDefinition(
        name="relationship_operations",
        description="Unified relationship operations: list, get, find, and CRUD (create/update/delete/rename/activate/deactivate)",
        handler=handle_relationship_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["list", "get", "find", "create", "update", "delete", "activate", "deactivate"],
                    "description": "Operation to perform on relationships"
                },
                "relationship_name": {
                    "type": "string",
                    "description": "Relationship name (required for: get, update, delete, rename, activate, deactivate)"
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name to find relationships for (required for: find operation)"
                },
                "from_table": {
                    "type": "string",
                    "description": "Source table name (required for: create)"
                },
                "from_column": {
                    "type": "string",
                    "description": "Source column name (required for: create)"
                },
                "to_table": {
                    "type": "string",
                    "description": "Target table name (required for: create)"
                },
                "to_column": {
                    "type": "string",
                    "description": "Target column name (required for: create)"
                },
                "name": {
                    "type": "string",
                    "description": "Relationship name (optional for: create - auto-generated if not provided)"
                },
                "from_cardinality": {
                    "type": "string",
                    "enum": ["One", "Many"],
                    "description": "Source cardinality (optional for: create, default: Many)",
                    "default": "Many"
                },
                "to_cardinality": {
                    "type": "string",
                    "enum": ["One", "Many"],
                    "description": "Target cardinality (optional for: create, default: One)",
                    "default": "One"
                },
                "cross_filtering_behavior": {
                    "type": "string",
                    "enum": ["OneDirection", "BothDirections", "Automatic"],
                    "description": "Cross-filtering direction (optional for: create/update, default: OneDirection)",
                    "default": "OneDirection"
                },
                "is_active": {
                    "type": "boolean",
                    "description": "Whether relationship is active (optional for: create/update, default: True)"
                },
                "new_name": {
                    "type": "string",
                    "description": "New relationship name (optional for: update)"
                },
                "active_only": {
                    "type": "boolean",
                    "description": "Only return active relationships (for list operation)",
                    "default": False
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
        sort_order=5
    )

    registry.register(tool)
    logger.info("Registered relationship_operations handler")
