import json
import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from src import pbixray_server_enhanced as srv

def main():
    det = srv._dispatch_tool('detect_powerbi_desktop', {})
    conn = srv._dispatch_tool('connect_to_powerbi', {'model_index': 0})
    res = srv._dispatch_tool('list_tables', {})
    print('LIST_TABLES rows:', len(res.get('rows', [])))
    if res.get('rows'):
        print('First 5 table names:', [r.get('Name') or r.get('[Name]') or r.get('TABLE_NAME') or r.get('Table') for r in res['rows'][:5]])
    resm = srv._dispatch_tool('list_measures', {})
    print('LIST_MEASURES rows:', len(resm.get('rows', [])))
    resc = srv._dispatch_tool('list_columns', {})
    print('LIST_COLUMNS rows:', len(resc.get('rows', [])))

if __name__ == '__main__':
    main()
