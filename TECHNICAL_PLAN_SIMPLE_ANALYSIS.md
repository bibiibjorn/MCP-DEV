# Technical Implementation Plan: Simplified Model Analysis

**Version**: 1.0
**Date**: 2025-11-19
**Feature**: Tool 05 Enhancement - Simple Analysis Mode
**Status**: Planning

---

## Executive Summary

This document outlines the technical implementation plan for adding a **simplified analysis mode** to the existing comprehensive_analysis tool (Tool 05), inspired by the Microsoft Official Power BI MCP Server's clean and efficient operations structure.

### Key Objectives

1. **Add a new "simple" analysis mode** that provides a fast, lean model overview similar to Microsoft MCP's GetStats operation
2. **Enhance comprehensive_analysis** with this simplified mode while preserving existing functionality
3. **Provide structured counts** for tables, columns, measures, relationships in a single efficient operation
4. **Maintain backward compatibility** with existing comprehensive_analysis usage

---

## 1. Analysis of Microsoft MCP Server Approach

### 1.1 Key Operations Used

The Microsoft MCP server uses a clean, structured approach for model analysis:

```
Connection → GetStats → Detailed Operations (as needed)
```

**GetStats Operation** provides:
- Model metadata (name, database, compatibility level)
- Aggregate counts (tables, measures, columns, partitions, relationships, roles)
- Per-table breakdown (name, column count, measure count, partition count, visibility)

### 1.2 Benefits of This Approach

1. **Single API call** - All basic metadata in one operation
2. **Lightweight** - Only counts and metadata, no DAX expressions or detailed data
3. **Fast execution** - Typically < 100ms even for large models
4. **Structured output** - Easy to parse and present
5. **Progressive disclosure** - Start simple, drill down as needed

### 1.3 Example Response Structure

```json
{
  "success": true,
  "operation": "GETSTATS",
  "modelName": "Model",
  "data": {
    "ModelName": "Model",
    "DatabaseName": "edb241b5-77e6-42a5-8199-67fc2c6224bd",
    "CompatibilityLevel": 1601,
    "TableCount": 109,
    "TotalMeasureCount": 239,
    "TotalColumnCount": 833,
    "TotalPartitionCount": 109,
    "RelationshipCount": 91,
    "RoleCount": 1,
    "Tables": [
      {
        "name": "d_Company",
        "columnCount": 6,
        "measureCount": 0,
        "partitionCount": 1,
        "isHidden": false
      },
      {
        "name": "m_Measures",
        "columnCount": 1,
        "measureCount": 224,
        "partitionCount": 1,
        "isHidden": false
      }
    ]
  }
}
```

---

## 2. Current comprehensive_analysis Implementation

### 2.1 Current Structure

Located in: `/core/orchestration/analysis_orchestrator.py`

**Current analysis types:**
1. **Integrity validation** - Relationships, duplicates, nulls, circular refs
2. **BPA (Best Practice Analyzer)** - 120+ rules for DAX and model quality
3. **M Practices** - Power Query anti-pattern detection
4. **Performance/Cardinality** - Relationship cardinality analysis
5. **Relationship overview** - Full relationship list

**Current parameters:**
```python
def comprehensive_analysis(
    connection_state,
    scope: str = "all",           # "all", "best_practices", "performance", "integrity"
    depth: str = "balanced",       # "fast", "balanced", "deep"
    include_bpa: bool = True,
    include_performance: bool = True,
    include_integrity: bool = True,
    max_seconds: Optional[int] = None
)
```

### 2.2 Performance Characteristics

- **Fast mode**: ~5-10 seconds (BPA skip, quick integrity)
- **Balanced mode**: ~20-30 seconds (BPA with limits, full integrity)
- **Deep mode**: ~60-120 seconds (Full BPA, deep analysis)

### 2.3 Current Gaps

1. **No quick metadata overview** - Even "fast" mode runs multiple analyses
2. **No structured model counts** - Must parse multiple analysis results
3. **No Microsoft-style GetStats equivalent** - Different approach to basic info
4. **Complexity overhead** - User needs to understand scope/depth/includes for simple queries

