# Agentic Routing Guide for MCP-PowerBi-Finvision

This guide helps AI agents understand which tools to use for different user requests.

## Quick Reference Table

| User Intent | Tool to Use | Handler Location |
|------------|-------------|------------------|
| "List all tables" | `list_tables` | metadata_handler.py |
| "Show me table X details" | `describe_table` | metadata_handler.py |
| "List columns" / "What columns are in table X" | `list_columns` | metadata_handler.py |
| "List measures" / "Show all measures" | `list_measures` | metadata_handler.py |
| "Get measure details" / "Show measure X" | `get_measure_details` | metadata_handler.py |
| "List calculated columns" | `list_calculated_columns` | metadata_handler.py |
| "Search for X" / "Find tables/columns/measures matching Y" | `search_objects` | metadata_handler.py |
| "Search in DAX" / "Find measures containing X" | `search_string` | metadata_handler.py |
| "Preview table data" / "Show me sample data" | `preview_table_data` | query_handler.py |
| "Run DAX query" / "Execute DAX" | `run_dax` | query_handler.py |
| "Create/update measure" / "Add measure" | `upsert_measure` | model_operations_handler.py |
| "Delete measure" / "Remove measure" | `delete_measure` | model_operations_handler.py |
| "Analyze model" / "Model overview" | `simple_analysis` | analysis_handler.py |
| "Full analysis" / "Deep analysis" | `full_analysis` | analysis_handler.py |

## Detailed Routing Logic

### 1. Metadata Discovery Operations

#### A. Table Operations
**User asks about tables:**
- "List tables" → `list_tables`
- "How many tables?" → `list_tables`
- "What tables exist?" → `list_tables`
- "Show me table details for X" → `describe_table` (requires table name)
- "Tell me about table X" → `describe_table`
- "What's in table X?" → `describe_table`

**Handler:** `metadata_handler.py::handle_list_tables()` or `handle_describe_table()`

#### B. Column Operations
**User asks about columns:**
- "List all columns" → `list_columns`
- "Show columns in table X" → `list_columns` (with table parameter)
- "What columns are in X?" → `list_columns`
- "Show calculated columns" → `list_calculated_columns`
- "List calculated columns in table X" → `list_calculated_columns` (with table parameter)

**Handler:** `metadata_handler.py::handle_list_columns()` or `handle_list_calculated_columns()`

#### C. Measure Operations
**User asks about measures:**
- "List measures" → `list_measures`
- "Show all measures" → `list_measures`
- "List measures in table X" → `list_measures` (with table parameter)
- "Show measure details for X" → `get_measure_details` (requires table and measure)
- "Get measure X from table Y" → `get_measure_details`
- "Show me the DAX for measure X" → `get_measure_details`
- "What's the expression for measure X?" → `get_measure_details`

**Handler:** `metadata_handler.py::handle_list_measures()` or `handle_get_measure_details()`

**IMPORTANT:**
- `list_measures` returns measure names and basic info (no DAX expressions)
- `get_measure_details` returns full measure details INCLUDING the DAX expression
- If user wants to see the DAX formula, use `get_measure_details`

#### D. Search Operations
**User wants to search:**
- "Find tables/columns/measures matching X" → `search_objects`
- "Search for pattern X" → `search_objects`
- "Find anything with name X" → `search_objects`
- "Search in measure DAX" → `search_string`
- "Find measures containing 'SUM'" → `search_string`
- "Search measure expressions for X" → `search_string`

**Handler:** `metadata_handler.py::handle_search_objects()` or `handle_search_string()`

**IMPORTANT:**
- `search_objects` searches object NAMES (tables, columns, measures)
- `search_string` searches inside measure DAX EXPRESSIONS

### 2. Data Query Operations

#### A. Data Preview
**User wants to see data:**
- "Preview table X" → `preview_table_data`
- "Show me sample data from table X" → `preview_table_data`
- "Show first 10 rows of table X" → `preview_table_data`

**Handler:** `query_handler.py::handle_preview_table_data()`

#### B. DAX Execution
**User wants to run DAX:**
- "Run this DAX query" → `run_dax`
- "Execute EVALUATE ..." → `run_dax`
- "Run DAX: ..." → `run_dax`

**Handler:** `query_handler.py::handle_run_dax()`

#### C. Column Analysis
**User wants column insights:**
- "Show distribution for column X" → `get_column_value_distribution`
- "Top values in column X" → `get_column_value_distribution`
- "Column summary for X" → `get_column_summary`
- "Stats for column X" → `get_column_summary`

**Handler:** `query_handler.py::handle_get_column_value_distribution()` or `handle_get_column_summary()`

### 3. Model Modification Operations

#### A. Measure Management
**User wants to create/modify measures:**
- "Create measure X" → `upsert_measure`
- "Update measure X" → `upsert_measure`
- "Add measure X with expression Y" → `upsert_measure`
- "Delete measure X" → `delete_measure`
- "Remove measure X from table Y" → `delete_measure`
- "Create multiple measures" → `bulk_create_measures`
- "Delete multiple measures" → `bulk_delete_measures`

