# Aggregation Analysis Tool - Implementation Plan

## Executive Summary

This document outlines the implementation plan for a comprehensive **Aggregation Analysis Tool** for the MCP-PowerBi-Finvision server. The tool will analyze Power BI models with manual aggregation tables, providing insights into:

- Which aggregation tables are used by which measures
- How filter context affects aggregation table selection
- Per-visual and per-page aggregation table hit rates
- Performance impact and row savings from aggregation
- Full dependency tree from aggregation-aware measures to their base tables

---

## 1. Background: Understanding Manual Aggregations in Power BI

### 1.1 Aggregation Pattern Overview

Manual aggregations in Power BI use:

1. **Base Fact Table**: Contains detailed transactional data (e.g., `Sales` with millions of rows)
2. **Aggregation Tables**: Pre-computed summarized tables at various granularities:
   - `Agg_Sales_YearQuarter` - Highest level (year/quarter only)
   - `Agg_Sales_YearMonth_Category` - Mid-level (month/category/channel)
3. **Dimension Tables with Aggregation Keys**: Shared between base and agg tables (e.g., `Dim_YearMonth`, `Dim_YearQuarter`)
4. **Aggregation-Aware Measures**: DAX measures that use `SWITCH()` logic based on `ISFILTERED()` checks to route queries to the appropriate aggregation table

### 1.2 Aggregation Detection Measure Pattern

From the example PBIP model, the key pattern is:

```dax
// _AggregationLevel measure
VAR _NeedsDetailFact =
    ISFILTERED(Product[ProductName])
    || ISFILTERED(Product[BrandName])
    || ISFILTERED(Stores[StoreName])
    // ... more detail dimension checks

VAR _NeedsMonthLevel =
    ISFILTERED('Calendar'[MonthOfYear])
    || ISFILTERED(ProductCategory[ProductCategory])
    || ISFILTERED('Channel'[ChannelName])

RETURN
    SWITCH(
        TRUE(),
        _NeedsDetailFact, 1,  // Base Sales table
        _NeedsMonthLevel, 2,  // Agg_Sales_YearMonth_Category
        3                     // Agg_Sales_YearQuarter
    )
```

### 1.3 Aggregation-Aware Measure Pattern

```dax
// Total Sales Amount with smart aggregation switching
VAR _AggLevel = [_AggregationLevel]

VAR _FromBase = SUM(Sales[SalesAmount])

VAR _FromAggYearMonthCategory =
    CALCULATE(
        SUM(Agg_Sales_YearMonth_Category[SalesAmount]),
        USERELATIONSHIP(...)
    )

VAR _FromAggYearQuarter = SUM(Agg_Sales_YearQuarter[SalesAmount])

RETURN
    SWITCH(
        _AggLevel,
        1, _FromBase,
        2, _FromAggYearMonthCategory,
        3, _FromAggYearQuarter,
        _FromBase  // Default fallback
    )
```

---

## 2. Functional Requirements

### 2.1 Core Analysis Capabilities

| # | Requirement | Description |
|---|-------------|-------------|
| R1 | **Aggregation Table Detection** | Automatically identify aggregation tables in the model based on naming patterns, hidden status, and calculated table definitions |
| R2 | **Aggregation Level Measure Detection** | Identify measures that implement aggregation routing logic (ISFILTERED + SWITCH pattern) |
| R3 | **Aggregation-Aware Measure Detection** | Identify measures that reference both base tables and aggregation tables via SWITCH |
| R4 | **Filter Context Analysis** | Analyze which columns/dimensions trigger different aggregation levels |
| R5 | **Visual Aggregation Analysis** | For each visual, determine which aggregation table would be hit based on the filter context |
| R6 | **Page Aggregation Summary** | Summarize aggregation table usage per page |
| R7 | **Report Aggregation Summary** | Provide overall report-level aggregation statistics |
| R8 | **Row Savings Estimation** | Estimate rows saved by using aggregation tables vs base table |
| R9 | **Measure Dependency Analysis** | Full dependency tree showing how measures relate to aggregation tables |
| R10 | **Export/Report Generation** | Generate HTML/JSON reports with aggregation analysis |

