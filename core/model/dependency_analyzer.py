"""
Dependency and usage analyzer for Power BI models.
Tracks dependencies and usage patterns across measures, columns, and relationships.
"""

import logging
import time
from typing import Dict, List, Set, Tuple, Optional, Any
from core.config.config_manager import config

# Import from dedicated parser module (breaks circular dependency)
from core.dax.dax_reference_parser import DaxReferenceIndex, parse_dax_references

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes usage patterns and dependencies in Power BI models."""

    def __init__(self, query_executor):
        self.query_executor = query_executor
        self._ref_index = None

        # DAX Parse Cache: (measure_name, expression_hash) -> parsed_references
        # This cache avoids re-parsing the same DAX expressions repeatedly
        self._parse_cache: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self._parse_cache_timestamps: Dict[Tuple[str, int], float] = {}
        self._cache_ttl = config.get('performance.dependency_cache_ttl', 600)  # 10 minutes default

        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
    
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

    def _parse_dax_cached(self, measure_name: str, expression: str) -> Dict[str, Any]:
        """
        Parse DAX expression with caching to avoid re-parsing the same expressions.

        Args:
            measure_name: Name of the measure (for cache key)
            expression: DAX expression to parse

        Returns:
            Parsed references dictionary
        """
        # Create cache key from measure name and expression hash
        cache_key = (measure_name, hash(expression))

        # Check if cache is valid
        if cache_key in self._parse_cache:
            # Check TTL
            timestamp = self._parse_cache_timestamps.get(cache_key, 0)
            age = time.time() - timestamp

            if age <= self._cache_ttl:
                self._cache_hits += 1
                logger.debug(f"DAX parse cache hit for {measure_name} (age: {age:.1f}s)")
                return self._parse_cache[cache_key]
            else:
                # Expired, remove from cache
                del self._parse_cache[cache_key]
                del self._parse_cache_timestamps[cache_key]

        # Cache miss - parse the DAX
        self._cache_misses += 1
        ref_index = self._ensure_reference_index()
        refs = parse_dax_references(expression, ref_index)

        # Store in cache with timestamp
        self._parse_cache[cache_key] = refs
        self._parse_cache_timestamps[cache_key] = time.time()

        logger.debug(f"DAX parse cache miss for {measure_name} (cache size: {len(self._parse_cache)})")
        return refs

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring performance."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'success': True,
            'cache_size': len(self._parse_cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 1),
            'ttl_seconds': self._cache_ttl
        }

    def clear_cache(self) -> Dict[str, Any]:
        """Clear the DAX parse cache."""
        cache_size = len(self._parse_cache)
        self._parse_cache.clear()
        self._parse_cache_timestamps.clear()
        logger.info(f"Cleared DAX parse cache ({cache_size} entries)")

        return {
            'success': True,
            'cleared_entries': cache_size,
            'message': f'Cleared {cache_size} cached parse results'
        }
    
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

        # Use cached parsing (PERFORMANCE IMPROVEMENT)
        measure_key = f"{table}[{measure}]"
        refs = self._parse_dax_cached(measure_key, expression)

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

            # Use cached parsing (PERFORMANCE IMPROVEMENT)
            measure_key = f"{m_table}[{m_name}]"
            refs = self._parse_dax_cached(measure_key, expression)

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

    def get_measure_impact_score(self, table: str, measure: str, depth: int = 10) -> Dict[str, Any]:
        """
        Calculate comprehensive impact score for a measure to prioritize refactoring.

        Impact Score is calculated based on:
        - Number of direct dependent measures
        - Number of total (transitive) dependent measures
        - Presence in calculation groups
        - Usage in RLS rules (future enhancement)

        Args:
            table: Table name containing the measure
            measure: Measure name
            depth: Maximum depth for transitive dependency analysis (default: 10)

        Returns:
            Dictionary with impact score and breakdown
        """
        try:
            # Get direct downstream usage
            usage_result = self.find_measure_usage(table, measure)
            if not usage_result.get('success'):
                return {'success': False, 'error': usage_result.get('error')}

            direct_dependents = usage_result.get('used_by', [])
            direct_count = len(direct_dependents)

            # Calculate transitive dependents (recursive depth search)
            all_dependents = set()
            visited = set()

            def find_transitive_dependents(t, m, current_depth):
                if current_depth > depth:
                    return
                key = f"{t}[{m}]"
                if key in visited:
                    return
                visited.add(key)

                usage = self.find_measure_usage(t, m)
                if usage.get('success'):
                    for dep in usage.get('used_by', []):
                        dep_key = f"{dep['table']}[{dep['measure']}]"
                        all_dependents.add(dep_key)
                        find_transitive_dependents(dep['table'], dep['measure'], current_depth + 1)

            # Start recursive search
            find_transitive_dependents(table, measure, 0)
            total_dependents = len(all_dependents)

            # Check calculation group usage (placeholder - requires TOM access)
            in_calc_groups = self._check_calc_group_usage(table, measure)

            # Check RLS usage (placeholder - requires TOM access)
            in_rls = self._check_rls_usage(table, measure)

            # Calculate impact level
            if total_dependents > 10 or in_calc_groups:
                impact_level = 'HIGH'
            elif total_dependents > 3:
                impact_level = 'MEDIUM'
            else:
                impact_level = 'LOW'

            return {
                'success': True,
                'measure': {'table': table, 'name': measure},
                'impact_score': {
                    'direct_dependents': direct_count,
                    'total_dependents': total_dependents,
                    'transitive_dependents': total_dependents - direct_count,
                    'in_calculation_groups': in_calc_groups,
                    'in_rls_rules': in_rls,
                    'impact_level': impact_level
                },
                'direct_dependent_list': direct_dependents[:10],  # Limit to first 10 for readability
                'recommendation': self._get_impact_recommendation(impact_level, total_dependents)
            }

        except Exception as e:
            logger.error(f"Error calculating impact score for {table}[{measure}]: {e}")
            return {'success': False, 'error': str(e)}

    def _check_calc_group_usage(self, table: str, measure: str) -> bool:
        """
        Check if measure is referenced in calculation groups.
        Currently a placeholder - requires TOM access for implementation.
        """
        # TODO: Implement calculation group check using TOM
        # For now, return False as a safe default
        return False

    def _check_rls_usage(self, table: str, measure: str) -> bool:
        """
        Check if measure is used in RLS rules.
        Currently a placeholder - requires TOM access for implementation.
        """
        # TODO: Implement RLS check using TOM
        # For now, return False as a safe default
        return False

    def _get_impact_recommendation(self, impact_level: str, dependent_count: int) -> str:
        """Generate recommendation based on impact level."""
        if impact_level == 'HIGH':
            return f"High-impact measure ({dependent_count} dependents). Changes will affect many calculations. Test thoroughly."
        elif impact_level == 'MEDIUM':
            return f"Medium-impact measure ({dependent_count} dependents). Review downstream measures before modifying."
        else:
            return "Low-impact measure. Safe to modify or delete with minimal risk."

    def find_unused_measures(self, include_hidden: bool = False) -> Dict[str, Any]:
        """
        Identify measures with zero dependents and not used in calculation groups or RLS.
        These measures are safe to delete.

        Args:
            include_hidden: Include hidden measures in results (default: False)

        Returns:
            Dictionary with list of unused measures
        """
        try:
            # Get all measures
            measures_result = self.query_executor.execute_info_query("MEASURES")
            if not measures_result.get('success'):
                return {'success': False, 'error': measures_result.get('error')}

            all_measures = measures_result.get('rows', [])
            unused_measures = []

            logger.info(f"Analyzing {len(all_measures)} measures for usage...")

            for m in all_measures:
                m_table = m.get('Table', '') or m.get('[Table]', '')
                m_name = m.get('Name', '') or m.get('[Name]', '')
                is_hidden = m.get('IsHidden', False) or m.get('[IsHidden]', False)

                if not m_table or not m_name:
                    continue

                # Skip hidden measures unless explicitly included
                if is_hidden and not include_hidden:
                    continue

                # Get impact score
                impact = self.get_measure_impact_score(m_table, m_name, depth=3)  # Lower depth for performance

                if impact.get('success'):
                    score = impact.get('impact_score', {})
                    total_deps = score.get('total_dependents', 0)
                    in_calc_groups = score.get('in_calculation_groups', False)
                    in_rls = score.get('in_rls_rules', False)

                    # Measure is unused if it has no dependents and not used in calc groups/RLS
                    if total_deps == 0 and not in_calc_groups and not in_rls:
                        unused_measures.append({
                            'table': m_table,
                            'measure': m_name,
                            'is_hidden': is_hidden
                        })

            logger.info(f"Found {len(unused_measures)} unused measures")

            return {
                'success': True,
                'unused_measures': unused_measures,
                'total_unused': len(unused_measures),
                'total_analyzed': len(all_measures),
                'unused_percentage': round(len(unused_measures) / len(all_measures) * 100, 1) if all_measures else 0,
                'recommendation': f"Consider removing {len(unused_measures)} unused measures to simplify the model"
            }

        except Exception as e:
            logger.error(f"Error finding unused measures: {e}")
            return {'success': False, 'error': str(e)}

    def get_deep_dependencies(self, table: str, measure: str, depth: int = 10) -> Dict[str, Any]:
        """
        Analyze dependencies to specified depth (default 10) with visualization data.

        Args:
            table: Table name containing the measure
            measure: Measure name
            depth: Maximum depth to traverse (default: 10)

        Returns:
            Dictionary with deep dependency tree and visualization data
        """
        try:
            # Build deep dependency tree
            tree_result = self.build_dependency_tree(table, measure, depth)
            if not tree_result.get('success'):
                return tree_result

            tree = tree_result.get('tree', {})

            # Extract metrics from tree
            metrics = self._extract_tree_metrics(tree)

            return {
                'success': True,
                'measure': {'table': table, 'name': measure},
                'max_depth': depth,
                'actual_depth': metrics['max_depth_reached'],
                'dependency_tree': tree,
                'metrics': metrics,
                'visualization_data': self._generate_tree_visualization_data(tree)
            }

        except Exception as e:
            logger.error(f"Error analyzing deep dependencies for {table}[{measure}]: {e}")
            return {'success': False, 'error': str(e)}

    def _extract_tree_metrics(self, tree: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from dependency tree."""
        total_measures = 0
        max_depth = 0
        circular_refs = 0
        max_depth_exceeded = False

        def traverse(node, current_depth=0):
            nonlocal total_measures, max_depth, circular_refs, max_depth_exceeded

            total_measures += 1
            max_depth = max(max_depth, current_depth)

            if node.get('circular'):
                circular_refs += 1
            if node.get('max_depth_reached'):
                max_depth_exceeded = True

            for child in node.get('dependencies', []):
                traverse(child, current_depth + 1)

        traverse(tree)

        return {
            'total_measures': total_measures,
            'max_depth_reached': max_depth,
            'circular_references': circular_refs,
            'max_depth_exceeded': max_depth_exceeded
        }

    def _generate_tree_visualization_data(self, tree: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data structure suitable for tree visualization (e.g., D3.js)."""
        def convert_node(node):
            result = {
                'name': f"{node.get('table', '')}[{node.get('measure', '')}]",
                'table': node.get('table', ''),
                'measure': node.get('measure', ''),
                'depth': node.get('depth', 0)
            }

            if node.get('circular'):
                result['circular'] = True
            if node.get('max_depth_reached'):
                result['max_depth_reached'] = True
            if node.get('error'):
                result['error'] = node['error']

            children = node.get('dependencies', [])
            if children:
                result['children'] = [convert_node(child) for child in children]

            return result

        return {
            'format': 'hierarchical',
            'tree': convert_node(tree),
            'description': 'Tree structure suitable for D3.js or similar visualization libraries'
        }