**Handler:** `model_operations_handler.py::handle_upsert_measure()` or `handle_delete_measure()`

#### B. Calculation Groups
**User asks about calculation groups:**
- "List calculation groups" → `list_calculation_groups`
- "Show calculation groups" → `list_calculation_groups`
- "Create calculation group X" → `create_calculation_group`
- "Delete calculation group X" → `delete_calculation_group`

**Handler:** `model_operations_handler.py::handle_list_calculation_groups()`, etc.

### 4. Analysis Operations

#### A. Quick Analysis
**User wants quick model overview:**
- "Analyze the model" → `simple_analysis` (mode='all')
- "Show model statistics" → `simple_analysis` (mode='stats')
- "List all tables and measures" → `simple_analysis` (mode='all')
- "Show model overview" → `simple_analysis` (mode='all')

**Handler:** `analysis_handler.py::handle_simple_analysis()`

#### B. Deep Analysis
**User wants comprehensive analysis:**
- "Full model analysis" → `full_analysis`
- "Comprehensive analysis" → `full_analysis`
- "Run BPA" → `full_analysis` (with include_bpa=True)
- "Check best practices" → `full_analysis`
- "Performance analysis" → `full_analysis` (scope='performance')

**Handler:** `analysis_handler.py::handle_full_analysis()`

### 5. Dependencies and Impact Analysis

**User asks about dependencies:**
- "Analyze dependencies for measure X" → `analyze_measure_dependencies`
- "What does measure X depend on?" → `analyze_measure_dependencies`
- "Show impact of measure X" → `get_measure_impact`
- "What uses measure X?" → `get_measure_impact`

**Handler:** `dependencies_handler.py::handle_analyze_measure_dependencies()` or `handle_get_measure_impact()`

## Decision Tree for Common Scenarios

### Scenario 1: User wants to check a specific measure
```
Q: "Show me the measure 'Total Sales'"
↓
Does user want just the name/basic info?
  → NO, they want to "check" or "see" the measure
  → Use: get_measure_details
  → Requires: table name and measure name
```

### Scenario 2: User wants to list measures
```
Q: "List all measures" or "What measures exist?"
↓
User wants a list, not details
  → Use: list_measures
  → Optional: table filter
```

### Scenario 3: User wants table information
```
Q: "Tell me about the Sales table"
↓
User wants details about a specific table
  → Use: describe_table
  → Returns: columns, measures, relationships
```

### Scenario 4: User wants to search
```
Q: "Find anything with 'Sales' in the name"
↓
Searching by NAME
  → Use: search_objects

Q: "Find measures that use CALCULATE"
↓
Searching by EXPRESSION content
  → Use: search_string
```

## Common Pitfalls to Avoid

### ❌ DON'T: Use list_measures to get DAX expressions
```
User: "Show me the DAX for measure X"
Wrong: list_measures (doesn't return expressions)
```

### ✅ DO: Use get_measure_details for DAX expressions
```
User: "Show me the DAX for measure X"
Correct: get_measure_details(table="TableName", measure="X")
```

### ❌ DON'T: Use search_objects to search DAX code
```
User: "Find measures that use SUM"
Wrong: search_objects (only searches names)
```

### ✅ DO: Use search_string to search DAX code
```
User: "Find measures that use SUM"
Correct: search_string(search_text="SUM", search_in_expression=True)
```

### ❌ DON'T: Use describe_table for listing all tables
```
User: "List all tables"
Wrong: describe_table (requires specific table name)
```

### ✅ DO: Use list_tables for listing all tables
```
User: "List all tables"
Correct: list_tables()
```

## Integration with AI Agents

### When processing user requests:
1. **Parse the intent**: What is the user asking for?
   - Listing? (use list_* tools)
   - Details? (use describe_* or get_* tools)
   - Searching? (use search_* tools)
   - Creating/modifying? (use upsert_* or delete_* tools)
   - Analysis? (use *_analysis tools)

2. **Identify required parameters**:
   - Table name? (required for describe_table, get_measure_details, etc.)
   - Measure name? (required for get_measure_details)
   - Search pattern? (required for search tools)

3. **Choose the right tool**:
   - Use the mapping tables above
   - Consider the decision trees
   - Avoid common pitfalls

4. **Validate parameters**:
   - Do you have all required parameters?
   - If not, ask the user for clarification

## Tool Categories Summary

| Category | Tools | Use When |
|----------|-------|----------|
| **Metadata** | list_tables, describe_table, list_columns, list_measures, get_measure_details, list_calculated_columns, search_objects, search_string | User wants to explore/discover model objects |
| **Query** | preview_table_data, run_dax, get_column_value_distribution, get_column_summary | User wants to see data or run queries |
| **Operations** | upsert_measure, delete_measure, bulk_create_measures, bulk_delete_measures | User wants to modify the model |
| **Analysis** | simple_analysis, full_analysis | User wants insights about the model |
| **Dependencies** | analyze_measure_dependencies, get_measure_impact | User wants to understand relationships between objects |
| **Export** | export_model_schema, export_tmsl, export_tmdl | User wants to export model definitions |

---

**Last Updated:** 2025-11-19
**Version:** 1.0
