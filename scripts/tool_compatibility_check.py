#!/usr/bin/env python3
"""
PBIXRay Tool Compatibility Check
- Connects to the most recent Power BI Desktop instance
- Enumerates public tools from pbixray_server_enhanced
- Invokes SAFE (read-only) tools with minimal arguments
- Captures PASS/FAIL and per-tool timing
- Writes a JSON report to logs/tool_compat_YYYYmmdd_HHMMSS.json

This avoids mutative tools (create/update/delete/refresh/apply patches).
"""
from __future__ import annotations
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import pbixray_server_enhanced as srv  # type: ignore


def _ok(resp: Any) -> bool:
    return isinstance(resp, dict) and bool(resp.get('success', False))


def _get_any(row: Dict[str, Any], keys: List[str]) -> Any:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
        bk = f"[{k}]"
        if bk in row and row[bk] not in (None, ""):
            return row[bk]
    return None


def _get_first_table() -> str | None:
    res = srv._dispatch_tool('list_tables', {})
    rows = (res or {}).get('rows') or []
    # Prefer common dimension tables if present; else first non-hidden, else any
    pref = ('d_Date', 'd_Period', 'f_FINREP')
    names = []
    for r in rows:
        nm = _get_any(r, ['Name', 'TABLE_NAME', 'Table', 'table'])
        if nm not in (None, ""):
            names.append(str(nm))
    for p in pref:
        if p in names:
            return p
    # Try first non-hidden
    for r in rows:
        hidden = bool(r.get('IsHidden', False))
        nm = _get_any(r, ['Name', 'TABLE_NAME', 'Table', 'table'])
        if not hidden and nm not in (None, ""):
            return str(nm)
    # Fallback to first name
    return names[0] if names else None


def _get_first_measure() -> Tuple[str | None, str | None]:
    res = srv._dispatch_tool('list_measures', {})
    rows = (res or {}).get('rows') or []
    if not rows:
        return None, None
    # Prefer first non-hidden measure
    for r in rows:
        if not bool(r.get('IsHidden', False)):
            table = _get_any(r, ['Table', 'TableName', 'TABLE_NAME'])
            meas = _get_any(r, ['Name', 'MEASURE_NAME'])
            if table and meas:
                return str(table), str(meas)
    # Next, find any row that has a table name
    for r in rows:
        table = _get_any(r, ['Table', 'TableName', 'TABLE_NAME'])
        meas = _get_any(r, ['Name', 'MEASURE_NAME'])
        if table and meas:
            return str(table), str(meas)
    # Fallback to first row
    r0 = rows[0]
    table = _get_any(r0, ['Table', 'TableName', 'TABLE_NAME'])
    meas = _get_any(r0, ['Name', 'MEASURE_NAME'])
    return (str(table) if table else None, str(meas) if meas else None)


def _get_first_column(table: str | None) -> Tuple[str | None, str | None]:
    # If table given, try it; else fetch any column
    if table:
        res = srv._dispatch_tool('list_columns', {'table': table})
        rows = (res or {}).get('rows') or []
        if rows:
            # Prefer first non-calculated column
            for r in rows:
                typ = str(_get_any(r, ['Type']) or '').lower()
                if typ != 'calculated':
                    col = _get_any(r, ['Name', 'COLUMN_NAME', 'Column'])
                    if col:
                        return table, str(col)
            r0 = rows[0]
            col = _get_any(r0, ['Name', 'COLUMN_NAME', 'Column'])
            return table, (str(col) if col else None)
    # Fallback: any column
    res = srv._dispatch_tool('list_columns', {})
    rows = (res or {}).get('rows') or []
    if not rows:
        return None, None
    # Prefer non-calculated and capture table from row
    for r in rows:
        typ = str(_get_any(r, ['Type']) or '').lower()
        if typ != 'calculated':
            tbl = _get_any(r, ['Table', 'TABLE_NAME'])
            col = _get_any(r, ['Name', 'COLUMN_NAME', 'Column'])
            if tbl and col:
                return str(tbl), str(col)
    r0 = rows[0]
    tbl = _get_any(r0, ['Table', 'TABLE_NAME'])
    col = _get_any(r0, ['Name', 'COLUMN_NAME', 'Column'])
    return (str(tbl) if tbl else None), (str(col) if col else None)


