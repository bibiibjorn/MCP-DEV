# PBIXRAY-V2 Tools Quick Reference

Complete list of all 47 tools available in PBIXRAY-V2.3

---

## Connection & Discovery (2)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `detect_powerbi_desktop` | Detect Power BI Desktop instances | None |
| `connect_to_powerbi` | Connect to a Power BI instance | `model_index` |

---

## Tables & Schema (5)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_tables` | List all tables in the model | None |
| `describe_table` | Get detailed table information | `table` |
| `list_columns` | List columns for a table | `table` |
| `preview_table_data` | Preview data from a table | `table` |
| `export_model_schema` | Export complete model schema | None |

---

## Measures (6)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_measures` | List all measures | None |
| `get_measure_details` | Get measure details | `table`, `measure` |
| `upsert_measure` | Create or update a measure | `table`, `measure`, `expression` |
| `delete_measure` | Delete a measure | `table`, `measure` |
| `bulk_create_measures` | Create multiple measures | `measures` (array) |
| `bulk_delete_measures` | Delete multiple measures | `measures` (array) |

---

## Calculated Columns (1)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_calculated_columns` | List calculated columns | None |

---

## Relationships (2)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_relationships` | List relationships | None |
| `analyze_relationship_cardinality` | Analyze relationship cardinality issues | None |

---

## DAX Execution (3)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `run_dax_query` | Execute a DAX query | `query` |
| `validate_dax_query` | Validate DAX syntax and analyze complexity | `query` |
| `analyze_query_performance` | Analyze query performance with SE/FE breakdown | `query` |

---

## Search & Discovery (4)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `search_objects` | Search for tables, columns, measures | `pattern` |
| `search_string` | Search in expressions | `search_text` |
| `get_column_values` | Get distinct column values | `table`, `column` |
| `get_column_summary` | Get column statistics | `table`, `column` |

---

## Dependencies & Usage (3)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `analyze_measure_dependencies` | Analyze measure dependencies | `table`, `measure` |
| `find_unused_objects` | Find unused objects in model | None |
| `analyze_column_usage` | Analyze where a column is used | `table`, `column` |

---

## Calculation Groups (3)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_calculation_groups` | List calculation groups | None |
| `create_calculation_group` | Create a calculation group | `name`, `items` |
| `delete_calculation_group` | Delete a calculation group | `name` |

---

## Data Sources (2)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `get_data_sources` | Get data sources | None |
| `get_m_expressions` | Get M expressions | None |

---

## Partitions & Refresh (4)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_partitions` | List table partitions | None |
| `refresh_partition` | Refresh a specific partition | `table`, `partition` |
| `refresh_table` | Refresh entire table | `table` |
| `analyze_data_freshness` | Analyze data refresh status | None |

---

## Row-Level Security (3)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `list_roles` | List security roles | None |
| `test_role_filter` | Test RLS filter | `role_name`, `test_query` |
| `validate_rls_coverage` | Validate RLS coverage | None |

---

## Storage & Optimization (3)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `get_vertipaq_stats` | Get VertiPaq statistics | None |
| `analyze_column_cardinality` | Analyze column cardinality | None |
| `analyze_encoding_efficiency` | Analyze encoding efficiency | `table` |

---

## Documentation & Export (5)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `generate_documentation` | Generate Markdown documentation | None |
| `export_tmsl` | Export model as TMSL (summary by default) | None |
| `export_tmdl` | Export model as TMDL | None |
| `get_model_summary` | Get lightweight model summary (RECOMMENDED) | None |
| `compare_models` | Compare two models | `reference_tmsl` |

---

## Validation (2)

| Tool | Description | Required Args |
|------|-------------|---------------|
| `validate_model_integrity` | Validate model integrity | None |
| `analyze_model_bpa` | Run Best Practice Analyzer | None |

---

## Usage Examples

### Basic Connection
```json
// 1. Detect instances
{"tool": "detect_powerbi_desktop"}

// 2. Connect to first instance
{"tool": "connect_to_powerbi", "model_index": 0}

// 3. List tables
{"tool": "list_tables"}
```

### Measure Operations
```json
// Create a measure
{
  "tool": "upsert_measure",
  "table": "Sales",
  "measure": "Total Revenue",
  "expression": "SUM(Sales[Amount])",
  "display_folder": "Key Metrics"
}

// Bulk create measures
{
  "tool": "bulk_create_measures",
  "measures": [
    {
      "table": "Sales",
      "measure": "Total Quantity",
      "expression": "SUM(Sales[Quantity])"
    },
    {
      "table": "Sales",
      "measure": "Avg Price",
      "expression": "AVERAGE(Sales[Price])"
    }
  ]
}
```

### Dependencies Analysis
```json
// Analyze measure dependencies
{
  "tool": "analyze_measure_dependencies",
  "table": "Sales",
  "measure": "Total Revenue",
  "depth": 3
}

// Find unused objects
{"tool": "find_unused_objects"}
```

### Performance Analysis
```json
// Analyze query performance
{
  "tool": "analyze_query_performance",
  "query": "EVALUATE TOPN(10, Sales)",
  "runs": 3,
  "clear_cache": true
}

// Analyze column cardinality
{
  "tool": "analyze_column_cardinality",
  "table": "Sales"
}
```

### Documentation & Model Comparison
```json
// Get lightweight model summary (RECOMMENDED for large models)
{"tool": "get_model_summary"}

// Generate documentation
{"tool": "generate_documentation"}

// Export TMSL (summary only - safe for large models)
{"tool": "export_tmsl"}

// Export TMSL with full model (only for small models!)
{"tool": "export_tmsl", "include_full_model": true}

// Validate model
{"tool": "validate_model_integrity"}
```

**Important:** For comparing large models, use `get_model_summary` instead of full TMSL export. See [MODEL_COMPARISON_GUIDE.md](MODEL_COMPARISON_GUIDE.md) for details.

---

## Tool Count by Category

| Category | Count |
|----------|-------|
| Connection & Discovery | 2 |
| Tables & Schema | 5 |
| Measures | 6 |
| Calculated Columns | 1 |
| Relationships | 2 |
| DAX Execution | 3 |
| Search & Discovery | 4 |
| Dependencies | 3 |
| Calculation Groups | 3 |
| Data Sources | 2 |
| Partitions & Refresh | 4 |
| RLS | 3 |
| Storage & Optimization | 3 |
| Documentation & Export | 5 |
| Validation | 2 |
| **TOTAL** | **48** |

---

## Return to Documentation
- [Feature Complete Report](FEATURE_COMPLETE_V2.3.md)
- [README](README.md)
