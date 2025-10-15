# MCP-PowerBi-Finvision

A production-ready Model Context Protocol (MCP) server for Power BI Desktop. Analyze your Power BI models locally with AI assistance - browse schema, inspect DAX and M code, run performance checks, export documentation, and more.

## Installation

### Option 1: One-Click Installation (Recommended)

1. **Download** the latest release: `mcp-powerbi-finvision-2.4.0.mcpb` (35 MB)
2. **Open Claude Desktop**
3. Click **Profile** → **Settings** → **Extensions**
4. Click **Install Extension**
5. Select the downloaded `.mcpb` file
6. **Restart** Claude Desktop when prompted

Done! The server is now installed with all dependencies bundled.

### Option 2: Development Installation

For developers who want to modify the server:

```powershell
# Clone the repository
git clone https://github.com/bibiibjorn/MCP-PowerBi-Finvision.git
cd MCP-PowerBi-Finvision

# Create virtual environment
py -3 -m venv venv
./venv/Scripts/Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Optional: Install .NET assemblies for enhanced features
cd lib/dotnet
./install.ps1
cd ../..

# Configure Claude Desktop
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "MCP-PowerBi-Finvision": {
      "command": "C:/path/to/venv/Scripts/python.exe",
      "args": ["C:/path/to/src/pbixray_server_enhanced.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

## Requirements

- **Windows 10/11** (64-bit)
- **Power BI Desktop** (latest recommended)
- **Python 3.10+** (for Option 2 or if bundled Python doesn't work)
- **.NET Framework 4.7.2+**
- **Claude Desktop** (latest version)

## Features

- Auto-detect and connect to Power BI Desktop instances
- Browse tables, columns, measures, and relationships
- Inspect DAX expressions and M queries
- Run performance analysis and VertiPaq stats
- Detect unused objects and analyze dependencies
- Export schema, TMSL/TMDL, and documentation
- Input validation and rate limiting for security
- Enhanced error context with Desktop version detection

## First Use

1. **Open Power BI Desktop** with a .pbix file loaded
2. **Wait 10-15 seconds** for the model to fully load
3. **In Claude Desktop**, ask:
   - "Detect Power BI Desktop instances"
   - "Connect to instance 0"
   - "List tables"

## Example Queries

Ask Claude:

- "Show me all measures that use CALCULATE"
- "Analyze this DAX expression for performance"
- "Export a compact schema of my model"
- "What tables are not being used?"
- "Generate documentation for my Power BI model"
- "Show me rate limit stats"

## Building the MCPB Package

For maintainers who want to create a new release:

```powershell
# Install mcpb CLI
npm install -g @anthropic-ai/mcpb

# Ensure venv has all dependencies
./venv/Scripts/Activate.ps1
pip install -r requirements.txt

# Build the package
mcpb pack . mcp-powerbi-finvision-2.4.0.mcpb

# The .mcpb file is now ready for distribution
```

## Troubleshooting

### Server Disconnects After Installation

Check Claude Desktop logs: `%APPDATA%\Claude\logs\mcp-server-Power BI Analysis MCP Server.log`

Common issues:
- Python not in PATH: Ensure `python --version` works
- Missing dependencies: The .mcpb should include everything, but verify Python 3.10+ is installed

### No Tools Appearing

1. Ensure extension is enabled in Settings → Extensions
2. Restart Claude Desktop
3. Start a new conversation

### Power BI Not Detected

1. Ensure Power BI Desktop is running
2. Ensure a .pbix file is open and **fully loaded** (wait 10-15 seconds)
3. Try running "Detect Power BI Desktop instances" again

## Architecture

The server uses:
- **MCP Protocol** for communication with Claude Desktop
- **Python.NET** for Power BI connectivity
- **ADOMD.NET** for querying Analysis Services
- **Bundled venv** with all dependencies (in .mcpb package)
- **Wrapper script** (`run_server.py`) to ensure dependencies are found

## Security & Performance

- Input sanitization prevents DAX/M injection attacks
- Rate limiting protects Desktop from query overload (10 req/sec default)
- Path validation prevents directory traversal in exports
- Bounded cache management (100MB/1000 entries)
- Enhanced error context with Desktop version detection
- Tool-specific timeout configuration

## Contributing

This is a production-ready release. For bugs or feature requests, please open an issue.

## License

MIT License - See LICENSE file for details

## Version

Current version: **2.4.0** (Production Ready)

Last updated: 2025-10-15
