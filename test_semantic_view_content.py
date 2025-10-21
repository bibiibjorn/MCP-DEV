"""
Test to verify Semantic View displays actual content
"""

from core.model_diff_report_v2 import ModelDiffReportV2

def test_semantic_view_content():
    """Test that Semantic View shows actual column changes"""

    diff_result = {
        'summary': {
            'model1_name': 'Model 60525',
            'model2_name': 'Model 60527',
            'total_changes': 32,
            'changes_by_category': {}
        }
    }

    # Mock TMDL data with column changes
    tmdl1_data = {
        'model': {'name': 'Model1'},
        'tables': {
            'd Assetinstrument': {
                'name': 'd Assetinstrument',
                'columns': [
                    {'name': 'Maturity Date', 'data_type': 'String'},
                    {'name': 'PEQ Max Period', 'data_type': 'Int64', 'is_calculated': False}
                ],
                'measures': []
            },
            'f Valtrans': {
                'name': 'f Valtrans',
                'columns': [
                    {'name': 'Fact Key', 'data_type': 'Int64', 'source_column': 'FactKey'}
                ],
                'measures': []
            }
        },
        'relationships': []
    }

    tmdl2_data = {
        'model': {'name': 'Model2'},
        'tables': {
            'd Assetinstrument': {
                'name': 'd Assetinstrument',
                'columns': [
                    {'name': 'Maturity Date', 'data_type': 'DateTime'},  # Changed type
                    {'name': 'PEQ Max Period', 'data_type': 'Int64', 'is_calculated': True}  # Changed to calculated
                ],
                'measures': []
            },
            'f Valtrans': {
                'name': 'f Valtrans',
                'columns': [
                    {'name': 'Fact Key', 'data_type': 'Int64', 'source_column': 'FactKey'},
                    {'name': 'Trace', 'data_type': 'String', 'source_column': 'Trace'}  # Added
                ],
                'measures': []
            }
        },
        'relationships': []
    }

    report = ModelDiffReportV2(diff_result, tmdl1_data, tmdl2_data)

    # Debug: Check what semantic diff returns
    from core.tmdl_semantic_diff import TmdlSemanticDiff
    analyzer = TmdlSemanticDiff(tmdl1_data, tmdl2_data)
    semantic_diff = analyzer.analyze()

    print("[DEBUG] Semantic diff structure:")
    print(f"  columns: {semantic_diff.get('columns', {})}")
    print(f"  any(columns.values()): {any(semantic_diff.get('columns', {}).values())}")

    # Test the section builder directly
    print("\n[DEBUG] Testing _build_semantic_section directly:")
    section_html = report._build_semantic_section('Columns', semantic_diff['columns'])
    print(f"  Section HTML length: {len(section_html)}")
    if section_html:
        print(f"  Section preview: {section_html[:200]}")
    else:
        print("  ERROR: Section is empty!")

    tmdl_changes_html = report._build_tmdl_changes_view()

    print("\n[TEST] Checking Semantic View content...")

    # Check for semantic view container
    assert 'semantic-diff-container' in tmdl_changes_html, "Semantic container should exist"
    print("[PASS] Semantic container exists")

    # Check for Columns section
    assert 'Columns' in tmdl_changes_html, "Columns section should exist"
    print("[PASS] Columns section header found")

    # Check for modified column (Maturity Date)
    assert 'Maturity Date' in tmdl_changes_html, "Modified column should be shown"
    print("[PASS] 'Maturity Date' is displayed")

    # Check for data type change
    assert 'String' in tmdl_changes_html, "Old data type should be shown"
    assert 'DateTime' in tmdl_changes_html, "New data type should be shown"
    print("[PASS] Data type change is displayed")

    # Check for added column (Trace)
    assert 'Trace' in tmdl_changes_html, "Added column should be shown"
    print("[PASS] 'Trace' added column is displayed")

    # Check for change badges
    assert 'badge mini added' in tmdl_changes_html or 'badge mini modified' in tmdl_changes_html, \
        "Change badges should be present"
    print("[PASS] Change badges are present")

    # Check for table prefixes
    assert 'd Assetinstrument' in tmdl_changes_html or 'f Valtrans' in tmdl_changes_html, \
        "Table names should be shown"
    print("[PASS] Table names are displayed")

    # Check for old/new styling
    assert "class='old'" in tmdl_changes_html or 'class="old"' in tmdl_changes_html, \
        "Old value styling should be present"
    assert "class='new'" in tmdl_changes_html or 'class="new"' in tmdl_changes_html, \
        "New value styling should be present"
    print("[PASS] Old/new value styling is present")

    print("\n[DEBUG] Sample of Semantic View HTML:")
    # Extract a snippet for debugging
    import re
    semantic_match = re.search(r'<div id="semantic-view".*?</div>\s*<div id="raw-view"',
                               tmdl_changes_html, re.DOTALL)
    if semantic_match:
        snippet = semantic_match.group(0)[:500].replace('\n', ' ')
        print(snippet[:300])

    return True

if __name__ == '__main__':
    try:
        test_semantic_view_content()
        print("\n" + "=" * 50)
        print("[SUCCESS] Semantic View content is working!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