### 2.2 Analysis Outputs

#### Per-Visual Analysis
```json
{
  "visual_id": "ce7703a5c89d99c1253e",
  "visual_type": "clusteredColumnChart",
  "title": "Sales by Brand",
  "page": "Page 1",
  "measures_used": ["Total Sales Amount", "Total Cost"],
  "columns_in_context": [
    {"entity": "Product", "column": "BrandName", "triggers_detail": true}
  ],
  "slicers_affecting": ["ProductCategory[Category]"],
  "filter_pane_filters": ["Calendar[Year]"],
  "aggregation_level": 1,
  "aggregation_table_hit": "Base Sales (Detail)",
  "reason": "Product[BrandName] requires detail-level data"
}
```

#### Per-Page Summary
```json
{
  "page_name": "Dashboard",
  "total_visuals": 12,
  "aggregation_breakdown": {
    "base_table": 3,
    "agg_yearmonth_category": 5,
    "agg_yearquarter": 4
  },
  "percentage_optimized": "75%",
  "estimated_row_savings": "2,500,000 rows"
}
```

#### Report Summary
```json
{
  "total_pages": 5,
  "total_visuals": 45,
  "aggregation_summary": {
    "base_table": {"count": 10, "percentage": "22%"},
    "agg_yearmonth_category": {"count": 20, "percentage": "44%"},
    "agg_yearquarter": {"count": 15, "percentage": "33%"}
  },
  "optimization_score": 78,
  "total_estimated_row_savings": "12,500,000 rows"
}
```

---

## 3. Technical Architecture

### 3.1 New Modules to Create

```
core/
├── aggregation/
│   ├── __init__.py
│   ├── aggregation_detector.py       # Detect agg tables and routing measures
│   ├── aggregation_analyzer.py       # Core analysis engine
│   ├── filter_context_analyzer.py    # Analyze filter context per visual
│   └── aggregation_report_builder.py # Build reports and visualizations

server/
├── handlers/
│   └── aggregation_handler.py        # MCP tool handler
```

### 3.2 Integration Points

The aggregation analysis tool will integrate with existing modules:

| Module | Purpose |
|--------|---------|
| `core/tmdl/tmdl_parser.py` | Parse TMDL model definitions |
| `core/dax/dax_reference_parser.py` | Parse DAX expressions for references |
| `core/pbip/pbip_dependency_engine.py` | Leverage existing dependency analysis |
| `server/handlers/report_info_handler.py` | Reuse report/visual parsing logic |

### 3.3 Data Flow

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│   PBIP Model    │────>│ Aggregation Detector│────>│ Aggregation Analyzer │
│ (.SemanticModel)│     │   - Find agg tables │     │   - Analyze measures │
└─────────────────┘     │   - Find routing    │     │   - Build dependency │
                        │     measures        │     │     graph            │
                        └─────────────────────┘     └──────────────────────┘
                                                              │
                                                              ▼
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│   PBIP Report   │────>│ Filter Context      │────>│ Report Builder       │
│   (.Report)     │     │ Analyzer            │     │   - Generate reports │
│                 │     │   - Per visual      │     │   - Calculate stats  │
│                 │     │   - Per page        │     │   - HTML/JSON output │
└─────────────────┘     └─────────────────────┘     └──────────────────────┘
```

---

## 4. Detailed Implementation Plan

### Phase 1: Aggregation Detection (`aggregation_detector.py`)

#### 4.1.1 Aggregation Table Detection

```python
class AggregationTableDetector:
    """Detect aggregation tables in a Power BI model."""

    def detect_aggregation_tables(self, model_data: Dict) -> List[AggregationTable]:
        """
        Identify aggregation tables using multiple heuristics:

        1. Naming patterns: Tables starting with "Agg_", "Agg", "Fact_Agg", etc.
        2. Hidden status: Aggregation tables are typically hidden
        3. Calculated table definition: SUMMARIZECOLUMNS/GROUPBY patterns
        4. Column patterns: Has subset of columns from fact table
        5. Relationship patterns: Connected to dimension tables shared with fact
        """