---

## 3. Proposed Solution: Simple Analysis Mode

### 3.1 New Analysis Mode

Add a new `scope` option: **`"simple"`** or **`"stats"`**

**Purpose**: Provide Microsoft MCP-style model statistics in < 1 second

**When to use**:
- Initial model overview
- Quick model health check
- Inventory/documentation generation
- Pre-flight checks before detailed analysis

### 3.2 New Implementation

#### Option A: Add to comprehensive_analysis (Recommended)

**Advantages**:
- Single tool interface
- Backward compatible
- Consistent with existing design
- Users can combine: `scope="simple"` or `scope="all"` with `include_simple_stats=True`

**Implementation**:

```python
def comprehensive_analysis(
    connection_state,
    scope: str = "all",           # Add: "simple" | "stats"
    depth: str = "balanced",
    include_bpa: bool = True,
    include_performance: bool = True,
    include_integrity: bool = True,
    include_simple_stats: bool = False,  # NEW: Include simple stats in any scope
    max_seconds: Optional[int] = None
)
```

#### Option B: Separate simple_model_analysis function

**Advantages**:
- Clean separation of concerns
- Can be called independently
- Easier to test

**Implementation**:

```python
def simple_model_analysis(self, connection_state) -> Dict[str, Any]:
    """
    Fast model statistics similar to Microsoft MCP GetStats.
    Returns model metadata and structured counts in < 1 second.
    """
    # Implementation details below
```

#### Recommended Approach: Hybrid (A + B)

1. Create `simple_model_analysis()` as a standalone function
2. Add `scope="simple"` to `comprehensive_analysis()` that calls `simple_model_analysis()`
3. Add `include_simple_stats=True` parameter to inject simple stats into any analysis

---

## 4. Detailed Implementation Specification

### 4.1 New Function: simple_model_analysis()

**Location**: `/core/orchestration/analysis_orchestrator.py`

**Function Signature**:

```python
def simple_model_analysis(self, connection_state) -> Dict[str, Any]:
    """
    Fast model statistics overview (< 1 second).

    Similar to Microsoft MCP Server's GetStats operation.
    Provides comprehensive model metadata and counts without heavy analysis.

    Returns:
        {
            'success': True,
            'analysis_type': 'simple_stats',
            'execution_time_seconds': 0.45,
            'model': {
                'name': 'Model',
                'database': 'guid',
                'compatibility_level': 1601,
                'compatibility_version': 'Power BI 2025'
            },
            'counts': {
                'tables': 109,
                'columns': 833,
                'measures': 239,
                'relationships': 91,
                'partitions': 109,
                'roles': 1,
                'calculation_groups': 5,
                'cultures': 1,
                'perspectives': 0
            },
            'tables': [
                {
                    'name': 'd_Company',
                    'type': 'dimension',  # inferred from prefix
                    'column_count': 6,
                    'measure_count': 0,
                    'partition_count': 1,
                    'is_hidden': False,
                    'has_relationships': True
                },
                ...
            ],
            'summary': {
                'total_objects': 1237,
                'measure_tables': ['m_Measures'],
                'largest_tables': [
                    {'name': 'f_FINREP', 'column_count': 30},
                    {'name': 'd_Period', 'column_count': 25}
                ],
                'table_types': {
                    'dimension': 45,
                    'fact': 12,
                    'measure': 1,
                    'support': 15,
                    'calculation_group': 5,
                    'other': 31
                }
            }
        }
    """
```

### 4.2 Implementation Steps

#### Step 1: Data Collection

Use existing DMV queries (already implemented in query_executor):

```python
# 1. Get model metadata
model_info = executor.execute_info_query('MODEL')

# 2. Get tables with counts
tables = executor.execute_info_query('TABLES')

# 3. Get aggregate counts
measures = executor.execute_info_query('MEASURES')
columns = executor.execute_info_query('COLUMNS')
relationships = executor.execute_info_query('RELATIONSHIPS')
partitions = executor.execute_info_query('PARTITIONS')
roles = executor.execute_info_query('ROLES')
calc_groups = executor.execute_info_query('CALCULATION_GROUPS')
```

