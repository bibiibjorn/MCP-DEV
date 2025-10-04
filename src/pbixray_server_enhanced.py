#!/usr/bin/env python3
"""
PBIXRay MCP Server V4 - OPTIMIZED EDITION
🚀 DAX-Level Filtering for Maximum Performance
- Pushes all filtering to the DAX engine (not Python)
- Uses SEARCH() and CONTAINSSTRING() DAX functions
- Eliminates unnecessary data transfer
- Matches powerbi-desktop-mcp performance patterns
"""

import asyncio
import json
import logging
import subprocess
import time
from enum import Enum
from typing import Optional, Any, Dict, List
from collections import defaultdict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Try to load ADOMD.NET and AMO
ADOMD_AVAILABLE = False
AMO_AVAILABLE = False
AdomdConnection = None
AdomdCommand = None
AMOServer = None
Guid = None
TraceEventClass = None

try:
    import clr
    import os
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the project root, then into lib/dotnet
    dll_folder = os.path.join(os.path.dirname(script_dir), "lib", "dotnet")
    
    # Load ADOMD.NET
    adomd_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.AdomdClient.dll")
    if os.path.exists(adomd_dll):
        clr.AddReference(adomd_dll)
        from Microsoft.AnalysisServices.AdomdClient import AdomdConnection, AdomdCommand
        ADOMD_AVAILABLE = True
    
    # Load AMO
    try:
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
        from System import Guid
        AMO_AVAILABLE = True
    except Exception as e:
        AMO_AVAILABLE = False
except Exception as e:
    pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pbixray_v4_optimized")


class QueryType(Enum):
    DAX = "DAX"
    DMV = "DMV"
    XMLA = "XMLA"


class PowerBIDesktopDetector:
    @staticmethod
    def find_powerbi_instances() -> List[Dict[str, Any]]:
        instances = []
        try:
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return instances
            
            port_pid_map = {}
            for line in result.stdout.splitlines():
                if 'LISTENING' in line and ('[::]' in line or '127.0.0.1' in line):
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            address = parts[1]
                            port = int(address.split(']:')[1]) if ']:' in address else int(address.split(':')[-1])
                            pid = int(parts[4])
                            port_pid_map[port] = pid
                        except (ValueError, IndexError):
                            continue
            
            tasklist_result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq msmdsrv.exe', '/FO', 'CSV', '/NH'],
                capture_output=True, text=True, timeout=10
            )
            
            msmdsrv_pids = set()
            if tasklist_result.returncode == 0:
                for line in tasklist_result.stdout.splitlines():
                    if 'msmdsrv.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            try:
                                msmdsrv_pids.add(int(parts[1].strip('"')))
                            except ValueError:
                                pass
            
            for port, pid in port_pid_map.items():
                if pid in msmdsrv_pids:
                    instances.append({
                        'port': port,
                        'pid': pid,
                        'workspace': f'msmdsrv_pid_{pid}',
                        'path': f'localhost:{port}'
                    })
            
            instances.sort(key=lambda x: x['port'], reverse=True)
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        return instances


