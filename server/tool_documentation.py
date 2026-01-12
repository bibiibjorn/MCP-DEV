"""
Tool Documentation Reference System
Maps tool names to their detailed documentation.
This keeps tool schemas compact while providing full docs on-demand.
"""

TOOL_DOCS = {
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

    # DAX Intelligence (Enhanced v4.0)
    'dax_intelligence': {
        'doc_url': 'docs/DAX_INTELLIGENCE_GUIDE.md',
        'summary': 'Advanced DAX validation, analysis, debugging, and optimization tool with VertiPaq integration and smart measure auto-detection',
        'version': '4.0.0 - Industry-standard analysis features with smart auto-detection',
        'smart_auto_detection': {
            'description': 'AUTOMATICALLY detects if you provided a measure name and fetches the DAX expression from the model',
            'supported_inputs': [
                'Measure name (e.g., "Total Revenue") - tool auto-fetches the expression',
                'Full DAX expression (e.g., "SUM(Sales[Amount])") - analyzes directly',
                'Measure name with spaces (e.g., "PL-AMT-BASE Scenario") - auto-fetched',
                'Complex DAX formula - analyzed directly'
            ],
            'workflow': 'Provide measure name → Tool auto-fetches DAX → Validates → Analyzes',
            'no_manual_steps': 'NO need to first call measure_operations to get the expression - just provide the measure name!'
        },
        'modes': {
            'all': 'DEFAULT MODE - Runs ALL analysis modes (analyze + debug + report) for comprehensive DAX intelligence',
            'analyze': 'Context transition analysis with anti-pattern detection and specific code improvements',
            'debug': 'Step-by-step debugging with friendly output showing context transitions',
            'report': 'Comprehensive enhanced report with 8 analysis modules (VertiPaq, call tree, calc groups, code rewriting, visual flow diagrams, and more)'
        },
        'usage_examples': {
            'simple_measure': "{'expression': 'Total Revenue', 'analysis_mode': 'analyze'} - Auto-fetches measure and analyzes",
            'dax_expression': "{'expression': 'CALCULATE(SUM(Sales[Amount]), Date[Year]=2024)', 'analysis_mode': 'report'}",
            'debug_measure': "{'expression': 'YTD Sales', 'analysis_mode': 'debug', 'output_format': 'friendly'}",
            'skip_validation': "{'expression': 'Total Revenue', 'analysis_mode': 'report', 'skip_validation': True}"
        },
        'new_features_v4': [
            'Smart Measure Auto-Detection - Automatically fetches measure expressions when measure name is provided',
            'VertiPaq Metrics Integration - Column cardinality analysis, memory footprint, data type optimization suggestions',
            'Call Tree Hierarchy - Hierarchical DAX breakdown with estimated iteration counts from actual model cardinality',
            'Calculation Group Analysis - Precedence conflict detection, performance impact assessment, best practice validation',
            'Advanced Code Rewriting - Actual DAX transformation (extracts repeated measures into variables, not just templates)',
            'SUMMARIZE vs SUMMARIZECOLUMNS Detection - Auto-detect and suggest 2-10x faster alternative',
            'Variable Optimization Scanner - Identifies repeated calculations with estimated savings percentage',
            'Visual Context Flow Diagrams - ASCII, HTML, and Mermaid diagrams showing context transitions',
            'Enhanced Iteration Analysis - Estimates actual row counts using VertiPaq cardinality data'
        ],
        'key_points': [
            'CRITICAL: Can accept EITHER a measure name OR a DAX expression - auto-detects which one you provided',
            'DEFAULT MODE is "all" - runs analyze + debug + report for comprehensive intelligence (can specify individual modes if needed)',
            'When measure name is provided, the tool automatically fetches the expression AND skips validation (already in model)',
            'Online research ENABLED - fetches optimization articles from SQLBI and other sources with specific recommendations',
            'Auto-skips validation for auto-fetched measures (they\'re already in the model and must be valid)',
            'Debug mode provides friendly output with emojis or raw steps',
            'Report mode now includes 8 comprehensive analysis sections',
            'VertiPaq integration requires connection to Power BI model',
            'Calculation group analysis only runs when calc groups are detected',
            'Code rewriter provides actual transformed DAX code, not just suggestions',
            '11 anti-pattern detectors with research-backed recommendations and SQLBI article references'
        ],
        'report_sections': {
            'always_included': [
                'Context Analysis - Transition detection and complexity scoring',
                'Anti-Pattern Detection - Known DAX performance issues',
                'Specific Improvements - Before/after code examples',
                'SUMMARIZE Pattern Detection - Upgrade suggestions',
                'Variable Optimization - Repeated calculation scanner',
                'Code Rewriting - Actual DAX transformations',
                'Visual Flow Diagram - ASCII visualization of context flow'
            ],
            'when_connected': [
                'VertiPaq Column Analysis - Cardinality and memory impact',
                'Call Tree Hierarchy - With estimated iterations from model data',
                'Calculation Group Analysis - Precedence and performance analysis'
            ]
        },
        'performance_metrics': {
            'cardinality_warnings': {
                'iterator_warning': '100,000+ rows',
                'iterator_critical': '1,000,000+ rows',
                'filter_warning': '500,000+ unique values'
            },
            'estimated_improvements': {
                'variable_extraction': '10-50% faster',
                'summarizecolumns': '2-10x faster',
                'iterator_to_column': '10x-100x faster for large tables'
            }
        }
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

    # TMDL Operations
    'tmdl_operations': {
        'summary': 'Unified TMDL operations for export, find/replace, bulk rename, and script generation',
        'key_points': [
            'Supports ALL TMDL operations: export, find_replace, bulk_rename, generate_script',
            'Export: Exports complete model to TMDL format',
            'Find/Replace: Find and replace in TMDL files using regex',
            'Bulk Rename: Rename objects across all TMDL files with reference updates',
            'Generate Script: Generate TMDL scripts from object definitions'
        ],
        'operations': {
            'export': 'Export full TMDL definition to file',
            'find_replace': 'Find and replace in TMDL files with regex',
            'bulk_rename': 'Bulk rename objects with reference updates',
            'generate_script': 'Generate TMDL script from definition'
        },
        'defaults': {
            'dry_run': True  # For find_replace and bulk_rename operations
        }
    },

    # Operations Tools
    'table_operations': {
        'summary': 'Complete CRUD operations for Power BI tables',
        'key_points': [
            'Supports ALL operations: list, describe, preview, create, update, delete, rename, refresh',
            'Create calculated tables with DAX expressions',
            'Update table properties (description, expression, hidden)',
            'Delete and rename tables',
            'Refresh table data'
        ],
        'operations': {
            'list': 'List all tables with counts',
            'describe': 'Get comprehensive table details (columns, measures, relationships)',
            'preview': 'Show sample data rows from table',
            'create': 'CREATE new table (data or calculated)',
            'update': 'UPDATE table properties',
            'delete': 'DELETE table',
            'rename': 'RENAME table',
            'refresh': 'REFRESH table data'
        },
        'examples': {
            'create_calculated': "{'operation': 'create', 'table_name': 'TopCustomers', 'expression': 'TOPN(100, Customer, [Revenue], DESC)'}",
            'update': "{'operation': 'update', 'table_name': 'Sales', 'description': 'Updated description', 'hidden': true}",
            'delete': "{'operation': 'delete', 'table_name': 'OldTable'}",
            'rename': "{'operation': 'rename', 'table_name': 'Sales', 'new_name': 'SalesData'}"
        }
    },

    'column_operations': {
        'summary': 'Complete CRUD operations for Power BI columns',
        'key_points': [
            'Supports ALL operations: list, get, statistics, distribution, create, update, delete, rename',
            'Create data columns or calculated columns with DAX',
            'Update column properties (expression, description, format, hidden)',
            'Get column statistics (distinct count, total count, blank count)',
            'Get value distribution (top N values with counts)',
            'Delete and rename columns'
        ],
        'operations': {
            'list': 'List columns (all/data/calculated)',
            'get': 'Get detailed column metadata',
            'statistics': 'Get column stats (distinct/total/blank counts)',
            'distribution': 'Get top N values with counts',
            'create': 'CREATE new column (data or calculated)',
            'update': 'UPDATE column properties',
            'delete': 'DELETE column',
            'rename': 'RENAME column'
        },
        'examples': {
            'create_data': "{'operation': 'create', 'table_name': 'Sales', 'column_name': 'NewColumn', 'data_type': 'String'}",
            'create_calculated': "{'operation': 'create', 'table_name': 'Sales', 'column_name': 'TotalAmount', 'expression': '[Quantity] * [Price]'}",
            'update': "{'operation': 'update', 'table_name': 'Sales', 'column_name': 'Amount', 'format_string': '$#,0.00'}",
            'delete': "{'operation': 'delete', 'table_name': 'Sales', 'column_name': 'OldColumn'}",
            'rename': "{'operation': 'rename', 'table_name': 'Sales', 'column_name': 'Amt', 'new_name': 'Amount'}"
        }
    },

    'measure_operations': {
        'summary': 'Complete CRUD operations for Power BI measures',
        'key_points': [
            'Supports ALL operations: list, get, create, update, delete, rename, move',
            'Create measures with DAX expressions',
            'Update measure properties (expression, description, format)',
            'Get measure details including DAX expression',
            'Delete, rename, and move measures between tables'
        ],
        'operations': {
            'list': 'List measure names (no DAX)',
            'get': 'Get measure details WITH DAX expression',
            'create': 'CREATE new measure',
            'update': 'UPDATE measure properties',
            'delete': 'DELETE measure',
            'rename': 'RENAME measure',
            'move': 'MOVE measure to different table'
        },
        'examples': {
            'create': "{'operation': 'create', 'table_name': 'Sales', 'measure_name': 'Total Revenue', 'expression': 'SUM(Sales[Amount])', 'format_string': '$#,0'}",
            'update': "{'operation': 'update', 'table_name': 'Sales', 'measure_name': 'Total Revenue', 'expression': 'SUMX(Sales, [Quantity] * [Price])'}",
            'delete': "{'operation': 'delete', 'table_name': 'Sales', 'measure_name': 'Old Measure'}",
            'rename': "{'operation': 'rename', 'table_name': 'Sales', 'measure_name': 'Rev', 'new_name': 'Revenue'}",
            'move': "{'operation': 'move', 'table_name': 'Sales', 'measure_name': 'Total Revenue', 'new_table': 'Measures'}"
        }
    },

    'relationship_operations': {
        'summary': 'Complete CRUD operations for Power BI relationships',
        'key_points': [
            'Supports ALL operations: list, get, find, create, update, delete, activate, deactivate',
            'Create relationships between tables',
            'Update relationship properties (cross-filtering, active/inactive)',
            'Find all relationships for a table',
            'Activate/deactivate relationships',
            'Delete relationships'
        ],
        'operations': {
            'list': 'List all relationships',
            'get': 'Get relationship details',
            'find': 'Find relationships for a table',
            'create': 'CREATE new relationship',
            'update': 'UPDATE relationship properties',
            'delete': 'DELETE relationship',
            'activate': 'ACTIVATE inactive relationship',
            'deactivate': 'DEACTIVATE active relationship'
        },
        'examples': {
            'create': "{'operation': 'create', 'from_table': 'Sales', 'from_column': 'CustomerID', 'to_table': 'Customer', 'to_column': 'ID', 'from_cardinality': 'Many', 'to_cardinality': 'One'}",
            'update': "{'operation': 'update', 'relationship_name': 'Sales-Customer', 'cross_filtering_behavior': 'BothDirections'}",
            'delete': "{'operation': 'delete', 'relationship_name': 'OldRelationship'}",
            'activate': "{'operation': 'activate', 'relationship_name': 'Sales-Product'}"
        }
    },

    'calculation_group_operations': {
        'summary': 'CRUD operations for Power BI calculation groups',
        'key_points': [
            'Supports operations: list, list_items, create, delete',
            'Create calculation groups with multiple items',
            'Each item has name, expression (DAX), and ordinal (sort order)',
            'Delete calculation groups'
        ],
        'operations': {
            'list': 'List all calculation groups',
            'list_items': 'List calculation items in a group',
            'create': 'CREATE new calculation group',
            'delete': 'DELETE calculation group'
        },
        'examples': {
            'create': "{'operation': 'create', 'group_name': 'Time Intelligence', 'items': [{'name': 'YTD', 'expression': 'TOTALYTD([Value], Calendar[Date])', 'ordinal': 1}]}",
            'delete': "{'operation': 'delete', 'group_name': 'Old Group'}"
        }
    },

    'role_operations': {
        'summary': 'RLS/OLS role operations for Power BI',
        'key_points': [
            'Currently supports: list operation',
            'RLS = Row-Level Security (filter data rows)',
            'OLS = Object-Level Security (hide objects)',
            'Additional CRUD operations (create, update, delete) coming soon'
        ],
        'operations': {
            'list': 'List all security roles'
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
