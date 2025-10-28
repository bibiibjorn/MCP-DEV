"""Base orchestrator class with common functionality."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseOrchestrator:
    """Base class for all orchestrators with common utilities."""
    
    def __init__(self, config):
        self.config = config
    
    def _get_preview_limit(self, max_rows: Optional[int]) -> int:
        """Get preview row limit from config or parameter."""
        if isinstance(max_rows, int) and max_rows > 0:
            return max_rows
        return (
            self.config.get("query.max_rows_preview", 1000)
            or self.config.get("performance.default_top_n", 1000)
            or 1000
        )
    
    def _get_default_perf_runs(self, runs: Optional[int]) -> int:
        """Get default performance analysis runs."""
        if isinstance(runs, int) and runs > 0:
            return runs
        return 3
    
    def _check_connection(self, connection_state) -> Optional[Dict[str, Any]]:
        """Check if connected, return error dict if not."""
        if not connection_state.is_connected():
            from core.validation.error_handler import ErrorHandler
            return ErrorHandler.handle_not_connected()
        return None
    
    def _check_manager(self, connection_state, manager_name: str) -> Optional[Dict[str, Any]]:
        """Check if manager exists, return error dict if not."""
        if not getattr(connection_state, manager_name, None):
            from core.validation.error_handler import ErrorHandler
            return ErrorHandler.handle_manager_unavailable(manager_name)
        return None
