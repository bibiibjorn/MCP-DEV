"""
Test to verify modified column metadata is properly displayed
"""

from core.model_diff_report_v2 import ModelDiffReportV2

def test_modified_column_metadata():
    """Test that modified columns show their change details"""

    # Mock diff data with modified columns
    diff_result = {
        'summary': {
            'model1_name': 'Test Model 1',
            'model2_name': 'Test Model 2',
            'total_changes': 1,
            'changes_by_category': {}
        },
        'tables': {
            'added': [],
            'removed': [],
            'modified': [
                {
                    'name': 'd Assetinstrument',
                    'changes': {
                        'columns': {
                            'added': [],
                            'removed': [],
                            'modified': [
                                {
                                    'name': 'Maturity Date',
                                    'changes': {
                                        'data_type': {
                                            'from': 'String',
                                            'to': 'DateTime'
                                        },
                                        'format_string': {
                                            'from': '',
                                            'to': 'yyyy-MM-dd'
                                        }
                                    }
                                },
                                {
                                    'name': 'PEQ Max Period',
                                    'changes': {
                                        'is_calculated': {
                                            'from': False,
                                            'to': True
                                        },
                                        'expression': {
                                            'from': '',
                                            'to': 'CALCULATE(MAX([Period]))'
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }
    }

    report = ModelDiffReportV2(diff_result, None, None)
    html = report._build_tables_section()

    # Verify modified columns are shown
    assert 'd Assetinstrument' in html, "Modified table should be shown"
    assert 'Maturity Date' in html, "Modified column name should be shown"
    assert 'PEQ Max Period' in html, "Second modified column should be shown"

    # Verify change details are shown
    assert 'String' in html and 'DateTime' in html, "Data type change should be shown"
    assert 'Format String' in html or 'format_string' in html.lower(), "Format string change should be mentioned"
    assert 'Expression changed' in html, "Expression change should be mentioned"
    assert 'Physical' in html or 'Calculated' in html, "Is calculated change should be shown"

    # Verify styling classes are present
    assert 'class="old"' in html or "class='old'" in html, "Old value styling should be present"
    assert 'class="new"' in html or "class='new'" in html, "New value styling should be present"

    print("[PASS] Modified column metadata test passed!")
    print(f"\nSample HTML output for 'Maturity Date':")
    # Extract a snippet
    import re
    match = re.search(r'Maturity Date.*?</div>', html, re.DOTALL)
    if match:
        snippet = match.group(0)[:300]
        # Replace unicode arrow for Windows console
        snippet = snippet.replace('→', '->')
        print(snippet)

    return True

if __name__ == '__main__':
    try:
        test_modified_column_metadata()
        print("\n" + "=" * 50)
        print("[SUCCESS] Column metadata display is working!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
