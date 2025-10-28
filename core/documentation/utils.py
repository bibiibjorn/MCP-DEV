"""Shared utilities for documentation generation."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.dax.dax_reference_parser import DaxReferenceIndex

# Constants
DEFAULT_SUBDIR = os.path.join("exports", "docs")
SNAPSHOT_SUFFIX = "documentation_snapshot.json"
GRAPH_SIZE = (11, 8)

# Branding configuration
DEFAULT_BRANDING = {
    "primary_color": (0, 70, 127),      # Dark blue
    "secondary_color": (0, 102, 204),    # Medium blue
    "accent_color": (68, 114, 196),      # Light blue
    "header_bg": (0, 70, 127),           # Dark blue for table headers
    "logo_path": None,                    # Path to company logo
    "company_name": None,                 # Company name for footer
}


def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")


def ensure_dir(path: Optional[str]) -> str:
    """Ensure directory exists, creating it if necessary."""
    base = path or DEFAULT_SUBDIR
    if not os.path.isabs(base):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base = os.path.join(root, base)
    os.makedirs(base, exist_ok=True)
    return base


def safe_filename(name: Optional[str], suffix: str) -> str:
    """Create a safe filename from a model name and suffix."""
    clean = re.sub(r"[^A-Za-z0-9_-]+", "_", (name or "powerbi_model").strip())
    clean = clean.strip("._") or "powerbi_model"
    return f"{clean}_{suffix}"


def pick(row: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Pick first available value from row using multiple key names."""
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
        alt = f"[{key}]"
        if alt in row and row[alt] not in (None, ""):
            return row[alt]
    return default


def to_bool(value: Any) -> bool:
    """Convert various types to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return False


def build_reference_index(
    measures: List[Dict[str, Any]], columns: List[Dict[str, Any]]
) -> Optional[DaxReferenceIndex]:
    """Build DAX reference index for dependency analysis."""
    try:
        return DaxReferenceIndex(measures, columns)
    except Exception:
        return None


def format_edge(source: str, targets: List[str], target_type: str) -> Dict[str, Any]:
    """Format dependency edge for documentation."""
    return {
        "source": source,
        "targets": targets,
        "target_type": target_type,
    }


def truncate(text: str, length: int = 400) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


def relationship_id(rel: Dict[str, Any]) -> str:
    """Generate unique identifier for a relationship."""
    left = f"{rel.get('from_table')}[{rel.get('from_column')}]"
    right = f"{rel.get('to_table')}[{rel.get('to_column')}]"
    card = rel.get("cardinality") or "?"
    direct = rel.get("direction") or "?"
    active = "Active" if rel.get("is_active") else "Inactive"
    return f"{left} -> {right} | {card} | {direct} | {active}"
