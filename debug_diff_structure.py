"""
Debug script to show EXACTLY what's in the diff structure
"""
import json
from pathlib import Path
from core.tmdl_parser import TmdlParser
from core.model_diff_engine import ModelDiffer

# Find the most recent TMDL exports in your exports folder
exports_dir = Path("exports/tmdl_exports")
if not exports_dir.exists():
    print("No TMDL exports found. Run a comparison first.")
    exit(1)

# Get the two most recent export folders
export_folders = sorted(exports_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
if len(export_folders) < 2:
    print(f"Only found {len(export_folders)} export folder(s). Need at least 2 for comparison.")
    exit(1)

folder1 = export_folders[1]  # Older
folder2 = export_folders[0]  # Newer

print("=" * 80)
print(f"COMPARING:")
print(f"  Model 1 (older): {folder1.name}")
print(f"  Model 2 (newer): {folder2.name}")
print("=" * 80)

# Parse both models
print("\nParsing models...")
parser1 = TmdlParser(str(folder1))
model1 = parser1.parse()

parser2 = TmdlParser(str(folder2))
model2 = parser2.parse()

print(f"Model 1: {len(model1.get('tables', []))} tables")
print(f"Model 2: {len(model2.get('tables', []))} tables")

# Run the diff
print("\nRunning diff engine...")
differ = ModelDiffer(model1, model2)
diff_result = differ.compare()

# Analyze the measures section in detail
measures_diff = diff_result.get('measures', {})
print("\n" + "=" * 80)
print("MEASURES DIFF STRUCTURE")
print("=" * 80)

print(f"\nAdded measures: {len(measures_diff.get('added', []))}")
print(f"Removed measures: {len(measures_diff.get('removed', []))}")
print(f"Modified measures: {len(measures_diff.get('modified', []))}")

# Look at the FIRST modified measure in detail
modified = measures_diff.get('modified', [])
if modified:
    first_mod = modified[0]
    print("\n" + "=" * 80)
    print(f"FIRST MODIFIED MEASURE: {first_mod.get('name')}")
    print("=" * 80)
    print(json.dumps(first_mod, indent=2))

    # Show what changes were detected
    changes = first_mod.get('changes', {})
    print("\n" + "=" * 80)
    print("CHANGES DETECTED:")
    print("=" * 80)
    for key, value in changes.items():
        print(f"\n{key}:")
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                print(f"  {sub_key}: {sub_val}")
        else:
            print(f"  {value}")

# Look at tables too
tables_diff = diff_result.get('tables', {})
modified_tables = tables_diff.get('modified', [])
if modified_tables:
    first_table = modified_tables[0]
    print("\n" + "=" * 80)
    print(f"FIRST MODIFIED TABLE: {first_table.get('name')}")
    print("=" * 80)
    print(json.dumps(first_table, indent=2, default=str)[:2000])  # First 2000 chars

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
