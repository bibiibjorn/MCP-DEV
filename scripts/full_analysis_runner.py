#!/usr/bin/env python3
r"""
Standalone full analysis runner for PBIXRay MCP Server.

- Detects and connects to the most recent Power BI Desktop instance
- Initializes managers
- Gathers model summary, relationships, best practices, M scan, optional BPA
- Optionally performs deeper checks
- Writes results to logs/full_analysis_YYYYmmdd_HHMMSS.json

Run with the project venv's Python:
    .\venv\Scripts\python.exe .\scripts\full_analysis_runner.py --depth standard --include-bpa
"""

import argparse
import json
import os
import sys
import time
import logging
from typing import Any, Dict

# Ensure project root on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pbixray_full_analysis")

# Imports from core
from core.connection_manager import ConnectionManager
from core.connection_state import connection_state
from core.config_manager import config
from core.model_narrative import generate_narrative


def clamp_list(obj: Dict[str, Any], key: str, max_items: int, note: str):
    try:
        if not isinstance(obj, dict):
            return
        arr = obj.get(key)
        if isinstance(arr, list) and len(arr) > max_items:
            obj[key] = arr[:max_items]
            obj.setdefault('notes', []).append(note)
    except Exception:
        pass


def _simple_main_purpose(summary: Dict[str, Any]) -> str:
    try:
        purpose = (summary or {}).get('purpose') or {}
        text = (purpose or {}).get('text')
        if isinstance(text, str) and text.strip():
            t = text.strip()
            t = t.replace('Model geared towards', 'This report focuses on')
            t = t.replace('row-level security', 'user-based access')
            t = t.replace('time intelligence', 'time-based analysis')
            return t
        domains = (purpose or {}).get('domains') or []
        if domains:
            friendly = []
            for d in domains:
                dl = str(d).lower()
                if 'period' in dl or 'time' in dl:
                    friendly.append('time-based analysis')
                elif 'row-level' in dl:
                    friendly.append('user-based access')
                elif 'currency' in dl or 'fx' in dl:
                    friendly.append('currency conversion')
                elif 'financial' in dl:
                    friendly.append('financial reporting')
                elif 'aging' in dl:
                    friendly.append('receivables/payables aging')
                elif 'customer' in dl or 'vendor' in dl:
                    friendly.append('customer and vendor insights')
                elif 'company' in dl or 'org' in dl:
                    friendly.append('company and organizational analysis')
                else:
                    friendly.append(d)
            seen = set()
            friendly = [x for x in friendly if not (x in seen or seen.add(x))]
            if friendly:
                if len(friendly) == 1:
                    return f"This report focuses on {friendly[0]}"
                return f"This report focuses on {', '.join(friendly[:-1])} and {friendly[-1]}"
        return 'This report provides general business analytics'
    except Exception:
        return 'This report provides general business analytics'


