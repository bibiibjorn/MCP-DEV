# MCP Server Token Usage Optimization Plan

**Version:** 1.0
**Date:** 2025-11-20
**Objective:** Reduce token usage on startup (primary) and during operations (secondary) without disabling, simplifying, or reducing tool functionality.

---

## Executive Summary

Current analysis indicates the MCP-PowerBi-Finvision server consumes an estimated **15,000-25,000 tokens on startup** due to:
- 45+ tools with verbose descriptions and complete JSON schemas
- Multi-line enum descriptions (e.g., `simple_analysis` has ~50 lines)
- Duplicate schema patterns across tools
- Embedded documentation in descriptions

This plan proposes **structural and technical optimizations** that can reduce startup tokens by **60-75%** (target: 4,000-8,000 tokens) while maintaining 100% tool functionality.

---

## Phase 1: Schema Optimization (Target: 40-50% reduction)

### 1.1 Schema Deduplication via JSON $ref

**Current Issue:**
- Repeated schema patterns across 45+ tools (e.g., `table`, `measure`, `query` parameters)
- Each tool defines its own complete schema inline

**Solution:**
Implement JSON Schema `$ref` references to shared definitions:

```python
# NEW: server/schema_definitions.py
COMMON_SCHEMAS = {
    "table_name": {
        "type": "string",
        "description": "Table name"
    },
    "measure_identifier": {
        "type": "object",
        "properties": {
            "table": {"$ref": "#/common/table_name"},
            "measure": {"type": "string", "description": "Measure name"}
        },
        "required": ["table", "measure"]
    },
    "pagination": {
        "type": "object",
        "properties": {
            "page_size": {"type": "integer", "default": 100},
            "next_token": {"type": "string"}
        }
    },
    "analysis_scope": {
        "type": "string",
        "enum": ["all", "best_practices", "performance", "integrity"],
        "default": "all"
    }
}

# In tool_schemas.py - BEFORE:
'get_measure_details': {
    "type": "object",
    "properties": {
        "table": {"type": "string", "description": "Table name"},
        "measure": {"type": "string", "description": "Measure name"}
    },
    "required": ["table", "measure"]
}

# AFTER:
'get_measure_details': {
    "type": "object",
    "properties": {
        "$ref": "#/common/measure_identifier"
    }
}
```

**Impact:** ~2,000-3,000 token reduction (15-20%)

---

### 1.2 Description Compression

**Current Issue:**
- `simple_analysis` description: ~2,500 characters with verbose explanations
- `analyze_hybrid_model` description: ~1,800 characters with warnings and emojis
- Many tools include usage examples in descriptions

**Solution:**
Implement two-tier description system:

```python
# NEW: server/registry.py enhancement
@dataclass
class ToolDefinition:
    name: str
    description: str              # Short version (1-2 lines, used on startup)
    detailed_description: str     # Full version (used on-demand via docs tool)
    handler: Callable
    input_schema: Dict[str, Any]
    category: str = "general"
    sort_order: int = 999

# Examples:
# BEFORE (2,500 chars):
"Analysis mode - Microsoft Official MCP Server operations:\n\n**ALL OPERATIONS (Recommended):**\n- 'all': Run ALL 9 core Microsoft MCP operations + generate expert analysis\n  Returns: Complete model overview with detailed Power BI expert insights\n  Execution time: ~2-5 seconds (all operations combined)\n\n**Database Operations:**\n- 'database': List databases - Microsoft MCP Database List operation\n..."

# AFTER (180 chars):
"Run Microsoft MCP operations: 'all' (complete analysis), 'tables', 'stats', 'measures', 'relationships', 'calculation_groups', 'roles'. Returns MCP-formatted responses. Fast (<5s)."
```

**Detailed descriptions available via:**
- `show_user_guide` tool (already exists)
- NEW: `get_tool_details(tool_name)` tool that returns full documentation on-demand
- External documentation (AGENTIC_ROUTING_GUIDE.md)

**Impact:** ~4,000-6,000 token reduction (25-35%)

---

### 1.3 Enum Description Consolidation

**Current Issue:**
```python
"mode": {
    "type": "string",
    "enum": ["all", "tables", "stats", "measures", "measure", "columns", "relationships", "roles", "database", "calculation_groups"],
    "description": (
        "Analysis mode - Microsoft Official MCP Server operations:\n"
        "\n"
        "**ALL OPERATIONS (Recommended):**\n"
        "- 'all': Run ALL 9 core Microsoft MCP operations + generate expert analysis\n"
        # ... 50 more lines
    )
}
```

