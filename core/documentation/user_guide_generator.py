"""
Comprehensive User Guide Generator for Power BI MCP Server
Provides detailed, categorized explanations of all tools with examples
"""

from typing import Dict, Any, List


def generate_comprehensive_user_guide(category: str = "all", format_type: str = "detailed", server_version: str = "2.7.0") -> dict:
    """Generate comprehensive user guide organized by category with detailed explanations."""

    guide_data = {
        "connection": {
            "title": "🔌 Connection & Setup",
            "description": "Tools for detecting and connecting to Power BI Desktop instances",
            "tools": [
                {
                    "name": "connection: detect powerbi desktop",
                    "purpose": "Scan for running Power BI Desktop instances on your machine",
                    "when_to_use": "Before connecting - to see which .pbix files are open",
                    "example": '{}',
                    "returns": "List of detected instances with ports and file paths",
                    "tips": ["Power BI takes 10-15 seconds after opening to be detectable", "Multiple instances can be open simultaneously"]
                },
                {
                    "name": "connection: connect to powerbi",
                    "purpose": "Establish connection to a specific Power BI Desktop instance",
                    "when_to_use": "First step before any analysis - connects to the model",
                    "example": '{"model_index": 0}',
                    "returns": "Connection status and quickstart guide",
                    "tips": ["Use model_index from detect results", "Connection persists for the session", "First-time users get a quickstart guide"]
                }
            ]
        },
        "exploration": {
            "title": "🔍 Model Exploration & Discovery",
            "description": "Tools for browsing and understanding your Power BI model structure",
            "tools": [
                {
                    "name": "list: tables",
                    "purpose": "List all tables in the model",
                    "when_to_use": "To get an overview of model structure",
                    "example": '{"page_size": 50}',
                    "returns": "List of tables with row counts and hidden status",
                    "tips": ["Use page_size and next_token for large models", "Shows both visible and hidden tables"]
                },
                {
                    "name": "list: columns",
                    "purpose": "List columns (all or filtered by table)",
                    "when_to_use": "To understand table structure and data types",
                    "example": '{"table": "Sales", "page_size": 100}',
                    "returns": "Columns with data types, source columns, hidden status",
                    "tips": ["Omit table parameter to get all columns", "Shows calculated vs regular columns"]
                },
                {
                    "name": "list: measures",
                    "purpose": "List all DAX measures in the model",
                    "when_to_use": "To inventory business logic and KPIs",
                    "example": '{"table": "Measures"}',
                    "returns": "Measures with names, expressions, format strings, folders",
                    "tips": ["Expressions can be large - use pagination", "Includes hidden measures"]
                },
                {
                    "name": "describe: table",
                    "purpose": "Get comprehensive details about a specific table",
                    "when_to_use": "Deep dive into table structure with columns, measures, and relationships",
                    "example": '{"table": "Sales"}',
                    "returns": "Complete table schema including related tables",
                    "tips": ["All-in-one view of table metadata", "Shows relationships for this table"]
                },
                {
                    "name": "preview: table",
                    "purpose": "Sample actual data from a table",
                    "when_to_use": "Verify data quality or understand content",
                    "example": '{"table": "Sales", "top_n": 10}',
                    "returns": "Sample rows from the table",
                    "tips": ["Default 10 rows", "Works with both fact and dimension tables"]
                },
                {
                    "name": "search: objects",
                    "purpose": "Find tables/columns/measures by pattern",
                    "when_to_use": "Locate objects when you don't know exact names",
                    "example": '{"pattern": "*customer*", "types": ["tables", "columns"]}',
                    "returns": "Matching objects across the model",
                    "tips": ["Supports wildcards (*)", "Case-insensitive search"]
                },
                {
                    "name": "search: text in measures",
                    "purpose": "Search for text within measure names or DAX expressions",
                    "when_to_use": "Find measures that use specific functions or patterns",
                    "example": '{"search_text": "CALCULATE", "search_in_expression": true}',
                    "returns": "Measures containing the search text",
                    "tips": ["Great for finding usage of specific DAX functions", "Can search in names, expressions, or both"]
                },
                {
                    "name": "get: model summary",
                    "purpose": "Lightweight overview of entire model",
                    "when_to_use": "Quick snapshot for large models",
                    "example": '{}',
                    "returns": "Counts of tables, measures, columns, relationships + heuristic purpose detection",
                    "tips": ["Very fast - doesn't load full objects", "Includes 'purpose' field with smart detection"]
                }
            ]
        },
        "analysis": {
            "title": "📊 Analysis & Insights",
            "description": "Tools for analyzing model quality, performance, and dependencies",
            "tools": [
                {
                    "name": "analysis: full model",
                    "purpose": "Comprehensive analysis including BPA, relationships, and M queries",
                    "when_to_use": "Complete health check of your Power BI model",
                    "example": '{"include_bpa": true, "depth": "standard"}',
                    "returns": "Full report with best practices, relationships, data quality issues",
                    "tips": ["Most comprehensive tool", "Can take 30-60s for large models", "Use 'light' depth for faster results"]
                },
                {
                    "name": "analysis: best practices",
                    "purpose": "Run Best Practice Analyzer and M query scanning",
                    "when_to_use": "Check for common modeling issues and anti-patterns",
                    "example": '{"mode": "all", "bpa_profile": "balanced"}',
                    "returns": "List of violations with severity and recommendations",
                    "tips": ["BPA requires tabular-editor rules", "M query scan checks for performance issues"]
                },
                {
                    "name": "analysis: performance",
                    "purpose": "Analyze query performance, cardinality, and storage compression",
                    "when_to_use": "Diagnose slow reports or model bloat",
                    "example": '{"mode": "comprehensive"}',
                    "returns": "Performance metrics, bottlenecks, compression stats",
                    "tips": ["Use 'queries' mode to test specific DAX", "Clear cache for accurate results"]
                },
                {
                    "name": "dependency: analyze measure",
                    "purpose": "Show dependency tree for a measure",
                    "when_to_use": "Understand measure calculations and dependencies",
                    "example": '{"table": "Measures", "measure": "Total Sales", "depth": 3}',
                    "returns": "Hierarchical dependency tree",
                    "tips": ["Depth controls how many levels deep", "Shows all referenced measures, columns, tables"]
                },
                {
                    "name": "usage: where measure is used",
                    "purpose": "Impact analysis - what uses this measure",
                    "when_to_use": "Before modifying/deleting a measure",
                    "example": '{"table": "Measures", "measure": "Revenue"}',
                    "returns": "Forward and backward dependencies",
                    "tips": ["Shows downstream impact of changes", "Helps prevent breaking changes"]
                },
                {
                    "name": "usage: find unused objects",
                    "purpose": "Find tables/columns/measures not used anywhere",
                    "when_to_use": "Model cleanup - remove unused objects",
                    "example": '{}',
                    "returns": "List of orphaned objects",
                    "tips": ["Helps reduce model size", "Verify before deleting - check relationships too"]
                }
            ]
        },
        "export": {
            "title": "📄 Export & Documentation",
            "description": "Tools for exporting model metadata and generating documentation",
            "tools": [
                {
                    "name": "export: model explorer html",
                    "purpose": "Generate interactive HTML documentation for ONE model",
                    "when_to_use": "Create shareable documentation with dependencies and data previews",
                    "example": '{"output_dir": "exports/", "dependency_depth": 5}',
                    "returns": "File path to generated HTML explorer",
                    "tips": ["Opens in browser", "Includes measure dependencies", "NOT for comparing models"]
                },
                {
                    "name": "comparison: compare two models",
                    "purpose": "Compare TWO Power BI models side-by-side with DAX diffs",
                    "when_to_use": "Track changes between model versions or environments",
                    "example": '{"port1": 12345, "port2": 12346, "model1_label": "Prod", "model2_label": "Dev"}',
                    "returns": "HTML diff report showing added/removed/modified objects",
                    "tips": ["Requires TWO .pbix files open", "Shows full DAX expression diffs", "Includes metadata changes"]
                },
                {
                    "name": "documentation: generate word",
                    "purpose": "Create professional Word document with full model documentation",
                    "when_to_use": "Formal documentation for stakeholders",
                    "example": '{"include_hidden": true, "dependency_depth": 1}',
                    "returns": "Path to generated .docx file",
                    "tips": ["Includes dependencies", "Professional formatting", "Can be converted to PDF"]
                },
                {
                    "name": "export: tmdl",
                    "purpose": "Export model as TMDL (Tabular Model Definition Language)",
                    "when_to_use": "Version control or advanced model analysis",
                    "example": '{}',
                    "returns": "Complete TMDL structure with all objects and DAX",
                    "tips": ["Includes ALL metadata", "Large output for big models", "Good for git tracking"]
                },
                {
                    "name": "export: compact schema",
                    "purpose": "Export lightweight schema without expressions",
                    "when_to_use": "Quick model comparison or schema documentation",
                    "example": '{"format": "json", "include_hidden": true}',
                    "returns": "Simplified schema (no DAX/M code)",
                    "tips": ["Much smaller than TMDL", "Good for overview comparisons"]
                }
            ]
        },
        "validation": {
            "title": "✅ Validation & Quality",
            "description": "Tools for validating DAX, model integrity, and data quality",
            "tools": [
                {
                    "name": "validate: dax",
                    "purpose": "Validate DAX syntax and analyze complexity",
                    "when_to_use": "Before deploying new measures or troubleshooting errors",
                    "example": '{"query": "CALCULATE(SUM(Sales[Amount]), ALL(Product))"}',
                    "returns": "Validation result, complexity metrics, potential issues",
                    "tips": ["Checks syntax without executing", "Provides optimization hints"]
                },
                {
                    "name": "validate: model integrity",
                    "purpose": "Check model for structural issues",
                    "when_to_use": "After major model changes or imports",
                    "example": '{}',
                    "returns": "List of integrity violations and warnings",
                    "tips": ["Checks orphaned relationships", "Validates RLS", "Finds circular dependencies"]
                },
                {
                    "name": "run: dax",
                    "purpose": "Execute DAX query with performance metrics",
                    "when_to_use": "Test measure calculations or query performance",
                    "example": '{"query": "EVALUATE TOPN(10, Sales)", "mode": "auto"}',
                    "returns": "Query results + execution time statistics",
                    "tips": ["Mode 'preview' limits rows", "Mode 'analyze' focuses on performance", "'auto' chooses best mode"]
                }
            ]
        },
        "management": {
            "title": "🛠️ Model Management",
            "description": "Tools for modifying model objects (measures, calculation groups)",
            "tools": [
                {
                    "name": "measure: create or update",
                    "purpose": "Create a new measure or update existing one",
                    "when_to_use": "Add business logic to the model",
                    "example": '{"table": "Measures", "measure": "Total Revenue", "expression": "SUM(Sales[Amount])"}',
                    "returns": "Success status",
                    "tips": ["Updates if measure exists", "Preserves other properties", "Use display_folder to organize"]
                },
                {
                    "name": "measure: delete",
                    "purpose": "Remove a measure from the model",
                    "when_to_use": "Clean up unused measures",
                    "example": '{"table": "Measures", "measure": "Old Metric"}',
                    "returns": "Success status",
                    "tips": ["Check dependencies first with 'usage: where measure is used'", "Cannot undo"]
                },
                {
                    "name": "measure: bulk create",
                    "purpose": "Create multiple measures in one operation",
                    "when_to_use": "Deploying multiple calculated metrics",
                    "example": '{"measures": [{"table": "Measures", "measure": "M1", "expression": "1"}]}',
                    "returns": "Results for each measure",
                    "tips": ["More efficient than individual creates", "Stops on first error"]
                },
                {
                    "name": "calc: create calculation group",
                    "purpose": "Create calculation group for time intelligence or scenarios",
                    "when_to_use": "Implement YTD, QTD, or scenario switching",
                    "example": '{"name": "Time Intelligence", "items": [{"name": "Current", "expression": "SELECTEDMEASURE()"}]}',
                    "returns": "Success status",
                    "tips": ["Advanced feature", "Requires understanding of calculation groups"]
                }
            ]
        },
        "comparison": {
            "title": "🔄 Model Comparison & Versioning",
            "description": "Compare models across versions or environments to track changes",
            "tools": [
                {
                    "name": "comparison: compare two models",
                    "purpose": "Generate comprehensive comparison report between TWO separate Power BI models",
                    "when_to_use": "Version control, dev vs prod comparison, change tracking, impact analysis",
                    "example": '{"port1": 55555, "port2": 55556, "model1_label": "Production v1.2", "model2_label": "Development v1.3"}',
                    "returns": "Professional HTML diff report with side-by-side DAX comparisons, metadata changes, and visual indicators",
                    "requirements": ["TWO .pbix files must be open in separate Power BI Desktop instances", "Use 'connection: detect powerbi desktop' first to find port numbers"],
                    "what_is_compared": [
                        "✅ Tables - Added/Removed/Modified with descriptions and metadata",
                        "✅ Columns - Data types, descriptions, display folders, format strings, sort by column, data categories",
                        "✅ Measures - DAX expressions with syntax-highlighted diffs, descriptions, format strings, hidden status",
                        "✅ Calculation Groups - Calculation items with expressions and ordinals",
                        "✅ Relationships - Cross-filter direction, security filtering, referential integrity",
                        "✅ Partitions - M/Power Query expression changes",
                        "✅ Hierarchies - Level changes",
                        "✅ Annotations - Custom metadata on all objects"
                    ],
                    "html_report_features": [
                        "📊 Executive summary with change counts",
                        "🎨 Color-coded change indicators (green=added, red=removed, blue=modified)",
                        "💾 Side-by-side DAX code comparison with syntax highlighting",
                        "📝 Metadata change tracking (descriptions, folders, categories)",
                        "🔍 Expandable/collapsible sections",
                        "🎯 Filter by change type",
                        "📱 Professional responsive design"
                    ],
                    "tips": [
                        "Open BOTH .pbix files before running comparison",
                        "Use descriptive model1_label and model2_label for clarity",
                        "HTML report opens in browser automatically",
                        "Great for code reviews and change documentation",
                        "Can be included in deployment pipelines"
                    ],
                    "common_use_cases": [
                        "Development vs Production comparison before deployment",
                        "Tracking changes between model versions over time",
                        "Impact analysis: see exactly what changed",
                        "Documentation for change requests/tickets",
                        "Compliance and audit trails"
                    ]
                }
            ]
        },
        "advanced": {
            "title": "⚙️ Advanced & Administration",
            "description": "Server administration, performance monitoring, and advanced features",
            "tools": [
                {
                    "name": "server: info",
                    "purpose": "Get server version, configuration, telemetry, and connection status",
                    "when_to_use": "Troubleshooting, checking configuration, viewing server stats",
                    "example": '{}',
                    "returns": "Server version, config snapshot, telemetry, BPA status",
                    "tips": ["Shows if BPA is available", "Includes recent call history", "Shows error schema"]
                },
                {
                    "name": "server: recent logs",
                    "purpose": "View recent server log entries for debugging",
                    "when_to_use": "Debugging errors, investigating issues",
                    "example": '{"lines": 200}',
                    "returns": "Last N lines from server log file",
                    "tips": ["Default 200 lines", "Look for ERROR or WARNING entries"]
                },
                {
                    "name": "health_check",
                    "purpose": "Comprehensive health check of server and connection",
                    "when_to_use": "Verify server is working correctly",
                    "example": '{}',
                    "returns": "Health status, uptime, connection status, system info",
                    "tips": ["Shows server uptime", "Memory usage if psutil available"]
                },
                {
                    "name": "get_data_sources",
                    "purpose": "List all Power Query data sources in the model",
                    "when_to_use": "Audit data connections, document data lineage",
                    "example": '{"page_size": 50}',
                    "returns": "List of data sources with connection strings and types",
                    "tips": ["Shows SQL, Excel, Web, etc.", "Paginated for large models"]
                },
                {
                    "name": "get_m_expressions",
                    "purpose": "List all M/Power Query expressions",
                    "when_to_use": "Review ETL logic, find M query patterns",
                    "example": '{"page_size": 50}',
                    "returns": "M expressions for all queries/partitions",
                    "tips": ["Full M code included", "Can be very large"]
                }',
                    "returns": "Column sizes, cardinality, compression ratios",
                    "tips": ["Shows actual memory usage", "Identifies bloat"]
                },
                {
                    "name": "analyze_column_usage",
                    "purpose": "Analyze how a column is used in the model",
                    "when_to_use": "Before removing/modifying a column",
                    "example": '{"table": "Sales", "column": "Amount"}',
                    "returns": "Where column is referenced (measures, relationships, etc.)",
                    "tips": ["Impact analysis", "Shows dependencies"]
                },
                {
                    "name": "list_partitions",
                    "purpose": "List partitions for a table",
                    "when_to_use": "Review partition strategy, check refresh scope",
                    "example": '{"table": "Sales"}',
                    "returns": "Partition names, modes, sources",
                    "tips": ["Shows Import vs DirectQuery", "Includes M expressions"]
                },
                {
                    "name": "list_roles",
                    "purpose": "List Row-Level Security (RLS) roles",
                    "when_to_use": "Audit security, document RLS",
                    "example": '{}',
                    "returns": "Role names and filter expressions",
                    "tips": ["Shows DAX filters per table", "Security documentation"]
                },
                {
                    "name": "get_measure_details",
                    "purpose": "Get complete details for a specific measure",
                    "when_to_use": "Deep dive into measure definition",
                    "example": '{"table": "Measures", "measure": "Total Sales"}',
                    "returns": "Full measure metadata including expression, folder, format",
                    "tips": ["All properties included", "More detailed than list measures"]
                },
                {
                    "name": "profile: top values for column",
                    "purpose": "Get value distribution for a column",
                    "when_to_use": "Data profiling, understand cardinality",
                    "example": '{"table": "Product", "column": "Category", "top_n": 50}',
                    "returns": "Top N values with counts",
                    "tips": ["Default 50 values", "Shows data distribution"]
                },
                {
                    "name": "get_column_summary",
                    "purpose": "Statistical summary for a column",
                    "when_to_use": "Understand data distribution, check for nulls",
                    "example": '{"table": "Sales", "column": "Amount"}',
                    "returns": "Min, max, avg, distinct count, null count",
                    "tips": ["Numeric columns only", "Quick data quality check"]
                },
                {
                    "name": "list_calculated_columns",
                    "purpose": "List only calculated columns (not regular columns)",
                    "when_to_use": "Find calculated columns, review DAX column logic",
                    "example": '{"table": "Sales"}',
                    "returns": "Calculated columns with DAX expressions",
                    "tips": ["Subset of list columns", "Shows only calc columns"]
                }
            ]
        }
    }

    # Add ALL tools overview at the beginning
    all_tools_count = sum(len(cat_data["tools"]) for cat_data in guide_data.values())

    tool_categories_summary = {
        "connection": "Connect to Power BI Desktop instances",
        "exploration": "Browse tables, columns, measures, and model structure",
        "analysis": "Quality checks, performance analysis, dependencies",
        "export": "Generate documentation and exports",
        "validation": "Validate DAX, model integrity",
        "management": "Create/modify measures and calculation groups",
        "comparison": "Compare two models for version control",
        "advanced": "Server admin, monitoring, advanced features"
    }

    # Build the response based on format
    if format_type == "quick":
        # Quick reference format
        result = {"guide_type": "quick", "categories": {}}
        for cat_key, cat_data in guide_data.items():
            if category != "all" and category != cat_key:
                continue
            result["categories"][cat_key] = {
                "title": cat_data["title"],
                "tools": [f"{t['name']} - {t['purpose']}" for t in cat_data["tools"]]
            }
        return {"success": True, **result}

    else:
        # Detailed format (default)
        result = {
            "guide_type": "detailed",
            "server_version": server_version,
            "overview": {
                "total_tools": all_tools_count,
                "categories": tool_categories_summary,
                "description": "Comprehensive Power BI Model Context Protocol Server with 60+ tools for model analysis, documentation, and management"
            },
            "categories": {}
        }
        for cat_key, cat_data in guide_data.items():
            if category != "all" and category != cat_key:
                continue
            result["categories"][cat_key] = cat_data

        # Add complete tool index
        all_tool_names: List[str] = []
        for cat_data in guide_data.values():
            if category == "all" or category in guide_data:
                for tool in cat_data["tools"]:
                    all_tool_names.append(tool["name"])

        result["tool_index"] = sorted(all_tool_names)
        result["quick_reference"] = {
            "getting_started": [
                "1. connection: detect powerbi desktop",
                "2. connection: connect to powerbi",
                "3. get: model summary",
                "4. list: tables",
                "5. analysis: full model"
            ],
            "most_useful": [
                "analysis: full model - Complete health check",
                "comparison: compare two models - Track changes between versions",
                "export: model explorer html - Interactive documentation",
                "dependency: analyze measure - Understand measure logic",
                "usage: find unused objects - Clean up model"
            ]
        }
        result["documentation"] = "Each tool includes: purpose, when_to_use, example, returns, and tips"
        return {"success": True, **result}
