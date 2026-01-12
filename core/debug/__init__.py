"""
Debug module for Power BI visual debugging and validation.

Provides tools for:
- Converting PBIP filters to DAX expressions
- Building queries that reproduce visual behavior
- Comparing measure results with filter context
- Drilling to detail rows
- Filter classification (data vs UI control vs field parameter)
- Cross-visual validation and expected value testing
- Page profiling and filter performance matrix
- Report documentation and lineage analysis
- Advanced analysis (decompose, contribution, trend, root cause)
"""

from .filter_to_dax import (
    FilterToDaxConverter,
    FilterExpression,
    FilterClassification,
    TypedValue,
    is_field_parameter_table,
    is_ui_control_table,
    classify_filter,
)
from .visual_query_builder import VisualQueryBuilder, FilterContext, VisualInfo
from .debug_operations import DebugOperations

__all__ = [
    'FilterToDaxConverter',
    'FilterExpression',
    'FilterClassification',
    'TypedValue',
    'VisualQueryBuilder',
    'FilterContext',
    'VisualInfo',
    'DebugOperations',
    'is_field_parameter_table',
    'is_ui_control_table',
    'classify_filter',
]