```

**Detection Heuristics:**

| Heuristic | Weight | Description |
|-----------|--------|-------------|
| Naming pattern | High | Table name contains "Agg", "Aggregat", "Summary" |
| Hidden table | Medium | `isHidden: true` in TMDL |
| Calculated table with SUMMARIZECOLUMNS | High | Partition source uses SUMMARIZECOLUMNS |
| Subset of fact columns | Medium | Has SUM columns that match fact table |
| Shared dimension keys | Medium | FK columns match dimension table PKs |

#### 4.1.2 Aggregation Level Measure Detection

```python
def detect_aggregation_level_measures(self, model_data: Dict) -> List[AggLevelMeasure]:
    """
    Identify measures that implement aggregation level detection logic.

    Pattern to detect:
    - Contains multiple ISFILTERED() calls
    - Uses SWITCH(TRUE(), ...) pattern
    - Returns numeric values (typically 1, 2, 3)
    - References dimension columns in ISFILTERED
    """
```

**DAX Pattern Signatures:**

```python
AGG_LEVEL_PATTERNS = [
    r'ISFILTERED\s*\([^)]+\)\s*\|\|',  # Multiple ISFILTERED with OR
    r'SWITCH\s*\(\s*TRUE\s*\(\s*\)',    # SWITCH(TRUE(), ...) pattern
    r'VAR\s+_Needs\w+\s*=',             # VAR _NeedsXxx pattern
]
```

#### 4.1.3 Aggregation-Aware Measure Detection

```python
def detect_aggregation_aware_measures(self, model_data: Dict,
                                       agg_tables: List[AggregationTable],
                                       agg_level_measure: str) -> List[AggAwareMeasure]:
    """
    Identify measures that switch between base and aggregation tables.

    Pattern to detect:
    - References the aggregation level measure
    - Contains SWITCH on aggregation level
    - References columns from aggregation tables
    - May use USERELATIONSHIP for inactive relationships
    """
```

### Phase 2: Filter Context Analysis (`filter_context_analyzer.py`)

#### 4.2.1 Filter Context Rules Engine

```python
class FilterContextAnalyzer:
    """Analyze filter context to determine aggregation level."""

    def __init__(self, agg_level_measure: AggLevelMeasure):
        """
        Parse the aggregation level measure to extract rules:
        - Which columns trigger detail level
        - Which columns trigger mid-level aggregation
        - Default aggregation level
        """
        self.detail_triggers = []  # Columns that force base table
        self.mid_level_triggers = []  # Columns that force mid-level agg
        self.default_level = 3  # Highest aggregation by default
```

#### 4.2.2 Visual Context Evaluation

```python
def evaluate_visual_context(self, visual_data: Dict) -> AggregationContext:
    """
    Evaluate a visual's filter context to determine aggregation level.

    Context sources:
    1. Visual fields (Category, Values, Tooltips, etc.)
    2. Visual-level filters
    3. Page-level filters (passed in)
    4. Report-level filters (passed in)
    5. Slicers affecting the visual (via sync groups)
    """
```

#### 4.2.3 Slicer Impact Analysis

```python
def analyze_slicer_impact(self, slicer_data: Dict) -> SlicerImpact:
    """
    Determine how a slicer affects aggregation levels.

    Returns:
    - entity: The table the slicer filters
    - column: The column being filtered
    - impacts_level: Which aggregation level it triggers
    - scope: Page-wide or specific sync group
    """
