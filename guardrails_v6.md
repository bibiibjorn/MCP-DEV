# Power BI Visual Mockup Guardrails v7.2

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

### Guardrail Workflow Checklist
- Call `html: guardrails` and store `guardrail_token` (expires in 15 minutes).
- Complete domain research (Section 0.3) before drafting visuals.
- Use approved icon libraries (Lucide, Bootstrap Icons, Heroicons inline) — no placeholders.
- Apply the spacing/layout tokens and card architecture patterns from this guide.
- Validate charts with Section 7.4 and Section 16 precision rules before hand-off.
- Run `html: validate mockup` (with token) at least twice, clearing every violation.
- Deliver a single responsive HTML file with inline CSS and CDN-only dependencies.
- Document data assumptions, palette, icon library, guardrail token, and validation score in the HTML comment block.

---
## 10. Guardrail Workflow & Enforcement

1. **Call `html: guardrails` before drafting anything.**  
   - The tool returns the full guardrail text plus a `guardrail_token`.  
   - Tokens expire after 15 minutes or if a new guardrail read occurs. Re-fetch when in doubt.
2. **Include the `guardrail_token` when calling `html: validate mockup`.**  
   - Validation fails without a matching token. This prevents "I already know the rules" shortcuts.
   - Treat the token like a session receipt: persist it in memory, recycle it between iterations, refresh it after expiry.
3. **Reference the returned checklist.** Mark each item as satisfied before handing work back to the user.
4. **Claude Desktop usage:** even if the user says "skip the MCP", remind them that the server will reject validation without the token. Always route mockup work through the MCP tools so the guardrail audit trail remains intact.

---

## 11. Execution Workflow (160 IQ) (160 IQ Edition)

1. **Frame the product story.** Capture business question, audience, cadence (daily vs quarterly), and delivery device (desktop, wallboard, tablet). Refuse to design blindly.

2. **Research the domain** (follow the protocol in Section 0.3).
   - Confirm the audience, cadence, and critical decisions driving the mockup.
   - List canonical visuals and metrics gathered from existing solutions or SME feedback.
   - Write down semantic colors and comparison baselines before drafting so every chart reinforces the same story.
3. **Mirror real data.** Derive representative ranges, seasonality, and edge cases. If the user has no numbers, infer plausible values from industry benchmarks and explain the logic.

4. **Draft information architecture first.** Block out sections using ASCII wireframes or semantic descriptions before touching pixels. Validate narrative, not colors.

5. **Select layout archetype.** Default: 12-column grid at 1200-1400px max width for desktop, golden-ratio split (62/38) for primary vs secondary panes, 5% header band, 3% footer.

6. **Apply the visual hierarchy system.** Assign hierarchy scores (1-5) to every element; check that larger score implies larger type, higher contrast, higher z-elevation, and placement closer to top-left.

7. **Codify design tokens.** Establish spacing scale (4/8/12/16/24/32/48/64), color palette, and typography map before writing HTML.

8. **Draft HTML + CSS in a single file.** Inline critical CSS, load external resources via CDN, avoid build tooling. **Use actual icons, not placeholders.**

9. **Run `html: validate mockup` with the current token.** Inspect violations, update, rerun. Minimum two passes: one after structural draft, one before delivery.

10. **Deliverable wrap-up.** Provide final HTML, summary of guardrail compliance, any residual risks, and suggestions for hand-off or next iteration.

---

## 12. Visual Hierarchy Doctrine

- **Signal stacking equation:** Visual Weight = Size + Contrast + Saturation + Proximity to Origin + Elevation. If two elements share the same content importance, their weight signature must match.

