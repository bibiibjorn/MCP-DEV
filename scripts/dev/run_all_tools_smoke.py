import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import pbixray_server_enhanced as srv  # type: ignore


def ok(d: dict) -> bool:
    return isinstance(d, dict) and d.get("success") is True


def _norm(name: Optional[str]) -> str:
    if not name:
        return ""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def get_tool_names() -> List[str]:
    # Prefer server_info for portability
    try:
        info = srv._dispatch_tool("get_server_info", {})
        names = info.get("tools", []) or []
        return sorted({str(n) for n in names})
    except Exception:
        # Last resort: no discovery
        return []


def _rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    return payload.get("rows") or payload.get("results") or []


def pick_sample_context() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    # table, column, measure
    tab, col, meas = None, None, None
    lt = srv._dispatch_tool("list_tables", {})
    tables = _rows(lt) if ok(lt) else []
    # Build table preference order
    preferred = ["d_Date", "d_Period", "f_FINREP"]
    ordered_tables: List[str] = []
    for p in preferred:
        if any((r.get("Name") or r.get("[Name]") or r.get("TABLE_NAME")) == p for r in tables):
            ordered_tables.append(p)
    for r in tables:
        name = r.get("Name") or r.get("[Name]") or r.get("TABLE_NAME")
        if name and name not in ordered_tables:
            ordered_tables.append(name)

    # Find first table with a non-calculated column
    for tname in ordered_tables:
        lc = srv._dispatch_tool("list_columns", {"table": tname})
        if ok(lc):
            for r in _rows(lc):
                t = str(r.get("Type") or r.get("[Type]") or r.get("DATA_TYPE") or "").lower()
                cname = r.get("Name") or r.get("[Name]") or r.get("COLUMN_NAME")
                if cname and t != "calculated":
                    tab, col = tname, cname
                    break
        if tab and col:
            break

    # Try to get a measure on the chosen table
    if tab:
        lm = srv._dispatch_tool("list_measures", {"table": tab})
        if ok(lm):
            ms = _rows(lm)
            if ms:
                meas = ms[0].get("Name") or ms[0].get("[Name]")

    # If still no measure, pick any global measure and align table if provided
    if not meas:
        lm_all = srv._dispatch_tool("list_measures", {})
        if ok(lm_all):
            ms = _rows(lm_all)
            if ms:
                m0 = ms[0]
                meas = m0.get("Name") or m0.get("[Name]")
                mt = m0.get("Table") or m0.get("[Table]") or m0.get("TABLE_NAME")
                if mt:
                    tab = mt

    # Ensure we have a column for the selected table
    if tab and not col:
        lc2 = srv._dispatch_tool("list_columns", {"table": tab})
        if ok(lc2):
            cand_any = None
            for r in _rows(lc2):
                cname = r.get("Name") or r.get("[Name]") or r.get("COLUMN_NAME")
                t = str(r.get("Type") or r.get("[Type]") or r.get("DATA_TYPE") or "").lower()
                if cname and cand_any is None:
                    cand_any = cname
                if cname and t != "calculated":
                    col = cname
                    break
            if not col and cand_any:
                col = cand_any
    return tab, col, meas


def safe_args(tool: str, tab: Optional[str], col: Optional[str], meas: Optional[str]) -> Dict[str, Any]:
    # Sensible defaults per tool family; unknown tools -> {}
    tool_n = _norm(tool)
    if tool_n in {"server_info", "server_rate_limiter_stats", "server_recent_logs", "server_runtime_cache_stats", "server_summarize_logs", "server_tool_timeouts"}:
        return {}
    if tool_n in {"connection_detect_powerbi_desktop", "detect_powerbi_desktop"}:
        return {}
    if tool_n in {"connection_connect_to_powerbi", "connect_to_powerbi"}:
        return {"model_index": 0}
    if tool_n in {"list_tables", "list_relationships", "get_data_sources", "get_m_expressions", "list_roles", "list_partitions", "get_model_summary"}:
        return {}
    if tool_n in {"list_columns"}:
        return {"table": tab} if tab else {}
    if tool_n in {"list_measures"}:
        # table is optional; use when available to reduce payload
        base: Dict[str, Any] = {"page_size": 1000}
        if tab:
            base["table"] = tab
        return base
    if tool_n in {"describe_table"}:
        return {"table": tab, "columns_page_size": 10, "measures_page_size": 10, "relationships_page_size": 20} if tab else {}
    if tool_n in {"get_column_values", "get_column_value_distribution"}:
        return {"table": tab, "column": col, "limit": 5} if tab and col else {}
    if tool_n in {"get_column_summary"}:
        return {"table": tab, "column": col, "top_n": 25} if tab and col else {}
    if tool_n in {"get_measure_details", "dependency_analyze_measure", "impact_measure"}:
        return {"table": tab, "measure": meas} if tab and meas else {}
    if tool_n in {"preview_table", "preview_table_data"}:
        return {"table": tab, "top_n": 5} if tab else {}
    if tool_n in {"run_dax", "run_dax_query"}:
        return {"query": "EVALUATE ROW(\"V\", 1)", "top_n": 0, "bypass_cache": True}
    if tool_n in {"validate_dax", "validate_dax_query"}:
        return {"query": "EVALUATE ROW(\"V\", 1)"}
    if tool_n in {"search_objects"}:
        return {"pattern": "*", "types": ["tables", "columns", "measures"], "page_size": 1000}
    if tool_n in {"search_text_in_measures"}:
        return {"search_text": "SUM", "limit": 10}
    if tool_n in {"list_calculated_columns"}:
        return {"table": tab} if tab else {}
    if tool_n in {"get_vertipaq_stats"}:
        return {"table": tab} if tab else {}
    if tool_n in {"analyze_query_performance"}:
        return {"query": "EVALUATE ROW(\"V\", 1)", "runs": 1, "clear_cache": True}
    if tool_n in {"export_model_schema", "export_model_overview", "export_schema_paged", "export_compact_schema", "export_relationships_graph", "export_tmdl", "export_tmsl"}:
        return {"preview_size": 5}
    if tool_n in {"export_relationship_graph", "export_relationships_graph"}:
        return {"format": "graphml", "limit": 200}
    if tool_n in {"analyze_model_bpa", "analysis_best_practices_bpa"}:
        return {"profile": "balanced"}
    if tool_n in {"full_analysis", "analysis_full_model"}:
        return {"depth": "light", "include_bpa": False, "profile": "fast"}
    if tool_n in {"analysis_storage_compression"}:
        return {"table": tab} if tab else {}
    if tool_n in {"apply_tmdl_patch"}:
        return {"updates": [{"table": tab or "T", "measure": (meas or "M"), "description": "dry run"}], "dry_run": True}
    if tool_n in {"apply_recommended_fixes"}:
        return {"actions": [], "dry_run": True}
    if tool_n in {"export_model_overview"}:
        return {"format": "json", "include_counts": True}
    if tool_n in {"generate_documentation_profiled", "generate_documentation"}:
        return {"format": "markdown", "include_examples": False}
    if tool_n in {"format_dax"}:
        return {"expression": "SUMX(Fact, Fact[Amount])"}
    if tool_n in {"auto_document", "auto_analyze_or_preview", "auto_route"}:
        return {"query": "EVALUATE ROW(\"V\", 1)", "runs": 1, "max_rows": 10, "priority": "depth"}
    # default empty
    return {}


