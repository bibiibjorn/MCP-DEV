# Power BI Visual Mockup Guardrails v7.0

**Audience**: Claude (160+ IQ) producing Power BI-style HTML mockups  
**Objective**: Deliver single-file mockups that look indistinguishable from production Power BI dashboards

---

## 0. Critical Design Mandates

### 0.1 Default Theme: Light Mode
**Light mode is default unless explicitly requested otherwise.**

```css
/* Base Palette */
--bg-primary: #FFFFFF;
--bg-secondary: #F8FAFC;
--bg-tertiary: #F1F5F9;

--surface-card: #FFFFFF;
--border-subtle: #E2E8F0;
--border-medium: #CBD5E1;

--text-primary: #0F172A;
--text-secondary: #334155;
--text-tertiary: #64748B;
--text-muted: #94A3B8;

--shadow-card: 0 2px 8px rgba(15,23,42,0.06);
--shadow-elevated: 0 4px 16px rgba(15,23,42,0.08);
--shadow-hover: 0 8px 24px rgba(15,23,42,0.12);
```

### 0.2 Icon Library Integration
**NEVER use placeholder text for icons. Always use actual icons.**

**Approved Sources**:
- Lucide: `<script src="https://unpkg.com/lucide@latest"></script>` + `lucide.createIcons()`
- Bootstrap Icons: `<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css">`
- Heroicons: Inline SVG paths only

**Icon Sizing**:
- Navigation: 20px
- KPI cards: 16px
- Buttons: 18px
- Inline trends: 12px

---

## 1. Universal Layout Patterns

### 1.1 Card Architecture (CORE PATTERN)
**Every dashboard is built from cards. Master this structure.**

```css
.card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(15,23,42,0.06);
    border: 1px solid rgba(15,23,42,0.04);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #E2E8F0;
}

.card-title {
    font-size: 16px;
    font-weight: 600;
    color: #1E293B;
    letter-spacing: -0.2px;
}

.card-actions {
    display: flex;
    gap: 8px;
}

.card-body {
    position: relative;
}

.card-footer {
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid #F1F5F9;
    font-size: 11px;
    color: #64748B;
}
```

**Card Variants Observed**:
1. **KPI Card**: Large metric + delta + sparkline
2. **Chart Card**: Title + legend + visualization
3. **Table Card**: Title + filters + data grid
4. **Metric Group**: Multiple mini-cards in one container

### 1.2 Grid System (12-Column Foundation)
```css
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 20px;
    padding: 20px;
    max-width: 1400px; /* Adjust based on screen detection */
    margin: 0 auto;
}

/* Span utilities */
.span-3 { grid-column: span 3; }  /* 25% - Sidebar/filter */
.span-4 { grid-column: span 4; }  /* 33% - Triptych */
.span-6 { grid-column: span 6; }  /* 50% - Split */
.span-8 { grid-column: span 8; }  /* 66% - Primary content */
.span-12 { grid-column: span 12; } /* 100% - Full width */
```

**Layout Archetypes**:
- **Hero + Supporting**: `span-8` + `span-4` (62/38 golden ratio)
- **Triptych**: Three `span-4` cards (33/33/33)
- **KPI Strip**: Four `span-3` cards (25/25/25/25)
- **Detail View**: `span-3` filters + `span-9` content (25/75)

### 1.3 Spacing Scale (8px Base)
**Observed spacing pattern across all 7 dashboards**:
```
4px  - Micro (icon-to-text gap, chip padding)
8px  - Tight (between related elements)
12px - Compact (card internal sections)
16px - Standard (between components)
20px - Comfortable (grid gaps)
24px - Relaxed (card padding)
32px - Spacious (section breaks)
48px - Major (page sections)
```

---

## 2. Typography System (Refined from Examples)

### 2.1 Font Stack
```css
font-family: 'Segoe UI', 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
font-feature-settings: "tnum" 1; /* Tabular numerals for metrics */
```