- **Hierarchy scoring (UPDATED for light mode)**:
  - Level 1 (Hero KPI): 44-56px, weight 700-800, color `#0F172A` (dark slate), subtle shadow, anchored top-left.
  - Level 2 (Primary trend or driver): 28-32px, weight 600-700, sits immediately to the right of Level 1 or beneath it with shared baseline.
  - Level 3 (Section titles): 18-22px, weight 600, color `#1E293B`, uppercase optional, rely on spacing not underline.
  - Level 4 (Card labels / axis titles): 12-14px, weight 500, color `#64748B` (60% opacity equivalent).
  - Level 5 (Metadata / footnotes): 10-12px, weight 400, color `#94A3B8`. Keep contrast >= 4.5:1 relative to background.

- **Rule of contrast:** consecutive hierarchy levels must differ by at least two of the five dimensions (size, contrast, saturation, position, elevation). Never rely on size alone.

- **Gestalt enforcement:** align baselines, maintain consistent gutter widths (multiples of 8px), and ensure dominant diagonals point toward the call-to-action metric.

---

## 13. Supplemental Grid & Layout Guidance

- **Canvas width targets:**  
  - <1440px monitor -> max content width 1200px (centered).  
  - 1440-1919px -> 1400px.  
  - 1920-2559px -> 1800px.  
  - >=2560px -> 2400px; only go to 3200px for 3440px ultrawide and command-center dashboards.  
  Capture the user screen guess using `html: guardrails` return payload and respect `recommended_max_width`.

- **Macro layout archetypes:**  
  - **Golden split (62/38)** when one narrative leads.  
  - **Triptych (33/33/33)** for balanced KPI sets; ensure equal gutters.  
  - **Temporal focus** (top band = pacing, middle = explanatory, bottom = diagnostic) for executive readouts.

- **Spacing scale:** Base unit 8px. Use 4px for micro adjustments sparingly. Do not invent 17px or 23px gaps.

- **Elevation map (UPDATED for light mode)**:
  - Base cards: shadow `0 2px 8px rgba(15,23,42,0.06)` plus `border-radius: 12px`.
  - Elevated cards: `0 4px 16px rgba(15,23,42,0.08)`.
  - Hover/focus: `0 8px 24px rgba(15,23,42,0.12)`.
  - Background: subtle gradient `linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)` optional.

---

## 14. Supplemental Typography Ladder

```css
Font stack: 'Segoe UI', 'Inter', 'DM Sans', 'SF Pro Display', -apple-system, sans-serif;

.display-hero  { font-size: 56px; font-weight: 800; letter-spacing: -1.5px; line-height: 1.0; color: #0F172A; }
.display-primary { font-size: 42px; font-weight: 700; letter-spacing: -1.0px; line-height: 1.05; color: #0F172A; }
.h1 { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2; color: #1E293B; }
.h2 { font-size: 20px; font-weight: 600; letter-spacing: 0px; line-height: 1.3; color: #334155; }
.h3 { font-size: 16px; font-weight: 600; line-height: 1.4; color: #475569; }
.body { font-size: 14px; font-weight: 400; line-height: 1.5; color: #334155; }
.label { font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: #64748B; }
.micro { font-size: 10px; font-weight: 400; letter-spacing: 0.5px; line-height: 1.4; color: #94A3B8; }
```

- Use negative tracking for any text >=36px to avoid wide gaps.
- For uppercase labels, apply 0.8-1.2px positive tracking.
- Maintain consistent baseline grids; mix `font-size` and `line-height` so combined height equals multiples of the 4px module.

---

## 15. Color Contrast & Gradient Rules

### 6.1 Base Neutrals (Light Mode - DEFAULT)
```css
--bg-primary: #FFFFFF;           /* Main background */
--bg-secondary: #F8FAFC;         /* Secondary background */
--bg-tertiary: #F1F5F9;          /* Sidebar/panel background */

--surface-primary: #FFFFFF;      /* Card surface */
--surface-elevated: #FFFFFF;     /* Elevated card with stronger shadow */

--border-light: #F1F5F9;         /* Subtle borders */
--border-medium: #E2E8F0;        /* Standard borders */
--border-strong: #CBD5E1;        /* Emphasized borders */

--text-primary: #0F172A;         /* Headlines, KPIs */
--text-secondary: #334155;       /* Body text */
--text-tertiary: #64748B;        /* Labels, metadata */
--text-disabled: #94A3B8;        /* Disabled/placeholder */

--shadow-sm: 0 1px 2px rgba(15,23,42,0.04);
--shadow-md: 0 2px 8px rgba(15,23,42,0.06);
--shadow-lg: 0 4px 16px rgba(15,23,42,0.08);
--shadow-xl: 0 8px 24px rgba(15,23,42,0.12);
```

