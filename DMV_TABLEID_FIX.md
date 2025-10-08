# DMV TableID Type Mismatch Fix

## Problem
The `list_columns` tool and other tools were failing with the error:
```
DAX comparison operations do not support comparing values of type Integer with values of type Text.
```

This occurred because the code was comparing `TableID` (an integer field in DMV tables) to table names (strings).

### Example of the Bug
```dax
-- BROKEN: TableID is integer, "_Measures" is string
EVALUATE FILTER(INFO.COLUMNS(), [TableID] = "_Measures")
```

## Root Cause
In Power BI's DMV (Dynamic Management Views):
- `TableID` in `INFO.COLUMNS()` and `INFO.MEASURES()` is an **INTEGER** field
- The code was passing **table names as strings** directly to filter expressions
- DAX cannot compare integers to strings, causing the query to fail

## Solution Implemented

### 1. Added Table Name Lookup Method
Added `_get_table_id_from_name()` method in [query_executor.py:155-179](core/query_executor.py#L155-L179):
- Queries `INFO.TABLES()` to get the numeric `TableID` for a given table name
- Caches table mappings for performance
- Returns `None` if table not found

### 2. Enhanced `execute_info_query()` Method
Updated the method signature to accept `table_name` parameter:
```python
def execute_info_query(
    self,
    function_name: str,
    filter_expr: str = None,
    exclude_columns: List[str] = None,
    table_name: str = None  # NEW PARAMETER
) -> Dict[str, Any]:
```

The method now:
- Accepts table names via `table_name` parameter
- Automatically looks up the numeric `TableID`
- Constructs filter expressions using the numeric ID
- Returns proper error if table not found

### 3. Fixed All Tool Implementations
Updated all tools to use the new `table_name` parameter:

#### [pbixray_server_enhanced.py](src/pbixray_server_enhanced.py):
- `list_columns` (line 261)
- `list_measures` (line 207)
- `describe_table` (lines 211-212)
- `get_measure_details` (line 216)
- `list_calculated_columns` (line 222)

#### [dependency_analyzer.py:88](core/dependency_analyzer.py#L88):
- Fixed measure lookup to use `table_name` parameter

#### [model_exporter.py:296](core/model_exporter.py#L296):
- Fixed column retrieval for documentation export

#### [performance_optimizer.py:94](core/performance_optimizer.py#L94):
- Fixed cardinality analysis column retrieval

## Before and After

### Before (BROKEN)
```python
# This failed with type mismatch error
cols = query_executor.execute_info_query("COLUMNS", f'[TableID] = "{table}"')
```

Generated DAX:
```dax
EVALUATE FILTER(INFO.COLUMNS(), [TableID] = "_Measures")
-- ERROR: Cannot compare integer to string!
```

### After (FIXED)
```python
# Now works correctly
cols = query_executor.execute_info_query("COLUMNS", table_name=table)
```

Generated DAX:
```dax
-- First lookup: _Measures -> TableID = 100
EVALUATE FILTER(INFO.COLUMNS(), [TableID] = 100)
-- SUCCESS: Comparing integer to integer
```

## Impact
- ✅ Fixes all `list_columns` queries
- ✅ Fixes all `describe_table` queries
- ✅ Fixes all `get_measure_details` queries
- ✅ Fixes all `list_calculated_columns` queries
- ✅ Fixes all table-filtered queries across all modules
- ✅ Provides better error messages when table not found
- ✅ Improves performance through table mapping cache

## Testing
The fix resolves the original test case:
```
list_columns(table="_Measures")
```

This now:
1. Looks up "_Measures" -> gets numeric TableID
2. Filters using: `[TableID] = <numeric_id>`
3. Returns columns successfully
