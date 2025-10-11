<!-- Deprecated pointer: The canonical mockup/visualization guardrails live in enhanced_pbi_mockup_guardrails.md at the repository root. -->
# HTML Mockup Guardrails (Deprecated)

Please use `enhanced_pbi_mockup_guardrails.md` as the single source of truth for mockup rules, SVG chart requirements, color palette, and responsive container guidance. This file is retained only to avoid breaking old links.

## Example Template Hints

- Title bar with page title and optional timestamp
- KPI grid (3 cards per row on desktop, 1 per row on mobile)
- One time-series chart and one categorical chart
- Optional compact table or financial summary list

## Screenshot Matching

When a screenshot is supplied:

- Identify visual regions (header, KPI row, main charts, tables)
- Mirror spacing and proportions (not exact pixels)
- Use the same theme (dark/light), accent colors, and typography scale
- Accept minor font and icon differences; prioritize structure and density

## Acceptance Checklist

- Single HTML file renders without build steps
- No console errors; scripts limited to CDN imports
- Page fits within a typical 1080p viewport (or gracefully scrolls < 1.5 screens)
- If screenshot provided: recognizable structural similarity

---

## Critical Chart Visualization Rules (SVG-first)

These augment the general guardrails with chart-specific requirements for financial dashboards.

## Rule 1: Use SVG for Data Visualizations

- Never simulate bars/lines with CSS heights/widths (e.g., `style="height: 75%"`).
- Use SVG with explicit coordinates so values map to pixels predictably.

Wrong (CSS-based bar):

```html
<div class="bar" style="height: 75%"></div>
```

Correct (SVG with values):

```html
<svg viewBox="0 0 1000 300">
  <rect x="100" y="155" width="50" height="95" fill="#5a7a9a"/>
  <text x="125" y="145">38.2M</text>
  <!-- Add axes, grid lines, etc. as needed -->
  <line x1="80" y1="250" x2="970" y2="250" stroke="#e0e0e0"/>
  <line x1="80" y1="200" x2="970" y2="200" stroke="#f0f0f0"/>
  <line x1="80" y1="150" x2="970" y2="150" stroke="#f0f0f0"/>
```

## Rule 2: Combo Charts Must Show Both Dimensions

- Bars (solid) for the primary metric (e.g., current period).
- Dashed line for comparison (e.g., prior period) with point markers.
- Include value labels and grid lines; include a legend.

Template:

```html
<svg class="combo-chart" viewBox="0 0 1000 300">
  <!-- Grid lines -->
  <line x1="80" y1="250" x2="970" y2="250" stroke="#e0e0e0"/>

  <!-- Bars (current year) -->
  <rect x="100" y="155" width="50" height="95" fill="#5a7a9a"/>

  <!-- Line (prior year) - dashed -->
  <polyline points="125,180 205,170 285,165"
            fill="none" stroke="#7f8c8d" stroke-width="2" stroke-dasharray="5,5"/>
  <circle cx="125" cy="180" r="4" fill="#7f8c8d"/>

  <!-- Labels -->
  <text x="125" y="145" text-anchor="middle" font-size="11">38.2M</text>
  <text x="125" y="270" text-anchor="middle" font-size="11">JAN 25</text>
</svg>
```

## Rule 3: Waterfall Charts Require Connectors

- Start total (full bar), floating increments/decrements, dashed connectors, end total.
- Value labels above, category labels below.

Template:

```html
<svg viewBox="0 0 1000 300">
  <rect x="100" y="50" width="80" height="200" fill="#5a7a9a"/>
  <text x="140" y="40">20.57M</text>
  <line x1="180" y1="250" x2="220" y2="250" stroke="#bdc3c7" stroke-dasharray="3,3"/>
  <rect x="220" y="185" width="60" height="65" fill="#b8997a"/>
  <text x="250" y="175">0.48M</text>
  <!-- ...more segments... -->
  <rect x="900" y="50" width="60" height="200" fill="#5a7a9a"/>
  <text x="930" y="40">21.81M</text>
</svg>
```

## Rule 4: Chart Legends Are Mandatory

- Legend must match colors and encodings (solid vs dashed).

```html
<div class="chart-legend">
  <div class="legend-item">
    <span class="legend-color" style="background:#5a7a9a;width:12px;height:12px;display:inline-block;border-radius:2px"></span>
    <span>Actual 2025</span>
  </div>
  <div class="legend-item">
    <span class="legend-color" style="border-top:2px dashed #7f8c8d;width:16px;display:inline-block;vertical-align:middle"></span>
    <span>Actual 2023 (2YA)</span>
  </div>
</div>
```

## Rule 5: Use Realistic Data Ranges

- Avoid perfectly linear sequences; prefer realistic business patterns.

```javascript
const assetTrends = [
  { month: 'JAN', current: 38.2, prior: 36.8 },
  { month: 'FEB', current: 40.1, prior: 37.5 },
  { month: 'MAR', current: 41.8, prior: 38.9 },
  { month: 'APR', current: 43.5, prior: 40.2 },
  { month: 'MAY', current: 45.2, prior: 41.7 } // Peak
];
```

## Rule 6: Financial Chart Color Palette (SVG)

```css
:root {
  --chart-primary: #5a7a9a;        /* Blue-grey bars */
  --chart-primary-light: #7a9aba;  /* Lighter variant */
  --chart-secondary: #c4c4c4;      /* Grey bars/forecast */
  --chart-line: #7f8c8d;           /* Dashed line */
  --chart-positive: #2ecc71;       /* Green increases */
  --chart-negative: #e74c3c;       /* Red decreases */
  --chart-neutral:  #b8997a;       /* Tan */
  --chart-grid: #e0e0e0;           /* Grid */
  --chart-connector: #bdc3c7;      /* Connectors */
}
```

## Rule 7: Proper SVG ViewBox Usage

Always set a `viewBox` and scale via CSS.

```html
<svg class="responsive-chart" viewBox="0 0 1000 300"></svg>
<style>
.responsive-chart { width: 100%; height: auto; }
</style>
```

## Rule 8: Text Positioning in SVG

Use `text-anchor` for alignment.

```html
<text x="500" y="20" text-anchor="middle">Title</text>
<text x="980" y="100" text-anchor="end">€45.2M</text>
<text x="20"  y="100" text-anchor="start">Label</text>
```

## Chart Validation Checklist

Before generation

- Identify chart types, dimensions, and palette.

During generation

- SVG with viewBox; grid lines; value labels; axes; connectors for waterfalls; legend with correct encodings.

After generation

- Realistic data, legend matches encoding, readable text (11–14px), colors follow financial palette, responsive scaling, consistent number formatting (e.g., 38.2M).

Common mistakes to avoid and their fixes are documented above.

## Prompt Snippet (copy/paste)

"""
You are generating a single HTML file for a dashboard mockup. Constraints:

- Single page, fits within a 1920x1080 screen (target content width 1200–1400px unless a full-width app is preferred)
- CSS baseline: Tailwind CDN OR your own stylesheet/inline CSS
- Do not assume any specific charting library. Use plain HTML/CSS/SVG/canvas or a lightweight library if it clearly helps.
- Include a clear hierarchy (title, optional KPIs/cards) and well-spaced sections. Charts/tables are optional.
- If I provide a screenshot, match its layout and theme closely
Return only valid HTML. No external build steps.
"""

## Tips

- Use a consistent spacing scale (e.g., Tailwind gap-4, p-6)

- Include comments marking sections to help iterative editing
