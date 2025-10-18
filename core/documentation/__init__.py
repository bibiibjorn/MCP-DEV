"""
Documentation generation modules for Power BI models.

This package provides modular components for generating comprehensive
documentation including Word reports, relationship graphs, snapshots,
and complexity analysis.
"""

from .word_generator import render_word_report, convert_to_pdf
from .relationship_graphs import (
    generate_relationship_graph,
    generate_interactive_relationship_graph,
)
from .snapshot_manager import (
    save_snapshot,
    load_snapshot,
    compute_diff,
    compare_snapshots,
    snapshot_from_context,
)
from .complexity_analyzer import calculate_measure_complexity
from .data_collector import collect_model_documentation

__all__ = [
    "render_word_report",
    "convert_to_pdf",
    "generate_relationship_graph",
    "generate_interactive_relationship_graph",
    "save_snapshot",
    "load_snapshot",
    "compute_diff",
    "compare_snapshots",
    "snapshot_from_context",
    "calculate_measure_complexity",
    "collect_model_documentation",
]
