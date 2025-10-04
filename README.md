# PBIXRay MCP Server V2 - Enhanced Edition

**Version:** 2.0 Enhanced  
**Status:** Production Ready
**Last Updated:** 2025-10-04

## What is This?

The **PBIXRay MCP Server V2** is a Model Context Protocol (MCP) server that enables Claude AI to analyze Power BI Desktop models with advanced performance analysis capabilities including Storage Engine (SE) and Formula Engine (FE) breakdown.

## Key Features

- Auto-detect Power BI Desktop instances
- Full Model Exploration - Tables, columns, measures, relationships
- DAX Analysis - Measures, calculated columns, with expressions
- Power Query (M) - View data source configurations
- Performance Analysis - Advanced SE/FE timing with SessionTrace
- VertiPaq Stats - Storage and compression metrics
- Search Capabilities - Find objects and text across the model
- Natural Language - Ask Claude questions about your model

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

## Available Tools

Key tools available:
- detect_powerbi_desktop - Find running Power BI instances
- connect_to_powerbi - Connect to a specific instance
- list_tables - List all tables in the model
- list_measures - List DAX measures
- describe_table - Get detailed table information
- run_dax_query - Execute DAX queries
- analyze_query_performance - SE/FE performance analysis
- get_vertipaq_stats - Storage and compression metrics
- search_objects - Find tables, columns, measures
- export_model_schema - Export complete model structure

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

```
You: "Analyze the performance of this DAX query"

Claude: [Runs analyze_query_performance with 3 runs]

Results:
- Total: 245ms
- Storage Engine: 189ms (77%)
- Formula Engine: 56ms (23%)
- SE Queries: 12

The query is SE-heavy, indicating most time is spent 
retrieving data. Consider adding filters to reduce 
the amount of data scanned.
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
