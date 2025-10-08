from typing import Any, Dict, List


def export_relationship_graph(query_executor: Any, fmt: str = 'json') -> Dict[str, Any]:
    tables = query_executor.execute_info_query("TABLES")
    rels = query_executor.execute_info_query("RELATIONSHIPS")
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
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
            for k in ('fromColumn','toColumn','active','direction','cardinality'):
                _data(k)
            parts.append('    </edge>')
        parts.append('  </graph>')
        parts.append('</graphml>')
        graphml = '\n'.join(parts)
        return {'success': True, 'format': 'graphml', 'graphml': graphml, 'counts': {'nodes': len(nodes), 'edges': len(edges)}}
    else:
        return {'success': True, 'format': 'json', 'nodes': nodes, 'edges': edges, 'counts': {'nodes': len(nodes), 'edges': len(edges)}}