def main() -> int:
    started = time.time()
    det = srv._dispatch_tool("detect_powerbi_desktop", {})
    if not ok(det):
        print("detect_powerbi_desktop: FAIL")
        print(json.dumps(det, indent=2))
        return 2
    conn = srv._dispatch_tool("connect_to_powerbi", {"model_index": 0})
    if not ok(conn):
        print("connect_to_powerbi: FAIL")
        print(json.dumps(conn, indent=2))
        return 3

    tab, col, meas = pick_sample_context()

    # Enumerate tools
    names = get_tool_names()
    if not names:
        print("list_tools unavailable; using minimal set")
        names = [
            "list_tables","list_columns","list_measures","list_relationships","get_data_sources","get_m_expressions",
            "describe_table","preview_table_data","get_column_values","get_column_summary","get_column_value_distribution",
            "search_objects","validate_dax_query","run_dax_query","get_vertipaq_stats","analyze_query_performance",
            "export_model_schema","export_model_overview","analyze_model_bpa","full_analysis"
        ]

    # Always run detection/connect first if present; remove duplicates
    ordered = []
    for x in ["detect_powerbi_desktop","connect_to_powerbi"]:
        if x in names:
            ordered.append(x)
    for n in names:
        if n not in ordered:
            ordered.append(n)

    # Skip write/destructive tools for smoke run
    skip_prefixes = ("calc-", "measure-", "apply-", "partition-", "bulk-", "tmdl-", "tmsl-apply")
    skip_exact = {"measure-upsert", "measure-delete", "measure-bulk-create", "measure-bulk-delete", "calc-create-calculation-group", "calc-delete-calculation-group"}

    results: List[Dict[str, Any]] = []
    for name in ordered:
        if name.lower().startswith(skip_prefixes) or name in skip_exact:
            results.append({"name": name, "success": True, "notes": "skipped (write operation)"})
            print(f"{name}: SKIPPED (write)")
            continue
        # Skip potentially disruptive tools (none known to perform writes due to design; still keep minimal skips if surfaced)
        args = safe_args(name, tab, col, meas)
        try:
            res = srv._dispatch_tool(name, args)
            success = ok(res)
            summary = {
                'name': name,
                'success': success,
                'error_type': res.get('error_type') if isinstance(res, dict) else None,
                'row_count': res.get('row_count') if isinstance(res, dict) else None,
                'notes': res.get('notes') if isinstance(res, dict) else None,
            }
            results.append(summary)
            print(f"{name}: {'OK' if success else 'FAIL'}")
            if not success:
                # Print a small error payload for quick triage
                print(json.dumps(res, indent=2)[:1000])
        except Exception as e:
            results.append({'name': name, 'success': False, 'error': str(e)})
            print(f"{name}: EXCEPTION -> {e}")

    report = {
        'success': any(r.get('success') for r in results),
        'started_at': started,
        'ended_at': time.time(),
        'tool_count': len(ordered),
        'passed': sum(1 for r in results if r.get('success')),
        'failed': sum(1 for r in results if not r.get('success')),
        'results': results,
        'sample_context': {'table': tab, 'column': col, 'measure': meas},
    }

    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    out_path = os.path.join(logs_dir, f"run_all_tools_{int(report['ended_at'])}.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(out_path)

    # Exit code: 0 if at least 80% of tools passed, else 1
    pass_ratio = report['passed'] / max(1, report['tool_count'])
    return 0 if pass_ratio >= 0.8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
