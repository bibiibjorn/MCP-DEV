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
        '01 Detect PBI Instances': 'detect_powerbi_desktop',
        '01 Connect To Instance': 'connect_to_powerbi',

        # 02 - Schema/Metadata Operations (6 tools - consolidated)
        '02 Table Operations': 'table_operations',
        '02 Column Operations': 'column_operations',
        '02 Measure Operations': 'measure_operations',
        '02 Relationship Operations': 'relationship_operations',
        '02 Search Objects': 'search_objects',
        '02 Search String': 'search_string',

        # 03 - Query & Data + DAX Intelligence (8 tools)
        '03 Run DAX': 'run_dax',
        '03 Standard DAX Analysis': 'dax_intelligence',  # Unified DAX analysis/debug/report
        '03 Validate DAX Query': 'validate_dax_query',
        '03 Get Column Value Distribution': 'get_column_value_distribution',
        '03 Get Column Summary': 'get_column_summary',
        '03 List Relationships': 'list_relationships',
        '03 Get Data Sources': 'get_data_sources',
        '03 Get M Expressions': 'get_m_expressions',

        # 04 - Model Operations (4 tools - consolidated)
        '04 Calculation Group Operations': 'calculation_group_operations',
        '04 Role Operations': 'role_operations',
        '04 Batch Operations': 'batch_operations',
        '04 Manage Transactions': 'manage_transactions',

        # 05 - Analysis (2 tools)
        '05 Live Model Simple Analysis': 'simple_analysis',
        '05 Live Model Full Analysis': 'full_analysis',

        # 06 - Dependencies (2 tools)
        '06 Analyze Measure Dependencies': 'analyze_measure_dependencies',
        '06 Get Measure Impact': 'get_measure_impact',

        # 07 - Export (1 tool)
        '07 Get Live Model Schema': 'get_live_model_schema',

        # 08 - Documentation (2 tools)
        '08 Generate Model Documentation': 'generate_model_documentation_word',
        '08 Update Model Documentation': 'update_model_documentation_word',

        # 09 - Comparison (1 tool)
        '09 Compare Open Live Models': 'compare_pbi_models',

        # 10 - PBIP Analysis - HTML (1 tool)
        '10 PBIP Analysis HTML': 'analyze_pbip_repository',

        # 11 - TMDL Operations (1 unified tool)
        '11 TMDL Operations': 'tmdl_operations',

        # 12 - Help (1 tool)
        '12 Show User Guide': 'show_user_guide',

        # 13 - Full Model (PBIP + Sample) (2 tools)
        '13 PBIP Model - Sample Export': 'export_hybrid_analysis',
        '13 PBIP Model + Sample Analysis': 'analyze_hybrid_model',

        # 14 - Monitoring & Token Usage (1 tool)
        '14 Get Token Usage': 'get_token_usage'
    }

    def __init__(self):
        self.registry = get_registry()
        self._call_count = 0

    def _resolve_tool_name(self, tool_name: str) -> str:
        """
        Resolve tool name to internal handler name.
        Supports both numbered (e.g., '01 Detect PBI Instances') and legacy names.
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
