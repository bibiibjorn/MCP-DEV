# Hybrid Analysis MCP Tools - Comprehensive Implementation Plan

## Executive Summary

This plan outlines the implementation of two new MCP server tools that enable Claude to efficiently analyze large Power BI models using a hybrid output format. The solution combines TMDL (for source of truth), JSON analysis files (for fast metadata), and sample data (for validation) - balancing speed, completeness, and Claude's token limits.

**Current MCP Server:** v4.2.07 with 51 tools across 13 categories
**Target:** Add 2 new tools in category "14 - Hybrid Analysis"
**Estimated Effort:** 2-3 days
**Priority:** High - enables efficient analysis of large models (66+ tables, 699+ measures)

---

## Problem Statement & Context

### Why This Approach is Needed

**Current Challenges with Large Model Analysis:**

1. **Slow Parsing:** Large model exports (66+ tables, 699+ measures) take significant time to parse
2. **Token Overflow:** Complete models can exceed Claude's 200K token context window
   - 66 tables × 20KB TMDL = 1.3MB
   - 699 measures in single file = 500KB
   - All dependencies = 200KB
   - Sample data = 5MB
   - **Total:** ~7MB raw text = ~2-3M tokens (exceeds limits by 10-15x)

3. **Mixed Access Patterns:** Need both:
   - Selective queries ("show me measure X")
   - Broad analysis ("find performance issues across entire model")

4. **Performance Analysis Overhead:** Running full analysis on every export is slow and wasteful

### Solution: Three-Layer Hybrid Architecture

**Layer 1: TMDL (Source of Truth)**
- Purpose: Complete model definition with perfect fidelity
- Access pattern: Selective file reading for specific objects
- Size: ~2MB for large model

**Layer 2: JSON Analysis (Foundation Layer)**
- Purpose: Pre-computed metadata, object catalog, and dependency graph
- Access pattern: Fast metadata queries and dependency lookups
- Size: ~255KB
- **Note:** Performance analysis and recommendations generated on-demand

**Layer 3: Sample Data (Validation Layer)**
- Purpose: Preview data for validation and example generation
- Access pattern: On-demand loading per table
- Size: ~5MB (Parquet compressed)

### Why Performance Analysis is On-Demand

**Design Philosophy:** Generate insights when needed, not upfront

**Benefits:**
- ✅ Faster exports: ~8 seconds instead of ~12 seconds
- ✅ Smaller packages: 7.3MB instead of 7.5MB
- ✅ Fresh analysis: Reflects current model state when requested
- ✅ Focused insights: Only analyze what's relevant to current query
- ✅ Flexible filtering: Can adjust priority/category without regenerating files

**Trade-offs:**
- ⚠️ First analysis request takes ~250-500ms instead of ~30ms
- ⚠️ Repeated requests without caching will re-analyze

**Mitigation:**
- MCP server implements response caching (5-minute TTL)
- First request pays 250ms cost, subsequent requests <50ms from cache
- Most queries don't need full performance analysis

**When Analysis Happens:**
1. User asks: "Find performance issues" → `analyze_performance` runs (~250ms)
2. User asks: "Recommend optimizations" → `generate_recommendations` runs (~200ms)
3. User asks: "Why is measure X slow?" → Partial analysis of that measure (~50ms)
4. User asks: "Show me DimDate table" → No analysis needed (~55ms)

**Bottom line:** Pay the analysis cost only when needed, keep everything else fast.

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

## Token Management & Context Window Strategy

### Claude's Limits

- **Context window:** 200K tokens
- **Output:** 8K tokens per response
- **Risk:** Cannot fit entire model in single conversation

### Core Principle: Never Load Entire Model

**Bad approach:**
```python
# ❌ Returns 500KB of DAX - exceeds limits
return {
  "all_measures": read_file("_measures.tmdl")  # 699 measures
}
```

**Good approach:**
```python
# ✅ Returns summary only - ~2KB
return {
  "total_measures": 699,
  "complex_measures": [
    {"name": "Rolling 12M", "complexity": 12, "line": 234},
    {"name": "Allocation %", "complexity": 8, "line": 456}
  ],
  "by_folder": {"Time Intelligence": 89, "Allocations": 67}
}
```

### Strategy 1: Hierarchical Summarization

**Process details, return only issues:**

```python
def analyze_measures_batch(measures: List[Measure]) -> Dict:
    """Analyze 50 measures, return only issues"""
    issues = []
    for measure in measures:
        # Parse full DAX (not returned to Claude)
        dax_tree = parse_dax(measure.expression)
        complexity = calculate_complexity(dax_tree)

        # Only add to results if issue found
        if complexity > 7:
            issues.append({
                "name": measure.name,
                "complexity": complexity,
                "line": measure.line_number,
                "primary_issue": identify_main_issue(dax_tree)
            })

    return {
        "measures_analyzed": len(measures),
        "issues_found": len(issues),
        "issues": issues  # Only problematic measures
    }
```

### Strategy 2: Batched Processing

**For large models, process in chunks:**

```python
# Claude calls with batch_size=50
analyze_performance({
  "batch_size": 50,
  "batch_number": 1  # Which batch (1-14 for 699 measures)
})
```

**Returns:**
```json
{
  "batch": 1,
  "total_batches": 14,
  "measures_analyzed": 50,
  "issues_found": 3,
  "next_batch": 2,
  "summary_so_far": {
    "complex_measures": 3,
    "high_priority_issues": 1
  }
}
```

**Claude workflow:**
1. Call batch 1 → Get 3 issues
2. Call batch 2 → Get 5 issues
3. Continue until complete
4. Synthesize all results

### Strategy 3: Response Size Limits

**Automatic truncation with warnings:**

```python
MAX_RESPONSE_SIZE = 50_000  # ~12K tokens

def truncate_if_needed(results: Dict) -> Dict:
    serialized = json.dumps(results)

    if len(serialized) > MAX_RESPONSE_SIZE:
        return {
            "truncated": True,
            "total_items": len(results.get('items', [])),
            "items": results['items'][:100],  # Return first 100
            "message": "Results truncated. Use pagination or filtering to see more.",
            "metadata": {
                "estimated_tokens": len(serialized) // 4,
                "max_tokens": MAX_RESPONSE_SIZE // 4
            }
        }

    return results
```

