# Token Optimization - Before & After Examples

This document shows concrete examples of how to optimize the most token-heavy tools.

---

## Example 1: 13_analyze_hybrid_model (1,377 tokens → ~350 tokens = 75% reduction)

### ❌ BEFORE (Verbose)

```python
'analyze_hybrid_model': {
    "type": "object",
    "properties": {
        "analysis_path": {
            "type": "string",
            "description": "⚠️ ONLY PARAMETER NEEDED: Path to exported analysis folder. This MCP server tool AUTOMATICALLY & INTERNALLY reads ALL files (TMDL relationships, measures with DAX, JSON metadata, parquet data). 🚫🚫🚫 CRITICAL: DO NOT use Read, Glob, Grep, or any filesystem tools - this tool returns COMPLETE data with full relationships list already parsed from TMDL! Example: 'c:\\path\\to\\Model_analysis'"
        },
        "operation": {
            "type": "string",
            "description": "🔧 100% AUTOMATED OPERATIONS (all file I/O handled internally): 'read_metadata' (returns: full metadata + complete relationships list parsed from TMDL + expert analysis), 'find_objects' (searches all TMDL internally), 'get_object_definition' (returns: complete DAX from TMDL), 'analyze_dependencies', 'analyze_performance', 'get_sample_data' (reads parquet internally), 'get_unused_columns' (reads JSON internally), 'get_report_dependencies' (reads JSON internally), 'smart_analyze' (NL query). 🚫 NEVER read files - all data is returned complete!",
            "enum": ["read_metadata", "find_objects", "get_object_definition", "analyze_dependencies", "analyze_performance", "get_sample_data", "get_unused_columns", "get_report_dependencies", "smart_analyze"],
            "default": "read_metadata"
        },
        "intent": {
            "type": "string",
            "description": "Natural language intent (only for operation='smart_analyze'). Example: 'Show me all measures in Time Intelligence folder'"
        },
        "object_filter": {
            "type": "object",
            "description": "Filter for objects",
            "properties": {
                "object_type": {
                    "type": "string",
                    "description": "Object type: 'tables', 'measures', 'columns', 'relationships', 'roles'",
                    "enum": ["tables", "measures", "columns", "relationships", "roles"]
                },
                "name_pattern": {
                    "type": "string",
                    "description": "Regex pattern for name matching"
                },
                "table": {
                    "type": "string",
                    "description": "Filter by table name"
                },
                "folder": {
                    "type": "string",
                    "description": "Filter by display folder (for measures)"
                },
                "is_hidden": {
                    "type": "boolean",
                    "description": "Filter by visibility"
                },
                "complexity": {
                    "type": "string",
                    "description": "Filter by complexity: 'simple', 'medium', 'complex'",
                    "enum": ["simple", "medium", "complex"]
                },
                "object_name": {
                    "type": "string",
                    "description": "Object name or search pattern (e.g., 'base scenario' will fuzzy match 'PL-AMT-BASE Scenario'). For get_object_definition and analyze_dependencies."
                },
                "table_name": {
                    "type": "string",
                    "description": "Table name (for get_sample_data operation - automatically reads and returns sample data from parquet file)"
                }
            }
        },
        "format_type": {
            "type": "string",
            "description": "Output format: 'json' (default) or 'toon' (50% smaller, auto-applied for large responses)",
            "enum": ["json", "toon"],
            "default": "json"
        },
        "batch_size": {
            "type": "integer",
            "description": "Results per page (default: 50)",
            "default": 50
        },
        "batch_number": {
            "type": "integer",
            "description": "Page number (default: 0)",
            "default": 0
        },
        "priority": {
            "type": "string",
            "description": "Filter by priority: 'critical', 'high', 'medium', 'low', or null for all",
            "enum": ["critical", "high", "medium", "low"]
        },
        "detailed": {
            "type": "boolean",
            "description": "Include detailed analysis (default: false)",
            "default": False
        },
        "include_dependencies": {
            "type": "boolean",
            "description": "Include dependency info (default: false)",
            "default": False
        },
        "include_sample_data": {
            "type": "boolean",
            "description": "Include sample data (default: false)",
            "default": False
        }
    },
    "required": ["analysis_path", "operation"]
}
```

**Character count:** ~4,800 chars
**Estimated tokens:** ~1,377 tokens

---

### ✅ AFTER (Optimized)