**Solution:**
```python
"mode": {
    "type": "string",
    "enum": ["all", "tables", "stats", "measures", "measure", "columns", "relationships", "roles", "database", "calculation_groups"],
    "description": "Analysis mode. Options: 'all' (recommended, <5s), 'tables', 'stats', 'measures', 'columns', 'relationships', 'roles', 'database', 'calculation_groups'. Use 'all' for complete model overview.",
    "default": "all"
}
```

**Impact:** ~1,500-2,000 token reduction (10-12%)

---

### 1.4 Schema Property Minimization

**Current Issue:**
Many schemas include optional metadata that inflates size:

```python
"top_n": {
    "type": "integer",
    "description": "Limit number of rows returned (default: 100)",
    "default": 100
}
```

**Solution:**
Remove defaults from schema (handle in code):

```python
"top_n": {
    "type": "integer",
    "description": "Row limit (default: 100)"
}

# In handler:
def handle_run_dax(args):
    top_n = args.get('top_n', 100)  # Default handled here
```

**Impact:** ~500-1,000 token reduction (3-5%)

---

## Phase 2: Lazy Loading & On-Demand Tool Discovery (Target: 20-30% additional reduction)

### 2.1 Implement search_tools Function

**Current Issue:**
- All 45+ tools sent on startup regardless of usage
- Client can't discover tools progressively

**Solution:**
Add a lightweight tool discovery mechanism:

```python
# NEW: server/handlers/tool_discovery_handler.py

def handle_search_tools(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search available tools by keyword, category, or pattern

    Parameters:
    - query: Search term (optional)
    - category: Filter by category (optional)
    - detail_level: "minimal" (name only), "standard" (name+desc), "full" (complete schema)
    """
    registry = get_registry()
    query = args.get('query', '')
    category = args.get('category')
    detail_level = args.get('detail_level', 'standard')

    # Filter tools
    tools = registry.get_all_tools()
    if category:
        tools = registry.get_tools_by_category(category)
    if query:
        tools = [t for t in tools if query.lower() in t.name.lower() or query.lower() in t.description.lower()]

    # Format response based on detail level
    if detail_level == 'minimal':
        return {'tools': [t.name for t in tools]}
    elif detail_level == 'standard':
        return {'tools': [{'name': t.name, 'description': t.description, 'category': t.category} for t in tools]}
    else:  # full
        return {'tools': [{'name': t.name, 'description': t.detailed_description, 'schema': t.input_schema} for t in tools]}

def handle_get_tool_details(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get complete documentation for a specific tool"""
    tool_name = args['tool_name']
    registry = get_registry()
    tool_def = registry.get_tool_def(tool_name)

    return {
        'name': tool_def.name,
        'description': tool_def.description,
        'detailed_description': tool_def.detailed_description,
        'input_schema': tool_def.input_schema,
        'category': tool_def.category,
        'examples': _get_tool_examples(tool_name)  # From documentation
    }
```

**Integration:**
```python
# In pbixray_server_enhanced.py
@app.list_tools()
async def list_tools() -> List[Tool]:
    """List essential tools on startup (progressive disclosure)"""

    # Option A: Return only frequently-used tools initially
    essential_tools = [
        'detect_powerbi_desktop', 'connect_to_powerbi',
        'list_tables', 'describe_table', 'list_measures',
        'run_dax', 'simple_analysis',
        'search_tools', 'get_tool_details'  # Discovery tools
    ]

    # Option B: Return all but with minimal descriptions (Phase 1 compression applied)
    return registry.get_all_tools_as_mcp(compression_mode='minimal')
```

**Impact:** With Option A (progressive disclosure): ~10,000-12,000 token reduction (60-70% startup reduction)

---

### 2.2 Category-Based Tool Loading

**Solution:**
```python
def handle_list_tool_categories(args: Dict[str, Any]) -> Dict[str, Any]:
    """List available tool categories with counts"""
    registry = get_registry()
    categories = {}
    for cat in registry.list_categories():
        tools = registry.get_tools_by_category(cat)
        categories[cat] = {
            'count': len(tools),
            'description': CATEGORY_DESCRIPTIONS.get(cat, ''),
            'tools': [t.name for t in tools]  # Just names
        }
    return {'categories': categories}
```

**Impact:** Enables clients to load tools by category on-demand

---

## Phase 3: Response Format Optimization (Target: 20-40% reduction during operations)

### 3.1 CSV Format for Tabular Data

