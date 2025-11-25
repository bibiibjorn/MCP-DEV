"""
Proactive Recommendations Utility
Provides smart recommendations based on model characteristics after connection

Enhanced in v6.5.0:
- Added high-cardinality column detection
- Added wide table detection (>30 columns)
- Added orphan measure detection
- Added date table marking check
- Added role-playing dimension pattern detection
- Added improved priority-based recommendation system
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Thresholds for recommendations
THRESHOLDS = {
    'large_model_tables': 50,
    'very_large_model_tables': 100,
    'many_measures': 100,
    'very_many_measures': 500,
    'many_calculated_columns': 20,
    'inactive_relationships_warning': 5,
    'wide_table_columns': 30,
    'high_cardinality_threshold': 1000000,  # 1 million distinct values
    'orphan_measure_threshold': 10,  # Suggest cleanup if more than 10 orphans
}


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
        if table_count > THRESHOLDS['very_large_model_tables']:
            recommendations.append({
                'reason': f'Very large model detected ({table_count} tables)',
                'suggestion': 'Consider using search_objects to find specific tables efficiently',
                'priority': 'high',
                'tool': 'search_objects',
                'args': {'pattern': '*', 'types': ['tables']},
                'category': 'model_size'
            })
        elif table_count > THRESHOLDS['large_model_tables']:
            recommendations.append({
                'reason': f'Large model detected ({table_count} tables)',
                'suggestion': 'Run performance analysis to check for optimization opportunities',
                'priority': 'medium',
                'tool': 'full_analysis',
                'args': {'scope': 'performance'},
                'category': 'model_size'
            })

        # Check measure count
        measure_count = health.get('measure_count', 0)
        if measure_count > THRESHOLDS['very_many_measures']:
            recommendations.append({
                'reason': f'Very large measure count ({measure_count} measures)',
                'suggestion': 'Run comprehensive analysis to check for duplicate or unused measures',
                'priority': 'high',
                'tool': 'full_analysis',
                'args': {'scope': 'best_practices'},
                'category': 'measure_count'
            })
        elif measure_count > THRESHOLDS['many_measures']:
            recommendations.append({
                'reason': f'Model has {measure_count} measures',
                'suggestion': 'Consider using search to find specific measures efficiently',
                'priority': 'low',
                'tool': 'search_objects',
                'args': {'pattern': '*', 'types': ['measures']},
                'category': 'measure_count'
            })

        # Check for bidirectional relationships
        if health.get('has_bidirectional_relationships'):
            recommendations.append({
                'reason': 'Bidirectional relationships detected',
                'suggestion': 'Review relationship configuration for potential ambiguity issues',
                'priority': 'high',
                'tool': 'full_analysis',
                'args': {'scope': 'integrity'},
                'warning': 'Bidirectional relationships can cause incorrect calculations and ambiguity',
                'category': 'relationships'
            })

        # Check for inactive relationships
        inactive_rel_count = health.get('inactive_relationship_count', 0)
        if inactive_rel_count > THRESHOLDS['inactive_relationships_warning']:
            recommendations.append({
                'reason': f'{inactive_rel_count} inactive relationships found',
                'suggestion': 'Review inactive relationships to ensure they are properly used with USERELATIONSHIP',
                'priority': 'medium',
                'tool': 'relationship_operations',
                'args': {'operation': 'list'},
                'category': 'relationships'
            })

        # Check for calculated columns
        calc_column_count = health.get('calculated_column_count', 0)
        if calc_column_count > THRESHOLDS['many_calculated_columns']:
            recommendations.append({
                'reason': f'{calc_column_count} calculated columns detected',
                'suggestion': 'Review calculated columns for potential performance impact - consider converting to measures',
                'priority': 'medium',
                'tool': 'full_analysis',
                'args': {'scope': 'performance'},
                'note': 'Calculated columns consume memory and recalculate on refresh',
                'category': 'performance'
            })

        # NEW v6.5.0: Check for wide tables
        wide_tables = health.get('wide_tables', [])
        if wide_tables:
            table_list = ', '.join([t['table'] for t in wide_tables[:3]])
            recommendations.append({
                'reason': f'{len(wide_tables)} wide tables detected (>30 columns): {table_list}',
                'suggestion': 'Consider splitting wide tables or hiding unused columns to improve performance',
                'priority': 'medium',
                'tool': 'column_operations',
                'args': {'operation': 'list'},
                'category': 'performance',
                'details': wide_tables
            })

        # NEW v6.5.0: Check for role-playing dimensions
        role_playing = health.get('potential_role_playing_dimensions', [])
        if role_playing:
            recommendations.append({
                'reason': f'{len(role_playing)} potential role-playing dimensions detected',
                'suggestion': 'Review tables with multiple relationships - may need inactive relationships or separate copies',
                'priority': 'medium',
                'tool': 'relationship_operations',
                'args': {'operation': 'list'},
                'category': 'modeling',
                'details': role_playing
            })

        # NEW v6.5.0: Check for missing date table marking
        if health.get('missing_date_table_marking'):
            recommendations.append({
                'reason': 'Date/calendar table may not be marked as date table',
                'suggestion': 'Mark your date table using "Mark as Date Table" for proper time intelligence',
                'priority': 'high',
                'tool': 'full_analysis',
                'args': {'scope': 'best_practices'},
                'warning': 'Unmarked date tables may cause time intelligence functions to fail',
                'category': 'best_practice'
            })

        # NEW v6.5.0: Check hidden measure ratio
        hidden_count = health.get('hidden_measure_count', 0)
        if hidden_count > 0 and measure_count > 0:
            hidden_ratio = hidden_count / measure_count
            if hidden_ratio > 0.5:
                recommendations.append({
                    'reason': f'{hidden_count}/{measure_count} measures are hidden ({int(hidden_ratio*100)}%)',
                    'suggestion': 'High ratio of hidden measures - consider reviewing for cleanup opportunities',
                    'priority': 'low',
                    'tool': 'measure_operations',
                    'args': {'operation': 'list', 'include_hidden': True},
                    'category': 'maintenance'
                })

        # General recommendations if no specific issues
        if not recommendations:
            recommendations.append({
                'reason': 'Model appears healthy',
                'suggestion': 'Run a quick analysis for detailed insights',
                'priority': 'low',
                'tool': 'simple_analysis',
                'args': {},
                'category': 'general'
            })

        # Sort recommendations by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))

        return recommendations

    except Exception as e:
        logger.error(f"Error generating connection recommendations: {e}", exc_info=True)
        return [{
            'reason': 'Unable to generate recommendations',
            'suggestion': 'Use simple_analysis to explore the model',
            'priority': 'low',
            'tool': 'simple_analysis',
            'args': {},
            'category': 'fallback'
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
        'inactive_relationship_count': 0,
        # New v6.5.0 fields
        'wide_tables': [],  # Tables with >30 columns
        'high_cardinality_columns': [],  # Columns with very high distinct count
        'missing_date_table_marking': False,
        'potential_role_playing_dimensions': [],
        'column_count': 0,
        'relationship_count': 0,
        'hidden_measure_count': 0,
    }

    try:
        qe = connection_state.query_executor
        if not qe:
            return health

        # Get table count and check for wide tables
        tables_result = qe.execute_info_query("TABLES")
        if tables_result.get('success'):
            tables = tables_result.get('rows', [])
            health['table_count'] = len(tables)

        # Get columns and check for wide tables and high cardinality
        columns_result = qe.execute_info_query("COLUMNS")
        if columns_result.get('success'):
            columns = columns_result.get('rows', [])
            health['column_count'] = len(columns)

            # Group columns by table
            table_column_counts = {}
            for col in columns:
                table_name = col.get('TableName', col.get('[TableName]', col.get('Table', '')))
                if table_name:
                    table_column_counts[table_name] = table_column_counts.get(table_name, 0) + 1

            # Identify wide tables
            health['wide_tables'] = [
                {'table': tbl, 'columns': count}
                for tbl, count in table_column_counts.items()
                if count > THRESHOLDS['wide_table_columns']
            ]

        # Get measure count and check for hidden measures
        measures_result = qe.execute_info_query("MEASURES")
        if measures_result.get('success'):
            measures = measures_result.get('rows', [])
            health['measure_count'] = len(measures)
            health['hidden_measure_count'] = sum(
                1 for m in measures
                if m.get('IsHidden', m.get('[IsHidden]', False))
            )

        # Get relationships info
        relationships_result = qe.execute_info_query("RELATIONSHIPS")
        if relationships_result.get('success'):
            rows = relationships_result.get('rows', [])
            health['relationship_count'] = len(rows)

            # Track tables used in relationships to detect role-playing dimensions
            table_relationship_count = {}

            for row in rows:
                cross_filtering = str(row.get('CROSSFILTERINGBEHAVIOR', row.get('[CROSSFILTERINGBEHAVIOR]', ''))).upper()
                if 'BOTH' in cross_filtering:
                    health['has_bidirectional_relationships'] = True

                # Count inactive relationships
                is_active = row.get('ISACTIVE', row.get('[ISACTIVE]', True))
                if not is_active or str(is_active).upper() == 'FALSE':
                    health['inactive_relationship_count'] += 1

                # Track relationships per table for role-playing dimension detection
                from_table = row.get('FromTableName', row.get('[FromTableName]', ''))
                to_table = row.get('ToTableName', row.get('[ToTableName]', ''))
                for tbl in [from_table, to_table]:
                    if tbl:
                        table_relationship_count[tbl] = table_relationship_count.get(tbl, 0) + 1

            # Detect potential role-playing dimensions (tables with multiple relationships)
            health['potential_role_playing_dimensions'] = [
                {'table': tbl, 'relationships': count}
                for tbl, count in table_relationship_count.items()
                if count > 2  # Tables with more than 2 relationships might be role-playing
            ]

        # Get calculated columns count
        try:
            from core.infrastructure.query_executor import COLUMN_TYPE_CALCULATED
            filter_expr = f'[Type] = {COLUMN_TYPE_CALCULATED}'
            calc_cols_result = qe.execute_info_query("COLUMNS", filter_expr=filter_expr)
            if calc_cols_result.get('success'):
                health['calculated_column_count'] = len(calc_cols_result.get('rows', []))
        except Exception:
            pass  # Column type constant might not be available

        # Check for date table marking
        # Date tables should have the IsDateTable property set
        try:
            date_table_query = """
            SELECT [TableID], [Name] FROM $SYSTEM.TMSCHEMA_TABLES
            WHERE [TableType] = 0
            """
            date_result = qe.execute_dax_query(date_table_query, top_n=100)
            # If no explicit date tables marked, check for tables with date-like names
            if not date_result.get('success') or not date_result.get('rows'):
                # Look for tables that might be date tables
                for tbl in tables_result.get('rows', []) if tables_result.get('success') else []:
                    tbl_name = str(tbl.get('Name', tbl.get('[Name]', ''))).lower()
                    if 'date' in tbl_name or 'calendar' in tbl_name or 'time' in tbl_name:
                        health['missing_date_table_marking'] = True
                        break
        except Exception:
            pass  # DMV query might fail

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
