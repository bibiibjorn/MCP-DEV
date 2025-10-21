"""
Quick verification script for optimization implementation.
Tests all new components without requiring Power BI connection.
"""

import json
from pathlib import Path

def test_imports():
    """Test that all new modules import correctly."""
    print("Testing imports...")
    try:
        from core.report_assets import get_css_styles, get_javascript, minify_css, minify_js
        from core.model_diff_report_v2 import ModelDiffReportV2
        from core.model_comparison_orchestrator import ModelComparisonOrchestrator, compare_pbi_models
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_asset_generation():
    """Test CSS and JS generation."""
    print("\nTesting asset generation...")
    try:
        from core.report_assets import get_css_styles, get_javascript

        css = get_css_styles()
        js = get_javascript()

        print(f"  CSS size: {len(css):,} bytes")
        print(f"  JS size: {len(js):,} bytes")

        # Verify key classes exist
        assert 'change-card' in css, "Missing change-card class"
        assert 'tmdl-line' in css, "Missing tmdl-line class"
        assert 'dax-box' in css, "Missing dax-box class"

        # Verify key functions exist
        assert 'switchTab' in js, "Missing switchTab function"
        assert 'loadTmdlFullView' in js, "Missing loadTmdlFullView function"
        assert 'addEventListener' in js, "Missing addEventListener (event delegation)"
        assert 'closest' in js, "Missing closest method (event delegation)"

        print("[OK] Asset generation working")
        return True
    except Exception as e:
        print(f"[FAIL] Asset generation failed: {e}")
        return False

def test_minification():
    """Test CSS/JS minification."""
    print("\nTesting minification...")
    try:
        from core.report_assets import minify_css, minify_js

        # Test CSS minification
        css_input = """
        /* This is a comment */
        .test {
            color: red;
            background: blue;
        }
        """
        css_output = minify_css(css_input)

        assert '/*' not in css_output, "Comments not removed"
        assert len(css_output) < len(css_input), "CSS not minified"
        reduction_pct = int(100*(1-len(css_output)/len(css_input)))
        print(f"  CSS: {len(css_input)} -> {len(css_output)} bytes ({reduction_pct}% reduction)")

        # Test JS minification
        js_input = """
        // This is a comment
        function test() {
            return true;
        }
        """
        js_output = minify_js(js_input)

        assert '//' not in js_output, "Comments not removed"
        assert len(js_output) < len(js_input), "JS not minified"
        reduction_pct = int(100*(1-len(js_output)/len(js_input)))
        print(f"  JS: {len(js_input)} -> {len(js_output)} bytes ({reduction_pct}% reduction)")

        print("[OK] Minification working")
        return True
    except Exception as e:
        print(f"[FAIL] Minification failed: {e}")
        return False

def test_report_generation():
    """Test report generation with mock data."""
    print("\nTesting report generation...")
    try:
        from core.model_diff_report_v2 import ModelDiffReportV2

        # Create minimal mock diff data
        mock_diff = {
            'summary': {
                'model1_name': 'Test Model 1',
                'model2_name': 'Test Model 2',
                'total_changes': 5,
                'changes_by_category': {
                    'tables_added': 1,
                    'tables_removed': 0,
                    'tables_modified': 1,
                    'measures_added': 2,
                    'measures_removed': 1,
                    'measures_modified': 0
                }
            },
            'tables': {
                'added': [{'name': 'NewTable', 'columns_count': 5, 'measures_count': 2}],
                'removed': [],
                'modified': [{
                    'name': 'ExistingTable',
                    'changes': {
                        'columns': {
                            'added': [{'name': 'NewColumn', 'data_type': 'String'}],
                            'removed': [],
                            'modified': []
                        },
                        'measures': {
                            'added': [],
                            'removed': [],
                            'modified': []
                        }
                    }
                }]
            },
            'measures': {
                'added': [
                    {'name': 'Total Sales', 'table': 'Sales', 'expression': 'SUM(Sales[Amount])'}
                ],
                'removed': [
                    {'name': 'Old Metric', 'table': 'Sales', 'expression': 'COUNT(Sales[ID])'}
                ],
                'modified': []
            },
            'relationships': {'added': [], 'removed': [], 'modified': []},
            'roles': {'added': [], 'removed': [], 'modified': []},
            'perspectives': {'added': [], 'removed': [], 'modified': []}
        }

        # Mock TMDL data (minimal)
        mock_tmdl1 = {'model': {'name': 'Test1'}, 'tables': []}
        mock_tmdl2 = {'model': {'name': 'Test2'}, 'tables': []}

        # Create report generator
        generator = ModelDiffReportV2(mock_diff, mock_tmdl1, mock_tmdl2)

        # Generate HTML to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            temp_path = f.name

        output_path = generator.generate_html(temp_path)

        # Verify file was created
        path_obj = Path(output_path)
        assert path_obj.exists(), "HTML file not created"

        # Read and verify content
        html_content = path_obj.read_text(encoding='utf-8')
        file_size = len(html_content)

        # Verify key elements
        assert 'Test Model 1' in html_content, "Model 1 name missing"
        assert 'Test Model 2' in html_content, "Model 2 name missing"
        assert 'NewTable' in html_content, "Added table missing"
        assert 'Total Sales' in html_content, "Added measure missing"
        assert 'window.tmdlData' in html_content, "TMDL data not embedded"
        assert 'loadTmdlFullView' in html_content, "Lazy loading JS missing"
        assert '<style>' in html_content, "CSS missing"
        assert '<script>' in html_content, "JavaScript missing"

        # Verify no inline event handlers
        assert 'onclick="onLineClick' not in html_content, "Inline onclick found (should use delegation)"
        assert 'onmouseenter=' not in html_content, "Inline onmouseenter found"

        print(f"  HTML size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"  File: {output_path}")

        # Cleanup
        path_obj.unlink()

        print("[OK] Report generation working")
        return True
    except Exception as e:
        print(f"[FAIL] Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generic_builder():
    """Test generic change card builder."""
    print("\nTesting generic change card builder...")
    try:
        from core.model_diff_report_v2 import ModelDiffReportV2

        mock_diff = {'summary': {}, 'tables': {}, 'measures': {}, 'relationships': {}, 'roles': {}, 'perspectives': {}}
        generator = ModelDiffReportV2(mock_diff)

        # Test added card
        item = {'name': 'TestItem', 'columns_count': 5}
        html = generator._build_change_card(item, 'added', 'table')
        assert 'TestItem' in html, "Item name missing"
        assert 'badge added' in html, "Badge missing"
        assert '+ ADDED' in html, "Added text missing"

        # Test modified card with details
        html = generator._build_change_card(item, 'modified', 'table', '<p>Details</p>')
        assert 'clickable' in html, "Clickable class missing"
        assert 'expand-icon' in html, "Expand icon missing"
        assert '<p>Details</p>' in html, "Details missing"

        print("[OK] Generic builder working")
        return True
    except Exception as e:
        print(f"[FAIL] Generic builder failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("OPTIMIZATION VERIFICATION")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Asset Generation", test_asset_generation),
        ("Minification", test_minification),
        ("Generic Builder", test_generic_builder),
        ("Report Generation", test_report_generation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"[CRASH] {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED - Optimizations working correctly!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed - Review errors above")
        return 1

if __name__ == "__main__":
    exit(main())
