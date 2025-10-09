import json
import os
import sys

# Ensure project root on path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import pbixray_server_enhanced as srv  # type: ignore


def main():
    det = srv._dispatch_tool('detect_powerbi_desktop', {})
    if not isinstance(det, dict) or not det.get('success'):
        print(json.dumps({'success': False, 'stage': 'detect_powerbi_desktop', 'details': det}, indent=2))
        return
    conn = srv._dispatch_tool('connect_to_powerbi', {'model_index': 0})
    if not isinstance(conn, dict) or not conn.get('success'):
        print(json.dumps({'success': False, 'stage': 'connect_to_powerbi', 'details': conn}, indent=2))
        return

    res = srv._dispatch_tool('export_compact_schema', {'include_hidden': True})
    ok = bool(isinstance(res, dict) and res.get('success'))
    out = {
        'success': ok,
        'tool': 'export_compact_schema',
        'error': None if ok else res,
    }
    if ok:
        stats = res.get('statistics') or {}
        out.update({
            'database': res.get('database_name'),
            'tables': stats.get('tables'),
            'columns': stats.get('columns'),
            'measures': stats.get('measures'),
            'relationships': stats.get('relationships'),
        })
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
