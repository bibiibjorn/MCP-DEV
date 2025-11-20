"""
Tool-specific timeout configuration and enforcement.
"""

from typing import Optional, Dict
import logging

logger = logging.getLogger("mcp_powerbi_finvision.tool_timeouts")


class ToolTimeoutManager:
    """Manages per-tool timeout settings."""
    
    # Default timeouts in seconds
    DEFAULT_TIMEOUTS = {
        # Quick metadata queries (1-5s)
        'list_tables': 5,
        'list_columns': 5,
        'list_measures': 5,
        'list_relationships': 10,
        'describe_table': 10,
        'get_measure_details': 5,
        
        # Preview queries (5-15s)
        'preview_table_data': 15,
        'get_column_values': 15,
        'get_column_summary': 15,
        'get_column_value_distribution': 20,
        
        # DAX execution (10-60s)
        'run_dax': 60,
        'run_dax_query': 60,
        'validate_dax_query': 10,
        
        # Search operations (5-20s)
        'search_string': 20,
        'search_objects': 20,
        
        # Analysis operations (30-120s)
        'analyze_query_performance': 120,
        'analyze_measure_dependencies': 30,
        'analyze_column_usage': 30,
        'find_unused_objects': 60,
        'analyze_relationship_cardinality': 60,
        'analyze_column_cardinality': 60,
        'analyze_storage_compression': 60,
        'analyze_m_practices': 30,
        
        # BPA and full analysis (60-300s)
        'analyze_model_bpa': 180,
        'full_analysis': 300,
        'analyze_queries_batch': 180,
        
        # Export operations (15-60s)
        'get_live_model_schema': 15,
        'export_compact_schema': 30,
        'export_relationship_graph': 20,
        'export_tmdl': 60,
        'generate_documentation': 60,

        # Word documentation generation (120-300s)
        'generate_model_documentation_word': 300,
        'update_model_documentation_word': 300,
        'export_interactive_relationship_graph': 60,
        
        # Bulk operations (30-120s)
        'bulk_create_measures': 60,
        'bulk_delete_measures': 60,
        
        # VertiPaq and DMV queries (10-30s)
        'get_data_sources': 15,
        'get_m_expressions': 20,
        
        # Model management (5-30s)
        'upsert_measure': 10,
        'delete_measure': 10,
        'create_calculation_group': 30,
        'delete_calculation_group': 20,
        
        # Security (10-30s)
        'list_roles': 10,
        'validate_rls_coverage': 30,
        
        # Connection (5-15s)
        'detect_powerbi_desktop': 15,
        'connect_to_powerbi': 15,
    }
    
    def __init__(self, custom_timeouts: Optional[Dict[str, int]] = None):
        """
        Initialize timeout manager.
        
        Args:
            custom_timeouts: Optional dict of tool_name -> timeout_seconds
        """
        self.timeouts = self.DEFAULT_TIMEOUTS.copy()
        if custom_timeouts:
            self.timeouts.update(custom_timeouts)
        
        logger.info(f"Timeout manager initialized with {len(self.timeouts)} tool configs")
    
    def get_timeout(self, tool_name: str, default: int = 60) -> int:
        """
        Get timeout for a tool.
        
        Args:
            tool_name: Name of the tool
            default: Default timeout if tool not configured
        
        Returns:
            Timeout in seconds
        """
        # Try exact match first
        timeout = self.timeouts.get(tool_name)
        if timeout is not None:
            return timeout
        
        # Try canonical name (strip friendly prefix)
        if ':' in tool_name:
            canonical = tool_name.split(':', 1)[1].strip()
            canonical = canonical.replace(' ', '_')
            timeout = self.timeouts.get(canonical)
            if timeout is not None:
                return timeout
        
        # Return default
        return default
    
    def set_timeout(self, tool_name: str, timeout_seconds: int):
        """Set custom timeout for a tool."""
        if timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        
        self.timeouts[tool_name] = timeout_seconds
        logger.info(f"Set timeout for {tool_name}: {timeout_seconds}s")
    
    def get_all_timeouts(self) -> Dict[str, int]:
        """Get all configured timeouts."""
        return self.timeouts.copy()
    
    def reset_to_defaults(self):
        """Reset all timeouts to defaults."""
        self.timeouts = self.DEFAULT_TIMEOUTS.copy()
        logger.info("Reset timeouts to defaults")


def create_timeout_manager(config: dict) -> ToolTimeoutManager:
    """Create timeout manager from config."""
    custom = config.get('tool_timeouts', {})
    return ToolTimeoutManager(custom)
