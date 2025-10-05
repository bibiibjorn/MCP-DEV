# PBIXRay MCP Server - Optimized Structure Guide

## Version 2.1.0 - Optimized Architecture

This guide documents the enhanced structure of the PBIXRay MCP Server, optimized based on best practices from the fabric-toolbox SemanticModelMCPServer.

## Directory Structure

```
pbixray-mcp-server/
├── __version__.py              # Version information (NEW)
├── requirements.txt            # Python dependencies
├── README.md                   # Main documentation
│
├── src/                        # Server implementation
│   └── pbixray_server_enhanced.py  # Main server file (legacy)
│
├── core/                       # Core services and utilities
│   ├── __init__.py
│   ├── bpa.json               # BPA rules configuration
│   ├── bpa_analyzer.py        # BPA analysis engine
│   └── bpa_service.py         # BPA service layer (NEW)
│
├── tools/                      # Tool modules
│   ├── __init__.py
│   └── bpa_tools.py           # BPA MCP tools (REFACTORED)
│
├── prompts/                    # MCP prompts (NEW)
│   ├── __init__.py
│   └── mcp_prompts.py         # Guided interaction prompts
│
├── lib/                        # External libraries
│   └── dotnet/                # .NET Analysis Services DLLs
│
├── docs/                       # Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── FAQ.md
│   └── STRUCTURE_GUIDE.md     # This file (NEW)
│
├── scripts/                    # Helper scripts
│   ├── install_to_claude.ps1
│   └── test_connection.ps1
│
└── venv/                       # Python virtual environment

## Key Improvements (v2.1.0)

### 1. Version Management (__version__.py)
**NEW**: Centralized version information
- Single source of truth for version numbers
- Easy to update and maintain
- Follows Python packaging best practices

```python
__version__ = "2.1.0"
__author__ = "PBIXRay Enhanced"
__description__ = "A Model Context Protocol server for Power BI Desktop analysis with BPA capabilities"
```

### 2. MCP Prompts Module (prompts/)
**NEW**: Organized guided interactions
- Separate module for all MCP prompts
- 40+ pre-built prompts for common tasks
- Categorized by functionality:
  - Detection & Connection
  - Model Exploration
  - DAX Analysis
  - Performance Analysis
  - Best Practice Analyzer
  - Data Exploration
  - Troubleshooting

#### Example Prompts:
- `detect_powerbi_instances()` - Find running Power BI Desktop instances
- `run_bpa_analysis()` - Run Best Practice Analyzer
- `analyze_query_performance()` - Analyze DAX query performance
- `model_health_check()` - Comprehensive model health check

### 3. Enhanced BPA Service (core/bpa_service.py)
**NEW**: Robust service layer for BPA functionality
- Clean separation of concerns
- TMSL JSON preprocessing and cleaning
- Violation filtering by severity and category
- Comprehensive report generation
- Better error handling

#### Key Features:
- `analyze_model_from_tmsl()` - Analyze TMSL against BPA rules
- `get_violations_by_severity()` - Filter by ERROR/WARNING/INFO
- `get_violations_by_category()` - Filter by category
- `generate_bpa_report()` - Generate formatted reports
- `_clean_tmsl_json()` - Handle JSON formatting issues

### 4. Refactored BPA Tools (tools/bpa_tools.py)
**REFACTORED**: Cleaner, more maintainable tool definitions
- Simplified tool registration
- Better error handling
- Consistent JSON responses
- Uses BPA service layer

#### Available Tools:
- `analyze_tmsl_bpa` - Analyze TMSL definition
- `get_bpa_violations_by_severity` - Filter violations by severity
- `get_bpa_violations_by_category` - Filter violations by category
- `get_bpa_rules_summary` - Get rules summary
- `get_bpa_categories` - List available categories
- `generate_bpa_report` - Generate comprehensive reports

## How to Use the New Structure

### 1. Accessing Version Information
```python
from __version__ import __version__, __description__