### Strategy 4: Progressive Disclosure

**Start with high-level summary, drill down on demand:**

```python
# Step 1: High-level summary
analyze_performance({"detailed": False})
# Returns: {"critical": 2, "high": 8, "medium": 15, "low": 6}

# Step 2: Get details on critical items
analyze_performance({
  "detailed": True,
  "priority": "critical"  # Only return critical items
})
# Returns: Full details for 2 critical issues

# Step 3: Get specific object definition
get_object_definition({"object_name": "Rolling 12M Average"})
# Returns: Full TMDL for just that measure
```

### Token Budget per Tool Call

| Tool | Input Tokens | Output Tokens | Total | Safe? |
|------|-------------|---------------|-------|-------|
| `read_model_metadata` | 100 | 500 | 600 | ✅ |
| `find_objects` | 200 | 1,000 | 1,200 | ✅ |
| `get_object_definition` | 500 | 2,000 | 2,500 | ✅ |
| `analyze_dependencies` | 1,000 | 3,000 | 4,000 | ✅ |
| `analyze_performance` (batch) | 5,000 | 3,000 | 8,000 | ✅ |
| `generate_recommendations` | 3,000 | 4,000 | 7,000 | ✅ |
| `get_sample_data` | 200 | 5,000 | 5,200 | ✅ |

**All tools stay well under limits by:**
- Returning summaries, not raw files
- Processing in batches when needed
- Aggregating results incrementally

---

## JSON File Format Specifications

### metadata.json

**Purpose:** High-level model statistics for quick assessment

```json
{
  "model": {
    "name": "FinvisionFamilyOffice",
    "compatibility_level": 1600,
    "default_mode": "Import",
    "culture": "en-US",
    "analysis_timestamp": "2025-11-11T10:30:00Z",
    "tmdl_export_path": "../model.bim"
  },
  "statistics": {
    "tables": {
      "total": 66,
      "fact_tables": 12,
      "dimension_tables": 54,
      "calculation_tables": 0
    },
    "columns": {
      "total": 542,
      "calculated": 45,
      "hidden": 123
    },
    "measures": {
      "total": 699,
      "by_complexity": {
        "simple": 234,
        "medium": 312,
        "complex": 153
      },
      "by_folder": {
        "Base Measures": 45,
        "Time Intelligence": 89,
        "Allocations": 67
      }
    },
    "relationships": {
      "total": 78,
      "active": 78,
      "inactive": 0,
      "bidirectional": 0,
      "many_to_many": 0
    },
    "security": {
      "roles": 3,
      "rls_tables": 8,
      "ols_objects": 0
    }
  },
  "row_counts": {
    "by_table": [
      {"table": "FactPortfolioValues", "row_count": 1245678, "last_refresh": "2025-11-11T08:30:00Z"},
      {"table": "FactTransactions", "row_count": 8934567, "last_refresh": "2025-11-11T08:30:00Z"},
      {"table": "DimDate", "row_count": 3653, "last_refresh": "2025-11-11T08:30:00Z"}
    ],
    "total_rows": 15234567,
    "largest_fact_tables": [
      {"name": "FactTransactions", "rows": 8934567},
      {"name": "FactPortfolioValues", "rows": 1245678}
    ]
  },
  "model_size_estimate": {
    "total_rows": 15234567,
    "estimated_memory_mb": 2847,
    "largest_tables": [
      {"name": "FactPortfolioValues", "rows": 1245678, "mb": 456},
      {"name": "FactTransactions", "rows": 8934567, "mb": 1234}
    ]
  }
}
```

**Size:** ~5KB
**Usage:** First file Claude reads to understand model scope

---

### catalog.json

**Purpose:** Fast lookup index for finding objects with usage tracking

```json
{
  "tables": [
    {
      "name": "DimDate",
      "type": "dimension",
      "tmdl_path": "model.bim/tables/DimDate.tmdl",
      "column_count": 15,
      "row_count": 3653,
      "relationship_count": 12,
      "has_sample_data": true,
      "sample_data_path": "sample_data/DimDate.parquet",
      "columns": [
        {
          "name": "Date",
          "data_type": "DateTime",
          "is_key": true,
          "is_hidden": false,
          "used_in_relationships": true,
          "used_in_measures": true,
          "used_in_visuals": true,
          "measure_references": 89,
          "is_unused": false
        },
        {
          "name": "FiscalQuarterOrder",
          "data_type": "Int64",
          "is_key": false,
          "is_hidden": true,
          "used_in_relationships": false,
          "used_in_measures": false,
          "used_in_visuals": false,
          "measure_references": 0,
          "is_unused": true,
          "cardinality": 12,
          "estimated_memory_mb": 0.01
        }
      ],
      "unused_columns": ["FiscalQuarterOrder"]
    },
    {
      "name": "FactPortfolioValues",
      "type": "fact",
      "tmdl_path": "model.bim/tables/FactPortfolioValues.tmdl",
      "column_count": 8,
      "row_count": 1245678,
      "relationship_count": 5,
      "columns": [
        {
          "name": "TransactionID",
          "data_type": "String",
          "is_key": false,
          "is_hidden": false,
          "used_in_relationships": false,
          "used_in_measures": false,
          "used_in_visuals": false,
          "measure_references": 0,
          "is_unused": true,
          "cardinality": 1245678,
          "cardinality_ratio": 1.0,
          "estimated_memory_mb": 45
        }
      ],
      "unused_columns": ["TransactionID"]
    }
  ],
  "measures": [
    {
      "name": "Total Market Value",
      "table": "FactPortfolioValues",
      "display_folder": "Base Measures",
      "tmdl_path": "model.bim/expressions/_measures.tmdl",
      "line_number": 45,
      "complexity_score": 1,
      "dependencies": ["FactPortfolioValues[MarketValue]"]
    },
    {
      "name": "Total Market Value YTD",
      "table": "FactPortfolioValues",
      "display_folder": "Time Intelligence/YTD",
      "tmdl_path": "model.bim/expressions/_measures.tmdl",
      "line_number": 52,
      "complexity_score": 3,
      "dependencies": ["[Total Market Value]", "DimDate[Date]"]
    }
  ],
  "relationships_path": "model.bim/relationships/relationships.tmdl",
  "roles": [
    {
      "name": "AdvisorView",
      "tmdl_path": "model.bim/roles/AdvisorView.tmdl",
      "table_count": 8
    }
  ]
}
```