```python
# Common schemas defined once (schema_definitions.py)
COMMON_SCHEMAS = {
    "file_path": {
        "type": "string",
        "description": "File or folder path"
    },
    "object_filter_hybrid": {
        "type": "object",
        "properties": {
            "object_type": {"type": "string", "enum": ["tables", "measures", "columns", "relationships", "roles"]},
            "name_pattern": {"type": "string"},
            "table": {"type": "string"},
            "folder": {"type": "string"},
            "is_hidden": {"type": "boolean"},
            "complexity": {"type": "string", "enum": ["simple", "medium", "complex"]},
            "object_name": {"type": "string"},
            "table_name": {"type": "string"}
        }
    },
    "pagination_params": {
        "type": "object",
        "properties": {
            "batch_size": {"type": "integer", "default": 50},
            "batch_number": {"type": "integer", "default": 0}
        }
    }
}

# Optimized tool schema
'analyze_hybrid_model': {
    "type": "object",
    "properties": {
        "analysis_path": {
            "$ref": "#/common/file_path"
        },
        "operation": {
            "type": "string",
            "description": "Analysis operation (all file I/O internal): read_metadata, find_objects, get_object_definition, analyze_dependencies, analyze_performance, get_sample_data, get_unused_columns, get_report_dependencies, smart_analyze",
            "enum": ["read_metadata", "find_objects", "get_object_definition", "analyze_dependencies", "analyze_performance", "get_sample_data", "get_unused_columns", "get_report_dependencies", "smart_analyze"],
            "default": "read_metadata",
            "_docs": "docs/HYBRID_ANALYSIS_GUIDE.md"
        },
        "intent": {
            "type": "string",
            "description": "NL query (for smart_analyze only)"
        },
        "object_filter": {
            "$ref": "#/common/object_filter_hybrid"
        },
        "format_type": {
            "type": "string",
            "enum": ["json", "toon"],
            "default": "json"
        },
        "batch_size": {"type": "integer", "default": 50},
        "batch_number": {"type": "integer", "default": 0},
        "priority": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low"]
        },
        "detailed": {"type": "boolean", "default": false},
        "include_dependencies": {"type": "boolean", "default": false},
        "include_sample_data": {"type": "boolean", "default": false}
    },
    "required": ["analysis_path", "operation"]
}
```

**Character count:** ~1,200 chars (75% reduction)
**Estimated tokens:** ~350 tokens (75% reduction)

**Key Changes:**
- ❌ Removed emojis and excessive warnings
- ❌ Removed verbose operation descriptions (moved to docs)
- ✅ Added `_docs` reference to external documentation
- ✅ Used `$ref` for common patterns
- ✅ Removed redundant defaults from descriptions
- ✅ Shortened "Natural language" to "NL"

---

## Example 2: 05_simple_analysis (995 tokens → ~200 tokens = 80% reduction)

### ❌ BEFORE (Verbose)

```python
'simple_analysis': {
    "type": "object",
    "properties": {
        "mode": {
            "type": "string",
            "enum": ["all", "tables", "stats", "measures", "measure", "columns", "relationships", "roles", "database", "calculation_groups"],
            "description": (
                "Analysis mode - Microsoft Official MCP Server operations:\n"
                "\n"
                "**ALL OPERATIONS (Recommended):**\n"
                "- 'all': Run ALL 9 core Microsoft MCP operations + generate expert analysis\n"
                "  Returns: Complete model overview with detailed Power BI expert insights\n"
                "  Execution time: ~2-5 seconds (all operations combined)\n"
                "\n"
                "**Database Operations:**\n"
                "- 'database': List databases - Microsoft MCP Database List operation\n"
                "  Returns: database ID, name, compatibilityLevel, state, estimated size\n"
                "\n"
                "**Model Operations:**\n"
                "- 'stats': Fast model statistics (< 1s) - Microsoft MCP GetStats operation\n"
                "  Returns: complete model metadata + all aggregate counts + per-table breakdown\n"
                "\n"
                "**Table Operations:**\n"
                "- 'tables': Ultra-fast table list (< 500ms) - Microsoft MCP List operation\n"
                "  Returns: table names with column/measure/partition counts\n"
                "\n"
                "**Measure Operations:**\n"
                "- 'measures': List measures - Microsoft MCP Measure List operation\n"
                "  Optional params: table (filter), max_results (limit)\n"
                "  Returns: measure names with displayFolder\n"
                "- 'measure': Get measure details - Microsoft MCP Measure Get operation\n"
                "  Required params: table, measure_name\n"
                "  Returns: full measure metadata including DAX expression\n"
                "\n"
                "**Column Operations:**\n"
                "- 'columns': List columns - Microsoft MCP Column List operation\n"
                "  Optional params: table (filter), max_results (limit)\n"
                "  Returns: columns grouped by table with dataType\n"
                "\n"
                "**Relationship Operations:**\n"
                "- 'relationships': List all relationships - Microsoft MCP Relationship List operation\n"
                "  Optional params: active_only (boolean)\n"
                "  Returns: all relationships with full metadata (fromTable, toTable, cardinality, etc.)\n"
                "\n"
                "**Calculation Group Operations:**\n"
                "- 'calculation_groups': List calculation groups - Microsoft MCP ListGroups operation\n"
                "  Returns: all calculation groups with their items (ordinal + name)\n"
                "\n"
                "**Security Operations:**\n"
                "- 'roles': List security roles - Microsoft MCP Role List operation\n"
                "  Returns: role names with modelPermission and table permission count"
            ),
            "default": "all"
        },
        "table": {
            "type": "string",
            "description": (
                "Table name - used by:\n"
                "- mode='measures': Filter measures by table (optional)\n"
                "- mode='measure': Table containing measure (required)\n"
                "- mode='columns': Filter columns by table (optional)\n"
                "- mode='partitions': Filter partitions by table (optional)"
            )
        },
        "measure_name": {
            "type": "string",
            "description": "Measure name - required for mode='measure'"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum results to return - used by mode='measures' and mode='columns' (optional)"
        },
        "active_only": {
            "type": "boolean",
            "description": "Only return active relationships - used by mode='relationships' (default: false)",
            "default": False
        }
    },
    "required": []
}
```

