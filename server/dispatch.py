"""
Central Tool Dispatcher
Routes tool calls to appropriate handlers with error handling
"""
from typing import Dict, Any
import logging
from server.registry import get_registry
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class ToolDispatcher:
    """Dispatches tool calls to registered handlers"""

    def __init__(self):
        self.registry = get_registry()
        self._call_count = 0

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a tool call to its handler

        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments

        Returns:
            Result dictionary from the handler
        """
        self._call_count += 1

        try:
            # Check if tool exists
            if not self.registry.has_tool(tool_name):
                logger.warning(f"Unknown tool requested: {tool_name}")
                return {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}',
                    'error_type': 'unknown_tool',
                    'available_tools': [t.name for t in self.registry.get_all_tools()[:10]]
                }

            # Get handler
            handler = self.registry.get_handler(tool_name)

            # Execute handler
            logger.debug(f"Dispatching tool: {tool_name}")
            result = handler(arguments)

            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.warning(f"Handler for {tool_name} returned non-dict: {type(result)}")
                result = {'success': True, 'result': result}

            return result

        except Exception as e:
            logger.error(f"Error dispatching tool {tool_name}: {e}", exc_info=True)
            return ErrorHandler.handle_unexpected_error(tool_name, e)

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        return {
            'total_calls': self._call_count,
            'registered_tools': len(self.registry.get_all_tools()),
            'categories': self.registry.list_categories()
        }
