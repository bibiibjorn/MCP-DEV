# MCP-PowerBi-Finvision Server

[![Version](https://img.shields.io/badge/version-2.4.0-blue.svg)](https://github.com/yourusername/MCP-PowerBi-Finvision)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

A production-ready Model Context Protocol (MCP) server for Power BI Desktop. Analyze your models locally with AI assistance - browse schema, inspect DAX and M code, run performance checks, export documentation, and more.

**Status:** Production-ready with security hardening
**Platform:** Windows 10/11 (64-bit)
**Last updated:** 2025-10-13

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

## Quick Start

### One-Click Installation ⚡

1. **Extract to a stable location** (avoid paths with spaces)

   ```text
   Recommended: C:\Tools\MCP-PowerBi-Finvision
   ```

2. **Run the automated setup** - Right-click in the folder, select "Open PowerShell here":

   ```powershell
   .\setup.ps1
   ```

   The script automatically:
   - ✅ Checks Python installation
   - ✅ Creates virtual environment
   - ✅ Installs all dependencies
   - ✅ Optionally installs .NET assemblies
   - ✅ Configures your AI client

**Done!** The venv is created fresh on your machine with all dependencies.

### Manual Installation (Alternative)

<details>
<summary>Click here if you prefer manual control</summary>

1. **Set up Python environment:**

   ```powershell
   py -3 -m venv venv
   ./venv/Scripts/Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Install .NET assemblies** (Optional):

   ```powershell
   cd lib/dotnet
   ./install.ps1
   ```

3. **Configure AI client:**

   ```powershell
   ./scripts/install_to_claude.ps1
   ```

   For ChatGPT Desktop, see [INSTALL.md](INSTALL.md)

</details>

### First Use

1. Open Power BI Desktop with a .pbix file loaded
2. Wait ~10-15 seconds for the model to fully load
3. In your AI client, ask:
   - "Detect Power BI Desktop instances"
   - "Connect to instance 0"
   - "List tables"

**You're ready to analyze your model!**

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

## Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Simple installation guide with automated setup script ⭐ Start here!
- **[INSTALL.md](INSTALL.md)** - Manual installation and troubleshooting details
- **[docs/Scripts.md](docs/Scripts.md)** - Script catalog and recommendations

## Additional Resources

- **Quickstart guide:** [docs/PBIXRAY_Quickstart.md](docs/PBIXRAY_Quickstart.md)
- **.NET assemblies:** [lib/dotnet/README.md](lib/dotnet/README.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

GitHub Pages publishes `docs/` automatically on push to `main` (if configured).

## Tips, diagnostics, and safety

- Results are paged (page_size + next_token) for large outputs
- Use `get_recent_logs`, `summarize_logs`, and `get_server_info` for quick diagnostics
- **NEW:** Use `get_rate_limit_stats` and `get_cache_stats` for performance monitoring
- To force a fresh DAX run, set `bypass_cache: true` on run_dax
- For DMV queries with $SYSTEM.*, wrap sources in TOPN(...) before SELECTCOLUMNS to materialize

### Privacy & Security

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
- Verify .NET assemblies: `venv\\Scripts\\python.exe scripts\\verify_dotnet_assemblies.py`
- See INSTALL.md for troubleshooting and uninstall

## Changelog

### Version 2.4.0 (2025-10-13)

#### Added

- Input validation to prevent injection attacks
- Rate limiting (token bucket, per-tool limits)
- Enhanced error handler with Desktop version detection
- Cache manager with size limits and eviction metrics
- Tool-specific timeout configuration
- .NET assembly auto-installer and verifier
- Monitoring tools: get_rate_limit_stats, get_cache_stats, get_error_stats

#### Security

- DAX/M expression validation
- Path traversal prevention
- Identifier sanitization
- Configurable rate limits

#### Performance

- Bounded cache (100MB, 1000 entries, LRU eviction)
- Per-tool timeouts
- Cache hit rate tracking

— Happy analyzing!
