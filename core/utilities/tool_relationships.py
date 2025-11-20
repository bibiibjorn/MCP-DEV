"""
Tool Relationship Metadata
Defines relationships between tools for improved workflow guidance
"""
from typing import Dict, List, Set, Optional
import logging

logger = logging.getLogger(__name__)


# Tool relationship graph - defines workflow connections between tools
TOOL_RELATIONSHIPS = {
    # Connection Tools
    'detect_powerbi_desktop': {
        'common_next_steps': ['connect_to_powerbi'],
        'prerequisites': [],
        'alternatives': [],
        'category': 'connection',
        'workflow_stage': 'initialization'
    },
    'connect_to_powerbi': {
        'common_next_steps': ['list_tables', 'comprehensive_analysis', 'search_objects'],
        'prerequisites': ['detect_powerbi_desktop'],  # Optional, can auto-detect
        'alternatives': [],
        'category': 'connection',
        'workflow_stage': 'initialization'
    },

    # Schema/Metadata Tools
    'list_tables': {
        'common_next_steps': ['describe_table', 'preview_table_data', 'list_measures'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['search_objects'],
        'category': 'metadata',
        'workflow_stage': 'exploration'
    },
    'describe_table': {
        'common_next_steps': ['preview_table_data', 'get_measure_details', 'analyze_measure_dependencies'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': [],
        'category': 'metadata',
        'workflow_stage': 'exploration'
    },
    'list_columns': {
        'common_next_steps': ['get_column_value_distribution', 'get_column_summary', 'preview_table_data'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['describe_table'],
        'category': 'metadata',
        'workflow_stage': 'exploration'
    },
    'list_measures': {
        'common_next_steps': ['get_measure_details', 'dax_intelligence', 'analyze_measure_dependencies'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['search_string', 'search_objects'],
        'category': 'metadata',
        'workflow_stage': 'exploration'
    },
    'get_measure_details': {
        'common_next_steps': ['dax_intelligence', 'analyze_measure_dependencies', 'get_measure_impact'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': [],
        'category': 'metadata',
        'workflow_stage': 'analysis'
    },
    'search_objects': {
        'common_next_steps': ['describe_table', 'get_measure_details', 'preview_table_data'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['list_tables', 'list_measures', 'search_string'],
        'category': 'metadata',
        'workflow_stage': 'exploration'
    },
    'search_string': {
        'common_next_steps': ['get_measure_details', 'dax_intelligence'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['search_objects', 'list_measures'],
        'category': 'metadata',
        'workflow_stage': 'exploration'
    },

    # Query & DAX Tools
    'preview_table_data': {
        'common_next_steps': ['describe_table', 'get_column_value_distribution', 'run_dax'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['run_dax'],
        'category': 'query',
        'workflow_stage': 'exploration'
    },
    'run_dax': {
        'common_next_steps': ['dax_intelligence', 'get_live_model_schema'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['preview_table_data'],
        'category': 'query',
        'workflow_stage': 'analysis'
    },
    'dax_intelligence': {
        'common_next_steps': ['analyze_measure_dependencies', 'get_measure_impact', 'upsert_measure'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': [],
        'category': 'dax_analysis',
        'workflow_stage': 'development'
    },
    'get_column_value_distribution': {
        'common_next_steps': ['get_column_summary', 'comprehensive_analysis'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['get_column_summary'],
        'category': 'query',
        'workflow_stage': 'analysis'
    },
    'get_column_summary': {
        'common_next_steps': ['get_column_value_distribution', 'comprehensive_analysis'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['get_column_value_distribution'],
        'category': 'query',
        'workflow_stage': 'analysis'
    },
    'list_relationships': {
        'common_next_steps': ['generate_relationships_graph', 'comprehensive_analysis'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['describe_table'],
        'category': 'query',
        'workflow_stage': 'exploration'
    },

    # Analysis Tools
    'comprehensive_analysis': {
        'common_next_steps': ['generate_model_documentation_word', 'get_live_model_schema'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': [],
        'category': 'analysis',
        'workflow_stage': 'analysis'
    },

    # Dependencies
    'analyze_measure_dependencies': {
        'common_next_steps': ['get_measure_impact', 'dax_intelligence'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['get_measure_impact'],
        'category': 'dependencies',
        'workflow_stage': 'analysis'
    },
    'get_measure_impact': {
        'common_next_steps': ['analyze_measure_dependencies', 'delete_measure'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['analyze_measure_dependencies'],
        'category': 'dependencies',
        'workflow_stage': 'analysis'
    },

    # Model Operations
    'upsert_measure': {
        'common_next_steps': ['dax_intelligence', 'get_measure_details', 'analyze_measure_dependencies'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['bulk_create_measures'],
        'category': 'model_operations',
        'workflow_stage': 'development'
    },
    'delete_measure': {
        'common_next_steps': ['list_measures'],
        'prerequisites': ['connect_to_powerbi', 'get_measure_impact'],  # Should check impact first
        'alternatives': ['bulk_delete_measures'],
        'category': 'model_operations',
        'workflow_stage': 'maintenance'
    },
    'bulk_create_measures': {
        'common_next_steps': ['list_measures', 'comprehensive_analysis'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['upsert_measure'],
        'category': 'model_operations',
        'workflow_stage': 'development'
    },
    'bulk_delete_measures': {
        'common_next_steps': ['list_measures'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['delete_measure'],
        'category': 'model_operations',
        'workflow_stage': 'maintenance'
    },

    # Export & Documentation
    'get_live_model_schema': {
        'common_next_steps': ['export_tmdl'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['export_tmdl'],
        'category': 'export',
        'workflow_stage': 'documentation'
    },
    'export_tmdl': {
        'common_next_steps': ['tmdl_find_replace', 'tmdl_bulk_rename'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': ['get_live_model_schema'],
        'category': 'export',
        'workflow_stage': 'documentation'
    },
    'generate_model_documentation_word': {
        'common_next_steps': ['update_model_documentation_word'],
        'prerequisites': ['connect_to_powerbi'],
        'alternatives': [],
        'category': 'documentation',
        'workflow_stage': 'documentation'
    },
    'update_model_documentation_word': {
        'common_next_steps': [],
        'prerequisites': ['connect_to_powerbi', 'generate_model_documentation_word'],
        'alternatives': [],
        'category': 'documentation',
        'workflow_stage': 'documentation'
    },

    # Comparison
    'compare_pbi_models': {
        'common_next_steps': ['generate_model_documentation_word'],
        'prerequisites': [],  # Needs 2 Power BI instances open, detects and compares in one tool
        'alternatives': [],
        'category': 'comparison',
        'workflow_stage': 'comparison'
    },

    # PBIP & TMDL
    'analyze_pbip_repository': {
        'common_next_steps': [],
        'prerequisites': [],  # Offline tool, no connection needed
        'alternatives': [],
        'category': 'pbip',
        'workflow_stage': 'offline_analysis'
    },
    'tmdl_find_replace': {
        'common_next_steps': ['export_tmdl'],
        'prerequisites': [],
        'alternatives': ['tmdl_bulk_rename'],
        'category': 'tmdl',
        'workflow_stage': 'maintenance'
    },
    'tmdl_bulk_rename': {
        'common_next_steps': ['export_tmdl'],
        'prerequisites': [],
        'alternatives': ['tmdl_find_replace'],
        'category': 'tmdl',
        'workflow_stage': 'maintenance'
    },

    # Hybrid Analysis
    'export_hybrid_analysis': {
        'common_next_steps': ['analyze_hybrid_model'],
        'prerequisites': [],
        'alternatives': [],
        'category': 'hybrid',
        'workflow_stage': 'offline_analysis'
    },
    'analyze_hybrid_model': {
        'common_next_steps': ['generate_model_documentation_word'],
        'prerequisites': ['export_hybrid_analysis'],
        'alternatives': [],
        'category': 'hybrid',
        'workflow_stage': 'offline_analysis'
    },
}


def get_tool_metadata(tool_name: str) -> Optional[Dict]:
    """Get metadata for a specific tool"""
    return TOOL_RELATIONSHIPS.get(tool_name)


def get_next_steps(tool_name: str) -> List[str]:
    """Get common next steps after using a tool"""
    metadata = get_tool_metadata(tool_name)
    if metadata:
        return metadata.get('common_next_steps', [])
    return []


def get_prerequisites(tool_name: str) -> List[str]:
    """Get prerequisites for a tool"""
    metadata = get_tool_metadata(tool_name)
    if metadata:
        return metadata.get('prerequisites', [])
    return []


def get_alternatives(tool_name: str) -> List[str]:
    """Get alternative tools that serve similar purposes"""
    metadata = get_tool_metadata(tool_name)
    if metadata:
        return metadata.get('alternatives', [])
    return []


def get_workflow_stage(tool_name: str) -> Optional[str]:
    """Get the workflow stage for a tool"""
    metadata = get_tool_metadata(tool_name)
    if metadata:
        return metadata.get('workflow_stage')
    return None


def get_tools_by_category(category: str) -> List[str]:
    """Get all tools in a specific category"""
    return [
        tool_name for tool_name, metadata in TOOL_RELATIONSHIPS.items()
        if metadata.get('category') == category
    ]


def get_tools_by_workflow_stage(stage: str) -> List[str]:
    """Get all tools for a specific workflow stage"""
    return [
        tool_name for tool_name, metadata in TOOL_RELATIONSHIPS.items()
        if metadata.get('workflow_stage') == stage
    ]


def suggest_workflow(goal: str) -> List[str]:
    """
    Suggest a workflow based on a high-level goal

    Args:
        goal: User's goal (e.g., 'explore', 'analyze', 'optimize', 'document')

    Returns:
        List of recommended tools in order
    """
    workflows = {
        'explore': [
            'connect_to_powerbi',
            'list_tables',
            'describe_table',
            'preview_table_data',
            'list_measures'
        ],
        'analyze': [
            'connect_to_powerbi',
            'comprehensive_analysis',
            'analyze_measure_dependencies',
            'dax_intelligence'
        ],
        'optimize': [
            'connect_to_powerbi',
            'comprehensive_analysis',
            'dax_intelligence',
            'analyze_measure_dependencies'
        ],
        'document': [
            'connect_to_powerbi',
            'comprehensive_analysis',
            'generate_model_documentation_word'
        ],
        'develop': [
            'connect_to_powerbi',
            'list_measures',
            'get_measure_details',
            'dax_intelligence',
            'upsert_measure'
        ],
        'compare': [
            'compare_pbi_models',
            'generate_model_documentation_word'
        ],
        'offline': [
            'analyze_pbip_repository'
        ]
    }

    return workflows.get(goal.lower(), workflows['explore'])


def validate_workflow(tool_sequence: List[str]) -> Dict[str, any]:
    """
    Validate a tool sequence for missing prerequisites or illogical flows

    Args:
        tool_sequence: List of tool names in order

    Returns:
        Validation result with warnings and suggestions
    """
    warnings = []
    suggestions = []
    seen_tools = set()

    for i, tool in enumerate(tool_sequence):
        metadata = get_tool_metadata(tool)
        if not metadata:
            warnings.append(f"Unknown tool: {tool}")
            continue

        # Check prerequisites
        prerequisites = metadata.get('prerequisites', [])
        for prereq in prerequisites:
            if prereq not in seen_tools:
                warnings.append(f"{tool} requires {prereq} but it hasn't been used yet")
                suggestions.append(f"Add {prereq} before {tool}")

        seen_tools.add(tool)

        # Suggest better next steps
        if i < len(tool_sequence) - 1:
            next_tool = tool_sequence[i + 1]
            common_next = metadata.get('common_next_steps', [])
            if next_tool not in common_next and common_next:
                suggestions.append(
                    f"After {tool}, consider: {', '.join(common_next[:3])} instead of {next_tool}"
                )

    return {
        'valid': len(warnings) == 0,
        'warnings': warnings,
        'suggestions': suggestions
    }
