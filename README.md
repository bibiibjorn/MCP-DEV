# MCP-PowerBi-Finvision

**Version 4.2.01** - Production-ready MCP server for comprehensive Power BI analysis

Enables Claude and other AI assistants to analyze Power BI models locally—browse schema, inspect DAX and M code, run performance checks, export documentation, edit TMDL, debug DAX context, and more. Everything runs locally over stdio with no exposed ports.

---

## Features

### Model Analysis & Exploration
- **Auto-detect** running Power BI Desktop instances via netstat + process scanning
- **Browse schema** - tables, columns, measures, relationships with full metadata
- **Inspect code** - DAX expressions, M/Power Query formulas
- **Dependency analysis** - measure dependencies, unused objects detection
- **Interactive HTML explorer** with D3.js visualization and full search
- **Table descriptions** - comprehensive table metadata with columns, measures, and relationships

### DAX Development & Debugging ⭐ NEW
- **DAX context analysis** - analyze context transitions and filter context flow
- **Visual filter context** - interactive visualization of filter propagation
- **Step-by-step debugging** - debug DAX expressions with detailed context insights
- **DAX validation** - syntax validation with detailed error messages
- **DAX reference parsing** - extract measure and column dependencies

### TMDL Editing & Management ⭐ NEW
- **TMDL validation** - syntax validation with linting and error reporting
- **Find & replace** - regex-supported search and replace across TMDL files
- **Bulk renaming** - rename objects with automatic reference updates
- **Script generation** - generate TMDL scripts from definitions
- **Semantic diff** - intelligent comparison of TMDL changes

### Model Operations ⭐ ENHANCED
- **Measure management** - create, update, delete single or bulk measures
- **Calculation groups** - list, create, and delete calculation groups
- **Partition management** - view and manage table partitions
- **RLS management** - list and manage Row-Level Security roles

### Performance & Optimization
- **Relationship cardinality analysis** - identify cardinality issues in relationships
- **Cache management** - TTL-based caching with configurable policies

### Best Practices & Quality
- **Best Practice Analyzer (BPA)** - 120+ default rules, 150+ comprehensive rules
- **M query practices** - scan Power Query for anti-patterns
- **Model validation** - integrity checks, naming conventions
- **DAX quality metrics** - complexity analysis, pattern detection

### Documentation & Export
- **Multiple formats** - JSON, Excel (XLSX), Word (DOCX), PDF
- **TMSL/TMDL export** - model schema in native formats (token-optimized: file-based exports)
- **Smart export modes** - compact preview (~1-2k tokens) or full export to file (~99% token reduction)
- **Interactive HTML reports** - dependency explorer, relationship graphs
- **Model comparison** - diff two Power BI models with interactive HTML report
- **PBIP support** - analyze modern Power BI project format (offline, no Desktop required)

### Enterprise & Security
- **Input validation** - DAX/M injection prevention, path traversal protection
- **Rate limiting** - token bucket algorithm with per-tool limits
- **Comprehensive error handling** - user-friendly messages with fix suggestions
- **Timeout protection** - per-tool timeouts (5s to 300s)
- **Audit logging** - structured logs with telemetry tracking
- **Token usage tracking** - monitor and manage token consumption

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

   **Basic Operations:**
   - "Detect Power BI instances"
   - "Connect to the first instance"
   - "Show me all measures"
   - "Describe the Sales table"

   **Analysis:**
   - "Run a full analysis of the model"
   - "What are the performance bottlenecks?"
   - "Analyze best practices"

   **DAX Development:**
   - "Debug this DAX measure: [Total Sales]"
   - "Show me the filter context flow for this measure"
   - "Analyze context transitions in this DAX expression"

   **TMDL Operations:**
   - "Validate TMDL syntax"
   - "Find and replace 'OldName' with 'NewName' in TMDL"
   - "Bulk rename all measures starting with 'old_'"

   **Model Operations:**
   - "Create a calculation group for time intelligence"
   - "List all RLS roles"
   - "Show table partitions"

---

## Available Tools (50+)

All tools are organized with numerical prefixes for easy discovery (01_ for Connection, 02_ for Schema, etc.)

| Category | Count | Key Tools |
|----------|-------|-----------|
| **01 - Connection** | 2 | Detect instances, connect to Power BI Desktop |
| **02 - Schema** | 8 | List/search tables, columns, measures, calculated columns |
| **03 - Query** | 8 | Run DAX, preview data, get distributions, M expressions |
| **04 - Model Operations** | 9 | Measures, calculation groups, partitions, RLS roles |
| **05 - Analysis** | 5 | Full analysis, best practices, performance, integrity |
| **06 - Dependencies** | 2 | Measure dependencies, impact analysis |
| **07 - Export** | 3 | Schema, TMSL, TMDL export |
| **08 - Documentation** | 3 | Word reports, HTML explorer, update docs |
| **09 - Comparison** | 3 | Model summary, prepare comparison, compare models |
| **10 - PBIP** | 1 | Offline PBIP repository analysis |
| **11 - TMDL** ⭐ NEW | 3 | Find/replace, bulk rename, script generation |
| **12 - DAX Context** ⭐ NEW | 2 | Context analysis, debugging |
| **13 - Help** | 1 | Comprehensive user guide |

