# Hybrid Analysis MCP Tools - Implementation Plan

## Executive Summary

This plan outlines the implementation of two new MCP server tools that enable Claude to efficiently analyze large Power BI models using a hybrid output format. The solution combines TMDL (for source of truth), JSON analysis files (for fast metadata), and sample data (for validation) - balancing speed, completeness, and Claude's token limits.

**Current MCP Server:** v4.2.07 with 51 tools across 13 categories
**Target:** Add 2 new tools in category "14 - Hybrid Analysis"
**Estimated Effort:** 2-3 days
**Priority:** High - enables efficient analysis of large models (66+ tables, 699+ measures)

---

## Current Architecture Analysis

### ✅ Existing Components (Leverage These)

1. **Handler Registry System** (`server/registry.py`)
   - Clean registration pattern with `ToolDefinition`
   - Category-based organization
   - Numbered tool naming convention (01-13)

2. **Tool Dispatcher** (`server/dispatch.py`)
   - Maps numbered names to internal handlers
   - Current highest number: `13_show_user_guide`
   - **Next available:** `14_*` prefix

3. **Export Infrastructure**
   - `AIModelExporter` (`core/model/ai_exporter.py`) - comprehensive JSON export
   - `ModelExporter` (`core/model/model_exporter.py`) - TMSL/TMDL export
   - `DependencyAnalyzer` (`core/model/dependency_analyzer.py`) - dependency graphs

4. **Connection & Query System**
   - `connection_state` - manages active connections
   - `query_executor` - runs DAX queries
   - AMO/TOM integration for model access

5. **Error Handling**
   - `ErrorHandler` - standardized error responses
   - Connection state validation
   - Manager availability checks

### 🔧 Required New Components

1. **Hybrid Analysis Exporter** (`core/model/hybrid_exporter.py`)
   - Generate 3-layer structure (TMDL + JSON + Sample Data)
   - Export to folder with organized structure
   - Row count extraction via DMV
   - Column usage tracking

2. **Hybrid Analysis Reader** (`core/model/hybrid_reader.py`)
   - Read folder structure
   - Parse JSON metadata/catalog/dependencies
   - Batch processing for large models
   - On-demand analysis generation

3. **Handler Module** (`server/handlers/hybrid_analysis_handler.py`)
   - Two tool handlers
   - Integration with registry
   - Token management and pagination

---

## Tool Specifications

### Tool 1: `14_export_hybrid_analysis`

**Purpose:** Export Power BI model to hybrid analysis format optimized for Claude

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "output_directory": {
      "type": "string",
      "description": "Directory to create analysis package"
    },
    "model_source": {
      "type": "string",
      "enum": ["connected_model", "pbix_file", "pbip_folder"],
      "default": "connected_model",
      "description": "Source of model data"
    },
    "model_path": {
      "type": "string",
      "description": "Path to .pbix or .pbip (if model_source is not connected_model)"
    },
    "include_sample_data": {
      "type": "boolean",
      "default": true,
      "description": "Export sample data as Parquet files"
    },
    "sample_rows": {
      "type": "number",
      "default": 1000,
      "description": "Number of sample rows per table"
    },
    "include_row_counts": {
      "type": "boolean",
      "default": true,
      "description": "Extract row counts via DMV queries"
    },
    "track_column_usage": {
      "type": "boolean",
      "default": true,
      "description": "Track which columns are used in measures/relationships/visuals"
    }
  },
  "required": ["output_directory"]
}
```

**Output Structure:**
```
output_directory/
├── model.bim/                 # Layer 1: TMDL (Source of Truth)
│   ├── model.tmdl
│   ├── tables/
│   │   ├── DimDate.tmdl
│   │   ├── FactPortfolioValues.tmdl
│   │   └── [all tables...]
│   ├── relationships/
│   │   └── relationships.tmdl
│   ├── expressions/
│   │   ├── _measures.tmdl
│   │   └── _columns.tmdl
│   ├── roles/
│   └── perspectives/
│
├── analysis/                  # Layer 2: JSON Analysis
│   ├── metadata.json         # Model statistics
│   ├── catalog.json          # Object index
│   └── dependencies.json     # Dependency graph
│
└── sample_data/              # Layer 3: Sample Data
    ├── DimDate.parquet
    ├── FactPortfolioValues.parquet
    └── [all tables...]
