"""
Error handling decorators for consistent error handling.

These decorators consolidate duplicate try/except patterns.
Reduces ~90 lines of duplicated code.
"""
import functools
import logging
from typing import Any, Callable, Dict, Optional

from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def handle_operation_errors(operation_name: str) -> Callable:
    """
    Decorator to handle common error patterns with logging.

    This wraps the function in a try/except and returns proper error responses
    while logging the error details.

    Args:
        operation_name: Name of the operation for logging and error messages

    Usage:
        @handle_operation_errors('list_measures')
        def _list_measures(self, args: Dict[str, Any]) -> Dict[str, Any]:
            # If any exception occurs, it will be caught, logged, and
            # returned as a proper error response
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                return ErrorHandler.handle_unexpected_error(operation_name, e)
        return wrapper
    return decorator


def handle_query_errors(query_type: str) -> Callable:
    """
    Decorator specifically for query execution with detailed error handling.

    Args:
        query_type: Type of query for logging (e.g., 'DAX', 'DMV', 'INFO')

    Usage:
        @handle_query_errors('DAX')
        def execute_dax(self, query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                return func(*args, **kwargs)
            except ConnectionError as e:
                logger.error(f"Connection error during {query_type} query: {e}")
                return ErrorHandler.handle_connection_error(e)
            except ValueError as e:
                logger.error(f"Value error during {query_type} query: {e}")
                return ErrorHandler.handle_validation_error(e)
            except Exception as e:
                logger.error(f"Error executing {query_type} query: {e}", exc_info=True)
                return ErrorHandler.handle_unexpected_error(f'{query_type}_query', e)
        return wrapper
    return decorator


def log_operation(operation_name: str, log_args: bool = False) -> Callable:
    """
    Decorator to add logging for operation entry/exit.

    Args:
        operation_name: Name of the operation for logging
        log_args: Whether to log the arguments (be careful with sensitive data)

    Usage:
        @log_operation('create_measure', log_args=True)
        def _create_measure(self, args: Dict[str, Any]):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if log_args:
                # Try to get args from kwargs or positional args
                call_args = kwargs.get('args', args[1] if len(args) > 1 else {})
                logger.info(f"[{operation_name}] Starting with args: {call_args}")
            else:
                logger.info(f"[{operation_name}] Starting")

            try:
                result = func(*args, **kwargs)
                success = isinstance(result, dict) and result.get('success', True)
                if success:
                    logger.info(f"[{operation_name}] Completed successfully")
                else:
                    error = result.get('error', 'Unknown error') if isinstance(result, dict) else 'Unknown error'
                    logger.warning(f"[{operation_name}] Completed with error: {error}")
                return result
            except Exception as e:
                logger.error(f"[{operation_name}] Failed with exception: {e}", exc_info=True)
                raise

        return wrapper
    return decorator


def with_error_context(context: Dict[str, Any]) -> Callable:
    """
    Decorator to add context to error responses.

    Args:
        context: Additional context to include in error responses

    Usage:
        @with_error_context({'component': 'measure_operations', 'version': '2.0'})
        def _create_measure(self, args: Dict[str, Any]):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                result = func(*args, **kwargs)

                # If result is an error, add context
                if isinstance(result, dict) and not result.get('success', True):
                    if 'context' not in result:
                        result['context'] = {}
                    result['context'].update(context)

                return result
            except Exception as e:
                error_result = ErrorHandler.handle_unexpected_error(func.__name__, e)
                if 'context' not in error_result:
                    error_result['context'] = {}
                error_result['context'].update(context)
                return error_result

        return wrapper
    return decorator


def retry_on_connection_error(max_retries: int = 1, delay_seconds: float = 0.5) -> Callable:
    """
    Decorator to retry operations on connection errors.

    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Delay between retries

    Usage:
        @retry_on_connection_error(max_retries=2)
        def _execute_query(self, query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            import time
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(f"Connection error in {func.__name__}, retrying ({attempt + 1}/{max_retries})...")
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"Connection error in {func.__name__} after {max_retries} retries: {e}")

            return ErrorHandler.handle_connection_error(last_error)

        return wrapper
    return decorator


def wrap_result(include_success: bool = True) -> Callable:
    """
    Decorator to ensure result is always in standard format.

    Args:
        include_success: Whether to add 'success': True for non-dict results

    Usage:
        @wrap_result()
        def _get_data(self):
            return some_list  # Will be wrapped as {'success': True, 'data': some_list}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            result = func(*args, **kwargs)

            if isinstance(result, dict) and 'success' in result:
                return result

            if include_success:
                return {
                    'success': True,
                    'data': result
                }
            else:
                return result if isinstance(result, dict) else {'data': result}

        return wrapper
    return decorator


class OperationErrorHandler:
    """
    Context manager for operation error handling.

    Usage:
        with OperationErrorHandler('list_measures') as handler:
            result = self._do_something()
            if handler.check_error(result):
                return handler.error_response

            # Continue with more operations...
            return result
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.error_response: Optional[Dict[str, Any]] = None

    def __enter__(self):
        logger.debug(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error in {self.operation_name}: {exc_val}", exc_info=True)
            self.error_response = ErrorHandler.handle_unexpected_error(self.operation_name, exc_val)
            return True  # Suppress the exception, error_response is set
        return False

    def check_error(self, result: Dict[str, Any]) -> bool:
        """Check if result is an error and store it."""
        if isinstance(result, dict) and not result.get('success', True):
            self.error_response = result
            return True
        return False

    def handle_exception(self, e: Exception) -> Dict[str, Any]:
        """Handle an exception and return error response."""
        logger.error(f"Error in {self.operation_name}: {e}", exc_info=True)
        self.error_response = ErrorHandler.handle_unexpected_error(self.operation_name, e)
        return self.error_response


def combine_decorators(*decorators: Callable) -> Callable:
    """
    Utility to combine multiple decorators into one.

    Args:
        *decorators: Decorators to combine (applied bottom-up)

    Usage:
        @combine_decorators(
            handle_operation_errors('create_measure'),
            log_operation('create_measure'),
            require_manager('dax_injector')
        )
        def _create_measure(self, args, manager=None):
            ...
    """
    def decorator(func: Callable) -> Callable:
        for dec in reversed(decorators):
            func = dec(func)
        return func
    return decorator
