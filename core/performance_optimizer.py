"""
Performance Optimizer for PBIXRay MCP Server
Analyzes cardinality, encoding, and provides optimization recommendations
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Analyze model performance and provide optimization recommendations."""

    def __init__(self, query_executor):
        """Initialize with query executor."""
        self.executor = query_executor

    def analyze_relationship_cardinality(self) -> Dict[str, Any]:
        """Analyze actual vs configured relationship cardinality."""
        try:
            # Get all relationships
            rels_result = self.executor.execute_info_query("RELATIONSHIPS")
            if not rels_result.get('success'):
                return {'success': False, 'error': 'Failed to get relationships'}

            relationships = rels_result['rows']
            issues = []

            for rel in relationships:
                from_table = rel.get('FromTable')
                from_col = rel.get('FromColumn')
                to_table = rel.get('ToTable')
                to_col = rel.get('ToColumn')
                configured_card = rel.get('Cardinality', 'Unknown')

                # Query to check for duplicates in "one" side
                if 'One' in configured_card:
                    # Check to-side (should be unique)
                    check_query = f"""
                    EVALUATE
                    ROW(
                        "TotalRows", COUNTROWS('{to_table}'),
                        "UniqueValues", DISTINCTCOUNT('{to_table}'[{to_col}])
                    )
                    """

                    result = self.executor.validate_and_execute_dax(check_query)
                    if result.get('success') and result.get('rows'):
                        row = result['rows'][0]
                        total = row.get('TotalRows', 0)
                        unique = row.get('UniqueValues', 0)

                        if total != unique and total > 0:
                            duplicate_count = total - unique
                            issues.append({
                                'relationship': f"{from_table}[{from_col}] -> {to_table}[{to_col}]",
                                'configured_cardinality': configured_card,
                                'issue': 'Duplicate keys in one-side',
                                'details': f"{to_table}[{to_col}] has {duplicate_count} duplicate values",
                                'severity': 'high',
                                'recommendation': f"Remove duplicates from {to_table}[{to_col}] or change relationship to Many-to-Many",
                                'total_rows': total,
                                'unique_values': unique
                            })

            return {
                'success': True,
                'relationships_analyzed': len(relationships),
                'issues_found': len(issues),
                'issues': issues,
                'summary': {
                    'healthy_relationships': len(relationships) - len(issues),
                    'relationships_with_issues': len(issues)
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing cardinality: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_column_cardinality(self, table: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze column cardinality and provide recommendations.

        Args:
            table: Optional table name to limit analysis

        Returns:
            Cardinality analysis with recommendations
        """
        try:
            # Get columns
            cols_result = self.executor.execute_info_query("COLUMNS", table_name=table)

            if not cols_result.get('success'):
                return {'success': False, 'error': 'Failed to get columns'}

            columns = cols_result['rows']
            analysis = []

            # Analyze up to 20 columns to avoid long execution
            for col in columns[:20]:
                col_table = col.get('Table')
                col_name = col.get('Name')
                data_type = col.get('DataType', 'Unknown')

                # Skip hidden columns
                if col.get('IsHidden'):
                    continue

                # Query cardinality
                card_query = f"""
                EVALUATE
                ROW(
                    "RowCount", COUNTROWS('{col_table}'),
                    "DistinctCount", DISTINCTCOUNT('{col_table}'[{col_name}]),
                    "NullCount", COUNTBLANK('{col_table}'[{col_name}])
                )
                """

                result = self.executor.validate_and_execute_dax(card_query)
                if result.get('success') and result.get('rows'):
                    row = result['rows'][0]
                    row_count = row.get('RowCount', 0)
                    distinct_count = row.get('DistinctCount', 0)
                    null_count = row.get('NullCount', 0)

                    # Calculate metrics
                    cardinality_ratio = distinct_count / row_count if row_count > 0 else 0

                    # Determine cardinality level
                    if cardinality_ratio > 0.95:
                        cardinality_level = 'very_high'
                        recommendation = f"Very high cardinality ({distinct_count:,} unique values). Consider removing if not needed for analysis."
                        severity = 'high'
                    elif cardinality_ratio > 0.50:
                        cardinality_level = 'high'
                        recommendation = f"High cardinality ({distinct_count:,} unique values). May impact performance and memory."
                        severity = 'medium'
                    elif cardinality_ratio < 0.01 and row_count > 100:
                        cardinality_level = 'very_low'
                        recommendation = f"Very low cardinality ({distinct_count} unique values). Good for compression."
                        severity = 'low'
                    else:
                        cardinality_level = 'normal'
                        recommendation = "Cardinality is acceptable."
                        severity = 'low'

                    analysis.append({
                        'table': col_table,
                        'column': col_name,
                        'data_type': data_type,
                        'row_count': row_count,
                        'distinct_count': distinct_count,
                        'null_count': null_count,
                        'cardinality_ratio': round(cardinality_ratio, 4),
                        'cardinality_level': cardinality_level,
                        'severity': severity,
                        'recommendation': recommendation
                    })

            # Sort by severity
            analysis.sort(key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['severity'], 3))

            return {
                'success': True,
                'columns_analyzed': len(analysis),
                'analysis': analysis,
                'summary': {
                    'high_severity': len([a for a in analysis if a['severity'] == 'high']),
                    'medium_severity': len([a for a in analysis if a['severity'] == 'medium']),
                    'low_severity': len([a for a in analysis if a['severity'] == 'low'])
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing column cardinality: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_encoding_efficiency(self, table: str) -> Dict[str, Any]:
        """
        Analyze VertiPaq encoding efficiency for a table.

        Args:
            table: Table name to analyze

        Returns:
            Encoding analysis with recommendations
        """
        try:
            # Query VertiPaq storage info
            query = f"""
            EVALUATE
            FILTER(
                INFO.STORAGETABLECOLUMNS(),
                [TABLE_ID] = "{table}"
            )
            """

            result = self.executor.validate_and_execute_dax(query)
            if not result.get('success'):
                return {'success': False, 'error': 'Failed to query VertiPaq stats'}

            rows = result.get('rows', [])
            if not rows:
                return {
                    'success': False,
                    'error': f"No VertiPaq data found for table '{table}'"
                }

            analysis = []
            total_size = 0
            total_cardinality = 0

            for row in rows:
                column = row.get('COLUMN_ID', 'Unknown')
                data_size = row.get('DICTIONARY_SIZE', 0) or 0
                cardinality = row.get('DICTIONARY_COUNT', 0) or 0

                total_size += data_size
                total_cardinality += cardinality

                # Estimate encoding efficiency
                if cardinality > 0:
                    avg_bytes_per_value = data_size / cardinality
                else:
                    avg_bytes_per_value = 0

                # Recommendations based on size and cardinality
                if data_size > 10_000_000:  # > 10MB
                    severity = 'high'
                    recommendation = f"Large dictionary size ({data_size/1_000_000:.1f}MB). Consider reducing cardinality or removing if not needed."
                elif cardinality > 1_000_000:
                    severity = 'medium'
                    recommendation = f"High cardinality ({cardinality:,} values). May benefit from binning or aggregation."
                else:
                    severity = 'low'
                    recommendation = "Encoding efficiency is acceptable."

                analysis.append({
                    'column': column,
                    'dictionary_size_bytes': data_size,
                    'dictionary_size_mb': round(data_size / 1_000_000, 2),
                    'cardinality': cardinality,
                    'avg_bytes_per_value': round(avg_bytes_per_value, 2),
                    'severity': severity,
                    'recommendation': recommendation
                })

            # Sort by size
            analysis.sort(key=lambda x: x['dictionary_size_bytes'], reverse=True)

            return {
                'success': True,
                'table': table,
                'columns_analyzed': len(analysis),
                'total_size_mb': round(total_size / 1_000_000, 2),
                'total_cardinality': total_cardinality,
                'analysis': analysis[:20],  # Top 20 columns
                'summary': {
                    'largest_column': analysis[0]['column'] if analysis else None,
                    'largest_column_size_mb': analysis[0]['dictionary_size_mb'] if analysis else 0
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing encoding: {e}")
            return {'success': False, 'error': str(e)}