### 6.2 Semantic Colors (Universal)
```css
/* Primary Actions - Blue */
--primary-50: #EFF6FF;
--primary-100: #DBEAFE;
--primary-500: #3B82F6;  /* Main blue */
--primary-600: #2563EB;  /* Hover blue */
--primary-700: #1D4ED8;  /* Active blue */

/* Success/Positive - Green */
--success-50: #F0FDF4;
--success-100: #DCFCE7;
--success-500: #22C55E;  /* Main green */
--success-600: #16A34A;  /* Darker green */

/* Danger/Negative - Red */
--danger-50: #FEF2F2;
--danger-100: #FEE2E2;
--danger-500: #EF4444;   /* Main red */
--danger-600: #DC2626;   /* Darker red */

/* Warning - Amber */
--warning-50: #FFFBEB;
--warning-100: #FEF3C7;
--warning-500: #F59E0B;  /* Main amber */
--warning-600: #D97706;  /* Darker amber */

/* Info - Cyan */
--info-50: #ECFEFF;
--info-100: #CFFAFE;
--info-500: #06B6D4;     /* Main cyan */
--info-600: #0891B2;     /* Darker cyan */
```

### 6.3 Contextual Color Mapping (Domain Agnostic)
- Define a palette per project that maps colors to data families (products, regions, statuses) and document the legend inline.
- Keep semantic signals universal: green for positive/progress, red for negative/risk, amber for caution, blue for focus elements.
- When a brand palette is provided, translate brand primaries into the semantic roles above while preserving contrast ratios from Section 6.4.
- For multi-series visuals, order hues from cool to warm (blue -> green -> amber -> red -> purple) so readers can rank importance at a glance.
- Validate palettes in grayscale or color-blind simulators to ensure charts remain readable without hue information.


### 6.4 Contrast Targets
- Primary text on white: >= 12:1 (aim for `#0F172A`)
- Secondary text: >= 7:1 (aim for `#334155`)
- Tertiary text: >= 4.5:1 (aim for `#64748B`)
- Data lines against card: >= 4.5:1
- Sparkline fill area: 10-15% opacity of line color

### 6.5 Gradient Strategy (Light Mode)
```css
/* Subtle card background gradients */
background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);

/* Header gradients (use sparingly) */
background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);

/* Chart area fills */
fill: linear-gradient(180deg, rgba(59,130,246,0.15) 0%, rgba(59,130,246,0.02) 100%);
```

---

## 16. Chart Rendering Precision

### 7.1 The Mathematics of Visual Accuracy

**160 IQ PRINCIPLE**: Every chart must be mathematically correct and visually verifiable.

**Donut Chart Geometry**:
```
Given:
- Center (cx, cy)
- Outer radius R
- Inner radius r
- Percentage p

Arc sweep angle theta = (p / 100) x 360 deg 
Start angle = 0 deg  (or cumulative from previous segments)

SVG Path for segment:
1. Move to outer arc start: (cx + Rxcos(start), cy + Rxsin(start))
2. Large arc flag = 1 if theta > 180 deg , else 0
3. Arc to outer end: A R,R 0 [large-arc-flag],1 (end_x, end_y)
4. Line to inner arc end
5. Arc back to inner start: A r,r 0 [large-arc-flag],0 (inner_start_x, inner_start_y)
6. Close path Z

CRITICAL: Verify angles sum to 360 deg  (+/-0.1 deg  tolerance for rounding)
```
**Practical Debugging Checklist (Donut Charts):**
1. Convert each percentage to degrees (p * 3.6) and confirm the running total ends at exactly 360 deg before drawing any SVG paths.
2. In browser DevTools, enable the SVG path outline (or add temporary stroke='black' fill='none') to see whether arcs close cleanly and inner radius stays concentric.
3. Test with a symmetric case (25/25/25/25) to confirm the math yields four identical slices; adjust large-arc flags only when theta > 180 deg .
4. If a slice renders as a blob, log the start and end coordinates for both outer and inner arcs to verify they share the same center and radius values.


