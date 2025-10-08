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
BPA_STATUS = {"available": False, "reason": None}
try:
    from core.bpa_analyzer import BPAAnalyzer
    BPA_AVAILABLE = True
    BPA_STATUS["available"] = True
except ImportError as e:
    logging.getLogger("pbixray_v2.3").warning(f"BPA not available: {e}")
    BPA_STATUS["reason"] = str(e)
except Exception as e:
    logging.getLogger("pbixray_v2.3").warning(f"Unexpected error loading BPA: {e}")
    BPA_STATUS["reason"] = str(e)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pbixray_v2.3")

# Configure file-based logging so get_recent_logs can read from a stable file
try:
    logs_dir = os.path.join(parent_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    LOG_PATH = os.path.join(logs_dir, "pbixray.log")
    # Avoid duplicate handlers on reloads
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == LOG_PATH for h in logger.handlers):
        _fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        _fh.setLevel(logging.INFO)
        _fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(_fh)
except Exception as _e:
    # Continue without file logging; get_recent_logs will report absence
    LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "pbixray.log")

# Track server start time
start_time = time.time()

# Initialize connection manager
connection_manager = ConnectionManager()
connection_state.set_connection_manager(connection_manager)

app = Server("pbixray-v2.3")
agent_policy = AgentPolicy(config)


