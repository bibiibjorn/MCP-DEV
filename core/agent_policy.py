"""
Agent policy layer for PBIXRay MCP Server

Provides orchestrated, guardrailed operations that an AI client (e.g., Claude)
can use as a single tool call. Keeps the server simple while centralizing
validation, safety limits, and fallbacks.
"""

from typing import Any, Dict, Optional, List


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
        verbose: bool = False,
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
        notes: List[str] = []

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
        # If query starts with EVALUATE and lacks TOPN, force safe TOPN by rewriting
        q_upper = (query or "").strip().upper()
        if q_upper.startswith("EVALUATE") and "TOPN(" not in q_upper:
            try:
                body = (query.strip()[len("EVALUATE"):]).strip()
                query = f"EVALUATE TOPN({lim}, {body})"
                notes.append(f"Applied TOPN({lim}) to EVALUATE query for safety")
            except Exception:
                pass

        exec_result = query_executor.validate_and_execute_dax(query, lim)
        if verbose and notes:
            exec_result.setdefault("notes", []).extend(notes)
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

    # -------- Advanced agent features --------
    def plan_query(self, intent: str, context_table: Optional[str] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Return a suggested approach and safe DAX skeleton based on a simple intent string."""
        intent_lower = (intent or "").lower()
        lim = self._get_preview_limit(max_rows)
        plan = {"success": True, "intent": intent, "recommendation": "preview", "max_rows": lim}

        if any(k in intent_lower for k in ["performance", "fast", "slow", "analyze se", "analyze fe"]):
            plan["recommendation"] = "analyze"
            plan["tool"] = "safe_run_dax(mode=analyze)"
        else:
            plan["tool"] = "safe_run_dax(mode=preview)"

        if context_table:
            plan["dax"] = f"EVALUATE TOPN({lim}, '{context_table}')"
        else:
            plan["dax"] = f"EVALUATE TOPN({lim}, <table_expression_here>)"

        plan["notes"] = [
            "Use SUMMARIZECOLUMNS / SELECTCOLUMNS for shaped previews",
            "Switch to mode=analyze for SE/FE breakdown",
        ]
        return plan

    def optimize_query(
        self,
        connection_state,
        candidate_a: str,
        candidate_b: str,
        runs: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Benchmark two DAX variants and pick a winner."""
        if not connection_state.is_connected():
            return {"success": False, "error": "Not connected", "error_type": "not_connected"}
        query_executor = connection_state.query_executor
        perf = connection_state.performance_analyzer
        r = self._get_default_perf_runs(runs)

        def basic_exec(q: str) -> Dict[str, Any]:
            res = query_executor.validate_and_execute_dax(q, 0)
            return {
                "success": bool(res.get("success")),
                "execution_time_ms": res.get("execution_time_ms", 0),
                "engine": "basic",
                "raw": res,
            }

        def perf_exec(q: str) -> Dict[str, Any]:
            if not perf:
                return basic_exec(q)
            res = perf.analyze_query(query_executor, q, r, True)
            # Prefer average total time when available
            avg_total = None
            if res.get("success"):
                avg_total = (
                    res.get("metrics", {}).get("avg_total_ms")
                    or res.get("summary", {}).get("avg_total_ms")
                )
            return {
                "success": bool(res.get("success")),
                "execution_time_ms": avg_total or 0,
                "engine": "perf" if perf else "basic",
                "raw": res,
            }

        a = perf_exec(candidate_a)
        b = perf_exec(candidate_b)

        winner = "A" if (a.get("execution_time_ms", 0) or 9e18) < (b.get("execution_time_ms", 0) or 9e18) else "B"
        return {
            "success": True,
            "runs": r,
            "candidate_a": a,
            "candidate_b": b,
            "winner": winner,
        }

    def agent_health(self, connection_manager, connection_state) -> Dict[str, Any]:
        """Consolidated health: server info, connection status, and a quick summary."""
        info = {
            "connected": connection_state.is_connected(),
            "managers_initialized": getattr(connection_state, "_managers_initialized", False),
        }
        if not info["connected"]:
            return {"success": True, "summary": info}
        # If connected, attempt a small summary
        model_summary = self.summarize_model_safely(connection_state)
        return {"success": True, "summary": info, "model": model_summary}

    def generate_docs_safe(self, connection_state) -> Dict[str, Any]:
        """Generate documentation, preferring safe/lightweight operations for large models."""
        if not connection_state.is_connected():
            return {"success": False, "error": "Not connected", "error_type": "not_connected"}
        exporter = connection_state.model_exporter
        executor = connection_state.query_executor
        if not exporter or not executor:
            return {"success": False, "error": "Required services not available", "error_type": "service_unavailable"}

        # Use get_model_summary first to get scale hints
        summary = exporter.get_model_summary(executor)
        notes: List[str] = []
        if not summary.get("success"):
            notes.append("Model summary unavailable; proceeding to basic documentation")
            return exporter.generate_documentation(executor)

        # If measure/table counts are very high, skip any heavy exports
        counts = summary.get("counts") or {}
        high = any((counts.get(k, 0) > 10000) for k in ["rows", "columns"])  # heuristic placeholder
        if high:
            notes.append("Large model detected; generating lightweight documentation")
        doc = exporter.generate_documentation(executor)
        if notes:
            doc.setdefault("notes", []).extend(notes)
        return doc
