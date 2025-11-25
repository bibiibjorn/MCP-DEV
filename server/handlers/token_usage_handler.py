"""
Token Usage Handler
Handles token usage tracking and reporting
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.token_usage_tracker import get_token_tracker

logger = logging.getLogger(__name__)


def handle_get_token_usage(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get token usage statistics for the current session.

    Args:
        args: Dictionary with optional 'format' parameter
              - 'json': Full statistics (default)
              - 'summary': Brief overview
              - 'detailed': Comprehensive report

    Returns:
        Dictionary with token usage statistics
    """
    try:
        tracker = get_token_tracker()
        format_type = args.get('format', 'json')

        # Get the full statistics
        stats = tracker.get_statistics()

        if format_type == 'summary':
            # Return brief summary
            return {
                'success': True,
                'format': 'summary',
                'summary': {
                    'total_tokens': stats['summary']['total_tokens_used'],
                    'total_calls': stats['summary']['total_calls'],
                    'avg_per_call': stats['summary']['avg_tokens_per_call'],
                    'session_duration_minutes': stats['session']['duration_minutes'],
                    'top_5_tools': _get_top_tools(stats['by_tool'], 5)
                }
            }

        elif format_type == 'detailed':
            # Return comprehensive report with formatted output
            return {
                'success': True,
                'format': 'detailed',
                'report': tracker.get_resource_content(),
                'statistics': stats
            }

        else:  # format_type == 'json' (default)
            # Return full JSON statistics
            return {
                'success': True,
                'format': 'json',
                'statistics': stats
            }

    except Exception as e:
        logger.error(f"Error getting token usage: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Error getting token usage: {str(e)}'
        }


def _get_top_tools(tool_breakdown: Dict[str, Any], limit: int = 5) -> list:
    """Get top N tools by token usage"""
    sorted_tools = sorted(
        tool_breakdown.items(),
        key=lambda x: x[1]['total_tokens'],
        reverse=True
    )

    return [
        {
            'tool': name,
            'tokens': stats['total_tokens'],
            'calls': stats['calls']
        }
        for name, stats in sorted_tools[:limit]
    ]


def register_token_usage_handlers(registry):
    """Register token usage handler"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="get_token_usage",
            description="Get token usage statistics for the current MCP session. Shows total tokens used, per-tool breakdown, and recent history. Use this to monitor token consumption across tool calls.",
            handler=handle_get_token_usage,
            input_schema=TOOL_SCHEMAS.get('get_token_usage', {}),
            category="monitoring",
            sort_order=110
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} token usage handlers")
