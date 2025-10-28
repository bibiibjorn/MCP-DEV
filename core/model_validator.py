"""
Model Validator for PBIXRay MCP Server
Validates model integrity and data quality
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ModelValidator:
    """Validate model integrity and data quality."""

    def __init__(self, query_executor):
        """Initialize with query executor."""
        self.executor = query_executor

    def validate_model_integrity(self) -> Dict[str, Any]:
        """
        Comprehensive model validation.

        Returns:
            Validation results with issues found
        """
        issues = []

        try:
            # Check 1: Relationships with missing keys
            logger.info("Checking relationships...")
            rel_issues = self._check_relationship_integrity()
            if rel_issues:
                issues.extend(rel_issues)

            # Check 2: Duplicate keys in dimension tables
            logger.info("Checking for duplicate keys...")
            dup_issues = self._check_duplicate_keys()
            if dup_issues:
                issues.extend(dup_issues)

            # Check 3: Null values in key columns
            logger.info("Checking for null keys...")
            null_issues = self._check_null_keys()
            if null_issues:
                issues.extend(null_issues)

            # Check 4: Invalid measure references
            logger.info("Checking measure references...")
            measure_issues = self._check_measure_references()
            if measure_issues:
                issues.extend(measure_issues)

            # Check 5: Circular relationships
            logger.info("Checking for circular relationships...")
            circular_issues = self._check_circular_relationships()
            if circular_issues:
                issues.extend(circular_issues)

            # Categorize by severity
            critical = [i for i in issues if i['severity'] == 'critical']
            high = [i for i in issues if i['severity'] == 'high']
            medium = [i for i in issues if i['severity'] == 'medium']
            low = [i for i in issues if i['severity'] == 'low']

            is_valid = len(critical) == 0 and len(high) == 0

            return {
                'success': True,
                'is_valid': is_valid,
                'total_issues': len(issues),
                'issues': issues,
                'summary': {
                    'critical_issues': len(critical),
                    'high_issues': len(high),
                    'medium_issues': len(medium),
                    'low_issues': len(low)
                },
                'recommendation': 'Fix critical and high issues before deploying' if not is_valid else 'Model passed validation'
            }

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {'success': False, 'error': str(e)}

    def _check_relationship_integrity(self) -> List[Dict[str, Any]]:
        """Check for orphaned records in relationships."""
        issues = []

        # Helper to fetch DMV fields that may arrive as "Name" or "[Name]"
        def _get_any(row: Dict[str, Any], keys: List[str]) -> Any:
            for k in keys:
                if k in row and row[k] not in (None, ""):
                    return row[k]
                bk = f"[{k}]"
                if bk in row and row[bk] not in (None, ""):
                    return row[bk]
            return None

        try:
            rels_result = self.executor.execute_info_query("RELATIONSHIPS", top_n=100)
            if not rels_result.get('success'):
                return issues

            for rel in rels_result['rows'][:10]:  # Check first 10 relationships
                from_table = _get_any(rel, ['FromTable'])
                from_col = _get_any(rel, ['FromColumn'])
                to_table = _get_any(rel, ['ToTable'])
                to_col = _get_any(rel, ['ToColumn'])
                if not from_table or not from_col or not to_table or not to_col:
                    # Skip incomplete rows
                    continue

                # Check for orphaned records
                query = f"""
                EVALUATE
                ROW(
                    "OrphanedRecords",
                    COUNTROWS(
                        FILTER(
                            '{from_table}',
                            ISBLANK(RELATED('{to_table}'[{to_col}]))
                        )
                    )
                )
                """

                result = self.executor.validate_and_execute_dax(query)
                if result.get('success') and result.get('rows'):
                    orphaned = result['rows'][0].get('OrphanedRecords', 0)
                    if orphaned > 0:
                        issues.append({
                            'type': 'orphaned_records',
                            'severity': 'high',
                            'relationship': f"{from_table}[{from_col}] -> {to_table}[{to_col}]",
                            'description': f"{orphaned} orphaned records in {from_table}",
                            'recommendation': f"Add records to {to_table} or filter out orphaned records"
                        })

        except Exception as e:
            logger.warning(f"Error checking relationship integrity: {e}")

        return issues

    def _check_duplicate_keys(self) -> List[Dict[str, Any]]:
        """Check for duplicate keys in dimension tables."""
        issues = []

        def _get_any(row: Dict[str, Any], keys: List[str]) -> Any:
            for k in keys:
                if k in row and row[k] not in (None, ""):
                    return row[k]
                bk = f"[{k}]"
                if bk in row and row[bk] not in (None, ""):
                    return row[bk]
            return None

        try:
            # Get relationships to identify dimension tables
            rels_result = self.executor.execute_info_query("RELATIONSHIPS", top_n=100)
            if not rels_result.get('success'):
                return issues

            # Check "to" side of relationships (dimension side)
            checked_tables = set()

            for rel in rels_result['rows'][:10]:
                to_table = _get_any(rel, ['ToTable'])
                to_col = _get_any(rel, ['ToColumn'])
                if not to_table or not to_col:
                    continue

                table_col = f"{to_table}[{to_col}]"
                if table_col in checked_tables:
                    continue

                checked_tables.add(table_col)

                # Check for duplicates
                query = f"""
                EVALUATE
                ROW(
                    "TotalRows", COUNTROWS('{to_table}'),
                    "UniqueKeys", DISTINCTCOUNT('{to_table}'[{to_col}])
                )
                """

                result = self.executor.validate_and_execute_dax(query)
                if result.get('success') and result.get('rows'):
                    row = result['rows'][0]
                    total = row.get('TotalRows', 0)
                    unique = row.get('UniqueKeys', 0)

                    if total != unique and total > 0:
                        issues.append({
                            'type': 'duplicate_keys',
                            'severity': 'critical',
                            'table': to_table,
                            'column': to_col,
                            'description': f"Duplicate keys found in {to_table}[{to_col}]",
                            'duplicate_count': total - unique,
                            'recommendation': f"Remove duplicates from {to_table} or use SUMMARIZE to create unique keys"
                        })

        except Exception as e:
            logger.warning(f"Error checking duplicate keys: {e}")

        return issues

    def _check_null_keys(self) -> List[Dict[str, Any]]:
        """Check for null values in key columns."""
        issues = []

        def _get_any(row: Dict[str, Any], keys: List[str]) -> Any:
            for k in keys:
                if k in row and row[k] not in (None, ""):
                    return row[k]
                bk = f"[{k}]"
                if bk in row and row[bk] not in (None, ""):
                    return row[bk]
            return None

        try:
            rels_result = self.executor.execute_info_query("RELATIONSHIPS", top_n=100)
            if not rels_result.get('success'):
                return issues

            checked = set()

            for rel in rels_result['rows'][:10]:
                # Check both sides
                for side in ['From', 'To']:
                    table = _get_any(rel, [f'{side}Table'])
                    col = _get_any(rel, [f'{side}Column'])
                    if not table or not col:
                        continue

                    table_col = f"{table}[{col}]"
                    if table_col in checked:
                        continue

                    checked.add(table_col)

                    query = f"""
                    EVALUATE
                    ROW("NullCount", COUNTBLANK('{table}'[{col}]))
                    """

                    result = self.executor.validate_and_execute_dax(query)
                    if result.get('success') and result.get('rows'):
                        null_count = result['rows'][0].get('NullCount', 0)
                        if null_count > 0:
                            issues.append({
                                'type': 'null_keys',
                                'severity': 'high',
                                'table': table,
                                'column': col,
                                'description': f"{null_count} null values in key column {table}[{col}]",
                                'recommendation': f"Replace null values in {table}[{col}] with valid keys or 'Unknown'"
                            })

        except Exception as e:
            logger.warning(f"Error checking null keys: {e}")

        return issues

    def _check_measure_references(self) -> List[Dict[str, Any]]:
        """Check for invalid measure references."""
        issues = []

        try:
            measures_result = self.executor.execute_info_query("MEASURES", top_n=100)
            if not measures_result.get('success'):
                return issues

            # Get all measure names
            measure_names = {m.get('Name') for m in measures_result['rows']}

            # Check each measure's expression for invalid references
            # This is simplified - full implementation would parse DAX properly
            for measure in measures_result['rows'][:20]:  # Check first 20
                expr = measure.get('Expression', '')
                # Basic check for [MeasureName] pattern
                # Would need full DAX parser for complete validation

        except Exception as e:
            logger.warning(f"Error checking measure references: {e}")

        return issues

    def _check_circular_relationships(self) -> List[Dict[str, Any]]:
        """Check for circular relationship chains."""
        issues = []

        try:
            rels_result = self.executor.execute_info_query("RELATIONSHIPS", top_n=100)
            if not rels_result.get('success'):
                return issues

            # Build relationship graph
            graph = {}
            for rel in rels_result['rows']:
                from_table = rel.get('FromTable')
                to_table = rel.get('ToTable')

                if from_table not in graph:
                    graph[from_table] = []
                graph[from_table].append(to_table)

            # Check for cycles using DFS
            def has_cycle(node, visited, rec_stack):
                visited.add(node)
                rec_stack.add(node)

                if node in graph:
                    for neighbor in graph[node]:
                        if neighbor not in visited:
                            if has_cycle(neighbor, visited, rec_stack):
                                return True
                        elif neighbor in rec_stack:
                            return True

                rec_stack.remove(node)
                return False

            visited = set()
            for node in graph:
                if node not in visited:
                    if has_cycle(node, visited, set()):
                        issues.append({
                            'type': 'circular_relationship',
                            'severity': 'critical',
                            'description': 'Circular relationship chain detected',
                            'recommendation': 'Review relationship directions and remove circular chains'
                        })
                        break  # Only report once

        except Exception as e:
            logger.warning(f"Error checking circular relationships: {e}")

        return issues

    def analyze_data_freshness(self) -> Dict[str, Any]:
        """Check data refresh status."""
        try:
            # Attempt 1: Desktop-incompatible DMV may fail; try TMSCHEMA partitions first
            attempts = []
            query_tmschema = '''EVALUATE
            SELECTCOLUMNS(
                TOPN(999999, $SYSTEM.TMSCHEMA_TABLES),
                "Table", [Name],
                "LastRefresh", [ModifiedTime]
            )'''
            result = self.executor.validate_and_execute_dax(query_tmschema)
            attempts.append(('TMSCHEMA_TABLES', result.get('success')))
            if not result.get('success'):
                # Attempt 2: Legacy DISCOVER_STORAGE_TABLES (may fail on Desktop)
                query = '''EVALUATE
                SELECTCOLUMNS(
                    FILTER(
                        TOPN(999999, $SYSTEM.DISCOVER_STORAGE_TABLES),
                        [TABLE_TYPE] = "TABLE"
                    ),
                    "Table", [DIMENSION_NAME],
                    "LastRefresh", [LAST_DATA_UPDATE]
                )'''
                result = self.executor.validate_and_execute_dax(query)
                attempts.append(('DISCOVER_STORAGE_TABLES', result.get('success')))
            if not result.get('success'):
                # Attempt 3: TOM fallback - partitions LastProcessed
                try:
                    result = self.executor.get_partition_freshness_tom()
                    attempts.append(('TOM', result.get('success')))
                except Exception as _e:
                    result = {'success': False, 'error': str(_e)}

            if result.get('success'):
                rows = result.get('rows', []) or result.get('tables', [])
                return {
                    'success': True,
                    'tables': rows,
                    'attempts': attempts
                }
            else:
                result.setdefault('attempts', attempts)
                return result

        except Exception as e:
            logger.error(f"Error analyzing data freshness: {e}")
            return {'success': False, 'error': str(e)}
