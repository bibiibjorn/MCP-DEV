# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MCP-PowerBi-Finvision** is a production-ready Model Context Protocol (MCP) server for Power BI Desktop. It enables AI-powered analysis of Power BI models locally - browsing schema, inspecting DAX and M code, running performance checks, exporting documentation, and more.

- **Version**: 2.7.0 (Year 1 Model Analysis Excellence - TMDL Comparison)
- **Platform**: Windows 10/11 only
- **Primary Language**: Python 3.10+
- **Distribution Format**: `.mcpb` package (bundled with dependencies)

## Development Setup

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10+
- Power BI Desktop (for testing)
- .NET Framework 4.7.2+

### Initial Setup
```powershell
# Create virtual environment
py -3 -m venv venv
./venv/Scripts/Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Optional: Install .NET assemblies for enhanced features
cd lib/dotnet
./install.ps1
cd ../..
```

### Running the Server (Development)
```powershell
# Activate virtual environment
./venv/Scripts/Activate.ps1

# Run server directly
python src/pbixray_server_enhanced.py

# Or use the wrapper script (mimics production)
python run_server.py
```

## Architecture

### Core Components

**Entry Point**: `run_server.py` is the production entry point that sets up the Python path and executes the main server module.

**Main Server**: `src/pbixray_server_enhanced.py` implements the MCP server protocol and tool handlers.

**Core Services** (in `core/` directory):
- `connection_manager.py`: Power BI Desktop instance detection and connection management via ADOMD.NET
- `query_executor.py`: DAX query execution with caching, error handling, and TOM/AMO fallback methods
- `config_manager.py`: Configuration management with default and local overrides (in `config/` directory)
- `agent_policy.py`: High-level orchestration layer for AI agents with safety guardrails
- `error_handler.py`: Centralized error handling with user-friendly suggestions
- `rate_limiter.py`: Request rate limiting to protect Desktop from query overload
- `cache_manager.py`: Query result caching with TTL and size limits
- `input_validator.py`: Input sanitization to prevent DAX/M injection attacks
- `tool_timeouts.py`: Per-tool timeout configuration

**Specialized Managers**:
- `model_exporter.py`: Schema export, documentation generation
- `performance_analyzer_v2.py`: DAX query performance analysis with accurate SE/FE breakdown via xEvents
- `xevent_trace_manager.py`: XMLA-based Extended Events tracing for authoritative timing data
- `performance_analyzer.py`: Legacy AMO SessionTrace analyzer (fallback only)
- `dependency_analyzer.py`: Measure dependency tree analysis
- `bpa_analyzer.py`: Best Practice Analyzer integration
- `dax_validator.py`: DAX syntax validation and pattern analysis
- `model_validator.py`: Model integrity validation

**Server Handlers** (in `server/` directory):
- `server/handlers/full_analysis.py`: Comprehensive model analysis orchestration
- `server/handlers/relationships_graph.py`: Relationship graph visualization
- `server/utils/m_practices.py`: M/Power Query best practices scanning

### Connection Flow

1. **Detection**: Uses `netstat` to find listening ports + `tasklist` to verify msmdsrv.exe processes
2. **Connection**: Establishes ADOMD.NET connection to Power BI Desktop Analysis Services instance
3. **Query Execution**: Uses DMV queries (via `INFO.*` functions) and optionally AMO/TOM for metadata
4. **Fallback Strategy**: Query executor tries DMV first, falls back to TOM when Desktop blocks certain queries

### Data Flow

```
MCP Client (Claude Desktop)
    ↓
MCP Protocol (stdio)
    ↓
pbixray_server_enhanced.py (tool handlers)
    ↓
agent_policy.py (orchestration + safety)
    ↓
connection_state.py (manager access)
    ↓
core managers (connection, query, performance, etc.)
    ↓
ADOMD.NET / TOM/AMO
    ↓
Power BI Desktop (Analysis Services)
```

### Key Design Patterns

**Fallback Architecture**: Query executor has multiple fallback paths:
- Primary: DMV queries via `INFO.TABLES()`, `INFO.COLUMNS()`, etc.
- Secondary: TOM/AMO object model when DMV is blocked (common in Desktop)
- Server-side filtering with client-side fallback when filters fail

**Centralized State**: `connection_state.py` holds the active connection and all initialized managers. Tools access managers through this singleton.

**Policy Layer**: `agent_policy.py` provides high-level orchestrations that combine multiple operations with safety checks, making it easier for AI agents to perform complex tasks in one call.

**Error Enrichment**: `error_handler.py` converts low-level .NET exceptions into actionable user guidance.

## Common Development Commands

### Testing
```powershell
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_connection.py

# Run with verbose output
pytest -v tests/
```

### Building MCPB Package
```powershell
# Install mcpb CLI (once)
npm install -g @anthropic-ai/mcpb

# Ensure dependencies are installed
./venv/Scripts/Activate.ps1
pip install -r requirements.txt

# Build the .mcpb package
mcpb pack . mcp-powerbi-finvision-2.4.0.mcpb

# The .mcpb file is now ready for distribution
```

