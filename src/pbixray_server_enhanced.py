#!/usr/bin/env python3
"""
PBIXRay MCP Server v2.3 - Professional Edition
Uses modular core services with enhanced DAX execution and error handling.
"""

import asyncio
import json
import logging
import sys
import os
import time
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
from core.query_executor import OptimizedQueryExecutor, COLUMN_TYPE_CALCULATED
from core.performance_analyzer import EnhancedAMOTraceAnalyzer
from core.dax_injector import DAXInjector
from core.dependency_analyzer import DependencyAnalyzer
from core.bulk_operations import BulkOperationsManager
from core.calculation_group_manager import CalculationGroupManager
from core.partition_manager import PartitionManager
from core.rls_manager import RLSManager
from core.model_exporter import ModelExporter
from core.performance_optimizer import PerformanceOptimizer
from core.model_validator import ModelValidator

from core.error_handler import ErrorHandler
from core.agent_policy import AgentPolicy

# Import configuration and connection state
from core.config_manager import config
from core.connection_state import connection_state

BPA_AVAILABLE = False
try:
    from core.bpa_analyzer import BPAAnalyzer
    BPA_AVAILABLE = True
except ImportError as e:
    print(f"BPA not available: {e}")
except Exception as e:
    print(f"Unexpected error loading BPA: {e}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pbixray_v2.3")

# Track server start time
start_time = time.time()

# Initialize connection manager
connection_manager = ConnectionManager()
connection_state.set_connection_manager(connection_manager)

app = Server("pbixray-v2.3")
agent_policy = AgentPolicy(config)


