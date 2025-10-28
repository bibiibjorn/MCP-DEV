"""Performance and BPA analysis orchestration."""
import logging
import time
from typing import Any, Dict, List, Optional
from .base_orchestrator import BaseOrchestrator

logger = logging.getLogger(__name__)

class AnalysisOrchestrator(BaseOrchestrator):
    """Handles performance and BPA analysis workflows."""

    def validate_best_practices(self, connection_state) -> Dict[str, Any]:
        """Validate model best practices with simple naming checks."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        validator = connection_state.model_validator
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        issues: List[Dict[str, Any]] = []
        # Include integrity issues if validator available
        if validator:
            integrity = validator.validate_model_integrity()
            if integrity.get('success'):
                for i in integrity.get('issues', []):
                    issues.append(i)
        # Simple naming checks
        tables = executor.execute_info_query('TABLES')
        if tables.get('success'):
            for t in tables.get('rows', []):
                name = t.get('Name') or ''
                if name != name.strip():
                    issues.append({'type': 'naming', 'severity': 'low', 'object': f"Table:{name}", 'description': 'Leading/trailing spaces in table name'})
        measures = executor.execute_info_query('MEASURES')
        if measures.get('success'):
            for m in measures.get('rows', []):
                name = m.get('Name') or ''
                if ' ' in name and name.strip().endswith(')'):
                    pass
                # Example heuristic: discourage very short names
                if len(name.strip()) < 2:
                    issues.append({'type': 'naming', 'severity': 'low', 'object': f"Measure:{name}", 'description': 'Very short measure name'})
        return {'success': True, 'issues': issues, 'total_issues': len(issues)}

    def analyze_queries_batch(self, connection_state, queries: List[str], runs: Optional[int] = 3, clear_cache: bool = True, include_event_counts: bool = False) -> Dict[str, Any]:
        """Run performance analysis on multiple queries in batch."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        perf = connection_state.performance_analyzer
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        r = self._get_default_perf_runs(runs)
        results: List[Dict[str, Any]] = []
        for q in queries or []:
            if perf:
                results.append(perf.analyze_query(executor, q, r, bool(clear_cache), include_event_counts))
            else:
                # basic timing fallback
                start = time.time()
                res = executor.validate_and_execute_dax(q, 0)
                ms = (time.time() - start) * 1000
                results.append({'success': res.get('success', False), 'query': q, 'summary': {'avg_execution_ms': round(ms, 2), 'note': 'analyzer unavailable'}})
        return {'success': True, 'runs': r, 'items': results}

    def profile_columns(self, connection_state, table: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Profile columns in a table with min/max/distinct/nulls stats."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        # Build per-column profiling queries
        cols = columns or []
        if not cols:
            # fetch all columns for table
            info = executor.execute_info_query('COLUMNS', table_name=table)
            if not info.get('success'):
                return info
            cols = [c.get('Name') for c in info.get('rows', []) if c.get('Name')]
        results: List[Dict[str, Any]] = []
        for col in cols[:200]:  # safety cap
            q = (
                f"EVALUATE ROW(\"Min\", MIN('{table}'[{col}]), "
                f"\"Max\", MAX('{table}'[{col}]), "
                f"\"Distinct\", DISTINCTCOUNT('{table}'[{col}]), "
                f"\"Nulls\", COUNTBLANK('{table}'[{col}]))"
            )
            r = executor.validate_and_execute_dax(q, 0)
            results.append({'column': col, 'success': r.get('success', False), 'stats': (r.get('rows') or [{}])[0] if r.get('rows') else {}})
        return {'success': True, 'table': table, 'columns': len(results), 'results': results}

    def get_value_distribution(self, connection_state, table: str, column: str, top_n: int = 50) -> Dict[str, Any]:
        """Get value distribution for a column."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        q = (
            f"EVALUATE TOPN({int(top_n)}, "
            f"SUMMARIZECOLUMNS('{table}'[{column}], \"Count\", COUNTROWS('{table}')), [Count], DESC)"
        )
        return executor.validate_and_execute_dax(q, 0)

    def relationship_overview(self, connection_state) -> Dict[str, Any]:
        """Return relationships list plus optional cardinality checks."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        rels = executor.execute_info_query('RELATIONSHIPS')
        result: Dict[str, Any] = {'success': bool(rels.get('success')), 'relationships': rels.get('rows', []), 'count': len(rels.get('rows', []) if rels.get('success') else [])}
        # Optionally attach issue analysis when available
        perf_opt = getattr(connection_state, 'performance_optimizer', None)
        try:
            if perf_opt:
                analysis = perf_opt.analyze_relationship_cardinality()
                result['analysis'] = analysis
        except Exception:
            # Non-fatal; just omit analysis
            pass
        return result

    def get_measure_impact(self, connection_state, table: str, measure: str, depth: Optional[int] = 3) -> Dict[str, Any]:
        """Get measure dependency impact analysis."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        dep = connection_state.dependency_analyzer
        if not dep:
            return ErrorHandler.handle_manager_unavailable('dependency_analyzer')
        return dep.analyze_measure_dependencies(table, measure, depth or 3)

    def propose_analysis_options(self, connection_state, goal: Optional[str] = None) -> Dict[str, Any]:
        """Return a simple decision card offering Fast vs Normal analysis."""
        # Determine if connected for realistic expectation
        connected = connection_state.is_connected()
        notes = []
        if not connected:
            notes.append("Not connected yet; choose an option to auto-connect and run.")
        options: List[Dict[str, Any]] = [
            {
                'name': 'Fast summary',
                'id': 'fast',
                'description': 'Very quick summary of model (tables, columns, measures, relationships) with relationship list.',
                'estimated_time': 'few seconds',
                'call': {
                    'tool': 'full_analysis',
                    'arguments': {
                        'profile': 'fast',
                        'depth': 'light',
                        'include_bpa': False,
                        'limits': {'relationships_max': 200, 'issues_max': 200}
                    }
                }
            },
            {
                'name': 'Normal analysis',
                'id': 'normal',
                'description': 'Comprehensive analysis including best practices and M scan; optionally BPA if available.',
                'estimated_time': 'tens of seconds',
                'call': {
                    'tool': 'full_analysis',
                    'arguments': {
                        'profile': 'balanced',
                        'depth': 'standard',
                        'include_bpa': True,
                        'limits': {'relationships_max': 200, 'issues_max': 200}
                    }
                }
            }
        ]
        return {
            'success': True,
            'decision': 'propose_analysis',
            'goal': goal,
            'connected': connected,
            'options': options,
            'notes': notes
        }

    def analyze_best_practices_unified(
        self,
        connection_state,
        mode: str = "all",
        bpa_profile: str = "balanced",
        max_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Unified best practices analysis combining BPA and M query practices."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        mode = (mode or "all").lower()
        results: Dict[str, Any] = {
            'success': True,
            'mode': mode,
            'analyses': {}
        }

        # Run BPA if requested
        if mode in ("all", "bpa"):
            bpa_analyzer = connection_state.bpa_analyzer
            if bpa_analyzer:
                try:
                    # Get TMSL definition first
                    query_executor = connection_state.query_executor
                    if not query_executor:
                        results['analyses']['bpa'] = {
                            'success': False,
                            'error': 'Query executor not available'
                        }
                    else:
                        tmsl_result = query_executor.get_tmsl_definition()
                        if not tmsl_result.get('success'):
                            results['analyses']['bpa'] = {
                                'success': False,
                                'error': f"Failed to get TMSL: {tmsl_result.get('error')}"
                            }
                        else:
                            # Run BPA analysis based on profile
                            tmsl_json = tmsl_result.get('tmsl')
                            if bpa_profile == "fast":
                                cfg = {
                                    'max_seconds': max_seconds or 10,
                                    'per_rule_max_ms': 100,
                                    'severity_at_least': 'WARNING'
                                }
                                violations = bpa_analyzer.analyze_model_fast(tmsl_json, cfg)
                            elif bpa_profile == "deep":
                                violations = bpa_analyzer.analyze_model(tmsl_json)
                            else:  # balanced
                                cfg = {
                                    'max_seconds': max_seconds or 20,
                                    'per_rule_max_ms': 150
                                }
                                violations = bpa_analyzer.analyze_model_fast(tmsl_json, cfg)

                            results['analyses']['bpa'] = {
                                'success': True,
                                'violations': [vars(v) for v in violations],
                                'violation_count': len(violations),
                                'summary': bpa_analyzer.get_violations_summary(),
                                'notes': bpa_analyzer.get_run_notes()
                            }
                except Exception as e:
                    results['analyses']['bpa'] = {
                        'success': False,
                        'error': f'BPA analysis failed: {str(e)}'
                    }
            else:
                results['analyses']['bpa'] = {
                    'success': True,
                    'skipped': True,
                    'reason': 'BPA analyzer not available - dependencies not installed',
                    'note': 'To enable BPA analysis, install Best Practice Analyzer dependencies',
                    'violations': [],
                    'violation_count': 0
                }

        # Run M query practices scan if requested
        if mode in ("all", "m_queries"):
            try:
                from core.analysis.m_practices import scan_m_practices
                m_result = scan_m_practices(connection_state.query_executor)
                results['analyses']['m_practices'] = m_result
            except Exception as e:
                results['analyses']['m_practices'] = {
                    'success': False,
                    'error': f'M practices scan failed: {str(e)}'
                }

        # Aggregate summary
        total_issues = 0
        for analysis_name, analysis_result in results['analyses'].items():
            if isinstance(analysis_result, dict):
                issues_count = analysis_result.get('total_issues', 0) or len(analysis_result.get('issues', []))
                total_issues += issues_count

        results['total_issues'] = total_issues
        results['summary'] = f'Found {total_issues} total issues across {len(results["analyses"])} analyses'

        return results

    def analyze_performance_unified(
        self,
        connection_state,
        mode: str = "comprehensive",
        queries: Optional[List[str]] = None,
        table: Optional[str] = None,
        runs: int = 3,
        clear_cache: bool = True,
        include_event_counts: bool = False
    ) -> Dict[str, Any]:
        """Unified performance analysis combining query performance, cardinality, and storage."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        mode = (mode or "comprehensive").lower()
        performance_optimizer = connection_state.performance_optimizer

        results: Dict[str, Any] = {
            'success': True,
            'mode': mode,
            'analyses': {}
        }

        # Run query batch performance if requested and queries provided
        if mode in ("comprehensive", "queries") and queries:
            perf_result = self.analyze_queries_batch(
                connection_state,
                queries,
                runs=runs,
                clear_cache=clear_cache,
                include_event_counts=include_event_counts
            )
            results['analyses']['query_performance'] = perf_result

        # Run cardinality analysis if requested
        if mode in ("comprehensive", "cardinality"):
            if performance_optimizer:
                try:
                    # Relationship cardinality
                    rel_card = performance_optimizer.analyze_relationship_cardinality()
                    results['analyses']['relationship_cardinality'] = rel_card

                    # Column cardinality if table specified
                    if table:
                        col_card = performance_optimizer.analyze_column_cardinality(table)
                        results['analyses']['column_cardinality'] = col_card
                except Exception as e:
                    results['analyses']['cardinality_error'] = {
                        'success': False,
                        'error': f'Cardinality analysis failed: {str(e)}'
                    }
            else:
                results['analyses']['cardinality'] = {
                    'success': False,
                    'error': 'Performance optimizer not available'
                }

        # Run storage compression analysis if requested
        if mode in ("comprehensive", "storage") and table:
            if performance_optimizer:
                try:
                    storage_result = performance_optimizer.analyze_encoding_efficiency(table)
                    results['analyses']['storage_compression'] = storage_result
                except Exception as e:
                    results['analyses']['storage_error'] = {
                        'success': False,
                        'error': f'Storage analysis failed: {str(e)}'
                    }
            else:
                results['analyses']['storage'] = {
                    'success': False,
                    'error': 'Performance optimizer not available'
                }

        # Generate summary
        analysis_count = len([a for a in results['analyses'].values() if isinstance(a, dict) and a.get('success')])
        results['summary'] = f'Completed {analysis_count} performance analyses'

        return results

    def _get_default_perf_runs(self, runs: Optional[int]) -> int:
        """Get default performance analysis run count."""
        if isinstance(runs, int) and runs > 0:
            return runs
        return self.config.get("performance.default_runs", 3) or 3

    def full_analysis(self, connection_state, summary_only: bool = False) -> Dict[str, Any]:
        """
        Comprehensive model analysis.
        Alias that delegates to the appropriate analysis methods.
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        results: Dict[str, Any] = {
            'success': True,
            'summary_only': summary_only,
            'analyses': {}
        }

        # Get basic best practices validation
        try:
            bp_result = self.validate_best_practices(connection_state)
            results['analyses']['best_practices'] = bp_result
        except Exception as e:
            results['analyses']['best_practices'] = {
                'success': False,
                'error': f'Best practices analysis failed: {str(e)}'
            }

        # Get relationship overview
        try:
            rel_result = self.relationship_overview(connection_state)
            results['analyses']['relationships'] = rel_result
        except Exception as e:
            results['analyses']['relationships'] = {
                'success': False,
                'error': f'Relationship analysis failed: {str(e)}'
            }

        # If not summary_only, run more detailed analysis
        if not summary_only:
            try:
                bpa_result = self.analyze_best_practices_unified(connection_state, mode="all")
                results['analyses']['bpa_unified'] = bpa_result
            except Exception as e:
                results['analyses']['bpa_unified'] = {
                    'success': False,
                    'error': f'Unified BPA analysis failed: {str(e)}'
                }

        return results

    def analyze_best_practices(self, connection_state, summary_only: bool = False) -> Dict[str, Any]:
        """
        Alias for analyze_best_practices_unified for backward compatibility.
        """
        mode = "all" if not summary_only else "bpa"
        return self.analyze_best_practices_unified(connection_state, mode=mode)

    def analyze_performance(self, connection_state, summary_only: bool = False) -> Dict[str, Any]:
        """
        Alias for analyze_performance_unified for backward compatibility.
        """
        mode = "comprehensive" if not summary_only else "cardinality"
        return self.analyze_performance_unified(connection_state, mode=mode)
