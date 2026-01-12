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

    # Documentation (2 tools)
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

    # 15 - PBIP Dependency Analysis (1 tool)
    'pbip_dependency_analysis': {
        "type": "object",
        "properties": {
            "pbip_folder_path": {
                "type": "string",
                "description": "Path to .SemanticModel folder or parent PBIP folder (auto-detects .SemanticModel). The tool will also look for .Report folder for visual dependencies."
            },
            "auto_open": {
                "type": "boolean",
                "description": "Automatically open the HTML analysis in browser (default: true)",
                "default": True
            },
            "output_path": {
                "type": "string",
                "description": "Optional custom output path for the HTML file. If not specified, saves to exports/pbip_dependency_analysis.html"
            },
            "main_item": {
                "type": "string",
                "description": "Optional specific item to select initially (e.g., 'TableName[MeasureName]' or 'TableName[ColumnName]'). If not specified, selects the first measure in the model. The HTML includes a sidebar with all measures, columns, and field parameters - click any item to view its dependencies."
            }
        },
        "required": ["pbip_folder_path"],
        "examples": [
            {
                "_description": "Generate dependency analysis for a PBIP project",
                "pbip_folder_path": "C:/repos/MyProject/MyModel.SemanticModel"
            },
            {
                "_description": "Generate analysis from parent folder (auto-detects .SemanticModel)",
                "pbip_folder_path": "C:/repos/MyProject"
            },
            {
                "_description": "Generate analysis and select a specific measure initially",
                "pbip_folder_path": "C:/repos/MyProject/MyModel.SemanticModel",
                "main_item": "Measures[Total Sales]"
            },
            {
                "_description": "Generate analysis without auto-opening browser",
                "pbip_folder_path": "C:/repos/MyProject/MyModel.SemanticModel",
                "auto_open": False
            },
            {
                "_description": "Generate analysis with custom output path",
                "pbip_folder_path": "C:/repos/MyProject",
                "output_path": "C:/output/my_analysis.html"
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

    # 014 Visual & Filter Info PBIP
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
    },

    # Aggregation Analysis (1 tool) - Category: PBIP
    'analyze_aggregation': {
        "type": "object",
        "properties": {
            "pbip_path": {
                "type": "string",
                "description": "Path to PBIP project folder, .SemanticModel folder, or parent directory containing the model"
            },
            "output_format": {
                "type": "string",
                "enum": ["summary", "detailed", "html", "json"],
                "description": "Output format: 'summary' (quick overview), 'detailed' (full text report), 'html' (interactive report), 'json' (structured data). HTML report is always generated.",
                "default": "summary"
            },
            "output_path": {
                "type": "string",
                "description": "Optional output path for HTML/JSON reports. If not specified, exports to default location."
            },
            "page_filter": {
                "type": "string",
                "description": "Analyze only pages matching this name (case-insensitive partial match)"
            },
            "include_visual_details": {
                "type": "boolean",
                "description": "Include detailed per-visual analysis in output (default: true)",
                "default": True
            }
        },
        "required": ["pbip_path"],
        "examples": [
            {
                "_description": "Quick aggregation summary",
                "pbip_path": "C:/repos/MyModel",
                "output_format": "summary"
            },
            {
                "_description": "Full detailed text analysis",
                "pbip_path": "C:/repos/MyModel",
                "output_format": "detailed",
                "include_visual_details": True
            },
            {
                "_description": "Generate interactive HTML report",
                "pbip_path": "C:/repos/MyModel",
                "output_format": "html"
            },
            {
                "_description": "Export structured JSON data",
                "pbip_path": "C:/repos/MyModel",
                "output_format": "json",
                "output_path": "C:/reports/agg_analysis.json"
            },
            {
                "_description": "Analyze specific page",
                "pbip_path": "C:/repos/MyModel",
                "page_filter": "Dashboard"
            }
        ]
    },

    # 15 - Bookmark Analysis HTML PBIP (1 tool)
    'analyze_bookmarks': {
        "type": "object",
        "properties": {
            "pbip_path": {
                "type": "string",
                "description": "Path to PBIP project folder, .Report folder, or .pbip file. Tool will auto-detect the .Report folder."
            },
            "auto_open": {
                "type": "boolean",
                "description": "Automatically open the HTML analysis in browser (default: true)",
                "default": True
            },
            "output_path": {
                "type": "string",
                "description": "Optional custom output path for the HTML file. If not specified, saves to exports/bookmark_analysis/"
            }
        },
        "required": ["pbip_path"],
        "examples": [
            {
                "_description": "Analyze bookmarks in a PBIP report",
                "pbip_path": "C:/repos/MyProject/MyProject.Report"
            },
            {
                "_description": "Analyze bookmarks from parent folder (auto-detects .Report)",
                "pbip_path": "C:/repos/MyProject"
            },
            {
                "_description": "Analyze bookmarks without auto-opening browser",
                "pbip_path": "C:/repos/MyProject/MyProject.Report",
                "auto_open": False
            },
            {
                "_description": "Analyze bookmarks with custom output path",
                "pbip_path": "C:/repos/MyProject",
                "output_path": "C:/output/bookmarks_analysis.html"
            }
        ]
    },

    # 16 - Theme Compliance Analysis HTML PBIP (1 tool)
    'analyze_theme_compliance': {
        "type": "object",
        "properties": {
            "pbip_path": {
                "type": "string",
                "description": "Path to PBIP project folder, .Report folder, or .pbip file. Tool will auto-detect the .Report folder."
            },
            "theme_path": {
                "type": "string",
                "description": "Optional path to a custom theme JSON file. If not specified, the tool will try to detect the theme from the report."
            },
            "auto_open": {
                "type": "boolean",
                "description": "Automatically open the HTML analysis in browser (default: true)",
                "default": True
            },
            "output_path": {
                "type": "string",
                "description": "Optional custom output path for the HTML file. If not specified, saves to exports/theme_compliance/"
            }
        },
        "required": ["pbip_path"],
        "examples": [
            {
                "_description": "Analyze theme compliance in a PBIP report",
                "pbip_path": "C:/repos/MyProject/MyProject.Report"
            },
            {
                "_description": "Analyze theme compliance from parent folder (auto-detects .Report)",
                "pbip_path": "C:/repos/MyProject"
            },
            {
                "_description": "Analyze compliance against a specific theme file",
                "pbip_path": "C:/repos/MyProject",
                "theme_path": "C:/themes/corporate_theme.json"
            },
            {
                "_description": "Analyze theme compliance without auto-opening browser",
                "pbip_path": "C:/repos/MyProject",
                "auto_open": False
            },
            {
                "_description": "Analyze with custom output path",
                "pbip_path": "C:/repos/MyProject",
                "output_path": "C:/output/theme_compliance_report.html"
            }
        ]
    }
}
