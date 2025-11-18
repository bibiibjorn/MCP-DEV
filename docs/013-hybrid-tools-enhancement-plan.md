# 013 Hybrid Tools Enhancement Plan

**Date:** 2025-01-18
**Status:** Planning Phase
**Target Tools:** `13_export_hybrid_analysis`, `13_analyze_hybrid_model`
**Estimated Total Effort:** 32-38 hours

---

## Executive Summary

This document outlines three major enhancements to the 013 Hybrid Tools for Power BI model optimization:

1. **VertiPaq Storage Analysis** - Memory footprint optimization
2. **Calculation Groups Analysis** - Measure consolidation and pattern detection
3. **Cardinality Analysis** - High-cardinality column detection and optimization

### Expected Impact

| Enhancement | Memory Savings | Performance Gain | Maintenance Reduction |
|-------------|----------------|------------------|----------------------|
| VertiPaq Storage | 40-60% | 20-30% | - |
| Calculation Groups | - | - | 70% fewer measures |
| Cardinality Optimization | 30-50% | 30-50% | - |
| **Combined** | **60-80%** | **50-70%** | **70%** |

### Industry Context (2025)

These enhancements align with industry-standard tools:
- **VertiPaq Analyzer** (in DAX Studio) - Memory optimization standard
- **Tabular Editor 3 BPA** - Best practice automation
- **SQLBI Best Practices** - Leading Power BI consulting firm standards

---

## Table of Contents