### 2.2 Type Scale (Extracted from Dashboards)
```css
/* Display Metrics */
.metric-hero {
    font-size: 48px;
    font-weight: 700;
    line-height: 1.0;
    letter-spacing: -1.2px;
    color: #0F172A;
}

.metric-large {
    font-size: 32px;
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -0.8px;
    color: #0F172A;
}

.metric-medium {
    font-size: 24px;
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.4px;
    color: #1E293B;
}

/* Headers */
.h1 { font-size: 20px; font-weight: 600; color: #1E293B; }
.h2 { font-size: 16px; font-weight: 600; color: #334155; }
.h3 { font-size: 14px; font-weight: 600; color: #475569; }

/* Body & Labels */
.body { font-size: 14px; font-weight: 400; line-height: 1.5; color: #334155; }
.label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #64748B; }
.micro { font-size: 10px; font-weight: 400; letter-spacing: 0.25px; color: #94A3B8; }

/* Table Specific */
.table-header {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748B;
}

.table-cell {
    font-size: 13px;
    font-weight: 400;
    line-height: 1.4;
    color: #1E293B;
    font-variant-numeric: tabular-nums;
}
```

---

## 3. Color System (Universal Semantic Palette)

### 3.1 Semantic Colors (Domain-Agnostic)
```css
/* Success/Positive - Green */
--success-bg: #ECFDF5;
--success-border: #A7F3D0;
--success-text: #059669;
--success-strong: #047857;

/* Danger/Negative - Red */
--danger-bg: #FEF2F2;
--danger-border: #FECACA;
--danger-text: #DC2626;
--danger-strong: #B91C1C;

/* Warning/Caution - Amber */
--warning-bg: #FFFBEB;
--warning-border: #FDE68A;
--warning-text: #D97706;
--warning-strong: #B45309;

/* Primary/Focus - Blue */
--primary-bg: #EFF6FF;
--primary-border: #BFDBFE;
--primary-text: #2563EB;
--primary-strong: #1D4ED8;

/* Info/Neutral - Cyan */
--info-bg: #ECFEFF;
--info-border: #A5F3FC;
--info-text: #0891B2;
--info-strong: #0E7490;

/* Secondary/Purple (for variance) */
--secondary-bg: #F5F3FF;
--secondary-border: #DDD6FE;
--secondary-text: #7C3AED;
--secondary-strong: #6D28D9;
```

### 3.2 Data Visualization Palettes
**Categorical (5-color max per view)**:
```css
--cat-1: #3B82F6;  /* Blue - Primary series */
--cat-2: #8B5CF6;  /* Purple - Secondary series */
--cat-3: #10B981;  /* Green - Tertiary series */
--cat-4: #F59E0B;  /* Amber - Quaternary */
--cat-5: #EF4444;  /* Red - Quinary */
```

**Sequential (single-hue scales)**:
```css
/* Blue Scale */
--seq-1: #EFF6FF;  /* Lightest */
--seq-2: #BFDBFE;
--seq-3: #60A5FA;
--seq-4: #3B82F6;
--seq-5: #1E40AF;  /* Darkest */
```

**Diverging (for variance visualization)**:
```css
/* Red-to-Green (negative to positive) */
--div-neg-2: #DC2626;  /* Strong negative */
--div-neg-1: #F87171;  /* Mild negative */
--div-zero: #94A3B8;   /* Neutral */
--div-pos-1: #4ADE80;  /* Mild positive */
--div-pos-2: #059669;  /* Strong positive */
```

---

## 4. Chart Type Specifications

### 4.1 KPI Card with Sparkline (MOST COMMON)
**Pattern observed in 6 of 7 dashboards**
**CRITICAL: Sparklines MUST span full card width for maximum impact**

```html
<div class="kpi-card">
    <div class="kpi-label">Total Revenue</div>
    <div class="kpi-value">$1.36M</div>
    <div class="kpi-delta positive">
        <i data-lucide="trending-up"></i>
        <span>+12.4% vs PY</span>
    </div>
    <!-- CRITICAL: Sparkline spans 100% width with proper aspect ratio -->
    <svg class="kpi-sparkline" viewBox="0 0 120 32" preserveAspectRatio="none">
        <!-- Sparkline path here -->
    </svg>
</div>
```