```

### Phase 3: Core Analyzer (`aggregation_analyzer.py`)

#### 4.3.1 Main Analyzer Class

```python
class AggregationAnalyzer:
    """Comprehensive aggregation analysis for PBIP models."""

    def __init__(self, pbip_path: str):
        self.pbip_path = Path(pbip_path)
        self.model_data = None
        self.report_data = None
        self.detector = AggregationTableDetector()
        self.context_analyzer = None

    def analyze(self) -> AggregationAnalysisResult:
        """
        Main analysis entry point.

        Steps:
        1. Load and parse PBIP model
        2. Detect aggregation infrastructure
        3. Load and parse report
        4. Analyze each visual
        5. Aggregate page-level statistics
        6. Aggregate report-level statistics
        7. Calculate optimization metrics
        """
```

#### 4.3.2 Result Data Structures

```python
@dataclass
class AggregationTable:
    name: str
    level: int  # 1=base, 2=mid, 3=high, etc.
    is_hidden: bool
    source_expression: str  # SUMMARIZECOLUMNS definition
    grain_columns: List[str]  # Columns defining the grain
    aggregated_columns: List[AggregatedColumn]
    related_dimensions: List[str]
    estimated_row_count: Optional[int]

@dataclass
class AggLevelMeasure:
    table: str
    name: str
    expression: str
    detail_trigger_columns: List[str]
    mid_level_trigger_columns: List[str]
    levels: Dict[int, str]  # level_num -> description

@dataclass
class AggAwareMeasure:
    table: str
    name: str
    expression: str
    uses_agg_level_measure: str
    table_switches: Dict[int, str]  # level -> table name
    dependencies: List[str]  # Other measures this depends on

@dataclass
class VisualAggregationAnalysis:
    visual_id: str
    visual_type: str
    visual_title: Optional[str]
    page_id: str
    page_name: str
    measures_used: List[str]
    columns_in_context: List[ColumnContext]
    filter_sources: List[FilterSource]
    determined_agg_level: int
    determined_agg_table: str
    reasoning: str

@dataclass
class PageAggregationSummary:
    page_id: str
    page_name: str
    total_visuals: int
    agg_table_breakdown: Dict[str, int]
    agg_table_percentages: Dict[str, float]
    visuals: List[VisualAggregationAnalysis]
    optimization_opportunities: List[str]

@dataclass
class ReportAggregationSummary:
    total_pages: int
    total_visuals: int
    agg_table_breakdown: Dict[str, int]
    agg_table_percentages: Dict[str, float]
    optimization_score: float
    estimated_row_savings: int
    pages: List[PageAggregationSummary]
    recommendations: List[str]
```

### Phase 4: Row Savings Estimation

#### 4.4.1 Row Count Estimation

```python
class RowSavingsEstimator:
    """Estimate row savings from aggregation usage."""

    def estimate_table_rows(self, agg_table: AggregationTable,
                            base_table_rows: int) -> int:
        """
        Estimate rows in aggregation table based on grain.

        Heuristics:
        - Count distinct values in grain columns (if available)
        - Use cardinality estimates from model metadata
        - Fall back to standard reduction ratios by grain level
        """

    def calculate_visual_savings(self, visual: VisualAggregationAnalysis,
                                  table_rows: Dict[str, int]) -> int:
        """
        Calculate rows saved for a single visual.

        Savings = BaseTableRows - AggTableRows (if using agg table)
        """

    def calculate_report_savings(self, report: ReportAggregationSummary,
                                  table_rows: Dict[str, int]) -> int:
        """Sum savings across all visuals."""