**Current Issue:**
Tabular data returned as JSON arrays with full field names repeated per row

**Solution:**
```python
# NEW: server/middleware.py enhancement

def format_tabular_response(data: List[Dict], format_type: str = 'json') -> str:
    """Format tabular data with optional CSV compression"""
    if format_type == 'csv' and len(data) > 5:
        import csv
        import io

        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return output.getvalue()
    else:
        return json.dumps(data, indent=2)

# In query handlers:
def handle_run_dax(args):
    result = query_executor.execute(args['query'])

    # Auto-detect: Use CSV for >5 rows
    if len(result['data']) > 5:
        result['data_format'] = 'csv'
        result['data'] = format_tabular_response(result['data'], 'csv')

    return result
```

**Impact:** 25-35% reduction for tabular responses (scales with row count: ~690 tokens saved per 50 rows)

---

### 3.2 Compact JSON Mode

**Current Issue:**
All responses use `json.dumps(result, indent=2)` which adds whitespace

**Solution:**
```python
# In pbixray_server_enhanced.py

def serialize_response(result: Dict, compact: bool = False) -> str:
    """Serialize with optional compact mode"""
    if compact or result.get('_use_compact_format'):
        # Remove whitespace
        return json.dumps(result, separators=(',', ':'))
    else:
        # Readable format
        return json.dumps(result, indent=2)

# Auto-detect large responses:
if len(str(result)) > 5000:
    result['_use_compact_format'] = True
```

**Impact:** ~15-20% reduction for large responses

---

### 3.3 Response Truncation with References

**Current Issue:**
Large exports (TMDL, schemas) sent inline

**Solution:**
```python
# Enhanced resource system
from server.resources import get_resource_manager

def handle_export_tmdl(args):
    # Generate TMDL
    tmdl_content = generator.export_tmdl(...)

    # Register as MCP resource instead of returning inline
    resource_manager = get_resource_manager()
    uri = resource_manager.register_export(tmdl_path, {
        'type': 'tmdl',
        'size': len(tmdl_content),
        'tables': table_count
    })

    return {
        'success': True,
        'message': f'TMDL exported: {tmdl_path}',
        'resource_uri': uri,  # Client can read via read_resource()
        'size': len(tmdl_content),
        'preview': tmdl_content[:500]  # First 500 chars only
    }
```

**Impact:** 80-95% reduction for large exports

---

### 3.4 Pagination Enhancement

**Current Implementation:**
```python
# In middleware.py - already exists
def paginate(items, page_size=50, next_token=None):
    # Returns paginated results
```

**Enhancement:**
Add automatic pagination for large result sets:

```python
def auto_paginate_if_needed(result: Dict, max_items: int = 100) -> Dict:
    """Auto-paginate large result sets"""
    if 'items' in result and len(result['items']) > max_items:
        result['items'] = result['items'][:max_items]
        result['_pagination'] = {
            'truncated': True,
            'total_count': len(result['items']),
            'returned': max_items,
            'message': f'Results truncated to {max_items}. Use pagination parameters for more.'
        }
    return result
```

**Impact:** Prevents accidental token overflow

---

## Phase 4: Structural Refactoring (Target: Additional 10-15% reduction)

### 4.1 Schema Generation Optimization

**Current Issue:**
Schemas built manually in 768-line `tool_schemas.py`

**Solution:**
Generate schemas programmatically with builder pattern:

```python
# NEW: server/schema_builder.py

class SchemaBuilder:
    """Fluent schema builder with automatic compression"""

    def __init__(self, name: str):
        self.name = name
        self.props = {}
        self.required = []

    def add_table_param(self, required: bool = True):
        """Add standard table parameter"""
        self.props['table'] = {"$ref": "#/common/table_name"}
        if required:
            self.required.append('table')
        return self

    def add_measure_params(self):
        """Add table + measure parameters"""
        self.props.update({
            "table": {"$ref": "#/common/table_name"},
            "measure": {"$ref": "#/common/measure_name"}
        })
        self.required.extend(['table', 'measure'])
        return self

    def add_pagination(self):
        """Add standard pagination"""
        self.props.update(COMMON_SCHEMAS['pagination']['properties'])
        return self

    def build(self) -> Dict:
        """Build final schema"""
        return {
            "type": "object",
            "properties": self.props,
            "required": self.required
        }

# Usage:
TOOL_SCHEMAS = {
    'get_measure_details': SchemaBuilder('get_measure_details')
        .add_measure_params()
        .build(),

    'list_measures': SchemaBuilder('list_measures')
        .add_table_param(required=False)
        .add_pagination()
        .build()
}
```

