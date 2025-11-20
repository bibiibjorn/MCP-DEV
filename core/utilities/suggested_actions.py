"""
Suggested Actions Utility
Provides context-aware next action suggestions for tool responses
"""
from typing import Dict, Any, List, Optional

# Enable suggested actions - but AI should ALWAYS ask user before executing them
ENABLE_SUGGESTED_ACTIONS = True

def add_suggested_actions(
    result: Dict[str, Any],
    tool_name: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add suggested next actions to tool response based on tool name and context

    Args:
        result: The tool response dictionary
        tool_name: Name of the tool that generated this response
        context: Optional context information (e.g., table name, measure count)

    Returns:
        Updated result dictionary with suggested_actions field
    """
    if not ENABLE_SUGGESTED_ACTIONS:
        return result

    if not result.get('success'):
        return result

    context = context or {}
    suggestions = _get_suggestions_for_tool(tool_name, result, context)

    if suggestions:
        # Add clear notice that these are suggestions only - DO NOT auto-execute
        result['suggested_actions'] = {
            '_notice': '⚠️ SUGGESTIONS ONLY - Do not execute without explicit user approval',
            'suggestions': suggestions
        }
        result['workflow_hint'] = _get_workflow_hint(tool_name, result, context)

    return result


def _get_suggestions_for_tool(
    tool_name: str,
    result: Dict[str, Any],
    context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate suggestions based on tool name and result"""

    suggestions_map = {
        'list_tables': _suggest_after_list_tables,
        'describe_table': _suggest_after_describe_table,
        'list_measures': _suggest_after_list_measures,
        'list_columns': _suggest_after_list_columns,
        'get_measure_details': _suggest_after_measure_details,
        'preview_table_data': _suggest_after_preview_data,
        'run_dax': _suggest_after_run_dax,
        'search_objects': _suggest_after_search_objects,
        'list_relationships': _suggest_after_list_relationships,
        'comprehensive_analysis': _suggest_after_analysis,
        'connect_to_powerbi': _suggest_after_connection,
    }

    suggest_fn = suggestions_map.get(tool_name)
    if suggest_fn:
        return suggest_fn(result, context)

    return []


def _suggest_after_list_tables(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after listing tables"""
    rows = result.get('rows', [])
    if not rows:
        return []

    first_table = rows[0].get('TABLE_NAME') or rows[0].get('[TABLE_NAME]', 'Sales')

    return [
        {
            'action': 'explore_table',
            'description': 'Get detailed information about a specific table including columns, measures, and relationships',
            'tool': 'describe_table',
            'example': {'table': first_table}
        },
        {
            'action': 'preview_data',
            'description': 'Preview sample data from a table',
            'tool': 'preview_table_data',
            'example': {'table': first_table, 'max_rows': 10}
        },
        {
            'action': 'search_for_measures',
            'description': 'Find all measures in a table or across the model',
            'tool': 'list_measures',
            'example': {'table': first_table}
        },
        {
            'action': 'analyze_model',
            'description': 'Run comprehensive analysis to check for issues and optimization opportunities',
            'tool': 'comprehensive_analysis',
            'example': {'scope': 'all', 'depth': 'balanced'}
        }
    ]


def _suggest_after_describe_table(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after describing a table"""
    table_name = context.get('table') or result.get('table', 'YourTable')
    measures = result.get('measures', [])
    columns = result.get('columns', [])

    suggestions = [
        {
            'action': 'preview_data',
            'description': 'Preview sample data from this table',
            'tool': 'preview_table_data',
            'example': {'table': table_name, 'max_rows': 10}
        }
    ]

    if measures:
        first_measure = measures[0].get('MEASURE_NAME') or measures[0].get('[MEASURE_NAME]', 'TotalSales')
        suggestions.append({
            'action': 'analyze_measure',
            'description': 'Analyze a specific measure with DAX intelligence',
            'tool': 'dax_intelligence',
            'example': {'table': table_name, 'measure': first_measure, 'mode': 'analyze'}
        })
        suggestions.append({
            'action': 'check_dependencies',
            'description': 'Analyze measure dependencies',
            'tool': 'analyze_measure_dependencies',
            'example': {'table': table_name, 'measure': first_measure}
        })

    if columns:
        first_column = columns[0].get('COLUMN_NAME') or columns[0].get('[COLUMN_NAME]', 'Date')
        suggestions.append({
            'action': 'analyze_column',
            'description': 'Get value distribution for a column',
            'tool': 'get_column_value_distribution',
            'example': {'table': table_name, 'column': first_column, 'top_n': 10}
        })

    return suggestions


def _suggest_after_list_measures(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after listing measures"""
    rows = result.get('rows', [])
    if not rows:
        return []

    first_measure = rows[0].get('MEASURE_NAME') or rows[0].get('[MEASURE_NAME]', 'TotalSales')
    table_name = rows[0].get('TABLE_NAME') or rows[0].get('[TABLE_NAME]', 'Sales')

    return [
        {
            'action': 'get_details',
            'description': 'Get detailed information about a specific measure including DAX formula',
            'tool': 'get_measure_details',
            'example': {'table': table_name, 'measure': first_measure}
        },
        {
            'action': 'analyze_dax',
            'description': 'Analyze DAX formula with syntax validation and context analysis',
            'tool': 'dax_intelligence',
            'example': {'table': table_name, 'measure': first_measure, 'mode': 'analyze'}
        },
        {
            'action': 'check_dependencies',
            'description': 'Analyze dependencies for a measure',
            'tool': 'analyze_measure_dependencies',
            'example': {'table': table_name, 'measure': first_measure}
        },
        {
            'action': 'search_usage',
            'description': 'Search for measures using specific DAX functions or patterns',
            'tool': 'search_string',
            'example': {'search_text': 'CALCULATE', 'search_in_expression': True}
        }
    ]


def _suggest_after_list_columns(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after listing columns"""
    rows = result.get('rows', [])
    if not rows:
        return []

    first_column = rows[0].get('COLUMN_NAME') or rows[0].get('[COLUMN_NAME]', 'Date')
    table_name = rows[0].get('TABLE_NAME') or rows[0].get('[TABLE_NAME]', 'Sales')

    return [
        {
            'action': 'get_distribution',
            'description': 'Get value distribution for a column',
            'tool': 'get_column_value_distribution',
            'example': {'table': table_name, 'column': first_column, 'top_n': 10}
        },
        {
            'action': 'get_summary',
            'description': 'Get summary statistics for a column',
            'tool': 'get_column_summary',
            'example': {'table': table_name, 'column': first_column}
        },
        {
            'action': 'preview_data',
            'description': 'Preview sample data from the table',
            'tool': 'preview_table_data',
            'example': {'table': table_name, 'max_rows': 10}
        }
    ]


def _suggest_after_measure_details(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after getting measure details"""
    table = context.get('table') or result.get('table', 'Sales')
    measure = context.get('measure') or result.get('measure', 'TotalSales')

    return [
        {
            'action': 'analyze_dax',
            'description': 'Analyze this DAX formula for syntax, context transitions, and optimization',
            'tool': 'dax_intelligence',
            'example': {'table': table, 'measure': measure, 'mode': 'analyze'}
        },
        {
            'action': 'check_dependencies',
            'description': 'Analyze what this measure depends on',
            'tool': 'analyze_measure_dependencies',
            'example': {'table': table, 'measure': measure}
        },
        {
            'action': 'check_impact',
            'description': 'Check what other objects depend on this measure',
            'tool': 'get_measure_impact',
            'example': {'table': table, 'measure': measure}
        }
    ]


def _suggest_after_preview_data(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after previewing table data"""
    table = context.get('table', 'YourTable')

    return [
        {
            'action': 'describe_table',
            'description': 'Get full table structure with columns, measures, and relationships',
            'tool': 'describe_table',
            'example': {'table': table}
        },
        {
            'action': 'analyze_column',
            'description': 'Analyze column value distribution',
            'tool': 'get_column_value_distribution',
            'example': {'table': table, 'column': 'YourColumn', 'top_n': 10}
        },
        {
            'action': 'run_custom_query',
            'description': 'Run a custom DAX query on this table',
            'tool': 'run_dax',
            'example': {'query': f"EVALUATE TOPN(100, '{table}')", 'mode': 'auto'}
        }
    ]


def _suggest_after_run_dax(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after running a DAX query"""
    suggestions = [
        {
            'action': 'export_results',
            'description': 'Export model schema or TMDL for documentation',
            'tool': 'get_live_model_schema',
            'example': {'include_hidden': True}
        }
    ]

    # Check if query had performance issues
    if result.get('storage_engine_ms', 0) > 1000:
        suggestions.insert(0, {
            'action': 'optimize_performance',
            'description': 'Query took over 1 second - run comprehensive performance analysis',
            'tool': 'comprehensive_analysis',
            'example': {'scope': 'performance', 'depth': 'balanced'}
        })

    return suggestions


def _suggest_after_search_objects(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after searching objects"""
    items = result.get('items', result.get('rows', []))
    if not items:
        return []

    suggestions = []

    # Check what types of objects were found
    for item in items[:3]:  # Only check first 3
        obj_type = item.get('TYPE', '').lower()
        name = item.get('NAME', '')
        table = item.get('TABLE_NAME', '')

        if obj_type == 'table' and table:
            suggestions.append({
                'action': 'explore_table',
                'description': f'Explore {table} in detail',
                'tool': 'describe_table',
                'example': {'table': table}
            })
            break
        elif obj_type == 'measure' and name and table:
            suggestions.append({
                'action': 'analyze_measure',
                'description': f'Analyze {name} with DAX intelligence',
                'tool': 'dax_intelligence',
                'example': {'table': table, 'measure': name, 'mode': 'analyze'}
            })
            break

    return suggestions


def _suggest_after_list_relationships(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after listing relationships"""
    return [
        {
            'action': 'visualize_relationships',
            'description': 'Generate relationship graph visualization',
            'tool': 'generate_relationships_graph',
            'example': {}
        },
        {
            'action': 'analyze_integrity',
            'description': 'Check for relationship issues and best practices violations',
            'tool': 'comprehensive_analysis',
            'example': {'scope': 'integrity', 'depth': 'balanced'}
        }
    ]


def _suggest_after_analysis(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after comprehensive analysis"""
    issues = result.get('issues', [])

    suggestions = []

    if issues:
        # High priority: suggest reviewing specific issues
        high_severity_issues = [i for i in issues if i.get('severity') in ['high', 'critical']]
        if high_severity_issues:
            suggestions.append({
                'action': 'review_critical_issues',
                'description': 'Review and fix critical/high severity issues first',
                'note': f'Found {len(high_severity_issues)} high/critical issues'
            })

    suggestions.extend([
        {
            'action': 'export_documentation',
            'description': 'Generate Word documentation with these findings',
            'tool': 'generate_model_documentation_word',
            'example': {'file_path': 'model_documentation.docx'}
        }
    ])

    return suggestions


def _suggest_after_connection(result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Suggestions after connecting to Power BI (will be enhanced with proactive recommendations)"""
    return [
        {
            'action': 'explore_schema',
            'description': 'List all tables in the model',
            'tool': 'list_tables',
            'example': {}
        },
        {
            'action': 'quick_health_check',
            'description': 'Run a quick comprehensive analysis',
            'tool': 'comprehensive_analysis',
            'example': {'scope': 'all', 'depth': 'fast'}
        },
        {
            'action': 'search_model',
            'description': 'Search for specific objects in the model',
            'tool': 'search_objects',
            'example': {'pattern': '*', 'types': ['tables', 'measures']}
        }
    ]


def _get_workflow_hint(tool_name: str, result: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Generate a workflow hint message"""

    hints_map = {
        'list_tables': lambda r, c: f"Found {len(r.get('rows', []))} tables. Next: Explore a table with describe_table or run comprehensive_analysis for health check.",
        'describe_table': lambda r, c: f"Table '{c.get('table', 'table')}' has {len(r.get('columns', []))} columns and {len(r.get('measures', []))} measures. Next: Preview data or analyze measures.",
        'list_measures': lambda r, c: f"Found {len(r.get('rows', []))} measures. Next: Get details or analyze DAX with dax_intelligence.",
        'list_columns': lambda r, c: f"Found {len(r.get('rows', []))} columns. Next: Analyze value distribution or preview data.",
        'comprehensive_analysis': lambda r, c: f"Analysis complete. Found {len(r.get('issues', []))} issues. Next: Review findings and export documentation.",
        'connect_to_powerbi': lambda r, c: "Connected successfully. Next: Explore schema with list_tables or run comprehensive_analysis.",
    }

    hint_fn = hints_map.get(tool_name)
    if hint_fn:
        try:
            return hint_fn(result, context)
        except:
            return ""

    return ""