```

### Phase 5: Report Builder (`aggregation_report_builder.py`)

#### 4.5.1 HTML Report Generation

```python
class AggregationReportBuilder:
    """Generate visual HTML reports for aggregation analysis."""

    def build_html_report(self, analysis: AggregationAnalysisResult) -> str:
        """
        Generate interactive HTML report with:

        1. Executive Summary Dashboard
           - Overall optimization score
           - Total visuals by aggregation level (pie chart)
           - Total estimated row savings

        2. Aggregation Infrastructure
           - Detected aggregation tables with grain details
           - Aggregation level measure with rule breakdown
           - Aggregation-aware measures list

        3. Per-Page Analysis
           - Visual breakdown per page
           - Aggregation distribution chart
           - Optimization opportunities

        4. Per-Visual Details (expandable)
           - Full filter context
           - Aggregation determination reasoning
           - Measures used and their dependencies

        5. Recommendations
           - Visuals that could be optimized
           - Missing aggregation coverage
           - Suggested aggregation table additions
        """
```

#### 4.5.2 JSON Export

```python
def build_json_export(self, analysis: AggregationAnalysisResult) -> Dict:
    """Export full analysis as structured JSON for programmatic use."""
```

### Phase 6: MCP Handler (`aggregation_handler.py`)

#### 4.6.1 Tool Registration

```python
def register_aggregation_handler(registry):
    """Register aggregation analysis handler."""

    tool = ToolDefinition(
        name="analyze_aggregation",
        description="[PBIP] Analyze manual aggregation table usage across visuals and pages. Shows which aggregation tables are hit, optimization opportunities, and estimated row savings.",
        handler=handle_aggregation_analysis,
        input_schema=TOOL_SCHEMAS.get('analyze_aggregation', {}),
        category="pbip",
        sort_order=140
    )
    registry.register(tool)
```

#### 4.6.2 Tool Schema

```python
# In tool_schemas.py
'analyze_aggregation': {
    "type": "object",
    "properties": {
        "pbip_path": {
            "type": "string",
            "description": "Path to PBIP project folder, .SemanticModel folder, or parent directory"
        },
        "output_format": {
            "type": "string",
            "enum": ["summary", "detailed", "html", "json"],
            "description": "Output format: 'summary' (quick overview), 'detailed' (full analysis), 'html' (interactive report), 'json' (structured data)",
            "default": "summary"
        },
        "output_path": {
            "type": "string",
            "description": "Optional output path for HTML/JSON reports"
        },
        "page_filter": {
            "type": "string",
            "description": "Analyze only pages matching this name (case-insensitive partial match)"
        },
        "include_visual_details": {
            "type": "boolean",
            "description": "Include detailed per-visual analysis (default: true)",
            "default": True
        },
        "estimate_row_savings": {
            "type": "boolean",
            "description": "Calculate estimated row savings (default: true)",
            "default": True
        },
        "base_table_rows": {
            "type": "integer",
            "description": "Optional: Actual row count of base fact table for accurate savings calculation"
        }
    },
    "required": ["pbip_path"],
    "examples": [
        {
            "_description": "Quick aggregation summary",
            "pbip_path": "C:/repos/MyModel",
            "output_format": "summary"
        },
        {
            "_description": "Full detailed analysis",
            "pbip_path": "C:/repos/MyModel",
            "output_format": "detailed",
            "include_visual_details": True
        },
        {
            "_description": "Generate HTML report",
            "pbip_path": "C:/repos/MyModel",
            "output_format": "html",
            "output_path": "C:/reports/agg_analysis.html"
        },
        {
            "_description": "Analyze specific page with row savings",
            "pbip_path": "C:/repos/MyModel",
            "page_filter": "Dashboard",
            "estimate_row_savings": True,
            "base_table_rows": 10000000
        }
    ]
}
```

---

## 5. Implementation Details

### 5.1 Aggregation Level Measure Parsing

The key challenge is parsing the `_AggregationLevel` measure to extract:

1. **Detail trigger columns**: Columns that force use of base table
2. **Mid-level trigger columns**: Columns that allow mid-level aggregation
3. **Level mappings**: What each return value (1, 2, 3) means

```python
def parse_aggregation_level_measure(expression: str) -> AggLevelMeasure:
    """
    Parse an aggregation level detection measure.

    Expected patterns:
    1. VAR definitions with ISFILTERED checks
    2. SWITCH(TRUE(), var1, 1, var2, 2, default) pattern

    Returns structured representation of aggregation rules.
    """

    # Extract VAR definitions
    var_pattern = r'VAR\s+(_\w+)\s*=\s*((?:ISFILTERED[^|]+\|\|\s*)+ISFILTERED[^|]+)'

    # Extract ISFILTERED columns from VAR
    isfiltered_pattern = r"ISFILTERED\s*\(\s*'?([^'\[\)]+)'?\s*\[([^\]]+)\]\s*\)"

    # Extract SWITCH return mapping
    switch_pattern = r'SWITCH\s*\(\s*TRUE\s*\(\s*\)\s*,\s*(.+)\)'