### Highlighted Tools

**DAX Development:**
- `12_analyze_dax_context` - Analyze context transitions and row context
- `12_debug_dax_context` - Step-by-step DAX debugging with context details

**TMDL Management:**
- `11_tmdl_find_replace` - Find and replace with regex support
- `11_tmdl_bulk_rename` - Bulk rename with automatic reference updates
- `11_tmdl_generate_script` - Generate TMDL scripts from definitions

**Model Operations:**
- `04_list_calculation_groups` - List calculation groups
- `04_create_calculation_group` - Create new calculation groups
- `04_delete_calculation_group` - Delete calculation groups
- `04_list_partitions` - View table partitions
- `04_list_roles` - List RLS roles

**Analysis:**
- `05_full_analysis` - Comprehensive model analysis with BPA
- `05_analyze_best_practices` - BPA + M query practices
- `05_analyze_performance` - Performance analysis (queries/cardinality/storage)

**Schema:**
- `02_describe_table` - Comprehensive table description with columns, measures, relationships
- `02_search_objects` - Search across tables, columns, and measures
- `02_search_string` - Search in measure names and expressions

---

## Architecture

### High-Level Flow
```
Claude Desktop (MCP Client)
    ↓ stdio
MCP Server (pbixray_server_enhanced.py)
    ↓
Server Layer (dispatch, middleware, registry)
    ↓
Orchestration Layer (agents, policies, workflows)
    ↓
Core Services (50+ modules across 9 domains)
    ↓
ADOMD.NET / TOM/AMO (.NET assemblies via pythonnet)
    ↓
Power BI Desktop (Analysis Services instance)
```

### Core Components

**Entry Point**: `src/run_server.py`
- Sets up Python path with bundled dependencies
- Handles virtual environment integration
- Executes main server module

**Main Server**: `src/pbixray_server_enhanced.py`
- Implements MCP protocol (stdio)
- Registers 50+ tools with organized numbering
- Routes to server dispatch layer

**Server Layer** (`server/` directory):
- `dispatch.py` - Tool request routing
- `middleware.py` - Request/response processing
- `registry.py` - Tool registration and discovery
- `tool_schemas.py` - Tool schema definitions
- `handlers/` - Specialized request handlers
- `utils/` - Server utilities (M practices, etc.)

**Orchestration Layer** (`core/orchestration/`, ~40K total LOC):
- `agent_policy.py` - High-level AI orchestrations
- `query_policy.py` - Query execution policies
- `analysis_orchestrator.py` - Analysis workflows
- `connection_orchestrator.py` - Connection management
- `documentation_orchestrator.py` - Documentation generation
- `cache_orchestrator.py` - Cache coordination
- `pbip_orchestrator.py` - PBIP workflows
- `base_orchestrator.py` - Common orchestration patterns

**Core Services** (organized by domain):

**Analysis** (`core/analysis/`):
- Best Practice Analyzer (120+ rules)
- Performance analyzer
- Dependency analyzer
- Model validator
- Impact analyzer

**DAX** (`core/dax/`):
- `context_analyzer.py` - Context transition analysis
- `context_debugger.py` - Step-by-step DAX debugging
- `context_visualizer.py` - Filter context visualization
- `dax_parser.py` - DAX expression parsing
- `dax_validator.py` - DAX syntax validation
- `dax_reference_parser.py` - Dependency extraction

**TMDL** (`core/tmdl/`):
- `validator.py` - TMDL syntax validation
- `bulk_editor.py` - Find/replace and bulk operations
- `script_generator.py` - TMDL script generation
- `tmdl_parser.py` - TMDL file parsing
- `tmdl_semantic_diff.py` - Intelligent TMDL diffing
- `tmdl_exporter.py` - TMDL export functionality

**Model Operations** (`core/operations/`):
- `calculation_group_manager.py` - Calculation group CRUD
- `partition_manager.py` - Partition management
- `rls_manager.py` - RLS role management
- `bulk_operations.py` - Bulk measure operations

**Infrastructure** (`core/infrastructure/`):
- Connection management
- Query execution (ADOMD.NET + TOM fallback)
- Cache management (TTL-based LRU)
- Rate limiting (token bucket)
- Error handling
- Input validation

**Documentation** (`core/documentation/`):
- Word/Excel/PDF generation
- HTML interactive explorer
- Schema export
- Model comparison

