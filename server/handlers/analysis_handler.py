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
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} analysis handlers")
