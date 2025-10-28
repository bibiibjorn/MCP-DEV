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
from core.dax.dax_validator import DaxValidator
from core.config.config_manager import config
from core.validation.constants import QueryLimits
from core.infrastructure.limits_manager import get_limits

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

    # Determine DLL path (this file is in core/infrastructure/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    core_dir = os.path.dirname(script_dir)  # core/
    root_dir = os.path.dirname(core_dir)     # project root
    dll_folder = os.path.join(root_dir, "lib", "dotnet")

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
    # This file is in core/infrastructure/, go up 2 levels to project root
    _script_dir = _os.path.dirname(_os.path.abspath(__file__))
    _core_dir = _os.path.dirname(_script_dir)  # core/
    _root_dir = _os.path.dirname(_core_dir)     # project root
    _dll_folder = _os.path.join(_root_dir, "lib", "dotnet")
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
        self.max_cache_items = getattr(QueryLimits, 'TELEMETRY_BUFFER_SIZE', 200)  # align with central limits where practical
        self.cache_ttl_seconds = max(0, int(config.get('performance.cache_ttl_seconds', 300) or 0))
        self._table_cache = None
        self._table_id_by_name: Optional[Dict[str, Any]] = None
        self._table_name_by_id: Optional[Dict[Any, str]] = None
        self._column_name_by_id: Optional[Dict[Any, str]] = None
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
        reader = None
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
        finally:
            # Ensure reader is always closed, even on exception
            if reader is not None:
                try:
                    reader.Close()
                except Exception:
                    pass

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

    def enumerate_measures_tom(self) -> Dict[str, Any]:
        """Enumerate measures via TOM with Name, Table, Expression."""
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {'success': False, 'error': 'AMO/TOM unavailable', 'error_type': 'amo_not_available'}
        try:
            rows: List[Dict[str, Any]] = []
            model = db.Model
            if hasattr(model, 'Tables'):
                for tbl in model.Tables:
                    try:
                        if hasattr(tbl, 'Measures'):
                            for m in tbl.Measures:
                                rows.append({
                                    'Name': getattr(m, 'Name', ''),
                                    'Table': getattr(tbl, 'Name', ''),
                                    'Expression': getattr(m, 'Expression', '')
                                })
                    except Exception:
                        pass
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'method': 'TOM'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except Exception:
                pass

    def enumerate_columns_tom(self) -> Dict[str, Any]:
        """Enumerate columns via TOM with Name, Table, Type, IsHidden, IsKey."""
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {'success': False, 'error': 'AMO/TOM unavailable', 'error_type': 'amo_not_available'}
        try:
            rows: List[Dict[str, Any]] = []
            model = db.Model
            if hasattr(model, 'Tables'):
                for tbl in model.Tables:
                    try:
                        for col in getattr(tbl, 'Columns', []):
                            rows.append({
                                'Name': getattr(col, 'Name', ''),
                                'Table': getattr(tbl, 'Name', ''),
                                'Type': str(getattr(col, 'Type', '')),
                                'IsHidden': bool(getattr(col, 'IsHidden', False)),
                                'IsKey': bool(getattr(col, 'IsKey', False))
                            })
                    except Exception:
                        pass
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'method': 'TOM'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except Exception:
                pass

    def list_relationships_tom(self) -> Dict[str, Any]:
        """Enumerate relationships via TOM with From/To table/column and IsActive."""
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {'success': False, 'error': 'AMO/TOM unavailable', 'error_type': 'amo_not_available'}
        try:
            rows: List[Dict[str, Any]] = []
            model = db.Model
            if hasattr(model, 'Relationships'):
                for rel in model.Relationships:
                    try:
                        rows.append({
                            'FromTable': getattr(getattr(rel, 'FromTable', None), 'Name', None),
                            'FromColumn': getattr(getattr(rel, 'FromColumn', None), 'Name', None),
                            'ToTable': getattr(getattr(rel, 'ToTable', None), 'Name', None),
                            'ToColumn': getattr(getattr(rel, 'ToColumn', None), 'Name', None),
                            'IsActive': bool(getattr(rel, 'IsActive', False))
                        })
                    except Exception:
                        pass
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
            # Also crawl partitions to infer data sources when DataSources is sparse
            try:
                if hasattr(model, 'Tables'):
                    for tbl in model.Tables:
                        for part in getattr(tbl, 'Partitions', []):
                            try:
                                ds = getattr(part, 'DataSource', None)
                                if ds:
                                    ds_type = type(ds).__name__
                                    entry = {
                                        'DataSourceID': getattr(ds, 'Name', None) or getattr(ds, 'ID', None),
                                        'Name': getattr(ds, 'Name', None) or 'DataSource',
                                        'Type': ds_type,
                                        'FromPartition': getattr(part, 'Name', None),
                                        'Table': getattr(tbl, 'Name', None)
                                    }
                                    # Dedup by DataSourceID + Name
                                    if not any((r.get('DataSourceID') == entry['DataSourceID'] and r.get('Name') == entry['Name']) for r in rows):
                                        rows.append(entry)
                            except Exception:
                                pass
            except Exception:
                pass
            # As a last resort, scan model.Expressions for M that declare sources
            try:
                exprs = getattr(model, 'Expressions', None)
                if exprs is not None:
                    for exp in exprs:
                        try:
                            name = getattr(exp, 'Name', None) or 'Expression'
                            kind = str(getattr(exp, 'Kind', 'M'))
                            if isinstance(kind, str) and '.' in kind:
                                kind = kind.split('.')[-1]
                            if kind.upper() == 'M':
                                entry = {
                                    'DataSourceID': name,
                                    'Name': name,
                                    'Description': 'From Expressions collection',
                                    'Type': 'Expression'
                                }
                                if not any((x.get('DataSourceID') == entry['DataSourceID'] and x.get('Type') == entry['Type']) for x in rows):
                                    rows.append(entry)
                        except Exception:
                            pass
            except Exception:
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
                # FIX: Set to None instead of {} to allow retry on next call
                self._table_id_by_name, self._table_name_by_id = None, None
                return
            id_by_name: Dict[str, Any] = {}
            name_by_id: Dict[Any, str] = {}
            for row in result.get('rows', []):
                # FIX: Check bracketed keys FIRST since Power BI Desktop returns [ID] and [Name]
                name = row.get('[Name]') or row.get('Name') or row.get('[TABLE_NAME]') or row.get('TABLE_NAME')
                # FIX: Check [ID] first - critical bug fix for bracketed column names
                tid = row.get('[ID]') or row.get('ID') or row.get('[TableID]') or row.get('TableID')
                if name is not None and tid is not None:
                    id_by_name[name] = tid
                    name_by_id[tid] = name
            self._table_id_by_name = id_by_name
            self._table_name_by_id = name_by_id
            logger.info(f"Table mappings loaded: {len(id_by_name)} tables")
        except Exception as e:
            logger.error(f"Error building table mappings: {e}")
            # FIX: Set to None instead of {} to allow retry on next call
            self._table_id_by_name, self._table_name_by_id = None, None

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

    def _ensure_column_mappings(self) -> None:
        """Load column ID<->name mappings once for fast lookups (for relationships)."""
        try:
            if self._column_name_by_id is not None:
                return
            # Load all columns from INFO.COLUMNS() to build ID->Name mapping
            result = self.validate_and_execute_dax("EVALUATE INFO.COLUMNS()", 0)
            if not result.get('success'):
                logger.error(f"Failed to load column mappings: {result.get('error')}")
                self._column_name_by_id = None
                return
            name_by_id: Dict[Any, str] = {}
            for row in result.get('rows', []):
                # Check bracketed keys first, then unbracketed
                # For columns, the name is in 'ExplicitName' or 'InferredName', not 'Name'
                col_name = (row.get('[ExplicitName]') or row.get('ExplicitName') or
                           row.get('[InferredName]') or row.get('InferredName') or
                           row.get('[Name]') or row.get('Name') or
                           row.get('[COLUMN_NAME]') or row.get('COLUMN_NAME'))
                col_id = row.get('[ID]') or row.get('ID') or row.get('[ColumnID]') or row.get('ColumnID')
                if col_name is not None and col_id is not None:
                    name_by_id[col_id] = col_name
            self._column_name_by_id = name_by_id
            logger.info(f"Column mappings loaded: {len(name_by_id)} columns")
        except Exception as e:
            logger.error(f"Error building column mappings: {e}")
            self._column_name_by_id = None

    def _get_column_name_from_id(self, column_id: Any) -> Optional[str]:
        """Map numeric/guid ColumnID back to human-readable column name."""
        try:
            self._ensure_column_mappings()
            return (self._column_name_by_id or {}).get(column_id)
        except Exception:
            return None

    def get_table_row_counts(self) -> Dict[str, int]:
        """Get row counts for all tables using DAX queries.

        Returns:
            Dictionary mapping table name to row count
        """
        try:
            # First, get all table names
            tables_result = self.execute_info_query("TABLES")
            if not tables_result.get('success'):
                logger.warning("Failed to get tables for row count query")
                return {}

            tables = tables_result.get('rows', [])
            row_counts = {}

            logger.info(f"Starting row count query for {len(tables)} tables")

            # Query each table's row count using COUNTROWS
            for table in tables:
                table_name = table.get('Name') or table.get('[Name]')
                if not table_name:
                    continue

                # Escape single quotes in table name
                escaped_name = table_name.replace("'", "''")

                try:
                    # Use the simplest possible DAX query: EVALUATE {{ value }}
                    # This returns a single-column, single-row table
                    dax_query = f"EVALUATE {{ COUNTROWS('{escaped_name}') }}"

                    result = self.validate_and_execute_dax(dax_query, top_n=0, bypass_cache=True)

                    if result.get('success'):
                        rows = result.get('rows', [])
                        if rows and len(rows) > 0:
                            # Get the first value from the first row
                            first_row = rows[0]
                            # Try to get any value from the row (column name varies)
                            count_value = None

                            # Log what we got for debugging
                            logger.debug(f"Row data for '{table_name}': {first_row}")

                            # Try all possible keys in the row
                            for key in first_row.keys():
                                if first_row[key] is not None:
                                    count_value = first_row[key]
                                    logger.debug(f"Found value in key '{key}': {count_value}")
                                    break

                            if count_value is not None:
                                try:
                                    row_counts[table_name] = int(count_value)
                                    logger.info(f"✓ Table '{table_name}': {row_counts[table_name]:,} rows")
                                except (ValueError, TypeError) as e:
                                    row_counts[table_name] = 0
                                    logger.warning(f"✗ Table '{table_name}': Could not convert value '{count_value}' (type: {type(count_value)}) to int: {e}")
                            else:
                                row_counts[table_name] = 0
                                logger.warning(f"✗ Table '{table_name}': No value found in result row. Keys: {list(first_row.keys())}")
                        else:
                            row_counts[table_name] = 0
                            logger.warning(f"✗ Table '{table_name}': Empty result")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        row_counts[table_name] = 0
                        logger.warning(f"✗ Table '{table_name}': Query failed - {error_msg}")

                except Exception as e:
                    logger.warning(f"✗ Error getting row count for table '{table_name}': {e}")
                    row_counts[table_name] = 0

            logger.info(f"Fetched row counts for {len(row_counts)} tables via DAX COUNTROWS")
            logger.info(f"Tables with data: {sum(1 for count in row_counts.values() if count > 0)}")
            return row_counts

        except Exception as e:
            logger.error(f"Error fetching row counts via DAX: {e}", exc_info=True)
            return {}

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

    def execute_info_query(self, function_name: str, filter_expr: Optional[str] = None, exclude_columns: Optional[List[str]] = None, table_name: Optional[str] = None, top_n: Optional[int] = None) -> Dict[str, Any]:
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

            # Apply default limit to prevent unlimited returns


            if top_n is None:
                # Use centralized limits manager if available
                try:
                    limits = get_limits()
                    top_n = limits.query.default_info_limit
                except RuntimeError:
                    # Fallback to config if limits_manager not initialized yet
                    top_n = config.get('query.default_info_limit', 100)

