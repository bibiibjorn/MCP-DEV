# PBIXRay MCP Server V2.3 - Professional Edition

**Version:** 2.3 Professional
**Status:** Production Ready
**Last Updated:** 2025-01-06
**Tools:** 50+ professional Power BI development tools

## What is This?

The **PBIXRay MCP Server V2** is a Model Context Protocol (MCP) server that enables Claude AI to analyze Power BI Desktop models with advanced performance analysis capabilities including Storage Engine (SE) and Formula Engine (FE) breakdown.

## Key Features

### Core Capabilities
- Auto-detect Power BI Desktop instances
- Full Model Exploration - Tables, columns, measures, relationships
- DAX Analysis - Measures, calculated columns, with expressions
- Power Query (M) - View data source configurations
- Performance Analysis - Advanced SE/FE timing with SessionTrace
- VertiPaq Stats - Storage and compression metrics
- Search Capabilities - Find objects and text across the model

### NEW: Advanced Features (v2.3)
- **Dependency Analysis** - Analyze measure dependencies and find unused objects
- **Version Control** - Export TMSL/TMDL for Git integration
- **Calculation Groups** - Create and manage calculation groups (not possible in Desktop!)
- **Performance Optimization** - Cardinality and encoding analysis with recommendations
- **Partition Management** - View and refresh partitions for incremental refresh
- **Bulk Operations** - Create/update/delete multiple measures at once
- **Model Validation** - Comprehensive integrity checks and data quality validation
- **RLS Management** - List roles, test filters, validate coverage
- **Documentation** - Auto-generate markdown documentation

## System Requirements

- **OS:** Windows 10/11 (64-bit)
- **.NET Framework:** 4.7.2+ (usually pre-installed)
- **Power BI Desktop:** Latest version recommended
- **Claude Desktop:** Latest version
- **Disk Space:** ~200 MB

## Quick Start

### 1. Extract the Package

Extract the entire folder to your preferred location, for example:
```
C:\Tools\pbixray-mcp-server
```

### 2. Verify Installation (Optional)

```powershell
cd C:\Tools\pbixray-mcp-server
.\scripts\test_connection.ps1
```

### 3. Configure Claude Desktop

```powershell
.\scripts\install_to_claude.ps1
```

This will automatically configure Claude Desktop for you.

### 4. Restart Claude Desktop

- **Fully close** Claude Desktop (check Task Manager)
- **Reopen** Claude Desktop

### 5. Test It!

1. Open Power BI Desktop with a .pbix file
2. In Claude, say: **"Detect my Power BI Desktop instances"**
3. Say: **"Connect to instance 0"**
4. Say: **"What tables are in this model?"**

You are now analyzing Power BI with Claude AI!

## Documentation

- **Quick Reference** - docs/QUICK_REFERENCE.md - Command cheat sheet
- **FAQ** - docs/FAQ.md - Frequently asked questions
- **Troubleshooting** - docs/TROUBLESHOOTING.md - Common issues
- **Deployment Guide** - docs/DEPLOYMENT_GUIDE.md - Team deployment

## Available Tools (50+ Tools)

### Connection & Discovery
- detect_powerbi_desktop, connect_to_powerbi

### Model Exploration
- list_tables, list_measures, list_columns, list_relationships
- describe_table, get_measure_details, search_objects

### DAX & Data
- run_dax_query, preview_table_data, get_column_values
- get_column_summary, validate_dax_query

### Measure Management
- upsert_measure, delete_measure
- **NEW:** bulk_create_measures, bulk_delete_measures

### Dependency Analysis (NEW)
- analyze_measure_dependencies - See what uses what
- find_unused_objects - Cleanup opportunities
- analyze_column_usage - Impact analysis

### Export & Version Control (NEW)
- export_tmsl - TMSL JSON format for Git
- export_tmdl - TMDL folder structure (modern)
- generate_documentation - Auto-generate markdown docs
- compare_models - Diff between versions

### Calculation Groups (NEW)
- list_calculation_groups
- create_calculation_group - Create time intelligence patterns
- delete_calculation_group

