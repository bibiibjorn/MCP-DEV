"""
Dependency and usage analyzer for Power BI models.
Tracks dependencies and usage patterns across measures, columns, and relationships.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional

# Import from dedicated parser module (breaks circular dependency)
from core.dax.dax_reference_parser import DaxReferenceIndex, parse_dax_references

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes usage patterns and dependencies in Power BI models."""
    
    def __init__(self, query_executor):
        self.query_executor = query_executor
        self._ref_index = None
    
    def _ensure_reference_index(self):
        """Lazily build the reference index"""
        if self._ref_index is not None:
            return self._ref_index
        
        measures_result = self.query_executor.execute_info_query("MEASURES")
        columns_result = self.query_executor.execute_info_query("COLUMNS")
        
        measure_rows = measures_result.get('rows', []) if measures_result.get('success') else []
        column_rows = columns_result.get('rows', []) if columns_result.get('success') else []
        
        self._ref_index = DaxReferenceIndex(measure_rows, column_rows)
        return self._ref_index
    
    def analyze_measure_dependencies(self, table: str, measure: str) -> Dict:
        """Analyze dependencies for a specific measure"""
        # Use get_measure_details_with_fallback for proper table+measure filtering
        result = self.query_executor.get_measure_details_with_fallback(table, measure)
        if not result.get('success'):
            return {'success': False, 'error': result.get('error')}

        rows = result.get('rows', [])
        if not rows:
            return {'success': False, 'error': f"Measure {table}[{measure}] not found"}
        
        measure_row = rows[0]
        expression = measure_row.get('Expression', '')
        
        ref_index = self._ensure_reference_index()
        refs = parse_dax_references(expression, ref_index)
        
        return {
            'success': True,
            'measure': {'table': table, 'name': measure},
            'expression': expression,
            'dependencies': refs,
            'referenced_measures': refs.get('measures', []),
            'referenced_columns': refs.get('columns', []),
            'referenced_tables': refs.get('tables', [])
        }
    
    def find_measure_usage(self, table: str, measure: str) -> Dict:
        """Find where a measure is used by other measures"""
        ref_index = self._ensure_reference_index()
        
        measures_result = self.query_executor.execute_info_query("MEASURES")
        if not measures_result.get('success'):
            return {'success': False, 'error': measures_result.get('error')}
        
        all_measures = measures_result.get('rows', [])
        usage_list = []
        
        for m in all_measures:
            m_table = m.get('Table', '')
            m_name = m.get('Name', '')
            if m_table == table and m_name == measure:
                continue
            
            expression = m.get('Expression', '')
            refs = parse_dax_references(expression, ref_index)
            
            for ref_table, ref_name in refs.get('measures', []):
                if (ref_table == table or ref_table == '') and ref_name == measure:
                    usage_list.append({
                        'table': m_table,
                        'measure': m_name
                    })
                    break
        
        return {
            'success': True,
            'measure': {'table': table, 'name': measure},
            'used_by': usage_list,
            'usage_count': len(usage_list)
        }
    
    def build_dependency_tree(self, table: str, measure: str, max_depth: int = 5) -> Dict:
        """Build a full dependency tree for a measure"""
        def recurse(tbl, msr, depth, visited):
            if depth > max_depth:
                return {'table': tbl, 'measure': msr, 'max_depth_reached': True}

            key = f"{tbl}|{msr}"
            if key in visited:
                return {'table': tbl, 'measure': msr, 'circular': True}

            visited.add(key)
            deps_result = self.analyze_measure_dependencies(tbl, msr)

            if not deps_result.get('success'):
                return {'table': tbl, 'measure': msr, 'error': deps_result.get('error')}

            children = []
            for dep_table, dep_name in deps_result.get('referenced_measures', []):
                if dep_table:
                    child = recurse(dep_table, dep_name, depth + 1, visited.copy())
                    children.append(child)

            return {
                'table': tbl,
                'measure': msr,
                'expression': deps_result.get('expression', ''),
                'dependencies': children,
                'depth': depth
            }

        tree = recurse(table, measure, 0, set())
        return {'success': True, 'tree': tree}

    def analyze_dependencies(self, table: str, measure: str, depth: int = 3) -> Dict:
        """
        Alias for analyze_measure_dependencies with optional depth parameter.
        Used by tool handlers for backward compatibility.
        """
        result = self.analyze_measure_dependencies(table, measure)
        if not result.get('success'):
            return result

        # If depth > 1, build full dependency tree
        if depth > 1:
            tree_result = self.build_dependency_tree(table, measure, depth)
            if tree_result.get('success'):
                result['dependency_tree'] = tree_result.get('tree')

        return result

    def get_measure_impact(self, table: str, measure: str, depth: int = 3) -> Dict:
        """
        Alias that combines find_measure_usage with dependency analysis.
        Returns both upstream dependencies and downstream usage.
        """
        # Get downstream usage (what uses this measure)
        usage_result = self.find_measure_usage(table, measure)

        # Get upstream dependencies (what this measure uses)
        deps_result = self.analyze_measure_dependencies(table, measure)

        # Combine results
        result = {
            'success': True,
            'measure': {'table': table, 'name': measure},
            'downstream_usage': usage_result.get('used_by', []) if usage_result.get('success') else [],
            'downstream_count': usage_result.get('usage_count', 0) if usage_result.get('success') else 0,
            'upstream_dependencies': {
                'measures': deps_result.get('referenced_measures', []) if deps_result.get('success') else [],
                'columns': deps_result.get('referenced_columns', []) if deps_result.get('success') else [],
                'tables': deps_result.get('referenced_tables', []) if deps_result.get('success') else []
            }
        }

        return result
