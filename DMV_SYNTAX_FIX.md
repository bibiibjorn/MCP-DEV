# DMV Query Syntax Fix

## Problem
Three tools were failing with "syntax incorrect" errors when querying `$SYSTEM.*` DMV tables:
- `get_data_sources` - Failed with: "The syntax for 'DISCOVER_DATASOURCES' is incorrect"
- `get_m_expressions` - Failed with: "The syntax for 'TMSCHEMA_EXPRESSIONS' is incorrect"
- `analyze_data_freshness` - Failed with: "The syntax for 'DISCOVER_STORAGE_TABLES' is incorrect"

### Example of the Bug
```dax
-- BROKEN: Cannot directly wrap $SYSTEM.* DMVs in SELECTCOLUMNS
EVALUATE
SELECTCOLUMNS(
    $SYSTEM.DISCOVER_DATASOURCES,
    "DataSourceID", [DataSourceID],
    "Name", [Name]
)
```

## Root Cause
In Power BI/SSAS, `$SYSTEM.*` DMV tables cannot be directly used inside DAX table functions like `SELECTCOLUMNS` or `FILTER`. They must be:
1. Queried directly: `EVALUATE $SYSTEM.DMV_NAME`, OR
2. Materialized first using `TOPN()` before wrapping in other functions

This is a limitation of how DMV tables work in the Analysis Services engine.

## Solution Implemented

### Fix Pattern
Wrap all `$SYSTEM.*` DMV references with `TOPN(999999, ...)` to materialize the DMV table before applying other DAX functions.

### 1. Fixed get_data_sources
**File:** [pbixray_server_enhanced.py:228](src/pbixray_server_enhanced.py#L228)

**Before:**
```dax
EVALUATE
SELECTCOLUMNS(
    $SYSTEM.DISCOVER_DATASOURCES,  -- BROKEN
    "DataSourceID", [DataSourceID],
    "Name", [Name],
    "Description", [Description],
    "Type", [Type]
)
```

**After:**
```dax
EVALUATE
SELECTCOLUMNS(
    TOPN(999999, $SYSTEM.DISCOVER_DATASOURCES),  -- FIXED
    "DataSourceID", [DataSourceID],
    "Name", [Name],
    "Description", [Description],
    "Type", [Type]
)
```

### 2. Fixed get_m_expressions
**File:** [pbixray_server_enhanced.py:239](src/pbixray_server_enhanced.py#L239)

**Before:**
```dax
EVALUATE
SELECTCOLUMNS(
    $SYSTEM.TMSCHEMA_EXPRESSIONS,  -- BROKEN
    "Name", [Name],
    "Expression", [Expression],
    "Kind", [Kind]
)
```

**After:**
```dax
EVALUATE
SELECTCOLUMNS(
    TOPN(999999, $SYSTEM.TMSCHEMA_EXPRESSIONS),  -- FIXED
    "Name", [Name],
    "Expression", [Expression],
    "Kind", [Kind]
)
```

### 3. Fixed analyze_data_freshness
**File:** [model_validator.py:314](core/model_validator.py#L314)

**Before:**
```dax
EVALUATE
SELECTCOLUMNS(
    FILTER(
        $SYSTEM.DISCOVER_STORAGE_TABLES,  -- BROKEN
        [TABLE_TYPE] = "TABLE"
    ),
    "Table", [DIMENSION_NAME],
    "LastRefresh", [LAST_DATA_UPDATE]
)
```

**After:**
```dax
EVALUATE
SELECTCOLUMNS(
    FILTER(
        TOPN(999999, $SYSTEM.DISCOVER_STORAGE_TABLES),  -- FIXED
        [TABLE_TYPE] = "TABLE"
    ),
    "Table", [DIMENSION_NAME],
    "LastRefresh", [LAST_DATA_UPDATE]
)
```

## Why TOPN(999999, ...) Works
The `TOPN()` function forces the DAX engine to:
1. Materialize the DMV table into memory
2. Return it as a regular DAX table
3. Allow it to be used with other DAX functions like `SELECTCOLUMNS` and `FILTER`

The large number (999999) ensures all rows are returned, effectively materializing the entire DMV.

## Impact
- ✅ `get_data_sources` now works - returns data source information
- ✅ `get_m_expressions` now works - returns M/Power Query expressions
- ✅ `analyze_data_freshness` now works - returns table refresh timestamps

## Alternative Approach (Not Used)
We could have queried DMVs directly and filtered in Python:
```dax
EVALUATE $SYSTEM.DISCOVER_DATASOURCES
```
Then filter/select columns in application code.

However, the TOPN approach is better because:
- ✅ Filters are applied in DAX (more efficient)
- ✅ Reduces data transfer over the wire
- ✅ Consistent with other query patterns in the codebase

## Testing
All three tools now work correctly:
```
get_data_sources()          # Returns data sources
get_m_expressions()         # Returns M expressions
analyze_data_freshness()    # Returns refresh times
```

## Related Fixes
This fix complements:
- [DMV_TABLEID_FIX.md](DMV_TABLEID_FIX.md) - Fixed TableID type mismatches
- [COLUMN_TYPE_FIX.md](COLUMN_TYPE_FIX.md) - Fixed Column Type field mismatches
