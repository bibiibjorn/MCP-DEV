"""
Agent policy layer for PBIXRay MCP Server

Provides orchestrated, guardrailed operations that an AI client (e.g., Claude)
can use as a single tool call. Keeps the server simple while centralizing
validation, safety limits, and fallbacks.
"""

import time
from typing import Any, Dict, Optional, List
from core.error_handler import ErrorHandler


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
        bypass_cache: bool = False,
    ) -> Dict[str, Any]:
        """Validate, limit, and execute a DAX query. Optionally perform perf analysis."""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        query_executor = connection_state.query_executor
        performance_analyzer = connection_state.performance_analyzer

        if not query_executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

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
        if effective_mode == "auto":
            q_upper = (query or "").strip().upper()
            # If EVALUATE and not a scalar, prefer preview
            if q_upper.startswith("EVALUATE") and "TOPN(" not in q_upper:
                do_perf = False
            else:
                do_perf = True
        else:
            do_perf = effective_mode in ("analyze",)

        if do_perf:
            # Performance analysis path
            r = self._get_default_perf_runs(runs)
            if not performance_analyzer:
                # Fallback to basic execution with a note
                basic = query_executor.validate_and_execute_dax(query, 0, bypass_cache=bypass_cache)
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

        exec_result = query_executor.validate_and_execute_dax(query, lim, bypass_cache=bypass_cache)
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
            return ErrorHandler.handle_not_connected()

        model_exporter = connection_state.model_exporter
        query_executor = connection_state.query_executor
        if not model_exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        if not query_executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

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

    # optimize_query removed; use optimize_variants for both 2+ candidates

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
            return ErrorHandler.handle_not_connected()
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
            return ErrorHandler.handle_not_connected()
        exporter = connection_state.model_exporter
        executor = connection_state.query_executor
        if not exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        # Use get_model_summary first to get scale hints
        summary = exporter.get_model_summary(executor)
        notes: List[str] = []
        if not summary.get("success"):
            notes.append("Model summary unavailable; proceeding to basic documentation")
            return exporter.generate_documentation(executor)

        # If model scale is high, prefer lightweight docs
        counts = summary.get("counts") or {}
        # Prefer named counts if provided by exporter; otherwise fallback heuristics
        measures_count = counts.get("measures", counts.get("measure_count", 0))
        tables_count = counts.get("tables", counts.get("table_count", 0))
        columns_count = counts.get("columns", counts.get("column_count", 0))
        relationships_count = counts.get("relationships", counts.get("relationship_count", 0))

        is_large = (
            measures_count > 2000 or
            tables_count > 200 or
            columns_count > 10000 or
            relationships_count > 5000
        )
        if is_large:
            notes.append("Large model detected; generating lightweight documentation")
        doc = exporter.generate_documentation(executor)
        if notes:
            doc.setdefault("notes", []).extend(notes)
        return doc

    # -------- New utilities & orchestrations --------
    def warm_query_cache(self, connection_state, queries: List[str], runs: Optional[int] = 1, clear_cache: bool = False) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        perf = connection_state.performance_analyzer
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        r = max(1, int(runs or 1))
        stats: List[Dict[str, Any]] = []
        if clear_cache:
            try:
                executor.flush_cache()
                if perf:
                    # Best-effort engine cache clear
                    perf._clear_cache(executor)  # type: ignore[attr-defined]
            except Exception:
                pass
        for q in queries or []:
            times = []
            ok = True
            for _ in range(r):
                start = time.time()
                res = executor.validate_and_execute_dax(q, 0, bypass_cache=False)
                ok = ok and bool(res.get('success'))
                times.append((time.time() - start) * 1000)
            stats.append({'query': q, 'success': ok, 'runs': r, 'avg_ms': round(sum(times)/len(times), 2) if times else 0})
        return {'success': True, 'warmed': len(stats), 'results': stats}

    def analyze_queries_batch(self, connection_state, queries: List[str], runs: Optional[int] = 3, clear_cache: bool = True) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        perf = connection_state.performance_analyzer
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        r = self._get_default_perf_runs(runs)
        results: List[Dict[str, Any]] = []
        for q in queries or []:
            if perf:
                results.append(perf.analyze_query(executor, q, r, bool(clear_cache)))
            else:
                # basic timing fallback
                start = time.time()
                res = executor.validate_and_execute_dax(q, 0)
                ms = (time.time() - start) * 1000
                results.append({'success': res.get('success', False), 'query': q, 'summary': {'avg_execution_ms': round(ms, 2), 'note': 'analyzer unavailable'}})
        return {'success': True, 'runs': r, 'items': results}

    def set_cache_policy(self, connection_state, ttl_seconds: Optional[int] = None) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        changed = {}
        if isinstance(ttl_seconds, int) and ttl_seconds >= 0:
            executor.cache_ttl_seconds = ttl_seconds
            executor.flush_cache()
            changed['cache_ttl_seconds'] = ttl_seconds
        return {'success': True, 'changed': changed, 'current': {'cache_ttl_seconds': executor.cache_ttl_seconds}}

    def profile_columns(self, connection_state, table: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        # Build per-column profiling queries
        cols = columns or []
        if not cols:
            # fetch all columns for table
            info = executor.execute_info_query('COLUMNS', table_name=table)
            if not info.get('success'):
                return info
            cols = [c.get('Name') for c in info.get('rows', []) if c.get('Name')]
        results: List[Dict[str, Any]] = []
        for col in cols[:200]:  # safety cap
            q = (
                f"EVALUATE ROW(\"Min\", MIN('{table}'[{col}]), "
                f"\"Max\", MAX('{table}'[{col}]), "
                f"\"Distinct\", DISTINCTCOUNT('{table}'[{col}]), "
                f"\"Nulls\", COUNTBLANK('{table}'[{col}]))"
            )
            r = executor.validate_and_execute_dax(q, 0)
            results.append({'column': col, 'success': r.get('success', False), 'stats': (r.get('rows') or [{}])[0] if r.get('rows') else {}})
        return {'success': True, 'table': table, 'columns': len(results), 'results': results}

    def get_value_distribution(self, connection_state, table: str, column: str, top_n: int = 50) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        q = (
            f"EVALUATE TOPN({int(top_n)}, "
            f"SUMMARIZECOLUMNS('{table}'[{column}], \"Count\", COUNTROWS('{table}')), [Count], DESC)"
        )
        return executor.validate_and_execute_dax(q, 0)

    def validate_best_practices(self, connection_state) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        validator = connection_state.model_validator
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        issues: List[Dict[str, Any]] = []
        # Include integrity issues if validator available
        if validator:
            integrity = validator.validate_model_integrity()
            if integrity.get('success'):
                for i in integrity.get('issues', []):
                    issues.append(i)
        # Simple naming checks
        tables = executor.execute_info_query('TABLES')
        if tables.get('success'):
            for t in tables.get('rows', []):
                name = t.get('Name') or ''
                if name != name.strip():
                    issues.append({'type': 'naming', 'severity': 'low', 'object': f"Table:{name}", 'description': 'Leading/trailing spaces in table name'})
        measures = executor.execute_info_query('MEASURES')
        if measures.get('success'):
            for m in measures.get('rows', []):
                name = m.get('Name') or ''
                if ' ' in name and name.strip().endswith(')'):
                    pass
                # Example heuristic: discourage very short names
                if len(name.strip()) < 2:
                    issues.append({'type': 'naming', 'severity': 'low', 'object': f"Measure:{name}", 'description': 'Very short measure name'})
        return {'success': True, 'issues': issues, 'total_issues': len(issues)}

    def generate_documentation_profiled(self, connection_state, format: str = 'markdown', include_examples: bool = False) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        exporter = connection_state.model_exporter
        executor = connection_state.query_executor
        if not exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        doc = exporter.generate_documentation(executor)
        doc.setdefault('format', format)
        doc.setdefault('include_examples', include_examples)
        return doc

    def create_model_changelog(self, connection_state, reference_tmsl) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        exporter = connection_state.model_exporter
        if not exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        diff = exporter.compare_models(reference_tmsl)
        summary: Dict[str, Any] = {'notes': 'Summary generated by server'}
        if isinstance(diff, dict):
            keys_list = [str(k) for k in diff.keys()]
            summary['keys'] = keys_list
        return {'success': True, 'diff': diff, 'summary': summary}

    def get_measure_impact(self, connection_state, table: str, measure: str, depth: Optional[int] = 3) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        dep = connection_state.dependency_analyzer
        if not dep:
            return ErrorHandler.handle_manager_unavailable('dependency_analyzer')
        return dep.analyze_measure_dependencies(table, measure, depth or 3)

    def get_column_usage_heatmap(self, connection_state, table: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        dep = connection_state.dependency_analyzer
        executor = connection_state.query_executor
        if not dep:
            return ErrorHandler.handle_manager_unavailable('dependency_analyzer')
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        info = executor.execute_info_query('COLUMNS', table_name=table)
        if not info.get('success'):
            return info
        cols = info.get('rows', [])[:limit]
        results: List[Dict[str, Any]] = []
        for c in cols:
            t = table or c.get('Table') or ''
            name = c.get('Name')
            if not name:
                continue
            usage = dep.analyze_column_usage(t, name)
            results.append({'table': t, 'column': name, 'usage': usage})
        return {'success': True, 'count': len(results), 'results': results}

    def auto_document(self, connection_manager, connection_state, profile: str = 'light', include_lineage: bool = False) -> Dict[str, Any]:
        actions: List[Dict[str, Any]] = []
        ensured = self.ensure_connected(connection_manager, connection_state)
        actions.append({'action': 'ensure_connected', 'result': ensured})
        if not ensured.get('success'):
            return {'success': False, 'phase': 'ensure_connected', 'actions': actions, 'final': ensured}
        summary = self.summarize_model_safely(connection_state)
        actions.append({'action': 'summarize_model_safely', 'result': summary})
        docs = self.generate_docs_safe(connection_state)
        actions.append({'action': 'generate_docs_safe', 'result': docs})
        return {'success': docs.get('success', False), 'actions': actions, 'final': docs}

    def auto_analyze_or_preview(self, connection_manager, connection_state, query: str, runs: Optional[int] = None, max_rows: Optional[int] = None, priority: str = 'depth') -> Dict[str, Any]:
        # priority: 'speed' -> preview, 'depth' -> analyze
        mode = 'preview' if (priority or 'depth').lower() == 'speed' else 'analyze'
        return self.safe_run_dax(connection_state, query, mode=mode, runs=runs, max_rows=max_rows)

    def apply_recommended_fixes(self, connection_state, actions: List[str]) -> Dict[str, Any]:
        # Currently returns a plan; actual mutations may require TOM APIs not exposed here.
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        plan = []
        for a in actions or []:
            if a == 'hide_keys':
                plan.append({'action': a, 'status': 'suggestion', 'note': 'Hide IsKey columns in report view'})
            elif a == 'fix_summarization':
                plan.append({'action': a, 'status': 'suggestion', 'note': 'Set default summarization for numeric columns appropriately'})
            elif a == 'organize_folders':
                plan.append({'action': a, 'status': 'suggestion', 'note': 'Group measures into display folders by subject'})
            else:
                plan.append({'action': a, 'status': 'unknown'})
        return {'success': True, 'plan': plan}

    def set_performance_trace(self, connection_state, enabled: bool) -> Dict[str, Any]:
        perf = connection_state.performance_analyzer
        if not perf:
            return ErrorHandler.handle_manager_unavailable('performance_analyzer')
        if enabled:
            ok = perf.connect_amo()
            if not ok:
                return {'success': False, 'error': 'AMO not available'}
            started = perf.start_session_trace()
            return {'success': bool(started), 'trace_active': perf.trace_active}
        else:
            perf.stop_session_trace()
            return {'success': True, 'trace_active': False}

    def format_dax(self, expression: str) -> Dict[str, Any]:
        # Minimal, non-destructive formatting: trim and collapse excessive spaces
        if expression is None:
            return {'success': False, 'error': 'No expression provided'}
        text = expression.strip()
        while '  ' in text:
            text = text.replace('  ', ' ')
        return {'success': True, 'formatted': text}

    def export_model_overview(self, connection_state, format: str = 'json', include_counts: bool = True) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        exporter = connection_state.model_exporter
        executor = connection_state.query_executor
        if not exporter:
            return ErrorHandler.handle_manager_unavailable('model_exporter')
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        summary = exporter.get_model_summary(executor)
        if not summary.get('success'):
            return summary
        return {'success': True, 'format': format, 'overview': summary}

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
            # Use optimize_variants for 2-candidate case to avoid duplicate tooling
            bench = self.optimize_variants(connection_state, [candidate_a, candidate_b], runs)
            actions.append({"action": "optimize_variants", "result": bench})
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
