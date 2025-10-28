"""
Error handling utilities for PBIXRay MCP Server
"""

import functools
import logging
from typing import Any, Dict, Callable, Optional
from core.validation.error_response import ErrorResponse

logger = logging.getLogger(__name__)


def safe_tool_execution(fallback_error: str = "Tool not available"):
    """
    Decorator to handle common tool execution patterns with proper error handling.
    
    Args:
        fallback_error: Default error message when tool is not available
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                result = func(*args, **kwargs)
                
                # Ensure result is properly formatted
                if not isinstance(result, dict):
                    return {
                        'success': True,
                        'data': result
                    }
                
                return result
                
            except ConnectionError as e:
                logger.error(f"Connection error in {func.__name__}: {e}")
                return ErrorResponse(
                    error=f'Connection error: {str(e)}',
                    error_type='connection_error',
                    suggestions=[
                        'Check Power BI Desktop connection',
                        'Verify instance is still running'
                    ]
                ).to_dict()
            except ValueError as e:
                logger.error(f"Value error in {func.__name__}: {e}")
                return ErrorResponse(
                    error=f'Invalid parameter: {str(e)}',
                    error_type='parameter_error'
                ).to_dict()
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                return ErrorResponse(
                    error=f'Unexpected error: {str(e)}',
                    error_type='unexpected_error',
                    context={'tool_name': func.__name__}
                ).to_dict()
        
        return wrapper
    return decorator


def require_connection(func: Callable) -> Callable:
    """
    Decorator to ensure a Power BI connection is active before executing a tool.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'connection_manager') or not self.connection_manager.is_connected():
            return ErrorResponse(
                error='Not connected to Power BI Desktop',
                error_type='not_connected',
                suggestions=[
                    'Use detect_powerbi_desktop to find instances',
                    'Use connect_to_powerbi to establish connection'
                ]
            ).to_dict()
        
        return func(self, *args, **kwargs)
    
    return wrapper


def validate_manager(manager_name: str, error_message: Optional[str] = None):
    """
    Decorator to validate that a required manager is available.
    
    Args:
        manager_name: Name of the manager attribute to check
        error_message: Custom error message if manager is not available
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            manager = getattr(self, manager_name, None)
            if not manager:
                return ErrorResponse(
                    error=error_message or f'{manager_name} not available',
                    error_type='manager_unavailable',
                    context={'required_manager': manager_name}
                ).to_dict()
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


class ErrorHandler:
    """
    Centralized error handling for common patterns.
    """
    
    @staticmethod
    def handle_manager_unavailable(manager_name: str) -> Dict[str, Any]:
        """Standard response when a manager is not available."""
        return ErrorResponse(
            error=f'{manager_name} not available',
            error_type='manager_unavailable',
            suggestions=[
                'Ensure connection to Power BI Desktop is established',
                'Check if all required services are initialized'
            ],
            context={'required_manager': manager_name}
        ).to_dict()
    
    @staticmethod
    def handle_not_connected() -> Dict[str, Any]:
        """Standard response when there is no active connection."""
        return ErrorResponse(
            error='Not connected to Power BI Desktop',
            error_type='not_connected',
            suggestions=[
                'Use detect_powerbi_desktop to find instances',
                'Use connect_to_powerbi to establish connection'
            ]
        ).to_dict()

    @staticmethod
    def handle_unknown_tool(tool_name: str) -> Dict[str, Any]:
        """Standard response for unknown tool invocations."""
        return ErrorResponse(
            error=f'Unknown tool: {tool_name}',
            error_type='unknown_tool',
            context={'tool_name': tool_name}
        ).to_dict()

    @staticmethod
    def handle_connection_error(error: Exception) -> Dict[str, Any]:
        """Standard response for connection errors."""
        return ErrorResponse(
            error=f'Connection error: {str(error)}',
            error_type='connection_error',
            suggestions=[
                'Verify Power BI Desktop is running',
                'Check network connectivity',
                'Try reconnecting to the instance'
            ]
        ).to_dict()
    
    @staticmethod
    def handle_validation_error(error: Exception) -> Dict[str, Any]:
        """Standard response for validation errors."""
        return ErrorResponse(
            error=f'Validation error: {str(error)}',
            error_type='validation_error'
        ).to_dict()
    
    @staticmethod
    def handle_unexpected_error(tool_name: str, error: Exception) -> Dict[str, Any]:
        """Standard response for unexpected errors with tool context."""
        return ErrorResponse(
            error=f'Unexpected error: {str(error)}',
            error_type='unexpected_error',
            context={'tool_name': tool_name}
        ).to_dict()

    @staticmethod
    def wrap_result(data: Any, success: bool = True) -> Dict[str, Any]:
        """Wrap raw data in standard response format."""
        if isinstance(data, dict) and 'success' in data:
            return data
        
        return {
            'success': success,
            'data': data
        }