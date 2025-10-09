#!/usr/bin/env python3
"""
Export a flat table listing all tables and columns with sample values.

Behavior:
- Default output format is CSV (fast). You can override with env PBIXRAY_FORMAT=csv|txt|xlsx.
- Default sample rows per column is 3. You can override with env PBIXRAY_ROWS.
- Optional extras (comma-separated) via env PBIXRAY_EXTRAS, e.g. "Description,IsHidden".
- Files are written to the server's exports/ folder by default (no prompts).
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

    # Defaults: keep CSV for speed; allow optional overrides via env
    fmt_env = (os.environ.get('PBIXRAY_FORMAT') or '').strip().lower()
    fmt = fmt_env if fmt_env in {'csv', 'txt', 'xlsx'} else 'csv'

    rows_env = os.environ.get('PBIXRAY_ROWS')
    try:
        rows = max(1, min(10, int(rows_env))) if rows_env else 3
    except Exception:
        rows = 3

    # Optional extras via environment variable PBIXRAY_EXTRAS (comma-separated)
    extras_env = os.environ.get('PBIXRAY_EXTRAS')
    extras = [e.strip() for e in extras_env.split(',')] if extras_env else []

    # No output_dir provided => server uses exports/ automatically; no prompts
    res = srv._dispatch_tool('export_columns_with_samples', {'format': fmt, 'rows': rows, 'extras': extras})
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