**Impact:** Improved maintainability + automatic deduplication

---

### 4.2 Dynamic Schema Loading

**Current Issue:**
All schemas loaded into memory on startup

**Solution:**
```python
# NEW: Lazy schema loading
class LazySchemaRegistry:
    def __init__(self):
        self._schema_cache = {}

    def get_schema(self, tool_name: str) -> Dict:
        """Get schema on-demand"""
        if tool_name not in self._schema_cache:
            # Load from definition
            self._schema_cache[tool_name] = self._build_schema(tool_name)
        return self._schema_cache[tool_name]

    def _build_schema(self, tool_name: str) -> Dict:
        """Build schema dynamically"""
        # Use schema builder or load from definitions
        pass
```

**Impact:** Reduced memory footprint + startup time

---

## Phase 5: Protocol-Level Optimizations

### 5.1 Initialization Instructions Compression

**Current:**
```python
def _initial_instructions() -> str:
    lines = [
        f"MCP-PowerBi-Finvision v{__version__} — Power BI Desktop MCP server.",
        "",
        "What you can do:",
        "- Connect to your open Power BI Desktop instance",
        "- Inspect tables/columns/measures and preview data",
        "- Search objects and view data sources and M expressions",
        "- Run Best Practice Analyzer (BPA) and relationship analysis",
        "- Export compact schema, TMDL, and documentation",
        "",
        "Quick start:",
        "1) Run tool: detect_powerbi_desktop",
        "2) Then: connect_to_powerbi (usually model_index=0)",
        "3) Try: list_tables | describe_table | preview_table_data",
        "",
        f"Full guide: {guides_dir}/PBIXRAY_Quickstart.pdf"
    ]
    return "\n".join(lines)
```

**Optimized:**
```python
def _initial_instructions() -> str:
    return (
        f"MCP-PowerBi-Finvision v{__version__} - Power BI Desktop MCP server. "
        f"Start: detect_powerbi_desktop → connect_to_powerbi → list_tables. "
        f"Use search_tools to discover 45+ tools across 13 categories."
    )
```

**Impact:** ~150-200 token reduction

---

## Implementation Roadmap

### Priority 1: Quick Wins (1-2 days)
1. **Phase 1.2:** Description compression (25-35% reduction)
   - Update all tool descriptions in handlers
   - Add detailed_description field
   - Create `get_tool_details` handler

2. **Phase 1.3:** Enum description consolidation (10-12% reduction)
   - Simplify verbose enum descriptions in tool_schemas.py

3. **Phase 5.1:** Instructions compression
   - Simplify startup instructions

**Expected Impact:** 40-50% startup reduction

---

### Priority 2: Schema Optimization (3-5 days)
1. **Phase 1.1:** Schema deduplication via $ref (15-20% reduction)
   - Create schema_definitions.py
   - Refactor tool_schemas.py to use $ref
   - Test schema validation

2. **Phase 1.4:** Schema property minimization (3-5% reduction)
   - Remove inline defaults
   - Move default handling to handlers

**Expected Impact:** Additional 20-25% reduction

---

### Priority 3: Response Optimization (2-3 days)
1. **Phase 3.1:** CSV format for tabular data (25-35% for queries)
   - Implement format_tabular_response()
   - Update query_handler.py
   - Add format parameter support

2. **Phase 3.2:** Compact JSON mode (15-20% for large responses)
   - Implement serialize_response()
   - Add auto-detection logic

3. **Phase 3.3:** Response truncation with references (80-95% for exports)
   - Enhance resource_manager
   - Update export handlers

**Expected Impact:** 30-50% operational reduction

---

### Priority 4: Advanced Optimization (5-7 days)
1. **Phase 2.1:** search_tools implementation
   - Create tool_discovery_handler.py
   - Add search_tools and get_tool_details
   - Update list_tools() for progressive disclosure

2. **Phase 4.1:** Schema builder pattern
   - Create schema_builder.py
   - Refactor tool_schemas.py

**Expected Impact:** Optional 60-70% startup reduction (if progressive disclosure adopted)

---

## Validation & Testing

