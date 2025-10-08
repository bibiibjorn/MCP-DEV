# PBIXRay MCP Server (v2.3)

Powerful local MCP server that lets Claude analyze your Power BI Desktop models: explore schema, inspect DAX and M, run performance analysis (SE/FE), export model metadata, and more — all via natural language.

• Status: Production-ready  • Platform: Windows 10/11  • Last updated: 2025-10-08

## What’s inside

- Auto-detect and connect to running Power BI Desktop instances
- Explore tables, columns, measures, relationships, and M expressions
- Run DAX queries and analyze performance with SE/FE breakdown
- VertiPaq stats, cardinality/encoding checks, and optimization helpers
- Dependencies, unused objects, calculation groups, partitions, RLS, validation

## Requirements

- Windows 10/11 (64-bit)
- .NET Framework 4.7.2+
- Power BI Desktop (current recommended)
- Claude Desktop

## Quick start

1) Extract the folder to a path you control (recommended: `C:\Tools\pbixray-mcp-server`).
2) Open Power BI Desktop with a .pbix file loaded and wait a few seconds.
3) Configure Claude Desktop:
	- In PowerShell from the project folder: `./scripts/install_to_claude.ps1`
	- Fully restart Claude Desktop afterwards.
4) Optional sanity check: `./scripts/test_connection.ps1`.
5) Ask Claude:
	- “Detect my Power BI Desktop instances” → then “Connect to instance 0”
	- “What tables are in this model?”

You’re now ready to explore your model with Claude.

## Common tasks

- List tools and health check: run `./scripts/test_connection.ps1`
- Performance: “Analyze this DAX query …” and review SE vs FE time
- Model export: “Export TMSL/TMDL” or “Generate documentation”
- Discovery: “Search for measures containing ‘CALCULATE’”

## Install, update, uninstall

- Installation steps, update notes, and cleanup are documented in INSTALL.md

## Notes on privacy & security

- All analysis is local and the server binds to 127.0.0.1
- Claude conversations may be stored by Anthropic; avoid pasting sensitive data

## Support

- If something doesn’t work: ensure Power BI Desktop has a model open, rerun detection, and reconnect. Check `logs/` if needed.
- For team distribution: use `./scripts/package_for_distribution.ps1` to create a zip you can share.

— Happy analyzing!