**PBIP** (`core/pbip/`):
- PBIP project scanning
- TMDL model analysis
- PBIR report parsing
- Dependency analysis
- Quality metrics
- HTML dashboard generation

**Performance** (`core/performance/`):
- Query profiling (SE/FE breakdown)
- Cardinality analysis
- VertiPaq statistics
- Storage optimization

**Validation** (`core/validation/`):
- Input validation (DAX/M injection prevention)
- Path validation (traversal protection)
- Model integrity checks

### Key Design Patterns

**Layered Architecture** (v4.0+):
- Server Layer: Request routing, middleware, tool registry
- Orchestration Layer: Workflow coordination, policy enforcement
- Core Services: Domain-specific business logic
- Infrastructure: Cross-cutting concerns (cache, logging, validation)

**Fallback Architecture**:
- Primary: DMV queries (`INFO.TABLES()`, `INFO.COLUMNS()`)
- Secondary: TOM/AMO object model (when Desktop blocks DMV)
- Tertiary: Client-side filtering (when server-side fails)

**Orchestration Patterns**: Specialized orchestrators for different workflows:
- `agent_policy.py` - AI agent orchestrations (ensure_connected, safe_run_dax)
- `query_policy.py` - Query execution policies
- `analysis_orchestrator.py` - Complex analysis workflows
- `connection_orchestrator.py` - Connection lifecycle management
- `documentation_orchestrator.py` - Documentation generation pipelines
- `cache_orchestrator.py` - Multi-level cache coordination

**Domain-Driven Design**: Services organized by domain:
- DAX domain: parsing, validation, context analysis, debugging
- TMDL domain: validation, editing, diffing, generation
- Operations domain: CRUD operations on model objects
- Analysis domain: BPA, performance, dependencies
- Documentation domain: export and reporting

**Tool Organization** (v4.0+): Numbered prefix system for discoverability:
- 01_ Connection, 02_ Schema, 03_ Query, 04_ Operations
- 05_ Analysis, 06_ Dependencies, 07_ Export, 08_ Documentation
- 09_ Comparison, 10_ PBIP, 11_ TMDL, 12_ DAX Context, 13_ Help

