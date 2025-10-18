"""Documentation builder utilities for generating rich Word reports for Power BI models.

This module provides backward-compatible exports from the modularized documentation package.
All functionality has been moved to focused submodules for better maintainability.
"""

from __future__ import annotations

# Import all public functions from submodules
from core.documentation import (
    calculate_measure_complexity,
    collect_model_documentation,
    compare_snapshots,
    compute_diff,
    convert_to_pdf,
    generate_interactive_relationship_graph,
    generate_relationship_graph,
    load_snapshot,
    render_word_report,
    save_snapshot,
    snapshot_from_context,
)

# Import constants from the utils module
from core.documentation.utils import (
    DEFAULT_BRANDING,
    DEFAULT_SUBDIR,
    SNAPSHOT_SUFFIX,
)

# Export all public functions for backward compatibility
__all__ = [
    # Main documentation functions
    "collect_model_documentation",
    "render_word_report",
    "convert_to_pdf",
    # Graph generation
    "generate_relationship_graph",
    "generate_interactive_relationship_graph",
    # Snapshot management
    "snapshot_from_context",
    "save_snapshot",
    "load_snapshot",
    "compute_diff",
    "compare_snapshots",
    # Analysis
    "calculate_measure_complexity",
    # Constants
    "DEFAULT_BRANDING",
    "DEFAULT_SUBDIR",
    "SNAPSHOT_SUFFIX",
]
