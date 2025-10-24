# MCP-PowerBi-Finvision


Enables Claude and other AI assistants to analyze Power BI models locally—browse schema, inspect DAX and M code, run performance checks, export documentation, and more. Everything runs locally over stdio with no exposed ports.

---

## Features

### Model Analysis & Exploration
- **Auto-detect** running Power BI Desktop instances via netstat + process scanning
- **Browse schema** - tables, columns, measures, relationships with full metadata
- **Inspect code** - DAX expressions, M/Power Query formulas
- **Dependency analysis** - measure dependencies, unused objects detection
- **Interactive HTML explorer** with D3.js visualization and full search

### Performance & Optimization
- **DAX query execution** with Storage Engine / Formula Engine breakdown
- **Performance profiling** - cardinality checks, storage compression analysis
- **Query benchmarking** - compare multiple DAX variants, find the fastest
- **Cache management** - TTL-based caching with configurable policies

### Best Practices & Quality
- **Best Practice Analyzer (BPA)** - 120+ default rules, 150+ comprehensive rules
- **M query practices** - scan Power Query for anti-patterns
- **Model validation** - integrity checks, naming conventions
- **DAX quality metrics** - complexity analysis, pattern detection

### Documentation & Export
- **Multiple formats** - JSON, Excel (XLSX), Word (DOCX), PDF
- **TMSL/TMDL export** - model schema in native formats
- **Interactive HTML reports** - dependency explorer, relationship graphs
- **Model comparison** - diff two Power BI models with interactive HTML report
- **PBIP support** - analyze modern Power BI project format (offline, no Desktop required)

### Enterprise & Security
- **Input validation** - DAX/M injection prevention, path traversal protection
- **Rate limiting** - token bucket algorithm with per-tool limits
- **Comprehensive error handling** - user-friendly messages with fix suggestions
- **Timeout protection** - per-tool timeouts (5s to 300s)
- **Audit logging** - structured logs with telemetry tracking

---

## Quick Start

### Prerequisites
- **Windows 10/11** (64-bit)
- **Python 3.10+**
- **Power BI Desktop** (for live model analysis)
- **.NET Framework 4.7.2+**

### Installation

#### Option 1: Install via Claude Desktop (Recommended)

