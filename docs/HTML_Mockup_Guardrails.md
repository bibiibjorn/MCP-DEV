# HTML Mockup Guardrails for Claude (MCP)

Purpose: When you ask Claude (or another MCP-enabled assistant) to generate a visualization or dashboard mockup, keep the rendering purely client-side (no server tools) but consistent, readable, and single-page. Use these constraints in your prompt and as acceptance criteria.

## Constraints (what Claude should follow)

- Single page only, designed to fit a 1920x1080 screen without vertical scroll when possible.
- Layout: centered max-width (1200–1400px) OR full-width when the application style or screenshot calls for it.
- Use only client-side HTML/CSS/JS. Prefer CDN links when libraries are used.
- No external images unless provided; inline small SVGs are fine.
- If a screenshot is provided, match layout structure (grid or flex sections, card arrangement, chart placement) and style (dark/light, spacing) as closely as feasible.
- Avoid heavy frameworks; Tailwind CSS via CDN is optional. Your own stylesheet or inline CSS is fine.
- Charts/components are optional and library-agnostic. You may use any lightweight client-side approach (or none). Include simple cards/tables if charts aren't necessary.
- Accessibility: sufficient color contrast, semantic tags, alt text where relevant.

## Minimal Page Shell

- Head includes meta viewport, CSS baseline (Tailwind CDN or a stylesheet), and chart library (if used)
- Body uses a structured layout via grid or flex; choose max-width container or full-width based on context
- Use data- attributes or embedded JSON for specs where helpful

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