### Performance & Optimization (NEW)
- analyze_query_performance - SE/FE breakdown
- analyze_relationship_cardinality - Find duplicates in one-side
- analyze_column_cardinality - High cardinality detection
- analyze_encoding_efficiency - VertiPaq compression analysis
- get_vertipaq_stats - Storage metrics

### Partition Management (NEW)
- list_partitions - View partition details
- refresh_partition - Refresh specific partition
- refresh_table - Refresh entire table

### Model Validation (NEW)
- validate_model_integrity - Comprehensive checks
- analyze_data_freshness - Last refresh times
- analyze_model_bpa - Best Practice Analyzer

### RLS Security (NEW)
- list_roles - List all security roles
- test_role_filter - Test RLS with queries
- validate_rls_coverage - Check which tables have RLS

## Folder Structure

```
pbixray-mcp-server/
├── venv/              # Python environment (portable)
├── src/               # Server source code
├── lib/dotnet/        # Analysis Services DLLs
├── docs/              # Documentation
├── scripts/           # Helper scripts
├── config/            # Configuration templates
├── logs/              # Auto-generated logs
└── requirements.txt   # Python dependencies
```

## Example Usage

### Performance Analysis
```
You: "Analyze the performance of this DAX query"
Claude: [Runs analyze_query_performance with 3 runs]

Results:
- Total: 245ms
- Storage Engine: 189ms (77%)
- Formula Engine: 56ms (23%)
- SE Queries: 12
```

### Dependency Analysis (NEW)
```
You: "If I modify [Total Sales], what will break?"
Claude: [Runs analyze_measure_dependencies]

7 measures depend on [Total Sales]:
- Sales YoY%, Sales Growth, Sales Rank, Sales vs Target...
```

### Version Control (NEW)
```
You: "Export this model for Git"
Claude: [Exports TMSL]

Exported 1.2MB TMSL file with 45 tables, 523 measures, 78 relationships.
Save this to your repository for version tracking.
```

### Bulk Operations (NEW)
```
You: "Create 20 time intelligence measures from this JSON"
Claude: [Bulk creates measures]

Created 20 measures across 3 tables in 5 seconds.
```

### Calculation Groups (NEW)
```
You: "Create a time intelligence calculation group with YTD, PY, and YoY%"
Claude: [Creates calculation group]

Created 'Time Intelligence' with 3 calculation items.
This replaces 60+ individual measures!
```

## Maintenance

### Update Python Packages

```powershell
.\venv\Scripts\pip.exe install --upgrade -r requirements.txt
```

### Verify Health

```powershell
.\verify_installation.ps1 -Verbose
```

## For Team Distribution

To package for colleagues:

```powershell
.\scripts\package_for_distribution.ps1
```

This creates a ready-to-share ZIP file on your Desktop.

## Troubleshooting

**No instances detected?**
- Ensure Power BI Desktop is running
- Open a .pbix file (not just Power BI)
- Wait 10-15 seconds after opening

**Connection fails?**
- Verify instance index (usually 0)
- Restart Power BI Desktop
- Check docs/TROUBLESHOOTING.md

**Claude does not see the server?**
- Run: `.\scripts\install_to_claude.ps1`
- Restart Claude Desktop completely
- Check JSON syntax in config

## Credits

Built with:
- **MCP SDK** - Model Context Protocol
- **Python.NET** - CLR integration
- **Analysis Services Client Libraries** - Microsoft
- **Power BI Desktop** - Microsoft

## Version History

- **V2.3** (Jan 2025) - 28 new tools! Dependency analysis, TMSL/TMDL export, calculation groups, cardinality analysis, partition management, bulk operations, model validation, RLS management
- **V2.0 Enhanced** (Oct 2025) - SessionTrace integration, improved SE/FE analysis
- **V2.0** (Oct 2025) - WMI-based detection, stability improvements
- **V1.0** (Sep 2025) - Initial release

## Privacy and Security

- **All processing is local** - No data sent to external servers
- **Localhost only** - Binds to 127.0.0.1
- **No network exposure** - Completely offline capable
- **Claude conversations** - May be stored by Anthropic (review their policy)

---

**Happy Analyzing!**

For questions or issues, see the FAQ or Troubleshooting Guide in the docs folder.
