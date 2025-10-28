"""
User Guide Handler
Handles user guide display
"""
from typing import Dict, Any
import logging
import os
from server.registry import ToolDefinition

logger = logging.getLogger(__name__)

def handle_show_user_guide(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show comprehensive user guide"""
    try:
        # Get the guide path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        guide_path = os.path.join(project_root, 'docs', 'PBIXRAY_Quickstart.md')

        if os.path.exists(guide_path):
            with open(guide_path, 'r', encoding='utf-8') as f:
                guide_content = f.read()

            return {
                'success': True,
                'guide': guide_content,
                'path': guide_path
            }
        else:
            # Return basic usage guide if file not found
            return {
                'success': True,
                'guide': _get_inline_guide(),
                'note': 'Using inline guide (file not found)'
            }

    except Exception as e:
        logger.error(f"Error loading user guide: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error loading user guide: {str(e)}',
            'fallback_guide': _get_inline_guide()
        }

def _get_inline_guide() -> str:
    """Get inline user guide"""
    return """# MCP-PowerBi-Finvision Quick Start Guide

## Connection
1. **detect_pbi_instances** - Detect running Power BI Desktop instances
2. **connect_to_instance** - Connect to a specific instance (usually model_index=0)

## Exploration
- **list_tables** - List all tables in the model
- **list_columns** - List columns (optionally filtered by table)
- **list_measures** - List all measures
- **describe_table** - Get comprehensive table description with columns, measures, relationships
- **get_measure_details** - Get detailed measure information including DAX formula

## Query & Preview
- **run_dax** - Execute DAX queries
- **preview_table_data** - Preview table rows
- **get_column_value_distribution** - Get column value distribution (top N)
- **get_column_summary** - Get column statistics

## Analysis
- **full_analysis** - Comprehensive model analysis with BPA
- **analyze_best_practices_unified** - BPA and M practices analysis
- **analyze_performance_unified** - Performance analysis
- **validate_model_integrity** - Validate model integrity
- **get_vertipaq_stats** - Get VertiPaq storage statistics

## Model Operations
- **upsert_measure** - Create or update a measure
- **delete_measure** - Delete a measure
- **bulk_create_measures** - Bulk create multiple measures
- **bulk_delete_measures** - Bulk delete multiple measures

## Export & Documentation
- **export_tmsl** - Export TMSL definition
- **export_tmdl** - Export TMDL definition
- **export_model_schema** - Export model schema by section
- **generate_model_documentation_word** - Generate Word documentation
- **export_model_explorer_html** - Generate interactive HTML documentation

## Dependencies
- **analyze_measure_dependencies** - Analyze measure dependencies tree
- **get_measure_impact** - Get measure usage impact

## Comparison
- **get_model_summary** - Get compact model summary
- **prepare_model_comparison** - Detect both models for comparison
- **compare_pbi_models** - Compare models after user confirms OLD/NEW

## PBIP Offline Analysis
- **analyze_pbip_repository** - Offline PBIP repository analysis (no connection needed)

For more details, see the full documentation at docs/PBIXRAY_Quickstart.pdf
"""

def register_user_guide_handlers(registry):
    """Register user guide handler"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="show_user_guide",
            description="Show comprehensive user guide",
            handler=handle_show_user_guide,
            input_schema=TOOL_SCHEMAS.get('show_user_guide', {}),
            category="help",
            sort_order=90
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} user guide handlers")
