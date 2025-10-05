#!/usr/bin/env python3
"""
PBIXRay MCP Server V5 - Fixed Edition
- All tools including BPA analysis
- DAX-level filtering for optimal performance
- Fixed Power BI detection and connection
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Any, Dict, List, Optional
from collections import OrderedDict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Try to load ADOMD.NET and AMO
ADOMD_AVAILABLE = False
AMO_AVAILABLE = False
BPA_ANALYZER_AVAILABLE = False
AdomdConnection = None
AdomdCommand = None
AMOServer = None
Guid = None
TraceEventClass = None

try:
    import clr
    import os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
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
        
        from Microsoft.AnalysisServices.Tabular import Server as AMOServer, Database, JsonSerializer, SerializeOptions
        from Microsoft.AnalysisServices import TraceEventClass
        from System import Guid
        AMO_AVAILABLE = True
    except Exception:
        AMO_AVAILABLE = False
except Exception:
    pass

# Try to load BPA analyzer
try:
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from core.bpa_analyzer import BPAAnalyzer, BPASeverity
    BPA_ANALYZER_AVAILABLE = True
except Exception:
    BPA_ANALYZER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pbixray_v5_fixed")


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
    def __init__(self, connection):
        self.connection = connection
        self.query_cache = OrderedDict()
        self.max_cache_items = 200
    
    def _escape_dax_string(self, text: str) -> str:
        return text.replace("'", "''") if text else text
    
    def _get_info_columns(self, function_name: str):
        column_map = {
            'MEASURES': ['Name', 'Table', 'DataType', 'IsHidden', 'DisplayFolder'],
            'TABLES': ['Name', 'IsHidden', 'ModifiedTime'],
            'COLUMNS': ['Name', 'Table', 'DataType', 'IsHidden', 'IsKey'],
            'RELATIONSHIPS': ['FromTable', 'FromColumn', 'ToTable', 'ToColumn', 'IsActive', 'CrossFilterDirection', 'Cardinality']
        }
        return column_map.get(function_name, [])
    
    def execute_info_query(self, function_name: str, filter_expr: str = None, exclude_columns: List[str] = None):
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
    
    def search_measures_dax(self, search_text: str, search_in_expression: bool = True, search_in_name: bool = True) -> Dict:
        try:
            escaped_text = self._escape_dax_string(search_text)
            conditions = []
            if search_in_expression:
                conditions.append(f'SEARCH("{escaped_text}", [Expression], 1, 0) > 0')
            if search_in_name:
                conditions.append(f'SEARCH("{escaped_text}", [Name], 1, 0) > 0')
            
            filter_expr = ' || '.join(conditions) if conditions else 'TRUE()'
            query = f"EVALUATE FILTER(INFO.VIEW.MEASURES(), {filter_expr})"
            return self.validate_and_execute_dax(query)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_objects_dax(self, pattern: str, object_types: List[str]) -> Dict:
        try:
            search_text = pattern.replace('*', '').replace('?', '')
            escaped_text = self._escape_dax_string(search_text)
            results_list = []
            
            if "tables" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.VIEW.TABLES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "table", "Name", [Name], "IsHidden", [IsHidden], "ModifiedTime", [ModifiedTime]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            if "columns" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.VIEW.COLUMNS(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "column", "Name", [Name], "Table", [Table], "DataType", [DataType], "IsHidden", [IsHidden]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            if "measures" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.VIEW.MEASURES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "measure", "Name", [Name], "Table", [Table], "DataType", [DataType], "IsHidden", [IsHidden], "DisplayFolder", [DisplayFolder]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])
            
            return {'success': True, 'results': results_list, 'count': len(results_list)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _is_table_expression(self, query: str):
        table_keywords = ['SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER', 'VALUES', 'ALL', 'INFO.', 'TOPN', 'SAMPLE', 'SUMMARIZECOLUMNS']
        return any(kw in query.upper() for kw in table_keywords)
    
    def validate_and_execute_dax(self, query: str, top_n: int = 0):
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
    
    def get_tmsl_definition(self) -> Dict:
        """Get TMSL definition for BPA analysis"""
        try:
            if not AMO_AVAILABLE:
                return {'success': False, 'error': 'AMO not available'}
            
            db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            cmd = AdomdCommand(db_query, self.connection)
            reader = cmd.ExecuteReader()
            
            db_name = None
            if reader.Read():
                db_name = str(reader.GetValue(0))
            reader.Close()
            
            if not db_name:
                return {'success': False, 'error': 'Could not determine database name'}
            
            server = AMOServer()
            server.Connect(self.connection.ConnectionString)
            database = server.Databases.GetByName(db_name)
            
            options = SerializeOptions()
            options.IgnoreTimestamps = True
            options.IgnoreInferredObjects = True
            options.IgnoreInferredProperties = True
            
            tmsl_json = JsonSerializer.SerializeDatabase(database, options)
            server.Disconnect()
            
            return {'success': True, 'tmsl': tmsl_json, 'database_name': db_name}
        except Exception as e:
            logger.error(f"Error getting TMSL: {e}")
            return {'success': False, 'error': str(e)}


class EnhancedAMOTraceAnalyzer:
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
            logger.info(f"AMO connected: {self.amo_server.Name}")
            return True
        except Exception as e:
            logger.error(f"AMO connection failed: {e}")
            return False
    
    def _trace_event_handler(self, sender, e):
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
        self.trace_active = False
    
    def start_session_trace(self):
        if not self.amo_server or not hasattr(self.amo_server, 'SessionTrace'):
            return False
        try:
            self.trace_events = []
            self.session_trace = self.amo_server.SessionTrace
            self.session_trace.OnEvent += self._trace_event_handler
            self.session_trace.Stopped += self._trace_stopped_handler
            self.session_trace.Start()
            self.trace_active = True
            return True
        except Exception as e:
            logger.error(f"Failed to start SessionTrace: {e}")
            return False
    
    def stop_session_trace(self):
        if self.session_trace and self.trace_active:
            try:
                self.session_trace.Stop()
                self.session_trace.OnEvent -= self._trace_event_handler
                self.session_trace.Stopped -= self._trace_stopped_handler
                self.trace_active = False
            except Exception:
                pass
    
    def _analyze_trace_events(self):
        if not self.trace_events:
            return {
                'total_duration_ms': 0,
                'se_duration_ms': 0,
                'fe_duration_ms': 0,
                'se_queries': 0,
                'metrics_available': False
            }
        
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
        xmla_clear = '<ClearCache xmlns="http://schemas.microsoft.com/analysisservices/2003/engine"><Object><DatabaseID></DatabaseID></Object></ClearCache>'
        try:
            cmd = AdomdCommand(xmla_clear, executor.connection)
            cmd.ExecuteNonQuery()
        except Exception:
            pass
    
    def analyze_query(self, executor, query: str, runs: int = 3, clear_cache: bool = True):
        if not self.amo_server or not AMO_AVAILABLE:
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
                results.append({'run': run + 1, 'success': False, 'error': str(e)})
        
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
            summary = {'total_runs': runs, 'successful_runs': 0, 'error': 'All runs failed'}
        
        return {'success': len(successful) > 0, 'runs': results, 'summary': summary}
    
    def _fallback_analysis(self, executor, query: str, runs: int, clear_cache: bool):
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
                'avg_execution_ms': round(sum(exec_times) / len(exec_times), 2) if exec_times else 0
            }
        }
    
    def disconnect(self):
        self.stop_session_trace()
        if self.amo_server:
            try:
                self.amo_server.Disconnect()
            except:
                pass


class DAXInjector:
    def __init__(self, connection):
        self.connection = connection
    
    def upsert_measure(self, table_name: str, measure_name: str, dax_expression: str, display_folder: str = None):
        if not AMO_AVAILABLE:
            return {"success": False, "error": "AMO not available"}
        
        if not all([table_name, measure_name, dax_expression]):
            return {"success": False, "error": "Table name, measure name, and DAX expression required"}
        
        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)
            
            db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            cmd = AdomdCommand(db_query, self.connection)
            reader = cmd.ExecuteReader()
            db_name = None
            if reader.Read():
                db_name = str(reader.GetValue(0))
            reader.Close()
            
            if not db_name:
                return {"success": False, "error": "Could not determine database name"}
            
            db = server.Databases.GetByName(db_name)
            model = db.Model
            
            table = next((t for t in model.Tables if t.Name == table_name), None)
            if not table:
                return {"success": False, "error": f"Table '{table_name}' not found"}
            
            measure = next((m for m in table.Measures if m.Name == measure_name), None)
            
            if measure:
                measure.Expression = dax_expression
                if display_folder is not None:
                    measure.DisplayFolder = display_folder
                action = "updated"
            else:
                from Microsoft.AnalysisServices.Tabular import Measure
                measure = Measure()
                measure.Name = measure_name
                measure.Expression = dax_expression
                if display_folder:
                    measure.DisplayFolder = display_folder
                table.Measures.Add(measure)
                action = "created"
            
            model.SaveChanges()
            logger.info(f"Measure '{measure_name}' {action} in table '{table_name}'")
            return {"success": True, "action": action, "table": table_name, "measure": measure_name}
        except Exception as e:
            logger.error(f"Error upserting measure: {e}")
            return {"success": False, "error": str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass


active_connection = None
active_instance = None
bpa_analyzer = None
amo_tracer = None
executor = None

app = Server("pbixray-v5-fixed")


@app.list_tools()
async def list_tools() -> List[Tool]:
    tools = [
        Tool(name="detect_powerbi_desktop", description="Detect active Power BI Desktop instances", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="connect_to_powerbi", description="Connect to Power BI Desktop instance", inputSchema={"type": "object", "properties": {"model_index": {"type": "integer"}}, "required": ["model_index"]}),
        Tool(name="list_tables", description="List all tables in the model", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="list_measures", description="List measures, optionally filtered by table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="describe_table", description="Describe a specific table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": ["table"]}),
        Tool(name="get_measure_details", description="Get details for a specific measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}}, "required": ["table", "measure"]}),
        Tool(name="search_string", description="Search for text in measures", inputSchema={"type": "object", "properties": {"search_text": {"type": "string"}, "search_in_expression": {"type": "boolean", "default": True}, "search_in_name": {"type": "boolean", "default": True}}, "required": ["search_text"]}),
        Tool(name="list_calculated_columns", description="List calculated columns", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="search_objects", description="Search for objects in the model", inputSchema={"type": "object", "properties": {"pattern": {"type": "string", "default": "*"}, "types": {"type": "array", "items": {"type": "string"}, "default": ["tables", "columns", "measures"]}}, "required": []}),
        Tool(name="get_data_sources", description="Get data sources", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="get_m_expressions", description="Get M expressions", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="preview_table_data", description="Preview table data", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "top_n": {"type": "integer", "default": 10}}, "required": ["table"]}),
        Tool(name="run_dax_query", description="Run a custom DAX query", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "top_n": {"type": "integer", "default": 0}}, "required": ["query"]}),
        Tool(name="export_model_schema", description="Export model schema", inputSchema={"type": "object", "properties": {}, "required": []}),
        Tool(name="upsert_measure", description="Create or update a DAX measure", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "measure": {"type": "string"}, "expression": {"type": "string"}, "display_folder": {"type": "string"}}, "required": ["table", "measure", "expression"]}),
        Tool(name="list_columns", description="List columns in a table", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="get_column_values", description="Sample column values", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["table", "column"]}),
        Tool(name="get_column_summary", description="Column statistics", inputSchema={"type": "object", "properties": {"table": {"type": "string"}, "column": {"type": "string"}}, "required": ["table", "column"]}),
        Tool(name="list_relationships", description="List relationships", inputSchema={"type": "object", "properties": {"active_only": {"type": "boolean"}}, "required": []}),
        Tool(name="get_vertipaq_stats", description="VertiPaq storage statistics", inputSchema={"type": "object", "properties": {"table": {"type": "string"}}, "required": []}),
        Tool(name="analyze_query_performance", description="Analyze query performance with SE/FE metrics", inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "runs": {"type": "integer", "default": 3}, "clear_cache": {"type": "boolean", "default": True}}, "required": ["query"]}),
    ]
    if BPA_ANALYZER_AVAILABLE:
        tools.append(Tool(name="analyze_model_bpa", description="Run BPA analysis on current model", inputSchema={"type": "object", "properties": {}, "required": []}))
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    global active_connection, active_instance, bpa_analyzer, amo_tracer, executor
    
    try:
        if name == "detect_powerbi_desktop":
            instances = PowerBIDesktopDetector.find_powerbi_instances()
            return [TextContent(type="text", text=json.dumps(instances, indent=2))]
        
        elif name == "connect_to_powerbi":
            if not ADOMD_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({"error": "ADOMD.NET not available"}, indent=2))]
            
            instances = PowerBIDesktopDetector.find_powerbi_instances()
            idx = arguments.get("model_index", 0)
            
            if idx >= len(instances):
                return [TextContent(type="text", text=json.dumps({"error": f"Index {idx} out of range"}, indent=2))]
            
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
                executor = OptimizedQueryExecutor(active_connection)
                
                amo_tracer = EnhancedAMOTraceAnalyzer(conn_str)
                amo_connected = amo_tracer.connect_amo()
                
                # Initialize BPA analyzer
                if BPA_ANALYZER_AVAILABLE:
                    try:
                        import os
                        script_dir = os.path.dirname(os.path.abspath(__file__))
                        parent_dir = os.path.dirname(script_dir)
                        rules_path = os.path.join(parent_dir, "core", "bpa.json")
                        bpa_analyzer = BPAAnalyzer(rules_path)
                        logger.info("BPA analyzer initialized")
                    except Exception as e:
                        logger.warning(f"BPA analyzer initialization failed: {e}")
                        bpa_analyzer = None
                
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "instance": instance,
                    "amo_available": AMO_AVAILABLE,
                    "amo_connected": amo_connected,
                    "bpa_available": BPA_ANALYZER_AVAILABLE and bpa_analyzer is not None
                }, indent=2))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]
        
        if not active_connection:
            return [TextContent(type="text", text=json.dumps({"error": "Not connected"}, indent=2))]
        
        if not executor:
            executor = OptimizedQueryExecutor(active_connection)
        
        result = {}
        
        if name == "list_tables":
            result = executor.execute_info_query("TABLES")
        
        elif name == "list_measures":
            table = arguments.get("table")
            result = executor.execute_info_query("MEASURES", f'[Table] = "{table}"' if table else None, exclude_columns=['Expression'])
        
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
        
        elif name == "get_measure_details":
            result = executor.execute_info_query("MEASURES", f'[Table] = "{arguments["table"]}" && [Name] = "{arguments["measure"]}"')
        
        elif name == "search_string":
            result = executor.search_measures_dax(
                arguments['search_text'],
                arguments.get('search_in_expression', True),
                arguments.get('search_in_name', True)
            )
        
        elif name == "list_calculated_columns":
            table = arguments.get("table")
            filter_expr = '[Type] = "Calculated"'
            if table:
                filter_expr += f' && [Table] = "{table}"'
            query = f'EVALUATE FILTER(INFO.VIEW.COLUMNS(), {filter_expr})'
            result = executor.validate_and_execute_dax(query)
        
        elif name == "search_objects":
            pattern = arguments.get("pattern", "*")
            types = arguments.get("types", ["tables", "columns", "measures"])
            result = executor.search_objects_dax(pattern, types)
        
        elif name == "get_data_sources":
            result = executor.validate_and_execute_dax("SELECT * FROM $SYSTEM.DISCOVER_DATASOURCES")
        
        elif name == "get_m_expressions":
            result = executor.validate_and_execute_dax("SELECT * FROM $SYSTEM.TMSCHEMA_EXPRESSIONS")
        
        elif name == "preview_table_data":
            result = executor.validate_and_execute_dax(f"EVALUATE TOPN({arguments.get('top_n', 10)}, '{arguments['table']}')")
        
        elif name == "run_dax_query":
            result = executor.validate_and_execute_dax(arguments['query'], arguments.get('top_n', 0))
        
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
        
        elif name == "upsert_measure":
            injector = DAXInjector(active_connection)
            result = injector.upsert_measure(
                arguments["table"],
                arguments["measure"],
                arguments["expression"],
                arguments.get("display_folder")
            )
        
        elif name == "list_columns":
            table = arguments.get("table")
            result = executor.execute_info_query("COLUMNS", f'[Table] = "{table}"' if table else None)
        
        elif name == "get_column_values":
            query = f"EVALUATE TOPN({arguments.get('limit', 100)}, VALUES('{arguments['table']}'[{arguments['column']}]))"
            result = executor.validate_and_execute_dax(query)
        
        elif name == "get_column_summary":
            query = f"EVALUATE ROW(\"Min\", MIN('{arguments['table']}'[{arguments['column']}]), \"Max\", MAX('{arguments['table']}'[{arguments['column']}]), \"Distinct\", DISTINCTCOUNT('{arguments['table']}'[{arguments['column']}]), \"Nulls\", COUNTBLANK('{arguments['table']}'[{arguments['column']}]))"
            result = executor.validate_and_execute_dax(query)
        
        elif name == "list_relationships":
            active_only = arguments.get("active_only")
            filter_expr = "[IsActive] = TRUE" if active_only is True else "[IsActive] = FALSE" if active_only is False else None
            result = executor.execute_info_query("RELATIONSHIPS", filter_expr)
        
        elif name == "get_vertipaq_stats":
            table = arguments.get("table")
            query = f'EVALUATE FILTER(INFO.STORAGETABLECOLUMNS(), LEFT([TABLE_ID], LEN("{table}")) = "{table}")' if table else "EVALUATE INFO.STORAGETABLECOLUMNS()"
            result = executor.validate_and_execute_dax(query)
        
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
        
        elif name == "analyze_model_bpa":
            if not BPA_ANALYZER_AVAILABLE or not bpa_analyzer:
                return [TextContent(type="text", text=json.dumps({"error": "BPA analyzer not available"}, indent=2))]
            try:
                tmsl_result = executor.get_tmsl_definition()
                if not tmsl_result.get('success'):
                    return [TextContent(type="text", text=json.dumps(tmsl_result, indent=2))]
                
                violations = bpa_analyzer.analyze_model(tmsl_result['tmsl'])
                summary = bpa_analyzer.get_violations_summary()
                
                result = {
                    'success': True,
                    'violations_count': len(violations),
                    'summary': summary,
                    'violations': [
                        {
                            'rule_id': v.rule_id,
                            'rule_name': v.rule_name,
                            'category': v.category,
                            'severity': v.severity.name if hasattr(v.severity, 'name') else str(v.severity),
                            'object_type': v.object_type,
                            'object_name': v.object_name,
                            'table_name': v.table_name,
                            'description': v.description
                        }
                        for v in violations
                    ]
                }
            except Exception as e:
                logger.error(f"BPA analysis failed: {e}")
                result = {"error": f"BPA analysis failed: {str(e)}"}
        
        else:
            result = {'error': f'Unknown tool: {name}'}
        
        if isinstance(result, dict) and active_instance:
            result['connection_info'] = active_instance
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}, indent=2))]


async def main():
    logger.info("=" * 80)
    logger.info("PBIXRay MCP Server V5 - Fixed Edition")
    logger.info("=" * 80)
    logger.info(f"ADOMD.NET: {'✓ Available' if ADOMD_AVAILABLE else '✗ NOT AVAILABLE'}")
    logger.info(f"AMO: {'✓ Available' if AMO_AVAILABLE else '✗ NOT AVAILABLE'}")
    logger.info(f"BPA Analyzer: {'✓ Available' if BPA_ANALYZER_AVAILABLE else '✗ NOT AVAILABLE'}")
    logger.info("")
    logger.info("Features:")
    logger.info("  • DAX-level filtering for performance")
    logger.info("  • Live DAX measure injection")
    logger.info("  • Performance analysis with SE/FE metrics")
    logger.info("  • BPA analysis with detailed violations")
    logger.info("  • Complete model exploration")
    logger.info("=" * 80)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())