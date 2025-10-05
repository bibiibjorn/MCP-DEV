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
    from Microsoft.AnalysisServices import TraceEventClass
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
        """Handle trace events."""
        try:
            event_data = {
                'event_class': str(e.EventClass) if hasattr(e, 'EventClass') else None,
                'duration_us': e.Duration if hasattr(e, 'Duration') and e.Duration is not None else 0,
                'duration_ms': (e.Duration / 1000.0) if hasattr(e, 'Duration') and e.Duration is not None else 0,
                'cpu_time_ms': e.CpuTime if hasattr(e, 'CpuTime') and e.CpuTime is not None else 0,
                'text_data': e.TextData if hasattr(e, 'TextData') else None,
                'timestamp': time.time()
            }
            self.trace_events.append(event_data)
        except Exception:
            pass

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
            logger.warning("SessionTrace not available")
            return False

        try:
            self.trace_events = []
            self.session_trace = self.amo_server.SessionTrace
            self.session_trace.OnEvent += self._trace_event_handler
            self.session_trace.Stopped += self._trace_stopped_handler
            self.session_trace.Start()
            self.trace_active = True
            logger.debug("SessionTrace started")
            return True

        except Exception as e:
            logger.error(f"Failed to start SessionTrace: {e}")
            return False

    def stop_session_trace(self):
        """Stop AMO SessionTrace."""
        if self.session_trace and self.trace_active:
            try:
                self.session_trace.Stop()
                self.session_trace.OnEvent -= self._trace_event_handler
                self.session_trace.Stopped -= self._trace_stopped_handler
                self.trace_active = False
                logger.debug("SessionTrace stopped")
            except Exception as e:
                logger.warning(f"Error stopping trace: {e}")

    def _analyze_trace_events(self) -> Dict[str, Any]:
        """
        Analyze collected trace events.

        Returns:
            Dictionary with SE/FE metrics
        """
        if not self.trace_events:
            return {
                'total_duration_ms': 0,
                'se_duration_ms': 0,
                'fe_duration_ms': 0,
                'se_queries': 0,
                'metrics_available': False
            }

        # Extract query end events
        query_end_events = [e for e in self.trace_events if e.get('event_class') == 'QueryEnd']
        se_query_end_events = [e for e in self.trace_events if 'VertiPaqSEQuery' in str(e.get('event_class'))]

        total_duration = sum(e['duration_ms'] for e in query_end_events)
        se_duration = sum(e['duration_ms'] for e in se_query_end_events)
        se_queries = len(se_query_end_events)
        fe_duration = max(0, total_duration - se_duration)

        return {
            'total_duration_ms': round(total_duration, 2),
            'se_duration_ms': round(se_duration, 2),
            'fe_duration_ms': round(fe_duration, 2),
            'se_queries': se_queries,
            'metrics_available': se_queries > 0 or se_duration > 0
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
                # Start trace
                if not self.start_session_trace():
                    raise Exception("Failed to start SessionTrace")

                time.sleep(0.1)  # Let trace initialize

                # Clear cache if requested
                if clear_cache:
                    self._clear_cache(executor)
                    time.sleep(0.2)

                # Execute query
                query_start = time.time()
                result = executor.validate_and_execute_dax(query, 0)
                query_time = (time.time() - query_start) * 1000

                # Wait for trace events
                time.sleep(0.15)
                self.stop_session_trace()

                # Analyze metrics
                metrics = self._analyze_trace_events()
                execution_time = metrics['total_duration_ms'] if metrics['total_duration_ms'] > 0 else query_time
                se_time = metrics['se_duration_ms']
                fe_time = max(0, execution_time - se_time)

                run_result = {
                    'run': run + 1,
                    'success': result.get('success', False),
                    'execution_time_ms': round(execution_time, 2),
                    'formula_engine_ms': round(fe_time, 2),
                    'storage_engine_ms': round(se_time, 2),
                    'storage_engine_queries': metrics['se_queries'],
                    'row_count': result.get('row_count', 0),
                    'metrics_available': metrics['metrics_available']
                }

                if execution_time > 0:
                    run_result['fe_percent'] = round((fe_time / execution_time) * 100, 1)
                    run_result['se_percent'] = round((se_time / execution_time) * 100, 1)

                results.append(run_result)
                logger.info(f"Run {run + 1}/{runs}: {execution_time:.2f}ms (SE: {se_time:.2f}ms, FE: {fe_time:.2f}ms)")

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