#### Step 2: Data Aggregation

```python
# Aggregate counts
total_tables = len(tables.get('rows', []))
total_columns = len(columns.get('rows', []))
total_measures = len(measures.get('rows', []))
total_relationships = len(relationships.get('rows', []))
# ... etc
```

#### Step 3: Per-Table Analysis

```python
tables_detailed = []
for table in tables.get('rows', []):
    table_name = table.get('Name', '')

    # Count columns for this table
    table_columns = [c for c in columns.get('rows', [])
                     if c.get('TableName') == table_name]

    # Count measures for this table
    table_measures = [m for m in measures.get('rows', [])
                      if m.get('TableName') == table_name]

    # Check if table has relationships
    has_relationships = any(
        r.get('FromTable') == table_name or r.get('ToTable') == table_name
        for r in relationships.get('rows', [])
    )

    # Infer table type from prefix
    table_type = _infer_table_type(table_name)

    tables_detailed.append({
        'name': table_name,
        'type': table_type,
        'column_count': len(table_columns),
        'measure_count': len(table_measures),
        'partition_count': table.get('PartitionCount', 1),
        'is_hidden': table.get('IsHidden', False),
        'has_relationships': has_relationships
    })
```

#### Step 4: Summary Generation

```python
# Identify measure tables (tables with high measure:column ratio)
measure_tables = [t['name'] for t in tables_detailed
                  if t['measure_count'] > 0 and t['column_count'] < 5]

# Find largest tables
largest_tables = sorted(tables_detailed,
                       key=lambda t: t['column_count'],
                       reverse=True)[:5]

# Count table types
table_types = {}
for t in tables_detailed:
    table_types[t['type']] = table_types.get(t['type'], 0) + 1
```

### 4.3 Helper Function: Table Type Inference

```python
def _infer_table_type(table_name: str) -> str:
    """
    Infer table type from naming convention.

    Common prefixes:
    - d_: dimension
    - f_: fact
    - m_: measure
    - s_: support/slicer
    - c_: calculation group
    - r_: RLS
    - sfp_/dfp_: field parameters
    - dyn_: dynamic
    """
    name_lower = table_name.lower()

    if name_lower.startswith('d_'):
        return 'dimension'
    elif name_lower.startswith('f_'):
        return 'fact'
    elif name_lower.startswith('m_'):
        return 'measure'
    elif name_lower.startswith('s_'):
        return 'support'
    elif name_lower.startswith('c_'):
        return 'calculation_group'
    elif name_lower.startswith('r_'):
        return 'rls'
    elif name_lower.startswith('sfp_') or name_lower.startswith('dfp_'):
        return 'field_parameter'
    elif name_lower.startswith('dyn_'):
        return 'dynamic'
    else:
        return 'other'
```

### 4.4 Integration with comprehensive_analysis

**Modify comprehensive_analysis** to support simple mode:

```python
def comprehensive_analysis(
    self,
    connection_state,
    scope: str = "all",
    depth: str = "balanced",
    include_bpa: bool = True,
    include_performance: bool = True,
    include_integrity: bool = True,
    include_simple_stats: bool = False,  # NEW
    max_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Unified comprehensive model analysis.

    Args:
        scope: "all", "best_practices", "performance", "integrity", "simple"
        include_simple_stats: Add simple stats to any analysis scope
    """
    from core.validation.error_handler import ErrorHandler

    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    scope = (scope or "all").lower()

    # NEW: Handle simple mode
    if scope == "simple" or scope == "stats":
        return self.simple_model_analysis(connection_state)

    # Existing code...
    results: Dict[str, Any] = {
        'success': True,
        'scope': scope,
        'depth': depth,
        'analyses': {},
        'start_time': time.time()
    }

    # NEW: Optionally include simple stats in any analysis
    if include_simple_stats:
        try:
            simple_result = self.simple_model_analysis(connection_state)
            results['analyses']['simple_stats'] = simple_result
        except Exception as e:
            logger.error(f"Simple stats failed: {e}")
            results['analyses']['simple_stats'] = {
                'success': False,
                'error': f'Simple stats failed: {str(e)}'
            }

    # Rest of existing implementation...
```

