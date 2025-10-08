from typing import Any, Dict
import time

from server.utils.m_practices import scan_m_practices
from core.model_narrative import generate_narrative


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
        what = None
        try:
            purpose = (sections.get('model_purpose') or {}).get('text')
            if purpose:
                what = purpose
            else:
                doms = (sections.get('model_purpose') or {}).get('domains') or []
                if doms:
                    what = ", ".join(doms[:5])
        except Exception:
            pass
        return {
            'success': True,
            'depth': 'light',
            'profile': profile,
            'include_bpa': False,
            'timings_ms': timings,
            'sections': sections,
            'what_the_model_does': what,
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

    what = None
    try:
        purpose = (sections.get('model_purpose') or {}).get('text')
        if purpose:
            what = purpose
        else:
            doms = (sections.get('model_purpose') or {}).get('domains') or []
            if doms:
                what = ", ".join(doms[:5])
    except Exception:
        pass

    return {
        'success': True,
        'depth': depth,
        'profile': profile,
        'include_bpa': include_bpa,
        'timings_ms': timings,
        'sections': sections,
        'what_the_model_does': what,
        'generated_at': time.time(),
    }
