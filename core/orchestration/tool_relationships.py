"""
Tool Relationship Metadata System

This module defines relationships between tools to enable intelligent tool orchestration.
It helps AI assistants understand which tools should be used together and in what sequence.

Enhanced in v6.5.0:
- Added inverse relationships for bidirectional tool suggestions
- Added workflow chains for multi-step analysis patterns
- Added issue-driven suggestions (BPA issues -> specific tool recommendations)
- Added contextual suggestions based on model characteristics
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolRelationship:
    """Defines relationship between tools"""
    source_tool: str
    related_tool: str
    relationship_type: str  # "requires", "suggests", "enriches", "validates", "inverse"
    when: str  # Condition when this relationship applies
    context_mapping: Dict[str, str]  # How to pass context from source to related
    priority: int  # 1-10, higher = more important
    description: str = ""  # Human-readable description of why this relationship exists
    bidirectional: bool = False  # If True, relationship works both ways


@dataclass
class WorkflowChain:
    """Defines a multi-step workflow pattern"""
    name: str
    description: str
    steps: List[Dict[str, Any]]  # List of {tool, context_from_previous, description}
    trigger_conditions: List[str]  # Conditions that suggest this workflow
    estimated_time: str  # e.g., "30-60 seconds"
    use_case: str  # When to use this workflow


# Pre-defined workflow chains for common analysis patterns
WORKFLOW_CHAINS = [
    WorkflowChain(
        name="complete_measure_audit",
        description="Comprehensive audit of a specific measure including dependencies, impact, and optimization",
        steps=[
            {"tool": "measure_operations", "args": {"operation": "get", "table": "{table}", "measure": "{measure}"}, "description": "Get measure details and DAX expression"},
            {"tool": "analyze_measure_dependencies", "args": {"table": "{table}", "measure": "{measure}"}, "description": "Analyze what this measure depends on"},
            {"tool": "get_measure_impact", "args": {"table": "{table}", "measure": "{measure}"}, "description": "Check what depends on this measure"},
            {"tool": "dax_intelligence", "args": {"table": "{table}", "measure": "{measure}", "mode": "analyze"}, "description": "Deep DAX analysis with optimization suggestions"},
        ],
        trigger_conditions=["user_wants_measure_analysis", "complex_measure_detected"],
        estimated_time="10-30 seconds",
        use_case="When investigating or optimizing a specific measure"
    ),
    WorkflowChain(
        name="model_health_check",
        description="Quick health check of the entire model",
        steps=[
            {"tool": "simple_analysis", "args": {}, "description": "Fast 8-operation model overview"},
            {"tool": "full_analysis", "args": {"scope": "best_practices", "timeout": 60}, "description": "BPA rule checking"},
        ],
        trigger_conditions=["first_connection", "model_changed", "user_requests_health_check"],
        estimated_time="15-60 seconds",
        use_case="After connecting to a new model or when checking overall model quality"
    ),
    WorkflowChain(
        name="performance_investigation",
        description="Investigate and optimize slow queries/measures",
        steps=[
            {"tool": "full_analysis", "args": {"scope": "performance"}, "description": "Identify performance issues"},
            {"tool": "dax_intelligence", "args": {"mode": "optimize"}, "description": "Optimize problematic measures"},
        ],
        trigger_conditions=["slow_query_detected", "performance_issues_reported"],
        estimated_time="30-120 seconds",
        use_case="When experiencing slow reports or investigating performance issues"
    ),
    WorkflowChain(
        name="dependency_cleanup",
        description="Find and clean up unused measures and dependencies",
        steps=[
            {"tool": "analyze_measure_dependencies", "args": {"find_unused": True}, "description": "Find measures with no dependents"},
            {"tool": "get_measure_impact", "args": {"batch": True}, "description": "Verify impact of each candidate"},
            {"tool": "batch_operations", "args": {"operation": "delete", "preview": True}, "description": "Preview cleanup operations"},
        ],
        trigger_conditions=["model_has_many_measures", "cleanup_requested"],
        estimated_time="30-90 seconds",
        use_case="When model has grown organically and needs cleanup"
    ),
    WorkflowChain(
        name="relationship_analysis",
        description="Analyze model relationships and their usage",
        steps=[
            {"tool": "relationship_operations", "args": {"operation": "list"}, "description": "List all relationships"},
            {"tool": "search_string", "args": {"search_text": "USERELATIONSHIP"}, "description": "Find measures using inactive relationships"},
            {"tool": "full_analysis", "args": {"scope": "integrity"}, "description": "Check relationship integrity"},
        ],
        trigger_conditions=["many_inactive_relationships", "bidirectional_relationships_detected"],
        estimated_time="20-60 seconds",
        use_case="When investigating relationship configuration or fixing relationship issues"
    ),
]


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

    # ==================== Inverse Relationships (v6.5.0) ====================
    # These allow suggestions to work in both directions
    ToolRelationship(
        source_tool="get_measure_impact",
        related_tool="analyze_measure_dependencies",
        relationship_type="inverse",
        when="always",
        context_mapping={"table": "table", "measure": "name"},
        priority=7,
        description="After checking impact, also analyze what this measure depends on",
        bidirectional=True
    ),
    ToolRelationship(
        source_tool="analyze_measure_dependencies",
        related_tool="dax_intelligence",
        relationship_type="suggests",
        when="has_complex_dependencies",
        context_mapping={"table": "table", "measure": "measure"},
        priority=8,
        description="Deep dependency chains benefit from DAX analysis"
    ),

    # ==================== PBIP/Hybrid Analysis Domain (v6.5.0) ====================
    ToolRelationship(
        source_tool="analyze_pbip_repository",
        related_tool="export_hybrid_analysis",
        relationship_type="suggests",
        when="always",
        context_mapping={},
        priority=6,
        description="After PBIP analysis, export hybrid package for deeper analysis"
    ),
    ToolRelationship(
        source_tool="export_hybrid_analysis",
        related_tool="analyze_hybrid_model",
        relationship_type="suggests",
        when="always",
        context_mapping={"export_path": "path"},
        priority=9,
        description="After exporting, analyze the hybrid model"
    ),

    # ==================== BPA Issue-Driven Suggestions (v6.5.0) ====================
    ToolRelationship(
        source_tool="full_analysis",
        related_tool="dax_intelligence",
        relationship_type="suggests",
        when="has_dax_issues",
        context_mapping={},
        priority=8,
        description="When BPA finds DAX issues, use dax_intelligence to investigate"
    ),
    ToolRelationship(
        source_tool="full_analysis",
        related_tool="batch_operations",
        relationship_type="suggests",
        when="has_unused_objects",
        context_mapping={},
        priority=7,
        description="When unused objects found, suggest batch cleanup"
    ),
    ToolRelationship(
        source_tool="simple_analysis",
        related_tool="full_analysis",
        relationship_type="suggests",
        when="issues_detected",
        context_mapping={},
        priority=8,
        description="After simple analysis finds issues, run full analysis for details"
    ),

    # ==================== Search Result Suggestions (v6.5.0) ====================
    ToolRelationship(
        source_tool="search_objects",
        related_tool="dax_intelligence",
        relationship_type="suggests",
        when="found_measures",
        context_mapping={},
        priority=7,
        description="When search finds measures, offer to analyze them"
    ),
    ToolRelationship(
        source_tool="search_string",
        related_tool="dax_intelligence",
        relationship_type="suggests",
        when="found_dax_patterns",
        context_mapping={},
        priority=7,
        description="When DAX pattern search finds results, analyze them"
    ),
]

# Issue category to tool mapping for intelligent suggestions
ISSUE_TO_TOOL_MAPPING = {
    "performance": ["dax_intelligence", "full_analysis"],
    "anti_pattern": ["dax_intelligence"],
    "unused_measure": ["get_measure_impact", "batch_operations"],
    "missing_description": ["measure_operations"],
    "naming_convention": ["tmdl_operations"],
    "relationship_issue": ["relationship_operations", "full_analysis"],
    "bidirectional_relationship": ["relationship_operations"],
    "high_cardinality": ["column_operations"],
    "circular_dependency": ["analyze_measure_dependencies"],
}


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

        # New conditions for v6.5.0
        if condition == "has_complex_dependencies":
            # Check if there are multiple levels of dependencies
            dep_tree = result.get('dependency_tree', {})
            depth = result.get('metrics', {}).get('max_depth_reached', 0)
            return depth > 2

        if condition == "has_dax_issues":
            # Check if BPA found DAX-related issues
            issues = result.get('issues', [])
            dax_categories = ['performance', 'anti_pattern', 'dax_complexity']
            return any(i.get('category') in dax_categories for i in issues)

        if condition == "has_unused_objects":
            # Check if analysis found unused measures/columns
            summary = result.get('summary', {})
            return summary.get('unused_measures', 0) > 0 or summary.get('unused_columns', 0) > 0

        if condition == "issues_detected":
            # Check if any issues were found
            issues = result.get('issues', [])
            warnings = result.get('warnings', [])
            return len(issues) > 0 or len(warnings) > 0

        if condition == "found_measures":
            # Check if search results include measures
            items = result.get('items', result.get('rows', []))
            return any(i.get('TYPE', '').lower() == 'measure' for i in items)

        if condition == "found_dax_patterns":
            # Check if DAX pattern search found results
            matches = result.get('matches', result.get('rows', []))
            return len(matches) > 0

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


# ==================== New v6.5.0 Functions ====================

def get_workflow_chain(name: str) -> Optional[WorkflowChain]:
    """
    Get a workflow chain by name.

    Args:
        name: Name of the workflow chain

    Returns:
        WorkflowChain if found, None otherwise
    """
    for wf in WORKFLOW_CHAINS:
        if wf.name == name:
            return wf
    return None


def get_suggested_workflow(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Suggest the best workflow based on current context.

    Args:
        context: Dictionary with keys like:
            - first_connection: bool
            - model_size: int (number of tables)
            - measure_count: int
            - has_issues: bool
            - issue_types: List[str]
            - user_intent: str

    Returns:
        Workflow suggestion or None
    """
    # Check trigger conditions
    for wf in WORKFLOW_CHAINS:
        for trigger in wf.trigger_conditions:
            if _matches_trigger(trigger, context):
                return {
                    'workflow': wf.name,
                    'description': wf.description,
                    'steps': wf.steps,
                    'estimated_time': wf.estimated_time,
                    'use_case': wf.use_case,
                    'reason': f"Triggered by: {trigger}"
                }
    return None