**Size:** ~50KB
**Usage:** Enables queries like "find all measures in folder X" or "which columns are unused"

---

### dependencies.json

**Purpose:** Pre-computed dependency graph for impact analysis

```json
{
  "measures": {
    "Total Market Value YTD": {
      "direct_dependencies": {
        "measures": ["Total Market Value"],
        "tables": ["DimDate"],
        "columns": ["DimDate[Date]", "FactPortfolioValues[MarketValue]"]
      },
      "all_dependencies": {
        "measures": ["Total Market Value"],
        "tables": ["FactPortfolioValues", "DimDate"],
        "columns": ["FactPortfolioValues[MarketValue]", "DimDate[Date]"]
      },
      "dependent_measures": [
        "Total Market Value YTD vs PY",
        "Total Market Value YTD %"
      ],
      "dependency_depth": 2
    }
  },
  "tables": {
    "DimDate": {
      "dependent_relationships": 12,
      "dependent_measures": 89,
      "dependent_rls_roles": 0,
      "is_date_table": true
    }
  },
  "circular_dependencies": [],
  "orphaned_measures": [],
  "unused_tables": []
}
```

**Size:** ~200KB
**Usage:** Answer "what breaks if I change X?" or "what uses this measure?"

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

---

## Usage Examples & Claude Workflows

### Example 1: Quick Model Assessment

**User:** "Give me a summary of this model"

**Claude workflow:**
```python
# Step 1: Read metadata
result = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "read_metadata"
})
# Returns: Model statistics in ~25ms

# Claude synthesizes response:
# "This model has 66 tables (12 fact, 54 dimension),
#  699 measures, 78 relationships, and 15M total rows..."
```

**Tokens used:** ~600

---

### Example 2: Find Performance Issues

**User:** "Find all performance issues and recommend fixes"

**Claude workflow:**
```python
# Step 1: Overview
metadata = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "read_metadata"
})
# Returns: 66 tables, 699 measures

# Step 2: Analyze in batches
for batch in range(1, 15):  # 14 batches for 699 measures
    result = analyze_hybrid_model({
        "analysis_path": "/exports/FamilyOffice_20250111/",
        "operation": "analyze_performance",
        "performance_focus": ["dax_complexity", "cardinality", "unused_columns"],
        "batch_config": {
            "enabled": True,
            "batch_size": 50,
            "batch_number": batch
        }
    })
    # Each batch returns issues for 50 measures
    # Accumulate results

# Step 3: Generate recommendations
recommendations = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "generate_recommendations",
    "recommendation_filters": {
        "min_priority": "high",
        "max_recommendations": 20
    }
})
# Returns: Top 20 actionable recommendations

# Claude synthesizes all findings and presents to user
```

**Total calls:** ~20
**Total tokens:** ~80,000 (well under 200K limit)
**Time:** ~8 seconds

---

### Example 3: Investigate Specific Measure

**User:** "Why is 'Rolling 12M Average' slow?"

**Claude workflow:**
```python
# Step 1: Find the measure
measures = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "find_objects",
    "object_filter": {
        "object_type": "measure",
        "name_contains": "Rolling 12M"
    }
})
# Returns: Measure location in catalog (~20ms)

# Step 2: Get full definition
definition = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "get_object_definition",
    "object_name": "Rolling 12M Average"
})
# Returns: Full TMDL + dependencies (~50ms)

# Step 3: Analyze dependencies
deps = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "analyze_dependencies",
    "object_name": "Rolling 12M Average"
})
# Returns: What this measure depends on and what depends on it

# Step 4: Performance analysis (focused)
perf = analyze_hybrid_model({
    "analysis_path": "/exports/FamilyOffice_20250111/",
    "operation": "analyze_performance",
    "performance_focus": ["dax_complexity"],
    "object_filter": {
        "object_type": "measure",
        "name_contains": "Rolling 12M"
    }
})
# Returns: Complexity analysis with recommendations

# Claude provides detailed answer with specific optimization suggestions
```

**Total calls:** 4
**Total tokens:** ~10,000
**Time:** ~200ms

---

## Implementation Phases

### Phase 1: Core Export Infrastructure (Day 1 Morning - 4 hours)

**Files to Create:**
1. `core/model/hybrid_exporter.py` - Main exporter class
2. `core/model/hybrid_structures.py` - Data classes for JSON structures

**Tasks:**
- [ ] Create `HybridAnalysisExporter` class
- [ ] Implement TMDL export via existing `ModelExporter`
- [ ] Generate `metadata.json` (model statistics + row counts)
- [ ] Generate `catalog.json` (object index with column usage tracking)
- [ ] Generate `dependencies.json` (from `DependencyAnalyzer`)
- [ ] Export sample data as Parquet (via polars/pyarrow)
- [ ] Add row count extraction via single DMV query
- [ ] Add column usage tracking (relationships/measures/visuals/RLS)
- [ ] Add cardinality calculation for columns

