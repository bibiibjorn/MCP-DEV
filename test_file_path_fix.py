"""
Test that generate_html returns file path, not HTML content
"""
from pathlib import Path
from core.model_diff_report_v2 import ModelDiffReportV2

# Create minimal test diff
test_diff = {
    "summary": {
        "model1_name": "Test Model 1",
        "model2_name": "Test Model 2",
        "total_changes": 1,
        "changes_by_category": {
            "tables_added": 1,
            "tables_removed": 0,
            "tables_modified": 0,
            "measures_added": 0,
            "measures_removed": 0,
            "measures_modified": 0
        }
    },
    "tables": {
        "added": [{"name": "TestTable", "columns_count": 1, "measures_count": 0}],
        "removed": [],
        "modified": []
    },
    "measures": {
        "added": [],
        "removed": [],
        "modified": []
    },
    "relationships": {
        "added": [],
        "removed": [],
        "modified": []
    },
    "roles": {
        "added": [],
        "removed": [],
        "modified": []
    },
    "perspectives": {
        "added": [],
        "removed": [],
        "modified": []
    }
}

# Generate report
output_path = "exports/model_diffs/test_file_path.html"
generator = ModelDiffReportV2(test_diff)
result = generator.generate_html(output_path)

# Verify result is file path, not HTML content
print(f"Result type: {type(result)}")
print(f"Result value: {result[:100]}..." if len(result) > 100 else f"Result value: {result}")

# Check if result looks like a file path
if result.startswith("<!DOCTYPE") or result.startswith("<html"):
    print("\n❌ FAIL: Result contains HTML content instead of file path!")
    exit(1)
elif Path(result).exists():
    print(f"\n✓ SUCCESS: Result is valid file path: {result}")
    print(f"✓ File exists and is {Path(result).stat().st_size:,} bytes")

    # Verify the file contains HTML
    with open(result, 'r', encoding='utf-8') as f:
        content = f.read()
        if content.startswith("<!DOCTYPE"):
            print("✓ File contains valid HTML content")
        else:
            print("❌ File does not contain valid HTML")
else:
    print(f"\n❌ FAIL: Result is not a valid file path: {result}")
    exit(1)