1. Download the latest `.mcpb` package from [Releases](https://github.com/bibiibjorn/MCP-PowerBi-Finvision/releases)
2. Open Claude Desktop → Settings → MCP Servers
3. Click "Install from file"
4. Select the downloaded `.mcpb` file
5. Restart Claude Desktop

#### Option 2: Install from Source

```powershell
# Clone repository
git clone https://github.com/bibiibjorn/MCP-PowerBi-Finvision.git
cd MCP-PowerBi-Finvision

# Create virtual environment
py -3 -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Test server
python src/pbixray_server_enhanced.py
```

Configure in Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "Power BI Analysis MCP Server": {
      "command": "python",
      "args": [
        "C:/path/to/MCP-PowerBi-Finvision/run_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### Usage

1. **Open Power BI Desktop** with a `.pbix` or `.pbip` file
2. **Wait 10-15 seconds** for the model to load
3. **In Claude Desktop**, ask:
   - "Detect Power BI instances"
   - "Connect to the first instance"
   - "Show me all measures"
   - "Run a full analysis of the model"
   - "What are the performance bottlenecks?"

---

## Available Tools (20+)

| Category | Tool | Description |
|----------|------|-------------|
| **Connection** | `detect_pbi_instances` | Detect running Power BI Desktop instances |
| | `connect_to_instance` | Connect to a specific instance |
| **Schema** | `list_tables` | List all tables in the model |
| | `list_columns` | List columns for a specific table |
| | `list_measures` | List all measures with metadata |
| | `get_measure_details` | Get detailed measure information |
| | `get_relationships` | Get all relationships |
| **DAX** | `run_dax` | Execute DAX queries |
| | `validate_dax` | Validate DAX syntax |
| | `analyze_dax` | Performance analysis with SE/FE breakdown |
| **M/Power Query** | `get_m_expressions` | Get M expressions for tables |
| **Analysis** | `full_analysis` | Comprehensive model analysis |
| | `analyze_best_practices_unified` | BPA + M practices scan |
| | `analyze_performance_unified` | Query perf + cardinality + storage |
| **Export** | `export_schema` | Export compact schema (JSON) |
| | `export_documentation` | Export comprehensive docs (JSON) |
| | `generate_model_documentation_word` | Generate Word report with graphs |
| | `export_model_explorer_html` | Interactive HTML explorer |
| | `compare_pbi_models` | Compare two models (TMDL diff) |
| **PBIP** | `analyze_pbip_repository` | Analyze PBIP project (offline) |
| **Diagnostics** | `get_server_info` | Server diagnostic information |
| | `get_cache_stats` | Cache performance metrics |
| | `get_rate_limit_stats` | Rate limiting statistics |

---

## Architecture

### High-Level Flow
```
Claude Desktop (MCP Client)
    ↓ stdio
MCP Server (pbixray_server_enhanced.py)
    ↓
Agent Policy Layer (orchestration + guardrails)
    ↓
Core Services (connection, query, performance, etc.)
    ↓
ADOMD.NET / TOM/AMO (.NET assemblies via pythonnet)
    ↓
Power BI Desktop (Analysis Services instance)
```

### Core Components

**Entry Point**: `run_server.py`
- Sets up Python path with bundled dependencies
- Executes main server module

**Main Server**: `src/pbixray_server_enhanced.py`
- Implements MCP protocol (stdio)
- Registers 20+ tools
- Delegates to agent policy layer

**Core Services** (`core/` directory, 46 modules, 28K LOC):
- `connection_manager.py` - Instance detection via netstat/tasklist
- `query_executor.py` - DAX execution with TOM/AMO fallback
- `agent_policy.py` - High-level orchestrations for AI agents
- `bpa_analyzer.py` - Best Practice Analyzer (120+ rules)
- `performance_analyzer.py` - Query performance profiling
- `dependency_analyzer.py` - Measure dependency trees
- `model_exporter.py` - Schema export, documentation generation
- `input_validator.py` - DAX/M injection prevention
- `rate_limiter.py` - Request rate limiting (token bucket)
- `cache_manager.py` - TTL-based LRU cache
- `error_handler.py` - Centralized error handling

**PBIP Support**:
- `pbip_project_scanner.py` - Scan PBIP repositories
- `pbip_model_analyzer.py` - Parse TMDL model files
- `pbip_report_analyzer.py` - Parse PBIR report files
- `pbip_dependency_engine.py` - Cross-model dependency analysis
- `pbip_enhanced_analyzer.py` - Quality metrics, lineage tracking
- `pbip_html_generator.py` - Interactive HTML dashboard

### Key Design Patterns

**Fallback Architecture**:
- Primary: DMV queries (`INFO.TABLES()`, `INFO.COLUMNS()`)
- Secondary: TOM/AMO object model (when Desktop blocks DMV)
- Tertiary: Client-side filtering (when server-side fails)

**Policy Layer**: `agent_policy.py` provides high-level orchestrations:
- `ensure_connected()` - Auto-detect + connect
- `safe_run_dax()` - Validate + execute + profile
- `decide_and_run()` - Intent-based execution
- `analyze_best_practices_unified()` - BPA + M scan
- `analyze_performance_unified()` - Multi-faceted perf analysis

**Centralized State**: `connection_state.py` singleton:
- Holds active connection
- Lazy-initializes managers
- Thread-safe access

**Security Hardening**:
- Input validation (DAX injection, path traversal)
- Rate limiting (10 req/sec global, per-tool limits)
- Timeout enforcement (5s-300s per tool)
- Error sanitization (no info leakage)

---

## Configuration

### Default Configuration (`config/default_config.json`)

```json
{
  "server": {
    "log_level": "INFO",
    "log_file": "logs/pbixray.log",
    "default_timeout": 30
  },
  "performance": {
    "cache_ttl_seconds": 300,
    "max_cache_size_mb": 100,
    "max_rows_preview": 1000,
    "default_top_n": 1000
  },
  "detection": {
    "instance_cache_ttl_seconds": 60,
    "discovery_timeout_seconds": 5
  },
  "query": {
    "max_rows": 10000,
    "default_validation_level": "strict"
  },
  "logging": {
    "enable_file_logging": true,
    "max_file_size_mb": 10,
    "backup_count": 3
  },
  "features": {
    "enable_bpa": true,
    "enable_performance_analysis": true,
    "enable_bulk_operations": true
  },
  "bpa": {
    "max_rules": 120,
    "severity_at_least": "WARNING",
    "max_tables": 60,
    "max_seconds": 60,
    "per_rule_max_ms": 500,
    "adaptive_timeouts": true,
    "parallel_rules": 4
  },
  "rate_limiting": {
    "global_max_calls_per_second": 10,
    "global_burst_size": 20,
    "per_tool_limits": {
      "run_dax": 5,
      "analyze_model_bpa": 1,
      "full_analysis": 0.5
    }
  },
  "security": {
    "input_validation": {
      "max_dax_query_length": 50000,
      "max_identifier_length": 128,
      "max_path_length": 260
    },
    "allowed_export_extensions": [".json", ".xlsx", ".docx", ".pdf", ".html"]
  },
  "tool_timeouts": {
    "detect_pbi_instances": 5,
    "connect_to_instance": 10,
    "run_dax": 30,
    "analyze_dax": 60,
    "full_analysis": 180,
    "analyze_model_bpa": 300,
    "export_model_explorer_html": 120
  }
}
```

### Local Overrides (`config/local_config.json`)

Create this file (gitignored) to override defaults:

```json
{
  "bpa": {
    "max_seconds": 120
  },
  "rate_limiting": {
    "global_max_calls_per_second": 20
  }
}
```

---

## Development

### Setup Development Environment

```powershell
# Clone repository
git clone https://github.com/bibiibjorn/MCP-PowerBi-Finvision.git
cd MCP-PowerBi-Finvision

# Create virtual environment
py -3 -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies (including dev tools)
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov black mypy flake8 pre-commit

# Run type checker
mypy core/

# Run formatter
black core/ src/

# Run linter
flake8 core/ src/

# Run tests (when available)
pytest tests/ -v
```

### Building `.mcpb` Package

```powershell
# Run the packaging script
.\package.bat

# Package will be created in dist/
# dist/mcp-powerbi-finvision-2.7.1.mcpb
```

The packaging process:
1. Checks Python 3 availability
2. Creates/activates virtual environment
3. Installs all dependencies
4. Verifies `mcpb` CLI is installed
5. Validates `manifest.json` version matches
6. Creates `.mcpb` package (includes `venv/` for reproducible deployment)

**Note**: Packaging takes 3-5 minutes with no visible progress after "Manifest schema validation passes!" - this is normal, it's packaging 9000+ files.

### Project Structure

```
MCP-PowerBi-Finvision/
├── src/
│   └── pbixray_server_enhanced.py   # Main MCP server (3.8K LOC)
├── core/                             # Core services (46 files, 28K LOC)
│   ├── connection_manager.py         # Instance detection, ADOMD.NET connection
│   ├── query_executor.py             # DAX execution with TOM fallback
│   ├── agent_policy.py               # AI orchestration layer
│   ├── bpa_analyzer.py               # Best Practice Analyzer
│   ├── performance_analyzer.py       # DAX query profiling
│   ├── dependency_analyzer.py        # Measure dependency trees
│   ├── model_exporter.py             # Schema export, docs generation
│   ├── input_validator.py            # Security: injection prevention
│   ├── rate_limiter.py               # Security: rate limiting
│   ├── cache_manager.py              # Performance: TTL cache
│   ├── error_handler.py              # Error handling with suggestions
│   ├── pbip_*.py                     # PBIP project analysis (7 modules)
│   └── ... (34 more modules)
├── server/                           # Handler layer
│   ├── handlers/
│   │   ├── full_analysis.py          # Comprehensive model analysis
│   │   └── relationships_graph.py    # Relationship visualization
│   └── utils/
│       └── m_practices.py            # M/Power Query best practices
├── config/                           # Configuration files
│   ├── default_config.json           # Default configuration
│   ├── local_config.json             # Local overrides (gitignored)
│   ├── bpa_rules_default.json        # 50+ BPA rules
│   └── bpa_rules_comprehensive.json  # 150+ BPA rules
├── lib/
│   └── dotnet/                       # .NET assemblies (20 DLLs)
│       ├── Microsoft.AnalysisServices.AdomdClient.dll
│       ├── Microsoft.AnalysisServices.Tabular.dll
│       └── ... (TOM/AMO DLLs)
├── tests/                            # Test infrastructure (tests to be added)
├── dev/                              # Development scripts (not packaged)
├── docs/                             # User documentation
│   ├── PBIXRAY_Quickstart.md
│   └── PBIXRAY_Quickstart.pdf
├── venv/                             # Bundled virtual environment (~1.2 GB)
├── exports/                          # Runtime export directory
├── logs/                             # Runtime log directory
├── run_server.py                     # Production entry point
├── manifest.json                     # MCPB manifest
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project metadata, tool configs
├── package.bat                       # Packaging script
├── __version__.py                    # Version information
├── CLAUDE.md                         # Developer documentation
└── README.md                         # This file
```

---
## Security

### Input Validation

All user inputs are validated to prevent:
- **DAX injection** - Escapes single quotes, validates identifiers
- **M expression injection** - Detects file/web access, dangerous functions
- **Path traversal** - Validates export paths, extension whitelist

### Rate Limiting

Protects Power BI Desktop from query floods:
- **Global**: 10 calls/second, burst 20
- **Per-tool**: Configurable limits (e.g., `run_dax`: 5/sec, `full_analysis`: 0.5/sec)
- **Token bucket algorithm** with automatic replenishment

### Error Handling

Errors are sanitized to prevent information leakage:
- Type-specific handlers
- User-friendly suggestions
- No stack traces in production responses

### Logging & Audit

All requests are logged with:
- Timestamp, tool name, execution time
- Success/failure status
- Sanitized error messages
- Telemetry buffer (last 200 calls)

---

## Dependencies

### Python Packages (15 core + 6 dev)

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | >= 1.0.0 | MCP protocol |
| `pythonnet` | >= 3.0.3 | .NET interop (ADOMD/AMO/TOM) |
| `WMI` | >= 1.5.1 | Windows Management Instrumentation |
| `psutil` | >= 5.9.0 | Process utilities |
| `pbixray` | 0.1.0-0.2.0 | Power BI analysis toolkit |
| `requests` | >= 2.31.0 | HTTP client |
| `python-docx` | >= 0.8.11 | Word document generation |
| `openpyxl` | >= 3.1.0 | Excel file generation |
| `reportlab` | >= 4.0.0 | PDF generation |
| `matplotlib` | >= 3.8.0 | Chart generation |
| `networkx` | >= 3.2.0 | Graph analysis |
| `pillow` | >= 10.0.0 | Image processing |
| `orjson` | >= 3.9.0 | Fast JSON serialization |
| `tqdm` | >= 4.66.0 | Progress bars |
| `pywin32` | >= 306 | Windows APIs |

All dependencies are bundled in the `.mcpb` package for reproducible deployment.


---
## Acknowledgments

- Built on [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- Uses [pbixray](https://github.com/KasperOnGit/pbixray) for Power BI analysis
- Powered by Microsoft Analysis Services Management Objects (AMO/TOM)
- Inspired by the Power BI community and best practices from [sqlbi.com](https://sqlbi.com)
