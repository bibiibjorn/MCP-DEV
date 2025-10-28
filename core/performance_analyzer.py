"""
Performance analyzer utilities for DAX queries.

This module provides a lightweight EnhancedAMOTraceAnalyzer used by the server
to analyze query performance. When AMO/xEvents are unavailable, it gracefully
falls back to basic timing using the provided query executor.
"""

import logging
import os
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# AMO import state is cached so repeated calls stay cheap
_AMO_IMPORT_LOCK = threading.RLock()
_AMO_IMPORT_READY: Optional[bool] = None
_AMO_TYPES: Dict[str, Any] = {}
_AMO_IMPORT_ERROR: Optional[str] = None


def _ensure_amo_environment() -> bool:
    """Load pythonnet + AMO assemblies once. Returns True on success."""
    global _AMO_IMPORT_READY, _AMO_TYPES, _AMO_IMPORT_ERROR
    with _AMO_IMPORT_LOCK:
        if _AMO_IMPORT_READY is not None:
            return bool(_AMO_IMPORT_READY)
        try:
            import clr  # type: ignore
        except Exception as exc:  # pragma: no cover - environment specific
            _AMO_IMPORT_READY = False
            _AMO_IMPORT_ERROR = f"pythonnet clr import failed: {exc}"
            logger.debug(_AMO_IMPORT_ERROR)
            return False

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(base_dir)
            dll_dir = os.path.join(root_dir, "lib", "dotnet")
            dlls = (
                "Microsoft.AnalysisServices.Core.dll",
                "Microsoft.AnalysisServices.dll",
                "Microsoft.AnalysisServices.Tabular.dll",
            )
            for name in dlls:
                path = os.path.join(dll_dir, name)
                if os.path.exists(path):
                    try:
                        clr.AddReference(path)  # type: ignore[attr-defined]
                    except Exception as add_exc:
                        logger.debug("Failed to add reference %s: %s", path, add_exc)
                else:
                    logger.debug("AMO DLL missing at %s", path)

            from Microsoft.AnalysisServices import Server as AmoServer  # type: ignore  # noqa: E402
            from Microsoft.AnalysisServices import TraceEventArgs, TraceEventClass  # type: ignore  # noqa: E402

            try:
                from Microsoft.AnalysisServices.Tabular import Server as TabularServer  # type: ignore  # noqa: E402
            except Exception:
                TabularServer = None

            _AMO_TYPES = {
                "AmoServer": AmoServer,
                "TabularServer": TabularServer,
                "TraceEventArgs": TraceEventArgs,
                "TraceEventClass": TraceEventClass,
            }
            _AMO_IMPORT_READY = True
            _AMO_IMPORT_ERROR = None
            return True
        except Exception as exc:  # pragma: no cover - environment specific
            _AMO_IMPORT_READY = False
            _AMO_IMPORT_ERROR = str(exc)
            logger.debug("Failed to initialize AMO environment: %s", exc)
            return False


