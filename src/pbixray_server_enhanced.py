#!/usr/bin/env python3
"""
MCP-PowerBi-Finvision Server v2.3 - Professional Edition
Uses modular core services with enhanced DAX execution and error handling.
"""

import asyncio
import json
import logging
import sys
import os
import time
import re
from collections import deque
from typing import Any, List, Optional, Callable, Dict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from datetime import datetime

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from __version__ import __version__
from core.connection_manager import ConnectionManager
from core.query_executor import COLUMN_TYPE_CALCULATED
from core.constants import QueryLimits

from core.error_handler import ErrorHandler
from core.tool_timeouts import ToolTimeoutManager
from core.cache_manager import EnhancedCacheManager, create_cache_manager
from core.input_validator import InputValidator
from core.rate_limiter import RateLimiter

from core.agent_policy import AgentPolicy

# Import configuration and connection state
from core.config_manager import config
from core.connection_state import connection_state

# Delegated handlers & utils (modularized)
from server.handlers.relationships_graph import export_relationship_graph as _export_relationship_graph
from server.handlers.full_analysis import run_full_analysis as _run_full_analysis
from server.handlers.visualization_tools import create_viz_tool_handlers
from server.utils.m_practices import scan_m_practices as _scan_m_practices

BPA_AVAILABLE = False
BPA_STATUS = {"available": False, "reason": None}
try:
    from core.bpa_analyzer import BPAAnalyzer
    BPA_AVAILABLE = True
    BPA_STATUS["available"] = True
except ImportError as e:
    logging.getLogger("mcp_powerbi_finvision").warning(f"BPA not available: {e}")
    BPA_STATUS["reason"] = str(e)
except Exception as e:
    logging.getLogger("mcp_powerbi_finvision").warning(f"Unexpected error loading BPA: {e}")
    BPA_STATUS["reason"] = str(e)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_powerbi_finvision")

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
_TELEMETRY_MAX = getattr(QueryLimits, 'TELEMETRY_BUFFER_SIZE', 200)
_telemetry = deque(maxlen=_TELEMETRY_MAX)

# Initialize connection manager
connection_manager = ConnectionManager()
# Initialize enhanced managers
timeout_manager = ToolTimeoutManager(config.get('tool_timeouts', {}))
# Build enhanced cache manager from full config dict
try:
    enhanced_cache = create_cache_manager(config.get_all())
except Exception:
    # Fallback to defaults if config manager changes shape
    enhanced_cache = EnhancedCacheManager()
rate_limiter = RateLimiter(config.get('rate_limiting', {}))


connection_state.set_connection_manager(connection_manager)

app = Server("MCP-PowerBi-Finvision")
agent_policy = AgentPolicy(
    config,
    timeout_manager=timeout_manager,
    cache_manager=enhanced_cache,
    rate_limiter=rate_limiter
)


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
# Row normalization helpers (cross-version DMV/TOM field variance)
# ----------------------------
def _norm_identifier(val: Any) -> str:
    try:
        s = str(val or "")
        # Remove wrapping brackets/quotes often present in DMVs
        if s.startswith("[") and s.endswith("]"):
            s = s[1:-1]
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        return s
    except Exception:
        return ""


def _row_table_name(row: dict) -> str:
    for k in ("Table", "TABLE_NAME", "TableName", "table", "[Table]", "TABLE"):
        if k in row and row[k] not in (None, ""):
            return _norm_identifier(row[k])
    # Some DMV variants embed table in a compound name; last resort attempt
    if 'FromTable' in row or 'ToTable' in row:
        # Not a column/measure row, ignore
        pass
    return ""


def _row_measure_name(row: dict) -> str:
    for k in ("Name", "MEASURE_NAME", "[Name]"):
        if k in row and row[k] not in (None, ""):
            return _norm_identifier(row[k])
    return ""


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

    if name == "get_runtime_cache_stats":
        try:
            stats = enhanced_cache.get_stats()
            stats['success'] = True
            return stats
        except Exception as e:
            return {'success': False, 'error': str(e)}

    if name == "get_rate_limit_stats":
        try:
            return {'success': True, 'stats': rate_limiter.get_stats()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    if name == "get_tool_timeouts":
        try:
            return {'success': True, 'timeouts': timeout_manager.get_all_timeouts()}
        except Exception as e:
            return {'success': False, 'error': str(e)}

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
            # Provide Quickstart guide path for first-time users
            try:
                parent = os.path.dirname(script_dir)
                guides_dir = os.path.join(parent, 'docs')
                os.makedirs(guides_dir, exist_ok=True)
                pdf_path = os.path.join(guides_dir, 'PBIXRAY_Quickstart.pdf')
                if not os.path.exists(pdf_path):
                    _write_quickstart_assets(guides_dir)
                # If still not present, fall back to .txt
                result['quickstart_guide'] = pdf_path if os.path.exists(pdf_path) else os.path.join(guides_dir, 'PBIXRAY_Quickstart.txt')
                # Also include an excerpt so clients can show something inline
                try:
                    excerpt = _generate_quickstart_markdown().splitlines()[:16]
                    result['quickstart_excerpt'] = "\n".join(excerpt)
                    result['open_hint'] = "Open the quickstart_guide path locally to view the full PDF."
                    # Add an explicit top-level message/notes so clients like Claude show it
                    msg = f"Connected successfully. Quickstart guide available at: {result['quickstart_guide']}"
                    result.setdefault('message', msg)
                    result.setdefault('notes', []).append(msg)
                except Exception:
                    pass
            except Exception:
                pass
            # Add a short summary to help AI clients display guidance inline
            try:
                result.setdefault('summary', 'Connected to Power BI Desktop. Use list_tools to discover capabilities. Quickstart guide path returned for details.')
                result.setdefault('hints', [
                    'Try: get_model_summary, analyze_measure_dependencies, find_unused_objects',
                    'Use describe_table to inspect schema; search_objects to find fields',
                ])
            except Exception:
                pass
        return result

    return None


def _write_quickstart_assets(guides_dir: str) -> None:
    """Create Quickstart content in docs/ as PDF (or .txt fallback)."""
    md = _generate_quickstart_markdown()
    md_path = os.path.join(guides_dir, 'PBIXRAY_Quickstart.md')
    try:
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md)
    except Exception:
        pass
    pdf_path = os.path.join(guides_dir, 'PBIXRAY_Quickstart.pdf')
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        y = height - 40
        for line in md.splitlines():
            if not line.strip():
                y -= 10
                continue
            # Basic heading emphasis
            text = line
            if line.startswith('#'):
                text = line.lstrip('# ').strip()
            c.drawString(40, y, text[:110])
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 40
        c.save()
    except Exception:
        # Fallback to .txt
        txt = os.path.join(guides_dir, 'PBIXRAY_Quickstart.txt')
        with open(txt, 'w', encoding='utf-8') as f:
            f.write(md)