---

## 5. Tool Schema Updates

### 5.1 Update tool_schemas.py

**Location**: `/server/tool_schemas.py`

**Changes**:

```python
'comprehensive_analysis': {
    "type": "object",
    "properties": {
        "scope": {
            "type": "string",
            "enum": ["all", "best_practices", "performance", "integrity", "simple"],  # ADD "simple"
            "description": (
                "Analysis scope:\n"
                "- 'all': Full analysis (BPA + performance + integrity)\n"
                "- 'best_practices': BPA and M practices only\n"
                "- 'performance': Cardinality analysis only\n"
                "- 'integrity': Model validation only\n"
                "- 'simple': Fast model statistics (< 1s, similar to Microsoft MCP GetStats)"  # NEW
            ),
            "default": "all"
        },
        "depth": {
            "type": "string",
            "enum": ["fast", "balanced", "deep"],
            "description": "Analysis depth (ignored for scope='simple')",
            "default": "balanced"
        },
        "include_simple_stats": {  # NEW
            "type": "boolean",
            "description": "Include simple model statistics in any scope (adds lightweight stats section)",
            "default": False
        },
        # ... existing parameters
    },
    "required": []
}
```

---

## 6. Performance Targets

### 6.1 Execution Time Goals

| Scope | Target Time | Max Acceptable |
|-------|-------------|----------------|
| simple | < 1 second | 2 seconds |
| fast | < 10 seconds | 15 seconds |
| balanced | < 30 seconds | 45 seconds |
| deep | < 120 seconds | 180 seconds |

### 6.2 Optimization Strategies

1. **Parallel DMV queries** - Execute multiple INFO queries concurrently
2. **Cached queries** - Cache table/column/measure lists (already implemented)
3. **Limit table details** - For models with 200+ tables, provide summary only
4. **Lazy loading** - Only fetch detailed data if requested

---

## 7. Testing Strategy

### 7.1 Unit Tests

**Location**: `/tests/test_simple_analysis.py`

```python
def test_simple_model_analysis_basic():
    """Test simple analysis returns required fields."""
    result = orchestrator.simple_model_analysis(connection_state)

    assert result['success'] is True
    assert 'model' in result
    assert 'counts' in result
    assert 'tables' in result
    assert 'summary' in result

def test_simple_model_analysis_performance():
    """Test simple analysis completes in < 2 seconds."""
    start = time.time()
    result = orchestrator.simple_model_analysis(connection_state)
    elapsed = time.time() - start

    assert result['success'] is True
    assert elapsed < 2.0

def test_comprehensive_analysis_simple_scope():
    """Test comprehensive_analysis with scope='simple'."""
    result = orchestrator.comprehensive_analysis(
        connection_state,
        scope="simple"
    )

    assert result['success'] is True
    assert result['analysis_type'] == 'simple_stats'

def test_comprehensive_analysis_with_simple_stats():
    """Test include_simple_stats parameter."""
    result = orchestrator.comprehensive_analysis(
        connection_state,
        scope="integrity",
        include_simple_stats=True
    )

    assert result['success'] is True
    assert 'simple_stats' in result['analyses']
```

### 7.2 Integration Tests

Test against real Power BI models:
- Small model (< 20 tables)
- Medium model (50-100 tables)
- Large model (200+ tables)
- Model with calculation groups
- Model with multiple measure tables

### 7.3 Comparison Tests

Compare output with Microsoft MCP Server GetStats:
- Verify count accuracy
- Verify metadata completeness
- Verify performance similarity

---

## 8. Documentation Updates

### 8.1 README.md

Add to "Unified Analysis Tools" section:

