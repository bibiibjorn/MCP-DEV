"""
Optimized Query Executor for PBIXRay MCP Server

Enhanced DAX query execution with:
- Better error handling and suggestions
- Table reference support
- Query caching
- DAX-level filtering
- Comprehensive error analysis

Based on fabric-toolbox best practices.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
from core.dax_validator import DaxValidator
from core.config_manager import config

logger = logging.getLogger(__name__)

# DMV Column Type Constants (INFO.COLUMNS()[Type] field)
# These are numeric values, not text
COLUMN_TYPE_DATA = 1        # Regular data column from source
COLUMN_TYPE_CALCULATED = 2  # Calculated column with DAX expression
COLUMN_TYPE_HIERARCHY = 3   # Hierarchy

# Try to load ADOMD.NET
ADOMD_AVAILABLE = False
AdomdConnection: Any = None
AdomdCommand: Any = None

try:
    import clr
    import os

    # Determine DLL path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    # Load ADOMD.NET
    adomd_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.AdomdClient.dll")
    if os.path.exists(adomd_dll):
        clr.AddReference(adomd_dll)  # type: ignore[attr-defined]
        from Microsoft.AnalysisServices.AdomdClient import AdomdConnection, AdomdCommand  # type: ignore
        ADOMD_AVAILABLE = True
        logger.info("ADOMD.NET loaded successfully")
except Exception as e:
    logger.warning(f"ADOMD.NET not available: {e}")

# Try to load AMO/TOM assemblies early so helpers can use them
AMO_AVAILABLE = False
try:
    import clr  # type: ignore
    import os as _os
    _script_dir = _os.path.dirname(_os.path.abspath(__file__))
    _parent_dir = _os.path.dirname(_script_dir)
    _dll_folder = _os.path.join(_parent_dir, "lib", "dotnet")
    _core_dll = _os.path.join(_dll_folder, "Microsoft.AnalysisServices.Core.dll")
    _amo_dll = _os.path.join(_dll_folder, "Microsoft.AnalysisServices.dll")
    _tabular_dll = _os.path.join(_dll_folder, "Microsoft.AnalysisServices.Tabular.dll")
    if _os.path.exists(_core_dll):
        clr.AddReference(_core_dll)  # type: ignore[attr-defined]
    if _os.path.exists(_amo_dll):
        clr.AddReference(_amo_dll)  # type: ignore[attr-defined]
    if _os.path.exists(_tabular_dll):
        clr.AddReference(_tabular_dll)  # type: ignore[attr-defined]
    from Microsoft.AnalysisServices.Tabular import Server as _AMOServer  # type: ignore
    AMO_AVAILABLE = True
except Exception as _e:
    logger.warning(f"AMO/TOM not available: {_e}")


class OptimizedQueryExecutor:
    """
    Optimized query executor with enhanced error handling and DAX query optimization.

    Features:
    - Intelligent table reference handling
    - Comprehensive error analysis with suggestions
    - Query result caching
    - DAX-level filtering for performance
    - Safe execution with multiple fallback strategies
    """

    def __init__(self, connection):
        """
        Initialize the query executor.

        Args:
            connection: Active ADOMD connection
        """
        self.connection = connection
        # Simple TTL-based LRU cache for query results
        self.query_cache: "OrderedDict[Tuple[str, int], Dict[str, Any]]" = OrderedDict()
        self.max_cache_items = 200
        self.cache_ttl_seconds = max(0, int(config.get('performance.cache_ttl_seconds', 300) or 0))
        self._table_cache = None
        self._table_id_by_name: Optional[Dict[str, Any]] = None
        self._table_name_by_id: Optional[Dict[Any, str]] = None
        # Command timeout (seconds) for ADOMD command execution
        try:
            self.command_timeout_seconds = int(config.get('performance.command_timeout_seconds', 60) or 60)
        except Exception:
            self.command_timeout_seconds = 60
        # Optional history logger callback: callable(dict)
        self._history_logger = None
        # Cache stats
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_bypass = 0

    # --------------------
    # AMO/TOM helper methods
    # --------------------
    def _get_database_name(self) -> Optional[str]:
        """Resolve the current database name via ADOMD catalogs DMV."""
        try:
            if not AdomdCommand:
                return None
            db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            cmd = AdomdCommand(db_query, self.connection)
            reader = cmd.ExecuteReader()
            db_name = None
            if reader.Read():
                db_name = str(reader.GetValue(0))
            reader.Close()
            return db_name
        except Exception as e:
            logger.debug(f"_get_database_name failed: {e}")
            return None

    def _connect_amo_server_db(self):
        """Return (server, database) using AMO/TOM or (None, None) if unavailable."""
        if not AMO_AVAILABLE:
            return None, None
        try:
            from Microsoft.AnalysisServices.Tabular import Server as AMOServer  # type: ignore
            srv = AMOServer()
            # Reuse ADOMD connection string when possible
            conn_str = getattr(self.connection, 'ConnectionString', None)
            if not conn_str:
                return None, None
            srv.Connect(conn_str)
            # Use current DB name if available
            db_name = self._get_database_name()
            db = None
            if db_name and hasattr(srv, 'Databases'):
                try:
                    db = srv.Databases.GetByName(db_name)
                except Exception:
                    db = srv.Databases[0] if srv.Databases.Count > 0 else None
            else:
                db = srv.Databases[0] if srv.Databases.Count > 0 else None
            if not db:
                try:
                    srv.Disconnect()
                except Exception:
                    pass
                return None, None
            return srv, db
        except Exception as e:
            logger.debug(f"_connect_amo_server_db failed: {e}")
            return None, None

    def enumerate_m_expressions_tom(self, limit: int | None = None) -> Dict[str, Any]:
        """Enumerate M expressions via TOM as a fallback when DMV is blocked."""
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {
                'success': False,
                'error': 'AMO/TOM unavailable to enumerate expressions',
                'error_type': 'amo_not_available'
            }
        try:
            rows: List[Dict[str, Any]] = []
            # Model.Expressions holds shared expressions (M queries)
            model = db.Model
            exprs = getattr(model, 'Expressions', None)
            if exprs is not None:
                for exp in exprs:
                    # Convert Kind (an enum) to string to ensure JSON serialization
                    kind_val = getattr(exp, 'Kind', 'M')
                    try:
                        kind_str = str(kind_val) if kind_val is not None else 'M'
                        # Some enums stringify as 'ExpressionKind.M'; keep only last token
                        if isinstance(kind_str, str) and '.' in kind_str:
                            kind_str = kind_str.split('.')[-1]
                    except Exception:
                        kind_str = 'M'
                    rows.append({
                        'Name': getattr(exp, 'Name', ''),
                        'Expression': getattr(exp, 'Expression', ''),
                        'Kind': kind_str or 'M'
                    })
                    if isinstance(limit, int) and limit > 0 and len(rows) >= limit:
                        break
            # Some models keep M in data sources as well (Mashup)
            if (not rows) and hasattr(model, 'DataSources'):
                for ds in model.DataSources:
                    mexp = getattr(ds, 'Expression', None)
                    if mexp:
                        rows.append({
                            'Name': getattr(ds, 'Name', 'DataSource'),
                            'Expression': mexp,
                            'Kind': 'M'
                        })
                        if isinstance(limit, int) and limit > 0 and len(rows) >= limit:
                            break
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'method': 'TOM'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except Exception:
                pass

    def list_data_sources_tom(self, limit: int | None = None) -> Dict[str, Any]:
        """List data sources via TOM for Desktop compatibility."""
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {
                'success': False,
                'error': 'AMO/TOM unavailable to list data sources',
                'error_type': 'amo_not_available'
            }
        try:
            rows: List[Dict[str, Any]] = []
            model = db.Model
            if hasattr(model, 'DataSources'):
                for ds in model.DataSources:
                    try:
                        ds_type = type(ds).__name__
                        rows.append({
                            'DataSourceID': getattr(ds, 'Name', None) or getattr(ds, 'ID', None) or getattr(ds, 'ConnectionName', None),
                            'Name': getattr(ds, 'Name', None) or getattr(ds, 'ConnectionName', None) or 'DataSource',
                            'Description': getattr(ds, 'Description', None),
                            'Type': ds_type
                        })
                        if isinstance(limit, int) and limit > 0 and len(rows) >= limit:
                            break
                    except Exception:
                        # Continue on per-datasource read errors
                        pass
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'method': 'TOM'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except Exception:
                pass

    def get_partition_freshness_tom(self) -> Dict[str, Any]:
        """Aggregate partition refresh timestamps per table via TOM."""
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {'success': False, 'error': 'AMO/TOM unavailable', 'error_type': 'amo_not_available'}
        try:
            model = db.Model
            per_table: Dict[str, Any] = {}
            if hasattr(model, 'Tables'):
                for tbl in model.Tables:
                    last_dt = None
                    try:
                        for part in tbl.Partitions:
                            # Prefer LastProcessed or RefreshedTime depending on TOM version
                            val = getattr(part, 'LastProcessed', None) or getattr(part, 'RefreshedTime', None)
                            if val:
                                try:
                                    # val may be .NET DateTime; convert to ISO string sortable
                                    iso = val.isoformat()
                                except Exception:
                                    iso = str(val)
                                # Track max
                                if (last_dt is None) or (iso > last_dt):
                                    last_dt = iso
                    except Exception:
                        pass
                    per_table[tbl.Name] = {
                        'Table': tbl.Name,
                        'LastRefresh': last_dt
                    }
            rows = list(per_table.values())
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'method': 'TOM'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except Exception:
                pass

    def set_history_logger(self, logger_cb) -> None:
        """Register a callback to receive execution history events.

        logger_cb will be invoked with a dict containing keys like
        { 'query': str, 'final_query': str, 'top_n': int, 'success': bool,
          'row_count': int, 'execution_time_ms': float, 'error': str|None, 'cached': bool }
        """
        self._history_logger = logger_cb

    def _ensure_table_mappings(self) -> None:
        """Load table ID<->name mappings once for fast lookups."""
        try:
            if self._table_id_by_name is not None and self._table_name_by_id is not None:
                return
            # Load all columns from INFO.TABLES() (no projection) to include ID
            result = self.validate_and_execute_dax("EVALUATE INFO.TABLES()", 0)
            if not result.get('success'):
                logger.error(f"Failed to load table mappings: {result.get('error')}")
                self._table_id_by_name, self._table_name_by_id = {}, {}
                return
            id_by_name: Dict[str, Any] = {}
            name_by_id: Dict[Any, str] = {}
            for row in result.get('rows', []):
                name = row.get('Name')
                tid = row.get('ID') if 'ID' in row else row.get('TableID')
                if name is not None and tid is not None:
                    id_by_name[name] = tid
                    name_by_id[tid] = name
            self._table_id_by_name = id_by_name
            self._table_name_by_id = name_by_id
        except Exception as e:
            logger.error(f"Error building table mappings: {e}")
            self._table_id_by_name, self._table_name_by_id = {}, {}

    def _cache_get(self, key: Tuple[str, int]) -> Optional[Dict[str, Any]]:
        """Get cached item if not expired; maintains LRU order."""
        if self.cache_ttl_seconds <= 0:
            return None
        item = self.query_cache.get(key)
        if not item:
            return None
        ts = item.get('__cached_at__')
        if ts is None:
            # Invalid cache record; drop it
            try:
                del self.query_cache[key]
            except Exception:
                pass
            return None
        age = time.time() - ts
        if age > self.cache_ttl_seconds:
            # Expired
            try:
                del self.query_cache[key]
            except Exception:
                pass
            return None
        # Refresh LRU order
        self.query_cache.move_to_end(key)
        # Return a shallow copy with cache metadata
        res = dict(item)
        res.setdefault('cache', {})
        res['cache'].update({'hit': True, 'age_seconds': round(age, 3)})
        return res

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache statistics and configuration."""
        try:
            return {
                'success': True,
                'size': len(self.query_cache),
                'max_items': self.max_cache_items,
                'ttl_seconds': self.cache_ttl_seconds,
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'bypassed': self.cache_bypass,
                'enabled': self.cache_ttl_seconds > 0,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_table_id_from_name(self, table_name: str) -> Optional[int]:
        """
        Get the numeric TableID from a table name by querying INFO.TABLES().

        Args:
            table_name: Name of the table

        Returns:
            Numeric table ID or None if not found
        """
        try:
            self._ensure_table_mappings()
            return (self._table_id_by_name or {}).get(table_name)
        except Exception as e:
            logger.error(f"Error getting table ID for {table_name}: {e}")
            return None

    def _get_table_name_from_id(self, table_id: Any) -> Optional[str]:
        """Map numeric/guid TableID back to human-readable table name."""
        try:
            self._ensure_table_mappings()
            return (self._table_name_by_id or {}).get(table_id)
        except Exception:
            return None

    def _cache_set(self, key: Tuple[str, int], value: Dict[str, Any]) -> None:
        """Insert item into cache and enforce size limit."""
        if self.cache_ttl_seconds <= 0:
            return
        try:
            cached = dict(value)
            cached['__cached_at__'] = time.time()
            self.query_cache[key] = cached
            self.query_cache.move_to_end(key)
            if len(self.query_cache) > self.max_cache_items:
                self.query_cache.popitem(last=False)
        except Exception:
            pass

    def flush_cache(self) -> Dict[str, Any]:
        """Clear the in-memory query cache and return stats."""
        try:
            size_before = len(self.query_cache)
            self.query_cache.clear()
            return {'success': True, 'cleared_items': size_before, 'cache_enabled': self.cache_ttl_seconds > 0}
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return {'success': False, 'error': str(e)}

    def _escape_dax_string(self, text: str) -> str:
        return text.replace("'", "''") if text else text

    def _get_info_columns(self, function_name: str) -> List[str]:
        column_map = {
            'MEASURES': ['Name', 'TableID', 'DataType', 'IsHidden', 'DisplayFolder', 'Expression'],
            'TABLES': ['Name', 'IsHidden', 'ModifiedTime', 'DataCategory'],
            'COLUMNS': ['Name', 'TableID', 'DataType', 'IsHidden', 'IsKey', 'Type'],
            'RELATIONSHIPS': ['FromTable', 'FromColumn', 'ToTable', 'ToColumn', 'IsActive', 'CrossFilterDirection', 'Cardinality']
        }
        return column_map.get(function_name, [])

    def _analyze_dax_error(self, error_msg: str, dax_query: str) -> List[str]:
        suggestions: List[str] = []
        error_lower = (error_msg or '').lower()
        if "table" in error_lower and ("not found" in error_lower or "doesn't exist" in error_lower):
            suggestions.extend([
                "Verify table exists with list_tables",
                "Check case-sensitive spelling",
                "Try single quotes: 'TableName'"
            ])
        if "column" in error_lower and ("not found" in error_lower or "doesn't exist" in error_lower):
            suggestions.extend([
                "Verify column with describe_table",
                "Check case-sensitive spelling",
                "Try [Table][Column] syntax"
            ])
        if "syntax" in error_lower:
            suggestions.extend([
                "Ensure EVALUATE for table expressions",
                "Check balanced delimiters",
                "Verify function parameters"
            ])
        if "function" in error_lower:
            suggestions.extend([
                "Check function name spelling",
                "Verify parameter types/count"
            ])
        if "error" in error_lower and "measure" in error_lower:
            suggestions.extend([
                "Check for circular dependencies",
                "Test expressions individually"
            ])
        if not suggestions:
            suggestions.extend([
                "Check DAX syntax",
                "Verify references exist",
                "Simplify query to isolate issue"
            ])
        return suggestions

    def execute_info_query(self, function_name: str, filter_expr: Optional[str] = None, exclude_columns: Optional[List[str]] = None, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute INFO.* DAX query with optional filtering.
        Automatically converts TableID to Table for MEASURES and COLUMNS.
        Handles table_name parameter by looking up the numeric TableID.

        Args:
            function_name: INFO function name (TABLES, COLUMNS, MEASURES, RELATIONSHIPS)
            filter_expr: Optional DAX filter expression (uses TableID as integer)
            exclude_columns: Optional list of columns to exclude
            table_name: Optional table name to filter by (will be converted to numeric TableID)

        Returns:
            Query result dictionary with Table column instead of TableID
        """
        try:
            # If table_name is provided, look up the numeric TableID and build filter
            if table_name:
                table_id = self._get_table_id_from_name(table_name)
                if table_id is None:
                    return {
                        'success': False,
                        'error': f'Table "{table_name}" not found',
                        'error_type': 'table_not_found',
                        'suggestions': ['Verify table name with list_tables', 'Check case-sensitive spelling']
                    }
                # Build or append to filter expression using numeric TableID
                table_filter = f'[TableID] = {table_id}'
                if filter_expr:
                    filter_expr = f'({filter_expr}) && ({table_filter})'
                else:
                    filter_expr = table_filter

            if exclude_columns:
                cols = self._get_info_columns(function_name)
                selected = [f'"{col}", [{col}]' for col in cols if col not in exclude_columns]
                query = f"EVALUATE SELECTCOLUMNS(INFO.{function_name}(), {', '.join(selected)})"
            else:
                query = f"EVALUATE INFO.{function_name}()"

            if filter_expr:
                query = f"EVALUATE FILTER(INFO.{function_name}(), {filter_expr})"

            result = self.validate_and_execute_dax(query, 0)

            # Convert TableID to Table for better usability
            if result.get('success') and function_name in ['MEASURES', 'COLUMNS']:
                rows = result.get('rows', [])
                for row in rows:
                    if 'TableID' in row and 'Table' not in row:
                        name = self._get_table_name_from_id(row.get('TableID'))
                        if name:
                            row['Table'] = name
                        else:
                            # Fallback to string form of TableID
                            row['Table'] = str(row.get('TableID'))

            return result
        except Exception as e:
            logger.error(f"Error executing INFO query: {e}")
            return {'success': False, 'error': str(e)}

    def search_measures_dax(self, search_text: str, search_in_expression: bool = True, search_in_name: bool = True) -> Dict:
        """
        Search for text in DAX measures.

        Args:
            search_text: Text to search for
            search_in_expression: Whether to search in measure expressions
            search_in_name: Whether to search in measure names

        Returns:
            Search results dictionary
        """
        try:
            escaped_text = self._escape_dax_string(search_text)
            conditions = []

            if search_in_expression:
                conditions.append(f'SEARCH("{escaped_text}", [Expression], 1, 0) > 0')
            if search_in_name:
                conditions.append(f'SEARCH("{escaped_text}", [Name], 1, 0) > 0')

            filter_expr = ' || '.join(conditions) if conditions else 'TRUE()'
            query = f"EVALUATE FILTER(INFO.MEASURES(), {filter_expr})"

            result = self.validate_and_execute_dax(query)
            # Map TableID -> Table name for usability
            if result.get('success'):
                rows = result.get('rows', [])
                for row in rows:
                    if 'TableID' in row and 'Table' not in row:
                        name = self._get_table_name_from_id(row.get('TableID'))
                        row['Table'] = name or str(row.get('TableID'))
            return result
        except Exception as e:
            logger.error(f"Error searching measures: {e}")
            return {'success': False, 'error': str(e)}

    def search_objects_dax(self, pattern: str, object_types: List[str]) -> Dict:
        """
        Search for objects by pattern.

        Args:
            pattern: Search pattern (wildcards removed internally)
            object_types: List of object types to search (tables, columns, measures)

        Returns:
            Search results dictionary
        """
        try:
            search_text = pattern.replace('*', '').replace('?', '')
            escaped_text = self._escape_dax_string(search_text)
            results_list = []

            if "tables" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.TABLES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
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
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.COLUMNS(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "column",
                    "Name", [Name],
                    "TableID", [TableID],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    # Map TableID -> Table name
                    for row in r.get('rows', []):
                        if 'TableID' in row:
                            name = self._get_table_name_from_id(row.get('TableID'))
                            row['Table'] = name or str(row.get('TableID'))
                    results_list.extend(r['rows'])

            if "measures" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.MEASURES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "measure",
                    "Name", [Name],
                    "TableID", [TableID],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden],
                    "DisplayFolder", [DisplayFolder]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    for row in r.get('rows', []):
                        if 'TableID' in row:
                            name = self._get_table_name_from_id(row.get('TableID'))
                            row['Table'] = name or str(row.get('TableID'))
                    results_list.extend(r['rows'])

            return {'success': True, 'results': results_list, 'count': len(results_list)}
        except Exception as e:
            logger.error(f"Error searching objects: {e}")
            return {'success': False, 'error': str(e)}

    def _is_table_expression(self, query: str) -> bool:
        """Check if query is a table expression."""
        table_keywords = [
            'SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER',
            'VALUES', 'ALL', 'INFO.', 'TOPN', 'SAMPLE', 'SUMMARIZECOLUMNS'
        ]
        return any(kw in query.upper() for kw in table_keywords)

    def validate_and_execute_dax(self, query: str, top_n: int = 0, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Validate and execute DAX query with comprehensive error handling.

        Args:
            query: DAX query to execute
            top_n: Optional row limit

        Returns:
            Query result dictionary with success status, data, and metadata
        """
        original_query = query
        try:
            # Ensure ADOMD is available
            if not ADOMD_AVAILABLE:
                return {
                    'success': False,
                    'error': 'ADOMD.NET not available; cannot execute DAX',
                    'error_type': 'adomd_not_available'
                }

            # Pre-execution syntax validation
            syntax_errors = DaxValidator.validate_query_syntax(query)
            if syntax_errors:
                return {
                    'success': False,
                    'error': f"Query validation failed: {'; '.join(syntax_errors)}",
                    'error_type': 'syntax_validation_error',
                    'query': query,
                    'suggestions': [
                        "Fix syntax errors before executing",
                        "Check balanced delimiters"
                    ]
                }

            # Auto-add EVALUATE if needed
            if not query.strip().upper().startswith('EVALUATE'):
                if self._is_table_expression(query):
                    query = f"EVALUATE TOPN({top_n}, {query})" if top_n > 0 else f"EVALUATE {query}"
                else:
                    query = f'EVALUATE ROW("Value", {query})'

            # Cache lookup based on normalized final query and top_n
            cache_key = (query, int(top_n or 0))
            if not bypass_cache:
                cached = self._cache_get(cache_key)
                if cached is not None:
                    # Count hit and emit history event
                    try:
                        self.cache_hits += 1
                    except Exception:
                        pass
                    try:
                        if callable(self._history_logger):
                            self._history_logger({
                                'query': original_query,
                                'final_query': query,
                                'top_n': int(top_n or 0),
                                'success': True,
                                'row_count': cached.get('row_count', 0),
                                'execution_time_ms': 0,
                                'cached': True,
                                'columns': cached.get('columns'),
                                'sample_rows': cached.get('rows', [])[: min(5, len(cached.get('rows', [])))],
                            })
                    except Exception:
                        pass
                    return cached
                else:
                    # Cache miss
                    try:
                        self.cache_misses += 1
                    except Exception:
                        pass
            else:
                try:
                    self.cache_bypass += 1
                except Exception:
                    pass

            start_time = time.time()
            cmd = AdomdCommand(query, self.connection)  # type: ignore
            # Apply command timeout if supported
            try:
                # Some bindings expose CommandTimeout as property, ensure integer seconds
                if hasattr(cmd, 'CommandTimeout'):
                    setattr(cmd, 'CommandTimeout', int(self.command_timeout_seconds))
            except Exception:
                # Do not fail execution if setting timeout isn't supported
                pass
            reader = cmd.ExecuteReader()

            # Get columns
            columns = [reader.GetName(i) for i in range(reader.FieldCount)]
            rows: List[Dict[str, Any]] = []

            # Read rows with proper error handling
            max_rows = 10000  # Safety limit
            row_count = 0

            while reader.Read() and row_count < max_rows:
                row: Dict[str, Any] = {}
                for i, col in enumerate(columns):
                    try:
                        val = reader.GetValue(i)
                        if val is None:
                            row[col] = None
                        elif hasattr(val, 'isoformat'):  # DateTime
                            row[col] = val.isoformat()
                        else:
                            row[col] = str(val)
                    except Exception as col_error:
                        logger.warning(f"Error reading column {col}: {col_error}")
                        row[col] = "<read_error>"

                rows.append(row)
                row_count += 1

            reader.Close()
            execution_time = (time.time() - start_time) * 1000

            result: Dict[str, Any] = {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': round(execution_time, 2),
                'truncated': row_count >= max_rows,
                'query': query
            }

            # Store in cache only on success and if not bypassing cache
            if not bypass_cache:
                self._cache_set(cache_key, result)
                # Add cache metadata to response
                result.setdefault('cache', {})
                result['cache'].update({'hit': False, 'ttl_seconds': self.cache_ttl_seconds})
            # else: bypassed; stats already counted
            # Emit history event (trim heavy payload)
            try:
                if callable(self._history_logger):
                    self._history_logger({
                        'query': original_query,
                        'final_query': query,
                        'top_n': int(top_n or 0),
                        'success': True,
                        'row_count': result.get('row_count', 0),
                        'execution_time_ms': result.get('execution_time_ms'),
                        'cached': False if bypass_cache else bool(result.get('cache', {}).get('hit') is True),
                        'columns': columns,
                        'sample_rows': rows[: min(5, len(rows))],
                    })
            except Exception:
                pass
            return result

        except Exception as e:
            error_msg = str(e)
            # Demote expected DMV-probe errors (e.g., $SYSTEM.TMSCHEMA_* or DISCOVER_*) to debug
            q_upper = (query or "").upper()
            is_expected_dmv_probe = (
                "$SYSTEM.TMSCHEMA_" in q_upper
                or "$SYSTEM.DISCOVER" in q_upper
                or "DISCOVER_" in q_upper
            )
            if is_expected_dmv_probe:
                logger.debug(f"DMV probe failed (expected on some Desktop builds): {error_msg}")
            else:
                logger.error(f"DAX query error: {error_msg}")

            suggestions = self._analyze_dax_error(error_msg, query)

            result: Dict[str, Any] = {
                'success': False,
                'error': error_msg,
                'error_type': 'query_execution_error',
                'query': query,
                'suggestions': suggestions
            }
            # Emit history event for failures
            try:
                if callable(self._history_logger):
                    self._history_logger({
                        'query': original_query,
                        'final_query': query,
                        'top_n': int(top_n or 0),
                        'success': False,
                        'row_count': 0,
                        'execution_time_ms': None,
                        'error': error_msg,
                        'cached': False,
                    })
            except Exception:
                pass
            return result

    def execute_with_table_reference_fallback(self, table_name: str, max_rows: int = 10) -> Dict[str, Any]:
        """
        Execute table query with automatic reference format fallback.

        Tries multiple table reference formats:
        - 'TableName' (single quotes)
        - TableName (direct)
        - [TableName] (brackets)

        Args:
            table_name: Name of table to query
            max_rows: Maximum rows to return

        Returns:
            Query result dictionary
        """
        table_formats = [
            f"'{table_name}'",     # Preferred - single quotes
            table_name,            # Direct name
            f"[{table_name}]",     # Brackets
        ]

        for table_ref in table_formats:
            query = f"EVALUATE TOPN({max_rows}, {table_ref})"
            result = self.validate_and_execute_dax(query)

            if result.get('success'):
                result['table_reference_used'] = table_ref
                result['table_name'] = table_name
                logger.debug(f"Successfully queried table with reference: {table_ref}")
                return result
            else:
                logger.debug(f"Table reference '{table_ref}' failed: {result.get('error')}")

        # All formats failed
        return {
            'success': False,
            'error': f"Could not query table '{table_name}' with any reference format",
            'error_type': 'table_reference_error',
            'attempted_formats': table_formats,
            'suggestions': [
                f"Verify table '{table_name}' exists with list_tables",
                "Check case-sensitivity and special characters"
            ]
        }

    def analyze_dax_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze DAX query for complexity, patterns, and optimization opportunities.

        Args:
            query: DAX query or expression to analyze

        Returns:
            Analysis results with complexity metrics and suggestions
        """
        try:
            # Validate syntax first
            syntax_errors = DaxValidator.validate_query_syntax(query)

            # Analyze complexity
            complexity_analysis = DaxValidator.analyze_complexity(query)

            # Analyze patterns
            good_patterns, anti_patterns = DaxValidator.analyze_patterns(query)

            # Generate optimization suggestions
            optimization_suggestions = DaxValidator.generate_optimization_suggestions(query)

            return {
                'success': True,
                'query': query,
                'syntax_valid': len(syntax_errors) == 0,
                'syntax_errors': syntax_errors,
                'complexity': complexity_analysis,
                'good_patterns': good_patterns,
                'anti_patterns': anti_patterns,
                'optimization_suggestions': optimization_suggestions,
                'security_validated': DaxValidator.validate_identifier(query.split()[0]) if query.strip() else True
            }
        except Exception as e:
            logger.error(f"Error analyzing DAX query: {e}")
            return {'success': False, 'error': str(e)}

    def get_tmsl_definition(self) -> Dict:
        """
        Get TMSL definition for BPA analysis.

        Returns:
            TMSL definition dictionary with metadata
        """
        try:
            if not AMO_AVAILABLE:
                return {'success': False, 'error': 'AMO/TOM not available'}
            from Microsoft.AnalysisServices.Tabular import Server as AMOServer  # type: ignore
            # Resolve database
            db_name = self._get_database_name()
            if not db_name:
                return {'success': False, 'error': 'Could not determine database name'}
            server = AMOServer()
            server.Connect(self.connection.ConnectionString)
            database = server.Databases.GetByName(db_name)
            # Try to serialize with options, fall back if unavailable
            tmsl_json = None
            try:
                from Microsoft.AnalysisServices.Tabular import JsonSerializer, JsonSerializeOptions  # type: ignore
                options = JsonSerializeOptions()
                # Some versions may not support these props; guard with setattr
                try:
                    setattr(options, 'IgnoreInferredObjects', False)
                    setattr(options, 'IgnoreInferredProperties', False)
                    setattr(options, 'IgnoreTimestamps', True)
                except Exception:
                    pass
                tmsl_json = JsonSerializer.SerializeObject(database.Model, options)
            except Exception:
                try:
                    from Microsoft.AnalysisServices.Tabular import JsonSerializer  # type: ignore
                    tmsl_json = JsonSerializer.SerializeObject(database.Model)
                except Exception as inner:
                    server.Disconnect()
                    return {'success': False, 'error': f'TMSL serialization not supported by installed AMO: {inner}'}

            server.Disconnect()
            return {
                'success': True,
                'tmsl': tmsl_json,
                'database_name': db_name,
                'method': 'TMSL extraction via AMO'
            }

        except Exception as e:
            logger.error(f"Error getting TMSL: {e}")
            return {'success': False, 'error': str(e)}
