"""
Optimization Workflow Orchestrator - Manages DAX optimization sessions.
Integrates with existing orchestration infrastructure.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class OptimizationOrchestrator:
    """
    Orchestrates DAX optimization workflows with session management.
    Integrates with existing orchestration patterns.
    """

    def __init__(self, query_executor=None):
        self.query_executor = query_executor
        self.dax_profiler = None
        self.research_provider = None
        self.active_session = None

    def prepare_optimization(
        self, query: str, connection_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare query for optimization - Phase 1 of workflow.

        Steps:
        1. Execute baseline with profiling
        2. Fetch research articles
        3. Create optimization session

        Returns:
            Comprehensive preparation results
        """
        logger.info("Starting optimization preparation...")

        # Lazy load dependencies
        if self.dax_profiler is None:
            try:
                from core.performance.dax_profiler import DaxPerformanceProfiler
                self.dax_profiler = DaxPerformanceProfiler(self.query_executor)
            except Exception as e:
                logger.error(f"Failed to load DAX profiler: {e}")
                return {"success": False, "error": f"Failed to load profiler: {e}"}

        if self.research_provider is None:
            try:
                from core.research.dax_research import DaxResearchProvider
                self.research_provider = DaxResearchProvider()
            except Exception as e:
                logger.error(f"Failed to load research provider: {e}")
                return {"success": False, "error": f"Failed to load research: {e}"}

        # Step 1: Execute baseline with profiling
        baseline_result = self.dax_profiler.profile_query(
            query=query,
            connection_info=connection_info,
            runs=3
        )

        if not baseline_result.get("success"):
            return {
                "success": False,
                "error": f"Baseline execution failed: {baseline_result.get('error')}"
            }

        # Step 2: Fetch research articles
        research = self.research_provider.get_optimization_guidance(
            query=query,
            performance_data=baseline_result["fastest_run"]
        )

        # Step 3: Create optimization session
        self.active_session = {
            "created_at": datetime.utcnow().isoformat(),
            "original_query": query,
            "baseline": baseline_result,
            "research": research,
            "iterations": []
        }

        return {
            "success": True,
            "prepared_query": {
                "original_query": query,
            },
            "baseline_execution": {
                "performance": baseline_result["fastest_run"]["Performance"],
                "event_details": baseline_result["fastest_run"].get("EventDetails", []),
                "analysis": baseline_result["analysis"]
            },
            "research_articles": research,
            "message": "Query prepared for optimization. Use execute_optimization to test improvements."
        }

    def execute_optimization(
        self, optimized_query: str, connection_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute optimized query and compare to baseline - Phase 2 of workflow.

        Returns:
            Comparison results with improvement analysis
        """
        if not self.active_session:
            return {
                "success": False,
                "error": "No active optimization session. Call prepare_optimization first."
            }

        if not self.dax_profiler:
            return {
                "success": False,
                "error": "DAX profiler not available"
            }

        logger.info("Executing optimized query...")

        # Execute optimized query with profiling
        optimized_result = self.dax_profiler.profile_query(
            query=optimized_query,
            connection_info=connection_info,
            runs=3
        )

        if not optimized_result.get("success"):
            return {
                "success": False,
                "error": f"Optimized query execution failed: {optimized_result.get('error')}"
            }

        # Compare to baseline
        baseline_run = self.active_session["baseline"]["fastest_run"]
        optimized_run = optimized_result["fastest_run"]

        comparison = self.dax_profiler.compare_queries(baseline_run, optimized_run)

        # Track iteration
        iteration = {
            "timestamp": datetime.utcnow().isoformat(),
            "optimized_query": optimized_query,
            "performance": optimized_run["Performance"],
            "analysis": optimized_result["analysis"],
            "comparison": comparison
        }

        self.active_session["iterations"].append(iteration)

        return {
            "success": True,
            "performance": optimized_run["Performance"],
            "event_details": optimized_run.get("EventDetails", []),
            "analysis": optimized_result["analysis"],
            "comparison": comparison,
            "semantic_equivalence": comparison["semantic_equivalence"],
            "message": self._generate_iteration_message(comparison)
        }

    def get_session_status(self) -> Dict[str, Any]:
        """Get current optimization session status"""
        if not self.active_session:
            return {
                "success": False,
                "error": "No active optimization session"
            }

        baseline_perf = self.active_session["baseline"]["fastest_run"]["Performance"]

        best_iteration = None
        if self.active_session["iterations"]:
            best_iteration = min(
                self.active_session["iterations"],
                key=lambda i: i["performance"]["Total"]
            )

        return {
            "success": True,
            "session": {
                "created_at": self.active_session["created_at"],
                "original_query": self.active_session["original_query"],
                "baseline_performance": {
                    "total_ms": baseline_perf["Total"],
                    "se_percentage": (baseline_perf["SE"] / baseline_perf["Total"] * 100) if baseline_perf["Total"] > 0 else 0,
                    "se_queries": baseline_perf.get("SE_Queries", 0)
                },
                "iterations_count": len(self.active_session["iterations"]),
                "best_iteration": {
                    "total_ms": best_iteration["performance"]["Total"],
                    "improvement_percent": best_iteration["comparison"]["improvement_percent"]
                } if best_iteration else None
            }
        }

    def _generate_iteration_message(self, comparison: Dict[str, Any]) -> str:
        """Generate user-friendly message about optimization result"""
        improvement = comparison["improvement_percent"]
        is_equivalent = comparison["semantic_equivalence"]["is_equivalent"]

        if not is_equivalent:
            return (
                f"WARNING: Results differ from baseline: {comparison['semantic_equivalence']['reason']}. "
                "Optimization is not valid."
            )

        if improvement > 20:
            return f"Excellent optimization! {improvement:.1f}% faster than baseline."
        elif improvement > 5:
            return f"Good improvement: {improvement:.1f}% faster than baseline."
        elif improvement > 0:
            return f"Minor improvement: {improvement:.1f}% faster than baseline."
        else:
            return f"No improvement: {abs(improvement):.1f}% slower than baseline."
