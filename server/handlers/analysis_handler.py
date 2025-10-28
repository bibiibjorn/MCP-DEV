"""
Analysis Handler
Handles model analysis tools including BPA, performance, validation, and VertiPaq stats
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_full_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensive model analysis with BPA"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    summary_only = args.get('summary_only', False)

    # Use the analysis orchestrator
    return agent_policy.analysis_orch.full_analysis(connection_state, summary_only)

def handle_analyze_best_practices_unified(args: Dict[str, Any]) -> Dict[str, Any]:
    """BPA and M practices analysis"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    summary_only = args.get('summary_only', False)

    return agent_policy.analysis_orch.analyze_best_practices(connection_state, summary_only)

def handle_analyze_performance_unified(args: Dict[str, Any]) -> Dict[str, Any]:
    """Performance analysis (queries/cardinality/storage)"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    summary_only = args.get('summary_only', False)

    return agent_policy.analysis_orch.analyze_performance(connection_state, summary_only)

def handle_validate_model_integrity(args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate model integrity"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_validator = connection_state.model_validator
    if not model_validator:
        return ErrorHandler.handle_manager_unavailable('model_validator')

    return model_validator.validate_model()

def handle_get_vertipaq_stats(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get VertiPaq storage statistics"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    qe = connection_state.query_executor
    if not qe:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    # Get storage stats from DMV
    try:
        # Use INFO.STORAGETABLECOLUMNSEGMENTS for VertiPaq stats
        result = qe.execute_info_query("STORAGETABLECOLUMNSEGMENTS")

        if result.get('success'):
            rows = result.get('rows', [])

            # Aggregate stats by table
            table_stats = {}
            for row in rows:
                table = row.get('Table') or row.get('[Table]')
                size = row.get('UsedSize') or row.get('[UsedSize]', 0)

                if table:
                    if table not in table_stats:
                        table_stats[table] = {
                            'table': table,
                            'total_size': 0,
                            'segment_count': 0
                        }
                    table_stats[table]['total_size'] += int(size) if size else 0
                    table_stats[table]['segment_count'] += 1

            # Convert to list and sort by size
            stats_list = list(table_stats.values())
            stats_list.sort(key=lambda x: x['total_size'], reverse=True)

            total_size = sum(s['total_size'] for s in stats_list)

            return {
                'success': True,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'table_count': len(stats_list),
                'tables': stats_list
            }
        else:
            return result

    except Exception as e:
        logger.error(f"Error getting VertiPaq stats: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error getting VertiPaq stats: {str(e)}'
        }

def register_analysis_handlers(registry):
    """Register all analysis handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="full_analysis",
            description="Comprehensive model analysis with BPA",
            handler=handle_full_analysis,
            input_schema=TOOL_SCHEMAS.get('full_analysis', {}),
            category="analysis",
            sort_order=27
        ),
        ToolDefinition(
            name="analyze_best_practices_unified",
            description="BPA and M practices analysis",
            handler=handle_analyze_best_practices_unified,
            input_schema=TOOL_SCHEMAS.get('analyze_best_practices_unified', {}),
            category="analysis",
            sort_order=28
        ),
        ToolDefinition(
            name="analyze_performance_unified",
            description="Performance analysis (queries/cardinality/storage)",
            handler=handle_analyze_performance_unified,
            input_schema=TOOL_SCHEMAS.get('analyze_performance_unified', {}),
            category="analysis",
            sort_order=29
        ),
        ToolDefinition(
            name="validate_model_integrity",
            description="Validate model integrity",
            handler=handle_validate_model_integrity,
            input_schema=TOOL_SCHEMAS.get('validate_model_integrity', {}),
            category="analysis",
            sort_order=30
        ),
        ToolDefinition(
            name="get_vertipaq_stats",
            description="Get VertiPaq storage statistics",
            handler=handle_get_vertipaq_stats,
            input_schema=TOOL_SCHEMAS.get('get_vertipaq_stats', {}),
            category="analysis",
            sort_order=31
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} analysis handlers")
