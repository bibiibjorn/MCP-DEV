# Power BI Model Analysis - Hybrid Output Format Plan

## Purpose
Design an optimal output format for Power BI model analysis that maximizes Claude's reading efficiency while providing complete model fidelity. Combines TMDL's selective file access with JSON's pre-computed insights and sample data for comprehensive analysis.

## Problem Statement
Current challenges:
- Large model exports (66+ tables, 699+ measures) are slow to parse
- Claude needs both detailed object definitions AND cross-model insights
- Sample data is needed for validation but shouldn't bloat main files
- Need to support both selective queries ("show me measure X") and broad analysis ("find performance issues")

## Solution: Three-Layer Architecture

### Layer 1: TMDL (Source of Truth)
**Purpose:** Complete model definition with perfect fidelity
**Access pattern:** Selective file reading for specific objects

### Layer 2: JSON Analysis (Foundation Layer)
**Purpose:** Pre-computed metadata, object catalog, and dependency graph
**Access pattern:** Fast metadata queries and dependency lookups
**Note:** Performance analysis and recommendations are generated on-demand by MCP tools

### Layer 3: Sample Data (Validation Layer)
**Purpose:** Preview data for validation and example generation
**Access pattern:** On-demand loading per table

---

## Why Performance Analysis is On-Demand

**Design Philosophy:** Generate insights when needed, not upfront

### Rationale:
1. **Faster exports** - Export completes in ~8 seconds instead of ~12 seconds
2. **Smaller packages** - 7.3MB instead of 7.5MB (performance.json + recommendations.json ~250KB)
3. **Fresh analysis** - Analysis reflects current model state when requested
4. **Focused insights** - Only analyze what's relevant to current query
5. **Flexible filtering** - Can adjust priority/category without regenerating files

### Trade-offs:
- ✅ **Pro:** Export is faster and leaner
- ✅ **Pro:** Analysis always current (no stale pre-computed data)
- ✅ **Pro:** Can focus analysis on specific areas
- ⚠️ **Con:** First analysis request takes ~250-500ms instead of ~30ms
- ⚠️ **Con:** Repeated requests without caching will re-analyze

### Mitigation:
- MCP server implements response caching (analysis results cached for 5 minutes)
- For repeated analysis, first request pays 250ms cost, subsequent requests <50ms from cache
- Most queries don't need full performance analysis, so majority are unaffected

### When Analysis Happens:
1. **User asks:** "Find performance issues" → `analyze_performance` runs (~250ms)
2. **User asks:** "Recommend optimizations" → `generate_recommendations` runs (~200ms)
3. **User asks:** "Why is measure X slow?" → Partial analysis of that measure (~50ms)
4. **User asks:** "Show me DimDate table" → No analysis needed (~55ms)

**Bottom line:** Pay the analysis cost only when needed, keep everything else fast.

---

## Context Window & Token Management

### The Challenge
**Large models can exceed Claude's context window:**
- 66 tables × 20KB TMDL = 1.3MB
- 699 measures in single file = 500KB  
- All dependencies = 200KB
- Sample data = 5MB
- **Total:** ~7MB raw text = ~2-3M tokens

**Claude's limits:**
- Context window: 200K tokens
- Output: 8K tokens per response
- **Risk:** Cannot fit entire model in single conversation

### Solution: Streaming & Chunked Analysis

#### Strategy 1: Never Load Entire Model
**Principle:** MCP tools return summaries, not raw content

**Bad approach:**
```typescript
// ❌ Returns 500KB of DAX - exceeds limits
return {
  all_measures: readFile("_measures.tmdl") // 699 measures
}
```

**Good approach:**
```typescript
// ✅ Returns summary only - ~2KB
return {
  total_measures: 699,
  complex_measures: [
    {name: "Rolling 12M", complexity: 12, line: 234},
    {name: "Allocation %", complexity: 8, line: 456}
  ],
  by_folder: {"Time Intelligence": 89, "Allocations": 67}
}
```

#### Strategy 2: Paginated Analysis
**For full model analysis, process in batches:**

```typescript
analyze_performance({
  batch_size: 50,  // Process 50 measures at a time
  batch_number: 1  // Which batch (1-14 for 699 measures)
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

#### Strategy 3: Incremental Aggregation
**MCP server maintains state across calls:**

```typescript
// First call - starts analysis
analyze_performance({
  analysis_id: "session_123",
  start: true
})
// Server creates analysis session, processes first chunk
// Returns: {session_id, progress: "10%", preliminary_results}

// Subsequent calls - continue analysis
analyze_performance({
  analysis_id: "session_123", 
  continue: true
})
// Server processes next chunk, aggregates
// Returns: {session_id, progress: "50%", updated_results}

// Final call - get complete results
analyze_performance({
  analysis_id: "session_123",
  finalize: true
})
// Returns: {complete_analysis, recommendations}
```

#### Strategy 4: Hierarchical Summarization
**Process details, return summaries:**

```python
def analyze_measures_batch(measures: list[Measure]) -> BatchSummary:
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

### Full Model Analysis Workflow

**User request:** "Analyze my entire model for performance issues and give me recommendations"

**Claude's multi-step approach:**

```
Step 1: Get model overview
→ read_model_metadata()
→ Returns: 66 tables, 699 measures, 78 relationships

Step 2: Analyze measures in batches
→ analyze_performance(focus="measures", batch=1/14)
→ analyze_performance(focus="measures", batch=2/14)
→ ... (14 calls total)
→ Accumulates: 23 complex measures flagged

Step 3: Analyze tables for cardinality
→ analyze_performance(focus="cardinality", batch=1/3)
→ analyze_performance(focus="cardinality", batch=2/3)  
→ analyze_performance(focus="cardinality", batch=3/3)
→ Accumulates: 8 high-cardinality columns found

Step 4: Analyze relationships
→ analyze_performance(focus="relationships")
→ Returns: 0 bidirectional, 0 many-to-many (good)

Step 5: Generate recommendations
→ generate_recommendations(based_on_previous_analysis)
→ Returns: 31 recommendations across 4 priorities

Step 6: Synthesize for user
→ Claude summarizes all findings in final response
→ Presents top 10 critical items with implementation steps
```

**Total tool calls:** ~20  
**Total tokens processed:** ~80,000 (well under 200K limit)  
**Time:** ~8 seconds for complete analysis

### Preventing Token Overflow

#### Rule 1: Never Return Full TMDL Files
```typescript
// ❌ BAD - Returns entire file
async function get_all_measures(analysis_path: string) {
  return {
    measures: await fs.readFile(`${analysis_path}/model.bim/expressions/_measures.tmdl`)
  };
}

// ✅ GOOD - Returns summary + specific measures
async function get_measures_summary(analysis_path: string, filter?: MeasureFilter) {
  const catalog = JSON.parse(await fs.readFile(`${analysis_path}/analysis/catalog.json`));
  const filtered = catalog.measures.filter(m => matchesFilter(m, filter));
  
  return {
    total_measures: catalog.measures.length,
    filtered_count: filtered.length,
    measures: filtered.map(m => ({
      name: m.name,
      table: m.table,
      complexity: m.complexity_score,
      tmdl_location: m.tmdl_path + ":" + m.line_number
    }))
  };
}
```

#### Rule 2: Implement Response Size Limits
```typescript
const MAX_RESPONSE_SIZE = 50_000; // ~12K tokens

function truncate_if_needed(results: any): any {
  const serialized = JSON.stringify(results);
  
  if (serialized.length > MAX_RESPONSE_SIZE) {
    return {
      truncated: true,
      total_items: results.items.length,
      items: results.items.slice(0, 100), // Return first 100
      message: "Results truncated. Use pagination or filtering to see more."
    };
  }
  
  return results;
}
```

#### Rule 3: Progressive Disclosure
```typescript
// Start with high-level summary
analyze_performance({detailed: false})
// Returns: {critical: 2, high: 8, medium: 15, low: 6}

// If user wants details on critical items:
analyze_performance({
  detailed: true,
  priority: "critical"  // Only return critical items
})
// Returns: Full details for 2 critical issues

// If user wants to see a specific issue:
get_object_definition({
  object_name: "Rolling 12M Average"
})
// Returns: Full TMDL for just that measure
```

#### Rule 4: Streaming for Large Operations
```typescript
// For very large models (1000+ measures)
async function* analyze_performance_stream(analysis_path: string) {
  const measures = await load_catalog(analysis_path);
  const batch_size = 50;
  
  for (let i = 0; i < measures.length; i += batch_size) {
    const batch = measures.slice(i, i + batch_size);
    const results = await analyze_batch(batch);
    
    yield {
      progress: (i + batch_size) / measures.length,
      batch_results: results,
      accumulated_summary: get_summary_so_far()
    };
  }
}
```

### Cache Strategy

**MCP server maintains internal cache:**