# Prefer plain INFO.* for broad compatibility; optionally attempt selective projection
            inner = f"INFO.{function_name}()"
            # Apply TOPN limit to prevent token overflow
            if filter_expr:
                inner_limited = f"TOPN({top_n}, FILTER({inner}, {filter_expr}))"
            else:
                inner_limited = f"TOPN({top_n}, {inner})"
            query = f"EVALUATE {inner_limited}"
            # If caller asked to exclude heavy columns (e.g., Expression), try a projected SELECTCOLUMNS,
            # but fall back to plain INFO.* if projection fails on this Desktop build.
            if exclude_columns:
                cols = self._get_info_columns(function_name)
                try:
                    selected = [f'"{col}", [{col}]' for col in cols if col not in exclude_columns]
                    inner_proj = f"SELECTCOLUMNS({inner}, {', '.join(selected)})"
                    query_proj = f"EVALUATE FILTER({inner_proj}, {filter_expr})" if filter_expr else f"EVALUATE {inner_proj}"
                    res_proj = self.validate_and_execute_dax(query_proj, 0)
                    if res_proj.get('success'):
                        result = res_proj
                    else:
                        # Fallback to plain query
                        result = self.validate_and_execute_dax(query, 0)
                except Exception:
                    result = self.validate_and_execute_dax(query, 0)
            else:
                result = self.validate_and_execute_dax(query, 0)
            # After here, 'result' holds execution

            # Normalize keys and convert TableID to Table for better usability
            if result.get('success'):
                rows = result.get('rows', []) or []
                for row in rows:
                    # Normalize bracketed aliases if any
                    for k in list(row.keys()):
                        if k.startswith('[') and k.endswith(']'):
                            row[k[1:-1]] = row.pop(k)
                    if function_name in ['MEASURES', 'COLUMNS']:
                        if 'Table' not in row and 'TableID' in row:
                            name = self._get_table_name_from_id(row.get('TableID'))
                            row['Table'] = name or (str(row.get('TableID')) if row.get('TableID') is not None else '')
                    elif function_name == 'RELATIONSHIPS':
                        # Convert FromTableID/ToTableID to FromTable/ToTable for relationships
                        if 'FromTable' not in row and 'FromTableID' in row:
                            from_table_id = row.get('FromTableID')
                            if from_table_id is not None:
                                from_name = self._get_table_name_from_id(from_table_id)
                                row['FromTable'] = from_name or str(from_table_id)
                        if 'ToTable' not in row and 'ToTableID' in row:
                            to_table_id = row.get('ToTableID')
                            if to_table_id is not None:
                                to_name = self._get_table_name_from_id(to_table_id)
                                row['ToTable'] = to_name or str(to_table_id)
                        # Convert FromColumnID/ToColumnID to FromColumn/ToColumn
                        if 'FromColumn' not in row and 'FromColumnID' in row:
                            from_column_id = row.get('FromColumnID')
                            if from_column_id is not None:
                                from_col_name = self._get_column_name_from_id(from_column_id)
                                row['FromColumn'] = from_col_name or str(from_column_id)
                        if 'ToColumn' not in row and 'ToColumnID' in row:
                            to_column_id = row.get('ToColumnID')
                            if to_column_id is not None:
                                to_col_name = self._get_column_name_from_id(to_column_id)
                                row['ToColumn'] = to_col_name or str(to_column_id)

            return result
        except Exception as e:
            logger.error(f"Error executing INFO query: {e}")
            return {'success': False, 'error': str(e)}

    # --- Unified fallback helpers to reduce duplication across tools ---
    def _needs_client_filter(self, result: Dict[str, Any], table_name: Optional[str]) -> bool:
        try:
            if not table_name:
                return False
            if not isinstance(result, dict) or not result.get('success'):
                return True
            rows = result.get('rows') or []
            return len(rows) == 0
        except Exception:
            return True

    def _apply_client_side_filter(
        self,
        query_type: str,
        table_name: Optional[str],
        all_rows_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            if not (all_rows_result.get('success') and isinstance(all_rows_result.get('rows'), list)):
                return all_rows_result
            t_norm = str(table_name or '').strip().lower()
            # Build table id -> name map
            id_to_name = {}
            try:
                tbls = self.execute_info_query("TABLES")
                if tbls.get('success'):
                    for t in tbls.get('rows', []) or []:
                        # Prefer bracketed keys first on raw DMV output; execute_info_query() normalizes,
                        # but keep defensive ordering for robustness.
                        tid = t.get('[ID]') or t.get('ID') or t.get('[TableID]') or t.get('TableID')
                        nm = t.get('Name') or t.get('[Name]')
                        if tid is not None and nm:
                            id_to_name[str(tid)] = str(nm).strip().lower()
            except Exception:
                pass

            def _row_table_name(r: Dict[str, Any]) -> Optional[str]:
                # prefer Table then map from TableID
                rt = r.get('Table') or r.get('[Table]') or r.get('TableName') or r.get('[TableName]')
                if isinstance(rt, str) and rt:
                    return rt.strip().lower()
                tid = r.get('TableID') or r.get('[TableID]') or r.get('TABLE_ID') or r.get('[TABLE_ID]')
                if tid is not None and str(tid) in id_to_name:
                    return id_to_name[str(tid)]
                return None

            rows = [r for r in (all_rows_result.get('rows') or []) if _row_table_name(r) == t_norm]
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'client_filtered': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_info_query_with_fallback(self, query_type: str, table_name: Optional[str] = None, exclude_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Single implementation with automatic fallback for table-scoped queries.

        Attempts table-scoped INFO.* first; if empty or failed and a table_name was requested,
        fetches all rows and filters client-side using robust Table/ID mapping.
        """
        result = self.execute_info_query(query_type, table_name=table_name, exclude_columns=exclude_columns)
        if self._needs_client_filter(result, table_name):
            all_res = self.execute_info_query(query_type, exclude_columns=exclude_columns)
            result = self._apply_client_side_filter(query_type, table_name, all_res)
        return result

    def get_measure_details_with_fallback(self, table_name: str, measure_name: str) -> Dict[str, Any]:
        """Fetch measure details scoped to a table with robust fallback.

        Strategy:
        1) Attempt server-side filter on table and name via INFO.MEASURES().
        2) If empty or failed, fetch all measures and filter client-side by
           normalized table name and exact measure name.
        """
        try:
            # Primary: table-scoped query with name filter
            primary = self.execute_info_query(
                "MEASURES",
                filter_expr=f'[Name] = "{self._escape_dax_string(measure_name)}"',
                table_name=table_name,
                exclude_columns=None
            )
            if primary.get('success') and (primary.get('rows') or []):
                return primary

            # Fallback: fetch all and filter client-side
            all_meas = self.execute_info_query("MEASURES")
            if not all_meas.get('success'):
                return primary

            t_norm = str(table_name or '').strip().lower()
            m_norm = str(measure_name or '').strip().lower()

            # Build id->name map once (execute_info_query(TABLES) already normalizes keys)
            id_to_name: Dict[str, str] = {}
            try:
                tbls = self.execute_info_query("TABLES")
                if tbls.get('success'):
                    for t in tbls.get('rows', []) or []:
                        tid = t.get('[ID]') or t.get('ID') or t.get('[TableID]') or t.get('TableID')
                        nm = t.get('Name') or t.get('[Name]')
                        if tid is not None and nm:
                            id_to_name[str(tid)] = str(nm).strip().lower()
            except Exception:
                pass

            def _row_table_name(r: Dict[str, Any]) -> Optional[str]:
                rt = r.get('Table') or r.get('[Table]')
                if isinstance(rt, str) and rt:
                    return rt.strip().lower()
                tid = r.get('TableID') or r.get('[TableID]')
                if tid is not None and str(tid) in id_to_name:
                    return id_to_name[str(tid)]
                return None

            def _row_measure_name(r: Dict[str, Any]) -> Optional[str]:
                rn = r.get('Name') or r.get('[Name]')
                return str(rn).strip().lower() if rn is not None else None

            rows = [r for r in (all_meas.get('rows') or []) if _row_table_name(r) == t_norm and _row_measure_name(r) == m_norm]
            return {'success': True, 'rows': rows, 'row_count': len(rows), 'client_filtered': True}
        except Exception as e:
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

            # Return in a shape compatible with server pagination helpers
            return {'success': True, 'rows': results_list, 'results': results_list, 'row_count': len(results_list), 'count': len(results_list)}
        except Exception as e:
            logger.error(f"Error searching objects: {e}")
            return {'success': False, 'error': str(e)}

    def describe_table(self, table_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive table description with columns, measures, and relationships.

        Args:
            table_name: Name of the table to describe
            args: Additional arguments (page sizes, etc.)

        Returns:
            Dictionary with table info, columns, measures, and relationships
        """
        try:
            result = {
                'success': True,
                'table': table_name,
                'columns': [],
                'measures': [],
                'relationships': []
            }

            # Get table basic info
            table_query = f"EVALUATE FILTER(INFO.TABLES(), [Name] = \"{table_name}\")"
            table_result = self.validate_and_execute_dax(table_query)
            if table_result.get('success') and table_result.get('rows'):
                result['table_info'] = table_result['rows'][0]

            # Get columns
            columns_page_size = args.get('columns_page_size', 50)
            columns_result = self.execute_info_query("COLUMNS", table_name=table_name, top_n=columns_page_size)
            if columns_result.get('success'):
                result['columns'] = columns_result.get('rows', [])
                result['columns_count'] = len(result['columns'])

            # Get measures
            measures_page_size = args.get('measures_page_size', 50)
            measures_result = self.execute_info_query("MEASURES", table_name=table_name, top_n=measures_page_size)
            if measures_result.get('success'):
                result['measures'] = measures_result.get('rows', [])
                result['measures_count'] = len(result['measures'])

            # Get relationships (both from and to this table)
            relationships_page_size = args.get('relationships_page_size', 50)
            relationships_result = self.execute_info_query("RELATIONSHIPS")
            if relationships_result.get('success'):
                all_rels = relationships_result.get('rows', [])
                # Filter for relationships involving this table
                table_rels = [
                    rel for rel in all_rels
                    if rel.get('FromTable') == table_name or
                       rel.get('ToTable') == table_name or
                       rel.get('[FromTable]') == table_name or
                       rel.get('[ToTable]') == table_name
                ]
                result['relationships'] = table_rels[:relationships_page_size]
                result['relationships_count'] = len(result['relationships'])

            return result

        except Exception as e:
            logger.error(f"Error describing table {table_name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Error describing table: {str(e)}',
                'table': table_name
            }

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
            # Additional complete-query structural checks when DEFINE is present
            try:
                if isinstance(query, str) and 'DEFINE' in query.upper():
                    struct_errors = DaxValidator.validate_complete_dax_query(query)
                    # Merge and de-duplicate
                    if struct_errors:
                        for e in struct_errors:
                            if e not in syntax_errors:
                                syntax_errors.append(e)
            except Exception:
                # Non-fatal: continue with basic errors
                pass
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

            reader = None
            try:
                reader = cmd.ExecuteReader()

                # Get columns
                columns = [reader.GetName(i) for i in range(reader.FieldCount)]
                rows: List[Dict[str, Any]] = []

                # Read rows with proper error handling
                max_rows = getattr(QueryLimits, 'SAFETY_MAX_ROWS', 10000)
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
            finally:
                # Ensure reader is always closed, even on exception
                if reader is not None:
                    try:
                        reader.Close()
                    except Exception:
                        pass

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

    # ---- Convenience surface for analyzers expecting a 'model' like interface ----
    # These wrappers allow components such as DependencyAnalyzer to work with the
    # query executor directly without needing a separate model API object.

    def list_measures(self) -> Dict[str, Any] | list[dict]:
        res = self.execute_info_query("MEASURES")
        return res.get('rows', []) if isinstance(res, dict) else []

    def list_columns(self, table: Optional[str] = None) -> Dict[str, Any] | list[dict]:
        res = self.execute_info_query("COLUMNS", table_name=table) if table else self.execute_info_query("COLUMNS")
        return res.get('rows', []) if isinstance(res, dict) else []

    def list_tables(self) -> Dict[str, Any] | list[dict]:
        res = self.execute_info_query("TABLES")
        return res.get('rows', []) if isinstance(res, dict) else []

    def list_relationships(self) -> Dict[str, Any] | list[dict]:
        res = self.execute_info_query("RELATIONSHIPS")
        return res.get('rows', []) if isinstance(res, dict) else []

    def get_measure_details(self, table: str, measure: str) -> Dict[str, Any]:
        res = self.get_measure_details_with_fallback(table, measure)
        # Return a single-object shape for dependency analyzers
        if res.get('success') and res.get('rows'):
            r0 = res['rows'][0]
            return {
                'table': r0.get('Table') or table,
                'name': r0.get('Name') or measure,
                'expression': r0.get('Expression')
            }
        return {}

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

    def get_column_datatypes_tom(self) -> Dict[str, Any]:
        """Return a nested map of {table: {column: dataType}} using AMO/TOM when available.

        Falls back to {'success': False} if AMO/TOM is not available.
        """
        if not AMO_AVAILABLE:
            return {'success': False, 'error': 'AMO/TOM not available'}
        server, db = self._connect_amo_server_db()
        if not server or not db:
            return {'success': False, 'error': 'Could not connect to AMO server or database'}
        try:
            type_map: Dict[str, Dict[str, str]] = {}
            model = db.Model
            if hasattr(model, 'Tables'):
                for tbl in model.Tables:
                    tname = getattr(tbl, 'Name', None)
                    if not tname:
                        continue
                    per_table: Dict[str, str] = {}
                    try:
                        for col in tbl.Columns:
                            cname = getattr(col, 'Name', None)
                            if not cname:
                                continue
                            # DataType is an enum; stringify and normalize
                            raw_dt = getattr(col, 'DataType', None)
                            dt_str = str(raw_dt) if raw_dt is not None else 'Unknown'
                            # Some enums stringify like 'DataType.Int64' — take last token
                            if isinstance(dt_str, str) and '.' in dt_str:
                                dt_str = dt_str.split('.')[-1]
                            # Normalize a few common aliases
                            alias_map = {
                                'Int64': 'Integer',
                                'WholeNumber': 'Integer',
                                'String': 'String',
                                'DateTime': 'DateTime',
                                'Boolean': 'Boolean',
                                'Decimal': 'Decimal',
                                'Double': 'Double',
                                'Currency': 'Currency',
                                'Binary': 'Binary',
                                'Unknown': 'Unknown'
                            }
                            per_table[cname] = alias_map.get(dt_str, dt_str)
                    except Exception:
                        pass
                    if per_table:
                        type_map[tname] = per_table
            return {'success': True, 'map': type_map}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except Exception:
                pass