**Example - Donut Chart 40% / 60% split**:
```svg
<!-- Center: 150,150; Outer: 80px; Inner: 50px -->

<!-- Segment 1: 40% = 144 deg  -->
<path d="M 150,70 
         A 80,80 0 0,1 214.8,180.4
         L 194.3,171.5
         A 50,50 0 0,0 150,100
         Z" 
      fill="#3B82F6"/>

<!-- Segment 2: 60% = 216 deg  -->
<path d="M 214.8,180.4
         A 80,80 0 1,1 150,70
         L 150,100
         A 50,50 0 1,0 194.3,171.5
         Z"
      fill="#22C55E"/>
```

**Bar Chart Precision**:
```
Given:
- Chart height H
- Y-axis range [min, max]
- Data value v

Bar height h = ((v - min) / (max - min)) x H
Bar y-position = H - h (SVG y-axis is inverted)

CRITICAL: All bars must align to same baseline
```

**Line Chart Smoothing**:
```
Use quadratic Bezier curves (Q command) for natural smoothing:

Q control_x,control_y end_x,end_y

Control point = midpoint between current and next point + vertical offset
Offset = 0.2 x (next_y - current_y) for subtle curve

AVOID: Sharp L (line) commands unless data truly has discrete jumps
```

### 7.2 Visual Accuracy Checklist
Before finalizing any chart, verify:

- [ ] **Percentages sum to 100%** (+/-0.5% tolerance for display rounding)
- [ ] **Bar heights proportional** to data values (measure pixel heights)
- [ ] **Line chart slopes** match data delta directions
- [ ] **Legend colors** exactly match chart segment colors
- [ ] **Axis labels** align with gridlines (+/-2px tolerance)
- [ ] **Data labels** positioned consistently (all inside or all outside bars)
- [ ] **Gradients render** smoothly without banding
- [ ] **Rounded corners** use same radius (typically 3-8px for bars)
- [ ] **Hover states** defined but non-functional (static mockup)

### 7.3 Common Chart Mistakes and Fixes

**[x] WRONG - Donut looks like a blob**:
```svg
<!-- Incorrectly calculated arc paths -->
<path d="M 160,140 L 160,155 A 65,65 0 0,1 196.7,267.3 ..." />
```

**[check] CORRECT - Precise mathematical arcs**:
```svg
<!-- Use online SVG arc calculator or derive from formulas above -->
<path d="M 160,80 A 80,80 0 0,1 232.4,184.7 L 206.5,175.9 A 50,50 0 0,0 160,100 Z"/>
```

**[x] WRONG - Bars don't align to baseline**:
```svg
<!-- Inconsistent y-positions -->
<rect x="100" y="110" height="90" />
<rect x="150" y="105" height="95" />  <!-- Baseline drift! -->
```

**[check] CORRECT - All bars share baseline**:
```svg
<!-- All bars end at y=200 -->
<rect x="100" y="110" height="90" />  <!-- 200 - 90 = 110 [check] -->
<rect x="150" y="105" height="95" />  <!-- 200 - 95 = 105 [check] -->
```



### 7.4 Donut Chart Standards