def _matches_trigger(trigger: str, context: Dict[str, Any]) -> bool:
    """Check if a trigger condition matches the context"""
    if trigger == "first_connection" and context.get('first_connection'):
        return True
    if trigger == "model_changed" and context.get('model_changed'):
        return True
    if trigger == "user_requests_health_check" and 'health' in context.get('user_intent', '').lower():
        return True
    if trigger == "slow_query_detected" and context.get('slow_query_detected'):
        return True
    if trigger == "performance_issues_reported" and 'performance' in context.get('issue_types', []):
        return True
    if trigger == "model_has_many_measures" and context.get('measure_count', 0) > 100:
        return True
    if trigger == "cleanup_requested" and 'cleanup' in context.get('user_intent', '').lower():
        return True
    if trigger == "many_inactive_relationships" and context.get('inactive_relationship_count', 0) > 3:
        return True
    if trigger == "bidirectional_relationships_detected" and context.get('has_bidirectional_relationships'):
        return True
    if trigger == "user_wants_measure_analysis" and 'measure' in context.get('user_intent', '').lower():
        return True
    if trigger == "complex_measure_detected" and context.get('measure_complexity', 0) > 3:
        return True
    return False


def get_tools_for_issue(issue_category: str) -> List[str]:
    """
    Get recommended tools for addressing a specific issue category.

    Args:
        issue_category: Category of the issue (e.g., 'performance', 'anti_pattern')

    Returns:
        List of recommended tool names
    """
    return ISSUE_TO_TOOL_MAPPING.get(issue_category.lower(), [])


