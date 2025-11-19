"""
User Guide Handler
Handles user guide display
"""
from typing import Dict, Any
import logging
import os
from server.registry import ToolDefinition

logger = logging.getLogger(__name__)

def handle_show_user_guide(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show comprehensive user guide"""
    try:
        # Get the guide path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        guide_path = os.path.join(project_root, 'docs', 'PBIXRAY_Quickstart.md')

        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_content = f.read()

            return {
                'success': True,
                'guide': guide_content,
                'path': guide_path
            }
        else:
            # Return basic usage guide if file not found
            return {
                'success': True,
                'guide': _get_inline_guide(),
                'note': 'Using inline guide (file not found)'
            }

    except Exception as e:
        logger.error(f"Error loading user guide: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error loading user guide: {str(e)}',
            'fallback_guide': _get_inline_guide()
        }

def _get_inline_guide() -> str:
    """Get inline user guide"""
    return """# MCP-PowerBi-Finvision Comprehensive User Guide v5.01

Welcome to MCP-PowerBi-Finvision! This guide covers all 50+ tools across 13 categories.

---

## 📋 QUICK START

### Step 1: Connect to Power BI
```
1. Open Power BI Desktop with your model
2. Use: 01_detect_pbi_instances
3. Use: 01_connect_to_instance (typically model_index=0)
```

### Step 2: Explore Your Model
```
- List tables: 02_list_tables
- Describe a table: 02_describe_table
- List measures: 02_list_measures
- Get measure details: 02_get_measure_details
```

---

## 🔧 CATEGORY 01: CONNECTION (2 tools)

### 01_detect_pbi_instances
**Purpose**: Detect running Power BI Desktop instances
**When to use**: Start of every session to find available models
**Parameters**: None
**Returns**: List of instances with ports and model names

### 01_connect_to_instance
**Purpose**: Connect to a specific Power BI Desktop instance
**When to use**: After detecting instances, to establish connection
**Parameters**:
  - model_index: Index from detection list (usually 0)
**Returns**: Connection status and model information

---

## 📊 CATEGORY 02: SCHEMA/METADATA (8 tools)

### 02_list_tables
**Purpose**: List all tables in the model
**When to use**: Initial exploration, understanding model structure
**Parameters**: None
**Returns**: Table names, row counts, types (fact/dimension)

### 02_describe_table
**Purpose**: Get comprehensive table information
**When to use**: Deep dive into specific table
**Parameters**:
  - table: Table name
**Returns**: Columns, measures, relationships, partitions, descriptions

### 02_list_columns
**Purpose**: List columns across tables
**When to use**: Finding columns by name or type
**Parameters**:
  - table (optional): Filter by table name
**Returns**: Column names, data types, tables

### 02_list_measures
**Purpose**: List all measures in the model
**When to use**: Understanding calculated metrics
**Parameters**:
  - table (optional): Filter by table name
**Returns**: Measure names, tables, display folders

### 02_get_measure_details
**Purpose**: Get detailed measure information
**When to use**: Analyzing specific measure logic
**Parameters**:
  - table: Table name
  - measure: Measure name
**Returns**: DAX formula, format string, dependencies, folder

### 02_list_calculated_columns
**Purpose**: List calculated columns
**When to use**: Finding calculated columns vs regular columns
**Parameters**: None
**Returns**: Column names, tables, DAX expressions

### 02_search_objects
**Purpose**: Search across tables, columns, and measures
**When to use**: Finding objects by name pattern
**Parameters**:
  - search_term: Text to search for
  - object_type (optional): Filter by type
**Returns**: Matching objects with details

### 02_search_string
**Purpose**: Search in measure names and expressions
**When to use**: Finding measures containing specific DAX patterns
**Parameters**:
  - search_string: Text to search for
  - search_in: 'name', 'expression', or 'both'
**Returns**: Matching measures with highlighted matches

---

## 🔍 CATEGORY 03: QUERY & DATA + DAX INTELLIGENCE (9 tools)

### 03_preview_table_data
**Purpose**: Preview actual data from a table
**When to use**: Checking data content and quality
**Parameters**:
  - table: Table name
  - max_rows: Limit (default: 10)
**Returns**: Sample rows from table

### 03_run_dax
**Purpose**: Execute any DAX query
**When to use**: Custom queries, testing calculations
**Parameters**:
  - query: DAX EVALUATE statement
  - top_n: Row limit (default: 100)
  - mode: 'auto', 'analyze', 'profile', or 'simple'
**Returns**: Query results with optional timing statistics

### 03_standard_dax_analysis (UNIFIED TOOL)
**Purpose**: Complete DAX analysis: syntax validation + context analysis + debugging
**When to use**: Understanding complex DAX, debugging issues
**Parameters**:
  - expression: DAX expression
  - analysis_mode: 'analyze' (context), 'debug' (step-by-step), 'report' (full)
  - skip_validation: Skip syntax check (default: false)
  - output_format: 'friendly' or 'steps' (debug mode)
  - include_optimization: Include suggestions (report mode)
  - include_profiling: Include performance (report mode)
**Returns**: Comprehensive DAX analysis with insights
**Modes**:
  - analyze: Context transition analysis
  - debug: Step-by-step execution breakdown
  - report: Full analysis with optimization + profiling

### 03_validate_dax_query
**Purpose**: Validate DAX syntax without execution
**When to use**: Quick syntax checks
**Parameters**:
  - query: DAX query to validate
**Returns**: Validation status and errors if any

### 03_get_column_value_distribution
**Purpose**: Get top N values for a column
**When to use**: Understanding column content, checking for issues
**Parameters**:
  - table: Table name
  - column: Column name
  - top_n: Number of values (default: 10)
**Returns**: Values with counts and percentages

### 03_get_column_summary
**Purpose**: Get statistical summary of column
**When to use**: Understanding numeric/date column ranges
**Parameters**:
  - table: Table name
  - column: Column name
**Returns**: Min, max, distinct count, null count

### 03_list_relationships
**Purpose**: List model relationships
**When to use**: Understanding model connectivity
**Parameters**:
  - active_only: Filter active relationships (default: false)
**Returns**: From/to tables/columns, cardinality, cross-filter direction

### 03_get_data_sources
**Purpose**: List all data sources
**When to use**: Understanding data origins
**Parameters**: None
**Returns**: Connection strings, types, credentials info

### 03_get_m_expressions
**Purpose**: List Power Query M expressions
**When to use**: Reviewing data transformation logic
**Parameters**:
  - limit (optional): Maximum expressions to return
**Returns**: M code for each partition/table

---

## ⚙️ CATEGORY 04: MODEL OPERATIONS (9 tools)

### 04_upsert_measure
**Purpose**: Create or update a measure
**When to use**: Adding new calculations or fixing existing ones
**Parameters**:
  - table: Target table name
  - measure: Measure name
  - expression: DAX formula
  - format_string (optional): Format like "#,0" or "0.0%"
  - description (optional): Measure description
  - display_folder (optional): Folder path
**Returns**: Success status
**Note**: Automatically backs up before changes

### 04_delete_measure
**Purpose**: Delete a measure
**When to use**: Removing unused or incorrect measures
**Parameters**:
  - table: Table name
  - measure: Measure name
**Returns**: Success status
**Note**: Check dependencies first with analyze_measure_dependencies

### 04_bulk_create_measures
**Purpose**: Create multiple measures at once
**When to use**: Initializing measure sets, batch operations
**Parameters**:
  - measures: Array of {table, measure, expression, format_string?, description?, display_folder?}
**Returns**: Success count and any errors

### 04_bulk_delete_measures
**Purpose**: Delete multiple measures at once
**When to use**: Cleanup operations
**Parameters**:
  - measures: Array of {table, measure}
**Returns**: Success count and any errors

### 04_list_calculation_groups
**Purpose**: List calculation groups
**When to use**: Understanding time intelligence or other calculation modifiers
**Parameters**: None
**Returns**: Calculation group names, items, precedence

### 04_create_calculation_group
**Purpose**: Create a new calculation group
**When to use**: Implementing time intelligence or custom calculation patterns
**Parameters**:
  - name: Calculation group name
  - items: Array of {name, expression}
  - description (optional)
  - precedence (optional)
**Returns**: Success status

### 04_delete_calculation_group
**Purpose**: Delete a calculation group
**When to use**: Removing calculation groups
**Parameters**:
  - name: Calculation group name
**Returns**: Success status

### 04_list_partitions
**Purpose**: List table partitions
**When to use**: Understanding data loading structure
**Parameters**:
  - table (optional): Filter by table
**Returns**: Partition names, modes, sources, queries

### 04_list_roles
**Purpose**: List Row-Level Security (RLS) roles
**When to use**: Understanding security configuration
**Parameters**: None
**Returns**: Role names, descriptions, table permissions, DAX filters

---

## 📈 CATEGORY 05: ANALYSIS (1 unified tool)

### 05_comprehensive_analysis (UNIFIED ANALYSIS TOOL)
**Purpose**: Complete model analysis: Best Practices + Performance + Integrity
**When to use**: Model health checks, optimization, documentation
**Parameters**:
  - scope: 'all' (default), 'best_practices', 'performance', 'integrity'
  - depth: 'fast', 'balanced' (default), 'deep'
  - include_bpa: Include BPA rules (default: true)
  - include_performance: Include performance analysis (default: true)
  - include_integrity: Include validation (default: true)
  - max_seconds: Time limit for BPA (5-300)
**Returns**: Comprehensive analysis report with:
  - Best practices violations (120+ BPA rules)
  - Performance metrics (cardinality, data types)
  - Integrity issues (circular refs, duplicates, nulls)
  - Recommendations and priority levels
**Scope Options**:
  - all: Complete analysis (recommended for full health check)
  - best_practices: Focus on BPA and M practices
  - performance: Focus on cardinality and optimization
  - integrity: Focus on validation and errors
**Depth Options**:
  - fast: Quick scan (< 1 minute)
  - balanced: Standard analysis (recommended)
  - deep: Thorough analysis (may take several minutes)

---

## 🔗 CATEGORY 06: DEPENDENCIES (2 tools)

### 06_analyze_measure_dependencies
**Purpose**: Analyze what a measure depends on
**When to use**: Understanding measure calculation chain
**Parameters**:
  - table: Table name
  - measure: Measure name
**Returns**: Dependency tree showing referenced measures, columns, tables
**Note**: Critical before modifying or deleting measures

### 06_get_measure_impact
**Purpose**: Analyze what uses a measure
**When to use**: Impact analysis before changes
**Parameters**:
  - table: Table name
  - measure: Measure name
**Returns**: List of measures that reference this measure
**Note**: Use with analyze_measure_dependencies for complete picture

---

## 💾 CATEGORY 07: EXPORT (3 tools)

### 07_export_model_schema
**Purpose**: Export model schema in TMDL format
**When to use**: Documentation, version control, backups
**Parameters**:
  - section: 'compact' (lightweight) or 'all' (full TMDL)
  - output_path (optional): Custom file path
**Returns**:
  - compact: Lightweight schema (~1-2k tokens) without DAX
  - all: Complete TMDL export to file
**Note**: 'all' mode creates file in exports/tmdl_exports/

### 07_export_tmsl
**Purpose**: Export model as TMSL (Tabular Model Scripting Language)
**When to use**: Automation, deployment scripts
**Parameters**:
  - file_path (optional): Output file path
**Returns**: TMSL JSON definition
**Note**: TMSL is JSON-based scripting language for SSAS/Power BI

### 07_export_tmdl
**Purpose**: Export model as TMDL (Tabular Model Definition Language)
**When to use**: Version control, Git-friendly format
**Parameters**:
  - output_dir: Output directory path
**Returns**: TMDL files in directory structure
**Note**: TMDL is text-based, Git-friendly format (Power BI 2024+)

---

## 📄 CATEGORY 08: DOCUMENTATION (3 tools)

### 08_generate_model_documentation_word
**Purpose**: Generate comprehensive Word documentation
**When to use**: Formal documentation, stakeholder reports
**Parameters**:
  - output_path (optional): Custom file path
**Returns**: Word document with tables, measures, relationships, best practices
**Contents**:
  - Model overview
  - Tables and columns
  - Measures with DAX
  - Relationships diagram
  - Best practices analysis

### 08_update_model_documentation_word
**Purpose**: Update existing Word documentation
**When to use**: Incremental documentation updates
**Parameters**:
  - input_path: Existing Word document
  - output_path: Where to save updated version
**Returns**: Updated Word document

### 08_export_model_explorer_html
**Purpose**: Generate interactive HTML documentation
**When to use**: Shareable, searchable documentation
**Parameters**:
  - output_path (optional): Custom file path
**Returns**: Interactive HTML with search, filtering, collapsible sections
**Features**:
  - Search across all objects
  - Filter by type
  - Collapsible sections
  - Copy DAX to clipboard
  - No dependencies, self-contained

---

## 🔄 CATEGORY 09: COMPARISON (2 tools)

### 09_prepare_model_comparison (STEP 1)
**Purpose**: Detect two Power BI models for comparison
**When to use**: Before comparing models (must run first)
**Parameters**: None
**Returns**: List of detected models, prompts user to identify OLD and NEW
**Workflow**:
  1. Open both Power BI files
  2. Run 09_prepare_model_comparison
  3. User confirms which is OLD and which is NEW
  4. Run 09_compare_pbi_models

### 09_compare_pbi_models (STEP 2)
**Purpose**: Compare two Power BI models
**When to use**: After prepare_model_comparison
**Parameters**:
  - old_port: Port number of OLD model
  - new_port: Port number of NEW model
**Returns**: Detailed comparison report:
  - Added/removed/modified tables
  - Added/removed/modified measures
  - Added/removed/modified columns
  - Relationship changes
  - DAX formula differences
**Use cases**:
  - Version comparison
  - Development vs production
  - Impact analysis of changes

---

## 📦 CATEGORY 10: PBIP OFFLINE ANALYSIS (1 tool)

### 10_analyze_pbip_repository
**Purpose**: Analyze PBIP format without Power BI Desktop
**When to use**: CI/CD pipelines, Git repo analysis, no desktop access
**Parameters**:
  - pbip_path: Path to .pbip file or folder
  - output_path (optional): Output directory for report
**Returns**: HTML report with model analysis
**Features**:
  - Works offline (no Power BI connection)
  - Analyzes TMDL/TMSL definition
  - Identifies tables, measures, relationships
  - Best practices from file analysis
  - Perfect for Git hooks and CI/CD
**Note**: PBIP format introduced in Power BI 2024

---

## 🔧 CATEGORY 11: TMDL AUTOMATION (3 tools)

### 11_tmdl_find_replace
**Purpose**: Find and replace patterns in TMDL files
**When to use**: Bulk DAX refactoring, renaming patterns
**Parameters**:
  - tmdl_path: Path to TMDL export folder
  - pattern: Regex pattern to find
  - replacement: Replacement text
  - dry_run: Preview without applying (default: true)
**Returns**: List of matches and changes
**Use cases**:
  - Rename table references in all measures
  - Update calculation patterns
  - Fix common mistakes across measures
**Safety**: Always run with dry_run=true first!

### 11_tmdl_bulk_rename
**Purpose**: Rename objects with automatic reference updates
**When to use**: Renaming tables/measures while maintaining references
**Parameters**:
  - tmdl_path: Path to TMDL export folder
  - renames: Array of {old_name, new_name}
  - dry_run: Preview without applying (default: true)
**Returns**: Preview of rename operations
**Intelligence**: Automatically updates all references to renamed objects
**Safety**: Always run with dry_run=true first!

### 11_tmdl_generate_script
**Purpose**: Generate TMDL code for new objects
**When to use**: Creating templates, scripting object creation
**Parameters**:
  - object_type: 'table', 'measure', 'relationship', 'calc_group'
  - definition: Object properties (varies by type)
**Returns**: Valid TMDL code ready to use
**Use cases**:
  - Generate measure templates
  - Create relationship definitions
  - Build calculation groups

---

## ❓ CATEGORY 12: HELP (1 tool)

### 12_show_user_guide
**Purpose**: Display this comprehensive user guide
**When to use**: Anytime you need tool reference
**Parameters**: None
**Returns**: This guide

---

## 🔀 CATEGORY 13: HYBRID ANALYSIS (2 tools)

### 13_export_hybrid_analysis
**Purpose**: Export combined TMDL + metadata + sample data
**When to use**: Complete offline analysis package
**Parameters**:
  - pbip_folder_path: Path to .SemanticModel folder or parent
  - output_dir (optional): Output location
  - connection_string/server/database (optional): Manual connection
  - include_sample_data: Include data samples (default: true)
  - sample_rows: Rows per table (default: 1000, max: 5000)
  - sample_compression: 'snappy' (default) or 'zstd'
  - include_row_counts: Include row counts (default: true)
  - track_column_usage: Track usage stats (default: true)
  - track_cardinality: Track cardinality (default: true)
  - tmdl_strategy: 'symlink' (default) or 'copy'
**Returns**: Folder with TMDL + metadata.json + sample_data (parquet)
**Features**:
  - Auto-detects running Power BI Desktop
  - Combines static TMDL with live metadata
  - Extracts sample data for testing
  - Optimized for AI analysis
**Use cases**:
  - AI-powered model analysis
  - Testing with real data
  - Comprehensive documentation

### 13_analyze_hybrid_model (FULLY AUTOMATED)
**Purpose**: Analyze exported hybrid model (reads all files internally)
**When to use**: After export_hybrid_analysis
**Parameters**:
  - analysis_path: Path to analysis folder (tool reads all files internally)
  - operation: Type of analysis
    - 'read_metadata': Parse TMDL + JSON
    - 'find_objects': Search TMDL files
    - 'get_object_definition': Extract DAX from TMDL
    - 'analyze_dependencies': Parse dependency tree
    - 'analyze_performance': Scan measures for issues
    - 'get_sample_data': Read parquet data
    - 'get_unused_columns': Read JSON stats
    - 'get_report_dependencies': Read JSON usage
    - 'smart_analyze': Natural language query
  - intent: Natural language query (for smart_analyze)
  - object_filter: Filter criteria
  - format_type: 'json' (default) or 'toon' (compact)
  - batch_size/batch_number: Pagination
  - priority: Filter by priority level
  - detailed: Include detailed analysis
**Returns**: Analysis results based on operation
**Key Feature**: Fully automated - NO manual file reading needed!
**Intelligence**:
  - Fuzzy search (e.g., "base scenario" finds "PL-AMT-BASE Scenario")
  - Natural language queries with smart_analyze
  - Automatic pagination for large results
  - TOON format for 50% size reduction

---

## 🎯 COMMON WORKFLOWS

### Workflow 1: Model Health Check
```
1. 01_detect_pbi_instances
2. 01_connect_to_instance
3. 05_comprehensive_analysis (scope='all', depth='balanced')
4. Review best practices violations
5. Address critical/high priority issues
```

### Workflow 2: Measure Development
```
1. 02_get_measure_details (study existing measures)
2. 03_standard_dax_analysis (test DAX logic, mode='debug')
3. 04_upsert_measure (create new measure)
4. 03_run_dax (test with real data)
5. 06_analyze_measure_dependencies (verify dependencies)
```

### Workflow 3: Model Documentation
```
1. 02_list_tables (get model overview)
2. 05_comprehensive_analysis (get full analysis)
3. 08_generate_model_documentation_word
4. 08_export_model_explorer_html (shareable version)
5. 07_export_model_schema (section='all') (version control)
```

### Workflow 4: Performance Optimization
```
1. 05_comprehensive_analysis (scope='performance')
2. Review cardinality issues
3. 03_get_column_value_distribution (check high-cardinality columns)
4. 02_list_relationships (verify relationship direction)
5. 03_standard_dax_analysis (mode='report') (optimize measures)
```

### Workflow 5: Model Comparison
```
1. Open both Power BI files
2. 09_prepare_model_comparison
3. Confirm OLD and NEW
4. 09_compare_pbi_models (old_port, new_port)
5. Review changes and impacts
```

### Workflow 6: CI/CD Integration
```
1. 10_analyze_pbip_repository (offline analysis)
2. Review best practices from PBIP
3. 13_export_hybrid_analysis (if live model available)
4. 13_analyze_hybrid_model (automated analysis)
5. Generate reports for pipeline
```

### Workflow 7: DAX Debugging
```
1. 02_get_measure_details (get measure formula)
2. 06_analyze_measure_dependencies (understand dependencies)
3. 03_standard_dax_analysis (mode='debug') (step-by-step)
4. 03_run_dax (test with modifications)
5. 04_upsert_measure (save fixed version)
```

---

## 💡 TIPS & BEST PRACTICES

### Connection Tips
- Always start with detect_pbi_instances
- Typically use model_index=0 for single file
- Keep Power BI Desktop open during analysis

### Analysis Tips
- Run comprehensive_analysis regularly (weekly recommended)
- Address CRITICAL and HIGH priority issues first
- Use depth='balanced' for most cases, 'deep' for problem areas

### DAX Development Tips
- Always use 03_standard_dax_analysis before creating measures
- Test with 03_run_dax before committing
- Check dependencies with analyze_measure_dependencies
- Use mode='debug' for step-by-step understanding

### Performance Tips
- Check cardinality with comprehensive_analysis
- Review column data types (integers > strings)
- Optimize bidirectional relationships
- Use calculated columns sparingly

### Documentation Tips
- Generate docs before major changes (baseline)
- Use HTML export for team sharing
- Export TMDL for version control (Git)
- Update docs after significant changes

### TMDL Automation Tips
- ALWAYS use dry_run=true first
- Test on a copy before bulk operations
- Use version control before find/replace
- Export TMDL before major refactoring

### Safety Tips
- Comprehensive_analysis backs up before changes
- Check measure_impact before deleting
- Use prepare_model_comparison before comparing
- Test DAX with validate_dax_query first

---

## 🚀 VERSION INFORMATION

**Current Version**: 5.01
**Tools**: 50+ across 13 categories
**Platform**: Windows 10/11 (64-bit)
**Requirements**:
  - Power BI Desktop installed
  - .NET Framework 4.7.2+
**Communication**: stdio (no exposed ports)

---

## 📞 SUPPORT & RESOURCES

For detailed documentation, visit:
- GitHub: https://github.com/bibiibjorn/MCP-PowerBi-Finvision
- Issues: Report bugs and feature requests on GitHub

---

**Note**: This MCP server runs locally and securely communicates via stdio. No data leaves your machine.
All operations are performed directly on your local Power BI Desktop instances.

**Last Updated**: January 2025
"""

def register_user_guide_handlers(registry):
    """Register user guide handler"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="show_user_guide",
            description="Show comprehensive user guide",
            handler=handle_show_user_guide,
            input_schema=TOOL_SCHEMAS.get('show_user_guide', {}),
            category="help",
            sort_order=51
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} user guide handlers")