**Character count:** ~3,500 chars
**Estimated tokens:** ~995 tokens

---

### ✅ AFTER (Optimized)

```python
'simple_analysis': {
    "type": "object",
    "properties": {
        "mode": {
            "type": "string",
            "enum": ["all", "tables", "stats", "measures", "measure", "columns", "relationships", "roles", "database", "calculation_groups"],
            "description": "Microsoft MCP operation: 'all' (complete, 2-5s), 'tables' (<500ms), 'stats' (<1s), 'measures', 'measure', 'columns', 'relationships', 'calculation_groups', 'roles', 'database'. See docs for details.",
            "default": "all",
            "_docs": "docs/AGENTIC_ROUTING_GUIDE.md#simple-analysis"
        },
        "table": {
            "type": "string",
            "description": "Table filter (for measures/columns/measure modes)"
        },
        "measure_name": {
            "type": "string",
            "description": "Measure name (required for mode='measure')"
        },
        "max_results": {
            "type": "integer",
            "description": "Result limit (for measures/columns)"
        },
        "active_only": {
            "type": "boolean",
            "default": false
        }
    },
    "required": []
}
```

**Character count:** ~700 chars (80% reduction)
**Estimated tokens:** ~200 tokens (80% reduction)

**Key Changes:**
- ❌ Removed 50+ lines of operation explanations
- ❌ Removed formatting (markdown headers, bullets)
- ❌ Removed timing details from description
- ✅ Consolidated to one-line description
- ✅ Added `_docs` reference
- ✅ Shortened parameter descriptions
- ✅ Removed "default: false" from description (kept in schema)

---

## Example 3: Schema Deduplication Pattern

### ❌ BEFORE (Repeated Patterns)

```python
# In multiple tools:
'get_measure_details': {
    "properties": {
        "table": {
            "type": "string",
            "description": "Table name containing the measure"
        },
        "measure": {
            "type": "string",
            "description": "Measure name to retrieve"
        }
    },
    "required": ["table", "measure"]
}

'analyze_measure_dependencies': {
    "properties": {
        "table": {
            "type": "string",
            "description": "Table name"
        },
        "measure": {
            "type": "string",
            "description": "Measure name"
        }
    },
    "required": ["table", "measure"]
}

'get_measure_impact': {
    "properties": {
        "table": {
            "type": "string",
            "description": "Table name"
        },
        "measure": {
            "type": "string",
            "description": "Measure name"
        }
    },
    "required": ["table", "measure"]
}
```

**Total for 3 tools:** ~500 tokens

---

### ✅ AFTER (Deduplicated with $ref)

```python
# Define once in schema_definitions.py:
COMMON_SCHEMAS = {
    "measure_identifier": {
        "type": "object",
        "properties": {
            "table": {"type": "string", "description": "Table name"},
            "measure": {"type": "string", "description": "Measure name"}
        },
        "required": ["table", "measure"]
    }
}

# Reference in multiple tools:
'get_measure_details': {
    "$ref": "#/common/measure_identifier"
}

'analyze_measure_dependencies': {
    "$ref": "#/common/measure_identifier"
}

'get_measure_impact': {
    "$ref": "#/common/measure_identifier"
}
```

**Total for 3 tools:** ~200 tokens (60% reduction)

---

## Example 4: Compact JSON in Responses

### ❌ BEFORE (Pretty-printed)

