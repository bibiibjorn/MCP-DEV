#!/usr/bin/env python3
"""
PBIXRay MCP Server v2.2 - Optimized Edition
Uses modular core services with enhanced DAX execution and error handling.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from __version__ import __version__
from core.connection_manager import ConnectionManager
from core.query_executor import OptimizedQueryExecutor
from core.performance_analyzer import EnhancedAMOTraceAnalyzer
from core.dax_injector import DAXInjector

BPA_AVAILABLE = False
try:
    from core.bpa_analyzer import BPAAnalyzer
    BPA_AVAILABLE = True
except:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pbixray_v2.2")

connection_manager = ConnectionManager()
query_executor = None
performance_analyzer = None
dax_injector = None
bpa_analyzer = None

app = Server("pbixray-v2.2")


@app.list_tools()
async def list_tools() -> List[Tool]:
    tools = [
        Tool(name="detect_powerbi_desktop", description="Detect Power BI instances", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="connect_to_powerbi", description="Connect to instance", inputSchema={"type": "object", "properties": {"model_index": {"type": "integer"}}, "required": ["model_index"]}),
        Tool(name="list_tables", description="List tables", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="list_measures", description="List measures", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="describe_table", description="Describe table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]}),
        Tool(name="get_measure_details", description="Measure details", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]}),
        Tool(name="search_string", description="Search measures", inputSchema={"type": "object", "properties": {"search_text": {"type": "string"}, "search_in_expression": {"type": "boolean", "default": True}, "search_in_name": {"type": "boolean", "default": True}}, "required": ["search_text"]}),
        Tool(name="list_calculated_columns", description="List calc columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="search_objects", description="Search objects", inputSchema={"type": "object", "properties": {"pattern": {"type": "string", "default": "*"}, "types": {"type": "array", "items": {"type": "string"}, "default": ["tables", "columns", "measures"]}}, "required": []}),
        Tool(name="get_data_sources", description="Data sources", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="get_m_expressions", description="M expressions", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="preview_table_data", description="Preview table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "top_n": {"type": "integer", "default": 10}}, "required": ["table"]}),
        Tool(name="run_dax_query", description="Run DAX", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "top_n": {"type": "integer", "default": 0}}, "required": ["query"]}),
        Tool(name="export_model_schema", description="Export schema", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="upsert_measure", description="Create/update measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}}, "required": ["table", "measure", "expression"]}),
        Tool(name="delete_measure", description="Delete a measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]}),
        Tool(name="list_columns", description="List columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="get_column_values", description="Column values", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["table", "column"]}),
        Tool(name="get_column_summary", description="Column stats", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]}),
        Tool(name="list_relationships", description="List relationships", inputSchema={"type": "object", "properties": {"active_only": {"type": "boolean"}}, "required": []}),
        Tool(name="get_vertipaq_stats", description="VertiPaq stats", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="analyze_query_performance", description="Analyze performance", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "runs": {"type": "integer", "default": 3}, "clear_cache": {"type": "boolean", "default": True}}, "required": ["query"]}),
        Tool(name="validate_dax_query", description="Validate DAX syntax and analyze complexity", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
    ]
    if BPA_AVAILABLE:
        tools.append(Tool(name="analyze_model_bpa", description="Run BPA", inputSchema={"type": "object", "properties": {}, "required": []}))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    global query_executor, performance_analyzer, dax_injector, bpa_analyzer

    try:
        if name == "detect_powerbi_desktop":
            instances = connection_manager.detect_instances()
            result = {'success': True, 'total_instances': len(instances), 'instances': instances}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "connect_to_powerbi":
            query_executor = None
            performance_analyzer = None
            dax_injector = None

            result = connection_manager.connect(arguments.get("model_index", 0))
            if result.get('success'):
                conn = connection_manager.get_connection()
                query_executor = OptimizedQueryExecutor(conn)

                # Initialize performance analyzer with AMO
                performance_analyzer = EnhancedAMOTraceAnalyzer(connection_manager.connection_string)
                amo_connected = performance_analyzer.connect_amo()

                if amo_connected:
                    result['performance_analysis'] = 'AMO SessionTrace available'
                    logger.info("✓ Performance analyzer initialized with AMO SessionTrace")
                else:
                    result['performance_analysis'] = 'AMO not available - performance analysis will use fallback mode'
                    logger.warning("✗ AMO not available - performance analysis limited")

                dax_injector = DAXInjector(conn)

                if BPA_AVAILABLE:
                    try:
                        rules_path = os.path.join(parent_dir, "core", "bpa.json")
                        bpa_analyzer = BPAAnalyzer(rules_path)
                    except:
                        pass

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        if not connection_manager.is_connected() or not query_executor:
            return [TextContent(type="text", text=json.dumps({"error": "Not connected"}, indent=2))]

        result = {}

        if name == "list_tables":
            result = query_executor.execute_info_query("TABLES")
        elif name == "list_measures":
            table = arguments.get("table")
            filter_expr = f'[Table] = "{table}"' if table else None
            result = query_executor.execute_info_query("MEASURES", filter_expr, exclude_columns=['Expression'])
        elif name == "describe_table":
            table = arguments["table"]
            cols = query_executor.execute_info_query("COLUMNS", f'[Table] = "{table}"')
            measures = query_executor.execute_info_query("MEASURES", f'[Table] = "{table}"', exclude_columns=['Expression'])
            rels = query_executor.execute_info_query("RELATIONSHIPS", f'[FromTable] = "{table}" || [ToTable] = "{table}"')
            result = {'success': True, 'table': table, 'columns': cols.get('rows', []), 'measures': measures.get('rows', []), 'relationships': rels.get('rows', [])}
        elif name == "get_measure_details":
            result = query_executor.execute_info_query("MEASURES", f'[Table] = "{arguments["table"]}" && [Name] = "{arguments["measure"]}"')
        elif name == "search_string":
            result = query_executor.search_measures_dax(arguments['search_text'], arguments.get('search_in_expression', True), arguments.get('search_in_name', True))
        elif name == "list_calculated_columns":
            table = arguments.get("table")
            filter_expr = '[Type] = "Calculated"'
            if table:
                filter_expr += f' && [Table] = "{table}"'
            query = f'EVALUATE FILTER(INFO.COLUMNS(), {filter_expr})'
            result = query_executor.validate_and_execute_dax(query)
        elif name == "search_objects":
            result = query_executor.search_objects_dax(arguments.get("pattern", "*"), arguments.get("types", ["tables", "columns", "measures"]))
        elif name == "get_data_sources":
            result = query_executor.validate_and_execute_dax("SELECT * FROM $SYSTEM.DISCOVER_DATASOURCES")
        elif name == "get_m_expressions":
            result = query_executor.validate_and_execute_dax("SELECT * FROM $SYSTEM.TMSCHEMA_EXPRESSIONS")
        elif name == "preview_table_data":
            result = query_executor.execute_with_table_reference_fallback(arguments['table'], arguments.get('top_n', 10))
        elif name == "run_dax_query":
            result = query_executor.validate_and_execute_dax(arguments['query'], arguments.get('top_n', 0))
        elif name == "export_model_schema":
            tables = query_executor.execute_info_query("TABLES")
            columns = query_executor.execute_info_query("COLUMNS")
            measures = query_executor.execute_info_query("MEASURES", exclude_columns=['Expression'])
            relationships = query_executor.execute_info_query("RELATIONSHIPS")
            result = {'success': True, 'schema': {'tables': tables.get('rows', []), 'columns': columns.get('rows', []), 'measures': measures.get('rows', []), 'relationships': relationships.get('rows', [])}}
        elif name == "upsert_measure":
            result = dax_injector.upsert_measure(arguments["table"], arguments["measure"], arguments["expression"], arguments.get("display_folder")) if dax_injector else {'success': False, 'error': 'Not available'}
        elif name == "delete_measure":
            result = dax_injector.delete_measure(arguments["table"], arguments["measure"]) if dax_injector else {'success': False, 'error': 'Not available'}
        elif name == "list_columns":
            table = arguments.get("table")
            result = query_executor.execute_info_query("COLUMNS", f'[Table] = "{table}"' if table else None)
        elif name == "get_column_values":
            query = f"EVALUATE TOPN({arguments.get('limit', 100)}, VALUES('{arguments['table']}'[{arguments['column']}]))"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "get_column_summary":
            query = f"EVALUATE ROW(\"Min\", MIN('{arguments['table']}'[{arguments['column']}]), \"Max\", MAX('{arguments['table']}'[{arguments['column']}]), \"Distinct\", DISTINCTCOUNT('{arguments['table']}'[{arguments['column']}]), \"Nulls\", COUNTBLANK('{arguments['table']}'[{arguments['column']}]))"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "list_relationships":
            active_only = arguments.get("active_only")
            filter_expr = "[IsActive] = TRUE" if active_only is True else "[IsActive] = FALSE" if active_only is False else None
            result = query_executor.execute_info_query("RELATIONSHIPS", filter_expr)
        elif name == "get_vertipaq_stats":
            table = arguments.get("table")
            query = f'EVALUATE FILTER(INFO.STORAGETABLECOLUMNS(), LEFT([TABLE_ID], LEN("{table}")) = "{table}")' if table else "EVALUATE INFO.STORAGETABLECOLUMNS()"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "analyze_query_performance":
            if not performance_analyzer:
                result = {
                    'success': False,
                    'error': 'Performance analyzer not initialized',
                    'error_type': 'analyzer_not_available',
                    'suggestions': ['Connect to Power BI Desktop first']
                }
            elif not performance_analyzer.amo_server:
                result = {
                    'success': False,
                    'error': 'AMO SessionTrace not available - using fallback mode',
                    'error_type': 'amo_not_connected',
                    'suggestions': [
                        'Check AMO libraries in lib/dotnet folder',
                        'Verify pythonnet (clr) configuration'
                    ],
                    'note': 'Using fallback mode (basic timing only)'
                }
                # Execute with fallback
                result = performance_analyzer.analyze_query(query_executor, arguments['query'], arguments.get('runs', 3), arguments.get('clear_cache', True))
            else:
                # AMO is connected, execute normally
                result = performance_analyzer.analyze_query(query_executor, arguments['query'], arguments.get('runs', 3), arguments.get('clear_cache', True))
        elif name == "validate_dax_query":
            result = query_executor.analyze_dax_query(arguments['query'])
        elif name == "analyze_model_bpa":
            if not BPA_AVAILABLE or not bpa_analyzer:
                result = {"error": "BPA not available"}
            else:
                tmsl_result = query_executor.get_tmsl_definition()
                if tmsl_result.get('success'):
                    violations = bpa_analyzer.analyze_model(tmsl_result['tmsl'])
                    summary = bpa_analyzer.get_violations_summary()
                    result = {'success': True, 'violations_count': len(violations), 'summary': summary, 'violations': [{'rule_id': v.rule_id, 'rule_name': v.rule_name, 'category': v.category, 'severity': v.severity.name if hasattr(v.severity, 'name') else str(v.severity), 'object_type': v.object_type, 'object_name': v.object_name, 'table_name': v.table_name, 'description': v.description} for v in violations]}
                else:
                    result = tmsl_result
        else:
            result = {'error': f'Unknown tool: {name}'}

        # Only add minimal connection info to reduce token usage
        if isinstance(result, dict) and result.get('success'):
            instance_info = connection_manager.get_instance_info()
            if instance_info:
                result['port'] = instance_info.get('port')

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}, indent=2))]


async def main():
    logger.info("=" * 80)
    logger.info(f"PBIXRay MCP Server v{__version__} - Optimized Edition")
    logger.info("=" * 80)
    logger.info("Features:")
    logger.info("  • Optimized DAX with table reference fallback")
    logger.info("  • Enhanced error handling & suggestions")
    logger.info("  • Performance analysis (SE/FE breakdown)")
    logger.info("  • BPA analysis")
    logger.info("=" * 80)

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
