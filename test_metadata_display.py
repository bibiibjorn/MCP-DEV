"""
Test script to verify metadata is being captured and displayed in diff reports.
"""

import json
from pathlib import Path
from core.model_diff_report import ModelDiffReportGenerator

# Create a mock diff result with ALL types of changes
mock_diff = {
    "summary": {
        "model1_name": "Model V1",
        "model2_name": "Model V2",
        "total_changes": 1,
        "changes_by_category": {"measures": 1}
    },
    "tables": {
        "added": [],
        "removed": [],
        "modified": [],
        "unchanged": []
    },
    "measures": {
        "added": [],
        "removed": [],
        "modified": [
            {
                "name": "Test Measure",
                "table": "Sales",
                "changes": {
                    "expression": {
                        "from": "SUM(Sales[Amount])",
                        "to": "SUMX(Sales, Sales[Amount])",
                        "diff": "Changed from SUM to SUMX",
                        "impact": "high"
                    },
                    "description": {
                        "from": "Old description",
                        "to": "New description"
                    },
                    "is_hidden": {
                        "from": False,
                        "to": True
                    },
                    "format_string": {
                        "from": "#,0",
                        "to": "$#,0.00"
                    },
                    "display_folder": {
                        "from": "Metrics",
                        "to": "KPIs"
                    },
                    "data_category": {
                        "from": None,
                        "to": "Currency"
                    },
                    "annotations": {
                        "Author": {"from": None, "to": "John Doe"},
                        "ModifiedBy": {"from": "Jane Smith", "to": "John Doe"},
                        "Version": {"from": "1.0", "to": None}
                    }
                }
            }
        ]
    },
    "relationships": {"added": [], "removed": [], "modified": []},
    "roles": {"added": [], "removed": [], "modified": []},
    "perspectives": {"added": [], "removed": [], "modified": []},
    "model_properties": {}
}

# Generate the report
print("Generating test report...")
output_file = Path("exports/docs/test_metadata_display.html")
output_file.parent.mkdir(parents=True, exist_ok=True)

generator = ModelDiffReportGenerator(mock_diff)
html_output = generator.generate_html_report(str(output_file))

print(f"Test report generated: {output_file}")
print("\nOpen this file in a browser and check if you see:")
print("  1. Metadata change grid showing description, is_hidden, format_string, display_folder, data_category")
print("  2. Annotation changes section")
print("  3. DAX expression diff")
print("\nIf you DON'T see the metadata changes, there's a bug in the HTML generation.")
print("If you DO see them, then the issue is that your actual TMDL files don't have metadata changes.")
