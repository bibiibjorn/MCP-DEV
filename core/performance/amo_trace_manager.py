"""
AMO Server.Traces-based trace manager for SE/FE timing capture.

This uses the AMO Trace object (not SessionTrace) which supports
explicit event subscriptions and proper trace configuration.
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)

# AMO import state
_AMO_IMPORT_LOCK = threading.RLock()
_AMO_IMPORT_READY: Optional[bool] = None
_AMO_TYPES: Dict[str, Any] = {}


def _ensure_amo_environment() -> bool:
    """Load pythonnet + AMO assemblies."""
    global _AMO_IMPORT_READY, _AMO_TYPES
    with _AMO_IMPORT_LOCK:
        if _AMO_IMPORT_READY is not None:
            return bool(_AMO_IMPORT_READY)
        try:
            import clr  # type: ignore
            import os

            base_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(base_dir))
            dll_dir = os.path.join(root_dir, "lib", "dotnet")

            dlls = [
                "Microsoft.AnalysisServices.Core.dll",
                "Microsoft.AnalysisServices.dll",
                "Microsoft.AnalysisServices.Tabular.dll",
            ]

            for dll in dlls:
                path = os.path.join(dll_dir, dll)
                if os.path.exists(path):
                    clr.AddReference(path)

            from Microsoft.AnalysisServices import Server, Trace, TraceEvent, TraceEventClass  # type: ignore

            _AMO_TYPES = {
                "Server": Server,
                "Trace": Trace,
                "TraceEvent": TraceEvent,
                "TraceEventClass": TraceEventClass,
            }
            _AMO_IMPORT_READY = True
            return True
        except Exception as exc:
            logger.debug("Failed to initialize AMO environment: %s", exc)
            _AMO_IMPORT_READY = False
            return False


class AmoTraceManager:
    """
    AMO Trace-based manager using Server.Traces collection.

    Unlike SessionTrace, this approach allows explicit event configuration
    and proper trace lifecycle management.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.server: Optional[Any] = None
        self.trace: Optional[Any] = None
        self.trace_id: Optional[str] = None
        self._event_buffer: List[Dict[str, Any]] = []
        self._event_lock = threading.RLock()
        self._trace_handler = None
        self._trace_handler_attached = False

    def connect(self) -> bool:
        """Connect to Analysis Services via AMO."""
        if not _ensure_amo_environment():
            logger.debug("AMO environment not available")
            return False

        Server = _AMO_TYPES.get("Server")
        if not Server:
            return False

        try:
            server = Server()
            server.Connect(self.connection_string)
            self.server = server
            logger.info("AMO Server connected")
            return True
        except Exception as exc:
            logger.warning("Failed to connect AMO server: %s", exc)
            return False

    def _handle_trace_event(self, args: Any) -> None:
        """Handle trace event callback."""
        try:
            event_class = getattr(args, "EventClass", None)
            event_name = str(event_class) if event_class else ""

            session_id = str(getattr(args, "SessionID", "") or "")

            try:
                duration_ms = float(getattr(args, "Duration", 0) or 0)
            except (TypeError, ValueError):
                duration_ms = 0.0

            try:
                cpu_time_ms = float(getattr(args, "CpuTime", 0) or 0)
            except (TypeError, ValueError):
                cpu_time_ms = 0.0

            record = {
                "event": event_name,
                "session_id": session_id,
                "duration_ms": duration_ms,
                "cpu_time_ms": cpu_time_ms,
                "event_subclass": int(getattr(args, "EventSubclass", 0) or 0),
                "request_id": str(getattr(args, "RequestID", "") or ""),
                "timestamp": getattr(args, "CurrentTime", None),
                "text": str(getattr(args, "TextData", "") or ""),
            }

            logger.debug("Trace event: %s (%.2fms)", event_name, duration_ms)

            with self._event_lock:
                self._event_buffer.append(record)

        except Exception as exc:
            logger.debug("Failed to parse trace event: %s", exc)

    def start_trace(self) -> bool:
        """Create and start AMO trace with event subscriptions."""
        if not self.server:
            if not self.connect():
                return False

        Trace = _AMO_TYPES.get("Trace")
        TraceEvent = _AMO_TYPES.get("TraceEvent")
        TraceEventClass = _AMO_TYPES.get("TraceEventClass")

        if not all([Trace, TraceEvent, TraceEventClass]):
            logger.warning("AMO Trace types not available")
            return False

        try:
            # Create trace
            self.trace_id = str(uuid.uuid4())
            trace_name = f"PowerBI_MCP_{self.trace_id[:8]}"

            # Add to server traces collection FIRST
            trace = self.server.Traces.Add(self.trace_id, trace_name)

            # Now configure event subscriptions via the Events collection
            # Add trace events (this is the TraceEventCollection, not EventHandlerList)
            event_collection = trace.Events
            event_collection.Add(TraceEventClass.QueryEnd)
            event_collection.Add(TraceEventClass.VertiPaqSEQueryEnd)
            event_collection.Add(TraceEventClass.VertiPaqSEQueryCacheMatch)
            event_collection.Add(TraceEventClass.VertiPaqSEQueryCacheMiss)
            event_collection.Add(TraceEventClass.DirectQueryEnd)

            logger.debug("Configured 5 trace events")

            # Attach event handler for OnEvent
            def _on_event(sender, args):
                self._handle_trace_event(args)

            self._trace_handler = _on_event
            trace.OnEvent += self._trace_handler
            self._trace_handler_attached = True

            logger.debug("Event handler attached")

            # Update server to persist trace configuration
            trace.Update()

            # Start trace
            trace.Start()

            self.trace = trace
            logger.info("AMO Trace started: %s", trace_name)
            return True

        except Exception as exc:
            logger.warning("Failed to start AMO trace: %s", exc)
            import traceback
            traceback.print_exc()
            return False

    def stop_trace(self) -> None:
        """Stop and remove trace."""
        if not self.trace:
            return

        try:
            if self.trace.IsStarted:
                self.trace.Stop()

            # Detach handler
            if self._trace_handler_attached and self._trace_handler:
                try:
                    self.trace.OnEvent -= self._trace_handler
                except Exception:
                    pass
                self._trace_handler_attached = False
                self._trace_handler = None

            # Remove from server
            if self.server and self.trace_id:
                try:
                    self.server.Traces.Remove(self.trace_id)
                except Exception:
                    pass

            logger.info("AMO trace stopped")
        except Exception as exc:
            logger.debug("Error stopping trace: %s", exc)
        finally:
            self.trace = None

    def get_events(self, since_index: int = 0) -> List[Dict[str, Any]]:
        """Get captured events since index."""
        with self._event_lock:
            if since_index <= 0:
                return list(self._event_buffer)
            else:
                return self._event_buffer[since_index:]

    def get_event_count(self) -> int:
        """Get total event count."""
        with self._event_lock:
            return len(self._event_buffer)

    def clear_events(self) -> None:
        """Clear event buffer."""
        with self._event_lock:
            self._event_buffer.clear()

    def summarize_events(self, events: List[Dict[str, Any]], fallback_ms: float) -> Dict[str, Any]:
        """Summarize events into SE/FE breakdown."""
        SE_EVENT_NAMES = {
            "VertiPaqSEQueryEnd",
            "VertiPaqSEQueryCacheMatch",
            "VertiPaqSEQueryCacheMiss",
            "DirectQueryEnd",
        }

        total_ms = None
        se_ms = 0.0
        counts: Dict[str, int] = defaultdict(int)

        for evt in events:
            name = evt.get("event") or ""
            counts[name] += 1

            if name == "QueryEnd":
                total_ms = float(evt.get("duration_ms") or 0)
            elif name in SE_EVENT_NAMES:
                se_ms += float(evt.get("duration_ms") or 0)

        if total_ms is None:
            total_ms = max(fallback_ms, 0.0)

        fe_ms = max(total_ms - se_ms, 0.0)

        return {
            "total_ms": round(total_ms, 2),
            "se_ms": round(se_ms, 2),
            "fe_ms": round(fe_ms, 2),
            "se_percent": round((se_ms / total_ms * 100) if total_ms > 0 else 0, 1),
            "fe_percent": round((fe_ms / total_ms * 100) if total_ms > 0 else 0, 1),
            "counts": dict(counts),
        }

    def close(self) -> None:
        """Close and cleanup."""
        self.stop_trace()

        if self.server:
            try:
                self.server.Disconnect()
            except Exception:
                pass
            self.server = None
