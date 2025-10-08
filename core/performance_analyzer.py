"""
Performance Analyzer for PBIXRay MCP Server

xEvents-based FE/SE analyzer using XMLA through ADOMD.
Creates a ring_buffer xEvent session, executes the query, reads events from
DMV $SYSTEM.DISCOVER_XEVENT_SESSION_TARGETS, and computes SE/FE metrics.
"""

import time
import logging
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class EnhancedAMOTraceAnalyzer:
    """
    Extended Events analyzer (reuses public class name for compatibility).

    Public API is preserved: analyze_query(executor, query, runs, clear_cache)
    and disconnect(). Internally, this class manages a per-run xEvent session.
    """

    def __init__(self, connection_string: str):
        # Keep signature for compatibility; we operate via executor.connection
        self.connection_string = connection_string
        self._last_session: Optional[str] = None
        # Back-compat fields referenced elsewhere
        self.amo_server = True  # truthy to indicate analyzer is available
        self.trace_active = False
        # Tunable waits (seconds) to minimize latency while keeping reliability
        self._session_start_wait = 0.03  # wait after session create
        self._cache_clear_wait = 0.08    # wait after cache clear
        self._event_poll_interval = 0.03 # interval when polling ring_buffer
        self._max_event_flush_wait = 0.25 # maximum time to wait for events

    # Back-compat: older code calls connect_amo() and checks amo_server
    def connect_amo(self) -> bool:
        return True

    # Compatibility no-ops for older tooling that toggles a SessionTrace
    def start_session_trace(self) -> bool:
        self.trace_active = True
        return True

    def stop_session_trace(self) -> None:
        self.trace_active = False

    # ---- XMLA helpers ----
    def _exec_xmla(self, executor, xmla: str) -> None:
        """Execute an XMLA command using ADOMD with the correct command type.

        Without explicitly setting CommandType=Xmla, ADOMD treats the text as
        MDX/DAX and the server returns a protocol/parse error. This method
        ensures proper XMLA execution and applies a conservative timeout.
        """
        from Microsoft.AnalysisServices.AdomdClient import AdomdCommand, AdomdCommandType
        cmd = AdomdCommand(xmla, executor.connection)
        try:
            # Ensure ADOMD understands this is XMLA, not DAX/MDX text
            cmd.CommandType = AdomdCommandType.Xmla  # type: ignore[attr-defined]
        except Exception:
            # Older clients may not expose the enum; best-effort fallback
            pass
        # Honor executor timeout if available
        try:
            timeout = int(getattr(executor, 'command_timeout_seconds', 60) or 60)
            cmd.CommandTimeout = timeout
        except Exception:
            pass
        cmd.ExecuteNonQuery()

    def _query_rowset(self, executor, rowset_sql: str):
        from Microsoft.AnalysisServices.AdomdClient import AdomdCommand
        cmd = AdomdCommand(rowset_sql, executor.connection)
        try:
            timeout = int(getattr(executor, 'command_timeout_seconds', 60) or 60)
            cmd.CommandTimeout = timeout
        except Exception:
            pass
        reader = cmd.ExecuteReader()
        columns = [reader.GetName(i) for i in range(reader.FieldCount)]
        rows: List[Dict[str, Any]] = []
        while reader.Read():
            row: Dict[str, Any] = {}
            for i, col in enumerate(columns):
                try:
                    val = reader.GetValue(i)
                    row[col] = None if val is None else str(val)
                except Exception:
                    row[col] = None
            rows.append(row)
        reader.Close()
        return rows

    def _create_xe_session(self, executor, name: str) -> None:
        # Create a ring_buffer xEvent session capturing FE/SE events with actions
        xmla = f"""
<Execute xmlns=\"urn:schemas-microsoft-com:xml-analysis\"
         xmlns:ddl300_300=\"http://schemas.microsoft.com/analysisservices/2011/engine/300/300\">
  <Command>
    <Create>
      <ObjectDefinition>
        <Trace>
          <ID>{name}</ID>
          <Name>{name}</Name>
          <ddl300_300:XEvent>
            <event_session name=\"{name}\" dispatchLatency=\"0\" eventRetentionMode=\"allowSingleEventLoss\" trackCausality=\"true\">
              <event package=\"AS\" name=\"QueryBegin\"> 
                <action package=\"AS\" name=\"ActivityID\"/>
                <action package=\"AS\" name=\"TextData\"/>
                <action package=\"AS\" name=\"CurrentTime\"/>
                <action package=\"AS\" name=\"StartTime\"/>
              </event>
                            <event package=\"AS\" name=\"QueryEnd\"> 
                                <action package=\"AS\" name=\"ActivityID\"/>
                                <action package=\"AS\" name=\"TextData\"/>
                                <action package=\"AS\" name=\"CurrentTime\"/>
                                <action package=\"AS\" name=\"StartTime\"/>
                            </event>
              <event package=\"AS\" name=\"VertiPaqSEQueryBegin\"> 
                <action package=\"AS\" name=\"ActivityID\"/>
              </event>
                            <event package=\"AS\" name=\"VertiPaqSEQueryEnd\"> 
                                <action package=\"AS\" name=\"ActivityID\"/>
                            </event>
              <event package=\"AS\" name=\"VertiPaqSEQueryCacheMatch\"> 
                <action package=\"AS\" name=\"ActivityID\"/>
              </event>
                            <target package=\"package0\" name=\"ring_buffer\"> 
                                <parameter name=\"bufferSize\" value=\"10000\"/>
                            </target>
            </event_session>
          </ddl300_300:XEvent>
        </Trace>
      </ObjectDefinition>
    </Create>
  </Command>
</Execute>
"""
        self._exec_xmla(executor, xmla)

    def _drop_xe_session(self, executor, name: str) -> None:
        xmla = f"""
<Execute xmlns=\"urn:schemas-microsoft-com:xml-analysis\">  
  <Command>  
    <Delete>  
      <Object>  
        <TraceID>{name}</TraceID>  
      </Object>  
    </Delete>  
  </Command>  
</Execute>  
"""
        try:
            self._exec_xmla(executor, xmla)
        except Exception as e:
            logger.debug(f"Drop session failed (may already be gone): {e}")

    def _fetch_ring_buffer(self, executor, name: str) -> List[Dict[str, Any]]:
        # Read target data from DMV; parse XML into event rows
        rows = self._query_rowset(executor, f"SELECT * FROM $SYSTEM.DISCOVER_XEVENT_SESSION_TARGETS WHERE SESSION_NAME = '{name}'")
        if not rows:
            return []
        # TARGET_DATA is XML
        xml_text = rows[0].get('TARGET_DATA') or rows[0].get('target_data') or ''
        if not xml_text:
            return []
        events: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
            # Iterate with namespace-agnostic tags
            def _lname(tag: str) -> str:
                return tag.split('}', 1)[-1] if '}' in tag else tag
            for ev in root.iter():
                if _lname(ev.tag) != 'event':
                    continue
                name_attr = ev.get('name')
                ts = ev.get('timestamp')
                data_map: Dict[str, Any] = {'event': str(name_attr or ''), 'timestamp': ts}
                for d in list(ev):
                    lt = _lname(d.tag)
                    if lt == 'data':
                        dn = d.get('name')
                        if not dn:
                            continue
                        v = None
                        val_node = None
                        # Find child named 'value' regardless of namespace
                        for ch in list(d):
                            if _lname(ch.tag) == 'value':
                                val_node = ch
                                break
                        if val_node is not None and val_node.text is not None:
                            v = val_node.text
                        data_map[str(dn)] = v
                    elif lt == 'action':
                        an = d.get('name')
                        if not an:
                            continue
                        aval_node = None
                        for ch in list(d):
                            if _lname(ch.tag) == 'value':
                                aval_node = ch
                                break
                        aval = aval_node.text if aval_node is not None else None
                        data_map[str(an)] = aval
                events.append(data_map)
        except Exception as e:
            logger.warning(f"Failed parsing ring_buffer XML: {e}")
        return events

    def _analyze_events(self, events: List[Dict[str, Any]], compute_counts: bool = True) -> Dict[str, Any]:
        if not events:
            return {
                'total_duration_ms': 0.0,
                'se_duration_ms': 0.0,
                'fe_duration_ms': 0.0,
                'se_queries': 0,
                'se_cache_matches': 0,
                'metrics_available': False,
                'total_events': 0,
                'query_end_events': 0,
                'se_end_events': 0,
                'event_counts': {} if compute_counts else None
            }
        # Map of events
        query_ends = [e for e in events if (e.get('event') == 'QueryEnd')]
        query_begins = [e for e in events if (e.get('event') == 'QueryBegin')]
        se_ends = [e for e in events if (e.get('event') == 'VertiPaqSEQueryEnd')]
        se_cache = [e for e in events if (e.get('event') == 'VertiPaqSEQueryCacheMatch')]
        # Aggregate counts by event name
        counts: Dict[str, int] = {}
        if compute_counts:
            for ev in events:
                nm = str(ev.get('event') or '')
                counts[nm] = counts.get(nm, 0) + 1

        # Choose the last QueryEnd as the one to report
        qe = query_ends[-1] if query_ends else None
        total_ms = 0.0
        se_ms = 0.0
        se_events: List[Dict[str, Any]] = []
        cache_events: List[Dict[str, Any]] = []
        if qe:
            total_ms = float((qe.get('Duration') or qe.get('duration') or 0) or 0)
            act = qe.get('ActivityID') or qe.get('activity_id')
            if act:
                se_events = [e for e in se_ends if (e.get('ActivityID') or e.get('activity_id')) == act]
                cache_events = [e for e in se_cache if (e.get('ActivityID') or e.get('activity_id')) == act]
            else:
                # Fallback: include all
                se_events = list(se_ends)
                cache_events = list(se_cache)
        else:
            # Fallback
            total_ms = max([float((e.get('Duration') or 0) or 0) for e in query_ends], default=0.0) if query_ends else 0.0
            se_events = list(se_ends)
            cache_events = list(se_cache)

        for se in se_events:
            try:
                se_ms += float((se.get('Duration') or se.get('duration') or 0) or 0)
            except Exception:
                pass

        fe_ms = max(0.0, total_ms - se_ms)

        return {
            'total_duration_ms': round(total_ms, 2),
            'se_duration_ms': round(se_ms, 2),
            'fe_duration_ms': round(fe_ms, 2),
            'se_queries': len(se_events),
            'se_cache_matches': len(cache_events),
            'metrics_available': total_ms > 0,
            'total_events': len(events),
            'query_end_events': len(query_ends),
            'se_end_events': len(se_events),
            'event_counts': counts if compute_counts else None
        }

    def _get_database_name(self, executor) -> Optional[str]:
        try:
            rows = self._query_rowset(executor, "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS")
            return rows[0]['CATALOG_NAME'] if rows else None
        except Exception:
            return None

    def _clear_cache(self, executor):
        db_name = self._get_database_name(executor)
        # Use a proper XMLA Execute envelope to ensure protocol correctness
        xmla_clear = (
            '<Execute xmlns="urn:schemas-microsoft-com:xml-analysis">'
            '  <Command>'
            '    <ClearCache xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">'
            '      <Object><DatabaseID>{db}</DatabaseID></Object>'
            '    </ClearCache>'
            '  </Command>'
            '</Execute>'
        ).format(db=db_name or '')
        try:
            self._exec_xmla(executor, xmla_clear)
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    # ---- public API ----
    def analyze_query(self, executor, query: str, runs: int = 3, clear_cache: bool = True, include_event_counts: bool = False) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        total_runs = max(1, int(runs or 1))
        for i in range(total_runs):
            run_no = i + 1
            session_name = f"PBIXRay_XE_{uuid.uuid4().hex[:8]}"
            self._last_session = session_name
            try:
                # Create session first
                self._create_xe_session(executor, session_name)
                # Small delay to ensure the session is active
                time.sleep(self._session_start_wait)

                # Only clear cache on the first run to provide cold vs warm comparison
                if clear_cache and i == 0:
                    self._clear_cache(executor)
                    time.sleep(self._cache_clear_wait)

                t0 = time.time()
                query_res = executor.validate_and_execute_dax(query, 0)
                wall_ms = (time.time() - t0) * 1000.0
                # Poll ring buffer briefly; return early once QueryEnd appears
                deadline = time.time() + self._max_event_flush_wait
                events: List[Dict[str, Any]] = []
                while True:
                    events = self._fetch_ring_buffer(executor, session_name)
                    if any((e.get('event') == 'QueryEnd') for e in events):
                        break
                    if time.time() >= deadline:
                        break
                    time.sleep(self._event_poll_interval)
                metrics = self._analyze_events(events, include_event_counts)
                total = metrics.get('total_duration_ms') or wall_ms
                se_ms = metrics.get('se_duration_ms', 0.0)
                fe_ms = max(0.0, total - se_ms)

                run_out = {
                    'run': run_no,
                    'success': query_res.get('success', False),
                    'execution_time_ms': round(total, 2),
                    'formula_engine_ms': round(fe_ms, 2),
                    'storage_engine_ms': round(se_ms, 2),
                    'storage_engine_queries': metrics.get('se_queries', 0),
                    'storage_engine_cache_matches': metrics.get('se_cache_matches', 0),
                    'row_count': query_res.get('row_count', 0),
                    'metrics_available': metrics.get('metrics_available', False),
                    'cache_state': 'cold' if (clear_cache and i == 0) else 'warm'
                }
                if include_event_counts:
                    run_out['event_counts'] = metrics.get('event_counts', {}) or {}
                if total > 0:
                    run_out['fe_percent'] = round((fe_ms / total) * 100, 1)
                    run_out['se_percent'] = round((se_ms / total) * 100, 1)
                results.append(run_out)
            except Exception as e:
                logger.error(f"xEvents run {run_no} failed: {e}")
                results.append({'run': run_no, 'success': False, 'error': str(e)})
            finally:
                # Drop session regardless of outcome
                try:
                    self._drop_xe_session(executor, session_name)
                except Exception:
                    pass

        ok = [r for r in results if r.get('success')]
        if ok:
            exec_times = [r['execution_time_ms'] for r in ok]
            fe_times = [r.get('formula_engine_ms', 0) for r in ok]
            se_times = [r.get('storage_engine_ms', 0) for r in ok]
            avg_exec = sum(exec_times)/len(exec_times)
            avg_fe = sum(fe_times)/len(fe_times)
            avg_se = sum(se_times)/len(se_times)
            summary = {
                'total_runs': total_runs,
                'successful_runs': len(ok),
                'avg_execution_ms': round(avg_exec, 2),
                'min_execution_ms': round(min(exec_times), 2),
                'max_execution_ms': round(max(exec_times), 2),
                'avg_formula_engine_ms': round(avg_fe, 2),
                'avg_storage_engine_ms': round(avg_se, 2),
                'fe_percent': round((avg_fe/avg_exec)*100, 1) if avg_exec > 0 else 0.0,
                'se_percent': round((avg_se/avg_exec)*100, 1) if avg_exec > 0 else 0.0,
                'cache_mode': 'cold_then_warm' if clear_cache else 'warm_only'
            }
        else:
            summary = {'total_runs': total_runs, 'successful_runs': 0, 'error': 'All runs failed'}

        return {'success': len(ok) > 0, 'runs': results, 'summary': summary, 'query': query}

    def _fallback_analysis(self, executor, query: str, runs: int, clear_cache: bool) -> Dict[str, Any]:
        # Retained for API compatibility (not used now that xEvents is default)
        results: List[Dict[str, Any]] = []
        for i in range(max(1, int(runs or 1))):
            if clear_cache:
                try:
                    self._clear_cache(executor)
                    time.sleep(0.1)
                except Exception:
                    pass
            t0 = time.time()
            res = executor.validate_and_execute_dax(query, 0)
            ms = (time.time() - t0) * 1000.0
            results.append({'run': i+1, 'success': res.get('success', False), 'execution_time_ms': round(ms, 2), 'row_count': res.get('row_count', 0), 'metrics_available': False})
        ok = [r for r in results if r.get('success')]
        exec_times = [r['execution_time_ms'] for r in ok] if ok else [0]
        return {'success': len(ok) > 0, 'runs': results, 'summary': {'total_runs': runs, 'successful_runs': len(ok), 'avg_execution_ms': round(sum(exec_times)/len(exec_times), 2) if exec_times else 0, 'note': 'xEvents unavailable'}, 'query': query}

    def disconnect(self):
        # Nothing persistent to close; ensure last session dropped
        if self._last_session:
            logger.debug(f"Last xEvent session: {self._last_session}")