**Security Hardening**:
- Input validation (DAX injection, path traversal)
- Rate limiting (10 req/sec global, per-tool limits)
- Timeout enforcement (5s-300s per tool)
- Error sanitization (no info leakage)
- Token usage tracking and limits

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
# dist/mcp-powerbi-finvision-4.2.01.mcpb
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
│   ├── run_server.py                 # Production entry point with venv setup
│   └── pbixray_server_enhanced.py    # Main MCP server
├── core/                             # Core services (~40K LOC, v4.0 refactored)
│   ├── analysis/                     # Analysis domain
│   │   ├── bpa_analyzer.py           # Best Practice Analyzer (120+ rules)
│   │   ├── performance_analyzer.py   # Query performance profiling
│   │   ├── dependency_analyzer.py    # Measure dependency trees
│   │   └── impact_analyzer.py        # Impact analysis
│   ├── dax/                          # DAX domain ⭐ NEW
│   │   ├── context_analyzer.py       # Context transition analysis
│   │   ├── context_debugger.py       # Step-by-step debugging
│   │   ├── context_visualizer.py     # Filter context visualization
│   │   ├── dax_parser.py             # DAX expression parsing
│   │   ├── dax_validator.py          # Syntax validation
│   │   └── dax_reference_parser.py   # Dependency extraction
│   ├── tmdl/                         # TMDL domain ⭐ NEW
│   │   ├── validator.py              # TMDL validation & linting
│   │   ├── bulk_editor.py            # Find/replace, bulk rename
│   │   ├── script_generator.py       # Script generation
│   │   ├── tmdl_parser.py            # TMDL parsing
│   │   ├── tmdl_semantic_diff.py     # Intelligent diffing
│   │   └── tmdl_exporter.py          # TMDL export
│   ├── operations/                   # Model operations ⭐ ENHANCED
│   │   ├── calculation_group_manager.py  # Calc group CRUD
│   │   ├── partition_manager.py      # Partition management
│   │   ├── rls_manager.py            # RLS role management
│   │   └── bulk_operations.py        # Bulk measure ops
│   ├── orchestration/                # Orchestration layer ⭐ NEW
│   │   ├── agent_policy.py           # AI orchestrations
│   │   ├── query_policy.py           # Query policies
│   │   ├── analysis_orchestrator.py  # Analysis workflows
│   │   ├── connection_orchestrator.py # Connection lifecycle
│   │   ├── documentation_orchestrator.py # Doc pipelines
│   │   ├── cache_orchestrator.py     # Cache coordination
│   │   └── pbip_orchestrator.py      # PBIP workflows
│   ├── infrastructure/               # Infrastructure services
│   │   ├── connection_manager.py     # Instance detection
│   │   ├── query_executor.py         # DAX execution
│   │   ├── cache_manager.py          # TTL cache
│   │   ├── rate_limiter.py           # Rate limiting
│   │   └── error_handler.py          # Error handling
│   ├── documentation/                # Documentation domain
│   │   ├── word_generator.py         # Word reports
│   │   ├── html_generator.py         # HTML explorer
│   │   └── model_exporter.py         # Schema export
│   ├── pbip/                         # PBIP domain
│   │   ├── project_scanner.py        # PBIP scanning
│   │   ├── model_analyzer.py         # TMDL analysis
│   │   ├── report_analyzer.py        # PBIR parsing
│   │   └── dependency_engine.py      # Dependency analysis
│   ├── performance/                  # Performance domain
│   │   ├── query_profiler.py         # SE/FE breakdown
│   │   ├── cardinality_analyzer.py   # Cardinality checks
│   │   └── vertipaq_stats.py         # VertiPaq statistics
│   ├── validation/                   # Validation domain
│   │   ├── input_validator.py        # Injection prevention
│   │   ├── model_validator.py        # Integrity checks
│   │   └── path_validator.py         # Path traversal protection
│   ├── comparison/                   # Comparison domain
│   │   └── model_comparator.py       # Model diffing
│   ├── model/                        # Domain models
│   ├── config/                       # Configuration management
│   └── policies/                     # Policy definitions
├── server/                           # Server layer ⭐ NEW
│   ├── dispatch.py                   # Request routing
│   ├── middleware.py                 # Request/response processing
│   ├── registry.py                   # Tool registration
│   ├── tool_schemas.py               # Schema definitions
│   ├── handlers/                     # Request handlers
│   └── utils/                        # Server utilities
├── config/                           # Configuration files
│   ├── default_config.json           # Default configuration
│   ├── local_config.json             # Local overrides (gitignored)
│   ├── bpa_rules_default.json        # 120+ BPA rules
│   └── bpa_rules_comprehensive.json  # 150+ BPA rules
├── lib/
│   └── dotnet/                       # .NET assemblies (20 DLLs)
│       ├── Microsoft.AnalysisServices.AdomdClient.dll
│       ├── Microsoft.AnalysisServices.Tabular.dll
│       └── ... (TOM/AMO DLLs)
├── scripts/                          # Build and deployment scripts
├── docs/                             # User documentation
├── venv/                             # Bundled virtual environment (~1.2 GB)
├── exports/                          # Runtime export directory
├── logs/                             # Runtime log directory
├── manifest.json                     # MCPB manifest (v4.2.01)
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Project metadata
├── package.bat                       # Packaging script
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

## What's New in v4.x

### v4.2.01 (Latest)
- Refactoring and cleanup
- Enhanced stability and performance
- Improved token usage tracking

### v4.2
- Major codebase refactoring (~40K LOC)
- Enhanced modular architecture with domain-driven design
- Improved separation of concerns

### v4.0 - Major Release
**New DAX Context Analysis Tools** (Category 12):
- `12_analyze_dax_context` - Analyze context transitions and row context behavior
- `12_debug_dax_context` - Step-by-step DAX debugging with detailed context insights

**New TMDL Editing Tools** (Category 11):
- `11_tmdl_find_replace` - Find and replace across TMDL files with regex support
- `11_tmdl_bulk_rename` - Bulk rename objects with automatic reference updates
- `11_tmdl_generate_script` - Generate TMDL scripts from definitions

**Enhanced Model Operations** (Category 04):
- Calculation group management (list, create, delete)
- Partition management (list, inspect)
- RLS role management (list roles)
- Bulk measure operations (create, delete multiple measures)

**New Help System** (Category 13):
- `13_show_user_guide` - Comprehensive user guide accessible from Claude

**Architecture Improvements**:
- New server layer with dispatch, middleware, and registry
- Orchestration layer with specialized orchestrators
- Domain-driven design: 9 core domains (analysis, dax, tmdl, operations, etc.)
- Tool numbering system (01-13) for better organization
- Enhanced token usage tracking and limits
- Improved error handling with better context

**Enhanced Schema Tools**:
- `02_describe_table` - Comprehensive table descriptions
- `02_search_objects` - Search across all object types
- `02_search_string` - Search in measure expressions

**Code Growth**:
- From 28K LOC (v3.x) to ~40K LOC (v4.x)
- From 46 modules to 50+ modules
- From 20+ tools to 50+ tools

---
## Acknowledgments

- Built on [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- Uses [pbixray](https://github.com/KasperOnGit/pbixray) for Power BI analysis
- Powered by Microsoft Analysis Services Management Objects (AMO/TOM)
- Inspired by the Power BI community and best practices from [sqlbi.com](https://sqlbi.com)