```

**Success Response:**
```json
{
  "success": true,
  "output_path": "/path/to/analysis/",
  "structure": {
    "tmdl_path": "model.bim/",
    "analysis_path": "analysis/",
    "sample_data_path": "sample_data/",
    "file_counts": {
      "tmdl_files": 72,
      "analysis_files": 3,
      "sample_data_files": 66
    }
  },
  "statistics": {
    "total_tables": 66,
    "total_measures": 699,
    "total_relationships": 78,
    "total_rows": 15234567,
    "package_size_mb": 7.3
  },
  "generation_time_seconds": 8.2,
  "note": "Performance analysis and recommendations generated on-demand via analyze_hybrid_model"
}
```

---

### Tool 2: `14_analyze_hybrid_model`

**Purpose:** Analyze exported hybrid model structure with token-aware batching

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "analysis_path": {
      "type": "string",
      "description": "Path to hybrid analysis directory"
    },
    "operation": {
      "type": "string",
      "enum": [
        "read_metadata",
        "find_objects",
        "get_object_definition",
        "analyze_dependencies",
        "analyze_performance",
        "generate_recommendations",
        "get_sample_data"
      ],
      "description": "Analysis operation to perform"
    },
    "object_filter": {
      "type": "object",
      "description": "Filter for find_objects operation",
      "properties": {
        "object_type": {
          "type": "string",
          "enum": ["table", "measure", "column", "relationship"]
        },
        "name_contains": {"type": "string"},
        "table": {"type": "string"},
        "complexity_min": {"type": "number"}
      }
    },
    "object_name": {
      "type": "string",
      "description": "Object name for get_object_definition"
    },
    "performance_focus": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["cardinality", "dax_complexity", "relationships", "unused_columns", "row_counts", "all"]
      },
      "default": ["all"],
      "description": "Focus areas for performance analysis"
    },
    "batch_config": {
      "type": "object",
      "description": "Batching for large models",
      "properties": {
        "enabled": {"type": "boolean", "default": true},
        "batch_size": {"type": "number", "default": 50},
        "batch_number": {"type": "number"}
      }
    },
    "recommendation_filters": {
      "type": "object",
      "properties": {
        "min_priority": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low"],
          "default": "high"
        },
        "category": {
          "type": "string",
          "enum": ["all", "performance", "architecture", "dax", "maintenance"],
          "default": "all"
        },
        "max_recommendations": {
          "type": "number",
          "default": 20
        }
      }
    },
    "sample_data_options": {
      "type": "object",
      "properties": {
        "table_name": {"type": "string"},
        "columns": {"type": "array", "items": {"type": "string"}},
        "max_rows": {"type": "number", "default": 100}
      }
    }
  },
  "required": ["analysis_path", "operation"]
}
```

**Example Outputs by Operation:**

1. **read_metadata** - Returns metadata.json contents
2. **find_objects** - Searches catalog.json
3. **get_object_definition** - Returns TMDL definition + dependencies
4. **analyze_dependencies** - Returns filtered dependencies.json
5. **analyze_performance** - Generates on-demand analysis with batching
6. **generate_recommendations** - Creates prioritized action items
7. **get_sample_data** - Reads Parquet files

---

## Implementation Phases

### Phase 1: Core Export Infrastructure (Day 1 Morning)

**Files to Create:**
1. `core/model/hybrid_exporter.py` - Main exporter class
2. `core/model/hybrid_structures.py` - Data classes for JSON structures

**Tasks:**
- [ ] Create `HybridAnalysisExporter` class
- [ ] Implement TMDL export via existing `ModelExporter`
- [ ] Generate `metadata.json` (model statistics)
- [ ] Generate `catalog.json` (object index with row counts & column usage)
- [ ] Generate `dependencies.json` (from `DependencyAnalyzer`)
- [ ] Export sample data as Parquet (via polars/pyarrow)
- [ ] Add row count extraction via DMV queries
- [ ] Add column usage tracking (relationships/measures/RLS)
- [ ] Add cardinality calculation for columns

**Code Skeleton:**
```python
# core/model/hybrid_exporter.py
class HybridAnalysisExporter:
    def __init__(self, connection, query_executor, model_exporter, dependency_analyzer):
        self.connection = connection
        self.query_executor = query_executor
        self.model_exporter = model_exporter
        self.dependency_analyzer = dependency_analyzer

    def export_hybrid_analysis(
        self,
        output_dir: str,
        include_sample_data: bool = True,
        sample_rows: int = 1000,
        include_row_counts: bool = True,
        track_column_usage: bool = True
    ) -> Dict[str, Any]:
        """Export model to hybrid format"""
        # 1. Create folder structure
        # 2. Export TMDL via model_exporter
        # 3. Generate metadata.json
        # 4. Generate catalog.json (with row counts & usage)
        # 5. Generate dependencies.json
        # 6. Export sample data as Parquet
        # 7. Return statistics
```

