"""
Lightweight DAX expression reference parser.

Provides best-effort extraction of table, column, and measure references from
raw DAX expressions without requiring a full parser or external dependency.
The parser is heuristic-based but leverages model metadata (when supplied) to
classify identifiers accurately.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Set, Tuple


def _clean_string(value: object) -> str:
    """Return a trimmed string representation or empty string."""
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _get_first(row: Dict[str, object], keys: Iterable[str]) -> str:
    """Return the first non-empty value for any key in ``keys``."""
    for key in keys:
        if key in row:
            text = _clean_string(row[key])
            if text:
                return text
    return ""


class DaxReferenceIndex:
    """
    Catalog of known measures and columns used to improve reference detection.

    The index stores normalized keys for quick lookups as well as mappings from
    unqualified names to their owning tables.
    """

    def __init__(
        self,
        measure_rows: Optional[Iterable[Dict[str, object]]] = None,
        column_rows: Optional[Iterable[Dict[str, object]]] = None,
    ) -> None:
        self.measure_keys: Set[str] = set()  # table|measure
        self.column_keys: Set[str] = set()  # table|column
        self.measure_names: Dict[str, Set[str]] = {}  # measure_name -> {table1, table2, ...}
        self.column_names: Dict[str, Set[str]] = {}  # column_name -> {table1, table2, ...}
        self.tables: Set[str] = set()

        if column_rows:
            self.add_columns(column_rows)
        if measure_rows:
            self.add_measures(measure_rows)

    @staticmethod
    def _normalize_pair(table: str, name: str) -> str:
        return f"{table.lower()}|{name.lower()}"

    def add_measures(self, rows: Iterable[Dict[str, object]]) -> None:
        for row in rows:
            table = _get_first(row, ("Table", "TableName", "TableID", "[Table]", "[TableName]"))
            name = _get_first(row, ("Name", "Measure", "ObjectName", "[Name]", "[Measure]"))
            if not name:
                continue
            if table:
                self.measure_keys.add(self._normalize_pair(table, name))
                self.tables.add(table)
                name_bucket = self.measure_names.setdefault(name.lower(), set())
                name_bucket.add(table)
            else:
                # Fallback when DMV omits table (rare but keep entry)
                name_bucket = self.measure_names.setdefault(name.lower(), set())
                name_bucket.add("")

    def add_columns(self, rows: Iterable[Dict[str, object]]) -> None:
        for row in rows:
            table = _get_first(row, ("Table", "TableName", "DimensionName", "[Table]", "[TableName]"))
            name = _get_first(
                row,
                (
                    "Name",
                    "Column",
                    "ColumnName",
                    "ColumnID",
                    "[Name]",
                    "[Column]",
                    "[ColumnName]",
                ),
            )
            if not table or not name:
                continue
            self.column_keys.add(self._normalize_pair(table, name))
            self.tables.add(table)
            # Add to column name index for unqualified reference lookup
            name_bucket = self.column_names.setdefault(name.lower(), set())
            name_bucket.add(table)


def _strip_comments(expression: str) -> str:
    """Remove block and line comments from a DAX expression."""
    without_block = re.sub(r"/\*.*?\*/", "", expression, flags=re.DOTALL)
    without_line = re.sub(r"//.*?$", "", without_block, flags=re.MULTILINE)
    return without_line


_QUALIFIED_REF = re.compile(r"'([^']+)'\s*\[([^\]]+)\]")
_UNQUALIFIED_REF = re.compile(r"(?<!['@])\[(.+?)\]")
_TABLE_LITERAL = re.compile(r"'([^']+)'\s*(?:\.|\[|\(|$)")


def parse_dax_references(
    expression: Optional[str],
    reference_index: Optional[DaxReferenceIndex] = None,
) -> Dict[str, List]:
    """
    Parse a DAX expression and return referenced tables, columns, and measures.

    Args:
        expression: Raw DAX expression text.
        reference_index: Optional ``DaxReferenceIndex`` with known metadata. When
            provided, the parser uses it to classify identifiers more accurately.

    Returns:
        Dictionary with ``tables``, ``columns`` (list of (table, column)),
        ``measures`` (list of (table, measure)), and ``identifiers`` (list of
        unique raw identifiers discovered).
    """
    if not isinstance(expression, str) or not expression.strip():
        return {"tables": [], "columns": [], "measures": [], "identifiers": []}

    cleaned = _strip_comments(expression)
    tables: Set[str] = set()
    columns: Set[Tuple[str, str]] = set()
    measures: Set[Tuple[str, str]] = set()
    identifiers: Set[str] = set()

    idx = reference_index
    measure_keys = idx.measure_keys if idx else set()
    column_keys = idx.column_keys if idx else set()
    measure_names = idx.measure_names if idx else {}
    column_names = idx.column_names if idx else {}

    for table, name in _QUALIFIED_REF.findall(cleaned):
        t = table.strip()
        n = name.strip()
        if not n:
            continue
        identifiers.add(n)
        tables.add(t)
        lookup_key = DaxReferenceIndex._normalize_pair(t, n)
        if lookup_key in measure_keys:
            measures.add((t, n))
        elif lookup_key in column_keys:
            columns.add((t, n))
        else:
            # Default to column to avoid under-reporting column usage.
            columns.add((t, n))

    for table in _TABLE_LITERAL.findall(cleaned):
        tbl = table.strip()
        if tbl:
            tables.add(tbl)

    # Unqualified references (e.g., [Total Sales])
    for match in _UNQUALIFIED_REF.finditer(cleaned):
        start = match.start()
        prefix = cleaned[max(0, start - 6) : start].upper()
        if prefix.endswith("VAR ") or prefix.endswith("DEFINE ") or prefix.endswith("MEASURE ") or prefix.endswith("COLUMN "):
            continue
        name = match.group(1).strip()
        if not name or name.startswith("@"):
            continue
        identifiers.add(name)

        # Check if it's a known measure
        measure_candidates = measure_names.get(name.lower())
        if measure_candidates:
            for table in measure_candidates:
                measures.add((table, name))
        else:
            # Check if it's a known column
            column_candidates = column_names.get(name.lower())
            if column_candidates:
                for table in column_candidates:
                    columns.add((table, name))
            else:
                # If not found as measure or column, default to measure (backward compatibility)
                measures.add(("", name))

    return {
        "tables": sorted(tables),
        "columns": sorted(columns),
        "measures": sorted(measures),
        "identifiers": sorted(identifiers),
    }


__all__ = ["DaxReferenceIndex", "parse_dax_references"]