print(f"PBIXRay MCP Server v{__version__}")
print(__description__)
```

### 2. Using Prompts in Claude
The new prompts make it easier to interact with the server:

```
You: "Can you detect my Power BI Desktop instances?"
Claude: [Uses detect_powerbi_instances() prompt]

You: "Can you run a Best Practice Analyzer scan?"
Claude: [Uses run_bpa_analysis() prompt]

You: "Can you perform a complete health check on this model?"
Claude: [Uses model_health_check() prompt]
```

### 3. Using BPA Service Programmatically
```python
from core.bpa_service import BPAService

# Initialize service
service = BPAService(server_directory)

# Analyze TMSL
result = service.analyze_model_from_tmsl(tmsl_json)

# Filter violations
errors = service.get_violations_by_severity('ERROR')
performance_issues = service.get_violations_by_category('Performance')

# Generate report
report = service.generate_bpa_report(tmsl_json, format_type='summary')
```

### 4. Registering BPA Tools
```python
from tools.bpa_tools import register_bpa_tools

# In your MCP server initialization
register_bpa_tools(mcp)
```

## Migration from v2.0 to v2.1

### What's Changed:
1. **No breaking changes** - All existing functionality preserved
2. **New files added** - __version__.py, prompts/, enhanced bpa_service.py
3. **BPA tools refactored** - Cleaner implementation, same interface

### For Users:
- All existing tools work the same way
- New prompts provide better guidance
- Enhanced error messages and logging
- No configuration changes needed

### For Developers:
- Import version from `__version__` instead of hardcoding
- Use BPAService for BPA functionality
- Register prompts using `register_prompts(mcp)`
- Follow new module structure for new tools

## Best Practices

### 1. Module Organization
- **core/** - Business logic and services
- **tools/** - MCP tool definitions
- **prompts/** - Guided interaction prompts
- Keep server.py focused on orchestration

### 2. Error Handling
- Use try-except blocks with specific error types
- Return JSON with `success`, `error`, and `error_type` fields
- Log errors with appropriate severity levels

### 3. BPA Analysis
- Always clean TMSL before parsing
- Use service layer for all BPA operations
- Filter violations by severity for prioritization
- Generate reports for comprehensive analysis

### 4. Adding New Tools
1. Create new file in `tools/` directory
2. Implement `register_<name>_tools(mcp)` function
3. Call registration in server initialization
4. Add corresponding prompts in `prompts/mcp_prompts.py`

## Future Enhancements

### Planned for v2.2:
- [ ] Additional tool modules (DAX tools, query tools)
- [ ] Enhanced prompt categorization
- [ ] Performance metrics service
- [ ] Model comparison tools

### Planned for v3.0:
- [ ] FastMCP migration
- [ ] Advanced caching strategies
- [ ] Real-time model monitoring
- [ ] Integration with external BPA rule sources

## Comparison with Fabric-Toolbox

### Adopted from SemanticModelMCPServer:
✅ `__version__.py` for version management
✅ `prompts/` module for organized prompts
✅ `core/bpa_service.py` service layer
✅ Refactored tool registration pattern
✅ Enhanced documentation structure

### PBIXRay-Specific Features:
- Power BI Desktop detection (not in Fabric server)
- Local model analysis (desktop vs service)
- Enhanced performance analysis with SE/FE breakdown
- DAX measure injection capabilities
- SessionTrace integration for detailed metrics

## Support

For questions or issues with the new structure:
1. Check this guide
2. Review docs/FAQ.md
3. Check existing issues on GitHub
4. Create new issue with [STRUCTURE] tag

## Version History

- **v2.1.0** (Current) - Optimized structure with prompts and enhanced BPA
- **v2.0.0** - Enhanced edition with BPA support
- **v1.0.0** - Initial release

---

**Updated:** 2025-10-05
**Maintainer:** PBIXRay Team
