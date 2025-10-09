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
from collections import deque
from typing import Any, List, Optional

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
from core.model_narrative import generate_narrative

from core.error_handler import ErrorHandler
from core.agent_policy import AgentPolicy

# Import configuration and connection state
from core.config_manager import config
from core.connection_state import connection_state

# Delegated handlers & utils (modularized)
from server.handlers.relationships_graph import export_relationship_graph as _export_relationship_graph
from server.handlers.full_analysis import run_full_analysis as _run_full_analysis
from server.utils.m_practices import scan_m_practices as _scan_m_practices

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

# Rolling call telemetry (in-memory)
_TELEMETRY_MAX = 200
_telemetry = deque(maxlen=_TELEMETRY_MAX)

# Initialize connection manager
connection_manager = ConnectionManager()
connection_state.set_connection_manager(connection_manager)

app = Server("pbixray-v2.3")
agent_policy = AgentPolicy(config)


# ----------------------------
# Module-level helper utilities
# ----------------------------
def _attach_port_if_connected(result: Any) -> Any:
    """Attach minimal port info on success to reduce token usage."""
    if isinstance(result, dict) and result.get('success') and connection_state.is_connected():
        instance_info = connection_manager.get_instance_info()
        if instance_info and instance_info.get('port'):
            result['port'] = str(instance_info.get('port'))
    return result


def _paginate(result: Any, page_size: Optional[int], next_token: Optional[str], list_keys: List[str]) -> Any:
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


def _schema_sample(rows: List[dict], sample_size: int) -> dict:
    """Return a compact schema section with count and a small sample of rows.

    Keeps payload sizes manageable for very large models while still providing
    a preview. Caller is expected to expose pagination via section/page_size
    if the full dataset is needed.
    """
    try:
        total = len(rows) if isinstance(rows, list) else 0
        n = max(0, int(sample_size))
        sample = rows[:n] if isinstance(rows, list) else []
        return {
            'count': total,
            'sample': sample,
            'truncated': bool(total > n)
        }
    except Exception:
        return {'count': 0, 'sample': [], 'truncated': False}


def _dax_quote_table(name: str) -> str:
    """Escape single quotes in table names for DAX and wrap in single quotes."""
    name = (name or "").replace("'", "''")
    return f"'{name}'"


def _dax_quote_column(name: str) -> str:
    """Escape closing brackets in column names for DAX by doubling.
    DAX uses [Column] notation; a ']' in the name is represented as ']]'."""
    name = (name or "").replace("]", "]]")
    return f"[{name}]"


# ----------------------------
# Standardized notes helpers
# ----------------------------
def _add_note(result: Any, note: str) -> Any:
    try:
        if isinstance(result, dict):
            result.setdefault('notes', []).append(note)
    except Exception:
        pass
    return result


def _note_truncated(result: Any, limit: int) -> Any:
    return _add_note(result, f"Result truncated to {limit} rows for safety.")


def _note_tom_fallback(result: Any) -> Any:
    return _add_note(result, "Used TOM fallback (DMV unavailable on this Desktop build).")


def _note_client_filter_columns(result: Any, table: str) -> Any:
    return _add_note(result, f"Used client-side filtering to select rows for table '{table}'.")


def _note_client_filter_vertipaq(result: Any, table: str) -> Any:
    return _add_note(result, f"Used INFO.STORAGETABLECOLUMNS() with client-side filtering for table '{table}' for cross-version compatibility.")


