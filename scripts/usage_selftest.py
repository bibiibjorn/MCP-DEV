import json
import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from src import pbixray_server_enhanced as srv  # type: ignore

def call(name, args):
    resp = srv._dispatch_tool(name, args)
    ok = isinstance(resp, dict) and resp.get('success')
    print(f"{name}: {'OK' if ok else 'FAIL'}")
    if not ok:
        print(json.dumps(resp, indent=2))
    return resp

srv._dispatch_tool('detect_powerbi_desktop', {})
conn = srv._dispatch_tool('connect_to_powerbi', {'model_index': 0})
print('connect:', conn.get('success'), conn.get('summary'))

# Choose a table and column
lt = srv._dispatch_tool('list_tables', {})
rows = lt.get('rows', []) or []
tab = None
for pref in ['d_Date', 'd_Period', 'f_FINREP']:
    if any((r.get('Name') or r.get('[Name]')) == pref for r in rows):
        tab = pref
        break
if not tab and rows:
    r0 = rows[0]
    tab = r0.get('Name') or r0.get('[Name]') or r0.get('TABLE_NAME') or r0.get('Table')

lc = srv._dispatch_tool('list_columns', {'table': tab})
col = None
if isinstance(lc, dict) and lc.get('success'):
    for r in (lc.get('rows', []) or []):
        typ = str(r.get('Type') or '').lower()
        if typ != 'calculated':
            col = r.get('Name') or r.get('[Name]') or r.get('COLUMN_NAME')
            if col:
                break
    if not col and (lc.get('rows') or []):
        r0 = lc['rows'][0]
        col = r0.get('Name') or r0.get('[Name]') or r0.get('COLUMN_NAME')
if not col:
    # Global fallback: pick any non-calculated column from entire model
    allc = srv._dispatch_tool('list_columns', {})
    for r in (allc.get('rows', []) or []):
        typ = str(r.get('Type') or '').lower()
        if typ != 'calculated':
            tab = r.get('Table') or r.get('[Table]') or r.get('TABLE_NAME') or tab
            col = r.get('Name') or r.get('[Name]') or r.get('COLUMN_NAME')
            if col:
                break

print('Sample table/column:', tab, col)

au = call('analyze_column_usage', {'table': tab, 'column': col})
print('usage summary:', au.get('summary'))

unused = call('find_unused_objects', {})
print('unused summary:', unused.get('summary'))
if isinstance(unused, dict):
    print('unused columns (first 5):', (unused.get('unused_columns') or [])[:5])