**Optimizations to Research:**
- Use polars for fast Parquet generation
- Parallel processing for sample data export
- Incremental JSON generation (avoid loading full model in memory)
- Cache DMV row count queries

---

### Phase 2: Analysis Reader (Day 1 Afternoon)

**Files to Create:**
1. `core/model/hybrid_reader.py` - Reader for hybrid structure

**Tasks:**
- [ ] Create `HybridAnalysisReader` class
- [ ] Implement JSON file readers (metadata/catalog/dependencies)
- [ ] Implement TMDL file reader (selective loading)
- [ ] Implement Parquet reader (with column selection)
- [ ] Add on-demand performance analysis
- [ ] Add recommendation generation
- [ ] Implement batching for large models
- [ ] Add response truncation logic

**Code Skeleton:**
```python
# core/model/hybrid_reader.py
class HybridAnalysisReader:
    def __init__(self, analysis_path: str):
        self.analysis_path = Path(analysis_path)
        self.metadata = None
        self.catalog = None
        self.dependencies = None
        self._cache = {}

    def read_metadata(self) -> Dict[str, Any]:
        """Read metadata.json"""

    def find_objects(self, filters: Dict[str, Any]) -> List[Dict]:
        """Search catalog.json"""

    def get_object_definition(self, object_name: str) -> Dict[str, Any]:
        """Get TMDL definition + dependencies"""

    def analyze_performance(
        self,
        focus_areas: List[str],
        batch_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate performance analysis on-demand"""

    def generate_recommendations(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate actionable recommendations"""
```

**Optimizations to Research:**
- Lazy loading of JSON files
- Cache parsed TMDL
- Stream large TMDL files
- Use polars for fast Parquet reading

---

### Phase 3: MCP Handler Integration (Day 2 Morning)

**Files to Create:**
1. `server/handlers/hybrid_analysis_handler.py`

**Tasks:**
- [ ] Create handler registration function
- [ ] Implement `handle_export_hybrid_analysis`
- [ ] Implement `handle_analyze_hybrid_model`
- [ ] Add to `server/handlers/__init__.py`
- [ ] Update `server/dispatch.py` TOOL_NAME_MAP
- [ ] Update `manifest.json` with new tools

**Code Skeleton:**
```python
# server/handlers/hybrid_analysis_handler.py
from server.registry import ToolDefinition

def handle_export_hybrid_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export model to hybrid analysis format"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    # Create exporter
    exporter = HybridAnalysisExporter(
        connection=connection_state.connection_manager.get_connection(),
        query_executor=connection_state.query_executor,
        model_exporter=connection_state.model_exporter,
        dependency_analyzer=DependencyAnalyzer(...)
    )

    # Export
    return exporter.export_hybrid_analysis(
        output_dir=args['output_directory'],
        include_sample_data=args.get('include_sample_data', True),
        sample_rows=args.get('sample_rows', 1000),
        include_row_counts=args.get('include_row_counts', True),
        track_column_usage=args.get('track_column_usage', True)
    )

def handle_analyze_hybrid_model(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze hybrid model structure"""
    analysis_path = args['analysis_path']
    operation = args['operation']

    # Create reader
    reader = HybridAnalysisReader(analysis_path)

    # Route to appropriate operation
    if operation == 'read_metadata':
        return reader.read_metadata()
    elif operation == 'find_objects':
        return reader.find_objects(args.get('object_filter', {}))
    # ... etc

def register_hybrid_analysis_handlers(registry):
    """Register hybrid analysis handlers"""
    registry.register(ToolDefinition(
        name="export_hybrid_analysis",
        description="[14-Hybrid] Export Power BI model to hybrid analysis format optimized for Claude",
        handler=handle_export_hybrid_analysis,
        input_schema={...},
        category="hybrid_analysis",
        sort_order=140
    ))

    registry.register(ToolDefinition(
        name="analyze_hybrid_model",
        description="[14-Hybrid] Analyze exported hybrid model with token-aware operations",
        handler=handle_analyze_hybrid_model,
        input_schema={...},
        category="hybrid_analysis",
        sort_order=141
    ))
```

**Updates Required:**

1. `server/handlers/__init__.py`:
```python
from server.handlers.hybrid_analysis_handler import register_hybrid_analysis_handlers

def register_all_handlers(registry):
    # ... existing ...
    register_hybrid_analysis_handlers(registry)
```

