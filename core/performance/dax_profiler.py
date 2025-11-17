"""
DAX Performance Profiler - Analyzes SE/FE breakdown and execution traces.
Integrates with existing performance infrastructure.
"""
from typing import Dict, Any, List, Optional
import logging
from .performance_optimizer import PerformanceOptimizer

logger = logging.getLogger(__name__)

class DaxPerformanceProfiler:
    """
    Specialized DAX performance profiler.
    Works alongside existing PerformanceOptimizer.
    """

    def __init__(self, query_executor=None):
        self.query_executor = query_executor
        self.optimizer = PerformanceOptimizer(query_executor) if query_executor else None

    def profile_query(
        self,
        query: str,
        connection_info: Dict[str, Any],
        runs: int = 3
    ) -> Dict[str, Any]:
        """
        Profile DAX query execution with multiple runs.

        Args:
            query: DAX query to profile
            connection_info: Connection information
            runs: Number of benchmark runs (after warm-up)

        Returns:
            Profiling results with performance analysis
        """
        if not self.query_executor:
            return {
                "success": False,
                "error": "Query executor not available"
            }

        xmla_endpoint = connection_info.get("xmla_endpoint", "localhost")
        dataset_name = connection_info.get("dataset_name", "")
        access_token = connection_info.get("access_token")

        logger.info("Executing warm-up run...")
        success, _, error = self.query_executor.execute_dax_with_profiling(
            query, xmla_endpoint, dataset_name, access_token, timeout=120
        )

        if not success:
            return {
                "success": False,
                "error": f"Warm-up execution failed: {error}"
            }

        # Benchmark runs
        benchmark_runs = []
        for i in range(runs):
            logger.info(f"Executing benchmark run {i+1}/{runs}...")
            success, result, error = self.query_executor.execute_dax_with_profiling(
                query, xmla_endpoint, dataset_name, access_token, timeout=120
            )

            if not success:
                return {
                    "success": False,
                    "error": f"Benchmark run {i+1} failed: {error}"
                }

            benchmark_runs.append(result)

        # Select fastest run
        fastest_run = self._select_fastest_run(benchmark_runs)

        # Analyze performance
        analysis = self.optimizer.analyze_dax_performance(fastest_run) if self.optimizer else {}

        return {
            "success": True,
            "fastest_run": fastest_run,
            "analysis": analysis,
            "all_runs": benchmark_runs
        }

    def _select_fastest_run(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the fastest run from benchmark runs"""
        fastest = min(
            runs,
            key=lambda r: r.get("Performance", {}).get("Total", float('inf'))
        )
        return fastest

    def compare_queries(
        self,
        baseline_result: Dict[str, Any],
        optimized_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare baseline and optimized query results.

        Returns:
            Comparison with improvement percentage and semantic equivalence
        """
        baseline_perf = baseline_result.get("Performance", {})
        optimized_perf = optimized_result.get("Performance", {})

        baseline_total = baseline_perf.get("Total", 0)
        optimized_total = optimized_perf.get("Total", 0)

        improvement = (
            ((baseline_total - optimized_total) / baseline_total * 100)
            if baseline_total > 0 else 0
        )

        # Check semantic equivalence
        semantic_eq = self._check_semantic_equivalence(
            baseline_result.get("Results", []),
            optimized_result.get("Results", [])
        )

        return {
            "improvement_percent": round(improvement, 2),
            "baseline_ms": baseline_total,
            "optimized_ms": optimized_total,
            "semantic_equivalence": semantic_eq,
            "performance_comparison": {
                "baseline": self.optimizer._calculate_performance_metrics(baseline_perf) if self.optimizer else {},
                "optimized": self.optimizer._calculate_performance_metrics(optimized_perf) if self.optimizer else {}
            }
        }

    def _check_semantic_equivalence(
        self, baseline_results: List[Dict], optimized_results: List[Dict]
    ) -> Dict[str, Any]:
        """Check if optimized query returns identical results to baseline"""
        import json

        if len(baseline_results) != len(optimized_results):
            return {
                "is_equivalent": False,
                "reason": f"Result count differs: baseline={len(baseline_results)}, optimized={len(optimized_results)}"
            }

        for i, (baseline, optimized) in enumerate(zip(baseline_results, optimized_results)):
            # Compare row counts
            if baseline.get("RowCount") != optimized.get("RowCount"):
                return {
                    "is_equivalent": False,
                    "reason": f"Row count differs in result {i}: baseline={baseline.get('RowCount')}, optimized={optimized.get('RowCount')}"
                }

            # Compare actual data (row by row)
            baseline_rows = baseline.get("Rows", [])
            optimized_rows = optimized.get("Rows", [])

            baseline_signatures = sorted([
                json.dumps(row, sort_keys=True, default=str)
                for row in baseline_rows
            ])
            optimized_signatures = sorted([
                json.dumps(row, sort_keys=True, default=str)
                for row in optimized_rows
            ])

            if baseline_signatures != optimized_signatures:
                return {
                    "is_equivalent": False,
                    "reason": f"Data values differ in result {i}"
                }

        return {
            "is_equivalent": True,
            "reason": "Results are semantically equivalent"
        }