**Code Skeleton:**
```python
# core/model/hybrid_exporter.py
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import polars as pl
from datetime import datetime

logger = logging.getLogger(__name__)

class HybridAnalysisExporter:
    """Export Power BI model to hybrid analysis format"""

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
        start_time = datetime.now()
        output_path = Path(output_dir)

        try:
            # 1. Create folder structure
            self._create_folder_structure(output_path)

            # 2. Export TMDL via model_exporter
            tmdl_path = output_path / "model.bim"
            self.model_exporter.export_tmdl(str(tmdl_path))

            # 3. Extract row counts (single DMV query)
            row_counts = {}
            if include_row_counts:
                row_counts = self._extract_row_counts_bulk()

            # 4. Track column usage
            column_usage = {}
            if track_column_usage:
                column_usage = self._track_column_usage()

            # 5. Generate metadata.json
            metadata = self._generate_metadata(row_counts)
            self._save_json(output_path / "analysis" / "metadata.json", metadata)

            # 6. Generate catalog.json (with usage tracking)
            catalog = self._generate_catalog(row_counts, column_usage)
            self._save_json(output_path / "analysis" / "catalog.json", catalog)

            # 7. Generate dependencies.json
            dependencies = self._generate_dependencies()
            self._save_json(output_path / "analysis" / "dependencies.json", dependencies)

            # 8. Export sample data (parallel)
            if include_sample_data:
                self._export_sample_data_parallel(output_path / "sample_data", sample_rows)

            # 9. Collect statistics
            stats = self._collect_statistics(output_path)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "output_path": str(output_path),
                "structure": {
                    "tmdl_path": "model.bim/",
                    "analysis_path": "analysis/",
                    "sample_data_path": "sample_data/",
                    "file_counts": stats["file_counts"]
                },
                "statistics": stats["statistics"],
                "generation_time_seconds": duration,
                "note": "Performance analysis and recommendations generated on-demand"
            }

        except Exception as e:
            logger.error(f"Error exporting hybrid analysis: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "export_failed"
            }

    def _extract_row_counts_bulk(self) -> Dict[str, int]:
        """Extract row counts for all tables via single DMV query"""
        query = """
        SELECT
            [DIMENSION_NAME] as TableName,
            SUM([ROWS_COUNT]) as RowCount
        FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
        GROUP BY [DIMENSION_NAME]
        """
        result = self.query_executor.execute_dmv_query(query)
        return {row["TableName"]: row["RowCount"] for row in result}

    def _track_column_usage(self) -> Dict[str, Dict]:
        """Track which columns are used in measures/relationships/visuals/RLS"""
        # Implementation: Parse all DAX, check relationships, RLS filters
        pass

    def _export_sample_data_parallel(self, output_dir: Path, sample_rows: int):
        """Export sample data in parallel using ThreadPoolExecutor"""
        import concurrent.futures

        tables = self._get_all_tables()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._export_table_sample, table, output_dir, sample_rows): table
                for table in tables
            }

            for future in concurrent.futures.as_completed(futures):
                table = futures[future]
                try:
                    future.result()
                    logger.debug(f"Exported sample data for {table}")
                except Exception as e:
                    logger.error(f"Error exporting {table}: {e}")

    def _export_table_sample(self, table_name: str, output_dir: Path, sample_rows: int):
        """Export sample data for single table as Parquet"""
        dax_query = f"EVALUATE TOPN({sample_rows}, '{table_name}')"
        result = self.query_executor.execute_dax_query(dax_query)

        # Convert to polars DataFrame and write as Parquet
        df = pl.DataFrame(result)
        output_file = output_dir / f"{table_name}.parquet"
        df.write_parquet(output_file, compression="snappy")
```

**Key Optimizations:**
1. **Single DMV query** for all row counts (66x faster than per-table)
2. **Parallel sample data export** (4x faster with ThreadPoolExecutor)
3. **Incremental JSON writing** (avoids loading full model in memory)
4. **Polars for Parquet** (5-10x faster than pandas)

---

### Phase 2: Analysis Reader (Day 1 Afternoon - 4 hours)

**Files to Create:**
1. `core/model/hybrid_reader.py` - Reader for hybrid structure

**Tasks:**
- [ ] Create `HybridAnalysisReader` class
- [ ] Implement JSON file readers (metadata/catalog/dependencies) with lazy loading
- [ ] Implement TMDL file reader (selective loading with caching)
- [ ] Implement Parquet reader (with column selection)
- [ ] Add on-demand performance analysis
- [ ] Add recommendation generation
- [ ] Implement batching for large models
- [ ] Add response truncation logic