def get_inverse_suggestions(
    tool_name: str,
    result: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Get suggestions for inverse relationships (tools that should have been run before).

    Args:
        tool_name: Name of the current tool
        result: Result from the tool
        context: Optional additional context

    Returns:
        List of suggestions for tools that could have provided useful context
    """
    suggestions = []
    context = context or {}

    for rel in TOOL_RELATIONSHIPS:
        if rel.related_tool == tool_name and rel.bidirectional:
            suggestion = {
                'tool': rel.source_tool,
                'reason': 'could_have_provided_context',
                'priority': rel.priority,
                'description': f"Consider running {rel.source_tool} for additional context",
                'context': map_context(rel.context_mapping, result, context)
            }
            suggestions.append(suggestion)

    return sorted(suggestions, key=lambda x: x['priority'], reverse=True)


def get_complete_tool_graph() -> Dict[str, Any]:
    """
    Get a complete graph of tool relationships including workflows.

    Returns:
        Dictionary with tool nodes and relationship edges
    """
    nodes = set()
    edges = []

    # Add tool relationships
    for rel in TOOL_RELATIONSHIPS:
        nodes.add(rel.source_tool)
        nodes.add(rel.related_tool)
        edges.append({
            'source': rel.source_tool,
            'target': rel.related_tool,
            'type': rel.relationship_type,
            'priority': rel.priority,
            'bidirectional': rel.bidirectional
        })

    # Add workflow chains
    workflows = []
    for wf in WORKFLOW_CHAINS:
        workflow_tools = [step['tool'] for step in wf.steps]
        workflows.append({
            'name': wf.name,
            'tools': workflow_tools,
            'description': wf.description
        })
        for tool in workflow_tools:
            nodes.add(tool)

    return {
        'nodes': sorted(nodes),
        'edges': edges,
        'workflows': workflows,
        'statistics': {
            'total_tools': len(nodes),
            'total_relationships': len(edges),
            'total_workflows': len(workflows)
        }
    }


def suggest_next_actions_from_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate intelligent next action suggestions based on BPA/analysis issues.

    Args:
        issues: List of issue dictionaries with 'category', 'severity', 'object', etc.

    Returns:
        List of suggested actions with tools and context
    """
    suggestions = []
    seen_tools = set()

    # Group issues by category and priority
    critical_issues = [i for i in issues if i.get('severity') in ['critical', 'error']]
    high_issues = [i for i in issues if i.get('severity') == 'high']
    other_issues = [i for i in issues if i.get('severity') not in ['critical', 'error', 'high']]

    # Process critical issues first
    for issue in critical_issues + high_issues:
        category = issue.get('category', '').lower()
        tools = get_tools_for_issue(category)

        for tool in tools:
            if tool not in seen_tools:
                seen_tools.add(tool)
                suggestions.append({
                    'tool': tool,
                    'priority': 10 if issue.get('severity') == 'critical' else 8,
                    'reason': f"Address {issue.get('severity', 'high')} severity {category} issue",
                    'issue_context': {
                        'object': issue.get('object', ''),
                        'message': issue.get('message', ''),
                        'category': category
                    }
                })

    # Add general suggestions for patterns
    if len([i for i in issues if i.get('category') == 'performance']) > 3:
        if 'full_analysis' not in seen_tools:
            suggestions.append({
                'tool': 'full_analysis',
                'priority': 7,
                'reason': 'Multiple performance issues detected - run comprehensive performance analysis',
                'args': {'scope': 'performance'}
            })

    if len([i for i in issues if i.get('category') == 'unused_measure']) > 5:
        suggestions.append({
            'tool': 'batch_operations',
            'priority': 6,
            'reason': f"Found {len([i for i in issues if i.get('category') == 'unused_measure'])} unused measures - consider batch cleanup",
            'args': {'operation': 'delete', 'preview': True}
        })

    return sorted(suggestions, key=lambda x: x.get('priority', 0), reverse=True)
