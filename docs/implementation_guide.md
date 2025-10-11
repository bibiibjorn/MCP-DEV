# Visual Component Library - Implementation Guide

## Complete File Structure

```
mcp-powerbi-finvision/
│
├── guardrails/
│   ├── guardrails_v7.2.md                 (EXISTING - your current guardrails)
│   ├── component_library_v1.0.md          (NEW - comprehensive component library)
│   └── integration_workflow.md            (NEW - how components work with guardrails)
│
├── docs/
│   ├── component_catalog.md               (NEW - quick reference guide)
│   ├── usage_examples.md                  (NEW - real-world examples)
│   ├── screenshot_analysis_log.md         (NEW - track analyzed screenshots)
│   └── component_metadata.json            (NEW - structured component data)
│
├── templates/
│   ├── base/
│   │   ├── dashboard_base.html            (NEW - minimal starter)
│   │   ├── dashboard_with_sidebar.html    (NEW - sidebar layout)
│   │   └── dashboard_responsive.html      (NEW - fully responsive)
│   │
│   ├── components/
│   │   ├── kpi_cards.html                 (NEW - all KPI variants)
│   │   ├── data_tables.html               (NEW - all table variants)
│   │   ├── charts.html                    (NEW - all chart types)
│   │   ├── controls.html                  (NEW - all control types)
│   │   ├── layouts.html                   (NEW - layout patterns)
│   │   └── navigation.html                (NEW - navigation components)
│   │
│   └── examples/
│       ├── executive_dashboard.html       (NEW - Pattern 1)
│       ├── financial_risk.html            (NEW - Pattern 2)
│       ├── operational_metrics.html       (NEW - Pattern 3)
│       ├── product_margin.html            (NEW - from screenshot 1)
│       ├── call_center.html               (NEW - from screenshot 8)
│       └── supply_chain.html              (NEW - from screenshot 7)
│
├── validation/
│   ├── component_validator.py             (NEW - validate individual components)
│   ├── screenshot_analyzer.py             (NEW - extract patterns from images)
│   ├── theme_extractor.py                 (NEW - extract colors/typography)
│   └── rules/
│       ├── kpi_card_rules.json            (NEW - validation rules per component)
│       ├── table_rules.json
│       ├── chart_rules.json
│       └── layout_rules.json
│
├── tools/
│   ├── component_generator.py             (NEW - generate components from metadata)
│   ├── html_minifier.py                   (NEW - optimize output)
│   └── accessibility_checker.py           (NEW - WCAG compliance)
│
└── README_COMPONENT_LIBRARY.md            (NEW - master documentation)
```

---

## File Contents & Purpose

### 1. guardrails/component_library_v1.0.md

**Content**: Full component library (already created in artifact above)

**Purpose**:
- Comprehensive reference for all 29 components
- HTML + CSS for each variant
- Usage guidelines
- Validation rules
- Integration with guardrails

**Usage**:
- Claude references this when selecting components
- User can view to understand available options
- Basis for code generation

---

### 2. guardrails/integration_workflow.md

**Content**: (Create this file)

```markdown
# Component Library Integration Workflow

## Claude's Decision Process

1. **Receive User Request**
   - Parse intent
   - Identify dashboard type
   - Extract requirements

2. **Call html:guardrails**
   ```javascript
   const result = await html_guardrails();
   const token = result.guardrail_token;
   ```

3. **Analyze Requirements Against Library**
   ```javascript
   const needs = {
     metrics: ['revenue', 'growth', 'margin'],
     visualizations: ['trend', 'comparison'],
     interactions: ['filter', 'date-select'],
     layout: 'executive-summary'
   };
   
   const components = mapNeedsToComponents(needs);
   // Returns: ['kpi-strip', 'kpi-standard', 'line-chart', 'button-group']
   ```

4. **Select Layout Archetype**
   - Executive Summary → KPI Strip + Golden Split
   - Financial Analysis → Nested KPIs + Three Column
   - Operational → Sidebar + Main Content
   - Comparison → Hierarchical Table + Bars

5. **Compose HTML**
   - Start with base template
   - Add selected components
   - Apply theme (light default)
   - Integrate icons (Lucide)
   - Ensure responsiveness

6. **Validate**
   ```javascript
   const validation = await html_validate_mockup({
     guardrail_token: token,
     html: generatedHTML,
     expected_library: "Lucide",
     expected_theme: "light"
   });
   ```

7. **Iterate if Needed**
   - Fix violations
   - Revalidate
   - Deliver final HTML

## Automatic Screenshot Learning

When user provides screenshot:

1. **Visual Analysis**
   - Extract colors, spacing, typography
   - Identify components (known vs unknown)
   - Measure proportions and layouts

2. **Pattern Extraction**
   - Detect new component patterns
   - Document variations of existing components
   - Note innovative interactions

3. **Library Update**
   - Add new components to component_library.md
   - Generate HTML/CSS templates
   - Update decision tree
   - Create validation rules

4. **Log & Version**
   - Add to screenshot_analysis_log.md
   - Increment library version
   - Update component_metadata.json
```