def run_full_analysis(depth: str, include_bpa: bool, relationships_max: int, issues_max: int, profile: str = 'balanced') -> Dict[str, Any]:
    cm = ConnectionManager()
    instances = cm.detect_instances()
    if not instances:
        return {'success': False, 'error': 'No Power BI Desktop instances detected'}
    # Connect to most recent (index 0)
    conn = cm.connect(0)
    if not conn.get('success'):
        return conn

    connection_state.set_connection_manager(cm)
    connection_state.initialize_managers(force_reinit=True)

    qe = connection_state.query_executor
    perf_opt = connection_state.performance_optimizer
    exporter = connection_state.model_exporter
    bpa = connection_state.bpa_analyzer

    sections: Dict[str, Any] = {}
    timings: Dict[str, float] = {}

    # Model summary
    t0 = time.time()
    if exporter and qe:
        sections['summary'] = exporter.get_model_summary(qe)
    else:
        sections['summary'] = {'success': False, 'error': 'Model exporter unavailable'}
    timings['summary_ms'] = round((time.time() - t0) * 1000, 2)

    # Attach concise purpose if available and also add a simple, non-technical main_purpose
    try:
        if isinstance(sections.get('summary'), dict):
            purpose = sections['summary'].get('purpose')
            if purpose:
                sections['model_purpose'] = {'success': True, **purpose}
            sections['summary']['main_purpose'] = _simple_main_purpose(sections['summary'])
    except Exception:
        pass

    # Relationships
    t0 = time.time()
    if qe:
        rels = qe.execute_info_query('RELATIONSHIPS')
        if rels.get('success'):
            clamp_list(rels, 'rows', relationships_max, f'Truncated to {relationships_max} relationships')
        sections['relationships'] = rels
    else:
        sections['relationships'] = {'success': False, 'error': 'Query executor unavailable'}
    timings['relationships_ms'] = round((time.time() - t0) * 1000, 2)

    # FAST profile: return early with just summary + relationships
    if (profile or 'balanced').lower() == 'fast':
        try:
            sections['narrative'] = generate_narrative(sections.get('summary') or {}, sections.get('relationships') or {})
        except Exception:
            pass
        # simple, non-technical main purpose
        main_purpose = _simple_main_purpose(sections.get('summary') or {})
        what = main_purpose
        return {
            'success': True,
            'depth': 'light',
            'profile': 'fast',
            'include_bpa': False,
            'generated_at': time.time(),
            'timings_ms': timings,
            'sections': sections,
            'what_the_model_does': what,
            'main_purpose': main_purpose,
            'instance': cm.get_instance_info(),
        }

    # Best practices (composite)
    from core.agent_policy import AgentPolicy
    ap = AgentPolicy(config)
    t0 = time.time()
    sections['best_practices'] = ap.validate_best_practices(connection_state)
    timings['best_practices_ms'] = round((time.time() - t0) * 1000, 2)

    # M practices scan (heuristics like analyze_m_practices)
    t0 = time.time()
    try:
        dmv_cap = int(config.get('query.max_rows_preview', 1000))
    except Exception:
        dmv_cap = 1000
    if qe:
        m_query = f'''EVALUATE\n            SELECTCOLUMNS(\n                TOPN({dmv_cap}, $SYSTEM.TMSCHEMA_EXPRESSIONS),\n                "Name", [Name],\n                "Expression", [Expression],\n                "Kind", [Kind]\n            )'''
        m_data = qe.validate_and_execute_dax(m_query, dmv_cap)
        if not m_data.get('success'):
            sections['m_practices'] = m_data
        else:
            issues = []
            for row in m_data.get('rows', []):
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
            if len(issues) > issues_max:
                issues = issues[:issues_max]
            sections['m_practices'] = {'success': True, 'count': len(issues), 'issues': issues}
    else:
        sections['m_practices'] = {'success': False, 'error': 'Query executor unavailable'}
    timings['m_practices_ms'] = round((time.time() - t0) * 1000, 2)

    # BPA (optional)
    if include_bpa and (profile or 'balanced').lower() != 'fast':
        t0 = time.time()
        if qe and bpa:
            tmsl = qe.get_tmsl_definition()
            if tmsl.get('success'):
                viols = bpa.analyze_model(tmsl['tmsl'])
                summary = bpa.get_violations_summary()
                trimmed = []
                for v in viols[:issues_max]:
                    trimmed.append({
                        'rule_id': v.rule_id,
                        'rule_name': v.rule_name,
                        'category': v.category,
                        'severity': getattr(v.severity, 'name', str(v.severity)),
                        'object_type': v.object_type,
                        'object_name': v.object_name,
                        'table_name': v.table_name,
                        'description': v.description
                    })
                sections['bpa'] = {'success': True, 'violations_count': len(viols), 'summary': summary, 'violations': trimmed}
            else:
                sections['bpa'] = tmsl
        else:
            sections['bpa'] = {'success': False, 'error': 'BPA analyzer unavailable'}
        timings['bpa_ms'] = round((time.time() - t0) * 1000, 2)

    # Deeper checks
    if depth in ('standard', 'deep') and perf_opt:
        t0 = time.time()
        sections['cardinality_overview'] = perf_opt.analyze_column_cardinality(None)
        timings['cardinality_overview_ms'] = round((time.time() - t0) * 1000, 2)
    if depth == 'deep' and perf_opt:
        t0 = time.time()
        sections['relationship_cardinality'] = perf_opt.analyze_relationship_cardinality()
        timings['relationship_cardinality_ms'] = round((time.time() - t0) * 1000, 2)

    # concise purpose at top-level
    # Compute a simple main purpose and mirror it at top-level
    main_purpose = _simple_main_purpose(sections.get('summary') or {})
    what = main_purpose

    return {
        'success': True,
        'depth': depth,
        'profile': (profile or 'balanced').lower(),
        'include_bpa': include_bpa,
        'generated_at': time.time(),
        'timings_ms': timings,
        'sections': {**sections, 'narrative': generate_narrative(sections.get('summary') or {}, sections.get('relationships') or {})},
        'what_the_model_does': what,
        'main_purpose': main_purpose,
        'instance': cm.get_instance_info(),
    }


def main():
    parser = argparse.ArgumentParser(description='PBIXRay full analysis runner')
    parser.add_argument('--depth', choices=['light', 'standard', 'deep'], default='standard')
    parser.add_argument('--include-bpa', action='store_true', default=False, help='Include BPA analysis if available')
    parser.add_argument('--relationships-max', type=int, default=200)
    parser.add_argument('--issues-max', type=int, default=200)
    parser.add_argument('--profile', choices=['fast', 'balanced', 'deep'], default='balanced')
    args = parser.parse_args()

    res = run_full_analysis(args.depth, args.include_bpa, args.relationships_max, args.issues_max, args.profile)
    ts = time.strftime('%Y%m%d_%H%M%S')
    logs_dir = os.path.join(PROJECT_ROOT, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    out_path = os.path.join(logs_dir, f'full_analysis_{ts}.json')
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=2)
        print(out_path)
    except Exception as e:
        print(json.dumps(res, indent=2))
        logger.error(f"Failed to write report: {e}")
        sys.exit(1 if not res.get('success') else 0)

    if not res.get('success'):
        sys.exit(1)


if __name__ == '__main__':
    main()