2. `server/dispatch.py`:
```python
TOOL_NAME_MAP = {
    # ... existing 01-13 ...

    # 14 - Hybrid Analysis (2 tools)
    '14_export_hybrid_analysis': 'export_hybrid_analysis',
    '14_analyze_hybrid_model': 'analyze_hybrid_model',
}
```

3. `manifest.json`:
```json
{
  "tools": [
    // ... existing tools ...
    {
      "name": "14_export_hybrid_analysis",
      "description": "[14-Hybrid] Export model to hybrid analysis format"
    },
    {
      "name": "14_analyze_hybrid_model",
      "description": "[14-Hybrid] Analyze hybrid model structure"
    }
  ]
}
```

---

### Phase 4: Testing & Validation (Day 2 Afternoon)

**Test Scenarios:**

1. **Small Model Test** (10 tables, 100 measures)
   - Export completes in <10 seconds
   - All files generated correctly
   - Metadata accurate
   - Sample data valid

2. **Large Model Test** (66 tables, 699 measures)
   - Export completes in <60 seconds
   - Row counts match actual data
   - Column usage detection accurate
   - Performance analysis generates correctly
   - Batching works properly

3. **Token Limit Tests**
   - analyze_performance with batch_size=50 stays under 8K tokens
   - Recommendations truncate properly at max_recommendations
   - No single response exceeds 50KB

4. **Error Handling**
   - Invalid analysis path returns clear error
   - Missing connection handled gracefully
   - Corrupted JSON files detected

**Test Files to Create:**
```python
# tests/test_hybrid_exporter.py
def test_export_small_model():
    """Test export on small model"""

def test_export_large_model():
    """Test export on large model (66 tables)"""

def test_row_count_accuracy():
    """Verify row counts match DMV results"""

def test_column_usage_detection():
    """Verify unused column detection"""

# tests/test_hybrid_reader.py
def test_read_metadata():
    """Test metadata reading"""

def test_find_objects():
    """Test object search"""

def test_performance_analysis_batching():
    """Test batching for large models"""

def test_token_limits():
    """Ensure responses stay under limits"""
```

---

## Key Optimizations

### 1. Export Performance

**Row Count Optimization:**
```python
# Use single DMV query for all row counts
query = """
SELECT
    [DIMENSION_NAME] as TableName,
    SUM([ROWS_COUNT]) as RowCount
FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
GROUP BY [DIMENSION_NAME]
"""
# vs individual queries per table (66x slower)
```

**Parallel Sample Data Export:**
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(export_table_sample, table): table
        for table in tables
    }
```

**Incremental JSON Generation:**
```python
# Don't load full model in memory
with open('catalog.json', 'w') as f:
    f.write('{"tables": [\n')
    for i, table in enumerate(tables):
        json.dump(process_table(table), f, indent=2)
        if i < len(tables) - 1:
            f.write(',\n')
    f.write('\n]}\n')
```

### 2. Analysis Performance

**Lazy Loading:**
```python
class HybridAnalysisReader:
    @property
    def metadata(self):
        if self._metadata is None:
            with open(self.analysis_path / 'analysis/metadata.json') as f:
                self._metadata = json.load(f)
        return self._metadata
