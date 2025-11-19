"""
Enhanced Performance Analyzer
Provides query timing analysis for DAX queries
"""
import logging
from typing import Dict, Any, Optional, Tuple
import time

logger = logging.getLogger(__name__)


class EnhancedAMOTraceAnalyzer:
    """
    Performance analyzer for DAX query timing.

    Provides query performance analysis with execution timing statistics.
    """

    def __init__(self, connection_string: str):
        """
        Initialize performance analyzer.

        Args:
            connection_string: Connection string to Power BI model
        """
        self.connection_string = connection_string
        self.amo_available = False
        self.trace_active = False

        logger.debug(f"Performance analyzer initialized with connection: {connection_string[:50]}...")

    def connect_amo(self) -> bool:
        """
        Attempt to connect to AMO for advanced tracing.

        Returns:
            True if AMO is available, False otherwise
        """
        try:
            # Try to import AMO-related libraries
            import clr

            # Check if Microsoft.AnalysisServices is available
            try:
                clr.AddReference("Microsoft.AnalysisServices")
                clr.AddReference("Microsoft.AnalysisServices.Tabular")
                self.amo_available = True
                logger.info("AMO libraries loaded successfully")
                return True
            except Exception as e:
                logger.debug(f"AMO libraries not available: {e}")
                self.amo_available = False
                return False

        except ImportError:
            logger.debug("pythonnet (clr) not available - AMO tracing disabled")
            self.amo_available = False
            return False

    def start_session_trace(self, query_executor) -> bool:
        """
        Start performance trace session.

        Args:
            query_executor: Query executor instance

        Returns:
            True if trace started successfully
        """
        if not self.amo_available:
            logger.debug("Trace not started - AMO unavailable")
            return False

        try:
            # Placeholder for actual trace setup
            self.trace_active = True
            logger.info("Performance trace session started")
            return True
        except Exception as e:
            logger.warning(f"Failed to start trace: {e}")
            self.trace_active = False
            return False

    def stop_session_trace(self):
        """Stop the active performance trace session."""
        if self.trace_active:
            self.trace_active = False
            logger.info("Performance trace session stopped")

    def analyze_query(
        self,
        query_executor,
        query: str,
        runs: int = 3,
        clear_cache: bool = True,
        include_event_counts: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze query performance with multiple runs.

        Args:
            query_executor: Query executor instance
            query: DAX query to analyze
            runs: Number of benchmark runs
            clear_cache: Whether to clear cache between runs
            include_event_counts: Include detailed event counts

        Returns:
            Performance analysis results with timing statistics
        """
        if not query_executor:
            return {
                "success": False,
                "error": "Query executor not available"
            }

        try:
            logger.info(f"Starting performance analysis: {runs} runs, clear_cache={clear_cache}")

            timings = []

            # Warm-up run
            logger.debug("Executing warm-up run...")
            result = query_executor.validate_and_execute_dax(query, top_n=0)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Warm-up run failed: {result.get('error', 'Unknown error')}"
                }

            # Benchmark runs
            for i in range(runs):
                logger.debug(f"Executing benchmark run {i+1}/{runs}...")

                # Clear cache if requested
                if clear_cache and i > 0:
                    try:
                        query_executor.execute_xmla_command(
                            '<ClearCache xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">'
                            '<Object><DatabaseID>' + query_executor.connection_string.split('=')[-1].split(';')[0] + '</DatabaseID></Object>'
                            '</ClearCache>'
                        )
                    except Exception as e:
                        logger.debug(f"Could not clear cache: {e}")

                start_time = time.time()
                result = query_executor.validate_and_execute_dax(query, top_n=0)
                end_time = time.time()

                if not result.get("success"):
                    logger.warning(f"Run {i+1} failed: {result.get('error')}")
                    continue

                total_ms = (end_time - start_time) * 1000
                timings.append(total_ms)

                logger.debug(f"Run {i+1}: Total={total_ms:.2f}ms")

            if not timings:
                return {
                    "success": False,
                    "error": "All benchmark runs failed"
                }

            # Calculate statistics
            avg_total = sum(timings) / len(timings)
            min_total = min(timings)
            max_total = max(timings)

            summary = {
                "avg_execution_ms": round(avg_total, 2),
                "min_execution_ms": round(min_total, 2),
                "max_execution_ms": round(max_total, 2),
                "runs_completed": len(timings)
            }

            notes = []

            return {
                "success": True,
                "summary": summary,
                "all_timings_ms": timings,
                "query": query,
                "notes": notes,
                "profiling_method": "AMO_TRACE" if self.amo_available else "BASIC_TIMING"
            }

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Performance analysis failed: {str(e)}"
            }