@app.list_tools()
async def list_tools() -> List[Tool]:
    tools = [
        Tool(name="get_server_info", description="Get server version and connection status", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="health_check", description="Comprehensive server health check", inputSchema={"type": "object", "properties": {}, "required": []}),
        # Agent meta-tools (guardrailed orchestration)
        Tool(name="ensure_connected", description="Ensure connection to a Power BI Desktop instance (detects and connects if needed)", inputSchema={"type": "object", "properties": {"preferred_index": {"type": "integer"}}, "required": []}),
        Tool(name="safe_run_dax", description="Validate and safely execute a DAX query; optionally analyze performance", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string", "enum": ["auto", "preview", "analyze"], "default": "auto"}, "runs": {"type": "integer"}, "max_rows": {"type": "integer"}}, "required": ["query"]}),
        Tool(name="summarize_model", description="Lightweight model summary suitable for large models", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="plan_query", description="Plan a safe query based on a high-level intent and optional table context", inputSchema={"type": "object", "properties": {"intent": {"type": "string"}, "table": {"type": "string"}, "max_rows": {"type": "integer"}}, "required": ["intent"]}),
        Tool(name="optimize_query", description="Benchmark two DAX variants and pick the faster one", inputSchema={"type": "object", "properties": {"candidate_a": {"type": "string"}, "candidate_b": {"type": "string"}, "runs": {"type": "integer"}}, "required": ["candidate_a", "candidate_b"]}),
        Tool(name="agent_health", description="Consolidated agent/server health and quick model snapshot", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="generate_docs_safe", description="Generate documentation with large-model safeguards", inputSchema={"type": "object", "properties": {}, "required": []}),
    Tool(name="execute_intent", description="Natural-language intent execution (connect, preview, analyze, document)", inputSchema={"type": "object", "properties": {"goal": {"type": "string"}, "query": {"type": "string"}, "table": {"type": "string"}, "runs": {"type": "integer"}, "max_rows": {"type": "integer"}, "candidate_a": {"type": "string"}, "candidate_b": {"type": "string"}, "verbose": {"type": "boolean", "default": False}}, "required": ["goal"]}),
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

        # Dependency Analysis
        Tool(name="analyze_measure_dependencies", description="Analyze measure dependencies", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "depth": {"type": "integer", "default": 3}}, "required": ["table", "measure"]}),
        Tool(name="find_unused_objects", description="Find unused objects", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="analyze_column_usage", description="Analyze column usage", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]}),

        # Bulk Operations
        Tool(name="bulk_create_measures", description="Create multiple measures", inputSchema={"type": "object", "properties": {"measures": {"type": "array", "items": {"type": "object"}}}, "required": ["measures"]}),
        Tool(name="bulk_delete_measures", description="Delete multiple measures", inputSchema={"type": "object", "properties": {"measures": {"type": "array", "items": {"type": "object"}}}, "required": ["measures"]}),

        # Calculation Groups
        Tool(name="list_calculation_groups", description="List calculation groups", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="create_calculation_group", description="Create calculation group", inputSchema={"type": "object", "properties": {"name": {"type": "string"}, "items": {"type": "array", "items": {"type": "object"}}, "description": {"type": "string"}, "precedence": {"type": "integer", "default": 0}}, "required": ["name", "items"]}),
        Tool(name="delete_calculation_group", description="Delete calculation group", inputSchema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}),

        # Partition Management
        Tool(name="list_partitions", description="List table partitions", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="refresh_partition", description="Refresh partition", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "partition": {"type": "string"}, "refresh_type": {"type": "string", "default": "full"}}, "required": ["table", "partition"]}),
        Tool(name="refresh_table", description="Refresh table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "refresh_type": {"type": "string", "default": "full"}}, "required": ["table"]}),

        # RLS Management
        Tool(name="list_roles", description="List security roles", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="test_role_filter", description="Test RLS role", inputSchema={"type": "object", "properties": {"role_name": {"type": "string"}, "test_query": {"type": "string"}}, "required": ["role_name", "test_query"]}),
        Tool(name="validate_rls_coverage", description="Validate RLS coverage", inputSchema={"type": "object", "properties": {}, "required": []}),

        # Model Export
        Tool(name="export_tmsl", description="Export TMSL (summary by default)", inputSchema={"type": "object", "properties": {"include_full_model": {"type": "boolean", "default": False}}, "required": []}),
        Tool(name="export_tmdl", description="Export TMDL", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="generate_documentation", description="Generate docs", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="get_model_summary", description="Get lightweight model summary", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="compare_models", description="Compare models", inputSchema={"type": "object", "properties": {"reference_tmsl": {"type": "object"}}, "required": ["reference_tmsl"]}),

        # Performance Optimization
        Tool(name="analyze_relationship_cardinality", description="Analyze relationship cardinality", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="analyze_column_cardinality", description="Analyze column cardinality", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="analyze_encoding_efficiency", description="Analyze encoding efficiency", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]}),

        # Model Validation
        Tool(name="validate_model_integrity", description="Validate model integrity", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="analyze_data_freshness", description="Analyze data freshness", inputSchema={"type": "object", "properties": {}, "required": []}),
    ]
    if BPA_AVAILABLE:
        tools.append(Tool(name="analyze_model_bpa", description="Run BPA", inputSchema={"type": "object", "properties": {}, "required": []}))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    try:
        # Tools that don't require a live connection
        if name == "get_server_info":
            info = {
                'success': True,
                'version': __version__,
                'server': app.name,
                'connected': connection_state.is_connected(),
                'bpa_available': BPA_AVAILABLE,
                'config': config.get_all()
            }
            if connection_state.is_connected():
                instance_info = connection_manager.get_instance_info()
                if instance_info:
                    info['port'] = instance_info.get('port')
            return [TextContent(type="text", text=json.dumps(info, indent=2))]
        
        elif name == "health_check":
            import psutil
            import time
            
            health_info = {
                'success': True,
                'timestamp': time.time(),
                'server': {
                    'version': __version__,
                    'name': app.name,
                    'uptime_seconds': time.time() - start_time if 'start_time' in globals() else 0
                },
                'connection': connection_state.get_status(),
                'system': {
                    'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                    'cpu_percent': psutil.cpu_percent(),
                    'disk_usage_percent': psutil.disk_usage('.').percent
                },
                'configuration': {
                    'cache_enabled': config.get('performance.cache_ttl_seconds', 0) > 0,
                    'features_enabled': config.get_section('features')
                }
            }
            return [TextContent(type="text", text=json.dumps(health_info, indent=2))]
        elif name == "ensure_connected":
            result = agent_policy.ensure_connected(connection_manager, connection_state, arguments.get("preferred_index"))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "safe_run_dax":
            result = agent_policy.safe_run_dax(
                connection_state,
                arguments.get("query", ""),
                arguments.get("mode", "auto"),
                arguments.get("runs"),
                arguments.get("max_rows"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "summarize_model":
            result = agent_policy.summarize_model_safely(connection_state)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "plan_query":
            result = agent_policy.plan_query(arguments.get("intent", ""), arguments.get("table"), arguments.get("max_rows"))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "optimize_query":
            result = agent_policy.optimize_query(connection_state, arguments.get("candidate_a", ""), arguments.get("candidate_b", ""), arguments.get("runs"))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "agent_health":
            result = agent_policy.agent_health(connection_manager, connection_state)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "generate_docs_safe":
            result = agent_policy.generate_docs_safe(connection_state)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        elif name == "execute_intent":
            result = agent_policy.execute_intent(
                connection_manager,
                connection_state,
                arguments.get("goal", ""),
                arguments.get("query"),
                arguments.get("table"),
                arguments.get("runs"),
                arguments.get("max_rows"),
                arguments.get("verbose", False),
                arguments.get("candidate_a"),
                arguments.get("candidate_b"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        if name == "detect_powerbi_desktop":
            instances = connection_manager.detect_instances()
            result = {'success': True, 'total_instances': len(instances), 'instances': instances}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "connect_to_powerbi":
            # Clean up any existing state
            connection_state.cleanup()
            
            result = connection_manager.connect(arguments.get("model_index", 0))
            if result.get('success'):
                # Update connection state
                connection_state.set_connection_manager(connection_manager)
                
                # Initialize all managers through connection state
                connection_state.initialize_managers()
                
                result['managers_initialized'] = connection_state._managers_initialized
                result['performance_analysis'] = 'Available' if connection_state.performance_analyzer else 'Limited'
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        if not connection_state.is_connected():
            return [TextContent(type="text", text=json.dumps({"error": "Not connected to Power BI Desktop", "error_type": "not_connected"}, indent=2))]

        result = {}

        # Use connection state managers with fallback
        query_executor = connection_state.query_executor
        performance_analyzer = connection_state.performance_analyzer
        dax_injector = connection_state.dax_injector
        bpa_analyzer = connection_state.bpa_analyzer
        dependency_analyzer = connection_state.dependency_analyzer
        bulk_operations = connection_state.bulk_operations
        calc_group_manager = connection_state.calc_group_manager
        partition_manager = connection_state.partition_manager
        rls_manager = connection_state.rls_manager
        model_exporter = connection_state.model_exporter
        performance_optimizer = connection_state.performance_optimizer
        model_validator = connection_state.model_validator

        # Check if query executor is available (required for most operations)
        if not query_executor:
            return [TextContent(type="text", text=json.dumps({"error": "Query executor not available", "error_type": "service_unavailable"}, indent=2))]

        if name == "list_tables":
            result = query_executor.execute_info_query("TABLES")
        elif name == "list_measures":
            table = arguments.get("table")
            result = query_executor.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
        elif name == "describe_table":
            table = arguments["table"]
            cols = query_executor.execute_info_query("COLUMNS", table_name=table)
            measures = query_executor.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
            rels = query_executor.execute_info_query("RELATIONSHIPS", f'[FromTable] = "{table}" || [ToTable] = "{table}"')
            result = {'success': True, 'table': table, 'columns': cols.get('rows', []), 'measures': measures.get('rows', []), 'relationships': rels.get('rows', [])}
        elif name == "get_measure_details":
            result = query_executor.execute_info_query("MEASURES", filter_expr=f'[Name] = "{arguments["measure"]}"', table_name=arguments["table"])
        elif name == "search_string":
            result = query_executor.search_measures_dax(arguments['search_text'], arguments.get('search_in_expression', True), arguments.get('search_in_name', True))
        elif name == "list_calculated_columns":
            table = arguments.get("table")
            filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
            result = query_executor.execute_info_query("COLUMNS", filter_expr=filter_expr, table_name=table)
        elif name == "search_objects":
            result = query_executor.search_objects_dax(arguments.get("pattern", "*"), arguments.get("types", ["tables", "columns", "measures"]))
        elif name == "get_data_sources":
            # DMV queries need special handling - materialize with TOPN before SELECTCOLUMNS
            query = '''EVALUATE
            SELECTCOLUMNS(
                TOPN(999999, $SYSTEM.DISCOVER_DATASOURCES),
                "DataSourceID", [DataSourceID],
                "Name", [Name],
                "Description", [Description],
                "Type", [Type]
            )'''
            result = query_executor.validate_and_execute_dax(query)
        elif name == "get_m_expressions":
            # DMV queries need special handling - materialize with TOPN before SELECTCOLUMNS
            query = '''EVALUATE
            SELECTCOLUMNS(
                TOPN(999999, $SYSTEM.TMSCHEMA_EXPRESSIONS),
                "Name", [Name],
                "Expression", [Expression],
                "Kind", [Kind]
            )'''
            result = query_executor.validate_and_execute_dax(query)
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
            result = query_executor.execute_info_query("COLUMNS", table_name=table)
        elif name == "get_column_values":
            query = f"EVALUATE TOPN({arguments.get('limit', 100)}, VALUES('{arguments['table']}'[{arguments['column']}]))"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "get_column_summary":
            query = f"EVALUATE ROW(\"Min\", MIN('{arguments['table']}'[{arguments['column']}]), \"Max\", MAX('{arguments['table']}'[{arguments['column']}]), \"Distinct\", DISTINCTCOUNT('{arguments['table']}'[{arguments['column']}]), \"Nulls\", COUNTBLANK('{arguments['table']}'[{arguments['column']}]))"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "list_relationships":
            active_only = arguments.get("active_only")
            if active_only is True:
                result = query_executor.execute_info_query("RELATIONSHIPS", "[IsActive] = TRUE")
            elif active_only is False:
                result = query_executor.execute_info_query("RELATIONSHIPS", "[IsActive] = FALSE")
            else:
                result = query_executor.execute_info_query("RELATIONSHIPS")
        elif name == "get_vertipaq_stats":
            table = arguments.get("table")
            if table:
                query = f'EVALUATE FILTER(INFO.STORAGETABLECOLUMNS(), [TABLE_ID] = "{table}")'
            else:
                query = "EVALUATE INFO.STORAGETABLECOLUMNS()"
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

        # Dependency Analysis
        elif name == "analyze_measure_dependencies":
            result = dependency_analyzer.analyze_measure_dependencies(
                arguments['table'],
                arguments['measure'],
                arguments.get('depth', 3)
            ) if dependency_analyzer else {'success': False, 'error': 'Not available'}
        elif name == "find_unused_objects":
            result = dependency_analyzer.find_unused_objects() if dependency_analyzer else {'success': False, 'error': 'Not available'}
        elif name == "analyze_column_usage":
            result = dependency_analyzer.analyze_column_usage(
                arguments['table'],
                arguments['column']
            ) if dependency_analyzer else {'success': False, 'error': 'Not available'}

        # Bulk Operations
        elif name == "bulk_create_measures":
            result = bulk_operations.bulk_create_measures(arguments['measures']) if bulk_operations else {'success': False, 'error': 'Not available'}
        elif name == "bulk_delete_measures":
            result = bulk_operations.bulk_delete_measures(arguments['measures']) if bulk_operations else {'success': False, 'error': 'Not available'}

        # Calculation Groups
        elif name == "list_calculation_groups":
            result = calc_group_manager.list_calculation_groups() if calc_group_manager else {'success': False, 'error': 'Not available'}
        elif name == "create_calculation_group":
            result = calc_group_manager.create_calculation_group(
                arguments['name'],
                arguments['items'],
                arguments.get('description'),
                arguments.get('precedence', 0)
            ) if calc_group_manager else {'success': False, 'error': 'Not available'}
        elif name == "delete_calculation_group":
            result = calc_group_manager.delete_calculation_group(arguments['name']) if calc_group_manager else {'success': False, 'error': 'Not available'}

        # Partition Management
        elif name == "list_partitions":
            result = partition_manager.list_table_partitions(arguments.get('table')) if partition_manager else {'success': False, 'error': 'Not available'}
        elif name == "refresh_partition":
            result = partition_manager.refresh_partition(
                arguments['table'],
                arguments['partition'],
                arguments.get('refresh_type', 'full')
            ) if partition_manager else {'success': False, 'error': 'Not available'}
        elif name == "refresh_table":
            result = partition_manager.refresh_table(
                arguments['table'],
                arguments.get('refresh_type', 'full')
            ) if partition_manager else {'success': False, 'error': 'Not available'}

        # RLS Management
        elif name == "list_roles":
            result = rls_manager.list_roles() if rls_manager else {'success': False, 'error': 'Not available'}
        elif name == "test_role_filter":
            result = rls_manager.test_role_filter(
                arguments['role_name'],
                arguments['test_query']
            ) if rls_manager else {'success': False, 'error': 'Not available'}
        elif name == "validate_rls_coverage":
            result = rls_manager.validate_rls_coverage() if rls_manager else {'success': False, 'error': 'Not available'}

        # Model Export
        elif name == "export_tmsl":
            result = model_exporter.export_tmsl(arguments.get('include_full_model', False)) if model_exporter else {'success': False, 'error': 'Not available'}
        elif name == "export_tmdl":
            result = model_exporter.export_tmdl_structure() if model_exporter else {'success': False, 'error': 'Not available'}
        elif name == "generate_documentation":
            result = model_exporter.generate_documentation(query_executor) if model_exporter else {'success': False, 'error': 'Not available'}
        elif name == "get_model_summary":
            result = model_exporter.get_model_summary(query_executor) if model_exporter else {'success': False, 'error': 'Not available'}
        elif name == "compare_models":
            result = model_exporter.compare_models(arguments['reference_tmsl']) if model_exporter else {'success': False, 'error': 'Not available'}

        # Performance Optimization
        elif name == "analyze_relationship_cardinality":
            result = performance_optimizer.analyze_relationship_cardinality() if performance_optimizer else {'success': False, 'error': 'Not available'}
        elif name == "analyze_column_cardinality":
            result = performance_optimizer.analyze_column_cardinality(arguments.get('table')) if performance_optimizer else {'success': False, 'error': 'Not available'}
        elif name == "analyze_encoding_efficiency":
            result = performance_optimizer.analyze_encoding_efficiency(arguments['table']) if performance_optimizer else {'success': False, 'error': 'Not available'}

        # Model Validation
        elif name == "validate_model_integrity":
            result = model_validator.validate_model_integrity() if model_validator else {'success': False, 'error': 'Not available'}
        elif name == "analyze_data_freshness":
            result = model_validator.analyze_data_freshness() if model_validator else {'success': False, 'error': 'Not available'}

        else:
            result = {'error': f'Unknown tool: {name}'}

        # Only add minimal connection info to reduce token usage
        if isinstance(result, dict) and result.get('success'):
            if connection_state.is_connected():
                instance_info = connection_manager.get_instance_info()
                if instance_info and instance_info.get('port'):
                    result['port'] = str(instance_info.get('port'))

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}, indent=2))]


async def main():
    logger.info("=" * 80)
    logger.info(f"PBIXRay MCP Server v{__version__} - Complete Edition")
    logger.info("=" * 80)
    logger.info("48 Tools Available (47 + BPA):")
    logger.info("  • Core (14): Detection, Connection, Tables, Measures, Columns")
    logger.info("  • DAX (3): Query Execution, Validation, Performance Analysis")
    logger.info("  • Dependencies (3): Measure Dependencies, Column Usage, Unused Objects")
    logger.info("  • Bulk Operations (2): Batch Create/Delete Measures")
    logger.info("  • Calculation Groups (3): List, Create, Delete")
    logger.info("  • Partitions (3): List, Refresh Partition/Table, Data Freshness")
    logger.info("  • RLS (3): List Roles, Test Filters, Validate Coverage")
    logger.info("  • Export (5): TMSL, TMDL, Documentation, Summary, Compare")
    logger.info("  • Optimization (3): Cardinality, Encoding, VertiPaq Analysis")
    logger.info("  • Validation (2): Model Integrity, BPA Analysis")
    logger.info("=" * 80)

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