def main():
    # 1) Detect and connect via server dispatcher so it initializes its own managers
    det = srv._dispatch_tool('detect_powerbi_desktop', {})
    if not _ok(det) and det.get('success') is not True:
        print(json.dumps({'success': False, 'error': 'No Power BI instances detected', 'details': det}, indent=2))
        sys.exit(1)
    conn = srv._dispatch_tool('connect_to_powerbi', {'model_index': 0})
    if not _ok(conn):
        print(json.dumps({'success': False, 'error': 'Failed to connect', 'details': conn}, indent=2))
        sys.exit(1)

    # 2) Gather sample objects
    sample_table = _get_first_table()
    meas_table, sample_measure = _get_first_measure()
    col_table, sample_column = _get_first_column(sample_table or meas_table)

    sampling_notes: Dict[str, Any] = {
        'table_selection': 'preferred in order: d_Date/d_Period/f_FINREP, then first non-hidden, else first table',
        'measure_selection': 'first non-hidden with table if available, else any',
        'column_selection': 'for selected table: first non-calculated, else first; if no table then first available pair',
    }

    # Prepare reference TMSL for compare_models: export full TMSL and use its model
    reference_tmsl: Dict[str, Any] | None = None
    try:
        ref = srv._dispatch_tool('export_tmsl', {'include_full_model': True})
        if isinstance(ref, dict) and ref.get('success') and isinstance(ref.get('model'), dict):
            reference_tmsl = ref
        else:
            # As a fallback, try to obtain TMSL from query executor and parse if needed
            qe = getattr(srv.connection_state, 'query_executor', None)
            if qe:
                tmsl_obj = qe.get_tmsl_definition()
                tmsl_val = (tmsl_obj or {}).get('tmsl') if isinstance(tmsl_obj, dict) else None
                if isinstance(tmsl_val, str):
                    try:
                        parsed = json.loads(tmsl_val)
                        reference_tmsl = {'model': parsed}
                    except Exception:
                        reference_tmsl = None
                elif isinstance(tmsl_val, dict):
                    reference_tmsl = {'model': tmsl_val}
    except Exception:
        reference_tmsl = None

    # 3) Define safe tests (skip mutative)
    from typing import Optional
    tests: List[Tuple[str, Optional[Dict[str, Any]]]] = [
        ('summarize_model', {}),
        ('relationships', {}),
        ('list_tables', {}),
        ('list_measures', {}),
        ('list_columns', {'table': sample_table} if sample_table else {}),
        ('describe_table', {'table': sample_table} if sample_table else None),
        ('get_measure_details', {'table': meas_table, 'measure': sample_measure} if meas_table and sample_measure else None),
        ('search_string', {'search_text': 'SUM'}),
        ('list_calculated_columns', {}),
        ('search_objects', {}),
        ('get_data_sources', {}),
        ('get_m_expressions', {}),
        ('preview_table_data', {'table': sample_table, 'top_n': 5} if sample_table else None),
        ('export_model_schema', {}),
        ('get_column_values', {'table': col_table, 'column': sample_column, 'limit': 5} if col_table and sample_column else None),
        ('get_column_summary', {'table': col_table, 'column': sample_column} if col_table and sample_column else None),
        ('get_vertipaq_stats', {'table': sample_table} if sample_table else {}),
        ('validate_dax_query', {'query': 'EVALUATE ROW("x",1)'}),
        ('analyze_measure_dependencies', {'table': meas_table, 'measure': sample_measure} if meas_table and sample_measure else None),
        ('find_unused_objects', {}),
        ('analyze_column_usage', {'table': col_table, 'column': sample_column} if col_table and sample_column else None),
        ('list_calculation_groups', {}),
        ('list_partitions', {}),
        ('list_roles', {}),
        ('validate_rls_coverage', {}),
        ('export_tmsl', {}),
        ('export_tmdl', {}),
        ('generate_documentation', {}),
        ('get_model_summary', {}),
        ('compare_models', {'reference_tmsl': reference_tmsl} if reference_tmsl else None),
        ('analyze_relationship_cardinality', {}),
        ('analyze_column_cardinality', {}),
        ('validate_model_integrity', {}),
        ('analyze_queries_batch', {'queries': ['EVALUATE ROW("x",1)'], 'runs': 1, 'clear_cache': True}),
        ('profile_columns', {'table': col_table, 'columns': [sample_column] if sample_column else []} if col_table else None),
        ('get_column_value_distribution', {'table': col_table, 'column': sample_column, 'top_n': 10} if col_table and sample_column else None),
        ('validate_best_practices', {}),
        ('get_measure_impact', {'table': meas_table, 'measure': sample_measure, 'depth': 2} if meas_table and sample_measure else None),
        ('get_column_usage_heatmap', {'table': col_table, 'limit': 50} if col_table else None),
        ('format_dax', {'expression': 'SUM ( [Amount] )'}),
        ('export_model_overview', {'format': 'json', 'include_counts': True}),
        ('analyze_m_practices', {}),
        ('export_relationship_graph', {'format': 'json'}),
        ('full_analysis', {'include_bpa': True, 'depth': 'standard', 'profile': 'balanced', 'limits': {'relationships_max': 50, 'issues_max': 50}}),
        ('propose_analysis', {'goal': 'quick model check'}),
    ]

    # BPA is conditional
    if srv.BPA_AVAILABLE:
        tests.insert(0, ('analyze_model_bpa', {}))

    # Remove None arg tests (lack of sample objects)
    runnable = [(n, a) for (n, a) in tests if a is not None]

    # 4) Execute tests
    results: Dict[str, Any] = {
        'success': True,
        'generated_at': time.time(),
        'instance': srv.connection_manager.get_instance_info(),
        'sample_table': sample_table,
        'sample_measure': {'table': meas_table, 'name': sample_measure},
        'sample_column': {'table': col_table, 'name': sample_column},
        'sampling_notes': sampling_notes,
        'tools': [],
        'summary': {},
    }

    passes = 0
    fails = 0
    for name, args in runnable:
        t0 = time.time()
        try:
            resp = srv._dispatch_tool(name, args)
            ok = _ok(resp)
            elapsed = round((time.time() - t0) * 1000, 2)
            results['tools'].append({'name': name, 'args': args, 'success': ok, 'elapsed_ms': elapsed, 'error': None if ok else resp})
            if ok:
                passes += 1
            else:
                fails += 1
        except Exception as e:
            elapsed = round((time.time() - t0) * 1000, 2)
            results['tools'].append({'name': name, 'args': args, 'success': False, 'elapsed_ms': elapsed, 'error': str(e)})
            fails += 1

    results['summary'] = {'total': len(runnable), 'passed': passes, 'failed': fails}
    results['success'] = fails == 0

    # 5) Write report
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(logs_dir, f'tool_compat_{ts}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(out_path)


if __name__ == '__main__':
    main()