```markdown
### Unified Analysis Tools ⭐ ENHANCED in v5.02

- **Simple Analysis** (05_comprehensive_analysis with scope="simple") -
  Fast model overview (< 1s) with structured counts for tables, columns,
  measures, relationships. Similar to Microsoft MCP GetStats operation.

- **Standard DAX Analysis** (03_standard_dax_analysis) -
  Unified tool combining validation + context analysis + debugging

- **Comprehensive Analysis** (05_comprehensive_analysis) -
  Single tool for BPA + performance + integrity + simple stats with
  configurable scope and depth
```

### 8.2 User Guide

Add section: "Quick Start: Model Overview"

```markdown
## Quick Start: Get Model Overview in 1 Second

To quickly understand a Power BI model, use simple analysis:

**Tool**: `comprehensive_analysis`
**Parameters**:
```json
{
  "scope": "simple"
}
```

**Returns**:
- Model name, database GUID, compatibility level
- Total counts: tables, columns, measures, relationships
- Per-table breakdown with counts and types
- Summary with table categorization

**Use Cases**:
- Initial model exploration
- Documentation generation
- Health checks before deployment
- Quick inventory for reporting
```

### 8.3 Code Comments

Add docstring examples:

```python
def simple_model_analysis(self, connection_state) -> Dict[str, Any]:
    """
    Fast model statistics overview (< 1 second).

    Similar to Microsoft MCP Server's GetStats operation.

    Example usage:
        result = orchestrator.simple_model_analysis(connection_state)

        print(f"Model: {result['model']['name']}")
        print(f"Tables: {result['counts']['tables']}")
        print(f"Measures: {result['counts']['measures']}")

        for table in result['tables']:
            print(f"  {table['name']}: {table['column_count']} columns")

    Example result:
        {
            'success': True,
            'execution_time_seconds': 0.45,
            'model': {'name': 'Model', 'compatibility_level': 1601},
            'counts': {
                'tables': 109,
                'columns': 833,
                'measures': 239,
                'relationships': 91
            },
            'tables': [
                {'name': 'd_Company', 'column_count': 6, 'measure_count': 0},
                {'name': 'm_Measures', 'column_count': 1, 'measure_count': 224}
            ],
            'summary': {
                'total_objects': 1237,
                'measure_tables': ['m_Measures'],
                'table_types': {'dimension': 45, 'fact': 12, ...}
            }
        }

    Returns:
        Dict with model statistics and metadata
    """
```

---

## 9. Migration Path

### 9.1 Backward Compatibility

✅ **No breaking changes** - All existing code continues to work

**Existing calls remain valid**:
```python
# Still works exactly as before
result = orchestrator.comprehensive_analysis(connection_state)
result = orchestrator.comprehensive_analysis(connection_state, scope="all")
result = orchestrator.comprehensive_analysis(connection_state, depth="fast")
```

**New calls are additive**:
```python
# New simple mode
result = orchestrator.comprehensive_analysis(connection_state, scope="simple")

# Add simple stats to any analysis
result = orchestrator.comprehensive_analysis(
    connection_state,
    scope="integrity",
    include_simple_stats=True
)
```

### 9.2 Version Compatibility

- **Minimum compatibility level**: 1200 (SQL Server 2016)
- **Recommended level**: 1500+ (for calculation group support)
- **Tested on**: Power BI Desktop 2024-2025

---

## 10. Implementation Checklist

### Phase 1: Core Implementation (Week 1)

- [ ] Implement `simple_model_analysis()` function in `analysis_orchestrator.py`
- [ ] Implement `_infer_table_type()` helper function
- [ ] Add data collection logic (DMV queries)
- [ ] Add data aggregation logic
- [ ] Add per-table analysis logic
- [ ] Add summary generation logic

### Phase 2: Integration (Week 1)

- [ ] Update `comprehensive_analysis()` to support `scope="simple"`
- [ ] Add `include_simple_stats` parameter
- [ ] Update tool schema in `tool_schemas.py`
- [ ] Add new enum value for scope
- [ ] Test integration with existing scopes

### Phase 3: Testing (Week 2)

