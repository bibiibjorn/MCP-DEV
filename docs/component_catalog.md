# Component Catalog & Quick Reference Guide

## How to Use This Library

### Workflow Integration

```
User Request → Screenshot Analysis → Component Selection → HTML Generation → Validation
     ↓              ↓                      ↓                    ↓               ↓
  "Create      Extract patterns     Choose from        Draft using      html:validate
  dashboard"   & identify needs     component lib      templates        with token
```

---

## Quick Start

### 1. Call Guardrails First
```javascript
// ALWAYS start here
const result = await html_guardrails();
const token = result.guardrail_token; // Save this!
```

### 2. Analyze User Request
```javascript
// What are they asking for?
const requestType = {
  singleMetric: false,      // → KPI Card
  multipleMetrics: true,    // → KPI Strip Layout
  tableData: true,          // → Hierarchical Table
  timeSeries: false,        // → Column/Line Chart
  comparison: true,         // → Horizontal Bars
  navigation: false,        // → Dark Sidebar
  filters: true            // → Button Group + Date Range
};
```

### 3. Select Components
```javascript
const selectedComponents = [
  'kpi-strip',              // Layout pattern
  'kpi-standard',           // 4x KPI cards
  'hierarchical-table',     // Main data display
  'button-group',           // Category filter
  'horizontal-bars'         // Comparison chart
];
```

### 4. Generate HTML
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Name</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        /* Include component CSS from library */
    </style>
</head>
<body>
    <!-- Compose components here -->
    <script>lucide.createIcons();</script>
</body>
</html>
```

### 5. Validate
```javascript
const validation = await html_validate_mockup({
  guardrail_token: token,
  html: finalHTML,
  expected_library: "Lucide",
  expected_theme: "light"
});

// Fix violations and iterate
```

---

## Component Selection Matrix

| User Need | Primary Component | Supporting Components | Layout |
|-----------|------------------|----------------------|--------|
| Executive Summary | kpi-standard (4x) | delta-chips, sparklines | kpi-strip |
| Financial Analysis | kpi-nested (3-4x) | half-gauge, status-badges | golden-split |
| Product Performance | hierarchical-table | inline-bars, button-group | sidebar-main |
| Risk Dashboard | donut-chart, numbered-card | heatmap-calendar, profile-card | three-column |
| Call Center Metrics | kpi-rating, kpi-stacked-bar | horizontal-bars, heatmap | sidebar-main |
| Regional Analysis | kpi-compact (grid) | column-chart, small-multiples | auto-grid |
| Supply Chain | column-chart, horizontal-bars | date-range, button-group, table | golden-split |
| Time Series | sparklines, line-chart | kpi-standard, filter-pills | kpi-strip |

---

## Common Dashboard Patterns

### Pattern 1: Executive KPI Dashboard
```
Structure:
├─ Header (Title + Date Range)
├─ KPI Strip (4 cards with sparklines)
├─ Primary Chart (Golden Split: 66/34)
│  ├─ Line Chart (Main)
│  └─ Top 5 List (Side)
└─ Footer (Last Updated)

Components:
- kpi-standard (x4)
- date-range-selector
- line-chart (from guardrails)
- numbered-card-list
```

### Pattern 2: Financial Risk Dashboard
```
Structure:
├─ Header (Bank Logo + Navigation)
├─ KPI Strip (4 nested cards)
├─ Comparison Section (2 column grid)
│  ├─ Loan-to-Income (Half-Gauge)
│  └─ Debt-to-Income (Horizontal Bars)
└─ History Analysis (Full Width)

Components:
- kpi-nested (x4)
- half-gauge (x2)
- horizontal-bars
- button-group
```

### Pattern 3: Operational Dashboard with Sidebar
```
Structure:
├─ Dark Sidebar (Navigation)
├─ Main Content
│  ├─ Header (Title + Filters)
│  ├─ KPI Strip (3 cards)
│  ├─ Heatmap Calendar
│  └─ Profile Card

