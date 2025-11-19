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
    Fast model statistics overview based on Microsoft Official MCP Server operations.

    Two modes:
    - 'tables': Ultra-fast table list (< 500ms) - Microsoft MCP List operation
    - 'stats': Fast model statistics (< 1s) - Microsoft MCP GetStats operation
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    # Extract mode parameter (default: stats)
    mode = args.get('mode', 'stats')

    # Route to appropriate function
    if mode == 'tables':
        result = agent_policy.analysis_orch.list_tables_simple(connection_state)
    else:  # mode == 'stats'
        result = agent_policy.analysis_orch.simple_model_analysis(connection_state)

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