# ----------------------------
# Small handler groups (reduce call_tool complexity)
# ----------------------------
def _handle_logs_and_health(name: str, arguments: Any) -> Optional[dict]:
    if name == "get_recent_logs":
        lines = int(arguments.get("lines", 200) or 200)
        log_path = LOG_PATH
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            tail = all_lines[-lines:] if lines > 0 else all_lines
            return {"success": True, "logs": "".join(tail)}
        except Exception as e:
            return {"success": False, "error": f"No log file available or could not read logs: {e}"}

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
            return summary
        except Exception as e:
            return {'success': False, 'error': str(e)}

    if name == "get_server_info":
        # Build compact telemetry summary
        try:
            total_calls = len(_telemetry)
            successes = sum(1 for t in _telemetry if t.get('success'))
            failures = total_calls - successes
            last = _telemetry[-1] if total_calls else None
            recent = list(_telemetry)[-10:]
            telemetry_summary = {
                'total_calls': total_calls,
                'successes': successes,
                'failures': failures,
                'last_call': last,
                'recent': recent,
                'capacity': _TELEMETRY_MAX,
            }
        except Exception:
            telemetry_summary = {'error': 'telemetry_unavailable'}
        info = {
            'success': True,
            'version': __version__,
            'server': app.name,
            'connected': connection_state.is_connected(),
            'bpa_available': BPA_AVAILABLE,
            'bpa_status': BPA_STATUS,
            'config': config.get_all(),
            'telemetry': telemetry_summary,
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
        return info

    if name == "health_check":
        now = time.time()
        system_info = {}
        psutil_note = None
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
        return health_info

    return None


def _handle_context_and_limits(name: str, arguments: Any) -> Optional[dict]:
    if name == "get_cache_stats":
        if connection_state and connection_state.query_executor:
            try:
                stats = connection_state.query_executor.get_cache_stats()
            except Exception as e:
                stats = {'success': False, 'error': str(e)}
        else:
            stats = ErrorHandler.handle_manager_unavailable('query_executor')
        return stats

    if name == "get_context":
        keys = arguments.get('keys')
        data = connection_state.get_context(keys) if connection_state else {}
        return {'success': True, 'context': data}

    if name == "set_context":
        data = arguments.get('data', {})
        current = connection_state.set_context(data) if connection_state else {}
        return {'success': True, 'context': current}

    if name == "get_safety_limits":
        limits = connection_state.get_safety_limits() if connection_state else {}
        return {'success': True, 'limits': limits}

    if name == "set_safety_limits":
        limits = {k: v for k, v in arguments.items() if k in {'max_rows_per_call'}}
        current = connection_state.set_safety_limits(limits) if connection_state else {}
        return {'success': True, 'limits': current}

    # summarize_last_result tool removed

    if name == "get_query_history":
        limit = arguments.get('limit')
        try:
            data = connection_state.get_query_history(limit)
            return {'success': True, 'items': data, 'count': len(data)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    if name == "clear_query_history":
        try:
            removed = connection_state.clear_query_history()
            return {'success': True, 'cleared': removed}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    if name == "set_command_timeout":
        try:
            secs = int(arguments.get('seconds'))
        except Exception:
            secs = None
        if secs is None or secs < 0:
            return {'success': False, 'error': 'seconds must be a non-negative integer'}
        if connection_state and connection_state.query_executor:
            try:
                connection_state.query_executor.command_timeout_seconds = secs
                return {'success': True, 'command_timeout_seconds': secs}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        return ErrorHandler.handle_manager_unavailable('query_executor')

    return None


def _handle_perf_baseline(name: str, arguments: Any) -> Optional[dict]:
    if name == "set_perf_baseline":
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        runs = int(arguments.get('runs', 3) or 3)
        elapsed = []
        for _ in range(max(1, runs)):
            r = qe.validate_and_execute_dax(arguments['query'], 0, True)
            if not r.get('success'):
                return r
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
        return saved

    if name == "get_perf_baseline":
        return connection_state.get_perf_baseline(arguments.get('name', ''))

    if name == "list_perf_baselines":
        return connection_state.list_perf_baselines()

    if name == "compare_perf_to_baseline":
        base = connection_state.get_perf_baseline(arguments.get('name', ''))
        if not base.get('success'):
            return base
        baseline = base.get('baseline', {})
        query = arguments.get('query') or baseline.get('query')
        if not query:
            return {'success': False, 'error': 'Query is required if baseline does not store one'}
        runs = int(arguments.get('runs', 3) or 3)
        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        elapsed = []
        for _ in range(max(1, runs)):
            r = qe.validate_and_execute_dax(query, 0, True)
            if not r.get('success'):
                return r
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
        return {'success': True, 'baseline': baseline, 'current': current, 'diff': diff}

    return None


def _handle_connection_and_instances(name: str, arguments: Any) -> Optional[dict]:
    if name == "flush_query_cache":
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        if not connection_state.query_executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        return connection_state.query_executor.flush_cache()

    if name == "ensure_connected":
        return agent_policy.ensure_connected(connection_manager, connection_state, arguments.get("preferred_index"))

    if name == "switch_instance":
        instances = connection_manager.detect_instances()
        if not instances:
            return {'success': False, 'error': 'No instances detected'}
        mode = arguments.get('mode', 'next')
        current = connection_manager.get_instance_info()
        indices = {inst['port']: i for i, inst in enumerate(instances)}
        target_index = 0
        if mode == 'index' and isinstance(arguments.get('index'), int):
            target_index = max(0, min(len(instances) - 1, int(arguments['index'])))
        elif mode in ('next', 'prev') and current and current.get('port') in indices:
            cur_i = indices[current['port']]
            target_index = (cur_i + 1) % len(instances) if mode == 'next' else (cur_i - 1) % len(instances)
        else:
            target_index = 0
        result = connection_manager.connect(target_index)
        if result.get('success'):
            connection_state.set_connection_manager(connection_manager)
            connection_state.initialize_managers(force_reinit=True)
            result['managers_initialized'] = connection_state._managers_initialized
        return result

    if name == "detect_powerbi_desktop":
        instances = connection_manager.detect_instances()
        return {'success': True, 'total_instances': len(instances), 'instances': instances}

    if name == "connect_to_powerbi":
        connection_state.cleanup()
        result = connection_manager.connect(arguments.get("model_index", 0))
        if result.get('success'):
            connection_state.set_connection_manager(connection_manager)
            connection_state.initialize_managers()
            result['managers_initialized'] = connection_state._managers_initialized
            result['performance_analysis'] = 'Available' if connection_state.performance_analyzer else 'Limited'
        return result

    return None


def _handle_agent_tools(name: str, arguments: Any) -> Optional[dict]:
    # Tools that leverage AgentPolicy (some auto-ensure connection)
    if name == "safe_run_dax":
        return agent_policy.safe_run_dax(
            connection_state,
            arguments.get("query", ""),
            arguments.get("mode", "auto"),
            arguments.get("runs"),
            arguments.get("max_rows"),
            arguments.get("verbose", False),
            arguments.get("bypass_cache", False),
            arguments.get("include_event_counts", False),
        )
    if name == "summarize_model":
        # Ensure connection for a smoother experience
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.summarize_model_safely(connection_state)
    if name == "plan_query":
        return agent_policy.plan_query(arguments.get("intent", ""), arguments.get("table"), arguments.get("max_rows"))
    if name == "optimize_variants":
        return agent_policy.optimize_variants(connection_state, arguments.get("candidates", []), arguments.get("runs"))
    if name == "agent_health":
        return agent_policy.agent_health(connection_manager, connection_state)
    if name == "generate_docs_safe":
        return agent_policy.generate_docs_safe(connection_state)
    if name == "relationship_overview":
        return agent_policy.relationship_overview(connection_state)
    if name == "run_dax":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.safe_run_dax(
            connection_state,
            arguments.get("query", ""),
            arguments.get("mode", "auto"),
            arguments.get("runs"),
            arguments.get("top_n"),
            arguments.get("verbose", False),
            False,
            arguments.get("include_event_counts", False),
        )
    if name == "relationships":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.relationship_overview(connection_state)
    if name == "document_model":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        fmt = arguments.get('format', 'markdown')
        include_examples = bool(arguments.get('include_examples', False))
        try:
            return agent_policy.generate_documentation_profiled(connection_state, fmt, include_examples)
        except Exception:
            return agent_policy.generate_docs_safe(connection_state)
    if name == "execute_intent":
        return agent_policy.execute_intent(
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
    if name == "decide_and_run":
        return agent_policy.decide_and_run(
            connection_manager,
            connection_state,
            arguments.get("goal", ""),
            arguments.get("query"),
            arguments.get("candidates"),
            arguments.get("runs"),
            arguments.get("max_rows"),
            arguments.get("verbose", False),
        )
    if name == "propose_analysis":
        return agent_policy.propose_analysis_options(connection_state, arguments.get('goal'))
    if name == "warm_query_cache":
        return agent_policy.warm_query_cache(connection_state, arguments.get('queries', []), arguments.get('runs'), arguments.get('clear_cache', False))
    if name == "analyze_queries_batch":
        inc = bool(arguments.get('include_event_counts', False))
        return agent_policy.analyze_queries_batch(connection_state, arguments.get('queries', []), arguments.get('runs'), arguments.get('clear_cache', True), inc)
    if name == "set_cache_policy":
        return agent_policy.set_cache_policy(connection_state, arguments.get('ttl_seconds'))
    if name == "profile_columns":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.profile_columns(connection_state, arguments.get('table', ''), arguments.get('columns'))
    if name == "get_value_distribution":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.get_value_distribution(connection_state, arguments.get('table', ''), arguments.get('column', ''), arguments.get('top_n', 50))
    if name == "validate_best_practices":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.validate_best_practices(connection_state)
    if name == "generate_documentation_profiled":
        return agent_policy.generate_documentation_profiled(connection_state, arguments.get('format', 'markdown'), arguments.get('include_examples', False))
    if name == "create_model_changelog":
        return agent_policy.create_model_changelog(connection_state, arguments.get('reference_tmsl'))
    if name == "get_measure_impact":
        return agent_policy.get_measure_impact(connection_state, arguments.get('table', ''), arguments.get('measure', ''), arguments.get('depth'))
    if name == "get_column_usage_heatmap":
        return agent_policy.get_column_usage_heatmap(connection_state, arguments.get('table'), arguments.get('limit', 100))
    if name == "auto_document":
        return agent_policy.auto_document(connection_manager, connection_state, arguments.get('profile', 'light'), arguments.get('include_lineage', False))
    if name == "auto_analyze_or_preview":
        return agent_policy.auto_analyze_or_preview(connection_manager, connection_state, arguments.get('query', ''), arguments.get('runs'), arguments.get('max_rows'), arguments.get('priority', 'depth'))
    if name == "apply_recommended_fixes":
        return agent_policy.apply_recommended_fixes(connection_state, arguments.get('actions', []))
    if name == "set_performance_trace":
        return agent_policy.set_performance_trace(connection_state, bool(arguments.get('enabled')))
    if name == "format_dax":
        return agent_policy.format_dax(arguments.get('expression', ''))
    if name == "export_model_overview":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.export_model_overview(connection_state, arguments.get('format', 'json'), arguments.get('include_counts', True))
    if name == "export_columns_with_samples":
        ensured = agent_policy.ensure_connected(connection_manager, connection_state, None)
        if not ensured.get('success'):
            return ensured
        return agent_policy.export_flat_schema_samples(
            connection_state,
            arguments.get('format', 'csv'),
            arguments.get('rows', 3),
            arguments.get('extras', []),
        )
    if name == "auto_route":
        return agent_policy.auto_analyze_or_preview(connection_manager, connection_state, arguments.get('query', ''), arguments.get('runs'), arguments.get('max_rows'), arguments.get('priority', 'depth'))
    return None


def _handle_connected_metadata_and_queries(name: str, arguments: Any) -> Optional[dict]:
    # Require live connection for these tools
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected() if name in {
            "list_tables", "list_measures", "describe_table", "get_measure_details",
            "search_string", "list_calculated_columns", "search_objects", "get_data_sources",
            "get_m_expressions", "preview_table_data", "run_dax_query", "export_model_schema",
            "list_columns", "get_column_values", "get_column_summary", "get_column_value_distribution",
            "list_relationships", "get_vertipaq_stats", "analyze_query_performance", "validate_dax_query",
            "analyze_m_practices", "analyze_model_bpa", "export_relationship_graph", "full_analysis"
        } else None

    qe = connection_state.query_executor
    performance_analyzer = connection_state.performance_analyzer
    bpa_analyzer = connection_state.bpa_analyzer
    model_exporter = connection_state.model_exporter
    performance_optimizer = connection_state.performance_optimizer
    model_validator = connection_state.model_validator

    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    dmv_cap = int(config.get('query.max_rows_preview', config.get('query', {}).get('max_rows_preview', 1000)))

    if name == "list_tables":
        result = qe.execute_info_query("TABLES")
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "list_measures":
        table = arguments.get("table")
        result = qe.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "describe_table":
        table = arguments["table"]
        cols = qe.execute_info_query("COLUMNS", table_name=table)
        measures = qe.execute_info_query("MEASURES", table_name=table, exclude_columns=['Expression'])
        # Fetch all relationships and filter client-side for robustness across engine versions
        rels_all = qe.execute_info_query("RELATIONSHIPS")
        rel_rows = rels_all.get('rows', []) if rels_all.get('success') else []
        filtered_rels = []
        if rel_rows:
            # Prefer direct name columns if present
            if any('FromTable' in r or 'ToTable' in r for r in rel_rows):
                for r in rel_rows:
                    ft = str(r.get('FromTable') or '')
                    tt = str(r.get('ToTable') or '')
                    if ft == str(table) or tt == str(table):
                        filtered_rels.append(r)
            else:
                # Fallback: map IDs to names using INFO.TABLES()
                tbls = qe.execute_info_query("TABLES")
                id_to_name = {}
                if tbls.get('success'):
                    for t in tbls.get('rows', []):
                        tid = t.get('ID') or t.get('TableID')
                        nm = t.get('Name')
                        if tid is not None and nm:
                            id_to_name[str(tid)] = str(nm)
                for r in rel_rows:
                    ftid = r.get('FromTableID') or r.get('[FromTableID]')
                    ttid = r.get('ToTableID') or r.get('[ToTableID]')
                    ft = id_to_name.get(str(ftid)) if ftid is not None else None
                    tt = id_to_name.get(str(ttid)) if ttid is not None else None
                    if ft == str(table) or tt == str(table):
                        # Optionally enrich with resolved names for convenience
                        if ft and 'FromTable' not in r:
                            r['FromTable'] = ft
                        if tt and 'ToTable' not in r:
                            r['ToTable'] = tt
                        filtered_rels.append(r)
        result = {'success': True, 'table': table, 'columns': cols.get('rows', []), 'measures': measures.get('rows', []), 'relationships': filtered_rels}
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
        return result
    if name == "get_measure_details":
        return qe.execute_info_query("MEASURES", filter_expr=f'[Name] = "{arguments["measure"]}"', table_name=arguments["table"])
    if name == "search_string":
        result = qe.search_measures_dax(arguments['search_text'], arguments.get('search_in_expression', True), arguments.get('search_in_name', True))
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "list_calculated_columns":
        table = arguments.get("table")
        filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
        result = qe.execute_info_query("COLUMNS", filter_expr=filter_expr, table_name=table)
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "search_objects":
        result = qe.search_objects_dax(arguments.get("pattern", "*"), arguments.get("types", ["tables", "columns", "measures"]))
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows', 'items'])
    if name == "get_data_sources":
        # Try Desktop-friendly DMV first, then TOM fallback
        attempts = []
        # Attempt 1: TMSCHEMA_DATA_SOURCES (preferred for Desktop)
        dmv_query = f'''EVALUATE
            SELECTCOLUMNS(
                TOPN({dmv_cap}, $SYSTEM.TMSCHEMA_DATA_SOURCES),
                "DataSourceID", [ID],
                "Name", [Name],
                "Description", [Description],
                "Type", [Type]
            )'''
        result = qe.validate_and_execute_dax(dmv_query, dmv_cap)
        attempts.append(('TMSCHEMA_DATA_SOURCES', result.get('success')))
        # If DMV failed or returned an empty set, try TOM fallback which can expose PQ-only sources
        dmv_empty = bool(result.get('success')) and len(result.get('rows', []) or []) == 0
        if (not result.get('success')) or dmv_empty:
            # Attempt 2: TOM fallback
            try:
                result = qe.list_data_sources_tom(dmv_cap)
                attempts.append(('TOM', result.get('success')))
                if result.get('success'):
                    _note_tom_fallback(result)
            except Exception as _e:
                result = {'success': False, 'error': str(_e)}
        if result.get('success') and len(result.get('rows', [])) >= dmv_cap:
            _note_truncated(result, dmv_cap)
        if not result.get('success'):
            # Graceful empty with note
            result = {
                'success': True,
                'rows': [],
                'row_count': 0,
                'attempts': attempts
            }
            _add_note(result, 'Data sources DMV not available; TOM fallback also unavailable on this Desktop build.')
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "get_m_expressions":
        query = f'''EVALUATE
            SELECTCOLUMNS(
                TOPN({dmv_cap}, $SYSTEM.TMSCHEMA_EXPRESSIONS),
                "Name", [Name],
                "Expression", [Expression],
                "Kind", [Kind]
            )'''
        result = qe.validate_and_execute_dax(query, dmv_cap)
        tried_dmv = True
        if not result.get('success'):
            # Fallback to TOM enumeration
            try:
                result = qe.enumerate_m_expressions_tom(dmv_cap)
                tried_dmv = False
                if result.get('success'):
                    _note_tom_fallback(result)
            except Exception as _e:
                result = {'success': False, 'error': str(_e)}
        if result.get('success') and len(result.get('rows', [])) >= dmv_cap:
            _note_truncated(result, dmv_cap)
        # Note: TOM fallback note is standardized above when used
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "preview_table_data":
        limits = connection_state.get_safety_limits()
        max_rows = int(limits.get('max_rows_per_call', 10000))
        req_top = int(arguments.get('top_n', 10) or 10)
        top_n = min(req_top, max_rows) if req_top > 0 else req_top
        result = qe.execute_with_table_reference_fallback(arguments['table'], top_n)
        if req_top != top_n and isinstance(result, dict):
            result.setdefault('notes', []).append(f'top_n clamped to safety limit of {max_rows}')
        return result
    if name == "run_dax_query":
        limits = connection_state.get_safety_limits()
        max_rows = int(limits.get('max_rows_per_call', 10000))
        req_top = int(arguments.get('top_n', 0) or 0)
        top_n = min(req_top, max_rows) if req_top > 0 else req_top
        result = qe.validate_and_execute_dax(arguments['query'], top_n, arguments.get('bypass_cache', False))
        if req_top != top_n and isinstance(result, dict):
            result.setdefault('notes', []).append(f'top_n clamped to safety limit of {max_rows}')
        return result
    if name == "export_model_schema":
        # Optional fine-grained export with pagination for a single section
        section = (arguments.get('section') or '').strip().lower()
        if section in {"tables", "columns", "measures", "relationships"}:
            if section == "tables":
                result = qe.execute_info_query("TABLES")
            elif section == "columns":
                result = qe.execute_info_query("COLUMNS")
            elif section == "measures":
                # Exclude potentially large expressions by default
                result = qe.execute_info_query("MEASURES", exclude_columns=['Expression'])
            else:  # relationships
                result = qe.execute_info_query("RELATIONSHIPS")
            return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])

        # Default: return compact counts + very small samples for each section to avoid
        # producing extremely large responses that UIs struggle to render.
        limits = connection_state.get_safety_limits()
        # Keep the response lean even if the safety limit is high; allow override via preview_size
        try:
            req_preview = int(arguments.get('preview_size')) if arguments.get('preview_size') is not None else None
        except Exception:
            req_preview = None
        # Conservative default sample size; can be increased by caller explicitly
        default_preview = 30
        sample_size = req_preview if (isinstance(req_preview, int) and req_preview >= 0) else default_preview
        # Never exceed global per-call safety limit
        try:
            safety_cap = int(limits.get('max_rows_per_call', 10000) or 10000)
        except Exception:
            safety_cap = 10000
        sample_size = min(sample_size, max(0, safety_cap))

        # Allow callers to restrict which sections to include in the compact payload
        include = arguments.get('include') or ["tables", "columns", "measures", "relationships"]
        try:
            include_set = {str(x).lower() for x in include}
        except Exception:
            include_set = {"tables", "columns", "measures", "relationships"}

        schema = {}
        if "tables" in include_set:
            tables = qe.execute_info_query("TABLES")
            schema['tables'] = _schema_sample(tables.get('rows', []), sample_size)
        if "columns" in include_set:
            columns = qe.execute_info_query("COLUMNS")
            schema['columns'] = _schema_sample(columns.get('rows', []), sample_size)
        if "measures" in include_set:
            measures = qe.execute_info_query("MEASURES", exclude_columns=['Expression'])
            schema['measures'] = _schema_sample(measures.get('rows', []), sample_size)
        if "relationships" in include_set:
            relationships = qe.execute_info_query("RELATIONSHIPS")
            schema['relationships'] = _schema_sample(relationships.get('rows', []), sample_size)

        notes = [
            "Payload reduced for display. For full data, call export_model_schema with 'section' plus optional 'page_size' and 'next_token'.",
            f"Compact preview_size={sample_size}. Override with 'preview_size' or request a single 'section' to page through full rows."
        ]
        result = {
            'success': True,
            'schema': schema,
            'notes': notes
        }
        return result
    if name == "list_columns":
        table = arguments.get("table")
        result = qe.execute_info_query("COLUMNS", table_name=table)
        # Fallback: if table-specific lookup fails, fetch all and filter client-side
        if table and not result.get('success'):
            all_cols = qe.execute_info_query("COLUMNS")
            if all_cols.get('success'):
                rows = [r for r in all_cols.get('rows', []) if str(r.get('Table') or '') == str(table)]
                result = {'success': True, 'rows': rows, 'row_count': len(rows)}
                _note_client_filter_columns(result, str(table))
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "get_column_values":
        t = _dax_quote_table(arguments['table'])
        c = _dax_quote_column(arguments['column'])
        query = f"EVALUATE TOPN({arguments.get('limit', 100)}, VALUES({t}{c}))"
        return qe.validate_and_execute_dax(query)
    if name == "get_column_summary":
        t = _dax_quote_table(arguments['table'])
        c = _dax_quote_column(arguments['column'])
        query = (
            f"EVALUATE ROW(\"Min\", MIN({t}{c}), "
            f"\"Max\", MAX({t}{c}), "
            f"\"Distinct\", DISTINCTCOUNT({t}{c}), "
            f"\"Nulls\", COUNTBLANK({t}{c}))"
        )
        return qe.validate_and_execute_dax(query)
    if name == "get_column_value_distribution":
        return agent_policy.get_value_distribution(connection_state, arguments.get('table', ''), arguments.get('column', ''), arguments.get('top_n', 50))
    if name == "list_relationships":
        active_only = arguments.get("active_only")
        if active_only is True:
            return qe.execute_info_query("RELATIONSHIPS", "[IsActive] = TRUE")
        if active_only is False:
            return qe.execute_info_query("RELATIONSHIPS", "[IsActive] = FALSE")
        return qe.execute_info_query("RELATIONSHIPS")
    if name == "get_vertipaq_stats":
        table = arguments.get("table")
        # Safest cross-version behavior: query full INFO.STORAGETABLECOLUMNS and apply client-side filtering if requested
        dsp = qe.validate_and_execute_dax("EVALUATE INFO.STORAGETABLECOLUMNS()")
        if table and dsp.get('success'):
            t = str(table)
            keys = [
                'TABLE_FULL_NAME', 'TABLE_ID', 'TABLE_NAME', 'Table', 'TABLE', 'Name'
            ]
            def match_row(r: dict) -> bool:
                for k in keys:
                    v = r.get(k)
                    if v is None:
                        continue
                    sv = str(v)
                    if sv == t or t in sv:
                        return True
                return False
            filtered = [r for r in dsp.get('rows', []) if isinstance(r, dict) and match_row(r)]
            res = {'success': True, 'rows': filtered, 'row_count': len(filtered)}
            _note_client_filter_vertipaq(res, str(table))
            return res
        return dsp
    if name == "analyze_query_performance":
        if not performance_analyzer:
            basic = qe.validate_and_execute_dax(arguments['query'], 0, arguments.get('clear_cache', True))
            basic.setdefault('notes', []).append('Performance analyzer not initialized; returned basic execution only')
            basic.setdefault('decision', 'analyze')
            basic.setdefault('reason', 'Requested performance analysis, but analyzer unavailable; returned basic execution')
            return basic
        if not performance_analyzer.amo_server:
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
                qe,
                arguments['query'],
                arguments.get('runs', 3),
                arguments.get('clear_cache', True),
                arguments.get('include_event_counts', False)
            )
            if isinstance(analysis, dict):
                analysis.setdefault('notes', []).append(warning.get('note'))
                analysis.setdefault('warnings', []).append({k: v for k, v in warning.items() if k != 'success'})
            return analysis
        return performance_analyzer.analyze_query(
            qe,
            arguments['query'],
            arguments.get('runs', 3),
            arguments.get('clear_cache', True),
            arguments.get('include_event_counts', False)
        )
    if name == "validate_dax_query":
        return qe.analyze_dax_query(arguments['query'])
    if name == "analyze_m_practices":
        return _scan_m_practices(qe, dmv_cap)
    if name == "analyze_model_bpa":
        if not BPA_AVAILABLE or not bpa_analyzer:
            return ErrorHandler.handle_manager_unavailable('bpa_analyzer')
        tmsl_result = qe.get_tmsl_definition()
        if tmsl_result.get('success'):
            # Prefer fast mode with config-based limits to keep latency down
            bpa_cfg = config.get('bpa', {})
            if hasattr(bpa_analyzer, 'analyze_model_fast'):
                violations = bpa_analyzer.analyze_model_fast(tmsl_result['tmsl'], bpa_cfg)
            else:
                violations = bpa_analyzer.analyze_model(tmsl_result['tmsl'])
            summary = bpa_analyzer.get_violations_summary()
            result = {'success': True, 'violations_count': len(violations), 'summary': summary, 'violations': [{'rule_id': v.rule_id, 'rule_name': v.rule_name, 'category': v.category, 'severity': getattr(v.severity, 'name', str(v.severity)), 'object_type': v.object_type, 'object_name': v.object_name, 'table_name': v.table_name, 'description': v.description} for v in violations]}
            if isinstance(bpa_cfg, dict) and bpa_cfg:
                result.setdefault('notes', []).append('BPA fast mode with configured filters applied')
            return result
        return tmsl_result
    if name == "export_relationship_graph":
        return _export_relationship_graph(qe, arguments.get('format', 'json'))
    if name == "full_analysis":
        return _run_full_analysis(connection_state, config, BPA_AVAILABLE, arguments)
    if name == "analyze_relationship_cardinality":
        return performance_optimizer.analyze_relationship_cardinality() if performance_optimizer else ErrorHandler.handle_manager_unavailable('performance_optimizer')
    if name == "analyze_column_cardinality":
        return performance_optimizer.analyze_column_cardinality(arguments.get('table')) if performance_optimizer else ErrorHandler.handle_manager_unavailable('performance_optimizer')
    if name == "analyze_storage_compression":
        return performance_optimizer.analyze_encoding_efficiency(arguments['table']) if performance_optimizer else ErrorHandler.handle_manager_unavailable('performance_optimizer')
    if name == "validate_model_integrity":
        return model_validator.validate_model_integrity() if model_validator else ErrorHandler.handle_manager_unavailable('model_validator')
    # analyze_data_freshness tool removed from public surface
    return None