```typescript
interface AnalysisCache {
  model_hash: string;  // Hash of catalog.json to detect changes
  timestamp: number;
  results: {
    performance_analysis?: PerformanceResults;
    recommendations?: Recommendation[];
    batch_analyses?: Map<string, any>;
  };
}

// Cache invalidation rules:
// 1. After 5 minutes
// 2. If catalog.json hash changes
// 3. If explicit cache_clear requested
```

**Benefits:**
- First `analyze_performance` call: 250ms
- Subsequent calls within 5 min: <50ms  
- Reduces redundant analysis
- Stays under token limits

### Monitoring Token Usage

```typescript
interface ToolResponse {
  data: any;
  metadata: {
    tokens_in_response: number;
    tokens_estimated: number;
    truncated: boolean;
    batch_info?: {
      current: number;
      total: number;
    };
  };
}

// Tools self-report token usage
function create_response(data: any): ToolResponse {
  const serialized = JSON.stringify(data);
  const estimated_tokens = serialized.length / 4;  // Rough estimate
  
  return {
    data,
    metadata: {
      tokens_in_response: serialized.length,
      tokens_estimated: estimated_tokens,
      truncated: false
    }
  };
}
```

### Testing Token Limits

**Test scenarios:**
1. ✅ Small model (10 tables, 50 measures) - single call
2. ✅ Medium model (30 tables, 300 measures) - 3-5 calls
3. ✅ Large model (66 tables, 699 measures) - 15-20 calls
4. ✅ Very large model (100+ tables, 1000+ measures) - 30+ calls with batching
5. ✅ Extreme model (200+ tables, 2000+ measures) - streaming required

**Success criteria:**
- No single tool response >50KB
- Total conversation stays under 150K tokens
- Clear progress indicators for long operations
- Graceful degradation with truncation warnings

---

## File Format Support: PBIX vs PBIP

### Overview

**PBIX (Power BI Desktop File)**
- Single compressed file (`.pbix`)
- Contains model, reports, data
- Binary format
- Standard for single-developer workflows

**PBIP (Power BI Project)**
- Folder structure with text files
- Contains TMDL files natively
- Git-friendly format
- Designed for team collaboration and version control

### Which Format to Use?

#### Export Tool Support

**Option 1: PBIX as Input** ✅ **RECOMMENDED**
```typescript
export_model_analysis({
  model_path: "C:/Models/FamilyOffice.pbix",
  output_directory: "C:/Analysis/FamilyOffice"
})
```

**How it works:**
1. Tool connects to Tabular Object Model (TOM) via AMO/ADOMD
2. Opens PBIX file (requires Power BI Desktop or Analysis Services)
3. Extracts model definition to TMDL
4. Generates JSON analysis files
5. Exports sample data from model

**Requirements:**
- Microsoft.AnalysisServices.Tabular NuGet package
- Power BI Desktop installed (or SSAS)
- Read access to `.pbix` file

**Advantages:**
- ✅ Works with standard Power BI files
- ✅ Most users already have `.pbix` files
- ✅ Can export from any existing model
- ✅ Handles data refresh scenarios

**Limitations:**
- ⚠️ Requires Power BI Desktop runtime
- ⚠️ Cannot run on Linux without workarounds
- ⚠️ Must extract TMDL (adds processing time)

---

**Option 2: PBIP as Input** ✅ **FASTER, NO EXTRACTION NEEDED**
```typescript
export_model_analysis({
  model_path: "C:/Models/FamilyOffice.pbip",
  output_directory: "C:/Analysis/FamilyOffice"
})
```

**How it works:**
1. Tool reads existing TMDL files from `.pbip/definition/`
2. Copies TMDL structure directly (no extraction!)
3. Generates JSON analysis files
4. **Cannot export sample data** (PBIP has no data)

**Requirements:**
- No special libraries needed
- Just filesystem access
- Works on any OS

**Advantages:**
- ✅ **Much faster** - no TMDL extraction (~2 seconds vs ~8 seconds)
- ✅ **Cross-platform** - works on Linux/Mac/Windows
- ✅ TMDL already available in `.pbip/definition/`
- ✅ No Power BI Desktop required
- ✅ Perfect for CI/CD pipelines

**Limitations:**
- ⚠️ **No sample data** - PBIP stores no data
- ⚠️ Fewer users have PBIP format
- ⚠️ Must convert PBIX → PBIP first

---

### Recommended Implementation Strategy

#### Phase 1: Support PBIX First
**Why:**
- Most users have `.pbix` files
- Complete functionality (including sample data)
- Proven TOM extraction workflow

**Implementation:**
```csharp
using Microsoft.AnalysisServices.Tabular;

public class PbixExporter {
  public async Task<ExportResult> ExportModel(string pbixPath, string outputDir) {
    // 1. Open PBIX via TOM
    var server = new Server();
    server.Connect($"Provider=MSOLAP;Data Source={pbixPath}");
    var database = server.Databases[0];
    var model = database.Model;
    
    // 2. Export to TMDL
    var tmdlPath = Path.Combine(outputDir, "model.bim");
    TmdlSerializer.SerializeDatabase(database, tmdlPath);
    
    // 3. Generate analysis files
    await GenerateMetadata(model, outputDir);
    await GenerateCatalog(model, outputDir);
    await GenerateDependencies(model, outputDir);
    
    // 4. Export sample data
    await ExportSampleData(model, outputDir);
    
    return new ExportResult { Success = true, Path = outputDir };
  }
}
```

#### Phase 2: Add PBIP Fast Path
**Why:**
- Dramatic speed improvement
- Enables CI/CD scenarios
- No dependency on Power BI Desktop

**Implementation:**
```typescript
export async function exportFromPbip(pbipPath: string, outputDir: string) {
  const definitionPath = path.join(pbipPath, ".pbip", "definition");
  
  // PBIP already has TMDL - just copy it!
  const tmdlSource = path.join(definitionPath, "model.tmdl");
  const tmdlDest = path.join(outputDir, "model.bim");
  await fs.cp(definitionPath, tmdlDest, { recursive: true });
  
  // Parse TMDL to generate analysis files
  const model = await parseTmdlFiles(tmdlDest);
  await generateMetadata(model, outputDir);
  await generateCatalog(model, outputDir);
  await generateDependencies(model, outputDir);
  
  // Note: No sample data from PBIP
  return {
    success: true,
    path: outputDir,
    note: "Sample data not available from PBIP format"
  };
}
```

### Handling Both Formats

**Auto-detection:**
```typescript
export async function exportModelAnalysis(modelPath: string, outputDir: string) {
  // Detect format
  if (modelPath.endsWith('.pbix')) {
    return await exportFromPbix(modelPath, outputDir);
  } else if (modelPath.endsWith('.pbip') || await isPbipDirectory(modelPath)) {
    return await exportFromPbip(modelPath, outputDir);
  } else if (modelPath.endsWith('.bim')) {
    return await exportFromBim(modelPath, outputDir);
  } else {
    throw new Error('Unsupported format. Use .pbix, .pbip, or .bim');
  }
}

async function isPbipDirectory(path: string): Promise<boolean> {
  try {
    const definitionPath = join(path, '.pbip', 'definition');
    const stats = await fs.stat(definitionPath);
    return stats.isDirectory();
  } catch {
    return false;
  }
}
```

### Sample Data Handling

**For PBIX:**
```csharp
async Task ExportSampleData(Model model, string outputDir) {
  var sampleDataDir = Path.Combine(outputDir, "sample_data");
  Directory.CreateDirectory(sampleDataDir);
  
  foreach (var table in model.Tables) {
    var query = $"EVALUATE TOPN(1000, {table.Name})";
    var result = ExecuteDaxQuery(query);
    
    // Write to Parquet
    var parquetPath = Path.Combine(sampleDataDir, $"{table.Name}.parquet");
    await WriteParquet(result, parquetPath);
  }
}
```

**For PBIP:**
```typescript
// Sample data cannot be exported from PBIP (no data in format)
// Options:
// 1. Skip sample data generation
// 2. Require user to provide separate data source
// 3. Create mock/synthetic data based on schema
```

---

## Row Count & Column Usage Tracking

### How Row Counts Are Obtained

**From PBIX (via TOM):**
```csharp
async Task<Dictionary<string, long>> GetRowCounts(Model model) {
  var rowCounts = new Dictionary<string, long>();
  
  foreach (var table in model.Tables) {
    // Query row count via DMV (Dynamic Management View)
    var query = $@"
      SELECT 
        [DIMENSION_NAME] as TableName,
        [ROWS_COUNT] as RowCount
      FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
      WHERE [DIMENSION_NAME] = '{table.Name}'
      GROUP BY [DIMENSION_NAME]
    ";
    
    var result = ExecuteDmvQuery(query);
    rowCounts[table.Name] = result.Rows[0]["RowCount"];
  }
  
  return rowCounts;
}
```

**Alternative method (DAX query):**
```csharp
// For each table, count rows
var daxQuery = $"EVALUATE ROW(\"RowCount\", COUNTROWS({table.Name}))";
var rowCount = ExecuteDaxQuery(daxQuery);
```

