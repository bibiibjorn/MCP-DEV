"""
Extended Events (xEvents) Trace Manager for Analysis Services

This module provides comprehensive xEvent tracing for DAX query performance analysis
using XMLA commands. It captures Storage Engine (SE) and Formula Engine (FE) timings
accurately using ExecutionStatistics, VertiPaqSEQueryEnd, and QueryEnd events.

Based on research from:
- Microsoft Learn: Analysis Services Extended Events
- DAX Studio implementation
- SQLBI best practices
- Chris Webb's blog on xEvents
"""

import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Complete performance metrics for a DAX query"""
    query_text: str
    total_duration_ms: float
    storage_engine_ms: float
    formula_engine_ms: float
    storage_engine_cpu_ms: float
    formula_engine_cpu_ms: float
    se_query_count: int
    se_cache_hits: int
    se_cache_misses: int
    rows_returned: int
    cache_state: str = "unknown"  # cold, warm
    se_percentage: float = 0.0
    fe_percentage: float = 0.0
    parallelism_factor: float = 0.0
    execution_metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate derived metrics"""
        total = self.total_duration_ms or 1.0  # Avoid division by zero
        self.se_percentage = round((self.storage_engine_ms / total) * 100, 1)
        self.fe_percentage = round((self.formula_engine_ms / total) * 100, 1)

        # Parallelism factor: SE CPU / SE Duration (rough indicator of parallelization)
        if self.storage_engine_ms > 0:
            self.parallelism_factor = round(
                self.storage_engine_cpu_ms / self.storage_engine_ms, 2
            )


