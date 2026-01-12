"""
Documentation Handler
Handles Word documentation and HTML model explorer generation
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_generate_model_documentation_word(args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Word documentation report"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    output_path = args.get('output_path')

    return agent_policy.documentation_orch.generate_word_documentation(connection_state, output_path)

def handle_update_model_documentation_word(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update Word documentation report"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    input_path = args.get('input_path')
    output_path = args.get('output_path')

    if not input_path:
        return {
            'success': False,
            'error': 'input_path parameter is required'
        }

    return agent_policy.documentation_orch.update_word_documentation(connection_state, input_path, output_path)

def register_documentation_handlers(registry):
    """Register all documentation handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="08_Generate_Documentation_Word",
            description="Generate Word documentation report",
            handler=handle_generate_model_documentation_word,
            input_schema=TOOL_SCHEMAS.get('generate_model_documentation_word', {}),
            category="documentation",
            sort_order=80  # 08 = Documentation
        ),
        ToolDefinition(
            name="08_Update_Documentation_Word",
            description="Update Word documentation report",
            handler=handle_update_model_documentation_word,
            input_schema=TOOL_SCHEMAS.get('update_model_documentation_word', {}),
            category="documentation",
            sort_order=81  # 08 = Documentation
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} documentation handlers")