**From PBIP:**
- Row counts NOT available (no data in PBIP)
- Set row_count to `null` or `-1` in metadata
- Document limitation for users

### How Column Usage Is Tracked

**1. Relationship Usage:**
```csharp
bool IsColumnUsedInRelationships(Column column) {
  var model = column.Table.Model;
  
  return model.Relationships.Any(r => 
    (r.FromColumn == column) || (r.ToColumn == column)
  );
}
```

**2. Measure References:**
```csharp
List<string> GetMeasuresThatUseColumn(Column column) {
  var model = column.Table.Model;
  var columnRef = $"{column.Table.Name}[{column.Name}]";
  var usedInMeasures = new List<string>();
  
  foreach (var measure in model.AllMeasures) {
    // Parse DAX expression for column references
    var dax = measure.Expression;
    if (ContainsColumnReference(dax, columnRef)) {
      usedInMeasures.Add(measure.Name);
    }
  }
  
  return usedInMeasures;
}

bool ContainsColumnReference(string daxExpression, string columnRef) {
  // Use DAX parser or regex to find column references
  // Account for both [Table].[Column] and Table[Column] syntax
  var patterns = new[] {
    $@"\b{Regex.Escape(columnRef)}\b",
    $@"\[{column.Table.Name}\]\.\[{column.Name}\]"
  };
  
  return patterns.Any(p => Regex.IsMatch(daxExpression, p));
}
```

**3. Visual/Report Usage (Advanced):**
```csharp
// This requires parsing PBIX report definition
bool IsColumnUsedInVisuals(Column column) {
  // For PBIX: Parse report JSON from model
  var reportJson = ExtractReportDefinition(pbixPath);
  var pages = ParsePages(reportJson);
  
  foreach (var page in pages) {
    foreach (var visual in page.Visuals) {
      // Check visual's data bindings
      if (visual.DataBindings.Any(db => 
        db.Table == column.Table.Name && 
        db.Column == column.Name)) {
        return true;
      }
    }
  }
  
  return false;
}

// Note: For PBIP, reports are in separate .pbir files
```

**4. Calculated Column Dependencies:**
```csharp
bool IsColumnUsedInCalculatedColumns(Column column) {
  var table = column.Table;
  var columnRef = $"[{column.Name}]";
  
  foreach (var calcColumn in table.Columns.Where(c => c.Type == ColumnType.Calculated)) {
    if (ContainsColumnReference(calcColumn.Expression, columnRef)) {
      return true;
    }
  }
  
  return false;
}
```

**5. RLS (Row-Level Security) Usage:**
```csharp
bool IsColumnUsedInRLS(Column column) {
  var model = column.Table.Model;
  var columnRef = $"{column.Table.Name}[{column.Name}]";
  
  foreach (var role in model.Roles) {
    foreach (var permission in role.TablePermissions) {
      if (permission.Table == column.Table && 
          ContainsColumnReference(permission.FilterExpression, columnRef)) {
        return true;
      }
    }
  }
  
  return false;
}
```

### Column Usage Summary

**Complete Usage Check:**
```csharp
ColumnUsageInfo AnalyzeColumnUsage(Column column) {
  return new ColumnUsageInfo {
    Name = column.Name,
    Table = column.Table.Name,
    DataType = column.DataType.ToString(),
    IsKey = column.IsKey,
    IsHidden = column.IsHidden,
    
    // Usage tracking
    UsedInRelationships = IsColumnUsedInRelationships(column),
    UsedInMeasures = GetMeasuresThatUseColumn(column).Count > 0,
    MeasureReferences = GetMeasuresThatUseColumn(column).Count,
    UsedInCalculatedColumns = IsColumnUsedInCalculatedColumns(column),
    UsedInRLS = IsColumnUsedInRLS(column),
    UsedInVisuals = IsColumnUsedInVisuals(column),
    
    // Derived fields
    IsUnused = IsColumnCompletelyUnused(column),
    
    // Cardinality (if available)
    Cardinality = GetColumnCardinality(column),
    CardinalityRatio = GetCardinalityRatio(column)
  };
}

bool IsColumnCompletelyUnused(Column column) {
  return !IsColumnUsedInRelationships(column) &&
         !IsColumnUsedInMeasures(column) &&
         !IsColumnUsedInCalculatedColumns(column) &&
         !IsColumnUsedInRLS(column) &&
         !IsColumnUsedInVisuals(column);
}
```

### Cardinality Calculation

**Method 1: DMV Query (Fastest):**
```csharp
long GetColumnCardinality(Column column) {
  var query = $@"
    SELECT 
      [COLUMN_NAME],
      [DICTIONARY_SIZE] as Cardinality
    FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS
    WHERE [DIMENSION_NAME] = '{column.Table.Name}'
      AND [COLUMN_NAME] = '{column.Name}'
  ";
  
  var result = ExecuteDmvQuery(query);
  return result.Rows[0]["Cardinality"];
}
```

**Method 2: DAX Query (Slower but reliable):**
```csharp
long GetColumnCardinality(Column column) {
  var daxQuery = $@"
    EVALUATE 
    ROW(
      ""Cardinality"", 
      DISTINCTCOUNT({column.Table.Name}[{column.Name}])
    )
  ";
  
  var result = ExecuteDaxQuery(daxQuery);
  return result.Rows[0]["Cardinality"];
}
```

### Generation Process

**During export_model_analysis:**

1. **Extract row counts** from model (PBIX only)
2. **Analyze each column** for usage patterns
3. **Calculate cardinality** for string/large columns
4. **Store in catalog.json** with per-column details
5. **Store in metadata.json** with table-level summaries

**Token impact:**
- Full column details in catalog.json: ~100 bytes per column
- For 542 columns: ~54KB total
- Summary in metadata.json: ~5KB
- Still well under limits

### Usage in Analysis

**Example: Find all unused high-cardinality columns:**
```typescript
// Query catalog.json
const unusedHighCardinalityColumns = catalog.tables
  .flatMap(t => t.columns)
  .filter(c => 
    c.is_unused && 
    c.cardinality > 100000
  )
  .sort((a, b) => b.cardinality - a.cardinality);

// Result prioritized by memory savings
return unusedHighCardinalityColumns.map(c => ({
  table: c.table,
  column: c.name,
  cardinality: c.cardinality,
  estimated_memory_mb: estimateMemory(c),
  recommendation: "Remove to save memory"
}));
```

**Example: Find large fact tables:**
```typescript
// Query metadata.json
const largeTables = metadata.row_counts.by_table
  .filter(t => t.row_count > 1000000)
  .sort((a, b) => b.row_count - a.row_count);

// Check if aggregation opportunity
return largeTables.map(t => ({
  table: t.table,
  row_count: t.row_count,
  recommendation: "Consider aggregation table for dashboard queries",
  potential_speedup: estimateSpeedup(t.row_count)
}));
```

---

### Sample Data Handling

**For PBIX:**
```csharp
async Task ExportSampleData(Model model, string outputDir) {
  var sampleDataDir = Path.Combine(outputDir, "sample_data");
  Directory.CreateDirectory(sampleDataDir);
  
  foreach (var table in model.Tables) {
    var query = $"EVALUATE TOPN(1000, {table.Name})";
    var result = ExecuteDaxQuery(query);
    
    // Write to Parquet
    var parquetPath = Path.Combine(sampleDataDir, $"{table.Name}.parquet");
    await WriteParquet(result, parquetPath);
  }
}
```

**For PBIP:**
```typescript
// Sample data cannot be exported from PBIP (no data in format)
// Options:
// 1. Skip sample data generation
// 2. Require user to provide separate data source
// 3. Create mock/synthetic data based on schema
```

### Comparison Table

| Feature | PBIX Input | PBIP Input | BIM Input |
|---------|-----------|-----------|-----------|
| **TMDL Export** | ✅ Via TOM | ✅ Already exists | ✅ Via TMDL Serializer |
| **Sample Data** | ✅ Via DAX queries | ❌ Not available | ⚠️ Only if connected |
| **Speed** | 8 seconds | 2 seconds | 5 seconds |
| **Cross-platform** | ❌ Windows only | ✅ Any OS | ⚠️ Limited |
| **Dependencies** | Power BI Desktop | None | SSAS libs |
| **Use Case** | Development | CI/CD, Git | Server models |
| **Most Common** | ✅✅✅ | ⚠️ Growing | ⚠️ Enterprise |

### Recommendations

#### For Development Workflow:
```
User → Works in Power BI Desktop → Saves as .pbix
       ↓
MCP Tool → export_model_analysis(pbix) → Complete analysis with sample data
       ↓
Claude → Analyzes using hybrid structure
```

#### For CI/CD / Team Workflow:
```
Team → Works in Power BI Desktop → Saves as .pbip (File → Save As → Power BI Project)
       ↓
Git → Commits PBIP to repository
       ↓
Pipeline → export_model_analysis(pbip) → Fast analysis (no sample data)
       ↓
Automated checks → Performance validation, security audit
```

