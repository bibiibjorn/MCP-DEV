"""
Intelligent Middleware for MCP Server

This middleware layer adds intelligence to every tool call:
- Context tracking across tool calls
- Automatic suggestion generation after each result
- Smart routing and workflow detection
- Tool relationship awareness

This is integrated at the server level, not as a separate tool.
"""

from typing import Dict, Any, List, Optional
import logging
from core.infrastructure.connection_state import connection_state
from core.orchestration.tool_relationships import get_related_tools
from core.intelligence.tool_router import IntelligentToolRouter
from core.orchestration.workflow_templates import get_workflow_by_trigger, list_available_workflows

logger = logging.getLogger(__name__)


class IntelligentMiddleware:
    """
    Intelligent middleware that enhances every tool call with:
    - Context awareness
    - Proactive suggestions
    - Workflow detection
    - Smart routing
    """

    def __init__(self):
        self.tool_router = IntelligentToolRouter()
        self._request_count = 0

    def should_suggest_workflow(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if a workflow might be better than individual tool call

        Args:
            tool_name: Tool being called
            arguments: Tool arguments

        Returns:
            Workflow suggestion or None
        """
        # Build a natural language representation of the request
        request_description = self._build_request_description(tool_name, arguments)

        # Check if any workflow matches
        matching_workflow = get_workflow_by_trigger(request_description)

        if matching_workflow:
            # Check if this is part of a pattern that suggests workflow use
            recent_tools = connection_state.context_tracker.current_context.tools_used if connection_state.context_tracker.current_context else []

            # If user has called multiple related tools, suggest consolidating into workflow
            if len(recent_tools) >= 2:
                suggestion = self.tool_router.suggest_workflow_based_on_tool_sequence(recent_tools + [tool_name])
                if suggestion:
                    return {
                        'workflow_id': suggestion,
                        'reason': f'You are using multiple tools ({", ".join(recent_tools[-2:])}, {tool_name}) - consider using the "{suggestion}" workflow instead',
                        'benefit': 'Single call with synthesized insights instead of multiple calls'
                    }

        return None

    def _build_request_description(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Build natural language description of request"""
        descriptions = {
            'get_measure_details': 'analyze measure',
            'analyze_measure_dependencies': 'analyze dependencies',
            'get_measure_impact': 'impact analysis',
            'list_tables': 'list tables',
            'list_measures': 'list measures',
            'list_relationships': 'check relationships',
            'comprehensive_analysis': 'model health check',
            'describe_table': 'profile table'
        }

        base = descriptions.get(tool_name, tool_name)

        # Add context from arguments
        if 'measure' in arguments:
            base += f" for measure {arguments['measure']}"
        elif 'table' in arguments:
            base += f" for table {arguments['table']}"

        return base

    def pre_process_request(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request before execution - add intelligence

        Args:
            tool_name: Name of tool being called
            arguments: Tool arguments

        Returns:
            Enhanced response with metadata
        """
        self._request_count += 1
        response = {
            'proceed': True,
            'metadata': {},
            'suggestions': []
        }

        try:
            # Update context tracker
            if connection_state.context_tracker.current_context:
                connection_state.context_tracker.add_tool_used(tool_name)
            else:
                # Start new context based on tool type
                focus_object = self._extract_focus_object(tool_name, arguments)
                focus_type = self._infer_focus_type(tool_name)

                if focus_object and focus_type:
                    connection_state.context_tracker.start_analysis(focus_object, focus_type)
                    connection_state.context_tracker.add_tool_used(tool_name)

            # Check for workflow suggestion
            workflow_suggestion = self.should_suggest_workflow(tool_name, arguments)
            if workflow_suggestion:
                response['suggestions'].append({
                    'type': 'workflow',
                    'priority': 'high',
                    'suggestion': workflow_suggestion
                })

            # Apply smart defaults
            from core.utilities.smart_defaults import apply_smart_defaults
            enhanced_args = apply_smart_defaults(
                tool_name,
                arguments,
                connection_state.context_tracker.get_relevant_context_for_tool(tool_name)
            )

            response['enhanced_arguments'] = enhanced_args
            response['metadata']['context_active'] = connection_state.context_tracker.current_context is not None

        except Exception as e:
            logger.error(f"Error in pre-processing: {e}", exc_info=True)
            # Don't block request on pre-processing error
            response['enhanced_arguments'] = arguments

        return response

    def post_process_result(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process result after execution - add suggestions and insights

        Args:
            tool_name: Name of tool that was executed
            arguments: Arguments that were used
            result: Result from tool execution

        Returns:
            Enhanced result with suggestions and context
        """
        try:
            if not isinstance(result, dict):
                return result

            # Generate suggestions based on result
            suggestions = connection_state.suggestion_engine.generate_suggestions(
                tool_name,
                result,
                connection_state.context_tracker.get_relevant_context_for_tool(tool_name)
            )

            if suggestions:
                result['_suggestions'] = suggestions[:5]  # Top 5 suggestions

            # Get related tools based on tool relationships
            related_tools = get_related_tools(tool_name, result)
            if related_tools:
                result['_related_tools'] = related_tools[:3]  # Top 3 related tools

            # Enrich result with context if available
            if connection_state.context_tracker.current_context:
                result = connection_state.context_tracker.enrich_result_with_context(result, tool_name)

                # Track analyzed objects
                if tool_name == 'get_measure_details':
                    measure = arguments.get('measure')
                    table = arguments.get('table')
                    if measure and table:
                        connection_state.context_tracker.add_analyzed_object(
                            f"{table}[{measure}]",
                            'measure'
                        )

                elif tool_name == 'describe_table':
                    table = arguments.get('table_name') or arguments.get('table')
                    if table:
                        connection_state.context_tracker.add_analyzed_object(table, 'table')

                # Track issues found
                if 'issues' in result:
                    for issue in result.get('issues', []):
                        connection_state.context_tracker.add_issue(issue)

            # Add intelligence metadata
            result['_intelligence'] = {
                'context_tracked': connection_state.context_tracker.current_context is not None,
                'suggestions_available': len(suggestions) if suggestions else 0,
                'related_tools_available': len(related_tools) if related_tools else 0
            }

        except Exception as e:
            logger.error(f"Error in post-processing: {e}", exc_info=True)
            # Don't modify result on error

        return result

    def _extract_focus_object(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Extract the focus object from tool arguments"""
        if 'measure' in arguments and 'table' in arguments:
            return f"{arguments['table']}[{arguments['measure']}]"
        elif 'table' in arguments:
            return arguments['table']
        elif 'table_name' in arguments:
            return arguments['table_name']
        return None

    def _infer_focus_type(self, tool_name: str) -> Optional[str]:
        """Infer the focus type from tool name"""
        if 'measure' in tool_name:
            return 'measure'
        elif 'table' in tool_name:
            return 'table'
        elif 'relationship' in tool_name:
            return 'relationship'
        elif 'model' in tool_name or 'comprehensive' in tool_name:
            return 'model'
        return None

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current analysis context"""
        return {
            'request_count': self._request_count,
            'context': connection_state.context_tracker.get_context_summary(),
            'available_workflows': len(list_available_workflows())
        }


# Global instance
_middleware_instance: Optional[IntelligentMiddleware] = None


def get_intelligent_middleware() -> IntelligentMiddleware:
    """Get or create global middleware instance"""
    global _middleware_instance

    if _middleware_instance is None:
        _middleware_instance = IntelligentMiddleware()

    return _middleware_instance