```python
return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

**Example response:**
```json
{
  "success": true,
  "tables": [
    {
      "name": "FactSales",
      "columns": 15,
      "measures": 23,
      "rows": 1000000
    },
    {
      "name": "DimCustomer",
      "columns": 8,
      "measures": 0,
      "rows": 50000
    }
  ],
  "total_tables": 2
}
```

**Character count:** 291 chars
**Estimated tokens:** ~83 tokens

---

### ✅ AFTER (Compact)

```python
return [TextContent(type="text", text=json.dumps(result, separators=(',', ':')))]
```

**Example response:**
```json
{"success":true,"tables":[{"name":"FactSales","columns":15,"measures":23,"rows":1000000},{"name":"DimCustomer","columns":8,"measures":0,"rows":50000}],"total_tables":2}
```

**Character count:** 193 chars (34% reduction)
**Estimated tokens:** ~55 tokens (34% reduction)

---

## Example 5: CSV Format for Tabular Data

### ❌ BEFORE (JSON Array)

```python
# Response from run_dax for 50 rows:
{
  "success": true,
  "data": [
    {"Date": "2023-01-01", "Sales": 12500.50, "Qty": 125},
    {"Date": "2023-01-02", "Sales": 13200.25, "Qty": 132},
    {"Date": "2023-01-03", "Sales": 11800.75, "Qty": 118},
    // ... 47 more rows
  ],
  "row_count": 50
}
```

**Estimated tokens for 50 rows:** ~2,500 tokens

---

### ✅ AFTER (CSV Format)

```python
# Auto-detect tabular data and use CSV:
{
  "success": true,
  "data_format": "csv",
  "data": "Date,Sales,Qty\n2023-01-01,12500.50,125\n2023-01-02,13200.25,132\n2023-01-03,11800.75,118\n...",
  "row_count": 50
}
```

**Estimated tokens for 50 rows:** ~1,750 tokens (30% reduction)

**Benefits:**
- Scales linearly: ~14 tokens saved per row
- For 100 rows: ~1,380 tokens saved
- For 1,000 rows: ~13,800 tokens saved

---

## Example 6: Resource References for Large Exports

### ❌ BEFORE (Inline Export)

```python
def handle_export_tmdl(args):
    tmdl_content = generate_tmdl()  # 500KB of TMDL

    return {
        "success": true,
        "tmdl": tmdl_content,  # Entire TMDL sent inline
        "size": len(tmdl_content)
    }
```

**Token cost:** ~140,000 tokens for 500KB TMDL

---

### ✅ AFTER (Resource Reference)

```python
def handle_export_tmdl(args):
    tmdl_path = generate_tmdl_file()
    tmdl_content = read_file(tmdl_path)

    # Register as MCP resource
    resource_manager = get_resource_manager()
    uri = resource_manager.register_export(tmdl_path, {
        'type': 'tmdl',
        'size': len(tmdl_content)
    })

    return {
        "success": true,
        "resource_uri": uri,  # Reference only
        "size": len(tmdl_content),
        "preview": tmdl_content[:500],  # First 500 chars
        "message": "Use read_resource() to access full TMDL"
    }
```

**Token cost:** ~500 tokens (99.6% reduction!)

**Benefits:**
- Client can read resource on-demand via `read_resource(uri)`
- Massive savings for large exports
- Useful for: TMDL, large schemas, documentation, reports

---

## Summary of Optimization Techniques

| Technique | Complexity | Impact | Example |
|-----------|-----------|--------|---------|
| Remove emojis/warnings | Low | 10-20% | analyze_hybrid_model |
| Compress descriptions | Low | 30-50% | simple_analysis |
| JSON $ref deduplication | Medium | 20-30% | measure_identifier |
| Compact JSON | Low | 15-25% | All responses |
| CSV for tables | Medium | 25-35% | run_dax |
| Resource references | Medium | 90-99% | export_tmdl |
| Progressive disclosure | High | 60-70% | Optional |

---

## Implementation Checklist

### Phase 1: Quick Wins (1-2 days)
- [ ] Compress `13_analyze_hybrid_model` schema
- [ ] Compress `05_simple_analysis` schema
- [ ] Compress `13_export_hybrid_analysis` schema
- [ ] Enable compact JSON globally
- [ ] Add `_docs` references to verbose tools

### Phase 2: Schema Optimization (3-5 days)
- [ ] Create `schema_definitions.py` with common schemas
- [ ] Refactor `tool_schemas.py` to use `$ref`
- [ ] Test schema validation with JSON Schema validator

### Phase 3: Response Optimization (2-3 days)
- [ ] Implement CSV format detection for tabular data
- [ ] Add resource references for large exports
- [ ] Test with real Power BI models

---

**For full details, see:**
- `TOKEN_OPTIMIZATION_PLAN.md` - Complete implementation plan
- `TOKEN_OPTIMIZATION_SUMMARY.md` - Executive summary
- `token_usage_baseline.json` - Measurement baseline

**Run measurements:**
```bash
python tests/measure_token_usage_simple.py
```