- [1. VertiPaq Storage Analysis](#1-vertipaq-storage-analysis)
- [2. Calculation Groups Analysis](#2-calculation-groups-analysis)
- [3. Cardinality Analysis](#3-cardinality-analysis)
- [4. Implementation Roadmap](#4-implementation-roadmap)
- [5. Technical Architecture](#5-technical-architecture)
- [6. Testing Strategy](#6-testing-strategy)
- [7. Documentation Updates](#7-documentation-updates)

---

## 1. VertiPaq Storage Analysis

### 1.1 Overview

**Purpose:** Analyze memory footprint of Power BI models to identify size optimization opportunities.

**New Operation:** `analyze_vertipaq_storage`

**Use Case:** Identify which columns/tables consume the most memory and receive concrete optimization recommendations.

### 1.2 Key Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| Column Size | Memory consumed per column | `DISCOVER_STORAGE_TABLE_COLUMNS` |
| Compression Ratio | How well data compresses | Calculated from DMVs |
| Dictionary Size | Overhead from unique values | `DISCOVER_STORAGE_TABLE_COLUMNS` |
| Table Size | Total memory per table | `DISCOVER_STORAGE_TABLES` |
| Data Type Impact | String vs Integer comparison | Calculated |
| Segment Count | Column store segments | `DISCOVER_STORAGE_TABLE_COLUMN_SEGMENTS` |

### 1.3 DMV Queries Required

#### Query 1: Table-Level Statistics

```sql
SELECT
    [TABLE_ID],
    [TABLE_NAME],
    [ROWS_COUNT],
    [USED_SIZE],
    [DATA_SIZE],
    [DICTIONARY_SIZE]
FROM $SYSTEM.DISCOVER_STORAGE_TABLES
```

#### Query 2: Column-Level Statistics

```sql
SELECT
    [DIMENSION_NAME] AS TableName,
    [ATTRIBUTE_NAME] AS ColumnName,
    [COLUMN_ID],
    [DICTIONARY_SIZE],
    [DICTIONARY_ENTRIES],
    [DATA_SIZE],
    [COLUMN_ENCODING] AS Encoding,
    [DATATYPE] AS DataType
FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
```

#### Query 3: Segment-Level Statistics

```sql
SELECT
    [DIMENSION_NAME] AS TableName,
    [ATTRIBUTE_NAME] AS ColumnName,
    [SEGMENT_NUMBER],
    [RECORDS_COUNT],
    [USED_SIZE],
    [COLUMN_ENCODING],
    [DICTIONARY_SIZE]
FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMN_SEGMENTS
```

### 1.4 Implementation Details

#### File: `hybrid_analysis_handler.py`

**New Function 1: Main Operation Handler**

```python
def _operation_analyze_vertipaq_storage(
    reader: HybridReader,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Analyze VertiPaq storage statistics for memory optimization

    Args:
        reader: HybridReader instance with access to live model
        detailed: Include segment-level analysis

    Returns:
        {
            "data": {
                "summary": {...},
                "top_20_largest_columns": [...],
                "top_10_largest_tables": [...],
                "recommendations": [...],
                "quick_wins": [...]
            },
            "count": <number of recommendations>
        }
    """

    # Check connection availability
    if not reader.has_live_connection():
        return {
            "data": {
                "error": "VertiPaq storage analysis requires connection to live model",
                "note": "Run export_hybrid_analysis with Power BI Desktop running"
            },
            "count": 0
        }

    # Query DMVs
    storage_stats = _query_vertipaq_storage(reader.query_executor)

    # Analyze and generate recommendations
    analysis = _analyze_storage_stats(storage_stats)

    return {
        "data": analysis,
        "count": len(analysis.get('recommendations', []))
    }
```

**New Function 2: DMV Query Executor**

```python
def _query_vertipaq_storage(query_executor) -> Dict[str, Any]:
    """
    Query VertiPaq storage DMVs

    Returns:
        {
            'tables': [...],
            'columns': [...],
            'segments': [...]  # Optional, for detailed analysis
        }
    """

    # Implementation: Execute the 3 DMV queries above
    # Return structured data
```

**New Function 3: Storage Analysis Logic**

```python
def _analyze_storage_stats(storage_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze storage statistics and generate recommendations

    Algorithm:
    1. Calculate total model size
    2. Sort columns by size (largest first)
    3. Calculate compression ratios
    4. Identify optimization opportunities:
       - High-cardinality strings (>10K unique values)
       - Poor compression (<2.0 ratio)
       - Large dictionary sizes (>50% of column size)
    5. Generate concrete recommendations with code

    Returns:
        {
            "summary": {
                "total_model_size_mb": 245.7,
                "total_tables": 15,
                "largest_column": "Sales[CustomerName]",
                "optimization_opportunities": 8
            },
            "top_20_largest_columns": [...],
            "recommendations": [...]
        }
    """
```

**New Function 4: Recommendation Generator**

```python
def _generate_storage_recommendations(
    columns: List[Dict[str, Any]],
    tables: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate concrete optimization recommendations

    Patterns detected:
    1. High-cardinality string columns
       - Recommendation: Convert to integer surrogate key
       - Expected savings: 60-90% memory, 2-5x faster filtering

    2. Poor compression (<2.0 ratio)
       - Check data quality, consider data type changes
       - Migrate calculated columns to Power Query

    3. Large dictionary overhead (>50%)
       - Reduce cardinality through binning/categorization
       - Remove if unused

    Returns:
        [
            {
                "priority": "high",
                "category": "Data Type Optimization",
                "column": "Sales[CustomerName]",
                "current_size_mb": 45.2,
                "optimized_size_mb": 0.95,
                "potential_savings_mb": 44.25,
                "recommendation": "Convert to Integer surrogate key",
                "implementation": "Step-by-step instructions..."
            }
        ]
    """
```

#### Helper Functions

```python
def _estimate_uncompressed_size(data_type: str, rows: int, cardinality: int) -> int:
    """Estimate uncompressed size based on data type"""

    size_map = {
        'Int64': rows * 8,
        'String': rows * min(50, max(10, cardinality / max(rows, 1) * 20)) * 2,
        'Double': rows * 8,
        'DateTime': rows * 8,
        'Boolean': rows * 1
    }

    return size_map.get(data_type, rows * 8)


def _get_table_rows(tables: List[Dict], table_name: str) -> int:
    """Get row count for a table"""
    for table in tables:
        if table.get('TABLE_NAME') == table_name:
            return table.get('ROWS_COUNT', 0)
    return 0
```

### 1.5 Expected Output Example

```json
{
  "success": true,
  "operation": "analyze_vertipaq_storage",
  "result": {
    "data": {
      "summary": {
        "total_model_size_mb": 245.7,
        "total_tables": 15,
        "total_columns": 187,
        "largest_table": "Sales",
        "largest_column": "Sales[CustomerName]",
        "optimization_opportunities": 8
      },
      "top_20_largest_columns": [
        {
          "table": "Sales",
          "column": "CustomerName",
          "size_mb": 45.2,
          "data_size_mb": 38.5,
          "dictionary_size_mb": 6.7,
          "cardinality": 125000,
          "data_type": "String",
          "encoding": "Hash",
          "compression_ratio": 2.3,
          "percentage_of_model": 18.4
        }
      ],
      "recommendations": [
        {
          "priority": "high",
          "category": "Data Type Optimization",
          "column": "Sales[CustomerName]",
          "issue": "High-cardinality string column (125,000 unique values)",
          "current_size_mb": 45.2,
          "optimized_size_mb": 0.95,
          "potential_savings_mb": 44.25,
          "recommendation": "Convert to Integer surrogate key",
          "implementation": "1. In source database:\n   - Create integer surrogate key\n   - Create lookup table\n\n2. In Power BI:\n   - Replace with integer key\n   - Use for relationships\n\nExpected savings: 44.3 MB (98% reduction)"
        }
      ],
      "quick_wins": [...]
    }
  }
}
```

### 1.6 Estimated Effort

- **DMV Query Implementation:** 3 hours
- **Analysis Logic:** 4 hours
- **Recommendation Engine:** 4 hours
- **Testing & Debugging:** 2 hours
- **Documentation:** 1 hour
- **Total:** 14 hours

---

## 2. Calculation Groups Analysis

### 2.1 Overview

**Purpose:** Automatically detect patterns in measures that can be consolidated into calculation groups.

**New Operation:** `identify_calc_groups`

**Use Case:** Reduce measure proliferation by identifying time intelligence, formatting, and structural patterns.

### 2.2 Pattern Detection

#### Pattern 1: Time Intelligence

**Detection Logic:**
- Measures with common base names + suffixes (YTD, MTD, PY, YoY, MoM)
- DAX expressions containing time intelligence functions

**Example:**
```dax
Sales = SUM(Sales[Amount])
Sales YTD = TOTALYTD([Sales], Date[Date])
Sales PY = CALCULATE([Sales], SAMEPERIODLASTYEAR(Date[Date]))
Sales YoY% = DIVIDE([Sales] - [Sales PY], [Sales PY])
```

**Consolidation:**
→ 1 calculation group with 4 items + 1 base measure

#### Pattern 2: Formatting Variations

**Detection Logic:**
- Multiple measures with identical DAX expressions
- Different format strings

**Example:**
```dax
Sales = SUM(Sales[Amount])
Sales ($) = SUM(Sales[Amount])  // FormatString: "$#,0"
Sales (K) = SUM(Sales[Amount]) / 1000  // FormatString: "#,0,K"
Sales (M) = SUM(Sales[Amount]) / 1000000  // FormatString: "#,0.0,,M"
```

**Consolidation:**
→ 1 calculation group with 4 items + 1 base measure

#### Pattern 3: Similar Structure

**Detection Logic:**
- Measures with similar DAX patterns across different base measures
- Same transformation applied to multiple measures

**Example:**
```dax
Profit Margin = DIVIDE([Profit], [Sales])
Profit Margin PY = CALCULATE([Profit Margin], SAMEPERIODLASTYEAR(Date[Date]))
Cost Ratio = DIVIDE([Cost], [Sales])
Cost Ratio PY = CALCULATE([Cost Ratio], SAMEPERIODLASTYEAR(Date[Date]))
```

**Consolidation:**
→ 1 calculation group with 2 items (Current, PY) + 2 base measures

### 2.3 Implementation Details

#### File: `hybrid_analysis_handler.py`

**New Function 1: Main Operation**

```python
def _operation_identify_calc_groups(
    reader: HybridReader,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Identify calculation group opportunities through pattern detection

    Returns:
        {
            "data": {
                "summary": {
                    "total_measures_current": 87,
                    "total_measures_optimized": 28,
                    "reduction_percentage": 68,
                    "patterns_found": 2
                },
                "recommendations": [
                    {
                        "pattern": "Time Intelligence",
                        "opportunity": "45 measures → 9 base + 1 calc group",
                        "affected_measures": [...],
                        "tmdl_code": "...",
                        "implementation_steps": [...]
                    }
                ]
            }
        }
    """

    # Get all measures from TMDL
    all_measures = _get_all_measures(reader)

    # Detect patterns
    patterns = _detect_calculation_group_patterns(all_measures)

    # Generate recommendations
    recommendations = _build_calc_group_recommendations(patterns, all_measures)

    return {
        "data": {
            "summary": _build_summary(all_measures, recommendations),
            "recommendations": recommendations
        },
        "count": len(recommendations)
    }
```

**New Function 2: Pattern Detection Engine**

```python
def _detect_calculation_group_patterns(all_measures: List[Dict]) -> Dict[str, Any]:
    """
    Analyze measures for calculation group patterns

    Algorithm:

    1. Time Intelligence Pattern:
       - Find measures ending with: YTD, MTD, QTD, PY, YoY, MoM, QoQ
       - Check for functions: TOTALYTD, SAMEPERIODLASTYEAR, DATEADD, PARALLELPERIOD
       - Group by base measure name
       - Require 3+ variations to recommend

    2. Formatting Pattern:
       - Normalize expressions (remove whitespace, uppercase)
       - Group measures with identical normalized expressions
       - Check if format strings differ
       - Require 2+ variations

    3. Similar Structure Pattern:
       - Extract expression templates (replace specific values with placeholders)
       - Group measures with similar templates
       - Require 3+ measures with same structure

    Returns:
        {
            'time_intelligence': [
                {
                    'measure': 'Sales YTD',
                    'base_name': 'Sales',
                    'pattern': 'time_intelligence',
                    'function': 'TOTALYTD'
                }
            ],
            'formatting': [
                {
                    'measures': ['Sales', 'Sales ($)', 'Sales (K)'],
                    'count': 3
                }
            ],
            'similar_structure': [...]
        }
    """

    patterns = {
        'time_intelligence': [],
        'formatting': [],
        'similar_structure': []
    }

    # Pattern 1: Time Intelligence
    time_suffixes = ['YTD', 'MTD', 'QTD', 'PY', 'YoY', 'MoM', 'QoQ']
    time_functions = ['TOTALYTD', 'TOTALMTD', 'TOTALQTD', 'SAMEPERIODLASTYEAR',
                      'DATEADD', 'PARALLELPERIOD']

    for measure in all_measures:
        expr = measure.get('expression', '')
        name = measure.get('name', '')

        # Check for time intelligence functions
        for func in time_functions:
            if func in expr.upper():
                # Extract base name
                base_name = name
                for suffix in time_suffixes:
                    if name.endswith(f' {suffix}') or name.endswith(f'_{suffix}'):
                        base_name = name.replace(f' {suffix}', '').replace(f'_{suffix}', '')
                        break

                patterns['time_intelligence'].append({
                    'measure': name,
                    'base_name': base_name,
                    'pattern': 'time_intelligence',
                    'function': func,
                    'expression': expr
                })
                break

    # Pattern 2: Formatting
    expr_groups = {}
    for measure in all_measures:
        # Normalize expression
        normalized = re.sub(r'\s+', '', measure.get('expression', '')).upper()

        if normalized not in expr_groups:
            expr_groups[normalized] = []
        expr_groups[normalized].append(measure)

    # Find groups with multiple measures and different formats
    for expr, measures in expr_groups.items():
        if len(measures) > 1:
            formats = [m.get('formatString', '') for m in measures]
            if len(set(formats)) > 1:
                patterns['formatting'].append({
                    'measures': [m['name'] for m in measures],
                    'count': len(measures),
                    'pattern': 'formatting',
                    'base_expression': measures[0].get('expression')
                })

    # Pattern 3: Similar Structure (simplified - full implementation would be more complex)
    # Group by similar DAX patterns using regex templates

    return patterns
```

**New Function 3: TMDL Code Generator**

```python
def _generate_calculation_group_tmdl(pattern_type: str, measures: List[str]) -> str:
    """
    Generate actual TMDL code for calculation group

    Templates for each pattern type
    """

    templates = {
        'time_intelligence': '''
table 'Time Intelligence'
	lineageTag: <GUID>
	calculationGroup

	column 'Time Calculation'
		dataType: string
		lineageTag: <GUID>
		summarizeBy: none
		isDataTypeInferred: false
		sourceColumn: [Time Calculation]
		sortByColumn: Ordinal

	column Ordinal
		dataType: int64
		isHidden: true
		lineageTag: <GUID>
		summarizeBy: none
		isDataTypeInferred: false
		sourceColumn: [Ordinal]

	calculationItem Current =
		SELECTEDMEASURE()
		ordinal: 0

	calculationItem YTD =
		CALCULATE(
			SELECTEDMEASURE(),
			DATESYTD('Date'[Date])
		)
		ordinal: 1

	calculationItem MTD =
		CALCULATE(
			SELECTEDMEASURE(),
			DATESMTD('Date'[Date])
		)
		ordinal: 2

	calculationItem PY =
		CALCULATE(
			SELECTEDMEASURE(),
			SAMEPERIODLASTYEAR('Date'[Date])
		)
		ordinal: 3

	calculationItem 'YoY %' =
		VAR CurrentValue = SELECTEDMEASURE()
		VAR PriorValue = CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Date'[Date]))
		RETURN
			DIVIDE(CurrentValue - PriorValue, PriorValue)
		ordinal: 4
		formatString: 0.0%;-0.0%;0.0%
''',

        'formatting': '''
table 'Format Scaling'
	lineageTag: <GUID>
	calculationGroup

	column 'Format Type'
		dataType: string
		lineageTag: <GUID>
		summarizeBy: none
		isDataTypeInferred: false
		sourceColumn: [Format Type]
		sortByColumn: Ordinal

	column Ordinal
		dataType: int64
		isHidden: true
		lineageTag: <GUID>
		summarizeBy: none
		isDataTypeInferred: false
		sourceColumn: [Ordinal]

	calculationItem 'No formatting' =
		SELECTEDMEASURE()
		ordinal: 0

	calculationItem '$' =
		SELECTEDMEASURE()
		ordinal: 1
		formatString: "$"#,0;-"$"#,0;"$"#,0

	calculationItem '(K)' =
		DIVIDE(SELECTEDMEASURE(), 1000)
		ordinal: 2
		formatString: #,0,"K"

	calculationItem '(M)' =
		DIVIDE(SELECTEDMEASURE(), 1000000)
		ordinal: 3
		formatString: #,0.0,,"M"
'''
    }

    return templates.get(pattern_type, '# Template not available')
```

**New Function 4: Recommendation Builder**

```python
def _build_calc_group_recommendations(
    patterns: Dict[str, Any],
    all_measures: List[Dict]
) -> List[Dict[str, Any]]:
    """
    Build recommendations from detected patterns

    For each pattern:
    1. Calculate before/after measure counts
    2. Generate TMDL code
    3. Provide implementation steps
    4. Estimate maintenance reduction
    """

    recommendations = []

    # Time Intelligence Pattern
    if patterns['time_intelligence']:
        # Group by base measure
        base_groups = {}
        for item in patterns['time_intelligence']:
            base = item['base_name']
            if base not in base_groups:
                base_groups[base] = []
            base_groups[base].append(item)

        # Only recommend if 3+ variations per base
        significant_groups = {k: v for k, v in base_groups.items() if len(v) >= 3}

        if significant_groups:
            affected_count = sum(len(v) for v in significant_groups.values())
            base_count = len(significant_groups)
            reduction_pct = int((1 - base_count/affected_count) * 100)

            recommendations.append({
                'pattern': 'Time Intelligence',
                'opportunity': f'{affected_count} measures → {base_count} base measures + 1 calc group',
                'affected_measures': [
                    {
                        'base': base,
                        'variations': [m['measure'] for m in measures]
                    }
                    for base, measures in significant_groups.items()
                ],
                'reduction': f'{affected_count} → {base_count} measures ({reduction_pct}% reduction)',
                'tmdl_code': _generate_calculation_group_tmdl('time_intelligence', []),
                'implementation_steps': [
                    '1. Create calculation group using Tabular Editor with TMDL above',
                    '2. Keep only base measures (delete YTD, PY, YoY variants)',
                    '3. Test calculations in reports',
                    '4. Update report visuals to use calc group slicer'
                ],
                'estimated_time': '2-4 hours'
            })

    # Formatting Pattern
    for fmt_pattern in patterns.get('formatting', []):
        if fmt_pattern['count'] >= 2:
            reduction_pct = int((1 - 1/fmt_pattern['count']) * 100)

            recommendations.append({
                'pattern': 'Format Scaling',
                'opportunity': f"{fmt_pattern['count']} measures → 1 measure + 1 calc group",
                'affected_measures': fmt_pattern['measures'],
                'reduction': f"{fmt_pattern['count']} → 1 measure ({reduction_pct}% reduction)",
                'tmdl_code': _generate_calculation_group_tmdl('formatting', []),
                'implementation_steps': [
                    '1. Create Format Scaling calculation group',
                    '2. Keep only one base measure',
                    '3. Delete duplicate formatted measures',
                    '4. Use calc group slicer for format selection'
                ],
                'estimated_time': '1-2 hours'
            })

    return recommendations
```

### 2.4 Expected Output Example

```json
{
  "success": true,
  "operation": "identify_calc_groups",
  "result": {
    "data": {
      "summary": {
        "total_measures_current": 87,
        "total_measures_optimized": 28,
        "reduction_count": 59,
        "reduction_percentage": 68,
        "patterns_found": 2,
        "estimated_maintenance_reduction": "68% fewer measures to maintain"
      },
      "recommendations": [
        {
          "pattern": "Time Intelligence",
          "opportunity": "45 measures → 9 base measures + 1 calc group",
          "affected_measures": [
            {
              "base": "Sales",
              "variations": ["Sales", "Sales YTD", "Sales PY", "Sales YoY %"]
            },
            {
              "base": "Profit",
              "variations": ["Profit", "Profit YTD", "Profit PY"]
            }
          ],
          "reduction": "45 → 9 measures (80% reduction)",
          "tmdl_code": "...",
          "implementation_steps": [...],
          "estimated_time": "2-4 hours"
        }
      ],
      "benefits": [
        "Reduced measure count → Easier navigation",
        "Centralized logic → Single source of truth",
        "Better report UX → Users select via slicer"
      ]
    }
  }
}
```

### 2.5 Estimated Effort

- **Pattern Detection Logic:** 4 hours
- **TMDL Code Generation:** 2 hours
- **Recommendation Engine:** 3 hours
- **Testing:** 2 hours
- **Documentation:** 1 hour
- **Total:** 12 hours

---

## 3. Cardinality Analysis

### 3.1 Overview

**Purpose:** Identify high-cardinality columns that cause performance issues and memory bloat.

**New Operation:** `analyze_cardinality`

**Use Case:** Detect columns with excessive unique values and receive optimization recommendations.

### 3.2 Key Metrics

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Column Cardinality | Number of unique values | >10,000 = high |
| Cardinality Ratio | Unique/Total rows | >0.95 = near-unique |
| Relationship Ratio | From/To cardinality | >100:1 or <0.01:1 = extreme |
| RI Violations | Blank members in relationships | >0 = issue |

### 3.3 Data Collection

#### Connected Mode (Preferred)

**For each column:**
```dax
EVALUATE
{
    DISTINCTCOUNT('Table'[Column]),
    COUNTROWS('Table')
}
```

**Batch optimization:**
- Process all columns sequentially
- Log progress every 50 columns
- Cache results per table

#### Offline Mode (Fallback)

**Estimate from sample data:**
- Read parquet files
- Calculate unique values in sample
- Extrapolate to full dataset (with warning)

### 3.4 Implementation Details

#### File: `hybrid_analysis_handler.py`

**New Function 1: Main Operation**

```python
def _operation_analyze_cardinality(
    reader: HybridReader,
    threshold: int = 10000
) -> Dict[str, Any]:
    """
    Analyze cardinality across model

    Args:
        threshold: Cardinality threshold for "high cardinality" (default 10,000)

    Returns:
        {
            "data": {
                "summary": {...},
                "high_cardinality_columns": [...],
                "near_unique_columns": [...],
                "relationship_cardinality": [...],
                "recommendations": [...]
            }
        }
    """

    # Check connection
    if not reader.has_live_connection():
        # Fallback: Estimate from sample data
        return _analyze_cardinality_from_sample_data(reader, threshold)

    # Query cardinality from live model
    cardinality_stats = _query_cardinality_stats(reader.query_executor)

    # Get relationships
    relationships = reader.get_relationships_from_tmdl()

    # Analyze
    analysis = _analyze_cardinality_stats(cardinality_stats, relationships, threshold)

    return {
        "data": analysis,
        "count": len(analysis.get('high_cardinality_columns', []))
    }
```

**New Function 2: Cardinality Query Engine**

```python
def _query_cardinality_stats(query_executor) -> Dict[str, Any]:
    """
    Query cardinality for all columns

    Process:
    1. Get all columns using INFO.COLUMNS()
    2. For each column, execute: DISTINCTCOUNT + COUNTROWS
    3. Calculate cardinality ratio
    4. Return structured data

    Performance:
    - ~0.5-2 seconds per column (depends on size)
    - For 200 columns: ~3-7 minutes total
    - Log progress every 50 columns
    """

    # Step 1: Get column list
    columns_query = """
    EVALUATE
    SELECTCOLUMNS(
        INFO.COLUMNS(),
        "TableName", [TableName],
        "ColumnName", [Name],
        "DataType", [DataType],
        "IsHidden", [IsHidden]
    )
    """

    columns_result = query_executor.validate_and_execute_dax(columns_query, top_n=0)
    columns_list = columns_result.get('rows', [])

    # Step 2: Get cardinality for each column
    cardinality_data = []

    for idx, col in enumerate(columns_list):
        table_name = col.get('[TableName]') or col.get('TableName')
        column_name = col.get('[ColumnName]') or col.get('ColumnName')

        try:
            # Escape quotes
            escaped_table = table_name.replace("'", "''")
            escaped_column = column_name.replace("'", "''")

            # Query: DISTINCTCOUNT and COUNTROWS
            query = f"""
            EVALUATE
            {{
                DISTINCTCOUNT('{escaped_table}'[{escaped_column}]),
                COUNTROWS('{escaped_table}')
            }}
            """

            result = query_executor.validate_and_execute_dax(query, top_n=0, bypass_cache=True)

            if result.get('success') and result.get('rows'):
                values = list(result['rows'][0].values())
                cardinality = int(values[0])
                row_count = int(values[1])

                cardinality_data.append({
                    'table': table_name,
                    'column': column_name,
                    'data_type': col.get('[DataType]') or col.get('DataType'),
                    'is_hidden': col.get('[IsHidden]') or col.get('IsHidden'),
                    'cardinality': cardinality,
                    'row_count': row_count,
                    'cardinality_ratio': round(cardinality / row_count, 4) if row_count > 0 else 0
                })

        except Exception as e:
            logger.debug(f"Error getting cardinality for {table_name}[{column_name}]: {e}")
            continue

        # Progress logging
        if (idx + 1) % 50 == 0:
            logger.info(f"  Progress: {idx + 1}/{len(columns_list)} columns")

    return {'columns': cardinality_data}
```

**New Function 3: Analysis Logic**

```python
def _analyze_cardinality_stats(
    cardinality_stats: Dict[str, Any],
    relationships: List[Dict[str, Any]],
    threshold: int
) -> Dict[str, Any]:
    """
    Analyze cardinality statistics

    Identifies:
    1. High-cardinality columns (>threshold)
    2. Near-unique columns (ratio >0.95)
    3. Relationship cardinality issues
    4. Generates recommendations
    """

    columns = cardinality_stats.get('columns', [])

    # Filter high-cardinality
    high_cardinality = [
        col for col in columns
        if col['cardinality'] > threshold
    ]
    high_cardinality_sorted = sorted(high_cardinality, key=lambda c: c['cardinality'], reverse=True)

    # Filter near-unique
    near_unique = [
        col for col in columns
        if col['cardinality_ratio'] > 0.95 and col['cardinality'] > 1000
    ]

    # Analyze relationships
    relationship_analysis = []
    for rel in relationships:
        from_table = rel.get('fromTable', '')
        from_column = rel.get('fromColumn', '')
        to_table = rel.get('toTable', '')
        to_column = rel.get('toColumn', '')

        # Find cardinalities
        from_card = next((c['cardinality'] for c in columns
                         if c['table'] == from_table and c['column'] == from_column), None)
        to_card = next((c['cardinality'] for c in columns
                       if c['table'] == to_table and c['column'] == to_column), None)

        if from_card and to_card:
            ratio = from_card / to_card if to_card > 0 else 0

            # Detect issues
            issues = []
            if from_card > 100000 or to_card > 100000:
                issues.append("High cardinality in relationship")
            if ratio < 0.01 or ratio > 100:
                issues.append("Extreme cardinality ratio")

            relationship_analysis.append({
                'from': f"{from_table}[{from_column}]",
                'to': f"{to_table}[{to_column}]",
                'from_cardinality': from_card,
                'to_cardinality': to_card,
                'cardinality_ratio': round(ratio, 2),
                'is_active': rel.get('isActive', True),
                'cross_filter': rel.get('crossFilteringBehavior', 'OneDirection'),
                'issues': issues,
                'status': '⚠️ Warning' if issues else '✓ Healthy'
            })

    # Generate recommendations
    recommendations = _generate_cardinality_recommendations(
        high_cardinality_sorted,
        near_unique,
        relationship_analysis
    )

    return {
        'summary': {
            'total_columns_analyzed': len(columns),
            'high_cardinality_columns': len(high_cardinality),
            'near_unique_columns': len(near_unique),
            'relationships_analyzed': len(relationship_analysis),
            'relationships_with_issues': len([r for r in relationship_analysis if r['issues']]),
            'threshold_used': threshold
        },
        'high_cardinality_columns': high_cardinality_sorted[:20],
        'near_unique_columns': near_unique,
        'relationship_cardinality': relationship_analysis,
        'recommendations': recommendations,
        'quick_wins': [r for r in recommendations if r['priority'] == 'high'][:5]
    }
```

**New Function 4: Recommendation Generator**

```python
def _generate_cardinality_recommendations(
    high_cardinality: List[Dict[str, Any]],
    near_unique: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate optimization recommendations

    Patterns:
    1. High-cardinality strings → Convert to integer keys
    2. Near-unique columns → Verify necessity, consider removing
    3. Relationship issues → Optimize key columns
    """

    recommendations = []

    # High-cardinality strings
    for col in high_cardinality:
        if col['data_type'] in ['String', 'WString']:
            recommendations.append({
                'priority': 'high',
                'category': 'High Cardinality',
                'column': f"{col['table']}[{col['column']}]",
                'cardinality': col['cardinality'],
                'issue': f"High-cardinality string ({col['cardinality']:,} unique values)",
                'recommendation': 'Convert to Integer surrogate key',
                'expected_benefit': '60-90% memory, 2-5x faster filtering',
                'implementation': f"""
1. In source system:
   - Create integer ID column
   - Create lookup table: {col['column']}ID → {col['column']}

2. In Power BI:
   - Replace column with integer key
   - Use integer for relationships
   - Keep lookup for display

Expected: {col['cardinality'] * 50 / (1024*1024):.1f} MB → {col['cardinality'] * 8 / (1024*1024):.1f} MB
"""
            })

    # Near-unique columns
    for col in near_unique:
        recommendations.append({
            'priority': 'medium',
            'category': 'Near-Unique Column',
            'column': f"{col['table']}[{col['column']}]",
            'cardinality': col['cardinality'],
            'cardinality_ratio': col['cardinality_ratio'],
            'issue': f"{col['cardinality_ratio']*100:.1f}% unique values",
            'recommendation': 'Verify necessity or remove',
            'implementation': """
Near-unique columns are often:
- Primary keys (may not be needed)
- Transaction IDs (remove if unused)
- Timestamps (round to hour/day)

Action:
1. Check usage with analyze_dependencies
2. If unused: Remove column
3. If key-only: Remove from model
"""
        })

    # Relationship issues
    for rel in relationships:
        if rel['issues']:
            recommendations.append({
                'priority': 'high' if 'High cardinality' in str(rel['issues']) else 'medium',
                'category': 'Relationship Cardinality',
                'relationship': f"{rel['from']} → {rel['to']}",
                'issues': rel['issues'],
                'recommendation': 'Optimize relationship keys',
                'implementation': """
Actions:
1. Convert to integer keys
2. Ensure referential integrity
3. Check for data quality issues
4. Consider aggregation at source
"""
            })

    return sorted(recommendations, key=lambda r: {'high': 0, 'medium': 1}[r['priority']])
```

**New Function 5: Sample Data Fallback**

```python
def _analyze_cardinality_from_sample_data(
    reader: HybridReader,
    threshold: int
) -> Dict[str, Any]:
    """
    Fallback: Estimate cardinality from sample data parquet files
    (When no live connection)

    Warning: Estimates only, not accurate for full dataset
    """

    sample_tables = reader.list_sample_data_tables()

    if not sample_tables:
        return {
            "data": {
                "error": "Cardinality analysis requires connection or sample data",
                "note": "Re-export with include_sample_data=true"
            },
            "count": 0
        }

    estimated_cardinality = []

    for table_name in sample_tables:
        sample_data = reader.read_sample_data(table_name)

        if sample_data and sample_data.get('data'):
            rows = sample_data['data']

            for col_name in rows[0].keys():
                unique_values = len(set(row.get(col_name) for row in rows))

                estimated_cardinality.append({
                    'table': table_name,
                    'column': col_name,
                    'unique_in_sample': unique_values,
                    'sample_size': len(rows),
                    'uniqueness_ratio': round(unique_values / len(rows), 4),
                    'note': '⚠️ Estimated from sample only'
                })

    return {
        "data": {
            "summary": {
                "mode": "sample_data_estimation",
                "note": "Connect to live model for accurate analysis"
            },
            "estimated_high_cardinality": estimated_cardinality
        },
        "count": len(estimated_cardinality)
    }
```

### 3.5 Expected Output Example

```json
{
  "success": true,
  "operation": "analyze_cardinality",
  "result": {
    "data": {
      "summary": {
        "total_columns_analyzed": 187,
        "high_cardinality_columns": 12,
        "near_unique_columns": 5,
        "relationships_analyzed": 18,
        "relationships_with_issues": 3,
        "threshold_used": 10000
      },
      "high_cardinality_columns": [
        {
          "table": "Sales",
          "column": "CustomerName",
          "data_type": "String",
          "cardinality": 125000,
          "row_count": 2500000,
          "cardinality_ratio": 0.05
        }
      ],
      "near_unique_columns": [
        {
          "table": "Sales",
          "column": "OrderID",
          "cardinality": 2499850,
          "cardinality_ratio": 0.9999
        }
      ],
      "relationship_cardinality": [
        {
          "from": "Sales[CustomerKey]",
          "to": "Customer[CustomerKey]",
          "from_cardinality": 125000,
          "to_cardinality": 125000,
          "cardinality_ratio": 1.0,
          "status": "✓ Healthy"
        }
      ],
      "recommendations": [...]
    }
  }
}
```

### 3.6 Estimated Effort

- **DAX Query Engine:** 3 hours
- **Analysis Logic:** 3 hours
- **Relationship Analysis:** 2 hours
- **Sample Data Fallback:** 2 hours
- **Testing:** 2 hours
- **Documentation:** 1 hour
- **Total:** 13 hours

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Goals:**
- Set up DMV query infrastructure
- Implement core data structures
- Create helper functions

**Tasks:**
1. Add `has_live_connection()` method to HybridReader
2. Create DMV query executor utility
3. Add error handling for connection issues
4. Set up logging for long-running operations

**Effort:** 4 hours

---

### Phase 2: VertiPaq Storage (Week 2)

**Goals:**
- Implement VertiPaq storage analysis
- Generate size optimization recommendations

**Tasks:**
1. Implement `_query_vertipaq_storage()` - 3 hrs
2. Implement `_analyze_storage_stats()` - 4 hrs
3. Implement `_generate_storage_recommendations()` - 4 hrs
4. Add operation handler - 1 hr
5. Testing - 2 hrs

**Effort:** 14 hours

---

### Phase 3: Calculation Groups (Week 3)

**Goals:**
- Implement pattern detection
- Generate TMDL code for calc groups

**Tasks:**
1. Implement `_detect_calculation_group_patterns()` - 4 hrs
2. Implement `_generate_calculation_group_tmdl()` - 2 hrs
3. Implement `_build_calc_group_recommendations()` - 3 hrs
4. Add operation handler - 1 hr
5. Testing - 2 hrs

**Effort:** 12 hours

---

### Phase 4: Cardinality Analysis (Week 4)

**Goals:**
- Implement cardinality analysis
- Support both connected and offline modes

**Tasks:**
1. Implement `_query_cardinality_stats()` - 3 hrs
2. Implement `_analyze_cardinality_stats()` - 3 hrs
3. Implement `_generate_cardinality_recommendations()` - 2 hrs
4. Implement `_analyze_cardinality_from_sample_data()` - 2 hrs
5. Add operation handler - 1 hr
6. Testing - 2 hrs

**Effort:** 13 hours

---

### Phase 5: Integration & Polish (Week 5)

**Goals:**
- Update tool schemas
- Integration testing
- Documentation

**Tasks:**
1. Update `tool_schemas.py` with new operations - 1 hr
2. Integration testing across all 3 features - 4 hrs
3. Performance optimization - 2 hrs
4. User documentation - 2 hrs
5. Code review and cleanup - 2 hrs

**Effort:** 11 hours

---

### Total Timeline

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1: Foundation | 2 days | 4 hrs |
| Phase 2: VertiPaq | 1 week | 14 hrs |
| Phase 3: Calc Groups | 1 week | 12 hrs |
| Phase 4: Cardinality | 1 week | 13 hrs |
| Phase 5: Integration | 1 week | 11 hrs |
| **Total** | **5 weeks** | **54 hrs** |

*Note: Effort assumes focused development time, not calendar time*

---

## 5. Technical Architecture

### 5.1 File Structure

```
/home/user/MCP-DEV/
├── server/
│   ├── handlers/
│   │   └── hybrid_analysis_handler.py    # PRIMARY FILE - Add all 3 operations
│   └── tool_schemas.py                   # Update operation enums
├── core/
│   ├── model/
│   │   ├── hybrid_reader.py              # Add has_live_connection() method
│   │   └── hybrid_analyzer.py            # No changes needed
│   └── utilities/
│       └── dmv_query_executor.py         # NEW - DMV query utilities
└── docs/
    └── 013-hybrid-tools-enhancement-plan.md  # THIS FILE
```

### 5.2 Dependencies

**Python Libraries:**
- No new dependencies required
- Uses existing: `logging`, `re`, `json`, `typing`

**Power BI Requirements:**
- Connection to live Power BI Desktop instance
- ADOMD.NET (already used by existing tools)
- Tabular Editor (for calc group implementation - user-side)

### 5.3 Data Flow

```
User Request
    ↓
handle_analyze_hybrid_model()
    ↓
Operation Router
    ↓
┌─────────────────┬──────────────────┬────────────────────┐
↓                 ↓                  ↓                    ↓
analyze_          identify_          analyze_
vertipaq_         calc_groups        cardinality
storage
    ↓                 ↓                  ↓
Query DMVs        Parse TMDL         Query DAX
(connected)       (offline OK)       (connected preferred)
    ↓                 ↓                  ↓
Analyze           Detect Patterns    Analyze Stats
    ↓                 ↓                  ↓
Generate          Generate           Generate
Recommendations   TMDL Code          Recommendations
    ↓                 ↓                  ↓
Return JSON       Return JSON        Return JSON
```

### 5.4 Error Handling

**Connection Issues:**
```python
if not reader.has_live_connection():
    return {
        "data": {
            "error": "Operation requires live connection",
            "note": "Run export_hybrid_analysis with Power BI Desktop open",
            "fallback": "Sample data estimation available for cardinality"
        },
        "count": 0
    }
```

**DMV Query Failures:**
```python
try:
    result = query_executor.execute_dmv_query(query)
except Exception as e:
    logger.error(f"DMV query failed: {e}")
    return {
        "data": {"error": f"Query failed: {str(e)}"},
        "count": 0
    }
```

**Performance Considerations:**
- Cardinality analysis can take 3-7 minutes for large models (200+ columns)
- Log progress every 50 items
- Provide time estimates to user
- Allow interruption for long-running operations

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Test File:** `tests/test_hybrid_analysis_enhancements.py`

```python
def test_vertipaq_storage_analysis():
    """Test VertiPaq storage analysis"""
    # Mock DMV data
    # Verify size calculations
    # Verify recommendations generated

def test_calc_group_pattern_detection():
    """Test calculation group pattern detection"""
    # Mock measures with time intelligence
    # Verify patterns detected
    # Verify TMDL code generated

def test_cardinality_analysis():
    """Test cardinality analysis"""
    # Mock cardinality data
    # Verify high-cardinality detection
    # Verify relationship analysis

def test_sample_data_fallback():
    """Test cardinality estimation from sample data"""
    # Mock sample data
    # Verify estimates calculated
```

### 6.2 Integration Tests

**Test Models:**
1. **Small Model** (< 50 MB, 10 tables)
   - Verify all operations complete quickly
   - Verify recommendations accurate

2. **Medium Model** (100-300 MB, 30 tables)
   - Verify performance acceptable
   - Verify memory optimization recommendations

3. **Large Model** (500+ MB, 100+ tables)
   - Verify timeout handling
   - Verify progress logging
   - Verify top-N limiting (not all columns analyzed)

### 6.3 Performance Benchmarks

| Operation | Small Model | Medium Model | Large Model |
|-----------|-------------|--------------|-------------|
| VertiPaq Storage | < 5 sec | 10-20 sec | 30-60 sec |
| Calc Groups | < 2 sec | 5-10 sec | 15-30 sec |
| Cardinality | 1-2 min | 3-5 min | 7-15 min |

**Optimization Targets:**
- No operation should block UI > 30 seconds
- Provide progress updates for long operations
- Cache results when possible

### 6.4 Validation Criteria

**VertiPaq Storage:**
- ✅ Correctly identifies top 20 largest columns
- ✅ Compression ratios within ±10% of DAX Studio VertiPaq Analyzer
- ✅ Recommendations include savings estimates

**Calculation Groups:**
- ✅ Detects 90%+ of time intelligence patterns
- ✅ Generated TMDL code is valid
- ✅ Measure reduction calculations accurate

**Cardinality:**
- ✅ Cardinality values match DISTINCTCOUNT queries
- ✅ Relationship analysis identifies all issues
- ✅ Sample data fallback provides reasonable estimates

---

## 7. Documentation Updates

### 7.1 User Guide Updates

**File:** `/home/user/MCP-DEV/docs/user-guide.md`

**Add Section:**

#### 13.3 Advanced Model Analysis

**VertiPaq Storage Analysis**
```json
{
  "operation": "analyze_vertipaq_storage",
  "detailed": false
}
```

**Calculation Groups Detection**
```json
{
  "operation": "identify_calc_groups"
}
```

**Cardinality Analysis**
```json
{
  "operation": "analyze_cardinality",
  "object_filter": {
    "cardinality_threshold": 10000
  }
}
```

### 7.2 API Documentation

**Tool: `13_analyze_hybrid_model`**

**New Operations:**

| Operation | Description | Requires Connection |
|-----------|-------------|---------------------|
| `analyze_vertipaq_storage` | Memory footprint analysis | ✅ Yes |
| `identify_calc_groups` | Measure pattern detection | ❌ No (TMDL only) |
| `analyze_cardinality` | High-cardinality detection | ⚠️ Preferred (fallback to sample) |

### 7.3 Example Workflows

**Workflow 1: Complete Model Optimization**

```bash
# Step 1: Export hybrid analysis
13_export_hybrid_analysis(pbip_folder_path="C:/MyModel.SemanticModel")

# Step 2: Analyze storage
13_analyze_hybrid_model(
  analysis_path="C:/MyModel_analysis",
  operation="analyze_vertipaq_storage"
)

# Step 3: Analyze cardinality
13_analyze_hybrid_model(
  analysis_path="C:/MyModel_analysis",
  operation="analyze_cardinality"
)

# Step 4: Identify calc groups
13_analyze_hybrid_model(
  analysis_path="C:/MyModel_analysis",
  operation="identify_calc_groups"
)

# Step 5: Apply recommendations
# (Manual implementation based on recommendations)
```

**Workflow 2: Quick Size Check**

```bash
# Export and immediately check storage
13_export_hybrid_analysis(pbip_folder_path="...")

13_analyze_hybrid_model(
  analysis_path="...",
  operation="analyze_vertipaq_storage"
)
# Review "quick_wins" section for immediate optimizations
```

---

## 8. Success Metrics

### 8.1 Quantitative Goals

| Metric | Target | Measurement |
|--------|--------|-------------|
| Model Size Reduction | 40-60% | Before/after model size in MB |
| Query Performance | 30-50% faster | Average query duration |
| Measure Count Reduction | 50-70% | Count of measures |
| Developer Productivity | 30% faster | Time to add new measures |

### 8.2 Qualitative Goals

- ✅ Recommendations are actionable (specific steps provided)
- ✅ TMDL code is valid and deployable
- ✅ Analysis completes in reasonable time (<15 min)
- ✅ Output is clear and understandable to non-experts

### 8.3 User Acceptance

**Pilot Testing:**
1. Internal testing with 3 sample models
2. Beta testing with 5 external users
3. Gather feedback on:
   - Accuracy of recommendations
   - Clarity of output
   - Performance/speed
   - Ease of implementation

**Launch Criteria:**
- ✅ 95% of recommendations are valid
- ✅ No critical bugs in core operations
- ✅ Documentation complete
- ✅ Performance meets benchmarks

---

## 9. Risk Mitigation

### 9.1 Known Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| DMV queries too slow | High | Medium | Add timeout, progress logging |
| Connection unavailable | Medium | High | Fallback to sample data |
| TMDL code invalid | High | Low | Extensive validation, testing |
| User confusion | Medium | Medium | Clear documentation, examples |

### 9.2 Rollback Plan

If critical issues discovered:
1. **Phase 1:** Disable operation via feature flag
2. **Phase 2:** Remove from tool schema (hide from users)
3. **Phase 3:** Fix issue in separate branch
4. **Phase 4:** Re-enable after validation

---

## 10. Future Enhancements (Post-Launch)

### 10.1 Additional Analysis Features

**Priority 2 (Future):**
- Incremental Refresh candidate detection
- Aggregation table recommendations
- Direct Lake/composite model analysis
- Field parameters optimization
- Auto-date table comprehensive scan

### 10.2 Integration Opportunities

- Integration with Tabular Editor API (auto-apply fixes)
- Export recommendations to Excel/PDF
- CI/CD pipeline integration (automated checks)
- Power BI Service integration (cloud models)

### 10.3 Performance Optimizations

- Parallel DMV queries (where possible)
- Caching of analysis results
- Incremental analysis (only changed objects)
- Progressive loading (show results as they arrive)

---

## Appendix A: Tool Schema Updates

**File:** `/home/user/MCP-DEV/server/tool_schemas.py`

**Update `analyze_hybrid_model` operation enum:**

```python
"operation": {
    "type": "string",
    "description": "Operation to perform",
    "enum": [
        "read_metadata",
        "find_objects",
        "get_object_definition",
        "analyze_dependencies",
        "analyze_performance",
        "get_sample_data",
        "smart_analyze",
        "analyze_vertipaq_storage",  # NEW
        "analyze_cardinality",        # NEW
        "identify_calc_groups"        # NEW
    ],
    "default": "read_metadata"
}
```

**Add new object_filter properties:**

```python
"object_filter": {
    "type": "object",
    "properties": {
        "cardinality_threshold": {
            "type": "integer",
            "description": "Threshold for high cardinality (default: 10000)",
            "default": 10000
        }
    }
}
```

---

## Appendix B: DMV Query Reference

### DMV: DISCOVER_STORAGE_TABLES

**Returns:** Table-level storage statistics

| Column | Type | Description |
|--------|------|-------------|
| TABLE_ID | string | Unique table identifier |
| TABLE_NAME | string | Table name |
| ROWS_COUNT | int64 | Number of rows |
| USED_SIZE | int64 | Total memory used (bytes) |
| DATA_SIZE | int64 | Data size (bytes) |
| DICTIONARY_SIZE | int64 | Dictionary size (bytes) |

### DMV: DISCOVER_STORAGE_TABLE_COLUMNS

**Returns:** Column-level storage statistics

| Column | Type | Description |
|--------|------|-------------|
| DIMENSION_NAME | string | Table name |
| ATTRIBUTE_NAME | string | Column name |
| DICTIONARY_SIZE | int64 | Dictionary size (bytes) |
| DICTIONARY_ENTRIES | int64 | Unique values (cardinality) |
| DATA_SIZE | int64 | Data size (bytes) |
| COLUMN_ENCODING | string | Encoding type (Hash, Value, etc.) |
| DATATYPE | string | Data type |

### DMV: DISCOVER_STORAGE_TABLE_COLUMN_SEGMENTS

**Returns:** Segment-level storage statistics

| Column | Type | Description |
|--------|------|-------------|
| DIMENSION_NAME | string | Table name |
| ATTRIBUTE_NAME | string | Column name |
| SEGMENT_NUMBER | int64 | Segment index |
| RECORDS_COUNT | int64 | Rows in segment |
| USED_SIZE | int64 | Segment size (bytes) |
| COLUMN_ENCODING | string | Encoding type |

---

## Appendix C: DAX Query Patterns

### Get All Columns with Metadata

```dax
EVALUATE
SELECTCOLUMNS(
    INFO.COLUMNS(),
    "TableName", [TableName],
    "ColumnName", [Name],
    "DataType", [DataType],
    "IsHidden", [IsHidden],
    "IsKey", [IsKey]
)
```

### Get Cardinality for Column

```dax
EVALUATE
{
    DISTINCTCOUNT('TableName'[ColumnName]),
    COUNTROWS('TableName')
}
```

### Get All Measures

```dax
EVALUATE
SELECTCOLUMNS(
    INFO.MEASURES(),
    "TableName", [TableName],
    "MeasureName", [Name],
    "Expression", [Expression],
    "FormatString", [FormatString],
    "DisplayFolder", [DisplayFolder]
)
```

---

## Appendix D: Contact & Support

**Document Owner:** Claude AI Assistant
**Last Updated:** 2025-01-18
**Version:** 1.0

**For Questions:**
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: https://docs.claude.com/

---

**End of Implementation Plan**
