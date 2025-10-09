#!/usr/bin/env python3
"""
Export a flat table listing all tables and columns with sample values.
Writes to exports/ as CSV/TXT/XLSX and prints the JSON result.
"""
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import pbixray_server_enhanced as srv  # type: ignore


def main():
    # Auto-detect and connect to first instance
    det = srv._dispatch_tool('detect_powerbi_desktop', {})
    conn = srv._dispatch_tool('connect_to_powerbi', {'model_index': 0})
    # Run export with defaults (xlsx if openpyxl installed, else csv)
    fmt = 'xlsx'
    try:
        import importlib.util
        if importlib.util.find_spec('openpyxl') is None:
            fmt = 'csv'
    except Exception:
        fmt = 'csv'
    # Allow optional extras via environment variable PBIXRAY_EXTRAS (comma-separated)
    extras_env = os.environ.get('PBIXRAY_EXTRAS')
    extras = [e.strip() for e in extras_env.split(',')] if extras_env else []
    res = srv._dispatch_tool('export_columns_with_samples', {'format': fmt, 'rows': 3, 'extras': extras})
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
