# Tool Routing Quick Reference

## When User Asks About... → Use This Tool

### Tables
- **"List tables"** → `table_operations` with `operation='list'`
- **"Describe table X"** → `table_operations` with `operation='describe'` + `table_name='X'`
- **"Preview table X data"** → `table_operations` with `operation='preview'` + `table_name='X'`

### Columns
- **"List columns"** → `column_operations` with `operation='list'`
- **"List calculated columns"** → `column_operations` with `operation='list'` + `column_type='calculated'`
- **"Column stats for X"** → `column_operations` with `operation='statistics'` + `table_name` + `column_name`
- **"Top values in column X"** → `column_operations` with `operation='distribution'` + `table_name` + `column_name`

### Measures
- **"List measures"** → `measure_operations` with `operation='list'`
  - Returns measure NAMES only (no DAX)
- **"Show measure X"** / **"Get DAX for measure X"** → `measure_operations` with `operation='get'` + `table_name` + `measure_name`
  - Returns FULL details INCLUDING DAX expression
- **"Create measure"** → `measure_operations` with `operation='create'` + required fields
- **"Delete measure X"** → `measure_operations` with `operation='delete'` + `table_name` + `measure_name`

### Search
- **"Find objects named X"** → `search_objects` with `pattern='*X*'`
  - Searches object NAMES only
- **"Find measures using CALCULATE"** → `search_string` with `search_text='CALCULATE'` + `search_in_expression=True`
  - Searches inside DAX expressions

## Critical Distinctions

### Measure List vs Get
```
❌ WRONG: User asks "Show me measure X" → measure_operations(operation='list')
   Problem: list returns names only, no DAX

✅ CORRECT: User asks "Show me measure X" → measure_operations(operation='get', table_name='...', measure_name='X')
   Returns: Full measure details WITH DAX expression
```

### Search Objects vs Search String
```
❌ WRONG: User asks "Find measures using SUM" → search_objects(pattern='SUM')
   Problem: Searches names only, not DAX code

✅ CORRECT: User asks "Find measures using SUM" → search_string(search_text='SUM', search_in_expression=True)
   Searches: Inside DAX expressions
```

### Table List vs Describe
```
❌ WRONG: User asks "Tell me about table Sales" → table_operations(operation='list')
   Problem: Returns all tables, not details for one

✅ CORRECT: User asks "Tell me about table Sales" → table_operations(operation='describe', table_name='Sales')
   Returns: Columns, measures, relationships for Sales table
```

## Common Patterns

| User Intent | Tool | Operation | Required Params |
|------------|------|-----------|----------------|
| List all X | `{x}_operations` | `list` | None |
| Get details for X | `{x}_operations` | `get` or `describe` | Name of X |
| Show data/values | `table_operations` or `column_operations` | `preview` or `distribution` | table_name, etc. |
| Create/modify X | `{x}_operations` | `create`/`update`/`delete` | Depends on operation |
| Search by name | `search_objects` | N/A | `pattern` |
| Search in DAX | `search_string` | N/A | `search_text` |

---
**Version:** 1.0 | **Last Updated:** 2025-11-19
