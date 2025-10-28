# Execution Module

This directory contains helper modules that support query execution operations.

## Purpose

These modules provide specialized utilities that extend the functionality of `core/infrastructure/query_executor.py`:

- **dmv_helper.py** - DMV query construction and execution helpers
- **query_cache.py** - Query result caching implementation
- **search_helper.py** - Search and filter helpers for metadata queries
- **table_mapper.py** - Table ID to table name mapping utilities
- **tom_fallback.py** - TOM/AMO fallback utilities when DMV queries are blocked

## Architecture Note

These modules work in conjunction with `core/infrastructure/query_executor.py` (the main query execution engine). They are separated out to keep the main query executor focused and maintainable while providing modular helper functions.

## Status

**Active**: All modules are actively used by the query executor and other parts of the system.

**Note**: `dax_executor.py` was removed as it was an empty stub. Actual DAX execution happens in `core/infrastructure/query_executor.py`.
