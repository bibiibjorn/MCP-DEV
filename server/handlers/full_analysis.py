from typing import Any, Dict
import time

from server.utils.m_practices import scan_m_practices
from core.model_narrative import generate_narrative


def _simple_main_purpose(summary: Dict[str, Any]) -> str:
    """Return a short, non-technical main purpose string for the report/model.
    Prefers summary.purpose.text; otherwise composes from purpose.domains; falls back to a general phrase.
    """
    try:
        purpose = (summary or {}).get('purpose') or {}
        text = (purpose or {}).get('text')
        if isinstance(text, str) and text.strip():
            # De-jargon some common phrases
            t = text.strip()
            t = t.replace('Model geared towards', 'This report focuses on')
            t = t.replace('row-level security', 'user-based access')
            t = t.replace('time intelligence', 'time-based analysis')
            return t
        # Build from domains if text missing
        domains = (purpose or {}).get('domains') or []
        if domains:
            # Map domains to friendlier wording
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
            # De-duplicate while preserving order
            seen = set()
            friendly = [x for x in friendly if not (x in seen or seen.add(x))]
            if friendly:
                if len(friendly) == 1:
                    return f"This report focuses on {friendly[0]}"
                return f"This report focuses on {', '.join(friendly[:-1])} and {friendly[-1]}"
        # Last resort
        return 'This report provides general business analytics'
    except Exception:
        return 'This report provides general business analytics'


def run_full_analysis(
    connection_state: Any,
    config: Any,
    BPA_AVAILABLE: bool,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    # Shortcut references
    query_executor = connection_state.query_executor
    bpa_analyzer = connection_state.bpa_analyzer
    model_exporter = connection_state.model_exporter
    performance_optimizer = connection_state.performance_optimizer

    include_bpa = bool(arguments.get('include_bpa', True)) and BPA_AVAILABLE and (bpa_analyzer is not None)
    depth = (arguments.get('depth') or 'standard').lower()
    profile = (arguments.get('profile') or 'balanced').lower()
    limits = arguments.get('limits') or {}
    rel_max = int(limits.get('relationships_max', 200) or 200)
    issues_max = int(limits.get('issues_max', 200) or 200)

    sections: dict[str, Any] = {}
    timings: dict[str, float] = {}

    # Summary
    t0 = time.time()
    sections['summary'] = model_exporter.get_model_summary(query_executor) if model_exporter else {'success': False, 'error': 'Model exporter unavailable'}
    timings['summary_ms'] = round((time.time() - t0) * 1000, 2)

    # Attach concise purpose if available in summary
    try:
        if isinstance(sections.get('summary'), dict):
            purpose = sections['summary'].get('purpose')
            if purpose:
                sections['model_purpose'] = {'success': True, **purpose}
            # Always attach a simple, non-technical main_purpose inside the summary
            sections['summary']['main_purpose'] = _simple_main_purpose(sections['summary'])
    except Exception:
        pass

    # Relationships
    t0 = time.time()
    rels = query_executor.execute_info_query("RELATIONSHIPS")
    if rels.get('success') and isinstance(rels.get('rows'), list) and len(rels['rows']) > rel_max:
        rels = dict(rels)
        rels['rows'] = rels['rows'][:rel_max]
        rels.setdefault('notes', []).append(f"Truncated to {rel_max} relationships")
    sections['relationships'] = rels
    timings['relationships_ms'] = round((time.time() - t0) * 1000, 2)

    # FAST profile: only summary + relationships for speed
    if profile == 'fast':
        try:
            sections['narrative'] = generate_narrative(sections.get('summary') or {}, sections.get('relationships') or {})
        except Exception:
            pass
        # Ensure a non-technical main purpose is available
        main_purpose = _simple_main_purpose(sections.get('summary') or {})
        what = main_purpose
        return {
            'success': True,
            'depth': 'light',
            'profile': profile,
            'include_bpa': False,
            'timings_ms': timings,
            'sections': sections,
            'what_the_model_does': what,
            'main_purpose': main_purpose,
            'generated_at': time.time(),
        }

    # Best practices (composite)
    from core.agent_policy import AgentPolicy
    ap = AgentPolicy(config)
    t0 = time.time()
    sections['best_practices'] = ap.validate_best_practices(connection_state)
    timings['best_practices_ms'] = round((time.time() - t0) * 1000, 2)

    # M practices
    try:
        dmv_cap = int(config.get('query.max_rows_preview', 1000))
    except Exception:
        dmv_cap = 1000
    sections['m_practices'] = scan_m_practices(query_executor, dmv_cap, issues_max)
    timings['m_practices_ms'] = round((time.time() - t0) * 1000, 2)

    # Optional BPA
    if include_bpa and profile != 'fast':
        t0 = time.time()
        tmsl = query_executor.get_tmsl_definition()
        if tmsl.get('success') and bpa_analyzer:
            viols = bpa_analyzer.analyze_model(tmsl['tmsl'])
            summary = bpa_analyzer.get_violations_summary()
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
            sections['bpa'] = {'success': False, 'error': 'TMSL unavailable or BPA analyzer missing'}
        timings['bpa_ms'] = round((time.time() - t0) * 1000, 2)

    # Optional deeper checks
    if depth in ('standard', 'deep') and performance_optimizer:
        t0 = time.time()
        sections['cardinality_overview'] = performance_optimizer.analyze_column_cardinality(None)
        timings['cardinality_overview_ms'] = round((time.time() - t0) * 1000, 2)
    if depth == 'deep' and performance_optimizer:
        t0 = time.time()
        sections['relationship_cardinality'] = performance_optimizer.analyze_relationship_cardinality()
        timings['relationship_cardinality_ms'] = round((time.time() - t0) * 1000, 2)

    # Narrative last
    try:
        sections['narrative'] = generate_narrative(sections.get('summary') or {}, sections.get('relationships') or {})
    except Exception:
        pass

    # Compute a simple main purpose for top-level convenience
    main_purpose = _simple_main_purpose(sections.get('summary') or {})
    what = main_purpose

    return {
        'success': True,
        'depth': depth,
        'profile': profile,
        'include_bpa': include_bpa,
        'timings_ms': timings,
        'sections': sections,
        'what_the_model_does': what,
        'main_purpose': main_purpose,
        'generated_at': time.time(),
    }
