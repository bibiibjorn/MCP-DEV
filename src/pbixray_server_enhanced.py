#!/usr/bin/env python3
"""
MCP-PowerBi-Finvision Server v3.4 - Clean Modular Edition
Uses handler registry for all tool routing
"""

import asyncio
import json
import logging
import sys
import os
import time
from pathlib import Path
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
from datetime import datetime

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from __version__ import __version__
from core.infrastructure.connection_manager import ConnectionManager
from core.validation.error_handler import ErrorHandler
from core.config.tool_timeouts import ToolTimeoutManager
from core.infrastructure.cache_manager import create_cache_manager
from core.validation.input_validator import InputValidator
from core.infrastructure.rate_limiter import RateLimiter
from core.infrastructure.limits_manager import init_limits_manager
from core.orchestration.agent_policy import AgentPolicy
from core.config.config_manager import config
from core.infrastructure.connection_state import connection_state

# Import handler registry system
from server.registry import get_registry
from server.dispatch import ToolDispatcher
from server.handlers import register_all_handlers
from server.resources import get_resource_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_powerbi_finvision")

# Configure file-based logging
try:
    logs_dir = os.path.join(parent_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    LOG_PATH = os.path.join(logs_dir, "pbixray.log")
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == LOG_PATH for h in logger.handlers):
        _fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        _fh.setLevel(logging.INFO)
        _fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(_fh)
except Exception:
    LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "pbixray.log")

# Track server start time
start_time = time.time()

# Initialize managers
connection_manager = ConnectionManager()
timeout_manager = ToolTimeoutManager(config.get('tool_timeouts', {}))
try:
    enhanced_cache = create_cache_manager(config.get_all())
except Exception:
    from core.infrastructure.cache_manager import EnhancedCacheManager
    enhanced_cache = EnhancedCacheManager()
rate_limiter = RateLimiter(config.get('rate_limiting', {}))
limits_manager = init_limits_manager(config.get_all())

connection_state.set_connection_manager(connection_manager)

# Initialize handler registry and dispatcher
registry = get_registry()
register_all_handlers(registry)
dispatcher = ToolDispatcher()

# Initialize MCP server
app = Server("MCP-PowerBi-Finvision")
agent_policy = AgentPolicy(
    config,
    timeout_manager=timeout_manager,
    cache_manager=enhanced_cache,
    rate_limiter=rate_limiter,
    limits_manager=limits_manager
)

