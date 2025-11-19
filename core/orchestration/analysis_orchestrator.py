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
        connection_state
    ) -> Dict[str, Any]:
        """Performance analysis focused on relationship and column cardinality."""
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        performance_optimizer = connection_state.performance_optimizer

        results: Dict[str, Any] = {
            'success': True,
            'analyses': {}
        }

        # Always run cardinality analysis
        if performance_optimizer:
            try:
                # Relationship cardinality analysis
                rel_card = performance_optimizer.analyze_relationship_cardinality()
                results['analyses']['relationship_cardinality'] = rel_card
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

    def comprehensive_analysis(
        self,
        connection_state,
        scope: str = "all",
        depth: str = "balanced",
        include_bpa: bool = True,
        include_performance: bool = True,
        include_integrity: bool = True,
        max_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Unified comprehensive model analysis combining best practices, performance, and integrity checks.

        Args:
            connection_state: Current connection state
            scope: Analysis scope - "all", "best_practices", "performance", "integrity"
            depth: Analysis depth - "fast", "balanced", "deep"
            include_bpa: Whether to run BPA analysis (requires dependencies)
            include_performance: Whether to run performance analysis
            include_integrity: Whether to run integrity validation
            max_seconds: Maximum execution time (optional)

        Returns:
            Comprehensive analysis results with all requested analyses
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        scope = (scope or "all").lower()
        depth = (depth or "balanced").lower()

        results: Dict[str, Any] = {
            'success': True,
            'scope': scope,
            'depth': depth,
            'analyses': {},
            'start_time': time.time()
        }

        # Determine what to run based on scope
        run_bp = scope in ("all", "best_practices")
        run_perf = scope in ("all", "performance") and include_performance
        run_integrity = scope in ("all", "integrity") and include_integrity

        # 1. Model Integrity Validation
        if run_integrity:
            try:
                validator = connection_state.model_validator
                if validator:
                    integrity_result = validator.validate_model_integrity()
                    results['analyses']['integrity'] = integrity_result
                else:
                    results['analyses']['integrity'] = {
                        'success': False,
                        'error': 'Model validator not available'
                    }
            except Exception as e:
                logger.error(f"Integrity validation failed: {e}")
                results['analyses']['integrity'] = {
                    'success': False,
                    'error': f'Integrity validation failed: {str(e)}'
                }

        # 2. Best Practice Analyzer (BPA)
        if run_bp and include_bpa:
            try:
                bpa_analyzer = connection_state.bpa_analyzer
                query_executor = connection_state.query_executor

                if bpa_analyzer and query_executor:
                    # Get TMSL definition
                    tmsl_result = query_executor.get_tmsl_definition()

                    if tmsl_result.get('success'):
                        tmsl_json = tmsl_result.get('tmsl')

                        # Configure BPA based on depth
                        if depth == "fast":
                            cfg = {
                                'max_seconds': max_seconds or 10,
                                'per_rule_max_ms': 100,
                                'severity_at_least': 'WARNING'
                            }
                            violations = bpa_analyzer.analyze_model_fast(tmsl_json, cfg)
                        elif depth == "deep":
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
                    else:
                        results['analyses']['bpa'] = {
                            'success': False,
                            'error': f"Failed to get TMSL: {tmsl_result.get('error')}"
                        }
                else:
                    results['analyses']['bpa'] = {
                        'success': True,
                        'skipped': True,
                        'reason': 'BPA analyzer not available - dependencies not installed',
                        'violations': [],
                        'violation_count': 0
                    }
            except Exception as e:
                logger.error(f"BPA analysis failed: {e}")
                results['analyses']['bpa'] = {
                    'success': False,
                    'error': f'BPA analysis failed: {str(e)}'
                }

        # 3. M Query Practices
        if run_bp:
            try:
                from core.analysis.m_practices import scan_m_practices
                query_executor = connection_state.query_executor

                if query_executor:
                    m_result = scan_m_practices(query_executor)
                    results['analyses']['m_practices'] = m_result
                else:
                    results['analyses']['m_practices'] = {
                        'success': False,
                        'error': 'Query executor not available'
                    }
            except Exception as e:
                logger.error(f"M practices scan failed: {e}")
                results['analyses']['m_practices'] = {
                    'success': False,
                    'error': f'M practices scan failed: {str(e)}'
                }

        # 4. Performance Analysis (Cardinality)
        if run_perf:
            try:
                performance_optimizer = connection_state.performance_optimizer

                if performance_optimizer:
                    rel_card = performance_optimizer.analyze_relationship_cardinality()
                    results['analyses']['performance'] = rel_card
                else:
                    results['analyses']['performance'] = {
                        'success': False,
                        'error': 'Performance optimizer not available'
                    }
            except Exception as e:
                logger.error(f"Performance analysis failed: {e}")
                results['analyses']['performance'] = {
                    'success': False,
                    'error': f'Performance analysis failed: {str(e)}'
                }

        # 5. Relationship Overview (always included for context)
        try:
            query_executor = connection_state.query_executor
            if query_executor:
                rels = query_executor.execute_info_query('RELATIONSHIPS')
                results['analyses']['relationships'] = {
                    'success': bool(rels.get('success')),
                    'count': len(rels.get('rows', [])),
                    'relationships': rels.get('rows', [])
                }
        except Exception as e:
            logger.error(f"Relationship overview failed: {e}")
            results['analyses']['relationships'] = {
                'success': False,
                'error': f'Relationship overview failed: {str(e)}'
            }

        # Calculate execution time
        results['execution_time_seconds'] = round(time.time() - results['start_time'], 2)
        del results['start_time']

        # Aggregate summary
        total_issues = 0
        successful_analyses = 0

        for analysis_name, analysis_result in results['analyses'].items():
            if isinstance(analysis_result, dict):
                if analysis_result.get('success'):
                    successful_analyses += 1

                # Count issues from different analysis types
                if analysis_name == 'integrity':
                    total_issues += analysis_result.get('total_issues', 0)
                elif analysis_name == 'bpa':
                    total_issues += analysis_result.get('violation_count', 0)
                elif analysis_name == 'm_practices':
                    total_issues += analysis_result.get('total_issues', 0)
                elif analysis_name == 'performance':
                    # Count high/critical performance issues
                    issues = analysis_result.get('issues', [])
                    if isinstance(issues, list):
                        total_issues += len([i for i in issues if isinstance(i, dict) and i.get('severity') in ('high', 'critical')])

        results['summary'] = {
            'total_issues': total_issues,
            'successful_analyses': successful_analyses,
            'total_analyses': len(results['analyses']),
            'recommendation': self._get_recommendation(total_issues, results['analyses'])
        }

        return results

    def _get_recommendation(self, total_issues: int, analyses: Dict[str, Any]) -> str:
        """Generate recommendation based on analysis results."""
        if total_issues == 0:
            return "Model is in good shape. No critical issues found."

        # Check for critical issues
        critical_count = 0
        high_count = 0

        if 'integrity' in analyses and isinstance(analyses['integrity'], dict):
            summary = analyses['integrity'].get('summary', {})
            if isinstance(summary, dict):
                critical_count += summary.get('critical_issues', 0)
                high_count += summary.get('high_issues', 0)

        if 'bpa' in analyses and isinstance(analyses['bpa'], dict):
            violations = analyses['bpa'].get('violations', [])
            for v in violations:
                if isinstance(v, dict):
                    severity = v.get('Severity', '').upper()
                    if 'ERROR' in severity or 'CRITICAL' in severity:
                        critical_count += 1
                    elif 'WARNING' in severity or 'HIGH' in severity:
                        high_count += 1

        if critical_count > 0:
            return f"CRITICAL: Found {critical_count} critical issues. Address immediately before deployment."
        elif high_count > 0:
            return f"WARNING: Found {high_count} high-priority issues. Review and fix before production use."
        else:
            return f"Found {total_issues} issues (low/medium severity). Consider addressing for optimization."

    def analyze_best_practices(self, connection_state, summary_only: bool = False) -> Dict[str, Any]:
        """
        Alias for comprehensive_analysis focused on best practices.
        """
        return self.comprehensive_analysis(
            connection_state,
            scope="best_practices",
            depth="balanced" if not summary_only else "fast",
            include_bpa=True,
            include_performance=False,
            include_integrity=True
        )

    def analyze_performance(self, connection_state) -> Dict[str, Any]:
        """
        Alias for comprehensive_analysis focused on performance.
        """
        return self.comprehensive_analysis(
            connection_state,
            scope="performance",
            depth="balanced",
            include_bpa=False,
            include_performance=True,
            include_integrity=False
        )

    def full_analysis_legacy(self, connection_state, summary_only: bool = False) -> Dict[str, Any]:
        """
        Legacy full_analysis - now delegates to comprehensive_analysis.
        """
        return self.comprehensive_analysis(
            connection_state,
            scope="all",
            depth="balanced" if not summary_only else "fast",
            include_bpa=True,
            include_performance=True,
            include_integrity=True
        )

    def validate_model_integrity(self, connection_state) -> Dict[str, Any]:
        """
        Validate model integrity - now delegates to comprehensive_analysis.

        Returns only the integrity analysis results for backward compatibility.
        """
        result = self.comprehensive_analysis(
            connection_state,
            scope="integrity",
            depth="balanced",
            include_bpa=False,
            include_performance=False,
            include_integrity=True
        )

        # Extract just the integrity analysis for backward compatibility
        if result.get('success') and 'integrity' in result.get('analyses', {}):
            integrity_result = result['analyses']['integrity']
            # Add execution metadata
            integrity_result['execution_time_seconds'] = result.get('execution_time_seconds')
            return integrity_result

        return result

    def _infer_table_type(self, table_name: str) -> str:
        """
        Infer table type from naming convention.

        Common prefixes in Power BI models:
        - d_: dimension tables
        - f_: fact tables
        - m_: measure tables
        - s_: support/slicer tables
        - c_: calculation groups
        - r_: RLS (Row-Level Security) tables
        - sfp_/dfp_: field parameters
        - dyn_: dynamic tables

        Args:
            table_name: Name of the table

        Returns:
            Table type category as string
        """
        name_lower = table_name.lower()

        if name_lower.startswith('d_'):
            return 'dimension'
        elif name_lower.startswith('f_'):
            return 'fact'
        elif name_lower.startswith('m_'):
            return 'measure'
        elif name_lower.startswith('s_'):
            return 'support'
        elif name_lower.startswith('c_'):
            return 'calculation_group'
        elif name_lower.startswith('r_'):
            return 'rls'
        elif name_lower.startswith('sfp_') or name_lower.startswith('dfp_'):
            return 'field_parameter'
        elif name_lower.startswith('dyn_'):
            return 'dynamic'
        else:
            return 'other'

    def list_tables_simple(self, connection_state) -> Dict[str, Any]:
        """
        Ultra-fast table list (< 500ms).

        Similar to Microsoft MCP Server's List operation.
        Returns table names with basic counts only.

        Args:
            connection_state: Current connection state

        Returns:
            {
                'success': True,
                'analysis_type': 'table_list',
                'execution_time_seconds': 0.25,
                'message': 'Found 109 tables',
                'table_count': 109,
                'tables': [
                    {
                        'name': 'd_Company',
                        'column_count': 5,
                        'partition_count': 1
                    },
                    {
                        'name': 'm_Measures',
                        'column_count': 1,
                        'measure_count': 224,
                        'partition_count': 1
                    }
                ]
            }
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        start_time = time.time()
        executor = connection_state.query_executor

        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        try:
            # Get tables (already cached in most cases)
            tables_result = executor.execute_info_query('TABLES')

            if not tables_result.get('success'):
                return tables_result

            # Build simple table list
            tables = []
            for table in tables_result.get('rows', []):
                table_info = {
                    'name': table.get('Name', ''),
                    'column_count': table.get('ColumnCount', 0),
                    'partition_count': table.get('PartitionCount', 1)
                }

                # Include measure count if > 0 (matching Microsoft MCP behavior)
                measure_count = table.get('MeasureCount', 0)
                if measure_count > 0:
                    table_info['measure_count'] = measure_count

                tables.append(table_info)

            execution_time = round(time.time() - start_time, 2)

            return {
                'success': True,
                'analysis_type': 'table_list',
                'execution_time_seconds': execution_time,
                'message': f'Found {len(tables)} tables',
                'table_count': len(tables),
                'tables': tables
            }

        except Exception as e:
            logger.error(f"Table list failed: {e}")
            return {
                'success': False,
                'error': f'Table list failed: {str(e)}'
            }

    def simple_model_analysis(self, connection_state) -> Dict[str, Any]:
        """
        Fast model statistics overview (< 1 second).

        Similar to Microsoft MCP Server's GetStats operation.
        Provides comprehensive model metadata and counts without heavy analysis.

        Args:
            connection_state: Current connection state

        Returns:
            {
                'success': True,
                'analysis_type': 'simple_stats',
                'execution_time_seconds': 0.45,
                'model': {
                    'name': 'Model',
                    'database': 'guid',
                    'compatibility_level': 1601,
                    'compatibility_version': 'Power BI 2025'
                },
                'counts': {
                    'tables': 109,
                    'columns': 833,
                    'measures': 239,
                    'relationships': 91,
                    'partitions': 109,
                    'roles': 1,
                    'data_sources': 0,
                    'cultures': 1,
                    'perspectives': 0,
                    'calculation_groups': 5
                },
                'tables': [...],
                'summary': {...}
            }
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        start_time = time.time()
        executor = connection_state.query_executor

        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        try:
            # Step 1: Get all object counts (matching Microsoft MCP GetStats)
            model_info = executor.execute_info_query('MODEL')
            tables = executor.execute_info_query('TABLES')
            measures = executor.execute_info_query('MEASURES')
            columns = executor.execute_info_query('COLUMNS')
            relationships = executor.execute_info_query('RELATIONSHIPS')
            partitions = executor.execute_info_query('PARTITIONS')
            roles = executor.execute_info_query('ROLES')
            calc_groups = executor.execute_info_query('CALCULATION_GROUPS')

            # Try to get optional counts (may not be available in all model versions)
            data_sources = executor.execute_info_query('DATA_SOURCES')
            cultures = executor.execute_info_query('CULTURES')
            perspectives = executor.execute_info_query('PERSPECTIVES')

            # Step 2: Extract model metadata
            model_data = model_info.get('rows', [{}])[0] if model_info.get('success') else {}
            model = {
                'name': model_data.get('Name', 'Model'),
                'database': model_data.get('Database', ''),
                'compatibility_level': model_data.get('CompatibilityLevel', 0)
            }

            # Add compatibility version description
            compat_level = model['compatibility_level']
            if compat_level >= 1601:
                model['compatibility_version'] = 'Power BI 2025'
            elif compat_level >= 1600:
                model['compatibility_version'] = 'Power BI 2021+'
            elif compat_level >= 1500:
                model['compatibility_version'] = 'SQL Server 2019 / Power BI'
            elif compat_level >= 1400:
                model['compatibility_version'] = 'SQL Server 2017 / Power BI'
            elif compat_level >= 1200:
                model['compatibility_version'] = 'SQL Server 2016 / Power BI'
            else:
                model['compatibility_version'] = 'Unknown'

            # Step 3: Aggregate counts (matching Microsoft MCP GetStats exactly)
            counts = {
                'tables': len(tables.get('rows', [])),
                'columns': len(columns.get('rows', [])),
                'measures': len(measures.get('rows', [])),
                'relationships': len(relationships.get('rows', [])),
                'partitions': len(partitions.get('rows', [])),
                'roles': len(roles.get('rows', [])),
                'data_sources': len(data_sources.get('rows', [])) if data_sources.get('success') else 0,
                'cultures': len(cultures.get('rows', [])) if cultures.get('success') else 1,
                'perspectives': len(perspectives.get('rows', [])) if perspectives.get('success') else 0,
                'calculation_groups': len(calc_groups.get('rows', []))
            }

            # Step 4: Per-table analysis
            tables_detailed = []
            for table in tables.get('rows', []):
                table_name = table.get('Name', '')

                # Infer table type from prefix (our enhancement for categorization)
                table_type = self._infer_table_type(table_name)

                # Build table info matching Microsoft MCP GetStats format
                table_info = {
                    'name': table_name,
                    'type': table_type,  # Our enhancement
                    'column_count': table.get('ColumnCount', 0),
                    'partition_count': table.get('PartitionCount', 1),
                    'is_hidden': table.get('IsHidden', False)
                }

                # Include measure_count only if > 0 (matching Microsoft MCP behavior)
                measure_count = table.get('MeasureCount', 0)
                if measure_count > 0:
                    table_info['measure_count'] = measure_count

                tables_detailed.append(table_info)

            # Step 5: Generate summary
            # Identify measure tables (tables with high measure:column ratio)
            measure_tables = [t['name'] for t in tables_detailed
                             if t.get('measure_count', 0) > 0 and t['column_count'] < 5]

            # Find largest tables by column count
            largest_tables = sorted(tables_detailed,
                                   key=lambda t: t['column_count'],
                                   reverse=True)[:5]
            largest_tables = [{'name': t['name'], 'column_count': t['column_count']}
                             for t in largest_tables]

            # Count table types
            table_types = {}
            for t in tables_detailed:
                table_type = t['type']
                table_types[table_type] = table_types.get(table_type, 0) + 1

            summary = {
                'total_objects': (counts['tables'] + counts['columns'] +
                                 counts['measures'] + counts['relationships']),
                'measure_tables': measure_tables,
                'largest_tables': largest_tables,
                'table_types': table_types
            }

            execution_time = round(time.time() - start_time, 2)

            return {
                'success': True,
                'analysis_type': 'simple_stats',
                'execution_time_seconds': execution_time,
                'model': model,
                'counts': counts,
                'tables': tables_detailed,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Simple model analysis failed: {e}")
            return {
                'success': False,
                'error': f'Simple model analysis failed: {str(e)}'
            }

    def list_measures_simple(self, connection_state, table_name: str = None, max_results: int = None) -> Dict[str, Any]:
        """
        List measures with optional table filter.
        Microsoft MCP Measure List operation.

        Args:
            connection_state: Current connection state
            table_name: Optional table filter
            max_results: Optional limit on results

        Returns:
            {
                'success': True,
                'message': 'Found 30 measures in table "m_Measures"',
                'operation': 'List',
                'tableName': 'm_Measures',
                'data': [
                    {
                        'displayFolder': 'Financial Model\\1.3 Base measures Balance Sheet',
                        'name': 'PL-COL-Background'
                    }
                ],
                'warnings': ['Results truncated: Showing 30 of 224 measures']
            }
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        try:
            # Get measures
            result = executor.execute_info_query('MEASURES', table_name=table_name, exclude_columns=['Expression'])

            if not result.get('success'):
                return result

            rows = result.get('rows', [])
            total_count = len(rows)

            # Build measure list (name and displayFolder only for List operation)
            measures = []
            for row in rows:
                measure_info = {
                    'name': row.get('Name', ''),
                    'displayFolder': row.get('DisplayFolder', '')
                }
                measures.append(measure_info)

            # Apply max_results if specified
            truncated = False
            if max_results and len(measures) > max_results:
                measures = measures[:max_results]
                truncated = True

            # Build response matching Microsoft MCP format
            response = {
                'success': True,
                'operation': 'List'
            }

            # Message format
            if table_name:
                response['message'] = f'Found {len(measures)} measures in table \'{table_name}\''
                response['tableName'] = table_name
            else:
                response['message'] = f'Found {len(measures)} measures'

            response['data'] = measures

            # Add warning if truncated
            if truncated:
                response['warnings'] = [
                    f'Results truncated: Showing {len(measures)} of {total_count} measures (limited by MaxResults={max_results})'
                ]

            return response

        except Exception as e:
            logger.error(f"List measures failed: {e}")
            return {
                'success': False,
                'error': f'List measures failed: {str(e)}'
            }

    def get_measure_simple(self, connection_state, table_name: str, measure_name: str) -> Dict[str, Any]:
        """
        Get detailed measure information including DAX expression.
        Microsoft MCP Measure Get operation.

        Args:
            connection_state: Current connection state
            table_name: Table containing the measure
            measure_name: Measure name to retrieve

        Returns:
            {
                'success': True,
                'message': 'Measure "PL-AMT-BASE Scenario" retrieved successfully',
                'operation': 'Get',
                'measureName': 'PL-AMT-BASE Scenario',
                'tableName': 'm_Measures',
                'data': {
                    'tableName': 'm_Measures',
                    'name': 'PL-AMT-BASE Scenario',
                    'expression': '...',
                    'description': '',
                    'formatString': '',
                    'isHidden': False,
                    'displayFolder': '...',
                    ...
                }
            }
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'table_name and measure_name are required'
            }

        try:
            # Use the existing get_measure_details_with_fallback
            result = executor.get_measure_details_with_fallback(table_name, measure_name)

            if not result.get('success'):
                return result

            measure_data = result.get('measure', {})

            # Build response matching Microsoft MCP format
            return {
                'success': True,
                'message': f'Measure \'{measure_name}\' retrieved successfully',
                'operation': 'Get',
                'measureName': measure_name,
                'tableName': table_name,
                'data': measure_data
            }

        except Exception as e:
            logger.error(f"Get measure failed: {e}")
            return {
                'success': False,
                'error': f'Get measure failed: {str(e)}'
            }

    def list_relationships_simple(self, connection_state, active_only: bool = False) -> Dict[str, Any]:
        """
        List all relationships with full metadata.
        Microsoft MCP Relationship List operation.

        Args:
            connection_state: Current connection state
            active_only: If True, only return active relationships

        Returns:
            {
                'success': True,
                'message': 'Found 91 relationships',
                'operation': 'LIST',
                'data': [
                    {
                        'fromTable': 'f_FINREP',
                        'fromColumn': '#Company Code',
                        'toTable': 'd_Company',
                        'toColumn': 'Company Code',
                        'isActive': True,
                        'crossFilteringBehavior': 'OneDirection',
                        'fromCardinality': 'Many',
                        'toCardinality': 'One',
                        'name': '70c38ab1-00b9-bb04-7903-4027e569f76e'
                    }
                ]
            }
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        try:
            # Get relationships
            result = executor.execute_info_query('RELATIONSHIPS')

            if not result.get('success'):
                return result

            rows = result.get('rows', [])

            # Filter for active only if requested
            if active_only:
                rows = [r for r in rows if r.get('IsActive')]

            # Build relationship list matching Microsoft MCP format
            relationships = []
            for row in rows:
                rel_info = {
                    'fromTable': row.get('FromTable', row.get('FromTableName', '')),
                    'fromColumn': row.get('FromColumn', row.get('FromColumnName', '')),
                    'toTable': row.get('ToTable', row.get('ToTableName', '')),
                    'toColumn': row.get('ToColumn', row.get('ToColumnName', '')),
                    'isActive': row.get('IsActive', False),
                    'crossFilteringBehavior': row.get('CrossFilteringBehavior', 'OneDirection'),
                    'fromCardinality': row.get('FromCardinality', 'Many'),
                    'toCardinality': row.get('ToCardinality', 'One'),
                    'name': row.get('Name', '')
                }
                relationships.append(rel_info)

            # Build response matching Microsoft MCP format
            return {
                'success': True,
                'message': f'Found {len(relationships)} relationships',
                'operation': 'LIST',
                'data': relationships
            }

        except Exception as e:
            logger.error(f"List relationships failed: {e}")
            return {
                'success': False,
                'error': f'List relationships failed: {str(e)}'
            }

    def list_calculation_groups_simple(self, connection_state) -> Dict[str, Any]:
        """
        List all calculation groups with their items.
        Microsoft MCP Calculation Group ListGroups operation.

        Args:
            connection_state: Current connection state

        Returns:
            {
                'success': True,
                'message': 'Found 5 calculation groups',
                'operation': 'ListGroups',
                'data': [
                    {
                        'calculationItems': [
                            {'ordinal': 0, 'name': 'MTD'},
                            {'ordinal': 1, 'name': 'QTD'}
                        ],
                        'name': 'c_Time Intelligence P&L'
                    }
                ]
            }
        """
        from core.validation.error_handler import ErrorHandler

        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        calc_group_mgr = connection_state.calc_group_manager
        if not calc_group_mgr:
            return ErrorHandler.handle_manager_unavailable('calc_group_manager')

        try:
            # Get calculation groups
            result = calc_group_mgr.list_calculation_groups()

            if not result.get('success'):
                return result

            groups = result.get('groups', [])

            # Transform to Microsoft MCP format
            mcp_groups = []
            for group in groups:
                items = group.get('items', [])

                # Transform items to MCP format
                mcp_items = []
                for item in items:
                    mcp_items.append({
                        'ordinal': item.get('ordinal', 0),
                        'name': item.get('name', '')
                    })

                mcp_groups.append({
                    'name': group.get('name', ''),
                    'calculationItems': mcp_items
                })

            # Build response matching Microsoft MCP format
            return {
                'success': True,
                'message': f'Found {len(mcp_groups)} calculation groups',
                'operation': 'ListGroups',
                'data': mcp_groups
            }

        except Exception as e:
            logger.error(f"List calculation groups failed: {e}")
            return {
                'success': False,
                'error': f'List calculation groups failed: {str(e)}'
            }
