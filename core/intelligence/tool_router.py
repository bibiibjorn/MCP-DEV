"""
Intelligent Tool Router

This module routes natural language requests to optimal tools or workflows
based on intent matching and context analysis.
"""

from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class IntelligentToolRouter:
    """Routes natural language requests to optimal tools or workflows"""

    def __init__(self):
        self.intent_patterns = self._build_intent_patterns()
        self.routing_history: List[Dict[str, Any]] = []

    def route_request(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a natural language request to the best tool or workflow

        Args:
            user_request: User's natural language request
            context: Optional context (previously used tools, objects, etc.)

        Returns:
            Routing decision with primary action and follow-ups
        """
        context = context or {}
        request_lower = user_request.lower()

        # Extract entities (table names, measure names, etc.)
        entities = self._extract_entities(user_request, context)

        # Match intent patterns
        intent = self._match_intent(request_lower, entities)

        # Determine routing strategy
        routing = None

        if intent['type'] == 'workflow':
            routing = self._route_to_workflow(intent, entities)
        elif intent['type'] == 'complex_query':
            routing = self._route_to_multi_tool(intent, entities)
        else:
            routing = self._route_to_single_tool(intent, entities)

        # Add to history
        self._add_to_history(user_request, routing)

        return routing

    def _build_intent_patterns(self) -> List[Dict[str, Any]]:
        """Build patterns for matching user intents"""
        return [
            # ==================== Workflow Intents ====================
            {
                'intent': 'complete_measure_analysis',
                'type': 'workflow',
                'patterns': [
                    r'analyze\s+(the\s+)?measure',
                    r'tell me (about|everything about)\s+(the\s+)?measure',
                    r'explain\s+(the\s+)?measure',
                    r'how does\s+(the\s+)?measure.*work',
                    r'what does\s+(the\s+)?measure.*do',
                    r'complete\s+analysis\s+of',
                    r'full\s+analysis'
                ],
                'requires': ['measure_name'],
                'workflow': 'complete_measure_analysis'
            },
            {
                'intent': 'measure_impact_analysis',
                'type': 'workflow',
                'patterns': [
                    r'what (uses|depends on|references)',
                    r'impact of (changing|deleting|modifying)',
                    r'safe to (delete|remove|change)',
                    r'(downstream|upstream) (dependencies|impact)',
                    r'who uses this',
                    r'impact analysis'
                ],
                'requires': ['measure_name'],
                'workflow': 'measure_impact_analysis'
            },
            {
                'intent': 'model_health_check',
                'type': 'workflow',
                'patterns': [
                    r'(check|analyze|validate)\s+(the\s+)?(entire\s+)?model',
                    r'model (health|issues|problems)',
                    r'what\'s wrong with\s+(the\s+)?model',
                    r'model best practices',
                    r'health check'
                ],
                'requires': [],
                'workflow': 'model_health_check'
            },
            {
                'intent': 'table_profiling',
                'type': 'workflow',
                'patterns': [
                    r'(profile|analyze|describe)\s+(the\s+)?table',
                    r'tell me about\s+(the\s+)?table',
                    r'what\'s in\s+(the\s+)?table'
                ],
                'requires': ['table_name'],
                'workflow': 'table_profiling'
            },
            {
                'intent': 'performance_investigation',
                'type': 'workflow',
                'patterns': [
                    r'slow\s+(measure|query)',
                    r'(measure|query)\s+performance',
                    r'optimize\s+(measure|query)',
                    r'why is.*(slow|taking long)',
                    r'performance\s+(issue|problem)'
                ],
                'requires': ['measure_name', 'dax_query'],
                'workflow': 'performance_investigation',
                'optional_params': True
            },
            {
                'intent': 'relationship_validation',
                'type': 'workflow',
                'patterns': [
                    r'validate\s+relationships',
                    r'check\s+relationships',
                    r'relationship\s+(problems|issues)',
                    r'relationship\s+validation'
                ],
                'requires': [],
                'workflow': 'relationship_validation'
            },

            # ==================== Complex Query Intents ====================
            {
                'intent': 'find_measure_performance_issues',
                'type': 'complex_query',
                'patterns': [
                    r'find\s+slow\s+measures',
                    r'which\s+measures\s+are\s+slow',
                    r'performance\s+issues\s+in\s+measures'
                ],
                'requires': [],
                'tools': ['list_measures', 'dax_intelligence', 'run_dax']
            },
            {
                'intent': 'find_relationship_issues',
                'type': 'complex_query',
                'patterns': [
                    r'relationship (problems|issues)',
                    r'(check|validate).*relationships',
                    r'relationship.*cardinality'
                ],
                'requires': [],
                'tools': ['list_relationships', 'comprehensive_analysis']
            },
            {
                'intent': 'find_unused_measures',
                'type': 'complex_query',
                'patterns': [
                    r'unused\s+measures',
                    r'orphaned\s+measures',
                    r'measures\s+not\s+used'
                ],
                'requires': [],
                'tools': ['list_measures', 'get_measure_impact']
            },

            # ==================== Single Tool Intents ====================
            {
                'intent': 'simple_measure_lookup',
                'type': 'single_tool',
                'patterns': [
                    r'^show\s+(me\s+)?(the\s+)?measure',
                    r'^get\s+(the\s+)?measure.*definition',
                    r'^what is the dax for',
                    r'^measure\s+definition'
                ],
                'requires': ['measure_name'],
                'tool': 'get_measure_details'
            },
            {
                'intent': 'list_tables',
                'type': 'single_tool',
                'patterns': [
                    r'^list (all )?(the )?tables',
                    r'^show me (all )?(the )?tables',
                    r'^what tables',
                    r'^get tables'
                ],
                'requires': [],
                'tool': 'list_tables'
            },
            {
                'intent': 'list_measures',
                'type': 'single_tool',
                'patterns': [
                    r'^list (all )?(the )?measures',
                    r'^show me (all )?(the )?measures',
                    r'^what measures',
                    r'^get measures'
                ],
                'requires': [],
                'tool': 'list_measures'
            },
            {
                'intent': 'list_relationships',
                'type': 'single_tool',
                'patterns': [
                    r'^list (all )?(the )?relationships',
                    r'^show me (all )?(the )?relationships',
                    r'^what relationships',
                    r'^get relationships'
                ],
                'requires': [],
                'tool': 'list_relationships'
            },
            {
                'intent': 'describe_table',
                'type': 'single_tool',
                'patterns': [
                    r'^describe\s+(the\s+)?table',
                    r'^show\s+(me\s+)?table\s+structure',
                    r'^table\s+schema'
                ],
                'requires': ['table_name'],
                'tool': 'describe_table'
            },
            {
                'intent': 'preview_data',
                'type': 'single_tool',
                'patterns': [
                    r'^preview\s+(the\s+)?data',
                    r'^show\s+(me\s+)?sample\s+data',
                    r'^get\s+data\s+from'
                ],
                'requires': ['table_name'],
                'tool': 'preview_table_data'
            },
            {
                'intent': 'analyze_dax',
                'type': 'single_tool',
                'patterns': [
                    r'^analyze\s+(this\s+)?dax',
                    r'^check\s+(this\s+)?dax',
                    r'^review\s+(this\s+)?dax',
                    r'^dax\s+analysis'
                ],
                'requires': ['dax_expression'],
                'tool': 'dax_intelligence'
            },
            {
                'intent': 'run_query',
                'type': 'single_tool',
                'patterns': [
                    r'^run\s+(this\s+)?query',
                    r'^execute\s+(this\s+)?dax',
                    r'^test\s+(this\s+)?query'
                ],
                'requires': ['dax_query'],
                'tool': 'run_dax'
            },
            {
                'intent': 'comprehensive_analysis',
                'type': 'single_tool',
                'patterns': [
                    r'^comprehensive\s+analysis',
                    r'^full\s+analysis',
                    r'^run\s+bpa',
                    r'^best\s+practice'
                ],
                'requires': [],
                'tool': 'comprehensive_analysis'
            }
        ]

    def _match_intent(self, request: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Match request to intent pattern"""
        # Try to match patterns in order of specificity
        for pattern_group in self.intent_patterns:
            for pattern in pattern_group['patterns']:
                if re.search(pattern, request):
                    logger.info(f"Matched intent: {pattern_group['intent']}")
                    return pattern_group

        # Default: generic analysis
        logger.info("No specific intent matched, using generic analysis")
        return {
            'intent': 'generic_analysis',
            'type': 'single_tool',
            'tool': 'comprehensive_analysis',
            'requires': []
        }

    def _extract_entities(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities from request

        This is a simplified implementation. In production, you might use
        more sophisticated NER (Named Entity Recognition).
        """
        entities = {}

        # Extract measure names (look for [MeasureName] pattern or 'MeasureName' in quotes)
        measure_matches = re.findall(r'\[([\w\s\-\_]+)\]', request)
        if measure_matches:
            entities['measure_name'] = measure_matches[0]
        else:
            # Try quoted strings
            quoted_matches = re.findall(r'["\']([^"\']+)["\']', request)
            if quoted_matches:
                # Assume first quoted string might be a measure
                entities['measure_name'] = quoted_matches[0]

        # Extract table names (look for 'TableName' pattern or table keyword)
        table_matches = re.findall(r'table\s+["\']?([\w\s]+)["\']?', request, re.IGNORECASE)
        if table_matches:
            entities['table_name'] = table_matches[0].strip()

        # Extract DAX expressions (look for EVALUATE or common DAX keywords)
        if 'EVALUATE' in request.upper() or 'CALCULATE' in request.upper():
            # Extract code-like patterns
            dax_matches = re.findall(r'```([^`]+)```', request)
            if dax_matches:
                entities['dax_query'] = dax_matches[0].strip()
                entities['dax_expression'] = dax_matches[0].strip()

        # Use context if entities not found in request
        if not entities.get('measure_name') and context.get('last_measure'):
            entities['measure_name'] = context['last_measure']

        if not entities.get('table_name') and context.get('last_table'):
            entities['table_name'] = context['last_table']

        return entities

    def _route_to_workflow(self, intent: Dict[str, Any], entities: Dict[str, Any]) -> Dict[str, Any]:
        """Route to workflow template"""
        workflow_name = intent['workflow']

        # Check if required parameters are available
        missing_params = []
        if not intent.get('optional_params', False):
            for param in intent.get('requires', []):
                if param not in entities:
                    missing_params.append(param)

        if missing_params:
            return {
                'routing_strategy': 'error',
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'explanation': f"To execute '{workflow_name}' workflow, please provide: {', '.join(missing_params)}"
            }

        return {
            'routing_strategy': 'workflow',
            'primary_action': {
                'type': 'workflow',
                'workflow': workflow_name,
                'inputs': entities
            },
            'explanation': f"Routing to '{workflow_name}' workflow for comprehensive analysis",
            'expected_duration': '15-45 seconds'
        }

    def _route_to_multi_tool(self, intent: Dict[str, Any], entities: Dict[str, Any]) -> Dict[str, Any]:
        """Route to multiple tools in sequence"""
        tools = intent['tools']

        return {
            'routing_strategy': 'multi_tool',
            'primary_action': {
                'type': 'tool',
                'tool': tools[0],
                'inputs': entities
            },
            'follow_up_actions': [
                {
                    'type': 'tool',
                    'tool': tool,
                    'inputs': entities
                }
                for tool in tools[1:]
            ],
            'explanation': f"Will execute {len(tools)} tools sequentially: {', '.join(tools)}",
            'expected_duration': f'{len(tools) * 5}-{len(tools) * 10} seconds'
        }

    def _route_to_single_tool(self, intent: Dict[str, Any], entities: Dict[str, Any]) -> Dict[str, Any]:
        """Route to single tool"""
        tool_name = intent.get('tool', 'comprehensive_analysis')

        # Check if required parameters are available
        missing_params = []
        for param in intent.get('requires', []):
            if param not in entities:
                missing_params.append(param)

        if missing_params:
            return {
                'routing_strategy': 'error',
                'error': f"Missing required parameters: {', '.join(missing_params)}",
                'explanation': f"To execute '{tool_name}' tool, please provide: {', '.join(missing_params)}"
            }

        return {
            'routing_strategy': 'single_tool',
            'primary_action': {
                'type': 'tool',
                'tool': tool_name,
                'inputs': entities
            },
            'explanation': f"Routing to '{tool_name}' tool",
            'expected_duration': '5-15 seconds'
        }

    def _add_to_history(self, request: str, routing: Dict[str, Any]):
        """Add routing decision to history"""
        self.routing_history.append({
            'request': request,
            'routing': routing
        })

        # Keep last 20 routing decisions
        if len(self.routing_history) > 20:
            self.routing_history = self.routing_history[-20:]

    def get_routing_history(self) -> List[Dict[str, Any]]:
        """Get routing history"""
        return self.routing_history

    def suggest_workflow_based_on_tool_sequence(self, tools_used: List[str]) -> Optional[str]:
        """
        Suggest a workflow based on a sequence of tools that were used

        Args:
            tools_used: List of tool names that were recently used

        Returns:
            Workflow name if a matching pattern is found
        """
        # Check for complete_measure_analysis pattern
        if 'get_measure_details' in tools_used and 'analyze_measure_dependencies' in tools_used:
            if 'dax_intelligence' in tools_used or 'get_measure_impact' in tools_used:
                return 'complete_measure_analysis'

        # Check for model_health_check pattern
        if 'list_tables' in tools_used and 'list_measures' in tools_used and 'list_relationships' in tools_used:
            return 'model_health_check'

        # Check for measure_impact_analysis pattern
        if 'get_measure_details' in tools_used and 'get_measure_impact' in tools_used:
            return 'measure_impact_analysis'

        # Check for table_profiling pattern
        if 'describe_table' in tools_used and 'list_relationships' in tools_used:
            return 'table_profiling'

        return None

    def explain_routing_decision(self, routing: Dict[str, Any]) -> str:
        """Generate human-readable explanation of routing decision"""
        strategy = routing.get('routing_strategy')

        if strategy == 'workflow':
            workflow = routing['primary_action']['workflow']
            return f"I'll execute the '{workflow}' workflow, which will automatically perform multiple analysis steps and synthesize the results. This provides comprehensive insights in a single operation."

        elif strategy == 'multi_tool':
            tools = [routing['primary_action']['tool']] + [a['tool'] for a in routing.get('follow_up_actions', [])]
            return f"I'll execute {len(tools)} tools in sequence ({', '.join(tools)}) to gather comprehensive information."

        elif strategy == 'single_tool':
            tool = routing['primary_action']['tool']
            return f"I'll use the '{tool}' tool to get the information you need."

        elif strategy == 'error':
            return routing.get('explanation', 'Unable to route request')

        return "Routing request..."
