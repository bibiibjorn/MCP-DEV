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
    # Note: Tool names must match pattern ^[a-zA-Z0-9_-]{1,64}$ (no spaces allowed)
    TOOL_NAME_MAP = {
        # 01 - Connection (2 tools)
        '01_Detect_PBI_Instances': 'detect_powerbi_desktop',
        '01_Connect_To_Instance': 'connect_to_powerbi',

        # 02 - Schema/Metadata & Model Operations (10 tools)
        '02_Search_Objects': 'search_objects',
        '02_Search_String': 'search_string',
        '02_Column_Operations': 'column_operations',
        '02_Measure_Operations': 'measure_operations',
        '02_Relationship_Operations': 'relationship_operations',
        '02_TMDL_Operations': 'tmdl_operations',
        '02_Calculation_Group_Operations': 'calculation_group_operations',
        '02_Role_Operations': 'role_operations',
        '02_Batch_Operations': 'batch_operations',
        '02_Manage_Transactions': 'manage_transactions',

        # 03 - DAX & Dependencies (6 tools)
        '03_Run_DAX': 'run_dax',
        '03_Standard_DAX_Analysis': 'dax_intelligence',
        '03_Analyze_Measure_Dependencies': 'analyze_measure_dependencies',
        '03_Get_Measure_Impact': 'get_measure_impact',
        '03_Usage_Analysis_Measures_Columns': 'column_usage_mapping',
        '03_Export_All_DAX_Measures': 'export_dax_measures',

        # 04 - Data Sources (2 tools)
        '04_Get_Data_Sources': 'get_data_sources',
        '04_Get_M_Expressions': 'get_m_expressions',

        # 05 - Live Model Analysis (2 tools)
        '05_Live_Model_Simple_Analysis': 'simple_analysis',
        '05_Live_Model_Full_Analysis': 'full_analysis',

        # 06 - Documentation (2 tools)
        '06_Generate_Model_Documentation': 'generate_model_documentation_word',
        '06_Update_Model_Documentation': 'update_model_documentation_word',

        # 07 - Comparison (1 tool)
        '07_Compare_Open_Live_Models': 'compare_pbi_models',

        # 08 - PBIP Analysis - HTML (1 tool)
        '08_PBIP_Analysis_HTML': 'analyze_pbip_repository',

        # 09 - Hybrid Analysis (PBIP + Sample) (2 tools)
        '09_PBIP_Model_Sample_Export': 'export_hybrid_analysis',
        '09_PBIP_Model_Sample_Analysis': 'analyze_hybrid_model',

        # 10 - Help (1 tool)
        '10_Show_User_Guide': 'show_user_guide',

        # 11 - Dependency Analysis HTML PBIP (1 tool)
        '11_Dependency_Analysis_HTML_PBIP': 'pbip_dependency_analysis',

        # 12 - Slicer Operations Analysis HTML PBIP (1 tool)
        '12_Slicer_Operations_Analysis_HTML_PBIP': 'slicer_operations',

        # 13 - Aggregation Analysis HTML PBIP (1 tool)
        '13_Aggregation_Analysis_HTML_PBIP': 'analyze_aggregation',

        # 14 - Visual & Filter Analysis PBIP (1 tool)
        '14_Visual_Filter_Analysis_PBIP': 'report_info',

        # 15 - Bookmark Analysis HTML PBIP (1 tool)
        '15_Bookmark_Analysis_HTML_PBIP': 'analyze_bookmarks',

        # 16 - Theme Compliance Analysis HTML PBIP (1 tool)
        '16_Theme_Compliance_HTML_PBIP': 'analyze_theme_compliance'
    }

    def __init__(self):
        self.registry = get_registry()
        self._call_count = 0

    def _resolve_tool_name(self, tool_name: str) -> str:
        """
        Resolve tool name to internal handler name.
        Supports both numbered (e.g., '01_Detect_PBI_Instances') and legacy names.
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