```css
.kpi-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(15,23,42,0.06);
    position: relative;
}

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #64748B;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 36px;
    font-weight: 700;
    line-height: 1.0;
    letter-spacing: -0.8px;
    color: #0F172A;
    margin-bottom: 8px;
}

.kpi-delta {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 16px;
}

.kpi-delta.positive {
    background: rgba(5,150,105,0.1);
    color: #059669;
}

.kpi-delta.negative {
    background: rgba(220,38,38,0.1);
    color: #DC2626;
}

/* CRITICAL: Sparkline sizing rules */
.kpi-sparkline {
    width: 100%;              /* MUST be 100% to span full card width */
    height: 48px;             /* Fixed height for consistency (can be 32-64px) */
    display: block;
    margin-top: auto;         /* Push to bottom of card */
}
```

**Sparkline Sizing Rules**:
- **Width**: ALWAYS 100% of card width - never centered or constrained
- **Height**: 32-64px depending on card size (48px recommended)
- **Aspect ratio**: Use `preserveAspectRatio="none"` to stretch full width
- **ViewBox**: Use fixed viewBox (e.g., "0 0 120 32") regardless of actual width
- **Position**: Last element in card, pushed to bottom with margin-top

### 4.2 Inline Bar Chart (Table Enhancement)
**Observed in financial tables across all examples**

```html
<tr class="table-row">
    <td class="table-cell-label">Cloud Infrastructure</td>
    <td class="table-cell-metric">
        <div class="inline-bar-container">
            <div class="inline-bar" style="width: 73%;"></div>
            <span class="inline-bar-value">$302.6K</span>
        </div>
    </td>
    <td class="table-cell-percent">87.4K</td>
    <td class="table-cell-percent">28.9%</td>
</tr>
```

```css
.inline-bar-container {
    position: relative;
    width: 100%;
    height: 20px;
    display: flex;
    align-items: center;
}

.inline-bar {
    position: absolute;
    left: 0;
    height: 12px;
    background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%);
    border-radius: 2px;
    opacity: 0.8;
}

.inline-bar-value {
    position: relative;
    z-index: 1;
    margin-left: 4px;
    font-size: 13px;
    font-weight: 500;
    color: #1E293B;
    font-variant-numeric: tabular-nums;
}
```

### 4.3 Small Multiples Grid
**Observed in geographic/segment comparisons**

```html
<div class="small-multiples-grid">
    <div class="small-multiple-card">
        <div class="small-multiple-header">
            <h3>Germany</h3>
            <span class="small-multiple-value">297</span>
        </div>
        <svg class="small-multiple-chart" viewBox="0 0 200 120">
            <!-- Chart content -->
        </svg>
    </div>
    <!-- Repeat for each region/segment -->
</div>
```

```css
.small-multiples-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

.small-multiple-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}

.small-multiple-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 12px;
}

.small-multiple-header h3 {
    font-size: 14px;
    font-weight: 600;
    color: #334155;
}

.small-multiple-value {
    font-size: 20px;
    font-weight: 700;
    color: #0F172A;
}

.small-multiple-chart {
    width: 100%;
    height: 120px;
}
```

### 4.4 Heatmap Calendar/Matrix
**Observed in temporal and distribution analysis**

```html
<div class="heatmap-container">
    <div class="heatmap-row">
        <div class="heatmap-label">Mon</div>
        <div class="heatmap-cell heat-2" title="23 items"></div>
        <div class="heatmap-cell heat-4" title="67 items"></div>
        <!-- More cells -->
    </div>
</div>
```

```css
.heatmap-container {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.heatmap-row {
    display: flex;
    gap: 4px;
    align-items: center;
}

.heatmap-label {
    width: 40px;
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-align: right;
    padding-right: 8px;
}

.heatmap-cell {
    width: 20px;
    height: 20px;
    border-radius: 3px;
    cursor: pointer;
    transition: transform 0.15s;
}

.heatmap-cell:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}

/* Sequential intensity scale */
.heat-0 { background: #F1F5F9; }  /* 0-20% */
.heat-1 { background: #DBEAFE; }  /* 21-40% */
.heat-2 { background: #93C5FD; }  /* 41-60% */
.heat-3 { background: #3B82F6; }  /* 61-80% */
.heat-4 { background: #1E40AF; }  /* 81-100% */
```

### 4.5 Circular Progress/Donut Chart
**CRITICAL: Donut charts must use thick strokes (35-50% of radius) to look substantial, not thin rings**