@app.list_tools()
async def list_tools() -> List[Tool]:
    # Public, simplified tool surface
    tools = [
        # Combined DAX runner (preview/analyze)
    Tool(name="run_dax", description="Run a DAX query (preview/analyze) with safe limits", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string", "enum": ["auto", "preview", "analyze"], "default": "auto"}, "runs": {"type": "integer"}, "top_n": {"type": "integer"}, "verbose": {"type": "boolean", "default": False}, "include_event_counts": {"type": "boolean", "default": False}}, "required": ["query"]}),
        Tool(name="summarize_model", description="Lightweight model summary suitable for large models", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="document_model", description="Generate documentation or overview for the model", inputSchema={"type": "object", "properties": {"format": {"type": "string", "enum": ["markdown", "html", "json"], "default": "markdown"}, "include_examples": {"type": "boolean", "default": False}}, "required": []}),
        Tool(name="plan_query", description="Plan a safe query based on a high-level intent and optional table context", inputSchema={"type": "object", "properties": {"intent": {"type": "string"}, "table": {"type": "string"}, "max_rows": {"type": "integer"}}, "required": ["intent"]}),
        Tool(name="optimize_variants", description="Benchmark multiple DAX variants and return the fastest", inputSchema={"type": "object", "properties": {"candidates": {"type": "array", "items": {"type": "string"}}, "runs": {"type": "integer"}}, "required": ["candidates"]}),
        Tool(name="relationships", description="List relationships with optional cardinality analysis", inputSchema={"type": "object", "properties": {}, "required": []}),
        # Instance discovery and connect remain available
        Tool(name="detect_powerbi_desktop", description="Detect Power BI instances", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="connect_to_powerbi", description="Connect to instance", inputSchema={"type": "object", "properties": {"model_index": {"type": "integer"}}, "required": ["model_index"]}),
        # Core metadata utilities
        Tool(name="list_tables", description="List tables", inputSchema={"type": "object", "properties": {"page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
        Tool(name="list_measures", description="List measures", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
    Tool(name="describe_table", description="Describe table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "columns_page_size": {"type": "integer"}, "columns_next_token": {"type": "string"}, "measures_page_size": {"type": "integer"}, "measures_next_token": {"type": "string"}, "relationships_page_size": {"type": "integer"}, "relationships_next_token": {"type": "string"}}, "required": ["table"]}),
        Tool(name="get_measure_details", description="Measure details", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]}),
        Tool(name="search_string", description="Search measures", inputSchema={"type": "object", "properties": {"search_text": {"type": "string"}, "search_in_expression": {"type": "boolean", "default": True}, "search_in_name": {"type": "boolean", "default": True}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": ["search_text"]}),
        Tool(name="list_calculated_columns", description="List calc columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
        Tool(name="search_objects", description="Search objects", inputSchema={"type": "object", "properties": {"pattern": {"type": "string", "default": "*"}, "types": {"type": "array", "items": {"type": "string"}, "default": ["tables", "columns", "measures"]}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
        Tool(name="get_data_sources", description="Data sources", inputSchema={"type": "object", "properties": {"page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
        Tool(name="get_m_expressions", description="M expressions", inputSchema={"type": "object", "properties": {"page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
        Tool(name="preview_table_data", description="Preview table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "top_n": {"type": "integer", "default": 10}}, "required": ["table"]}),
        Tool(name="export_model_schema", description="Export schema", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="upsert_measure", description="Create/update measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}}, "required": ["table", "measure", "expression"]}),
        Tool(name="delete_measure", description="Delete a measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}} , "required": ["table", "measure"]}),
    Tool(name="list_columns", description="List columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []}),
        Tool(name="get_column_values", description="Column values", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["table", "column"]}),
        Tool(name="get_column_summary", description="Column stats", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]}),
        Tool(name="get_vertipaq_stats", description="VertiPaq stats", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
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
        Tool(name="analyze_storage_compression", description="Analyze storage/compression efficiency for a table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]}),

        # Model Validation
        Tool(name="validate_model_integrity", description="Validate model integrity", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="analyze_data_freshness", description="Analyze data freshness", inputSchema={"type": "object", "properties": {}, "required": []}),

        # Diagnostics and maintenance (trimmed; hide cache/safety/agent internals)
    Tool(name="summarize_last_result", description="Return metadata about the last successful query result", inputSchema={"type": "object", "properties": {}, "required": []}),
    Tool(name="warm_query_cache", description="Execute queries to warm both local and engine caches", inputSchema={"type": "object", "properties": {"queries": {"type": "array", "items": {"type": "string"}}, "runs": {"type": "integer", "default": 1}, "clear_cache": {"type": "boolean", "default": True}}, "required": ["queries"]}),
    Tool(name="analyze_queries_batch", description="Analyze performance for multiple DAX queries", inputSchema={"type": "object", "properties": {"queries": {"type": "array", "items": {"type": "string"}}, "runs": {"type": "integer", "default": 3}, "clear_cache": {"type": "boolean", "default": True}, "include_event_counts": {"type": "boolean", "default": False}}, "required": ["queries"]}),
    Tool(name="profile_columns", description="Profile columns (min, max, distinct, nulls)", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "columns": {"type": "array", "items": {"type": "string"}}}, "required": ["table"]}),
    Tool(name="get_column_value_distribution", description="Top values distribution for a column", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}, "top_n": {"type": "integer", "default": 50}}, "required": ["table", "column"]}),
        Tool(name="validate_best_practices", description="Composite validator for modeling best practices", inputSchema={"type": "object", "properties": {}, "required": []}),
    # Hidden agent orchestration variants are removed from public list (document_model covers docs)
        Tool(name="get_measure_impact", description="Forward/backward impact for a measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "depth": {"type": "integer", "default": 3}}, "required": ["table", "measure"]}),
        Tool(name="get_column_usage_heatmap", description="Column usage heat map across measures", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": []}),
        Tool(name="format_dax", description="Lightweight DAX formatter (whitespace)", inputSchema={"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}),
    Tool(name="export_model_overview", description="Export a compact model overview (json/yaml)", inputSchema={"type": "object", "properties": {"format": {"type": "string", "enum": ["json", "yaml"], "default": "json"}, "include_counts": {"type": "boolean", "default": True}}, "required": []}),
        # Introspection & tuning
    ]
    if BPA_AVAILABLE:
        tools.append(Tool(name="analyze_model_bpa", description="Run BPA", inputSchema={"type": "object", "properties": {}, "required": []}))
    # M best practices
    tools.append(Tool(name="analyze_m_practices", description="Scan M expressions for common issues", inputSchema={"type": "object", "properties": {}, "required": []}))
    # Output schemas and lineage export
    tools.append(Tool(name="get_output_schemas", description="Describe output schemas for key tools", inputSchema={"type": "object", "properties": {}, "required": []}))
    tools.append(Tool(name="export_relationship_graph", description="Export relationships as a graph (JSON or GraphML)", inputSchema={"type": "object", "properties": {"format": {"type": "string", "enum": ["json", "graphml"], "default": "json"}}, "required": []}))
    tools.append(Tool(name="apply_tmdl_patch", description="Apply safe TMDL patch operations (measures only)", inputSchema={"type": "object", "properties": {"updates": {"type": "array", "items": {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}}, "required": ["table", "measure", "expression"]}}, "dry_run": {"type": "boolean", "default": False}}, "required": ["updates"]}))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    try:
        def attach_port_if_connected(result: Any) -> Any:
            """Attach minimal port info on success to reduce token usage."""
            if isinstance(result, dict) and result.get('success') and connection_state.is_connected():
                instance_info = connection_manager.get_instance_info()
                if instance_info and instance_info.get('port'):
                    result['port'] = str(instance_info.get('port'))
            return result

        def _paginate(result: Any, page_size: int | None, next_token: str | None, list_keys: List[str]) -> Any:
            """Apply simple pagination to dicts with list fields. Returns next_token when truncated.

            list_keys: the keys in result that are arrays to paginate (first one found used if multiple).
            """
            try:
                ps = int(page_size) if page_size is not None else None
            except Exception:
                ps = None
            token_index = 0
            if next_token:
                try:
                    token_index = max(0, int(next_token))
                except Exception:
                    token_index = 0
            if not isinstance(result, dict) or not ps or ps <= 0:
                return result
            for k in list_keys:
                arr = result.get(k)
                if isinstance(arr, list):
                    end = token_index + ps
                    sliced = arr[token_index:end]
                    result[k] = sliced
                    if end < len(arr):
                        result['next_token'] = str(end)
                    break
            return result

        def _dax_quote_table(name: str) -> str:
            """Escape single quotes in table names for DAX and wrap in single quotes."""
            name = (name or "").replace("'", "''")
            return f"'{name}'"

        def _dax_quote_column(name: str) -> str:
            """Escape closing brackets in column names for DAX by doubling.
            DAX uses [Column] notation; a ']' in the name is represented as ']]'."""
            name = (name or "").replace("]", "]]")
            return f"[{name}]"

        # Diagnostics: logs
        if name == "get_recent_logs":
            lines = int(arguments.get("lines", 200) or 200)
            log_path = LOG_PATH
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    all_lines = f.readlines()
                tail = all_lines[-lines:] if lines > 0 else all_lines
                return [TextContent(type="text", text="".join(tail))]
            except Exception as e:
                return [TextContent(type="text", text=f"No log file available or could not read logs: {e}")]

        if name == "summarize_logs":
            lines = int(arguments.get("lines", 500) or 500)
            log_path = LOG_PATH
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    all_lines = f.readlines()
                tail = all_lines[-lines:] if lines > 0 else all_lines
                error_count = sum(1 for l in tail if "- ERROR -" in l)
                warn_count = sum(1 for l in tail if "- WARNING -" in l or "- WARN -" in l)
                info_count = sum(1 for l in tail if "- INFO -" in l)
                last_entries = tail[-10:]
                summary = {
                    'success': True,
                    'lines_analyzed': len(tail),
                    'counts': {
                        'error': error_count,
                        'warning': warn_count,
                        'info': info_count,
                    },
                    'last_entries': last_entries,
                }
                return [TextContent(type="text", text=json.dumps(summary, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({'success': False, 'error': str(e)}, indent=2))]

        if name == "get_cache_stats":
            if connection_state and connection_state.query_executor:
                try:
                    stats = connection_state.query_executor.get_cache_stats()
                except Exception as e:
                    stats = {'success': False, 'error': str(e)}
            else:
                stats = ErrorHandler.handle_manager_unavailable('query_executor')
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]

        if name == "get_context":
            keys = arguments.get('keys')
            data = connection_state.get_context(keys) if connection_state else {}
            return [TextContent(type="text", text=json.dumps({'success': True, 'context': data}, indent=2))]

        if name == "set_context":
            data = arguments.get('data', {})
            current = connection_state.set_context(data) if connection_state else {}
            return [TextContent(type="text", text=json.dumps({'success': True, 'context': current}, indent=2))]

        if name == "get_safety_limits":
            limits = connection_state.get_safety_limits() if connection_state else {}
            return [TextContent(type="text", text=json.dumps({'success': True, 'limits': limits}, indent=2))]

        if name == "set_safety_limits":
            limits = {k: v for k, v in arguments.items() if k in {'max_rows_per_call'}}
            current = connection_state.set_safety_limits(limits) if connection_state else {}
            return [TextContent(type="text", text=json.dumps({'success': True, 'limits': current}, indent=2))]

        if name == "summarize_last_result":
            summary = connection_state.get_last_result_summary()
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]

        if name == "set_perf_baseline":
            # Ensure we can run queries
            if not connection_state.is_connected():
                return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_not_connected(), indent=2))]
            qe = connection_state.query_executor
            runs = int(arguments.get('runs', 3) or 3)
            elapsed = []
            for _ in range(max(1, runs)):
                r = qe.validate_and_execute_dax(arguments['query'], 0, True)
                if not r.get('success'):
                    return [TextContent(type="text", text=json.dumps(r, indent=2))]
                elapsed.append(r.get('execution_time_ms', 0))
            record = {
                'query': arguments['query'],
                'runs': runs,
                'avg_ms': sum(elapsed)/len(elapsed) if elapsed else None,
                'min_ms': min(elapsed) if elapsed else None,
                'max_ms': max(elapsed) if elapsed else None,
                'ts': time.time(),
            }
            saved = connection_state.set_perf_baseline_record(arguments['name'], record)
            return [TextContent(type="text", text=json.dumps(saved, indent=2))]

        if name == "get_perf_baseline":
            res = connection_state.get_perf_baseline(arguments.get('name', ''))
            return [TextContent(type="text", text=json.dumps(res, indent=2))]

        if name == "list_perf_baselines":
            res = connection_state.list_perf_baselines()
            return [TextContent(type="text", text=json.dumps(res, indent=2))]

        if name == "compare_perf_to_baseline":
            base = connection_state.get_perf_baseline(arguments.get('name', ''))
            if not base.get('success'):
                return [TextContent(type="text", text=json.dumps(base, indent=2))]
            baseline = base.get('baseline', {})
            query = arguments.get('query') or baseline.get('query')
            if not query:
                return [TextContent(type="text", text=json.dumps({'success': False, 'error': 'Query is required if baseline does not store one'}, indent=2))]
            runs = int(arguments.get('runs', 3) or 3)
            qe = connection_state.query_executor
            elapsed = []
            for _ in range(max(1, runs)):
                r = qe.validate_and_execute_dax(query, 0, True)
                if not r.get('success'):
                    return [TextContent(type="text", text=json.dumps(r, indent=2))]
                elapsed.append(r.get('execution_time_ms', 0))
            current = {
                'runs': runs,
                'avg_ms': sum(elapsed)/len(elapsed) if elapsed else None,
                'min_ms': min(elapsed) if elapsed else None,
                'max_ms': max(elapsed) if elapsed else None,
            }
            diff = {}
            for k in ['avg_ms', 'min_ms', 'max_ms']:
                if baseline.get(k) is not None and current.get(k) is not None:
                    diff[k] = current[k] - baseline[k]
            res = {'success': True, 'baseline': baseline, 'current': current, 'diff': diff}
            return [TextContent(type="text", text=json.dumps(res, indent=2))]

        # Maintenance: flush cache
        if name == "flush_query_cache":
            if not connection_state.is_connected():
                return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_not_connected(), indent=2))]
            if not connection_state.query_executor:
                return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_manager_unavailable('query_executor'), indent=2))]
            result = connection_state.query_executor.flush_cache()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Tools that don't require a live connection
        if name == "get_server_info":
            info = {
                'success': True,
                'version': __version__,
                'server': app.name,
                'connected': connection_state.is_connected(),
                'bpa_available': BPA_AVAILABLE,
                'bpa_status': BPA_STATUS,
                'config': config.get_all(),
                'error_schema': {
                    'not_connected': {
                        'success': False,
                        'error_type': 'not_connected',
                        'error': 'No Power BI Desktop instance is connected.'
                    },
                    'manager_unavailable': {
                        'success': False,
                        'error_type': 'manager_unavailable',
                        'error': 'Required manager is unavailable.'
                    },
                    'unknown_tool': {
                        'success': False,
                        'error_type': 'unknown_tool',
                        'error': 'Requested tool is not recognized.'
                    },
                    'unexpected_error': {
                        'success': False,
                        'error_type': 'unexpected_error',
                        'error': 'An unexpected error occurred.'
                    },
                    'no_instances': {
                        'success': False,
                        'error_type': 'no_instances',
                        'error': 'No Power BI Desktop instances detected.'
                    },
                    'syntax_validation_error': {
                        'success': False,
                        'error_type': 'syntax_validation_error',
                        'error': 'Query validation failed.'
                    }
                }
            }
            if connection_state.is_connected():
                instance_info = connection_manager.get_instance_info()
                if instance_info:
                    info['port'] = instance_info.get('port')
            return [TextContent(type="text", text=json.dumps(info, indent=2))]

        if name == "health_check":
            now = time.time()
            system_info = {}
            psutil_note = None
            # Determine drive letter for current working directory on Windows (e.g., C:)
            try:
                cwd = os.getcwd()
                drive = os.path.splitdrive(cwd)[0] or None
            except Exception:
                drive = None
            try:
                import psutil  # type: ignore
                process_mem = psutil.Process().memory_info().rss / 1024 / 1024
                cpu = psutil.cpu_percent()
                disk = psutil.disk_usage('.').percent
                system_info = {
                    'memory_usage_mb': process_mem,
                    'cpu_percent': cpu,
                    'disk_usage_percent': disk,
                    'disk_drive': drive,
                }
            except Exception as e:
                psutil_note = f"psutil unavailable or failed: {e}"
                system_info = {
                    'psutil_unavailable': True,
                    'note': psutil_note,
                    'disk_drive': drive,
                }

            health_info = {
                'success': True,
                'timestamp': now,
                'server': {
                    'version': __version__,
                    'name': app.name,
                    'uptime_seconds': now - start_time
                },
                'connection': connection_state.get_status(),
                'system': system_info,
                'configuration': {
                    'cache_enabled': config.get('performance.cache_ttl_seconds', 0) > 0,
                    'features_enabled': config.get_section('features')
                }
            }
            return [TextContent(type="text", text=json.dumps(health_info, indent=2))]

        if name == "ensure_connected":
            result = agent_policy.ensure_connected(connection_manager, connection_state, arguments.get("preferred_index"))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "switch_instance":
            # Detect and choose target index
            instances = connection_manager.detect_instances()
            if not instances:
                return [TextContent(type="text", text=json.dumps({'success': False, 'error': 'No instances detected'}, indent=2))]
            mode = arguments.get('mode', 'next')
            current = connection_manager.get_instance_info()
            indices = {inst['port']: i for i, inst in enumerate(instances)}
            target_index = 0
            if mode == 'index' and isinstance(arguments.get('index'), int):
                target_index = max(0, min(len(instances) - 1, int(arguments['index'])))
            elif mode in ('next', 'prev') and current and current.get('port') in indices:
                cur_i = indices[current['port']]
                if mode == 'next':
                    target_index = (cur_i + 1) % len(instances)
                else:
                    target_index = (cur_i - 1) % len(instances)
            else:
                target_index = 0
            # Connect to target
            result = connection_manager.connect(target_index)
            if result.get('success'):
                connection_state.set_connection_manager(connection_manager)
                connection_state.initialize_managers(force_reinit=True)
                result['managers_initialized'] = connection_state._managers_initialized
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        if name == "get_query_history":
            limit = arguments.get('limit')
            try:
                data = connection_state.get_query_history(limit)
                return [TextContent(type="text", text=json.dumps({'success': True, 'items': data, 'count': len(data)}, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({'success': False, 'error': str(e)}, indent=2))]

        if name == "clear_query_history":
            try:
                removed = connection_state.clear_query_history()
                return [TextContent(type="text", text=json.dumps({'success': True, 'cleared': removed}, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({'success': False, 'error': str(e)}, indent=2))]

        if name == "set_command_timeout":
            try:
                secs = int(arguments.get('seconds'))
            except Exception:
                secs = None
            if secs is None or secs < 0:
                return [TextContent(type="text", text=json.dumps({'success': False, 'error': 'seconds must be a non-negative integer'}, indent=2))]
            if connection_state and connection_state.query_executor:
                try:
                    connection_state.query_executor.command_timeout_seconds = secs
                    return [TextContent(type="text", text=json.dumps({'success': True, 'command_timeout_seconds': secs}, indent=2))]
                except Exception as e:
                    return [TextContent(type="text", text=json.dumps({'success': False, 'error': str(e)}, indent=2))]
            return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_manager_unavailable('query_executor'), indent=2))]

        if name == "safe_run_dax":
            result = agent_policy.safe_run_dax(
                connection_state,
                arguments.get("query", ""),
                arguments.get("mode", "auto"),
                arguments.get("runs"),
                arguments.get("max_rows"),
                arguments.get("verbose", False),
                arguments.get("bypass_cache", False),
                arguments.get("include_event_counts", False),
            )
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "summarize_model":
            result = agent_policy.summarize_model_safely(connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "plan_query":
            result = agent_policy.plan_query(arguments.get("intent", ""), arguments.get("table"), arguments.get("max_rows"))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "optimize_variants":
            result = agent_policy.optimize_variants(connection_state, arguments.get("candidates", []), arguments.get("runs"))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "agent_health":
            result = agent_policy.agent_health(connection_manager, connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "generate_docs_safe":
            result = agent_policy.generate_docs_safe(connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "relationship_overview":
            result = agent_policy.relationship_overview(connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        # Public wrappers that auto-ensure connection and hide agent internals
        if name == "run_dax":
            ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
            if not ensured.get('success'):
                return [TextContent(type="text", text=json.dumps(ensured, indent=2))]
            # Map top_n -> max_rows for policy
            result = agent_policy.safe_run_dax(
                connection_state,
                arguments.get("query", ""),
                arguments.get("mode", "auto"),
                arguments.get("runs"),
                arguments.get("top_n"),
                arguments.get("verbose", False),
                False,
                arguments.get("include_event_counts", False),
            )
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "relationships":
            ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
            if not ensured.get('success'):
                return [TextContent(type="text", text=json.dumps(ensured, indent=2))]
            result = agent_policy.relationship_overview(connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "document_model":
            ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
            if not ensured.get('success'):
                return [TextContent(type="text", text=json.dumps(ensured, indent=2))]
            # Prefer profiled doc generator to honor params; falls back to safe docs
            fmt = arguments.get('format', 'markdown')
            include_examples = bool(arguments.get('include_examples', False))
            try:
                result = agent_policy.generate_documentation_profiled(connection_state, fmt, include_examples)
            except Exception:
                result = agent_policy.generate_docs_safe(connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "execute_intent":
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
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "decide_and_run":
            result = agent_policy.decide_and_run(
                connection_manager,
                connection_state,
                arguments.get("goal", ""),
                arguments.get("query"),
                arguments.get("candidates"),
                arguments.get("runs"),
                arguments.get("max_rows"),
                arguments.get("verbose", False),
            )
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        # New utilities & orchestrations (pre-connection checks handled in policy)
        if name == "warm_query_cache":
            result = agent_policy.warm_query_cache(connection_state, arguments.get('queries', []), arguments.get('runs'), arguments.get('clear_cache', False))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "analyze_queries_batch":
            inc = bool(arguments.get('include_event_counts', False))
            result = agent_policy.analyze_queries_batch(connection_state, arguments.get('queries', []), arguments.get('runs'), arguments.get('clear_cache', True), inc)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "set_cache_policy":
            result = agent_policy.set_cache_policy(connection_state, arguments.get('ttl_seconds'))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "profile_columns":
            result = agent_policy.profile_columns(connection_state, arguments.get('table', ''), arguments.get('columns'))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "get_value_distribution":
            result = agent_policy.get_value_distribution(connection_state, arguments.get('table', ''), arguments.get('column', ''), arguments.get('top_n', 50))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "validate_best_practices":
            result = agent_policy.validate_best_practices(connection_state)
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "generate_documentation_profiled":
            result = agent_policy.generate_documentation_profiled(connection_state, arguments.get('format', 'markdown'), arguments.get('include_examples', False))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "create_model_changelog":
            result = agent_policy.create_model_changelog(connection_state, arguments.get('reference_tmsl'))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "get_measure_impact":
            result = agent_policy.get_measure_impact(connection_state, arguments.get('table', ''), arguments.get('measure', ''), arguments.get('depth'))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "get_column_usage_heatmap":
            result = agent_policy.get_column_usage_heatmap(connection_state, arguments.get('table'), arguments.get('limit', 100))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "auto_document":
            result = agent_policy.auto_document(connection_manager, connection_state, arguments.get('profile', 'light'), arguments.get('include_lineage', False))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "auto_analyze_or_preview":
            result = agent_policy.auto_analyze_or_preview(connection_manager, connection_state, arguments.get('query', ''), arguments.get('runs'), arguments.get('max_rows'), arguments.get('priority', 'depth'))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "apply_recommended_fixes":
            result = agent_policy.apply_recommended_fixes(connection_state, arguments.get('actions', []))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "set_performance_trace":
            result = agent_policy.set_performance_trace(connection_state, bool(arguments.get('enabled')))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        if name == "format_dax":
            result = agent_policy.format_dax(arguments.get('expression', ''))
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        if name == "export_model_overview":
            result = agent_policy.export_model_overview(connection_state, arguments.get('format', 'json'), arguments.get('include_counts', True))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

        if name == "detect_powerbi_desktop":
            instances = connection_manager.detect_instances()
            result = {'success': True, 'total_instances': len(instances), 'instances': instances}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        if name == "connect_to_powerbi":
            # Clean up any existing state
            connection_state.cleanup()
            result = connection_manager.connect(arguments.get("model_index", 0))
            if result.get('success'):
                connection_state.set_connection_manager(connection_manager)
                connection_state.initialize_managers()
                result['managers_initialized'] = connection_state._managers_initialized
                result['performance_analysis'] = 'Available' if connection_state.performance_analyzer else 'Limited'
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # Require live connection for remaining tools
        if not connection_state.is_connected():
            return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_not_connected(), indent=2))]

        # Shortcut references
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

        if not query_executor:
            return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_manager_unavailable('query_executor'), indent=2))]

        # DMV cap for $SYSTEM.* helpers
        dmv_cap = int(config.get('query.max_rows_preview', config.get('query', {}).get('max_rows_preview', 1000)))

        if name == "list_tables":
            result = query_executor.execute_info_query("TABLES")
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "list_measures":
            table = arguments.get("table")
            result = query_executor.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "describe_table":
            table = arguments["table"]
            cols = query_executor.execute_info_query("COLUMNS", table_name=table)
            measures = query_executor.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
            rels = query_executor.execute_info_query("RELATIONSHIPS", f'[FromTable] = "{table}" || [ToTable] = "{table}"')
            result = {'success': True, 'table': table, 'columns': cols.get('rows', []), 'measures': measures.get('rows', []), 'relationships': rels.get('rows', [])}
            # Per-section pagination
            def _slice(arr, size, token):
                try:
                    ps = int(size) if size is not None else None
                except Exception:
                    ps = None
                start = 0
                if token:
                    try:
                        start = max(0, int(token))
                    except Exception:
                        start = 0
                if not ps or ps <= 0 or not isinstance(arr, list):
                    return arr, None
                end = start + ps
                nxt = str(end) if end < len(arr) else None
                return arr[start:end], nxt
            c, c_next = _slice(result['columns'], arguments.get('columns_page_size'), arguments.get('columns_next_token'))
            m, m_next = _slice(result['measures'], arguments.get('measures_page_size'), arguments.get('measures_next_token'))
            r, r_next = _slice(result['relationships'], arguments.get('relationships_page_size'), arguments.get('relationships_next_token'))
            result['columns'] = c
            result['measures'] = m
            result['relationships'] = r
            if c_next:
                result['columns_next_token'] = c_next
            if m_next:
                result['measures_next_token'] = m_next
            if r_next:
                result['relationships_next_token'] = r_next
        elif name == "get_measure_details":
            result = query_executor.execute_info_query("MEASURES", filter_expr=f'[Name] = "{arguments["measure"]}"', table_name=arguments["table"])
        elif name == "search_string":
            result = query_executor.search_measures_dax(arguments['search_text'], arguments.get('search_in_expression', True), arguments.get('search_in_name', True))
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "list_calculated_columns":
            table = arguments.get("table")
            filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
            result = query_executor.execute_info_query("COLUMNS", filter_expr=filter_expr, table_name=table)
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "search_objects":
            result = query_executor.search_objects_dax(arguments.get("pattern", "*"), arguments.get("types", ["tables", "columns", "measures"]))
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows', 'items'])
        elif name == "get_data_sources":
            query = f'''EVALUATE
            SELECTCOLUMNS(
                TOPN({dmv_cap}, $SYSTEM.DISCOVER_DATASOURCES),
                "DataSourceID", [DataSourceID],
                "Name", [Name],
                "Description", [Description],
                "Type", [Type]
            )'''
            result = query_executor.validate_and_execute_dax(query, dmv_cap)
            if result.get('success') and len(result.get('rows', [])) >= dmv_cap:
                result.setdefault('notes', []).append(f"Result truncated to {dmv_cap} rows for safety.")
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "get_m_expressions":
            query = f'''EVALUATE
            SELECTCOLUMNS(
                TOPN({dmv_cap}, $SYSTEM.TMSCHEMA_EXPRESSIONS),
                "Name", [Name],
                "Expression", [Expression],
                "Kind", [Kind]
            )'''
            result = query_executor.validate_and_execute_dax(query, dmv_cap)
            if result.get('success') and len(result.get('rows', [])) >= dmv_cap:
                result.setdefault('notes', []).append(f"Result truncated to {dmv_cap} rows for safety.")
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "preview_table_data":
            limits = connection_state.get_safety_limits()
            max_rows = int(limits.get('max_rows_per_call', 10000))
            req_top = int(arguments.get('top_n', 10) or 10)
            top_n = min(req_top, max_rows) if req_top > 0 else req_top
            result = query_executor.execute_with_table_reference_fallback(arguments['table'], top_n)
            if req_top != top_n and isinstance(result, dict):
                result.setdefault('notes', []).append(f'top_n clamped to safety limit of {max_rows}')
        elif name == "run_dax_query":
            limits = connection_state.get_safety_limits()
            max_rows = int(limits.get('max_rows_per_call', 10000))
            req_top = int(arguments.get('top_n', 0) or 0)
            top_n = min(req_top, max_rows) if req_top > 0 else req_top
            result = query_executor.validate_and_execute_dax(arguments['query'], top_n, arguments.get('bypass_cache', False))
            if req_top != top_n and isinstance(result, dict):
                result.setdefault('notes', []).append(f'top_n clamped to safety limit of {max_rows}')
        elif name == "export_model_schema":
            tables = query_executor.execute_info_query("TABLES")
            columns = query_executor.execute_info_query("COLUMNS")
            measures = query_executor.execute_info_query("MEASURES", exclude_columns=['Expression'])
            relationships = query_executor.execute_info_query("RELATIONSHIPS")
            result = {'success': True, 'schema': {'tables': tables.get('rows', []), 'columns': columns.get('rows', []), 'measures': measures.get('rows', []), 'relationships': relationships.get('rows', [])}}
        elif name == "upsert_measure":
            result = dax_injector.upsert_measure(arguments["table"], arguments["measure"], arguments["expression"], arguments.get("display_folder")) if dax_injector else ErrorHandler.handle_manager_unavailable('dax_injector')
        elif name == "delete_measure":
            result = dax_injector.delete_measure(arguments["table"], arguments["measure"]) if dax_injector else ErrorHandler.handle_manager_unavailable('dax_injector')
        elif name == "list_columns":
            table = arguments.get("table")
            result = query_executor.execute_info_query("COLUMNS", table_name=table)
            result = _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
        elif name == "get_column_values":
            t = _dax_quote_table(arguments['table'])
            c = _dax_quote_column(arguments['column'])
            query = f"EVALUATE TOPN({arguments.get('limit', 100)}, VALUES({t}{c}))"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "get_column_summary":
            t = _dax_quote_table(arguments['table'])
            c = _dax_quote_column(arguments['column'])
            query = (
                f"EVALUATE ROW(\"Min\", MIN({t}{c}), "
                f"\"Max\", MAX({t}{c}), "
                f"\"Distinct\", DISTINCTCOUNT({t}{c}), "
                f"\"Nulls\", COUNTBLANK({t}{c}))"
            )
            result = query_executor.validate_and_execute_dax(query)
        elif name == "get_column_value_distribution":
            # Alias to prior get_value_distribution with clearer name
            result = agent_policy.get_value_distribution(connection_state, arguments.get('table', ''), arguments.get('column', ''), arguments.get('top_n', 50))
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
                query = f"""
                EVALUATE
                VAR Src = INFO.STORAGETABLECOLUMNS()
                VAR Exact = FILTER(Src, [TABLE_FULL_NAME] = "{table}" || [TABLE_ID] = "{table}")
                RETURN
                IF(
                    COUNTROWS(Exact) > 0,
                    Exact,
                    FILTER(
                        Src,
                        CONTAINSSTRING([TABLE_FULL_NAME], "{table}") || CONTAINSSTRING([TABLE_ID], "{table}")
                    )
                )
                """
            else:
                query = "EVALUATE INFO.STORAGETABLECOLUMNS()"
            result = query_executor.validate_and_execute_dax(query)
        elif name == "analyze_query_performance":
            if not performance_analyzer:
                # Fallback to basic execution with a clear note
                basic = query_executor.validate_and_execute_dax(arguments['query'], 0, arguments.get('clear_cache', True))
                basic.setdefault('notes', []).append('Performance analyzer not initialized; returned basic execution only')
                basic.setdefault('decision', 'analyze')
                basic.setdefault('reason', 'Requested performance analysis, but analyzer unavailable; returned basic execution')
                result = basic
            elif not performance_analyzer.amo_server:
                warning = {
                    'success': False,
                    'error': 'AMO SessionTrace not available - using fallback mode',
                    'error_type': 'amo_not_connected',
                    'suggestions': [
                        'Check AMO libraries in lib/dotnet folder',
                        'Verify pythonnet (clr) configuration'
                    ],
                    'note': 'Using fallback mode (basic timing only)'
                }
                analysis = performance_analyzer.analyze_query(
                    query_executor,
                    arguments['query'],
                    arguments.get('runs', 3),
                    arguments.get('clear_cache', True),
                    arguments.get('include_event_counts', False)
                )
                if isinstance(analysis, dict):
                    analysis.setdefault('notes', []).append(warning.get('note'))
                    analysis.setdefault('warnings', []).append({k: v for k, v in warning.items() if k != 'success'})
                result = analysis
            else:
                result = performance_analyzer.analyze_query(
                    query_executor,
                    arguments['query'],
                    arguments.get('runs', 3),
                    arguments.get('clear_cache', True),
                    arguments.get('include_event_counts', False)
                )
        elif name == "validate_dax_query":
            result = query_executor.analyze_dax_query(arguments['query'])
        elif name == "auto_route":
            result = agent_policy.auto_analyze_or_preview(connection_manager, connection_state, arguments.get('query', ''), arguments.get('runs'), arguments.get('max_rows'), arguments.get('priority', 'depth'))
            return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]
        elif name == "analyze_m_practices":
            # Simple heuristics over M expressions
            query = f'''EVALUATE
            SELECTCOLUMNS(
                TOPN({dmv_cap}, $SYSTEM.TMSCHEMA_EXPRESSIONS),
                "Name", [Name],
                "Expression", [Expression],
                "Kind", [Kind]
            )'''
            data = query_executor.validate_and_execute_dax(query, dmv_cap)
            if not data.get('success'):
                result = data
            else:
                issues = []
                for row in data.get('rows', []):
                    if str(row.get('Kind', '')).upper() != 'M':
                        continue
                    name = row.get('Name') or '<unknown>'
                    expr = (row.get('Expression') or '')
                    expr_lower = expr.lower()
                    if 'table.buffer(' in expr_lower:
                        issues.append({'rule': 'M001', 'severity': 'warning', 'name': name, 'description': 'Table.Buffer used; can cause high memory usage if misapplied.'})
                    if 'web.contents(' in expr_lower and ('relativepath' not in expr_lower and 'query=' not in expr_lower):
                        issues.append({'rule': 'M002', 'severity': 'info', 'name': name, 'description': 'Web.Contents without RelativePath/Query options may be less cache-friendly.'})
                    if 'excel.workbook(file.contents(' in expr_lower and (':\\' in expr_lower or ':/'):
                        issues.append({'rule': 'M003', 'severity': 'warning', 'name': name, 'description': 'Excel.Workbook(File.Contents) with absolute path detected; consider parameterizing path.'})
                    if 'table.selectrows(' in expr_lower:
                        issues.append({'rule': 'M004', 'severity': 'info', 'name': name, 'description': 'Table.SelectRows found; ensure filtering is pushed to source where possible.'})
                result = {'success': True, 'count': len(issues), 'issues': issues}
        elif name == "analyze_model_bpa":
            if not BPA_AVAILABLE or not bpa_analyzer:
                result = ErrorHandler.handle_manager_unavailable('bpa_analyzer')
            else:
                tmsl_result = query_executor.get_tmsl_definition()
                if tmsl_result.get('success'):
                    violations = bpa_analyzer.analyze_model(tmsl_result['tmsl'])
                    summary = bpa_analyzer.get_violations_summary()
                    result = {'success': True, 'violations_count': len(violations), 'summary': summary, 'violations': [{'rule_id': v.rule_id, 'rule_name': v.rule_name, 'category': v.category, 'severity': getattr(v.severity, 'name', str(v.severity)), 'object_type': v.object_type, 'object_name': v.object_name, 'table_name': v.table_name, 'description': v.description} for v in violations]}
                else:
                    result = tmsl_result

        # Dependency Analysis
        elif name == "analyze_measure_dependencies":
            result = dependency_analyzer.analyze_measure_dependencies(
                arguments['table'],
                arguments['measure'],
                arguments.get('depth', 3)
            ) if dependency_analyzer else ErrorHandler.handle_manager_unavailable('dependency_analyzer')
        elif name == "find_unused_objects":
            result = dependency_analyzer.find_unused_objects() if dependency_analyzer else ErrorHandler.handle_manager_unavailable('dependency_analyzer')
        elif name == "analyze_column_usage":
            result = dependency_analyzer.analyze_column_usage(
                arguments['table'],
                arguments['column']
            ) if dependency_analyzer else ErrorHandler.handle_manager_unavailable('dependency_analyzer')

        # Bulk Operations
        elif name == "bulk_create_measures":
            result = bulk_operations.bulk_create_measures(arguments['measures']) if bulk_operations else ErrorHandler.handle_manager_unavailable('bulk_operations')
        elif name == "bulk_delete_measures":
            result = bulk_operations.bulk_delete_measures(arguments['measures']) if bulk_operations else ErrorHandler.handle_manager_unavailable('bulk_operations')

        # Calculation Groups
        elif name == "list_calculation_groups":
            result = calc_group_manager.list_calculation_groups() if calc_group_manager else ErrorHandler.handle_manager_unavailable('calc_group_manager')
        elif name == "create_calculation_group":
            result = calc_group_manager.create_calculation_group(
                arguments['name'],
                arguments['items'],
                arguments.get('description'),
                arguments.get('precedence', 0)
            ) if calc_group_manager else ErrorHandler.handle_manager_unavailable('calc_group_manager')
        elif name == "delete_calculation_group":
            result = calc_group_manager.delete_calculation_group(arguments['name']) if calc_group_manager else ErrorHandler.handle_manager_unavailable('calc_group_manager')

        # Partition Management
        elif name == "list_partitions":
            result = partition_manager.list_table_partitions(arguments.get('table')) if partition_manager else ErrorHandler.handle_manager_unavailable('partition_manager')
        elif name == "refresh_partition":
            result = partition_manager.refresh_partition(
                arguments['table'],
                arguments['partition'],
                arguments.get('refresh_type', 'full')
            ) if partition_manager else ErrorHandler.handle_manager_unavailable('partition_manager')
        elif name == "refresh_table":
            result = partition_manager.refresh_table(
                arguments['table'],
                arguments.get('refresh_type', 'full')
            ) if partition_manager else ErrorHandler.handle_manager_unavailable('partition_manager')

        # RLS Management
        elif name == "list_roles":
            result = rls_manager.list_roles() if rls_manager else ErrorHandler.handle_manager_unavailable('rls_manager')
        elif name == "test_role_filter":
            result = rls_manager.test_role_filter(
                arguments['role_name'],
                arguments['test_query']
            ) if rls_manager else ErrorHandler.handle_manager_unavailable('rls_manager')
        elif name == "validate_rls_coverage":
            result = rls_manager.validate_rls_coverage() if rls_manager else ErrorHandler.handle_manager_unavailable('rls_manager')

        # Model Export
        elif name == "export_tmsl":
            result = model_exporter.export_tmsl(arguments.get('include_full_model', False)) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
        elif name == "export_tmdl":
            result = model_exporter.export_tmdl_structure() if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
        elif name == "generate_documentation":
            result = model_exporter.generate_documentation(query_executor) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
        elif name == "get_model_summary":
            result = model_exporter.get_model_summary(query_executor) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
        elif name == "compare_models":
            result = model_exporter.compare_models(arguments['reference_tmsl']) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')

        # Output schemas (static)
        elif name == "get_output_schemas":
            schemas = {
                'version': '1.0.0',
                'tools': {
                    'run_dax': {
                        'preview': {
                            'rows': 'array<object>',
                            'row_count': 'number',
                            'execution_time_ms': 'number'
                        },
                        'analyze': {
                            'runs': 'array<object(run, execution_time_ms, formula_engine_ms, storage_engine_ms, metrics_available, cache_state, [event_counts?])>',
                            'summary': 'object(avg_execution_ms, min_execution_ms, max_execution_ms, avg_formula_engine_ms, avg_storage_engine_ms, fe_percent, se_percent, cache_mode)'
                        }
                    },
                    'relationships': {
                        'relationships': 'array<object(FromTable, FromColumn, ToTable, ToColumn, IsActive, CrossFilterDirection, Cardinality)>',
                        'analysis': 'object? (optimizer output)'
                    },
                    'get_vertipaq_stats': {
                        'rows': 'array<object(TABLE_ID, TABLE_FULL_NAME, COLUMN_NAME, DICTIONARY_SIZE, ...)>',
                    },
                    'summarize_model': {
                        'counts': 'object(tables:number, columns:number, measures:number, relationships:number)',
                        'tables_by_name': 'object<string, object>'
                    },
                    'document_model': {
                        'format': 'string(markdown|html|json)',
                        'sections': 'object<string, any>'
                    },
                    'export_relationship_graph': {
                        'json': {
                            'nodes': 'array<object(id,label,hidden)>',
                            'edges': 'array<object(from,to,fromColumn,toColumn,active,direction,cardinality)>'
                        },
                        'graphml': 'string (GraphML document)'
                    },
                    'validate_best_practices': {
                        'issues': 'array<object(type,severity,object,description)>'
                    },
                    'export_model_overview': {
                        'overview': 'object(same as summarize_model)'
                    }
                }
            }
            result = {'success': True, 'schemas': schemas, 'version': __version__}

        # Relationship graph export (JSON/GraphML)
        elif name == "export_relationship_graph":
            tables = query_executor.execute_info_query("TABLES")
            rels = query_executor.execute_info_query("RELATIONSHIPS")
            nodes = []
            edges = []
            tnames = set()
            if tables.get('success'):
                for t in tables.get('rows', []):
                    nm = t.get('Name')
                    if nm and nm not in tnames:
                        nodes.append({'id': nm, 'label': nm, 'hidden': bool(t.get('IsHidden'))})
                        tnames.add(nm)
            if rels.get('success'):
                for r in rels.get('rows', []):
                    edges.append({
                        'from': r.get('FromTable'),
                        'to': r.get('ToTable'),
                        'fromColumn': r.get('FromColumn'),
                        'toColumn': r.get('ToColumn'),
                        'active': bool(r.get('IsActive')),
                        'direction': r.get('CrossFilterDirection'),
                        'cardinality': r.get('Cardinality'),
                    })
            fmt = (arguments.get('format') or 'json').lower()
            if fmt == 'graphml':
                parts = [
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
                    '  <graph edgedefault="directed">'
                ]
                for n in nodes:
                    nid = (n.get('id') or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    parts.append(f'    <node id="{nid}"/>')
                for e in edges:
                    s = (e.get('from') or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    t = (e.get('to') or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    parts.append(f'    <edge source="{s}" target="{t}">')
                    def _data(k):
                        v = e.get(k)
                        if v is None:
                            return
                        text = str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        parts.append(f'      <data key="{k}">{text}</data>')
                    for k in ('fromColumn','toColumn','active','direction','cardinality'):
                        _data(k)
                    parts.append('    </edge>')
                parts.append('  </graph>')
                parts.append('</graphml>')
                graphml = '\n'.join(parts)
                result = {'success': True, 'format': 'graphml', 'graphml': graphml, 'counts': {'nodes': len(nodes), 'edges': len(edges)}}
            else:
                result = {'success': True, 'format': 'json', 'nodes': nodes, 'edges': edges, 'counts': {'nodes': len(nodes), 'edges': len(edges)}}

        # Guarded TMDL patch: measures only (uses dax_injector)
        elif name == "apply_tmdl_patch":
            updates = arguments.get('updates') or []
            dry_run = bool(arguments.get('dry_run', False))
            if not isinstance(updates, list) or not updates:
                result = {'success': False, 'error': 'updates must be a non-empty array'}
            else:
                if len(updates) > 200:
                    result = {'success': False, 'error': 'Too many updates; limit to 200 per call', 'error_type': 'limit_exceeded'}
                else:
                    plan = []
                    errors = []
                    for idx, u in enumerate(updates):
                        t = (u or {}).get('table')
                        m = (u or {}).get('measure')
                        e = (u or {}).get('expression')
                        df = (u or {}).get('display_folder')
                        if not t or not m or e is None:
                            errors.append({'index': idx, 'error': 'Missing table/measure/expression'})
                            continue
                        plan.append({'action': 'upsert_measure', 'table': t, 'measure': m, 'display_folder': df is not None})
                    if errors:
                        result = {'success': False, 'errors': errors, 'plan': plan}
                    elif dry_run:
                        result = {'success': True, 'dry_run': True, 'applied': 0, 'plan': plan}
                    else:
                        if not dax_injector:
                            result = ErrorHandler.handle_manager_unavailable('dax_injector')
                        else:
                            applied = 0
                            ops = []
                            for u in updates:
                                r = dax_injector.upsert_measure(u.get('table'), u.get('measure'), u.get('expression'), u.get('display_folder'))
                                ops.append(r)
                                if r.get('success'):
                                    applied += 1
                            result = {'success': True, 'applied': applied, 'operations': ops}

        # Performance Optimization
        elif name == "analyze_relationship_cardinality":
            result = performance_optimizer.analyze_relationship_cardinality() if performance_optimizer else ErrorHandler.handle_manager_unavailable('performance_optimizer')
        elif name == "analyze_column_cardinality":
            result = performance_optimizer.analyze_column_cardinality(arguments.get('table')) if performance_optimizer else ErrorHandler.handle_manager_unavailable('performance_optimizer')
        elif name == "analyze_storage_compression":
            # New, clearer name; call the same underlying optimizer
            result = performance_optimizer.analyze_encoding_efficiency(arguments['table']) if performance_optimizer else ErrorHandler.handle_manager_unavailable('performance_optimizer')

        # Model Validation
        elif name == "validate_model_integrity":
            result = model_validator.validate_model_integrity() if model_validator else ErrorHandler.handle_manager_unavailable('model_validator')
        elif name == "analyze_data_freshness":
            result = model_validator.analyze_data_freshness() if model_validator else ErrorHandler.handle_manager_unavailable('model_validator')

        else:
            result = ErrorHandler.handle_unknown_tool(name)

        return [TextContent(type="text", text=json.dumps(attach_port_if_connected(result), indent=2))]

    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps(ErrorHandler.handle_unexpected_error(name, e), indent=2))]


async def main():
    logger.info("=" * 80)
    logger.info(f"PBIXRay MCP Server v{__version__} - Complete Edition")
    logger.info("=" * 80)
    logger.info("Tools available")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
