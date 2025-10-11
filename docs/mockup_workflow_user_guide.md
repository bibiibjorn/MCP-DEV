# Power BI Mockup System — User Guide

Welcome! This walkthrough explains how to use the self-improving Power BI mockup system that now ships with the MCP PowerBi Finvision server. It is written for first-time users and covers everything from running the MCP tools to keeping the component library up to date.

---

## 1. What You Get
- **Component Library** → production-ready HTML snippets in `templates/components/` (29 components across KPI cards, tables, charts, controls, layouts, navigation, and status widgets).
- **Base Shell** → shared styling in `templates/base/dashboard_base.css` and a layout template at `templates/base/dashboard_base.html`.
- **Example Dashboard** → `templates/examples/product_margin.html` to see a complete dark-mode page assembled from the library.
- **Automation Tools** → MCP tools (`mockup: list components`, `mockup: generate html`, `mockup: analyze screenshots`) plus guardrail tooling (`html: guardrails`, `html: validate mockup`).
- **Validation Scripts** → `validation/component_validator.py` and `validation/screenshot_analyzer.py` for deeper offline checks.
- **Learning Loop** → screenshot drop folders at `assets/screenshots` and an audit log in `docs/screenshot_analysis_log.md`.

---

## 2. One-Time Prerequisites
1. **Activate the MCP server** (same as before). From your IDE, launch the MCP PowerBi Finvision server so Claude (or any MCP client) can connect over stdio.
2. **Install Python dependencies** if you plan to run the local validators (optional but recommended):
   ```powershell
   pip install -r requirements.txt
   ```
3. **Familiarize yourself with guardrails** – the canonical spec lives at `guardrails/guardrails_v6.md`; the component library reference is at `guardrails/component_library_v1.0.md`.

---

## 3. Directory Cheat Sheet
| Location | Purpose |
|----------|---------|
| `templates/base/dashboard_base.html` | Base HTML shell with placeholders for navigation, controls, content. |
| `templates/base/dashboard_base.css` | Global dark-mode styling shared across dashboards. |
| `templates/components/` | All reusable building blocks grouped by category. |
| `templates/examples/product_margin.html` | Full sample dashboard assembled from the library. |
| `docs/component_metadata.json` | Machine-readable metadata describing every component. |
| `docs/component_catalog.md` | Human-readable quick reference for the component library. |
| `docs/implementation_guide.md` | Technical integration instructions (Claude/Desktop workflows). |
| `docs/screenshot_analysis_log.md` | Running log of screenshot analyses (auto-appended by the tool). |
| `assets/screenshots/incoming/` | Drop screenshots here for analysis. |
| `assets/screenshots/processed/` | Automatically populated with analyzed screenshots. |
| `validation/component_validator.py` | HTML validator script. |
| `validation/screenshot_analyzer.py` | Local screenshot analysis script. |
| `server/handlers/mockup_library.py` | Implementation of the new mockup MCP tools. |

---

## 4. MCP Tool Overview
All tools can be triggered from Claude (or any MCP-aware IDE) via `call_tool`.

| Friendly Name | Canonical | What it does |
|---------------|-----------|--------------|
| `mockup: list components` | `mockup_list_components` | Returns component metadata (optionally filtered by category). |
| `mockup: generate html` | `mockup_generate_html` | Assembles a finished HTML page using the base template + selected components. |
| `mockup: analyze screenshots` | `mockup_analyze_screenshots` | Scans screenshots, appends analysis to the log, and suggests components. |
| `html: guardrails` | `help_html_mockup_guardrails` | Loads the guardrail spec and issues the required `guardrail_token`. |
| `html: validate mockup` | `validate_html_mockup` | Validates HTML against guardrails_v6 (requires the token). |

> **Tip:** The friendly names above are what you type inside your MCP client. The canonical names are what the server uses internally; you can reference either.

---

## 5. End-to-End Workflow (Designing a New Dashboard)
### Step 1 — Gather Requirements
Collect user goals or screenshots. If you have images, copy them into `assets/screenshots/incoming/` right away (see Section 6).

### Step 2 — Grab Guardrails
From Claude, run:
```
call_tool("html: guardrails", {})
```
Save the `guardrail_token` from the JSON response. It expires in 15 minutes, so fetch a fresh one for each work session.

### Step 3 — Explore Components
```
call_tool("mockup: list components", {})
```
Optional filters:
```json
{ "category": "kpi_cards" }
```
Use `docs/component_catalog.md` alongside the returned metadata to pick the right pieces.

### Step 4 — Generate HTML
Provide a list of component IDs (see `docs/component_metadata.json` for the exact IDs). Example:
```json
{
  "components": [
    "nav_dark_sidebar",
    "control_date_range",
    "control_button_segmented",
    "layout_kpi_strip",
    "kpi_standard",
    "kpi_nested",
    "chart_column_combo",
    "table_kpi_matrix"
  ],
  "title": "Margin Command Center",
  "heading": "Executive Margin Overview",
  "subtitle": "Highlights for Q3 FY25"
}
```
Run in Claude:
```
call_tool("mockup: generate html", { ... })
```
Copy the `html` string from the response to a local file (for example `exports/mockup_margin.html`).

### Step 5 — Validate
```
call_tool("html: validate mockup", {
  "guardrail_token": "<token-from-step-2>",
  "html": "<paste-your-html>",
  "expected_theme": "dark",
  "expected_library": "lucide"
})
```
Resolve any `violations` or `suggestions`. Re-run until the `ok` flag is true. Aim for a high score.