```

**TMDL Caching:**
```python
@lru_cache(maxsize=100)
def read_tmdl_file(self, file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
```

**Batched Analysis:**
```python
def analyze_performance_batch(measures: List[Measure], batch_size: int = 50):
    for i in range(0, len(measures), batch_size):
        batch = measures[i:i+batch_size]
        yield analyze_batch(batch)
```

### 3. Token Management

**Response Size Estimation:**
```python
def estimate_tokens(data: Dict) -> int:
    """Rough token estimate: 1 token ≈ 4 characters"""
    return len(json.dumps(data)) // 4

def truncate_if_needed(data: Dict, max_tokens: int = 12000) -> Dict:
    estimated = estimate_tokens(data)
    if estimated > max_tokens:
        # Truncate and add warning
        data['truncated'] = True
        data['note'] = f"Results truncated ({estimated} → {max_tokens} tokens)"
    return data
```

---

## Dependencies

### Python Packages Required

```txt
# Already in project
pythonnet>=3.0.0
polars>=0.19.0  # Fast Parquet I/O
pyarrow>=14.0.0  # Parquet format
```

### Verify Installation

```bash
pip install polars pyarrow
```

---

## Folder Structure (After Implementation)

```
MCP-DEV/
├── core/
│   └── model/
│       ├── hybrid_exporter.py       ← NEW
│       ├── hybrid_reader.py         ← NEW
│       ├── hybrid_structures.py     ← NEW (data classes)
│       ├── ai_exporter.py           (existing)
│       ├── model_exporter.py        (existing)
│       └── dependency_analyzer.py   (existing)
├── server/
│   └── handlers/
│       ├── hybrid_analysis_handler.py  ← NEW
│       ├── __init__.py                 (update)
│       └── [other handlers...]
├── tests/
│   ├── test_hybrid_exporter.py      ← NEW
│   └── test_hybrid_reader.py        ← NEW
├── exports/
│   └── hybrid_analysis/             ← NEW (generated exports)
│       └── [analysis folders...]
├── manifest.json                    (update)
└── HYBRID_ANALYSIS_IMPLEMENTATION_PLAN.md  ← This file
```

---

## Risk Mitigation

### Risk 1: TMDL Export Performance
**Mitigation:** Leverage existing `ModelExporter` which already handles TMDL efficiently

### Risk 2: Memory Usage on Large Models
**Mitigation:**
- Incremental JSON generation (stream to file)
- Lazy loading in reader
- Batch processing

### Risk 3: Row Count Extraction Failures
**Mitigation:**
- Graceful fallback (set row_count to null)
- Clear error messages
- Optional row count extraction

### Risk 4: Token Overflow
**Mitigation:**
- Automatic batching for large results
- Truncation with warnings
- Pagination support

### Risk 5: Parquet Compatibility
**Mitigation:**
- Use standard Parquet format
- Test with both polars and pandas
- Provide CSV fallback option

---

## Success Criteria

### Functional
- ✅ Export completes in <60s for 66-table model
- ✅ All JSON files valid and complete
- ✅ TMDL can be reimported to Power BI
- ✅ Row counts accurate (±1% tolerance)
- ✅ Column usage detection 100% accurate
- ✅ Sample data preserves types and nulls

### Performance
- ✅ read_metadata: <50ms
- ✅ find_objects: <100ms
- ✅ analyze_performance (batch): <500ms
- ✅ Package size: <10MB for typical model

### Token Management
- ✅ No single response >50KB
- ✅ Batching works for 699+ measures
- ✅ Truncation warnings clear
- ✅ All responses <8K output tokens

---

## Timeline

### Day 1
**Morning (4 hours):**
- Create `hybrid_exporter.py` core structure
- Implement TMDL export integration
- Generate metadata.json and catalog.json
- Add row count extraction

**Afternoon (4 hours):**
- Implement sample data export (Parquet)
- Add column usage tracking
- Create `hybrid_reader.py`
- Implement read operations

### Day 2
**Morning (4 hours):**
- Create MCP handler integration
- Update manifest and dispatcher
- Wire up connection state
- Test basic export/read cycle

**Afternoon (4 hours):**
- Implement performance analysis
- Add recommendation generation
- Test with large model
- Fix issues and optimize

---

## Next Steps Tomorrow

1. **Start Here:** Create `core/model/hybrid_exporter.py`
2. **Reference:** Use `ai_exporter.py` as template for structure
3. **Leverage:** Reuse `ModelExporter.export_tmdl()` for TMDL layer
4. **Test Early:** Export small model first, validate structure
5. **Iterate:** Add features incrementally, test continuously

---

## Questions to Resolve

1. **Parquet vs CSV for sample data?**
   - Recommendation: Parquet (5-10x smaller, preserves types)
   - Fallback: CSV option if compatibility issues

2. **Cache location for analysis results?**
   - Recommendation: In-memory with 5-minute TTL
   - Alternative: SQLite cache file

3. **Maximum batch size?**
   - Recommendation: 50 measures per batch
   - Rationale: Keeps responses under 8K tokens

4. **Row count extraction method?**
   - Primary: DMV query (fastest)
   - Fallback: DAX COUNTROWS (slower but reliable)

---

## Additional Resources

- **Hybrid Analysis Plan:** `/home/user/MCP-DEV/hybrid-analysis-output-plan.md`
- **Current MCP Server:** `/home/user/MCP-DEV/src/pbixray_server_enhanced.py`
- **Handler Examples:** `/home/user/MCP-DEV/server/handlers/export_handler.py`
- **Exporter Reference:** `/home/user/MCP-DEV/core/model/ai_exporter.py`

---

**Ready to Code!** 🚀

Follow this plan step-by-step tomorrow. Start with Phase 1, test early, and iterate. The architecture is solid, the patterns are clear, and the path is laid out.
