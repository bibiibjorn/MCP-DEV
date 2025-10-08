"""
Agent policy layer for PBIXRay MCP Server

Provides orchestrated, guardrailed operations that an AI client (e.g., Claude)
can use as a single tool call. Keeps the server simple while centralizing
validation, safety limits, and fallbacks.
"""

from typing import Any, Dict, Optional


class AgentPolicy:
    def __init__(self, config):
        self.config = config

    # ---- helpers ----
    def _get_preview_limit(self, max_rows: Optional[int]) -> int:
        if isinstance(max_rows, int) and max_rows > 0:
            return max_rows
        return (
            self.config.get("query.max_rows_preview", 1000)
            or self.config.get("performance.default_top_n", 1000)
            or 1000
        )

    def _get_default_perf_runs(self, runs: Optional[int]) -> int:
        if isinstance(runs, int) and runs > 0:
            return runs
        return 3

    # ---- public orchestrations ----
    def ensure_connected(self, connection_manager, connection_state, preferred_index: Optional[int] = None) -> Dict[str, Any]:
        """Ensure the server is connected to a Power BI Desktop instance."""
        if connection_state.is_connected():
            info = connection_manager.get_instance_info() or {}
            return {
                "success": True,
                "already_connected": True,
                "instance": info,
            }

        instances = connection_manager.detect_instances()
        if not instances:
            return {
                "success": False,
                "error": "No Power BI Desktop instances detected. Open a .pbix in Power BI Desktop and try again.",
                "error_type": "no_instances",
                "suggestions": [
                    "Open Power BI Desktop with a .pbix file",
                    "Wait 10–15 seconds for the model to load",
                    "Then run detection again",
                ],
            }

        index = preferred_index if preferred_index is not None else 0
        connect_result = connection_manager.connect(index)
        if not connect_result.get("success"):
            return connect_result

        connection_state.set_connection_manager(connection_manager)
        connection_state.initialize_managers()

        return {
            "success": True,
            "connected_index": index,
            "instances": instances,
            "managers_initialized": connection_state._managers_initialized,
        }

    def safe_run_dax(
        self,
        connection_state,
        query: str,
        mode: str = "auto",
        runs: Optional[int] = None,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Validate, limit, and execute a DAX query. Optionally perform perf analysis."""
        if not connection_state.is_connected():
            return {"success": False, "error": "Not connected", "error_type": "not_connected"}

        query_executor = connection_state.query_executor
        performance_analyzer = connection_state.performance_analyzer

        if not query_executor:
            return {"success": False, "error": "Query executor not available", "error_type": "service_unavailable"}

        # First, static analysis (syntax, complexity, patterns)
        analysis = query_executor.analyze_dax_query(query)
        if not analysis.get("success"):
            return analysis
        if analysis.get("syntax_errors"):
            return {
                "success": False,
                "error": "Query validation failed",
                "error_type": "syntax_validation_error",
                "details": analysis,
            }

        lim = self._get_preview_limit(max_rows)
        effective_mode = (mode or "auto").lower()

        # Decide mode automatically: if user supplied EVALUATE and likely table expr, do preview; else analyze if explicitly requested
        do_perf = effective_mode in ("analyze",) or (
            effective_mode == "auto" and False
        )

        if do_perf:
            # Performance analysis path
            r = self._get_default_perf_runs(runs)
            if not performance_analyzer:
                # Fallback to basic execution with a note
                basic = query_executor.validate_and_execute_dax(query, 0)
                basic.setdefault("notes", []).append("Performance analyzer unavailable; returned basic execution only")
                basic["success"] = basic.get("success", False)
                return basic

            result = performance_analyzer.analyze_query(query_executor, query, r, True)
            return result

        # Preview/standard execution path with safe TOPN
        exec_result = query_executor.validate_and_execute_dax(query, lim)
        return exec_result

    def summarize_model_safely(self, connection_state) -> Dict[str, Any]:
        """Prefer lightweight summary over full exports for large models."""
        if not connection_state.is_connected():
            return {"success": False, "error": "Not connected", "error_type": "not_connected"}

        model_exporter = connection_state.model_exporter
        query_executor = connection_state.query_executor
        if not model_exporter or not query_executor:
            return {"success": False, "error": "Required services not available", "error_type": "service_unavailable"}

        # Prefer summary
        summary = model_exporter.get_model_summary(query_executor)
        if summary.get("success"):
            return summary

        # Fallback to schema export (no expressions by default in your implementation)
        schema = {
            "success": True,
            "fallback": True,
            "schema": {
                "tables": [],
                "columns": [],
                "measures": [],
                "relationships": [],
            },
            "notes": ["Model summary unavailable; returned minimal structure"],
        }
        try:
            tables = query_executor.execute_info_query("TABLES")
            columns = query_executor.execute_info_query("COLUMNS")
            measures = query_executor.execute_info_query("MEASURES", exclude_columns=["Expression"])
            relationships = query_executor.execute_info_query("RELATIONSHIPS")
            if tables.get("success"):
                schema["schema"]["tables"] = tables.get("rows", [])
            if columns.get("success"):
                schema["schema"]["columns"] = columns.get("rows", [])
            if measures.get("success"):
                schema["schema"]["measures"] = measures.get("rows", [])
            if relationships.get("success"):
                schema["schema"]["relationships"] = relationships.get("rows", [])
        except Exception:
            pass
        return schema