```html
<div class="donut-container">
    <svg class="donut-chart" viewBox="0 0 200 200">
        <!-- Use stroke-width 35-50% of radius for substantial appearance -->
        <!-- For r=70, use stroke-width between 25-35 -->
        <circle cx="100" cy="100" r="70" fill="none" stroke="#E2E8F0" stroke-width="32"/>
        <circle cx="100" cy="100" r="70" fill="none" stroke="#3B82F6" stroke-width="32"
                stroke-dasharray="307 440" stroke-dashoffset="0" 
                stroke-linecap="round" transform="rotate(-90 100 100)"/>
        <text x="100" y="95" text-anchor="middle" class="donut-value">159</text>
        <text x="100" y="115" text-anchor="middle" class="donut-label">Risks to Date</text>
    </svg>
</div>
```

```css
.donut-container {
    position: relative;
    width: 200px;
    height: 200px;
}

.donut-chart {
    width: 100%;
    height: 100%;
}

.donut-value {
    font-size: 42px;
    font-weight: 700;
    fill: #0F172A;
}

.donut-label {
    font-size: 12px;
    font-weight: 500;
    fill: #64748B;
}
```

**Donut Thickness Rule**:
- Radius 70-80px → stroke-width: 28-35px (thick, substantial)
- Radius 50-60px → stroke-width: 20-26px
- Radius 90-100px → stroke-width: 35-45px
- **NEVER use stroke-width less than 35% of radius** - thin rings look incomplete

### 4.6 Gauge/Semi-Circle Progress
**CRITICAL: Use thick strokes (stroke-width 30-40% of radius) for substantial appearance**

```html
<svg class="gauge-chart" viewBox="0 0 200 120">
    <!-- Background arc - thick stroke -->
    <path d="M 20,100 A 80,80 0 0,1 180,100"
          stroke="#E2E8F0" stroke-width="28" fill="none"/>
    
    <!-- Progress arc (86% shown) - thick stroke with round cap -->
    <path d="M 20,100 A 80,80 0 0,1 165,45"
          stroke="#059669" stroke-width="28" fill="none" stroke-linecap="round"/>
    
    <!-- Center value -->
    <text x="100" y="85" text-anchor="middle" class="gauge-value">86%</text>
    <text x="100" y="105" text-anchor="middle" class="gauge-label">of Q4 Target</text>
</svg>
```

```css
.gauge-chart {
    width: 200px;
    height: 120px;
}

.gauge-value {
    font-size: 36px;
    font-weight: 700;
    fill: #0F172A;
}

.gauge-label {
    font-size: 11px;
    font-weight: 500;
    fill: #64748B;
}
```

**Gauge Thickness Rule**:
- Radius 80px → stroke-width: 26-32px (substantial)
- Radius 60px → stroke-width: 20-24px
- Radius 100px → stroke-width: 32-40px
- **NEVER use stroke-width less than 30% of radius** - thin arcs look weak

### 4.7 Rating Stars (Qualitative Metrics)
```html
<div class="rating-display">
    <div class="rating-value">3.38</div>
    <div class="rating-stars">
        <i data-lucide="star" class="star filled"></i>
        <i data-lucide="star" class="star filled"></i>
        <i data-lucide="star" class="star filled"></i>
        <i data-lucide="star" class="star"></i>
        <i data-lucide="star" class="star"></i>
    </div>
    <div class="rating-count">1,298 Ratings</div>
</div>
```

```css
.rating-display {
    text-align: center;
}

.rating-value {
    font-size: 56px;
    font-weight: 700;
    line-height: 1.0;
    color: #0F172A;
    margin-bottom: 8px;
}

.rating-stars {
    display: flex;
    justify-content: center;
    gap: 4px;
    margin-bottom: 8px;
}

.star {
    width: 20px;
    height: 20px;
    color: #E2E8F0;
}

.star.filled {
    color: #F59E0B;
}

.rating-count {
    font-size: 12px;
    color: #64748B;
}
```

---

## 5. Component Library (Production-Ready)

