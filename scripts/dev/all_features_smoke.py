import json
import os
import sys

# Ensure project root on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import pbixray_server_enhanced as srv  # type: ignore


def ok(d: dict) -> bool:
    return isinstance(d, dict) and d.get("success") is True


from typing import List, Optional


def print_res(name: str, res: dict, keys: Optional[List[str]] = None):
    keys = keys or []
    status = "OK" if ok(res) else "FAIL"
    print(f"{name}: {status}")
    if not ok(res):
        print(json.dumps(res, indent=2)[:1000])
    else:
        for k in keys:
            if k in res:
                v = res[k]
                if isinstance(v, list):
                    print(f"  - {k}: {len(v)} items")
                else:
                    sv = str(v)
                    print(f"  - {k}: {sv[:200]}{'...' if len(sv) > 200 else ''}")


def main():
    # Detect and connect
    det = srv._dispatch_tool("detect_powerbi_desktop", {})
    print_res("detect_powerbi_desktop", det, ["models"])    
    conn = srv._dispatch_tool("connect_to_powerbi", {"model_index": 0})
    print_res("connect_to_powerbi", conn, ["summary"])    

    # Basic metadata
    tables = srv._dispatch_tool("list_tables", {})
    print_res("list_tables", tables, ["row_count"])    
    columns = srv._dispatch_tool("list_columns", {"table": (tables.get("rows") or [{}])[0].get("Name") if ok(tables) and tables.get("rows") else None})
    print_res("list_columns", columns, ["row_count"])    
    measures = srv._dispatch_tool("list_measures", {})
    print_res("list_measures", measures, ["row_count"])    

    # Data sources & M expressions
    ds = srv._dispatch_tool("get_data_sources", {})
    print_res("get_data_sources", ds, ["row_count"])    
    mex = srv._dispatch_tool("get_m_expressions", {})
    print_res("get_m_expressions", mex, ["row_count"])    

    # Search & validation
    so = srv._dispatch_tool("search_objects", {"pattern": "*", "types": ["tables", "columns", "measures"]})
    print_res("search_objects", so, ["row_count"])    
    vd = srv._dispatch_tool("validate_dax_query", {"query": "EVALUATE ROW(\"A\", 1)"})
    print_res("validate_dax_query", vd, ["syntax_valid"])    

    # Performance basic path
    qp = srv._dispatch_tool("analyze_query_performance", {"query": "EVALUATE ROW(\"X\", 1)", "runs": 1, "clear_cache": True})
    print_res("analyze_query_performance", qp, ["success", "execution_time_ms"])    

    # Export
    schema = srv._dispatch_tool("export_model_schema", {"preview_size": 5})
    print_res("export_model_schema", schema, ["success"])    

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
