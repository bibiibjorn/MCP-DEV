"""
Performance Analyzer for PBIXRay MCP Server

Provides advanced query performance analysis with Storage Engine (SE) and
Formula Engine (FE) breakdown using AMO SessionTrace.
"""

import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to load AMO
AMO_AVAILABLE = False
AMOServer = None
TraceEventClass = None

try:
    import clr
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    core_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
    amo_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.dll")
    tabular_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")

    if os.path.exists(core_dll):
        clr.AddReference(core_dll)
    if os.path.exists(amo_dll):
        clr.AddReference(amo_dll)
    if os.path.exists(tabular_dll):
        clr.AddReference(tabular_dll)

    from Microsoft.AnalysisServices.Tabular import Server as AMOServer
    from Microsoft.AnalysisServices import TraceEventClass, Trace, TraceEvent
    AMO_AVAILABLE = True
    logger.info("AMO available for performance analysis")

except Exception as e:
    logger.warning(f"AMO not available: {e}")


class EnhancedAMOTraceAnalyzer:
    """
    Enhanced performance analyzer using AMO SessionTrace.

    Provides detailed breakdown of:
    - Total query execution time
    - Storage Engine (SE) time
    - Formula Engine (FE) time
    - SE query count
    - Multiple run averaging
    """

    def __init__(self, connection_string: str):
        """
        Initialize analyzer.

        Args:
            connection_string: Connection string for Power BI Desktop
        """
        self.connection_string = connection_string
        self.amo_server = None
        self.trace_events = []
        self.session_trace = None
        self.trace_active = False

    def connect_amo(self) -> bool:
        """
        Connect to Analysis Services using AMO.

        Returns:
            True if connected, False otherwise
        """
        if not AMO_AVAILABLE:
            logger.warning("AMO not available")
            return False

        try:
            self.amo_server = AMOServer()
            self.amo_server.Connect(self.connection_string)
            logger.info(f"AMO connected: {self.amo_server.Name}")
            return True

        except Exception as e:
            logger.error(f"AMO connection failed: {e}")
            return False

    def _trace_event_handler(self, sender, e):
        """
        Handle trace events.

        CRITICAL: This runs on a separate thread. Keep it lightweight to avoid
        blocking the trace and losing events.
        """
        try:
            event_class_value = int(e.EventClass) if hasattr(e, 'EventClass') else 0
            event_class_name = str(e.EventClass) if hasattr(e, 'EventClass') else 'Unknown'

            # Only capture relevant events to reduce overhead
            # QueryEnd=10, VertiPaqSEQueryBegin=82, VertiPaqSEQueryEnd=83, CacheMatch=85
            if event_class_value not in [10, 82, 83, 85]:
                return

            # Extract duration - CRITICAL: Duration is in microseconds, convert to ms
            duration_us = e.Duration if hasattr(e, 'Duration') and e.Duration is not None else 0
            duration_ms = duration_us / 1000.0 if duration_us > 0 else 0

            event_data = {
                'event_class': event_class_name,
                'event_class_value': event_class_value,
                'event_subclass': e.EventSubclass if hasattr(e, 'EventSubclass') else None,
                'duration_us': duration_us,
                'duration_ms': duration_ms,
                'cpu_time_ms': e.CpuTime if hasattr(e, 'CpuTime') and e.CpuTime is not None else 0,
                'text_data': str(e.TextData)[:200] if hasattr(e, 'TextData') and e.TextData else None,  # Truncate for performance
                'timestamp': time.time(),
                'current_time': e.CurrentTime if hasattr(e, 'CurrentTime') else None,
                'start_time': e.StartTime if hasattr(e, 'StartTime') else None
            }

            self.trace_events.append(event_data)

            # Log important events (QueryEnd and VertiPaqSEQueryEnd)
            if event_class_value in [10, 83]:
                logger.info(f"✓ Captured {event_class_name} (value={event_class_value}, duration={duration_ms:.2f}ms)")

        except Exception as ex:
            logger.error(f"Error in trace handler: {ex}", exc_info=True)

    def _trace_stopped_handler(self, sender, e):
        """Handle trace stopped event."""
        self.trace_active = False
        logger.debug("Trace stopped")

    def start_session_trace(self) -> bool:
        """
        Start AMO SessionTrace.

        Returns:
            True if started successfully
        """
        if not self.amo_server or not hasattr(self.amo_server, 'SessionTrace'):
            logger.error("SessionTrace not available - AMO server not connected")
            return False

        try:
            # Clear previous events
            self.trace_events = []

            # Get SessionTrace instance
            self.session_trace = self.amo_server.SessionTrace

            # Attach event handlers BEFORE starting
            self.session_trace.OnEvent += self._trace_event_handler
            self.session_trace.Stopped += self._trace_stopped_handler

            # Start the trace
            self.session_trace.Start()
            self.trace_active = True

            logger.info(f"✓ SessionTrace started successfully (Session ID: {self.amo_server.SessionID if hasattr(self.amo_server, 'SessionID') else 'N/A'})")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to start SessionTrace: {e}", exc_info=True)
            self.trace_active = False
            return False

    def stop_session_trace(self):
        """Stop AMO SessionTrace and detach event handlers."""
        if self.session_trace and self.trace_active:
            try:
                # Stop the trace
                self.session_trace.Stop()

                # Detach event handlers AFTER stopping
                self.session_trace.OnEvent -= self._trace_event_handler
                self.session_trace.Stopped -= self._trace_stopped_handler

                self.trace_active = False

                events_captured = len(self.trace_events)
                logger.info(f"✓ SessionTrace stopped - Captured {events_captured} events")

            except Exception as e:
                logger.error(f"✗ Error stopping trace: {e}", exc_info=True)
                self.trace_active = False

    def _analyze_trace_events(self) -> Dict[str, Any]:
        """
        Analyze collected trace events using proper event class codes.

        Event Class Values:
        - QueryEnd = 10
        - VertiPaqSEQueryBegin = 82
        - VertiPaqSEQueryEnd = 83

        Returns:
            Dictionary with SE/FE metrics
        """
        if not self.trace_events:
            return {
                'total_duration_ms': 0,
                'se_duration_ms': 0,
                'fe_duration_ms': 0,
                'se_queries': 0,
                'se_cache_matches': 0,
                'metrics_available': False,
                'total_events': 0
            }

        # Filter events by event class value (more reliable than string matching)
        query_end_events = [e for e in self.trace_events if e.get('event_class_value') == 10]  # QueryEnd
        se_query_end_events = [e for e in self.trace_events if e.get('event_class_value') == 83]  # VertiPaqSEQueryEnd
        se_query_begin_events = [e for e in self.trace_events if e.get('event_class_value') == 82]  # VertiPaqSEQueryBegin
        se_cache_match_events = [e for e in self.trace_events if e.get('event_class_value') == 85]  # VertiPaqSEQueryCacheMatch

        # Calculate total duration from QueryEnd events
        total_duration = sum(e['duration_ms'] for e in query_end_events)

        # Calculate SE duration from VertiPaqSEQueryEnd events
        se_duration = sum(e['duration_ms'] for e in se_query_end_events)

        # Count SE queries
        se_queries = len(se_query_end_events)
        se_cache_matches = len(se_cache_match_events)

        # FE duration is total minus SE
        fe_duration = max(0, total_duration - se_duration)

        logger.debug(f"Trace analysis: {len(self.trace_events)} total events, "
                    f"{len(query_end_events)} QueryEnd, {se_queries} SE queries")

        return {
            'total_duration_ms': round(total_duration, 2),
            'se_duration_ms': round(se_duration, 2),
            'fe_duration_ms': round(fe_duration, 2),
            'se_queries': se_queries,
            'se_cache_matches': se_cache_matches,
            'metrics_available': total_duration > 0,
            'total_events': len(self.trace_events),
            'query_end_events': len(query_end_events),
            'se_end_events': se_queries
        }

    def _clear_cache(self, executor):
        """Clear Analysis Services cache."""
        xmla_clear = '<ClearCache xmlns="http://schemas.microsoft.com/analysisservices/2003/engine"><Object><DatabaseID></DatabaseID></Object></ClearCache>'
        try:
            # Import ADOMD command
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand
            cmd = AdomdCommand(xmla_clear, executor.connection)
            cmd.ExecuteNonQuery()
            logger.debug("Cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    def analyze_query(self, executor, query: str, runs: int = 3, clear_cache: bool = True) -> Dict[str, Any]:
        """
        Analyze query performance with multiple runs.

        Args:
            executor: Query executor instance
            query: DAX query to analyze
            runs: Number of runs to average
            clear_cache: Whether to clear cache between runs

        Returns:
            Performance analysis results
        """
        if not self.amo_server or not AMO_AVAILABLE:
            return self._fallback_analysis(executor, query, runs, clear_cache)

        results = []

        for run in range(runs):
            try:
                logger.info(f"========== Run {run + 1}/{runs} ==========")

                # Start trace BEFORE anything else
                if not self.start_session_trace():
                    raise Exception("Failed to start SessionTrace - AMO not available")

                # CRITICAL: Let trace fully initialize before query
                time.sleep(0.2)  # Increased from 0.1
                logger.info("Trace initialized, ready to execute query")

                # Clear cache if requested
                if clear_cache:
                    logger.info("Clearing cache...")
                    self._clear_cache(executor)
                    time.sleep(0.3)  # Increased wait after cache clear

                # Execute query
                logger.info(f"Executing DAX query...")
                query_start = time.time()
                result = executor.validate_and_execute_dax(query, 0)
                query_time = (time.time() - query_start) * 1000
                logger.info(f"Query completed in {query_time:.2f}ms (wall clock)")

                # CRITICAL: Wait longer for trace events to be fully captured
                # Events are generated asynchronously by the engine
                time.sleep(0.5)  # Increased from 0.15 to 0.5

                # Stop trace and collect events
                self.stop_session_trace()

                # Analyze metrics
                metrics = self._analyze_trace_events()
                execution_time = metrics['total_duration_ms'] if metrics['total_duration_ms'] > 0 else query_time
                se_time = metrics['se_duration_ms']
                fe_time = max(0, execution_time - se_time)

                # Diagnostics
                logger.info(f"Event Analysis: {metrics.get('total_events', 0)} total, "
                           f"{metrics.get('query_end_events', 0)} QueryEnd, "
                           f"{metrics.get('se_end_events', 0)} VertiPaqSEQueryEnd")

                run_result = {
                    'run': run + 1,
                    'success': result.get('success', False),
                    'execution_time_ms': round(execution_time, 2),
                    'formula_engine_ms': round(fe_time, 2),
                    'storage_engine_ms': round(se_time, 2),
                    'storage_engine_queries': metrics['se_queries'],
                    'storage_engine_cache_matches': metrics.get('se_cache_matches', 0),
                    'row_count': result.get('row_count', 0),
                    'metrics_available': metrics['metrics_available'],
                    'debug_total_events': metrics.get('total_events', 0),
                    'debug_query_end_events': metrics.get('query_end_events', 0),
                    'debug_se_end_events': metrics.get('se_end_events', 0)
                }

                if execution_time > 0:
                    run_result['fe_percent'] = round((fe_time / execution_time) * 100, 1)
                    run_result['se_percent'] = round((se_time / execution_time) * 100, 1)

                results.append(run_result)

                if metrics['metrics_available']:
                    logger.info(f"✓ Run {run + 1}/{runs}: Total={execution_time:.2f}ms, FE={fe_time:.2f}ms ({run_result.get('fe_percent', 0)}%), SE={se_time:.2f}ms ({run_result.get('se_percent', 0)}%), SE Queries={metrics['se_queries']}")
                else:
                    logger.warning(f"✗ Run {run + 1}/{runs}: No trace events captured! Used wall clock time: {query_time:.2f}ms")

            except Exception as e:
                logger.error(f"Run {run+1} error: {e}")
                self.stop_session_trace()
                results.append({
                    'run': run + 1,
                    'success': False,
                    'error': str(e)
                })

        # Calculate summary statistics
        successful = [r for r in results if r.get('success')]

        if successful:
            exec_times = [r['execution_time_ms'] for r in successful]
            fe_times = [r.get('formula_engine_ms', 0) for r in successful]
            se_times = [r.get('storage_engine_ms', 0) for r in successful]

            avg_exec = sum(exec_times) / len(exec_times)
            avg_fe = sum(fe_times) / len(fe_times)
            avg_se = sum(se_times) / len(se_times)

            summary = {
                'total_runs': runs,
                'successful_runs': len(successful),
                'avg_execution_ms': round(avg_exec, 2),
                'min_execution_ms': round(min(exec_times), 2),
                'max_execution_ms': round(max(exec_times), 2),
                'avg_formula_engine_ms': round(avg_fe, 2),
                'avg_storage_engine_ms': round(avg_se, 2),
                'cache_cleared': clear_cache
            }

            if avg_exec > 0:
                summary['fe_percent'] = round((avg_fe / avg_exec) * 100, 1)
                summary['se_percent'] = round((avg_se / avg_exec) * 100, 1)

        else:
            summary = {
                'total_runs': runs,
                'successful_runs': 0,
                'error': 'All runs failed'
            }

        return {
            'success': len(successful) > 0,
            'runs': results,
            'summary': summary,
            'query': query
        }

    def _fallback_analysis(self, executor, query: str, runs: int, clear_cache: bool) -> Dict[str, Any]:
        """
        Fallback analysis without AMO trace (basic timing only).

        Args:
            executor: Query executor
            query: DAX query
            runs: Number of runs
            clear_cache: Whether to clear cache

        Returns:
            Basic performance results
        """
        logger.info("Using fallback analysis (no SE/FE breakdown)")
        results = []

        for run in range(runs):
            if clear_cache:
                self._clear_cache(executor)
                time.sleep(0.5)

            start_time = time.time()
            result = executor.validate_and_execute_dax(query, 0)
            execution_time = (time.time() - start_time) * 1000

            results.append({
                'run': run + 1,
                'success': result.get('success', False),
                'execution_time_ms': round(execution_time, 2),
                'row_count': result.get('row_count', 0),
                'metrics_available': False
            })

        successful = [r for r in results if r.get('success')]
        exec_times = [r['execution_time_ms'] for r in successful] if successful else [0]

        return {
            'success': len(successful) > 0,
            'runs': results,
            'summary': {
                'total_runs': runs,
                'successful_runs': len(successful),
                'avg_execution_ms': round(sum(exec_times) / len(exec_times), 2) if exec_times else 0,
                'note': 'AMO not available - SE/FE breakdown not available'
            },
            'query': query
        }

    def disconnect(self):
        """Disconnect from AMO server."""
        self.stop_session_trace()
        if self.amo_server:
            try:
                self.amo_server.Disconnect()
                logger.info("AMO disconnected")
            except:
                pass