### 5.1 Data Table with Hierarchical Rows
```html
<table class="data-table">
    <thead>
        <tr>
            <th class="table-header">Segment</th>
            <th class="table-header text-right">Revenue</th>
            <th class="table-header text-right">Rev %</th>
            <th class="table-header text-right">GM</th>
            <th class="table-header">Trend</th>
        </tr>
    </thead>
    <tbody>
        <tr class="table-row-group">
            <td class="table-cell-group">Cloud Infrastructure</td>
            <td class="table-cell text-right">$302.6K</td>
            <td class="table-cell text-right">87.4K</td>
            <td class="table-cell text-right">28.9%</td>
            <td class="table-cell">
                <div class="inline-bar-container">
                    <div class="inline-bar" style="width: 87%;"></div>
                </div>
            </td>
        </tr>
        <tr class="table-row-item">
            <td class="table-cell-item">NetSystems</td>
            <td class="table-cell text-right">$107.4K</td>
            <td class="table-cell text-right">33.3K</td>
            <td class="table-cell text-right">31.0%</td>
            <td class="table-cell">
                <div class="inline-bar-container">
                    <div class="inline-bar" style="width: 33%;"></div>
                </div>
            </td>
        </tr>
        <!-- More rows -->
    </tbody>
</table>
```

```css
.data-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
}

.table-header {
    padding: 12px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748B;
    background: #F8FAFC;
    border-bottom: 2px solid #E2E8F0;
}

.table-row-group {
    background: #F8FAFC;
    border-top: 2px solid #CBD5E1;
}

.table-cell-group {
    padding: 12px 16px;
    font-weight: 600;
    color: #1E293B;
}

.table-row-item {
    background: #FFFFFF;
}

.table-row-item:nth-child(even) {
    background: rgba(15,23,42,0.02);
}

.table-cell-item {
    padding: 10px 16px;
    padding-left: 32px; /* Indent for hierarchy */
    color: #334155;
}

.table-cell {
    padding: 10px 16px;
    color: #334155;
    font-variant-numeric: tabular-nums;
}

.text-right {
    text-align: right;
}

.table-row-item:hover {
    background: rgba(59,130,246,0.04);
}
```

### 5.2 Sidebar Navigation (Dark Variant)
```html
<aside class="sidebar">
    <div class="sidebar-header">
        <div class="logo">
            <i data-lucide="activity"></i>
            <span>Analytics</span>
        </div>
    </div>
    
    <nav class="sidebar-nav">
        <a href="#" class="nav-item active">
            <i data-lucide="layout-dashboard"></i>
            <span>Overview</span>
        </a>
        <a href="#" class="nav-item">
            <i data-lucide="users"></i>
            <span>Agents</span>
        </a>
        <a href="#" class="nav-item">
            <i data-lucide="message-square"></i>
            <span>Contact</span>
        </a>
        <a href="#" class="nav-item">
            <i data-lucide="settings"></i>
            <span>Settings</span>
        </a>
    </nav>
</aside>
```

```css
.sidebar {
    width: 220px;
    height: 100vh;
    background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    border-right: 1px solid rgba(255,255,255,0.1);
    display: flex;
    flex-direction: column;
    position: fixed;
    left: 0;
    top: 0;
}

.sidebar-header {
    padding: 24px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
}

.logo i {
    width: 24px;
    height: 24px;
}

.sidebar-nav {
    padding: 16px 12px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    color: #CBD5E1;
    text-decoration: none;
    transition: all 0.2s;
    margin-bottom: 4px;
}

.nav-item:hover {
    background: rgba(255,255,255,0.08);
    color: #FFFFFF;
}

.nav-item.active {
    background: #3B82F6;
    color: #FFFFFF;
}

.nav-item i {
    width: 20px;
    height: 20px;
}
```

### 5.3 Filter Pills/Chips
```html
<div class="filter-bar">
    <button class="filter-chip active">
        <span>All Regions</span>
        <i data-lucide="x"></i>
    </button>
    <button class="filter-chip">
        <span>2024</span>
    </button>
    <button class="filter-chip">
        <i data-lucide="plus"></i>
        <span>Add Filter</span>
    </button>
</div>
```

