"""
Enhanced Performance Analyzer v2 with SE/FE breakdown, query plan analysis, and batch profiling.

This module provides comprehensive query performance analysis using AMO tracing with:
- Storage Engine (SE) vs Formula Engine (FE) timing breakdown
- Query plan capture and analysis
- Batch profiling for multiple queries
- Performance comparison capabilities
- Visualization data generation for waterfall charts and query plans
"""

import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class PerformanceAnalyzerV2:
    """
    Enhanced performance analyzer with query plan analysis and batch profiling.

    Uses AMO trace manager for authoritative SE/FE timing breakdown.
    """

    def __init__(self, connection_string: str, query_executor: Any):
        """
        Initialize performance analyzer.

        Args:
            connection_string: Connection string for Analysis Services
            query_executor: Query executor instance for running DAX queries
        """
        self.connection_string = connection_string
        self.query_executor = query_executor
        self.trace_manager: Optional[Any] = None
        self._trace_backend: Optional[str] = None

    def _get_trace_manager(self) -> Optional[Any]:
        """Get or initialize trace manager (lazy initialization)."""
        if self.trace_manager is not None:
            return self.trace_manager

        # Try AMO trace manager first (most reliable for Desktop)
        try:
            from core.performance.amo_trace_manager import AmoTraceManager
            manager = AmoTraceManager(self.connection_string)
            if manager.connect():
                self.trace_manager = manager
                self._trace_backend = "amo"
                logger.info("Using AMO trace backend")
                return manager
        except Exception as exc:
            logger.debug("AMO trace manager initialization failed: %s", exc)

        # Try XMLA trace manager as fallback
        try:
            from core.performance.xmla_trace_manager import XmlaTraceManager
            manager = XmlaTraceManager(self.connection_string)
            if manager.connect():
                self.trace_manager = manager
                self._trace_backend = "xmla"
                logger.info("Using XMLA trace backend")
                return manager
        except Exception as exc:
            logger.debug("XMLA trace manager initialization failed: %s", exc)

        logger.warning("No trace backend available - SE/FE breakdown unavailable")
        return None

    def analyze_query_detailed(
        self,
        query: str,
        runs: int = 3,
        clear_cache: bool = True,
        capture_query_plan: bool = False,
        event_timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Perform detailed query analysis with SE/FE breakdown.

        Args:
            query: DAX query to analyze
            runs: Number of execution runs
            clear_cache: Whether to clear cache before first run
            capture_query_plan: Whether to capture query plan (if supported)
            event_timeout: Timeout for trace event capture (seconds)

        Returns:
            Dictionary with detailed performance metrics and breakdowns
        """
        trace_mgr = self._get_trace_manager()
        trace_enabled = False

        if trace_mgr:
            try:
                if trace_mgr.start_trace():
                    trace_enabled = True
                    logger.debug("Trace started for detailed query analysis")
            except Exception as exc:
                logger.debug("Failed to start trace: %s", exc)

        results: List[Dict[str, Any]] = []
        se_totals: List[float] = []
        fe_totals: List[float] = []
        aggregated_event_counts: Dict[str, int] = defaultdict(int)

        try:
            # Clear cache if requested
            if clear_cache and hasattr(self.query_executor, "flush_cache"):
                try:
                    self.query_executor.flush_cache()
                    logger.debug("Query cache cleared")
                except Exception:
                    pass

            # Execute query multiple times
            run_count = max(1, int(runs or 1))
            for i in range(run_count):
                # Snapshot event buffer index before query
                start_index = 0
                if trace_enabled and hasattr(trace_mgr, 'get_event_count'):
                    start_index = trace_mgr.get_event_count()

                # Execute query with timing
                t0 = time.perf_counter()
                result = self.query_executor.validate_and_execute_dax(
                    query, top_n=0, bypass_cache=(i == 0 and clear_cache)
                )
                t1 = time.perf_counter()
                elapsed_ms = round((t1 - t0) * 1000.0, 2)

                # Analyze trace events for this run
                event_summary = None
                if trace_enabled:
                    try:
                        # Get events since query start
                        events = []
                        if hasattr(trace_mgr, 'get_events'):
                            events = trace_mgr.get_events(since_index=start_index)

                        # Summarize events
                        if events and hasattr(trace_mgr, 'summarize_events'):
                            event_summary = trace_mgr.summarize_events(events, elapsed_ms)

                            if event_summary:
                                se_totals.append(event_summary.get("se_ms", 0.0))
                                fe_totals.append(event_summary.get("fe_ms", 0.0))

                                # Aggregate event counts
                                for name, count in event_summary.get("counts", {}).items():
                                    aggregated_event_counts[name] += count

                    except Exception as exc:
                        logger.debug("Failed to capture trace events: %s", exc)

                # Build run record
                run_record: Dict[str, Any] = {
                    "run": i + 1,
                    "execution_time_ms": elapsed_ms,
                    "row_count": result.get("row_count", 0) if isinstance(result, dict) else 0,
                    "cache_state": "cold" if (i == 0 and clear_cache) else "warm",
                }

                if event_summary:
                    run_record["trace_execution_ms"] = event_summary.get("total_ms", elapsed_ms)
                    run_record["storage_engine_ms"] = event_summary.get("se_ms", 0.0)
                    run_record["formula_engine_ms"] = event_summary.get("fe_ms", 0.0)
                    run_record["se_percent"] = event_summary.get("se_percent", 0.0)
                    run_record["fe_percent"] = event_summary.get("fe_percent", 0.0)

                results.append(run_record)

            # Calculate averages
            avg_exec_ms = round(
                sum(r["execution_time_ms"] for r in results) / len(results), 2
            ) if results else 0.0

            avg_se_ms = round(sum(se_totals) / len(se_totals), 2) if se_totals else 0.0
            avg_fe_ms = round(sum(fe_totals) / len(fe_totals), 2) if fe_totals else 0.0
            total_for_percent = avg_se_ms + avg_fe_ms or avg_exec_ms

            se_percent = round((avg_se_ms / total_for_percent) * 100.0, 1) if total_for_percent else 0.0
            fe_percent = round((avg_fe_ms / total_for_percent) * 100.0, 1) if total_for_percent else 0.0

            # Build output
            output: Dict[str, Any] = {
                "success": True,
                "query": query,
                "runs": results,
                "summary": {
                    "avg_execution_ms": avg_exec_ms,
                    "avg_se_ms": avg_se_ms,
                    "avg_fe_ms": avg_fe_ms,
                    "se_percent": se_percent,
                    "fe_percent": fe_percent,
                    "trace_backend": self._trace_backend or "none",
                },
                "notes": self._generate_analysis_notes(trace_enabled, se_totals),
            }

            if aggregated_event_counts:
                output["event_counts"] = dict(sorted(aggregated_event_counts.items()))

            # Add visualization data
            output["visualization"] = self._generate_visualization_data(results, avg_se_ms, avg_fe_ms)

            return output

        except Exception as exc:
            logger.error("Detailed query analysis failed: %s", exc)
            return {"success": False, "error": str(exc)}

        finally:
            # Stop trace
            if trace_enabled and trace_mgr:
                try:
                    trace_mgr.stop_trace()
                except Exception:
                    pass

    def batch_profile_queries(
        self,
        queries: List[Dict[str, str]],
        runs_per_query: int = 1,
        clear_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Profile multiple queries in a single trace session.

        Args:
            queries: List of query dicts with 'name' and 'query' keys
            runs_per_query: Number of runs per query
            clear_cache: Whether to clear cache before each query

        Returns:
            Dictionary with batch profiling results and comparative analysis
        """
        trace_mgr = self._get_trace_manager()
        trace_enabled = False

        if trace_mgr:
            try:
                if trace_mgr.start_trace():
                    trace_enabled = True
                    logger.info("Trace started for batch profiling")
            except Exception as exc:
                logger.debug("Failed to start trace: %s", exc)

        query_results: List[Dict[str, Any]] = []

        try:
            for query_def in queries:
                query_name = query_def.get("name", f"Query {len(query_results) + 1}")
                query = query_def.get("query", "")

                if not query:
                    logger.warning("Skipping empty query: %s", query_name)
                    continue

                logger.info("Profiling query: %s", query_name)

                # Analyze this query
                result = self.analyze_query_detailed(
                    query=query,
                    runs=runs_per_query,
                    clear_cache=clear_cache,
                    capture_query_plan=False,
                    event_timeout=30.0,
                )

                result["query_name"] = query_name
                query_results.append(result)

            # Generate comparative analysis
            comparative = self._generate_comparative_analysis(query_results)

            return {
                "success": True,
                "total_queries": len(query_results),
                "queries": query_results,
                "comparative_analysis": comparative,
                "trace_backend": self._trace_backend or "none",
            }

        except Exception as exc:
            logger.error("Batch profiling failed: %s", exc)
            return {"success": False, "error": str(exc)}

        finally:
            # Stop trace
            if trace_enabled and trace_mgr:
                try:
                    trace_mgr.stop_trace()
                except Exception:
                    pass

    def compare_query_performance(
        self,
        query_before: str,
        query_after: str,
        runs: int = 3,
    ) -> Dict[str, Any]:
        """
        Compare performance of two query versions.

        Args:
            query_before: Original query
            query_after: Optimized query
            runs: Number of runs per query

        Returns:
            Dictionary with before/after comparison and improvement metrics
        """
        logger.info("Comparing query performance (before vs after)")

        # Profile both queries
        before_result = self.analyze_query_detailed(query_before, runs=runs, clear_cache=True)
        after_result = self.analyze_query_detailed(query_after, runs=runs, clear_cache=True)

        if not (before_result.get("success") and after_result.get("success")):
            return {
                "success": False,
                "error": "One or both queries failed to execute",
                "before": before_result,
                "after": after_result,
            }

        # Calculate improvements
        before_summary = before_result.get("summary", {})
        after_summary = after_result.get("summary", {})

        before_time = before_summary.get("avg_execution_ms", 0.0)
        after_time = after_summary.get("avg_execution_ms", 0.0)

        improvement_ms = before_time - after_time
        improvement_percent = round((improvement_ms / before_time) * 100.0, 1) if before_time > 0 else 0.0

        before_se = before_summary.get("avg_se_ms", 0.0)
        after_se = after_summary.get("avg_se_ms", 0.0)
        se_improvement_ms = before_se - after_se

        before_fe = before_summary.get("avg_fe_ms", 0.0)
        after_fe = after_summary.get("avg_fe_ms", 0.0)
        fe_improvement_ms = before_fe - after_fe

        return {
            "success": True,
            "before": before_result,
            "after": after_result,
            "improvement": {
                "total_ms": round(improvement_ms, 2),
                "total_percent": improvement_percent,
                "se_ms": round(se_improvement_ms, 2),
                "fe_ms": round(fe_improvement_ms, 2),
                "verdict": self._get_performance_verdict(improvement_percent),
            },
            "visualization": self._generate_comparison_visualization(
                before_summary, after_summary
            ),
        }

    def _generate_analysis_notes(self, trace_enabled: bool, se_totals: List[float]) -> List[str]:
        """Generate human-readable notes about the analysis."""
        notes: List[str] = []

        if trace_enabled and se_totals:
            notes.append(
                f"{self._trace_backend.upper()} trace active - SE/FE breakdown available"
            )
        elif trace_enabled:
            notes.append(
                f"{self._trace_backend.upper()} trace active but events not captured. "
                "Power BI Desktop has limited trace support."
            )
        else:
            notes.append(
                "Trace not available - showing wall-clock timing only. "
                "SE/FE breakdown requires AMO/XMLA trace support."
            )

        return notes

    def _generate_visualization_data(
        self,
        runs: List[Dict[str, Any]],
        avg_se_ms: float,
        avg_fe_ms: float,
    ) -> Dict[str, Any]:
        """Generate data for waterfall chart visualization."""
        return {
            "type": "waterfall",
            "data": {
                "categories": ["Total", "Storage Engine", "Formula Engine"],
                "values": [
                    round(avg_se_ms + avg_fe_ms, 2),
                    round(avg_se_ms, 2),
                    round(avg_fe_ms, 2),
                ],
            },
            "run_timeline": [
                {
                    "run": r["run"],
                    "total": r.get("execution_time_ms", 0),
                    "se": r.get("storage_engine_ms", 0),
                    "fe": r.get("formula_engine_ms", 0),
                }
                for r in runs
            ],
        }

    def _generate_comparative_analysis(
        self, query_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comparative analysis across multiple queries."""
        # Extract execution times
        times = []
        for qr in query_results:
            if qr.get("success"):
                summary = qr.get("summary", {})
                times.append({
                    "name": qr.get("query_name", "Unknown"),
                    "avg_ms": summary.get("avg_execution_ms", 0.0),
                    "se_ms": summary.get("avg_se_ms", 0.0),
                    "fe_ms": summary.get("avg_fe_ms", 0.0),
                })

        # Sort by execution time (slowest first)
        times_sorted = sorted(times, key=lambda x: x["avg_ms"], reverse=True)

        # Identify bottlenecks
        bottlenecks = []
        if times_sorted:
            # Top 3 slowest queries
            for i, item in enumerate(times_sorted[:3]):
                bottlenecks.append({
                    "rank": i + 1,
                    "query_name": item["name"],
                    "total_ms": item["avg_ms"],
                    "se_ms": item["se_ms"],
                    "fe_ms": item["fe_ms"],
                    "primary_bottleneck": "Storage Engine" if item["se_ms"] > item["fe_ms"] else "Formula Engine",
                })

        return {
            "total_queries": len(query_results),
            "successful_queries": len(times),
            "top_bottlenecks": bottlenecks,
            "all_queries_ranked": times_sorted,
        }

    def _generate_comparison_visualization(
        self,
        before_summary: Dict[str, Any],
        after_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate visualization data for before/after comparison."""
        return {
            "type": "comparison_bars",
            "data": {
                "before": {
                    "total": before_summary.get("avg_execution_ms", 0.0),
                    "se": before_summary.get("avg_se_ms", 0.0),
                    "fe": before_summary.get("avg_fe_ms", 0.0),
                },
                "after": {
                    "total": after_summary.get("avg_execution_ms", 0.0),
                    "se": after_summary.get("avg_se_ms", 0.0),
                    "fe": after_summary.get("avg_fe_ms", 0.0),
                },
            },
        }

    def _get_performance_verdict(self, improvement_percent: float) -> str:
        """Get human-readable performance verdict."""
        if improvement_percent >= 50:
            return "Excellent - Major performance improvement"
        elif improvement_percent >= 20:
            return "Good - Significant improvement"
        elif improvement_percent >= 5:
            return "Moderate - Noticeable improvement"
        elif improvement_percent >= -5:
            return "Neutral - Similar performance"
        else:
            return "Regression - Performance degraded"

    def close(self) -> None:
        """Close trace manager and cleanup resources."""
        if self.trace_manager:
            try:
                self.trace_manager.close()
            except Exception:
                pass
            self.trace_manager = None