#### For Server Models:
```
SSAS/Fabric → Model deployed
       ↓
MCP Tool → export_model_analysis(connection_string) → Analysis from live server
       ↓
Optional → Generate sample data from server
```

### Implementation Priority

**Week 1-2: PBIX Support** (MVP)
- Most users need this
- Complete functionality
- Proven approach

**Week 3: PBIP Fast Path**
- Dramatic speed improvement
- Enables automation
- Simple implementation (just copy TMDL)

**Week 4: Enhanced Features**
- Connection string support (live models)
- Sample data from external sources for PBIP
- Hybrid workflows (PBIP structure + PBIX data)

### Sample Data Workaround for PBIP

**If user has PBIP but wants sample data:**

```typescript
export_model_analysis({
  model_path: "FamilyOffice.pbip",     // PBIP for structure
  sample_data_source: "FamilyOffice.pbix"  // Optional PBIX for data
})
```

**Or connect to data source directly:**
```typescript
export_model_analysis({
  model_path: "FamilyOffice.pbip",
  sample_data_connection: {
    provider: "SQL Server",
    connection_string: "Server=...",
    tables_to_sample: ["FactPortfolioValues", "DimDate"]
  }
})
```

### Best Practice Recommendation

**For your MCP server:**

1. **Start with PBIX support** - covers 90% of use cases
2. **Add PBIP fast path** - enables advanced scenarios
3. **Document the tradeoff** - PBIX = complete, PBIP = fast
4. **Provide hybrid option** - PBIP structure + external data for samples

**Example tool signature:**
```typescript
{
  name: "export_model_analysis",
  inputSchema: {
    properties: {
      model_path: {
        type: "string",
        description: "Path to .pbix, .pbip, or connection string"
      },
      format: {
        type: "string",
        enum: ["auto", "pbix", "pbip", "connection"],
        default: "auto",
        description: "Model format (auto-detected if not specified)"
      },
      include_sample_data: {
        type: "boolean",
        default: true,
        description: "Export sample data (only works with .pbix or connection)"
      },
      sample_data_source: {
        type: "string",
        description: "Optional: .pbix file for sample data when using .pbip"
      }
    }
  }
}
```

---

```
powerbi_analysis/
├── model.bim/                          # TMDL Export (Layer 1)
│   ├── model.tmdl                      # Model-level settings
│   ├── tables/
│   │   ├── DimDate.tmdl
│   │   ├── DimAccount.tmdl
│   │   ├── FactPortfolioValues.tmdl
│   │   └── [66 more tables...]
│   ├── relationships/
│   │   └── relationships.tmdl
│   ├── expressions/
│   │   ├── _measures.tmdl              # All measures in one file
│   │   └── _columns.tmdl               # Calculated columns
│   ├── roles/
│   │   ├── AdvisorView.tmdl
│   │   └── ClientView.tmdl
│   └── perspectives/
│       └── ClientDashboard.tmdl
│
├── analysis/                           # JSON Analysis (Layer 2)
│   ├── metadata.json                   # Model summary & statistics
│   ├── dependencies.json               # Object dependency graph
│   └── catalog.json                    # Quick lookup index
│
└── sample_data/                        # Sample Data (Layer 3)
    ├── DimDate.parquet                 # First 1000 rows
    ├── DimAccount.parquet
    ├── FactPortfolioValues.parquet
    └── [66 more files...]
```

---

## Layer 1: TMDL Structure

### File Organization
- **One file per table** in `tables/` directory
- **Single relationships file** (Power BI limitation)
- **Single measures file** (easier to search all measures)
- **One file per role** for security

### What TMDL Provides
```tmdl
table FactPortfolioValues
    lineageTag: 8a2b9c4d-1234-5678-90ab-cdef12345678
    
    partition FactPortfolioValues = m
        mode: import
        source = 
            let
                Source = Sql.Database("server", "db"),
                Table = Source{[Schema="dbo",Item="PortfolioValues"]}[Data]
            in
                Table
    
    column DateKey
        dataType: dateTime
        isKey
        sourceColumn: DateKey
        formatString: Short Date
        lineageTag: def12345-6789-0abc-def1-234567890abc
    
    column MarketValue
        dataType: decimal
        sourceColumn: MarketValue
        formatString: $#,0.00
        summarizeBy: sum
        lineageTag: abc12345-6789-0abc-def1-234567890abc
    
    measure 'Total Market Value' = SUM(FactPortfolioValues[MarketValue])
        formatString: $#,0
        lineageTag: xyz12345-6789-0abc-def1-234567890abc
```

### TMDL Advantages
- ✅ **Selective reading:** Load only `tables/DimDate.tmdl` when asked about that table
- ✅ **Native format:** Can be reimported to Power BI without conversion
- ✅ **Complete metadata:** Lineage tags, annotations, extended properties
- ✅ **Version control friendly:** Git diffs show actual changes
- ✅ **Human readable:** Clear syntax, proper DAX formatting

---

## Layer 2: JSON Analysis Files

### 2.1 metadata.json
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
  "model_size_estimate": {
    "total_rows": 15234567,
    "estimated_memory_mb": 2847,
    "largest_tables": [
      {"name": "FactPortfolioValues", "rows": 1245678, "mb": 456},
      {"name": "FactTransactions", "rows": 8934567, "mb": 1234}
    ]
  },
  "row_counts": {
    "by_table": [
      {"table": "FactPortfolioValues", "row_count": 1245678, "last_refresh": "2025-11-11T08:30:00Z"},
      {"table": "FactTransactions", "row_count": 8934567, "last_refresh": "2025-11-11T08:30:00Z"},
      {"table": "DimDate", "row_count": 3653, "last_refresh": "2025-11-11T08:30:00Z"},
      {"table": "DimAccount", "row_count": 456, "last_refresh": "2025-11-11T08:30:00Z"}
    ],
    "total_rows": 15234567,
    "largest_fact_tables": [
      {"name": "FactTransactions", "rows": 8934567},
      {"name": "FactPortfolioValues", "rows": 1245678}
    ]
  }
}
```

**Usage:** First file Claude reads to understand model scope

---

### 2.2 catalog.json
**Purpose:** Fast lookup index for finding objects

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
          "name": "Year",
          "data_type": "Int64",
          "is_key": false,
          "is_hidden": false,
          "used_in_relationships": false,
          "used_in_measures": true,
          "used_in_visuals": true,
          "measure_references": 12,
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
          "is_unused": true
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
      "has_sample_data": true,
      "sample_data_path": "sample_data/FactPortfolioValues.parquet",
      "columns": [
        {
          "name": "DateKey",
          "data_type": "DateTime",
          "is_key": true,
          "is_hidden": true,
          "used_in_relationships": true,
          "used_in_measures": false,
          "used_in_visuals": false,
          "measure_references": 0,
          "is_unused": false
        },
        {
          "name": "MarketValue",
          "data_type": "Decimal",
          "is_key": false,
          "is_hidden": false,
          "used_in_relationships": false,
          "used_in_measures": true,
          "used_in_visuals": true,
          "measure_references": 234,
          "is_unused": false
        },
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
          "cardinality_ratio": 1.0
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

**Usage:** Enables queries like "find all measures in folder X" or "which table is largest"

---

### 2.3 dependencies.json
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
    },
    "Strategic Allocation %": {
      "direct_dependencies": {
        "measures": [],
        "tables": ["DimAssetClass", "FactStrategicAllocations"],
        "columns": [
          "DimAssetClass[AssetClass]",
          "FactStrategicAllocations[AllocationPercent]"
        ]
      },
      "all_dependencies": {
        "measures": [],
        "tables": ["DimAssetClass", "FactStrategicAllocations"],
        "columns": [
          "DimAssetClass[AssetClass]",
          "FactStrategicAllocations[AllocationPercent]"
        ]
      },
      "dependent_measures": [
        "Actual vs Strategic Allocation",
        "Allocation Variance"
      ],
      "dependency_depth": 1,
      "uses_context_transition": true,
      "uses_allselected": true
    }
  },
  "tables": {
    "DimDate": {
      "dependent_relationships": 12,
      "dependent_measures": 89,
      "dependent_rls_roles": 0,
      "is_date_table": true
    },
    "FactPortfolioValues": {
      "dependent_relationships": 5,
      "dependent_measures": 234,
      "dependent_rls_roles": 2,
      "is_date_table": false
    }
  },
  "circular_dependencies": [],
  "orphaned_measures": [],
  "unused_tables": []
}
```

**Usage:** Answer "what breaks if I change X?" or "what uses this measure?"

---

## Layer 3: Sample Data

### File Format: Parquet
**Why Parquet:**
- ✅ **Columnar format:** Fast to read specific columns
- ✅ **Compressed:** 5-10x smaller than CSV
- ✅ **Type-safe:** Preserves data types (dates, decimals, integers)
- ✅ **Fast:** Claude can read via pandas/polars
- ✅ **Partial reading:** Can read subset of columns/rows