```css
.filter-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 16px;
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    color: #475569;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.filter-chip:hover {
    border-color: #CBD5E1;
    background: #F8FAFC;
}

.filter-chip.active {
    background: #FDF2F8;
    border-color: #F9A8D4;
    color: #DB2777;
}

.filter-chip i {
    width: 14px;
    height: 14px;
}
```

### 5.4 Metric Badge (Status Indicator)
```html
<span class="metric-badge success">On Track</span>
<span class="metric-badge warning">At Risk</span>
<span class="metric-badge danger">Overdue</span>
<span class="metric-badge neutral">Not Started</span>
```

```css
.metric-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-badge.success {
    background: rgba(5,150,105,0.12);
    color: #047857;
}

.metric-badge.warning {
    background: rgba(245,158,11,0.12);
    color: #B45309;
}

.metric-badge.danger {
    background: rgba(220,38,38,0.12);
    color: #991B1B;
}

.metric-badge.neutral {
    background: rgba(100,116,139,0.12);
    color: #475569;
}
```

---

## 6. Chart Rendering Mathematics

### 6.1 Donut Chart (Precise Arc Calculation)
```javascript
function createDonutSegment(cx, cy, outerR, innerR, startAngle, endAngle, color) {
    const largeArc = (endAngle - startAngle) > 180 ? 1 : 0;
    
    const outerStart = polarToCartesian(cx, cy, outerR, startAngle);
    const outerEnd = polarToCartesian(cx, cy, outerR, endAngle);
    const innerStart = polarToCartesian(cx, cy, innerR, startAngle);
    const innerEnd = polarToCartesian(cx, cy, innerR, endAngle);
    
    return `
        M ${outerStart.x},${outerStart.y}
        A ${outerR},${outerR} 0 ${largeArc},1 ${outerEnd.x},${outerEnd.y}
        L ${innerEnd.x},${innerEnd.y}
        A ${innerR},${innerR} 0 ${largeArc},0 ${innerStart.x},${innerStart.y}
        Z
    `;
}

function polarToCartesian(cx, cy, r, angle) {
    const rad = (angle - 90) * Math.PI / 180;
    return {
        x: cx + r * Math.cos(rad),
        y: cy + r * Math.sin(rad)
    };
}

// Usage: 42% High, 28% Medium, 30% Low
const segments = [
    { percent: 42, color: '#EF4444', label: 'High' },
    { percent: 28, color: '#F59E0B', label: 'Medium' },
    { percent: 30, color: '#22C55E', label: 'Low' }
];

let cumulative = 0;
segments.forEach(seg => {
    const startAngle = cumulative * 3.6;
    const endAngle = (cumulative + seg.percent) * 3.6;
    const path = createDonutSegment(100, 100, 80, 50, startAngle, endAngle, seg.color);
    cumulative += seg.percent;
});
```

### 6.2 Bar Chart (Proportional Heights)
```javascript
function createBar(value, maxValue, chartHeight, baseline) {
    const barHeight = (value / maxValue) * chartHeight;
    const yPosition = baseline - barHeight;
    return { height: barHeight, y: yPosition };
}

// Example: Values [302.6, 215.5, 416.1] with max 500
const data = [302.6, 215.5, 416.1];
const maxValue = 500;
const chartHeight = 200;
const baseline = 220; // Y-position of x-axis

data.forEach((value, i) => {
    const bar = createBar(value, maxValue, chartHeight, baseline);
    // bar.height = 121.04, 86.2, 166.44
    // bar.y = 98.96, 133.8, 53.56
});
```

### 6.3 Sparkline (Smooth Path)
```javascript
function createSparkline(data, width, height) {
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min;
    const stepX = width / (data.length - 1);
    
    let path = `M 0,${height - ((data[0] - min) / range * height)}`;
    
    for (let i = 1; i < data.length; i++) {
        const x = i * stepX;
        const y = height - ((data[i] - min) / range * height);
        
        // Smooth curve using quadratic bezier
        const prevX = (i - 1) * stepX;
        const prevY = height - ((data[i-1] - min) / range * height);
        const cpX = (prevX + x) / 2;
        const cpY = (prevY + y) / 2;
        
        path += ` Q ${cpX},${prevY} ${x},${y}`;
    }
    
    return path;
}

// Usage
const revenueData = [120, 135, 128, 142, 156, 151, 168];
const sparklinePath = createSparkline(revenueData, 120, 32);
```

