#!/usr/bin/env python3
"""
Token Usage Measurement Script
Measures token consumption for MCP server startup and operations
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import MCP server components
from server.registry import get_registry
from server.handlers import register_all_handlers
from mcp.types import Tool

def estimate_tokens(text: str) -> int:
    """
    Estimate token count using simple heuristic
    (OpenAI's tiktoken uses ~4 chars per token for English text)
    For JSON/technical content, use ~3.5 chars per token
    """
    # Simple estimation: 1 token ≈ 3.5 characters for technical content
    return len(text) // 3.5

def estimate_tokens_precise(text: str) -> int:
    """
    More precise token estimation using tiktoken if available
    Falls back to simple estimation
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return estimate_tokens(text)

def measure_tool_tokens(tool: Tool, precise: bool = False) -> Dict[str, Any]:
    """Measure tokens for a single tool"""
    estimator = estimate_tokens_precise if precise else estimate_tokens

    # Measure individual components
    name_tokens = estimator(tool.name)
    desc_tokens = estimator(tool.description)
    schema_text = json.dumps(tool.inputSchema, indent=2)
    schema_tokens = estimator(schema_text)

    # Compact schema for comparison
    schema_compact = json.dumps(tool.inputSchema, separators=(',', ':'))
    schema_compact_tokens = estimator(schema_compact)

    total_tokens = name_tokens + desc_tokens + schema_tokens

    return {
        'name': tool.name,
        'name_tokens': int(name_tokens),
        'description_tokens': int(desc_tokens),
        'schema_tokens': int(schema_tokens),
        'schema_compact_tokens': int(schema_compact_tokens),
        'total_tokens': int(total_tokens),
        'description_length': len(tool.description),
        'schema_length': len(schema_text),
        'schema_compact_length': len(schema_compact)
    }

def measure_startup_tokens(precise: bool = False):
    """Measure tokens sent on MCP server startup"""
    print("=" * 80)
    print("MCP Server Token Usage Analysis")
    print("=" * 80)
    print()

    # Initialize registry
    registry = get_registry()
    register_all_handlers(registry)

    # Get all tools
    tools = registry.get_all_tools_as_mcp()

    print(f"Total tools registered: {len(tools)}")
    print()

    # Measure each tool
    results = []
    total_startup_tokens = 0

    for tool in tools:
        tool_metrics = measure_tool_tokens(tool, precise)
        results.append(tool_metrics)
        total_startup_tokens += tool_metrics['total_tokens']

    # Sort by token usage (highest first)
    results.sort(key=lambda x: x['total_tokens'], reverse=True)

    print("Top 10 Tools by Token Usage:")
    print("-" * 80)
    print(f"{'Tool Name':<40} {'Desc':<8} {'Schema':<8} {'Total':<8}")
    print("-" * 80)

    for tool in results[:10]:
        print(f"{tool['name']:<40} {tool['description_tokens']:<8} {tool['schema_tokens']:<8} {tool['total_tokens']:<8}")

    print()
    print("=" * 80)
    print(f"TOTAL STARTUP TOKENS: {int(total_startup_tokens):,}")
    print("=" * 80)
    print()

    # Category breakdown
    categories = {}
    for tool_def in registry.get_all_tools():
        cat = tool_def.category
        if cat not in categories:
            categories[cat] = {'count': 0, 'tokens': 0}
        categories[cat]['count'] += 1

    # Match tokens to categories
    for tool_metrics in results:
        tool_name = tool_metrics['name']
        # Resolve internal name
        from server.dispatch import ToolDispatcher
        internal_name = tool_name
        for k, v in ToolDispatcher.TOOL_NAME_MAP.items():
            if k == tool_name:
                internal_name = v
                break

        try:
            tool_def = registry.get_tool_def(internal_name)
            cat = tool_def.category
            if cat in categories:
                categories[cat]['tokens'] += tool_metrics['total_tokens']
        except KeyError:
            pass

    print("Token Usage by Category:")
    print("-" * 60)
    print(f"{'Category':<30} {'Tools':<8} {'Tokens':<12} {'Avg/Tool':<10}")
    print("-" * 60)

    for cat, data in sorted(categories.items(), key=lambda x: x[1]['tokens'], reverse=True):
        avg = int(data['tokens'] / data['count']) if data['count'] > 0 else 0
        print(f"{cat:<30} {data['count']:<8} {int(data['tokens']):<12} {avg:<10}")

    print()

    # Optimization opportunities
    print("Optimization Opportunities:")
    print("-" * 80)

    # Find tools with long descriptions
    long_desc = [t for t in results if t['description_tokens'] > 500]
    if long_desc:
        print(f"\n1. Tools with verbose descriptions (>{500} tokens):")
        for tool in long_desc[:5]:
            print(f"   - {tool['name']}: {tool['description_tokens']} tokens ({tool['description_length']} chars)")
        if len(long_desc) > 5:
            print(f"   ... and {len(long_desc) - 5} more")

    # Find tools with complex schemas
    complex_schema = [t for t in results if t['schema_tokens'] > 300]
    if complex_schema:
        print(f"\n2. Tools with complex schemas (>{300} tokens):")
        for tool in complex_schema[:5]:
            savings = tool['schema_tokens'] - tool['schema_compact_tokens']
            print(f"   - {tool['name']}: {tool['schema_tokens']} tokens (compact: {tool['schema_compact_tokens']}, save {savings})")
        if len(complex_schema) > 5:
            print(f"   ... and {len(complex_schema) - 5} more")

    # Estimate savings
    print()
    print("Estimated Savings Potential:")
    print("-" * 80)

    # Compact JSON savings
    total_compact_savings = sum(t['schema_tokens'] - t['schema_compact_tokens'] for t in results)
    print(f"1. Compact JSON (remove whitespace): ~{int(total_compact_savings):,} tokens ({int(total_compact_savings / total_startup_tokens * 100)}%)")

    # Description compression savings
    desc_tokens = sum(t['description_tokens'] for t in results)
    estimated_desc_savings = desc_tokens * 0.5  # Assume 50% reduction possible
    print(f"2. Description compression: ~{int(estimated_desc_savings):,} tokens ({int(estimated_desc_savings / total_startup_tokens * 100)}%)")

    # Schema deduplication savings
    schema_tokens = sum(t['schema_tokens'] for t in results)
    estimated_schema_savings = schema_tokens * 0.25  # Assume 25% reduction via deduplication
    print(f"3. Schema deduplication (JSON $ref): ~{int(estimated_schema_savings):,} tokens ({int(estimated_schema_savings / total_startup_tokens * 100)}%)")

    # Total potential savings
    total_savings = total_compact_savings + estimated_desc_savings + estimated_schema_savings
    print()
    print(f"TOTAL POTENTIAL SAVINGS: ~{int(total_savings):,} tokens ({int(total_savings / total_startup_tokens * 100)}%)")
    print(f"OPTIMIZED STARTUP TOKENS: ~{int(total_startup_tokens - total_savings):,} tokens")
    print()

    # Save detailed report
    report_path = os.path.join(parent_dir, 'token_usage_report.json')
    report = {
        'timestamp': str(os.path.getmtime(__file__)),
        'total_tools': len(tools),
        'total_startup_tokens': int(total_startup_tokens),
        'tools': results,
        'categories': categories,
        'optimization_potential': {
            'compact_json': int(total_compact_savings),
            'description_compression': int(estimated_desc_savings),
            'schema_deduplication': int(estimated_schema_savings),
            'total_savings': int(total_savings),
            'optimized_total': int(total_startup_tokens - total_savings)
        }
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Detailed report saved to: {report_path}")
    print()

    return total_startup_tokens

def compare_reports(old_report_path: str, new_report_path: str):
    """Compare two token usage reports"""
    with open(old_report_path) as f:
        old = json.load(f)
    with open(new_report_path) as f:
        new = json.load(f)

    old_tokens = old['total_startup_tokens']
    new_tokens = new['total_startup_tokens']
    diff = old_tokens - new_tokens
    pct = (diff / old_tokens) * 100

    print("=" * 80)
    print("Token Usage Comparison")
    print("=" * 80)
    print(f"Before: {old_tokens:,} tokens")
    print(f"After:  {new_tokens:,} tokens")
    print(f"Reduction: {diff:,} tokens ({pct:.1f}%)")
    print("=" * 80)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Measure MCP server token usage')
    parser.add_argument('--precise', action='store_true', help='Use tiktoken for precise measurement (requires tiktoken package)')
    parser.add_argument('--compare', nargs=2, metavar=('OLD', 'NEW'), help='Compare two token reports')

    args = parser.parse_args()

    if args.compare:
        compare_reports(args.compare[0], args.compare[1])
    else:
        if args.precise:
            try:
                import tiktoken
                print("Using tiktoken for precise token measurement")
            except ImportError:
                print("WARNING: tiktoken not installed, using simple estimation")
                print("Install with: pip install tiktoken")
                print()
                args.precise = False

        measure_startup_tokens(precise=args.precise)