### Step 6 — Optional Local Checks
Run the offline validator for extra assurance (see Section 7). This is useful if you edit the HTML by hand outside the MCP workflow.

### Step 7 — Deliver
Provide the validated HTML file to stakeholders. Include the guardrail validation score in your handoff notes.

---

## 6. Feeding the System with Screenshots
1. Drop PNG/JPG files into `assets/screenshots/incoming/`. The analyzer scans this folder automatically; you can still organise into subfolders if you pass a custom path.
2. Tell Claude (or your MCP client):
   ```
   call_tool("mockup: analyze screenshots", { "auto_update_library": true })
   ```
   - Optional overrides if you keep screenshots elsewhere:
     ```json
     {
       "folder": "assets/screenshots/incoming",
       "log_path": "docs/screenshot_analysis_log.md"
     }
     ```
3. The tool will:
   - Return JSON summarising theme, palette, grid hints, and component suggestions.
   - Append a Markdown entry to `docs/screenshot_analysis_log.md`.
   - Move processed images into `assets/screenshots/processed/` (time-stamped for traceability).
   - **Auto-generate new component variants** (one per detected feature) inside `templates/components/auto_generated/`, update `docs/component_metadata.json`, and append notes to `docs/component_catalog.md` and `guardrails/component_library_v1.0.md`.
4. Review the newly generated components when convenient. They are ready for immediate use, but you can edit the HTML/CSS if you want to polish them further.

---

## 7. Local Validation & Analysis Scripts
> The MCP tool already validates palettes and creates components automatically. Use these scripts only when you need offline/batch workflows.

### HTML Component Validator
```
python validation/component_validator.py exports/mockup_margin.html --metadata docs/component_metadata.json
```
Outputs:
- Score (0–100)
- Lists of `violations` (must fix) and `warnings` (nice to fix)
- Notes about missing CSS tokens, accessibility gaps, etc.

### Screenshot Analyzer (CLI)
```
python validation/screenshot_analyzer.py assets/screenshots/incoming/latest_dashboard.png --metadata docs/component_metadata.json
```
Writes JSON to stdout with the same info the MCP tool returns (theme, palette, grid, component suggestions). Use the `--metadata` flag to keep suggestions aligned with the current library.

To process a whole folder at once:
```
python validation/screenshot_analyzer.py assets/screenshots/incoming --metadata docs/component_metadata.json
```

---

## 8. What the Auto-Updater Produces
When `auto_update_library` is enabled, the analyzer creates everything for you:

- **Component HTML** → saved under `templates/components/auto_generated/auto_<type>_<timestamp>.html` with a unique component anchor.
- **Metadata entry** → appended to `docs/component_metadata.json` (including id, template path, description, and guardrail reminders).
- **Catalog note** → added to the bottom of `docs/component_catalog.md`, listing component id, source screenshot, theme, and palette.
- **Guardrail awareness** → an extra bullet in `guardrails/component_library_v1.0.md` so future guardrail revisions recognise the new pieces.

> If you want to refine a generated component, edit the HTML/CSS file directly. The metadata already points to it, so any improvements go live instantly.

---

## 9. Troubleshooting
| Issue | Fix |
|-------|-----|
| `mockup: generate html` complains about missing component anchors | Check that the HTML snippet contains `<!-- component: your-id -->` before the markup and that the ID matches `docs/component_metadata.json`. |
| Guardrail validation fails due to missing token | Always call `html: guardrails` within 15 minutes of validation. Tokens expire automatically. |
| Lucide icons not rendering | Ensure the generated HTML contains `<script src="https://unpkg.com/lucide@latest"></script>` (built into the base template). |
| Screenshot tool reports “No screenshots found” | Confirm the file extension is `.png`, `.jpg`, or `.jpeg` and that the file is in `assets/screenshots/incoming/` (not nested deeper unless you pass a custom folder). |
| Component validator warns about spacing | Align CSS padding/margin/gap values to multiples of 4 pixels (8px preferred). |
| Need more component examples | Refer to `templates/examples/product_margin.html` or generate your own and store under `templates/examples/`. |

---

## 10. Quick Reference Commands
- List components:  
  `call_tool("mockup: list components", {})`
- Generate HTML:  
  `call_tool("mockup: generate html", { "components": ["nav_dark_sidebar", ...] })`
- Analyze screenshots:  
  `call_tool("mockup: analyze screenshots", {})`
- Validate HTML with token:  
  `call_tool("html: validate mockup", { "guardrail_token": "...", "html": "..." })`
- Local HTML validation:  
  `python validation/component_validator.py <file> --metadata docs/component_metadata.json`
- Local screenshot analysis:  
  `python validation/screenshot_analyzer.py <image-or-folder> --metadata docs/component_metadata.json`

---

## 11. Staying Organized
- Save generated HTML files under `exports/` with meaningful names (`exports/<project>_mockup_v1.html`).
- After each screenshot analysis run, review `docs/screenshot_analysis_log.md` and capture any useful design insights in your component catalog or project documentation.
- Commit the updated docs (`docs/…`) and templates (`templates/…`) with clear messages so the evolution of the library stays traceable.

You now have a complete, guardrailed mockup system that learns from your input. Use the MCP tools for day-to-day work, fall back to the Python scripts for batch validation, and keep feeding it screenshots to make every dashboard iteration smarter. Happy building!
