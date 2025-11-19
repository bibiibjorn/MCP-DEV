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
                "new_name": {
                    "type": "string",
                    "description": "New relationship name (required for: rename)"
                },
                "definition": {
                    "type": "object",
                    "description": "Relationship definition (required for: create, update)",
                    "properties": {
                        "from_table": {"type": "string"},
                        "from_column": {"type": "string"},
                        "to_table": {"type": "string"},
                        "to_column": {"type": "string"},
                        "cardinality": {
                            "type": "string",
                            "enum": ["OneToMany", "ManyToOne", "OneToOne", "ManyToMany"]
                        },
                        "cross_filtering_behavior": {
                            "type": "string",
                            "enum": ["OneDirection", "BothDirections"]
                        },
                        "is_active": {"type": "boolean"}
                    }
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
