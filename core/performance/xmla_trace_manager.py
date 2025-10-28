"""
XMLA-based Extended Events trace manager for capturing SE/FE timing metrics.

This module provides an alternative to AMO SessionTrace using XMLA CreateObject
commands to create explicit trace definitions with better event control.
"""

import logging
import time
import threading
from collections import defaultdict
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)

# XMLA import state
_XMLA_IMPORT_LOCK = threading.RLock()
_XMLA_IMPORT_READY: Optional[bool] = None
_XMLA_TYPES: Dict[str, Any] = {}


def _ensure_xmla_environment() -> bool:
    """Load pythonnet + ADOMD assemblies for XMLA execution."""
    global _XMLA_IMPORT_READY, _XMLA_TYPES
    with _XMLA_IMPORT_LOCK:
        if _XMLA_IMPORT_READY is not None:
            return bool(_XMLA_IMPORT_READY)
        try:
            import clr  # type: ignore
            import os

            base_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(base_dir))
            dll_dir = os.path.join(root_dir, "lib", "dotnet")

            adomd_path = os.path.join(dll_dir, "Microsoft.AnalysisServices.AdomdClient.dll")
            if os.path.exists(adomd_path):
                clr.AddReference(adomd_path)

            from Microsoft.AnalysisServices.AdomdClient import AdomdConnection  # type: ignore

            _XMLA_TYPES = {"AdomdConnection": AdomdConnection}
            _XMLA_IMPORT_READY = True
            return True
        except Exception as exc:
            logger.debug("Failed to initialize XMLA environment: %s", exc)
            _XMLA_IMPORT_READY = False
            return False


class XmlaTraceManager:
    """
    XMLA-based trace manager using Extended Events.

    This approach creates explicit trace definitions via XMLA CreateObject,
    giving more control over event subscriptions than AMO SessionTrace.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection: Optional[Any] = None
        self.trace_id: Optional[str] = None
        self.trace_active = False
        self._event_buffer: List[Dict[str, Any]] = []
        self._event_lock = threading.RLock()

    def connect(self) -> bool:
        """Establish XMLA connection."""
        if not _ensure_xmla_environment():
            logger.debug("XMLA environment not available")
            return False

        AdomdConnection = _XMLA_TYPES.get("AdomdConnection")
        if not AdomdConnection:
            return False

        try:
            conn = AdomdConnection()
            conn.ConnectionString = self.connection_string
            conn.Open()
            self.connection = conn
            logger.info("XMLA connection established")
            return True
        except Exception as exc:
            logger.warning("Failed to establish XMLA connection: %s", exc)
            return False

    def _build_create_trace_xmla(self, trace_id: str) -> str:
        """
        Build XMLA command to create an Extended Events trace.

        This creates a session-level trace with the events we need for SE/FE analysis.
        """
        xmla = f"""
        <Create xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
            <ObjectDefinition>
                <Trace xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <ID>{trace_id}</ID>
                    <Name>PowerBI_MCP_Trace_{trace_id[:8]}</Name>
                    <Events>
                        <!-- Query completion event (QueryEnd = 10) -->
                        <Event>
                            <EventID>10</EventID>
                            <Columns>
                                <Column>EventClass</Column>
                                <Column>EventSubclass</Column>
                                <Column>CurrentTime</Column>
                                <Column>StartTime</Column>
                                <Column>EndTime</Column>
                                <Column>Duration</Column>
                                <Column>CpuTime</Column>
                                <Column>SessionID</Column>
                                <Column>TextData</Column>
                                <Column>RequestID</Column>
                            </Columns>
                        </Event>
                        <!-- Storage Engine events -->
                        <!-- VertiPaqSEQueryEnd = 83 -->
                        <Event>
                            <EventID>83</EventID>
                            <Columns>
                                <Column>EventClass</Column>
                                <Column>EventSubclass</Column>
                                <Column>CurrentTime</Column>
                                <Column>Duration</Column>
                                <Column>CpuTime</Column>
                                <Column>SessionID</Column>
                                <Column>RequestID</Column>
                            </Columns>
                        </Event>
                        <!-- VertiPaqSEQueryCacheMatch = 85 -->
                        <Event>
                            <EventID>85</EventID>
                            <Columns>
                                <Column>EventClass</Column>
                                <Column>Duration</Column>
                                <Column>SessionID</Column>
                                <Column>RequestID</Column>
                            </Columns>
                        </Event>
                        <!-- VertiPaqSEQueryCacheMiss = 86 -->
                        <Event>
                            <EventID>86</EventID>
                            <Columns>
                                <Column>EventClass</Column>
                                <Column>Duration</Column>
                                <Column>SessionID</Column>
                                <Column>RequestID</Column>
                            </Columns>
                        </Event>
                        <!-- DirectQueryEnd = 99 -->
                        <Event>
                            <EventID>99</EventID>
                            <Columns>
                                <Column>EventClass</Column>
                                <Column>Duration</Column>
                                <Column>CpuTime</Column>
                                <Column>SessionID</Column>
                                <Column>RequestID</Column>
                            </Columns>
                        </Event>
                    </Events>
                </Trace>
            </ObjectDefinition>
        </Create>
        """
        return xmla.strip()

    def _build_delete_trace_xmla(self, trace_id: str) -> str:
        """Build XMLA command to delete a trace."""
        xmla = f"""
        <Delete xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
            <Object>
                <TraceID>{trace_id}</TraceID>
            </Object>
        </Delete>
        """
        return xmla.strip()

    def start_trace(self) -> bool:
        """Start XMLA Extended Events trace."""
        if not self.connection:
            if not self.connect():
                return False

        # Generate unique trace ID
        self.trace_id = str(uuid.uuid4())

        try:
            # Create trace via XMLA
            xmla_command = self._build_create_trace_xmla(self.trace_id)

            command = self.connection.CreateCommand()
            command.CommandText = xmla_command
            command.ExecuteNonQuery()

            self.trace_active = True
            logger.info("XMLA trace started with ID: %s", self.trace_id[:8])
            return True

        except Exception as exc:
            logger.warning("Failed to start XMLA trace: %s", exc)
            self.trace_active = False
            return False

    def stop_trace(self) -> None:
        """Stop and delete XMLA trace."""
        if not self.trace_id or not self.connection:
            return

        try:
            xmla_command = self._build_delete_trace_xmla(self.trace_id)
            command = self.connection.CreateCommand()
            command.CommandText = xmla_command
            command.ExecuteNonQuery()

            logger.info("XMLA trace stopped: %s", self.trace_id[:8])
        except Exception as exc:
            logger.debug("Error stopping XMLA trace: %s", exc)
        finally:
            self.trace_active = False
            self.trace_id = None

    def get_trace_events(self, timeout: float = 30.0) -> List[Dict[str, Any]]:
        """
        Retrieve trace events via XMLA Discover command.

        Args:
            timeout: Maximum time to wait for events (seconds)

        Returns:
            List of captured trace events
        """
        if not self.connection or not self.trace_id:
            return []

        # TODO: Implement event retrieval via DISCOVER_TRACE_EVENT_CATEGORIES
        # or by reading trace file if configured

        logger.debug("Event retrieval via XMLA not yet implemented")
        return []

    def close(self) -> None:
        """Close XMLA connection and cleanup."""
        self.stop_trace()

        if self.connection:
            try:
                self.connection.Close()
            except Exception:
                pass
            self.connection = None
