"""
Optimization tool handlers - NEW tools for DAX optimization workflow.
Integrates with existing handler infrastructure.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OptimizationHandler:
    """Handles optimization workflow tools"""

    def __init__(self):
        """Initialize optimization handler"""
        self._orchestrator = None  # Lazy load

    def _get_query_executor(self):
        """Get query executor from global connection state"""
        from core.infrastructure.connection_state import connection_state

        if not connection_state.is_connected():
            return None

        return connection_state.query_executor

    def _get_orchestrator(self):
        """
        Lazy load optimization orchestrator.

        Note: Creates a new orchestrator each time to ensure fresh query_executor reference.
        This is necessary because the query_executor can change after reconnection.
        """
        query_executor = self._get_query_executor()
        if not query_executor:
            raise RuntimeError("Query executor not available. Ensure you are connected to Power BI.")

        try:
            from core.orchestration.optimization_orchestrator import OptimizationOrchestrator
            # Always create fresh orchestrator to ensure current query_executor
            self._orchestrator = OptimizationOrchestrator(query_executor)
        except Exception as e:
            logger.error(f"Failed to load optimization orchestrator: {e}")
            raise

        return self._orchestrator

    def handle_analyze_dax_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool: 15_analyze_dax_query

        Analyze DAX query and prepare for optimization.

        Arguments:
            query: str - DAX query to analyze and optimize
        """
        query = arguments.get("query")

        if not query:
            return {"success": False, "error": "Query parameter required"}

        # Get connection info from existing infrastructure
        connection_info = self._get_connection_info()
        if not connection_info.get("success"):
            return connection_info

        try:
            orchestrator = self._get_orchestrator()
            result = orchestrator.prepare_optimization(query, connection_info)

            # Add session status to result
            if result.get("success"):
                status = orchestrator.get_session_status()
                if status.get("success"):
                    result["session_info"] = status.get("session", {})

            return result
        except Exception as e:
            logger.exception("Error analyzing DAX query")
            return {"success": False, "error": str(e)}

    def handle_test_optimized_dax(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tool: 15_test_optimized_dax

        Test optimized DAX query and compare to baseline.

        Arguments:
            optimized_query: str - Optimized DAX query to test
        """
        optimized_query = arguments.get("optimized_query")

        if not optimized_query:
            return {"success": False, "error": "optimized_query parameter required"}

        connection_info = self._get_connection_info()
        if not connection_info.get("success"):
            return connection_info

        try:
            orchestrator = self._get_orchestrator()
            result = orchestrator.execute_optimization(optimized_query, connection_info)

            # Add session status to result
            if result.get("success"):
                status = orchestrator.get_session_status()
                if status.get("success"):
                    result["session_info"] = status.get("session", {})

            return result
        except Exception as e:
            logger.exception("Error testing optimized DAX")
            return {"success": False, "error": str(e)}


    def _get_connection_info(self) -> Dict[str, Any]:
        """Get connection info from global connection state"""
        try:
            from core.infrastructure.connection_state import connection_state

            # Check if connected
            if not connection_state.is_connected():
                return {
                    "success": False,
                    "error": "Not connected to any dataset. Use connect_to_powerbi first."
                }

            # Extract connection details from connection manager
            cm = connection_state.connection_manager
            if not cm:
                return {
                    "success": False,
                    "error": "Connection manager not available"
                }

            # Get database name from active instance
            dataset_name = ""
            if cm.active_instance:
                dataset_name = cm.active_instance.get('database', '')

            connection_info = {
                "success": True,
                "xmla_endpoint": "localhost",  # Default for Power BI Desktop
                "dataset_name": dataset_name,
                "connection_string": cm.connection_string or ""
            }

            return connection_info

        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {"success": False, "error": f"Failed to get connection info: {e}"}


def register_optimization_handlers(registry):
    """Register optimization tool handlers"""
    from server.registry import ToolDefinition

    # Handler accesses query_executor dynamically from connection_state
    handler = OptimizationHandler()

    # Register tools
    registry.register(ToolDefinition(
        name="analyze_dax_query",
        description="""Analyze DAX query and prepare for optimization.

This tool performs comprehensive analysis and preparation:
1. Executes baseline query with performance profiling (SE/FE breakdown)
2. Analyzes query patterns for anti-patterns (SUMX+FILTER, nested CALCULATE, etc.)
3. Fetches relevant optimization articles and guidance from SQLBI patterns
4. Provides detailed bottleneck analysis and recommendations
5. Creates optimization session for tracking iterations

Returns:
- Baseline performance metrics (Total ms, SE%, FE%, query count)
- Performance analysis with bottlenecks and severity
- Matched optimization articles with specific guidance
- Research recommendations based on patterns detected
- Session info (created_at, baseline_performance)

Use this as the FIRST step before attempting optimizations.""",
        handler=handler.handle_analyze_dax_query,
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "DAX query to analyze and optimize"
                }
            },
            "required": ["query"]
        },
        category="optimization",
        sort_order=150
    ))

    registry.register(ToolDefinition(
        name="test_optimized_dax",
        description="""Test optimized DAX query and compare to baseline.

This tool validates and benchmarks optimizations:
1. Executes the optimized query with performance profiling
2. Compares performance metrics to baseline (improvement %)
3. Validates semantic equivalence (ensures results are identical)
4. Provides detailed performance comparison and analysis
5. Updates session with iteration history

Returns:
- Optimized performance metrics (Total ms, SE%, FE%, query count)
- Performance comparison (improvement_percent, baseline_ms, optimized_ms)
- Semantic equivalence validation (is_equivalent, reason)
- Performance analysis with bottlenecks
- Session info (iterations_count, best_iteration)
- User-friendly message about optimization result

Use this after modifying the DAX query based on analysis insights.
Ensures optimizations are valid and quantifies improvements.""",
        handler=handler.handle_test_optimized_dax,
        input_schema={
            "type": "object",
            "properties": {
                "optimized_query": {
                    "type": "string",
                    "description": "Optimized DAX query to test and compare"
                }
            },
            "required": ["optimized_query"]
        },
        category="optimization",
        sort_order=151
    ))
