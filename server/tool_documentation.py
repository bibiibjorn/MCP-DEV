"""
Tool Documentation Reference System
Maps tool names to their detailed documentation.
This keeps tool schemas compact while providing full docs on-demand.
"""

TOOL_DOCS = {
    # Hybrid Analysis Tools
    'analyze_hybrid_model': {
        'doc_url': 'docs/HYBRID_ANALYSIS_GUIDE.md#operations',
        'summary': 'Analyze exported hybrid model data (TMDL + metadata + sample data)',
        'key_points': [
            'All file I/O is handled internally by the tool',
            'Returns complete data without needing additional Read/Glob/Grep tools',
            'Use operation="read_metadata" for comprehensive analysis with relationships',
            'Supports find_objects, get_object_definition (DAX), analyze_dependencies, and more'
        ],
        'operations': {
            'read_metadata': 'Full metadata + relationships list parsed from TMDL + expert analysis',
            'find_objects': 'Search all TMDL files internally',
            'get_object_definition': 'Get complete DAX expression from TMDL',
            'analyze_dependencies': 'Analyze object dependencies',
            'analyze_performance': 'Performance analysis',
            'get_sample_data': 'Read sample data from parquet files internally',
            'get_unused_columns': 'Read JSON metadata for unused columns',
            'get_report_dependencies': 'Read JSON metadata for report dependencies',
            'smart_analyze': 'Natural language query analysis'
        },
        'warnings': [
            'CRITICAL: Do not use Read, Glob, or Grep tools - this tool returns complete data',
            'All relationships are already parsed from TMDL and included in responses'
        ]
    },

    'export_hybrid_analysis': {
        'doc_url': 'docs/HYBRID_ANALYSIS_GUIDE.md#export',
        'summary': 'Export hybrid analysis combining TMDL files with live model metadata',
        'key_points': [
            'Combines PBIP TMDL files with live Power BI model metadata',
            'Exports sample data to parquet files',
            'Auto-detects Power BI Desktop connection if not specified',
            'Creates symlink or copy of TMDL files'
        ],
        'defaults': {
            'output_dir': '[ModelName]_analysis folder next to PBIP',
            'include_sample_data': True,
            'sample_rows': 1000,
            'sample_compression': 'snappy',
            'tmdl_strategy': 'symlink'
        }
    },

    # Analysis Tools
    'simple_analysis': {
        'doc_url': 'docs/AGENTIC_ROUTING_GUIDE.md#simple-analysis',
        'summary': 'Microsoft MCP operations for quick model analysis',
        'key_points': [
            'Recommended: Use mode="all" for complete model overview (2-5s)',
            'All operations are official Microsoft MCP server operations',
            'Fast operations: tables (<500ms), stats (<1s)'
        ],
        'operations': {
            'all': 'Run ALL 9 core Microsoft MCP operations + generate expert analysis (2-5s)',
            'database': 'List databases - Microsoft MCP Database List (ID, name, compatibility, size)',
            'stats': 'Fast model statistics - Microsoft MCP GetStats (<1s)',
            'tables': 'Ultra-fast table list - Microsoft MCP List (<500ms)',
            'measures': 'List measures - Microsoft MCP Measure List (optional: table filter, max_results)',
            'measure': 'Get measure details - Microsoft MCP Measure Get (requires: table, measure_name)',
            'columns': 'List columns - Microsoft MCP Column List (optional: table filter, max_results)',
            'relationships': 'List relationships - Microsoft MCP Relationship List (optional: active_only)',
            'calculation_groups': 'List calculation groups - Microsoft MCP ListGroups',
            'roles': 'List security roles - Microsoft MCP Role List'
        },
        'parameters': {
            'table': 'Used by: measures (filter), measure (required), columns (filter), partitions (filter)',
            'measure_name': 'Required for mode=measure',
            'max_results': 'Used by: measures, columns',
            'active_only': 'Used by: relationships (default: false)'
        }
    },

    'full_analysis': {
        'doc_url': 'docs/AGENTIC_ROUTING_GUIDE.md#full-analysis',
        'summary': 'Comprehensive model analysis with BPA, performance, and integrity checks',
        'key_points': [
            'Runs Best Practice Analyzer (BPA) rules',
            'Analyzes performance and cardinality',
            'Validates model integrity (relationships, duplicates, nulls, circular refs)',
            'Recommended: Use scope="all" and depth="balanced"'
        ],
        'scopes': {
            'all': 'Run all analyses (default)',
            'best_practices': 'Focus on BPA and M practices',
            'performance': 'Focus on cardinality',
            'integrity': 'Focus on validation'
        },
        'depths': {
            'fast': 'Quick scan',
            'balanced': 'Default, recommended',
            'deep': 'Thorough but slower'
        }
    },

    # DAX Intelligence
    'dax_intelligence': {
        'doc_url': 'docs/DAX_INTELLIGENCE_GUIDE.md',
        'summary': 'DAX validation, analysis, and debugging tool',
        'modes': {
            'analyze': 'Context transition analysis',
            'debug': 'Step-by-step debugging with friendly output',
            'report': 'Comprehensive report with optimization + profiling'
        },
        'key_points': [
            'Validates DAX syntax by default (skip with skip_validation=true)',
            'Debug mode provides friendly output with emojis or raw steps',
            'Report mode includes optimization suggestions and performance profiling'
        ]
    },

    # Query Tools
    'run_dax': {
        'summary': 'Execute DAX queries with performance analysis',
        'modes': {
            'auto': 'Smart choice (default)',
            'analyze': 'With timing analysis',
            'profile': 'With timing analysis',
            'simple': 'Preview only'
        },
        'defaults': {
            'top_n': 100,
            'mode': 'auto'
        }
    },

    # TMDL Tools
    'export_tmdl': {
        'summary': 'Export model to TMDL format',
        'key_points': [
            'Exports complete model to Tabular Model Definition Language',
            'Creates directory structure with definition files',
            'Compatible with tabular-editor and other TMDL tools'
        ]
    },

    'tmdl_find_replace': {
        'summary': 'Find and replace in TMDL files using regex',
        'key_points': [
            'Uses regex patterns for flexible matching',
            'Dry run mode by default (preview changes)',
            'Set dry_run=false to apply changes'
        ],
        'defaults': {
            'dry_run': True
        }
    },

    'tmdl_bulk_rename': {
        'summary': 'Bulk rename objects in TMDL files',
        'key_points': [
            'Renames tables, measures, columns across all TMDL files',
            'Dry run mode by default (preview changes)',
            'Updates all references automatically'
        ],
        'defaults': {
            'dry_run': True
        }
    }
}


def get_tool_documentation(tool_name: str) -> dict:
    """
    Get detailed documentation for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Dictionary with documentation details, or minimal info if not found
    """
    return TOOL_DOCS.get(tool_name, {
        'summary': 'Documentation not available',
        'key_points': []
    })


def get_operation_details(tool_name: str, operation: str) -> str:
    """
    Get details for a specific operation of a tool.

    Args:
        tool_name: Name of the tool
        operation: Name of the operation

    Returns:
        Description of the operation, or generic message if not found
    """
    tool_doc = TOOL_DOCS.get(tool_name, {})
    operations = tool_doc.get('operations', {})
    return operations.get(operation, f'Operation: {operation}')


def list_available_docs() -> list:
    """Get list of tools with available documentation."""
    return list(TOOL_DOCS.keys())
