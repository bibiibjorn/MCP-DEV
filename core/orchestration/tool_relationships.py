"""
Tool Relationship Metadata System

This module defines relationships between tools to enable intelligent tool orchestration.
It helps AI assistants understand which tools should be used together and in what sequence.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolRelationship:
    """Defines relationship between tools"""
    source_tool: str
    related_tool: str
    relationship_type: str  # "requires", "suggests", "enriches", "validates"
    when: str  # Condition when this relationship applies
    context_mapping: Dict[str, str]  # How to pass context from source to related
    priority: int  # 1-10, higher = more important
    description: str = ""  # Human-readable description of why this relationship exists


# Tool Relationship Registry
# This registry defines which tools work well together and should be suggested in sequence
TOOL_RELATIONSHIPS = [
    # ==================== Measure Analysis Domain ====================
    ToolRelationship(
        source_tool="get_measure_details",
        related_tool="analyze_measure_dependencies",
        relationship_type="suggests",
        when="always",
        context_mapping={"table": "table", "measure": "name"},
        priority=9,
        description="After getting measure details, analyze dependencies to understand what it references"
    ),
    ToolRelationship(
        source_tool="get_measure_details",
        related_tool="dax_intelligence",
        relationship_type="suggests",
        when="expression.length > 50",
        context_mapping={"expression": "expression", "analysis_mode": "'report'"},
        priority=8,
        description="For complex measures, analyze DAX patterns and context transitions"
    ),
    ToolRelationship(
        source_tool="get_measure_details",
        related_tool="get_measure_impact",
        relationship_type="suggests",
        when="always",
        context_mapping={"table": "table", "measure": "name"},
        priority=8,
        description="Check what other measures depend on this one"
    ),
    ToolRelationship(
        source_tool="analyze_measure_dependencies",
        related_tool="list_relationships",
        relationship_type="enriches",
        when="dependencies.tables.length > 1",
        context_mapping={},
        priority=7,
        description="When measure uses multiple tables, check relationships between them"
    ),
    ToolRelationship(
        source_tool="analyze_measure_dependencies",
        related_tool="get_measure_impact",
        relationship_type="enriches",
        when="always",
        context_mapping={"table": "table", "measure": "measure"},
        priority=6,
        description="After understanding dependencies, check impact on other measures"
    ),

    # ==================== Table Analysis Domain ====================
    ToolRelationship(
        source_tool="describe_table",
        related_tool="list_relationships",
        relationship_type="enriches",
        when="always",
        context_mapping={},
        priority=7,
        description="After describing table, check its relationships with other tables"
    ),
    ToolRelationship(
        source_tool="describe_table",
        related_tool="preview_table_data",
        relationship_type="suggests",
        when="row_count < 1000000",
        context_mapping={"table": "name"},
        priority=5,
        description="For smaller tables, preview sample data to understand content"
    ),
    ToolRelationship(
        source_tool="describe_table",
        related_tool="list_measures",
        relationship_type="enriches",
        when="always",
        context_mapping={},
        priority=6,
        description="Check what measures exist in this table"
    ),

    # ==================== Model Analysis Domain ====================
    ToolRelationship(
        source_tool="comprehensive_analysis",
        related_tool="list_relationships",
        relationship_type="requires",
        when="scope in ['all', 'integrity']",
        context_mapping={},
        priority=10,
        description="Comprehensive analysis requires relationship data for integrity checks"
    ),
    ToolRelationship(
        source_tool="list_relationships",
        related_tool="analyze_measure_dependencies",
        relationship_type="validates",
        when="inactive_relationships_exist",
        context_mapping={},
        priority=6,
        description="Check if inactive relationships are properly used with USERELATIONSHIP"
    ),
    ToolRelationship(
        source_tool="list_tables",
        related_tool="list_relationships",
        relationship_type="enriches",
        when="always",
        context_mapping={},
        priority=7,
        description="After listing tables, understand how they're connected"
    ),

    # ==================== DAX Analysis Domain ====================
    ToolRelationship(
        source_tool="dax_intelligence",
        related_tool="analyze_measure_dependencies",
        relationship_type="enriches",
        when="analysis_mode == 'report'",
        context_mapping={},
        priority=7,
        description="DAX intelligence can be enriched with actual dependency information"
    ),
    ToolRelationship(
        source_tool="run_dax",
        related_tool="dax_intelligence",
        relationship_type="suggests",
        when="execution_time > 1000",
        context_mapping={"expression": "query"},
        priority=8,
        description="For slow queries, analyze DAX patterns to find optimization opportunities"
    ),
    ToolRelationship(
        source_tool="dax_intelligence",
        related_tool="list_relationships",
        relationship_type="enriches",
        when="context_transitions > 0",
        context_mapping={},
        priority=6,
        description="When context transitions detected, check relationships for validation"
    ),

    # ==================== Documentation Domain ====================
    ToolRelationship(
        source_tool="generate_documentation",
        related_tool="comprehensive_analysis",
        relationship_type="requires",
        when="include_analysis == True",
        context_mapping={},
        priority=8,
        description="Documentation generation benefits from comprehensive analysis"
    ),

    # ==================== Modification Domain ====================
    ToolRelationship(
        source_tool="upsert_measure",
        related_tool="get_measure_impact",
        relationship_type="validates",
        when="mode == 'update'",
        context_mapping={"table": "table", "measure": "name"},
        priority=9,
        description="Before updating measure, check its impact on other measures"
    ),
    ToolRelationship(
        source_tool="delete_measure",
        related_tool="get_measure_impact",
        relationship_type="requires",
        when="always",
        context_mapping={"table": "table", "measure": "name"},
        priority=10,
        description="Before deleting measure, MUST check what depends on it"
    ),
]


def get_related_tools(
    tool_name: str,
    result: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Get suggested related tools based on current tool result

    Args:
        tool_name: Name of the tool that was just executed
        result: Result returned by the tool
        context: Optional additional context

    Returns:
        List of related tool suggestions sorted by priority
    """
    suggestions = []
    context = context or {}

    for rel in TOOL_RELATIONSHIPS:
        if rel.source_tool == tool_name:
            # Check if condition matches
            if should_suggest(rel, result, context):
                suggestion = {
                    'tool': rel.related_tool,
                    'reason': rel.relationship_type,
                    'priority': rel.priority,
                    'description': rel.description,
                    'context': map_context(rel.context_mapping, result, context)
                }
                suggestions.append(suggestion)

    # Sort by priority (highest first)
    return sorted(suggestions, key=lambda x: x['priority'], reverse=True)


