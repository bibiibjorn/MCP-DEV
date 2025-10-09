import json
import os
import sys

# Ensure project root on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

try:
	from src import pbixray_server_enhanced as srv  # type: ignore
except Exception as e:
	raise SystemExit(f"Failed to import server: {e}")


def ok(d: dict) -> bool:
	return isinstance(d, dict) and d.get("success") is True


def main():
	# Detect and connect
	det = srv._dispatch_tool("detect_powerbi_desktop", {})
	if not ok(det):
		print("detect_powerbi_desktop: FAIL")
		print(json.dumps(det, indent=2))
		return 1
	models = det.get("models") or det.get("results") or []
	if not models:
		print("No Power BI Desktop models detected.")
		return 2
	conn = srv._dispatch_tool("connect_to_powerbi", {"model_index": 0})
	print("connect:", conn.get("success"), conn.get("summary"))
	if not ok(conn):
		print(json.dumps(conn, indent=2))
		return 3

	# List tables and pick a sample table
	lt = srv._dispatch_tool("list_tables", {})
	if not ok(lt):
		print("list_tables: FAIL")
		print(json.dumps(lt, indent=2))
		return 4
	rows = lt.get("rows", []) or lt.get("results", []) or []
	table_name = None
	# Prefer common dimension/fact names; else first
	for pref in ["d_Date", "d_Period", "f_FINREP"]:
		if any((r.get("Name") or r.get("[Name]") or r.get("TABLE_NAME")) == pref for r in rows):
			table_name = pref
			break
	if not table_name and rows:
		r0 = rows[0]
		table_name = r0.get("Name") or r0.get("[Name]") or r0.get("TABLE_NAME")
	print("Sample table:", table_name)
	if not table_name:
		print("No tables found.")
		return 5

	# Pick a non-calculated column from that table
	lc = srv._dispatch_tool("list_columns", {"table": table_name})
	if not ok(lc):
		print("list_columns: FAIL")
		print(json.dumps(lc, indent=2))
		return 6
	col_name = None
	for r in (lc.get("rows") or lc.get("results") or []):
		t = str(r.get("Type") or r.get("[Type]") or r.get("DATA_TYPE") or "").lower()
		if t != "calculated":
			col_name = r.get("Name") or r.get("[Name]") or r.get("COLUMN_NAME")
			break
	if not col_name:
		cols = (lc.get("rows") or lc.get("results") or [])
		if cols:
			r0 = cols[0]
			col_name = r0.get("Name") or r0.get("[Name]") or r0.get("COLUMN_NAME")
	print("Sample column:", col_name)
	if not col_name:
		print("No columns found on table.")
		return 7

	# Column usage analysis (supported)
	au = srv._dispatch_tool("analyze_column_usage", {"table": table_name, "column": col_name})
	print("analyze_column_usage:", "OK" if ok(au) else "FAIL")
	if not ok(au):
		print(json.dumps(au, indent=2))

	# Unused objects
	fu = srv._dispatch_tool("find_unused_objects", {})
	print("find_unused_objects:", "OK" if ok(fu) else "FAIL")
	if not ok(fu):
		print(json.dumps(fu, indent=2))
	else:
		summary = fu.get("summary") or ""
		print("unused summary:", summary[:200] + ("..." if len(summary) > 200 else ""))

	# Quick describe table and preview
	dt = srv._dispatch_tool("describe_table", {"table": table_name, "columns_page_size": 10, "measures_page_size": 10})
	print("describe_table:", "OK" if ok(dt) else "FAIL")
	if not ok(dt):
		print(json.dumps(dt, indent=2))

	pv = srv._dispatch_tool("preview_table_data", {"table": table_name, "top_n": 5})
	print("preview_table_data:", "OK" if ok(pv) else "FAIL")
	if not ok(pv):
		print(json.dumps(pv, indent=2))

	return 0


if __name__ == "__main__":
	raise SystemExit(main())