def _handle_dependency_and_bulk(name: str, arguments: Any) -> Optional[dict]:
    dependency_analyzer = connection_state.dependency_analyzer
    bulk_operations = connection_state.bulk_operations
    calc_group_manager = connection_state.calc_group_manager
    partition_manager = connection_state.partition_manager
    rls_manager = connection_state.rls_manager
    dax_injector = connection_state.dax_injector
    model_exporter = connection_state.model_exporter

    if name == "analyze_measure_dependencies":
        return dependency_analyzer.analyze_measure_dependencies(
            arguments['table'],
            arguments['measure'],
            arguments.get('depth', 3)
        ) if dependency_analyzer else ErrorHandler.handle_manager_unavailable('dependency_analyzer')
    if name == "find_unused_objects":
        return dependency_analyzer.find_unused_objects() if dependency_analyzer else ErrorHandler.handle_manager_unavailable('dependency_analyzer')
    if name == "analyze_column_usage":
        return dependency_analyzer.analyze_column_usage(arguments['table'], arguments['column']) if dependency_analyzer else ErrorHandler.handle_manager_unavailable('dependency_analyzer')
    if name == "bulk_create_measures":
        return bulk_operations.bulk_create_measures(arguments['measures']) if bulk_operations else ErrorHandler.handle_manager_unavailable('bulk_operations')
    if name == "bulk_delete_measures":
        return bulk_operations.bulk_delete_measures(arguments['measures']) if bulk_operations else ErrorHandler.handle_manager_unavailable('bulk_operations')
    if name == "list_calculation_groups":
        return calc_group_manager.list_calculation_groups() if calc_group_manager else ErrorHandler.handle_manager_unavailable('calc_group_manager')
    if name == "create_calculation_group":
        return calc_group_manager.create_calculation_group(
            arguments['name'],
            arguments['items'],
            arguments.get('description'),
            arguments.get('precedence', 0)
        ) if calc_group_manager else ErrorHandler.handle_manager_unavailable('calc_group_manager')
    if name == "delete_calculation_group":
        return calc_group_manager.delete_calculation_group(arguments['name']) if calc_group_manager else ErrorHandler.handle_manager_unavailable('calc_group_manager')
    if name == "list_partitions":
        return partition_manager.list_table_partitions(arguments.get('table')) if partition_manager else ErrorHandler.handle_manager_unavailable('partition_manager')
    # Refresh operations removed from public tool surface
    if name == "list_roles":
        return rls_manager.list_roles() if rls_manager else ErrorHandler.handle_manager_unavailable('rls_manager')
    if name == "test_role_filter":
        return rls_manager.test_role_filter(arguments['role_name'], arguments['test_query']) if rls_manager else ErrorHandler.handle_manager_unavailable('rls_manager')
    if name == "validate_rls_coverage":
        return rls_manager.validate_rls_coverage() if rls_manager else ErrorHandler.handle_manager_unavailable('rls_manager')
    if name == "upsert_measure":
        return (dax_injector.upsert_measure(
            arguments["table"],
            arguments["measure"],
            arguments["expression"],
            arguments.get("display_folder"),
            arguments.get("description"),
            arguments.get("format_string")
        ) if dax_injector else ErrorHandler.handle_manager_unavailable('dax_injector'))
    if name == "delete_measure":
        return dax_injector.delete_measure(arguments["table"], arguments["measure"]) if dax_injector else ErrorHandler.handle_manager_unavailable('dax_injector')
    if name == "export_tmsl":
        return model_exporter.export_tmsl(arguments.get('include_full_model', False)) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
    if name == "export_tmdl":
        return model_exporter.export_tmdl_structure() if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
    if name == "export_compact_schema":
        return model_exporter.export_compact_schema(arguments.get('include_hidden', True)) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
    if name == "generate_documentation":
        return model_exporter.generate_documentation(connection_state.query_executor) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
    if name == "get_model_summary":
        return model_exporter.get_model_summary(connection_state.query_executor) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
    if name == "compare_models":
        return model_exporter.compare_models(arguments['reference_tmsl']) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
    if name == "apply_tmdl_patch":
        # Safe patch application limited to measures only; supports dry_run
        updates = arguments.get('updates', []) or []
        dry_run = bool(arguments.get('dry_run', False))
        if not isinstance(updates, list) or not updates:
            return {'success': False, 'error': 'updates array is required', 'error_type': 'invalid_input'}
        if not dax_injector:
            return ErrorHandler.handle_manager_unavailable('dax_injector')
        # Validate payload and optionally execute
        plan = []
        results = []
        for u in updates:
            try:
                tbl = (u or {}).get('table')
                meas = (u or {}).get('measure')
                expr = (u or {}).get('expression')
                disp = (u or {}).get('display_folder')
                descr = (u or {}).get('description')
                fmt = (u or {}).get('format_string')
                if not tbl or not meas:
                    results.append({'success': False, 'error': 'Missing table or measure', 'error_type': 'invalid_input', 'item': u})
                    continue
                if expr is None and disp is None and descr is None and fmt is None:
                    results.append({'success': False, 'error': 'No changes specified (need one of expression/display_folder/description/format_string)', 'error_type': 'invalid_input', 'item': u})
                    continue
                if dry_run:
                    plan.append({'action': 'upsert_measure', 'table': tbl, 'measure': meas, 'display_folder': disp, 'description': descr, 'format_string': fmt, 'expression_present': expr is not None})
                else:
                    # Ensure non-None string for expression; injector will handle metadata-only update when empty
                    expr_str = str(expr) if expr is not None else ""
                    res = dax_injector.upsert_measure(str(tbl), str(meas), expr_str, disp, descr, fmt)
                    # Normalize and attach item for traceability
                    if isinstance(res, dict):
                        res.setdefault('table', tbl)
                        res.setdefault('measure', meas)
                    results.append(res)
            except Exception as e:
                results.append({'success': False, 'error': str(e), 'item': u})
        if dry_run:
            return {'success': True, 'dry_run': True, 'planned': plan, 'count': len(plan)}
        ok = all(bool(r.get('success')) for r in results) if results else False
        return {'success': ok, 'updated': sum(1 for r in results if r.get('success')), 'results': results}
    return None