# Set agent_policy in connection_state so handlers can access it
connection_state.agent_policy = agent_policy


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools from registry"""
    return registry.get_all_tools_as_mcp()


@app.list_resources()
async def list_resources() -> List[Resource]:
    """List all available MCP resources (exported model files)"""
    try:
        resource_manager = get_resource_manager()
        return resource_manager.list_resources()
    except Exception as e:
        logger.error(f"Error listing resources: {e}", exc_info=True)
        return []


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read an MCP resource (exported model file) by URI"""
    try:
        resource_manager = get_resource_manager()
        content = resource_manager.read_resource(uri)
        return content
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
        raise ValueError(f"Failed to read resource {uri}: {str(e)}")


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute tool via dispatcher"""
    try:
        _t0 = time.time()

        # Input validation
        if 'table' in arguments:
            is_valid, error = InputValidator.validate_table_name(arguments['table'])
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    'success': False,
                    'error': error,
                    'error_type': 'invalid_input'
                }, indent=2))]

        if 'query' in arguments:
            is_valid, error = InputValidator.validate_dax_query(arguments['query'])
            if not is_valid:
                return [TextContent(type="text", text=json.dumps({
                    'success': False,
                    'error': error,
                    'error_type': 'invalid_input'
                }, indent=2))]

        # Rate limiting
        if rate_limiter and not rate_limiter.allow_request(name):
            return [TextContent(type="text", text=json.dumps({
                'success': False,
                'error': 'Rate limit exceeded',
                'error_type': 'rate_limit',
                'retry_after': rate_limiter.get_retry_after(name)
            }, indent=2))]

        # Dispatch to handler
        result = dispatcher.dispatch(name, arguments)

        # Record telemetry
        _dur = round((time.time() - _t0) * 1000, 2)
        logger.debug(f"Tool {name} completed in {_dur}ms")

        # Add limits awareness
        if isinstance(result, dict):
            result = agent_policy.wrap_response_with_limits_info(result, name)

            # Check for token overflow
            if result.get('_limits_info', {}).get('token_usage', {}).get('level') == 'over':
                high_token_tools = ['full_analysis', 'export_tmsl', 'export_tmdl', 'analyze_model_bpa']
                if name in high_token_tools:
                    token_info = result['_limits_info']['token_usage']
                    return [TextContent(type="text", text=json.dumps({
                        'success': False,
                        'error': 'Response would exceed token limit',
                        'error_type': 'token_limit_exceeded',
                        'estimated_tokens': token_info['estimated_tokens'],
                        'max_tokens': token_info['max_tokens'],
                        'percentage': token_info['percentage'],
                        'requires_user_confirmation': True,
                        'tool_name': name,
                        'message': (
                            f"The '{name}' tool would return {token_info['estimated_tokens']:,} tokens, "
                            f"exceeding the {token_info['max_tokens']:,} token limit ({token_info['percentage']}%). "
                            f"\n\nThis response has been BLOCKED to prevent automatic overflow. "
                            f"\n\nPlease choose one of these options:"
                            f"\n  1. Use 'summary_only=true' parameter for a compact summary"
                            f"\n  2. Use pagination with 'limit' and 'offset' parameters"
                            f"\n  3. Export results to a file instead (use export tools)"
                            f"\n  4. Ask me to proceed anyway (response will be truncated)"
                        )
                    }, indent=2))]

            # Add optimization suggestions
            suggestion = agent_policy.suggest_optimizations(name, result)
            if suggestion:
                if '_limits_info' not in result:
                    result['_limits_info'] = {}
                result['_limits_info']['suggestion'] = suggestion

        # Apply global truncation
        max_tokens = limits_manager.token.max_result_tokens
        if isinstance(result, dict):
            from server.middleware import truncate_if_needed
            result = truncate_if_needed(result, max_tokens)

        # Special handling for get_recent_logs
        if name == "get_recent_logs" and isinstance(result, dict) and 'logs' in result:
            return [TextContent(type="text", text=result['logs'])]

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps(
            ErrorHandler.handle_unexpected_error(name, e), indent=2
        ))]


async def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info(f"MCP-PowerBi-Finvision Server v{__version__} - Clean Modular Edition")
    logger.info("=" * 80)
    logger.info(f"Registered {len(registry._handlers)} tools")

    # Build initialization instructions
    def _initial_instructions() -> str:
        try:
            guides_dir = os.path.join(parent_dir, 'docs')
            lines = [
                f"MCP-PowerBi-Finvision v{__version__} — Power BI Desktop MCP server.",
                "",
                "What you can do:",
                "- Connect to your open Power BI Desktop instance",
                "- Inspect tables/columns/measures and preview data",
                "- Search objects and view data sources and M expressions",
                "- Run Best Practice Analyzer (BPA) and relationship analysis",
                "- Export compact schema, TMSL/TMDL, and documentation",
                "",
                "Quick start:",
                "1) Run tool: detect_powerbi_desktop",
                "2) Then: connect_to_powerbi (usually model_index=0)",
                "3) Try: list_tables | describe_table | preview_table_data",
                "",
                f"Full guide: {guides_dir}/PBIXRAY_Quickstart.pdf"
            ]
            return "\n".join(lines)
        except Exception:
            return (
                f"MCP-PowerBi-Finvision v{__version__}. "
                "Start by running 'detect_powerbi_desktop' and then 'connect_to_powerbi'."
            )

    init_opts = app.create_initialization_options()
    try:
        setattr(init_opts, "instructions", _initial_instructions())
    except Exception:
        pass

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, init_opts)


if __name__ == "__main__":
    asyncio.run(main())
