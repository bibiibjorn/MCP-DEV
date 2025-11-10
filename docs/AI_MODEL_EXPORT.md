# AI Model Export Tool - Complete Guide

## Overview

The **`analyze_model_for_ai`** tool exports your entire Power BI model in an AI-optimized format, designed specifically for comprehensive analysis by AI/LLMs like Claude. This export includes everything needed for deep model analysis, optimization recommendations, and best practice reviews.

## What's Included in the Export

The export creates a comprehensive JSON file containing:

### 1. **Metadata**
- Export version and timestamp
- Model name and compatibility level
- Source file information
- Complete statistics (tables, measures, columns, relationships, calc groups)

### 2. **Tables & Columns**
- Table names, types (Table/CalculatedTable), visibility
- Row counts (if sample data included)
- Column metadata: name, data type, is_key, is_hidden, data_category
- Sort by column references
- Format strings
- Source columns vs calculated columns
- Column descriptions

### 3. **Measures**
- All measure names with full DAX expressions
- Display folders for organization
- Data types and format strings
- Hidden/visible status
- Descriptions
- **DAX pattern detection** (Time Intelligence, Aggregation, Iterator, Filter Context, etc.)

### 4. **Measure Dependencies** (if included)
- Direct dependencies (columns & measures used)
- Downstream dependencies (measures that depend on this measure)
- Dependency depth and complexity scores
- Column lineage (which columns are used in which measures)

### 5. **Sample Data** (if included)
- Configurable number of rows per table (default: 20)
- **Columnar format** for efficient AI processing
- Actual data values for context

### 6. **Relationships**
- From/To table and column
- Cardinality (Many:One, One:Many, etc.)
- Cross-filter direction (Single/Both)
- Active/Inactive status
- Security filtering behavior
- Referential integrity settings

### 7. **Calculation Groups**
- Calculation group names and precedence
- All calculation items with expressions
- Format string expressions
- Descriptions

### 8. **Row-Level Security (RLS)**
- Role names and descriptions
- Table permissions
- Filter expressions for each role

### 9. **M Expressions**
- Power Query expressions
- Data source connections
- Transformation logic

### 10. **Hierarchies**
- Hierarchy names and levels
- Column associations
- Hidden status

### 11. **Partitions**
- Partition names and modes (Import/DirectQuery/Dual)
- Source types
- M expressions (truncated for large expressions)

## Usage

### Basic Export (Recommended)

```json
{
  "tool": "analyze_model_for_ai"
}
```

This uses all defaults:
- Format: `json_gzip` (compressed JSON)
- Sample rows: 20 per table
- Includes sample data: Yes
- Includes dependencies: Yes
- Includes DAX patterns: Yes
- Auto-generates output path in `exports/ai_exports/`

### Custom Export Options

```json
{
  "tool": "analyze_model_for_ai",
  "output_format": "json",
  "sample_rows": 50,
  "include_sample_data": true,
  "include_dependencies": true,
  "include_bpa_issues": false,
  "include_dax_patterns": true,
  "output_path": "C:\\MyExports\\model_analysis.json"
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_format` | string | `"json_gzip"` | Export format: `"json"`, `"json_gzip"` (recommended), or `"markdown"` |
| `sample_rows` | integer | 20 | Number of sample data rows per table (0 to skip) |
| `include_sample_data` | boolean | true | Include actual data samples from tables |
| `include_dependencies` | boolean | true | Include measure and column dependency analysis |
| `include_bpa_issues` | boolean | false | Include Best Practice Analyzer results |
| `include_dax_patterns` | boolean | true | Detect and tag DAX patterns in measures |
| `output_path` | string | auto | Custom output path (auto-generated if not specified) |

## Output Formats

### JSON (Uncompressed)
- Best for: Small models, debugging, manual inspection
- File size: 5-50 MB for typical models
- Extension: `.json`

### JSON GZIP (Recommended)
- Best for: Most use cases, large models
- File size: 1-10 MB (60-80% compression)
- Extension: `.json.gz`
- Compression ratio: typically 3-5x

### Markdown
- Best for: Human-readable documentation, reports
- File size: 10-100 MB
- Extension: `.md`
- Includes formatted tables and code blocks

## Export Results

The tool returns comprehensive results:

```json
{
  "success": true,
  "export_file": "C:\\...\\exports\\ai_exports\\SalesModel_ai_20250110_143022.json.gz",
  "file_size_mb": 3.5,
  "compression_ratio": 4.2,
  "export_time_seconds": 12.3,
  "format": "json_gzip",
  "statistics": {
    "table_count": 15,
    "measure_count": 120,
    "column_count": 250,
    "relationship_count": 18,
    "calculation_group_count": 2
  },
  "user_prompt": {
    "message": "...",
    "export_path": "...",
    "suggested_actions": [...]
  }
}
```

## User Interaction After Export

After a successful export, the tool provides a comprehensive prompt asking the user what type of analysis they'd like to perform:

**Suggested Analysis Types:**
1. **Model Optimization** - Identify opportunities to improve model performance and reduce memory usage
2. **DAX Performance** - Review measures for performance issues, inefficient patterns, and optimization opportunities
3. **Best Practices** - Check adherence to Power BI modeling best practices
4. **Relationships** - Audit relationship cardinality, filter direction, and potential issues
5. **Security (RLS)** - Review row-level security implementation and potential gaps
6. **Comprehensive Assessment** - Full model health check covering all areas

## Use Cases

### 1. Model Optimization
```
"Analyze the exported model for memory optimization opportunities.
Focus on column cardinality, data types, and unused columns."
```

### 2. DAX Performance Review
```
"Review all measures in the export. Identify:
- Measures using inefficient patterns
- Opportunities to use variables
- Measures that could benefit from CALCULATE optimization"
```

### 3. Dependency Analysis
```
"Analyze the measure dependencies. Find:
- Measures with the most complex dependency chains
- Unused measures
- Circular or problematic dependencies"
```

### 4. Data Model Assessment
```
"Review the relationships and suggest:
- Potential many-to-many relationship issues
- Bidirectional filters that could be avoided
- Missing relationships based on column names"
```

### 5. Security Audit
```
"Review the RLS roles and identify:
- Tables without RLS that might need it
- Potential security gaps
- Complex filter expressions that could be simplified"
```

### 6. Migration Planning
```
"Compare this model structure against best practices for
migration from Import to DirectQuery mode."
```

## File Size Expectations

| Model Size | Tables | Measures | JSON (uncompressed) | JSON GZIP | Markdown |
|------------|--------|----------|---------------------|-----------|----------|
| Small | 5-10 | 20-50 | 2-5 MB | 0.5-1 MB | 5-10 MB |
| Medium | 10-30 | 50-200 | 10-25 MB | 2-5 MB | 20-50 MB |
| Large | 30-100 | 200-500 | 25-100 MB | 5-20 MB | 50-200 MB |
| Very Large | 100+ | 500+ | 100+ MB | 20+ MB | 200+ MB |

**Note:** Sample data rows significantly impact file size. Reduce `sample_rows` for very large models.

## JSON Schema Structure

```json
{
  "success": true,
  "metadata": {
    "export_version": "1.0.0",
    "export_timestamp": "2025-01-10T14:30:22",
    "source_file": "Sales Model.pbix",
    "compatibility_level": 1600,
    "model_name": "Sales Model",
    "culture": "en-US",
    "exporter": "MCP-PowerBi-Finvision AI Exporter",
    "statistics": { ... }
  },
  "tables": [
    {
      "name": "Sales",
      "type": "Table",
      "is_hidden": false,
      "row_count": 1500000,
      "data_category": "Uncategorized",
      "description": null,
      "columns": [ ... ],
      "measures": [ ... ],
      "hierarchies": [ ... ],
      "partitions": [ ... ],
      "sample_data": {
        "format": "columnar",
        "row_count": 20,
        "total_row_count": 1500000,
        "columns": ["OrderDate", "CustomerKey", "Amount"],
        "data": {
          "OrderDate": ["2024-01-01", "2024-01-02", ...],
          "CustomerKey": [1001, 1002, ...],
          "Amount": [250.50, 1200.00, ...]
        }
      }
    }
  ],
  "relationships": [ ... ],
  "calculation_groups": [ ... ],
  "roles": [ ... ],
  "m_expressions": [ ... ],
  "dependency_graph": {
    "measures": {
      "Sales[Total Sales]": {
        "direct_dependencies": {
          "columns": ["Sales[Amount]"],
          "measures": []
        },
        "dependency_depth": 0,
        "complexity_score": 18
      }
    },
    "columns": {
      "Sales[Amount]": {
        "used_in_measures": ["Sales[Total Sales]", "Sales[Average Sale]"],
        "used_in_calculated_columns": [],
        "used_in_rls": false
      }
    }
  }
}
```

## Reading the Export File

### Python
```python
import json
import gzip

# Read gzipped JSON
with gzip.open('model_export.json.gz', 'rt', encoding='utf-8') as f:
    model = json.load(f)

print(f"Model: {model['metadata']['model_name']}")
print(f"Tables: {model['metadata']['statistics']['table_count']}")
print(f"Measures: {model['metadata']['statistics']['measure_count']}")

# Access tables
for table in model['tables']:
    print(f"Table: {table['name']}")
    for measure in table['measures']:
        print(f"  Measure: {measure['name']}")
        print(f"  DAX: {measure['expression']}")
```

### PowerShell
```powershell
# Decompress gzip file
$infile = "model_export.json.gz"
$outfile = "model_export.json"

$input = New-Object System.IO.FileStream $infile, ([IO.FileMode]::Open)
$output = New-Object System.IO.FileStream $outfile, ([IO.FileMode]::Create)
$gzipStream = New-Object System.IO.Compression.GzipStream $input, ([IO.Compression.CompressionMode]::Decompress)

$gzipStream.CopyTo($output)
$gzipStream.Close()
$output.Close()
$input.Close()

# Read JSON
$model = Get-Content $outfile | ConvertFrom-Json
Write-Host "Model: $($model.metadata.model_name)"
```

