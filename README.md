# MCP-PowerBi-Finvision Server (v2.4)

Analyze your Power BI Desktop model locally with an MCP server. Browse schema, inspect DAX and M, run SE/FE performance checks, export docs, and more — just by asking your AI client.

• Status: Production-ready with security hardening  • OS: Windows 10/11  • Last updated: 2025-10-09

## Who is this for?

- Power BI analysts who want instant, safe model introspection from Claude or ChatGPT
- Engineers who need fast diagnostics, exports, and best-practices checks

## Features at a glance

- Auto-detect and connect to Power BI Desktop
- List tables/columns/measures, preview data, inspect relationships and M
- Validate DAX, scan VertiPaq stats, analyze cardinality/encoding
- Detect unused objects, analyze dependencies and RLS coverage
- Export compact schema, TMSL/TMDL, relationship graph, docs
- **NEW v2.4:** Input validation, rate limiting, enhanced error context

## Security & Performance (v2.4)

- ✅ **Input sanitization** - Prevents DAX/M injection attacks
- ✅ **Rate limiting** - Protects Desktop from query overload (10 req/sec default)
- ✅ **Path validation** - Prevents directory traversal in exports
- ✅ **Cache management** - Bounded memory (100MB/1000 entries)
- ✅ **Enhanced errors** - Desktop version context & known issue detection
- ✅ **Tool timeouts** - Per-tool execution limits

## Requirements

- Windows 10/11 (64‑bit)
- Power BI Desktop (latest recommended)
- .NET Framework 4.7.2+
- An MCP-capable client: Claude Desktop or ChatGPT Desktop (with MCP)

## Quick start (Windows)

1) Place this folder somewhere stable, e.g. `C:\Tools\pbixray-mcp-server`.
2) **Install .NET assemblies** (for full features):
   ```powershell
   cd lib/dotnet
   ./install.ps1
   ```
3) Open Power BI Desktop with a .pbix loaded and wait ~10 seconds.
4) Connect your AI client:
   - Claude Desktop: run `./scripts/install_to_claude.ps1`, then fully restart Claude.
   - ChatGPT Desktop: run `./scripts/install_to_chatgpt.ps1`, then restart ChatGPT.
   - Prefer no scripts? See "Manual install (Claude)" in INSTALL.md.
5) Optional check: run `./scripts/test_connection.ps1`.
6) In your AI client, try: "Detect Power BI Desktop instances" → "Connect to instance 0" → "List tables".

You're ready to explore your model.

## Common things to ask

- "Search for measures containing CALCULATE"
- "Analyze this DAX and break down SE vs FE"
- "Export a compact schema" or "Generate documentation"
- "Show me rate limit stats" (NEW)
- "Check cache performance" (NEW)

### Full analysis: fast vs normal

- full_analysis: summary, relationships, best practices, M scan, optional BPA
  - profile: fast | balanced | deep (default: balanced)
  - depth: light | standard | deep (default: standard)
  - include_bpa: true/false (ignored when profile=fast)

- propose_analysis: returns a small menu with fast vs normal options when a user asks to "analyze the model".

## Install and manage

- Full install/update/uninstall steps: see INSTALL.md
  - Scripted install (Claude/ChatGPT)
  - Manual Claude install by editing a JSON file (no scripts)
- Script catalog and recommendations: see docs/Scripts.md

## Docs and links

- Production Guide: `docs/Guide.md`
- Quickstart (friendly): `docs/PBIXRAY_Quickstart.md` (PDF/TXT variants included)
- Scripts catalog: `docs/Scripts.md`
- .NET Assembly Guide: `lib/dotnet/VERSIONS.md`

If you use GitHub Pages, `.github/workflows/docs.yml` publishes `docs/` on push to `main`.

## Tips, diagnostics, and safety

- Results are paged (page_size + next_token) for large outputs
- Use `get_recent_logs`, `summarize_logs`, and `get_server_info` for quick diagnostics
- **NEW:** Use `get_rate_limit_stats` and `get_cache_stats` for performance monitoring
- To force a fresh DAX run, set `bypass_cache: true` on run_dax
- For DMV queries with $SYSTEM.*, wrap sources in TOPN(...) before SELECTCOLUMNS to materialize

Privacy & security

- Everything runs locally over stdio; no ports exposed
- Connections use Desktop's embedded SSAS over localhost
- Input validation prevents injection attacks
- Rate limiting protects Desktop from overload
- Logs live in `logs/pbixray.log`

## Error envelope shape (for integrators)

- Not connected → `{ success: false, error_type: "not_connected", ... }`
- Manager unavailable → `{ success: false, error_type: "manager_unavailable", required_manager: "<n>" }`
- Unknown tool → `{ success: false, error_type: "unknown_tool", tool_name: "..." }`
- Unexpected error → `{ success: false, error_type: "unexpected_error", tool_name: "..." }`
- **NEW:** Rate limited → `{ success: false, error_type: "rate_limited", retry_after_seconds: X }`
- **NEW:** Validation error → `{ success: false, error_type: "validation_error", field: "..." }`

Successful responses include minimal connection metadata when available, like `{ port: "<desktop-port>" }`.

## Configuration

Edit `config/default_config.json` or create `config/local_config.json` for overrides.

New v2.4 settings:
- `rate_limiting.enabled` - Enable rate limiting (default: true)
- `rate_limiting.profile` - conservative | balanced | aggressive | development
- `security.enable_input_validation` - Validate inputs (default: true)
- `security.strict_m_validation` - Strict M expression validation (default: false)

## Support

- Ensure a .pbix is open, then detect → connect → run tools
- Verify .NET assemblies: `python scripts/verify_dotnet_assemblies.py`
- See INSTALL.md for troubleshooting and uninstall

## Changelog (v2.4)

### Added
- Input validation to prevent injection attacks
- Rate limiting (token bucket, per-tool limits)
- Enhanced error handler with Desktop version detection
- Cache manager with size limits and eviction metrics
- Tool-specific timeout configuration
- .NET assembly auto-installer and verifier
- Monitoring tools: get_rate_limit_stats, get_cache_stats, get_error_stats

### Security
- DAX/M expression validation
- Path traversal prevention
- Identifier sanitization
- Configurable rate limits

### Performance
- Bounded cache (100MB, 1000 entries, LRU eviction)
- Per-tool timeouts
- Cache hit rate tracking

— Happy analyzing!
