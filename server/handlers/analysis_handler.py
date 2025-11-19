"""
Analysis Handler
Handles model analysis tools including simple analysis, full analysis, BPA, performance, and validation
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.utilities.business_impact import enrich_issue_with_impact, add_impact_summary

logger = logging.getLogger(__name__)

def handle_simple_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fast model operations based on Microsoft Official MCP Server operations.

    Modes:
    - 'tables': Ultra-fast table list (< 500ms) - Microsoft MCP List operation
    - 'stats': Fast model statistics (< 1s) - Microsoft MCP GetStats operation
    - 'measures': List measures (optional table filter) - Microsoft MCP Measure List operation
    - 'measure': Get measure details (requires table + measure_name) - Microsoft MCP Measure Get operation
    - 'relationships': List relationships - Microsoft MCP Relationship List operation
    - 'calculation_groups': List calculation groups - Microsoft MCP ListGroups operation
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    # Extract mode parameter (default: stats)
    mode = args.get('mode', 'stats')

    # Route to appropriate function based on mode
    if mode == 'tables':
        result = agent_policy.analysis_orch.list_tables_simple(connection_state)
    elif mode == 'stats':
        result = agent_policy.analysis_orch.simple_model_analysis(connection_state)
    elif mode == 'measures':
        # Measure List operation
        table_name = args.get('table')
        max_results = args.get('max_results')
        result = agent_policy.analysis_orch.list_measures_simple(connection_state, table_name, max_results)
    elif mode == 'measure':
        # Measure Get operation - requires table and measure_name
        table_name = args.get('table')
        measure_name = args.get('measure_name')
        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'mode="measure" requires both table and measure_name parameters'
            }
        result = agent_policy.analysis_orch.get_measure_simple(connection_state, table_name, measure_name)
    elif mode == 'relationships':
        # Relationship List operation
        active_only = args.get('active_only', False)
        result = agent_policy.analysis_orch.list_relationships_simple(connection_state, active_only)
    elif mode == 'calculation_groups':
        # Calculation Group ListGroups operation
        result = agent_policy.analysis_orch.list_calculation_groups_simple(connection_state)
    else:
        return {
            'success': False,
            'error': f'Unknown mode: {mode}. Valid modes: tables, stats, measures, measure, relationships, calculation_groups'
        }

    return result

def handle_full_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified comprehensive model analysis combining best practices, performance, and integrity.

    Formerly known as comprehensive_analysis.
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    # Extract parameters with defaults
    scope = args.get('scope', 'all')
    depth = args.get('depth', 'balanced')
    include_bpa = args.get('include_bpa', True)
    include_performance = args.get('include_performance', True)
    include_integrity = args.get('include_integrity', True)
    max_seconds = args.get('max_seconds', None)

    # Run the analysis
    result = agent_policy.analysis_orch.comprehensive_analysis(
        connection_state,
        scope=scope,
        depth=depth,
        include_bpa=include_bpa,
        include_performance=include_performance,
        include_integrity=include_integrity,
        max_seconds=max_seconds
    )

    # Enrich issues with business impact context
    if result.get('success') and result.get('issues'):
        try:
            enriched_issues = []
            for issue in result['issues']:
                enriched_issue = enrich_issue_with_impact(issue)
                enriched_issues.append(enriched_issue)

            result['issues'] = enriched_issues

            # Add overall impact summary
            result = add_impact_summary(result)

        except Exception as e:
            logger.error(f"Error enriching issues with business impact: {e}", exc_info=True)
            # Don't fail the analysis if enrichment fails

    return result

def register_analysis_handlers(registry):
    """Register all analysis handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="simple_analysis",
            description="Fast model statistics (< 1s) based on Microsoft MCP operations: table list or full GetStats overview",
            handler=handle_simple_analysis,
            input_schema=TOOL_SCHEMAS.get('simple_analysis', {}),
            category="analysis",
            sort_order=26
        ),
        ToolDefinition(
            name="full_analysis",
            description="Comprehensive analysis: best practices (BPA), performance, and integrity validation (10-180s)",
            handler=handle_full_analysis,
            input_schema=TOOL_SCHEMAS.get('full_analysis', {}),
            category="analysis",
            sort_order=27
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} analysis handlers")
