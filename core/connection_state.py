"""
Connection State Manager for PBIXRay MCP Server

Manages connection state and service initialization to avoid repeated initialization.
"""

import logging
from typing import Any, Dict, Optional, Type
from core.config_manager import config
import threading

logger = logging.getLogger(__name__)


class ConnectionState:
    """
    Manages connection state and service instances to avoid repeated initialization.
    """
    
    def __init__(self):
        """Initialize connection state manager."""
        self.connection_manager = None
        self.query_executor = None
        self.performance_analyzer = None
        self.dax_injector = None
        self.bpa_analyzer = None
        self.dependency_analyzer = None
        self.bulk_operations = None
        self.calc_group_manager = None
        self.partition_manager = None
        self.rls_manager = None
        self.model_exporter = None
        self.performance_optimizer = None
        self.model_validator = None
        
        self._is_connected = False
        self._connection_info = None
        self._managers_initialized = False
        # Rolling query history (lightweight)
        self._query_history = []
        self._query_history_max = 200
        # Agent context memory and safety limits
        self._context: Dict[str, Any] = {}
        self._safety_limits: Dict[str, Any] = {
            'max_rows_per_call': 10000,
        }
        # Performance baselines and last result summary
        self._perf_baselines: Dict[str, Any] = {}
        self._last_result_meta: Dict[str, Any] = {}
        # Init lock for lazy managers
        self._init_lock = threading.RLock()
    
    def is_connected(self) -> bool:
        """Check if currently connected to Power BI."""
        return (self._is_connected and 
                self.connection_manager is not None and 
                self.connection_manager.is_connected())
    
    def set_connection_manager(self, connection_manager):
        """Set the connection manager instance."""
        self.connection_manager = connection_manager
        self._is_connected = connection_manager.is_connected() if connection_manager else False
    
    def initialize_managers(self, force_reinit: bool = False):
        """
        Initialize all service managers.
        
        Args:
            force_reinit: Force reinitialization even if already initialized
        """
        if self._managers_initialized and not force_reinit:
            logger.debug("Managers already initialized, skipping")
            return
        
        if not self.is_connected() or not self.connection_manager:
            logger.warning("Cannot initialize managers: not connected")
            return
        
        try:
            conn = self.connection_manager.get_connection()
            
            # Import managers
            from core.query_executor import OptimizedQueryExecutor
            from core.performance_analyzer import EnhancedAMOTraceAnalyzer
            from core.dax_injector import DAXInjector
            from core.dependency_analyzer import DependencyAnalyzer
            from core.bulk_operations import BulkOperationsManager
            from core.calculation_group_manager import CalculationGroupManager
            from core.partition_manager import PartitionManager
            from core.rls_manager import RLSManager
            from core.model_exporter import ModelExporter
            from core.performance_optimizer import PerformanceOptimizer
            from core.model_validator import ModelValidator
            
            # Initialize query executor first (others depend on it)
            if not self.query_executor or force_reinit:
                self.query_executor = OptimizedQueryExecutor(conn)
                # Register history logger to capture executions
                try:
                    self.query_executor.set_history_logger(self._history_logger)
                except Exception:
                    pass
                logger.info("[OK] Query executor initialized")
            
            # Initialize performance analyzer with AMO SessionTrace (now fixed!)
            if not self.performance_analyzer or force_reinit:
                if self.connection_manager and self.connection_manager.connection_string:
                    self.performance_analyzer = EnhancedAMOTraceAnalyzer(self.connection_manager.connection_string)
                    amo_connected = self.performance_analyzer.connect_amo()

                    # Respect configured trace mode for clearer logs
                    try:
                        mode = str(config.get('performance.trace_mode', 'full') or 'full').lower()
                    except Exception:
                        mode = 'full'
                    if mode == 'off':
                        logger.info("[OK] Performance analyzer initialized (trace_mode=off; basic timing only)")
                    elif mode == 'basic':
                        logger.info("[OK] Performance analyzer initialized (trace_mode=basic; basic timing preferred)")
                    else:
                        if amo_connected:
                            logger.info("[OK] Performance analyzer initialized (AMO SessionTrace with event subscriptions)")
                        else:
                            logger.warning("[WARN] AMO not available - performance analysis will use basic timing")
                else:
                    logger.warning("Cannot initialize performance analyzer: no connection string")
            
            # Initialize other managers
            if not self.dax_injector or force_reinit:
                self.dax_injector = DAXInjector(conn)
                logger.debug("[OK] DAX injector initialized")
            
            if not self.dependency_analyzer or force_reinit:
                self.dependency_analyzer = DependencyAnalyzer(self.query_executor)
                logger.debug("[OK] Dependency analyzer initialized")
            
            if not self.bulk_operations or force_reinit:
                self.bulk_operations = BulkOperationsManager(self.dax_injector)
                logger.debug("[OK] Bulk operations initialized")
            
            if not self.calc_group_manager or force_reinit:
                self.calc_group_manager = CalculationGroupManager(conn)
                logger.debug("[OK] Calculation group manager initialized")
            
            if not self.partition_manager or force_reinit:
                self.partition_manager = PartitionManager(conn)
                logger.debug("[OK] Partition manager initialized")
            
            if not self.rls_manager or force_reinit:
                self.rls_manager = RLSManager(conn, self.query_executor)
                logger.debug("[OK] RLS manager initialized")
            
            if not self.model_exporter or force_reinit:
                self.model_exporter = ModelExporter(conn)
                logger.debug("[OK] Model exporter initialized")
            
            if not self.performance_optimizer or force_reinit:
                self.performance_optimizer = PerformanceOptimizer(self.query_executor)
                logger.debug("[OK] Performance optimizer initialized")
            
            if not self.model_validator or force_reinit:
                self.model_validator = ModelValidator(self.query_executor)
                logger.debug("[OK] Model validator initialized")
            
            # Initialize BPA if available
            if config.is_feature_enabled('enable_bpa'):
                self._initialize_bpa(force_reinit)
            
            self._managers_initialized = True
            logger.info("[OK] All managers initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing managers: {e}", exc_info=True)
            self._managers_initialized = False
    
    def _initialize_bpa(self, force_reinit: bool = False):
        """Initialize BPA analyzer if available."""
        if not self.bpa_analyzer or force_reinit:
            try:
                from core.bpa_analyzer import BPAAnalyzer
                import os
                
                script_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(script_dir)
                rules_path = os.path.join(parent_dir, "core", "bpa.json")
                
                self.bpa_analyzer = BPAAnalyzer(rules_path)
                logger.debug("[OK] BPA analyzer initialized")
            except ImportError:
                logger.debug("BPA not available (import error)")
            except FileNotFoundError:
                logger.warning("BPA rules file not found")
            except Exception as e:
                logger.error(f"Error initializing BPA: {e}")

    # ---- Thread-safe lazy manager ensure helpers ----
    def _ensure_model_exporter(self):
        """Thread-safe lazy initialization for model_exporter manager."""
        if self.model_exporter is not None:
            return self.model_exporter
        with self._init_lock:
            if self.model_exporter is None:
                try:
                    from core.model_exporter import ModelExporter
                    conn = self.connection_manager.get_connection() if self.connection_manager else None
                    if conn is None:
                        raise RuntimeError("No active connection")
                    self.model_exporter = ModelExporter(conn)
                    logger.info("[OK] Initialized model_exporter")
                except Exception as e:
                    logger.error(f"Failed to initialize model_exporter: {e}")
                    raise
        return self.model_exporter
    
    def get_manager(self, manager_name: str) -> Optional[Any]:
        """
        Get a specific manager instance.
        
        Args:
            manager_name: Name of the manager to retrieve
            
        Returns:
            Manager instance or None if not available
        """
        return getattr(self, manager_name, None)
    
    def cleanup(self):
        """Clean up connection state and managers."""
        self.query_executor = None
        self.performance_analyzer = None
        self.dax_injector = None
        self.bpa_analyzer = None
        self.dependency_analyzer = None
        self.bulk_operations = None
        self.calc_group_manager = None
        self.partition_manager = None
        self.rls_manager = None
        self.model_exporter = None
        self.performance_optimizer = None
        self.model_validator = None
        
        self._is_connected = False
        self._connection_info = None
        self._managers_initialized = False
        
        logger.info("Connection state cleaned up")

    # ---- Query history helpers ----
    def _history_logger(self, entry: dict) -> None:
        """Internal callback used by query executor to log execution metadata."""
        try:
            # Attach timestamp and minimal connection hint
            import time as _t
            entry = dict(entry or {})
            entry.setdefault('ts', _t.time())
            try:
                if self.connection_manager:
                    info = self.connection_manager.get_instance_info() or {}
                    if 'port' in info:
                        entry.setdefault('port', info.get('port'))
            except Exception:
                pass
            self._query_history.append(entry)
            if len(self._query_history) > self._query_history_max:
                # Trim oldest
                overflow = len(self._query_history) - self._query_history_max
                if overflow > 0:
                    del self._query_history[0:overflow]
            # Update last result meta for successes
            try:
                if entry.get('success'):
                    keys = ['query', 'final_query', 'top_n', 'row_count', 'execution_time_ms', 'cached', 'columns', 'sample_rows', 'ts']
                    self._last_result_meta = {k: entry.get(k) for k in keys if k in entry}
            except Exception:
                pass
        except Exception:
            # Never break execution on history issues
            pass

    def get_query_history(self, limit: Optional[int] = None) -> list[dict]:
        """Return newest-first history up to limit (default: all)."""
        data = list(self._query_history)
        data.sort(key=lambda x: x.get('ts', 0), reverse=True)
        if isinstance(limit, int) and limit > 0:
            return data[:limit]
        return data

    def clear_query_history(self) -> int:
        """Clear history and return number of items removed."""
        n = len(self._query_history)
        self._query_history.clear()
        return n

    # ---- Last result summary ----
    def get_last_result_summary(self) -> Dict[str, Any]:
        if not self._last_result_meta:
            return {'success': False, 'error': 'No recent results'}
        out = dict(self._last_result_meta)
        out['success'] = True
        return out

    # ---- Performance baselines ----
    def set_perf_baseline_record(self, name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        if not name:
            return {'success': False, 'error': 'Baseline name required'}
        self._perf_baselines[name] = dict(record or {})
        return {'success': True, 'name': name, 'baseline': self._perf_baselines[name]}

    def get_perf_baseline(self, name: str) -> Dict[str, Any]:
        if name in self._perf_baselines:
            return {'success': True, 'name': name, 'baseline': dict(self._perf_baselines[name])}
        return {'success': False, 'error': f'Baseline "{name}" not found'}

    def list_perf_baselines(self) -> Dict[str, Any]:
        return {'success': True, 'baselines': {k: v for k, v in self._perf_baselines.items()}}

    # ---- Context helpers ----
    def set_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge provided key/values into context and return current context."""
        try:
            self._context.update(dict(data or {}))
        except Exception:
            pass
        return dict(self._context)

    def get_context(self, keys: Optional[list[str]] = None) -> Dict[str, Any]:
        """Return full context or only selected keys."""
        if keys is None:
            return dict(self._context)
        out: Dict[str, Any] = {}
        for k in keys:
            if k in self._context:
                out[k] = self._context[k]
        return out

    # ---- Safety limits ----
    def set_safety_limits(self, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Update safety limits; unknown keys ignored. Returns current limits."""
        allowed = {'max_rows_per_call'}
        try:
            for k, v in dict(limits or {}).items():
                if k in allowed:
                    self._safety_limits[k] = v
        except Exception:
            pass
        return dict(self._safety_limits)

    def get_safety_limits(self) -> Dict[str, Any]:
        return dict(self._safety_limits)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current connection and manager status.
        
        Returns:
            Status dictionary with connection and manager states
        """
        managers_status = {}
        manager_names = [
            'query_executor', 'performance_analyzer', 'dax_injector',
            'bpa_analyzer', 'dependency_analyzer', 'bulk_operations',
            'calc_group_manager', 'partition_manager', 'rls_manager',
            'model_exporter', 'performance_optimizer', 'model_validator'
        ]
        
        for name in manager_names:
            managers_status[name] = getattr(self, name) is not None
        
        return {
            'connected': self.is_connected(),
            'managers_initialized': self._managers_initialized,
            'managers': managers_status,
            'connection_info': self._connection_info
        }


# Global connection state instance
connection_state = ConnectionState()