class EnhancedAMOTraceAnalyzer:
    """Analyzer facade used by the server with optional AMO/xEvents support."""

    _TRACE_BUFFER_LIMIT = 5000
    _SE_EVENT_NAMES = {
        "VertiPaqSEQueryEnd",
        "VertiPaqSEQueryCacheMatch",
        "VertiPaqSEQueryCacheMiss",
        "QuerySubcube",
        "QuerySubcubeVerbose",
        "DirectQueryEnd",
    }

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.amo_server: Optional[Any] = None
        self.trace_active = False
        self._trace: Optional[Any] = None
        self._trace_handler = None
        self._trace_handler_attached = False
        self._session_id: Optional[str] = None
        self._event_buffer: List[Dict[str, Any]] = []
        self._event_lock = threading.RLock()

    # ---- AMO/xEvents wiring ----
    def _resolve_session_id(self, query_executor: Any) -> Optional[str]:
        connection = getattr(query_executor, "connection", None)
        if connection is None:
            return self._session_id
        try:
            session_id = getattr(connection, "SessionID", None)
        except Exception:
            session_id = None
        if session_id:
            self._session_id = str(session_id)
        return self._session_id

    def _get_session_trace(self) -> Optional[Any]:
        if not self.amo_server:
            return None
        try:
            trace = getattr(self.amo_server, "SessionTrace", None)
            return trace
        except Exception as exc:
            logger.debug("Failed to access SessionTrace: %s", exc)
            return None

    def _attach_trace_handler(self, trace: Any) -> None:
        if self._trace_handler_attached or trace is None:
            return

        def _on_event(sender, args):  # type: ignore[no-redef]
            self._handle_trace_event(args)

        self._trace_handler = _on_event
        try:
            trace.add_OnEvent(self._trace_handler)
            self._trace_handler_attached = True
            return
        except Exception as exc:
            logger.debug("add_OnEvent failed: %s", exc)
        try:
            trace.OnEvent += self._trace_handler  # type: ignore[attr-defined]
            self._trace_handler_attached = True
        except Exception as exc:
            logger.debug("Failed to attach trace handler via OnEvent: %s", exc)
            self._trace_handler = None

    def _detach_trace_handler(self) -> None:
        if not self._trace or not self._trace_handler_attached or not self._trace_handler:
            return
        try:
            self._trace.remove_OnEvent(self._trace_handler)
            self._trace_handler_attached = False
            self._trace_handler = None
            return
        except Exception as exc:
            logger.debug("remove_OnEvent failed: %s", exc)
        try:
            self._trace.OnEvent -= self._trace_handler  # type: ignore[attr-defined]
        except Exception as exc:
            logger.debug("Failed to detach trace handler via OnEvent: %s", exc)
        self._trace_handler_attached = False
        self._trace_handler = None

    def _handle_trace_event(self, args: Any) -> None:
        try:
            event_name = str(getattr(args, "EventClass", "") or "")
            session_id = str(getattr(args, "SessionID", "") or "")
            record = {
                "event": event_name,
                "session_id": session_id,
                "duration_ms": float(getattr(args, "Duration", 0) or 0),
                "cpu_time_ms": float(getattr(args, "CpuTime", 0) or 0),
                "event_subclass": int(getattr(args, "EventSubclass", 0) or 0),
                "request_id": str(getattr(args, "RequestID", "") or ""),
                "timestamp": getattr(args, "CurrentTime", None),
                "text": str(getattr(args, "TextData", "") or ""),
            }
        except Exception:
            return

        with self._event_lock:
            self._event_buffer.append(record)
            # Avoid unbounded growth across long sessions
            if len(self._event_buffer) > self._TRACE_BUFFER_LIMIT:
                excess = len(self._event_buffer) - self._TRACE_BUFFER_LIMIT
                del self._event_buffer[0:excess]

    def _snapshot_event_index(self) -> int:
        with self._event_lock:
            return len(self._event_buffer)

    def _events_since(self, index: int) -> Tuple[List[Dict[str, Any]], int]:
        with self._event_lock:
            if index <= 0:
                data = list(self._event_buffer)
            else:
                data = self._event_buffer[index:]
            return data, len(self._event_buffer)

    def _summarize_events(self, events: List[Dict[str, Any]], fallback_ms: float) -> Optional[Dict[str, Any]]:
        if not events:
            return None
        session_id = self._session_id or ""
        total_ms = None
        se_ms = 0.0
        counts: Dict[str, int] = defaultdict(int)
        for evt in events:
            if session_id and evt.get("session_id") and evt["session_id"] != session_id:
                continue
            name = evt.get("event") or ""
            counts[name] += 1
            if name == "QueryEnd":
                total_ms = float(evt.get("duration_ms") or 0)
            elif name in self._SE_EVENT_NAMES:
                se_ms += float(evt.get("duration_ms") or 0)

        if total_ms is None:
            total_ms = max(fallback_ms, 0.0)
        fe_ms = max(total_ms - se_ms, 0.0)
        return {
            "total_ms": round(total_ms, 2),
            "se_ms": round(se_ms, 2),
            "fe_ms": round(fe_ms, 2),
            "counts": dict(counts),
        }

    def connect_amo(self) -> bool:
        """Best-effort AMO connect. Returns False when unavailable."""
        if self.amo_server is not None:
            return True
        if not _ensure_amo_environment():
            logger.debug("AMO environment unavailable: %s", _AMO_IMPORT_ERROR)
            return False

        server_cls = _AMO_TYPES.get("TabularServer") or _AMO_TYPES.get("AmoServer")
        if not server_cls:
            logger.debug("AMO server class missing after import")
            return False

        try:
            server = server_cls()
            server.Connect(self.connection_string)
            self.amo_server = server
            logger.info("Connected to AMO using connection string")
            return True
        except Exception as exc:
            logger.warning("AMO connect failed: %s", exc)
            self.amo_server = None
            return False

    def start_session_trace(self, query_executor: Optional[Any] = None) -> bool:
        if not self.connect_amo():
            self.trace_active = False
            return False

        session_id = self._resolve_session_id(query_executor) or ""
        if not session_id:
            logger.debug("Cannot start trace without session id")
            self.trace_active = False
            return False

        trace = self._get_session_trace()
        if trace is None:
            logger.debug("SessionTrace not available on AMO server")
            self.trace_active = False
            return False

        self._attach_trace_handler(trace)
        self._trace = trace

        # Ensure a clean buffer for new runs
        with self._event_lock:
            self._event_buffer.clear()

        try:
            # Stop trace if already running
            if getattr(trace, "IsStarted", False):
                trace.Stop()

            # **CRITICAL FIX**: Subscribe to trace events
            # SessionTrace needs explicit event subscriptions!
            TraceEventClass = _AMO_TYPES.get("TraceEventClass")
            if TraceEventClass:
                try:
                    # Clear any existing event subscriptions
                    trace.Events.Clear()

                    # Subscribe to QueryEnd event (total query duration)
                    trace.Events.Add(TraceEventClass.QueryEnd)

                    # Subscribe to Storage Engine events
                    trace.Events.Add(TraceEventClass.VertiPaqSEQueryEnd)
                    trace.Events.Add(TraceEventClass.VertiPaqSEQueryCacheMatch)
                    trace.Events.Add(TraceEventClass.VertiPaqSEQueryCacheMiss)

                    # Subscribe to QuerySubcube events
                    trace.Events.Add(TraceEventClass.QuerySubcube)
                    trace.Events.Add(TraceEventClass.QuerySubcubeVerbose)

                    # Update the trace with new event subscriptions
                    trace.Update()

                    logger.debug("✓ Subscribed to 7 trace events")
                except Exception as e:
                    logger.warning(f"Failed to subscribe to trace events: {e}")
                    logger.debug("  This may indicate enum values don't match AS version")

            # Start the trace
            trace.Start()
            self.trace_active = True
            logger.info("✓ AMO SessionTrace started for session %s", session_id)
            return True
        except Exception as exc:
            logger.warning("✗ Failed to start SessionTrace: %s", exc)
            self.trace_active = False
            return False

    def stop_session_trace(self) -> None:
        self.trace_active = False
        if not self._trace:
            return
        try:
            if getattr(self._trace, "IsStarted", False):
                self._trace.Stop()
        except Exception as exc:
            logger.debug("Error stopping trace: %s", exc)
        finally:
            self._detach_trace_handler()

    def _ensure_trace_ready(self, query_executor: Any) -> bool:
        if not self.amo_server:
            return False

        self._resolve_session_id(query_executor)
        if not self.trace_active:
            # Attempt to auto-start the trace so callers don't have to invoke set_performance_trace first.
            started = self.start_session_trace(query_executor)
            if not started:
                return False

        trace = self._get_session_trace()
        if trace is None:
            return False

        self._attach_trace_handler(trace)
        self._trace = trace

        if not getattr(trace, "IsStarted", False):
            try:
                trace.Start()
            except Exception as exc:
                logger.debug("Could not start trace during analyze: %s", exc)
                return False
        return True

    # ---- Core API expected by server/agent_policy ----
    def analyze_query(
        self,
        query_executor,
        query: str,
        runs: int = 3,
        clear_cache: bool = True,
        include_event_counts: bool = False,
    ) -> Dict[str, Any]:
        """Time the query over N runs using the provided executor."""
        results: List[Dict[str, Any]] = []
        se_totals: List[float] = []
        fe_totals: List[float] = []
        trace_totals: List[float] = []
        aggregated_counts: Dict[str, int] = defaultdict(int)
        trace_enabled = self._ensure_trace_ready(query_executor)

        try:
            if clear_cache and hasattr(query_executor, "flush_cache"):
                try:
                    query_executor.flush_cache()
                except Exception:
                    pass

            run_count = max(1, int(runs or 1))
            for i in range(run_count):
                start_index = self._snapshot_event_index() if trace_enabled else 0

                t0 = time.perf_counter()
                res = query_executor.validate_and_execute_dax(query, 0, bypass_cache=False)
                t1 = time.perf_counter()
                elapsed = round((t1 - t0) * 1000.0, 2)

                event_summary = None
                if trace_enabled:
                    events, _ = self._events_since(start_index)
                    event_summary = self._summarize_events(events, elapsed)
                    if event_summary:
                        trace_total = event_summary["total_ms"]
                        trace_totals.append(trace_total)
                        se_totals.append(event_summary["se_ms"])
                        fe_totals.append(event_summary["fe_ms"])
                        if include_event_counts:
                            for name, count in event_summary["counts"].items():
                                aggregated_counts[name] += count

                run_record: Dict[str, Any] = {
                    "run": i + 1,
                    "execution_time_ms": elapsed,
                    "row_count": res.get("row_count", 0) if isinstance(res, dict) else None,
                    "cache_state": "cold" if (i == 0 and clear_cache) else "warm",
                }
                if event_summary:
                    run_record["trace_execution_ms"] = event_summary["total_ms"]
                    run_record["storage_engine_ms"] = event_summary["se_ms"]
                    run_record["formula_engine_ms"] = event_summary["fe_ms"]
                    if include_event_counts:
                        run_record["event_counts"] = event_summary["counts"]

                results.append(run_record)

            avg_exec_ms = round(
                sum(r.get("execution_time_ms", 0) for r in results) / len(results), 2
            ) if results else 0.0

            avg_trace_ms = round(sum(trace_totals) / len(trace_totals), 2) if trace_totals else 0.0
            avg_se_ms = round(sum(se_totals) / len(se_totals), 2) if se_totals else 0.0
            avg_fe_ms = round(sum(fe_totals) / len(fe_totals), 2) if fe_totals else 0.0
            total_for_percent = avg_trace_ms or avg_exec_ms
            se_percent = round((avg_se_ms / total_for_percent) * 100.0, 1) if total_for_percent else 0.0
            fe_percent = round((avg_fe_ms / total_for_percent) * 100.0, 1) if total_for_percent else 0.0

            notes: List[str] = []
            if trace_enabled and trace_totals:
                notes.append("AMO SessionTrace active; FE/SE metrics derived from xEvents")
            elif trace_enabled:
                notes.append("AMO SessionTrace active but no matching events captured; falling back to wall-clock timings")
            else:
                notes.append("AMO/xEvents not active; returning basic timing only")

            output: Dict[str, Any] = {
                "success": True,
                "query": query,
                "runs": results,
                "summary": {
                    "avg_execution_ms": avg_exec_ms,
                    "avg_trace_ms": avg_trace_ms,
                    "avg_se_ms": avg_se_ms,
                    "avg_fe_ms": avg_fe_ms,
                    "se_percent": se_percent,
                    "fe_percent": fe_percent,
                },
                "notes": notes,
            }

            if include_event_counts and aggregated_counts:
                output.setdefault("events", {})["counts"] = dict(sorted(aggregated_counts.items()))

            return output
        except Exception as exc:
            logger.error("Performance analysis failed: %s", exc)
            return {"success": False, "error": str(exc)}
