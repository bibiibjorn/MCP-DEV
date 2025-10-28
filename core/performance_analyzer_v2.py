"""
Enhanced Performance Analyzer v2 - xEvents Integration

This module integrates the comprehensive XEventTraceManager for accurate
SE/FE timing while maintaining backward compatibility with the existing API.

Primary Features:
- XMLA-based Extended Events tracing
- ExecutionStatistics event for authoritative FE timing
- VertiPaqSEQueryEnd for detailed SE breakdown
- Automatic fallback to legacy SessionTrace or basic timing

Usage:
    analyzer = EnhancedPerformanceAnalyzer(connection_string)
    results = analyzer.analyze_query(query_executor, "EVALUATE Sales", runs=3)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import new XEvent manager
try:
    from .xevent_trace_manager import XEventTraceManager, QueryPerformanceMetrics
    XEVENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"XEventTraceManager not available: {e}")
    XEVENT_AVAILABLE = False

# Fallback to legacy analyzer
try:
    from .performance_analyzer import EnhancedAMOTraceAnalyzer
    LEGACY_ANALYZER_AVAILABLE = True
except ImportError:
    LEGACY_ANALYZER_AVAILABLE = False


class EnhancedPerformanceAnalyzer:
    """
    Unified performance analyzer with xEvents support

    Automatically selects best available tracing method:
    1. XMLA-based xEvents (most accurate)
    2. AMO SessionTrace (legacy fallback)
    3. Basic timing (no trace)
    """

    def __init__(self, connection_string: str):
        """
        Initialize analyzer

        Args:
            connection_string: Connection string to Analysis Services
        """
        self.connection_string = connection_string
        self.xevent_manager: Optional[XEventTraceManager] = None
        self.legacy_analyzer: Optional[Any] = None
        self.tracing_mode = "none"

        # Try to initialize xEvent manager first
        if XEVENT_AVAILABLE:
            try:
                self.xevent_manager = XEventTraceManager(connection_string)
                if self.xevent_manager.connect():
                    self.tracing_mode = "xevents"
                    logger.info("Using XEvent trace manager for performance analysis")
                else:
                    self.xevent_manager = None
            except Exception as e:
                logger.debug(f"Failed to initialize XEventTraceManager: {e}")
                self.xevent_manager = None

        # Fallback to legacy AMO SessionTrace
        if not self.xevent_manager and LEGACY_ANALYZER_AVAILABLE:
            try:
                self.legacy_analyzer = EnhancedAMOTraceAnalyzer(connection_string)
                if self.legacy_analyzer.connect_amo():
                    self.tracing_mode = "amo_session"
                    logger.info("Using AMO SessionTrace for performance analysis")
                else:
                    self.legacy_analyzer = None
            except Exception as e:
                logger.debug(f"Failed to initialize legacy analyzer: {e}")
                self.legacy_analyzer = None

        if self.tracing_mode == "none":
            logger.warning("No tracing available - will use basic timing only")

    def analyze_query(
        self,
        query_executor: Any,
        query: str,
        runs: int = 3,
        clear_cache: bool = True,
        include_event_counts: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze DAX query performance with SE/FE breakdown

        Args:
            query_executor: Query executor instance
            query: DAX query to analyze
            runs: Number of execution runs
            clear_cache: Whether to clear cache before first run
            include_event_counts: Include detailed event counts

        Returns:
            Dictionary with performance metrics and breakdown
        """
        # Use xEvent manager if available (most accurate)
        if self.xevent_manager:
            return self._analyze_with_xevents(
                query_executor, query, runs, clear_cache, include_event_counts
            )

        # Fallback to legacy AMO SessionTrace
        if self.legacy_analyzer:
            return self._analyze_with_legacy(
                query_executor, query, runs, clear_cache, include_event_counts
            )

        # Last resort: basic timing only
        return self._analyze_basic(query_executor, query, runs, clear_cache)

    def _analyze_with_xevents(
        self,
        query_executor: Any,
        query: str,
        runs: int,
        clear_cache: bool,
        include_event_counts: bool,
    ) -> Dict[str, Any]:
        """Analyze using XMLA xEvents (most accurate method)"""
        try:
            # Capture metrics using xEvent manager
            metrics_list = self.xevent_manager.capture_query_metrics(
                query=query,
                query_executor=query_executor,
                runs=runs,
                clear_cache=clear_cache
            )

            if not metrics_list:
                logger.warning("No metrics captured, falling back")
                return self._analyze_basic(query_executor, query, runs, clear_cache)

            # Convert to server-expected format
            results = []
            for i, metrics in enumerate(metrics_list):
                run_record = {
                    "run": i + 1,
                    "execution_time_ms": metrics.total_duration_ms,
                    "trace_execution_ms": metrics.total_duration_ms,
                    "storage_engine_ms": metrics.storage_engine_ms,
                    "formula_engine_ms": metrics.formula_engine_ms,
                    "storage_engine_cpu_ms": metrics.storage_engine_cpu_ms,
                    "formula_engine_cpu_ms": metrics.formula_engine_cpu_ms,
                    "row_count": metrics.rows_returned,
                    "cache_state": metrics.cache_state,
                    "se_query_count": metrics.se_query_count,
                    "se_cache_hits": metrics.se_cache_hits,
                    "se_cache_misses": metrics.se_cache_misses,
                }

                if include_event_counts:
                    run_record["event_counts"] = {
                        "VertiPaqSEQueryEnd": metrics.se_query_count,
                        "VertiPaqSEQueryCacheMatch": metrics.se_cache_hits,
                        "VertiPaqSEQueryCacheMiss": metrics.se_cache_misses,
                    }

                results.append(run_record)

            # Calculate averages
            avg_total_ms = sum(r["execution_time_ms"] for r in results) / len(results)
            avg_se_ms = sum(r["storage_engine_ms"] for r in results) / len(results)
            avg_fe_ms = sum(r["formula_engine_ms"] for r in results) / len(results)

            se_percent = (avg_se_ms / avg_total_ms * 100) if avg_total_ms > 0 else 0
            fe_percent = (avg_fe_ms / avg_total_ms * 100) if avg_total_ms > 0 else 0

            # Parallelism factor from first cold run
            parallelism = metrics_list[0].parallelism_factor if metrics_list else 0

            return {
                "success": True,
                "query": query[:200],
                "runs": len(results),
                "results": results,
                "average_execution_ms": round(avg_total_ms, 2),
                "average_storage_engine_ms": round(avg_se_ms, 2),
                "average_formula_engine_ms": round(avg_fe_ms, 2),
                "storage_engine_percent": round(se_percent, 1),
                "formula_engine_percent": round(fe_percent, 1),
                "parallelism_factor": round(parallelism, 2),
                "tracing_method": "xevents_xmla",
                "total_se_queries": sum(r["se_query_count"] for r in results),
                "total_cache_hits": sum(r["se_cache_hits"] for r in results),
                "total_cache_misses": sum(r["se_cache_misses"] for r in results),
            }

        except Exception as e:
            logger.error(f"xEvent analysis failed: {e}", exc_info=True)
            return self._analyze_basic(query_executor, query, runs, clear_cache)

    def _analyze_with_legacy(
        self,
        query_executor: Any,
        query: str,
        runs: int,
        clear_cache: bool,
        include_event_counts: bool,
    ) -> Dict[str, Any]:
        """Analyze using legacy AMO SessionTrace"""
        try:
            result = self.legacy_analyzer.analyze_query(
                query_executor=query_executor,
                query=query,
                runs=runs,
                clear_cache=clear_cache,
                include_event_counts=include_event_counts
            )

            result["tracing_method"] = "amo_session_trace"
            return result

        except Exception as e:
            logger.error(f"Legacy analysis failed: {e}", exc_info=True)
            return self._analyze_basic(query_executor, query, runs, clear_cache)

    def _analyze_basic(
        self,
        query_executor: Any,
        query: str,
        runs: int,
        clear_cache: bool
    ) -> Dict[str, Any]:
        """Basic timing without trace (fallback)"""
        import time

        if clear_cache and hasattr(query_executor, 'flush_cache'):
            try:
                query_executor.flush_cache()
            except Exception:
                pass

        results = []

        for run_num in range(runs):
            t0 = time.perf_counter()

            try:
                res = query_executor.validate_and_execute_dax(query, 0, bypass_cache=False)
                row_count = res.get("row_count", 0) if isinstance(res, dict) else 0
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                row_count = 0

            t1 = time.perf_counter()
            elapsed_ms = (t1 - t0) * 1000

            results.append({
                "run": run_num + 1,
                "execution_time_ms": round(elapsed_ms, 2),
                "row_count": row_count,
                "cache_state": "cold" if (run_num == 0 and clear_cache) else "warm",
            })

        avg_ms = sum(r["execution_time_ms"] for r in results) / len(results)

        return {
            "success": True,
            "query": query[:200],
            "runs": len(results),
            "results": results,
            "average_execution_ms": round(avg_ms, 2),
            "tracing_method": "basic_timing",
            "note": "SE/FE breakdown unavailable - tracing not supported",
        }

    def start_trace(self, query_executor: Optional[Any] = None) -> bool:
        """
        Manually start trace (usually automatic)

        Args:
            query_executor: Query executor instance

        Returns:
            True if trace started
        """
        if self.xevent_manager:
            return self.xevent_manager.start_trace()

        if self.legacy_analyzer:
            return self.legacy_analyzer.start_session_trace(query_executor)

        return False

    def stop_trace(self) -> None:
        """Stop active trace"""
        if self.xevent_manager:
            self.xevent_manager.stop_trace()

        if self.legacy_analyzer:
            self.legacy_analyzer.stop_session_trace()

    def close(self) -> None:
        """Cleanup resources"""
        if self.xevent_manager:
            self.xevent_manager.close()

        self.xevent_manager = None
        self.legacy_analyzer = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Maintain backward compatibility with existing code
def create_performance_analyzer(connection_string: str) -> EnhancedPerformanceAnalyzer:
    """
    Factory function to create performance analyzer

    Args:
        connection_string: Connection string to Analysis Services

    Returns:
        EnhancedPerformanceAnalyzer instance
    """
    return EnhancedPerformanceAnalyzer(connection_string)
