"""Manager registry pattern for dependency injection."""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ManagerRegistry:
    """
    Registry for lazy initialization of managers with dependency injection.

    This pattern eliminates the tight coupling in connection_state.py by allowing
    managers to be registered with their dependencies explicitly declared.
    """

    def __init__(self):
        self._factories: Dict[str, Tuple[Callable, List[str]]] = {}
        self._instances: Dict[str, Any] = {}
        self._initializing: set = set()  # Circular dependency detection

    def register(self, name: str, factory: Callable, dependencies: Optional[List[str]] = None):
        """
        Register a manager factory with its dependencies.

        Args:
            name: Manager name (e.g., 'query_executor')
            factory: Callable that creates the manager instance
            dependencies: List of other manager names this manager depends on

        Example:
            registry.register('query_executor',
                            lambda ctx: DaxExecutor(ctx.connection))

            registry.register('performance_analyzer',
                            lambda ctx, query_executor: PerformanceAnalyzer(ctx.connection, query_executor),
                            dependencies=['query_executor'])
        """
        self._factories[name] = (factory, dependencies or [])
        logger.debug(f"Registered manager '{name}' with dependencies: {dependencies or []}")

    def get(self, name: str, context: Any) -> Any:
        """
        Get or create manager instance (lazy initialization).

        Args:
            name: Manager name
            context: Connection context with connection info

        Returns:
            Manager instance

        Raises:
            RuntimeError: If circular dependency detected
            KeyError: If manager not registered
        """
        if name in self._instances:
            return self._instances[name]

        if name not in self._factories:
            raise KeyError(f"Manager '{name}' not registered")

        if name in self._initializing:
            raise RuntimeError(f"Circular dependency detected while initializing '{name}'")

        try:
            self._initializing.add(name)
            self._instances[name] = self._create(name, context)
            return self._instances[name]
        finally:
            self._initializing.discard(name)

    def _create(self, name: str, context: Any) -> Any:
        """Create manager instance with dependency injection."""
        factory, deps = self._factories[name]

        # Recursively get dependencies
        dep_instances = {}
        for dep_name in deps:
            dep_instances[dep_name] = self.get(dep_name, context)

        # Call factory with context and dependencies
        try:
            if dep_instances:
                return factory(context, **dep_instances)
            else:
                return factory(context)
        except Exception as e:
            logger.error(f"Failed to create manager '{name}': {e}", exc_info=True)
            raise

    def has(self, name: str) -> bool:
        """Check if manager is registered."""
        return name in self._factories

    def clear(self):
        """Clear all instances (keeps registrations)."""
        self._instances.clear()
        self._initializing.clear()

    def reset(self):
        """Clear both instances and registrations."""
        self._factories.clear()
        self._instances.clear()
        self._initializing.clear()

    def list_registered(self) -> List[str]:
        """List all registered manager names."""
        return list(self._factories.keys())

    def list_initialized(self) -> List[str]:
        """List all initialized manager names."""
        return list(self._instances.keys())


class ConnectionContext:
    """Context object passed to manager factories."""

    def __init__(self, connection, connection_string: str = ""):
        self.connection = connection
        self.connection_string = connection_string


__all__ = ['ManagerRegistry', 'ConnectionContext']
