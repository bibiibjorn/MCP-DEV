"""
Suggestion Engine

This module generates proactive suggestions based on analysis results,
guiding users and AI assistants toward the next best actions.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """Generates proactive suggestions based on analysis results"""

    def __init__(self):
        self.suggestion_history: List[Dict[str, Any]] = []
        self._max_history = 50

    def generate_suggestions(
        self,
        tool_name: str,
        result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate contextual suggestions based on tool result

        Args:
            tool_name: Name of the tool that was executed
            result: Result returned by the tool
            context: Optional additional context

        Returns:
            List of suggestions sorted by priority (highest first)
        """
        context = context or {}
        suggestions = []

        # Route to specific suggestion generator
        if tool_name == "get_measure_details":
            suggestions.extend(self._suggest_for_measure_details(result, context))

        elif tool_name == "analyze_measure_dependencies":
            suggestions.extend(self._suggest_for_dependencies(result, context))

        elif tool_name == "list_relationships":
            suggestions.extend(self._suggest_for_relationships(result, context))

        elif tool_name == "dax_intelligence":
            suggestions.extend(self._suggest_for_dax_analysis(result, context))

        elif tool_name == "comprehensive_analysis":
            suggestions.extend(self._suggest_for_comprehensive_analysis(result, context))

        elif tool_name == "run_dax":
            suggestions.extend(self._suggest_for_query_execution(result, context))

        elif tool_name == "describe_table":
            suggestions.extend(self._suggest_for_table_description(result, context))

        elif tool_name == "list_tables":
            suggestions.extend(self._suggest_for_table_list(result, context))

        elif tool_name == "list_measures":
            suggestions.extend(self._suggest_for_measure_list(result, context))

        elif tool_name == "get_measure_impact":
            suggestions.extend(self._suggest_for_impact_analysis(result, context))

        # Sort by priority (highest first)
        sorted_suggestions = sorted(suggestions, key=lambda x: x.get('priority', 0), reverse=True)

        # Store in history
        self._add_to_history(tool_name, sorted_suggestions)

        return sorted_suggestions

    def _suggest_for_measure_details(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after getting measure details"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        expression = result.get('expression', '')
        table = result.get('table', '')
        measure = result.get('name', '')

        # Always suggest dependency analysis
        suggestions.append({
            'action': 'analyze_dependencies',
            'tool': 'analyze_measure_dependencies',
            'reason': 'Understand what this measure depends on',
            'priority': 9,
            'category': 'Analysis',
            'context': {
                'table': table,
                'measure': measure
            }
        })

        # Always suggest impact analysis
        suggestions.append({
            'action': 'check_impact',
            'tool': 'get_measure_impact',
            'reason': 'See what other measures use this one',
            'priority': 8,
            'category': 'Analysis',
            'context': {
                'table': table,
                'measure': measure
            }
        })

        # Suggest DAX analysis if expression is non-trivial
        if len(expression) > 50 or any(keyword in expression.upper() for keyword in ['CALCULATE', 'FILTER', 'SUMX', 'AVERAGEX']):
            suggestions.append({
                'action': 'analyze_dax_patterns',
                'tool': 'dax_intelligence',
                'reason': 'DAX expression is complex - analyze patterns and context transitions',
                'priority': 8,
                'category': 'DAX Analysis',
                'context': {
                    'expression': expression,
                    'analysis_mode': 'report'
                }
            })

        # Suggest testing the measure
        suggestions.append({
            'action': 'test_execution',
            'tool': 'run_dax',
            'reason': 'Test measure execution and check performance',
            'priority': 6,
            'category': 'Testing',
            'context': {
                'query': f'EVALUATE ROW("Result", [{measure}])',
                'mode': 'profile'
            }
        })

        # Check for missing description
        if not result.get('description'):
            suggestions.append({
                'action': 'add_description',
                'reason': 'Measure lacks documentation - consider adding a description',
                'priority': 5,
                'category': 'Documentation'
            })

        # Check for potentially problematic patterns
        if 'ALL(' in expression.upper():
            suggestions.append({
                'action': 'verify_all_usage',
                'reason': 'DAX uses ALL() which removes filters - verify this is intentional',
                'priority': 7,
                'category': 'Validation',
                'detail': 'ALL() will show totals across all data regardless of slicers'
            })

        if 'EARLIER(' in expression.upper():
            suggestions.append({
                'action': 'review_row_context',
                'reason': 'EARLIER() detected - complex row context manipulation',
                'priority': 7,
                'category': 'Complexity',
                'detail': 'EARLIER is often difficult to understand and maintain'
            })

        return suggestions

    def _suggest_for_dependencies(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after dependency analysis"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        tables = result.get('referenced_tables', [])
        measures = result.get('referenced_measures', [])
        columns = result.get('referenced_columns', [])

        # Suggest relationship check if multiple tables involved
        if len(tables) > 1:
            suggestions.append({
                'action': 'check_relationships',
                'tool': 'list_relationships',
                'reason': f'Measure uses {len(tables)} tables - validate relationships between them',
                'priority': 8,
                'category': 'Relationships',
                'context': {},
                'tables_involved': tables
            })

        # Suggest analyzing dependent measures if there are many
        if len(measures) > 3:
            suggestions.append({
                'action': 'analyze_dependent_measures',
                'reason': f'This measure depends on {len(measures)} other measures - consider reviewing them',
                'priority': 6,
                'category': 'Dependencies',
                'measures': measures[:5]  # Show top 5
            })

        # Suggest checking table sizes for performance
        if len(tables) > 0:
            suggestions.append({
                'action': 'check_table_sizes',
                'tool': 'describe_table',
                'reason': 'Check if dependent tables are large (affects performance)',
                'priority': 5,
                'category': 'Performance',
                'context': {
                    'tables': tables
                }
            })

        # Warn about deep dependency chains
        if len(measures) > 5:
            suggestions.append({
                'action': 'review_dependency_depth',
                'reason': f'Deep dependency chain ({len(measures)} measures) can make debugging difficult',
                'priority': 7,
                'category': 'Architecture',
                'recommendation': 'Consider flattening the dependency tree'
            })

        # Suggest column distribution analysis if many columns used
        if len(columns) > 8:
            suggestions.append({
                'action': 'review_column_usage',
                'reason': f'Measure references {len(columns)} columns - may be doing too much',
                'priority': 5,
                'category': 'Architecture',
                'recommendation': 'Consider splitting into multiple focused measures'
            })

        return suggestions

    def _suggest_for_relationships(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after listing relationships"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        rows = result.get('rows', [])

        # Check for inactive relationships
        inactive = [r for r in rows if not r.get('isActive', True)]
        if inactive:
            suggestions.append({
                'action': 'investigate_inactive_relationships',
                'reason': f'{len(inactive)} inactive relationships found - verify they\'re used with USERELATIONSHIP',
                'priority': 7,
                'category': 'Validation',
                'details': [f"{r.get('fromTable')}→{r.get('toTable')}" for r in inactive[:5]]
            })

        # Check for many-to-many relationships
        many_to_many = [r for r in rows if r.get('fromCardinality') == 'many' and r.get('toCardinality') == 'many']
        if many_to_many:
            suggestions.append({
                'action': 'review_many_to_many',
                'reason': f'{len(many_to_many)} many-to-many relationships can cause performance and correctness issues',
                'priority': 8,
                'category': 'Architecture',
                'recommendation': 'Consider using bridge tables instead',
                'details': [f"{r.get('fromTable')}↔{r.get('toTable')}" for r in many_to_many[:5]]
            })

        # Check for bidirectional relationships
        bidirectional = [r for r in rows if r.get('crossFilteringBehavior') == 'bothDirections']
        if bidirectional:
            suggestions.append({
                'action': 'review_bidirectional_filtering',
                'reason': f'{len(bidirectional)} bidirectional relationships can cause performance issues',
                'priority': 7,
                'category': 'Performance',
                'recommendation': 'Use TREATAS or CROSSFILTER functions instead where possible',
                'details': [f"{r.get('fromTable')}↔{r.get('toTable')}" for r in bidirectional[:5]]
            })

        # Suggest comprehensive analysis if many issues
        if len(inactive) + len(many_to_many) + len(bidirectional) > 5:
            suggestions.append({
                'action': 'run_comprehensive_analysis',
                'tool': 'comprehensive_analysis',
                'reason': 'Multiple relationship issues detected - run full model analysis',
                'priority': 9,
                'category': 'Analysis',
                'context': {
                    'scope': 'integrity',
                    'depth': 'balanced'
                }
            })

        return suggestions

    def _suggest_for_dax_analysis(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after DAX analysis"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        anti_patterns = result.get('anti_patterns', [])
        complexity = result.get('complexity_assessment', {})
        complexity_level = complexity.get('level', '')

        # Suggest refactoring if complex
        if complexity_level in ['High', 'Very High']:
            suggestions.append({
                'action': 'refactor_measure',
                'reason': f'{complexity_level} complexity detected - consider breaking into smaller measures',
                'priority': 7,
                'category': 'Refactoring',
                'recommendation': 'Use variables or split into multiple helper measures',
                'complexity_score': complexity.get('score', 0)
            })

        # Suggest performance testing if anti-patterns found
        if len(anti_patterns) > 0:
            suggestions.append({
                'action': 'performance_test',
                'tool': 'run_dax',
                'reason': f'{len(anti_patterns)} anti-patterns detected - test actual performance',
                'priority': 8,
                'category': 'Performance',
                'context': {
                    'mode': 'profile'
                },
                'anti_patterns': [ap.get('pattern', '') for ap in anti_patterns[:3]]
            })

        # Suggest specific fixes for common anti-patterns
        for pattern in anti_patterns:
            pattern_name = pattern.get('pattern', '')

            if 'FILTER' in pattern_name and 'iterator' in pattern_name.lower():
                suggestions.append({
                    'action': 'optimize_filter_usage',
                    'reason': 'FILTER in iterator can be replaced with CALCULATE filter arguments',
                    'priority': 7,
                    'category': 'Optimization',
                    'example': 'Replace SUMX(FILTER(...), ...) with CALCULATE(SUM(...), filter_condition)'
                })

        # Check for context transitions
        dax_data = result.get('dax_analysis', {})
        context_transitions = dax_data.get('context_transitions', {})

        if context_transitions.get('count', 0) > 3:
            suggestions.append({
                'action': 'review_context_transitions',
                'reason': f'{context_transitions.get("count")} context transitions detected - verify all are necessary',
                'priority': 6,
                'category': 'Complexity',
                'recommendation': 'Each context transition has performance cost'
            })

        # Suggest documentation
        if complexity_level in ['High', 'Very High']:
            suggestions.append({
                'action': 'add_documentation',
                'reason': 'Complex measure should be well-documented for maintainability',
                'priority': 6,
                'category': 'Documentation'
            })

        return suggestions

    def _suggest_for_comprehensive_analysis(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after comprehensive analysis"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        issues = result.get('issues', [])
        high_priority = [i for i in issues if i.get('severity') in ['high', 'critical']]
        medium_priority = [i for i in issues if i.get('severity') == 'medium']

        if high_priority:
            suggestions.append({
                'action': 'address_critical_issues',
                'reason': f'{len(high_priority)} critical/high-priority issues found',
                'priority': 10,
                'category': 'Issues',
                'next_steps': 'Review and fix high-priority issues first',
                'issues': [i.get('message', '')[:100] for i in high_priority[:3]]
            })

        if medium_priority:
            suggestions.append({
                'action': 'review_medium_issues',
                'reason': f'{len(medium_priority)} medium-priority issues found',
                'priority': 7,
                'category': 'Issues',
                'recommendation': 'Address medium issues after critical ones'
            })

        # Suggest documentation generation
        suggestions.append({
            'action': 'generate_documentation',
            'tool': 'generate_documentation',
            'reason': 'Generate comprehensive model documentation including analysis results',
            'priority': 6,
            'category': 'Documentation',
            'context': {
                'include_analysis': True
            }
        })

        # Suggest export for reporting
        suggestions.append({
            'action': 'export_results',
            'tool': 'export_model_schema',
            'reason': 'Export analysis results and model schema for reporting',
            'priority': 5,
            'category': 'Export'
        })

        return suggestions

    def _suggest_for_query_execution(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after query execution"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        exec_time = result.get('execution_time_ms', 0)

        # Suggest optimization if slow
        if exec_time > 1000:
            suggestions.append({
                'action': 'optimize_query',
                'tool': 'dax_intelligence',
                'reason': f'Slow execution time ({exec_time}ms) - analyze for optimization opportunities',
                'priority': 9,
                'category': 'Performance',
                'context': {
                    'expression': context.get('query', ''),
                    'analysis_mode': 'optimize'
                }
            })

        # Suggest profiling if not already done
        if context.get('mode') != 'profile' and exec_time > 500:
            suggestions.append({
                'action': 'profile_query',
                'tool': 'run_dax',
                'reason': 'Run with profiling enabled to identify bottlenecks',
                'priority': 8,
                'category': 'Performance',
                'context': {
                    'query': context.get('query', ''),
                    'mode': 'profile'
                }
            })

        # Suggest checking data volume
        if exec_time > 2000:
            suggestions.append({
                'action': 'check_data_volume',
                'reason': 'Very slow execution - check if iterating over large tables',
                'priority': 8,
                'category': 'Performance',
                'recommendation': 'Use CALCULATE instead of iterators where possible'
            })

        return suggestions

    def _suggest_for_table_description(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after describing a table"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        table_name = result.get('name', '')
        row_count = result.get('row_count', 0)

        # Suggest relationship check
        suggestions.append({
            'action': 'check_relationships',
            'tool': 'list_relationships',
            'reason': 'Check how this table relates to other tables in the model',
            'priority': 8,
            'category': 'Relationships',
            'context': {}
        })

        # Suggest measure list
        suggestions.append({
            'action': 'list_measures',
            'tool': 'list_measures',
            'reason': 'See what measures exist in this table',
            'priority': 7,
            'category': 'Analysis',
            'context': {}
        })

        # Suggest data preview if table is small
        if row_count < 10000:
            suggestions.append({
                'action': 'preview_data',
                'tool': 'preview_table_data',
                'reason': 'Table is small enough to preview sample data',
                'priority': 6,
                'category': 'Data',
                'context': {
                    'table': table_name,
                    'max_rows': 50
                }
            })

        # Warn about large tables
        if row_count > 1000000:
            suggestions.append({
                'action': 'review_large_table',
                'reason': f'Large table ({row_count:,} rows) - review aggregations carefully',
                'priority': 7,
                'category': 'Performance',
                'recommendation': 'Use CALCULATE with filters instead of iterators on this table'
            })

        return suggestions

    def _suggest_for_table_list(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after listing tables"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        tables = result.get('rows', [])

        if len(tables) > 0:
            # Suggest relationship analysis
            suggestions.append({
                'action': 'analyze_relationships',
                'tool': 'list_relationships',
                'reason': 'Understand how tables are connected',
                'priority': 8,
                'category': 'Relationships',
                'context': {}
            })

            # Suggest model health check
            suggestions.append({
                'action': 'model_health_check',
                'reason': 'Run comprehensive model health check',
                'priority': 7,
                'category': 'Analysis',
                'workflow': 'model_health_check'
            })

        return suggestions

    def _suggest_for_measure_list(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after listing measures"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        measures = result.get('rows', [])

        if len(measures) > 20:
            suggestions.append({
                'action': 'review_measure_organization',
                'reason': f'Model contains {len(measures)} measures - consider organizing into folders',
                'priority': 6,
                'category': 'Organization',
                'recommendation': 'Use display folders or dedicated measure tables'
            })

        return suggestions

    def _suggest_for_impact_analysis(self, result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggestions after impact analysis"""
        suggestions = []

        if not result.get('success', False):
            return suggestions

        downstream_count = result.get('downstream_count', 0)

        if downstream_count > 10:
            suggestions.append({
                'action': 'careful_modification',
                'reason': f'High impact: {downstream_count} measures depend on this one',
                'priority': 9,
                'category': 'Safety',
                'recommendation': 'Test thoroughly after any changes'
            })

        if downstream_count == 0:
            suggestions.append({
                'action': 'safe_to_modify',
                'reason': 'No downstream dependencies - safe to modify or delete',
                'priority': 6,
                'category': 'Safety'
            })

        return suggestions

    def _add_to_history(self, tool_name: str, suggestions: List[Dict[str, Any]]):
        """Add suggestions to history"""
        self.suggestion_history.append({
            'tool': tool_name,
            'suggestions': suggestions,
            'timestamp': logger.name  # Simple timestamp placeholder
        })

        # Trim history if needed
        if len(self.suggestion_history) > self._max_history:
            self.suggestion_history = self.suggestion_history[-self._max_history:]

    def get_suggestion_history(self) -> List[Dict[str, Any]]:
        """Get suggestion history"""
        return self.suggestion_history

    def clear_history(self):
        """Clear suggestion history"""
        self.suggestion_history = []
