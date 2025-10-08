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
                basic.setdefault("decision", "analyze")
                basic.setdefault("reason", "Requested performance analysis, but analyzer unavailable; returned basic execution")
                return basic

            result = performance_analyzer.analyze_query(query_executor, query, r, True)
            result.setdefault("decision", "analyze")
            result.setdefault("reason", "Performance analysis selected to obtain FE/SE breakdown and average timings")
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
        exec_result.setdefault("decision", "preview")
        exec_result.setdefault("reason", "Fast preview chosen to minimize latency and limit rows safely with TOPN")
        if verbose:
            # Attach lightweight analysis/suggestions for best practices visibility
            exec_result.setdefault("analysis", analysis)
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
                # Standard path in EnhancedAMOTraceAnalyzer
                summary = res.get("summary") or {}
                avg_total = summary.get("avg_execution_ms")
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
            "decision": "optimize_query",
            "reason": f"Chose candidate {winner} based on the lower average execution time"
        }

    def optimize_variants(
        self,
        connection_state,
        candidates: List[str],
        runs: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Benchmark N DAX variants and return the fastest.

        Returns per-variant timings and a winner with minimal avg_execution_ms.
        """
        if not connection_state.is_connected():
            return {"success": False, "error": "Not connected", "error_type": "not_connected"}
        if not candidates or len([c for c in candidates if (c or "").strip()]) < 2:
            return {"success": False, "error": "Provide at least two non-empty candidates", "error_type": "invalid_input"}

        query_executor = connection_state.query_executor
        perf = connection_state.performance_analyzer
        r = self._get_default_perf_runs(runs)

        def run_bench(q: str) -> Dict[str, Any]:
            q = q or ""
            if perf:
                res = perf.analyze_query(query_executor, q, r, True)
                summary = res.get("summary") or {}
                avg_ms = summary.get("avg_execution_ms") or 0
                return {"success": bool(res.get("success")), "execution_time_ms": avg_ms, "raw": res}
            else:
                res = query_executor.validate_and_execute_dax(q, 0)
                return {"success": bool(res.get("success")), "execution_time_ms": res.get("execution_time_ms", 0), "raw": res}

        results: List[Dict[str, Any]] = []
        for idx, cand in enumerate(candidates):
            results.append({"candidate": idx, **run_bench(cand)})

        # Choose the minimal positive time; if all zero/False, mark no_winner
        valid = [r for r in results if r.get("success") and r.get("execution_time_ms", 0) >= 0]
        if not valid:
            return {"success": False, "error": "All candidates failed", "results": results}
        winner = min(valid, key=lambda r: r.get("execution_time_ms", float("inf")))
        return {"success": True, "runs": r, "results": results, "winner": winner, "decision": "optimize_variants", "reason": "Selected variant with minimum average execution time across runs"}

    def decide_and_run(
        self,
        connection_manager,
        connection_state,
        goal: str,
        query: Optional[str] = None,
        candidates: Optional[List[str]] = None,
        runs: Optional[int] = None,
        max_rows: Optional[int] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Performance-first decision orchestrator.

        - Ensures connection
        - If multiple candidates → benchmark and return the winner
        - Else if goal mentions performance → analyze query
        - Else → fast preview with safe TOPN
        """
        actions: List[Dict[str, Any]] = []
        ensured = self.ensure_connected(connection_manager, connection_state)
        actions.append({"action": "ensure_connected", "result": ensured})
        if not ensured.get("success"):
            return {"success": False, "phase": "ensure_connected", "actions": actions, "final": ensured}

        text = (goal or "").lower()
        nonempty_candidates = [c for c in (candidates or []) if (c or "").strip()]

        if len(nonempty_candidates) >= 2:
            bench = self.optimize_variants(connection_state, nonempty_candidates, runs)
            actions.append({"action": "optimize_variants", "result": bench})
            return {"success": bench.get("success", False), "decision": "optimize_variants", "reason": "Multiple candidates provided; benchmarking to pick the fastest", "actions": actions, "final": bench}

        if any(k in text for k in ["analyze", "performance", "perf", "se/fe", "storage engine", "formula engine"]):
            if not query:
                return {"success": False, "error": "No query provided for performance analysis", "phase": "input_validation", "actions": actions}
            res = self.safe_run_dax(connection_state, query, mode="analyze", runs=runs, max_rows=max_rows, verbose=verbose)
            actions.append({"action": "safe_run_dax(analyze)", "result": res})
            return {"success": res.get("success", False), "decision": "analyze", "reason": "Goal indicates performance focus; running analyzer for FE/SE breakdown", "actions": actions, "final": res}

        # Default to preview for speed
        res = self.safe_run_dax(connection_state, query or "", mode="preview", runs=runs, max_rows=max_rows, verbose=verbose)
        actions.append({"action": "safe_run_dax(preview)", "result": res})
        return {"success": res.get("success", False), "decision": "preview", "reason": "No performance focus or multiple candidates; using fast safe preview for minimal latency", "actions": actions, "final": res}

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

    # -------- NL intent executor --------
    def execute_intent(
        self,
        connection_manager,
        connection_state,
        goal: str,
        query: Optional[str] = None,
        table: Optional[str] = None,
        runs: Optional[int] = None,
        max_rows: Optional[int] = None,
        verbose: bool = False,
        candidate_a: Optional[str] = None,
        candidate_b: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Simple rule-based intent executor so users don't need to say 'run safely'.
        Decides which orchestrations to call based on keywords and inputs.
        """
        # Ensure connection first
        ensured = self.ensure_connected(connection_manager, connection_state)
        actions: List[Dict[str, Any]] = [{"action": "ensure_connected", "result": ensured}]
        if not ensured.get("success"):
            return {"success": False, "error": "Connection not established", "phase": "ensure_connected", "details": ensured}

        text = (goal or "").lower()

        # Optimization benchmark if both candidates present
        if candidate_a and candidate_b:
            bench = self.optimize_query(connection_state, candidate_a, candidate_b, runs)
            actions.append({"action": "optimize_query", "result": bench})
            return {"success": bench.get("success", False), "actions": actions, "final": bench}

        # Documentation or model summary intents
        if any(k in text for k in ["document", "documentation", "docs", "summarize", "overview", "schema", "structure", "model summary", "list tables", "list measures", "relationship"]):
            # Prefer a safe summary
            summary = self.summarize_model_safely(connection_state)
            actions.append({"action": "summarize_model", "result": summary})
            if not summary.get("success"):
                return {"success": False, "phase": "summarize_model", "actions": actions, "final": summary}
            # If explicitly asked to document, proceed to docs
            if any(k in text for k in ["document", "documentation", "docs"]):
                doc = self.generate_docs_safe(connection_state)
                actions.append({"action": "generate_docs_safe", "result": doc})
                return {"success": doc.get("success", False), "actions": actions, "final": doc}
            return {"success": True, "actions": actions, "final": summary}

        # Performance analysis intents
        if any(k in text for k in ["analyze performance", "performance", "perf", "se/fe", "storage engine", "formula engine"]):
            if not query:
                return {"success": False, "error": "No query provided for performance analysis", "phase": "input_validation", "actions": actions}
            res = self.safe_run_dax(connection_state, query, mode="analyze", runs=runs, max_rows=max_rows, verbose=verbose)
            actions.append({"action": "safe_run_dax(analyze)", "result": res})
            return {"success": res.get("success", False), "actions": actions, "final": res}

        # Generic run/query/preview intents
        if query or any(k in text for k in ["run", "execute", "preview", "query", "show"]):
            res = self.safe_run_dax(connection_state, query or "", mode="preview", runs=runs, max_rows=max_rows, verbose=verbose)
            actions.append({"action": "safe_run_dax(preview)", "result": res})
            return {"success": res.get("success", False), "actions": actions, "final": res}

        # Health/status intents
        if any(k in text for k in ["health", "status", "connected", "ready"]):
            health = self.agent_health(connection_manager, connection_state)
            actions.append({"action": "agent_health", "result": health})
            return {"success": health.get("success", False), "actions": actions, "final": health}

        # Default: plan based on table context
        plan = self.plan_query(text, table, max_rows)
        actions.append({"action": "plan_query", "result": plan})
        return {"success": True, "actions": actions, "final": plan}
