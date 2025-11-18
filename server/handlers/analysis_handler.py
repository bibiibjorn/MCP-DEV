"""
Analysis Handler
Handles model analysis tools including BPA, performance, validation, and VertiPaq stats
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.utilities.business_impact import enrich_issue_with_impact, add_impact_summary
from core.utilities.suggested_actions import add_suggested_actions

logger = logging.getLogger(__name__)

def handle_comprehensive_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified comprehensive model analysis combining best practices, performance, and integrity.

    Replaces and consolidates: full_analysis, analyze_best_practices, analyze_performance
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

    # Add suggested next actions
    result = add_suggested_actions(result, 'comprehensive_analysis', args)

    return result

def register_analysis_handlers(registry):
    """Register all analysis handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="comprehensive_analysis",
            description="Unified comprehensive analysis: best practices, performance, and integrity validation",
            handler=handle_comprehensive_analysis,
            input_schema=TOOL_SCHEMAS.get('comprehensive_analysis', {}),
            category="analysis",
            sort_order=27
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} analysis handlers")