- [ ] Write unit tests for `simple_model_analysis()`
- [ ] Write unit tests for `_infer_table_type()`
- [ ] Write integration tests for scope="simple"
- [ ] Write integration tests for include_simple_stats
- [ ] Test with small/medium/large models
- [ ] Performance benchmarking (target < 1s)
- [ ] Comparison testing with Microsoft MCP GetStats

### Phase 4: Documentation (Week 2)

- [ ] Update README.md with new feature
- [ ] Add code documentation and examples
- [ ] Update user guide
- [ ] Create migration guide
- [ ] Add performance benchmarks to docs

### Phase 5: Release (Week 3)

- [ ] Code review
- [ ] Integration testing with Claude Desktop
- [ ] Performance validation
- [ ] Create release notes
- [ ] Tag version 5.02
- [ ] Update changelog

---

## 11. Success Criteria

### 11.1 Functional Requirements

✅ Simple analysis returns all required fields:
- Model metadata (name, database, compatibility)
- Aggregate counts (tables, columns, measures, relationships)
- Per-table breakdown with types and counts
- Summary with categorization

✅ Integration works seamlessly:
- `scope="simple"` returns simple stats
- `include_simple_stats=True` adds stats to any scope
- No breaking changes to existing functionality

### 11.2 Performance Requirements

✅ Execution time < 1 second for typical models
✅ Execution time < 2 seconds for large models (200+ tables)
✅ Memory usage < 50MB

### 11.3 Quality Requirements

✅ Test coverage > 80%
✅ No new linting errors
✅ All existing tests pass
✅ Documentation complete and accurate

---

## 12. Future Enhancements

### 12.1 Short-term (v5.03)

1. **Add column-level statistics** - Include min/max/distinct counts for key columns
2. **Add measure complexity scores** - Simple/Medium/Complex classification
3. **Add relationship type summary** - Count of many-to-one, many-to-many, bidirectional

### 12.2 Medium-term (v5.1)

1. **Add comparison mode** - Compare simple stats between two models
2. **Add change detection** - Track changes to counts over time
3. **Add export formats** - Export simple stats as CSV/JSON/Excel

### 12.3 Long-term (v6.0)

1. **Add visual summary** - HTML/SVG model diagram from simple stats
2. **Add intelligent recommendations** - "Model has 50+ hidden tables - consider cleanup"
3. **Add health score** - Overall model health based on simple metrics

---

## 13. Risk Assessment

### 13.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| DMV queries slow on large models | Medium | Medium | Implement timeout + pagination |
| Table type inference inaccurate | Low | Low | Make type inference optional |
| Memory usage spikes | Low | Medium | Stream results, limit table count |
| Compatibility issues with old PBI | Low | High | Test on PBI 2019-2025 |

### 13.2 Integration Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing comprehensive_analysis | Low | High | Extensive regression testing |
| Schema changes break Claude integration | Low | High | Validate with Claude Desktop |
| Performance regression in other scopes | Low | Medium | Performance benchmarking |

---

## 14. Conclusion

This implementation plan provides a clear path to adding Microsoft MCP-style simple analysis to the comprehensive_analysis tool (Tool 05). The approach is:

✅ **Non-breaking** - Fully backward compatible
✅ **Well-tested** - Comprehensive test coverage
✅ **Performant** - Sub-second execution for typical models
✅ **User-friendly** - Simple parameter: `scope="simple"`
✅ **Flexible** - Can be combined with other analyses

The simple analysis mode will provide users with a fast, efficient way to understand Power BI models, similar to the Microsoft Official MCP Server's GetStats operation, while maintaining the power and flexibility of the existing comprehensive analysis capabilities.

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-19 | System | Initial technical plan |

**Approvals Required**

- [ ] Technical Review
- [ ] Architecture Review
- [ ] Security Review
- [ ] Documentation Review
- [ ] User Acceptance Testing

---

**Next Steps**

1. Review and approve this technical plan
2. Create development branch: `feature/simple-analysis-mode`
3. Begin Phase 1 implementation
4. Schedule code review after Phase 2
5. Release as v5.02 after successful testing
