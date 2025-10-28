from typing import Any, Dict, List, Optional
from core.validation.error_handler import ErrorHandler


class QueryPolicy:
    def __init__(self, config: Any):
        self.config = config

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
        if not connection_state.is_connected():
            return ErrorHandler.handle_not_connected()
        query_executor = connection_state.query_executor
        performance_analyzer = connection_state.performance_analyzer
        if not query_executor:
            return ErrorHandler.handle_manager_unavailable('query_executor')
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
        try:
            limits = connection_state.get_safety_limits()
            max_rows_cap = int(limits.get('max_rows_per_call', 10000))
            if isinstance(lim, int) and lim > 0:
                lim = min(lim, max_rows_cap)
        except Exception:
            pass
        effective_mode = (mode or "auto").lower()
        notes: List[str] = []
        if effective_mode == "auto":
            q_upper = (query or "").strip().upper()
            do_perf = not (q_upper.startswith("EVALUATE") and "TOPN(" not in q_upper)
        else:
            # Support both "analyze" and "profile" modes for performance analysis
            # "simple" mode is treated as preview (no performance analysis)
            do_perf = effective_mode in ("analyze", "profile")
        if do_perf:
            r = self._get_default_perf_runs(runs)
            if not performance_analyzer:
                basic = query_executor.validate_and_execute_dax(query, 0, bypass_cache=bypass_cache)
                basic.setdefault("notes", []).append("Performance analyzer unavailable; returned basic execution only")
                basic["success"] = basic.get("success", False)
                basic.setdefault("decision", "analyze")
                basic.setdefault("reason", "Requested performance analysis, but analyzer unavailable; returned basic execution")
                return basic
            try:
                result = performance_analyzer.analyze_query(query_executor, query, r, True, include_event_counts)
                if not result.get("success"):
                    raise RuntimeError(result.get("error") or "analysis_failed")
                result.setdefault("decision", "analyze")
                result.setdefault("reason", "Performance analysis selected to obtain FE/SE breakdown and average timings")
                return result
            except Exception as _e:
                q_upper = (query or "").strip().upper()
                if q_upper.startswith("EVALUATE") and "TOPN(" not in q_upper:
                    try:
                        body = (query.strip()[len("EVALUATE"):]).strip()
                        query = f"EVALUATE TOPN({lim}, {body})"
                        notes.append(f"Applied TOPN({lim}) to EVALUATE query for safety (analyze fallback)")
                    except Exception:
                        pass
                exec_result = query_executor.validate_and_execute_dax(query, lim, bypass_cache=bypass_cache)
                exec_result.setdefault("notes", []).append(
                    f"Analyzer error; returned preview instead: {str(_e)}"
                )
                exec_result.setdefault("decision", "analyze_fallback_preview")
                exec_result.setdefault("reason", "XMLA/xEvents unavailable or errored; provided successful preview with safe TOPN")
                if verbose and notes:
                    exec_result.setdefault("notes", []).extend(notes)
                return exec_result
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
            exec_result.setdefault("analysis", analysis)
        return exec_result