**Code Skeleton:**
```python
# core/model/hybrid_reader.py
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache
import polars as pl

logger = logging.getLogger(__name__)

class HybridAnalysisReader:
    """Read and analyze hybrid model structure"""

    def __init__(self, analysis_path: str):
        self.analysis_path = Path(analysis_path)
        self._metadata = None
        self._catalog = None
        self._dependencies = None
        self._cache = {}

    # Lazy loading properties
    @property
    def metadata(self) -> Dict[str, Any]:
        """Lazy load metadata.json"""
        if self._metadata is None:
            with open(self.analysis_path / "analysis" / "metadata.json") as f:
                self._metadata = json.load(f)
        return self._metadata

    @property
    def catalog(self) -> Dict[str, Any]:
        """Lazy load catalog.json"""
        if self._catalog is None:
            with open(self.analysis_path / "analysis" / "catalog.json") as f:
                self._catalog = json.load(f)
        return self._catalog

    @property
    def dependencies(self) -> Dict[str, Any]:
        """Lazy load dependencies.json"""
        if self._dependencies is None:
            with open(self.analysis_path / "analysis" / "dependencies.json") as f:
                self._dependencies = json.load(f)
        return self._dependencies

    def read_metadata(self) -> Dict[str, Any]:
        """Read metadata.json"""
        return {
            "success": True,
            "metadata": self.metadata,
            "source": "metadata.json"
        }

    def find_objects(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Search catalog.json with filters"""
        object_type = filters.get("object_type")
        name_contains = filters.get("name_contains", "").lower()
        table_filter = filters.get("table")
        complexity_min = filters.get("complexity_min")

        results = []

        if object_type == "table" or object_type is None:
            for table in self.catalog.get("tables", []):
                if name_contains and name_contains not in table["name"].lower():
                    continue
                results.append({"type": "table", **table})

        if object_type == "measure" or object_type is None:
            for measure in self.catalog.get("measures", []):
                if name_contains and name_contains not in measure["name"].lower():
                    continue
                if table_filter and measure.get("table") != table_filter:
                    continue
                if complexity_min and measure.get("complexity_score", 0) < complexity_min:
                    continue
                results.append({"type": "measure", **measure})

        # Truncate if needed
        return self._truncate_if_needed({
            "success": True,
            "total_matches": len(results),
            "matches": results
        })

    @lru_cache(maxsize=100)
    def _read_tmdl_file(self, file_path: str) -> str:
        """Read TMDL file with caching"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_object_definition(self, object_name: str, object_type: str = "measure") -> Dict[str, Any]:
        """Get TMDL definition + dependencies"""
        # Find object in catalog
        obj = None
        for item in self.catalog.get("measures" if object_type == "measure" else "tables", []):
            if item["name"] == object_name:
                obj = item
                break

        if not obj:
            return {
                "success": False,
                "error": f"{object_type} '{object_name}' not found"
            }

        # Read TMDL
        tmdl_path = self.analysis_path / obj["tmdl_path"]
        tmdl_content = self._read_tmdl_file(str(tmdl_path))

        # Extract specific definition (for measures file)
        if object_type == "measure" and "line_number" in obj:
            tmdl_content = self._extract_measure_from_file(tmdl_content, obj["line_number"])

        # Get dependencies
        deps = self.dependencies.get("measures", {}).get(object_name, {})

        return {
            "success": True,
            "object_name": object_name,
            "object_type": object_type,
            "tmdl_definition": tmdl_content,
            "dependencies": deps.get("direct_dependencies", {}),
            "dependent_objects": deps.get("dependent_measures", []),
            "tmdl_path": obj["tmdl_path"]
        }

    def analyze_performance(
        self,
        focus_areas: List[str],
        batch_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate performance analysis on-demand"""
        batch_enabled = batch_config and batch_config.get("enabled", True)
        batch_size = batch_config.get("batch_size", 50) if batch_config else 50
        batch_number = batch_config.get("batch_number") if batch_config else None

        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "focus_areas": focus_areas
        }

        # Analyze based on focus areas
        if "unused_columns" in focus_areas or "all" in focus_areas:
            results["unused_columns"] = self._find_unused_columns()

        if "dax_complexity" in focus_areas or "all" in focus_areas:
            if batch_enabled and batch_number:
                results["complex_measures"] = self._analyze_dax_complexity_batch(batch_size, batch_number)
                results["batch_info"] = {
                    "batch_number": batch_number,
                    "batch_size": batch_size,
                    "total_measures": len(self.catalog.get("measures", [])),
                    "total_batches": (len(self.catalog.get("measures", [])) + batch_size - 1) // batch_size
                }
            else:
                results["complex_measures"] = self._analyze_dax_complexity_all()

        if "cardinality" in focus_areas or "all" in focus_areas:
            results["high_cardinality_columns"] = self._find_high_cardinality_columns()

        if "row_counts" in focus_areas or "all" in focus_areas:
            results["row_count_analysis"] = self._analyze_row_counts()

        # Truncate if needed
        return self._truncate_if_needed(results)

    def _find_unused_columns(self) -> List[Dict]:
        """Find all unused columns with memory impact"""
        unused = []
        for table in self.catalog.get("tables", []):
            for col in table.get("columns", []):
                if col.get("is_unused", False):
                    unused.append({
                        "table": table["name"],
                        "column": col["name"],
                        "data_type": col["data_type"],
                        "cardinality": col.get("cardinality"),
                        "estimated_memory_mb": col.get("estimated_memory_mb", 0),
                        "priority": self._calculate_priority(col),
                        "tmdl_location": table["tmdl_path"]
                    })

        # Sort by memory impact
        unused.sort(key=lambda x: x["estimated_memory_mb"], reverse=True)
        return unused

    def _analyze_dax_complexity_batch(self, batch_size: int, batch_number: int) -> List[Dict]:
        """Analyze DAX complexity for a batch of measures"""
        measures = self.catalog.get("measures", [])
        start = (batch_number - 1) * batch_size
        end = start + batch_size
        batch = measures[start:end]

        complex_measures = []
        for measure in batch:
            if measure.get("complexity_score", 0) > 7:
                complex_measures.append({
                    "name": measure["name"],
                    "table": measure.get("table"),
                    "complexity_score": measure["complexity_score"],
                    "tmdl_location": f"{measure['tmdl_path']}:{measure.get('line_number')}",
                    "priority": "high" if measure["complexity_score"] > 10 else "medium"
                })

        return complex_measures

    def _truncate_if_needed(self, data: Dict, max_tokens: int = 12000) -> Dict:
        """Truncate response if too large"""
        serialized = json.dumps(data)
        estimated_tokens = len(serialized) // 4

        if estimated_tokens > max_tokens:
            # Add truncation warning
            data["truncated"] = True
            data["metadata"] = {
                "estimated_tokens": estimated_tokens,
                "max_tokens": max_tokens,
                "note": "Results truncated. Use filters or pagination to see more."
            }

            # Truncate lists
            for key in ["matches", "unused_columns", "complex_measures"]:
                if key in data and isinstance(data[key], list):
                    original_count = len(data[key])
                    data[key] = data[key][:20]  # Keep first 20
                    data["metadata"][f"{key}_truncated_from"] = original_count

        return data

    def generate_recommendations(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate prioritized recommendations"""
        min_priority = filters.get("min_priority", "high")
        category = filters.get("category", "all")
        max_recommendations = filters.get("max_recommendations", 20)

        recommendations = []

        # Generate from unused columns
        unused_cols = self._find_unused_columns()
        for col in unused_cols[:10]:  # Top 10 by memory
            if col["estimated_memory_mb"] > 5:
                recommendations.append({
                    "id": f"PERF-{len(recommendations)+1:03d}",
                    "category": "Performance",
                    "priority": col["priority"],
                    "title": f"Remove unused column '{col['column']}' in {col['table']}",
                    "impact": {
                        "memory_savings_mb": col["estimated_memory_mb"],
                        "performance_improvement": "5-10%"
                    },
                    "implementation": {
                        "steps": [
                            "Verify column not used in any reports",
                            "Delete column from Power Query",
                            "Refresh model",
                            "Verify memory reduction"
                        ],
                        "estimated_time_minutes": 15
                    }
                })

        # Generate from complex measures
        complex = self._analyze_dax_complexity_all()
        for measure in complex[:10]:  # Top 10 by complexity
            recommendations.append({
                "id": f"DAX-{len(recommendations)+1:03d}",
                "category": "DAX Optimization",
                "priority": measure["priority"],
                "title": f"Optimize '{measure['name']}' measure",
                "impact": {
                    "performance_improvement": "30-50%"
                },
                "implementation": {
                    "current_location": measure["tmdl_location"],
                    "steps": [
                        "Review DAX for nested CALCULATE",
                        "Consider using variables",
                        "Test optimization",
                        "Update dependent measures if needed"
                    ],
                    "estimated_time_minutes": 30
                }
            })

        # Filter and limit
        if min_priority != "all":
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            min_level = priority_order[min_priority]
            recommendations = [r for r in recommendations if priority_order[r["priority"]] <= min_level]

        if category != "all":
            recommendations = [r for r in recommendations if r["category"].lower() == category.lower()]

        recommendations = recommendations[:max_recommendations]

        return {
            "success": True,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "truncated": len(recommendations) == max_recommendations,
            "note": "Use filters to see more specific recommendations"
        }
```

