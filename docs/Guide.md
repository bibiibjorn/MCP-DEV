# MCP-PowerBi-Finvision – Production Guide

This guide helps analysts and engineers install, use, and automate the server reliably.

Last updated: 2025-10-09

## What the server does

- Connects to an open Power BI Desktop instance and inspects the model
- Lists tables/columns/measures and previews data safely (paginated)
- Searches objects and parses DAX/M/DMV metadata
- Runs Best Practice Analyzer (BPA) when enabled
- Analyzes relationships, VertiPaq stats, column usage and dependencies
- Exports compact schema, documentation, TMSL/TMDL, and relationship graphs

## Prerequisites

- Windows 10/11
- Power BI Desktop running with your model open
- .NET ADOMD/AMO libraries in `lib/dotnet` for advanced features (optional but recommended)
- Python 3.11+ in a virtual environment

## Install and run

1. Clone or extract the repo and create a venv
2. Install requirements
3. Start from an MCP client (Claude/ChatGPT) or run the server entrypoint directly

Common scripts are provided in `scripts/`. For quick validation, use the PowerShell helpers in README/INSTALL.

## Quick start tasks

- connection: detect powerbi desktop → connect to powerbi (model_index=0 is typical)
- Explore:
  - list: tables | list: columns | list: measures
  - describe: table | preview: table
  - search: text in measures | search: objects
- Analytics:
  - analysis: best practices (BPA)
  - usage: find unused objects
  - get: vertipaq stats | analysis: storage compression
- Export/Docs:
  - export: compact schema | export: columns with samples | export: relationships graph
  - export: tmsl | export: tmdl | get: model summary | docs: overview

Tips

- Large results are paginated with `page_size` + `next_token`
- Some Desktop builds hide DMVs; server falls back to TOM or client-side filtering when possible
- Use `get_recent_logs` and `get_server_info` for diagnostics

## Tool surface (friendly names)

Run `list_tools` in your MCP client to see exact schemas. Highlights:

- connection: detect powerbi desktop | connection: connect to powerbi
- list: tables | list: columns | list: measures | list: relationships | list: partitions | list: roles
- describe: table | preview: table | get: measure details
- search: text in measures | search: objects
- get: m expressions | get: data sources | get: column value distribution | get: column summary | get: vertipaq stats | get: model summary
- usage: analyze column | usage: find unused objects
- dependency: analyze measure | impact: measure
- validate: dax | validate: model integrity | security: validate rls
- analysis: performance (batch) | analysis: relationship cardinality | analysis: column cardinality | analysis: storage compression | analysis: best practices (BPA) | analysis: full model
- export: compact schema | export: columns with samples | export: tmsl | export: tmdl | export: relationships graph | export: schema (paged) | export: model overview

## Configuration

Edit `config/default_config.json` or provide `config/local_config.json`.

Notable flags:

- `features.enable_bpa` – enable Best Practice Analyzer (requires `core/bpa.json`)
- `server.tool_names_mode` – `friendly` (default) or `canonical`
- `performance.cache_ttl_seconds` – TTL for query cache
- `query.max_rows_preview` – cap for DMV preview queries

## Logs and health

- get_recent_logs – tail of `logs/pbixray.log`
- summarize_logs – counts of errors/warnings/info
- get_server_info – version, config, telemetry, error schema
- health_check – quick CPU/memory/disk snapshot (uses psutil if available)

## Known limitations

- Some DMVs vary across Desktop versions; fields may differ
- AMO SessionTrace needs proper .NET assemblies; without them, performance analysis is simplified
- Safety limits clamp very large result sets

## CI: Publish docs to GitHub Pages

`.github/workflows/docs.yml` publishes `docs/` to GitHub Pages on push to `main`.

To enable Pages: Settings → Pages → Build and deployment → Source = GitHub Actions.

## Contributing and support

- Use `scripts/test_connection.ps1` to validate your environment
- Open issues with a small repro and outputs from `get_server_info` and `get_recent_logs`

## Changelog snippets (server v2.3)

- Unified friendly tool naming with alias mapping
- Safer pagination and compact exports
- BPA lazy-init with profiles: fast/balanced/deep
- Expanded health, telemetry, and cache controls
- Removed deprecated, unused modules (see below)

## Deprecated/removed

Removed as unused or deprecated:

- `core/bpa_service.py` – BPA now via `core.bpa_analyzer.BPAAnalyzer`
- `core/dax_advanced_validator.py` – replaced by `core.dax_validator.DaxValidator`
- `core/measure_manager_enhanced.py` – superseded by `core.dax_injector.DAXInjector`

If you had custom imports pointing to these, switch to the indicated replacements.
