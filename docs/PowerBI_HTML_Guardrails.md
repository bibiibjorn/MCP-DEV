# Power BI HTML Visualization Guardrails (Profile: powerbi)

These guardrails target HTML visuals embedded in Power BI (iframe environment). They prioritize single-file delivery, accessibility, and performance while allowing full-width application layouts and custom CSS.

## Foundation & Architecture (CRITICAL)

- Single-file delivery: one HTML file with inline &lt;style&gt; and &lt;script&gt;. External dependencies must be CDN-based only.
- Responsive design: use grid/flex with min/max constraints; test at 1920x1080, 1366x768, and ultrawide (3840x1080).
- No browser storage APIs: do not use localStorage, sessionStorage, IndexedDB, or cookies.

## Visual Design & Theming (HIGH)

- Corporate color palette: define primary/secondary/accent and semantic roles; support light/dark themes.
- WCAG AA: minimum 4.5:1 contrast for normal text; 3:1 for large text and UI components.
- Financial formatting: Intl.NumberFormat for currency/percentages; negatives in parentheses.
- Typography: system font stack (Segoe UI/Tahoma/Verdana). H1 24–28px, H2 20–24px, H3 16–18px, Body 14px.

## Data Handling & Performance (CRITICAL)

- Data binding: use data- attributes and JS helpers; avoid inline event handlers.
- Virtual scrolling/pagination for 100+ rows.
- Debounce UI interactions (250–500ms) for search/filter/resize.

## Interactivity & UX (HIGH)

- Single state object; document shape; predictable updates.
- Loading overlay for >200ms operations; friendly error messages.
- Keyboard navigation: Tab/Enter/Space; visible focus indicators.
- Tooltips/context help for complex metrics; show formulas on hover.

## Power BI–Specific (CRITICAL)

- Cross-filter simulation: click-to-filter with visual feedback and filter context.
- Slicer panel design: grouped filters, active filter count.
- Drill-through emulation: hierarchical navigation with breadcrumb.
- Export CSV/Excel with formatted values and metadata.

## Testing & Validation (MEDIUM)

- Cross-browser: Edge/Chrome/Firefox with fallbacks.
- Data edge cases: null/undefined, zero, extreme numbers (±999T), empty sets.
- Performance: initial render <500ms; filter <200ms; sort <100ms for 1,000 rows.

## Layout Modes

- centered: classic dashboard; max-width ~1200–1400px, mx-auto, padding.
- full-width: application-style layout; custom CSS; no centering required.
- auto (default): heuristic suggestions only.

## MCP Usage

- help tool: pass profile=powerbi to receive these guardrails.
- validate tool: pass profile=powerbi and choose layout_mode (auto|centered|full-width). Validator returns suggestions and violations specific to Power BI.