```

### 5.2 Visual Filter Context Resolution

```python
def resolve_visual_filter_context(visual_data: Dict,
                                   page_filters: List[Dict],
                                   report_filters: List[Dict],
                                   slicers: List[Dict]) -> FilterContext:
    """
    Build complete filter context for a visual.

    Priority (lowest to highest):
    1. Report-level filters
    2. Page-level filters
    3. Visual-level filters
    4. Slicers (via sync groups)
    5. Visual fields (implicit filter from Category/Legend/etc.)

    Returns list of all columns in filter context.
    """
```

### 5.3 Aggregation Level Determination

```python
def determine_aggregation_level(filter_context: FilterContext,
                                  agg_rules: AggLevelMeasure) -> Tuple[int, str]:
    """
    Determine which aggregation level applies given filter context.

    Logic:
    1. If ANY detail trigger column is in context -> Level 1 (base table)
    2. Else if ANY mid-level trigger column is in context -> Level 2
    3. Else -> Level 3 (highest aggregation)

    Returns (level_number, reasoning_explanation)
    """

    # Check detail triggers first (highest priority)
    for col in agg_rules.detail_trigger_columns:
        if col in filter_context.columns:
            return (1, f"Column {col} requires detail-level data")

    # Check mid-level triggers
    for col in agg_rules.mid_level_trigger_columns:
        if col in filter_context.columns:
            return (2, f"Column {col} allows mid-level aggregation")

    # Default to highest aggregation
    return (3, "No dimension filtering requires detail data")
```

---

## 6. Edge Cases and Considerations

### 6.1 Complex Aggregation Patterns

| Pattern | Handling |
|---------|----------|
| **Multiple aggregation level measures** | Support multiple detection, allow user to specify which to use |
| **Nested aggregation switching** | Parse recursive measure dependencies |
| **Dynamic aggregation based on DAX conditions** | Flag as "dynamic" with warning |
| **USERELATIONSHIP in aggregation measures** | Track inactive relationship usage |
| **Calculation groups affecting aggregation** | Analyze calculation item expressions |

### 6.2 Report Analysis Complexities

| Scenario | Handling |
|----------|----------|
| **Drillthrough pages** | Analyze as separate context with source page context |
| **Bookmarks** | Flag that bookmarks may alter filter context |
| **Cross-filtering visuals** | Note potential cascading filter effects |
| **What-if parameters** | Include in filter context analysis |
| **Field parameters** | Resolve to actual columns for analysis |

### 6.3 Estimation Challenges

| Challenge | Approach |
|-----------|----------|
| **Unknown base table size** | Use default ratio estimates or prompt for input |
| **Variable filter selections** | Analyze "worst case" (all filters) and "best case" (no filters) |
| **Calculated columns** | Include in dependency analysis |
| **Time intelligence** | Special handling for date hierarchy columns |

---

## 7. Testing Strategy

### 7.1 Unit Tests

```
tests/
├── test_aggregation_detector.py
│   ├── test_detect_agg_tables_by_name
│   ├── test_detect_agg_tables_by_definition
│   ├── test_detect_agg_level_measure
│   └── test_detect_agg_aware_measures
├── test_filter_context_analyzer.py
│   ├── test_parse_visual_fields
│   ├── test_combine_filter_sources
│   └── test_determine_agg_level
├── test_aggregation_analyzer.py
│   ├── test_full_analysis_pipeline
│   ├── test_page_aggregation
│   └── test_report_aggregation
└── test_row_savings_estimator.py
    ├── test_table_row_estimation
    └── test_savings_calculation
