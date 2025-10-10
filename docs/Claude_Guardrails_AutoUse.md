# Make Claude auto-use HTML guardrails

Claude does not automatically call MCP tools unless its system/instructions tell it to. Use this pinned instruction to ensure the guardrails are always applied.

## Pinned instruction (copy/paste into Claude Desktop)

When the user asks for an HTML mockup, dashboard, or visualization:

1) Call the MCP tool "html: guardrails" to retrieve the current guardrails and checklist.
2) Generate a first HTML draft following those guardrails.
3) Call the MCP tool "html: validate mockup" with the full HTML string as the `html` argument. Optionally include `expected_theme` ("dark"|"light") and `layout_mode` ("auto"|"centered"|"full-width"). Use "full-width" when the app or screenshot is clearly full-bleed.
4) If `ok` is false or suggestions are present, revise the HTML and re-run validation up to 2 iterations.
5) Return only the final HTML (and a one-line summary of what changed if you iterated).

Example tool calls:

- Retrieve guardrails:
  - name: html: guardrails
  - args: {}

- Validate mockup:
  - name: html: validate mockup
  - args:
    - html: "&lt;html&gt;...full HTML...&lt;/html&gt;"
    - expected_theme: "light"
    - layout_mode: "full-width"
    - screenshot_colors: ["#0b5fff", "#101115", "#e6f0ff"]

Notes:

- The validator is library-agnostic: you can choose plain HTML/CSS/SVG/canvas or any lightweight library.
- Aim for a single-page, centered layout (~1200–1400px width), responsive typography, and accessible contrast.
- Prefer a clear hierarchy: title, optional summary/KPIs/cards, and well-spaced sections.
- If the style is a full-width app, set `layout_mode` to `full-width` so the validator doesn’t suggest centering.

## Responsive Layout Requirements

To ensure visuals fit the user's display (including Claude Desktop panels) and remain readable, follow these rules.

### Container Width Strategy

- Use a centered container with `max-width` and `margin: 0 auto` for most dashboards.
- Base the container width on the detected screen size rather than a single hardcoded value.
- Keep content to one page where possible; paginate or collapse long tables.

### Required Screen Breakpoints

1. 3440px+ (Ultrawide): 3-column layouts, max-width ≈ 3200px
2. 2560px–3439px (QHD Wide): 2-column optimized, max-width ≈ 2400px
3. 1920px–2559px (FHD): 2-column standard, max-width ≈ 1800px
4. 1440px–1919px (Standard): 2-column compact, max-width ≈ 1400px
5. <1440px (Compact): 1–2 columns, max-width ≈ 1200px

### CSS Media Query Pattern (example)

```css
@media screen and (min-width: 3440px) {
  .main-container { max-width: 3200px; }
  .grid-layout { grid-template-columns: repeat(3, 1fr); }
}
@media screen and (min-width: 2560px) and (max-width: 3439px) {
  .main-container { max-width: 2400px; }
}
@media screen and (min-width: 1920px) and (max-width: 2559px) {
  .main-container { max-width: 1800px; }
}
@media screen and (min-width: 1440px) and (max-width: 1919px) {
  .main-container { max-width: 1400px; }
}
@media screen and (max-width: 1439px) {
  .main-container { max-width: 1200px; }
}
```

### JavaScript Screen Detection (example)

```javascript
function optimizeLayout() {
  const screenWidth = window.innerWidth;
  const container = document.querySelector('.main-container');
  if (!container) return;
  if (screenWidth >= 3440) {
    container.style.maxWidth = '3200px';
  } else if (screenWidth >= 2560) {
    container.style.maxWidth = '2400px';
  } else if (screenWidth >= 1920) {
    container.style.maxWidth = '1800px';
  } else if (screenWidth >= 1440) {
    container.style.maxWidth = '1400px';
  } else {
    container.style.maxWidth = '1200px';
  }
}
optimizeLayout();
window.addEventListener('resize', optimizeLayout);
```

### Grid Adaptations

- KPI cards: 6 cols (ultrawide) → 4 cols (wide) → 2 cols (compact)
- Main content: 3 cols (ultrawide) → 2 cols (standard) → 1 col (mobile)

---

## Tool Parameters for Screen-Aware Validation

Both tools accept optional screen parameters. If omitted, the server will try to auto-detect the local screen size (Windows supported) and return structured `user_screen_info`.

### Retrieve guardrails with screen info

- name: html: guardrails
- args: {}

Optionally provide:

- screen_width: 3840
- screen_height: 1080
- detect_ultrawide: true

Response includes:

```json
{
  "guardrails": "...",
  "checklist": ["..."],
  "user_screen_info": {
    "width": 3840,
    "height": 1080,
    "is_ultrawide": true,
    "recommended_max_width": "3200px",
    "recommended_breakpoints": [1440, 1920, 2560, 3440]
  }
}
```

### Validate mockup with screen info

- name: html: validate mockup
- args:
  - html: "&lt;html&gt;...full HTML...&lt;/html&gt;"
  - layout_mode: "auto"

Optional parameters (auto-detected on Windows if omitted):

- screen_width: 3840
- screen_height: 1080
- detect_ultrawide: true

The validator will suggest container widths close to the recommended value when `layout_mode` is not `full-width`.

---

## Restricted Color Palette (Professional)