**Key Optimizations:**
1. **Lazy loading** of JSON files (only load when accessed)
2. **LRU cache** for TMDL files (100 most recent)
3. **Automatic truncation** with warnings
4. **Batched processing** for large measure sets

---

### Phase 3: MCP Handler Integration (Day 2 Morning - 4 hours)

**Files to Create:**
1. `server/handlers/hybrid_analysis_handler.py`

**Tasks:**
- [ ] Create handler registration function
- [ ] Implement `handle_export_hybrid_analysis`
- [ ] Implement `handle_analyze_hybrid_model`
- [ ] Add to `server/handlers/__init__.py`
- [ ] Update `server/dispatch.py` TOOL_NAME_MAP
- [ ] Update `manifest.json` with new tools

**Code:** *(See previous version - remains the same)*

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
      "description": "[14-Hybrid] Export model to hybrid analysis format optimized for Claude"
    },
    {
      "name": "14_analyze_hybrid_model",
      "description": "[14-Hybrid] Analyze hybrid model with token-aware operations"
    }
  ]
}
```

---

### Phase 4: Testing & Validation (Day 2 Afternoon - 4 hours)

**Test Scenarios:**

1. **Small Model Test** (10 tables, 100 measures)
   - Export completes in <10 seconds ✓
   - All files generated correctly ✓
   - Metadata accurate ✓
   - Sample data valid ✓

2. **Large Model Test** (66 tables, 699 measures)
   - Export completes in <60 seconds ✓
   - Row counts match actual data (±1%) ✓
   - Column usage detection accurate (100%) ✓
   - Performance analysis generates correctly ✓
   - Batching works properly ✓

3. **Token Limit Tests**
   - analyze_performance with batch_size=50 stays under 8K tokens ✓
   - Recommendations truncate properly at max_recommendations ✓
   - No single response exceeds 50KB ✓

4. **Error Handling**
   - Invalid analysis path returns clear error ✓
   - Missing connection handled gracefully ✓
   - Corrupted JSON files detected ✓

**Test Files to Create:**
```python
# tests/test_hybrid_exporter.py
import pytest
from core.model.hybrid_exporter import HybridAnalysisExporter

def test_export_small_model():
    """Test export on small model"""
    # Implementation

def test_export_large_model():
    """Test export on large model (66 tables)"""
    # Implementation

def test_row_count_accuracy():
    """Verify row counts match DMV results"""
    # Implementation

def test_column_usage_detection():
    """Verify unused column detection"""
    # Implementation

def test_parallel_sample_export():
    """Verify parallel export works correctly"""
    # Implementation

# tests/test_hybrid_reader.py
def test_read_metadata():
    """Test metadata reading"""
    # Implementation

def test_find_objects():
    """Test object search"""
    # Implementation

def test_performance_analysis_batching():
    """Test batching for large models"""
    # Implementation

def test_token_limits():
    """Ensure responses stay under limits"""
    # Implementation

def test_lazy_loading():
    """Verify lazy loading works"""
    # Implementation
```

---

## Comprehensive Optimization Guide

### 1. Export Performance Optimizations

#### A. Row Count Extraction
```python
# ❌ BAD: Individual queries (66x slower)
row_counts = {}
for table in tables:
    query = f"SELECT COUNT(*) FROM '{table}'"
    row_counts[table] = execute_query(query)

# ✅ GOOD: Single DMV query
query = """
SELECT
    [DIMENSION_NAME] as TableName,
    SUM([ROWS_COUNT]) as RowCount
FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
GROUP BY [DIMENSION_NAME]
"""
row_counts = {row["TableName"]: row["RowCount"] for row in execute_dmv(query)}
```

**Impact:** 66x faster for large models

---

#### B. Parallel Sample Data Export
```python
# ❌ BAD: Sequential export
for table in tables:
    export_table_sample(table)

# ✅ GOOD: Parallel with ThreadPoolExecutor
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(export_table_sample, table): table
        for table in tables
    }

    for future in concurrent.futures.as_completed(futures):
        try:
            future.result()
        except Exception as e:
            logger.error(f"Export failed: {e}")
```

**Impact:** 4x faster with 4 workers

---

#### C. Incremental JSON Generation
```python
# ❌ BAD: Load full model in memory
all_tables = []
for table in tables:
    all_tables.append(process_table(table))
with open('catalog.json', 'w') as f:
    json.dump({"tables": all_tables}, f)

# ✅ GOOD: Stream to file
with open('catalog.json', 'w') as f:
    f.write('{"tables": [\n')
    for i, table in enumerate(tables):
        json.dump(process_table(table), f, indent=2)
        if i < len(tables) - 1:
            f.write(',\n')
    f.write('\n]}\n')
