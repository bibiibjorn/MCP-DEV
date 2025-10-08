"""
Connection State Manager for PBIXRay MCP Server

Manages connection state and service initialization to avoid repeated initialization.
"""

import logging
from typing import Any, Dict, Optional, Type
from core.config_manager import config

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
                logger.info("✓ Query executor initialized")
            
            # Initialize performance analyzer
            if not self.performance_analyzer or force_reinit:
                if self.connection_manager and self.connection_manager.connection_string:
                    self.performance_analyzer = EnhancedAMOTraceAnalyzer(self.connection_manager.connection_string)
                    amo_connected = self.performance_analyzer.connect_amo()
                    if amo_connected:
                        logger.info("✓ Performance analyzer initialized with AMO SessionTrace")
                    else:
                        logger.warning("✗ AMO not available - performance analysis limited")
                else:
                    logger.warning("Cannot initialize performance analyzer: no connection string")
            
            # Initialize other managers
            if not self.dax_injector or force_reinit:
                self.dax_injector = DAXInjector(conn)
                logger.debug("✓ DAX injector initialized")
            
            if not self.dependency_analyzer or force_reinit:
                self.dependency_analyzer = DependencyAnalyzer(self.query_executor)
                logger.debug("✓ Dependency analyzer initialized")
            
            if not self.bulk_operations or force_reinit:
                self.bulk_operations = BulkOperationsManager(self.dax_injector)
                logger.debug("✓ Bulk operations initialized")
            
            if not self.calc_group_manager or force_reinit:
                self.calc_group_manager = CalculationGroupManager(conn)
                logger.debug("✓ Calculation group manager initialized")
            
            if not self.partition_manager or force_reinit:
                self.partition_manager = PartitionManager(conn)
                logger.debug("✓ Partition manager initialized")
            
            if not self.rls_manager or force_reinit:
                self.rls_manager = RLSManager(conn, self.query_executor)
                logger.debug("✓ RLS manager initialized")
            
            if not self.model_exporter or force_reinit:
                self.model_exporter = ModelExporter(conn)
                logger.debug("✓ Model exporter initialized")
            
            if not self.performance_optimizer or force_reinit:
                self.performance_optimizer = PerformanceOptimizer(self.query_executor)
                logger.debug("✓ Performance optimizer initialized")
            
            if not self.model_validator or force_reinit:
                self.model_validator = ModelValidator(self.query_executor)
                logger.debug("✓ Model validator initialized")
            
            # Initialize BPA if available
            if config.is_feature_enabled('enable_bpa'):
                self._initialize_bpa(force_reinit)
            
            self._managers_initialized = True
            logger.info("✓ All managers initialized successfully")
            
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
                logger.debug("✓ BPA analyzer initialized")
            except ImportError:
                logger.debug("BPA not available (import error)")
            except FileNotFoundError:
                logger.warning("BPA rules file not found")
            except Exception as e:
                logger.error(f"Error initializing BPA: {e}")
    
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