### Sample Data Rules
```json
{
  "sampling_strategy": {
    "max_rows_per_table": 1000,
    "method": "top_n",
    "include_nulls": true,
    "preserve_relationships": true
  },
  "file_naming": "{TableName}.parquet",
  "compression": "snappy",
  "schema_preservation": true
}
```

### Example Usage
```python
# Claude can efficiently read sample data when needed
import polars as pl

# Read only needed columns
df = pl.read_parquet(
    "sample_data/FactPortfolioValues.parquet",
    columns=["DateKey", "MarketValue"]
)

# Quick stats for validation
print(df.describe())
```

---

## Access Patterns & Performance

### Pattern 1: Quick Model Assessment
**Query:** "Give me a summary of this model"

**Steps:**
1. Read `analysis/metadata.json` (10ms)
2. Read `analysis/catalog.json` (15ms)
3. Summarize statistics

**Total time:** ~25ms

---

### Pattern 2: Specific Object Query
**Query:** "Show me the DimDate table definition"

**Steps:**
1. Read `analysis/catalog.json` to find path (5ms)
2. Read `model.bim/tables/DimDate.tmdl` (50ms)
3. Optional: Read `sample_data/DimDate.parquet` if user asks for examples (100ms)

**Total time:** ~55ms (155ms with sample data)

---

### Pattern 3: Measure Analysis
**Query:** "Why is 'Rolling 12M Average' slow?"

**Steps:**
1. Read `analysis/catalog.json` to find measure location (5ms)
2. Read `model.bim/expressions/_measures.tmdl` lines 234-262 (30ms)
3. Parse DAX to analyze complexity (50ms)
4. Read `analysis/dependencies.json` to check impact (15ms)
5. Generate optimization recommendations (25ms)

**Total time:** ~125ms with complete analysis generated on-the-fly

---

### Pattern 4: Cross-Model Performance Analysis
**Query:** "Find all performance issues and recommend fixes"

**Steps:**
1. Read `analysis/catalog.json` for all measures and tables (15ms)
2. Read `analysis/metadata.json` for model statistics (10ms)
3. Analyze each measure for complexity patterns (200ms for 699 measures)
4. Check relationships for anti-patterns (30ms)
5. Identify high cardinality columns from metadata (20ms)
6. Generate prioritized recommendations (50ms)

**Total time:** ~325ms for comprehensive performance analysis

---

### Pattern 5: Impact Analysis
**Query:** "What breaks if I change the DimDate table?"

**Steps:**
1. Read `analysis/dependencies.json` (20ms)
2. Filter to DimDate dependencies
3. Read `analysis/catalog.json` to get affected object details (10ms)

**Total time:** ~30ms

---

### Pattern 6: Sample Data Validation
**Query:** "Show me example data from FactPortfolioValues"

**Steps:**
1. Read `analysis/catalog.json` to find sample data path (5ms)
2. Read `sample_data/FactPortfolioValues.parquet` (100ms)
3. Format and display

**Total time:** ~105ms

---

## MCP Server Implementation

### Tool Design

#### 1. export_model_analysis
**Purpose:** Generate complete hybrid analysis package

```typescript
{
  name: "export_model_analysis",
  description: "Export Power BI model in hybrid format optimized for Claude analysis",
  inputSchema: {
    type: "object",
    properties: {
      model_path: {
        type: "string",
        description: "Path to .pbix or .bim file"
      },
      output_directory: {
        type: "string",
        description: "Where to create analysis package"
      },
      include_sample_data: {
        type: "boolean",
        default: true,
        description: "Generate sample data parquet files"
      },
      sample_rows: {
        type: "number",
        default: 1000,
        description: "Number of rows per table sample"
      }
    },
    required: ["model_path", "output_directory"]
  }
}
```

**Output:**
```json
{
  "success": true,
  "output_path": "/path/to/powerbi_analysis/",
  "structure": {
    "tmdl_path": "model.bim/",
    "analysis_path": "analysis/",
    "sample_data_path": "sample_data/",
    "file_count": {
      "tmdl_files": 72,
      "analysis_files": 3,
      "sample_data_files": 66
    }
  },
  "generation_time_seconds": 8.2,
  "package_size_mb": 145,
  "note": "Performance analysis and recommendations generated on-demand"
}
```

---

#### 2. read_model_metadata
**Purpose:** Quick model statistics without reading TMDL

```typescript
{
  name: "read_model_metadata",
  description: "Get high-level model statistics and summary",
  inputSchema: {
    type: "object",
    properties: {
      analysis_path: {
        type: "string",
        description: "Path to analysis directory"
      }
    },
    required: ["analysis_path"]
  }
}
```

**Output:** Contents of `metadata.json`

---

#### 3. find_objects
**Purpose:** Search for tables, measures, columns using catalog

```typescript
{
  name: "find_objects",
  description: "Search for objects in model using fast catalog lookup",
  inputSchema: {
    type: "object",
    properties: {
      analysis_path: {
        type: "string",
        description: "Path to analysis directory"
      },
      object_type: {
        type: "string",
        enum: ["table", "measure", "column", "relationship", "role"],
        description: "Type of object to search for"
      },
      filter: {
        type: "object",
        properties: {
          name_contains: { type: "string" },
          display_folder: { type: "string" },
          complexity_min: { type: "number" },
          complexity_max: { type: "number" }
        }
      }
    },
    required: ["analysis_path", "object_type"]
  }
}
```

**Output:**
```json
{
  "matches": [
    {
      "name": "Total Market Value YTD",
      "table": "FactPortfolioValues",
      "display_folder": "Time Intelligence/YTD",
      "tmdl_path": "model.bim/expressions/_measures.tmdl",
      "line_number": 52,
      "complexity_score": 3
    }
  ],
  "total_matches": 1
}
```

---

#### 4. get_object_definition
**Purpose:** Read TMDL definition for specific object

```typescript
{
  name: "get_object_definition",
  description: "Get TMDL definition for a specific object",
  inputSchema: {
    type: "object",
    properties: {
      tmdl_path: {
        type: "string",
        description: "Path to TMDL file from catalog"
      },
      object_name: {
        type: "string",
        description: "Name of object (for measures file)"
      },
      include_dependencies: {
        type: "boolean",
        default: true,
        description: "Include dependency information"
      }
    },
    required: ["tmdl_path"]
  }
}
```

**Output:**
```json
{
  "object_name": "Total Market Value YTD",
  "tmdl_definition": "measure 'Total Market Value YTD' = \n    CALCULATE (\n        [Total Market Value],\n        DATESYTD ( DimDate[Date] )\n    )\n    formatString: $#,0\n    displayFolder: Time Intelligence\\YTD",
  "dependencies": {
    "measures": ["Total Market Value"],
    "tables": ["DimDate"],
    "columns": ["DimDate[Date]"]
  },
  "dependent_measures": ["Total Market Value YTD vs PY"],
  "file_path": "model.bim/expressions/_measures.tmdl",
  "line_number": 52
}
```

---

#### 5. analyze_performance
**Purpose:** Generate performance analysis on-demand with batching support

```typescript
{
  name: "analyze_performance",
  description: "Analyze model for performance issues and optimization opportunities. Supports batching for large models.",
  inputSchema: {
    type: "object",
    properties: {
      analysis_path: {
        type: "string",
        description: "Path to analysis directory"
      },
      focus_areas: {
        type: "array",
        items: {
          type: "string",
          enum: ["cardinality", "dax_complexity", "relationships", "aggregations", "unused_columns", "row_counts", "all"]
        },
        default: ["all"],
        description: "Which areas to analyze"
      },
      min_priority: {
        type: "string",
        enum: ["critical", "high", "medium", "low"],
        default: "medium",
        description: "Minimum priority level to report"
      },
      batch_config: {
        type: "object",
        description: "Batching configuration for large models",
        properties: {
          enabled: {
            type: "boolean",
            default: true,
            description: "Enable automatic batching for large models"
          },
          batch_size: {
            type: "number",
            default: 50,
            description: "Number of measures/tables to analyze per batch"
          },
          batch_number: {
            type: "number",
            description: "Specific batch to analyze (1-indexed). If not provided, analyzes all batches."
          }
        }
      },
      use_cache: {
        type: "boolean",
        default: true,
        description: "Use cached results if available (5 minute TTL)"
      }
    },
    required: ["analysis_path"]
  }
}
```