def _dispatch_tool(name: str, arguments: Any) -> dict:
    # 1) Logs/health/server info
    res = _handle_logs_and_health(name, arguments)
    if res is not None:
        return res
    # 2) Context and limits & last-result, timeouts
    res = _handle_context_and_limits(name, arguments)
    if res is not None:
        return res
    # 3) Perf baseline helpers
    res = _handle_perf_baseline(name, arguments)
    if res is not None:
        return res
    # 4) Connection & instance management
    res = _handle_connection_and_instances(name, arguments)
    if res is not None:
        return res
    # 5) Agent-policy driven tools
    res = _handle_agent_tools(name, arguments)
    if res is not None:
        return _attach_port_if_connected(res)
    # 6) Connected metadata & query tools
    res = _handle_connected_metadata_and_queries(name, arguments)
    if res is not None:
        return _attach_port_if_connected(res)
    # 7) Dependency, bulk ops, calc groups, partitions, RLS, model export
    res = _handle_dependency_and_bulk(name, arguments)
    if res is not None:
        return _attach_port_if_connected(res)
    # Unknown tool
    return ErrorHandler.handle_unknown_tool(name)


@app.list_tools()
async def list_tools() -> List[Tool]:
    # Public, simplified tool surface
    tools = [
        # Combined DAX runner (preview/analyze)
    Tool(name="run_dax", description="Run a DAX query (preview/analyze) with safe limits", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string", "enum": ["auto", "preview", "analyze"], "default": "auto"}, "runs": {"type": "integer"}, "top_n": {"type": "integer"}, "verbose": {"type": "boolean", "default": False}, "include_event_counts": {"type": "boolean", "default": False}}, "required": ["query"]}),
        Tool(name="summarize_model", description="Lightweight model summary suitable for large models", inputSchema={"type": "object", "properties": {}, "required": []}),
    Tool(name="document_model", description="Generate documentation or overview for the model", inputSchema={"type": "object", "properties": {"format": {"type": "string", "enum": ["markdown", "html", "json"], "default": "markdown"}, "include_examples": {"type": "boolean", "default": False}}, "required": []}),
    # plan_query intentionally hidden from public tool list (still callable internally)
    # optimize_variants: intentionally hidden from public tool list (used internally by agent_policy)
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
        Tool(
            name="export_model_schema",
            description="Export model schema (compact overview by default; use 'section' to page through full data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {"type": "string", "enum": ["tables", "columns", "measures", "relationships"]},
                    "page_size": {"type": "integer"},
                    "next_token": {"type": "string"},
                    "preview_size": {"type": "integer", "description": "Rows per section in compact preview (default 30)"},
                    "include": {"type": "array", "items": {"type": "string"}, "description": "Subset of sections to include in compact preview"}
                },
                "required": []
            }
    ),
    Tool(name="upsert_measure", description="Create/update measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}, "description": {"type": "string"}, "format_string": {"type": "string"}}, "required": ["table", "measure", "expression"]}),
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

        # Diagnostics and maintenance (trimmed; hide cache/safety/agent internals)
    # warm_query_cache: intentionally hidden from public tool list (internal utility)
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
    tools.append(Tool(name="export_relationship_graph", description="Export relationships as a graph (JSON or GraphML)", inputSchema={"type": "object", "properties": {"format": {"type": "string", "enum": ["json", "graphml"], "default": "json"}}, "required": []}))
    tools.append(Tool(name="apply_tmdl_patch", description="Apply safe TMDL patch operations (measures only)", inputSchema={"type": "object", "properties": {"updates": {"type": "array", "items": {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}, "description": {"type": "string"}, "format_string": {"type": "string"}}, "required": ["table", "measure"]}}, "dry_run": {"type": "boolean", "default": False}}, "required": ["updates"]}))
    tools.append(Tool(name="export_compact_schema", description="Export compact model schema (no expressions) for reliable diffs",
                      inputSchema={"type": "object", "properties": {"include_hidden": {"type": "boolean", "default": True}}, "required": []}))
    # Orchestrated comprehensive analysis
    tools.append(Tool(name="full_analysis", description="Run a comprehensive model analysis (summary, relationships, best practices, M scan, optional BPA)", inputSchema={"type": "object", "properties": {"include_bpa": {"type": "boolean", "default": True}, "depth": {"type": "string", "enum": ["light", "standard", "deep"], "default": "standard"}, "profile": {"type": "string", "enum": ["fast", "balanced", "deep"], "default": "balanced"}, "limits": {"type": "object", "properties": {"relationships_max": {"type": "integer", "default": 200}, "issues_max": {"type": "integer", "default": 200}}, "default": {}}}, "required": []}))
    # Proposal helper so the agent can offer options to the user
    tools.append(Tool(name="propose_analysis", description="Propose normal vs fast analysis options depending on need", inputSchema={"type": "object", "properties": {"goal": {"type": "string"}}, "required": []}))
    # Export flat schema with sample values per column
    tools.append(Tool(
        name="export_columns_with_samples",
        description="Export flat list of all tables and columns with top sample values (txt/csv/xlsx). Supports extras like Description, IsHidden, IsNullable, IsKey, SummarizeBy.",
        inputSchema={
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": ["csv", "txt", "xlsx"], "default": "csv"},
                "rows": {"type": "integer", "default": 3},
                "extras": {"type": "array", "items": {"type": "string"}, "default": []}
            },
            "required": []
        }
    ))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    try:
        _t0 = time.time()
        result = _dispatch_tool(name, arguments)
        _dur = round((time.time() - _t0) * 1000, 2)
        try:
            _telemetry.append({
                'name': name,
                'duration_ms': _dur,
                'success': bool(isinstance(result, dict) and result.get('success', False)),
                'ts': time.time()
            })
        except Exception:
            pass
        # Special-case get_recent_logs to return plain text to preserve formatting in clients
        if name == "get_recent_logs" and isinstance(result, dict) and 'logs' in result:
            return [TextContent(type="text", text=result['logs'])]
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
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