Components:
- dark-sidebar
- kpi-stacked-bar (x3)
- heatmap-calendar
- profile-card
- button-group
```

---

## Component Combinations

### Combination 1: KPI Card + Sparkline
**Purpose**: Show metric with trend  
**Frequency**: Very High (80%)  
**Code**: See Library Section 1.1

### Combination 2: Hierarchical Table + Inline Bars
**Purpose**: Category breakdown with visual comparison  
**Frequency**: High (60%)  
**Code**: See Library Section 2.1 + 2.2

### Combination 3: Button Group + Date Range + Table
**Purpose**: Filtered data display  
**Frequency**: High (55%)  
**Code**: Combine Section 4.1 + 4.2 + 2.1

### Combination 4: Sidebar + KPI Strip + Main Chart
**Purpose**: Full dashboard with navigation  
**Frequency**: Medium (40%)  
**Code**: Combine Section 6.1 + 5.1 + 3.4

### Combination 5: Nested KPI + Half-Gauge + Horizontal Bars
**Purpose**: Financial metrics with breakdown  
**Frequency**: Medium (35%)  
**Code**: Combine Section 1.2 + 3.2 + 3.3

---

## Responsive Patterns

### Mobile-First Approach
```css
/* Base: Mobile (< 768px) */
.kpi-strip {
    grid-template-columns: 1fr;
}