def should_suggest(
    relationship: ToolRelationship,
    result: Dict[str, Any],
    context: Dict[str, Any]
) -> bool:
    """
    Determine if a relationship should trigger a suggestion

    Args:
        relationship: The tool relationship to evaluate
        result: Result from the source tool
        context: Additional context

    Returns:
        True if the suggestion should be made
    """
    condition = relationship.when

    # Always suggest
    if condition == "always":
        return True

    # Conditional suggestions
    try:
        # Simple expression evaluation
        if "expression.length" in condition:
            expression = result.get('expression', '')
            length = len(expression)
            # Extract threshold from condition (e.g., "expression.length > 50")
            if '>' in condition:
                threshold = int(condition.split('>')[-1].strip())
                return length > threshold

        if "dependencies.tables.length" in condition:
            dependencies = result.get('referenced_tables', [])
            length = len(dependencies)
            if '>' in condition:
                threshold = int(condition.split('>')[-1].strip())
                return length > threshold

        if "row_count" in condition:
            row_count = result.get('row_count', 0) or result.get('rows', 0)
            if '<' in condition:
                threshold = int(condition.split('<')[-1].strip())
                return row_count < threshold

        if "scope in" in condition:
            scope = result.get('scope', context.get('scope', ''))
            # Extract list from condition
            if 'all' in condition and scope == 'all':
                return True
            if 'integrity' in condition and scope == 'integrity':
                return True

        if "execution_time" in condition:
            exec_time = result.get('execution_time_ms', 0)
            if '>' in condition:
                threshold = int(condition.split('>')[-1].strip())
                return exec_time > threshold

        if "context_transitions" in condition:
            dax_analysis = result.get('dax_analysis', {})
            transitions = dax_analysis.get('context_transitions', {})
            count = transitions.get('count', 0)
            if '>' in condition:
                threshold = int(condition.split('>')[-1].strip())
                return count > threshold

        if "inactive_relationships_exist" in condition:
            rows = result.get('rows', [])
            return any(not r.get('isActive', True) for r in rows)

        if "analysis_mode ==" in condition:
            mode = result.get('analysis_mode', context.get('analysis_mode', ''))
            target_mode = condition.split('==')[-1].strip().strip("'\"")
            return mode == target_mode

        if "mode ==" in condition:
            mode = result.get('mode', context.get('mode', ''))
            target_mode = condition.split('==')[-1].strip().strip("'\"")
            return mode == target_mode

    except Exception as e:
        logger.debug(f"Error evaluating condition '{condition}': {e}")
        return False

    # Default: don't suggest if condition not understood
    return False


