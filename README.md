# MCP-PowerBi-Finvision

[![Version](https://img.shields.io/badge/version-6.0.3-blue.svg)](https://github.com/bibiibjorn/MCP-PowerBi-Finvision)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

A production-ready Model Context Protocol (MCP) server for Power BI Desktop analysis with DAX debugging, TMDL editing, and comprehensive model operations.

## Overview

MCP-PowerBi-Finvision enables AI-powered analysis of Power BI models with 45+ tools across 13 categories. It connects directly to running Power BI Desktop instances over stdio with no exposed ports, providing a secure and efficient way to analyze, debug, and modify Power BI semantic models.

## Key Features

### 🔌 Core Analysis
- Auto-detect and connect to Power BI Desktop instances
- Browse tables, columns, measures, and relationships
- Inspect DAX expressions and M queries
- Run comprehensive analysis with consolidated tools

### 🧠 DAX Development (Enhanced)
- **Unified DAX analysis**: syntax validation + context analysis in one tool
- Debug DAX with context transition analysis
- Visualize filter context flow through relationships
- Step-by-step DAX debugging with detailed insights
- Automatic syntax validation before analysis

### 🔄 Hybrid Analysis (v5.0+)
- Export TMDL + metadata + sample data packages
- BI Expert analysis with concrete recommendations
- Pattern-based fuzzy search
- Natural language query support
- Token-optimized TOON format

### 📝 TMDL Management
- Validate TMDL syntax with linting
- Find & replace with regex support
- Bulk rename with automatic reference updates
- Generate TMDL scripts

### ⚙️ Model Operations
- Create/manage calculation groups
- View/manage partitions and RLS roles
- Bulk measure operations (create, update, delete)
- Table and column operations

### 📊 Performance & Quality
- Performance analysis with DAX profiling and VertiPaq stats
- Best practices analysis (120+ BPA rules)
- Dependency analysis and impact assessment
- Export to Word, Excel, PDF, HTML, TMSL/TMDL

## Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Power BI Desktop**: Installed and running
- **.NET Framework**: 4.7.2 or higher
- **Python**: 3.8 or higher

## Installation

### Option 1: Install from Package (Recommended)

1. Download the latest `.mcpb` package from releases
2. Open Claude Desktop
3. Go to **Settings > MCP Servers**
4. Click **Install from file**
5. Select the downloaded `.mcpb` file

### Option 2: Install from Source

1. Clone the repository:
```bash
git clone https://github.com/bibiibjorn/MCP-PowerBi-Finvision.git
cd MCP-PowerBi-Finvision
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Claude Desktop to use the server by adding to your MCP config:
```json
{
  "mcpServers": {
    "mcp-powerbi-finvision": {
      "command": "python",
      "args": [
        "path/to/MCP-PowerBi-Finvision/src/run_server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

## Usage

### Quick Start

1. **Start Power BI Desktop** with a model open
2. **Open Claude Desktop** with the MCP server installed
3. **Detect Power BI instances**:
   ```
   Use tool: 01 Detect PBI Instances
   ```
4. **Connect to an instance**:
   ```
   Use tool: 01 Connect To Instance with the port from detection
   ```
5. **Start analyzing**!

### Example Workflows

#### Analyze a Measure
```
Use tool: 03 Standard DAX Analysis
Input: "Total Sales" (measure name)
```

#### Export Model Documentation
```
Use tool: 08 Generate Model Documentation
Output: Comprehensive Word document with model documentation
```

#### Debug DAX Context
```
Use tool: 03 Standard DAX Analysis
Input: Full DAX expression or measure name
Mode: report (detailed analysis with 8 sections)
```

## Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **01-Connection** | 2 tools | Detect and connect to Power BI instances |
| **02-Schema** | 8 tools | Browse model schema (tables, columns, measures) |
| **03-Query** | 8 tools | Execute queries and analyze data |
| **04-Model Operations** | 10 tools | Create/modify measures, calculation groups, roles |
| **05-Analysis** | 2 tools | Simple and comprehensive model analysis |
| **06-Dependencies** | 2 tools | Analyze measure dependencies and impact |
| **07-Export** | 2 tools | Export model schema and TMDL |
| **08-Documentation** | 2 tools | Generate and update documentation |
| **09-Comparison** | 1 tool | Compare open/live models |
| **10-PBIP** | 1 tool | Offline PBIP repository analysis |
| **11-TMDL** | 3 tools | TMDL find/replace, bulk rename, script generation |
| **12-Help** | 1 tool | User guide |
| **13-Hybrid** | 2 tools | Export and analyze full models with sample data |

## Development

### Building from Source

Run the package script:
```bash
build\package.bat
```

This will:
1. Check Python installation
2. Setup virtual environment
3. Install dependencies
4. Package the MCP server into `.mcpb` format

The output will be in `dist\mcp-powerbi-finvision-{version}.mcpb`

### Project Structure

```
MCP-PowerBi-Finvision/
├── core/                  # Core business logic
│   ├── dax/              # DAX analysis and debugging
│   ├── model/            # Model operations
│   ├── pbip/             # PBIP repository analysis
│   └── utilities/        # Shared utilities
├── server/               # MCP server handlers
│   └── handlers/         # Tool handlers
├── src/                  # Entry point
│   └── run_server.py     # Server startup
├── lib/                  # .NET libraries
├── build/                # Build scripts
├── manifest.json         # MCP manifest
└── requirements.txt      # Python dependencies
```

### Running Tests

```bash
pytest tests/
```

## Version History

### v6.0.3 (Current)
- Token optimization improvements
- Tool name refinements
- Enhanced stability

### v5.01
- Hybrid analysis features
- Token-optimized TOON format
- Pattern-based fuzzy search

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

**Finvision**
GitHub: [@bibiibjorn](https://github.com/bibiibjorn/MCP-PowerBi-Finvision)

## Support

For issues, questions, or feature requests, please open an issue on the [GitHub repository](https://github.com/bibiibjorn/MCP-PowerBi-Finvision/issues).

## Acknowledgments

- Built with [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [PBIXRay](https://github.com/Power-BI-Ray/pbixray) for model analysis
- Powered by [pythonnet](https://github.com/pythonnet/pythonnet) for .NET interop

---

**Note**: This tool runs entirely locally with no data sent to external servers. All analysis happens on your machine over stdio communication.