---

## 7. Validation Checklist (Pre-Delivery)

### 7.1 Visual Accuracy
- [ ] All percentages sum to 100% (+/-0.5% rounding tolerance)
- [ ] Bar heights are mathematically proportional to data
- [ ] Donut arcs total 360 degrees
- [ ] Line chart slopes match data direction
- [ ] Color legend matches chart segments exactly
- [ ] Axis labels align with gridlines (+/-2px)

### 7.2 Typography & Spacing
- [ ] All type sizes from defined scale (10/11/12/13/14/16/18/20/24/32/36/42/48/56)
- [ ] Spacing uses 8px base (4/8/12/16/20/24/32/48)
- [ ] Tabular figures enabled for all metrics (`font-variant-numeric: tabular-nums`)
- [ ] Letter-spacing negative for sizes >32px

### 7.3 Color & Contrast
- [ ] Primary text contrast ≥12:1 on white
- [ ] Secondary text contrast ≥7:1
- [ ] Tertiary text contrast ≥4.5:1
- [ ] No more than 5 categorical colors per view
- [ ] Semantic colors follow green=positive, red=negative pattern

### 7.4 Component Integrity
- [ ] All cards have consistent border-radius (12px)
- [ ] Card shadows use approved values (0 2px 8px rgba(15,23,42,0.06))
- [ ] Icons are actual SVGs, not placeholder text
- [ ] All interactive elements have hover states
- [ ] Grid gaps are consistent (16-24px)

### 7.5 Data Realism
- [ ] Values fall within plausible ranges for domain
- [ ] Both positive and negative deltas present (not all positive)
- [ ] Temporal trends align (if +growth, line slopes up)
- [ ] Units are consistent (K/M/B notation)
- [ ] At least one edge case or anomaly included

---

