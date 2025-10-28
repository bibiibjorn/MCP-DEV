"""
DAX Context Analysis Module

This module provides advanced DAX context analysis capabilities:
- Context transition detection (explicit CALCULATE, implicit measures, iterators)
- Filter context visualization (text, Mermaid, HTML)
- Step-by-step context debugging
- Performance impact assessment

Version: 3.0.0
"""

from .context_analyzer import (
    DaxContextAnalyzer,
    ContextTransition,
    ContextFlowExplanation,
    PerformanceWarning,
)
from .context_visualizer import FilterContextVisualizer
from .context_debugger import DaxContextDebugger, EvaluationStep, ContextExplanation

__all__ = [
    "DaxContextAnalyzer",
    "ContextTransition",
    "ContextFlowExplanation",
    "PerformanceWarning",
    "FilterContextVisualizer",
    "DaxContextDebugger",
    "EvaluationStep",
    "ContextExplanation",
]