### Configuration
- Default config: `config/default_config.json`
- Local overrides: `config/local_config.json` (gitignored)
- Config is loaded via `ConfigManager` and accessed via singleton `config` instance

## Important Implementation Notes

### Working with ADOMD.NET and TOM/AMO

Power BI Desktop uses Analysis Services (tabular model). Access is via:
- **ADOMD.NET**: For executing DAX queries and DMV queries
- **AMO/TOM**: For metadata access when DMV is restricted

DLLs are in `lib/dotnet/`. The server uses `pythonnet` (clr) to load these assemblies.

**Critical**: Desktop often blocks certain DMV queries ($SYSTEM.TMSCHEMA_*, DISCOVER_*). The query executor logs these as debug, not errors, and falls back to TOM methods automatically.

### Table ID vs Table Name Mapping

`INFO.MEASURES()` and `INFO.COLUMNS()` return `TableID` (numeric or GUID), not table names. The query executor maintains a mapping:
- `_ensure_table_mappings()`: Loads `INFO.TABLES()` once and builds bidirectional map
- `execute_info_query()`: Automatically converts TableID to Table for usability
- **Important**: Always check bracketed keys first (`[ID]`, `[Name]`) as Desktop returns these, then fall back to unbracketed

### Query Executor Caching

`OptimizedQueryExecutor` caches query results with TTL:
- Cache key: `(final_query, top_n)`
- Default TTL: 300 seconds (configurable via `performance.cache_ttl_seconds`)
- Cache stats tracked: hits, misses, bypassed
- Bypass cache with `bypass_cache=True` parameter

### Rate Limiting

`RateLimiter` protects Desktop from query floods:
- Default: 10 requests/second
- Configurable per-client or globally
- Returns 429-like error when exceeded

### Security Features

- **Input Validation**: `InputValidator` sanitizes all user-provided strings before DAX execution
- **Path Validation**: Export paths validated to prevent directory traversal
- **DAX Injection Prevention**: Escapes single quotes and validates identifiers
- **Timeout Enforcement**: Per-tool timeouts prevent runaway queries

## Adding New Tools

1. **Define tool in manifest.json**: Add to `tools` array with name and description
2. **Register handler in pbixray_server_enhanced.py**:
   ```python
   @server.list_tools()
   async def list_tools() -> list[Tool]:
       return [
           # ... existing tools
           Tool(
               name="your_new_tool",
               description="What it does",
               inputSchema={
                   "type": "object",
                   "properties": {
                       "param": {"type": "string"}
                   }
               }
           )
       ]
   ```
3. **Implement handler**:
   ```python
   @server.call_tool()
   async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
       if name == "your_new_tool":
           # Use agent_policy for orchestrated operations
           result = agent_policy.your_method(connection_state, **arguments)
           return [TextContent(type="text", text=json.dumps(result, indent=2))]
   ```

4. **Add orchestration to agent_policy.py** (recommended):
   - Keeps server handlers thin
   - Centralizes validation and error handling
   - Enables reuse across multiple tools

## File Organization

```
MCP-PowerBi-Finvision/
├── src/
│   └── pbixray_server_enhanced.py   # Main MCP server
├── core/                             # Core services
│   ├── connection_manager.py
│   ├── query_executor.py
│   ├── agent_policy.py              # AI orchestration layer
│   ├── error_handler.py
│   ├── config_manager.py
│   └── ... (other managers)
├── server/                           # Server handlers
│   ├── handlers/
│   │   ├── full_analysis.py
│   │   └── relationships_graph.py
│   └── utils/
│       └── m_practices.py
├── config/                           # Configuration files
│   ├── default_config.json
│   └── local_config.json (gitignored)
├── lib/
│   └── dotnet/                       # .NET assemblies
│       ├── Microsoft.AnalysisServices.AdomdClient.dll
│       └── ... (TOM/AMO DLLs)
├── tests/                            # Test files
├── exports/                          # Default export directory
├── run_server.py                     # Production entry point
├── manifest.json                     # MCPB manifest
└── requirements.txt                  # Python dependencies
```

## Debugging Tips

### Logs
- Server logs: `logs/pbixray.log` (if file logging succeeds)
- Claude Desktop logs: `%APPDATA%\Claude\logs\mcp-server-Power BI Analysis MCP Server.log`

### Common Issues
1. **"ADOMD.NET not available"**: DLLs not found or pythonnet not installed
2. **"No Power BI Desktop instances detected"**: Power BI not running or .pbix not loaded (wait 10-15s after opening)
3. **Empty results from DMV**: Desktop blocking query → server automatically falls back to TOM
4. **TableID mapping errors**: Check bracketed keys first (`[ID]`, `[Name]`) before unbracketed

### Testing Connection
```python
# In Python REPL with venv activated
from core.connection_manager import ConnectionManager
cm = ConnectionManager()
instances = cm.detect_instances()
print(instances)  # Should show detected ports
```

## Version History Note

This is a production-ready server (v2.4.0). Earlier versions (v1.x-v2.3) were development iterations. The architecture is now stable with:
- Modular core services
- Policy-based orchestration layer
- Comprehensive error handling
- TOM/AMO fallback support
- Security hardening (input validation, rate limiting, path validation)