### Token Measurement Script
```python
# NEW: tests/measure_token_usage.py

import tiktoken
from mcp.types import Tool
from server.registry import get_registry

def estimate_tokens(text: str) -> int:
    """Estimate token count using tiktoken"""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def measure_startup_tokens():
    """Measure tokens sent on startup"""
    registry = get_registry()
    tools = registry.get_all_tools_as_mcp()

    total_tokens = 0
    for tool in tools:
        tool_text = f"{tool.name}\n{tool.description}\n{json.dumps(tool.inputSchema)}"
        tokens = estimate_tokens(tool_text)
        total_tokens += tokens
        print(f"{tool.name}: {tokens} tokens")

    print(f"\nTotal startup tokens: {total_tokens}")
    return total_tokens

if __name__ == "__main__":
    measure_startup_tokens()
```

### Regression Tests
```python
# tests/test_token_optimization.py

def test_tool_functionality_preserved():
    """Ensure all tools still work after optimization"""
    # Test each tool with sample inputs
    pass

def test_schema_validation():
    """Verify schemas are still valid JSON Schema"""
    from jsonschema import Draft7Validator
    for tool_name, schema in TOOL_SCHEMAS.items():
        Draft7Validator.check_schema(schema)

def test_token_reduction():
    """Verify token reduction targets met"""
    tokens = measure_startup_tokens()
    assert tokens < 10000, f"Startup tokens {tokens} exceeds target 10,000"
```

---

## Estimated Impact Summary

| Phase | Optimization | Token Reduction | Implementation Effort |
|-------|-------------|----------------|---------------------|
| 1.1 | Schema deduplication | 15-20% | Medium |
| 1.2 | Description compression | 25-35% | Low |
| 1.3 | Enum consolidation | 10-12% | Low |
| 1.4 | Schema minimization | 3-5% | Low |
| 2.1 | Progressive disclosure | 60-70% (optional) | High |
| 3.1 | CSV format | 25-35% (queries) | Medium |
| 3.2 | Compact JSON | 15-20% (large responses) | Low |
| 3.3 | Resource references | 80-95% (exports) | Medium |
| 5.1 | Instructions compression | 1-2% | Low |

**Total Estimated Reduction:**
- **Startup (without progressive disclosure):** 55-75% (target: 4,000-8,000 tokens)
- **Startup (with progressive disclosure):** 70-85% (target: 2,500-5,000 tokens)
- **Operational (queries):** 30-50%
- **Operational (exports):** 80-95%

---

## Risks & Mitigations

### Risk 1: JSON $ref Support
**Risk:** Some MCP clients may not fully support JSON Schema $ref
**Mitigation:** Provide fallback option to expand refs inline via config flag

### Risk 2: Breaking Changes
**Risk:** Shortened descriptions may reduce discoverability
**Mitigation:**
- Add `get_tool_details` for full documentation
- Update AGENTIC_ROUTING_GUIDE.md
- Provide migration guide

### Risk 3: CSV Format Compatibility
**Risk:** Clients may expect JSON arrays
**Mitigation:**
- Make CSV opt-in initially
- Include format indicator in response
- Provide both formats for testing

---

## Success Metrics

1. **Startup token usage:** < 8,000 tokens (current: ~20,000)
2. **Query response tokens:** 30-50% reduction for tabular data
3. **Export response tokens:** 80%+ reduction via resource references
4. **Zero functionality loss:** All 45+ tools work identically
5. **Backward compatibility:** Existing integrations continue working
6. **Performance maintained:** No increase in response latency

---

## References

### Industry Research
1. **Anthropic Engineering:** "Code execution with MCP: building more efficient AI agents" (98.7% reduction via code execution pattern)
2. **GitHub SEP-1576:** "Mitigating Token Bloat in MCP" (schema deduplication, adaptive control)
3. **Block Engineering:** "Designing MCP Servers for Wide Schemas" (cell budgets, CSV vs JSON)
4. **Craig Walls (Medium):** "Optimizing API Output for MCP" (93-98% reduction via response filtering)

### Key Principles
- **Progressive disclosure:** Load tools on-demand rather than upfront
- **Schema deduplication:** Use JSON $ref for common patterns
- **Concise descriptions:** Replace verbose explanations with clear, short language
- **Response filtering:** Return minimal data sets, use handles for large payloads
- **Format optimization:** CSV for tables (29% less than JSON), compact JSON for large responses

---

## Next Steps

1. **Review & Approval:** Stakeholder review of plan
2. **Token Baseline:** Run measurement script to establish current baseline
3. **Phase 1 Implementation:** Start with quick wins (Priority 1)
4. **Iterative Testing:** Measure impact after each phase
5. **Documentation Updates:** Update user guides and routing documentation
6. **Production Rollout:** Gradual rollout with feature flags

---

**End of Plan**