#### 7.4.1 Mathematical precision
```javascript
function getPoint(cx, cy, radius, angleDeg) {
    const angleRad = (angleDeg - 90) * Math.PI / 180; // start at 12 o'clock
    return {
        x: cx + radius * Math.cos(angleRad),
        y: cy + radius * Math.sin(angleRad)
    };
}

const path = `
    M outerStartX,outerStartY
    A outerR,outerR 0 ${largeArcFlag ? 1 : 0},1 outerEndX,outerEndY
    L innerEndX,innerEndY
    A innerR,innerR 0 ${largeArcFlag ? 1 : 0},0 innerStartX,innerStartY
    Z
`;
```
- Set `largeArcFlag = 1` when the sweep exceeds 180 degrees, otherwise `0`.
- Calculate coordinates to two decimals; round only when presenting to stakeholders.
- Keep the inner radius between 50 percent and 65 percent of the outer radius (thickness 35 percent to 50 percent).
- Verify math: percentages must total 100 percent (+/-0.1 percent) and arc angles 360 degrees (+/-0.1 degrees).

#### 7.4.2 Visual design
- Leave enough aperture for two lines of center text (value and subtitle using hierarchy levels 1 and 5).
- Use subtle drop shadows (opacity 0.06 to 0.10) for depth; avoid heavy glows.
- Choose palettes from Section 6.3 semantics. Recommended sequences: cool (cyan -> blue -> indigo -> purple) or warm (yellow -> orange -> red -> magenta) with at least 3:1 contrast between neighbors.
- Reserve status colors (green/amber/red/gray) for health metrics; keep the mapping consistent across the dashboard.

#### 7.4.3 Labels and leader lines
```svg
<g class="donut-label">
    <path class="leader-line"
          d="M midX,midY L anchorX,anchorY L labelX,labelY"
          stroke="#94A3B8" stroke-width="1.5" fill="none" opacity="0.6" />
    <text x="labelX" y="labelY" class="label-value">562.2K</text>
    <text x="labelX" y="labelY + 16" class="label-percent">(30.8%)</text>
</g>
```
- Use two-segment leader lines: a radial segment from the arc midpoint, then a horizontal run to the label.
- Flip `text-anchor` based on quadrant so labels never overlap the donut.
- Format values with K/M/B suffixes and percentages in parentheses on a second line.
- Keep leader strokes 1 to 1.5 px at 0.5 to 0.6 opacity so they stay legible but unobtrusive.

#### 7.4.4 Validation routine
- Step through segments computing start and end angles; ensure each new segment begins where the previous one ended.
- Toggle an outline (temporary `stroke="black" fill="none"`) during QA to spot gaps or overlaps.
- Test a symmetric dataset (25/25/25/25) to confirm slice equality; adjust arc flags if any slice crosses the 180-degree threshold.
- Log outer and inner coordinates while debugging; mismatched centers indicate math errors.

#### 7.4.5 Donut checklist
- [ ] Percentages sum to 100 percent and arcs cover 360 degrees.
- [ ] Inner radius is between 0.50 and 0.65 of the outer radius; center text fits comfortably.
- [ ] Palette follows semantic rules and adjacent segments pass contrast checks.
- [ ] External labels with leader lines are legible, aligned, and color-matched to their segments.
- [ ] Center value and subtitle use the proper typography hierarchy and reinforce the dashboard story.
- [ ] Donut uses `viewBox` sizing so it scales without fixed pixel widths.

---

## 17. Component Standards

### 8.1 Executive KPI Strip
- Use 3-4 cards max per row
- Layout inside card: label (Level 4), main metric (Level 1), delta chip with **actual icon** (not placeholder)
- Delta chip styling: 
  ```css
  .delta-chip {
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 4px;
  }
  .delta-chip.positive {
      background: rgba(34,197,94,0.12);
      color: #16A34A;
  }
  .delta-chip.negative {
      background: rgba(239,68,68,0.12);
      color: #DC2626;
  }
  ```