class XEventTraceManager:
    """
    Manages Extended Events traces for Analysis Services using XMLA

    Provides accurate SE/FE timing breakdown using:
    - ExecutionStatistics: Authoritative FE timing (modern approach)
    - VertiPaqSEQueryEnd: Storage engine query timings
    - QueryEnd: Total query duration
    - DirectQueryEnd: DirectQuery source timings
    """

    # Event types to capture
    TRACE_EVENTS = [
        "QueryEnd",                    # Total query timing
        "VertiPaqSEQueryEnd",         # Storage engine queries
        "VertiPaqSEQueryCacheMatch",  # Cache hits
        "VertiPaqSEQueryCacheMiss",   # Cache misses
        "ExecutionStatistics",         # Authoritative FE/SE breakdown
        "DirectQueryEnd",              # DirectQuery timings
        "QuerySubcube",                # Subcube operations
        "QuerySubcubeVerbose",         # Detailed subcube info
    ]

    def __init__(self, connection_string: str):
        """
        Initialize trace manager

        Args:
            connection_string: ADOMD.NET connection string to Analysis Services
        """
        self.connection_string = connection_string
        self.trace_session_name: Optional[str] = None
        self.connection: Optional[Any] = None
        self._event_buffer: List[Dict[str, Any]] = []

    def connect(self) -> bool:
        """
        Establish ADOMD.NET connection to Analysis Services

        Returns:
            True if connection successful
        """
        try:
            import clr  # type: ignore
            import sys
            import os

            # Add ADOMD.NET reference
            base_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(base_dir)
            dll_path = os.path.join(root_dir, "lib", "dotnet",
                                    "Microsoft.AnalysisServices.AdomdClient.dll")

            if not os.path.exists(dll_path):
                logger.error(f"ADOMD.NET DLL not found at {dll_path}")
                return False

            clr.AddReference(dll_path)  # type: ignore
            from Microsoft.AnalysisServices.AdomdClient import AdomdConnection  # type: ignore

            conn = AdomdConnection(self.connection_string)
            conn.Open()
            self.connection = conn

            # Log connection details
            server_version = conn.ServerVersion if hasattr(conn, 'ServerVersion') else 'unknown'
            logger.info(f"✓ Connected to Analysis Services for xEvent tracing")
            logger.debug(f"  Server version: {server_version}")
            logger.debug(f"  Connection string: {self.connection_string[:50]}...")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to connect ADOMD: {e}", exc_info=True)
            return False

    def _generate_xmla_create_trace(self, session_name: str) -> str:
        """
        Generate XMLA command to create Extended Events trace session

        Args:
            session_name: Unique name for the trace session

        Returns:
            XMLA command string
        """
        # Build XMLA for creating xEvent session
        # Based on SSAS xEvent templates and DAX Studio implementation
        xmla = f"""
        <Create xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
            <ObjectDefinition>
                <Trace>
                    <ID>{session_name}</ID>
                    <Name>{session_name}</Name>
                    <ddl300:XEvent xmlns:ddl300="http://schemas.microsoft.com/analysisservices/2011/engine/300">
                        <event_session name="{session_name}"
                                     dispatchLatency="1"
                                     maxMemory="4"
                                     memoryPartitionMode="none"
                                     eventRetentionMode="AllowSingleEventLoss"
                                     maxEventSize="4"
                                     trackCausality="true">
        """

        # Add each event we want to capture
        for event_name in self.TRACE_EVENTS:
            xmla += f"""
                            <event package="AS" name="{event_name}">
                                <action package="AS" name="session_id"/>
                                <action package="AS" name="request_id"/>
                            </event>
        """

        # Complete the XMLA
        xmla += """
                            <target package="package0" name="ring_buffer">
                                <parameter name="max_memory" value="4096"/>
                                <parameter name="max_events_limit" value="10000"/>
                            </target>
                        </event_session>
                    </ddl300:XEvent>
                </Trace>
            </ObjectDefinition>
        </Create>
        """

        return xmla.strip()

    def _generate_xmla_delete_trace(self, session_name: str) -> str:
        """
        Generate XMLA command to delete trace session

        Args:
            session_name: Name of trace session to delete

        Returns:
            XMLA command string
        """
        return f"""
        <Delete xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
            <Object>
                <TraceID>{session_name}</TraceID>
            </Object>
        </Delete>
        """.strip()

    def _execute_xmla(self, xmla_command: str) -> bool:
        """
        Execute XMLA command against Analysis Services

        Args:
            xmla_command: XMLA command to execute

        Returns:
            True if successful
        """
        if not self.connection:
            logger.error("No active connection to execute XMLA")
            return False

        try:
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

            cmd = AdomdCommand(xmla_command, self.connection)
            cmd.ExecuteNonQuery()

            return True

        except Exception as e:
            logger.error(f"XMLA execution failed: {e}", exc_info=True)
            return False

    def start_trace(self) -> bool:
        """
        Start Extended Events trace session

        Returns:
            True if trace started successfully
        """
        if not self.connection:
            logger.debug("No connection, attempting to connect...")
            if not self.connect():
                logger.warning("Failed to connect for xEvent tracing")
                return False

        # Generate unique session name
        self.trace_session_name = f"dax_perf_trace_{uuid.uuid4().hex[:8]}"
        logger.debug(f"Creating xEvent session: {self.trace_session_name}")

        # Clean up any existing session with same name
        logger.debug("Cleaning up any existing trace session...")
        self._execute_xmla(self._generate_xmla_delete_trace(self.trace_session_name))

        # Create new trace session
        logger.debug("Generating XMLA create command...")
        xmla_create = self._generate_xmla_create_trace(self.trace_session_name)

        logger.debug(f"Executing XMLA to create trace (events: {', '.join(self.TRACE_EVENTS)})")
        if self._execute_xmla(xmla_create):
            logger.info(f"✓ Started xEvent trace: {self.trace_session_name}")
            logger.debug(f"  Capturing events: {', '.join(self.TRACE_EVENTS)}")
            logger.debug(f"  Target: ring_buffer (4MB max, 10000 events)")
            self._event_buffer.clear()
            return True
        else:
            logger.error("✗ Failed to start xEvent trace - XMLA execution failed")
            return False

    def stop_trace(self) -> None:
        """Stop and cleanup trace session"""
        if not self.trace_session_name:
            return

        try:
            xmla_delete = self._generate_xmla_delete_trace(self.trace_session_name)
            self._execute_xmla(xmla_delete)
            logger.info(f"Stopped xEvent trace: {self.trace_session_name}")
        except Exception as e:
            logger.debug(f"Error stopping trace: {e}")
        finally:
            self.trace_session_name = None

    def _read_ring_buffer_events(self) -> List[Dict[str, Any]]:
        """
        Read events from the ring buffer target using DMV query

        Returns:
            List of event dictionaries parsed from XML
        """
        if not self.connection or not self.trace_session_name:
            logger.debug("Cannot read ring buffer: no connection or trace session")
            return []

        try:
            from Microsoft.AnalysisServices.AdomdClient import AdomdCommand  # type: ignore

            # Query the ring buffer target data using DMV
            # The ring buffer stores events as XML
            dmv_query = f"""
            SELECT target_data
            FROM sys.dm_xe_sessions s
            JOIN sys.dm_xe_session_targets t ON s.address = t.event_session_address
            WHERE s.name = '{self.trace_session_name}'
                AND t.target_name = 'ring_buffer'
            """

            logger.debug(f"Querying ring buffer for session: {self.trace_session_name}")
            cmd = AdomdCommand(dmv_query, self.connection)
            reader = cmd.ExecuteReader()

            events = []

            if reader.Read():
                target_data_xml = reader.GetString(0)
                reader.Close()

                logger.debug(f"Ring buffer XML length: {len(target_data_xml) if target_data_xml else 0} chars")

                # Parse XML to extract events
                if target_data_xml:
                    events = self._parse_ring_buffer_xml(target_data_xml)
                    logger.debug(f"✓ Parsed {len(events)} events from ring buffer")
                    if events:
                        event_types = {}
                        for evt in events:
                            evt_name = evt.get('event', 'unknown')
                            event_types[evt_name] = event_types.get(evt_name, 0) + 1
                        logger.debug(f"  Event breakdown: {event_types}")
                else:
                    logger.debug("Ring buffer returned empty XML")
            else:
                reader.Close()
                logger.warning(f"⚠ No ring buffer data found for session '{self.trace_session_name}'")
                logger.debug("This may indicate: trace not started, no events captured, or DMV not supported")

            return events

        except Exception as e:
            logger.warning(f"✗ Failed to read ring buffer: {e}")
            logger.debug(f"  Full error: {e}", exc_info=True)
            return []

    def _parse_ring_buffer_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        """
        Parse ring buffer XML data into event dictionaries

        Args:
            xml_data: XML string from ring buffer target_data

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            root = ET.fromstring(xml_data)

            # Ring buffer XML structure:
            # <RingBufferTarget>
            #   <event name="QueryEnd" ...>
            #     <data name="Duration"><value>123</value></data>
            #     <data name="TextData"><value>SELECT...</value></data>
            #   </event>
            # </RingBufferTarget>

            for event_elem in root.iter('event'):
                event_name = event_elem.get('name', '')
                event_dict = {'event': event_name}

                # Extract data fields
                for data_elem in event_elem.findall('.//data'):
                    field_name = data_elem.get('name', '')
                    value_elem = data_elem.find('value')

                    if value_elem is not None and value_elem.text:
                        value_text = value_elem.text

                        # Convert known numeric fields
                        if field_name in ('Duration', 'CpuTime', 'RowCount'):
                            try:
                                # Duration is typically in microseconds, convert to ms
                                if field_name == 'Duration':
                                    event_dict['duration_ms'] = float(value_text) / 1000.0
                                elif field_name == 'CpuTime':
                                    event_dict['cpu_time_ms'] = float(value_text) / 1000.0
                                elif field_name == 'RowCount':
                                    event_dict['row_count'] = int(value_text)
                            except ValueError:
                                event_dict[field_name.lower()] = value_text
                        elif field_name == 'TextData':
                            event_dict['text'] = value_text
                        else:
                            event_dict[field_name.lower()] = value_text

                events.append(event_dict)

        except Exception as e:
            logger.debug(f"Failed to parse ring buffer XML: {e}")

        return events

    def capture_query_metrics(
        self,
        query: str,
        query_executor: Any,
        runs: int = 3,
        clear_cache: bool = True
    ) -> List[QueryPerformanceMetrics]:
        """
        Execute query and capture detailed performance metrics

        Args:
            query: DAX query to analyze
            query_executor: Query executor instance
            runs: Number of times to execute query
            clear_cache: Whether to clear cache before execution

        Returns:
            List of QueryPerformanceMetrics for each run
        """
        metrics_list: List[QueryPerformanceMetrics] = []

        # Ensure trace is running
        if not self.trace_session_name:
            if not self.start_trace():
                logger.warning("Trace not available, using fallback timing")
                return self._fallback_metrics(query, query_executor, runs, clear_cache)

        try:
            # Clear cache if requested
            if clear_cache and hasattr(query_executor, 'flush_cache'):
                try:
                    query_executor.flush_cache()
                except Exception as e:
                    logger.debug(f"Cache flush failed: {e}")

            for run_num in range(runs):
                # Clear ring buffer before query execution to isolate events
                # (Read and discard any pending events from previous queries)
                self._read_ring_buffer_events()

                # Capture start time
                t0 = time.perf_counter()

                # Execute query
                try:
                    result = query_executor.validate_and_execute_dax(
                        query, top_n=0, bypass_cache=False
                    )
                    row_count = result.get("row_count", 0) if isinstance(result, dict) else 0
                except Exception as e:
                    logger.error(f"Query execution failed: {e}")
                    continue

                # Capture end time
                t1 = time.perf_counter()
                execution_time_ms = (t1 - t0) * 1000

                # Wait briefly for events to flush to ring buffer
                time.sleep(0.1)

                # Read events from ring buffer for this query
                run_events = self._read_ring_buffer_events()
                logger.debug(f"Run {run_num + 1}: Captured {len(run_events)} events from ring buffer")

                # Parse events and calculate metrics
                metrics = self._parse_events_to_metrics(
                    query=query,
                    events=run_events,
                    fallback_duration_ms=execution_time_ms,
                    row_count=row_count,
                    cache_state="cold" if (run_num == 0 and clear_cache) else "warm"
                )

                metrics_list.append(metrics)

        finally:
            # Keep trace running for potential additional queries
            pass

        return metrics_list

    def _parse_events_to_metrics(
        self,
        query: str,
        events: List[Dict[str, Any]],
        fallback_duration_ms: float,
        row_count: int,
        cache_state: str
    ) -> QueryPerformanceMetrics:
        """
        Parse captured events into comprehensive metrics

        Uses ExecutionStatistics event for authoritative FE timing when available,
        falls back to calculation method (Total - SE = FE) otherwise.

        Args:
            query: DAX query text
            events: List of captured event dicts
            fallback_duration_ms: Client-side measured duration
            row_count: Number of rows returned
            cache_state: "cold" or "warm"

        Returns:
            QueryPerformanceMetrics object
        """
        total_duration_ms = fallback_duration_ms
        fe_duration_ms = 0.0
        se_duration_ms = 0.0
        se_cpu_ms = 0.0
        fe_cpu_ms = 0.0
        se_count = 0
        cache_hits = 0
        cache_misses = 0
        execution_metrics = {}

        # First pass: find QueryEnd for total duration
        for event in events:
            event_name = event.get("event", "")

            if event_name == "QueryEnd":
                total_duration_ms = event.get("duration_ms", fallback_duration_ms)
                execution_metrics["query_end"] = event

            elif event_name == "ExecutionStatistics":
                # This is the authoritative source for FE timing!
                # Parse TextData which contains XML with detailed stats
                text_data = event.get("text", "")
                fe_duration_ms, se_duration_ms = self._parse_execution_statistics(text_data)
                execution_metrics["execution_statistics"] = event

            elif event_name.startswith("VertiPaqSEQuery"):
                se_count += 1
                se_duration_ms += event.get("duration_ms", 0)
                se_cpu_ms += event.get("cpu_time_ms", 0)

                if event_name == "VertiPaqSEQueryCacheMatch":
                    cache_hits += 1
                elif event_name == "VertiPaqSEQueryCacheMiss":
                    cache_misses += 1

            elif event_name == "DirectQueryEnd":
                # DirectQuery storage engine timing
                se_duration_ms += event.get("duration_ms", 0)
                se_count += 1
                execution_metrics["direct_query"] = event

        # If ExecutionStatistics wasn't available, calculate FE by subtraction
        if fe_duration_ms == 0 and se_duration_ms > 0:
            fe_duration_ms = max(total_duration_ms - se_duration_ms, 0)
            fe_cpu_ms = fe_duration_ms  # FE is single-threaded

        return QueryPerformanceMetrics(
            query_text=query[:200],  # Truncate for storage
            total_duration_ms=round(total_duration_ms, 2),
            storage_engine_ms=round(se_duration_ms, 2),
            formula_engine_ms=round(fe_duration_ms, 2),
            storage_engine_cpu_ms=round(se_cpu_ms, 2),
            formula_engine_cpu_ms=round(fe_cpu_ms, 2),
            se_query_count=se_count,
            se_cache_hits=cache_hits,
            se_cache_misses=cache_misses,
            rows_returned=row_count,
            cache_state=cache_state,
            execution_metrics=execution_metrics
        )

    def _parse_execution_statistics(self, xml_text: str) -> Tuple[float, float]:
        """
        Parse ExecutionStatistics event XML to extract FE and SE timings

        The ExecutionStatistics event contains authoritative timing data
        that is more reliable than the subtraction method.

        Args:
            xml_text: XML content from ExecutionStatistics TextData

        Returns:
            Tuple of (fe_duration_ms, se_duration_ms)
        """
        fe_ms = 0.0
        se_ms = 0.0

        try:
            if not xml_text or not xml_text.strip():
                return fe_ms, se_ms

            # Parse XML
            root = ET.fromstring(xml_text)

            # Look for timing elements
            # ExecutionStatistics structure varies by AS version
            # Common elements: FEDuration, SEDuration, TotalDuration

            for elem in root.iter():
                tag = elem.tag.lower()

                if 'formulaengineduration' in tag or 'feduration' in tag:
                    try:
                        fe_ms = float(elem.text or 0)
                    except ValueError:
                        pass

                elif 'storageengineduration' in tag or 'seduration' in tag:
                    try:
                        se_ms = float(elem.text or 0)
                    except ValueError:
                        pass

            logger.debug(f"Parsed ExecutionStatistics: FE={fe_ms}ms, SE={se_ms}ms")

        except Exception as e:
            logger.debug(f"Failed to parse ExecutionStatistics XML: {e}")

        return fe_ms, se_ms

    def _fallback_metrics(
        self,
        query: str,
        query_executor: Any,
        runs: int,
        clear_cache: bool
    ) -> List[QueryPerformanceMetrics]:
        """
        Fallback to basic timing when xEvents unavailable

        Args:
            query: DAX query
            query_executor: Query executor
            runs: Number of runs
            clear_cache: Whether to clear cache

        Returns:
            List of basic metrics
        """
        metrics_list = []

        if clear_cache and hasattr(query_executor, 'flush_cache'):
            try:
                query_executor.flush_cache()
            except Exception:
                pass

        for run_num in range(runs):
            t0 = time.perf_counter()

            try:
                result = query_executor.validate_and_execute_dax(query, 0, bypass_cache=False)
                row_count = result.get("row_count", 0) if isinstance(result, dict) else 0
            except Exception:
                row_count = 0

            t1 = time.perf_counter()
            duration_ms = (t1 - t0) * 1000

            metrics = QueryPerformanceMetrics(
                query_text=query[:200],
                total_duration_ms=round(duration_ms, 2),
                storage_engine_ms=0.0,
                formula_engine_ms=0.0,
                storage_engine_cpu_ms=0.0,
                formula_engine_cpu_ms=0.0,
                se_query_count=0,
                se_cache_hits=0,
                se_cache_misses=0,
                rows_returned=row_count,
                cache_state="cold" if (run_num == 0 and clear_cache) else "warm"
            )

            metrics_list.append(metrics)

        return metrics_list

    def close(self) -> None:
        """Cleanup resources"""
        self.stop_trace()

        if self.connection:
            try:
                self.connection.Close()
            except Exception:
                pass
            self.connection = None

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