**Output (Single Batch):**
```json
{
  "analysis_timestamp": "2025-11-11T11:45:00Z",
  "analysis_duration_ms": 234,
  "batch_info": {
    "batch_number": 1,
    "total_batches": 14,
    "items_in_batch": 50,
    "total_items": 699,
    "next_batch": 2
  },
  "high_cardinality_columns": [
    {
      "table": "FactPortfolioValues",
      "column": "TransactionID",
      "distinct_count": 1245678,
      "cardinality_ratio": 1.0,
      "used_in_relationships": false,
      "estimated_memory_mb": 45,
      "recommendation": "Remove - not used in relationships",
      "priority": "high",
      "tmdl_location": "model.bim/tables/FactPortfolioValues.tmdl"
    }
  ],
  "complex_measures": [
    {
      "name": "Rolling 12M Average",
      "table": "Time Intelligence",
      "complexity_score": 12,
      "issues": [
        "Nested CALCULATE (5 levels)",
        "Uses DATESINPERIOD (expensive)",
        "Iterator over filtered table"
      ],
      "recommendation": "Rewrite using calculation group",
      "priority": "high",
      "tmdl_location": "model.bim/expressions/_measures.tmdl:234"
    }
  ],
  "unused_columns": [
    {
      "table": "FactPortfolioValues",
      "column": "TransactionID",
      "data_type": "String",
      "cardinality": 1245678,
      "estimated_memory_mb": 45,
      "reason": "Not used in relationships, measures, or visuals",
      "recommendation": "Remove to save memory and improve refresh performance",
      "priority": "high",
      "tmdl_location": "model.bim/tables/FactPortfolioValues.tmdl"
    },
    {
      "table": "DimDate",
      "column": "FiscalQuarterOrder",
      "data_type": "Int64",
      "cardinality": 12,
      "estimated_memory_mb": 0.01,
      "reason": "Hidden column not referenced anywhere",
      "recommendation": "Remove if not needed for future calculations",
      "priority": "low",
      "tmdl_location": "model.bim/tables/DimDate.tmdl"
    },
    {
      "table": "DimAccount",
      "column": "LegacyAccountCode",
      "data_type": "String",
      "cardinality": 456,
      "estimated_memory_mb": 0.5,
      "reason": "Not used in relationships, measures, or visuals",
      "recommendation": "Verify with business users before removing",
      "priority": "medium",
      "tmdl_location": "model.bim/tables/DimAccount.tmdl"
    }
  ],
  "row_count_analysis": {
    "large_fact_tables": [
      {
        "table": "FactTransactions",
        "row_count": 8934567,
        "estimated_memory_mb": 1234,
        "grain": "One row per transaction",
        "recommendation": "Consider aggregation table for common queries",
        "potential_aggregation_rows": 234567,
        "potential_speedup": "15-20x",
        "priority": "high"
      },
      {
        "table": "FactPortfolioValues",
        "row_count": 1245678,
        "estimated_memory_mb": 456,
        "grain": "One row per account-security-date",
        "recommendation": "Monitor growth, may need aggregation at 2M+ rows",
        "priority": "medium"
      }
    ],
    "empty_tables": [],
    "low_row_count_facts": [
      {
        "table": "FactManualAdjustments",
        "row_count": 23,
        "recommendation": "Consider if this needs to be a fact table or could be a dimension",
        "priority": "low"
      }
    ]
  },
  "batch_summary": {
    "measures_analyzed": 50,
    "complex_measures_found": 3,
    "unused_columns_found": 3,
    "high_priority_issues": 4,
    "medium_priority_issues": 2
  }
}
```

**Output (Complete Analysis - All Batches):**
```json
{
  "analysis_timestamp": "2025-11-11T11:45:00Z",
  "analysis_duration_ms": 3420,
  "total_batches_processed": 14,
  "total_items_analyzed": 699,
  "high_cardinality_columns": [...],
  "complex_measures": [...],
  "unused_columns": [
    {
      "table": "FactPortfolioValues",
      "column": "TransactionID",
      "cardinality": 1245678,
      "estimated_memory_mb": 45,
      "priority": "high"
    },
    {
      "table": "DimAccount",
      "column": "LegacyAccountCode",
      "cardinality": 456,
      "estimated_memory_mb": 0.5,
      "priority": "medium"
    }
  ],
  "row_count_analysis": {
    "large_fact_tables": [
      {
        "table": "FactTransactions",
        "row_count": 8934567,
        "potential_aggregation_rows": 234567,
        "potential_speedup": "15-20x",
        "priority": "high"
      }
    ],
    "total_rows": 15234567,
    "tables_analyzed": 66
  },
  "relationship_issues": [],
  "aggregation_opportunities": [...],
  "summary": {
    "critical_issues": 0,
    "high_priority": 25,
    "medium_priority": 47,
    "low_priority": 14,
    "unused_columns_found": 12,
    "large_tables_needing_aggregation": 2,
    "estimated_memory_savings_mb": 123,
    "estimated_total_improvement": "30-50% average query time",
    "token_usage": {
      "input_tokens": 12450,
      "output_tokens": 8920,
      "total_tokens": 21370
    }
  },
  "cached": false
}
```

**Batching Behavior:**
- **Small models (<100 measures):** Processes in single call, no batching
- **Medium models (100-500 measures):** Processes in 2-10 batches automatically
- **Large models (500+ measures):** Returns batch info, user can request specific batches or all
- **Auto-aggregation:** When processing all batches, server aggregates results internally
- **Token management:** Each batch stays under 8K output tokens

**Note:** This tool dynamically analyzes the model by reading TMDL files, catalog, dependencies, and metadata to generate insights in real-time. Results are cached for 5 minutes.

---

#### 6. generate_recommendations
**Purpose:** Generate actionable recommendations based on analysis with token management

```typescript
{
  name: "generate_recommendations",
  description: "Generate prioritized recommendations with implementation steps. Automatically manages token limits for large result sets.",
  inputSchema: {
    type: "object",
    properties: {
      analysis_path: {
        type: "string",
        description: "Path to analysis directory"
      },
      based_on_analysis: {
        type: "object",
        description: "Optional: Results from analyze_performance to generate recommendations from",
        properties: {
          high_cardinality_columns: { type: "array" },
          complex_measures: { type: "array" },
          relationship_issues: { type: "array" },
          aggregation_opportunities: { type: "array" }
        }
      },
      priority: {
        type: "string",
        enum: ["all", "critical", "high", "medium", "low"],
        default: "high",
        description: "Minimum priority level to include (default: high and above)"
      },
      category: {
        type: "string",
        enum: ["all", "performance", "architecture", "dax", "maintenance"],
        default: "all"
      },
      include_implementation_steps: {
        type: "boolean",
        default: true,
        description: "Include detailed implementation steps"
      },
      max_recommendations: {
        type: "number",
        default: 20,
        description: "Maximum number of recommendations to return (prevents token overflow)"
      },
      use_cache: {
        type: "boolean",
        default: true,
        description: "Use cached recommendations if available (5 minute TTL)"
      }
    },
    required: ["analysis_path"]
  }
}
```

**Output:**
```json
{
  "generation_timestamp": "2025-11-11T11:46:00Z",
  "generation_duration_ms": 156,
  "recommendations": {
    "critical": [],
    "high": [
      {
        "id": "PERF-001",
        "category": "Performance",
        "title": "Remove unused high-cardinality column",
        "description": "TransactionID has 1.2M unique values but is unused",
        "impact": {
          "memory_savings_mb": 45,
          "performance_improvement": "5-10%"
        },
        "affected_objects": {
          "tables": ["FactPortfolioValues"],
          "columns": ["TransactionID"]
        },
        "implementation": {
          "steps": [
            "Verify column not used in bookmarks",
            "Delete column from Power Query",
            "Refresh model",
            "Verify memory reduction"
          ],
          "estimated_time_minutes": 15,
          "rollback_plan": "Re-add from source if needed"
        },
        "tmdl_location": "model.bim/tables/FactPortfolioValues.tmdl",
        "priority": "high"
      },
      {
        "id": "DAX-001",
        "category": "DAX Optimization",
        "title": "Optimize 'Rolling 12M Average' measure",
        "description": "Uses expensive DATESINPERIOD and nested CALCULATE",
        "impact": {
          "performance_improvement": "50-70%",
          "affected_reports": ["Executive Dashboard"]
        },
        "affected_objects": {
          "measures": ["Rolling 12M Average"],
          "dependent_measures": ["Rolling 12M vs Target"]
        },
        "implementation": {
          "current_dax": "See model.bim/expressions/_measures.tmdl:234",
          "proposed_pattern": "Use calculation group with PARALLELPERIOD",
          "steps": [
            "Create calculation group for rolling periods",
            "Replace with simpler base measure",
            "Test against existing visuals",
            "Update dependent measures"
          ],
          "estimated_time_minutes": 45
        },
        "tmdl_location": "model.bim/expressions/_measures.tmdl:234",
        "priority": "high"
      }
    ],
    "medium": [
      {
        "id": "ARCH-001",
        "category": "Architecture",
        "title": "Create aggregation table for dashboards",
        "description": "Dashboard queries at Account+Date grain, model has Security detail",
        "impact": {
          "performance_improvement": "10-12x for dashboards",
          "memory_increase_mb": 15
        },
        "implementation": {
          "steps": [
            "Create aggregation at Account+Date grain",
            "Add aggregated columns (SUM)",
            "Configure automatic aggregation",
            "Test with DAX Studio",
            "Document in model"
          ],
          "estimated_time_minutes": 120
        },
        "priority": "medium"
      }
    ],
    "low": []
  },
  "summary": {
    "total_recommendations": 3,
    "recommendations_returned": 3,
    "truncated": false,
    "critical": 0,
    "high": 2,
    "medium": 1,
    "low": 0,
    "estimated_total_time_hours": 3,
    "estimated_memory_savings_mb": 45,
    "estimated_performance_improvement": "30-50% average",
    "token_usage": {
      "input_tokens": 3420,
      "output_tokens": 4850,
      "total_tokens": 8270
    }
  },
  "cached": false,
  "note": "Showing top recommendations. Use priority/category filters to see more."
}
```