class OptimizedQueryExecutor:
    """
    🚀 OPTIMIZED: All filtering happens in DAX, not Python
    """
    def __init__(self, connection):
        self.connection = connection
    
    def execute_info_query(self, function_name: str, filter_expr: str = None, exclude_columns: List[str] = None):
        """Execute INFO.VIEW queries with optional DAX-level filtering"""
        try:
            if exclude_columns:
                cols = self._get_info_columns(function_name)
                selected = [f'"{col}", [{col}]' for col in cols if col not in exclude_columns]
                query = f"EVALUATE SELECTCOLUMNS(INFO.VIEW.{function_name}(), {', '.join(selected)})"
            else:
                query = f"EVALUATE INFO.VIEW.{function_name}()"
            
            if filter_expr:
                query = f"EVALUATE FILTER(INFO.VIEW.{function_name}(), {filter_expr})"
            
            return self.validate_and_execute_dax(query, 0)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_info_columns(self, function_name: str):
        """Get standard columns for INFO.VIEW functions"""
        column_map = {
            'MEASURES': ['Name', 'Table', 'DataType', 'IsHidden', 'DisplayFolder'],
            'TABLES': ['Name', 'IsHidden', 'ModifiedTime'],
            'COLUMNS': ['Name', 'Table', 'DataType', 'IsHidden', 'IsKey'],
            'RELATIONSHIPS': ['FromTable', 'FromColumn', 'ToTable', 'ToColumn', 'IsActive', 'CrossFilterDirection', 'Cardinality']
        }
        return column_map.get(function_name, [])
    
    def _escape_dax_string(self, text: str) -> str:
        """Escape single quotes for DAX string literals"""
        return text.replace("'", "''")
    
    def search_measures_dax(self, search_text: str, search_in_expression: bool = True, search_in_name: bool = True) -> Dict:
        """
        🚀 OPTIMIZED: Search measures using DAX SEARCH() function
        - Filtering happens in the DAX engine
        - No data transfer of non-matching measures
        - Much faster than Python string matching
        """
        try:
            escaped_text = self._escape_dax_string(search_text)
            
            # Build DAX filter conditions
            conditions = []
            if search_in_expression:
                conditions.append(f'SEARCH("{escaped_text}", [Expression], 1, 0) > 0')
            if search_in_name:
                conditions.append(f'SEARCH("{escaped_text}", [Name], 1, 0) > 0')
            
            filter_expr = ' || '.join(conditions) if conditions else 'TRUE()'
            
            query = f"""
            EVALUATE 
            FILTER(
                INFO.VIEW.MEASURES(),
                {filter_expr}
            )
            """
            
            return self.validate_and_execute_dax(query)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_objects_dax(self, pattern: str, object_types: List[str]) -> Dict:
        """
        🚀 OPTIMIZED: Search objects using DAX SEARCH() function
        - Converts wildcard pattern to DAX search
        - Filters at DAX level, not Python level
        - Returns only matching objects
        """
        try:
            # Convert wildcard pattern to search text
            # * becomes empty (match anything), ? becomes single char
            search_text = pattern.replace('*', '').replace('?', '')
            escaped_text = self._escape_dax_string(search_text)
            
            results_list = []
            
            # Search in each object type using DAX filtering
            if "tables" in object_types:
                query = f"""
                EVALUATE 
                SELECTCOLUMNS(
                    FILTER(
                        INFO.VIEW.TABLES(),
                        SEARCH("{escaped_text}", [Name], 1, 0) > 0
                    ),
                    "type", "table",
                    "Name", [Name],
                    "IsHidden", [IsHidden],
                    "ModifiedTime", [ModifiedTime]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            if "columns" in object_types:
                query = f"""
                EVALUATE 
                SELECTCOLUMNS(
                    FILTER(
                        INFO.VIEW.COLUMNS(),
                        SEARCH("{escaped_text}", [Name], 1, 0) > 0
                    ),
                    "type", "column",
                    "Name", [Name],
                    "Table", [Table],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            if "measures" in object_types:
                query = f"""
                EVALUATE 
                SELECTCOLUMNS(
                    FILTER(
                        INFO.VIEW.MEASURES(),
                        SEARCH("{escaped_text}", [Name], 1, 0) > 0
                    ),
                    "type", "measure",
                    "Name", [Name],
                    "Table", [Table],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden],
                    "DisplayFolder", [DisplayFolder]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            if "calculated_columns" in object_types:
                query = f"""
                EVALUATE 
                SELECTCOLUMNS(
                    FILTER(
                        INFO.VIEW.COLUMNS(),
                        [Type] = "Calculated"
                        && SEARCH("{escaped_text}", [Name], 1, 0) > 0
                    ),
                    "type", "calculated_column",
                    "Name", [Name],
                    "Table", [Table],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            return {
                'success': True,
                'results': results_list,
                'count': len(results_list),
                'method': 'DAX_SEARCH_Optimized'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_and_execute_dax(self, query: str, top_n: int = 0):
        """Execute DAX query with validation"""
        try:
            if not query.strip().upper().startswith('EVALUATE'):
                if self._is_table_expression(query):
                    query = f"EVALUATE TOPN({top_n}, {query})" if top_n > 0 else f"EVALUATE {query}"
                else:
                    query = f'EVALUATE ROW("Value", {query})'
            
            start_time = time.time()
            cmd = AdomdCommand(query, self.connection)
            reader = cmd.ExecuteReader()
            
            columns = [reader.GetName(i) for i in range(reader.FieldCount)]
            rows = []
            
            while reader.Read():
                row = {}
                for i, col in enumerate(columns):
                    val = reader.GetValue(i)
                    row[col] = str(val) if val is not None else None
                rows.append(row)
            
            reader.Close()
            execution_time = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': round(execution_time, 2)
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'query': query}
    
    def _is_table_expression(self, query: str):
        """Check if query is a table expression"""
        table_keywords = ['SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER', 'VALUES', 'ALL', 'INFO.', 'TOPN', 'SAMPLE', 'SUMMARIZECOLUMNS']
        return any(kw in query.upper() for kw in table_keywords)


class EnhancedAMOTraceAnalyzer:
    """Enhanced AMO trace analyzer for SE/FE metrics"""
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.amo_server = None
        self.trace_events = []
        self.session_trace = None
        self.trace_active = False
        
    def connect_amo(self):
        if not AMO_AVAILABLE:
            return False
        try:
            self.amo_server = AMOServer()
            self.amo_server.Connect(self.connection_string)
            logger.info(f"✓ AMO connected: {self.amo_server.Name} v{self.amo_server.Version}")
            return True
        except Exception as e:
            logger.error(f"✗ AMO connection failed: {e}")
            return False
    
    def _trace_event_handler(self, sender, e):
        """Event handler for trace events"""
        try:
            event_data = {
                'event_class': str(e.EventClass) if hasattr(e, 'EventClass') else None,
                'duration_us': e.Duration if hasattr(e, 'Duration') and e.Duration is not None else 0,
                'duration_ms': (e.Duration / 1000.0) if hasattr(e, 'Duration') and e.Duration is not None else 0,
                'cpu_time_ms': e.CpuTime if hasattr(e, 'CpuTime') and e.CpuTime is not None else 0,
                'text_data': e.TextData if hasattr(e, 'TextData') else None,
                'activity_id': str(e.ActivityID) if hasattr(e, 'ActivityID') else None,
                'event_subclass': e.EventSubclass if hasattr(e, 'EventSubclass') else None,
                'timestamp': time.time()
            }
            self.trace_events.append(event_data)
        except Exception as ex:
            logger.debug(f"Error in trace handler: {ex}")
    
    def _trace_stopped_handler(self, sender, e):
        """Handler for when trace stops"""
        self.trace_active = False
        logger.debug("Trace stopped")
    
    def start_session_trace(self):
        """Start SessionTrace with event handlers"""
        if not self.amo_server or not hasattr(self.amo_server, 'SessionTrace'):
            return False
        
        try:
            self.trace_events = []
            self.session_trace = self.amo_server.SessionTrace
            self.session_trace.OnEvent += self._trace_event_handler
            self.session_trace.Stopped += self._trace_stopped_handler
            self.session_trace.Start()
            self.trace_active = True
            logger.debug("SessionTrace started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start SessionTrace: {e}")
            return False
    
    def stop_session_trace(self):
        """Stop SessionTrace"""
        if self.session_trace and self.trace_active:
            try:
                self.session_trace.Stop()
                self.session_trace.OnEvent -= self._trace_event_handler
                self.session_trace.Stopped -= self._trace_stopped_handler
                self.trace_active = False
                logger.debug("SessionTrace stopped")
            except Exception as e:
                logger.debug(f"Error stopping trace: {e}")
    
    def _analyze_trace_events(self):
        """Analyze captured trace events to extract SE/FE metrics"""
        if not self.trace_events:
            return {
                'total_duration_ms': 0,
                'se_duration_ms': 0,
                'fe_duration_ms': 0,
                'se_queries': 0,
                'se_cache_hits': 0,
                'metrics_available': False
            }
        
        query_end_events = [e for e in self.trace_events if e.get('event_class') == 'QueryEnd']
        se_query_end_events = [e for e in self.trace_events if 'VertiPaqSEQuery' in str(e.get('event_class'))]
        se_cache_match_events = [e for e in self.trace_events if 'CacheMatch' in str(e.get('event_class'))]
        
        total_duration = sum(e['duration_ms'] for e in query_end_events)
        se_duration = sum(e['duration_ms'] for e in se_query_end_events)
        se_queries = len(se_query_end_events)
        se_cache_hits = len(se_cache_match_events)
        fe_duration = max(0, total_duration - se_duration)
        
        return {
            'total_duration_ms': round(total_duration, 2),
            'se_duration_ms': round(se_duration, 2),
            'fe_duration_ms': round(fe_duration, 2),
            'se_queries': se_queries,
            'se_cache_hits': se_cache_hits,
            'metrics_available': se_queries > 0 or se_duration > 0,
            'query_end_count': len(query_end_events),
            'raw_event_count': len(self.trace_events)
        }
    
    def analyze_query(self, executor, query: str, runs: int = 3, clear_cache: bool = True):
        """Enhanced performance analysis"""
        if not self.amo_server or not AMO_AVAILABLE:
            logger.warning("AMO unavailable - using fallback timing")
            return self._fallback_analysis(executor, query, runs, clear_cache)
        
        results = []
        
        for run in range(runs):
            try:
                if not self.start_session_trace():
                    raise Exception("Failed to start SessionTrace")
                
                time.sleep(0.1)
                
                if clear_cache:
                    self._clear_cache(executor)
                    time.sleep(0.2)
                
                query_start = time.time()
                result = executor.validate_and_execute_dax(query, 0)
                query_time = (time.time() - query_start) * 1000
                
                time.sleep(0.15)
                self.stop_session_trace()
                
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
                    'storage_engine_cache_hits': metrics['se_cache_hits'],
                    'row_count': result.get('row_count', 0),
                    'metrics_available': metrics['metrics_available']
                }
                
                if execution_time > 0:
                    run_result['fe_percent'] = round((fe_time / execution_time) * 100, 1)
                    run_result['se_percent'] = round((se_time / execution_time) * 100, 1)
                
                results.append(run_result)
                
            except Exception as e:
                logger.error(f"Run {run+1} error: {e}")
                self.stop_session_trace()
                
                start = time.time()
                result = executor.validate_and_execute_dax(query, 0)
                exec_time = (time.time() - start) * 1000
                
                results.append({
                    'run': run + 1,
                    'success': result.get('success', False),
                    'execution_time_ms': round(exec_time, 2),
                    'row_count': result.get('row_count', 0),
                    'metrics_available': False,
                    'error': str(e)
                })
        
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
                'cache_cleared': clear_cache,
                'method': 'AMO_SessionTrace_Optimized'
            }
            
            if avg_exec > 0:
                summary['fe_percent'] = round((avg_fe / avg_exec) * 100, 1)
                summary['se_percent'] = round((avg_se / avg_exec) * 100, 1)
        else:
            summary = {'total_runs': runs, 'successful_runs': 0, 'error': 'All runs failed'}
        
        return {'success': len(successful) > 0, 'runs': results, 'summary': summary}
    
    def _clear_cache(self, executor):
        """Clear Analysis Services cache"""
        xmla_clear = '<ClearCache xmlns="http://schemas.microsoft.com/analysisservices/2003/engine"><Object><DatabaseID></DatabaseID></Object></ClearCache>'
        try:
            cmd = AdomdCommand(xmla_clear, executor.connection)
            cmd.ExecuteNonQuery()
            logger.debug("Cache cleared")
        except Exception as e:
            logger.debug(f"Cache clear failed: {e}")
    
    def _fallback_analysis(self, executor, query: str, runs: int, clear_cache: bool):
        """Fallback timing when tracing unavailable"""
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
                'method': 'Fallback_Timing'
            }
        }
    
    def disconnect(self):
        """Cleanup and disconnect"""
        self.stop_session_trace()
        if self.amo_server:
            try:
                self.amo_server.Disconnect()
            except:
                pass