```

### 7.2 Integration Tests

Use the provided PBIP model (`Contoso Sales Sample for Power BI Desktop`) as test fixture:

- **Expected aggregation tables**: `Agg_Sales_YearMonth_Category`, `Agg_Sales_YearQuarter`
- **Expected level measure**: `_AggregationLevel`
- **Expected aware measures**: `Total Sales Amount`, `Total Cost`, `Total Quantity`, `Transaction Count`

### 7.3 Test PBIP Model

The model at `C:\Users\bjorn.braet\OneDrive - Finvision\FINTICX - Documenten\M01 - Wealth Reporting\04-Analytics\Aggregation Analysis MCP` contains:

**Tables:**
- `Sales` (base fact table)
- `Agg_Sales_YearMonth_Category` (mid-level aggregation)
- `Agg_Sales_YearQuarter` (high-level aggregation)
- Dimension tables: `Calendar`, `Product`, `ProductCategory`, `Stores`, `Channel`, etc.

**Measures:**
- `_AggregationLevel` - Detection measure
- `_AggregationUsed (Debug)` - Debug output measure
- `Total Sales Amount`, `Total Cost`, `Total Quantity` - Aggregation-aware measures

**Report:**
- 3 pages with various visuals
- Visuals using different dimension combinations

---

## 8. Future Enhancements

### 8.1 Phase 2 Features

| Feature | Description |
|---------|-------------|
| **Live model analysis** | Connect to running Power BI Desktop for actual row counts |
| **DAX query generation** | Generate test queries to verify aggregation behavior |
| **Aggregation recommendations** | Suggest new aggregation tables based on visual patterns |
| **Historical tracking** | Track aggregation optimization over time |
| **Performance benchmarking** | Measure actual query times with/without aggregations |

### 8.2 Integration with Other Tools

| Tool | Integration |
|------|-------------|
| **analyze_pbip_repository** | Add aggregation section to existing PBIP analysis |
| **generate_pbip_dependency_diagram** | Highlight aggregation table relationships |
| **full_analysis** | Include aggregation check in performance analysis |
| **dax_intelligence** | Enhance with aggregation context analysis |

---

## 9. File Structure Summary

```
MCP-PowerBi-Finvision/
├── core/
│   └── aggregation/
│       ├── __init__.py
│       ├── aggregation_detector.py      # ~300 lines
│       ├── filter_context_analyzer.py   # ~250 lines
│       ├── aggregation_analyzer.py      # ~400 lines
│       ├── row_savings_estimator.py     # ~150 lines
│       └── aggregation_report_builder.py # ~500 lines
├── server/
│   └── handlers/
│       └── aggregation_handler.py       # ~200 lines
├── server/
│   └── tool_schemas.py                  # Add analyze_aggregation schema
├── tests/
│   └── test_aggregation_*.py            # ~400 lines total
└── docs/
    └── AGGREGATION_ANALYSIS_IMPLEMENTATION_PLAN.md  # This file