**Token Management:**
- Automatically limits output to prevent overflow
- If >20 recommendations, returns top priority items
- Sets `truncated: true` when results are limited
- Provides filtering guidance in `note` field
- Each recommendation ~200-400 tokens
- Max output: ~8,000 tokens

**Pagination for Large Result Sets:**
```typescript
// Get critical and high priority first
generate_recommendations({
  priority: "high",
  max_recommendations: 10
})

// Then get medium priority
generate_recommendations({
  priority: "medium", 
  max_recommendations: 10
})

// Or focus on specific category
generate_recommendations({
  category: "dax",
  priority: "all",
  max_recommendations: 15
})
```

**Note:** This tool can work standalone (analyzing from scratch) or accept results from `analyze_performance` to generate targeted recommendations. Results are cached for 5 minutes.

---

#### 7. analyze_dependencies
**Purpose:** Get dependency graph for object

```typescript
{
  name: "analyze_dependencies",
  description: "Get dependency information for objects",
  inputSchema: {
    type: "object",
    properties: {
      analysis_path: {
        type: "string",
        description: "Path to analysis directory"
      },
      object_name: {
        type: "string",
        description: "Name of measure or table"
      },
      object_type: {
        type: "string",
        enum: ["measure", "table"],
        description: "Type of object"
      },
      direction: {
        type: "string",
        enum: ["dependencies", "dependents", "both"],
        default: "both",
        description: "Which direction to analyze"
      }
    },
    required: ["analysis_path", "object_name", "object_type"]
  }
}
```

**Output:** Filtered contents from `dependencies.json`

---

#### 8. get_sample_data
**Purpose:** Read sample data for table

```typescript
{
  name: "get_sample_data",
  description: "Get sample data preview for a table",
  inputSchema: {
    type: "object",
    properties: {
      sample_data_path: {
        type: "string",
        description: "Path to sample data parquet file from catalog"
      },
      columns: {
        type: "array",
        items: { type: "string" },
        description: "Specific columns to read (optional)"
      },
      max_rows: {
        type: "number",
        default: 100,
        description: "Maximum rows to return"
      }
    },
    required: ["sample_data_path"]
  }
}
```

**Output:**
```json
{
  "table_name": "FactPortfolioValues",
  "rows_returned": 100,
  "total_rows_in_sample": 1000,
  "columns": ["DateKey", "AccountKey", "MarketValue"],
  "data": [
    {"DateKey": "2024-01-01", "AccountKey": 1001, "MarketValue": 1250000.00},
    {"DateKey": "2024-01-01", "AccountKey": 1002, "MarketValue": 850000.00}
  ],
  "statistics": {
    "MarketValue": {
      "min": 10000.00,
      "max": 5000000.00,
      "mean": 1234567.89,
      "null_count": 0
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Core Export (Week 1)
**Goal:** Generate basic hybrid structure with TMDL + metadata

**Tasks:**
1. ✅ Design folder structure
2. ✅ Implement TMDL export via Tabular Object Model
3. ✅ Generate `metadata.json` (model statistics)
4. ✅ Generate `catalog.json` (object index)
5. ✅ Generate `dependencies.json` (dependency graph)
6. ✅ Add sample data export (parquet)

**Deliverables:**
- `export_model_analysis` tool working
- Three-layer structure generated (TMDL + Analysis + Sample Data)
- Can read TMDL files manually

**Testing:**
- Export 66-table model
- Verify TMDL can be reimported
- Check catalog and dependencies accuracy

---

### Phase 2: MCP Server Read Tools (Week 2)
**Goal:** Implement read tools for Claude to consume the exported data

**Tasks:**
1. ✅ Implement `read_model_metadata`
2. ✅ Implement `find_objects`
3. ✅ Implement `get_object_definition`
4. ✅ Implement `analyze_dependencies`
5. ✅ Implement `get_sample_data`
6. ✅ Add row count extraction via DMV queries
7. ✅ Add column usage tracking (relationships, measures, visuals, RLS)
8. ✅ Add cardinality calculation for all columns

**Deliverables:**
- 5 working read tools
- Row count data in metadata.json
- Column usage tracking in catalog.json
- Tool integration tests
- Performance benchmarks

**Testing:**
- Test all tools on exported model
- Verify row counts match actual data
- Validate column usage detection (spot-check 20 columns)
- Measure response times (<500ms target)
- Test unused column detection accuracy

---

### Phase 3: Dependency Analysis Enhancement (Week 3)
**Goal:** Enhance dependency calculation and impact analysis

**Tasks:**
1. ✅ Parse DAX for deep dependencies
2. ✅ Calculate transitive dependencies
3. ✅ Identify circular references
4. ✅ Find orphaned measures
5. ✅ Detect unused tables

**Deliverables:**
- Enhanced `dependencies.json` generation
- Complete dependency graph with depth
- Impact analysis capabilities

**Testing:**
- Validate against known dependencies
- Test circular dependency detection
- Verify transitive closure accuracy

---

### Phase 4: Performance Analysis Tools (Week 4)
**Goal:** Implement on-demand performance analysis

**Tasks:**
1. ✅ Implement `analyze_performance` tool
2. ✅ Build cardinality analysis
3. ✅ Build DAX complexity scoring
4. ✅ Detect relationship anti-patterns
5. ✅ Identify aggregation opportunities
6. ✅ **Detect unused columns with memory impact**
7. ✅ **Analyze row counts for optimization opportunities**
8. ✅ Implement `generate_recommendations` tool

**Deliverables:**
- `analyze_performance` tool (generates insights on-demand)
- `generate_recommendations` tool (creates action plans)
- Performance scoring algorithms
- Unused column detection with priority scoring
- Row count analysis for aggregation recommendations
- Recommendation generation engine

**Testing:**
- Test on models with known issues
- Validate complexity scoring
- Test unused column detection (ensure no false positives)
- Verify row count-based aggregation recommendations
- Compare recommendations with DAX Studio analysis
- Measure tool execution time (<500ms target)

**Success Criteria:**
- Detects 100% of truly unused columns
- 0% false positives (columns flagged as unused but actually used)
- Correctly identifies tables needing aggregation (>1M rows)
- Provides accurate memory savings estimates

---

### Phase 5: Optimization & Documentation (Week 5)
**Goal:** Performance tuning and comprehensive docs

**Tasks:**
1. ✅ Optimize file reading performance
2. ✅ Add caching for parsed DAX
3. ✅ Implement parallel processing for analysis
4. ✅ Write comprehensive README
5. ✅ Create example workflows
6. ✅ Add error handling

**Deliverables:**
- Performance benchmarks
- Complete documentation
- Example queries and workflows
- Error handling guide

**Testing:**
- Load test with large models
- Test error scenarios
- Validate documentation accuracy
- Measure end-to-end performance

---

## Performance Targets

### Export Performance
| Model Size | Target Time | Acceptable |
|-----------|-------------|------------|
| Small (10 tables, 100 measures) | 5 seconds | 10 seconds |
| Medium (30 tables, 300 measures) | 15 seconds | 30 seconds |
| Large (66 tables, 699 measures) | 30 seconds | 60 seconds |
| Very Large (100+ tables, 1000+ measures) | 60 seconds | 120 seconds |

### Read Performance
| Operation | Target | Acceptable |
|-----------|--------|------------|
| Read metadata.json | 10ms | 50ms |
| Read catalog.json | 15ms | 50ms |
| Find object in catalog | 20ms | 100ms |
| Read single TMDL file | 50ms | 200ms |
| Read dependencies.json | 30ms | 100ms |
| Read sample data (1000 rows) | 100ms | 500ms |
| Complete impact analysis | 100ms | 500ms |
| **Analyze performance (on-demand)** | **250ms** | **500ms** |
| **Generate recommendations (on-demand)** | **200ms** | **500ms** |

### Memory Usage
| Model Size | Max Memory |
|-----------|------------|
| Small | 100MB |
| Medium | 250MB |
| Large | 500MB |
| Very Large | 1GB |

---

## File Size Estimates

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

**Note:** Performance insights and recommendations are generated on-demand by MCP tools (not stored as files)

### Sample Data
```
Parquet compression: 5-10x vs CSV
1000 rows × 10 columns × 66 tables = ~5-15MB
Total with compression: ~2-5MB
```

### Complete Package
```
TMDL: 2MB
Analysis: 0.26MB
Sample Data: 5MB
Total: ~7.3MB
```

For 66-table, 699-measure model: **~7.3MB** (vs 50-100MB for raw exports)

**Performance analysis adds:** ~200-500ms processing time when requested (not stored as files)

---

## Error Handling Strategy

### Export Errors
```python
class ExportError(Exception):
    """Base exception for export issues"""
    pass

