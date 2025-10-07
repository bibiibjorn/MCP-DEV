"""
Dependency Analyzer for PBIXRay MCP Server
Analyzes measure and column dependencies across the model
"""

import re
import logging
from typing import Dict, Any, List, Set, Optional

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes dependencies between measures, columns, and tables."""

    def __init__(self, query_executor):
        """Initialize with query executor."""
        self.executor = query_executor
        self._dependency_cache = {}

    def _extract_dax_references(self, expression: str) -> Dict[str, List[str]]:
        """Extract table, column, and measure references from DAX expression."""
        if not expression:
            return {"tables": [], "columns": [], "measures": []}

        # Remove comments and strings to avoid false positives
        clean_expr = re.sub(r'--[^\n]*', '', expression)
        clean_expr = re.sub(r'"[^"]*"', '', clean_expr)

        tables = set()
        columns = set()
        measures = set()

        # Pattern: 'TableName'[ColumnName] or TableName[ColumnName]
        column_refs = re.findall(r"(?:'([^']+)'|\b(\w+))\[([^\]]+)\]", clean_expr)
        for match in column_refs:
            table = match[0] or match[1]
            column = match[2]
            tables.add(table)
            columns.add(f"{table}[{column}]")

        # Pattern: [MeasureName] (not preceded by table reference)
        measure_refs = re.findall(r"(?<!['\w])\[([^\]]+)\]", clean_expr)
        for measure in measure_refs:
            # Exclude if it's part of a table reference
            if not any(f"[{measure}]" in col for col in columns):
                measures.add(measure)

        # RELATED, RELATEDTABLE functions
        related_refs = re.findall(r"RELATED(?:TABLE)?\s*\(\s*(?:'([^']+)'|(\w+))\[([^\]]+)\]", clean_expr)
        for match in related_refs:
            table = match[0] or match[1]
            column = match[2]
            tables.add(table)
            columns.add(f"{table}[{column}]")

        return {
            "tables": sorted(list(tables)),
            "columns": sorted(list(columns)),
            "measures": sorted(list(measures))
        }

    def analyze_measure_dependencies(
        self,
        table: str,
        measure: str,
        depth: int = 3,
        include_upstream: bool = True,
        include_downstream: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze dependencies for a measure.

        Args:
            table: Table containing the measure
            measure: Measure name
            depth: Maximum depth to traverse
            include_upstream: Include what this measure depends on
            include_downstream: Include what depends on this measure

        Returns:
            Dependency analysis results
        """
        try:
            # Get measure details
            measure_result = self.executor.execute_info_query(
                "MEASURES",
                f'[Table] = "{table}" && [Name] = "{measure}"'
            )

            if not measure_result.get('success') or not measure_result.get('rows'):
                return {
                    'success': False,
                    'error': f"Measure '{measure}' not found in table '{table}'"
                }

            measure_data = measure_result['rows'][0]
            expression = measure_data.get('Expression', '')

            # Extract direct dependencies
            direct_deps = self._extract_dax_references(expression)

            result = {
                'success': True,
                'measure': measure,
                'table': table,
                'expression': expression,
                'direct_dependencies': direct_deps
            }

            # Get all measures for downstream analysis
            if include_downstream:
                all_measures_result = self.executor.execute_info_query("MEASURES")
                if all_measures_result.get('success'):
                    downstream = self._find_downstream_dependencies(
                        measure,
                        all_measures_result['rows'],
                        depth
                    )
                    result['downstream_dependencies'] = downstream

            # Get upstream chain
            if include_upstream:
                upstream = self._build_upstream_chain(direct_deps, depth)
                result['upstream_dependencies'] = upstream

            return result

        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return {'success': False, 'error': str(e)}

    def _find_downstream_dependencies(
        self,
        measure_name: str,
        all_measures: List[Dict],
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """Find measures that depend on the given measure."""
        downstream = []

        for m in all_measures:
            expr = m.get('Expression', '')
            if not expr:
                continue

            # Check if this measure references the target measure
            refs = self._extract_dax_references(expr)
            if measure_name in refs['measures']:
                downstream.append({
                    'measure': m.get('Name'),
                    'table': m.get('Table'),
                    'expression': expr[:200]  # Truncate for readability
                })

        return downstream

    def _build_upstream_chain(
        self,
        dependencies: Dict[str, List[str]],
        max_depth: int,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """Build upstream dependency chain."""
        if current_depth >= max_depth:
            return dependencies

        # For now, return direct dependencies
        # Full recursive chain would require querying each dependent measure
        return dependencies

    def find_unused_objects(self) -> Dict[str, Any]:
        """Find unused tables, columns, and measures."""
        try:
            # Get all measures
            measures_result = self.executor.execute_info_query("MEASURES")
            if not measures_result.get('success'):
                return {'success': False, 'error': 'Failed to get measures'}

            measures = measures_result['rows']

            # Get all columns
            columns_result = self.executor.execute_info_query("COLUMNS")
            if not columns_result.get('success'):
                return {'success': False, 'error': 'Failed to get columns'}

            columns = columns_result['rows']

            # Get all tables
            tables_result = self.executor.execute_info_query("TABLES")
            if not tables_result.get('success'):
                return {'success': False, 'error': 'Failed to get tables'}

            tables = tables_result['rows']

            # Build reference sets
            referenced_measures = set()
            referenced_columns = set()
            referenced_tables = set()

            # Analyze all measure expressions
            for m in measures:
                expr = m.get('Expression', '')
                refs = self._extract_dax_references(expr)

                referenced_measures.update(refs['measures'])
                referenced_columns.update(refs['columns'])
                referenced_tables.update(refs['tables'])

            # Check relationships for table/column usage
            rels_result = self.executor.execute_info_query("RELATIONSHIPS")
            if rels_result.get('success'):
                for rel in rels_result['rows']:
                    from_table = rel.get('FromTable', '')
                    to_table = rel.get('ToTable', '')
                    from_col = rel.get('FromColumn', '')
                    to_col = rel.get('ToColumn', '')

                    referenced_tables.add(from_table)
                    referenced_tables.add(to_table)
                    referenced_columns.add(f"{from_table}[{from_col}]")
                    referenced_columns.add(f"{to_table}[{to_col}]")

            # Find unused objects
            unused_measures = []
            for m in measures:
                if m.get('Name') not in referenced_measures:
                    # Skip if it's hidden (likely internal)
                    if not m.get('IsHidden'):
                        unused_measures.append({
                            'name': m.get('Name'),
                            'table': m.get('Table')
                        })

            unused_columns = []
            for c in columns:
                col_ref = f"{c.get('Table')}[{c.get('Name')}]"
                if col_ref not in referenced_columns:
                    # Skip hidden and key columns
                    if not c.get('IsHidden') and not c.get('IsKey'):
                        unused_columns.append({
                            'name': c.get('Name'),
                            'table': c.get('Table'),
                            'type': c.get('Type')
                        })

            unused_tables = []
            for t in tables:
                if t.get('Name') not in referenced_tables:
                    # Check if table has any non-calculated columns (data table)
                    table_cols = [col for col in columns if col.get('Table') == t.get('Name')]
                    if table_cols and not t.get('IsHidden'):
                        unused_tables.append({
                            'name': t.get('Name')
                        })

            return {
                'success': True,
                'unused_measures': unused_measures,
                'unused_columns': unused_columns[:50],  # Limit for readability
                'unused_tables': unused_tables,
                'summary': {
                    'total_unused_measures': len(unused_measures),
                    'total_unused_columns': len(unused_columns),
                    'total_unused_tables': len(unused_tables)
                }
            }

        except Exception as e:
            logger.error(f"Error finding unused objects: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_column_usage(self, table: str, column: str) -> Dict[str, Any]:
        """Analyze where a column is used in the model."""
        try:
            col_ref = f"{table}[{column}]"

            usage = {
                'success': True,
                'column': column,
                'table': table,
                'used_in_measures': [],
                'used_in_calculated_columns': [],
                'used_in_relationships': []
            }

            # Check measures
            measures_result = self.executor.execute_info_query("MEASURES")
            if measures_result.get('success'):
                for m in measures_result['rows']:
                    expr = m.get('Expression', '')
                    refs = self._extract_dax_references(expr)

                    if col_ref in refs['columns'] or table in refs['tables']:
                        usage['used_in_measures'].append({
                            'measure': m.get('Name'),
                            'table': m.get('Table')
                        })

            # Check calculated columns
            calc_cols_query = 'EVALUATE FILTER(INFO.COLUMNS(), [Type] = "Calculated")'
            calc_result = self.executor.validate_and_execute_dax(calc_cols_query)
            if calc_result.get('success'):
                for row in calc_result.get('rows', []):
                    # Would need expression to check, skip for now
                    pass

            # Check relationships
            rels_result = self.executor.execute_info_query("RELATIONSHIPS")
            if rels_result.get('success'):
                for rel in rels_result['rows']:
                    if ((rel.get('FromTable') == table and rel.get('FromColumn') == column) or
                        (rel.get('ToTable') == table and rel.get('ToColumn') == column)):
                        usage['used_in_relationships'].append({
                            'from': f"{rel.get('FromTable')}[{rel.get('FromColumn')}]",
                            'to': f"{rel.get('ToTable')}[{rel.get('ToColumn')}]",
                            'active': rel.get('IsActive')
                        })

            usage['summary'] = {
                'used_in_measures_count': len(usage['used_in_measures']),
                'used_in_relationships_count': len(usage['used_in_relationships']),
                'is_used': (len(usage['used_in_measures']) +
                           len(usage['used_in_relationships'])) > 0
            }

            return usage

        except Exception as e:
            logger.error(f"Error analyzing column usage: {e}")
            return {'success': False, 'error': str(e)}