def _generate_quickstart_markdown() -> str:
    now = datetime.now().strftime('%Y-%m-%d')
    lines = [
        f"# MCP-PowerBi-Finvision Quickstart Guide ({now})",
        "",
        "MCP-PowerBi-Finvision is a Model Context Protocol (MCP) server for Power BI Desktop. It lets tools/agents inspect and analyze your open model safely.",
        "",
        "What you can do:",
        "- Connect to an open Power BI Desktop model",
        "- List tables/columns/measures and preview data",
        "- Search objects and inspect data sources and M expressions",
        "- Run Best Practice Analyzer (BPA) on the model",
        "- Analyze relationships, column cardinality, VertiPaq stats",
        "- Generate documentation and export TMSL/TMDL",
        "- Validate RLS coverage and DAX syntax",
        "",
        "Popular tools (friendly names):",
        "- connection: detect powerbi desktop | connection: connect to powerbi",
        "- list: tables | list: columns | list: measures | describe: table | preview: table",
        "- search: objects | search: text in measures | get: data sources | get: m expressions",
        "- analysis: best practices (BPA) | analysis: relationship/cardinality | analysis: storage compression",
    "- usage: find unused objects",
        "- export: compact schema | export: tmsl | export: tmdl | docs: generate",
        "",
        "Tips:",
        "- Large results are paged; use page_size + next_token",
        "- Some Desktop builds hide DMVs; the server falls back to TOM or client-side filtering",
        "- Use list_tools to see all tool names and schemas",
        "",
        "Troubleshooting:",
        "- Use get_recent_logs and get_server_info",
        "- Ensure ADOMD/AMO DLLs exist in lib/dotnet for advanced features",
    ]
    return "\n".join(lines)


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
    # get_column_usage_heatmap removed from public surface
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
            arguments.get('output_dir'),
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

    try:
        dmv_cap = int(config.get('query.max_rows_preview', config.get('query', {}).get('max_rows_preview', QueryLimits.DMV_DEFAULT_CAP)))
    except Exception:
        dmv_cap = getattr(QueryLimits, 'DMV_DEFAULT_CAP', 1000)

    if name == "list_tables":
        result = qe.execute_info_query("TABLES")
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "list_measures":
        table = arguments.get("table")
        result = qe.execute_info_query_with_fallback("MEASURES", table_name=table, exclude_columns=['Expression'])
        return _paginate(result, arguments.get('page_size'), arguments.get('next_token'), ['rows'])
    if name == "describe_table":
        table = arguments["table"]
        # Use unified fallback to reduce duplication and improve cross-version robustness
        cols = qe.execute_info_query_with_fallback("COLUMNS", table_name=table)
        measures = qe.execute_info_query_with_fallback("MEASURES", table_name=table, exclude_columns=['Expression'])
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
                        # Prefer bracketed keys first for Desktop builds that return [ID]
                        tid = t.get('[ID]') or t.get('ID') or t.get('[TableID]') or t.get('TableID')
                        nm = t.get('Name') or t.get('[Name]')
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
        return qe.get_measure_details_with_fallback(arguments["table"], arguments["measure"])
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
        result = qe.execute_info_query_with_fallback("COLUMNS", table_name=table)
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
        dsp = qe.validate_and_execute_dax("EVALUATE INFO.STORAGETABLECOLUMNS()")
        if not dsp.get('success'):
            return dsp

        rows = list(dsp.get('rows') or [])
        if table:
            t = str(table)
            keys = [
                'TABLE_FULL_NAME',
                'TABLE_ID',
                'TABLE_NAME',
                'Table',
                'TABLE',
                'Name',
                '[TABLE_ID]',
                '[TABLE_NAME]',
                '[MEASURE_GROUP_NAME]',
                '[DIMENSION_NAME]',
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

            filtered = [r for r in rows if isinstance(r, dict) and match_row(r)]
            if filtered:
                rows = filtered
                dsp = {k: v for k, v in dsp.items() if k != 'rows'}
                dsp['rows'] = rows
                _note_client_filter_vertipaq(dsp, t)

        total_rows = len(rows)
        try:
            page_size = int(arguments.get("page_size", 400) or 400)
        except Exception:
            page_size = 400
        page_size = max(50, min(page_size, 1000))

        try:
            start = int(arguments.get("next_token", 0) or 0)
        except Exception:
            start = 0
        start = max(0, min(start, max(total_rows - 1, 0)))
        end = start + page_size

        paged_rows = rows[start:end]
        result = {k: v for k, v in dsp.items() if k != 'rows' and k != 'row_count'}
        result['rows'] = paged_rows
        result['row_count'] = len(paged_rows)
        result['total_rows'] = total_rows
        if end < total_rows:
            result['next_token'] = str(end)
        if start > 0:
            prev = max(0, start - page_size)
            if prev != start:
                result['previous_token'] = str(prev)
        if total_rows > page_size:
            _note_truncated(result, page_size)
            result.setdefault('notes', []).append(
                "Use page_size/next_token arguments to page through the complete VertiPaq stats dataset."
            )
        return result
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
        try:
            # Lazy-init BPA if feature enabled but analyzer missing
            if (not bpa_analyzer) and hasattr(connection_state, '_initialize_bpa') and getattr(config, 'is_feature_enabled', lambda x: True)('enable_bpa'):
                try:
                    connection_state._initialize_bpa(False)  # best-effort
                    bpa_analyzer = connection_state.bpa_analyzer
                except Exception:
                    pass
            if not BPA_AVAILABLE or not bpa_analyzer:
                return ErrorHandler.handle_manager_unavailable('bpa_analyzer')
            tmsl_result = qe.get_tmsl_definition()
            if tmsl_result.get('success'):
                # Prefer fast/balanced modes by default; allow caller override
                mode = (arguments.get('mode') or 'fast').lower()
                req_cats = arguments.get('categories')
                # Start from default config then apply overrides
                bpa_cfg = dict(config.get('bpa', {}) or {})
                if isinstance(req_cats, list) and req_cats:
                    bpa_cfg['include_categories'] = req_cats
                # Apply mode presets
                if mode == 'fast':
                    # keep defaults
                    pass
                elif mode == 'balanced':
                    bpa_cfg['max_seconds'] = max(30, int(bpa_cfg.get('max_seconds', 20)))
                    bpa_cfg['per_rule_max_ms'] = max(250, int(bpa_cfg.get('per_rule_max_ms', 150)))
                elif mode == 'deep':
                    # remove most limits, run longer in fast engine
                    bpa_cfg.pop('max_rules', None)
                    bpa_cfg.pop('max_tables', None)
                    bpa_cfg['max_seconds'] = 90
                    bpa_cfg['per_rule_max_ms'] = 500
                    # widen per-scope caps
                    bpa_cfg['max_columns_per_rule'] = 10_000
                    bpa_cfg['max_measures_per_rule'] = 10_000
                    bpa_cfg['max_relationships_per_rule'] = 10_000
                # Caller can hard override seconds
                if isinstance(arguments.get('max_seconds'), (int, float)):
                    bpa_cfg['max_seconds'] = float(arguments.get('max_seconds'))
                # Execute
                if hasattr(bpa_analyzer, 'analyze_model_fast') and mode in ('fast','balanced','deep'):
                    violations = bpa_analyzer.analyze_model_fast(tmsl_result['tmsl'], bpa_cfg)
                else:
                    violations = bpa_analyzer.analyze_model(tmsl_result['tmsl'])
                summary = bpa_analyzer.get_violations_summary()
                result = {'success': True, 'violations_count': len(violations), 'summary': summary, 'violations': [{'rule_id': v.rule_id, 'rule_name': v.rule_name, 'category': v.category, 'severity': getattr(v.severity, 'name', str(v.severity)), 'object_type': v.object_type, 'object_name': v.object_name, 'table_name': v.table_name, 'description': v.description} for v in violations]}
                if isinstance(bpa_cfg, dict) and bpa_cfg:
                    result.setdefault('notes', []).append('BPA fast mode with configured filters applied')
                # Surface run-time notes from analyzer (timeouts, truncation, per-rule slow warnings)
                if hasattr(bpa_analyzer, 'get_run_notes'):
                    notes = bpa_analyzer.get_run_notes()
                    if notes:
                        result.setdefault('notes', []).extend(notes)
                # Clarify the common confusion around date table rule naming heuristics
                result.setdefault('notes', []).append(
                    'Note: The BPA "Date/calendar tables should be marked as a date table" rule pattern-matches table names and checks DataCategory/IsKey. '
                    'If you recently marked a table as a date table in Desktop and still see warnings, refresh TMSL export or ignore name-based matches.'
                )
                result['mode'] = mode
                return result
            return tmsl_result
        except Exception as _e:
            return {'success': False, 'error': str(_e), 'error_type': 'bpa_error'}
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


# ----------------------------
# Register a few common handlers via registry
# ----------------------------
def _h_list_tables(args: Any) -> dict:
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()
    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')
    result = qe.execute_info_query("TABLES")
    return _paginate(result, args.get('page_size'), args.get('next_token'), ['rows'])


def _h_list_columns(args: Any) -> dict:
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()
    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')
    table = args.get('table')
    res = qe.execute_info_query_with_fallback("COLUMNS", table_name=table)
    return _paginate(res, args.get('page_size'), args.get('next_token'), ['rows'])


def _h_list_measures(args: Any) -> dict:
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()
    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')
    table = args.get('table')
    res = qe.execute_info_query_with_fallback("MEASURES", table_name=table, exclude_columns=['Expression'])
    return _paginate(res, args.get('page_size'), args.get('next_token'), ['rows'])


def _h_describe_table(args: Any) -> dict:
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()
    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')
    table = args.get('table')
    cols = qe.execute_info_query_with_fallback("COLUMNS", table_name=table)
    measures = qe.execute_info_query_with_fallback("MEASURES", table_name=table, exclude_columns=['Expression'])
    rels_all = qe.execute_info_query("RELATIONSHIPS")
    rel_rows = rels_all.get('rows', []) if rels_all.get('success') else []
    filtered_rels = []
    if rel_rows:
        if any('FromTable' in r or 'ToTable' in r for r in rel_rows):
            for r in rel_rows:
                ft = str(r.get('FromTable') or '')
                tt = str(r.get('ToTable') or '')
                if ft == str(table) or tt == str(table):
                    filtered_rels.append(r)
        else:
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
                    if ft and 'FromTable' not in r:
                        r['FromTable'] = ft
                    if tt and 'ToTable' not in r:
                        r['ToTable'] = tt
                    filtered_rels.append(r)
    result = {'success': True, 'table': table, 'columns': cols.get('rows', []), 'measures': measures.get('rows', []), 'relationships': filtered_rels}
    # paginate per-section
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
    c, c_next = _slice(result['columns'], args.get('columns_page_size'), args.get('columns_next_token'))
    m, m_next = _slice(result['measures'], args.get('measures_page_size'), args.get('measures_next_token'))
    r, r_next = _slice(result['relationships'], args.get('relationships_page_size'), args.get('relationships_next_token'))
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


# Register
__DEFERRED_REGISTRATION__ = [
    ('list_tables', _h_list_tables),
    ('list_columns', _h_list_columns),
    ('list_measures', _h_list_measures),
    ('describe_table', _h_describe_table),
    # Helper tool to surface Quickstart guide and excerpt on demand
    ('show_quickstart', lambda args: (lambda: (
        (lambda guides_dir: (lambda pdf_path: (
            (lambda guide_path: {
                'success': True,
                'quickstart_guide': guide_path,
                'quickstart_excerpt': ("\n".join(_generate_quickstart_markdown().splitlines()[:16]) if True else None),
                'open_hint': 'Open the quickstart_guide path locally to view the full PDF.',
                'summary': f'Quickstart guide available at: {guide_path}'
            })(pdf_path if os.path.exists(pdf_path) else os.path.join(guides_dir, 'PBIXRAY_Quickstart.txt'))
        ))(os.path.join(guides_dir, 'PBIXRAY_Quickstart.pdf'))
    ))(os.path.join(os.path.dirname(script_dir), 'docs')) )()),
]


def _handle_dependency_and_bulk(name: str, arguments: Any) -> Optional[dict]:
    dependency_analyzer = connection_state.dependency_analyzer
    bulk_operations = connection_state.bulk_operations
    calc_group_manager = connection_state.calc_group_manager
    partition_manager = connection_state.partition_manager
    rls_manager = connection_state.rls_manager
    dax_injector = connection_state.dax_injector
    # Ensure model_exporter is available even if managers weren't fully initialized
    model_exporter = connection_state.model_exporter
    if model_exporter is None:
        try:
            model_exporter = connection_state._ensure_model_exporter()
        except Exception as _e:
            logger.warning(f"Failed lazy init of model_exporter: {_e}")

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
        fmt = (arguments.get('format') or 'json').lower()
        include_hidden = arguments.get('include_hidden', True)
        if fmt == 'xlsx':
            return agent_policy.export_compact_schema_xlsx(connection_state, include_hidden, arguments.get('output_dir'))
        return model_exporter.export_compact_schema(include_hidden) if model_exporter else ErrorHandler.handle_manager_unavailable('model_exporter')
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


# Friendly alias map: expose user-friendly names while keeping canonical names working
FRIENDLY_TOOL_ALIASES = {
    # Connection & basics
    "Find Power BI Desktop": "detect_powerbi_desktop",
    "Connect to Power BI": "connect_to_powerbi",
    "Run DAX (safe)": "run_dax",
    # Explore & inspect
    "Inspect: List tables": "list_tables",
    "Inspect: List columns": "list_columns",
    "Inspect: List measures": "list_measures",
    "Inspect: Calculated columns": "list_calculated_columns",
    "Inspect: Describe table": "describe_table",
    "Inspect: Preview table": "preview_table_data",
    "Search: Text in measures": "search_string",
    "Search: Objects": "search_objects",
    "Inspect: Measure details": "get_measure_details",
    "Inspect: Data sources": "get_data_sources",
    "Inspect: M expressions": "get_m_expressions",
    # Profiling & data
    "Profile: Columns": "profile_columns",
    "Profile: Value distribution": "get_column_value_distribution",
    "Column summary": "get_column_summary",
    "VertiPaq stats": "get_vertipaq_stats",
    # Dependencies & impact
    "Dependencies: Measure": "analyze_measure_dependencies",
    "Impact: Measure": "get_measure_impact",
    # heatmap removed from public surface
    "Dependencies: Column usage": "analyze_column_usage",
    "Find unused objects": "find_unused_objects",
    # Model management
    "Measure: Upsert": "upsert_measure",
    "Measure: Delete": "delete_measure",
    "Measures: Bulk create": "bulk_create_measures",
    "Measures: Bulk delete": "bulk_delete_measures",
    "Calc groups: List": "list_calculation_groups",
    "Calc group: Create": "create_calculation_group",
    "Calc group: Delete": "delete_calculation_group",
    "Partitions: List": "list_partitions",
    # Security
    "Security: List roles": "list_roles",
    "Security: Validate RLS": "validate_rls_coverage",
    # Validation & governance
    "Validate: DAX": "validate_dax_query",
    "Validate: Model integrity": "validate_model_integrity",
    "Best practices (BPA)": "analyze_model_bpa",
    "Best practices: M queries": "analyze_m_practices",
    # Performance
    "Performance: Analyze queries": "analyze_queries_batch",
    "Performance: Relationship cardinality": "analyze_relationship_cardinality",
    "Performance: Column cardinality": "analyze_column_cardinality",
    "Performance: Storage compression": "analyze_storage_compression",
    # Docs & export
    "Export: Columns with samples": "export_columns_with_samples",
    "Export: Compact schema": "export_compact_schema",
    "Export: Relationships graph": "export_relationship_graph",
    "Export: TMSL": "export_tmsl",
    "Export: TMDL": "export_tmdl",
    "Docs: Generate": "generate_documentation",
    "Docs: Overview": "export_model_overview",
    "Model: Summary": "get_model_summary",
    "Compare: Models": "compare_models",
    "Schema: Relationships": "relationships",
    # Renamed for clarity; keep old alias too below
    "Export: Model schema (sections)": "export_model_schema",
    # Orchestration
    "Analyze: Full model": "full_analysis",
    # Renamed for clarity; keep old alias too below
    "Analysis: Recommend analysis plan": "propose_analysis",
    # New alphabetized friendly names (v2.3 style)
    # analysis:
    "analysis: best practices (BPA)": "analyze_model_bpa",
    "analysis: column cardinality": "analyze_column_cardinality",
    "analysis: full model": "full_analysis",
    "analysis: m query practices": "analyze_m_practices",
    "analysis: performance (batch)": "analyze_queries_batch",
    "analysis: relationship cardinality": "analyze_relationship_cardinality",
    "analysis: storage compression": "analyze_storage_compression",
    # calc groups:
    "calc: create calculation group": "create_calculation_group",
    "calc: delete calculation group": "delete_calculation_group",
    "calc: list calculation groups": "list_calculation_groups",
    # connection:
    "connection: connect to powerbi": "connect_to_powerbi",
    "connection: detect powerbi desktop": "detect_powerbi_desktop",
    # describe/search/get:
    "describe: table": "describe_table",
    "get: column summary": "get_column_summary",
    # Renamed surface label for clarity under profiling context
    "profile: top values for column": "get_column_value_distribution",
    "get: data sources": "get_data_sources",
    "get: m expressions": "get_m_expressions",
    "get: measure details": "get_measure_details",
    "get: model summary": "get_model_summary",
    "get: vertipaq stats": "get_vertipaq_stats",
    "list: calculated columns": "list_calculated_columns",
    "list: columns": "list_columns",
    "list: measures": "list_measures",
    "list: partitions": "list_partitions",
    "list: relationships": "relationships",
    "list: roles": "list_roles",
    "list: tables": "list_tables",
    # measure ops:
    "measure: bulk create": "bulk_create_measures",
    "measure: bulk delete": "bulk_delete_measures",
    "measure: delete": "delete_measure",
    # Friendlier name for Power BI users
    "measure: create or update": "upsert_measure",
    # export/docs:
    "export: columns with samples": "export_columns_with_samples",
    "export: compact schema": "export_compact_schema",
    "export: model overview": "export_model_overview",
    "export: relationships graph": "export_relationship_graph",
    "export: schema (paged)": "export_model_schema",
    "export: tmdl": "export_tmdl",
    "export: tmsl": "export_tmsl",
    # performance/run
    "run: dax": "run_dax",
    # search:
    "search: objects": "search_objects",
    "search: text in measures": "search_string",
    # security/validate
    "security: validate rls": "validate_rls_coverage",
    "security: list roles": "list_roles",
    "validate: dax": "validate_dax_query",
    "validate: model integrity": "validate_model_integrity",
    # preview
    "preview: table": "preview_table_data",
    # spelling variant (user typo safety)
    "anlysis: full model": "full_analysis",
    # Back-compat entries for renamed labels
    "Schema: Export (paged)": "export_model_schema",
    "Analyze: Propose plan": "propose_analysis",
    "get: column value distribution": "get_column_value_distribution",
    "measure: upsert": "upsert_measure",
    # Visualization mockup tools
    "viz: prepare dashboard data": "viz_prepare_dashboard_data",
    "viz: get chart data": "viz_get_chart_data",
    "viz: recommend visualizations": "viz_recommend_visualizations",
    "Viz: Dashboard data": "viz_prepare_dashboard_data",
    "Viz: Chart data": "viz_get_chart_data",
    "Viz: Recommendations": "viz_recommend_visualizations",
}

# Lightweight handler registry (progressive migration)
Handler = Callable[[Any], dict]
_HANDLERS: Dict[str, Handler] = {}

try:
    _VIZ_HANDLERS: Dict[str, Handler] = create_viz_tool_handlers(connection_state, config)
except Exception as _viz_error:
    logger.debug(f"Visualization handlers unavailable: {_viz_error}")
    _VIZ_HANDLERS = {}

def register_handler(tool_name: str, func: Handler) -> None:
    try:
        _HANDLERS[tool_name] = func
    except Exception:
        pass

# Perform deferred registrations if any were defined earlier in the module
try:
    for tn, fn in list(globals().get('__DEFERRED_REGISTRATION__', []) or []):
        try:
            register_handler(tn, fn)
        except Exception:
            pass
    # Clear to avoid duplicates on reload
    if '__DEFERRED_REGISTRATION__' in globals():
        globals()['__DEFERRED_REGISTRATION__'] = []
except Exception:
    pass


def _dispatch_tool(name: str, arguments: Any) -> dict:
    # Normalize friendly aliases to canonical tool names
    try:
        # Tolerate legacy typo prefix 'anlysis:' by rewriting to 'analysis:'
        if isinstance(name, str) and name.lower().startswith('anlysis:'):
            name = 'analysis:' + name[len('anlysis:'):]
        name = FRIENDLY_TOOL_ALIASES.get(name, name)
    except Exception:
        pass
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
    # 6) Registered handlers (progressive routing)
    handler = _HANDLERS.get(name)
    if handler is not None:
        try:
            return _attach_port_if_connected(handler(arguments))
        except Exception as e:
            return ErrorHandler.handle_unexpected_error(name, e)
    # 7) Connected metadata & query tools
    res = _handle_connected_metadata_and_queries(name, arguments)
    if res is not None:
        return _attach_port_if_connected(res)
    # 8) Dependency, bulk ops, calc groups, partitions, RLS, model export
    res = _handle_dependency_and_bulk(name, arguments)
    if res is not None:
        return _attach_port_if_connected(res)
    # 9) Visualization mockup tools
    global _VIZ_HANDLERS
    handler = _VIZ_HANDLERS.get(name)
    if handler is None and isinstance(name, str) and name.startswith('viz_'):
        try:
            _VIZ_HANDLERS = create_viz_tool_handlers(connection_state, config)
            handler = _VIZ_HANDLERS.get(name)
        except Exception as e:
            logger.debug(f"Unable to refresh visualization handlers: {e}")
    if handler is not None:
        try:
            return _attach_port_if_connected(handler(arguments))
        except Exception as e:
            return ErrorHandler.handle_unexpected_error(name, e)
    # Unknown tool
    return ErrorHandler.handle_unknown_tool(name)


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Expose alphabetically sorted friendly tool names mapping to canonical handlers.

    We keep canonical names working via FRIENDLY_TOOL_ALIASES, but present a lean,
    categorized surface with prefixes like "analysis:", "list:", "export:", etc.
    """
    entries: List[tuple[str, str, str, dict]] = []  # (friendly, canonical, description, schema)

    def add(friendly: str, canonical: str, description: str, schema: dict):
        # Register alias so call_tool can resolve friendly names
        try:
            FRIENDLY_TOOL_ALIASES.setdefault(friendly, canonical)
        except Exception:
            pass
        entries.append((friendly, canonical, description, schema))

    # Connection & run
    add("connection: detect powerbi desktop", "detect_powerbi_desktop", "Detect local Power BI Desktop instances", {"type": "object", "properties": {}, "required": []})
    add("connection: connect to powerbi", "connect_to_powerbi", "Connect to a detected Power BI Desktop instance", {"type": "object", "properties": {"model_index": {"type": "integer"}}, "required": ["model_index"]})
    add("run: dax", "run_dax", "Run a DAX query with safe limits (auto preview/analyze)", {"type": "object", "properties": {"query": {"type": "string"}, "mode": {"type": "string", "enum": ["auto", "preview", "analyze"], "default": "auto"}, "runs": {"type": "integer"}, "top_n": {"type": "integer"}, "verbose": {"type": "boolean", "default": False}, "include_event_counts": {"type": "boolean", "default": False}}, "required": ["query"]})

    # List / describe / search / get
    add("list: tables", "list_tables", "List tables with pagination", {"type": "object", "properties": {"page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})
    add("list: columns", "list_columns", "List columns (optionally by table)", {"type": "object", "properties": {"table": {"type": "string"}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})
    add("list: calculated columns", "list_calculated_columns", "List calculated columns", {"type": "object", "properties": {"table": {"type": "string"}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})
    add("list: measures", "list_measures", "List measures", {"type": "object", "properties": {"table": {"type": "string"}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})
    add("list: relationships", "relationships", "List relationships with optional cardinality analysis", {"type": "object", "properties": {}, "required": []})
    add("list: roles", "list_roles", "List RLS roles", {"type": "object", "properties": {}, "required": []})
    add("list: partitions", "list_partitions", "List partitions for a table", {"type": "object", "properties": {"table": {"type": "string"}}, "required": []})

    add("describe: table", "describe_table", "Describe a table (columns, measures, relationships)", {"type": "object", "properties": {"table": {"type": "string"}, "columns_page_size": {"type": "integer"}, "columns_next_token": {"type": "string"}, "measures_page_size": {"type": "integer"}, "measures_next_token": {"type": "string"}, "relationships_page_size": {"type": "integer"}, "relationships_next_token": {"type": "string"}}, "required": ["table"]})
    add("preview: table", "preview_table_data", "Preview sample rows from a table", {"type": "object", "properties": {"table": {"type": "string"}, "top_n": {"type": "integer", "default": 10}}, "required": ["table"]})
    add("search: text in measures", "search_string", "Search in measure names/expressions", {"type": "object", "properties": {"search_text": {"type": "string"}, "search_in_expression": {"type": "boolean", "default": True}, "search_in_name": {"type": "boolean", "default": True}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": ["search_text"]})
    add("search: objects", "search_objects", "Search across tables, columns, measures", {"type": "object", "properties": {"pattern": {"type": "string", "default": "*"}, "types": {"type": "array", "items": {"type": "string"}, "default": ["tables", "columns", "measures"]}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})

    add("get: measure details", "get_measure_details", "Get details for a specific measure", {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]})
    add("get: data sources", "get_data_sources", "List Power Query data sources", {"type": "object", "properties": {"page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})
    add("get: m expressions", "get_m_expressions", "List M expressions for queries", {"type": "object", "properties": {"page_size": {"type": "integer"}, "next_token": {"type": "string"}}, "required": []})
    add("profile: top values for column", "get_column_value_distribution", "Top values distribution for a column", {"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}, "top_n": {"type": "integer", "default": 50}}, "required": ["table", "column"]})
    add("get: column summary", "get_column_summary", "Summary stats for a column", {"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]})
    add("get: vertipaq stats", "get_vertipaq_stats", "VertiPaq statistics (table-level)", {"type": "object", "properties": {"table": {"type": "string"}}, "required": []})
    add("get: model summary", "get_model_summary", "Lightweight model summary suitable for large models", {"type": "object", "properties": {}, "required": []})

    # Dependencies & impact
    add("dependency: analyze measure", "analyze_measure_dependencies", "Analyze measure dependencies", {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "depth": {"type": "integer", "default": 3}}, "required": ["table", "measure"]})
    add("usage: where measure is used", "get_measure_impact", "Forward/backward impact for a measure", {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "depth": {"type": "integer", "default": 3}}, "required": ["table", "measure"]})
    # heatmap removed from public surface

    # Maintenance and runtime insight tools (hidden by default; can be enabled via server.show_admin_tools)
    if bool(config.get('server.show_admin_tools', False)):
        add("server: info", "get_server_info", "Server info, telemetry, and config snapshot", {"type": "object", "properties": {}, "required": []})
        add("server: recent logs", "get_recent_logs", "Tail of server logs for debugging", {"type": "object", "properties": {"lines": {"type": "integer", "default": 200}}, "required": []})
        add("server: summarize logs", "summarize_logs", "Summarize recent logs (error/warn/info)", {"type": "object", "properties": {"lines": {"type": "integer", "default": 500}}, "required": []})
        add("server: rate limiter stats", "get_rate_limit_stats", "Rate limiter token and throttle stats", {"type": "object", "properties": {}, "required": []})
        add("server: tool timeouts", "get_tool_timeouts", "Configured per-tool timeouts", {"type": "object", "properties": {}, "required": []})
        add("server: runtime cache stats", "get_runtime_cache_stats", "In-process cache stats (TTL/LRU)", {"type": "object", "properties": {}, "required": []})
    add("usage: analyze column", "analyze_column_usage", "Analyze how a column is used", {"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]})
    add("usage: find unused objects", "find_unused_objects", "Find unused tables/columns/measures", {"type": "object", "properties": {}, "required": []})

    # Model management
    add("measure: create or update", "upsert_measure", "Create or update a measure", {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}, "description": {"type": "string"}, "format_string": {"type": "string"}}, "required": ["table", "measure", "expression"]})
    add("measure: delete", "delete_measure", "Delete a measure", {"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]})
    add("measure: bulk create", "bulk_create_measures", "Create multiple measures", {"type": "object", "properties": {"measures": {"type": "array", "items": {"type": "object"}}}, "required": ["measures"]})
    add("measure: bulk delete", "bulk_delete_measures", "Delete multiple measures", {"type": "object", "properties": {"measures": {"type": "array", "items": {"type": "object"}}}, "required": ["measures"]})
    add("calc: list calculation groups", "list_calculation_groups", "List calculation groups", {"type": "object", "properties": {}, "required": []})
    add("calc: create calculation group", "create_calculation_group", "Create a calculation group", {"type": "object", "properties": {"name": {"type": "string"}, "items": {"type": "array", "items": {"type": "object"}}, "description": {"type": "string"}, "precedence": {"type": "integer", "default": 0}}, "required": ["name", "items"]})
    add("calc: delete calculation group", "delete_calculation_group", "Delete a calculation group", {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]})

    # Security
    add("security: validate rls", "validate_rls_coverage", "Validate RLS coverage", {"type": "object", "properties": {}, "required": []})

    # Validation & governance
    add("validate: dax", "validate_dax_query", "Validate DAX syntax and analyze complexity", {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]})
    add("validate: model integrity", "validate_model_integrity", "Validate model integrity", {"type": "object", "properties": {}, "required": []})

    # Docs & export
    add("export: columns with samples", "export_columns_with_samples", "Export flat list of columns with sample values (csv/txt/xlsx)", {"type": "object", "properties": {"format": {"type": "string", "enum": ["csv", "txt", "xlsx"], "default": "csv"}, "rows": {"type": "integer", "default": 3}, "extras": {"type": "array", "items": {"type": "string"}, "default": []}, "output_dir": {"type": "string", "description": "Directory to write export files; defaults to exports/"}}, "required": []})
    add("export: compact schema", "export_compact_schema", "Export compact model schema for diffs (json/xlsx)", {"type": "object", "properties": {"include_hidden": {"type": "boolean", "default": True}, "format": {"type": "string", "enum": ["json", "xlsx"], "default": "json"}, "output_dir": {"type": "string", "description": "Directory to write XLSX (or other files) to; defaults to exports/"}}, "required": []})
    add("export: relationships graph", "export_relationship_graph", "Export relationships graph (json/graphml)", {"type": "object", "properties": {"format": {"type": "string", "enum": ["json", "graphml"], "default": "json"}}, "required": []})
    add("export: tmsl", "export_tmsl", "Export TMSL (summary by default)", {"type": "object", "properties": {"include_full_model": {"type": "boolean", "default": False}}, "required": []})
    add("export: tmdl", "export_tmdl", "Export TMDL model structure", {"type": "object", "properties": {}, "required": []})
    add("export: model overview", "export_model_overview", "Export compact model overview (json/yaml)", {"type": "object", "properties": {"format": {"type": "string", "enum": ["json", "yaml"], "default": "json"}, "include_counts": {"type": "boolean", "default": True}}, "required": []})
    add("export: model schema (sections)", "export_model_schema", "Export model schema by section with pagination", {"type": "object", "properties": {"section": {"type": "string", "enum": ["tables", "columns", "measures", "relationships"]}, "page_size": {"type": "integer"}, "next_token": {"type": "string"}, "preview_size": {"type": "integer", "description": "Rows per section in compact preview (default 30)"}, "include": {"type": "array", "items": {"type": "string"}, "description": "Subset of sections to include in compact preview"}}, "required": []})

    # Analysis
    add("analysis: m query practices", "analyze_m_practices", "Scan M expressions for common issues", {"type": "object", "properties": {}, "required": []})
    if BPA_AVAILABLE:
        add(
            "analysis: best practices (BPA)",
            "analyze_model_bpa",
            "Run Best Practice Analyzer (rules-based)",
            {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["fast", "balanced", "deep"], "default": "fast"},
                    "categories": {"type": "array", "items": {"type": "string"}},
                    "max_seconds": {"type": "number"}
                },
                "required": []
            }
        )
    add("analysis: performance (batch)", "analyze_queries_batch", "Analyze performance for multiple DAX queries (AMO trace)", {"type": "object", "properties": {"queries": {"type": "array", "items": {"type": "string"}}, "runs": {"type": "integer", "default": 3}, "clear_cache": {"type": "boolean", "default": True}, "include_event_counts": {"type": "boolean", "default": False}}, "required": ["queries"]})
    add("analysis: relationship cardinality", "analyze_relationship_cardinality", "Analyze relationship cardinality and recommendations", {"type": "object", "properties": {}, "required": []})
    add("analysis: column cardinality", "analyze_column_cardinality", "Analyze column cardinality for a table", {"type": "object", "properties": {"table": {"type": "string"}}, "required": []})
    add("analysis: storage compression", "analyze_storage_compression", "Analyze storage/compression efficiency for a table", {"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]})
    add("analysis: full model", "full_analysis", "Comprehensive model analysis (summary, relationships, best practices, M scan, optional BPA)", {"type": "object", "properties": {"include_bpa": {"type": "boolean", "default": True}, "depth": {"type": "string", "enum": ["light", "standard", "deep"], "default": "standard"}, "profile": {"type": "string", "enum": ["fast", "balanced", "deep"], "default": "balanced"}, "limits": {"type": "object", "properties": {"relationships_max": {"type": "integer", "default": 200}, "issues_max": {"type": "integer", "default": 200}}, "default": {}}}, "required": []})
    add("analysis: recommend analysis plan", "propose_analysis", "Recommend fast vs thorough analysis options based on your goal", {"type": "object", "properties": {"goal": {"type": "string"}}, "required": []})

    # Visualization mockup tools
    add(
        "viz: prepare dashboard data",
        "viz_prepare_dashboard_data",
        "Prepare Power BI data for dashboard mockup generation",
        {
            "type": "object",
            "properties": {
                "request_type": {
                    "type": "string",
                    "enum": ["overview", "executive_summary", "operational", "financial", "custom"],
                    "default": "overview",
                    "description": "Type of dashboard to prepare"
                },
                "tables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific tables to include (optional)"
                },
                "measures": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string"},
                            "measure": {"type": "string"},
                            "chart_type": {
                                "type": "string",
                                "enum": ["auto", "kpi_card", "line", "bar", "area", "pie"],
                                "default": "auto"
                            }
                        }
                    },
                    "description": "Specific measures to visualize"
                },
                "max_rows": {
                    "type": "integer",
                    "default": 100,
                    "description": "Maximum rows per query"
                },
                "sample_rows": {
                    "type": "integer",
                    "default": 20,
                    "description": "Sample size for preview data"
                }
            },
            "required": []
        }
    )
    add(
        "viz: get chart data",
        "viz_get_chart_data",
        "Get formatted data for specific chart type",
        {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["kpi_card", "line", "area", "bar", "pie"],
                    "default": "line"
                },
                "table": {"type": "string"},
                "measure": {"type": "string"},
                "dimension": {
                    "type": "string",
                    "description": "Dimension table to group by (optional for bar charts)"
                },
                "sample_rows": {"type": "integer", "default": 20}
            },
            "required": ["table", "measure"]
        }
    )
    add(
        "viz: recommend visualizations",
        "viz_recommend_visualizations",
        "Recommend appropriate visualizations for model or measures",
        {
            "type": "object",
            "properties": {
                "measures": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string"},
                            "measure": {"type": "string"}
                        }
                    },
                    "description": "Specific measures (optional, auto-detects if not provided)"
                }
            },
            "required": []
        }
    )

    # Help
    add("help: quickstart guide", "show_quickstart", "Show path to Quickstart guide and an excerpt", {"type": "object", "properties": {}, "required": []})

    # Helper: sanitize tool identifier to match ^[a-zA-Z0-9_-]{1,64}$ while preserving readability
    def _sanitize_tool_identifier(name: str) -> str:
        try:
            # Replace disallowed chars with '-'
            s = re.sub(r"[^a-zA-Z0-9_-]+", "-", name)
            # Collapse repeats and trim
            s = re.sub(r"-+", "-", s).strip("-")
            # Ensure not empty
            if not s:
                s = "tool"
            # Truncate to 64 chars
            if len(s) > 64:
                s = s[:64]
            return s
        except Exception:
            return (name or "tool")[:64]

    # Sort and emit Tool objects per configured naming mode
    mode = str(config.get('server.tool_names_mode', 'friendly') or 'friendly').lower()
    used_ids: set[str] = set()

    def _unique_id(base: str) -> str:
        """Ensure unique identifier within this listing, appending -2, -3, ... as needed."""
        ident = base
        counter = 2
        while ident in used_ids:
            suffix = f"-{counter}"
            # Keep within 64 char limit
            trimmed = base[: max(1, 64 - len(suffix))]
            ident = trimmed.rstrip('-') + suffix
            counter += 1
        used_ids.add(ident)
        return ident

    if mode == 'canonical':
        # Sort by canonical to keep stable order
        entries.sort(key=lambda x: x[1])
        tools_list: List[Tool] = []
        for (_friendly, canon, desc, schema) in entries:
            safe = _unique_id(_sanitize_tool_identifier(canon))
            # Accept both safe id and the original as aliases for call_tool
            try:
                FRIENDLY_TOOL_ALIASES.setdefault(safe, canon)
            except Exception:
                pass
            schema_with_title = dict(schema)
            schema_with_title.setdefault('title', canon)
            tools_list.append(Tool(name=safe, description=desc, inputSchema=schema_with_title))
        tools = tools_list
    else:
        # Default: friendly names sorted alphabetically
        entries.sort(key=lambda x: x[0])
        tools_list: List[Tool] = []
        for (friendly, canon, desc, schema) in entries:
            safe = _unique_id(_sanitize_tool_identifier(friendly))
            # Map both the friendly text and the sanitized id to the canonical handler
            try:
                FRIENDLY_TOOL_ALIASES.setdefault(safe, canon)
            except Exception:
                pass
            schema_with_title = dict(schema)
            # Preserve the exact friendly name for clients that surface JSON Schema titles
            schema_with_title.setdefault('title', friendly)
            tools_list.append(Tool(name=safe, description=desc, inputSchema=schema_with_title))
        tools = tools_list
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    try:
        _t0 = time.time()
                # Input validation
        if 'table' in arguments:
            is_valid, error = InputValidator.validate_table_name(arguments['table'])
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    'success': False, 
                    'error': error,
                    'error_type': 'invalid_input'
                }, indent=2))]
        
        if 'query' in arguments:
            is_valid, error = InputValidator.validate_dax_query(arguments['query'])
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    'success': False,
                    'error': error,
                    'error_type': 'invalid_input'
                }, indent=2))]
        
        # Rate limiting
        if rate_limiter and not rate_limiter.allow_request(name):
            return [TextContent(type="text", text=json.dumps({
                'success': False,
                'error': 'Rate limit exceeded',
                'error_type': 'rate_limit',
                'retry_after': rate_limiter.get_retry_after(name)
            }, indent=2))]
        

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
    logger.info(f"MCP-PowerBi-Finvision Server v{__version__} - Complete Edition")
    logger.info("=" * 80)
    logger.info("Tools available")

    # Provide rich initialization instructions so clients show helpful guidance on connect
    def _initial_instructions() -> str:
        try:
            parent = os.path.dirname(script_dir)
            guides_dir = os.path.join(parent, 'docs')
            os.makedirs(guides_dir, exist_ok=True)
            pdf_path = os.path.join(guides_dir, 'PBIXRAY_Quickstart.pdf')
            if not os.path.exists(pdf_path):
                _write_quickstart_assets(guides_dir)
            # Build a concise intro that many MCP clients render on startup
            lines = [
                f"MCP-PowerBi-Finvision v{__version__} — Power BI Desktop MCP server.",
                "",
                "What you can do:",
                "- Connect to your open Power BI Desktop instance",
                "- Inspect tables/columns/measures and preview data",
                "- Search objects and view data sources and M expressions",
                "- Run Best Practice Analyzer (BPA) and relationship analysis",
                "- Export compact schema, TMSL/TMDL, and documentation",
                "",
                "Quick start:",
                "1) Run tool: connection: detect powerbi desktop",
                "2) Then: connection: connect to powerbi (usually model_index=0)",
                "3) Try: list: tables | describe: table | preview: table",
                "",
                f"Full guide: {pdf_path if os.path.exists(pdf_path) else os.path.join(guides_dir, 'PBIXRAY_Quickstart.txt')}"
            ]
            return "\n".join(lines)
        except Exception:
            # Last-resort short instructions
            return (
                f"MCP-PowerBi-Finvision v{__version__}. Start by running 'connection: detect powerbi desktop' and then 'connection: connect to powerbi'. "
                "Use list_tools to see available operations."
            )

    init_opts = app.create_initialization_options()
    try:
        # Inject instructions text expected by MCP clients
        setattr(init_opts, "instructions", _initial_instructions())
    except Exception:
        pass

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, init_opts)


if __name__ == "__main__":
    asyncio.run(main())
