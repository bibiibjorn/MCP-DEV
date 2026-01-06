# Power BI MCP Server Enhancement Opportunities
## Comprehensive Research & Analysis for PBIP Format Integration

**Research Date:** January 2026
**Current Version:** v6.6

---

## Table of Contents

1. [Current Capabilities Summary](#1-current-capabilities-summary)
2. [PBIP Format Deep Dive](#2-pbip-format-deep-dive)
3. [Report-Level Analysis Opportunities](#3-report-level-analysis-opportunities)
4. [Semantic Model Analysis Opportunities](#4-semantic-model-analysis-opportunities)
5. [Filter & Slicer Analysis](#5-filter--slicer-analysis)
6. [Governance & Compliance Tools](#6-governance--compliance-tools)
7. [Documentation Automation](#7-documentation-automation)
8. [AI/Copilot Integration](#8-aicopilot-integration)
9. [Performance & Optimization Tools](#9-performance--optimization-tools)
10. [Migration & Testing Automation](#10-migration--testing-automation)
11. [Visual Consistency & Branding](#11-visual-consistency--branding)
12. [Data Lineage & Impact Analysis](#12-data-lineage--impact-analysis)
13. [Implementation Priority Matrix](#13-implementation-priority-matrix)
14. [Quick Win Opportunities](#14-quick-win-opportunities)

---

## 1. Current Capabilities Summary

### What You Already Have (31+ Tools)

Your MCP server already provides comprehensive coverage:

| Category | Existing Tools |
|----------|---------------|
| **Connection** | detect_powerbi_desktop, connect_to_powerbi |
| **Schema CRUD** | column/measure/relationship/role operations, TMDL ops, batch ops |
| **DAX Intelligence** | run_dax, dax_intelligence, dependency analysis, impact analysis |
| **PBIP Analysis** | analyze_pbip_repository, pbip_dependency_analysis |
| **Report Analysis** | report_info, slicer_operations |
| **Aggregation** | Full aggregation detection, hit rate, recommendations |
| **Documentation** | Word generation, HTML dashboards |
| **Comparison** | compare_pbi_models |
| **Hybrid** | export_hybrid_analysis, analyze_hybrid_model |

### Existing PBIP Analyzers

1. **TmdlModelAnalyzer** - TMDL parsing
2. **PbirReportAnalyzer** - Report structure extraction
3. **PbipDependencyEngine** - Dependency graph analysis
4. **EnhancedPbipAnalyzer** - DAX quality, data types, relationships
5. **PbipHtmlGenerator** - Interactive HTML reports

---

## 2. PBIP Format Deep Dive

### PBIP Structure Reference

```
{Project}.pbip
├── {Project}.SemanticModel/
│   ├── definition/
│   │   ├── database.tmdl          # Data sources, partitions
│   │   ├── model.tmdl             # Model settings
│   │   ├── expressions.tmdl       # Shared expressions
│   │   ├── relationships.tmdl     # All relationships
│   │   ├── tables/                # One TMDL per table
│   │   ├── roles/                 # RLS/OLS definitions
│   │   ├── cultures/              # Translations
│   │   └── perspectives/          # Perspectives
│   └── item.metadata.json
│
└── {Project}.Report/
    └── definition/
        ├── report.json            # Report-level config & filters
        ├── pages/
        │   └── {PageId}/
        │       ├── page.json      # Page config & filters
        │       └── visuals/
        │           └── {VisualId}/
        │               └── visual.json  # Visual config
        └── bookmarks/             # Bookmark definitions
```

### PBIR (Enhanced Format) - Coming January 2026

Microsoft is transitioning to PBIR as the default format:
- Granular file structure (one file per visual/page/bookmark)
- Public JSON schemas with IntelliSense support
- Better merge conflict resolution
- Script-based automation support
- **Implication:** Your tools should support both PBIR-Legacy (report.json) and PBIR formats

---

## 3. Report-Level Analysis Opportunities

### 3.1 Visual Inventory Analysis

**What it does:** Complete inventory of all visuals across all pages

**Analysis points:**
- Visual type distribution (bar chart, table, card, etc.)
- Custom vs. native visual usage
- Visual density per page
- Duplicate visual detection
- Visual naming consistency

**New Tool Concept:**
```python
analyze_visual_inventory:
  - visual_type_summary: {"bar_chart": 15, "table": 8, ...}
  - custom_visuals: [{"name": "Zebra BI", "count": 4}]
  - density_warnings: [{"page": "Overview", "visual_count": 25}]
  - naming_issues: [{"visual": "Visual 1", "issue": "Generic name"}]
```

### 3.2 Page Layout Quality Analysis

**What it does:** Analyze page layout for UX best practices

**Analysis points:**
- Visual alignment consistency
- Overlapping visuals detection
- White space distribution
- Title and header placement
- Mobile layout compatibility

**New Tool Concept:**
```python
analyze_page_layout:
  - alignment_score: 85
  - overlap_warnings: [{"page": "Sales", "visuals": ["v1", "v2"]}]
  - mobile_issues: [{"page": "Dashboard", "issue": "Too wide"}]
```

### 3.3 Bookmark Analysis

**What it does:** Deep analysis of bookmark configurations

**Analysis points:**
- Bookmark purpose categorization (navigation, filter state, visual state)
- Orphaned bookmarks (not used in navigation)
- Bookmark naming conventions
- Complex bookmark chains
- Performance impact of bookmark states

**New Tool Concept:**
```python
analyze_bookmarks:
  - bookmark_count: 15
  - categories: {"navigation": 5, "filter_state": 10}
  - orphaned: ["Bookmark_Old", "Test Bookmark"]
  - complexity_warnings: [...]
```

### 3.4 Drill-through & Navigation Analysis

**What it does:** Analyze report navigation patterns

**Analysis points:**
- Drill-through page mappings
- Navigation button inventory
- Dead-end pages (no way out)
- Circular navigation paths
- Cross-page filter context

**New Tool Concept:**
```python
analyze_navigation:
  - drillthrough_mappings: {"Detail Page": ["Category", "Product"]}
  - dead_end_pages: ["Archive"]
  - navigation_buttons: 12
  - circular_paths: []
```

### 3.5 Tooltip Analysis

**What it does:** Analyze tooltip configurations

**Analysis points:**
- Report page tooltips vs. default tooltips
- Tooltip page sizing
- Tooltip visual complexity
- Tooltip performance impact

---

## 4. Semantic Model Analysis Opportunities

### 4.1 Enhanced Best Practice Analyzer (BPA)

**Current state:** Basic BPA exists
**Enhancement opportunities:**

| Rule Category | New Rules to Add |
|--------------|------------------|
| **Performance** | High-cardinality text columns, unused indexes |
| **Naming** | Reserved word usage, special character detection |
| **DAX Patterns** | Time intelligence anti-patterns, context transition abuse |
| **Modeling** | Circular dependencies, snowflake schema detection |
| **Security** | RLS gaps, missing role coverage |
| **Documentation** | Missing descriptions, empty folders |

**Implementation:**
```python
enhanced_bpa_analysis:
  - rules_checked: 150
  - violations: [
      {"rule": "High cardinality text", "severity": "warning", "object": "Customer[Address]"},
      {"rule": "Missing description", "severity": "info", "objects": ["Sales[Amount]", ...]},
    ]
  - score: 78/100
  - priority_fixes: [...]
```

### 4.2 Time Intelligence Validation

**What it does:** Validates time intelligence setup

**Analysis points:**
- Date table detection and validation
- Mark as date table verification
- Required columns check (Date, Year, Month, Quarter, Day)
- Fiscal year configuration
- Time intelligence measure patterns

**New Tool Concept:**
```python
validate_time_intelligence:
  - date_tables: [{"table": "Calendar", "is_marked": true, "is_valid": true}]
  - missing_columns: []
  - fiscal_config: {"start_month": 7}
  - ti_measures: 15
  - ti_issues: []
```

### 4.3 Star Schema Validation

**What it does:** Validates star schema design patterns

**Analysis points:**
- Fact table identification (by relationships and measure count)
- Dimension table identification
- Snowflake vs. star detection
- Bridge table identification
- Degenerate dimension detection

**New Tool Concept:**
```python
validate_star_schema:
  - fact_tables: ["Sales", "Inventory"]
  - dimension_tables: ["Customer", "Product", "Date"]
  - schema_type: "star" | "snowflake" | "hybrid"
  - issues: [{"type": "snowflake", "path": "Product -> Category -> Division"}]
```

### 4.4 Calculation Group Analysis

**What it does:** Deep analysis of calculation groups

**Analysis points:**
- Calculation item coverage
- Format string expressions
- Precedence configuration
- Time intelligence calculation groups
- Interaction with regular measures

**New Tool Concept:**
```python
analyze_calculation_groups:
  - groups: [
      {"name": "Time Intelligence", "items": 6, "coverage": "85%"},
      {"name": "Currency", "items": 3, "coverage": "100%"}
    ]
  - precedence_issues: []
  - format_string_usage: true
```

### 4.5 Field Parameter Analysis

**What it does:** Analyze field parameter usage

**Analysis points:**
- Field parameter inventory
- Fields included in each parameter
- Slicer bindings
- Measure vs. column parameters
- Dynamic measure switching patterns

**New Tool Concept:**
```python
analyze_field_parameters:
  - parameters: [
      {"name": "Metric Selection", "type": "measure", "fields": 8},
      {"name": "Dimension Selector", "type": "column", "fields": 4}
    ]
  - slicer_usage: {"Metric Selection": ["Page1", "Page2"]}
```

### 4.6 Partition Strategy Analysis

**What it does:** Analyze data partitioning for refresh optimization

**Analysis points:**
- Partition type (incremental, full, etc.)
- Partition size distribution
- Refresh policy configuration
- Historical vs. current partitions
- Partition pruning opportunities

---

## 5. Filter & Slicer Analysis

### 5.1 Filter Complexity Analysis

**Current state:** Basic filter info exists
**Enhancement opportunities:**

**Analysis points:**
- Filter count per page (warn if > threshold)
- Filter type distribution (basic, advanced, TopN, relative date)
- Cross-page filter inheritance
- Conflicting filters
- Hidden filter detection
- Filter performance impact

**New Tool Concept:**
```python
analyze_filter_complexity:
  - report_level_filters: 3
  - page_filters: {"Page1": 5, "Page2": 8}
  - visual_filters: {"total": 45, "average_per_visual": 1.2}
  - complexity_score: "medium"
  - warnings: [{"page": "Detail", "issue": "15 filters may impact performance"}]
```

### 5.2 Slicer Sync Analysis

**What it does:** Analyze slicer synchronization across pages

**Analysis points:**
- Sync group identification
- Cross-page slicer consistency
- Orphaned slicers (not synced)
- Default value configurations
- Slicer interaction modes

**Enhancement to existing slicer_operations:**
```python
slicer_sync_analysis:
  - sync_groups: [
      {"field": "Date[Year]", "pages": ["Page1", "Page2", "Page3"]},
      {"field": "Product[Category]", "pages": ["Page1", "Page2"]}
    ]
  - orphaned_slicers: [{"page": "Page4", "field": "Date[Year]"}]
  - interaction_matrix: {...}
```

### 5.3 Filter Impact Simulation

**What it does:** Simulate how filters affect data reduction

**Analysis points:**
- Estimated row reduction per filter
- Filter selectivity analysis
- Cascading filter effects
- Filter order optimization

---

## 6. Governance & Compliance Tools

### 6.1 Governance Scoring Dashboard

**What it does:** Comprehensive governance health score

**Scoring dimensions:**
- Documentation completeness (descriptions, folders)
- Naming convention compliance
- Security coverage (RLS defined, tested)
- Best practice adherence
- Performance metrics

**New Tool Concept:**
```python
governance_scorecard:
  - overall_score: 72/100
  - dimensions:
      - documentation: 65
      - naming: 85
      - security: 70
      - best_practices: 78
      - performance: 62
  - top_issues: [...]
  - improvement_roadmap: [...]
```

### 6.2 RLS/OLS Validation

**What it does:** Validate and test Row-Level and Object-Level Security

**Analysis points:**
- Role coverage (all tables protected?)
- Filter expression validation
- Role complexity analysis
- Test case generation
- Cross-role conflict detection

**New Tool Concept:**
```python
validate_security:
  - roles: ["Sales Manager", "Regional Director", "Executive"]
  - table_coverage: {"Sales": ["all roles"], "Finance": ["Executive only"]}
  - expression_issues: []
  - test_cases: [
      {"role": "Sales Manager", "expected_rows": 1000, "tables": ["Sales"]}
    ]
  - gaps: ["Budget table has no RLS"]
```

### 6.3 Sensitivity Label Analysis

**What it does:** Analyze data sensitivity and label compliance

**Analysis points:**
- Columns with PII patterns (name, email, phone, SSN)
- Suggested sensitivity classifications
- Label propagation from sources
- GDPR/compliance considerations

**New Tool Concept:**
```python
sensitivity_analysis:
  - pii_detected: [
      {"column": "Customer[Email]", "type": "email", "suggested_label": "Confidential"},
      {"column": "Employee[SSN]", "type": "ssn", "suggested_label": "Highly Confidential"}
    ]
  - classification_summary: {"public": 45, "internal": 30, "confidential": 10}
```

### 6.4 Audit Trail Generation

**What it does:** Generate audit reports for compliance

**Outputs:**
- Change history from git commits
- Model modification timeline
- Security configuration history
- Measure formula history

---

## 7. Documentation Automation

### 7.1 Enhanced Auto-Documentation

**Current state:** Word generation exists
**Enhancement opportunities:**

**New documentation features:**
- **Data Dictionary Export**: Table/column/measure catalog with descriptions
- **Relationship Diagram**: Auto-generated ERD
- **DAX Formula Reference**: All measures with dependencies
- **Filter Documentation**: Complete filter catalog
- **Visual Catalog**: Visual inventory with screenshots

**New Tool Concept:**
```python
generate_comprehensive_docs:
  - output_formats: ["word", "markdown", "confluence", "notion"]
  - sections:
      - executive_summary
      - data_dictionary
      - measure_reference
      - relationship_diagram
      - visual_catalog
      - filter_documentation
      - security_matrix
```

### 7.2 Data Dictionary Generator

**What it does:** Generate structured data dictionary

**Output format:**
```markdown
## Customer Table
| Column | Data Type | Description | Usage Count |
|--------|-----------|-------------|-------------|
| CustomerID | Int32 | Unique identifier | 15 measures, 3 visuals |
| CustomerName | String | Customer display name | 2 visuals |
```

### 7.3 Change Log Generator

**What it does:** Generate changelog from PBIP git history

**Analysis:**
- Parse git commits for PBIP changes
- Categorize changes (new measures, modified relationships, etc.)
- Generate release notes
- Semantic versioning suggestions

**New Tool Concept:**
```python
generate_changelog:
  - from_commit: "abc123"
  - to_commit: "HEAD"
  - output:
      - version: "2.1.0"
      - changes:
          - added: ["Sales[YTD Revenue]", "Sales[QTD Growth]"]
          - modified: ["Sales[Total Revenue]"]
          - removed: []
      - breaking_changes: []
```

---

## 8. AI/Copilot Integration

### 8.1 Copilot-Ready Analysis

**What it does:** Analyze model readiness for Copilot integration

**Analysis points:**
- Description completeness (Copilot needs descriptions)
- Naming clarity (unambiguous names)
- Synonym suggestions
- Question-answer examples
- Linguistic schema optimization

**New Tool Concept:**
```python
copilot_readiness_analysis:
  - readiness_score: 65/100
  - missing_descriptions: 45
  - ambiguous_names: ["Amount", "Value", "ID"]
  - suggested_synonyms: {
      "Revenue": ["Sales", "Income", "Earnings"],
      "Customer": ["Client", "Account"]
    }
  - sample_questions: [
      "What is total revenue by region?",
      "Show me top 10 customers by sales"
    ]
```

### 8.2 Natural Language Query Generation

**What it does:** Generate natural language query examples

**Features:**
- Auto-generate Q&A pairs from model structure
- Linguistic schema generation
- Question templates based on measure types
- Business glossary extraction

### 8.3 AI-Assisted Optimization Suggestions

**What it does:** Use AI to suggest model improvements

**Features:**
- Pattern recognition in DAX formulas
- Similar measure consolidation suggestions
- Naming standardization recommendations
- Documentation generation from DAX patterns

---

## 9. Performance & Optimization Tools

### 9.1 VertiPaq Simulation

**What it does:** Estimate VertiPaq compression without data

**Analysis points:**
- Estimated column cardinality (from naming patterns, data types)
- Dictionary size predictions
- Memory footprint estimates
- Compression recommendations

**New Tool Concept:**
```python
vertipaq_estimation:
  - estimated_model_size: "150 MB"
  - high_cardinality_warnings: [
      {"column": "Transaction[ID]", "estimated_unique": "1M+"}
    ]
  - optimization_suggestions: [
      {"action": "Remove unused column", "column": "Customer[Notes]"}
    ]
```

### 9.2 Query Pattern Analysis

**What it does:** Analyze DAX query patterns for optimization

**Analysis points:**
- Common query patterns across measures
- CALCULATE nesting depth
- Iterator function usage
- Variable usage opportunities
- Query folding potential

### 9.3 Visual Query Estimation

**What it does:** Estimate query cost for each visual

**Analysis points:**
- Measures used per visual
- Filter context complexity
- Estimated data volume
- Cross-filter impact

**New Tool Concept:**
```python
visual_query_cost:
  - visuals: [
      {"name": "Sales Matrix", "cost": "high", "reasons": ["5 measures", "3 row groups"]},
      {"name": "Revenue Card", "cost": "low", "reasons": ["1 measure", "no grouping"]}
    ]
  - page_costs: {"Dashboard": "medium", "Detail": "high"}
```

### 9.4 Aggregation Opportunity Detection

**Current state:** Full aggregation analysis exists
**Enhancement opportunities:**
- Auto-generate aggregation table TMDL
- Precedence optimization
- Aggregation coverage reporting
- What-if analysis for new aggregations

---

## 10. Migration & Testing Automation

### 10.1 Report Regression Testing

**What it does:** Validate report consistency across versions

**Features:**
- Visual count comparison
- Measure result comparison
- Filter configuration comparison
- Layout change detection

**New Tool Concept:**
```python
regression_test:
  - baseline_path: "v1.0/"
  - current_path: "v2.0/"
  - results:
      - visual_changes: [{"page": "Sales", "added": 2, "removed": 0}]
      - measure_changes: [{"measure": "Total Revenue", "expression_changed": true}]
      - filter_changes: []
  - pass: true
```

### 10.2 Migration Validation

**What it does:** Validate PBIP migration from other formats

**Features:**
- PBIX to PBIP comparison
- Missing object detection
- Expression validation
- Relationship verification

### 10.3 CI/CD Integration

**What it does:** Enable CI/CD pipeline integration

**Features:**
- CLI interface for automation
- Exit codes for pass/fail
- JSON output for pipeline parsing
- GitHub Actions / Azure DevOps integration

**New Tool Concept:**
```python
ci_cd_validation:
  - checks: ["bpa", "governance", "security", "performance"]
  - thresholds: {"bpa_score": 70, "governance_score": 60}
  - output_format: "json" | "junit" | "markdown"
  - exit_code: 0 | 1
```

### 10.4 Test Case Generation

**What it does:** Auto-generate test cases from model structure

**Features:**
- Measure test cases with expected results
- RLS test cases per role
- Filter test scenarios
- Edge case identification

---

## 11. Visual Consistency & Branding

### 11.1 Theme Compliance Checker

**What it does:** Validate visual consistency against theme

**Analysis points:**
- Color usage against approved palette
- Font consistency
- Visual formatting standards
- Custom visual compliance

**New Tool Concept:**
```python
theme_compliance:
  - theme_file: "corporate_theme.json"
  - violations: [
      {"visual": "Chart1", "issue": "Non-standard color #FF0000"},
      {"visual": "Title", "issue": "Wrong font family"}
    ]
  - compliance_score: 85
```

### 11.2 Branding Validation

**What it does:** Validate corporate branding guidelines

**Analysis points:**
- Logo placement
- Header/footer consistency
- Color palette adherence
- Typography standards

### 11.3 Accessibility Checker

**What it does:** Validate accessibility standards

**Analysis points:**
- Color contrast ratios
- Alt text for images
- Tab order for navigation
- Screen reader compatibility

**New Tool Concept:**
```python
accessibility_check:
  - wcag_level: "AA"
  - violations: [
      {"visual": "Chart1", "issue": "Low contrast ratio 2.5:1"},
      {"visual": "Image1", "issue": "Missing alt text"}
    ]
  - score: 72
```

---

## 12. Data Lineage & Impact Analysis

### 12.1 Enhanced Lineage Visualization

**Current state:** Dependency analysis exists
**Enhancement opportunities:**

**New features:**
- Source-to-visual lineage (data source -> column -> measure -> visual)
- Interactive lineage explorer
- Filter impact on lineage
- Cross-report lineage (shared datasets)

**New Tool Concept:**
```python
full_lineage_analysis:
  - source_lineage: {
      "SQL Server.Sales": ["Sales[Amount]", "Sales[Quantity]"]
    }
  - measure_lineage: {
      "Total Revenue": {
        "columns": ["Sales[Amount]"],
        "measures": [],
        "visuals": ["Page1.Chart1", "Page2.Card1"]
      }
    }
  - visual_lineage: [...]
```

### 12.2 Impact Analysis Enhancement

**Current state:** Measure impact exists
**Enhancement opportunities:**

**New features:**
- Column rename impact simulation
- Table removal impact
- Relationship change impact
- Cross-report impact (if using shared datasets)

**New Tool Concept:**
```python
change_impact_simulation:
  - proposed_change: {"type": "rename_column", "from": "Amount", "to": "Revenue"}
  - impact:
      - measures_affected: 15
      - visuals_affected: 8
      - filters_affected: 3
      - estimated_effort: "medium"
  - auto_fix_available: true
```

### 12.3 Unused Object Detection

**Current state:** Unused column detection exists
**Enhancement opportunities:**

**New features:**
- Unused measure detection
- Unused table detection
- Unused relationship detection
- Cleanup script generation

---

## 13. Implementation Priority Matrix

### High Priority (High Impact, Lower Effort)

| Opportunity | Effort | Impact | Notes |
|-------------|--------|--------|-------|
| Enhanced BPA Rules | Medium | High | Extend existing BPA |
| Governance Scorecard | Low | High | Aggregate existing analyses |
| Copilot Readiness | Low | High | Description analysis |
| Theme Compliance | Low | Medium | Parse theme JSON |
| Visual Inventory | Low | Medium | Extend report analyzer |

### Medium Priority (High Impact, Higher Effort)

| Opportunity | Effort | Impact | Notes |
|-------------|--------|--------|-------|
| CI/CD Integration | Medium | High | Add CLI interface |
| Data Dictionary Export | Medium | High | New export format |
| RLS Validation | Medium | High | Test case generation |
| Regression Testing | High | High | Comparison framework |
| Full Lineage | High | High | Source integration |

### Lower Priority (Future Consideration)

| Opportunity | Effort | Impact | Notes |
|-------------|--------|--------|-------|
| Accessibility Checker | High | Medium | WCAG implementation |
| AI Optimization | High | Medium | ML integration |
| Visual Query Cost | Medium | Medium | Estimation algorithms |
| Change Log Generator | Medium | Low | Git integration |

---

## 14. Quick Win Opportunities

### Immediate Enhancements (< 1 day each)

1. **Visual Count Per Page Warning**
   - Add threshold check to existing report analyzer
   - Warn if page has > 20 visuals

2. **Description Coverage Report**
   - Count objects with/without descriptions
   - Calculate coverage percentage

3. **Naming Convention Summary**
   - Report on naming patterns found
   - Flag inconsistencies

4. **Filter Complexity Score**
   - Count filters at each level
   - Generate complexity rating

5. **Duplicate Measure Detection**
   - Hash DAX expressions
   - Find exact/similar duplicates

### Week 1 Enhancements

1. **Governance Score Dashboard**
   - Aggregate existing analysis outputs
   - Single health score

2. **Enhanced BPA Rules (20 new rules)**
   - Time intelligence patterns
   - Naming conventions
   - Security coverage

3. **Bookmark Analysis**
   - Parse bookmark JSON
   - Orphan detection

4. **Theme Compliance Check**
   - Parse theme files
   - Compare visual colors

### Month 1 Enhancements

1. **CI/CD Integration**
   - CLI wrapper
   - JSON output mode
   - Exit codes

2. **Data Dictionary Export**
   - Markdown format
   - CSV format

3. **RLS Test Case Generation**
   - Generate test scenarios
   - Expected result templates

---

## Sources & References

### Microsoft Documentation
- [Power BI Desktop projects (PBIP)](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [PBIR Enhanced Report Format](https://learn.microsoft.com/en-us/power-bi/developer/embedded/projects-enhanced-report-format)
- [Power BI Desktop project report folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Data Lineage in Power BI](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-data-lineage)
- [Performance Analyzer](https://learn.microsoft.com/en-us/power-bi/create-reports/performance-analyzer)
- [Content Validation Planning](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-implementation-planning-content-lifecycle-management-validate)
- [Copilot for Power BI](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction)
- [Optimize Semantic Model for Copilot](https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-evaluate-data)

### Industry Resources
- [DAX Optimizer](https://www.daxoptimizer.com/)
- [DAX Studio](https://daxstudio.org/)
- [SQLBI Tools in Power BI](https://www.sqlbi.com/articles/tools-in-power-bi/)
- [Semantic Link Labs](https://data-goblins.com/power-bi/semantic-link-labs)
- [BI Validator](https://www.datagaps.com/automate-power-bi-testing/)

### Format Transition
- [PBIR Default Format Transition](https://powerbi.microsoft.com/en-us/blog/pbir-will-become-the-default-power-bi-report-format-get-ready-for-the-transition/)
- [Why Developers Should Care About PBIP](https://endjin.com/blog/2024/08/why-power-bi-developers-should-care-about-power-bi-projects)
- [Why Developers Should Care About PBIR](https://endjin.com/blog/2024/09/why-power-bi-developers-should-care-about-the-power-bi-enhanced-report-format)

### Power BI Updates
- [Power BI November 2025 Update](https://powerbi.microsoft.com/en-us/blog/power-bi-november-2025-feature-summary/)
- [Power BI Modeling MCP Server](https://powerbi.microsoft.com/en-us/blog/power-bi-semantic-models-as-accelerators-for-ai-enabled-consumption/)

---

*Generated by MCP-PowerBi-Finvision Research Analysis*
