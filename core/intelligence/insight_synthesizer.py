"""
Insight Synthesizer

This module combines insights from multiple analysis tools to discover
cross-domain patterns, hidden issues, and optimization opportunities.
"""

from typing import Dict, Any, List, Set, Optional
import logging
import re

logger = logging.getLogger(__name__)


class InsightSynthesizer:
    """Combines insights from multiple analysis tools"""

    def __init__(self):
        self.insight_cache: Dict[str, List[Dict[str, Any]]] = {}

    def synthesize_measure_insights(
        self,
        measure_details: Dict[str, Any],
        dependencies: Dict[str, Any],
        dax_analysis: Dict[str, Any],
        relationships: Dict[str, Any],
        performance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize insights by connecting:
        - DAX patterns
        - Dependencies
        - Relationship structure
        - Performance characteristics

        Args:
            measure_details: Result from get_measure_details
            dependencies: Result from analyze_measure_dependencies
            dax_analysis: Result from dax_intelligence
            relationships: Result from list_relationships
            performance: Optional result from run_dax with profiling

        Returns:
            Synthesized insights with cross-domain analysis
        """
        insights = {
            'cross_domain_insights': [],
            'hidden_issues': [],
            'optimization_opportunities': [],
            'architectural_concerns': []
        }

        # Extract key information
        expression = measure_details.get('expression', '')
        dep_tables = set(dependencies.get('referenced_tables', []))
        dep_measures = dependencies.get('referenced_measures', [])
        dep_columns = dependencies.get('referenced_columns', [])

        dax_data = dax_analysis.get('dax_analysis', {}) if isinstance(dax_analysis.get('dax_analysis'), dict) else {}
        context_transitions = dax_data.get('context_transitions', {})
        iterators = dax_data.get('iterators', {})

        # INSIGHT 1: Context transitions + Relationships
        if context_transitions.get('count', 0) > 0:
            involved_rels = self._find_relationships_for_tables(dep_tables, relationships)

            if involved_rels:
                for rel in involved_rels:
                    # Check for inactive relationships with context transitions
                    if rel.get('isActive') == False:
                        insights['cross_domain_insights'].append({
                            'category': 'Context + Relationships',
                            'finding': f"Measure uses CALCULATE but {rel['fromTable']}→{rel['toTable']} relationship is INACTIVE",
                            'impact': 'This measure will NOT automatically use this relationship unless USERELATIONSHIP is specified',
                            'severity': 'high',
                            'evidence': {
                                'dax_pattern': 'CALCULATE detected',
                                'inactive_relationship': f"{rel['fromTable']}→{rel['toTable']}"
                            },
                            'recommendation': f"Add USERELATIONSHIP({rel['fromTable']}[{rel.get('fromColumn', '')}], {rel['toTable']}[{rel.get('toColumn', '')}]) if you need this relationship"
                        })

                    # Check for many-to-many relationships
                    if rel.get('fromCardinality') == 'many' and rel.get('toCardinality') == 'many':
                        insights['architectural_concerns'].append({
                            'category': 'Many-to-Many Relationships',
                            'finding': f"Measure depends on many-to-many relationship {rel['fromTable']}↔{rel['toTable']}",
                            'impact': 'Many-to-many relationships can cause unexpected aggregation results and performance issues',
                            'severity': 'high',
                            'recommendation': 'Review if this relationship is necessary or if a bridge table would be better',
                            'details': {
                                'from_cardinality': rel.get('fromCardinality'),
                                'to_cardinality': rel.get('toCardinality'),
                                'cross_filter': rel.get('crossFilteringBehavior', 'single')
                            }
                        })

                    # Check for bidirectional filtering with context transitions
                    if rel.get('crossFilteringBehavior') == 'bothDirections' and context_transitions.get('count', 0) > 2:
                        insights['cross_domain_insights'].append({
                            'category': 'Bidirectional Filtering + Context',
                            'finding': f"Measure uses multiple CALCULATE operations with bidirectional relationship {rel['fromTable']}↔{rel['toTable']}",
                            'impact': 'Bidirectional filtering with complex context transitions can cause performance issues and unexpected results',
                            'severity': 'medium',
                            'recommendation': 'Consider using TREATAS or CROSSFILTER instead of permanent bidirectional relationships'
                        })

        # INSIGHT 2: Iterators + Table Size
        if iterators.get('count', 0) > 0:
            iterator_functions = iterators.get('functions', [])

            for table in dep_tables:
                # Check for common iterator patterns
                if any(func in ['SUMX', 'AVERAGEX', 'COUNTX', 'FILTER'] for func in iterator_functions):
                    insights['optimization_opportunities'].append({
                        'category': 'Iterator Performance',
                        'finding': f"Iterator function operating on table '{table}'",
                        'impact': f"If '{table}' is large (>100K rows), this could cause slow performance",
                        'recommendation': 'Consider using CALCULATE with filter arguments instead of iterator+FILTER pattern',
                        'pattern': {
                            'current': 'SUMX(FILTER(Table, condition), expression)',
                            'optimized': 'CALCULATE(SUM(Table[Column]), condition)'
                        },
                        'severity': 'medium'
                    })

        # INSIGHT 3: Circular Dependencies Detection
        circular_deps = self._detect_circular_dependencies(measure_details, dependencies, dep_measures)
        if circular_deps:
            insights['hidden_issues'].append({
                'category': 'Circular Dependencies',
                'finding': f"Potential circular dependency chain detected: {' → '.join(circular_deps)}",
                'impact': 'Circular dependencies can cause evaluation errors or infinite loops',
                'severity': 'critical',
                'recommendation': 'Refactor to break the circular chain by introducing intermediate measures or calculations'
            })

        # INSIGHT 4: ALL/ALLEXCEPT + Relationships
        if 'ALL(' in expression.upper() or 'ALLEXCEPT(' in expression.upper():
            affected_tables = self._extract_all_tables(expression)

            insights['cross_domain_insights'].append({
                'category': 'Filter Removal + Relationships',
                'finding': f"Measure uses ALL/ALLEXCEPT to remove filters from {len(affected_tables)} table(s)",
                'impact': f"This affects filter context propagation through {len(involved_rels)} relationship(s)",
                'detail': 'ALL removes filters from specified tables, which also stops filter propagation through relationships',
                'tables_affected': list(affected_tables),
                'severity': 'medium',
                'recommendation': 'Verify this is intentional - often used for totals/YTD calculations'
            })

        # INSIGHT 5: Nested CALCULATE + Complexity
        complexity_score = dax_analysis.get('complexity_assessment', {}).get('score', 0)
        nesting_level = context_transitions.get('max_nesting_level', 0)

        if complexity_score > 60 and nesting_level > 3:
            insights['optimization_opportunities'].append({
                'category': 'Complexity + Maintainability',
                'finding': f"High complexity (score: {complexity_score}) with deep nesting ({nesting_level} levels)",
                'impact': 'Difficult to understand, debug, and maintain',
                'severity': 'high',
                'recommendation': 'Break into multiple simpler measures or use calculation groups',
                'refactoring_benefit': 'Improves readability, enables reusability, easier to optimize',
                'suggestion': {
                    'approach': 'Extract repeated calculations into separate measures',
                    'use_variables': 'Use VAR to store intermediate results and reduce redundancy'
                }
            })

        # INSIGHT 6: Unused Relationships
        if len(dep_tables) > 1:
            unused_rels = self._find_unused_relationships(dep_tables, involved_rels, relationships)

            if unused_rels:
                insights['architectural_concerns'].append({
                    'category': 'Model Structure',
                    'finding': f"Measure uses {len(dep_tables)} tables but doesn't leverage {len(unused_rels)} available relationships",
                    'detail': [f"{r['fromTable']}→{r['toTable']}" for r in unused_rels[:3]],
                    'impact': 'Model may be over-engineered or measure logic may be incomplete',
                    'severity': 'low',
                    'recommendation': 'Review if these relationships are actually needed in the model'
                })

        # INSIGHT 7: Performance + Complexity Correlation
        if performance:
            exec_time = performance.get('execution_time_ms', 0)

            if exec_time > 1000 and complexity_score > 50:
                insights['optimization_opportunities'].append({
                    'category': 'Performance + Complexity',
                    'finding': f"Slow execution ({exec_time}ms) combined with high complexity (score: {complexity_score})",
                    'impact': 'User experience will be degraded, especially in interactive reports',
                    'severity': 'high',
                    'immediate_actions': [
                        'Profile the query to identify bottlenecks',
                        'Check if iterators can be replaced with CALCULATE',
                        'Consider caching with variables',
                        'Review if all calculations are necessary'
                    ]
                })

            # Check for specific performance patterns
            if 'FILTER(' in expression.upper() and exec_time > 500:
                insights['optimization_opportunities'].append({
                    'category': 'FILTER Performance',
                    'finding': f"FILTER function detected with {exec_time}ms execution time",
                    'impact': 'FILTER creates a new table in memory which can be expensive',
                    'severity': 'medium',
                    'recommendation': 'Replace FILTER with native CALCULATE filter arguments where possible',
                    'example': "CALCULATE(SUM(Table[Column]), Table[Status] = 'Active') instead of SUMX(FILTER(Table, ...), ...)"
                })

        # INSIGHT 8: Dependency Depth Analysis
        if len(dep_measures) > 5:
            insights['architectural_concerns'].append({
                'category': 'Deep Measure Dependencies',
                'finding': f"Measure depends on {len(dep_measures)} other measures",
                'impact': 'Deep dependency chains make debugging difficult and can cause cascading recalculations',
                'severity': 'medium',
                'recommendation': 'Consider flattening the dependency tree',
                'measures_referenced': dep_measures[:5]  # Show first 5
            })

        # INSIGHT 9: Column Usage Patterns
        if len(dep_columns) > 10:
            insights['cross_domain_insights'].append({
                'category': 'Column Usage',
                'finding': f"Measure references {len(dep_columns)} columns from {len(dep_tables)} tables",
                'impact': 'Wide column usage may indicate the measure is doing too much',
                'severity': 'low',
                'recommendation': 'Consider splitting into multiple focused measures'
            })

        # INSIGHT 10: Time Intelligence Patterns
        time_intel_funcs = ['DATEADD', 'DATESBETWEEN', 'SAMEPERIODLASTYEAR', 'PARALLELPERIOD', 'TOTALYTD', 'TOTALQTD']
        if any(func in expression.upper() for func in time_intel_funcs):
            # Check if a Date table is referenced
            date_table_present = any('date' in table.lower() or 'calendar' in table.lower() for table in dep_tables)

            if not date_table_present:
                insights['hidden_issues'].append({
                    'category': 'Time Intelligence',
                    'finding': 'Time intelligence function detected but no obvious Date table referenced',
                    'impact': 'Time intelligence requires a proper Date table marked in the model',
                    'severity': 'high',
                    'recommendation': 'Verify that a Date table is properly configured and marked as such in the model'
                })

        return insights

    def _find_relationships_for_tables(
        self,
        tables: Set[str],
        relationships: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find relationships that connect the specified tables"""
        involved_rels = []
        all_rels = relationships.get('rows', [])

        for rel in all_rels:
            from_table = rel.get('fromTable')
            to_table = rel.get('toTable')

            if from_table in tables or to_table in tables:
                involved_rels.append(rel)

        return involved_rels

    def _find_unused_relationships(
        self,
        dep_tables: Set[str],
        involved_rels: List[Dict[str, Any]],
        all_relationships: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find relationships that exist between dependent tables but aren't actively used"""
        all_rels = all_relationships.get('rows', [])

        # Get all table pairs from dependencies
        table_list = list(dep_tables)
        used_pairs = set()

        for rel in involved_rels:
            pair = (rel.get('fromTable'), rel.get('toTable'))
            used_pairs.add(pair)
            used_pairs.add((pair[1], pair[0]))  # Both directions

        # Find relationships between dependent tables that aren't in involved_rels
        unused = []
        for rel in all_rels:
            from_table = rel.get('fromTable')
            to_table = rel.get('toTable')

            if from_table in dep_tables and to_table in dep_tables:
                if (from_table, to_table) not in used_pairs:
                    unused.append(rel)

        return unused

    def _detect_circular_dependencies(
        self,
        measure_details: Dict[str, Any],
        dependencies: Dict[str, Any],
        dep_measures: List[str]
    ) -> List[str]:
        """
        Detect circular dependency chains

        Note: This is a simplified detection. Full implementation would need
        recursive dependency graph traversal.
        """
        # For now, just check if measure references itself (direct circular)
        measure_name = measure_details.get('name', '')
        table_name = measure_details.get('table', '')
        full_name = f"{table_name}[{measure_name}]"

        # Check for self-reference
        for dep_measure in dep_measures:
            if measure_name in dep_measure or full_name == dep_measure:
                return [full_name, dep_measure, full_name]

        # TODO: Implement deeper circular detection with graph traversal
        return []

    def _extract_all_tables(self, expression: str) -> Set[str]:
        """Extract table names from ALL/ALLEXCEPT functions"""
        tables = set()

        # Pattern to match ALL(TableName) or ALLEXCEPT(TableName, ...)
        patterns = [
            r'ALL\s*\(\s*([A-Za-z0-9_]+)\s*\)',
            r'ALLEXCEPT\s*\(\s*([A-Za-z0-9_]+)\s*,'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, expression, re.IGNORECASE)
            for match in matches:
                tables.add(match.group(1))

        return tables

    def synthesize_model_insights(
        self,
        tables: Dict[str, Any],
        measures: Dict[str, Any],
        relationships: Dict[str, Any],
        comprehensive_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize model-level insights

        Args:
            tables: Result from list_tables
            measures: Result from list_measures
            relationships: Result from list_relationships
            comprehensive_analysis: Optional result from comprehensive_analysis

        Returns:
            Model-level insights
        """
        insights = {
            'model_summary': {},
            'structural_issues': [],
            'best_practice_violations': [],
            'optimization_opportunities': []
        }

        table_rows = tables.get('rows', [])
        measure_rows = measures.get('rows', [])
        rel_rows = relationships.get('rows', [])

        # Calculate model metrics
        table_count = len(table_rows)
        measure_count = len(measure_rows)
        rel_count = len(rel_rows)

        insights['model_summary'] = {
            'tables': table_count,
            'measures': measure_count,
            'relationships': rel_count,
            'avg_measures_per_table': round(measure_count / table_count, 1) if table_count > 0 else 0
        }

        # Check for orphaned tables
        connected_tables = set()
        for rel in rel_rows:
            connected_tables.add(rel.get('fromTable'))
            connected_tables.add(rel.get('toTable'))

        all_table_names = {t.get('Name') for t in table_rows}
        orphaned = all_table_names - connected_tables

        if orphaned:
            insights['structural_issues'].append({
                'category': 'Orphaned Tables',
                'finding': f"{len(orphaned)} tables are not connected to the model via relationships",
                'tables': list(orphaned),
                'impact': 'These tables cannot be used in cross-table analysis',
                'severity': 'medium',
                'recommendation': 'Review if these tables are needed or should be connected'
            })

        # Check for many-to-many relationships
        many_to_many = [r for r in rel_rows if r.get('fromCardinality') == 'many' and r.get('toCardinality') == 'many']

        if many_to_many:
            insights['structural_issues'].append({
                'category': 'Many-to-Many Relationships',
                'finding': f"{len(many_to_many)} many-to-many relationships found",
                'relationships': [f"{r['fromTable']}↔{r['toTable']}" for r in many_to_many],
                'impact': 'Can cause performance issues and unexpected aggregation results',
                'severity': 'high',
                'recommendation': 'Consider using bridge tables with one-to-many relationships'
            })

        # Check for inactive relationships
        inactive = [r for r in rel_rows if not r.get('isActive', True)]

        if inactive:
            insights['structural_issues'].append({
                'category': 'Inactive Relationships',
                'finding': f"{len(inactive)} inactive relationships found",
                'relationships': [f"{r['fromTable']}→{r['toTable']}" for r in inactive],
                'impact': 'Must be explicitly activated with USERELATIONSHIP',
                'severity': 'low',
                'recommendation': 'Document why these relationships are inactive and where they should be used'
            })

        # Check for bidirectional relationships
        bidirectional = [r for r in rel_rows if r.get('crossFilteringBehavior') == 'bothDirections']

        if bidirectional:
            insights['best_practice_violations'].append({
                'category': 'Bidirectional Filtering',
                'finding': f"{len(bidirectional)} bidirectional relationships found",
                'relationships': [f"{r['fromTable']}↔{r['toTable']}" for r in bidirectional],
                'impact': 'Can cause performance issues and ambiguous filter context',
                'severity': 'medium',
                'recommendation': 'Use TREATAS or CROSSFILTER functions instead where possible'
            })

        # Check measure concentration
        measure_distribution = {}
        for m in measure_rows:
            table = m.get('Table', 'Unknown')
            measure_distribution[table] = measure_distribution.get(table, 0) + 1

        # Find tables with many measures
        heavy_tables = {t: count for t, count in measure_distribution.items() if count > 20}

        if heavy_tables:
            insights['optimization_opportunities'].append({
                'category': 'Measure Organization',
                'finding': f"{len(heavy_tables)} tables contain more than 20 measures",
                'tables': heavy_tables,
                'impact': 'Many measures in one table can make model harder to navigate',
                'severity': 'low',
                'recommendation': 'Consider organizing measures into dedicated measure tables or folders'
            })

        # Incorporate comprehensive analysis if available
        if comprehensive_analysis:
            ca_issues = comprehensive_analysis.get('issues', [])

            # Group by category
            for issue in ca_issues:
                severity = issue.get('severity', 'medium')
                category = issue.get('category', 'General')

                if severity in ['critical', 'high']:
                    insights['best_practice_violations'].append({
                        'category': category,
                        'finding': issue.get('message', ''),
                        'severity': severity,
                        'recommendation': issue.get('recommendation', '')
                    })

        return insights

    def clear_cache(self):
        """Clear the insight cache"""
        self.insight_cache = {}

    def get_cached_insights(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached insights for a key"""
        return self.insight_cache.get(key)

    def cache_insights(self, key: str, insights: List[Dict[str, Any]]):
        """Cache insights for a key"""
        self.insight_cache[key] = insights
