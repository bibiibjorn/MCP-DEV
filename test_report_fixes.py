"""
Quick test to verify report generation fixes
"""

# Test 1: Verify escapeHtml logic for empty lines
def test_escape_logic():
    """Simulate the JavaScript escapeHtml behavior"""
    def escape_html(text):
        # Python equivalent of JavaScript's textContent approach
        import html
        return html.escape(str(text)) if text else ""

    # Test empty line
    content = ""
    escaped_content = escape_html(content) or "&nbsp;"
    print(f"Test 1 - Empty line: '{escaped_content}' (should be '&nbsp;')")
    assert escaped_content == "&nbsp;", "Empty line should become &nbsp;"

    # Test non-empty line
    content = "model Model"
    escaped_content = escape_html(content) or "&nbsp;"
    print(f"Test 2 - Non-empty line: '{escaped_content}' (should be 'model Model')")
    assert escaped_content == "model Model", "Non-empty line should be unchanged"

    # Test line with special chars
    content = "table 'Measure' extends"
    escaped_content = escape_html(content) or "&nbsp;"
    print(f"Test 3 - Special chars: '{escaped_content}' (should escape quotes)")
    assert "&#x27;" in escaped_content, "Should escape single quotes"

    print("\n[PASS] All escape logic tests passed!")

# Test 2: Verify measure card structure
def test_measure_card_structure():
    """Verify that measure cards have proper clickable structure"""
    from core.model_diff_report_v2 import ModelDiffReportV2

    # Mock data
    diff_result = {
        'summary': {
            'model1_name': 'Test Model 1',
            'model2_name': 'Test Model 2',
            'total_changes': 1,
            'changes_by_category': {}
        },
        'measures': {
            'added': [
                {'name': 'Test Measure', 'table': 'm Measure', 'expression': 'SUM(Table[Column])'}
            ],
            'removed': [],
            'modified': []
        }
    }

    report = ModelDiffReportV2(diff_result, None, None)
    html = report._build_measures_section()

    # Check that added measure has clickable header
    assert 'change-header clickable' in html, "Measure should have clickable header"
    assert 'expand-icon' in html, "Measure should have expand icon"
    assert 'change-body' in html, "Measure should have collapsible body"

    print("[PASS] Measure card structure test passed!")

# Test 3: Verify TMDL Changes tab is marked as loaded
def test_tmdl_changes_loaded():
    """Verify that TMDL Changes tab has data-loaded='true'"""
    from core.model_diff_report_v2 import ModelDiffReportV2

    diff_result = {
        'summary': {
            'model1_name': 'Test Model 1',
            'model2_name': 'Test Model 2',
            'total_changes': 0,
            'changes_by_category': {}
        }
    }

    report = ModelDiffReportV2(diff_result, None, None)
    html = report._build_html()

    # Check that TMDL Changes tab is marked as loaded
    assert 'id="tab-tmdl-changes" class="tab-pane" data-loaded="true"' in html, \
        "TMDL Changes tab should be marked as loaded"

    print("[PASS] TMDL Changes tab loaded flag test passed!")

if __name__ == '__main__':
    print("Running report fixes tests...\n")

    try:
        test_escape_logic()
        print()
        test_measure_card_structure()
        print()
        test_tmdl_changes_loaded()
        print()
        print("=" * 50)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 50)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