def map_context(
    mapping: Dict[str, str],
    result: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Map context from source tool result to target tool parameters

    Args:
        mapping: Context mapping definition
        result: Result from source tool
        context: Additional context

    Returns:
        Mapped context for target tool
    """
    mapped = {}

    for target_key, source_key in mapping.items():
        # Handle literal values (e.g., "'report'")
        if source_key.startswith("'") and source_key.endswith("'"):
            mapped[target_key] = source_key.strip("'")
            continue

        # Handle nested keys (e.g., "dependencies.tables")
        if '.' in source_key:
            parts = source_key.split('.')
            value = result
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = None
                    break
            if value is not None:
                mapped[target_key] = value
        else:
            # Direct key mapping
            value = result.get(source_key) or context.get(source_key)
            if value is not None:
                mapped[target_key] = value

    return mapped


def get_tool_relationship_graph() -> Dict[str, List[str]]:
    """
    Get a graph representation of tool relationships

    Returns:
        Dictionary mapping source tools to list of related tools
    """
    graph = {}
    for rel in TOOL_RELATIONSHIPS:
        if rel.source_tool not in graph:
            graph[rel.source_tool] = []
        graph[rel.source_tool].append(rel.related_tool)
    return graph


def get_workflow_suggestions(tools_used: List[str]) -> List[Dict[str, Any]]:
    """
    Suggest potential workflow optimizations based on tool usage pattern

    Args:
        tools_used: List of tool names that were used

    Returns:
        List of workflow suggestions
    """
    suggestions = []

    # Check for common patterns that could be workflows
    if 'get_measure_details' in tools_used and 'analyze_measure_dependencies' in tools_used:
        if 'dax_intelligence' in tools_used:
            suggestions.append({
                'workflow': 'complete_measure_analysis',
                'reason': 'You used multiple measure analysis tools - consider using complete_measure_analysis workflow',
                'tools_replaced': ['get_measure_details', 'analyze_measure_dependencies', 'dax_intelligence'],
                'benefit': 'Single call instead of 3+ calls, with synthesized insights'
            })

    if 'list_tables' in tools_used and 'list_measures' in tools_used and 'list_relationships' in tools_used:
        suggestions.append({
            'workflow': 'model_health_check',
            'reason': 'You listed multiple model components - consider model_health_check workflow',
            'tools_replaced': ['list_tables', 'list_measures', 'list_relationships', 'comprehensive_analysis'],
            'benefit': 'Complete model validation with prioritized issues'
        })

    return suggestions