class TmdlExportError(ExportError):
    """TMDL export failed"""
    # Fallback: Export only JSON analysis
    
class AnalysisGenerationError(ExportError):
    """Analysis generation failed"""
    # Fallback: Export TMDL only, skip analysis
    
class SampleDataError(ExportError):
    """Sample data export failed"""
    # Fallback: Export without sample data
```

### Read Errors
```python
class ReadError(Exception):
    """Base exception for read issues"""
    pass

class FileNotFoundError(ReadError):
    """Expected file missing"""
    # Return clear error with expected path
    
class InvalidFormatError(ReadError):
    """File format invalid"""
    # Return error with validation details
```

### MCP Server Errors
```typescript
// All tools return structured errors
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "Analysis file not found at path",
    "details": {
      "expected_path": "analysis/metadata.json",
      "suggestion": "Run export_model_analysis first"
    }
  }
}
```

---

## Testing Strategy

### Unit Tests
- ✅ TMDL export accuracy
- ✅ JSON schema validation
- ✅ Dependency calculation correctness
- ✅ Performance metric accuracy
- ✅ Parquet file integrity

### Integration Tests
- ✅ Complete export → read cycle
- ✅ Tool chain execution
- ✅ Cross-file reference validation
- ✅ Sample data consistency

### Performance Tests
- ✅ Export time benchmarks
- ✅ Read operation timing
- ✅ Memory usage profiling
- ✅ Large model stress testing

### Validation Tests
- ✅ Compare with known good exports
- ✅ Verify against DAX Studio metrics
- ✅ Check TMDL reimport success
- ✅ Validate recommendations

---

## Success Criteria

### Functional Requirements
- ✅ Generate complete hybrid structure in <60 seconds for large models
- ✅ All read operations complete in <500ms
- ✅ TMDL files can be reimported to Power BI without errors
- ✅ Dependency graph 100% accurate
- ✅ Performance insights match DAX Studio analysis
- ✅ Sample data preserves types and relationships

### Non-Functional Requirements
- ✅ Total package size <10MB for typical models
- ✅ Zero data loss from original model
- ✅ Idempotent exports (same input = same output)
- ✅ Clear error messages with remediation steps
- ✅ Comprehensive documentation

### User Experience
- ✅ Claude can answer queries in 1-2 tool calls
- ✅ Single export supports multiple analysis sessions
- ✅ Clear file organization (obvious where to look)
- ✅ Actionable recommendations with implementation steps

---

## Risks & Mitigation

### Risk 1: TMDL Export Limitations
**Risk:** Some Power BI features may not export cleanly to TMDL
**Probability:** Medium
**Impact:** High
**Mitigation:** 
- Test with diverse model types
- Document known limitations
- Provide fallback to .bim format
- Validate reimport before declaring success

### Risk 2: Analysis Generation Performance
**Risk:** Dependency analysis slow on very large models (1000+ measures)
**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Implement caching for parsed DAX
- Use parallel processing for independent tables
- Add progress reporting for long operations
- Set timeout limits with graceful degradation

### Risk 3: Sample Data Privacy
**Risk:** Sample data might contain sensitive information
**Probability:** Low
**Impact:** High
**Mitigation:**
- Add option to exclude sample data
- Document that users should review samples
- Consider data masking options
- Make sample generation opt-in

### Risk 4: JSON Schema Evolution
**Risk:** Analysis JSON format may need changes, breaking old exports
**Probability:** High
**Impact:** Low
**Mitigation:**
- Version JSON schemas (v1, v2, etc.)
- Add schema version field to all JSON files
- Maintain backward compatibility for 2 versions
- Provide migration tools

### Risk 5: Memory Usage on Huge Models
**Risk:** Very large models (200+ tables) might exceed memory limits
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Implement streaming for large TMDL files
- Add memory usage monitoring
- Provide "lite" export option (no sample data)
- Document memory requirements

---

## Future Enhancements (Post-v1)

### Phase 6: Interactive Updates
- ✅ Update single object without full re-export
- ✅ Incremental dependency recalculation
- ✅ Live sync with Power BI Desktop

### Phase 7: Advanced Analysis
- ✅ Query performance prediction
- ✅ What-if analysis ("what if I remove this measure?")
- ✅ Automated DAX optimization suggestions
- ✅ Comparison between two model versions

### Phase 8: Integration
- ✅ Git integration for version control
- ✅ CI/CD pipeline support
- ✅ Automated testing of recommendations
- ✅ Team collaboration features

---

## Conclusion

This hybrid approach provides:

1. **Speed:** 50-100x faster than parsing full exports for reads, ~500ms for on-demand analysis
2. **Selectivity:** Read only what's needed, generate insights when requested
3. **Completeness:** No information loss from TMDL
4. **Intelligence:** On-demand performance analysis and recommendations (not pre-computed)
5. **Validation:** Sample data for testing
6. **Scalability:** Works from small to very large models
7. **Efficiency:** Smaller export packages (~7MB vs 50-100MB), faster generation

The three-layer architecture (TMDL + JSON Foundation + Sample Data) gives Claude the perfect balance of speed, depth, and flexibility. Performance analysis and recommendations are generated on-demand by MCP tools, ensuring fresh insights based on current model state.

**Key Advantage:** Export is fast (~8 seconds) and creates a lean package. Analysis complexity happens only when requested, keeping the system responsive while providing deep insights when needed.

**Next step:** Begin Phase 1 implementation with `export_model_analysis` tool.

---

## Summary: Row Count & Unused Column Features

### What Gets Tracked

**Row Counts (from PBIX):**
- ✅ Per-table row counts via DMV queries
- ✅ Last refresh timestamp
- ✅ Total model row count
- ✅ Largest fact tables identified
- ✅ Memory consumption estimates
- ❌ Not available from PBIP (no data)

**Column Usage (from PBIX/PBIP):**
- ✅ Used in relationships (FK/PK)
- ✅ Used in measures (DAX references)
- ✅ Used in calculated columns
- ✅ Used in RLS filters
- ✅ Used in visuals (PBIX only)
- ✅ Cardinality and memory impact
- ✅ Flag for completely unused columns

### Benefits

**1. Unused Column Detection:**
```
Finding: "TransactionID" in FactPortfolioValues
- Cardinality: 1,245,678 (100% unique)
- Memory usage: 45 MB
- Used in: Nothing
- Recommendation: Remove → Save 45 MB + faster refresh
```

**2. Row Count Analysis:**
```
Finding: FactTransactions has 8.9M rows
- Current grain: Transaction-level detail
- Query pattern: Most dashboards group by Account+Date
- Recommendation: Create aggregation → 15-20x speedup
- Aggregated rows: 234K (vs 8.9M)
```

**3. Memory Optimization:**
```
Total unused columns found: 12
Total memory savings: 123 MB
Potential memory reduction: 4.3% of model size
Refresh time savings: Estimated 5-10% faster
```

### Usage Examples

**Query 1: "Find all unused columns"**
```typescript
analyze_performance({
  focus_areas: ["unused_columns"],
  min_priority: "medium"
})
// Returns: 12 unused columns with memory impact
```

**Query 2: "Which tables are too large?"**
```typescript
analyze_performance({
  focus_areas: ["row_counts"],
  min_priority: "high"
})
// Returns: 2 tables >1M rows needing aggregation
```

**Query 3: "Full model cleanup analysis"**
```typescript
analyze_performance({
  focus_areas: ["all"],
  min_priority: "medium"
})
// Returns: Unused columns + large tables + complex measures + cardinality issues
```

### Implementation Notes

**Phase 1 (Export):**
- Extract row counts from model via DMV
- Calculate cardinality per column
- Parse all DAX to find column references
- Store in catalog.json and metadata.json

**Phase 2 (Read Tools):**
- Validate row count extraction accuracy
- Test column usage detection thoroughly
- Ensure no false positives for unused columns

**Phase 4 (Analysis):**
- Use catalog data to identify unused columns
- Use row counts to recommend aggregations
- Generate prioritized recommendations with memory impact

**Accuracy Critical:**
- **False positive (column flagged as unused but is used):** Could break model if removed
- **Solution:** Multi-layered detection (relationships + measures + visuals + RLS + calculated columns)
- **Validation:** Spot-check 20+ columns manually against actual usage
- **Conservative approach:** When in doubt, don't flag as unused
