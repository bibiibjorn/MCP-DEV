"""
Performance monitoring utilities for tracking operation execution times.

Provides decorators and utilities for monitoring slow operations and
collecting performance metrics.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Any, Callable, Deque, Dict, Optional

logger = logging.getLogger("mcp_powerbi_finvision.performance")

# Performance metrics storage
_performance_metrics: Dict[str, Dict[str, Any]] = defaultdict(
    lambda: {
        "call_count": 0,
        "total_time": 0.0,
        "min_time": float("inf"),
        "max_time": 0.0,
        "recent_times": deque(maxlen=100),  # Last 100 executions
    }
)

# Slow operation threshold (seconds)
SLOW_OPERATION_THRESHOLD = 1.0


def monitor_performance(
    operation_name: Optional[str] = None,
    threshold: float = SLOW_OPERATION_THRESHOLD,
    log_all: bool = False,
) -> Callable:
    """
    Decorator to monitor function performance.

    Args:
        operation_name: Custom name for the operation (defaults to function name)
        threshold: Time threshold in seconds for logging warnings
        log_all: If True, log all executions, not just slow ones

    Example:
        @monitor_performance("query_execution", threshold=2.0)
        async def run_query(query: str) -> Dict[str, Any]:
            # implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    _record_performance(op_name, duration, threshold, log_all)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    _record_performance(op_name, duration, threshold, log_all)

            return sync_wrapper

    return decorator


def _record_performance(
    operation_name: str, duration: float, threshold: float, log_all: bool
) -> None:
    """Record performance metrics for an operation."""
    metrics = _performance_metrics[operation_name]

    # Update metrics
    metrics["call_count"] += 1
    metrics["total_time"] += duration
    metrics["min_time"] = min(metrics["min_time"], duration)
    metrics["max_time"] = max(metrics["max_time"], duration)
    metrics["recent_times"].append(duration)

    # Log if needed
    if log_all or duration >= threshold:
        level = logging.WARNING if duration >= threshold else logging.DEBUG
        logger.log(
            level,
            f"{operation_name} took {duration:.3f}s "
            f"(avg: {get_average_time(operation_name):.3f}s, "
            f"calls: {metrics['call_count']})",
        )


def get_performance_metrics(operation_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get performance metrics for operations.

    Args:
        operation_name: Specific operation name, or None for all operations

    Returns:
        Dictionary of performance metrics
    """
    if operation_name:
        if operation_name not in _performance_metrics:
            return {"error": f"No metrics found for {operation_name}"}

        metrics = _performance_metrics[operation_name]
        return {
            "operation": operation_name,
            "call_count": metrics["call_count"],
            "total_time": round(metrics["total_time"], 3),
            "avg_time": round(get_average_time(operation_name), 3),
            "min_time": round(metrics["min_time"], 3),
            "max_time": round(metrics["max_time"], 3),
            "recent_avg": round(_calculate_recent_average(metrics["recent_times"]), 3),
        }

    # Return all metrics
    return {
        name: {
            "call_count": metrics["call_count"],
            "total_time": round(metrics["total_time"], 3),
            "avg_time": round(get_average_time(name), 3),
            "min_time": round(metrics["min_time"], 3),
            "max_time": round(metrics["max_time"], 3),
            "recent_avg": round(_calculate_recent_average(metrics["recent_times"]), 3),
        }
        for name, metrics in _performance_metrics.items()
    }


def get_average_time(operation_name: str) -> float:
    """Calculate average execution time for an operation."""
    metrics = _performance_metrics.get(operation_name)
    if not metrics or metrics["call_count"] == 0:
        return 0.0
    return metrics["total_time"] / metrics["call_count"]


def _calculate_recent_average(recent_times: Deque[float]) -> float:
    """Calculate average of recent execution times."""
    if not recent_times:
        return 0.0
    return sum(recent_times) / len(recent_times)


def get_slow_operations(threshold: float = SLOW_OPERATION_THRESHOLD) -> Dict[str, Any]:
    """
    Get operations that are running slower than threshold on average.

    Args:
        threshold: Time threshold in seconds

    Returns:
        Dictionary of slow operations with their metrics
    """
    slow_ops = {}
    for name, metrics in _performance_metrics.items():
        avg_time = get_average_time(name)
        if avg_time >= threshold:
            slow_ops[name] = {
                "avg_time": round(avg_time, 3),
                "call_count": metrics["call_count"],
                "max_time": round(metrics["max_time"], 3),
            }

    return slow_ops


def reset_metrics(operation_name: Optional[str] = None) -> None:
    """
    Reset performance metrics.

    Args:
        operation_name: Specific operation to reset, or None to reset all
    """
    if operation_name:
        if operation_name in _performance_metrics:
            del _performance_metrics[operation_name]
            logger.info(f"Reset metrics for {operation_name}")
    else:
        _performance_metrics.clear()
        logger.info("Reset all performance metrics")


def get_performance_summary() -> Dict[str, Any]:
    """
    Get a summary of overall performance.

    Returns:
        Summary statistics across all operations
    """
    total_calls = sum(m["call_count"] for m in _performance_metrics.values())
    total_time = sum(m["total_time"] for m in _performance_metrics.values())

    if total_calls == 0:
        return {
            "total_operations": 0,
            "total_calls": 0,
            "total_time": 0.0,
            "slow_operations": [],
        }

    slow_ops = [
        {"operation": name, "avg_time": round(get_average_time(name), 3)}
        for name in _performance_metrics.keys()
        if get_average_time(name) >= SLOW_OPERATION_THRESHOLD
    ]

    return {
        "total_operations": len(_performance_metrics),
        "total_calls": total_calls,
        "total_time": round(total_time, 3),
        "avg_time_per_call": round(total_time / total_calls, 3),
        "slow_operations": sorted(slow_ops, key=lambda x: x["avg_time"], reverse=True),
    }