active_connection = None
active_instance = None
amo_tracer = None

app = Server("pbixray-v4-optimized")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="detect_powerbi_desktop", description="Auto-detect Power BI Desktop instances", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="connect_to_powerbi", description="Connect to Power BI instance", inputSchema={"type": "object", "properties": {"model_index": {"type": "integer"}}, "required": ["model_index"]}),
        Tool(name="list_tables", description="List all tables", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="describe_table", description="Detailed table info", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]}),
        Tool(name="list_measures", description="List measures", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="get_measure_details", description="Get measure details", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]}),
        Tool(name="export_model_schema", description="Export model", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="list_columns", description="List columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="get_column_values", description="Sample column values", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["table", "column"]}),
        Tool(name="get_column_summary", description="Column statistics", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]}),
        Tool(name="list_calculated_columns", description="List calculated columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="list_relationships", description="List relationships", inputSchema={"type": "object", "properties": {"active_only": {"type": "boolean"}}, "required": []}),
        Tool(name="get_vertipaq_stats", description="VertiPaq statistics", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="search_objects", description="🚀 OPTIMIZED: Search objects using DAX-level filtering", inputSchema={"type": "object", "properties": {"pattern": {"type": "string"}, "types": {"type": "array"}}, "required": ["pattern"]}),
        Tool(name="search_string", description="🚀 OPTIMIZED: Search in DAX expressions using DAX SEARCH()", inputSchema={"type": "object", "properties": {"search_text": {"type": "string"}, "search_in_expression": {"type": "boolean", "default": True}, "search_in_name": {"type": "boolean", "default": True}}, "required": ["search_text"]}),
        Tool(name="get_data_sources", description="Get data sources", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="get_m_expressions", description="Get M code", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="preview_table_data", description="Preview data", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "top_n": {"type": "integer"}}, "required": ["table"]}),
        Tool(name="run_dax_query", description="Run DAX query", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        Tool(name="analyze_query_performance", description="Analyze performance with SE/FE", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "runs": {"type": "integer"}, "clear_cache": {"type": "boolean"}}, "required": ["query"]}),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    global active_connection, active_instance, amo_tracer
    
    try:
        if name == "detect_powerbi_desktop":
            instances = PowerBIDesktopDetector.find_powerbi_instances()
            return [TextContent(type="text", text=json.dumps(instances, indent=2))]
        
        if name == "connect_to_powerbi":
            if not ADOMD_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({"error": "ADOMD.NET not available"}))]
            
            instances = PowerBIDesktopDetector.find_powerbi_instances()
            idx = arguments.get("model_index", 0)
            
            if idx >= len(instances):
                return [TextContent(type="text", text=json.dumps({"error": f"Index {idx} out of range"}))]
            
            instance = instances[idx]
            conn_str = f"Data Source=localhost:{instance['port']}"
            
            try:
                if active_connection:
                    active_connection.Close()
                if amo_tracer:
                    amo_tracer.disconnect()
                
                active_connection = AdomdConnection(conn_str)
                active_connection.Open()
                active_instance = instance
                
                amo_tracer = EnhancedAMOTraceAnalyzer(conn_str)
                amo_connected = amo_tracer.connect_amo()
                
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "instance": instance,
                    "amo_available": AMO_AVAILABLE,
                    "amo_connected": amo_connected,
                    "version": "v4_optimized_dax_filtering"
                }, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
        
        if not active_connection:
            return [TextContent(type="text", text=json.dumps({"error": "Not connected"}))]
        
        executor = OptimizedQueryExecutor(active_connection)
        result = {}
        
        if name == "list_tables":
            result = executor.execute_info_query("TABLES")
        
        elif name == "list_measures":
            table = arguments.get("table")
            result = executor.execute_info_query("MEASURES", f'[Table] = "{table}"' if table else None, exclude_columns=['Expression'])
        
        elif name == "get_measure_details":
            result = executor.execute_info_query("MEASURES", f'[Table] = "{arguments["table"]}" && [Name] = "{arguments["measure"]}"')
        
        elif name == "list_columns":
            table = arguments.get("table")
            result = executor.execute_info_query("COLUMNS", f'[Table] = "{table}"' if table else None)
        
        elif name == "list_relationships":
            active_only = arguments.get("active_only")
            filter_expr = "[IsActive] = TRUE" if active_only is True else "[IsActive] = FALSE" if active_only is False else None
            result = executor.execute_info_query("RELATIONSHIPS", filter_expr)
        
        elif name == "get_vertipaq_stats":
            table = arguments.get("table")
            query = f'EVALUATE FILTER(INFO.STORAGETABLECOLUMNS(), LEFT([TABLE_ID], LEN("{table}")) = "{table}")' if table else "EVALUATE INFO.STORAGETABLECOLUMNS()"
            result = executor.validate_and_execute_dax(query)
        
        elif name == "describe_table":
            table = arguments["table"]
            cols = executor.execute_info_query("COLUMNS", f'[Table] = "{table}"')
            measures = executor.execute_info_query("MEASURES", f'[Table] = "{table}"', exclude_columns=['Expression'])
            rels = executor.execute_info_query("RELATIONSHIPS", f'[FromTable] = "{table}" || [ToTable] = "{table}"')
            result = {
                'success': True,
                'table': table,
                'columns': cols.get('rows', []),
                'measures': measures.get('rows', []),
                'relationships': rels.get('rows', [])
            }
        
        elif name == "get_column_values":
            query = f"EVALUATE TOPN({arguments.get('limit', 100)}, VALUES('{arguments['table']}'[{arguments['column']}]))"
            result = executor.validate_and_execute_dax(query)
        
        elif name == "get_column_summary":
            query = f"EVALUATE ROW(\"Min\", MIN('{arguments['table']}'[{arguments['column']}]), \"Max\", MAX('{arguments['table']}'[{arguments['column']}]), \"Distinct\", DISTINCTCOUNT('{arguments['table']}'[{arguments['column']}]), \"Nulls\", COUNTBLANK('{arguments['table']}'[{arguments['column']}]))"
            result = executor.validate_and_execute_dax(query)
        
        elif name == "list_calculated_columns":
            table = arguments.get("table")
            filter_expr = '[Type] = "Calculated"'
            if table:
                filter_expr += f' && [Table] = "{table}"'
            query = f'EVALUATE FILTER(INFO.VIEW.COLUMNS(), {filter_expr})'
            result = executor.validate_and_execute_dax(query)
        
        elif name == "search_objects":
            # 🚀 OPTIMIZED: Uses DAX-level filtering
            pattern = arguments.get("pattern", "*")
            types = arguments.get("types", ["tables", "columns", "measures"])
            result = executor.search_objects_dax(pattern, types)
        
        elif name == "search_string":
            # 🚀 OPTIMIZED: Uses DAX SEARCH() function
            search_text = arguments['search_text']
            search_in_expression = arguments.get('search_in_expression', True)
            search_in_name = arguments.get('search_in_name', True)
            result = executor.search_measures_dax(search_text, search_in_expression, search_in_name)
        
        elif name == "get_data_sources":
            result = executor.validate_and_execute_dax("SELECT * FROM $SYSTEM.DISCOVER_DATASOURCES")
        
        elif name == "get_m_expressions":
            result = executor.validate_and_execute_dax("SELECT * FROM $SYSTEM.TMSCHEMA_EXPRESSIONS")
        
        elif name == "preview_table_data":
            result = executor.validate_and_execute_dax(f"EVALUATE TOPN({arguments.get('top_n', 10)}, '{arguments['table']}')")
        
        elif name == "run_dax_query":
            result = executor.validate_and_execute_dax(arguments['query'], arguments.get('top_n', 0))
        
        elif name == "analyze_query_performance":
            if amo_tracer:
                result = amo_tracer.analyze_query(
                    executor,
                    arguments['query'],
                    arguments.get('runs', 3),
                    arguments.get('clear_cache', True)
                )
            else:
                result = {'success': False, 'error': 'AMO tracer not initialized'}
        
        elif name == "export_model_schema":
            tables = executor.execute_info_query("TABLES")
            columns = executor.execute_info_query("COLUMNS")
            measures = executor.execute_info_query("MEASURES", exclude_columns=['Expression'])
            relationships = executor.execute_info_query("RELATIONSHIPS")
            result = {
                'success': True,
                'schema': {
                    'tables': tables.get('rows', []),
                    'columns': columns.get('rows', []),
                    'measures': measures.get('rows', []),
                    'relationships': relationships.get('rows', [])
                }
            }
        
        else:
            result = {'error': f'Unknown tool: {name}'}
        
        if isinstance(result, dict) and active_instance:
            result['connection_info'] = active_instance
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}, indent=2))]


async def main():
    logger.info("═" * 80)
    logger.info("🚀 PBIXRAY MCP Server V4 - OPTIMIZED EDITION")
    logger.info("═" * 80)
    logger.info(f"ADOMD.NET: {'✓ Available' if ADOMD_AVAILABLE else '✗ NOT AVAILABLE'}")
    logger.info(f"AMO: {'✓ Available' if AMO_AVAILABLE else '✗ NOT AVAILABLE'}")
    logger.info("")
    logger.info("🚀 PERFORMANCE OPTIMIZATIONS:")
    logger.info("  • DAX-level filtering (not Python string matching)")
    logger.info("  • SEARCH() function for text matching")
    logger.info("  • Minimal data transfer from Analysis Services")
    logger.info("  • Matches powerbi-desktop-mcp performance patterns")
    logger.info("")
    logger.info("🎯 OPTIMIZED TOOLS:")
    logger.info("  • search_objects - Uses DAX SEARCH() at engine level")
    logger.info("  • search_string - Filters measures in DAX, not Python")
    logger.info("  • All queries push filtering to VertiPaq engine")
    logger.info("═" * 80)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())