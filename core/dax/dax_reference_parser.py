"""
DAX Reference Parser

Shared module for parsing DAX expressions and extracting references to tables, columns, and measures.
This module breaks the circular dependency between core/model and core/documentation.
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional

logger = logging.getLogger(__name__)

_QUALIFIED_TOKEN = re.compile(r"'([^']+)'\s*\[([^\]]+)\]")
_UNQUALIFIED_TOKEN = re.compile(r"(?<!')\[(.+?)\]")


class DaxReferenceIndex:
    """
    Index of known measures and columns for DAX reference resolution.

    Used to distinguish between measure and column references in DAX expressions.
    """

    def __init__(self, measure_rows=None, column_rows=None) -> None:
        """
        Initialize the reference index.

        Args:
            measure_rows: List of measure dictionaries with 'Table' and 'Name' keys
            column_rows: List of column dictionaries with 'Table' and 'Name' keys
        """
        self.measure_keys: Set[str] = set()
        self.measure_names: Dict[str, Set[str]] = {}
        self.column_keys: Set[str] = set()

        if measure_rows:
            for row in measure_rows:
                table = str(row.get("Table") or "").strip()
                name = str(row.get("Name") or "").strip()
                if table and name:
                    key = f"{table.lower()}|{name.lower()}"
                    self.measure_keys.add(key)
                    self.measure_names.setdefault(name.lower(), set()).add(table)

        if column_rows:
            for row in column_rows:
                table = str(row.get("Table") or "").strip()
                name = str(row.get("Name") or "").strip()
                if table and name:
                    self.column_keys.add(f"{table.lower()}|{name.lower()}")


def parse_dax_references(
    expression: Optional[str],
    reference_index: Optional[DaxReferenceIndex] = None,
) -> Dict[str, List]:
    """
    Parse DAX expression and extract references to tables, columns, and measures.

    This is a simplified parser that extracts qualified ('Table'[Column]) and
    unqualified ([Measure]) references from DAX expressions.

    Args:
        expression: The DAX expression to parse
        reference_index: Optional index to distinguish measures from columns

    Returns:
        Dictionary with keys:
        - tables: List of table names referenced
        - columns: List of (table, column) tuples
        - measures: List of (table, measure) tuples
        - identifiers: List of all bracket-enclosed identifiers

    Example:
        >>> parse_dax_references("CALCULATE([Sales], 'Product'[Category] = \"Bikes\")")
        {
            "tables": ["Product"],
            "columns": [("Product", "Category")],
            "measures": [("", "Sales")],
            "identifiers": ["Sales", "Category"]
        }
    """
    if not isinstance(expression, str) or not expression.strip():
        return {"tables": [], "columns": [], "measures": [], "identifiers": []}

    # Remove comments
    cleaned = re.sub(r"/\*.*?\*/", "", expression, flags=re.DOTALL)
    cleaned = re.sub(r"//.*?$", "", cleaned, flags=re.MULTILINE)

    tables: Set[str] = set()
    columns: Set[Tuple[str, str]] = set()
    measures: Set[Tuple[str, str]] = set()
    identifiers: Set[str] = set()

    ref_idx = reference_index or DaxReferenceIndex()

    # Parse qualified references: 'Table'[Column]
    for table, name in _QUALIFIED_TOKEN.findall(cleaned):
        tbl = table.strip()
        obj = name.strip()
        if not obj:
            continue
        identifiers.add(obj)
        key = f"{tbl.lower()}|{obj.lower()}"
        tables.add(tbl)
        if key in ref_idx.measure_keys:
            measures.add((tbl, obj))
        else:
            columns.add((tbl, obj))

    # Parse unqualified references: [Measure]
    for match in _UNQUALIFIED_TOKEN.finditer(cleaned):
        name = match.group(1).strip()
        if not name or name.startswith("@"):  # Skip parameters
            continue
        identifiers.add(name)
        owners = ref_idx.measure_names.get(name.lower())
        if owners:
            for tbl in owners:
                measures.add((tbl, name))
        else:
            # Unknown - assume measure with no table
            measures.add(("", name))

    return {
        "tables": sorted(tables),
        "columns": sorted(columns),
        "measures": sorted(measures),
        "identifiers": sorted(identifiers),
    }


__all__ = ["DaxReferenceIndex", "parse_dax_references"]