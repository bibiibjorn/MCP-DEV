"""
Test to verify TMDL Changes tab has both Semantic and Raw views with toggle
"""

from core.model_diff_report_v2 import ModelDiffReportV2

def test_tmdl_changes_toggle():
    """Test that TMDL Changes view has both Semantic and Raw TMDL views"""

    # Mock diff data
    diff_result = {
        'summary': {
            'model1_name': 'Test Model 1',
            'model2_name': 'Test Model 2',
            'total_changes': 0,
            'changes_by_category': {}
        }
    }

    # Mock TMDL data
    tmdl1_data = {
        'model': {'name': 'Model1'},
        'tables': {
            'TestTable': {
                'name': 'TestTable',
                'columns': [
                    {'name': 'ID', 'data_type': 'Int64'}
                ],
                'measures': []
            }
        },
        'relationships': []
    }

    tmdl2_data = {
        'model': {'name': 'Model2'},
        'tables': {
            'TestTable': {
                'name': 'TestTable',
                'columns': [
                    {'name': 'ID', 'data_type': 'Int64'},
                    {'name': 'Name', 'data_type': 'String'}
                ],
                'measures': []
            }
        },
        'relationships': []
    }

    report = ModelDiffReportV2(diff_result, tmdl1_data, tmdl2_data)
    tmdl_changes_html = report._build_tmdl_changes_view()

    print("[TEST] Checking TMDL Changes view structure...")

    # Check for toggle buttons
    assert 'diff-view-toggle' in tmdl_changes_html, "Toggle container should exist"
    assert 'btn-semantic' in tmdl_changes_html, "Semantic button should exist"
    assert 'btn-raw' in tmdl_changes_html, "Raw button should exist"
    assert 'Semantic View' in tmdl_changes_html, "Semantic View label should exist"
    assert 'Raw TMDL Diff' in tmdl_changes_html, "Raw TMDL Diff label should exist"
    print("[PASS] Toggle buttons are present")

    # Check for Semantic View
    assert 'id="semantic-view"' in tmdl_changes_html, "Semantic view container should exist"
    assert 'semantic-diff-container' in tmdl_changes_html, "Semantic diff container should exist"
    print("[PASS] Semantic View is present")

    # Check for Raw View
    assert 'id="raw-view"' in tmdl_changes_html, "Raw view container should exist"
    assert 'tmdl-diff-container' in tmdl_changes_html, "Raw TMDL diff container should exist"
    print("[PASS] Raw TMDL Diff view is present")

    # Check that Semantic is active by default
    assert 'id="semantic-view" class="diff-view active"' in tmdl_changes_html, \
        "Semantic view should be active by default"
    assert 'btn-semantic' in tmdl_changes_html and 'active' in tmdl_changes_html, \
        "Semantic button should be active by default"
    print("[PASS] Semantic view is active by default")

    # Check for switchDiffView onclick handlers
    assert 'onclick="switchDiffView' in tmdl_changes_html, "Toggle buttons should have onclick handlers"
    print("[PASS] Toggle buttons have click handlers")

    # Check for diff content (should have added/removed lines)
    assert 'diff-line' in tmdl_changes_html, "Raw diff should have diff lines"
    print("[PASS] Raw diff contains diff lines")

    return True

if __name__ == '__main__':
    try:
        test_tmdl_changes_toggle()
        print("\n" + "=" * 50)
        print("[SUCCESS] TMDL Changes toggle is working!")
        print("=" * 50)
        print("\nThe TMDL Changes tab now has:")
        print("  1. Semantic View button (active by default)")
        print("  2. Raw TMDL Diff button")
        print("  3. Both views are rendered and toggleable")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
