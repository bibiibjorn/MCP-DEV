"""
Model Diff Report Generator V2 - Complete Rewrite
Modern, clean HTML layout that shows EVERYTHING
"""

import logging
import json
import html
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ModelDiffReportV2:
    """
    Brand new HTML report generator with modern design.
    Shows EVERY type of change clearly.
    """

    def __init__(self, diff_result: Dict[str, Any]):
        self.diff = diff_result
        self.summary = diff_result.get('summary', {})

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
        {self._build_tables_section()}
        {self._build_measures_section()}
        {self._build_relationships_section()}
        {self._build_roles_section()}
        {self._build_perspectives_section()}
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
</style>
        """

    def _get_scripts(self) -> str:
        """Get JavaScript."""
        return """
<script>
// Click handlers are inline in HTML
console.log('Power BI Model Diff Report V2 loaded');
</script>
        """