- Delta copy format: icon + value + unit + reference (example: [triangle-up] 5.1% vs PY). Place the percent sign immediately after the number, then the comparison label, and right-align the chip on the KPI card so it stays clear of the sparkline.
- Ensure the sparkline baseline uses the same unit cadence as the delta. If the delta compares against prior year, the sparkline must show that same time range with matching axis labels.

- Include sparkline or micro bar spanning full width with 8px rounded corners

### 8.2 Trend Panels
- Provide 3 annotations: most recent value, trailing average, outlier callout
- Axis: left axis with `font-size: 11px`, right axis optional for dual-scale but avoid unless justified
- Include data point markers only when necessary (e.g., monthly). For dense series, rely on area fill
- **Use smooth Bezier curves** for line charts, not jagged L commands

### 8.3 Comparison Tables
- Header row: 13px, 600 weight, color `#64748B`
- Row height: 44px desktop, 36px compact
- Keep stripes subtle: `background: rgba(15,23,42,0.02)` on alternating rows
- Incorporate inline bars or dots for quick scanning
- Freeze first column using `position: sticky; left: 0;` if table scrolls horizontally

### 8.4 Diagnostic Drill
- Provide waterfall or variance decomposition with absolute numbers and percentages
- Add contextual footnote clarifying assumptions or data vintage
- Use consistent color coding: positive changes green, negative changes red

### 8.5 Narrative Sidebar
- Use 14px body copy, 1.6 line-height, bullet list for top insights
- Provide explicit "Next experiment" or "Decision" statement to avoid vague commentary
- Include icons for visual anchors ([check] success, [warning] warning, [info] info)

---

## 18. Data Realism Heuristics

- **Ranges:** KPIs must fall within plausible ranges (e.g., revenue $1.2M-$1.5M, growth +/-25%)
- **Variance:** Include both positive and negative deltas; pure positive dashboards look fabricated
- **Temporal logic:** If growth is positive month-over-month, trend lines must slope upward. Ensure YoY vs MoM labels align with data
- **Correlation checks:** When showing two related metrics (e.g., revenue vs profit), ensure correlation coefficient implied by chart angle is plausible
- **Balance sheet constraint**: Total Assets MUST equal Total Equity + Total Liabilities (to the penny)
- **Units consistency:** Express currency at two significant figures, abbreviate with `M` or `K`, show basis points for small percentages
- **Shock testing:** Introduce at least one edge-case data point (e.g., anomaly spike) and annotate it. Real-world data is messy

---

## 19. Accessibility and QA

- Support keyboard focus order even though mockup is static; demonstrate by styling `:focus-visible`
- Ensure all color meaning is duplicated via shape or icon (e.g., arrow + color)
- Provide text alternatives: include hidden `<span class="sr-only">` summarizing chart takeaway
- Check responsiveness at 768px breakpoint: stack cards vertically, preserve 24px gutters
- Confirm no layout shift when fonts load; preload fonts via `link rel="preload"` if using hosted files
- **Icon accessibility**: Include `aria-label` on decorative icons or use `aria-hidden="true"` if redundant with adjacent text

---

## 20. Deliverable Constraints

- Single HTML file, UTF-8, max 250 KB when minified (target 150 KB)
- Inline CSS preferred; limit external resources to fonts/icons via CDN (Google Fonts, Lucide, Bootstrap Icons)
- **Icon libraries allowed**:
  - Lucide: `<script src="https://unpkg.com/lucide@latest"></script>`
  - Bootstrap Icons: `<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css">`
  - Heroicons: Inline SVG only
- No frameworks requiring build steps (React, Vue). Tailwind via CDN acceptable if purge style applied
- No JavaScript except:
  - Icon library initialization (Lucide: `lucide.createIcons()`)
  - Lightweight charting (ApexCharts, Chart.js) via CDN if complex charts needed
