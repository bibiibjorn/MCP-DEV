"""
Debug Operations

Consolidated operations for visual debugging, validation, profiling,
documentation, and advanced analysis.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a visual validation."""
    visual_id: str
    visual_name: str
    page_name: str
    measure_name: str
    value: Any
    execution_time_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class ProfileResult:
    """Result of profiling a visual."""
    visual_id: str
    visual_name: str
    visual_type: str
    page_name: str
    measures: List[str]
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    row_count: int
    filter_count: int
    issues: List[str] = field(default_factory=list)


@dataclass
class LineageInfo:
    """Measure or filter lineage information."""
    name: str
    table: Optional[str]
    visuals: List[Dict[str, Any]] = field(default_factory=list)
    pages: List[str] = field(default_factory=list)
    usage_count: int = 0


class DebugOperations:
    """
    Consolidated debug operations for validation, profiling, documentation, and analysis.

    Designed to minimize tool count by grouping related operations.
    """

    def __init__(self, visual_query_builder, query_executor=None):
        """
        Initialize debug operations.

        Args:
            visual_query_builder: VisualQueryBuilder instance with PBIP loaded
            query_executor: Optional QueryExecutor for live model queries
        """
        self.builder = visual_query_builder
        self.qe = query_executor
        self.logger = logging.getLogger(__name__)

    # ========== VALIDATION OPERATIONS ==========

    def cross_visual_validation(
        self,
        measure_name: str,
        page_names: Optional[List[str]] = None,
        tolerance: float = 0.001
    ) -> Dict[str, Any]:
        """
        Compare the same measure across multiple visuals to find inconsistencies.

        Args:
            measure_name: The measure to validate
            page_names: Pages to check (None = all pages)
            tolerance: Numeric tolerance for comparison

        Returns:
            Validation report with discrepancies
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        results: List[ValidationResult] = []
        pages = page_names or [p['name'] for p in self.builder.list_pages()]

        clean_measure = measure_name.strip('[]')

        for page_name in pages:
            visuals = self.builder.list_visuals(page_name)

            for visual in visuals:
                if visual.get('is_slicer'):
                    continue

                # Check if visual uses this measure
                visual_measures = visual.get('measures', [])
                if clean_measure not in [m.strip('[]') for m in visual_measures]:
                    continue

                # Get filter context and execute
                try:
                    query_result = self.builder.build_visual_query(
                        page_name=page_name,
                        visual_id=visual['id'],
                        measure_name=measure_name
                    )

                    if query_result and query_result.dax_query:
                        exec_result = self.qe.validate_and_execute_dax(
                            query_result.dax_query, top_n=1
                        )

                        value = None
                        if exec_result.get('success') and exec_result.get('rows'):
                            row = exec_result['rows'][0]
                            value = list(row.values())[0] if row else None

                        results.append(ValidationResult(
                            visual_id=visual['id'],
                            visual_name=visual.get('friendly_name', visual['id']),
                            page_name=page_name,
                            measure_name=clean_measure,
                            value=value,
                            execution_time_ms=exec_result.get('execution_time_ms', 0),
                            success=exec_result.get('success', False),
                            error=exec_result.get('error')
                        ))

                except Exception as e:
                    results.append(ValidationResult(
                        visual_id=visual['id'],
                        visual_name=visual.get('friendly_name', visual['id']),
                        page_name=page_name,
                        measure_name=clean_measure,
                        value=None,
                        execution_time_ms=0,
                        success=False,
                        error=str(e)
                    ))

        # Analyze for discrepancies
        discrepancies = self._find_discrepancies(results, tolerance)

        return {
            'success': True,
            'measure': clean_measure,
            'visuals_checked': len(results),
            'results': [
                {
                    'page': r.page_name,
                    'visual': r.visual_name,
                    'value': r.value,
                    'time_ms': r.execution_time_ms,
                    'success': r.success,
                    'error': r.error
                }
                for r in results
            ],
            'discrepancies': discrepancies,
            'has_discrepancies': len(discrepancies) > 0
        }

    def _execute_with_smart_retry(
        self,
        query: str,
        filters: List,
        rebuild_query_func,
        top_n: int = 100
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Execute query with automatic retry on composite key error.

        On composite key error:
        1. Identify field_parameter filters
        2. Rebuild query excluding them
        3. Retry execution
        4. Return result with retry info

        Args:
            query: DAX query to execute
            filters: List of FilterExpression objects
            rebuild_query_func: Function to rebuild query with reduced filters
            top_n: Max rows to return

        Returns:
            Tuple of (execution_result, retry_info or None)
        """
        from .filter_to_dax import FilterClassification

        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}, None

        # First attempt with full query
        exec_result = self.qe.validate_and_execute_dax(query, top_n=top_n)

        if exec_result.get('success'):
            return exec_result, None

        error_msg = exec_result.get('error', '').lower()

        # Check for composite key / ambiguous relationship errors
        retry_patterns = [
            'composite',
            'multiple columns',
            'ambiguous',
            'cannot determine',
            'more than one',
            'duplicate key'
        ]

        should_retry = any(pattern in error_msg for pattern in retry_patterns)

        if not should_retry:
            return exec_result, None

        # Identify field parameter filters to exclude
        field_param_filters = [
            f for f in filters
            if getattr(f, 'classification', '') == FilterClassification.FIELD_PARAMETER
            or getattr(f, 'is_field_parameter', False)
        ]

        if not field_param_filters:
            # No field parameters to exclude, can't help
            return exec_result, None

        # Build excluded filter descriptions for reporting
        excluded_descriptions = [
            f"'{f.table}'[{f.column}]" for f in field_param_filters
        ]

        self.logger.info(
            f"Composite key error detected, retrying without {len(field_param_filters)} "
            f"field parameter filters: {excluded_descriptions}"
        )

        # Filter out field parameter filters
        reduced_filters = [
            f for f in filters
            if f not in field_param_filters
        ]

        # Rebuild query with reduced filters
        try:
            reduced_query = rebuild_query_func(reduced_filters)
        except Exception as e:
            self.logger.warning(f"Failed to rebuild query: {e}")
            return exec_result, None

        # Retry with reduced query
        retry_result = self.qe.validate_and_execute_dax(reduced_query, top_n=top_n)

        retry_info = {
            'retried': True,
            'original_error': exec_result.get('error'),
            'excluded_filters': excluded_descriptions,
            'reason': 'Composite key error resolved by excluding field parameter filters'
        }

        if retry_result.get('success'):
            retry_info['success'] = True
            retry_info['note'] = 'Results may differ from visual due to excluded field parameters'
        else:
            retry_info['success'] = False
            retry_info['retry_error'] = retry_result.get('error')

        return retry_result, retry_info

    def _find_discrepancies(
        self,
        results: List[ValidationResult],
        tolerance: float
    ) -> List[Dict[str, Any]]:
        """Find value discrepancies across validation results."""
        discrepancies = []

        # Group successful results by value
        successful = [r for r in results if r.success and r.value is not None]
        if len(successful) < 2:
            return discrepancies

        # Use first value as baseline
        baseline = successful[0]
        baseline_value = baseline.value

        for result in successful[1:]:
            try:
                if isinstance(baseline_value, (int, float)) and isinstance(result.value, (int, float)):
                    diff = abs(float(result.value) - float(baseline_value))
                    if diff > tolerance:
                        discrepancies.append({
                            'type': 'value_mismatch',
                            'baseline': {
                                'page': baseline.page_name,
                                'visual': baseline.visual_name,
                                'value': baseline_value
                            },
                            'different': {
                                'page': result.page_name,
                                'visual': result.visual_name,
                                'value': result.value
                            },
                            'difference': diff
                        })
                elif str(baseline_value) != str(result.value):
                    discrepancies.append({
                        'type': 'value_mismatch',
                        'baseline': {
                            'page': baseline.page_name,
                            'visual': baseline.visual_name,
                            'value': baseline_value
                        },
                        'different': {
                            'page': result.page_name,
                            'visual': result.visual_name,
                            'value': result.value
                        }
                    })
            except (ValueError, TypeError):
                continue

        return discrepancies

    def expected_value_test(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        expected_value: Any = None,
        filters: Optional[List[str]] = None,
        tolerance: float = 0.001
    ) -> Dict[str, Any]:
        """
        Test that a visual returns an expected value with given filters.

        Args:
            page_name: Page containing the visual
            visual_id: Visual ID
            visual_name: Visual name (alternative to ID)
            expected_value: The expected value
            filters: Optional additional DAX filters
            tolerance: Numeric tolerance

        Returns:
            Test result with pass/fail
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        query_result = self.builder.build_visual_query(
            page_name=page_name,
            visual_id=visual_id,
            visual_name=visual_name
        )

        if not query_result:
            return {'success': False, 'error': 'Visual not found'}

        # Execute with optional additional filters
        query = query_result.dax_query
        if filters:
            # Rebuild query with additional filters
            from .filter_to_dax import FilterExpression
            all_filters = query_result.filter_context.all_filters()
            for f in filters:
                all_filters.append(FilterExpression(
                    dax=f, source='manual', table='', column='',
                    condition_type='Manual', values=[]
                ))
            measures = query_result.visual_info.measures or [query_result.measure_name]
            measures = [m if m.startswith('[') else f'[{m}]' for m in measures]
            query = self.builder._build_visual_dax_query(
                measures, query_result.visual_info.columns or [], all_filters
            )

        exec_result = self.qe.validate_and_execute_dax(query, top_n=10)

        if not exec_result.get('success'):
            return {
                'success': False,
                'error': exec_result.get('error'),
                'test_passed': False
            }

        # Extract actual value
        actual_value = None
        if exec_result.get('rows'):
            row = exec_result['rows'][0]
            actual_value = list(row.values())[0] if row else None

        # Compare values
        test_passed = False
        difference = None

        if expected_value is not None and actual_value is not None:
            try:
                exp_num = float(expected_value)
                act_num = float(actual_value)
                difference = act_num - exp_num
                test_passed = abs(difference) <= tolerance
            except (ValueError, TypeError):
                test_passed = str(expected_value) == str(actual_value)
                difference = 'N/A (non-numeric)'
        elif expected_value is None and actual_value is None:
            test_passed = True

        return {
            'success': True,
            'test_passed': test_passed,
            'visual': {
                'id': query_result.visual_info.visual_id,
                'name': query_result.visual_info.visual_name,
                'page': page_name
            },
            'expected_value': expected_value,
            'actual_value': actual_value,
            'difference': difference,
            'tolerance': tolerance,
            'execution_time_ms': exec_result.get('execution_time_ms'),
            'query': query,
            'filters_applied': len(query_result.filter_context.all_filters()) + (len(filters) if filters else 0)
        }

    def filter_permutation_test(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        max_permutations: int = 20
    ) -> Dict[str, Any]:
        """
        Test visual with different slicer value combinations.

        Args:
            page_name: Page to test
            visual_id: Visual ID
            visual_name: Visual name
            max_permutations: Maximum number of combinations to test

        Returns:
            Test results for each permutation
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        # Get slicers on the page
        slicers = self.builder.list_slicers(page_name)
        if not slicers:
            return {
                'success': True,
                'message': 'No slicers found on page',
                'results': []
            }

        # Get unique values for each slicer (limited)
        slicer_values = {}
        for slicer in slicers[:3]:  # Limit to 3 slicers to avoid explosion
            table = slicer.table
            column = slicer.column

            # Query distinct values
            try:
                query = f"EVALUATE TOPN(5, DISTINCT('{table}'[{column}]))"
                result = self.qe.validate_and_execute_dax(query, top_n=5)
                if result.get('success') and result.get('rows'):
                    values = [list(r.values())[0] for r in result['rows'] if list(r.values())[0] is not None]
                    slicer_values[f"'{table}'[{column}]"] = values[:5]
            except Exception:
                continue

        if not slicer_values:
            return {
                'success': True,
                'message': 'Could not get slicer values',
                'results': []
            }

        # Generate permutations
        permutations = self._generate_filter_permutations(slicer_values, max_permutations)

        # Test each permutation
        results = []
        query_result = self.builder.build_visual_query(
            page_name=page_name,
            visual_id=visual_id,
            visual_name=visual_name
        )

        if not query_result:
            return {'success': False, 'error': 'Visual not found'}

        measures = query_result.visual_info.measures or [query_result.measure_name]
        measures = [m if m.startswith('[') else f'[{m}]' for m in measures]
        columns = query_result.visual_info.columns or []

        for i, perm in enumerate(permutations[:max_permutations]):
            try:
                # Build filters for this permutation
                filter_parts = []
                for col_ref, value in perm.items():
                    if isinstance(value, str):
                        filter_parts.append(f'{col_ref} = "{value}"')
                    else:
                        filter_parts.append(f'{col_ref} = {value}')

                from .filter_to_dax import FilterExpression
                test_filters = [
                    FilterExpression(dax=f, source='test', table='', column='',
                                   condition_type='Manual', values=[])
                    for f in filter_parts
                ]

                query = self.builder._build_visual_dax_query(measures, columns, test_filters)
                exec_result = self.qe.validate_and_execute_dax(query, top_n=1)

                value = None
                if exec_result.get('success') and exec_result.get('rows'):
                    row = exec_result['rows'][0]
                    value = list(row.values())[0] if row else None

                results.append({
                    'permutation': i + 1,
                    'filters': perm,
                    'value': value,
                    'is_null': value is None,
                    'is_error': not exec_result.get('success'),
                    'error': exec_result.get('error'),
                    'time_ms': exec_result.get('execution_time_ms', 0)
                })

            except Exception as e:
                results.append({
                    'permutation': i + 1,
                    'filters': perm,
                    'value': None,
                    'is_null': True,
                    'is_error': True,
                    'error': str(e),
                    'time_ms': 0
                })

        # Analyze results
        null_count = sum(1 for r in results if r['is_null'])
        error_count = sum(1 for r in results if r['is_error'])

        return {
            'success': True,
            'visual': {
                'id': query_result.visual_info.visual_id,
                'name': query_result.visual_info.visual_name,
                'page': page_name
            },
            'permutations_tested': len(results),
            'null_results': null_count,
            'error_results': error_count,
            'results': results,
            'issues': [
                f'{null_count} filter combinations returned NULL' if null_count > 0 else None,
                f'{error_count} filter combinations caused errors' if error_count > 0 else None
            ]
        }

    def _generate_filter_permutations(
        self,
        slicer_values: Dict[str, List[Any]],
        max_count: int
    ) -> List[Dict[str, Any]]:
        """Generate filter value permutations."""
        if not slicer_values:
            return []

        keys = list(slicer_values.keys())
        values_list = [slicer_values[k] for k in keys]

        # Simple cartesian product with limit
        permutations = []

        def generate(current: Dict, depth: int):
            if len(permutations) >= max_count:
                return
            if depth == len(keys):
                permutations.append(current.copy())
                return

            key = keys[depth]
            for val in values_list[depth]:
                current[key] = val
                generate(current, depth + 1)

        generate({}, 0)
        return permutations

    # ========== PROFILING OPERATIONS ==========

    def profile_page(
        self,
        page_name: str,
        iterations: int = 3,
        include_slicers: bool = True,
        parallel: bool = True,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Profile all visuals on a page to identify slow visuals.

        Args:
            page_name: Page to profile
            iterations: Number of times to run each visual for averaging
            include_slicers: Include slicer filters
            parallel: Use parallel execution (default True)
            max_workers: Max concurrent queries (default 4)

        Returns:
            Page profile with timing and issues
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        visuals = self.builder.list_visuals(page_name)
        if not visuals:
            return {'success': False, 'error': f'No visuals found on page "{page_name}"'}

        # Filter to data visuals only (exclude slicers)
        data_visuals = [v for v in visuals if not v.get('is_slicer')]

        if not data_visuals:
            return {
                'success': True,
                'page': page_name,
                'visuals_profiled': 0,
                'message': 'No data visuals to profile (page contains only slicers/UI elements)'
            }

        results: List[ProfileResult] = []

        def _profile_single_visual(visual: Dict) -> Optional[ProfileResult]:
            """Profile a single visual (thread-safe)."""
            try:
                query_result = self.builder.build_visual_query(
                    page_name=page_name,
                    visual_id=visual['id'],
                    include_slicers=include_slicers
                )

                if not query_result or not query_result.dax_query:
                    return None

                times = []
                row_count = 0

                for _ in range(iterations):
                    exec_result = self.qe.validate_and_execute_dax(
                        query_result.dax_query, top_n=100
                    )
                    if exec_result.get('success'):
                        times.append(exec_result.get('execution_time_ms', 0))
                        row_count = max(row_count, len(exec_result.get('rows', [])))

                if not times:
                    return None

                avg_time = sum(times) / len(times)

                # Identify issues
                issues = []
                if avg_time > 2000:
                    issues.append(f'Slow query ({avg_time:.0f}ms > 2000ms)')
                if row_count > 1000:
                    issues.append(f'Large result set ({row_count} rows)')
                if max(times) > min(times) * 2 and len(times) > 1:
                    issues.append(f'High variance ({min(times):.0f}-{max(times):.0f}ms)')

                return ProfileResult(
                    visual_id=visual['id'],
                    visual_name=visual.get('friendly_name', visual['id']),
                    visual_type=visual.get('type', 'unknown'),
                    page_name=page_name,
                    measures=visual.get('measures', []),
                    avg_time_ms=avg_time,
                    min_time_ms=min(times),
                    max_time_ms=max(times),
                    row_count=row_count,
                    filter_count=len(query_result.filter_context.all_filters()),
                    issues=issues
                )
            except Exception as e:
                self.logger.warning(f"Error profiling visual {visual['id']}: {e}")
                return None

        # Execute profiling
        execution_mode = 'sequential'

        if parallel and len(data_visuals) > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            execution_mode = 'parallel'

            with ThreadPoolExecutor(max_workers=min(max_workers, len(data_visuals))) as executor:
                futures = {
                    executor.submit(_profile_single_visual, v): v
                    for v in data_visuals
                }

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        visual = futures[future]
                        self.logger.warning(f"Future failed for visual {visual.get('id')}: {e}")
        else:
            # Sequential execution
            for visual in data_visuals:
                result = _profile_single_visual(visual)
                if result:
                    results.append(result)

        # Sort by avg time descending
        results.sort(key=lambda x: x.avg_time_ms, reverse=True)

        total_time = sum(r.avg_time_ms for r in results)

        # Generate recommendations
        recommendations = []
        slow_visuals = [r for r in results if r.avg_time_ms > 1000]

        if slow_visuals:
            recommendations.append(
                f'Optimize {len(slow_visuals)} slow visual(s): ' +
                ', '.join(r.visual_name for r in slow_visuals[:3])
            )

        if total_time > 5000:
            recommendations.append(
                f'Page total load time ({total_time:.0f}ms) exceeds 5s target'
            )

        large_results = [r for r in results if r.row_count > 500]
        if large_results:
            recommendations.append(
                f'{len(large_results)} visual(s) return large result sets - consider aggregation'
            )

        return {
            'success': True,
            'page': page_name,
            'visuals_profiled': len(results),
            'total_time_ms': round(total_time, 1),
            'avg_time_per_visual_ms': round(total_time / len(results), 1) if results else 0,
            'execution_mode': execution_mode,
            'results': [
                {
                    'visual_id': r.visual_id,
                    'visual_name': r.visual_name,
                    'visual_type': r.visual_type,
                    'measures': r.measures,
                    'avg_time_ms': round(r.avg_time_ms, 1),
                    'min_time_ms': round(r.min_time_ms, 1),
                    'max_time_ms': round(r.max_time_ms, 1),
                    'row_count': r.row_count,
                    'filter_count': r.filter_count,
                    'issues': r.issues
                }
                for r in results
            ],
            'recommendations': recommendations
        }

    def filter_performance_matrix(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        filter_columns: Optional[List[str]] = None,
        max_combinations: int = 15
    ) -> Dict[str, Any]:
        """
        Test measure performance with different filter combinations.

        Args:
            page_name: Page name
            visual_id: Visual to test
            visual_name: Visual name (alternative)
            filter_columns: Specific columns to vary (auto-detect if None)
            max_combinations: Max filter combinations to test

        Returns:
            Performance matrix with timing for each filter combo
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        query_result = self.builder.build_visual_query(
            page_name=page_name,
            visual_id=visual_id,
            visual_name=visual_name
        )

        if not query_result:
            return {'success': False, 'error': 'Visual not found'}

        # Get filter columns from slicers if not specified
        if not filter_columns:
            slicers = self.builder.list_slicers(page_name)
            filter_columns = [f"'{s.table}'[{s.column}]" for s in slicers[:3]]

        if not filter_columns:
            return {
                'success': True,
                'message': 'No filter columns to test',
                'matrix': []
            }

        # Get sample values for each filter column
        filter_values = {}
        for col in filter_columns:
            try:
                query = f"EVALUATE TOPN(5, DISTINCT({col}))"
                result = self.qe.validate_and_execute_dax(query, top_n=5)
                if result.get('success') and result.get('rows'):
                    values = [list(r.values())[0] for r in result['rows']]
                    filter_values[col] = [v for v in values if v is not None][:5]
            except Exception:
                continue

        # Generate test matrix
        measures = query_result.visual_info.measures or [query_result.measure_name]
        measures = [m if m.startswith('[') else f'[{m}]' for m in measures]
        columns = query_result.visual_info.columns or []

        matrix_results = []

        # Test baseline (no extra filters)
        baseline_result = self.qe.validate_and_execute_dax(query_result.dax_query, top_n=1)
        baseline_time = baseline_result.get('execution_time_ms', 0)

        matrix_results.append({
            'filters': 'baseline (current)',
            'time_ms': baseline_time,
            'relative': 1.0,
            'status': 'baseline'
        })

        # Test each filter value
        for col, values in filter_values.items():
            for val in values[:3]:  # Limit per column
                if len(matrix_results) >= max_combinations:
                    break

                try:
                    if isinstance(val, str):
                        filter_dax = f'{col} = "{val}"'
                    else:
                        filter_dax = f'{col} = {val}'

                    from .filter_to_dax import FilterExpression
                    test_filter = FilterExpression(
                        dax=filter_dax, source='test', table='', column='',
                        condition_type='Manual', values=[val]
                    )

                    test_query = self.builder._build_visual_dax_query(
                        measures, columns, [test_filter]
                    )

                    result = self.qe.validate_and_execute_dax(test_query, top_n=1)
                    time_ms = result.get('execution_time_ms', 0)

                    relative = time_ms / baseline_time if baseline_time > 0 else 1.0

                    status = 'normal'
                    if relative > 2.0:
                        status = 'slow'
                    elif relative < 0.5:
                        status = 'fast'

                    matrix_results.append({
                        'filters': filter_dax,
                        'time_ms': time_ms,
                        'relative': round(relative, 2),
                        'status': status
                    })

                except Exception as e:
                    matrix_results.append({
                        'filters': filter_dax,
                        'time_ms': 0,
                        'relative': 0,
                        'status': 'error',
                        'error': str(e)
                    })

        # Find problematic filters
        slow_filters = [r for r in matrix_results if r['status'] == 'slow']

        return {
            'success': True,
            'visual': {
                'id': query_result.visual_info.visual_id,
                'name': query_result.visual_info.visual_name,
                'page': page_name
            },
            'baseline_time_ms': baseline_time,
            'combinations_tested': len(matrix_results),
            'matrix': matrix_results,
            'slow_filters': [r['filters'] for r in slow_filters],
            'recommendation': f'{len(slow_filters)} filter(s) cause >2x slowdown' if slow_filters else 'No problematic filters found'
        }

    # ========== DOCUMENTATION OPERATIONS ==========

    def document_page(self, page_name: str, lightweight: bool = True, include_ui_elements: bool = False) -> Dict[str, Any]:
        """
        Generate documentation for all visuals on a page.

        Args:
            page_name: Page to document
            lightweight: If True (default), skip expensive operations like measure expansion
                        and detailed filter context building for faster documentation.
            include_ui_elements: If True, include UI elements like shapes, buttons, visual groups.
                               Default False shows only data-bearing visuals (charts, tables, cards).

        Returns:
            Complete page documentation
        """
        # Get all visuals first to count totals
        all_visuals = self.builder.list_visuals(page_name, include_ui_elements=True)
        slicers = self.builder.list_slicers(page_name)

        # Count UI vs data visuals for summary
        total_elements = len(all_visuals)
        data_visuals = [v for v in all_visuals if v.get('is_data_visual', False)]
        ui_elements = [v for v in all_visuals if not v.get('is_data_visual', False)]

        # Filter to just data visuals unless UI elements requested
        visuals = all_visuals if include_ui_elements else data_visuals

        visual_docs = []

        # In lightweight mode, get page-level filter counts once for all visuals
        page_filter_count = 0
        report_filter_count = 0
        if lightweight:
            # Get page filters once (cached internally)
            page_path = self.builder._find_page_by_name(page_name)
            if page_path:
                page_filters = self.builder._get_page_filters(page_path)
                page_filter_count = len(page_filters)
            report_filters = self.builder._get_report_filters()
            report_filter_count = len(report_filters)

        for visual in visuals:
            if visual.get('is_slicer'):
                continue

            try:
                if lightweight:
                    # Fast path: use pre-extracted visual info without building queries
                    # Visual-level filters are already in the visual data from list_visuals
                    visual_filter_count = len(visual.get('filters', []))

                    visual_docs.append({
                        'id': visual['id'],
                        'name': visual.get('friendly_name', visual['id']),
                        'type': visual.get('type_display', visual.get('type')),
                        'title': visual.get('title'),
                        'is_data_visual': visual.get('is_data_visual', True),
                        'measures': visual.get('measures', []),
                        'columns': visual.get('columns', []),
                        'filters': {
                            'report': report_filter_count,
                            'page': page_filter_count,
                            'visual': visual_filter_count,
                            'slicer': len(slicers)  # All slicers affect all visuals
                        }
                    })
                else:
                    # Full path: build complete query with filter context
                    # Skip expand_measures for documentation - we don't need DAX expressions
                    query_result = self.builder.build_visual_query(
                        page_name=page_name,
                        visual_id=visual['id'],
                        expand_measures=False  # Skip expensive DMV queries
                    )

                    filter_info = {
                        'report': 0,
                        'page': 0,
                        'visual': 0,
                        'slicer': 0
                    }

                    if query_result:
                        filter_info = {
                            'report': len(query_result.filter_context.report_filters),
                            'page': len(query_result.filter_context.page_filters),
                            'visual': len(query_result.filter_context.visual_filters),
                            'slicer': len(query_result.filter_context.slicer_filters)
                        }

                    visual_docs.append({
                        'id': visual['id'],
                        'name': visual.get('friendly_name', visual['id']),
                        'type': visual.get('type_display', visual.get('type')),
                        'title': visual.get('title'),
                        'is_data_visual': visual.get('is_data_visual', True),
                        'measures': visual.get('measures', []),
                        'columns': visual.get('columns', []),
                        'filters': filter_info
                    })

            except Exception as e:
                visual_docs.append({
                    'id': visual['id'],
                    'name': visual.get('friendly_name', visual['id']),
                    'type': visual.get('type', 'unknown'),
                    'error': str(e)
                })

        slicer_docs = [
            {
                'id': s.slicer_id,
                'field': s.field_reference,
                'table': s.table,
                'column': s.column,
                'selection_mode': s.selection_mode,
                'current_selection': s.selected_values[:5] if s.selected_values else [],
                'selection_count': len(s.selected_values)
            }
            for s in slicers
        ]

        # Build visual type breakdown for summary (UI vs Data)
        ui_type_counts = {}
        data_type_counts = {}
        for v in all_visuals:
            vtype = v.get('type_display', v.get('type', 'Unknown'))
            if v.get('is_data_visual', False):
                data_type_counts[vtype] = data_type_counts.get(vtype, 0) + 1
            else:
                ui_type_counts[vtype] = ui_type_counts.get(vtype, 0) + 1

        # Count slicers separately (they're in ui_elements but shown separately)
        slicer_count_in_ui = sum(1 for v in ui_elements if v.get('is_slicer', False))

        return {
            'success': True,
            'page': page_name,
            'data_visual_count': len(visual_docs),  # Renamed for clarity
            'slicer_count': len(slicer_docs),
            'visuals': visual_docs,
            'slicers': slicer_docs,
            'summary': {
                'total_page_elements': total_elements,
                'data_visuals': len(data_visuals),
                'slicers': len(slicer_docs),
                'ui_elements': len(ui_elements) - slicer_count_in_ui,  # Exclude slicers from UI count
                'showing': 'all elements' if include_ui_elements else 'data visuals only',
                'total_measures': len(set(m for v in visual_docs for m in v.get('measures', []))),
                'total_columns': len(set(c for v in visual_docs for c in v.get('columns', []))),
                'data_visual_types': data_type_counts,
                'ui_element_types': ui_type_counts
            }
        }

    def document_report(self, lightweight: bool = True) -> Dict[str, Any]:
        """
        Generate complete documentation for the entire report.

        Args:
            lightweight: If True (default), skip expensive operations like measure expansion
                        and detailed filter context building for faster documentation.

        Returns:
            Complete report documentation
        """
        pages = self.builder.list_pages()

        report_doc = {
            'success': True,
            'pages': [],
            'summary': {
                'page_count': len(pages),
                'total_visuals': 0,
                'total_slicers': 0,
                'all_measures': set(),
                'all_columns': set()
            }
        }

        for page in pages:
            page_doc = self.document_page(page['name'], lightweight=lightweight)

            report_doc['pages'].append({
                'name': page['name'],
                'id': page['id'],
                'ordinal': page.get('ordinal', 0),
                'visual_count': page_doc.get('visual_count', 0),
                'slicer_count': page_doc.get('slicer_count', 0),
                'visuals': page_doc.get('visuals', []),
                'slicers': page_doc.get('slicers', [])
            })

            report_doc['summary']['total_visuals'] += page_doc.get('visual_count', 0)
            report_doc['summary']['total_slicers'] += page_doc.get('slicer_count', 0)

            for v in page_doc.get('visuals', []):
                report_doc['summary']['all_measures'].update(v.get('measures', []))
                report_doc['summary']['all_columns'].update(v.get('columns', []))

        # Convert sets to lists for JSON
        report_doc['summary']['all_measures'] = list(report_doc['summary']['all_measures'])
        report_doc['summary']['all_columns'] = list(report_doc['summary']['all_columns'])
        report_doc['summary']['measure_count'] = len(report_doc['summary']['all_measures'])
        report_doc['summary']['column_count'] = len(report_doc['summary']['all_columns'])

        return report_doc

    def measure_lineage(self, measure_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Show which visuals use which measures.

        Args:
            measure_name: Specific measure to trace (None = all measures)

        Returns:
            Lineage information mapping measures to visuals
        """
        pages = self.builder.list_pages()

        # Build measure -> visuals mapping
        measure_map: Dict[str, LineageInfo] = {}

        for page in pages:
            visuals = self.builder.list_visuals(page['name'])

            for visual in visuals:
                if visual.get('is_slicer'):
                    continue

                for m in visual.get('measures', []):
                    clean_m = m.strip('[]')

                    # Skip if specific measure requested and this isn't it
                    if measure_name and clean_m.lower() != measure_name.strip('[]').lower():
                        continue

                    if clean_m not in measure_map:
                        measure_map[clean_m] = LineageInfo(
                            name=clean_m,
                            table=None
                        )

                    measure_map[clean_m].visuals.append({
                        'visual_id': visual['id'],
                        'visual_name': visual.get('friendly_name', visual['id']),
                        'visual_type': visual.get('type', 'unknown'),
                        'page': page['name']
                    })

                    if page['name'] not in measure_map[clean_m].pages:
                        measure_map[clean_m].pages.append(page['name'])

                    measure_map[clean_m].usage_count += 1

        # Sort by usage
        sorted_measures = sorted(
            measure_map.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )

        return {
            'success': True,
            'measure_filter': measure_name,
            'measures_found': len(sorted_measures),
            'lineage': [
                {
                    'measure': m.name,
                    'usage_count': m.usage_count,
                    'pages': m.pages,
                    'page_count': len(m.pages),
                    'visuals': m.visuals
                }
                for m in sorted_measures
            ]
        }

    def filter_lineage(self, page_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Show which filters affect which visuals.

        Args:
            page_name: Specific page to analyze (None = all pages)

        Returns:
            Filter lineage information
        """
        pages = self.builder.list_pages()
        if page_name:
            pages = [p for p in pages if p['name'].lower() == page_name.lower()]

        # Build filter -> visuals mapping
        filter_map: Dict[str, Dict] = {}

        # Report-level filters affect all visuals
        report_filters = self.builder._get_report_filters()
        for rf in report_filters:
            from .filter_to_dax import FilterToDaxConverter
            converter = FilterToDaxConverter()
            expr = converter.convert_filter(rf, source='report')
            if expr:
                key = f"report:{expr.table}.{expr.column}"
                if key not in filter_map:
                    filter_map[key] = {
                        'level': 'report',
                        'table': expr.table,
                        'column': expr.column,
                        'dax': expr.dax,
                        'affects_all': True,
                        'pages': [],
                        'visual_count': 0
                    }

        for page in pages:
            page_path = self.builder._find_page_by_name(page['name'])
            if not page_path:
                continue

            # Page-level filters
            page_filters = self.builder._get_page_filters(page_path)
            for pf in page_filters:
                from .filter_to_dax import FilterToDaxConverter
                converter = FilterToDaxConverter()
                expr = converter.convert_filter(pf, source='page')
                if expr:
                    key = f"page:{page['name']}:{expr.table}.{expr.column}"
                    if key not in filter_map:
                        filter_map[key] = {
                            'level': 'page',
                            'page': page['name'],
                            'table': expr.table,
                            'column': expr.column,
                            'dax': expr.dax,
                            'affects_all': False,
                            'visual_count': 0
                        }

            # Slicer filters
            slicers = self.builder.list_slicers(page['name'])
            for slicer in slicers:
                key = f"slicer:{page['name']}:{slicer.table}.{slicer.column}"
                if key not in filter_map:
                    filter_map[key] = {
                        'level': 'slicer',
                        'page': page['name'],
                        'table': slicer.table,
                        'column': slicer.column,
                        'field': slicer.field_reference,
                        'affects_all': False,
                        'current_selection': slicer.selected_values[:3] if slicer.selected_values else [],
                        'visual_count': 0
                    }

            # Count affected visuals
            visuals = self.builder.list_visuals(page['name'])
            non_slicer_count = len([v for v in visuals if not v.get('is_slicer')])

            for key, info in filter_map.items():
                if info['level'] == 'report':
                    info['visual_count'] += non_slicer_count
                    if page['name'] not in info['pages']:
                        info['pages'].append(page['name'])
                elif info.get('page') == page['name']:
                    info['visual_count'] = non_slicer_count

        return {
            'success': True,
            'page_filter': page_name,
            'filters_found': len(filter_map),
            'lineage': list(filter_map.values())
        }

    # ========== ADVANCED ANALYSIS OPERATIONS ==========

    def decompose_value(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        dimension: Optional[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Break down an aggregated value by dimensions.

        Args:
            page_name: Page containing the visual
            visual_id: Visual ID
            visual_name: Visual name
            dimension: Dimension to decompose by (auto-detect if None)
            top_n: Number of top contributors

        Returns:
            Decomposition by dimension values
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        query_result = self.builder.build_visual_query(
            page_name=page_name,
            visual_id=visual_id,
            visual_name=visual_name
        )

        if not query_result:
            return {'success': False, 'error': 'Visual not found'}

        # Get total value first
        total_result = self.qe.validate_and_execute_dax(query_result.dax_query, top_n=1)
        total_value = None
        if total_result.get('success') and total_result.get('rows'):
            row = total_result['rows'][0]
            total_value = list(row.values())[0] if row else None

        # Determine dimension to decompose by
        if not dimension:
            # Try to find a good dimension from the visual or model
            if query_result.visual_info.columns:
                dimension = query_result.visual_info.columns[0]
            else:
                # Query available dimensions
                return {
                    'success': False,
                    'error': 'No dimension specified. Provide a dimension like "\'Product\'[Category]"'
                }

        # Build decomposition query
        measure = query_result.visual_info.measures[0] if query_result.visual_info.measures else query_result.measure_name
        measure = measure if measure.startswith('[') else f'[{measure}]'

        filters = query_result.filter_context.all_filters()
        filter_dax = [f.dax for f in filters if f.dax and f.classification == 'data']
        filter_str = ', '.join(filter_dax) if filter_dax else ''

        if filter_str:
            decomp_query = f"""EVALUATE
TOPN(
    {top_n},
    ADDCOLUMNS(
        CALCULATETABLE(VALUES({dimension}), {filter_str}),
        "Value", CALCULATE({measure}, {filter_str})
    ),
    [Value], DESC
)"""
        else:
            decomp_query = f"""EVALUATE
TOPN(
    {top_n},
    ADDCOLUMNS(
        VALUES({dimension}),
        "Value", {measure}
    ),
    [Value], DESC
)"""

        decomp_result = self.qe.validate_and_execute_dax(decomp_query, top_n=top_n)

        if not decomp_result.get('success'):
            return {
                'success': False,
                'error': decomp_result.get('error'),
                'query': decomp_query
            }

        # Process results
        components = []
        running_total = 0

        for row in decomp_result.get('rows', []):
            values = list(row.values())
            dim_value = values[0] if len(values) > 0 else None
            measure_value = values[1] if len(values) > 1 else values[0]

            try:
                num_value = float(measure_value) if measure_value is not None else 0
                pct = (num_value / float(total_value) * 100) if total_value else 0
                running_total += num_value
            except (ValueError, TypeError):
                num_value = measure_value
                pct = 0

            components.append({
                'dimension_value': dim_value,
                'value': measure_value,
                'percentage': round(pct, 1),
                'cumulative_pct': round(running_total / float(total_value) * 100, 1) if total_value else 0
            })

        return {
            'success': True,
            'visual': {
                'id': query_result.visual_info.visual_id,
                'name': query_result.visual_info.visual_name,
                'page': page_name
            },
            'total_value': total_value,
            'dimension': dimension,
            'top_n': top_n,
            'components': components,
            'coverage': components[-1]['cumulative_pct'] if components else 0
        }

    def contribution_analysis(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        dimension: Optional[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Identify which dimension values contribute most to the total (Pareto analysis).

        Similar to decompose but focused on identifying the 80/20 contributors.
        """
        decomp = self.decompose_value(page_name, visual_id, visual_name, dimension, top_n)

        if not decomp.get('success'):
            return decomp

        components = decomp.get('components', [])

        # Find the 80% threshold
        pareto_contributors = []
        others = []

        for comp in components:
            if comp['cumulative_pct'] <= 80:
                pareto_contributors.append(comp)
            else:
                others.append(comp)

        return {
            'success': True,
            'visual': decomp.get('visual'),
            'total_value': decomp.get('total_value'),
            'dimension': decomp.get('dimension'),
            'pareto_analysis': {
                'top_contributors': pareto_contributors,
                'top_contributor_count': len(pareto_contributors),
                'top_contributor_coverage': pareto_contributors[-1]['cumulative_pct'] if pareto_contributors else 0,
                'remaining_items': len(others),
                'remaining_coverage': 100 - (pareto_contributors[-1]['cumulative_pct'] if pareto_contributors else 0)
            },
            'insight': f'{len(pareto_contributors)} of {len(components)} {decomp.get("dimension", "items")} contribute ~80% of the total'
        }

    def trend_analysis(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        date_column: Optional[str] = None,
        granularity: str = 'month'
    ) -> Dict[str, Any]:
        """
        Analyze value trend over time.

        Args:
            page_name: Page name
            visual_id: Visual ID
            visual_name: Visual name
            date_column: Date column (auto-detect if None)
            granularity: 'day', 'week', 'month', 'quarter', 'year'

        Returns:
            Trend analysis with growth rates
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        query_result = self.builder.build_visual_query(
            page_name=page_name,
            visual_id=visual_id,
            visual_name=visual_name
        )

        if not query_result:
            return {'success': False, 'error': 'Visual not found'}

        # Find date column
        if not date_column:
            # Try to detect from columns
            for col in query_result.visual_info.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    date_column = col
                    break

        if not date_column:
            return {
                'success': False,
                'error': 'No date column specified. Provide date_column like "\'Date\'[Date]"'
            }

        measure = query_result.visual_info.measures[0] if query_result.visual_info.measures else query_result.measure_name
        measure = measure if measure.startswith('[') else f'[{measure}]'

        # Build trend query based on granularity
        granularity_map = {
            'day': date_column,
            'week': f'WEEKNUM({date_column})',
            'month': f'FORMAT({date_column}, "YYYY-MM")',
            'quarter': f'FORMAT({date_column}, "YYYY") & "-Q" & FORMAT(QUARTER({date_column}), "0")',
            'year': f'YEAR({date_column})'
        }

        group_expr = granularity_map.get(granularity, date_column)

        trend_query = f"""EVALUATE
ADDCOLUMNS(
    SUMMARIZE(ALL(), {date_column}),
    "Period", {group_expr},
    "Value", {measure}
)
ORDER BY {date_column}"""

        result = self.qe.validate_and_execute_dax(trend_query, top_n=100)

        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error'),
                'query': trend_query
            }

        # Process trend data
        trend_data = []
        prev_value = None

        for row in result.get('rows', []):
            values = list(row.values())
            period = values[1] if len(values) > 1 else values[0]
            value = values[2] if len(values) > 2 else (values[1] if len(values) > 1 else values[0])

            growth = None
            growth_pct = None

            if prev_value is not None and value is not None:
                try:
                    growth = float(value) - float(prev_value)
                    growth_pct = (growth / float(prev_value) * 100) if prev_value != 0 else None
                except (ValueError, TypeError):
                    pass

            trend_data.append({
                'period': period,
                'value': value,
                'growth': growth,
                'growth_pct': round(growth_pct, 1) if growth_pct is not None else None
            })

            prev_value = value

        # Calculate overall trend
        if len(trend_data) >= 2:
            first_val = trend_data[0]['value']
            last_val = trend_data[-1]['value']
            try:
                overall_growth = float(last_val) - float(first_val)
                overall_growth_pct = (overall_growth / float(first_val) * 100) if first_val else None
            except (ValueError, TypeError):
                overall_growth = None
                overall_growth_pct = None
        else:
            overall_growth = None
            overall_growth_pct = None

        # Determine trend direction
        positive_periods = sum(1 for t in trend_data if t.get('growth_pct') and t['growth_pct'] > 0)
        negative_periods = sum(1 for t in trend_data if t.get('growth_pct') and t['growth_pct'] < 0)

        if positive_periods > negative_periods * 2:
            trend_direction = 'strongly_upward'
        elif positive_periods > negative_periods:
            trend_direction = 'upward'
        elif negative_periods > positive_periods * 2:
            trend_direction = 'strongly_downward'
        elif negative_periods > positive_periods:
            trend_direction = 'downward'
        else:
            trend_direction = 'stable'

        return {
            'success': True,
            'visual': {
                'id': query_result.visual_info.visual_id,
                'name': query_result.visual_info.visual_name,
                'page': page_name
            },
            'date_column': date_column,
            'granularity': granularity,
            'periods': len(trend_data),
            'trend_direction': trend_direction,
            'overall_growth': overall_growth,
            'overall_growth_pct': round(overall_growth_pct, 1) if overall_growth_pct else None,
            'data': trend_data[:50]  # Limit output
        }

    def root_cause_analysis(
        self,
        page_name: str,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        baseline_filters: Optional[List[str]] = None,
        comparison_filters: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze why a value changed between two filter contexts.

        Args:
            page_name: Page name
            visual_id: Visual ID
            visual_name: Visual name
            baseline_filters: Filters for baseline (e.g., previous period)
            comparison_filters: Filters for comparison (e.g., current period)
            dimensions: Dimensions to analyze for root cause
            top_n: Top contributors to show

        Returns:
            Root cause analysis showing which dimensions drove the change
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        query_result = self.builder.build_visual_query(
            page_name=page_name,
            visual_id=visual_id,
            visual_name=visual_name
        )

        if not query_result:
            return {'success': False, 'error': 'Visual not found'}

        measure = query_result.visual_info.measures[0] if query_result.visual_info.measures else query_result.measure_name
        measure = measure if measure.startswith('[') else f'[{measure}]'

        # Get baseline and comparison totals
        base_filters = ', '.join(baseline_filters) if baseline_filters else ''
        comp_filters = ', '.join(comparison_filters) if comparison_filters else ''

        if base_filters:
            base_query = f'EVALUATE ROW("Value", CALCULATE({measure}, {base_filters}))'
        else:
            base_query = f'EVALUATE ROW("Value", {measure})'

        if comp_filters:
            comp_query = f'EVALUATE ROW("Value", CALCULATE({measure}, {comp_filters}))'
        else:
            comp_query = f'EVALUATE ROW("Value", {measure})'

        base_result = self.qe.validate_and_execute_dax(base_query, top_n=1)
        comp_result = self.qe.validate_and_execute_dax(comp_query, top_n=1)

        baseline_value = None
        comparison_value = None

        if base_result.get('success') and base_result.get('rows'):
            baseline_value = list(base_result['rows'][0].values())[0]

        if comp_result.get('success') and comp_result.get('rows'):
            comparison_value = list(comp_result['rows'][0].values())[0]

        if baseline_value is None or comparison_value is None:
            return {
                'success': False,
                'error': 'Could not get baseline or comparison values',
                'baseline_error': base_result.get('error'),
                'comparison_error': comp_result.get('error')
            }

        try:
            total_change = float(comparison_value) - float(baseline_value)
            change_pct = (total_change / float(baseline_value) * 100) if baseline_value else None
        except (ValueError, TypeError):
            total_change = None
            change_pct = None

        # If no dimensions specified, try to use visual columns
        if not dimensions:
            dimensions = query_result.visual_info.columns[:3] if query_result.visual_info.columns else []

        # Analyze each dimension
        dimension_impacts = []

        for dim in dimensions:
            try:
                # Get breakdown by dimension for baseline and comparison
                if base_filters:
                    dim_base_query = f"""EVALUATE
ADDCOLUMNS(
    CALCULATETABLE(VALUES({dim}), {base_filters}),
    "Value", CALCULATE({measure}, {base_filters})
)"""
                else:
                    dim_base_query = f"""EVALUATE
ADDCOLUMNS(
    VALUES({dim}),
    "Value", {measure}
)"""

                if comp_filters:
                    dim_comp_query = f"""EVALUATE
ADDCOLUMNS(
    CALCULATETABLE(VALUES({dim}), {comp_filters}),
    "Value", CALCULATE({measure}, {comp_filters})
)"""
                else:
                    dim_comp_query = dim_base_query

                dim_base_result = self.qe.validate_and_execute_dax(dim_base_query, top_n=50)
                dim_comp_result = self.qe.validate_and_execute_dax(dim_comp_query, top_n=50)

                if not dim_base_result.get('success') or not dim_comp_result.get('success'):
                    continue

                # Build value maps
                base_map = {}
                for row in dim_base_result.get('rows', []):
                    vals = list(row.values())
                    if len(vals) >= 2:
                        base_map[vals[0]] = vals[1]

                comp_map = {}
                for row in dim_comp_result.get('rows', []):
                    vals = list(row.values())
                    if len(vals) >= 2:
                        comp_map[vals[0]] = vals[1]

                # Find top changers
                changes = []
                all_keys = set(base_map.keys()) | set(comp_map.keys())

                for key in all_keys:
                    base_val = base_map.get(key, 0) or 0
                    comp_val = comp_map.get(key, 0) or 0

                    try:
                        change = float(comp_val) - float(base_val)
                        changes.append({
                            'value': key,
                            'baseline': base_val,
                            'comparison': comp_val,
                            'change': change,
                            'abs_change': abs(change)
                        })
                    except (ValueError, TypeError):
                        continue

                # Sort by absolute change
                changes.sort(key=lambda x: x['abs_change'], reverse=True)
                top_changes = changes[:top_n]

                dimension_impacts.append({
                    'dimension': dim,
                    'top_changes': top_changes,
                    'total_positive': sum(c['change'] for c in changes if c['change'] > 0),
                    'total_negative': sum(c['change'] for c in changes if c['change'] < 0)
                })

            except Exception as e:
                self.logger.warning(f"Error analyzing dimension {dim}: {e}")

        return {
            'success': True,
            'visual': {
                'id': query_result.visual_info.visual_id,
                'name': query_result.visual_info.visual_name,
                'page': page_name
            },
            'baseline': {
                'filters': baseline_filters or [],
                'value': baseline_value
            },
            'comparison': {
                'filters': comparison_filters or [],
                'value': comparison_value
            },
            'total_change': total_change,
            'change_pct': round(change_pct, 1) if change_pct else None,
            'dimension_analysis': dimension_impacts
        }

    def export_debug_report(
        self,
        page_name: Optional[str] = None,
        visual_id: Optional[str] = None,
        visual_name: Optional[str] = None,
        format: str = 'markdown'
    ) -> Dict[str, Any]:
        """
        Export debug information as a formatted report.

        Args:
            page_name: Page to export (None = current)
            visual_id: Specific visual (None = all on page)
            visual_name: Visual name
            format: 'markdown' or 'json'

        Returns:
            Formatted debug report
        """
        if page_name and (visual_id or visual_name):
            # Export single visual
            query_result = self.builder.build_visual_query(
                page_name=page_name,
                visual_id=visual_id,
                visual_name=visual_name
            )

            if not query_result:
                return {'success': False, 'error': 'Visual not found'}

            report_data = {
                'type': 'visual',
                'visual': {
                    'id': query_result.visual_info.visual_id,
                    'name': query_result.visual_info.visual_name,
                    'type': query_result.visual_info.visual_type,
                    'page': page_name,
                    'title': query_result.visual_info.title,
                    'measures': query_result.visual_info.measures,
                    'columns': query_result.visual_info.columns
                },
                'filter_context': query_result.filter_breakdown,
                'query': query_result.dax_query,
                'expanded_query': query_result.expanded_query
            }
        elif page_name:
            # Export page
            report_data = self.document_page(page_name)
            report_data['type'] = 'page'
        else:
            # Export entire report
            report_data = self.document_report()
            report_data['type'] = 'report'

        if format == 'markdown':
            markdown = self._generate_markdown_report(report_data)
            return {
                'success': True,
                'format': 'markdown',
                'content': markdown,
                'data': report_data
            }
        else:
            return {
                'success': True,
                'format': 'json',
                'data': report_data
            }

    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate markdown report from data."""
        lines = []
        report_type = data.get('type', 'unknown')

        lines.append(f"# Power BI Debug Report")
        lines.append(f"")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"")

        if report_type == 'visual':
            visual = data.get('visual', {})
            lines.append(f"## Visual: {visual.get('name', 'Unknown')}")
            lines.append(f"")
            lines.append(f"| Property | Value |")
            lines.append(f"|----------|-------|")
            lines.append(f"| ID | `{visual.get('id')}` |")
            lines.append(f"| Type | {visual.get('type')} |")
            lines.append(f"| Page | {visual.get('page')} |")
            lines.append(f"| Measures | {', '.join(visual.get('measures', []))} |")
            lines.append(f"| Columns | {', '.join(visual.get('columns', []))} |")
            lines.append(f"")

            lines.append(f"### Filter Context")
            lines.append(f"")

            filter_context = data.get('filter_context', {})
            for level, filters in filter_context.items():
                if filters:
                    lines.append(f"**{level.replace('_', ' ').title()}:**")
                    for f in filters:
                        lines.append(f"- `{f.get('dax', f)}`")
                    lines.append(f"")

            lines.append(f"### Generated Query")
            lines.append(f"")
            lines.append(f"```dax")
            lines.append(data.get('query', 'N/A'))
            lines.append(f"```")

        elif report_type == 'page':
            lines.append(f"## Page: {data.get('page', 'Unknown')}")
            lines.append(f"")
            lines.append(f"**Visuals:** {data.get('visual_count', 0)}")
            lines.append(f"**Slicers:** {data.get('slicer_count', 0)}")
            lines.append(f"")

            lines.append(f"### Visuals")
            lines.append(f"")
            for v in data.get('visuals', []):
                lines.append(f"- **{v.get('name')}** ({v.get('type')})")
                if v.get('measures'):
                    lines.append(f"  - Measures: {', '.join(v['measures'])}")

        elif report_type == 'report':
            summary = data.get('summary', {})
            lines.append(f"## Report Summary")
            lines.append(f"")
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Pages | {summary.get('page_count', 0)} |")
            lines.append(f"| Total Visuals | {summary.get('total_visuals', 0)} |")
            lines.append(f"| Total Slicers | {summary.get('total_slicers', 0)} |")
            lines.append(f"| Unique Measures | {summary.get('measure_count', 0)} |")
            lines.append(f"")

            for page in data.get('pages', []):
                lines.append(f"### {page.get('name')}")
                lines.append(f"")
                lines.append(f"- Visuals: {page.get('visual_count', 0)}")
                lines.append(f"- Slicers: {page.get('slicer_count', 0)}")
                lines.append(f"")

        return '\n'.join(lines)
