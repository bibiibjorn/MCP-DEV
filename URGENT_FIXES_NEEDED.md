# Urgent Fixes Needed for PBIP Analyzer

## Issues Identified

### 1. ✅ M/Power Query Expressions Show "0" (FIXED)
**Issue:** Expression count shows 0 even when expressions exist
**Cause:** TMDL parser not extracting multiline M expressions properly
**Fix Applied:** Enhanced `_parse_expressions()` to look for expression text in any non-meta field

### 2. ✅ Model Tab - Remove "len" Display (FIXED)
**Issue:** Tables heading shows "Tables ({{len(tables)}})" with literal "len" text
**Fix Applied:** Changed to separate heading and count display

### 3. ⚠️ Usage Tab - Show Column Usage Not Table Usage (IN PROGRESS)
**Issue:** Usage tab shows table-level usage, but columns are what's actually used
**Required Changes:**
- Modify dependency engine to track column usage in visuals
- Update Usage tab to show:
  - Columns used in measures
  - Columns used in visuals
  - Columns used in relationships
  - Unused columns with recommendations

### 4. ⚠️ DAX Expression Display Issues (NEEDS INVESTIGATION)
**Issue:** Some DAX measures not displaying properly
**Possible Causes:**
- Special characters not being escaped
- Multiline expressions truncated
- Expression field mapping issues in TMDL parser

### 5. ⚠️ Report Tab - Group Visuals by Name (NOT STARTED)
**Issue:** Multiple visuals with same type shown separately
**Required:**
- Group visuals of same type together
- Show count per visual type
- Collapsible groups

### 6. ⚠️ Report Tab - Add Page Selector Sidebar (NOT STARTED)
**Issue:** Too much scrolling with many pages
**Required:**
- Left sidebar with page list
- Click to jump to page section
- Active page highlighting

### 7. 🔴 Dependency Analysis - Measure Used By Not Working (CRITICAL)
**Issue:** "Used By Measures" shows 0 even when measures are clearly used
**Investigation Needed:**
- Check if DAX parser is correctly extracting measure references
- Verify measure key format consistency (with/without brackets)
- Test with known dependencies

### 8. 🔴 Dependency Analysis - Visual Usage Not Showing (CRITICAL)
**Issue:** "Used In Visuals" shows 0 even when measures are in visuals
**Investigation Needed:**
- Verify visual field extraction from PBIR
- Check measure name matching between model and report
- Validate visual_dependencies data structure

## Priority Order

1. **Critical (Fix First)**
   - Issue #7: Dependency analysis - measure used by
   - Issue #8: Dependency analysis - visual usage

2. **High (Fix Next)**
   - Issue #4: DAX expression display
   - Issue #3: Column-level usage tab

3. **Medium (Nice to Have)**
   - Issue #6: Report page sidebar
   - Issue #5: Group visuals by type

## Debugging Strategy

### For Dependency Issues (#7, #8)

```python
# Add debug logging to dependency engine
print("=== DEBUGGING DEPENDENCIES ===")
print(f"Total measures: {len(measure_to_measure)}")
print(f"Sample measure keys: {list(measure_to_measure.keys())[:5]}")

# Check if parser is extracting references
for measure_key, deps in list(measure_to_measure.items())[:3]:
    print(f"\n{measure_key} depends on:")
    for dep in deps:
        print(f"  - {dep}")

# Check reverse lookup
test_measure = list(measure_to_measure.keys())[0]
used_by = [k for k, v in measure_to_measure.items() if test_measure in v]
print(f"\n{test_measure} is used by:")
for user in used_by:
    print(f"  - {user}")

# Check visual usage
print(f"\nVisual dependencies: {len(visual_dependencies)}")
for visual_key, visual_deps in list(visual_dependencies.items())[:3]:
    print(f"{visual_key}:")
    print(f"  Measures: {visual_deps.get('measures', [])}")
```

### For DAX Display Issues (#4)

```python
# Check if expressions are being extracted
for table in model_data.get("tables", [])[:3]:
    print(f"\nTable: {table.get('name')}")
    for measure in table.get("measures", [])[:2]:
        print(f"  Measure: {measure.get('name')}")
        expr = measure.get('expression', '')
        print(f"  Expression length: {len(expr)}")
        print(f"  First 100 chars: {expr[:100]}")
```

## Test Cases Needed

### Test Case 1: Known Dependency
```
Measure: "Amount in selected currency"
Expected to depend on: Reporting Currency column
Expected to be used by: Other calculation measures

Verify:
- dependsOn.length > 0
- usedBy.length > 0
- Column reference is found
```

### Test Case 2: Visual Usage
```
Measure: "m00. Amount in selected currency"
Expected: Used in at least one visual

Verify:
- visualUsage.length > 0
- Page name is correct
- Visual type is correct
```

### Test Case 3: M Expressions
```
Check: expressions.tmdl file
Expected: List of Power Query expressions with full M code

Verify:
- expressions array length > 0
- Each expression has name and expression text
- Expression text is complete (not truncated)
```

## Recommended Next Steps

1. **Run test with debug logging** to see actual data structures
2. **Verify measure key formats** are consistent
3. **Check DAX parser** is correctly identifying measure references
4. **Validate PBIR parsing** extracts visual fields correctly
5. **Fix critical dependency issues** before UI enhancements

## Quick Win: Add Debug Tab

Consider adding a "Debug" tab to the HTML output that shows:
- Raw dependency data structure
- Measure key samples
- Visual dependencies sample
- Expression extraction results

This would help diagnose issues without modifying code.

