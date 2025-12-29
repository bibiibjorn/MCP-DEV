"""
Tool Input Schemas for Bridged Tools
Defines proper input schemas with required parameters and examples.

Examples follow JSON Schema draft-06+ format and help Claude understand:
- Correct parameter formats and conventions
- When to use optional parameters
- Domain-specific patterns (DAX syntax, Power BI naming)
- Operation-specific parameter requirements
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
        "required": ["query"],
        "examples": [
            {
                "_description": "Simple table preview - get first 10 rows",
                "query": "EVALUATE TOPN(10, 'Sales')",
                "top_n": 10
            },
            {
                "_description": "Aggregation with grouping by category",
                "query": "EVALUATE SUMMARIZECOLUMNS('Product'[Category], \"TotalSales\", SUM('Sales'[Amount]))",
                "top_n": 100
            },
            {
                "_description": "Evaluate a measure with performance profiling",
                "query": "EVALUATE ROW(\"Result\", [Total Sales])",
                "mode": "profile"
            },
            {
                "_description": "Filter table with condition",
                "query": "EVALUATE FILTER('Customer', 'Customer'[Country] = \"USA\")",
                "top_n": 50
            },
            {
                "_description": "Time intelligence query",
                "query": "EVALUATE ADDCOLUMNS(VALUES('Date'[Year]), \"YTD Sales\", CALCULATE([Total Sales], DATESYTD('Date'[Date])))"
            },
            {
                "_description": "Cross-join for matrix analysis",
                "query": "EVALUATE SUMMARIZECOLUMNS('Product'[Category], 'Date'[Year], \"Sales\", [Total Sales])"
            }
        ]
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
        "required": ["table", "column"],
        "examples": [
            {
                "_description": "Top 10 countries by frequency",
                "table": "Customer",
                "column": "Country",
                "top_n": 10
            },
            {
                "_description": "Product category distribution",
                "table": "Product",
                "column": "Category"
            }
        ]
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
        "required": ["table", "column"],
        "examples": [
            {
                "_description": "Get statistics for CustomerID column",
                "table": "Customer",
                "column": "CustomerID"
            },
            {
                "_description": "Analyze Amount column for blanks",
                "table": "Sales",
                "column": "Amount"
            }
        ]
    },

    'validate_dax_query': {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "DAX query to validate"
            }
        },
        "required": ["query"],
        "examples": [
            {
                "_description": "Validate EVALUATE query",
                "query": "EVALUATE SUMMARIZE('Sales', 'Product'[Category])"
            },
            {
                "_description": "Validate measure expression",
                "query": "CALCULATE(SUM(Sales[Amount]), FILTER(ALL(Date), Date[Year] = 2024))"
            }
        ]
    },

    # Data Sources (2 tools)
    'get_data_sources': {
        "type": "object",
        "properties": {},
        "required": [],
        "examples": [
            {
                "_description": "List all data sources in the model"
            }
        ]
    },

    'get_m_expressions': {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Max expressions to return"
            }
        },
        "required": [],
        "examples": [
            {
                "_description": "Get all M expressions"
            },
            {
                "_description": "Get first 5 M expressions",
                "limit": 5
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "List all relationships"
            },
            {
                "_description": "List only active relationships",
                "active_only": True
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "List all measures in the model"
            },
            {
                "_description": "List measures in Sales table only",
                "table": "Sales"
            },
            {
                "_description": "Paginated list with 50 per page",
                "page_size": 50
            }
        ]
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
        "required": ["table", "measure"],
        "examples": [
            {
                "_description": "Get Total Revenue measure details with DAX",
                "table": "Sales",
                "measure": "Total Revenue"
            },
            {
                "_description": "Get Profit Margin measure",
                "table": "_Measures",
                "measure": "Profit Margin"
            }
        ]
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
        "required": ["measures"],
        "examples": [
            {
                "_description": "Create multiple sales measures at once",
                "measures": [
                    {"table": "Sales", "measure": "Total Sales", "expression": "SUM(Sales[Amount])"},
                    {"table": "Sales", "measure": "Avg Sales", "expression": "AVERAGE(Sales[Amount])"},
                    {"table": "Sales", "measure": "Sales Count", "expression": "COUNTROWS(Sales)"}
                ]
            }
        ]
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
        "required": ["measures"],
        "examples": [
            {
                "_description": "Delete multiple obsolete measures",
                "measures": [
                    {"table": "Sales", "measure": "Old Metric 1"},
                    {"table": "Sales", "measure": "Old Metric 2"},
                    {"table": "_Measures", "measure": "Deprecated KPI"}
                ]
            }
        ]
    },

    'list_calculation_groups': {
        "type": "object",
        "properties": {},
        "required": [],
        "examples": [
            {
                "_description": "List all calculation groups in the model"
            }
        ]
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
        "required": ["name"],
        "examples": [
            {
                "_description": "Create Time Intelligence calculation group",
                "name": "Time Intelligence",
                "items": [
                    {"name": "Current", "expression": "SELECTEDMEASURE()"},
                    {"name": "YTD", "expression": "CALCULATE(SELECTEDMEASURE(), DATESYTD('Date'[Date]))"},
                    {"name": "PY", "expression": "CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Date'[Date]))"},
                    {"name": "YoY %", "expression": "VAR _Current = SELECTEDMEASURE() VAR _PY = CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('Date'[Date])) RETURN DIVIDE(_Current - _PY, _PY)"}
                ],
                "description": "Standard time intelligence calculations",
                "precedence": 10
            },
            {
                "_description": "Create Currency conversion calculation group",
                "name": "Currency",
                "items": [
                    {"name": "Local", "expression": "SELECTEDMEASURE()"},
                    {"name": "USD", "expression": "SELECTEDMEASURE() * MAX('Exchange Rates'[ToUSD])"},
                    {"name": "EUR", "expression": "SELECTEDMEASURE() * MAX('Exchange Rates'[ToEUR])"}
                ]
            }
        ]
    },

    'delete_calculation_group': {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Calculation group name"
            }
        },
        "required": ["name"],
        "examples": [
            {
                "_description": "Delete obsolete calculation group",
                "name": "Old Time Intelligence"
            }
        ]
    },

    'list_roles': {
        "type": "object",
        "properties": {},
        "required": [],
        "examples": [
            {
                "_description": "List all RLS/OLS security roles"
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "Complete model analysis (recommended)",
                "mode": "all"
            },
            {
                "_description": "Quick table list",
                "mode": "tables"
            },
            {
                "_description": "Get specific measure details",
                "mode": "measure",
                "table": "Sales",
                "measure_name": "Total Revenue"
            },
            {
                "_description": "List columns in a specific table",
                "mode": "columns",
                "table": "Customer",
                "max_results": 50
            },
            {
                "_description": "List only active relationships",
                "mode": "relationships",
                "active_only": True
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "Complete analysis with all checks (recommended)",
                "scope": "all",
                "depth": "balanced"
            },
            {
                "_description": "Quick best practices scan only",
                "scope": "best_practices",
                "depth": "fast"
            },
            {
                "_description": "Deep performance analysis",
                "scope": "performance",
                "depth": "deep"
            },
            {
                "_description": "Skip BPA if dependencies missing",
                "scope": "all",
                "include_bpa": False
            },
            {
                "_description": "Time-limited analysis (max 30 seconds)",
                "scope": "all",
                "depth": "balanced",
                "max_seconds": 30
            }
        ]
    },

    # Dependencies (2 tools)
    'analyze_measure_dependencies': {
        "type": "object",
        "description": """Analyze measure dependencies with professional formatted output.