## 8. Complete Example: KPI Dashboard

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Dashboard</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', 'Inter', sans-serif;
            background: #F8FAFC;
            padding: 24px;
            font-feature-settings: "tnum" 1;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .dashboard-header {
            margin-bottom: 24px;
        }
        
        .dashboard-title {
            font-size: 28px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
        }
        
        .dashboard-subtitle {
            font-size: 14px;
            color: #64748B;
        }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }
        
        .kpi-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.06);
            border: 1px solid rgba(15,23,42,0.04);
        }
        
        .kpi-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: #64748B;
            margin-bottom: 8px;
        }
        
        .kpi-value {
            font-size: 42px;
            font-weight: 700;
            line-height: 1.0;
            letter-spacing: -1px;
            color: #0F172A;
            margin-bottom: 8px;
        }
        
        .kpi-delta {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        
        .kpi-delta.positive {
            background: rgba(5,150,105,0.12);
            color: #059669;
        }
        
        .kpi-delta.negative {
            background: rgba(220,38,38,0.12);
            color: #DC2626;
        }
        
        .kpi-sparkline {
            width: 100%;
            height: 32px;
        }
        
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        
        .card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(15,23,42,0.06);
        }
        
        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: #1E293B;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="dashboard-header">
            <h1 class="dashboard-title">Q4 2024 Performance</h1>
            <p class="dashboard-subtitle">Last updated: Oct 11, 2025 at 2:45 PM</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Revenue</div>
                <div class="kpi-value">$1.36M</div>
                <div class="kpi-delta positive">
                    <i data-lucide="trending-up" style="width: 12px; height: 12px;"></i>
                    <span>+12.4% vs PY</span>
                </div>
                <svg class="kpi-sparkline" viewBox="0 0 120 32">
                    <path d="M 0,24 Q 10,20 20,16 Q 30,12 40,14 Q 50,16 60,10 Q 70,4 80,6 Q 90,8 100,4 Q 110,0 120,2" 
                          fill="none" stroke="#3B82F6" stroke-width="2"/>
                    <path d="M 0,24 Q 10,20 20,16 Q 30,12 40,14 Q 50,16 60,10 Q 70,4 80,6 Q 90,8 100,4 Q 110,0 120,2 L 120,32 L 0,32 Z" 
                          fill="rgba(59,130,246,0.1)"/>
                </svg>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">Active Customers</div>
                <div class="kpi-value">2,847</div>
                <div class="kpi-delta positive">
                    <i data-lucide="trending-up" style="width: 12px; height: 12px;"></i>
                    <span>+8.3% vs LM</span>
                </div>
                <svg class="kpi-sparkline" viewBox="0 0 120 32">
                    <path d="M 0,28 L 20,26 L 40,22 L 60,24 L 80,18 L 100,16 L 120,14" 
                          fill="none" stroke="#10B981" stroke-width="2"/>
                    <path d="M 0,28 L 20,26 L 40,22 L 60,24 L 80,18 L 100,16 L 120,14 L 120,32 L 0,32 Z" 
                          fill="rgba(16,185,129,0.1)"/>
                </svg>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">Avg Order Value</div>
                <div class="kpi-value">$478</div>
                <div class="kpi-delta negative">
                    <i data-lucide="trending-down" style="width: 12px; height: 12px;"></i>
                    <span>-3.2% vs LM</span>
                </div>
                <svg class="kpi-sparkline" viewBox="0 0 120 32">
                    <path d="M 0,8 L 20,12 L 40,10 L 60,14 L 80,18 L 100,22 L 120,24" 
                          fill="none" stroke="#EF4444" stroke-width="2"/>
                    <path d="M 0,8 L 20,12 L 40,10 L 60,14 L 80,18 L 100,22 L 120,24 L 120,32 L 0,32 Z" 
                          fill="rgba(239,68,68,0.1)"/>
                </svg>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">Conversion Rate</div>
                <div class="kpi-value">3.42%</div>
                <div class="kpi-delta positive">
                    <i data-lucide="trending-up" style="width: 12px; height: 12px;"></i>
                    <span>+0.8% vs LM</span>
                </div>
                <svg class="kpi-sparkline" viewBox="0 0 120 32">
                    <path d="M 0,20 L 20,18 L 40,22 L 60,16 L 80,14 L 100,12 L 120,10" 
                          fill="none" stroke="#8B5CF6" stroke-width="2"/>
                    <path d="M 0,20 L 20,18 L 40,22 L 60,16 L 80,14 L 100,12 L 120,10 L 120,32 L 0,32 Z" 
                          fill="rgba(139,92,246,0.1)"/>
                </svg>
            </div>
        </div>
        
        <div class="content-grid">
            <div class="card">
                <h2 class="card-title">Revenue Trend</h2>
                <!-- Chart content here -->
            </div>
            
            <div class="card">
                <h2 class="card-title">Top Products</h2>
                <!-- Table content here -->
            </div>
        </div>
    </div>
    
    <script>
        lucide.createIcons();
    </script>
</body>
</html>
```

---

## 9. Quick Reference

### Design Token Summary
```
SPACING:     4px | 8px | 12px | 16px | 20px | 24px | 32px | 48px
TYPE SIZES:  10px | 11px | 12px | 13px | 14px | 16px | 18px | 20px | 24px | 32px | 36px | 42px | 48px | 56px
RADIUS:      3px (bars) | 8px (small) | 12px (cards) | 16px (chips)
SHADOWS:     0 2px 8px (cards) | 0 4px 16px (elevated) | 0 8px 24px (hover)
BORDERS:     1px solid #E2E8F0 (standard) | 2px solid #CBD5E1 (emphasized)
```

### Color Quick Pick
```
PRIMARY:   #3B82F6  SUCCESS:  #059669   DANGER:   #DC2626
SECONDARY: #8B5CF6  WARNING:  #D97706   INFO:     #0891B2
TEXT:      #0F172A  BORDERS:  #E2E8F0   BG:       #F8FAFC
```

### Chart Type Selection
```
Trends over time:        Line chart with area fill
Part-to-whole:           Donut chart with center text
Comparisons (few):       Column chart with labels
Comparisons (many):      Table with inline bars
Distribution:            Heatmap matrix
Progress to goal:        Gauge (semi-circle)
Ratings/quality:         Star display with count
Small datasets:          Small multiples grid
```

---

**Version**: 7.0 (October 2025)  
**Focus**: Universal patterns extracted from production dashboards  
**Philosophy**: Domain-agnostic, production-ready, mathematically precise