/* Tablet (768px - 1200px) */
@media (min-width: 768px) {
    .kpi-strip {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop (> 1200px) */
@media (min-width: 1200px) {
    .kpi-strip {
        grid-template-columns: repeat(4, 1fr);
    }
}
```

### Container Queries (Modern)
```css
.card-container {
    container-type: inline-size;
}

@container (max-width: 400px) {
    .kpi-card {
        padding: 16px;
        min-height: 140px;
    }
    
    .kpi-value {
        font-size: 32px;
    }
}
```

---

## Color Palette Reference

### Semantic Colors (Copy-Paste Ready)
```css
/* Success/Positive */
--success-bg: #ECFDF5;
--success-text: #059669;
--success-border: #A7F3D0;

/* Danger/Negative */
--danger-bg: #FEF2F2;
--danger-text: #DC2626;
--danger-border: #FECACA;

/* Warning */
--warning-bg: #FFFBEB;
--warning-text: #D97706;
--warning-border: #FDE68A;

/* Primary */
--primary-bg: #EFF6FF;
--primary-text: #3B82F6;
--primary-border: #BFDBFE;

/* Neutral */
--neutral-bg: #F8FAFC;
--neutral-text: #64748B;
--neutral-border: #E2E8F0;
```

### Data Visualization Palette
```css
/* Categorical (5 colors max) */
--cat-1: #3B82F6;  /* Blue */
--cat-2: #8B5CF6;  /* Purple */
--cat-3: #10B981;  /* Green */
--cat-4: #F59E0B;  /* Amber */
--cat-5: #EF4444;  /* Red */

/* Sequential (Blue scale) */
--seq-1: #EFF6FF;
--seq-2: #BFDBFE;
--seq-3: #60A5FA;
--seq-4: #3B82F6;
--seq-5: #1E40AF;
```

---

## Typography Scale (Copy-Paste Ready)

```css
/* Display */
.display-hero   { font-size: 56px; font-weight: 700; letter-spacing: -1.5px; }
.display-large  { font-size: 42px; font-weight: 700; letter-spacing: -1px; }

/* Headings */
.h1 { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }
.h2 { font-size: 20px; font-weight: 600; }
.h3 { font-size: 16px; font-weight: 600; }
.h4 { font-size: 14px; font-weight: 600; }

/* Body */
.body-large  { font-size: 16px; line-height: 1.6; }
.body        { font-size: 14px; line-height: 1.5; }
.body-small  { font-size: 13px; line-height: 1.5; }

/* Labels */
.label-large { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
.label       { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
.label-small { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

/* Captions */
.caption { font-size: 11px; color: #64748B; }
.micro   { font-size: 10px; color: #94A3B8; }
```

---

## Spacing Scale (Copy-Paste Ready)

```css
/* Spacing Variables (8px base) */
--space-1: 4px;   /* Micro gaps */
--space-2: 8px;   /* Tight spacing */
--space-3: 12px;  /* Compact */
--space-4: 16px;  /* Standard */
--space-5: 20px;  /* Grid gaps */
--space-6: 24px;  /* Card padding */
--space-8: 32px;  /* Section breaks */
--space-12: 48px; /* Major sections */
--space-16: 64px; /* Page sections */

/* Usage Examples */
.card { padding: var(--space-6); }
.dashboard-grid { gap: var(--space-5); }
.kpi-label { margin-bottom: var(--space-2); }
```

---

## Icon Integration

### Lucide Icons (Recommended)
```html
<!-- Include in <head> -->
<script src="https://unpkg.com/lucide@latest"></script>

<!-- Use in HTML -->
<i data-lucide="trending-up"></i>
<i data-lucide="alert-triangle"></i>
<i data-lucide="check-circle"></i>

<!-- Initialize at end of <body> -->
<script>lucide.createIcons();</script>
```

### Common Dashboard Icons
```
trending-up, trending-down → Delta indicators
chevron-down, chevron-right → Expand/collapse
calendar → Date selector
filter → Filter controls
search → Search input
settings → Settings menu
users → Team/people metrics
bar-chart-2, line-chart, pie-chart → Chart types
alert-triangle → Warnings
check-circle → Success states
x-circle → Error states
info → Information
download → Export functions
refresh-cw → Refresh data
```

---

## Error Prevention Checklist

### Before Generating HTML

- [ ] Called `html:guardrails` and stored token
- [ ] Analyzed user request for component needs
- [ ] Selected appropriate layout archetype
- [ ] Confirmed theme (light is default)
- [ ] Chosen icon library (Lucide recommended)
- [ ] Verified data ranges are realistic
- [ ] Planned responsive breakpoints

### During HTML Generation

- [ ] Using semantic HTML5 elements
- [ ] Inline CSS in `<style>` tag
- [ ] Only CDN dependencies (no local files)
- [ ] All icons are actual SVG/icon font (no placeholders)
- [ ] Tabular-nums on all numeric values
- [ ] Color contrast >= 4.5:1 for text
- [ ] Focus states on interactive elements
- [ ] ARIA labels where appropriate

### Before Validation

- [ ] Percentages sum to 100% in charts
- [ ] Bar heights proportional to data
- [ ] Sparklines span full card width
- [ ] All gaps use 8px base spacing
- [ ] Typography from defined scale
- [ ] Max-width appropriate for screen
- [ ] Responsive at 768px breakpoint
- [ ] No external scripts except CDN

---

## Screenshot Analysis Template

When user provides new screenshot:

```markdown
## Screenshot Analysis: [Name]

### Visual Characteristics
- **Theme**: [Light/Dark/Mixed]
- **Dominant Colors**: [List hex codes]
- **Layout**: [Grid structure, columns]
- **Typography**: [Observed sizes, weights]

### Components Identified
1. **[Component Name]**
   - Type: [KPI/Table/Chart/Control]
   - Frequency: [High/Medium/Low]
   - New?: [Yes/No - explain if new]
   - Location: [Where in dashboard]

### New Patterns Discovered
- Pattern 1: [Description + use case]
- Pattern 2: [Description + use case]

### Missing from Library
- [ ] Component X - [Priority] - [Description]
- [ ] Component Y - [Priority] - [Description]

### Integration Plan
1. Extract component HTML structure
2. Write CSS following design tokens
3. Add to library with metadata
4. Update decision tree
5. Generate validation rules
6. Test with guardrails
```

---

## Common Mistakes to Avoid

### ❌ WRONG: Placeholder Icons
```html
<div>[trending-up icon]</div>
<div>📈</div>
```

### ✅ CORRECT: Actual Icons
```html
<i data-lucide="trending-up"></i>
```

---

### ❌ WRONG: Dark Theme by Default
```css
body {
    background: #0F172A;
    color: #FFFFFF;
}
```

### ✅ CORRECT: Light Theme Default
```css
body {
    background: #F8FAFC;
    color: #0F172A;
}
```

---

### ❌ WRONG: Non-Proportional Bars
```html
<div class="bar" style="width: 50%">$100K</div>
<div class="bar" style="width: 70%">$120K</div> <!-- WRONG! -->
```

### ✅ CORRECT: Proportional Bars
```html
<div class="bar" style="width: 45.5%">$100K</div>
<div class="bar" style="width: 54.5%">$120K</div> <!-- Correct ratio -->
```

---

### ❌ WRONG: Missing Tabular Nums
```css
.kpi-value {
    font-size: 42px;
    font-weight: 700;
}
```

### ✅ CORRECT: Tabular Nums
```css
.kpi-value {
    font-size: 42px;
    font-weight: 700;
    font-variant-numeric: tabular-nums; /* Numbers align */
}
```

---

## Performance Tips

### CSS Optimization
```css
/* Use custom properties for repeated values */
:root {
    --card-radius: 12px;
    --card-shadow: 0 2px 8px rgba(15,23,42,0.06);
}

/* Avoid complex selectors */
.card .header .title span { } /* Bad */
.card-title { } /* Good */

/* Use containment for performance */
.kpi-card {
    contain: layout style;
}
```

### HTML Optimization
```html
<!-- Minimize nesting depth -->
<div class="dashboard-grid">
    <div class="kpi-card"><!-- Content --></div>
</div>

<!-- Not this: -->
<div><div><div><div>
    <div class="kpi-card"><!-- Content --></div>
</div></div></div></div>
```

---

## Testing Checklist

### Visual Testing
- [ ] View at 1920x1080 (desktop)
- [ ] View at 1366x768 (laptop)
- [ ] View at 768x1024 (tablet)
- [ ] View at 375x667 (mobile)
- [ ] Check text contrast (WCAG AA)
- [ ] Verify icon rendering
- [ ] Test hover states
- [ ] Check responsive breakpoints

### Data Validation
- [ ] All percentages sum to 100%
- [ ] Bar heights match data ratios
- [ ] Trend lines match deltas
- [ ] Numbers use consistent units
- [ ] Dates formatted consistently

### Code Validation
- [ ] HTML validates (W3C)
- [ ] CSS has no errors
- [ ] All CDN links work
- [ ] Icons initialize properly
- [ ] No console errors

---

## Quick Copy-Paste Templates

### Template 1: Basic Dashboard Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #F8FAFC;
            padding: 24px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        /* Add component styles */
    </style>
</head>
<body>
    <div class="dashboard-grid">
        <!-- Components here -->
    </div>
    <script>lucide.createIcons();</script>
</body>
</html>
```

### Template 2: With Sidebar
```html
<div class="app-layout">
    <aside class="sidebar"><!-- Nav --></aside>
    <main class="main-content">
        <div class="dashboard-grid">
            <!-- Components -->
        </div>
    </main>
</div>
```

---

## Version Control

When updating the library:

```markdown
## Update Log

### v1.1 (Date)
**Added:**
- Component: [name] - [description]
- Pattern: [name] - [use case]

**Modified:**
- Component: [name] - [what changed]

**Fixed:**
- Issue: [description] - [solution]

**Deprecated:**
- Component: [name] - [reason] - [replacement]
```

---

## Support & Troubleshooting

### Issue: Validation Fails
**Check:**
1. Guardrail token not expired
2. All icons are actual (not placeholders)
3. Theme is light (unless requested)
4. Chart math is correct
5. Spacing uses 8px base

### Issue: Layout Breaks
**Check:**
1. Grid spans sum correctly
2. Responsive breakpoints defined
3. Max-width set appropriately
4. Flex/grid properties correct
5. Z-index layering logical

### Issue: Poor Performance
**Check:**
1. Too many elements (>200)
2. Complex CSS selectors
3. Missing containment
4. Inefficient animations
5. Large SVG files

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2025-01-11  
**Maintainer**: Claude AI  
**Integration**: MCP PowerBI Finvision Server
