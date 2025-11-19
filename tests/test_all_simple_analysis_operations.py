"""
Test All 9 Microsoft MCP Operations in simple_analysis tool

This script tests all 9 available modes in the simple_analysis tool.
Note: The default "all" mode runs 8 operations automatically (excludes "measure get" which requires parameters).
Each operation is optimized for speed (< 1s) with minimal output.
Partitions operation has been removed per requirements.
"""
import json
from pathlib import Path

# Test cases for all 9 simple_analysis modes
# NOTE: The default mode "all" runs 8 operations automatically (all except "measure" which requires table+measure_name)
# The 9 available modes are: all, tables, stats, measures, measure, columns, relationships, calculation_groups, roles, database
# The test cases below test each operation individually
TEST_OPERATIONS = [
    {
        "name": "1. Table List Operation",
        "description": "Ultra-fast table list (< 500ms) - Microsoft MCP List operation",
        "request": {
            "mode": "tables"
        },
        "expected_fields": ["success", "analysis_type", "table_count", "tables"],
        "expected_operation": "table_list"
    },
    {
        "name": "2. Model Statistics Operation",
        "description": "Fast model statistics (< 1s) - Microsoft MCP GetStats operation",
        "request": {
            "mode": "stats"
        },
        "expected_fields": ["success", "analysis_type", "model", "counts", "tables", "summary"],
        "expected_operation": "simple_stats"
    },
    {
        "name": "3. Measure List Operation",
        "description": "List measures - Microsoft MCP Measure List operation",
        "request": {
            "mode": "measures",
            "max_results": 50
        },
        "expected_fields": ["success", "operation", "message", "data"],
        "expected_operation": "List"
    },
    {
        "name": "4. Measure Get Operation",
        "description": "Get measure details - Microsoft MCP Measure Get operation",
        "request": {
            "mode": "measure",
            "table": "m_Measures",
            "measure_name": "Total Sales"  # Example - adjust to your model
        },
        "expected_fields": ["success", "operation", "measureName", "tableName", "data"],
        "expected_operation": "Get",
        "note": "Requires valid measure name from your model"
    },
    {
        "name": "5. Column List Operation",
        "description": "List columns - Microsoft MCP Column List operation",
        "request": {
            "mode": "columns",
            "max_results": 20
        },
        "expected_fields": ["success", "operation", "message", "data"],
        "expected_operation": "List"
    },
    {
        "name": "6. Relationship List Operation",
        "description": "List all relationships - Microsoft MCP Relationship List operation",
        "request": {
            "mode": "relationships",
            "active_only": False
        },
        "expected_fields": ["success", "operation", "message", "data"],
        "expected_operation": "LIST"
    },
    {
        "name": "7. Calculation Group List Operation",
        "description": "List calculation groups - Microsoft MCP ListGroups operation",
        "request": {
            "mode": "calculation_groups"
        },
        "expected_fields": ["success", "operation", "message", "data"],
        "expected_operation": "ListGroups"
    },
    {
        "name": "8. Security Role List Operation",
        "description": "List security roles - Microsoft MCP Role List operation",
        "request": {
            "mode": "roles"
        },
        "expected_fields": ["success", "operation", "message", "data"],
        "expected_operation": "List"
    },
    {
        "name": "9. Database List Operation",
        "description": "List databases - Microsoft MCP Database List operation",
        "request": {
            "mode": "database"
        },
        "expected_fields": ["success", "operation", "message", "data"],
        "expected_operation": "List"
    }
]


def print_test_summary():
    """Print summary of all 9 test operations"""
    print("=" * 80)
    print("MICROSOFT MCP SIMPLE_ANALYSIS - ALL 9 AVAILABLE MODES TEST PLAN")
    print("=" * 80)
    print()
    print("NOTE: The 'all' mode (default) runs 8 operations automatically.")
    print("      The 'measure' mode requires table+measure_name parameters.")
    print("=" * 80)
    print()

    for i, test in enumerate(TEST_OPERATIONS, 1):
        print(f"{i}. {test['name']}")
        print(f"   Description: {test['description']}")
        print(f"   Request: {json.dumps(test['request'], indent=6)}")
        print(f"   Expected Operation: {test['expected_operation']}")
        if 'note' in test:
            print(f"   Note: {test['note']}")
        print()

    print("=" * 80)
    print("ALL 9 MODES READY FOR TESTING")
    print("8 auto-executable + 1 parameterized (measure get)")
    print("=" * 80)


def generate_test_requests_json():
    """Generate JSON file with all test requests"""
    output = {
        "description": "Test all 9 available modes in simple_analysis tool. The 'all' mode (default) runs 8 operations automatically. The 'measure' mode requires table+measure_name parameters.",
        "total_modes": len(TEST_OPERATIONS),
        "auto_executable_operations": 8,
        "parameterized_operations": 1,
        "operations": []
    }

    for test in TEST_OPERATIONS:
        operation = {
            "name": test["name"],
            "description": test["description"],
            "tool": "simple_analysis",
            "request": test["request"],
            "expected_fields": test["expected_fields"],
            "expected_operation": test["expected_operation"]
        }
        if "note" in test:
            operation["note"] = test["note"]

        output["operations"].append(operation)

    # Save to file
    output_path = Path(__file__).parent / "simple_analysis_all_operations_test.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Test requests saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    print_test_summary()
    print()
    generate_test_requests_json()