---

### 3. docs/component_catalog.md

**Content**: (Already created in artifact - "Component Catalog & Usage Guide")

**Purpose**:
- Quick reference for Claude and users
- Component selection matrix
- Common patterns and combinations
- Copy-paste templates

---

### 4. docs/component_metadata.json

**Content**: (Create this file)

```json
{
  "version": "1.0",
  "last_updated": "2025-01-11",
  "total_components": 29,
  "categories": {
    "kpi_cards": {
      "count": 5,
      "components": {
        "kpi-standard": {
          "id": "kpi-standard",
          "name": "Standard KPI Card",
          "frequency": "very_high",
          "complexity": "low",
          "use_cases": ["executive_summary", "metrics_overview"],
          "required_data": ["label", "value", "delta", "sparkline_data"],
          "theme_support": ["light", "dark"],
          "responsive": true,
          "accessibility": {
            "aria_labels": true,
            "keyboard_nav": false
          },
          "source_screenshots": [1, 8],
          "template_file": "templates/components/kpi_cards.html",
          "section_ref": "1.1",
          "tags": ["metric", "trend", "comparison", "sparkline"]
        },
        "kpi-nested": {
          "id": "kpi-nested",
          "name": "Nested KPI Card",
          "frequency": "high",
          "complexity": "medium",
          "use_cases": ["financial_analysis", "detailed_metrics"],
          "required_data": ["main_value", "main_label", "sub_metrics[]"],
          "theme_support": ["light", "dark"],
          "responsive": true,
          "source_screenshots": [2],
          "section_ref": "1.2",
          "tags": ["metric", "breakdown", "financial"]
        }
        // ... all other components
      }
    },
    "tables": { /* ... */ },
    "charts": { /* ... */ },
    "controls": { /* ... */ },
    "layouts": { /* ... */ },
    "navigation": { /* ... */ },
    "indicators": { /* ... */ },
    "specialized": { /* ... */ }
  },
  "screenshot_analysis_history": [
    {
      "screenshot_id": 1,
      "name": "Product Margin Analysis",
      "date_analyzed": "2025-01-11",
      "components_extracted": [
        "kpi-standard",
        "hierarchical-table",
        "donut-chart",
        "horizontal-bars",
        "button-group"
      ],
      "new_patterns": [
        "three-column-bottom-grid"
      ]
    }
    // ... more screenshots
  ]
}
```

---

### 5. docs/screenshot_analysis_log.md

**Content**: (Create this file)

```markdown
# Screenshot Analysis Log

## Screenshot 1: Product Margin Analysis (2025-01-11)

**Theme**: Dark  
**Primary Colors**: #1E293B (background), #3B82F6 (accent), #22C55E (success)  
**Layout**: 12-column grid, 1920px max-width  

### Components Identified
- ✓ Standard KPI Card x4 (with sparklines)
- ✓ Hierarchical Table (2 levels)
- ✓ Donut Chart (thick segments)
- ✓ Horizontal Bar Chart x3
- ✓ Button Group (Category filter)

### New Patterns
- Three-column bottom grid layout
- Performance bar with gradient fill

### Added to Library
- Section 5.4: Three-Column Bottom Grid

---

## Screenshot 2: Financial Risk Analysis (2025-01-11)

**Theme**: Light with teal/red accents  
**Primary Colors**: #FFFFFF (background), #14B8A6 (teal), #EF4444 (red)  
**Layout**: Mixed, brand-specific  

### Components Identified
- ✓ Nested KPI Card x4 (NEW)
- ✓ Half-Circle Gauge x2
- ✓ Horizontal Bar Chart (with percentages)
- ✗ Side-by-side comparison charts (NEW)

### New Patterns
- Nested KPI with sub-metric grid
- Dual comparison charts in single card

### Added to Library
- Section 1.2: Nested KPI Card
- Section 3.2: Half-Circle Gauge (enhanced)
- Section 3.3: Horizontal Bars with Percentages

---

## Screenshot 3: Enterprise Risk Dashboard (2025-01-11)

**Theme**: Dark with purple accent  
**Primary Colors**: #0F172A (sidebar), #8B5CF6 (accent)  

### Components Identified
- ✓ Dark Sidebar Navigation (NEW)
- ✓ Circular Progress (large)
- ✓ Donut Chart
- ✓ Heatmap Calendar (NEW)
- ✓ Numbered Risk Cards (NEW)

### New Patterns
- Heatmap calendar grid (7 days x weeks)
- Numbered card list with indicators

### Added to Library
- Section 3.1: Heatmap Calendar Grid
- Section 6.1: Dark Sidebar Navigation
- Section 8.1: Numbered Risk/Task Card

---

[Continue for all 7 screenshots...]
```

