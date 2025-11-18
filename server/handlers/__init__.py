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

def register_all_handlers(registry):
    """Register all handlers with the registry"""
    # Register all proper handlers (no more bridge!)
    register_connection_handlers(registry)
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

__all__ = [
    'register_all_handlers',
]
