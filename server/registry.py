"""
Handler Registry System
Manages registration and lookup of tool handlers
"""
from typing import Dict, Callable, Any, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolDefinition:
    """Definition of a tool with its handler"""
    name: str
    description: str
    handler: Callable
    input_schema: Dict[str, Any]
    category: str = "general"
    sort_order: int = 999  # Default to end if not specified

class HandlerRegistry:
    """Central registry for all tool handlers"""

    def __init__(self):
        self._handlers: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        """Register a tool handler"""
        self._handlers[tool_def.name] = tool_def

        # Track by category
        if tool_def.category not in self._categories:
            self._categories[tool_def.category] = []
        self._categories[tool_def.category].append(tool_def.name)

        logger.debug(f"Registered tool: {tool_def.name} (category: {tool_def.category})")

    def get_handler(self, tool_name: str) -> Callable:
        """Get handler function for a tool"""
        if tool_name not in self._handlers:
            raise KeyError(f"Unknown tool: {tool_name}")
        return self._handlers[tool_name].handler

    def get_tool_def(self, tool_name: str) -> ToolDefinition:
        """Get full tool definition"""
        if tool_name not in self._handlers:
            raise KeyError(f"Unknown tool: {tool_name}")
        return self._handlers[tool_name]

    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools"""
        return list(self._handlers.values())

    def get_all_tools_as_mcp(self):
        """Get all tools as MCP Tool objects"""
        from mcp.types import Tool

        tools = []
        # Sort by sort_order, then by name
        sorted_defs = sorted(self._handlers.values(), key=lambda x: (x.sort_order, x.name))

        for tool_def in sorted_defs:
            tools.append(Tool(
                name=tool_def.name,
                description=tool_def.description,
                inputSchema=tool_def.input_schema
            ))
        return tools

    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """Get tools in a specific category"""
        tool_names = self._categories.get(category, [])
        return [self._handlers[name] for name in tool_names if name in self._handlers]

    def list_categories(self) -> List[str]:
        """List all categories"""
        return list(self._categories.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if tool is registered"""
        return tool_name in self._handlers

# Global registry instance
_registry = HandlerRegistry()

def get_registry() -> HandlerRegistry:
    """Get the global handler registry"""
    return _registry
