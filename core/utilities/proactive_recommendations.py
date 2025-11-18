"""
Proactive Recommendations Utility
Provides smart recommendations based on model characteristics after connection
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def get_connection_recommendations(connection_state) -> List[Dict[str, Any]]:
    """
    Generate proactive recommendations after connecting to Power BI Desktop
    based on quick health check of the model

    Args:
        connection_state: The connection state object with query executor

    Returns:
        List of recommendation dictionaries
    """
    try:
        recommendations = []

        # Run quick health checks
        health = _quick_health_check(connection_state)

        # Check model size (table count)
        table_count = health.get('table_count', 0)
        if table_count > 50:
            recommendations.append({
                'reason': f'Large model detected ({table_count} tables)',
                'suggestion': 'Run performance analysis to check for optimization opportunities',
                'priority': 'medium',
                'tool': 'comprehensive_analysis',
                'args': {'scope': 'performance', 'depth': 'fast'}
            })
        elif table_count > 100:
            recommendations.append({
                'reason': f'Very large model detected ({table_count}+ tables)',
                'suggestion': 'Consider using search_objects to find specific tables efficiently',
                'priority': 'high',
                'tool': 'search_objects',
                'args': {'pattern': '*', 'types': ['tables']}
            })

        # Check measure count
        measure_count = health.get('measure_count', 0)
        if measure_count > 100:
            recommendations.append({
                'reason': f'Model has {measure_count}+ measures',
                'suggestion': 'Consider using search to find specific measures efficiently',
                'priority': 'low',
                'tool': 'search_objects',
                'args': {'pattern': '*', 'types': ['measures']}
            })
        elif measure_count > 500:
            recommendations.append({
                'reason': f'Very large measure count ({measure_count}+ measures)',
                'suggestion': 'Run comprehensive analysis to check for duplicate or unused measures',
                'priority': 'medium',
                'tool': 'comprehensive_analysis',
                'args': {'scope': 'best_practices', 'depth': 'fast'}
            })

        # Check for bidirectional relationships
        if health.get('has_bidirectional_relationships'):
            recommendations.append({
                'reason': 'Bidirectional relationships detected',
                'suggestion': 'Review relationship configuration for potential issues',
                'priority': 'high',
                'tool': 'comprehensive_analysis',
                'args': {'scope': 'integrity', 'depth': 'balanced'},
                'warning': 'Bidirectional relationships can cause incorrect calculations'
            })

        # Check for inactive relationships
        inactive_rel_count = health.get('inactive_relationship_count', 0)
        if inactive_rel_count > 5:
            recommendations.append({
                'reason': f'{inactive_rel_count} inactive relationships found',
                'suggestion': 'Review inactive relationships to ensure they are intentional',
                'priority': 'low',
                'tool': 'list_relationships',
                'args': {'active_only': False}
            })

        # Check for calculated columns
        calc_column_count = health.get('calculated_column_count', 0)
        if calc_column_count > 20:
            recommendations.append({
                'reason': f'{calc_column_count} calculated columns detected',
                'suggestion': 'Review calculated columns for potential performance impact',
                'priority': 'medium',
                'tool': 'comprehensive_analysis',
                'args': {'scope': 'performance', 'depth': 'balanced'},
                'note': 'Consider converting to measures where possible'
            })

        # General recommendations if no specific issues
        if not recommendations:
            recommendations.append({
                'reason': 'Model appears healthy',
                'suggestion': 'Run a comprehensive analysis for detailed insights',
                'priority': 'low',
                'tool': 'comprehensive_analysis',
                'args': {'scope': 'all', 'depth': 'fast'}
            })

        return recommendations

    except Exception as e:
        logger.error(f"Error generating connection recommendations: {e}", exc_info=True)
        return [{
            'reason': 'Unable to generate recommendations',
            'suggestion': 'Use list_tables to explore the model',
            'priority': 'low',
            'tool': 'list_tables',
            'args': {}
        }]


def _quick_health_check(connection_state) -> Dict[str, Any]:
    """
    Perform a quick health check to gather model characteristics

    Args:
        connection_state: The connection state object

    Returns:
        Dictionary with health check results
    """
    health = {
        'table_count': 0,
        'measure_count': 0,
        'calculated_column_count': 0,
        'has_bidirectional_relationships': False,
        'inactive_relationship_count': 0
    }

    try:
        qe = connection_state.query_executor
        if not qe:
            return health

        # Get table count
        tables_result = qe.execute_info_query("TABLES")
        if tables_result.get('success'):
            health['table_count'] = len(tables_result.get('rows', []))

        # Get measure count
        measures_result = qe.execute_info_query("MEASURES")
        if measures_result.get('success'):
            health['measure_count'] = len(measures_result.get('rows', []))

        # Get relationships info
        relationships_result = qe.execute_info_query("RELATIONSHIPS")
        if relationships_result.get('success'):
            rows = relationships_result.get('rows', [])

            # Check for bidirectional relationships
            for row in rows:
                cross_filtering = str(row.get('CROSSFILTERINGBEHAVIOR', row.get('[CROSSFILTERINGBEHAVIOR]', ''))).upper()
                if 'BOTH' in cross_filtering:
                    health['has_bidirectional_relationships'] = True

                # Count inactive relationships
                is_active = row.get('ISACTIVE', row.get('[ISACTIVE]', True))
                if not is_active or str(is_active).upper() == 'FALSE':
                    health['inactive_relationship_count'] += 1

        # Get calculated columns count (approximate)
        from core.infrastructure.query_executor import COLUMN_TYPE_CALCULATED
        filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
        calc_cols_result = qe.execute_info_query("COLUMNS", filter_expr=filter_expr)
        if calc_cols_result.get('success'):
            health['calculated_column_count'] = len(calc_cols_result.get('rows', []))

    except Exception as e:
        logger.error(f"Error in quick health check: {e}", exc_info=True)

    return health


def format_recommendations_summary(recommendations: List[Dict[str, Any]]) -> str:
    """
    Format recommendations into a human-readable summary

    Args:
        recommendations: List of recommendation dictionaries

    Returns:
        Formatted summary string
    """
    if not recommendations:
        return "No specific recommendations at this time."

    lines = []
    lines.append(f"\nProactive Recommendations ({len(recommendations)}):")
    lines.append("-" * 50)

    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
    low_priority = [r for r in recommendations if r.get('priority') == 'low']

    def format_rec_group(priority_name, recs):
        if not recs:
            return []
        group_lines = [f"\n{priority_name.upper()} PRIORITY:"]
        for i, rec in enumerate(recs, 1):
            group_lines.append(f"  {i}. {rec['reason']}")
            group_lines.append(f"     → {rec['suggestion']}")
            if rec.get('warning'):
                group_lines.append(f"     ⚠️  {rec['warning']}")
        return group_lines

    lines.extend(format_rec_group("high", high_priority))
    lines.extend(format_rec_group("medium", medium_priority))
    lines.extend(format_rec_group("low", low_priority))

    return "\n".join(lines)
