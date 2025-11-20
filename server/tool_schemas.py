"""
Tool Input Schemas for Bridged Tools
Defines proper input schemas with required parameters
"""

TOOL_SCHEMAS = {
    # Query & Preview (5 tools)
    'run_dax': {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "DAX query to execute (EVALUATE statement)"
            },
            "top_n": {
                "type": "integer",
                "description": "Limit number of rows returned (default: 100)",
                "default": 100
            },
            "mode": {
                "type": "string",
                "description": "Execution mode: 'auto' (smart choice), 'analyze' or 'profile' (with timing analysis), 'simple' (preview only)",
                "enum": ["auto", "analyze", "profile", "simple"],
                "default": "auto"
            }
        },
        "required": ["query"]
    },

    'get_column_value_distribution': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "column": {
                "type": "string",
                "description": "Column name"
            },
            "top_n": {
                "type": "integer",
                "description": "Number of top values (default: 10)",
                "default": 10
            }
        },
        "required": ["table", "column"]
    },

    'get_column_summary': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "column": {
                "type": "string",
                "description": "Column name"
            }
        },
        "required": ["table", "column"]
    },

    'validate_dax_query': {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "DAX query to validate"
            }
        },
        "required": ["query"]
    },

    # Data Sources (2 tools)
    'get_data_sources': {
        "type": "object",
        "properties": {},
        "required": []
    },

    'get_m_expressions': {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Max expressions to return"
            }
        },
        "required": []
    },

    # Relationships (1 tool)
    'list_relationships': {
        "type": "object",
        "properties": {
            "active_only": {
                "type": "boolean",
                "description": "Only return active relationships (default: false)",
                "default": False
            }
        },
        "required": []
    },

    # Measures (2 tools - Microsoft MCP operations)
    'list_measures': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Filter measures by table name (optional - if not provided, returns all measures)"
            },
            "page_size": {
                "type": "integer",
                "description": "Maximum number of measures to return (default: 100)",
                "default": 100
            },
            "next_token": {
                "type": "string",
                "description": "Pagination token for next page"
            }
        },
        "required": []
    },

    'get_measure_details': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name containing the measure"
            },
            "measure": {
                "type": "string",
                "description": "Measure name to retrieve"
            }
        },
        "required": ["table", "measure"]
    },

    # Model Management (7 tools - upsert_measure and delete_measure moved to model_operations_handler.py)

    'bulk_create_measures': {
        "type": "object",
        "properties": {
            "measures": {
                "type": "array",
                "description": "Array of measure definitions",
                "items": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "measure": {"type": "string"},
                        "expression": {"type": "string"}
                    }
                }
            }
        },
        "required": ["measures"]
    },

    'bulk_delete_measures': {
        "type": "object",
        "properties": {
            "measures": {
                "type": "array",
                "description": "Array of {table, measure} objects",
                "items": {
                    "type": "object"
                }
            }
        },
        "required": ["measures"]
    },

    'list_calculation_groups': {
        "type": "object",
        "properties": {},
        "required": []
    },

    'create_calculation_group': {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Calculation group name"
            },
            "items": {
                "type": "array",
                "description": "Calculation items with 'name' and 'expression' fields",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "expression": {"type": "string"}
                    }
                }
            },
            "description": {
                "type": "string",
                "description": "Optional description for the calculation group"
            },
            "precedence": {
                "type": "integer",
                "description": "Optional precedence level (auto-assigned if not specified). Must be unique across calculation groups."
            }
        },
        "required": ["name"]
    },

    'delete_calculation_group': {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Calculation group name"
            }
        },
        "required": ["name"]
    },

    'list_roles': {
        "type": "object",
        "properties": {},
        "required": []
    },

    # Analysis (2 tools)
    'simple_analysis': {
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": ["all", "tables", "stats", "measures", "measure", "columns", "relationships", "roles", "database", "calculation_groups"],
                "description": "Microsoft MCP operation. Use 'all' (recommended, 2-5s) for complete model analysis. Options: 'tables' (<500ms), 'stats' (<1s), 'measures', 'measure', 'columns', 'relationships', 'calculation_groups', 'roles', 'database'.",
                "default": "all"
            },
            "table": {
                "type": "string",
                "description": "Table name filter (for measures/columns/measure/partitions modes)"
            },
            "measure_name": {
                "type": "string",
                "description": "Measure name - required for mode='measure'"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum results to return - used by mode='measures' and mode='columns' (optional)"
            },
            "active_only": {
                "type": "boolean",
                "description": "Only return active relationships - used by mode='relationships' (default: false)",
                "default": False
            }
        },
        "required": []
    },

    'full_analysis': {
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "enum": ["all", "best_practices", "performance", "integrity"],
                "description": "Analysis scope: 'all' (default) runs all analyses, 'best_practices' focuses on BPA and M practices, 'performance' focuses on cardinality, 'integrity' focuses on validation",
                "default": "all"
            },
            "depth": {
                "type": "string",
                "enum": ["fast", "balanced", "deep"],
                "description": "Analysis depth: 'fast' (quick scan), 'balanced' (default, recommended), 'deep' (thorough but slower)",
                "default": "balanced"
            },
            "include_bpa": {
                "type": "boolean",
                "description": "Include Best Practice Analyzer (BPA) rules. Set to false if BPA dependencies not installed or to skip BPA checks",
                "default": True
            },
            "include_performance": {
                "type": "boolean",
                "description": "Include performance/cardinality analysis",
                "default": True
            },
            "include_integrity": {
                "type": "boolean",
                "description": "Include model integrity validation (relationships, duplicates, nulls, circular refs)",
                "default": True
            },
            "max_seconds": {
                "type": "integer",
                "description": "Optional maximum execution time in seconds (primarily affects BPA analysis)",
                "minimum": 5,
                "maximum": 300
            }
        },
        "required": []
    },

    # Dependencies (2 tools)
    'analyze_measure_dependencies': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "measure": {
                "type": "string",
                "description": "Measure name"
            }
        },
        "required": ["table", "measure"]
    },

    'get_measure_impact': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "measure": {
                "type": "string",
                "description": "Measure name"
            }
        },
        "required": ["table", "measure"]
    },

    # Export (2 tools)
    'export_tmdl': {
        "type": "object",
        "properties": {
            "output_dir": {
                "type": "string",
                "description": "Output directory path"
            }
        },
        "required": []
    },

    'get_live_model_schema': {
        "type": "object",
        "properties": {
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden objects (tables, columns, measures). Default: true",
                "default": True
            }
        },
        "required": []
    },

    # 
    # Documentation (3 tools)
    'generate_model_documentation_word': {
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Output Word file path"
            }
        },
        "required": []
    },

    'update_model_documentation_word': {
        "type": "object",
        "properties": {
            "input_path": {
                "type": "string",
                "description": "Existing Word document"
            },
            "output_path": {
                "type": "string",
                "description": "Output path"
            }
        },
        "required": ["input_path"]
    },

    'export_model_explorer_html': {
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Output HTML file path"
            }
        },
        "required": []
    },

    # Comparison (1 tool)
    'compare_pbi_models': {
        "type": "object",
        "properties": {
            "old_port": {
                "type": "integer",
                "description": "Port of OLD model instance (optional - if not provided, tool will detect instances and ask)"
            },
            "new_port": {
                "type": "integer",
                "description": "Port of NEW model instance (optional - if not provided, tool will detect instances and ask)"
            }
        },
        "required": []
    },

    # PBIP Offline Analysis (1 tool)
    'analyze_pbip_repository': {
        "type": "object",
        "properties": {
            "pbip_path": {
                "type": "string",
                "description": "Path to .pbip file or directory"
            },
            "output_path": {
                "type": "string",
                "description": "Optional output directory for HTML report (defaults to 'exports')"
            }
        },
        "required": ["pbip_path"]
    },

    # TMDL Automation (3 tools)
    'tmdl_find_replace': {
        "type": "object",
        "properties": {
            "tmdl_path": {
                "type": "string",
                "description": "Path to TMDL export folder (containing definition/ subfolder)"
            },
            "pattern": {
                "type": "string",
                "description": "Regex pattern to find"
            },
            "replacement": {
                "type": "string",
                "description": "Replacement text"
            },
            "dry_run": {
                "type": "boolean",
                "description": "Preview changes without applying them (default: true)",
                "default": True
            }
        },
        "required": ["tmdl_path", "pattern", "replacement"]
    },

    'tmdl_bulk_rename': {
        "type": "object",
        "properties": {
            "tmdl_path": {
                "type": "string",
                "description": "Path to TMDL export folder (containing definition/ subfolder)"
            },
            "renames": {
                "type": "array",
                "description": "Array of rename operations with 'old_name' and 'new_name' properties",
                "items": {
                    "type": "object",
                    "properties": {
                        "old_name": {"type": "string"},
                        "new_name": {"type": "string"}
                    },
                    "required": ["old_name", "new_name"]
                }
            },
            "dry_run": {
                "type": "boolean",
                "description": "Preview changes without applying them (default: true)",
                "default": True
            }
        },
        "required": ["tmdl_path", "renames"]
    },

    'tmdl_generate_script': {
        "type": "object",
        "properties": {
            "object_type": {
                "type": "string",
                "description": "Type of object to generate: 'table', 'measure', 'relationship', or 'calc_group'",
                "enum": ["table", "measure", "relationship", "calc_group"],
                "default": "table"
            },
            "definition": {
                "type": "object",
                "description": "Object definition (varies by object_type - see handler for details)"
            }
        },
        "required": ["definition"]
    },

    # DAX Intelligence (1 unified tool) - Tool 03: Validation + Analysis + Debugging
    'dax_intelligence': {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "DAX expression to analyze/debug (measure expression, calculated column, or table query)"
            },
            "analysis_mode": {
                "type": "string",
                "description": "Analysis mode: 'analyze' (context transition analysis), 'debug' (step-by-step debugging with friendly output), 'report' (comprehensive report with optimization + profiling). Default: 'analyze'",
                "enum": ["analyze", "debug", "report"],
                "default": "analyze"
            },
            "skip_validation": {
                "type": "boolean",
                "description": "Skip DAX syntax validation before analysis (default: false). Validation is performed by default.",
                "default": False
            },
            "output_format": {
                "type": "string",
                "description": "Output format for debug mode: 'friendly' (user-friendly with emojis), 'steps' (raw step data). Ignored for other modes. Default: 'friendly'",
                "enum": ["friendly", "steps"],
                "default": "friendly"
            },
            "include_optimization": {
                "type": "boolean",
                "description": "Include optimization suggestions (only for analysis_mode='report', default: true)",
                "default": True
            },
            "include_profiling": {
                "type": "boolean",
                "description": "Include performance profiling (only for analysis_mode='report', default: true)",
                "default": True
            },
            "breakpoints": {
                "type": "array",
                "description": "Optional character positions to pause at during debugging (advanced usage)",
                "items": {
                    "type": "integer"
                }
            }
        },
        "required": ["expression"]
    },

    # User Guide (1 tool)
    'show_user_guide': {
        "type": "object",
        "properties": {},
        "required": []
    },

    # Hybrid Analysis (2 tools) - Category 13
    'export_hybrid_analysis': {
        "type": "object",
        "properties": {
            "pbip_folder_path": {
                "type": "string",
                "description": "Path to .SemanticModel folder or parent PBIP folder (auto-detects .SemanticModel)"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory (default: '[ModelName]_analysis' next to PBIP)"
            },
            "connection_string": {
                "type": "string",
                "description": "Connection string (optional, auto-detects Power BI Desktop)"
            },
            "server": {
                "type": "string",
                "description": "Server name (optional, auto-detects)"
            },
            "database": {
                "type": "string",
                "description": "Database name (optional, auto-detects)"
            },
            "include_sample_data": {
                "type": "boolean",
                "default": True
            },
            "sample_rows": {
                "type": "integer",
                "description": "Sample rows per table (default: 1000, max: 5000)",
                "default": 1000
            },
            "sample_compression": {
                "type": "string",
                "enum": ["snappy", "zstd"],
                "default": "snappy"
            },
            "include_row_counts": {
                "type": "boolean",
                "default": True
            },
            "track_column_usage": {
                "type": "boolean",
                "default": True
            },
            "track_cardinality": {
                "type": "boolean",
                "default": True
            },
            "tmdl_strategy": {
                "type": "string",
                "enum": ["symlink", "copy"],
                "default": "symlink"
            },
            "progress_callback": {
                "type": "boolean",
                "default": False
            }
        },
        "required": ["pbip_folder_path"]
    },

    'analyze_hybrid_model': {
        "type": "object",
        "properties": {
            "analysis_path": {
                "type": "string",
                "description": "Path to exported analysis folder (e.g., 'c:\\path\\to\\Model_analysis'). Tool reads all files internally - do not use Read/Glob/Grep tools."
            },
            "operation": {
                "type": "string",
                "description": "Analysis operation (all file I/O internal): 'read_metadata' (full analysis with relationships), 'find_objects', 'get_object_definition' (DAX), 'analyze_dependencies', 'analyze_performance', 'get_sample_data', 'get_unused_columns', 'get_report_dependencies', 'smart_analyze' (NL query).",
                "enum": ["read_metadata", "find_objects", "get_object_definition", "analyze_dependencies", "analyze_performance", "get_sample_data", "get_unused_columns", "get_report_dependencies", "smart_analyze"],
                "default": "read_metadata"
            },
            "intent": {
                "type": "string",
                "description": "Natural language intent (only for operation='smart_analyze'). Example: 'Show me all measures in Time Intelligence folder'"
            },
            "object_filter": {
                "type": "object",
                "description": "Filter for objects",
                "properties": {
                    "object_type": {
                        "type": "string",
                        "description": "Object type: 'tables', 'measures', 'columns', 'relationships', 'roles'",
                        "enum": ["tables", "measures", "columns", "relationships", "roles"]
                    },
                    "name_pattern": {
                        "type": "string",
                        "description": "Regex pattern for name matching"
                    },
                    "table": {
                        "type": "string",
                        "description": "Filter by table name"
                    },
                    "folder": {
                        "type": "string",
                        "description": "Filter by display folder (for measures)"
                    },
                    "is_hidden": {
                        "type": "boolean",
                        "description": "Filter by visibility"
                    },
                    "complexity": {
                        "type": "string",
                        "description": "Filter by complexity: 'simple', 'medium', 'complex'",
                        "enum": ["simple", "medium", "complex"]
                    },
                    "object_name": {
                        "type": "string",
                        "description": "Object name or search pattern (e.g., 'base scenario' will fuzzy match 'PL-AMT-BASE Scenario'). For get_object_definition and analyze_dependencies."
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Table name (for get_sample_data operation - automatically reads and returns sample data from parquet file)"
                    }
                }
            },
            "format_type": {
                "type": "string",
                "description": "Output format: 'json' (default) or 'toon' (50% smaller, auto-applied for large responses)",
                "enum": ["json", "toon"],
                "default": "json"
            },
            "batch_size": {
                "type": "integer",
                "description": "Results per page (default: 50)",
                "default": 50
            },
            "batch_number": {
                "type": "integer",
                "description": "Page number (default: 0)",
                "default": 0
            },
            "priority": {
                "type": "string",
                "description": "Filter by priority: 'critical', 'high', 'medium', 'low', or null for all",
                "enum": ["critical", "high", "medium", "low"]
            },
            "detailed": {
                "type": "boolean",
                "description": "Include detailed analysis (default: false)",
                "default": False
            },
            "include_dependencies": {
                "type": "boolean",
                "description": "Include dependency info (default: false)",
                "default": False
            },
            "include_sample_data": {
                "type": "boolean",
                "description": "Include sample data (default: false)",
                "default": False
            }
        },
        "required": ["analysis_path", "operation"]
    },

    # Token Usage Tracking (1 tool)
    'get_token_usage': {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["json", "summary", "detailed"],
                "description": "Output format: 'json' (full statistics), 'summary' (brief overview), 'detailed' (comprehensive report). Default: 'json'",
                "default": "json"
            }
        },
        "required": []
    }
}