```

**Impact:** Prevents memory issues on 200+ table models

---

#### D. Polars for Parquet I/O
```python
# ❌ BAD: Use pandas (slower)
import pandas as pd
df = pd.DataFrame(data)
df.to_parquet('output.parquet')

# ✅ GOOD: Use polars (5-10x faster)
import polars as pl
df = pl.DataFrame(data)
df.write_parquet('output.parquet', compression='snappy')
```

**Impact:** 5-10x faster Parquet generation

---

### 2. Analysis Performance Optimizations

#### A. Lazy Loading
```python
# ❌ BAD: Load all JSON files upfront
def __init__(self, path):
    self.metadata = json.load(open(f"{path}/metadata.json"))
    self.catalog = json.load(open(f"{path}/catalog.json"))
    self.dependencies = json.load(open(f"{path}/dependencies.json"))

# ✅ GOOD: Load on first access
def __init__(self, path):
    self.path = path
    self._metadata = None
    self._catalog = None
    self._dependencies = None

@property
def metadata(self):
    if self._metadata is None:
        with open(f"{self.path}/metadata.json") as f:
            self._metadata = json.load(f)
    return self._metadata
```

**Impact:** <50ms for metadata-only queries

---

#### B. TMDL Caching
```python
# ❌ BAD: Read file every time
def read_tmdl(self, path):
    with open(path) as f:
        return f.read()

# ✅ GOOD: LRU cache
from functools import lru_cache

@lru_cache(maxsize=100)
def read_tmdl(self, path):
    with open(path) as f:
        return f.read()
```

**Impact:** 10x faster repeated reads

---

#### C. Batched Analysis
```python
# ❌ BAD: Return all 699 measures
def analyze_measures(self):
    return analyze_all_measures()  # Returns 500KB

# ✅ GOOD: Return batches of 50
def analyze_measures_batch(self, batch_num, batch_size=50):
    start = (batch_num - 1) * batch_size
    end = start + batch_size
    return analyze_measures(measures[start:end])
```

**Impact:** Stays under 8K token limit

---

### 3. Token Management Optimizations

#### A. Hierarchical Summarization
```python
# ❌ BAD: Return full DAX expressions
def get_measures(self):
    return [
        {"name": m.name, "dax": m.expression}  # Full DAX
        for m in measures
    ]

# ✅ GOOD: Return summaries with references
def get_measures(self):
    return [
        {
            "name": m.name,
            "complexity": calculate_complexity(m.expression),
            "tmdl_location": f"{m.file}:{m.line}",
            # DAX not included, available via get_object_definition
        }
        for m in measures
    ]
```

**Impact:** 90% size reduction

---

#### B. Automatic Truncation
```python
MAX_RESPONSE_SIZE = 50_000  # ~12K tokens

def truncate_if_needed(data: Dict) -> Dict:
    serialized = json.dumps(data)
    estimated_tokens = len(serialized) // 4

    if estimated_tokens > 12000:
        data["truncated"] = True
        data["metadata"] = {
            "estimated_tokens": estimated_tokens,
            "note": "Results truncated. Use filters to see more."
        }

        # Truncate lists
        for key, value in list(data.items()):
            if isinstance(value, list) and len(value) > 20:
                data[key] = value[:20]

    return data
```

**Impact:** Prevents token overflow

---

#### C. Progressive Disclosure
```python
# Step 1: High-level summary
{
  "critical_issues": 2,
  "high_priority": 8,
  "medium_priority": 15
}

# Step 2: Details for critical only
{
  "critical_issues": [
    {"id": "PERF-001", "title": "...", "details": "..."},
    {"id": "PERF-002", "title": "...", "details": "..."}
  ]
}

# Step 3: Specific object if needed
{
  "object_name": "Rolling 12M",
  "full_definition": "...",
  "analysis": "..."
}
```

**Impact:** Users see what they need, when they need it

---

## Complete File Size Breakdown

### TMDL Files
```
Tables: ~5-20KB per table = 330KB - 1.3MB (66 tables)
Relationships: ~10-50KB total
Measures: ~100-500KB (699 measures in one file)
Roles: ~5KB per role
Total TMDL: ~500KB - 2MB
```

### JSON Analysis
```
metadata.json: ~5KB
catalog.json: ~50KB (66 tables + 699 measures)
dependencies.json: ~200KB (full graph)
Total Analysis: ~255KB
```

### Sample Data (Parquet)
```
Parquet compression: 5-10x vs CSV
1000 rows × 10 columns × 66 tables = ~5-15MB raw
Total with compression: ~2-5MB
```

### Complete Package
```
TMDL: 2MB
Analysis: 0.26MB
Sample Data: 5MB
Total: ~7.3MB
```

**For 66-table, 699-measure model: ~7.3MB** (vs 50-100MB for raw exports)

---

## Dependencies

### Python Packages Required

```txt
# Already in project
pythonnet>=3.0.0

# NEW - Add these
polars>=0.19.0  # Fast Parquet I/O
pyarrow>=14.0.0  # Parquet format support
```

### Installation

```bash
pip install polars pyarrow
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
- Parallel export with limited workers

### Risk 3: Row Count Extraction Failures
**Mitigation:**
- Graceful fallback (set row_count to null)
- Clear error messages
- Optional row count extraction (can skip if fails)

### Risk 4: Token Overflow
**Mitigation:**
- Automatic batching for large results
- Truncation with clear warnings
- Pagination support
- Response size estimation

### Risk 5: Parquet Compatibility
**Mitigation:**
- Use standard Parquet format (Apache Arrow)
- Test with both polars and pandas
- Provide CSV fallback option
- Document compression settings

