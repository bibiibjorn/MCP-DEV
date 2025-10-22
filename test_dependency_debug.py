#!/usr/bin/env python3
"""
Debug script to identify dependency analysis issues.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from core.pbip_project_scanner import PbipProjectScanner
from core.pbip_model_analyzer import TmdlModelAnalyzer
from core.pbip_report_analyzer import PbirReportAnalyzer
from core.pbip_dependency_engine import PbipDependencyEngine


def debug_dependencies(repo_path: str):
    """Debug dependency analysis to find issues."""
    print("=" * 80)
    print("DEPENDENCY ANALYSIS DEBUG")
    print("=" * 80)

    # Step 1: Scan repository
    print("\n[1] Scanning repository...")
    scanner = PbipProjectScanner()
    projects = scanner.scan_repository(repo_path, [])

    semantic_models = projects.get("semantic_models", [])
    reports = projects.get("reports", [])

    if not semantic_models:
        print("ERROR: No semantic models found!")
        return

    print(f"Found {len(semantic_models)} model(s) and {len(reports)} report(s)")

    # Step 2: Analyze model
    print("\n[2] Analyzing model...")
    model = semantic_models[0]
    model_folder = model.get("model_folder")

    analyzer = TmdlModelAnalyzer()
    model_data = analyzer.analyze_model(model_folder)

    total_measures = sum(len(t.get("measures", [])) for t in model_data.get("tables", []))
    print(f"Model has {len(model_data.get('tables', []))} tables with {total_measures} measures")

    # Step 3: Analyze report
    report_data = None
    if reports:
        print("\n[3] Analyzing report...")
        report = reports[0]
        report_folder = report.get("report_folder")

        report_analyzer = PbirReportAnalyzer()
        report_data = report_analyzer.analyze_report(report_folder)

        total_visuals = sum(len(p.get("visuals", [])) for p in report_data.get("pages", []))
        print(f"Report has {len(report_data.get('pages', []))} pages with {total_visuals} visuals")

    # Step 4: Dependency analysis
    print("\n[4] Performing dependency analysis...")
    dep_engine = PbipDependencyEngine(model_data, report_data)
    dependencies = dep_engine.analyze_all_dependencies()

    # Debug output
    print("\n" + "=" * 80)
    print("DEPENDENCY ANALYSIS RESULTS")
    print("=" * 80)

    # Measure-to-measure dependencies
    measure_to_measure = dependencies.get("measure_to_measure", {})
    print(f"\n[Measure Dependencies]")
    print(f"Measures with dependencies: {len(measure_to_measure)}")

    if measure_to_measure:
        print("\nSample measure dependencies (first 5):")
        for i, (measure_key, deps) in enumerate(list(measure_to_measure.items())[:5]):
            print(f"\n  {i+1}. {measure_key}")
            print(f"     Depends on {len(deps)} object(s):")
            for dep in deps[:3]:  # Show first 3 dependencies
                print(f"       - {dep}")
            if len(deps) > 3:
                print(f"       ... and {len(deps)-3} more")

    # Reverse lookup test
    print(f"\n[Reverse Lookup Test]")
    measure_to_measure_reverse = dependencies.get("measure_to_measure_reverse", {})
    if measure_to_measure:
        test_measure = list(measure_to_measure.keys())[0]
        # Get the first dependency of the first measure
        if measure_to_measure[test_measure]:
            test_dependency = measure_to_measure[test_measure][0]
            used_by = measure_to_measure_reverse.get(test_dependency, [])
            print(f"Testing reverse lookup for: {test_dependency}")
            print(f"Used by {len(used_by)} measure(s):")
            for user in used_by[:5]:
                print(f"  - {user}")

    # Visual dependencies
    visual_deps = dependencies.get("visual_dependencies", {})
    print(f"\n[Visual Dependencies]")
    print(f"Total visuals with dependencies: {len(visual_deps)}")

    if visual_deps:
        print("\nSample visual dependencies (first 3):")
        for i, (visual_key, deps) in enumerate(list(visual_deps.items())[:3]):
            print(f"\n  {i+1}. {visual_key}")
            print(f"     Visual type: {deps.get('visual_type', 'unknown')}")
            measures = deps.get('measures', [])
            columns = deps.get('columns', [])
            print(f"     Uses {len(measures)} measure(s) and {len(columns)} column(s)")
            if measures:
                print(f"     Measures:")
                for m in measures[:3]:
                    print(f"       - {m}")
            if columns:
                print(f"     Columns:")
                for c in columns[:3]:
                    print(f"       - {c}")

    # Check specific measure usage in visuals
    print(f"\n[Measure Usage in Visuals Test]")
    # Test with Currency since we saw it in the samples
    test_measure = "m Measure[Currency]"
    visuals_using_measure = [
        visual_key for visual_key, deps in visual_deps.items()
        if test_measure in deps.get('measures', [])
    ]
    print(f"Testing: {test_measure}")
    print(f"Used in {len(visuals_using_measure)} visual(s)")
    for visual in visuals_using_measure[:5]:
        print(f"  - {visual}")

    # Unused objects
    unused_measures = dependencies.get("unused_measures", [])
    unused_columns = dependencies.get("unused_columns", [])
    print(f"\n[Unused Objects]")
    print(f"Unused measures: {len(unused_measures)}")
    print(f"Unused columns: {len(unused_columns)}")

    if unused_measures:
        print(f"\nSample unused measures (first 5):")
        for m in unused_measures[:5]:
            print(f"  - {m}")

    # M Expressions
    expressions = model_data.get("expressions", [])
    print(f"\n[M/Power Query Expressions]")
    print(f"Total expressions: {len(expressions)}")

    if expressions:
        print(f"\nSample expressions:")
        for i, expr in enumerate(expressions[:3]):
            name = expr.get('name', 'Unknown')
            expression = expr.get('expression', '')
            print(f"  {i+1}. {name}")
            print(f"     Length: {len(expression)} characters")
            print(f"     Preview: {expression[:100]}...")

    # Export debug data
    debug_file = "exports/dependency_debug.json"
    os.makedirs("exports", exist_ok=True)

    debug_data = {
        "measure_to_measure_sample": dict(list(measure_to_measure.items())[:10]),
        "visual_dependencies_sample": dict(list(visual_deps.items())[:10]),
        "unused_measures_sample": unused_measures[:20],
        "expressions_sample": expressions[:5],
        "summary": dependencies.get("summary", {})
    }

    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(debug_data, f, indent=2)

    print(f"\nDebug data exported to: {debug_file}")

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_dependency_debug.py <path_to_pbip_repo>")
        sys.exit(1)

    repo_path = sys.argv[1]
    if not os.path.exists(repo_path):
        print(f"Error: Path does not exist: {repo_path}")
        sys.exit(1)

    debug_dependencies(repo_path)
