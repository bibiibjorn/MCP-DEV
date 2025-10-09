# MCP-PowerBi-Finvision Server (v2.3)

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
3) Configure Claude Desktop (or ChatGPT):
	- In PowerShell from the project folder: `./scripts/install_to_claude.ps1`
	- Fully restart Claude Desktop afterwards.
	- For ChatGPT desktop with MCP: `./scripts/install_to_chatgpt.ps1` then restart the ChatGPT app.
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

### Full analysis: normal vs fast

- full_analysis: Runs a comprehensive model analysis with sections for summary, relationships, best practices, M scan, and optionally BPA.
	- Parameters:
		- profile: "fast" | "balanced" | "deep" (default: balanced)
		- depth: "light" | "standard" | "deep" (default: standard)
		- include_bpa: boolean (default: true; ignored when profile=fast)
	- Fast profile returns only summary + relationships for a very quick overview.

- propose_analysis: Returns a small decision card offering:
	- Fast summary (profile=fast, depth=light, include_bpa=false)
	- Normal analysis (profile=balanced, depth=standard, include_bpa=true)
	Use this when the user asks “analyze the model” and wants a choice.

## Performance tools and cache

 
- decide_and_run: Give a goal plus an optional query or list of candidates; it will connect, decide whether to analyze or preview, or benchmark candidates when provided.
- Cache bypass: safe_run_dax and run_dax_query accept a bypass_cache flag to force a fresh execution and ignore the TTL LRU cache when needed.

Tip: For DMV queries using $SYSTEM.* with SELECTCOLUMNS, wrap the source in TOPN(...) first to materialize before projection.

### Diagnostics & helpers

- Log summary: `summarize_logs` reports counts of ERROR/WARNING/INFO and shows recent entries.
- Query history: `get_query_history` (and `clear_query_history`) exposes a rolling, lightweight history of executed queries for quick recall and debugging.
- Command timeout: `set_command_timeout(seconds: int)` lets you raise/lower the ADOMD command timeout per session when exploring heavy queries.
- Cache stats: `get_cache_stats` returns size, ttl, hits/misses, and whether the LRU TTL cache is enabled.
- Context memory: `set_context({ ... })` and `get_context(keys?: string[])` maintain lightweight session memory (e.g., default table/measure).
- Safety limits: `set_safety_limits({ max_rows_per_call })` clamps high-row requests; enforced in `run_dax_query` and `preview_table_data`.
 
- Performance baselines: `set_perf_baseline(name, query, runs?)`, `get_perf_baseline(name)`, `list_perf_baselines()`, `compare_perf_to_baseline(name, query?, runs?)`.
- Auto router: `auto_route` chooses preview vs performance analysis based on priority and context.
- M analysis: `analyze_m_practices` scans `$SYSTEM.TMSCHEMA_EXPRESSIONS` for common M issues (heuristics).
- Instance switching: `switch_instance(mode: next|prev|index, index?)` cycles between detected Power BI Desktop instances.

Tip: To bypass cache on an individual query, pass `bypass_cache: true` in `run_dax_query` or use performance analysis tools.

## Install, update, uninstall

- Installation steps, update notes, and cleanup are documented in INSTALL.md
	- Claude config: `./scripts/install_to_claude.ps1`
	- ChatGPT MCP config: `./scripts/install_to_chatgpt.ps1`

If you use ChatGPT desktop with MCP, run the installer script to generate the JSON you can paste under Settings > Tools > Developer.

## Notes on privacy & security

- All analysis is local. The MCP server communicates with the client over stdio (no TCP port is opened).
- Connections to Power BI Desktop use the local loopback (localhost/127.0.0.1) to the model's embedded Analysis Services. Nothing is exposed to the network by default.
- Logs are written to `logs/pbixray.log` for diagnostics (also accessible via the `get_recent_logs` tool).
- Claude conversations may be stored by Anthropic; avoid pasting sensitive data.

Developer note: IDEs may show warnings for clr imports (pythonnet) until runtime. On Windows with the included lib/dotnet DLLs, these resolve when the server runs.

### Standard error envelopes

All tools return consistent envelopes to simplify client handling:

- Not connected:
	- { "success": false, "error_type": "not_connected", "error": "Not connected to Power BI Desktop", "suggestions": ["detect_powerbi_desktop", "connect_to_powerbi"] }
- Manager unavailable (feature not initialized):
	- { "success": false, "error_type": "manager_unavailable", "error": "<manager> not available", "required_manager": "<manager>" }
- Unknown tool:
	- { "success": false, "error_type": "unknown_tool", "tool_name": "<name>" }
- Unexpected error:
	- { "success": false, "error_type": "unexpected_error", "tool_name": "<name>", "error": "<message>" }

On success, responses include minimal connection metadata when available: { "port": "<desktop-port>" }.

## Support

- If something doesn’t work: ensure Power BI Desktop has a model open, rerun detection, and reconnect. Check `logs/` if needed.
- For team distribution: use `./scripts/package_for_distribution.ps1` to create a zip you can share.

— Happy analyzing!
