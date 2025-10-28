# Experimental Features

This directory contains experimental code that is not yet integrated into the main codebase.

## manager_registry.py

**Status**: Experimental dependency injection pattern

**Purpose**: Provides a registry-based dependency injection container for lazy initialization of managers with explicit dependency declarations.

**Why it's here**: Well-implemented but not currently used in the codebase. Represents a potential future refactoring to eliminate tight coupling in connection_state.py.

**Future integration**:
- Could replace the manual initialization pattern in `core/infrastructure/connection_state.py`
- Would enable more flexible testing with mock managers
- Provides circular dependency detection

**Example usage** (not active):
```python
registry = ManagerRegistry()

# Register managers with dependencies
registry.register('query_executor',
                 lambda ctx: OptimizedQueryExecutor(ctx.connection))

registry.register('performance_analyzer',
                 lambda ctx, query_executor: PerformanceAnalyzer(ctx.connection, query_executor),
                 dependencies=['query_executor'])

# Get manager (lazy initialization)
context = ConnectionContext(connection, connection_string)
query_executor = registry.get('query_executor', context)
```

**Decision needed**:
- Integrate it properly (requires refactoring connection_state.py)
- Delete if not part of roadmap
- Keep as experimental for future consideration
