import sys, os, json
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from src import pbixray_server_enhanced as srv

def run(name, args):
    print(f"=== {name} ===")
    res = srv._dispatch_tool(name, args)
    print(json.dumps({'success': res.get('success'), 'summary': res.get('summary'), 'error': res.get('error')}, indent=2))

if __name__ == '__main__':
    srv._dispatch_tool('connect_to_powerbi', {'model_index': 0})
    run('validate_model_integrity', {})
    run('analyze_relationship_cardinality', {})
    run('analyze_column_cardinality', {})