Rule: Use a maximum of 2–3 main colors that harmonize with the theme background. Avoid rainbow charts or excessive color variation.

Primary principle: Charts and visuals should use monochromatic shades of the main theme color (typically blue/slate) with subtle variations in opacity or saturation. Only use accent colors (green/red) for semantic meaning (positive/negative variance).

### Core Colors (Max 3)

```css
:root {
  /* PRIMARY - Main theme color (blue/slate family) */
  --primary: #3498db;           /* Main interactive blue */
  --primary-dark: #2c7cb0;      /* Darker shade for hover/active */
  --primary-light: #5dade2;     /* Lighter shade for backgrounds */
  --primary-alpha-10: rgba(52, 152, 219, 0.1);
  --primary-alpha-20: rgba(52, 152, 219, 0.2);
  --primary-alpha-50: rgba(52, 152, 219, 0.5);

  /* SEMANTIC - Only for positive/negative indicators */
  --success: #2ecc71;           /* Positive variance ONLY */
  --danger:  #e74c3c;           /* Negative variance ONLY */

  /* NEUTRALS - Background and text (not counted in 3-color limit) */
  --bg-primary: #ffffff;
  --bg-secondary: #f8f9fa;
  --bg-tertiary: #ecf0f1;
  --bg-dark: #2c3e50;
  --bg-dark-secondary: #34495e;

  --text-primary: #2c3e50;
  --text-secondary: #7f8c8d;
  --text-tertiary: #95a5a6;
  --text-inverse: #ffffff;

  --border-color: #bdc3c7;
}
```

### Avoid: Rainbow Charts

```css
/* DON'T USE multiple bright unrelated colors for categories */
/* Example of an anti-pattern */
/* #3498db, #e74c3c, #f39c12, #9b59b6, #1abc9c, #e67e22 */
```

### Use: Monochromatic Progression

```css
/* Shades of primary */
.chart-bar-1 { background: var(--primary); }
.chart-bar-2 { background: var(--primary-dark); }
.chart-bar-3 { background: var(--primary-light); }
.chart-bar-4 { background: var(--primary-alpha-50); }

/* Or single color with varying opacity */
.metric-1 { background: rgba(52, 152, 219, 1.0); }
.metric-2 { background: rgba(52, 152, 219, 0.8); }
.metric-3 { background: rgba(52, 152, 219, 0.6); }
.metric-4 { background: rgba(52, 152, 219, 0.4); }
```

### Chart-Specific Color Rules

Bar charts

```css
/* Single-color bars (preferred) */
.bar-chart .bar {
  background: var(--primary);
  border-radius: 4px 4px 0 0;
}
/* Monochromatic variation (if categories needed) */
.bar-chart .bar.current-year { background: var(--primary); }
.bar-chart .bar.prior-year   { background: var(--primary-alpha-50); }
.bar-chart-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}
```

Waterfall charts

```css
.waterfall-segment.asset    { background: var(--primary); }
.waterfall-segment.liability{ background: var(--danger); }
.waterfall-segment.equity   { background: var(--primary-light); }
```

Pie/Donut charts

```css
.pie-slice-1 { fill: #3498db; }
.pie-slice-2 { fill: #5dade2; }
.pie-slice-3 { fill: #2c7cb0; }
.pie-slice-4 { fill: rgba(52, 152, 219, 0.6); }
.pie-slice-5 { fill: rgba(52, 152, 219, 0.4); }
```

Line charts

```css
.line-chart .line-primary {
  stroke: var(--primary);
  stroke-width: 3px;
}
.line-chart .line-comparison {
  stroke: var(--primary-alpha-50);
  stroke-width: 2px;
  stroke-dasharray: 5 5;
}
/* Area fill via gradient stops (pseudo-code) */
/* stop-color: var(--primary-alpha-20) at 0%;
   stop-color: var(--primary-alpha-10) at 100%; */
```

KPI cards/metrics

```css
.kpi-card {
  background: #ffffff;
  border-left: 3px solid var(--primary);
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}
.kpi-value { color: var(--text-primary); }
.kpi-variance.positive { color: var(--success); }
.kpi-variance.negative { color: var(--danger); }
```

Theme-matched backgrounds

```css
/* Dark theme */
body[data-theme="dark"] { background: #2c3e50; }
body[data-theme="dark"] .chart-container {
  background: #34495e;
  border: 1px solid #4a5f7f;
}
body[data-theme="dark"] .card {
  background: #34495e;
  color: #ecf0f1;
}
/* Light theme */
body[data-theme="light"] { background: #f8f9fa; }
body[data-theme="light"] .chart-container {
  background: #ffffff;
  border: 1px solid #e0e0e0;
}
```

### Color Selection Decision Tree

1) Is this a variance/change indicator?
   - YES → Use semantic colors (green/red)
   - NO  → Continue

2) Does the chart need multiple colors?
   - NO → Use single primary color
   - YES → Continue

3) Is there semantic meaning (asset vs liability)?
   - YES → Primary for positive, Danger for negative
   - NO  → Use monochromatic shades of primary

### Testing Checklist

- No rainbow palettes; max 3 core colors used
- Semantic colors only for positive/negative
- Neutral backgrounds and subtle borders
- Consistent primary across visuals
- Accessible contrast maintained

## Why this is needed

MCP servers expose tools, but the model only calls them if guided to. The prompt in this doc ensures Claude follows the guardrails workflow every time.
