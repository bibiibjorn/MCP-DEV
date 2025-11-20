"""
Server Handlers Package
Individual handler modules for different tool categories
"""
from server.handlers.connection_handler import register_connection_handlers
from server.handlers.metadata_handler import register_metadata_handlers
from server.handlers.query_handler import register_query_handlers
from server.handlers.model_operations_handler import register_model_operations_handlers
from server.handlers.analysis_handler import register_analysis_handlers
from server.handlers.dependencies_handler import register_dependencies_handlers
from server.handlers.export_handler import register_export_handlers
from server.handlers.documentation_handler import register_documentation_handlers
from server.handlers.comparison_handler import register_comparison_handlers
from server.handlers.pbip_handler import register_pbip_handlers
from server.handlers.tmdl_handler import register_tmdl_handlers
from server.handlers.dax_context_handler import register_dax_handlers
from server.handlers.user_guide_handler import register_user_guide_handlers
from server.handlers.hybrid_analysis_handler import register_hybrid_analysis_handlers
from server.handlers.token_usage_handler import register_token_usage_handlers
# Workflow handlers are internalized and not registered as public tools

# Phase 1 Consolidated Operations (Tool Consolidation Plan)
from server.handlers.table_operations_handler import register_table_operations_handler
from server.handlers.column_operations_handler import register_column_operations_handler
from server.handlers.measure_operations_handler import register_measure_operations_handler

# Phase 2 Extended CRUD Operations
from server.handlers.relationship_operations_handler import register_relationship_operations_handler
from server.handlers.calculation_group_operations_handler import register_calculation_group_operations_handler
from server.handlers.role_operations_handler import register_role_operations_handler

# Phase 3 Batch Operations & Transactions
from server.handlers.batch_operations_handler import register_batch_operations_handler
from server.handlers.transaction_management_handler import register_transaction_management_handler

def register_all_handlers(registry):
    """Register all handlers with the registry"""
    # Register all proper handlers (no more bridge!)
    register_connection_handlers(registry)

    # Phase 1: Consolidated operations (replaces parts of metadata handlers)
    register_table_operations_handler(registry)
    register_column_operations_handler(registry)
    register_measure_operations_handler(registry)

    # Phase 2: Extended CRUD operations
    register_relationship_operations_handler(registry)
    register_calculation_group_operations_handler(registry)
    register_role_operations_handler(registry)

    # Phase 3: Batch operations & transactions
    register_batch_operations_handler(registry)
    register_transaction_management_handler(registry)

    register_metadata_handlers(registry)
    register_query_handlers(registry)
    register_model_operations_handlers(registry)
    register_analysis_handlers(registry)
    register_dependencies_handlers(registry)
    register_export_handlers(registry)
    register_documentation_handlers(registry)
    register_comparison_handlers(registry)
    register_pbip_handlers(registry)
    register_tmdl_handlers(registry)
    register_dax_handlers(registry)
    register_user_guide_handlers(registry)
    register_hybrid_analysis_handlers(registry)
    register_token_usage_handlers(registry)
    # Workflow handlers are internalized and not registered as public tools

__all__ = [
    'register_all_handlers',
]