### Risk 6: Column Usage Detection Accuracy
**Mitigation:**
- Multi-layered detection (relationships + measures + visuals + RLS)
- Conservative approach (when in doubt, don't mark as unused)
- Spot-check validation (20+ columns manually verified)
- Include "confidence" score in results

---

## Success Criteria

### Functional Requirements
- ✅ Export completes in <60s for 66-table model
- ✅ All JSON files valid and complete
- ✅ TMDL can be reimported to Power BI without errors
- ✅ Row counts accurate (±1% tolerance)
- ✅ Column usage detection 100% accurate (no false positives)
- ✅ Sample data preserves types and nulls
- ✅ Dependencies graph 100% accurate

### Performance Requirements
- ✅ read_metadata: <50ms
- ✅ find_objects: <100ms
- ✅ get_object_definition: <200ms
- ✅ analyze_performance (batch): <500ms
- ✅ generate_recommendations: <500ms
- ✅ Package size: <10MB for typical model

### Token Management Requirements
- ✅ No single response >50KB
- ✅ Batching works for 699+ measures
- ✅ Truncation warnings clear and actionable
- ✅ All responses <8K output tokens
- ✅ Token usage metadata included in responses

### User Experience Requirements
- ✅ Claude can answer queries in 1-2 tool calls
- ✅ Single export supports multiple analysis sessions
- ✅ Clear file organization (obvious where to look)
- ✅ Actionable recommendations with implementation steps
- ✅ Error messages include remediation steps

---

## Timeline

### Day 1
**Morning (4 hours):**
- ✅ Create `hybrid_exporter.py` core structure
- ✅ Implement TMDL export integration
- ✅ Generate metadata.json and catalog.json
- ✅ Add row count extraction (optimized single query)
- ✅ Add column usage tracking

**Afternoon (4 hours):**
- ✅ Implement sample data export (Parquet with parallel processing)
- ✅ Create `hybrid_reader.py`
- ✅ Implement read operations (with lazy loading)
- ✅ Add TMDL caching

### Day 2
**Morning (4 hours):**
- ✅ Create MCP handler integration
- ✅ Update manifest and dispatcher
- ✅ Wire up connection state
- ✅ Test basic export/read cycle
- ✅ Verify token management works

**Afternoon (4 hours):**
- ✅ Implement performance analysis (with batching)
- ✅ Add recommendation generation
- ✅ Test with large model (66 tables, 699 measures)
- ✅ Validate token limits respected
- ✅ Fix issues and optimize
- ✅ Create test suite

---

## Next Steps Tomorrow

1. **Start Here:** Create `core/model/hybrid_exporter.py`
2. **Reference:** Use `ai_exporter.py` as template for structure
3. **Leverage:** Reuse `ModelExporter.export_tmdl()` for TMDL layer
4. **Test Early:** Export small model first, validate structure
5. **Iterate:** Add features incrementally, test continuously

### Step-by-Step Checklist

**Morning Session:**
- [ ] Create `core/model/hybrid_structures.py` (data classes)
- [ ] Create `core/model/hybrid_exporter.py` skeleton
- [ ] Implement folder structure creation
- [ ] Integrate TMDL export (use existing ModelExporter)
- [ ] Implement bulk row count extraction (single DMV query)
- [ ] Test on small model (10 tables)
- [ ] Implement column usage tracking
- [ ] Generate metadata.json and catalog.json
- [ ] Test JSON validity

**Afternoon Session:**
- [ ] Implement parallel sample data export (ThreadPoolExecutor)
- [ ] Test Parquet generation (polars)
- [ ] Generate dependencies.json (use DependencyAnalyzer)
- [ ] Create `core/model/hybrid_reader.py`
- [ ] Implement lazy loading properties
- [ ] Implement read_metadata operation
- [ ] Implement find_objects operation
- [ ] Add LRU cache for TMDL files
- [ ] Test reader on exported model

---

## Questions & Decisions

### 1. Parquet vs CSV for sample data?
**Decision:** Parquet (5-10x smaller, preserves types)
**Fallback:** CSV option if compatibility issues arise

### 2. Cache location for analysis results?
**Decision:** In-memory with 5-minute TTL
**Alternative:** SQLite cache file for persistence

### 3. Maximum batch size?
**Decision:** 50 measures per batch
**Rationale:** Keeps responses under 8K tokens

### 4. Row count extraction method?
**Decision:** Primary = DMV query (fastest), Fallback = DAX COUNTROWS
**Rationale:** DMV is 10x faster but may fail on some sources

### 5. Column usage confidence threshold?
**Decision:** Mark as unused only if 100% confident
**Rationale:** False positive (marking used column as unused) is worse than false negative

---

## Additional Resources

- **Original Hybrid Analysis Plan:** `/home/user/MCP-DEV/hybrid-analysis-output-plan.md` (2,785 lines)
- **Current MCP Server:** `/home/user/MCP-DEV/src/pbixray_server_enhanced.py`
- **Handler Examples:** `/home/user/MCP-DEV/server/handlers/export_handler.py`
- **Exporter Reference:** `/home/user/MCP-DEV/core/model/ai_exporter.py`
- **Registry System:** `/home/user/MCP-DEV/server/registry.py`
- **Dispatcher:** `/home/user/MCP-DEV/server/dispatch.py`

---

## Summary

This comprehensive implementation plan provides:

✅ **Complete Context** - Why this approach solves the large model analysis problem
✅ **Detailed Architecture** - Three-layer design with token management strategy
✅ **Code Skeletons** - Ready-to-implement classes with optimization examples
✅ **File Format Specs** - Exact JSON structure for all analysis files
✅ **Usage Examples** - Real Claude workflows demonstrating the tools
✅ **Optimization Guide** - 12+ specific optimization techniques with code
✅ **Test Scenarios** - Comprehensive test cases with success criteria
✅ **Risk Mitigation** - Identified risks with concrete mitigation strategies
✅ **Timeline** - Hour-by-hour breakdown for 2-day implementation

**Ready to Code!** 🚀

Follow this plan step-by-step tomorrow. The architecture is solid, the optimizations are proven, and the path is clear. Start with Phase 1 (Export Infrastructure), test early with small models, and iterate rapidly. By end of Day 2, you'll have two powerful MCP tools that enable Claude to efficiently analyze models of any size.
