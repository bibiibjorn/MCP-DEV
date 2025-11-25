"""
Manager decorators for connection and manager validation.

These decorators eliminate duplicate connection/manager check patterns across operations.
Reduces ~200 lines of duplicated code.
"""
import functools
import logging
from typing import Any, Callable, Dict, Optional, Union

from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def require_connection(func: Callable) -> Callable:
    """
    Decorator to ensure a Power BI connection is active before executing an operation.

    Usage:
        @require_connection
        def _list_items(self, args: Dict[str, Any]) -> Dict[str, Any]:
            # Connection is guaranteed to be active here
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        return func(*args, **kwargs)
    return wrapper


def require_manager(manager_attr: str, manager_display_name: Optional[str] = None) -> Callable:
    """
    Decorator to enforce connection and manager availability.

    This decorator:
    1. Checks if the connection is active
    2. Checks if the specified manager is available on connection_state
    3. Injects the manager as 'manager' keyword argument to the function

    Args:
        manager_attr: The attribute name on connection_state (e.g., 'query_executor', 'dax_injector')
        manager_display_name: Optional display name for error messages (defaults to manager_attr)

    Usage:
        @require_manager('query_executor')
        def _list_measures(self, args: Dict[str, Any], manager=None) -> Dict[str, Any]:
            # manager is the query_executor instance
            result = manager.execute_info_query("MEASURES")
            ...

        @require_manager('dax_injector', 'DAX Injector')
        def _create_measure(self, args: Dict[str, Any], manager=None) -> Dict[str, Any]:
            # manager is the dax_injector instance
            return manager.upsert_measure(...)
    """
    display_name = manager_display_name or manager_attr

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Check connection first
            if not connection_state.is_connected():
                return ErrorHandler.handle_not_connected()

            # Get manager from connection state
            manager = getattr(connection_state, manager_attr, None)
            if not manager:
                return ErrorHandler.handle_manager_unavailable(display_name)

            # Inject manager as keyword argument
            kwargs['manager'] = manager
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_managers(*manager_specs: Union[str, tuple]) -> Callable:
    """
    Decorator to enforce connection and multiple manager availability.

    Args:
        *manager_specs: Variable number of manager specifications.
            Each can be either:
            - A string (manager_attr name, injected with same name)
            - A tuple of (manager_attr, injection_name) to inject with a different name

    Usage:
        @require_managers('query_executor', 'dax_injector')
        def _complex_operation(self, args: Dict[str, Any], query_executor=None, dax_injector=None):
            # Both managers are available
            ...

        @require_managers(('query_executor', 'qe'), ('dax_injector', 'di'))
        def _another_operation(self, args: Dict[str, Any], qe=None, di=None):
            # Managers injected with custom names
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Check connection first
            if not connection_state.is_connected():
                return ErrorHandler.handle_not_connected()

            # Check each manager and inject
            for spec in manager_specs:
                if isinstance(spec, tuple):
                    manager_attr, injection_name = spec
                else:
                    manager_attr = spec
                    injection_name = spec

                manager = getattr(connection_state, manager_attr, None)
                if not manager:
                    return ErrorHandler.handle_manager_unavailable(manager_attr)

                kwargs[injection_name] = manager

            return func(*args, **kwargs)
        return wrapper
    return decorator


class ManagerContext:
    """
    Context manager for accessing connection state managers with validation.

    Usage:
        with ManagerContext('query_executor') as qe:
            if qe is None:
                return self.error_result  # Set by context
            result = qe.execute_info_query("TABLES")

    Or using the get() method for inline access:
        qe = ManagerContext.get('query_executor')
        if isinstance(qe, dict):  # Error response
            return qe
        result = qe.execute_info_query("TABLES")
    """

    def __init__(self, manager_attr: str, manager_display_name: Optional[str] = None):
        self.manager_attr = manager_attr
        self.manager_display_name = manager_display_name or manager_attr
        self.manager = None
        self.error_result = None

    def __enter__(self):
        if not connection_state.is_connected():
            self.error_result = ErrorHandler.handle_not_connected()
            return None

        self.manager = getattr(connection_state, self.manager_attr, None)
        if not self.manager:
            self.error_result = ErrorHandler.handle_manager_unavailable(self.manager_display_name)
            return None

        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager = None
        return False  # Don't suppress exceptions

    @staticmethod
    def get(manager_attr: str, manager_display_name: Optional[str] = None) -> Union[Any, Dict[str, Any]]:
        """
        Get a manager with validation, returning error dict if unavailable.

        Args:
            manager_attr: The attribute name on connection_state
            manager_display_name: Optional display name for error messages

        Returns:
            The manager instance if available, or an error dict if not

        Usage:
            qe = ManagerContext.get('query_executor')
            if isinstance(qe, dict):  # Error response
                return qe
            result = qe.execute_info_query("TABLES")
        """
        display_name = manager_display_name or manager_attr

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        manager = getattr(connection_state, manager_attr, None)
        if not manager:
            return ErrorHandler.handle_manager_unavailable(display_name)

        return manager


def get_manager_or_error(manager_attr: str, manager_display_name: Optional[str] = None) -> Union[Any, Dict[str, Any]]:
    """
    Helper function to get a manager with connection validation.

    Returns the manager if available, or an error dict if not.

    Args:
        manager_attr: The attribute name on connection_state
        manager_display_name: Optional display name for error messages

    Returns:
        The manager instance if available, or an error dict if not

    Usage:
        qe = get_manager_or_error('query_executor')
        if isinstance(qe, dict):  # Error response
            return qe
        result = qe.execute_info_query("TABLES")
    """
    return ManagerContext.get(manager_attr, manager_display_name)


def check_connection_and_manager(manager_attr: str, manager_display_name: Optional[str] = None) -> tuple[bool, Optional[Any], Optional[Dict[str, Any]]]:
    """
    Check connection and manager availability, returning a tuple.

    Returns:
        (success, manager, error_response)
        - If successful: (True, manager_instance, None)
        - If failed: (False, None, error_dict)

    Usage:
        success, qe, error = check_connection_and_manager('query_executor')
        if not success:
            return error
        result = qe.execute_info_query("TABLES")
    """
    display_name = manager_display_name or manager_attr

    if not connection_state.is_connected():
        return (False, None, ErrorHandler.handle_not_connected())

    manager = getattr(connection_state, manager_attr, None)
    if not manager:
        return (False, None, ErrorHandler.handle_manager_unavailable(display_name))

    return (True, manager, None)