```

---

## 10. Implementation Order

### Step 1: Core Detection (Day 1-2)
1. Create `core/aggregation/__init__.py`
2. Implement `aggregation_detector.py`
   - Aggregation table detection
   - Aggregation level measure detection
   - Aggregation-aware measure detection

### Step 2: Filter Context Analysis (Day 2-3)
3. Implement `filter_context_analyzer.py`
   - Parse visual field contexts
   - Combine filter sources
   - Determine aggregation level

### Step 3: Main Analyzer (Day 3-4)
4. Implement `aggregation_analyzer.py`
   - Full analysis pipeline
   - Data structure definitions
   - Page and report aggregation

### Step 4: Row Savings (Day 4)
5. Implement `row_savings_estimator.py`
   - Table size estimation
   - Savings calculation

### Step 5: Report Generation (Day 5-6)
6. Implement `aggregation_report_builder.py`
   - HTML report with charts
   - JSON export

### Step 6: MCP Integration (Day 6-7)
7. Create `aggregation_handler.py`
8. Add tool schema
9. Register handler

### Step 7: Testing (Day 7-8)
10. Write unit tests
11. Integration testing with PBIP model
12. Documentation updates

---

## Appendix A: Example Output

### A.1 Summary Output

```
AGGREGATION ANALYSIS SUMMARY
============================

Model: Contoso Sales Sample for Power BI Desktop
Path: C:\Users\...\Aggregation Analysis MCP

AGGREGATION INFRASTRUCTURE
--------------------------
Aggregation Tables Found: 2
  1. Agg_Sales_YearQuarter (Level 3 - Highest)
     Grain: YearQuarterKey
     Measures: SalesAmount, TotalCost, SalesQuantity, ReturnAmount, DiscountAmount, TransactionCount

  2. Agg_Sales_YearMonth_Category (Level 2 - Mid)
     Grain: YearMonthKey, ProductCategoryKey, Channel
     Measures: SalesAmount, TotalCost, SalesQuantity, ReturnAmount, DiscountAmount, TransactionCount

Aggregation Level Measure: Sales[_AggregationLevel]
  Level 1 (Base): Triggered by Product[ProductName], Product[BrandName], Stores[StoreName], ...
  Level 2 (Mid): Triggered by Calendar[MonthName], ProductCategory[ProductCategory], Channel[ChannelName]
  Level 3 (High): Default when no dimension filtering

Aggregation-Aware Measures: 4
  - Total Sales Amount, Total Cost, Total Quantity, Transaction Count

REPORT ANALYSIS
---------------
Total Pages: 3
Total Visuals: 9

Aggregation Distribution:
  Base Table (Level 1):    3 visuals (33%)
  Mid-Level Agg (Level 2): 3 visuals (33%)
  High-Level Agg (Level 3): 3 visuals (33%)

OPTIMIZATION SCORE: 67/100

ESTIMATED ROW SAVINGS
---------------------
Base Table Rows: 10,000,000 (estimated)
Avg Query Rows Saved: 8,500,000 rows per query
Total Report Savings: ~85% reduction in data scanned

RECOMMENDATIONS
---------------
1. Visual "Sales by Brand" on Page 1 hits base table due to Product[BrandName]
   - Consider adding brand to mid-level aggregation if frequently used

2. 3 visuals could benefit from higher aggregation with filter redesign
```

### A.2 Per-Visual Detail Output

```
VISUAL ANALYSIS: ce7703a5c89d99c1253e
========================================
Type: clusteredColumnChart
Title: Full Bar Page 1
Page: Page 1

Measures Used:
  - Total Cost (aggregation-aware)
  - Total Quantity (aggregation-aware)
  - Total Return Amount (NOT aggregation-aware - uses base only)
  - Total Sales Amount (aggregation-aware)

Columns in Context:
  - Product[BrandName] (Category axis) -> TRIGGERS DETAIL LEVEL

Filter Sources:
  - Visual field: Product[BrandName]
  - Page filters: (none)
  - Report filters: (none)

AGGREGATION DETERMINATION:
  Level: 1 (Base Table)
  Table: Sales
  Reason: Product[BrandName] is in filter context, which requires detail-level data

Optimization Note:
  This visual requires base table due to Product[BrandName] grouping.
  If brand-level aggregation is frequently needed, consider:
  - Adding Agg_Sales_YearMonth_Brand table
  - Or accepting base table queries for this use case
```

---

*Document Version: 1.0*
*Created: 2025-12-30*
*For: MCP-PowerBi-Finvision v6.x*