- No data fetch calls, localStorage, cookies, or analytics scripts
- Include metadata: `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<meta name="description">`
- Comment block at top documenting:
  ```html
  <!--
  Dashboard: [Name]
  Domain: [Balance Sheet / P&L / Portfolio / etc.]
  Data assumptions: [ranges, variance logic]
  Color palette: [primary, secondary, semantic colors]
  Icon library: [Lucide / Bootstrap Icons / etc.]
  Guardrail token: [token from MCP call]
  Validation score: [score from html: validate mockup]
  -->
  ```

---

## 21. Failure Triggers (Automatic Rejection)

- Guardrail token missing, expired, or not matching last `html: guardrails` call
- **Using placeholder icons** (text like "[hamburger]" for menu is acceptable, but no `<div>[icon]</div>` placeholders)
- **Chart geometry errors**: percentages don't sum to 100%, bar heights not proportional, arcs visually incorrect
- **Dark theme used without explicit request** (default must be light mode)
- Layout widths exceeding recommended maximum for detected screen without explicit justification
- Non-CDN scripts or stylesheets (relative paths, local files)
- Tables over 120 rows with no pagination or virtualization note
- Missing meta viewport, DOCTYPE, or `<html lang="...">`
- KPIs with zero decimals when trends imply precision, or percentages without `%`
- Color contrast failures (<4.5:1) for text or data encodings
- **Domain research not performed**: Balance sheet without standard ratios, P&L without gross margin, etc.
- Copy-paste of Power BI export (revealed by `data-vis-id` attributes) without customization

---

## 22. Guardrail Compliance Checklist

- [ ] Called `html: guardrails`, stored latest `guardrail_token`, read updates
- [ ] **Researched domain norms** (data definitions, standard visuals, comparison baselines)
- [ ] **Confirmed light mode as default** (unless user requested dark theme)
- [ ] **Selected actual icon library** (Lucide, Bootstrap Icons, or Heroicons inline)
- [ ] Captured business goal, audience, and delivery surface
- [ ] Chosen layout archetype and documented spacing scale
- [ ] Locked typography ladder and color palette (light mode colors)
- [ ] Verified data realism (ranges, variance, correlations, anomalies)
- [ ] **Verified chart geometry** (percentages sum to 100%, bars proportional, arcs correct)
- [ ] Applied hierarchy scoring (1-5) across all elements
- [ ] Ensured accessibility rules: contrast, focus states, semantic HTML, icon labels
- [ ] **No placeholder icons** - all icons are actual SVG or icon font glyphs
- [ ] Ran `html: validate mockup` with token twice; resolved violations and suggestions
- [ ] Final HTML is single file, CDN-only dependencies, responsive at 768px
- [ ] Provided summary of risks, next experiment, and guardrail compliance when handing off

---

## 23. The 160 IQ Standard

Your mockup should be so precise that:

1. **A data analyst** can reconcile every number with the source without extra clarification.
2. **A product designer** would sign off on it for production with zero visual changes.
3. **A front-end engineer** can lift exact spacing, colors, and component specs directly from the file.
4. **A decision maker** could present it to any audience with confidence that the story is accurate and clear.
5. **A subject-matter expert** immediately recognizes the metrics, units, and comparisons as credible for the request.

**If any of those peers would hesitate to use it as-is, keep iterating.**

---

**Version History**:
- v7.2 (2025): Synced latest v7 design system into MCP guardrail workflow (cards, grids, components)
- v7.1 (2025): Merged v7 layout/card enhancements with v6 guardrail workflow and validation rigor
- v7.0 (2025): Introduced universal card architecture, grid system, and icon integration
- v6.0 (2025): Added light mode default, actual icon requirements, domain research protocol, chart geometry precision
- v5.0: Added guardrail token enforcement, enhanced validation
- v4.0: Baseline professional standards

**Remember: Excellence is the only acceptable standard.**

---
**Version**: 7.2 (merged v6 token workflow with v7 layout patterns)  
**Focus**: Universal Power BI mockup system with enforced MCP workflows  
**Philosophy**: Production-grade visuals backed by guardrail automation and mathematical proof