### JavaScript/Node.js
```javascript
const fs = require('fs');
const zlib = require('zlib');

// Read gzipped JSON
const buffer = fs.readFileSync('model_export.json.gz');
const decompressed = zlib.gunzipSync(buffer);
const model = JSON.parse(decompressed.toString());

console.log(`Model: ${model.metadata.model_name}`);
console.log(`Tables: ${model.metadata.statistics.table_count}`);
```

## Performance Considerations

### Export Time
- Small models: 5-15 seconds
- Medium models: 15-60 seconds
- Large models: 1-3 minutes
- Very large models: 3-10 minutes

**Factors affecting speed:**
- Number of tables (biggest factor)
- Sample data rows (20 rows vs 100 rows = 5x slower)
- Number of measures
- Connection speed to Power BI Desktop

### Optimization Tips

1. **Skip sample data for metadata-only analysis:**
   ```json
   {
     "include_sample_data": false
   }
   ```

2. **Reduce sample rows for large models:**
   ```json
   {
     "sample_rows": 5
   }
   ```

3. **Use JSON GZIP for faster file transfer:**
   ```json
   {
     "output_format": "json_gzip"
   }
   ```

4. **Skip BPA for faster export:**
   ```json
   {
     "include_bpa_issues": false
   }
   ```

## Troubleshooting

### Export Fails with "Not connected"
**Solution:** Ensure you're connected to Power BI Desktop first:
```json
{
  "tool": "detect_instances"
}
```
Then connect to an instance before exporting.

### Export File Too Large
**Solutions:**
1. Reduce `sample_rows` from 20 to 5 or 10
2. Set `include_sample_data` to `false`
3. Use `json_gzip` format instead of `json`

### Out of Memory Error
**Solution:** For very large models (100+ tables), use minimal settings:
```json
{
  "sample_rows": 0,
  "include_sample_data": false,
  "include_dependencies": false
}
```

### Slow Export Performance
**Solutions:**
1. Reduce sample_rows
2. Skip BPA: `"include_bpa_issues": false`
3. Close other applications using Power BI Desktop
4. Ensure Power BI Desktop file is not too large

## Integration Examples

### AI-Powered Analysis Workflow

1. **Export Model:**
   ```json
   {
     "tool": "analyze_model_for_ai"
   }
   ```

2. **Analyze Export:**
   ```
   "Please analyze the exported model and identify:
   - Top 5 performance optimization opportunities
   - Any DAX measures using deprecated or inefficient patterns
   - Tables that could benefit from aggregations
   - Relationships that might cause performance issues"
   ```

3. **Generate Report:**
   ```
   "Create a comprehensive optimization report with:
   - Executive summary
   - Detailed findings by category
   - Prioritized recommendations
   - Implementation complexity estimates"
   ```

### CI/CD Integration

```python
# automated_analysis.py
import json
import gzip
from mcp_client import MCPClient

client = MCPClient()

# Export model
result = client.call_tool("analyze_model_for_ai", {
    "output_format": "json_gzip",
    "include_bpa_issues": True
})

# Analyze export
with gzip.open(result['export_file'], 'rt') as f:
    model = json.load(f)

# Check for issues
issues = []
for table in model['tables']:
    for measure in table['measures']:
        if 'CALCULATE' in measure['expression'] and 'FILTER' in measure['expression']:
            issues.append(f"Potential performance issue: {table['name']}.{measure['name']}")

if issues:
    print("WARNINGS FOUND:")
    for issue in issues:
        print(f"  - {issue}")
```

## Best Practices

1. **Regular Exports:** Export your model weekly to track changes over time
2. **Version Control:** Store exports in version control alongside your PBIX files
3. **Baseline Analysis:** Create a baseline export after major optimizations
4. **Documentation:** Use Markdown exports for human-readable documentation
5. **Automation:** Integrate into CI/CD pipelines for automated quality checks

## Limitations

1. **Requires Open PBIX:** Model must be open in Power BI Desktop
2. **Read-Only:** This tool only reads the model, it doesn't modify it
3. **Sample Data Limits:** Large tables may take time to sample
4. **Memory:** Very large exports may use significant memory
5. **Dependencies:** Basic dependency analysis (full DAX parsing requires additional tools)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review export results for error messages
3. Reduce export scope (fewer sample rows, skip dependencies)
4. Report issues to the MCP-PowerBi-Finvision repository

## Version History

- **v1.0.0** (2025-01-10): Initial release
  - Comprehensive model export
  - JSON, JSON GZIP, and Markdown formats
  - Dependency analysis
  - DAX pattern detection
  - Sample data support
  - User interaction prompts
