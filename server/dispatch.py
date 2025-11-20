"""
Central Tool Dispatcher
Routes tool calls to appropriate handlers with error handling
"""
from typing import Dict, Any
import logging
from server.registry import get_registry
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

class ToolDispatcher:
    """Dispatches tool calls to registered handlers"""

    # Mapping of numbered tool names (from manifest.json) to internal handler names
    TOOL_NAME_MAP = {
        # 01 - Connection (2 tools)
        '01_detect_pbi_instances': 'detect_powerbi_desktop',
        '01_connect_to_instance': 'connect_to_powerbi',

        # 02 - Schema/Metadata Operations (12 tools - consolidated + individual)
        # Phase 1 Consolidated Operations (preferred)
        '02_table_operations': 'table_operations',
        '02_column_operations': 'column_operations',
        '02_measure_operations': 'measure_operations',
        '02_relationship_operations': 'relationship_operations',

        # Legacy Individual Operations (for backward compatibility)
        '02_list_tables': 'list_tables',
        '02_describe_table': 'describe_table',
        '02_list_columns': 'list_columns',
        '02_list_measures': 'list_measures',
        '02_get_measure_details': 'get_measure_details',
        '02_list_calculated_columns': 'list_calculated_columns',
        '02_search_objects': 'search_objects',
        '02_search_string': 'search_string',

        # 03 - Query & Data + DAX Intelligence (8 tools)
        '03_run_dax': 'run_dax',
        '03_standard_dax_analysis': 'dax_intelligence',  # Unified DAX analysis/debug/report
        '03_validate_dax_query': 'validate_dax_query',
        '03_get_column_value_distribution': 'get_column_value_distribution',
        '03_get_column_summary': 'get_column_summary',
        '03_list_relationships': 'list_relationships',
        '03_get_data_sources': 'get_data_sources',
        '03_get_m_expressions': 'get_m_expressions',

        # 04 - Model Operations (13 tools - consolidated + individual)
        # Phase 2-3 Consolidated Operations (preferred)
        '04_calculation_group_operations': 'calculation_group_operations',
        '04_role_operations': 'role_operations',
        '04_batch_operations': 'batch_operations',
        '04_manage_transactions': 'manage_transactions',

        # Legacy Individual Operations (for backward compatibility)
        '04_upsert_measure': 'upsert_measure',
        '04_delete_measure': 'delete_measure',
        '04_bulk_create_measures': 'bulk_create_measures',
        '04_bulk_delete_measures': 'bulk_delete_measures',
        '04_list_calculation_groups': 'list_calculation_groups',
        '04_create_calculation_group': 'create_calculation_group',
        '04_delete_calculation_group': 'delete_calculation_group',
        '04_list_roles': 'list_roles',

        # 05 - Analysis (2 tools)
        '05_live_model_simple_analysis': 'simple_analysis',
        '05_live_model_full_analysis': 'full_analysis',

        # 06 - Dependencies (2 tools)
        '06_analyze_measure_dependencies': 'analyze_measure_dependencies',
        '06_get_measure_impact': 'get_measure_impact',

        # 07 - Export (1 tool)
        '07_get_live_model_schema': 'get_live_model_schema',

        # 08 - Documentation (2 tools)
        '08_generate_model_documentation_word': 'generate_model_documentation_word',
        '08_update_model_documentation_word': 'update_model_documentation_word',

        # 09 - Comparison (1 tool)
        '09_Compare_Open_Live_Models': 'compare_pbi_models',

        # 10 - PBIP Analysis - HTML (1 tool)
        '10_pbip_analysis_html': 'analyze_pbip_repository',

        # 11 - TMDL Operations (1 unified tool)
        '11_tmdl_operations': 'tmdl_operations',

        # 12 - Help (1 tool)
        '12_show_user_guide': 'show_user_guide',

        # 13 - Full Model (PBIP + Sample) (2 tools)
        '13_full_model_pbip_and_sample_export': 'export_hybrid_analysis',
        '13_full_model_pbip_and_sample_analysis': 'analyze_hybrid_model',

        # 14 - Monitoring & Token Usage (1 tool)
        '14_get_token_usage': 'get_token_usage'
    }

    def __init__(self):
        self.registry = get_registry()
        self._call_count = 0

    def _resolve_tool_name(self, tool_name: str) -> str:
        """
        Resolve tool name to internal handler name.
        Supports both numbered (e.g., '01_detect_pbi_instances') and legacy names.
        """
        # If it's a numbered name, map it to internal name
        if tool_name in self.TOOL_NAME_MAP:
            return self.TOOL_NAME_MAP[tool_name]
        # Otherwise, assume it's already an internal/legacy name
        return tool_name

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch a tool call to its handler

        Args:
            tool_name: Name of the tool to invoke (numbered or legacy)
            arguments: Tool arguments

        Returns:
            Result dictionary from the handler
        """
        self._call_count += 1

        try:
            # Resolve to internal handler name
            internal_name = self._resolve_tool_name(tool_name)

            # Check if tool exists
            if not self.registry.has_tool(internal_name):
                logger.warning(f"Unknown tool requested: {tool_name} (resolved to: {internal_name})")
                return {
                    'success': False,
                    'error': f'Unknown tool: {tool_name}',
                    'error_type': 'unknown_tool',
                    'available_tools': [t.name for t in self.registry.get_all_tools()[:10]]
                }

            # Get handler
            handler = self.registry.get_handler(internal_name)

            # Execute handler
            logger.debug(f"Dispatching tool: {tool_name} -> {internal_name}")
            result = handler(arguments)

            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.warning(f"Handler for {internal_name} returned non-dict: {type(result)}")
                result = {'success': True, 'result': result}

            return result

        except Exception as e:
            logger.error(f"Error dispatching tool {tool_name}: {e}", exc_info=True)
            return ErrorHandler.handle_unexpected_error(tool_name, e)

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        return {
            'total_calls': self._call_count,
            'registered_tools': len(self.registry.get_all_tools()),
            'categories': self.registry.list_categories()
        }
