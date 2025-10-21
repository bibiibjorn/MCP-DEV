"""
Model Diff Report Generator V2 - Complete Rewrite
Modern, clean HTML layout that shows EVERYTHING
"""

import logging
import json
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import difflib

logger = logging.getLogger(__name__)


class ModelDiffReportV2:
    """
    Brand new HTML report generator with modern design.
    Shows EVERY type of change clearly.
    """

    def __init__(self, diff_result: Dict[str, Any], tmdl1_data: Optional[Dict[str, Any]] = None, tmdl2_data: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator.

        Args:
            diff_result: Comparison diff result
            tmdl1_data: Full TMDL structure for model 1 (optional, for TMDL tabs)
            tmdl2_data: Full TMDL structure for model 2 (optional, for TMDL tabs)
        """
        self.diff = diff_result
        self.summary = diff_result.get('summary', {})
        self.tmdl1_data = tmdl1_data
        self.tmdl2_data = tmdl2_data

    def generate_html(self, output_path: str) -> str:
        """Generate complete HTML report."""
        logger.info(f"Generating HTML report v2: {output_path}")

        html_content = self._build_html()

        # Write to file
        Path(output_path).write_text(html_content, encoding='utf-8')
        logger.info(f"Report generated: {output_path}")

        return output_path

    def _escape(self, text: str) -> str:
        """HTML escape."""
        if text is None:
            return ""
        return html.escape(str(text))

    def _build_html(self) -> str:
        """Build complete HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Power BI Model Comparison - {self.summary.get('model1_name')} vs {self.summary.get('model2_name')}</title>
    {self._get_styles()}
</head>
<body>
    <div class="container">
        {self._build_header()}
        {self._build_summary()}
        {self._build_tabs()}
        <div class="tab-content">
            <div id="tab-diff" class="tab-pane active">
                {self._build_tables_section()}
                {self._build_measures_section()}
                {self._build_relationships_section()}
                {self._build_roles_section()}
                {self._build_perspectives_section()}
            </div>
            <div id="tab-tmdl-full" class="tab-pane">
                {self._build_tmdl_full_view()}
            </div>
            <div id="tab-tmdl-changes" class="tab-pane">
                {self._build_tmdl_changes_view()}
            </div>
        </div>
    </div>
    {self._get_scripts()}
</body>
</html>
"""

    def _build_header(self) -> str:
        """Build page header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""
        <div class="header">
            <h1>Power BI Model Comparison</h1>
            <div class="models">
                <div class="model-badge old">{self._escape(self.summary.get('model1_name', 'Model 1'))}</div>
                <span class="vs">vs</span>
                <div class="model-badge new">{self._escape(self.summary.get('model2_name', 'Model 2'))}</div>
            </div>
            <div class="timestamp">{timestamp}</div>
        </div>
        """

    def _build_summary(self) -> str:
        """Build summary dashboard."""
        changes = self.summary.get('changes_by_category', {})
        total = self.summary.get('total_changes', 0)

        return f"""
        <div class="summary-card">
            <h2>Summary</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total Changes</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value added">{changes.get('tables_added', 0)}</div>
                    <div class="stat-label">Tables Added</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value removed">{changes.get('tables_removed', 0)}</div>
                    <div class="stat-label">Tables Removed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value modified">{changes.get('tables_modified', 0)}</div>
                    <div class="stat-label">Tables Modified</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value added">{changes.get('measures_added', 0)}</div>
                    <div class="stat-label">Measures Added</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value removed">{changes.get('measures_removed', 0)}</div>
                    <div class="stat-label">Measures Removed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value modified">{changes.get('measures_modified', 0)}</div>
                    <div class="stat-label">Measures Modified</div>
                </div>
            </div>
        </div>
        """

    def _build_tables_section(self) -> str:
        """Build tables changes section."""
        tables = self.diff.get('tables', {})
        added = tables.get('added', [])
        removed = tables.get('removed', [])
        modified = tables.get('modified', [])

        if not (added or removed or modified):
            return ""

        items_html = []

        # Added tables
        for table in added:
            items_html.append(self._build_table_added(table))

        # Removed tables
        for table in removed:
            items_html.append(self._build_table_removed(table))

        # Modified tables
        for table in modified:
            items_html.append(self._build_table_modified(table))

        return f"""
        <div class="section">
            <h2>Tables ({len(added)} added, {len(removed)} removed, {len(modified)} modified)</h2>
            <div class="changes-list">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_table_added(self, table: Dict) -> str:
        """Build HTML for added table."""
        name = table.get('name', 'Unknown')
        cols = table.get('columns_count', 0)
        meas = table.get('measures_count', 0)

        return f"""
        <div class="change-card added">
            <div class="change-header">
                <span class="badge added">+ ADDED</span>
                <strong class="item-name">{self._escape(name)}</strong>
                <span class="meta">{cols} columns, {meas} measures</span>
            </div>
        </div>
        """

    def _build_table_removed(self, table: Dict) -> str:
        """Build HTML for removed table."""
        name = table.get('name', 'Unknown')
        cols = table.get('columns_count', 0)
        meas = table.get('measures_count', 0)

        return f"""
        <div class="change-card removed">
            <div class="change-header">
                <span class="badge removed">- REMOVED</span>
                <strong class="item-name">{self._escape(name)}</strong>
                <span class="meta">{cols} columns, {meas} measures</span>
            </div>
        </div>
        """

    def _build_table_modified(self, table: Dict) -> str:
        """Build HTML for modified table."""
        name = table.get('name', 'Unknown')
        changes = table.get('changes', {})

        # Build content for all types of changes
        content_parts = []

        # Column changes
        col_changes = changes.get('columns', {})
        if col_changes:
            content_parts.append(self._build_column_changes(col_changes))

        # Measure changes
        meas_changes = changes.get('measures', {})
        if meas_changes:
            content_parts.append(self._build_measure_changes(meas_changes))

        content_html = ''.join(content_parts) if content_parts else '<div class="no-details">No detailed changes available</div>'

        return f"""
        <div class="change-card modified">
            <div class="change-header clickable" onclick="this.parentElement.classList.toggle('expanded')">
                <span class="badge modified">~ MODIFIED</span>
                <strong class="item-name">{self._escape(name)}</strong>
                <span class="expand-icon">▼</span>
            </div>
            <div class="change-body">
                {content_html}
            </div>
        </div>
        """

    def _build_column_changes(self, col_changes: Dict) -> str:
        """Build column changes section."""
        added = col_changes.get('added', [])
        removed = col_changes.get('removed', [])
        modified = col_changes.get('modified', [])

        if not (added or removed or modified):
            return ""

        items = []

        # Added columns
        for col in added:
            items.append(f"""
                <div class="sub-item added">
                    <span class="badge mini added">+</span>
                    <strong>{self._escape(col.get('name'))}</strong>
                    <span class="type">{self._escape(col.get('data_type', 'Unknown'))}</span>
                </div>
            """)

        # Removed columns
        for col in removed:
            items.append(f"""
                <div class="sub-item removed">
                    <span class="badge mini removed">-</span>
                    <strong>{self._escape(col.get('name'))}</strong>
                    <span class="type">{self._escape(col.get('data_type', 'Unknown'))}</span>
                </div>
            """)

        # Modified columns
        for col in modified:
            col_name = col.get('name', 'Unknown')
            col_changes_detail = col.get('changes', {})
            change_desc = ", ".join([f"{k}: {v.get('from')} → {v.get('to')}" for k, v in col_changes_detail.items()])
            items.append(f"""
                <div class="sub-item modified">
                    <span class="badge mini modified">~</span>
                    <strong>{self._escape(col_name)}</strong>
                    <span class="changes-detail">{self._escape(change_desc)}</span>
                </div>
            """)

        return f"""
        <div class="subsection">
            <h4>Columns ({len(added)} added, {len(removed)} removed, {len(modified)} modified)</h4>
            <div class="sub-items-list">
                {''.join(items)}
            </div>
        </div>
        """

    def _build_measure_changes(self, meas_changes: Dict) -> str:
        """Build measure changes section within a table."""
        added = meas_changes.get('added', [])
        removed = meas_changes.get('removed', [])
        modified = meas_changes.get('modified', [])

        if not (added or removed or modified):
            return ""

        items = []

        # Added measures
        for meas in added:
            expr = (meas.get('expression', '') or '')
            items.append(f"""
                <div class="sub-item added">
                    <span class="badge mini added">+</span>
                    <strong>{self._escape(meas.get('name'))}</strong>
                    <div class="dax-full"><pre>{self._escape(expr)}</pre></div>
                </div>
            """)

        # Removed measures
        for meas in removed:
            expr = (meas.get('expression', '') or '')
            items.append(f"""
                <div class="sub-item removed">
                    <span class="badge mini removed">-</span>
                    <strong>{self._escape(meas.get('name'))}</strong>
                    <div class="dax-full"><pre>{self._escape(expr)}</pre></div>
                </div>
            """)

        # Modified measures
        for meas in modified:
            meas_name = meas.get('name', 'Unknown')
            meas_changes_detail = meas.get('changes', {})

            # Build change summary
            change_parts = []
            for key in meas_changes_detail.keys():
                if key == 'expression':
                    change_parts.append('DAX modified')
                else:
                    change_parts.append(key)

            change_summary = ", ".join(change_parts)

            items.append(f"""
                <div class="sub-item modified">
                    <span class="badge mini modified">~</span>
                    <strong>{self._escape(meas_name)}</strong>
                    <span class="changes-detail">{self._escape(change_summary)}</span>
                </div>
            """)

        return f"""
        <div class="subsection">
            <h4>Measures ({len(added)} added, {len(removed)} removed, {len(modified)} modified)</h4>
            <div class="sub-items-list">
                {''.join(items)}
            </div>
        </div>
        """

    def _build_measures_section(self) -> str:
        """Build top-level measures section."""
        measures = self.diff.get('measures', {})
        added = measures.get('added', [])
        removed = measures.get('removed', [])
        modified = measures.get('modified', [])

        if not (added or removed or modified):
            return ""

        items_html = []

        # Group by table
        for meas in added:
            items_html.append(self._build_measure_item(meas, 'added'))

        for meas in removed:
            items_html.append(self._build_measure_item(meas, 'removed'))

        for meas in modified:
            items_html.append(self._build_measure_item(meas, 'modified'))

        return f"""
        <div class="section collapsible-section">
            <h2 class="section-header clickable" onclick="this.parentElement.classList.toggle('expanded')">
                <span class="expand-icon">▼</span>
                Measures (All Tables) - {len(added)} added, {len(removed)} removed, {len(modified)} modified
            </h2>
            <div class="section-body">
                <div class="changes-list">
                    {''.join(items_html)}
                </div>
            </div>
        </div>
        """

    def _build_measure_item(self, meas: Dict, change_type: str) -> str:
        """Build individual measure item."""
        name = meas.get('name', 'Unknown')
        table = meas.get('table', 'Unknown')
        folder = meas.get('display_folder', '')

        # Build metadata badges
        metadata_badges = f'<span class="table-badge">{self._escape(table)}</span>'
        if folder:
            metadata_badges += f'<span class="folder-badge">{self._escape(folder)}</span>'

        if change_type == 'added':
            expr = meas.get('expression', '')
            return f"""
            <div class="change-card added">
                <div class="change-header">
                    <span class="badge added">+ ADDED</span>
                    <strong class="item-name">{self._escape(name)}</strong>
                    {metadata_badges}
                </div>
                <div class="dax-box added">
                    <pre>{self._escape(expr)}</pre>
                </div>
            </div>
            """

        elif change_type == 'removed':
            expr = meas.get('expression', '')
            return f"""
            <div class="change-card removed">
                <div class="change-header">
                    <span class="badge removed">- REMOVED</span>
                    <strong class="item-name">{self._escape(name)}</strong>
                    {metadata_badges}
                </div>
                <div class="dax-box removed">
                    <pre>{self._escape(expr)}</pre>
                </div>
            </div>
            """

        else:  # modified
            changes = meas.get('changes', {})
            expr_change = changes.get('expression', {})
            expr_from = expr_change.get('from', '')
            expr_to = expr_change.get('to', '')

            # Other metadata changes
            metadata_html = []
            for key, value in changes.items():
                if key != 'expression' and isinstance(value, dict):
                    metadata_html.append(f"""
                        <div class="metadata-row">
                            <strong>{self._escape(key)}:</strong>
                            <span class="old">{self._escape(str(value.get('from', '')))}</span>
                            <span>→</span>
                            <span class="new">{self._escape(str(value.get('to', '')))}</span>
                        </div>
                    """)

            metadata_section = ""
            if metadata_html:
                metadata_section = f'<div class="metadata-changes">{"".join(metadata_html)}</div>'

            dax_section = ""
            if expr_from or expr_to:
                dax_section = f"""
                <div class="dax-comparison">
                    <div class="dax-side before">
                        <div class="dax-label">BEFORE</div>
                        <pre>{self._escape(expr_from)}</pre>
                    </div>
                    <div class="dax-side after">
                        <div class="dax-label">AFTER</div>
                        <pre>{self._escape(expr_to)}</pre>
                    </div>
                </div>
                """

            return f"""
            <div class="change-card modified">
                <div class="change-header clickable" onclick="this.parentElement.classList.toggle('expanded')">
                    <span class="badge modified">~ MODIFIED</span>
                    <strong class="item-name">{self._escape(name)}</strong>
                    {metadata_badges}
                    <span class="expand-icon">▼</span>
                </div>
                <div class="change-body">
                    {metadata_section}
                    {dax_section}
                </div>
            </div>
            """

    def _build_relationships_section(self) -> str:
        """Build relationships section."""
        rels = self.diff.get('relationships', {})
        added = rels.get('added', [])
        removed = rels.get('removed', [])
        modified = rels.get('modified', [])

        if not (added or removed or modified):
            return ""

        items_html = []

        # Added relationships
        for rel in added:
            items_html.append(self._build_relationship_item(rel, 'added'))

        # Removed relationships
        for rel in removed:
            items_html.append(self._build_relationship_item(rel, 'removed'))

        # Modified relationships
        for rel in modified:
            items_html.append(self._build_relationship_item(rel, 'modified'))

        return f"""
        <div class="section">
            <h2>Relationships ({len(added)} added, {len(removed)} removed, {len(modified)} modified)</h2>
            <div class="changes-list">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_relationship_item(self, rel: Dict, change_type: str) -> str:
        """Build individual relationship item."""
        from_col = rel.get('from_column', 'Unknown')
        to_col = rel.get('to_column', 'Unknown')
        from_card = rel.get('from_cardinality', '')
        to_card = rel.get('to_cardinality', '')
        is_active = rel.get('is_active', True)
        cross_filter = rel.get('cross_filtering_behavior', '')

        # Parse table names from column references (format: 'Table'[Column])
        from_parts = from_col.split('[')
        to_parts = to_col.split('[')
        from_display = f"{from_parts[0].strip(chr(39))}.{from_parts[1].rstrip(']')}" if len(from_parts) > 1 else from_col
        to_display = f"{to_parts[0].strip(chr(39))}.{to_parts[1].rstrip(']')}" if len(to_parts) > 1 else to_col

        rel_name = f"{from_display} → {to_display}"

        meta_parts = []
        if from_card and to_card:
            meta_parts.append(f"{from_card}:{to_card}")
        if is_active is False:
            meta_parts.append("Inactive")
        if cross_filter:
            meta_parts.append(f"Filter: {cross_filter}")

        meta = " | ".join(meta_parts) if meta_parts else ""

        if change_type == 'added':
            return f"""
            <div class="change-card added">
                <div class="change-header">
                    <span class="badge added">+ ADDED</span>
                    <strong class="item-name">{self._escape(rel_name)}</strong>
                    {f'<span class="meta">{self._escape(meta)}</span>' if meta else ''}
                </div>
            </div>
            """
        elif change_type == 'removed':
            return f"""
            <div class="change-card removed">
                <div class="change-header">
                    <span class="badge removed">- REMOVED</span>
                    <strong class="item-name">{self._escape(rel_name)}</strong>
                    {f'<span class="meta">{self._escape(meta)}</span>' if meta else ''}
                </div>
            </div>
            """
        else:  # modified
            changes = rel.get('changes', {})
            change_desc = []
            for key, value in changes.items():
                if isinstance(value, dict) and 'from' in value and 'to' in value:
                    change_desc.append(f"{key}: {value['from']} → {value['to']}")

            change_text = ", ".join(change_desc) if change_desc else "Modified"

            return f"""
            <div class="change-card modified">
                <div class="change-header">
                    <span class="badge modified">~ MODIFIED</span>
                    <strong class="item-name">{self._escape(rel_name)}</strong>
                    {f'<span class="meta">{self._escape(meta)}</span>' if meta else ''}
                    <div class="changes-detail" style="margin-left: auto;">{self._escape(change_text)}</div>
                </div>
            </div>
            """

    def _build_roles_section(self) -> str:
        """Build roles section."""
        roles = self.diff.get('roles', {})
        added = roles.get('added', [])
        removed = roles.get('removed', [])
        modified = roles.get('modified', [])

        if not (added or removed or modified):
            return ""

        items_html = []

        for role in added:
            role_name = role.get('name', 'Unknown')
            items_html.append(f"""
            <div class="change-card added">
                <div class="change-header">
                    <span class="badge added">+ ADDED</span>
                    <strong class="item-name">{self._escape(role_name)}</strong>
                </div>
            </div>
            """)

        for role in removed:
            role_name = role.get('name', 'Unknown')
            items_html.append(f"""
            <div class="change-card removed">
                <div class="change-header">
                    <span class="badge removed">- REMOVED</span>
                    <strong class="item-name">{self._escape(role_name)}</strong>
                </div>
            </div>
            """)

        for role in modified:
            role_name = role.get('name', 'Unknown')
            changes = role.get('changes', {})
            change_desc = ", ".join([f"{k} changed" for k in changes.keys()])
            items_html.append(f"""
            <div class="change-card modified">
                <div class="change-header">
                    <span class="badge modified">~ MODIFIED</span>
                    <strong class="item-name">{self._escape(role_name)}</strong>
                    <span class="meta">{self._escape(change_desc)}</span>
                </div>
            </div>
            """)

        return f"""
        <div class="section">
            <h2>Roles ({len(added)} added, {len(removed)} removed, {len(modified)} modified)</h2>
            <div class="changes-list">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_perspectives_section(self) -> str:
        """Build perspectives section."""
        perspectives = self.diff.get('perspectives', {})
        added = perspectives.get('added', [])
        removed = perspectives.get('removed', [])
        modified = perspectives.get('modified', [])

        if not (added or removed or modified):
            return ""

        items_html = []

        for persp in added:
            persp_name = persp.get('name', 'Unknown')
            items_html.append(f"""
            <div class="change-card added">
                <div class="change-header">
                    <span class="badge added">+ ADDED</span>
                    <strong class="item-name">{self._escape(persp_name)}</strong>
                </div>
            </div>
            """)

        for persp in removed:
            persp_name = persp.get('name', 'Unknown')
            items_html.append(f"""
            <div class="change-card removed">
                <div class="change-header">
                    <span class="badge removed">- REMOVED</span>
                    <strong class="item-name">{self._escape(persp_name)}</strong>
                </div>
            </div>
            """)

        for persp in modified:
            persp_name = persp.get('name', 'Unknown')
            changes = persp.get('changes', {})
            change_desc = ", ".join([f"{k} changed" for k in changes.keys()])
            items_html.append(f"""
            <div class="change-card modified">
                <div class="change-header">
                    <span class="badge modified">~ MODIFIED</span>
                    <strong class="item-name">{self._escape(persp_name)}</strong>
                    <span class="meta">{self._escape(change_desc)}</span>
                </div>
            </div>
            """)

        return f"""
        <div class="section">
            <h2>Perspectives ({len(added)} added, {len(removed)} removed, {len(modified)} modified)</h2>
            <div class="changes-list">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_tabs(self) -> str:
        """Build tab navigation."""
        return """
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('tab-diff')">
                <span class="tab-icon">📊</span>
                Diff Summary
            </button>
            <button class="tab-button" onclick="switchTab('tab-tmdl-full')">
                <span class="tab-icon">📄</span>
                Full TMDL (Side-by-Side)
            </button>
            <button class="tab-button" onclick="switchTab('tab-tmdl-changes')">
                <span class="tab-icon">🔍</span>
                TMDL Changes Only
            </button>
        </div>
        """

    def _build_tmdl_full_view(self) -> str:
        """Build side-by-side full TMDL view."""
        if not self.tmdl1_data or not self.tmdl2_data:
            return """
            <div class="tmdl-section">
                <div class="info-message">
                    <p>TMDL data not available. This view requires full TMDL structures from both models.</p>
                    <p>The comparison was performed but TMDL text data was not included.</p>
                </div>
            </div>
            """

        # Generate TMDL text from structures
        from core.tmdl_text_generator import generate_tmdl_text

        try:
            tmdl1_text = generate_tmdl_text(self.tmdl1_data)
            tmdl2_text = generate_tmdl_text(self.tmdl2_data)
        except Exception as e:
            logger.error(f"Failed to generate TMDL text: {e}")
            return f"""
            <div class="tmdl-section">
                <div class="info-message error">
                    <p>Error generating TMDL text: {self._escape(str(e))}</p>
                </div>
            </div>
            """

        # Split into lines for line-by-line rendering
        lines1 = tmdl1_text.split('\n')
        lines2 = tmdl2_text.split('\n')

        # Build line-numbered HTML
        left_html = self._build_tmdl_lines(lines1, 'model1', len(lines1))
        right_html = self._build_tmdl_lines(lines2, 'model2', len(lines2))

        model1_name = self.summary.get('model1_name', 'Model 1')
        model2_name = self.summary.get('model2_name', 'Model 2')

        return f"""
        <div class="tmdl-section">
            <div class="tmdl-controls">
                <label>
                    <input type="checkbox" id="sync-scroll" checked onchange="toggleSyncScroll()">
                    Sync Scroll
                </label>
            </div>
            <div class="tmdl-split-view">
                <div class="tmdl-pane left">
                    <div class="tmdl-pane-header">{self._escape(model1_name)}</div>
                    <div class="tmdl-code-container" id="tmdl-left" onscroll="onTmdlScroll('left')">
                        {left_html}
                    </div>
                </div>
                <div class="tmdl-pane right">
                    <div class="tmdl-pane-header">{self._escape(model2_name)}</div>
                    <div class="tmdl-code-container" id="tmdl-right" onscroll="onTmdlScroll('right')">
                        {right_html}
                    </div>
                </div>
            </div>
        </div>
        """

    def _build_tmdl_lines(self, lines: List[str], model_id: str, total_lines: int) -> str:
        """Build HTML for TMDL lines with line numbers."""
        html_parts = ['<div class="tmdl-code">']

        for i, line in enumerate(lines, 1):
            line_num = i
            escaped_line = self._escape(line) if line else "&nbsp;"

            html_parts.append(f'''
                <div class="tmdl-line" data-line="{line_num}" data-model="{model_id}" onclick="onLineClick('{model_id}', {line_num})" onmouseenter="onLineHover('{model_id}', {line_num})" onmouseleave="onLineHoverOut('{model_id}', {line_num})">
                    <span class="line-number">{line_num}</span>
                    <span class="line-content">{escaped_line}</span>
                </div>
            ''')

        html_parts.append('</div>')
        return ''.join(html_parts)

    def _build_tmdl_changes_view(self) -> str:
        """Build TMDL changes only view (semantic + raw diff)."""
        if not self.tmdl1_data or not self.tmdl2_data:
            return """
            <div class="tmdl-section">
                <div class="info-message">
                    <p>TMDL data not available for changes view.</p>
                </div>
            </div>
            """

        # Use semantic diff analyzer
        from core.tmdl_semantic_diff import TmdlSemanticDiff
        from core.tmdl_text_generator import generate_tmdl_text

        try:
            analyzer = TmdlSemanticDiff(self.tmdl1_data, self.tmdl2_data)
            semantic_diff = analyzer.analyze()
        except Exception as e:
            logger.error(f"Failed to analyze semantic diff: {e}")
            return f"""
            <div class="tmdl-section">
                <div class="info-message error">
                    <p>Error analyzing changes: {self._escape(str(e))}</p>
                </div>
            </div>
            """

        if not semantic_diff.get('has_changes'):
            return """
            <div class="tmdl-section">
                <div class="info-message">
                    <p>✅ No TMDL changes detected. The models are identical.</p>
                </div>
            </div>
            """

        # Build categorized HTML
        sections_html = []

        # Model properties
        if semantic_diff['model_properties']:
            sections_html.append(self._build_semantic_section_model_props(semantic_diff['model_properties']))

        # Tables
        if any(semantic_diff['tables'].values()):
            sections_html.append(self._build_semantic_section_tables(semantic_diff['tables']))

        # Columns
        if any(semantic_diff['columns'].values()):
            sections_html.append(self._build_semantic_section_columns(semantic_diff['columns']))

        # Measures
        if any(semantic_diff['measures'].values()):
            sections_html.append(self._build_semantic_section_measures(semantic_diff['measures']))

        # Relationships
        if any(semantic_diff['relationships'].values()):
            sections_html.append(self._build_semantic_section_relationships(semantic_diff['relationships']))

        # Roles
        if any(semantic_diff['roles'].values()):
            sections_html.append(self._build_semantic_section_roles(semantic_diff['roles']))

        # Generate raw TMDL diff
        try:
            tmdl1_text = generate_tmdl_text(self.tmdl1_data)
            tmdl2_text = generate_tmdl_text(self.tmdl2_data)

            lines1 = tmdl1_text.split('\n')
            lines2 = tmdl2_text.split('\n')

            model1_name = self.summary.get('model1_name', 'Model 1')
            model2_name = self.summary.get('model2_name', 'Model 2')

            diff_lines = list(difflib.unified_diff(
                lines1,
                lines2,
                fromfile=model1_name,
                tofile=model2_name,
                lineterm=''
            ))

            raw_diff_html = self._build_unified_diff_html(diff_lines) if diff_lines else ""
        except Exception as e:
            logger.error(f"Failed to generate raw diff: {e}")
            raw_diff_html = f"<p>Error generating raw diff: {self._escape(str(e))}</p>"

        return f"""
        <div class="tmdl-section">
            <div class="diff-view-toggle">
                <button class="toggle-btn active" onclick="switchDiffView('semantic')" id="btn-semantic">
                    <span class="toggle-icon">📋</span>
                    Semantic View
                </button>
                <button class="toggle-btn" onclick="switchDiffView('raw')" id="btn-raw">
                    <span class="toggle-icon">📝</span>
                    Raw TMDL Diff
                </button>
            </div>

            <div id="semantic-view" class="diff-view active">
                <div class="semantic-diff-container">
                    {''.join(sections_html)}
                </div>
            </div>

            <div id="raw-view" class="diff-view">
                <div class="tmdl-diff-container">
                    {raw_diff_html}
                </div>
            </div>
        </div>
        """

    def _build_semantic_section_model_props(self, props: Dict[str, Any]) -> str:
        """Build model properties section."""
        items_html = []
        for key, change in props.items():
            items_html.append(f"""
                <div class="semantic-item">
                    <span class="property-name">{self._escape(key)}</span>
                    <div class="property-change">
                        <span class="old-value">{self._escape(str(change.get('from', '')))}</span>
                        <span class="arrow">→</span>
                        <span class="new-value">{self._escape(str(change.get('to', '')))}</span>
                    </div>
                </div>
            """)

        return f"""
        <div class="semantic-category">
            <h3 class="category-header">
                <span class="category-icon">⚙️</span>
                Model Properties
                <span class="category-badge">{len(props)} changed</span>
            </h3>
            <div class="category-items">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_semantic_section_tables(self, tables: Dict[str, List]) -> str:
        """Build tables section."""
        items_html = []

        for table in tables.get('added', []):
            items_html.append(f"""
                <div class="semantic-item added">
                    <span class="badge mini added">+</span>
                    <strong>{self._escape(table['name'])}</strong>
                    <span class="meta">{table['columns_count']} columns, {table['measures_count']} measures</span>
                </div>
            """)

        for table in tables.get('removed', []):
            items_html.append(f"""
                <div class="semantic-item removed">
                    <span class="badge mini removed">-</span>
                    <strong>{self._escape(table['name'])}</strong>
                    <span class="meta">{table['columns_count']} columns, {table['measures_count']} measures</span>
                </div>
            """)

        for table in tables.get('modified', []):
            changes_text = ', '.join([f"{k} changed" for k in table['changes'].keys()])
            items_html.append(f"""
                <div class="semantic-item modified">
                    <span class="badge mini modified">~</span>
                    <strong>{self._escape(table['name'])}</strong>
                    <span class="meta">{self._escape(changes_text)}</span>
                </div>
            """)

        total = len(tables.get('added', [])) + len(tables.get('removed', [])) + len(tables.get('modified', []))

        return f"""
        <div class="semantic-category">
            <h3 class="category-header">
                <span class="category-icon">📊</span>
                Tables
                <span class="category-badge">{total} changed</span>
            </h3>
            <div class="category-items">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_semantic_section_columns(self, columns: Dict[str, List]) -> str:
        """Build columns section."""
        items_html = []

        for col in columns.get('added', []):
            items_html.append(f"""
                <div class="semantic-item added">
                    <span class="badge mini added">+</span>
                    <span class="table-ref">{self._escape(col['table'])}</span>
                    <strong>{self._escape(col['name'])}</strong>
                    <span class="type-badge">{self._escape(col.get('data_type', 'Unknown'))}</span>
                    {f'<span class="calc-badge">Calculated</span>' if col.get('is_calculated') else ''}
                    {f'<span class="source-badge">Source: {self._escape(col.get("source_column", ""))}</span>' if col.get('source_column') else ''}
                </div>
            """)

        for col in columns.get('removed', []):
            items_html.append(f"""
                <div class="semantic-item removed">
                    <span class="badge mini removed">-</span>
                    <span class="table-ref">{self._escape(col['table'])}</span>
                    <strong>{self._escape(col['name'])}</strong>
                    <span class="type-badge">{self._escape(col.get('data_type', 'Unknown'))}</span>
                </div>
            """)

        for col in columns.get('modified', []):
            changes = col['changes']
            changes_html = []

            for key, change in changes.items():
                if key == 'expression':
                    # Show DAX diff for calculated columns
                    changes_html.append(f"""
                        <div class="property-change-block">
                            <strong>Expression changed:</strong>
                            <div class="dax-mini-diff">
                                <div class="dax-before">
                                    <div class="label">Before:</div>
                                    <pre>{self._escape(change.get('from', ''))}</pre>
                                </div>
                                <div class="dax-after">
                                    <div class="label">After:</div>
                                    <pre>{self._escape(change.get('to', ''))}</pre>
                                </div>
                            </div>
                        </div>
                    """)
                else:
                    changes_html.append(f"""
                        <div class="property-change-inline">
                            <strong>{self._escape(key)}:</strong>
                            <span class="old-value">{self._escape(str(change.get('from', '')))}</span>
                            →
                            <span class="new-value">{self._escape(str(change.get('to', '')))}</span>
                        </div>
                    """)

            items_html.append(f"""
                <div class="semantic-item modified expandable">
                    <div class="item-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <span class="badge mini modified">~</span>
                        <span class="table-ref">{self._escape(col['table'])}</span>
                        <strong>{self._escape(col['name'])}</strong>
                        <span class="changes-count">{len(changes)} changes</span>
                        <span class="expand-icon">▼</span>
                    </div>
                    <div class="item-details">
                        {''.join(changes_html)}
                    </div>
                </div>
            """)

        total = len(columns.get('added', [])) + len(columns.get('removed', [])) + len(columns.get('modified', []))

        return f"""
        <div class="semantic-category">
            <h3 class="category-header">
                <span class="category-icon">📝</span>
                Columns
                <span class="category-badge">{total} changed</span>
            </h3>
            <div class="category-items">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_semantic_section_measures(self, measures: Dict[str, List]) -> str:
        """Build measures section."""
        items_html = []

        for meas in measures.get('added', []):
            items_html.append(f"""
                <div class="semantic-item added expandable">
                    <div class="item-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <span class="badge mini added">+</span>
                        <span class="table-ref">{self._escape(meas['table'])}</span>
                        <strong>{self._escape(meas['name'])}</strong>
                        {f'<span class="folder-ref">{self._escape(meas.get("display_folder", ""))}</span>' if meas.get('display_folder') else ''}
                        <span class="expand-icon">▼</span>
                    </div>
                    <div class="item-details">
                        <div class="dax-expression added">
                            <pre>{self._escape(meas.get('expression', ''))}</pre>
                        </div>
                    </div>
                </div>
            """)

        for meas in measures.get('removed', []):
            items_html.append(f"""
                <div class="semantic-item removed expandable">
                    <div class="item-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <span class="badge mini removed">-</span>
                        <span class="table-ref">{self._escape(meas['table'])}</span>
                        <strong>{self._escape(meas['name'])}</strong>
                        <span class="expand-icon">▼</span>
                    </div>
                    <div class="item-details">
                        <div class="dax-expression removed">
                            <pre>{self._escape(meas.get('expression', ''))}</pre>
                        </div>
                    </div>
                </div>
            """)

        for meas in measures.get('modified', []):
            changes = meas['changes']
            changes_html = []

            if 'expression' in changes:
                changes_html.append(f"""
                    <div class="dax-mini-diff">
                        <div class="dax-before">
                            <div class="label">Before:</div>
                            <pre>{self._escape(changes['expression'].get('from', ''))}</pre>
                        </div>
                        <div class="dax-after">
                            <div class="label">After:</div>
                            <pre>{self._escape(changes['expression'].get('to', ''))}</pre>
                        </div>
                    </div>
                """)

            for key, change in changes.items():
                if key != 'expression':
                    changes_html.append(f"""
                        <div class="property-change-inline">
                            <strong>{self._escape(key)}:</strong>
                            <span class="old-value">{self._escape(str(change.get('from', '')))}</span>
                            →
                            <span class="new-value">{self._escape(str(change.get('to', '')))}</span>
                        </div>
                    """)

            items_html.append(f"""
                <div class="semantic-item modified expandable">
                    <div class="item-header" onclick="this.parentElement.classList.toggle('expanded')">
                        <span class="badge mini modified">~</span>
                        <span class="table-ref">{self._escape(meas['table'])}</span>
                        <strong>{self._escape(meas['name'])}</strong>
                        <span class="changes-count">{len(changes)} changes</span>
                        <span class="expand-icon">▼</span>
                    </div>
                    <div class="item-details">
                        {''.join(changes_html)}
                    </div>
                </div>
            """)

        total = len(measures.get('added', [])) + len(measures.get('removed', [])) + len(measures.get('modified', []))

        return f"""
        <div class="semantic-category">
            <h3 class="category-header">
                <span class="category-icon">📐</span>
                Measures
                <span class="category-badge">{total} changed</span>
            </h3>
            <div class="category-items">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_semantic_section_relationships(self, relationships: Dict[str, List]) -> str:
        """Build relationships section."""
        items_html = []

        for rel in relationships.get('added', []):
            from_col = rel.get('from_column', '')
            to_col = rel.get('to_column', '')
            items_html.append(f"""
                <div class="semantic-item added">
                    <span class="badge mini added">+</span>
                    <strong>{self._escape(from_col)} → {self._escape(to_col)}</strong>
                    <span class="meta">{rel.get('from_cardinality', '')}:{rel.get('to_cardinality', '')}</span>
                    {f'<span class="inactive-badge">Inactive</span>' if not rel.get('is_active', True) else ''}
                </div>
            """)

        for rel in relationships.get('removed', []):
            from_col = rel.get('from_column', '')
            to_col = rel.get('to_column', '')
            items_html.append(f"""
                <div class="semantic-item removed">
                    <span class="badge mini removed">-</span>
                    <strong>{self._escape(from_col)} → {self._escape(to_col)}</strong>
                    <span class="meta">{rel.get('from_cardinality', '')}:{rel.get('to_cardinality', '')}</span>
                </div>
            """)

        for rel in relationships.get('modified', []):
            from_col = rel.get('from_column', '')
            to_col = rel.get('to_column', '')
            changes = rel['changes']
            changes_text = ', '.join([f"{k}: {v.get('from', '')} → {v.get('to', '')}" for k, v in changes.items()])
            items_html.append(f"""
                <div class="semantic-item modified">
                    <span class="badge mini modified">~</span>
                    <strong>{self._escape(from_col)} → {self._escape(to_col)}</strong>
                    <div class="changes-detail">{self._escape(changes_text)}</div>
                </div>
            """)

        total = len(relationships.get('added', [])) + len(relationships.get('removed', [])) + len(relationships.get('modified', []))

        return f"""
        <div class="semantic-category">
            <h3 class="category-header">
                <span class="category-icon">🔗</span>
                Relationships
                <span class="category-badge">{total} changed</span>
            </h3>
            <div class="category-items">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_semantic_section_roles(self, roles: Dict[str, List]) -> str:
        """Build roles section."""
        items_html = []

        for role_name in roles.get('added', []):
            items_html.append(f"""
                <div class="semantic-item added">
                    <span class="badge mini added">+</span>
                    <strong>{self._escape(role_name)}</strong>
                </div>
            """)

        for role_name in roles.get('removed', []):
            items_html.append(f"""
                <div class="semantic-item removed">
                    <span class="badge mini removed">-</span>
                    <strong>{self._escape(role_name)}</strong>
                </div>
            """)

        total = len(roles.get('added', [])) + len(roles.get('removed', []))

        return f"""
        <div class="semantic-category">
            <h3 class="category-header">
                <span class="category-icon">🔐</span>
                Roles
                <span class="category-badge">{total} changed</span>
            </h3>
            <div class="category-items">
                {''.join(items_html)}
            </div>
        </div>
        """

    def _build_unified_diff_html(self, diff_lines: List[str]) -> str:
        """Build HTML for unified diff output."""
        html_parts = ['<div class="unified-diff">']

        for line in diff_lines:
            if not line:
                continue

            escaped_line = self._escape(line)

            if line.startswith('---') or line.startswith('+++'):
                # File headers
                html_parts.append(f'<div class="diff-line file-header">{escaped_line}</div>')
            elif line.startswith('@@'):
                # Chunk headers
                html_parts.append(f'<div class="diff-line chunk-header">{escaped_line}</div>')
            elif line.startswith('-'):
                # Removed line
                html_parts.append(f'<div class="diff-line removed-line">{escaped_line}</div>')
            elif line.startswith('+'):
                # Added line
                html_parts.append(f'<div class="diff-line added-line">{escaped_line}</div>')
            else:
                # Context line
                html_parts.append(f'<div class="diff-line context-line">{escaped_line}</div>')

        html_parts.append('</div>')
        return ''.join(html_parts)

    def _get_styles(self) -> str:
        """Get CSS styles."""
        return """
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: #f8f9fa;
    color: #212529;
    line-height: 1.6;
    padding: 20px;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 40px;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.header h1 {
    font-size: 2.5rem;
    margin-bottom: 20px;
}

.models {
    display: flex;
    align-items: center;
    gap: 15px;
    margin: 20px 0;
}

.model-badge {
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
}

.model-badge.old {
    background: rgba(255,255,255,0.2);
}

.model-badge.new {
    background: rgba(255,255,255,0.3);
}

.vs {
    font-weight: bold;
    font-size: 1.2rem;
}

.timestamp {
    margin-top: 10px;
    opacity: 0.9;
}

.summary-card {
    background: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.summary-card h2 {
    margin-bottom: 20px;
    color: #495057;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 20px;
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: #495057;
}

.stat-value.added {
    color: #28a745;
}

.stat-value.removed {
    color: #dc3545;
}

.stat-value.modified {
    color: #ffc107;
}

.stat-label {
    color: #6c757d;
    font-size: 0.9rem;
    margin-top: 5px;
}

.section {
    background: white;
    padding: 30px;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.section h2 {
    color: #495057;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
}

.section-header {
    display: block;
    cursor: pointer;
    user-select: none;
    color: #495057;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
}

.section-header .expand-icon {
    display: inline-block;
    font-size: 0.8rem;
    margin-right: 10px;
    transition: transform 0.2s;
}

.collapsible-section .section-body {
    display: none;
    margin-top: 20px;
}

.collapsible-section.expanded .section-body {
    display: block;
}

.collapsible-section.expanded .section-header .expand-icon {
    transform: rotate(180deg);
}

.changes-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.change-card {
    border-radius: 8px;
    border: 2px solid #dee2e6;
    overflow: hidden;
    transition: all 0.2s;
}

.change-card.added {
    border-color: #28a745;
    background: #f8fff9;
}

.change-card.removed {
    border-color: #dc3545;
    background: #fff5f5;
}

.change-card.modified {
    border-color: #ffc107;
    background: #fffef8;
}

.change-header {
    padding: 15px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.change-header.clickable {
    cursor: pointer;
    user-select: none;
}

.change-header.clickable:hover {
    background: rgba(0,0,0,0.02);
}

.badge {
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
}

.badge.added {
    background: #28a745;
    color: white;
}

.badge.removed {
    background: #dc3545;
    color: white;
}

.badge.modified {
    background: #ffc107;
    color: #000;
}

.badge.mini {
    padding: 2px 8px;
    font-size: 0.7rem;
}

.item-name {
    font-size: 1.1rem;
    color: #212529;
}

.table-badge {
    padding: 4px 10px;
    background: #6c757d;
    color: white;
    border-radius: 4px;
    font-size: 0.85rem;
}

.folder-badge {
    padding: 4px 10px;
    background: #17a2b8;
    color: white;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: 'Consolas', 'Monaco', monospace;
}

.meta {
    color: #6c757d;
    font-size: 0.9rem;
}

.expand-icon {
    margin-left: auto;
    font-size: 0.8rem;
    transition: transform 0.2s;
}

.change-card.expanded .expand-icon {
    transform: rotate(180deg);
}

.change-body {
    display: none;
    padding: 20px;
    border-top: 1px solid #dee2e6;
    background: white;
}

.change-card.expanded .change-body {
    display: block;
}

.subsection {
    margin-bottom: 20px;
}

.subsection h4 {
    color: #495057;
    margin-bottom: 12px;
    font-size: 1rem;
}

.sub-items-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.sub-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    border-radius: 6px;
    background: white;
    border: 1px solid #dee2e6;
}

.sub-item.added {
    background: #f8fff9;
    border-color: #c3e6cb;
}

.sub-item.removed {
    background: #fff5f5;
    border-color: #f5c6cb;
}

.sub-item.modified {
    background: #fffef8;
    border-color: #ffeeba;
}

.sub-item strong {
    color: #212529;
}

.type {
    padding: 2px 8px;
    background: #e9ecef;
    border-radius: 3px;
    font-size: 0.8rem;
    color: #495057;
}

.changes-detail {
    color: #6c757d;
    font-size: 0.9rem;
    font-style: italic;
}

.dax-preview {
    margin-top: 8px;
    padding: 8px;
    background: #f8f9fa;
    border-left: 3px solid #6c757d;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.85rem;
    color: #495057;
    overflow-x: auto;
}

.dax-full {
    margin-top: 8px;
    width: 100%;
}

.dax-full pre {
    margin: 0;
    padding: 12px;
    background: #f8f9fa;
    border-left: 3px solid #6c757d;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.85rem;
    color: #212529;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.dax-box {
    margin-top: 15px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 4px solid #6c757d;
}

.dax-box.added {
    border-left-color: #28a745;
}

.dax-box.removed {
    border-left-color: #dc3545;
}

.dax-box pre {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
    color: #212529;
    overflow-x: auto;
    white-space: pre-wrap;
}

.metadata-changes {
    margin-bottom: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
}

.metadata-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid #dee2e6;
}

.metadata-row:last-child {
    border-bottom: none;
}

.metadata-row strong {
    min-width: 150px;
    color: #495057;
}

.metadata-row .old {
    padding: 4px 8px;
    background: #fff5f5;
    border-radius: 4px;
    color: #721c24;
}

.metadata-row .new {
    padding: 4px 8px;
    background: #f8fff9;
    border-radius: 4px;
    color: #155724;
}

.dax-comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 15px;
}

.dax-side {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #dee2e6;
}

.dax-side.before {
    border-color: #dc3545;
}

.dax-side.after {
    border-color: #28a745;
}

.dax-label {
    padding: 8px 12px;
    font-weight: bold;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.dax-side.before .dax-label {
    background: #dc3545;
    color: white;
}

.dax-side.after .dax-label {
    background: #28a745;
    color: white;
}

.dax-side pre {
    padding: 15px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.85rem;
    overflow-x: auto;
    white-space: pre-wrap;
    background: #f8f9fa;
    margin: 0;
}

.info {
    color: #6c757d;
    font-style: italic;
}

.no-details {
    padding: 15px;
    color: #6c757d;
    font-style: italic;
    text-align: center;
}

@media (max-width: 768px) {
    .dax-comparison {
        grid-template-columns: 1fr;
    }

    .stat-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Tab Navigation */
.tabs {
    display: flex;
    gap: 5px;
    margin-bottom: 20px;
    border-bottom: 2px solid #dee2e6;
    background: white;
    border-radius: 12px 12px 0 0;
    padding: 10px 10px 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.tab-button {
    padding: 12px 24px;
    border: none;
    background: transparent;
    color: #6c757d;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.tab-button:hover {
    color: #495057;
    background: rgba(0,0,0,0.02);
    border-radius: 6px 6px 0 0;
}

.tab-button.active {
    color: #667eea;
    border-bottom-color: #667eea;
}

.tab-icon {
    font-size: 1.2rem;
}

.tab-content {
    position: relative;
}

.tab-pane {
    display: none;
}

.tab-pane.active {
    display: block;
}

/* TMDL Section */
.tmdl-section {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.tmdl-controls {
    margin-bottom: 15px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 6px;
}

.tmdl-controls label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-weight: 500;
}

.tmdl-split-view {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    height: calc(100vh - 350px);
    min-height: 600px;
}

.tmdl-pane {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.tmdl-pane-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    font-weight: 600;
    font-size: 1rem;
}

.tmdl-code-container {
    flex: 1;
    overflow-y: auto;
    overflow-x: auto;
    background: #f8f9fa;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
}

.tmdl-code {
    min-width: fit-content;
}

.tmdl-line {
    display: flex;
    align-items: flex-start;
    cursor: pointer;
    transition: background 0.1s;
    min-height: 20px;
}

.tmdl-line:hover {
    background: rgba(255, 193, 7, 0.1);
}

.tmdl-line.highlighted {
    background: rgba(255, 193, 7, 0.3);
}

.tmdl-line.selected {
    background: rgba(102, 126, 234, 0.2);
    border-left: 3px solid #667eea;
}

.line-number {
    display: inline-block;
    min-width: 50px;
    padding: 2px 12px;
    text-align: right;
    color: #6c757d;
    background: #e9ecef;
    user-select: none;
    border-right: 1px solid #dee2e6;
}

.line-content {
    padding: 2px 12px;
    white-space: pre;
    flex: 1;
}

/* TMDL Diff Container */
.tmdl-diff-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    overflow-x: auto;
}

.unified-diff {
    background: white;
    border-radius: 6px;
    border: 1px solid #dee2e6;
}

.diff-line {
    padding: 4px 12px;
    white-space: pre;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.diff-line.file-header {
    background: #e9ecef;
    color: #495057;
    font-weight: bold;
    border-bottom: 1px solid #dee2e6;
}

.diff-line.chunk-header {
    background: #d6e9f8;
    color: #0056b3;
    font-weight: 600;
}

.diff-line.added-line {
    background: #d4edda;
    color: #155724;
}

.diff-line.removed-line {
    background: #f8d7da;
    color: #721c24;
}

.diff-line.context-line {
    background: white;
    color: #212529;
}

.info-message {
    padding: 40px;
    text-align: center;
    color: #6c757d;
    font-size: 1.1rem;
}

.info-message.error {
    color: #dc3545;
}

.info-message p {
    margin: 10px 0;
}

/* Diff View Toggle */
.diff-view-toggle {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    background: white;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}

.toggle-btn {
    flex: 1;
    padding: 12px 20px;
    border: 2px solid #dee2e6;
    background: white;
    color: #6c757d;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.toggle-btn:hover {
    background: #f8f9fa;
    border-color: #adb5bd;
}

.toggle-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-color: #667eea;
}

.toggle-icon {
    font-size: 1.2rem;
}

.diff-view {
    display: none;
}

.diff-view.active {
    display: block;
}

/* Semantic Diff Styles */
.semantic-diff-container {
    display: flex;
    flex-direction: column;
    gap: 25px;
}

.semantic-category {
    background: white;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    overflow: hidden;
}

.category-header {
    background: linear-gradient(to right, #f8f9fa, white);
    padding: 15px 20px;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    border-bottom: 2px solid #e9ecef;
    font-size: 1.1rem;
    color: #495057;
}

.category-icon {
    font-size: 1.3rem;
}

.category-badge {
    margin-left: auto;
    background: #6c757d;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
}

.category-items {
    padding: 15px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.semantic-item {
    padding: 12px 15px;
    border-radius: 6px;
    border: 1px solid #dee2e6;
    background: white;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    transition: all 0.2s;
}

.semantic-item.added {
    background: #f8fff9;
    border-color: #c3e6cb;
}

.semantic-item.removed {
    background: #fff5f5;
    border-color: #f5c6cb;
}

.semantic-item.modified {
    background: #fffef8;
    border-color: #ffeeba;
}

.semantic-item.expandable {
    flex-direction: column;
    align-items: stretch;
    cursor: default;
}

.item-header {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    cursor: pointer;
    user-select: none;
}

.item-header:hover {
    opacity: 0.8;
}

.item-details {
    display: none;
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid #dee2e6;
}

.semantic-item.expandable.expanded .item-details {
    display: block;
}

.semantic-item.expandable.expanded .expand-icon {
    transform: rotate(180deg);
}

.table-ref {
    padding: 3px 10px;
    background: #6c757d;
    color: white;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
}

.type-badge {
    padding: 3px 8px;
    background: #17a2b8;
    color: white;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
}

.calc-badge {
    padding: 3px 8px;
    background: #ffc107;
    color: #000;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.source-badge {
    padding: 3px 8px;
    background: #e9ecef;
    color: #495057;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: 'Consolas', 'Monaco', monospace;
}

.folder-ref {
    padding: 3px 8px;
    background: #17a2b8;
    color: white;
    border-radius: 4px;
    font-size: 0.75rem;
}

.inactive-badge {
    padding: 3px 8px;
    background: #dc3545;
    color: white;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}

.changes-count {
    padding: 3px 10px;
    background: #e9ecef;
    color: #495057;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.property-change {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.property-change-inline {
    margin: 5px 0;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

.property-change-block {
    margin: 10px 0;
}

.old-value {
    padding: 4px 10px;
    background: #fff5f5;
    color: #721c24;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
}

.new-value {
    padding: 4px 10px;
    background: #f8fff9;
    color: #155724;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9rem;
}

.arrow {
    color: #6c757d;
    font-weight: bold;
}

.dax-expression {
    padding: 15px;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 4px solid #6c757d;
    margin-top: 10px;
}

.dax-expression.added {
    border-left-color: #28a745;
    background: #f8fff9;
}

.dax-expression.removed {
    border-left-color: #dc3545;
    background: #fff5f5;
}

.dax-expression pre {
    margin: 0;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.85rem;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.dax-mini-diff {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-top: 10px;
}

.dax-before,
.dax-after {
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid #dee2e6;
}

.dax-before {
    border-left: 4px solid #dc3545;
}

.dax-after {
    border-left: 4px solid #28a745;
}

.dax-before .label,
.dax-after .label {
    padding: 6px 12px;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.dax-before .label {
    background: #f8d7da;
    color: #721c24;
}

.dax-after .label {
    background: #d4edda;
    color: #155724;
}

.dax-before pre,
.dax-after pre {
    margin: 0;
    padding: 12px;
    background: #f8f9fa;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.85rem;
    white-space: pre-wrap;
    word-wrap: break-word;
}

@media (max-width: 1024px) {
    .dax-mini-diff {
        grid-template-columns: 1fr;
    }
}
</style>
        """

    def _get_scripts(self) -> str:
        """Get JavaScript."""
        return """
<script>
// Tab switching
function switchTab(tabId) {
    // Remove active class from all tabs and panes
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

    // Add active class to selected tab and pane
    event.target.closest('.tab-button').classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Sync scroll state
let syncScrollEnabled = true;
let isScrolling = false;

function toggleSyncScroll() {
    syncScrollEnabled = document.getElementById('sync-scroll').checked;
}

// TMDL scroll synchronization
function onTmdlScroll(source) {
    if (!syncScrollEnabled || isScrolling) return;

    isScrolling = true;

    const sourceContainer = document.getElementById('tmdl-' + source);
    const targetContainer = document.getElementById(source === 'left' ? 'tmdl-right' : 'tmdl-left');

    if (sourceContainer && targetContainer) {
        // Sync scroll position
        targetContainer.scrollTop = sourceContainer.scrollTop;
        targetContainer.scrollLeft = sourceContainer.scrollLeft;
    }

    setTimeout(() => { isScrolling = false; }, 50);
}

// Line hover highlighting
let currentHoveredLine = null;

function onLineHover(modelId, lineNum) {
    currentHoveredLine = lineNum;

    // Highlight current line in both models
    highlightLine('model1', lineNum, true);
    highlightLine('model2', lineNum, true);
}

function onLineHoverOut(modelId, lineNum) {
    if (currentHoveredLine === lineNum) {
        currentHoveredLine = null;
        // Remove highlight from both models
        unhighlightLine('model1', lineNum);
        unhighlightLine('model2', lineNum);
    }
}

function highlightLine(modelId, lineNum, isHover) {
    const line = document.querySelector(`.tmdl-line[data-model="${modelId}"][data-line="${lineNum}"]`);
    if (line) {
        if (isHover) {
            line.classList.add('highlighted');
        } else {
            line.classList.add('selected');
        }
    }
}

function unhighlightLine(modelId, lineNum) {
    const line = document.querySelector(`.tmdl-line[data-model="${modelId}"][data-line="${lineNum}"]`);
    if (line) {
        line.classList.remove('highlighted');
    }
}

// Line click - select and scroll to same line in other pane
let selectedLines = { model1: null, model2: null };

function onLineClick(modelId, lineNum) {
    // Clear previous selections
    document.querySelectorAll('.tmdl-line.selected').forEach(line => {
        line.classList.remove('selected');
    });

    // Select current line in both models
    selectedLines.model1 = lineNum;
    selectedLines.model2 = lineNum;

    const line1 = document.querySelector(`.tmdl-line[data-model="model1"][data-line="${lineNum}"]`);
    const line2 = document.querySelector(`.tmdl-line[data-model="model2"][data-line="${lineNum}"]`);

    if (line1) line1.classList.add('selected');
    if (line2) line2.classList.add('selected');

    // Scroll the other pane to this line
    const otherModelId = modelId === 'model1' ? 'model2' : 'model1';
    const otherContainer = document.getElementById('tmdl-' + (otherModelId === 'model1' ? 'left' : 'right'));
    const otherLine = document.querySelector(`.tmdl-line[data-model="${otherModelId}"][data-line="${lineNum}"]`);

    if (otherContainer && otherLine) {
        // Temporarily disable sync scroll to prevent feedback loop
        const wasSyncing = syncScrollEnabled;
        syncScrollEnabled = false;

        // Scroll to line (centered)
        const lineTop = otherLine.offsetTop;
        const containerHeight = otherContainer.clientHeight;
        const lineHeight = otherLine.clientHeight;
        const scrollTop = lineTop - (containerHeight / 2) + (lineHeight / 2);

        otherContainer.scrollTop = scrollTop;

        // Re-enable sync scroll after a delay
        setTimeout(() => { syncScrollEnabled = wasSyncing; }, 100);
    }
}

// Diff view toggle (for TMDL Changes tab)
function switchDiffView(viewType) {
    // Remove active class from all buttons and views
    document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.diff-view').forEach(view => view.classList.remove('active'));

    // Add active class to selected button and view
    if (viewType === 'semantic') {
        document.getElementById('btn-semantic').classList.add('active');
        document.getElementById('semantic-view').classList.add('active');
    } else if (viewType === 'raw') {
        document.getElementById('btn-raw').classList.add('active');
        document.getElementById('raw-view').classList.add('active');
    }
}

console.log('Power BI Model Diff Report V2 with TMDL tabs loaded');
</script>
        """