---

### 6. templates/base/dashboard_base.html

**Content**: (Create this file)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        /* Reset & Base */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
            font-feature-settings: "tnum" 1;
            background: #F8FAFC;
            color: #0F172A;
            padding: 24px;
        }
        
        /* Grid System */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* Utility Classes */
        .span-3 { grid-column: span 3; }
        .span-4 { grid-column: span 4; }
        .span-6 { grid-column: span 6; }
        .span-8 { grid-column: span 8; }
        .span-12 { grid-column: span 12; }
        
        /* Component Styles */
        /* [Insert component CSS here] */
        
        /* Responsive */
        @media (max-width: 1200px) {
            .span-3, .span-4, .span-6, .span-8 {
                grid-column: span 6;
            }
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            .span-3, .span-4, .span-6, .span-8, .span-12 {
                grid-column: span 1;
            }
        }
    </style>
</head>
<body>
    <div class="dashboard-grid">
        <!-- Components go here -->
    </div>
    
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
```

---

### 7. templates/components/kpi_cards.html

**Content**: (Create this file - contains ALL KPI variants)

```html
<!-- Standard KPI Card -->
<div class="kpi-card kpi-standard">
    <div class="kpi-label">Total Revenue</div>
    <div class="kpi-value">$1.36M</div>
    <div class="kpi-delta positive">
        <i data-lucide="trending-up"></i>
        <span>+12.4% vs PY</span>
    </div>
    <svg class="kpi-sparkline" viewBox="0 0 120 32" preserveAspectRatio="none">
        <path d="M 0,24 Q 10,20 20,16 Q 30,12 40,14 Q 50,16 60,10 Q 70,4 80,6 Q 90,8 100,4 Q 110,0 120,2" 
              fill="none" stroke="#3B82F6" stroke-width="2"/>
        <path d="M 0,24 Q 10,20 20,16 Q 30,12 40,14 Q 50,16 60,10 Q 70,4 80,6 Q 90,8 100,4 Q 110,0 120,2 L 120,32 L 0,32 Z" 
              fill="rgba(59,130,246,0.1)"/>
    </svg>
</div>

<!-- Nested KPI Card -->
<div class="kpi-card kpi-nested">
    <div class="kpi-label">Expected Loss</div>
    <div class="kpi-value-large negative">-$67.8M</div>
    <div class="kpi-subtitle">Net Loss</div>
    <div class="kpi-metric-grid">
        <div class="kpi-sub-metric">
            <div class="kpi-sub-label">EL Portfolio</div>
            <div class="kpi-sub-value">-$5.5M</div>
        </div>
        <div class="kpi-sub-metric">
            <div class="kpi-sub-label">% of Total</div>
            <div class="kpi-sub-value">722.3%</div>
        </div>
    </div>
</div>

<!-- [All other KPI variants...] -->

<style>
/* [All KPI card CSS from library] */
</style>
```

---

### 8. validation/component_validator.py

**Content**: (Create this file)

```python
"""
Component Validator
Validates HTML mockups against component library standards
"""

import re
import json
from bs4 import BeautifulSoup

class ComponentValidator:
    def __init__(self, html_content, component_metadata_path):
        self.html = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
        with open(component_metadata_path) as f:
            self.metadata = json.load(f)
        self.violations = []
        self.warnings = []
    
    def validate_kpi_cards(self):
        """Validate KPI card structure and styling"""
        kpi_cards = self.soup.find_all(class_='kpi-card')
        
        for card in kpi_cards:
            # Check for required elements
            if not card.find(class_='kpi-label'):
                self.violations.append(f"KPI card missing label element")
            
            if not card.find(class_='kpi-value'):
                self.violations.append(f"KPI card missing value element")
            
            # Check sparkline width
            sparkline = card.find(class_='kpi-sparkline')
            if sparkline and 'width: 100%' not in str(sparkline.get('style', '')):
                self.violations.append(f"Sparkline must span 100% width")
            
            # Check for tabular-nums on values
            value = card.find(class_='kpi-value')
            if value:
                style = value.get('style', '')
                if 'font-variant-numeric: tabular-nums' not in style:
                    self.warnings.append(f"KPI value should use tabular-nums")
    
    def validate_charts(self):
        """Validate chart mathematics and proportions"""
        # Check donut charts sum to 360 degrees
        # Check bar heights are proportional
        # etc.
        pass
    
    def validate_theme(self, expected_theme='light'):
        """Validate theme consistency"""
        body = self.soup.find('body')
        if body:
            style = body.get('style', '')
            if expected_theme == 'light':
                if 'background: #0F172A' in style or 'background: #1E293B' in style:
                    self.violations.append(f"Dark theme used but light theme expected")
    
    def validate_