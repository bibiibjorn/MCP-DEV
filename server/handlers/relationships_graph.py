from typing import Any, Dict, List


def export_relationship_graph(query_executor: Any, fmt: str = 'json') -> Dict[str, Any]:
    """Export a lightweight relationship graph.

    Backward-compatible JSON output now includes rich details:
    - nodes: id, label, hidden, details (raw INFO.TABLES row when available)
    - edges: from, to, fromColumn, toColumn, active, direction, cardinality,
             id (stable key) and details (raw INFO.RELATIONSHIPS row)
    """
    tables = query_executor.execute_info_query("TABLES")
    rels = query_executor.execute_info_query("RELATIONSHIPS")
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    tnames = set()
    if tables.get('success'):
        for t in tables.get('rows', []):
            nm = t.get('Name') or t.get('[Name]')
            if nm and nm not in tnames:
                # Preserve prior shape and enrich with details
                nodes.append({
                    'id': nm,
                    'label': nm,
                    'hidden': bool(t.get('IsHidden')),
                    'details': t  # raw row for consumers needing more metadata
                })
                tnames.add(nm)
    # Build ID -> name maps as fallback when relationship rows carry only IDs
    id_to_table: Dict[str, str] = {}
    id_to_column: Dict[str, str] = {}
    if tables.get('success'):
        for t in tables.get('rows', []):
            tid = t.get('ID') or t.get('TableID') or t.get('[ID]') or t.get('[TableID]')
            nm = t.get('Name') or t.get('[Name]')
            if tid is not None and nm:
                id_to_table[str(tid)] = str(nm)
    cols = query_executor.execute_info_query("COLUMNS")
    if cols.get('success'):
        for c in cols.get('rows', []):
            cid = c.get('ID') or c.get('ColumnID') or c.get('[ID]') or c.get('[ColumnID]')
            cn = c.get('Name') or c.get('[Name]')
            if cid is not None and cn:
                id_to_column[str(cid)] = str(cn)

    if rels.get('success'):
        for r in rels.get('rows', []):
            ft = r.get('FromTable') or r.get('[FromTable]')
            tt = r.get('ToTable') or r.get('[ToTable]')
            fc = r.get('FromColumn') or r.get('[FromColumn]')
            tc = r.get('ToColumn') or r.get('[ToColumn]')
            if not ft:
                ftid = r.get('FromTableID') or r.get('[FromTableID]')
                if ftid is not None and str(ftid) in id_to_table:
                    ft = id_to_table[str(ftid)]
            if not tt:
                ttid = r.get('ToTableID') or r.get('[ToTableID]')
                if ttid is not None and str(ttid) in id_to_table:
                    tt = id_to_table[str(ttid)]
            if not fc:
                fcid = r.get('FromColumnID') or r.get('[FromColumnID]')
                if fcid is not None and str(fcid) in id_to_column:
                    fc = id_to_column[str(fcid)]
            if not tc:
                tcid = r.get('ToColumnID') or r.get('[ToColumnID]')
                if tcid is not None and str(tcid) in id_to_column:
                    tc = id_to_column[str(tcid)]
            edge = {
                'from': ft,
                'to': tt,
                'fromColumn': fc,
                'toColumn': tc,
                'active': bool(r.get('IsActive')),
                'direction': r.get('CrossFilterDirection') or r.get('CrossFilteringBehavior'),
                'cardinality': r.get('Cardinality'),
                # Stable ID helps clients map edge -> details quickly
                'id': f"{ft}.{fc}->{tt}.{tc}",
                # Attach full raw relationship row for detailed consumers
                'details': r,
            }
            edges.append(edge)
    fmt = (fmt or 'json').lower()
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
            # Ensure source/target are non-empty strings
            s = (e.get('from') or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            t = (e.get('to') or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            parts.append(f'    <edge source="{s}" target="{t}">')
            def _data(k):
                v = e.get(k)
                if v is None:
                    return
                text = str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                parts.append(f'      <data key="{k}">{text}</data>')
            for k in ('fromColumn','toColumn','active','direction','cardinality','id'):
                _data(k)
            parts.append('    </edge>')
        parts.append('  </graph>')
        parts.append('</graphml>')
        graphml = '\n'.join(parts)
        return {
            'success': True,
            'format': 'graphml',
            'graphml': graphml,
            'counts': {'nodes': len(nodes), 'edges': len(edges)}
        }
    else:
        return {
            'success': True,
            'format': 'json',
            'nodes': nodes,
            'edges': edges,
            'relationships': rels.get('rows', []) if rels.get('success') else [],
            'counts': {'nodes': len(nodes), 'edges': len(edges)}
        }
