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
    if rels.get('success'):
        for r in rels.get('rows', []):
            ft = r.get('FromTable') or r.get('[FromTable]')
            tt = r.get('ToTable') or r.get('[ToTable]')
            fc = r.get('FromColumn') or r.get('[FromColumn]')
            tc = r.get('ToColumn') or r.get('[ToColumn]')
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
