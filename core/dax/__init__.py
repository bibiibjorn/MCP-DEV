"""
DAX Context Analysis Module

This module provides advanced DAX context analysis capabilities:
- Context transition detection (explicit CALCULATE, implicit measures, iterators)
- Filter context visualization (text, Mermaid, HTML)
- Step-by-step context debugging
- Performance impact assessment
- VertiPaq column metrics integration
- Call tree hierarchy visualization
- Calculation group analysis
- Advanced DAX code rewriting
- Variable optimization scanning
- Visual context flow diagrams

Version: 4.0.0 - Enhanced with industry-standard analysis features
"""

from .context_analyzer import (
    DaxContextAnalyzer,
    ContextTransition,
    ContextFlowExplanation,
    PerformanceWarning,
)
from .context_visualizer import FilterContextVisualizer
from .context_debugger import DaxContextDebugger, EvaluationStep, ContextExplanation
from .vertipaq_analyzer import VertiPaqAnalyzer, ColumnMetrics, CardinalityImpact
from .call_tree_builder import CallTreeBuilder, CallTreeNode, NodeType
from .calculation_group_analyzer import (
    CalculationGroupAnalyzer,
    CalculationGroup,
    PrecedenceConflict,
    CalculationGroupIssue,
)
from .code_rewriter import (
    DaxCodeRewriter,
    VariableOptimizationScanner,
    Transformation,
)
from .visual_flow import VisualFlowDiagramGenerator, FlowStep

__all__ = [
    # Core analyzers
    "DaxContextAnalyzer",
    "ContextTransition",
    "ContextFlowExplanation",
    "PerformanceWarning",
    "FilterContextVisualizer",
    "DaxContextDebugger",
    "EvaluationStep",
    "ContextExplanation",
    # VertiPaq integration
    "VertiPaqAnalyzer",
    "ColumnMetrics",
    "CardinalityImpact",
    # Call tree
    "CallTreeBuilder",
    "CallTreeNode",
    "NodeType",
    # Calculation groups
    "CalculationGroupAnalyzer",
    "CalculationGroup",
    "PrecedenceConflict",
    "CalculationGroupIssue",
    # Code rewriting
    "DaxCodeRewriter",
    "VariableOptimizationScanner",
    "Transformation",
    # Visual flow
    "VisualFlowDiagramGenerator",
    "FlowStep",
]
