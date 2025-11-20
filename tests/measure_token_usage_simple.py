#!/usr/bin/env python3
"""
Simplified Token Usage Measurement Script
Analyzes token consumption from manifest and schema files directly
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any

def estimate_tokens(text: str) -> int:
    """
    Estimate token count using simple heuristic
    ~3.5 characters per token for technical content
    """
    return int(len(text) / 3.5)

def load_manifest():
    """Load manifest.json"""
    manifest_path = Path(__file__).parent.parent / 'manifest.json'
    with open(manifest_path) as f:
        return json.load(f)

def load_tool_schemas():
    """Load tool schemas"""
    schemas_path = Path(__file__).parent.parent / 'server' / 'tool_schemas.py'

    # Execute the file to get TOOL_SCHEMAS
    import importlib.util
    spec = importlib.util.spec_from_file_location("tool_schemas", schemas_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.TOOL_SCHEMAS

def analyze_startup_tokens():
    """Analyze token usage on startup"""
    print("=" * 80)
    print("MCP Server Token Usage Analysis (Simplified)")
    print("=" * 80)
    print()

    # Load manifest
    manifest = load_manifest()
    tools_list = manifest.get('tools', [])

    # Load schemas
    try:
        tool_schemas = load_tool_schemas()
    except Exception as e:
        print(f"Warning: Could not load tool_schemas.py: {e}")
        tool_schemas = {}

    print(f"Total tools in manifest: {len(tools_list)}")
    print()

    # Analyze each tool
    results = []
    total_tokens = 0

    for tool in tools_list:
        tool_name = tool['name']
        description = tool['description']

        # Get schema from tool_schemas.py if available
        # Map numbered name to internal name
        internal_name = tool_name.replace('01_', '').replace('02_', '').replace('03_', '').replace('04_', '').replace('05_', '').replace('06_', '').replace('07_', '').replace('08_', '').replace('09_', '').replace('10_', '').replace('11_', '').replace('12_', '').replace('13_', '')
        internal_name = internal_name.replace('detect_pbi_instances', 'detect_powerbi_desktop')
        internal_name = internal_name.replace('connect_to_instance', 'connect_to_powerbi')

        # Try various name mappings
        schema = None
        possible_names = [
            internal_name,
            tool_name,
            internal_name.replace('_pbi_', '_powerbi_'),
            internal_name.replace('pbi_', 'powerbi_')
        ]

        for name in possible_names:
            if name in tool_schemas:
                schema = tool_schemas[name]
                break

        if not schema:
            schema = {"type": "object", "properties": {}, "required": []}

        # Measure tokens
        name_tokens = estimate_tokens(tool_name)
        desc_tokens = estimate_tokens(description)

        schema_text = json.dumps(schema, indent=2)
        schema_compact = json.dumps(schema, separators=(',', ':'))

        schema_tokens = estimate_tokens(schema_text)
        schema_compact_tokens = estimate_tokens(schema_compact)

        tool_total = name_tokens + desc_tokens + schema_tokens
        total_tokens += tool_total

        results.append({
            'name': tool_name,
            'name_tokens': name_tokens,
            'description_tokens': desc_tokens,
            'schema_tokens': schema_tokens,
            'schema_compact_tokens': schema_compact_tokens,
            'total_tokens': tool_total,
            'description_length': len(description),
            'schema_length': len(schema_text)
        })

    # Sort by token usage
    results.sort(key=lambda x: x['total_tokens'], reverse=True)

    print("Top 15 Tools by Token Usage:")
    print("-" * 80)
    print(f"{'Tool Name':<45} {'Desc':<8} {'Schema':<8} {'Total':<8}")
    print("-" * 80)

    for tool in results[:15]:
        print(f"{tool['name']:<45} {tool['description_tokens']:<8} {tool['schema_tokens']:<8} {tool['total_tokens']:<8}")

    print()
    print("=" * 80)
    print(f"TOTAL STARTUP TOKENS (estimated): {total_tokens:,}")
    print("=" * 80)
    print()

    # Optimization analysis
    print("Optimization Opportunities:")
    print("-" * 80)

    # Long descriptions
    long_desc = [t for t in results if t['description_tokens'] > 300]
    if long_desc:
        print(f"\n1. Tools with verbose descriptions (>300 tokens): {len(long_desc)} tools")
        for tool in long_desc[:5]:
            print(f"   - {tool['name']}: {tool['description_tokens']} tokens")
        if len(long_desc) > 5:
            print(f"   ... and {len(long_desc) - 5} more")

    # Complex schemas
    complex_schema = [t for t in results if t['schema_tokens'] > 200]
    if complex_schema:
        print(f"\n2. Tools with complex schemas (>200 tokens): {len(complex_schema)} tools")
        for tool in complex_schema[:5]:
            savings = tool['schema_tokens'] - tool['schema_compact_tokens']
            print(f"   - {tool['name']}: {tool['schema_tokens']} tokens (save {savings} with compact JSON)")
        if len(complex_schema) > 5:
            print(f"   ... and {len(complex_schema) - 5} more")

    # Estimate savings
    print()
    print("Estimated Savings Potential:")
    print("-" * 80)

    # Compact JSON
    total_compact_savings = sum(t['schema_tokens'] - t['schema_compact_tokens'] for t in results)
    print(f"1. Compact JSON: ~{total_compact_savings:,} tokens ({int(total_compact_savings / total_tokens * 100)}%)")

    # Description compression (assume 50% reduction for verbose ones)
    desc_tokens = sum(t['description_tokens'] for t in results)
    verbose_desc_tokens = sum(t['description_tokens'] for t in results if t['description_tokens'] > 150)
    estimated_desc_savings = verbose_desc_tokens * 0.5  # 50% reduction
    print(f"2. Description compression: ~{int(estimated_desc_savings):,} tokens ({int(estimated_desc_savings / total_tokens * 100)}%)")

    # Schema deduplication (assume 25% reduction)
    schema_tokens = sum(t['schema_tokens'] for t in results)
    estimated_schema_savings = schema_tokens * 0.25
    print(f"3. Schema deduplication: ~{int(estimated_schema_savings):,} tokens ({int(estimated_schema_savings / total_tokens * 100)}%)")

    # Progressive disclosure (only send 10 essential tools initially)
    essential_tool_count = 10
    essential_tokens = sum(t['total_tokens'] for t in results[:essential_tool_count])
    progressive_savings = total_tokens - essential_tokens
    print(f"4. Progressive disclosure (10 tools initially): ~{progressive_savings:,} tokens ({int(progressive_savings / total_tokens * 100)}%)")

    # Total savings
    conservative_savings = total_compact_savings + estimated_desc_savings + estimated_schema_savings
    aggressive_savings = progressive_savings

    print()
    print(f"CONSERVATIVE APPROACH (keep all tools visible):")
    print(f"  Total savings: ~{int(conservative_savings):,} tokens ({int(conservative_savings / total_tokens * 100)}%)")
    print(f"  Optimized startup: ~{int(total_tokens - conservative_savings):,} tokens")
    print()
    print(f"AGGRESSIVE APPROACH (progressive disclosure):")
    print(f"  Total savings: ~{int(aggressive_savings):,} tokens ({int(aggressive_savings / total_tokens * 100)}%)")
    print(f"  Optimized startup: ~{int(total_tokens - aggressive_savings):,} tokens")
    print()

    # Category analysis
    print("Token Usage by Category (from manifest):")
    print("-" * 60)

    categories = {}
    for tool in results:
        # Extract category from description [XX-Category]
        desc = tool['name']
        cat = "Unknown"
        for t in tools_list:
            if t['name'] == tool['name']:
                desc = t['description']
                if '[' in desc and ']' in desc:
                    cat = desc[desc.index('[')+1:desc.index(']')]
                break

        if cat not in categories:
            categories[cat] = {'count': 0, 'tokens': 0}
        categories[cat]['count'] += 1
        categories[cat]['tokens'] += tool['total_tokens']

    print(f"{'Category':<30} {'Tools':<8} {'Tokens':<12} {'Avg':<10}")
    print("-" * 60)

    for cat, data in sorted(categories.items(), key=lambda x: x[1]['tokens'], reverse=True):
        avg = int(data['tokens'] / data['count']) if data['count'] > 0 else 0
        print(f"{cat:<30} {data['count']:<8} {data['tokens']:<12} {avg:<10}")

    print()

    # Save report
    report_path = Path(__file__).parent.parent / 'token_usage_baseline.json'
    report = {
        'total_tools': len(results),
        'total_startup_tokens': total_tokens,
        'tools': results,
        'categories': categories,
        'optimization_potential': {
            'compact_json': int(total_compact_savings),
            'description_compression': int(estimated_desc_savings),
            'schema_deduplication': int(estimated_schema_savings),
            'progressive_disclosure': int(progressive_savings),
            'conservative_total_savings': int(conservative_savings),
            'aggressive_total_savings': int(aggressive_savings),
            'conservative_optimized': int(total_tokens - conservative_savings),
            'aggressive_optimized': int(total_tokens - aggressive_savings)
        }
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Baseline report saved to: {report_path}")
    print()

    return total_tokens

if __name__ == "__main__":
    analyze_startup_tokens()
