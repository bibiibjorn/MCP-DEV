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
                "description": "Execution mode: 'auto' (smart choice), 'analyze' or 'profile' (with SE/FE timing), 'simple' (preview only)",
                "enum": ["auto", "analyze", "profile", "simple"],
                "default": "auto"
            }
        },
        "required": ["query"]
    },

    'preview_table_data': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name to preview"
            },
            "max_rows": {
                "type": "integer",
                "description": "Maximum rows to return (default: 10)",
                "default": 10
            }
        },
        "required": ["table"]
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

    'list_partitions': {
        "type": "object",
        "properties": {
            "table": {
                "type": "string",
                "description": "Optional table filter"
            }
        },
        "required": []
    },

    'list_roles': {
        "type": "object",
        "properties": {},
        "required": []
    },

    # Analysis (5 tools)
    'full_analysis': {
        "type": "object",
        "properties": {},
        "required": []
    },

    'analyze_best_practices_unified': {
        "type": "object",
        "properties": {
            "summary_only": {
                "type": "boolean",
                "description": "Return compact summary"
            }
        },
        "required": []
    },

    'analyze_performance_unified': {
        "type": "object",
        "properties": {
            "summary_only": {
                "type": "boolean",
                "description": "Return compact summary"
            }
        },
        "required": []
    },

    'validate_model_integrity': {
        "type": "object",
        "properties": {},
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

    # Export (3 tools)
    'export_tmsl': {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Optional output file path"
            }
        },
        "required": []
    },

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

    'export_model_schema': {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "description": "Section to export: 'compact' (lightweight schema without DAX expressions, ~1-2k tokens) or 'all' (full TMDL with all DAX, exports to file). Default: 'all'",
                "enum": ["compact", "all"],
                "default": "all"
            },
            "output_path": {
                "type": "string",
                "description": "Optional output file path. For section='all', file is auto-generated in exports/tmdl_exports/ if not specified. File can be read back using standard file operations."
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

    # Comparison (2 tools)
    'prepare_model_comparison': {
        "type": "object",
        "properties": {},
        "required": []
    },

    'compare_pbi_models': {
        "type": "object",
        "properties": {
            "old_port": {
                "type": "integer",
                "description": "Port of OLD model instance"
            },
            "new_port": {
                "type": "integer",
                "description": "Port of NEW model instance"
            }
        },
        "required": ["old_port", "new_port"]
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

    # TMDL Automation (6 tools)
    'validate_tmdl': {
        "type": "object",
        "properties": {
            "tmdl_path": {
                "type": "string",
                "description": "Path to TMDL file or directory"
            }
        },
        "required": ["tmdl_path"]
    },

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

    # DAX Context Analysis (3 tools)
    'analyze_dax_context': {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "DAX expression to analyze"
            }
        },
        "required": ["expression"]
    },

    'visualize_filter_context': {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "DAX expression"
            }
        },
        "required": ["expression"]
    },

    'debug_dax_context': {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "DAX expression to debug (can be a measure definition or any DAX formula)"
            },
            "format": {
                "type": "string",
                "description": "Output format: 'friendly' (default, user-friendly with emojis and explanations), 'steps' (raw step data), or 'report' (full analysis with optimization suggestions)",
                "enum": ["friendly", "steps", "report"],
                "default": "friendly"
            },
            "include_optimization": {
                "type": "boolean",
                "description": "Include optimization suggestions (only for 'report' format, default: true)",
                "default": True
            },
            "include_profiling": {
                "type": "boolean",
                "description": "Include performance profiling information (only for 'report' format, default: true)",
                "default": True
            },
            "breakpoints": {
                "type": "array",
                "description": "Optional list of character positions to pause at (advanced usage)",
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
}
