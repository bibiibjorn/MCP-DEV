"""
Test the new V2 HTML report with your actual diff data
"""
import json
from pathlib import Path
from core.model_diff_report_v2 import ModelDiffReportV2

# Load your actual diff JSON
json_path = Path("exports/model_diffs/model_diff_20251020_223959.json")
if not json_path.exists():
    print(f"ERROR: JSON file not found: {json_path}")
    exit(1)

print("Loading diff JSON...")
with open(json_path, 'r', encoding='utf-8') as f:
    diff_data = json.load(f)

print(f"Loaded diff with {diff_data['summary']['total_changes']} changes")

# Generate new HTML report
output_path = "exports/model_diffs/model_diff_V2_TEST.html"
print(f"Generating new V2 HTML report...")

generator = ModelDiffReportV2(diff_data)
html_output = generator.generate_html(output_path)

print(f"\nSUCCESS! New HTML report generated:")
print(f"  {output_path}")
print(f"  Size: {len(html_output):,} bytes")
print("\nOpen this file in your browser to see the new modern layout!")
print("It will show:")
print("  - Clean, modern design")
print("  - ALL added/removed/modified items")
print("  - Expandable cards for modified items")
print("  - Side-by-side DAX comparison")
print("  - Full metadata changes")
print("  - Nested table > column/measure changes")