Returns TWO separate outputs:
1. formatted_output: Professional text analysis with summary, expression, and dependency breakdown
2. mermaid_diagram_output: Renderable Mermaid diagram showing dependency graph

Display BOTH outputs to the user - formatted_output first, then mermaid_diagram_output.""",
        "properties": {
            "table": {
                "type": "string",
                "description": "Table name containing the measure"
            },
            "measure": {
                "type": "string",
                "description": "Measure name to analyze"
            },
            "include_diagram": {
                "type": "boolean",
                "description": "Include a Mermaid diagram visualization (default: true)",
                "default": True
            }
        },
        "required": ["table", "measure"],
        "examples": [
            {
                "_description": "Analyze measure dependencies with visual diagram",
                "table": "Sales",
                "measure": "Profit Margin"
            },
            {
                "_description": "Get dependency analysis without diagram",
                "table": "_Measures",
                "measure": "YTD Revenue",
                "include_diagram": False
            }
        ]
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
        "required": ["table", "measure"],
        "examples": [
            {
                "_description": "See what depends on Total Sales (impact analysis)",
                "table": "Sales",
                "measure": "Total Sales"
            },
            {
                "_description": "Check impact before modifying a base measure",
                "table": "_Measures",
                "measure": "Base Revenue"
            }
        ]
    },

    # Export (1 tool)
    'get_live_model_schema': {
        "type": "object",
        "properties": {
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden objects (tables, columns, measures). Default: true",
                "default": True
            }
        },
        "required": [],
        "examples": [
            {
                "_description": "Export complete model schema including hidden objects"
            },
            {
                "_description": "Export only visible objects",
                "include_hidden": False
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "Generate documentation to default location"
            },
            {
                "_description": "Generate documentation to specific path",
                "output_path": "C:/docs/MyModel_Documentation.docx"
            }
        ]
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
        "required": ["input_path"],
        "examples": [
            {
                "_description": "Update existing documentation in place",
                "input_path": "C:/docs/MyModel_Documentation.docx"
            },
            {
                "_description": "Update and save to new file",
                "input_path": "C:/docs/MyModel_Documentation.docx",
                "output_path": "C:/docs/MyModel_Documentation_v2.docx"
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "Auto-detect instances and compare (interactive)"
            },
            {
                "_description": "Compare specific instances by port",
                "old_port": 52000,
                "new_port": 52100
            }
        ]
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
        "required": ["pbip_path"],
        "examples": [
            {
                "_description": "Analyze PBIP repository",
                "pbip_path": "C:/repos/MyModel/MyModel.pbip"
            },
            {
                "_description": "Analyze with custom output location",
                "pbip_path": "C:/repos/MyModel/MyModel.pbip",
                "output_path": "C:/reports/pbip_analysis"
            },
            {
                "_description": "Analyze SemanticModel folder directly",
                "pbip_path": "C:/repos/MyModel/MyModel.SemanticModel"
            }
        ]
    },

    # TMDL Automation - Now handled by unified tmdl_operations handler (schema embedded in handler)

    # DAX Intelligence (1 unified tool) - Tool 03: Validation + Analysis + Debugging
    'dax_intelligence': {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "DAX expression OR measure name. MEASURE LOOKUP FIRST: When a measure name is provided, the tool FIRST finds and verifies the correct measure before running analysis. This ensures the right measure is always analyzed. Examples: 'amount in selected currency' (finds exact match or suggests similar), 'CALCULATE(SUM(...))' (direct DAX expression)"
            },
            "analysis_mode": {
                "type": "string",
                "description": "Analysis mode: 'all' (runs ALL modes: analyze + debug + report), 'analyze' (context transition analysis with anti-patterns and improvements), 'debug' (step-by-step debugging with friendly output), 'report' (comprehensive report with 8 analysis sections including VertiPaq metrics, call tree, optimization suggestions). Default: 'all'",
                "enum": ["all", "analyze", "debug", "report"],
                "default": "all"
            },
            "skip_validation": {
                "type": "boolean",
                "description": "Skip DAX syntax validation before analysis (default: false). Set to true only when you know the syntax is valid and want to perform static analysis without execution.",
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
        "required": ["expression"],
        "examples": [
            {
                "_description": "Analyze measure by name (auto-fetches DAX from model)",
                "expression": "Total Revenue"
            },
            {
                "_description": "Analyze measure with fuzzy name matching",
                "expression": "profit margin"
            },
            {
                "_description": "Full analysis of DAX expression (all modes)",
                "expression": "CALCULATE(SUM(Sales[Amount]), FILTER(ALL(Date), Date[Year] = 2024))",
                "analysis_mode": "all"
            },
            {
                "_description": "Context transition analysis only",
                "expression": "SUMX(FILTER(Sales, Sales[IsActive]), [Unit Price] * Sales[Quantity])",
                "analysis_mode": "analyze"
            },
            {
                "_description": "Step-by-step debugging with friendly output",
                "expression": "Profit Margin",
                "analysis_mode": "debug",
                "output_format": "friendly"
            },
            {
                "_description": "Debug with raw step data",
                "expression": "CALCULATE([Total Sales], SAMEPERIODLASTYEAR('Date'[Date]))",
                "analysis_mode": "debug",
                "output_format": "steps"
            },
            {
                "_description": "Comprehensive report with all optimizations",
                "expression": "VAR _Total = SUM(Sales[Amount]) VAR _Cost = SUM(Sales[Cost]) RETURN DIVIDE(_Total - _Cost, _Total)",
                "analysis_mode": "report",
                "include_optimization": True,
                "include_profiling": True
            },
            {
                "_description": "Analyze complex nested CALCULATE",
                "expression": "CALCULATE(CALCULATE([Base Measure], REMOVEFILTERS(Product)), Date[Year] = 2024)",
                "analysis_mode": "all"
            },
            {
                "_description": "Analyze iterator with context transition",
                "expression": "SUMX(ALL(Product[Category]), [Category Sales])",
                "analysis_mode": "analyze"
            }
        ]
    },

    # User Guide (1 tool)
    'show_user_guide': {
        "type": "object",
        "properties": {},
        "required": [],
        "examples": [
            {
                "_description": "Show the user guide"
            }
        ]
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
        "required": ["pbip_folder_path"],
        "examples": [
            {
                "_description": "Export with defaults (auto-detect Power BI Desktop)",
                "pbip_folder_path": "C:/repos/MyModel/MyModel.SemanticModel"
            },
            {
                "_description": "Export with custom output directory",
                "pbip_folder_path": "C:/repos/MyModel",
                "output_dir": "C:/analysis/MyModel_export"
            },
            {
                "_description": "Export with more sample data rows",
                "pbip_folder_path": "C:/repos/MyModel/MyModel.SemanticModel",
                "sample_rows": 5000,
                "include_sample_data": True
            },
            {
                "_description": "Export TMDL only (no sample data)",
                "pbip_folder_path": "C:/repos/MyModel",
                "include_sample_data": False
            },
            {
                "_description": "Export with copy strategy (no symlinks)",
                "pbip_folder_path": "C:/repos/MyModel",
                "tmdl_strategy": "copy"
            }
        ]
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
        "required": ["analysis_path", "operation"],
        "examples": [
            {
                "_description": "Read full metadata with relationships and expert analysis",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "read_metadata"
            },
            {
                "_description": "Find all measures in Time Intelligence folder",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "find_objects",
                "object_filter": {
                    "object_type": "measures",
                    "folder": "Time Intelligence"
                }
            },
            {
                "_description": "Find complex measures only",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "find_objects",
                "object_filter": {
                    "object_type": "measures",
                    "complexity": "complex"
                }
            },
            {
                "_description": "Get measure definition with fuzzy name matching",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "get_object_definition",
                "object_filter": {
                    "object_name": "total revenue",
                    "object_type": "measure"
                }
            },
            {
                "_description": "Analyze dependencies of a specific measure",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "analyze_dependencies",
                "object_filter": {
                    "object_name": "Profit Margin"
                }
            },
            {
                "_description": "Get sample data from Sales table (20 rows)",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "get_sample_data",
                "object_filter": {
                    "table_name": "Sales"
                },
                "batch_size": 20
            },
            {
                "_description": "Run performance analysis with high priority issues",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "analyze_performance",
                "priority": "high",
                "detailed": True
            },
            {
                "_description": "Get unused columns report",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "get_unused_columns"
            },
            {
                "_description": "Get report visual dependencies",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "get_report_dependencies"
            },
            {
                "_description": "Smart analyze with natural language",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "smart_analyze",
                "intent": "Show me all complex measures that use CALCULATE"
            },
            {
                "_description": "Find measures by regex pattern",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "find_objects",
                "object_filter": {
                    "object_type": "measures",
                    "name_pattern": "^YTD.*"
                }
            },
            {
                "_description": "Find hidden columns in a specific table",
                "analysis_path": "C:/models/MyModel_analysis",
                "operation": "find_objects",
                "object_filter": {
                    "object_type": "columns",
                    "table": "Sales",
                    "is_hidden": True
                }
            }
        ]
    },

    'generate_pbip_dependency_diagram': {
        "type": "object",
        "properties": {
            "pbip_folder_path": {
                "type": "string",
                "description": "Path to .SemanticModel folder or parent PBIP folder (auto-detects .SemanticModel). The tool will also look for .Report folder for visual dependencies."
            },
            "auto_open": {
                "type": "boolean",
                "description": "Automatically open the HTML diagram in browser (default: true)",
                "default": True
            },
            "output_path": {
                "type": "string",
                "description": "Optional custom output path for the HTML file. If not specified, saves to exports/pbip_dependency_diagram.html"
            },
            "main_item": {
                "type": "string",
                "description": "Optional specific item to select initially (e.g., 'TableName[MeasureName]' or 'TableName[ColumnName]'). If not specified, selects the first measure in the model. The HTML includes a sidebar with all measures, columns, and field parameters - click any item to view its dependencies."
            }
        },
        "required": ["pbip_folder_path"],
        "examples": [
            {
                "_description": "Generate dependency diagram for a PBIP project",
                "pbip_folder_path": "C:/repos/MyProject/MyModel.SemanticModel"
            },
            {
                "_description": "Generate diagram from parent folder (auto-detects .SemanticModel)",
                "pbip_folder_path": "C:/repos/MyProject"
            },
            {
                "_description": "Generate diagram and select a specific measure initially",
                "pbip_folder_path": "C:/repos/MyProject/MyModel.SemanticModel",
                "main_item": "Measures[Total Sales]"
            },
            {
                "_description": "Generate diagram without auto-opening browser",
                "pbip_folder_path": "C:/repos/MyProject/MyModel.SemanticModel",
                "auto_open": False
            },
            {
                "_description": "Generate diagram with custom output path",
                "pbip_folder_path": "C:/repos/MyProject",
                "output_path": "C:/output/my_diagram.html"
            }
        ]
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
        "required": [],
        "examples": [
            {
                "_description": "Get token usage summary"
            },
            {
                "_description": "Get brief overview",
                "format": "summary"
            },
            {
                "_description": "Get comprehensive token report",
                "format": "detailed"
            }
        ]
    },

    # Slicer Operations (Tool 13) - PBIP Slicer Configuration
    'slicer_operations': {
        "type": "object",
        "properties": {
            "pbip_path": {
                "type": "string",
                "description": "Path to PBIP project folder, .Report folder, or definition folder containing the report visuals"
            },
            "operation": {
                "type": "string",
                "enum": ["list", "configure_single_select"],
                "description": "Operation: 'list' finds slicers and shows their current configuration/values, 'configure_single_select' changes matching slicers to single-select with All selected. Default: 'list'",
                "default": "list"
            },
            "display_name": {
                "type": "string",
                "description": "Filter by slicer display name/title (case-insensitive partial match). Example: 'Choose an asset' or 'Family Name'"
            },
            "entity": {
                "type": "string",
                "description": "Filter by table/entity name (case-insensitive). Example: 'd Assetinstrument' or 'd Family'"
            },
            "property": {
                "type": "string",
                "description": "Filter by column/property name (case-insensitive). Example: 'Asset Label' or 'Family Label'"
            },
            "dry_run": {
                "type": "boolean",
                "description": "For configure_single_select: if true, shows what would change without making actual changes. Default: false",
                "default": False
            }
        },
        "required": ["pbip_path"],
        "examples": [
            {
                "_description": "List all slicers in the report with their current values and configuration",
                "pbip_path": "C:/repos/MyProject/MyProject.Report",
                "operation": "list"
            },
            {
                "_description": "List slicers that use a specific column (e.g., Asset Label from d Assetinstrument)",
                "pbip_path": "C:/repos/MyProject",
                "operation": "list",
                "entity": "d Assetinstrument",
                "property": "Asset Label"
            },
            {
                "_description": "Find slicers by display name",
                "pbip_path": "C:/repos/MyProject",
                "operation": "list",
                "display_name": "Choose an asset"
            },
            {
                "_description": "Preview changes - show what would be changed without modifying files",
                "pbip_path": "C:/repos/MyProject",
                "operation": "configure_single_select",
                "entity": "d Assetinstrument",
                "property": "Asset Label",
                "dry_run": True
            },
            {
                "_description": "Change all slicers using Asset Label to single-select with All selected",
                "pbip_path": "C:/repos/MyProject",
                "operation": "configure_single_select",
                "entity": "d Assetinstrument",
                "property": "Asset Label"
            },
            {
                "_description": "Change specific slicer by display name to single-select",
                "pbip_path": "C:/repos/MyProject",
                "operation": "configure_single_select",
                "display_name": "Choose an asset"
            },
            {
                "_description": "List all slicers from Family table",
                "pbip_path": "C:/repos/MyProject",
                "operation": "list",
                "entity": "d Family"
            }
        ]
    },

    # Report Info (Tool 14) - PBIP Report Structure Information
    'report_info': {
        "type": "object",
        "properties": {
            "pbip_path": {
                "type": "string",
                "description": "Path to PBIP project folder, .Report folder, or definition folder containing the report"
            },
            "include_visuals": {
                "type": "boolean",
                "description": "Include detailed visual information per page (default: true)",
                "default": True
            },
            "include_filters": {
                "type": "boolean",
                "description": "Include filter pane filter information per page (default: true)",
                "default": True
            },
            "page_name": {
                "type": "string",
                "description": "Filter results to pages matching this name (case-insensitive partial match)"
            }
        },
        "required": ["pbip_path"],
        "examples": [
            {
                "_description": "Get full report structure with all pages, filters, and visuals",
                "pbip_path": "C:/repos/MyProject/MyProject.Report"
            },
            {
                "_description": "Get pages list with filter pane info only (no visual details)",
                "pbip_path": "C:/repos/MyProject",
                "include_visuals": False
            },
            {
                "_description": "Get pages list only (minimal info)",
                "pbip_path": "C:/repos/MyProject",
                "include_visuals": False,
                "include_filters": False
            },
            {
                "_description": "Get info for pages matching 'Dashboard'",
                "pbip_path": "C:/repos/MyProject",
                "page_name": "Dashboard"
            },
            {
                "_description": "Get all visuals and filters for a specific page",
                "pbip_path": "C:/repos/MyProject",
                "page_name": "Overview"
            }
        ]
    }
}
