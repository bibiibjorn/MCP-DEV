"""
Agent policy layer for PBIXRay MCP Server

Provides orchestrated, guardrailed operations that an AI client (e.g., Claude)
can use as a single tool call. Keeps the server simple while centralizing
validation, safety limits, and fallbacks.
"""

import time
import os
import csv
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
from core.error_handler import ErrorHandler
from core.policies.query_policy import QueryPolicy
from core.documentation_builder import (
    collect_model_documentation,
    compute_diff,
    load_snapshot,
    render_word_report,
    save_snapshot,
    snapshot_from_context,
)


logger = logging.getLogger("mcp_powerbi_finvision")


class AgentPolicy:
    def __init__(self, config, timeout_manager=None, cache_manager=None, rate_limiter=None):
        self.config = config
        self.timeout_manager = timeout_manager
        self.cache_manager = cache_manager
        self.rate_limiter = rate_limiter
        # Initialize policy helpers
        try:
            self.query_policy: Optional[QueryPolicy] = QueryPolicy(config)
        except Exception:
            self.query_policy = None

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
        include_event_counts: bool = False,
    ) -> Dict[str, Any]:
        """Validate, limit, and execute a DAX query. Optionally perform perf analysis."""
        qp = self.query_policy
        if qp is not None:
            return qp.safe_run_dax(
                connection_state,
                query,
                mode=mode,
                runs=runs,
                max_rows=max_rows,
                verbose=verbose,
                bypass_cache=bypass_cache,
                include_event_counts=include_event_counts,
            )
        # Fallback: in rare case policy import failed, use legacy logic
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        qe = connection_state.query_executor
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        return qe.validate_and_execute_dax(query, 0)

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

    def analyze_queries_batch(self, connection_state, queries: List[str], runs: Optional[int] = 3, clear_cache: bool = True, include_event_counts: bool = False) -> Dict[str, Any]:
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
                results.append(perf.analyze_query(executor, q, r, bool(clear_cache), include_event_counts))
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

    def generate_model_documentation_word(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 1,
        export_pdf: bool = False,
    ) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        try:
            lightweight_bpa = self.validate_best_practices(connection_state)
        except Exception:
            lightweight_bpa = None

        context = collect_model_documentation(
            connection_state,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth,
            lightweight_best_practices=lightweight_bpa if isinstance(lightweight_bpa, dict) else None,
        )
        if not context.get('success'):
            return context

        # graph_path, graph_notes = generate_relationship_graph(context.get('relationships', [])  # Visualization removed, output_dir)
        graph_path = None  # Visualization removed
        graph_notes = []  # Visualization removed

        doc_result = render_word_report(
            context,
            output_dir=output_dir,
            graph_path=graph_path,
            graph_notes=graph_notes,
            change_summary=None,
            mode='full',
            export_pdf=export_pdf,
        )
        if not doc_result.get('success'):
            return doc_result

        snapshot_result = save_snapshot(context, output_dir)
        response: Dict[str, Any] = {
            'success': True,
            'doc_path': doc_result.get('doc_path'),
            'snapshot_path': snapshot_result.get('snapshot_path'),
            'graph_path': graph_path,
            'counts': (context.get('summary') or {}).get('counts'),
            'best_practices': context.get('best_practices'),
        }
        if doc_result.get('pdf_path'):
            response['pdf_path'] = doc_result.get('pdf_path')
        if doc_result.get('pdf_warning'):
            response['pdf_warning'] = doc_result.get('pdf_warning')
        if graph_notes:
            response['graph_notes'] = graph_notes
        if context.get('notes'):
            response['notes'] = context.get('notes')
        return response

    def update_model_documentation_word(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        snapshot_path: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 1,
        export_pdf: bool = False,
    ) -> Dict[str, Any]:
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = getattr(connection_state, 'query_executor', None)
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        try:
            lightweight_bpa = self.validate_best_practices(connection_state)
        except Exception:
            lightweight_bpa = None

        try:
            database_name = qe._get_database_name()
        except Exception:
            database_name = None

        previous_snapshot = load_snapshot(snapshot_path, output_dir, database_name)

        context = collect_model_documentation(
            connection_state,
            include_hidden=include_hidden,
            dependency_depth=dependency_depth,
            lightweight_best_practices=lightweight_bpa if isinstance(lightweight_bpa, dict) else None,
        )
        if not context.get('success'):
            return context

        new_snapshot = snapshot_from_context(context)
        diff = compute_diff(previous_snapshot, new_snapshot)

        # graph_path, graph_notes = generate_relationship_graph(context.get('relationships', [])  # Visualization removed, output_dir)
        graph_path = None  # Visualization removed
        graph_notes = []  # Visualization removed

        doc_result = render_word_report(
            context,
            output_dir=output_dir,
            graph_path=graph_path,
            graph_notes=graph_notes,
            change_summary=diff,
            mode='update',
            export_pdf=export_pdf,
        )
        if not doc_result.get('success'):
            return doc_result

        snapshot_result = save_snapshot(context, output_dir)

        response: Dict[str, Any] = {
            'success': True,
            'doc_path': doc_result.get('doc_path'),
            'snapshot_path': snapshot_result.get('snapshot_path'),
            'graph_path': graph_path,
            'change_summary': diff,
            'best_practices': context.get('best_practices'),
        }
        if doc_result.get('pdf_path'):
            response['pdf_path'] = doc_result.get('pdf_path')
        if doc_result.get('pdf_warning'):
            response['pdf_warning'] = doc_result.get('pdf_warning')
        if graph_notes:
            response['graph_notes'] = graph_notes
        if context.get('notes'):
            response['notes'] = context.get('notes')
        if not diff.get('changes_detected'):
            response['message'] = 'No structural changes detected; documentation refreshed with latest metadata.'
        return response

    def export_interactive_relationship_graph(
        self,
        connection_state,
        output_dir: Optional[str] = None,
        include_hidden: bool = True,
        dependency_depth: int = 5,
    ) -> Dict[str, Any]:
        """Export an interactive HTML dependency explorer (replaces old relationship graph).

        This generates a comprehensive interactive HTML app that shows:
        - Tables with their dependencies, measures, columns, and relationships
        - Measures with dependency trees (forward and reverse)
        - Interactive relationship graph visualization with D3.js
        - Full search and navigation capabilities

        Args:
            connection_state: Active connection state
            output_dir: Optional output directory for HTML file
            include_hidden: Include hidden objects in analysis (default: True)
            dependency_depth: Maximum depth for dependency tree analysis

        Returns:
            Dictionary with success status and file path
        """
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        try:
            # Use new comprehensive dependency explorer
            from core.documentation import generate_interactive_dependency_explorer

            html_path, error_notes = generate_interactive_dependency_explorer(
                connection_state,
                output_dir=output_dir,
                include_hidden=include_hidden,
                dependency_depth=dependency_depth
            )

            if html_path:
                return {
                    'success': True,
                    'html_path': html_path,
                    'notes': error_notes if error_notes else []
                }
            else:
                # Provide more detailed error information
                error_msg = 'Failed to generate interactive dependency explorer'
                if error_notes and len(error_notes) > 0:
                    error_msg = error_notes[0] if isinstance(error_notes, list) else str(error_notes)
                return {
                    'success': False,
                    'error': error_msg,
                    'notes': error_notes if isinstance(error_notes, list) else [str(error_notes)]
                }

        except Exception as e:
            logger.error(f"Error generating dependency explorer: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to generate dependency explorer: {str(e)}'
            }

    def export_interactive_relationship_graph_legacy(
        self,
        connection_state,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Legacy method for backward compatibility - exports simple Plotly relationship graph."""
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        qe = getattr(connection_state, 'query_executor', None)
        if not qe:
            return ErrorHandler.handle_manager_unavailable('query_executor')

        # Get relationships
        relationships_res = qe.execute_info_query("RELATIONSHIPS")
        if not relationships_res.get('success'):
            return {
                'success': False,
                'error': 'Failed to fetch relationships from model',
                'details': relationships_res
            }

        relationships_rows = relationships_res.get('rows', [])
        if not relationships_rows:
            return {
                'success': False,
                'error': 'No relationships found in the model'
            }

        # Convert to standard format
        from core.documentation_builder import generate_interactive_relationship_graph

        def _pick(row: Dict[str, Any], *keys: str, default: Any = None) -> Any:
            for key in keys:
                if key in row and row[key] not in (None, ""):
                    return row[key]
                alt = f"[{key}]"
                if alt in row and row[alt] not in (None, ""):
                    return row[alt]
            return default

        def _to_bool(value: Any) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                return value.strip().lower() in {"true", "1", "yes", "y"}
            return False

        relationships: List[Dict[str, Any]] = []
        for rel in relationships_rows:
            relationships.append({
                "from_table": str(_pick(rel, "FromTable", default="")),
                "from_column": str(_pick(rel, "FromColumn", default="")),
                "to_table": str(_pick(rel, "ToTable", default="")),
                "to_column": str(_pick(rel, "ToColumn", default="")),
                "is_active": _to_bool(_pick(rel, "IsActive", default=False)),
                "cardinality": str(_pick(rel, "Cardinality", default=_pick(rel, "RelationshipType", default=""))),
                "direction": str(_pick(rel, "CrossFilterDirection", default="")),
            })

        graph_path, graph_notes = generate_interactive_relationship_graph(relationships, output_dir)

        if graph_path:
            return {
                'success': True,
                'graph_path': graph_path,
                'relationships_count': len(relationships),
                'notes': graph_notes
            }
        else:
            return {
                'success': False,
                'error': 'Failed to generate interactive relationship graph',
                'notes': graph_notes
            }

    def relationship_overview(self, connection_state) -> Dict[str, Any]:
        """Return relationships list plus optional cardinality checks.

        This prevents brittle DMV/DAX attempts from the client and offers
        a stable, typed response for relationship exploration.
        """
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        executor = connection_state.query_executor
        if not executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
        rels = executor.execute_info_query('RELATIONSHIPS')
        result: Dict[str, Any] = {'success': bool(rels.get('success')), 'relationships': rels.get('rows', []), 'count': len(rels.get('rows', []) if rels.get('success') else [])}
        # Optionally attach issue analysis when available
        perf_opt = getattr(connection_state, 'performance_optimizer', None)
        try:
            if perf_opt:
                analysis = perf_opt.analyze_relationship_cardinality()
                result['analysis'] = analysis
        except Exception:
            # Non-fatal; just omit analysis
            pass
        return result

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
            qe = connection_state.query_executor
            if not qe:
                return ErrorHandler.handle_manager_unavailable('query_executor')
            started = perf.start_session_trace(qe)
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

        # Schema + samples intent: produce flat list with sample values per column
        if any(k in text for k in [
            "sample row", "sample rows", "sample values", "columns with sample", "columns and samples",
            "flat schema", "schema samples", "all tables and columns with sample"
        ]):
            # Determine preferred format from intent
            fmt = 'csv'
            if 'excel' in text or 'xlsx' in text:
                fmt = 'xlsx'
            elif 'txt' in text or 'text' in text:
                fmt = 'txt'
            # Detect desired row count (1-10) if present
            import re
            m = re.search(r"(\d+)\s*(sample|row|rows)", text)
            rows = 3
            try:
                if m:
                    rows = max(1, min(10, int(m.group(1))))
            except Exception:
                pass

        # Relationship-focused intents: return list and analysis directly
        if any(k in text for k in ["relationship", "relationships", "rels", "cardinality", "relations"]):
            rel = self.relationship_overview(connection_state)
            actions.append({"action": "relationship_overview", "result": rel})
            return {"success": rel.get("success", False), "actions": actions, "final": rel}

        # Optimization benchmark if both candidates present
        if candidate_a and candidate_b:
            # Use optimize_variants for 2-candidate case to avoid duplicate tooling
            bench = self.optimize_variants(connection_state, [candidate_a, candidate_b], runs)
            actions.append({"action": "optimize_variants", "result": bench})
            return {"success": bench.get("success", False), "actions": actions, "final": bench}

        # Documentation or model summary intents
        if any(k in text for k in ["document", "documentation", "docs", "summarize", "overview", "schema", "structure", "model summary", "list tables", "list measures"]):
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

        # If user asks to analyze the model without specifics, propose options (fast vs normal)
        if any(k in text for k in ["analyze", "analysis"]) and not query and not any(k in text for k in ["performance", "perf", "se/fe", "storage engine", "formula engine"]):
            proposal = self.propose_analysis_options(connection_state, goal)
            actions.append({"action": "propose_analysis_options", "result": proposal})
            return {"success": True, "decision": "propose_analysis", "actions": actions, "final": proposal}

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

    def analyze_best_practices_unified(
        self,
        connection_state,
        mode: str = "all",
        bpa_profile: str = "balanced",
        max_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Unified best practices analysis combining BPA and M query practices.

        Args:
            connection_state: Active connection state
            mode: "all" (both BPA and M), "bpa" (BPA only), "m_queries" (M only)
            bpa_profile: BPA analysis depth - "fast", "balanced", or "deep"
            max_seconds: Maximum time for BPA analysis

        Returns:
            Combined analysis results
        """
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        mode = (mode or "all").lower()
        results: Dict[str, Any] = {
            'success': True,
            'mode': mode,
            'analyses': {}
        }

        # Run BPA if requested
        if mode in ("all", "bpa"):
            bpa_analyzer = connection_state.bpa_analyzer
            if bpa_analyzer:
                try:
                    bpa_result = bpa_analyzer.run_bpa(
                        mode=bpa_profile,
                        max_seconds=max_seconds
                    )
                    results['analyses']['bpa'] = bpa_result
                except Exception as e:
                    results['analyses']['bpa'] = {
                        'success': False,
                        'error': f'BPA analysis failed: {str(e)}'
                    }
            else:
                results['analyses']['bpa'] = {
                    'success': False,
                    'error': 'BPA analyzer not available',
                    'note': 'Install BPA dependencies to enable this analysis'
                }

        # Run M query practices scan if requested
        if mode in ("all", "m_queries"):
            try:
                from server.utils.m_practices import scan_m_practices
                m_result = scan_m_practices(connection_state.query_executor)
                results['analyses']['m_practices'] = m_result
            except Exception as e:
                results['analyses']['m_practices'] = {
                    'success': False,
                    'error': f'M practices scan failed: {str(e)}'
                }

        # Aggregate summary
        total_issues = 0
        for analysis_name, analysis_result in results['analyses'].items():
            if isinstance(analysis_result, dict):
                issues_count = analysis_result.get('total_issues', 0) or len(analysis_result.get('issues', []))
                total_issues += issues_count

        results['total_issues'] = total_issues
        results['summary'] = f'Found {total_issues} total issues across {len(results["analyses"])} analyses'

        return results

    def analyze_performance_unified(
        self,
        connection_state,
        mode: str = "comprehensive",
        queries: Optional[List[str]] = None,
        table: Optional[str] = None,
        runs: int = 3,
        clear_cache: bool = True,
        include_event_counts: bool = False
    ) -> Dict[str, Any]:
        """
        Unified performance analysis combining query performance, cardinality, and storage.

        Args:
            connection_state: Active connection state
            mode: "comprehensive" (all), "queries" (query batch only), "cardinality" (relationship/column),
                  "storage" (storage compression only)
            queries: List of DAX queries for batch performance testing
            table: Table name for table-specific analyses
            runs: Number of runs for query performance testing
            clear_cache: Whether to clear cache before performance testing
            include_event_counts: Include detailed event counts in query analysis

        Returns:
            Combined performance analysis results
        """
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()

        mode = (mode or "comprehensive").lower()
        performance_optimizer = connection_state.performance_optimizer

        results: Dict[str, Any] = {
            'success': True,
            'mode': mode,
            'analyses': {}
        }

        # Run query batch performance if requested and queries provided
        if mode in ("comprehensive", "queries") and queries:
            perf_result = self.analyze_queries_batch(
                connection_state,
                queries,
                runs=runs,
                clear_cache=clear_cache,
                include_event_counts=include_event_counts
            )
            results['analyses']['query_performance'] = perf_result

        # Run cardinality analysis if requested
        if mode in ("comprehensive", "cardinality"):
            if performance_optimizer:
                try:
                    # Relationship cardinality
                    rel_card = performance_optimizer.analyze_relationship_cardinality()
                    results['analyses']['relationship_cardinality'] = rel_card

                    # Column cardinality if table specified
                    if table:
                        col_card = performance_optimizer.analyze_column_cardinality(table)
                        results['analyses']['column_cardinality'] = col_card
                except Exception as e:
                    results['analyses']['cardinality_error'] = {
                        'success': False,
                        'error': f'Cardinality analysis failed: {str(e)}'
                    }
            else:
                results['analyses']['cardinality'] = {
                    'success': False,
                    'error': 'Performance optimizer not available'
                }

        # Run storage compression analysis if requested
        if mode in ("comprehensive", "storage") and table:
            if performance_optimizer:
                try:
                    storage_result = performance_optimizer.analyze_encoding_efficiency(table)
                    results['analyses']['storage_compression'] = storage_result
                except Exception as e:
                    results['analyses']['storage_error'] = {
                        'success': False,
                        'error': f'Storage analysis failed: {str(e)}'
                    }
            else:
                results['analyses']['storage'] = {
                    'success': False,
                    'error': 'Performance optimizer not available'
                }

        # Generate summary
        analysis_count = len([a for a in results['analyses'].values() if isinstance(a, dict) and a.get('success')])
        results['summary'] = f'Completed {analysis_count} performance analyses'

        return results

    def propose_analysis_options(self, connection_state, goal: Optional[str] = None) -> Dict[str, Any]:
        """Return a simple decision card offering Fast vs Normal analysis using full_analysis.

        - Fast: summary + relationships only (profile=fast, depth=light, include_bpa=false)
        - Normal: full sections (profile=balanced, depth=standard, include_bpa=true when available)
        """
        # Determine if connected for realistic expectation
        connected = connection_state.is_connected()
        notes = []
        if not connected:
            notes.append("Not connected yet; choose an option to auto-connect and run.")
        options: List[Dict[str, Any]] = [
            {
                'name': 'Fast summary',
                'id': 'fast',
                'description': 'Very quick summary of model (tables, columns, measures, relationships) with relationship list.',
                'estimated_time': 'few seconds',
                'call': {
                    'tool': 'full_analysis',
                    'arguments': {
                        'profile': 'fast',
                        'depth': 'light',
                        'include_bpa': False,
                        'limits': {'relationships_max': 200, 'issues_max': 200}
                    }
                }
            },
            {
                'name': 'Normal analysis',
                'id': 'normal',
                'description': 'Comprehensive analysis including best practices and M scan; optionally BPA if available.',
                'estimated_time': 'tens of seconds',
                'call': {
                    'tool': 'full_analysis',
                    'arguments': {
                        'profile': 'balanced',
                        'depth': 'standard',
                        'include_bpa': True,
                        'limits': {'relationships_max': 200, 'issues_max': 200}
                    }
                }
            }
        ]
        return {
            'success': True,
            'decision': 'propose_analysis',
            'goal': goal,
            'connected': connected,
            'options': options,
            'notes': notes
        }

    # ---- PBIP Enhanced Analysis ----
    def analyze_pbip_repository_enhanced(
        self,
        repo_path: str,
        output_path: str = "exports/pbip_analysis",
        exclude_folders: Optional[List[str]] = None,
        bpa_rules_path: Optional[str] = "config/bpa_rules_comprehensive.json",
        enable_enhanced: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive PBIP repository analysis with enhanced features.

        Args:
            repo_path: Path to PBIP repository
            output_path: Output directory for reports
            exclude_folders: Optional list of folders to exclude
            bpa_rules_path: Optional path to BPA rules JSON file
            enable_enhanced: Enable enhanced analysis features

        Returns:
            Dictionary with analysis results and HTML report path
        """
        try:
            from core.pbip_project_scanner import PbipProjectScanner
            from core.pbip_model_analyzer import TmdlModelAnalyzer
            from core.pbip_report_analyzer import PbirReportAnalyzer
            from core.pbip_dependency_engine import PbipDependencyEngine
            from core.pbip_html_generator import PbipHtmlGenerator
            from core.pbip_enhanced_analyzer import EnhancedPbipAnalyzer

            logger.info(f"Starting PBIP analysis: {repo_path}")

            # Step 1: Scan repository
            scanner = PbipProjectScanner()
            projects = scanner.scan_repository(repo_path, exclude_folders or [])

            semantic_models = projects.get("semantic_models", [])
            reports = projects.get("reports", [])

            if not semantic_models:
                return {
                    "success": False,
                    "error": "No semantic models found in repository",
                    "error_type": "no_models"
                }

            # Step 2: Analyze semantic model (first one)
            model = semantic_models[0]
            model_folder = model.get("model_folder")

            if not model_folder:
                return {
                    "success": False,
                    "error": "No model folder found",
                    "error_type": "invalid_model"
                }

            analyzer = TmdlModelAnalyzer()
            model_data = analyzer.analyze_model(model_folder)

            # Step 3: Analyze report (if available)
            report_data = None
            if reports:
                report = reports[0]
                report_folder = report.get("report_folder")
                if report_folder:
                    report_analyzer = PbirReportAnalyzer()
                    report_data = report_analyzer.analyze_report(report_folder)

            # Step 4: Dependency analysis
            dep_engine = PbipDependencyEngine(model_data, report_data)
            dependencies = dep_engine.analyze_all_dependencies()

            # Step 5: Enhanced analysis (if enabled)
            enhanced_results = None
            if enable_enhanced:
                logger.info("Running enhanced analysis...")
                enhanced_analyzer = EnhancedPbipAnalyzer(model_data, report_data, dependencies)
                enhanced_results = enhanced_analyzer.run_full_analysis(bpa_rules_path)

                logger.info(
                    f"Enhanced analysis complete: "
                    f"{len(enhanced_results.get('analyses', {}).get('column_lineage', {}))} columns tracked, "
                    f"{enhanced_results.get('analyses', {}).get('dax_quality', {}).get('summary', {}).get('total_issues', 0)} DAX issues found"
                )

            # Step 6: Generate HTML report
            generator = PbipHtmlGenerator()
            html_path = generator.generate_full_report(
                model_data,
                report_data,
                dependencies,
                output_path,
                os.path.basename(repo_path),
                enhanced_results=enhanced_results
            )

            # Build summary
            summary = {
                "success": True,
                "repository": repo_path,
                "html_report": html_path,
                "statistics": {
                    "tables": len(model_data.get("tables", [])),
                    "measures": sum(len(t.get("measures", [])) for t in model_data.get("tables", [])),
                    "columns": sum(len(t.get("columns", [])) for t in model_data.get("tables", [])),
                    "relationships": len(model_data.get("relationships", [])),
                    "pages": len(report_data.get("pages", [])) if report_data else 0,
                    "visuals": sum(len(p.get("visuals", [])) for p in report_data.get("pages", [])) if report_data else 0,
                    "unused_measures": dependencies.get("summary", {}).get("unused_measures", 0),
                    "unused_columns": dependencies.get("summary", {}).get("unused_columns", 0)
                }
            }

            # Add enhanced statistics if available
            if enhanced_results:
                summary["enhanced_statistics"] = {
                    "column_lineage_tracked": len(enhanced_results.get("analyses", {}).get("column_lineage", {})),
                    "data_type_issues": len(enhanced_results.get("analyses", {}).get("data_types", {}).get("type_issues", [])),
                    "cardinality_warnings": len(enhanced_results.get("analyses", {}).get("cardinality", {}).get("cardinality_warnings", [])),
                    "relationship_issues": len(enhanced_results.get("analyses", {}).get("relationships", {}).get("issues", [])),
                    "dax_quality_issues": len(enhanced_results.get("analyses", {}).get("dax_quality", {}).get("quality_issues", [])),
                    "naming_violations": len(enhanced_results.get("analyses", {}).get("naming_conventions", {}).get("violations", [])),
                    "high_complexity_measures": enhanced_results.get("analyses", {}).get("dax_quality", {}).get("summary", {}).get("high_complexity_measures", 0)
                }

                # Add BPA statistics if available
                if enhanced_results.get("analyses", {}).get("bpa"):
                    bpa_summary = enhanced_results["analyses"]["bpa"].get("summary", {})
                    summary["enhanced_statistics"]["bpa_violations"] = bpa_summary.get("total", 0)
                    summary["enhanced_statistics"]["bpa_errors"] = bpa_summary.get("by_severity", {}).get("ERROR", 0)
                    summary["enhanced_statistics"]["bpa_warnings"] = bpa_summary.get("by_severity", {}).get("WARNING", 0)

            return summary

        except Exception as e:
            logger.error(f"PBIP analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "analysis_error"
            }

    def get_column_lineage(
        self,
        repo_path: str,
        column_key: str,
        exclude_folders: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed lineage information for a specific column.

        Args:
            repo_path: Path to PBIP repository
            column_key: Column identifier (Table[Column])
            exclude_folders: Optional list of folders to exclude

        Returns:
            Dictionary with column lineage details
        """
        try:
            from core.pbip_project_scanner import PbipProjectScanner
            from core.pbip_model_analyzer import TmdlModelAnalyzer
            from core.pbip_report_analyzer import PbirReportAnalyzer
            from core.pbip_dependency_engine import PbipDependencyEngine
            from core.pbip_enhanced_analyzer import EnhancedPbipAnalyzer

            # Analyze model
            scanner = PbipProjectScanner()
            projects = scanner.scan_repository(repo_path, exclude_folders or [])

            if not projects.get("semantic_models"):
                return {"success": False, "error": "No semantic models found"}

            model = projects["semantic_models"][0]
            analyzer = TmdlModelAnalyzer()
            model_data = analyzer.analyze_model(model["model_folder"])

            # Analyze report if available
            report_data = None
            if projects.get("reports"):
                report = projects["reports"][0]
                if report.get("report_folder"):
                    report_analyzer = PbirReportAnalyzer()
                    report_data = report_analyzer.analyze_report(report["report_folder"])

            # Build dependencies
            dep_engine = PbipDependencyEngine(model_data, report_data)
            dependencies = dep_engine.analyze_all_dependencies()

            # Get lineage
            enhanced_analyzer = EnhancedPbipAnalyzer(model_data, report_data, dependencies)
            lineage = enhanced_analyzer.lineage_analyzer.analyze_column_lineage()

            if column_key not in lineage:
                return {
                    "success": False,
                    "error": f"Column not found: {column_key}",
                    "available_columns": list(lineage.keys())[:10]
                }

            # Get impact analysis
            impact = enhanced_analyzer.lineage_analyzer.calculate_column_impact(column_key)

            return {
                "success": True,
                "column": column_key,
                "lineage": lineage[column_key],
                "impact_analysis": impact
            }

        except Exception as e:
            logger.error(f"Column lineage analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": "lineage_error"
            }
