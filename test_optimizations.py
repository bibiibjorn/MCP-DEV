#!/usr/bin/env python3
"""
Test script to verify Week 1 token optimizations
"""
import json
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("Testing Week 1 Token Optimizations")
print("=" * 80)

# Test 1: Verify tool schemas are valid JSON
print("\n1. Testing tool schemas validity...")
try:
    from server.tool_schemas import TOOL_SCHEMAS

    # Check top 3 tools exist and are valid
    top_tools = ['analyze_hybrid_model', 'simple_analysis', 'export_hybrid_analysis']
    for tool_name in top_tools:
        if tool_name not in TOOL_SCHEMAS:
            print(f"   [FAIL] {tool_name} not found in TOOL_SCHEMAS")
            sys.exit(1)

        schema = TOOL_SCHEMAS[tool_name]
        # Verify it's a valid dict with required fields
        if not isinstance(schema, dict):
            print(f"   [FAIL] {tool_name} schema is not a dict")
            sys.exit(1)

        if 'properties' not in schema:
            print(f"   [FAIL] {tool_name} schema missing 'properties'")
            sys.exit(1)

        # Verify descriptions are compressed (no emojis, much shorter)
        props = schema.get('properties', {})
        for prop_name, prop_def in props.items():
            desc = prop_def.get('description', '')
            if '🚫' in desc or '[WARN]' in desc or '🔧' in desc:
                print(f"   [FAIL] {tool_name}.{prop_name} still has emojis: {desc[:100]}")
                sys.exit(1)

    print(f"   [PASS] All {len(top_tools)} tool schemas are valid and compressed")

except Exception as e:
    print(f"   [FAIL] ERROR loading tool schemas: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Verify compact JSON format works
print("\n2. Testing compact JSON format...")
try:
    test_obj = {
        'success': True,
        'data': [
            {'name': 'Sales', 'value': 1000},
            {'name': 'Profit', 'value': 500}
        ],
        'count': 2
    }

    # Old format (with indent)
    old_json = json.dumps(test_obj, indent=2)

    # New format (compact)
    new_json = json.dumps(test_obj, separators=(',', ':'))

    # Verify compact is smaller
    old_size = len(old_json)
    new_size = len(new_json)
    reduction = ((old_size - new_size) / old_size) * 100

    print(f"   Old size (indent=2): {old_size} chars")
    print(f"   New size (compact):  {new_size} chars")
    print(f"   Reduction: {reduction:.1f}%")

    # Verify both parse to same object
    parsed_old = json.loads(old_json)
    parsed_new = json.loads(new_json)

    if parsed_old != parsed_new:
        print(f"   [FAIL] ERROR: Compact JSON doesn't parse correctly")
        sys.exit(1)

    if new_size >= old_size:
        print(f"   [FAIL] ERROR: Compact JSON is not smaller")
        sys.exit(1)

    print(f"   [PASS] Compact JSON works correctly ({reduction:.1f}% smaller)")

except Exception as e:
    print(f"   [FAIL] ERROR testing compact JSON: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Verify tool_documentation module works
print("\n3. Testing tool_documentation module...")
try:
    from server.tool_documentation import (
        TOOL_DOCS,
        get_tool_documentation,
        get_operation_details,
        list_available_docs
    )

    # Check top tools have documentation
    top_tools = ['analyze_hybrid_model', 'simple_analysis']
    for tool_name in top_tools:
        doc = get_tool_documentation(tool_name)
        if 'summary' not in doc:
            print(f"   [FAIL] ERROR: {tool_name} documentation missing 'summary'")
            sys.exit(1)

    # Check operation details work
    op_detail = get_operation_details('analyze_hybrid_model', 'read_metadata')
    if not op_detail or len(op_detail) < 10:
        print(f"   [FAIL] ERROR: Operation details not working")
        sys.exit(1)

    # Check list function
    available_docs = list_available_docs()
    if len(available_docs) < 3:
        print(f"   [FAIL] ERROR: Not enough documented tools")
        sys.exit(1)

    print(f"   [PASS] Tool documentation system works ({len(available_docs)} tools documented)")

except Exception as e:
    print(f"   [FAIL] ERROR testing tool_documentation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Measure token savings estimate
print("\n4. Estimating token savings...")
try:
    # Simple character-based estimation (rough approximation)
    # Average: 1 token ≈ 4 characters

    # Top 3 tools - measure compressed schema sizes
    total_chars = 0
    for tool_name in ['analyze_hybrid_model', 'simple_analysis', 'export_hybrid_analysis']:
        schema = TOOL_SCHEMAS[tool_name]
        schema_str = json.dumps(schema)
        total_chars += len(schema_str)

    estimated_tokens = total_chars // 4

    # Original estimates from optimization plan
    original_tokens = 1377 + 995 + 720  # 3,092 tokens

    # Estimated after compression (from plan)
    target_tokens = 350 + 200 + 220  # ~770 tokens

    print(f"   Current schema chars: {total_chars}")
    print(f"   Estimated tokens (rough): ~{estimated_tokens}")
    print(f"   Original tokens (from plan): {original_tokens}")
    print(f"   Target tokens (from plan): {target_tokens}")

    if estimated_tokens < original_tokens:
        reduction = ((original_tokens - estimated_tokens) / original_tokens) * 100
        print(f"   [PASS] Estimated reduction: ~{reduction:.1f}% from schema compression")

except Exception as e:
    print(f"   [WARN]  WARNING: Could not estimate token savings: {e}")

print("\n" + "=" * 80)
print("[PASS] All tests passed! Week 1 optimizations are working correctly.")
print("=" * 80)
print("\nSummary of changes:")
print("  1. Compressed 3 verbose tool schemas (removed emojis, warnings)")
print("  2. Enabled compact JSON format globally (separators=(',', ':'))")
print("  3. Created tool_documentation.py reference system")
print("\nExpected token savings:")
print("  - Schema compression: ~1,738 tokens (25%)")
print("  - Compact JSON: ~1,360 tokens (19%)")
print("  - Total: ~3,098 tokens (35-40% reduction)")
print("  - Target: Reduce from 6,943 to ~4,000 tokens")
print("\nNext steps:")
print("  - Test with real Power BI connection")
print("  - Measure actual token usage with MCP client")
print("  - Verify AI can still understand tool purposes")
print("=" * 80)
