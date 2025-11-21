"""
Centralized limits manager for MCP-PowerBi-Finvision.

This module provides a single source of truth for all rate limits, token limits,
query limits, and other constraints across the entire server.

Benefits:
- Single location for all limit configuration
- Consistent limit enforcement across all modules
- Easy to adjust limits globally
- Clear visibility of all constraints
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger("mcp_powerbi_finvision.limits")


@dataclass
class QueryLimits:
    """Limits for query execution and data retrieval."""
    # INFO.* query limits (per-call defaults)
    default_info_limit: int = 100
    max_info_limit: int = 1000

    # Preview limits
    max_rows_preview: int = 1000
    preview_sample_size: int = 30

    # Query constraints
    max_dax_query_length: int = 50000
    max_query_timeout: int = 60
    default_top_n: int = 1000

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 200

    # Safety limits
    safety_max_rows: int = 10_000

    # Dependency analysis
    default_dependency_depth: int = 2
    max_dependency_depth: int = 5

    # Expression display
    max_expression_display_length: int = 500


@dataclass
class TokenLimits:
    """Limits for token usage and response sizes."""
    # Maximum tokens per tool response (increased from 15000 to 100000 to support DAX Intelligence full output)
    max_result_tokens: int = 100000

    # Estimated tokens per character (rough approximation)
    chars_per_token: int = 4

    # Warning thresholds
    warning_threshold_tokens: int = 80000  # 80% of max
    critical_threshold_tokens: int = 90000  # 90% of max

    # Description table page sizes (token-optimized)
    describe_table_columns_page_size: int = 20
    describe_table_measures_page_size: int = 20
    describe_table_relationships_page_size: int = 50

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        return len(text) // self.chars_per_token

    def is_at_warning(self, tokens: int) -> bool:
        """Check if token count is at warning threshold."""
        return tokens >= self.warning_threshold_tokens

    def is_at_critical(self, tokens: int) -> bool:
        """Check if token count is at critical threshold."""
        return tokens >= self.critical_threshold_tokens

    def is_over_limit(self, tokens: int) -> bool:
        """Check if token count exceeds maximum."""
        return tokens >= self.max_result_tokens


@dataclass
class RateLimits:
    """Rate limiting configuration."""
    enabled: bool = True
    profile: str = "balanced"

    # Global limits
    global_calls_per_second: float = 10.0
    global_burst: int = 20

    # Tool-specific limits (calls per second)
    tool_limits: Dict[str, float] = field(default_factory=lambda: {
        "run_dax": 5.0,
        "analyze_model_bpa": 1.0,
        "full_analysis": 0.5,
        "analyze_queries_batch": 2.0,
    })

    # Tool-specific burst sizes
    tool_bursts: Dict[str, int] = field(default_factory=lambda: {
        "run_dax": 10,
        "analyze_model_bpa": 3,
        "full_analysis": 2,
        "analyze_queries_batch": 5,
    })

    def get_tool_limit(self, tool_name: str) -> Optional[float]:
        """Get rate limit for specific tool."""
        return self.tool_limits.get(tool_name)

    def get_tool_burst(self, tool_name: str) -> Optional[int]:
        """Get burst limit for specific tool."""
        return self.tool_bursts.get(tool_name)


@dataclass
class TimeoutLimits:
    """Timeout configuration for all tools."""
    default_timeout: int = 60

    # Per-tool timeouts (seconds)
    tool_timeouts: Dict[str, int] = field(default_factory=lambda: {
        "list_tables": 5,
        "list_columns": 5,
        "list_measures": 5,
        "list_relationships": 10,
        "describe_table": 10,
        "preview_table_data": 15,
        "run_dax": 60,
        "analyze_model_bpa": 180,
        "full_analysis": 300,
        "analyze_queries_batch": 180,
        "export_tmdl": 60,
        "generate_documentation": 60,
    })

    def get_timeout(self, tool_name: str) -> int:
        """Get timeout for specific tool."""
        return self.tool_timeouts.get(tool_name, self.default_timeout)


@dataclass
class BpaLimits:
    """Limits for Best Practice Analyzer."""
    max_rules: int = 120
    severity_at_least: str = "WARNING"
    max_tables: int = 60
    max_seconds: int = 60
    per_rule_max_ms: int = 500
    max_columns_per_rule: int = 5000
    max_measures_per_rule: int = 1000
    max_relationships_per_rule: int = 1000
    adaptive_timeouts: bool = True
    parallel_rules: int = 4


@dataclass
class CacheLimits:
    """Cache configuration limits."""
    ttl_seconds: int = 300
    max_entries: int = 1000
    max_size_mb: int = 100
    eviction_policy: str = "lru"


class LimitsManager:
    """
    Centralized manager for all server limits.

    This is the single source of truth for rate limits, token limits,
    query limits, and all other constraints.

    Usage:
        limits = LimitsManager(config)

        # Get query limit
        top_n = limits.query.default_info_limit

        # Check token usage
        if limits.token.is_over_limit(estimated_tokens):
            # Truncate response

        # Get rate limit for tool
        rate = limits.rate.get_tool_limit("run_dax")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize limits manager from configuration.

        Args:
            config: Configuration dict (from ConfigManager)
        """
        self.config = config or {}

        # Initialize all limit categories
        self.query = self._init_query_limits()
        self.token = self._init_token_limits()
        self.rate = self._init_rate_limits()
        self.timeout = self._init_timeout_limits()
        self.bpa = self._init_bpa_limits()
        self.cache = self._init_cache_limits()

        logger.info(f"LimitsManager initialized: query_limit={self.query.default_info_limit}, "
                   f"token_limit={self.token.max_result_tokens}, "
                   f"rate={self.rate.global_calls_per_second}/s")

    def _init_query_limits(self) -> QueryLimits:
        """Initialize query limits from config."""
        return QueryLimits(
            default_info_limit=self._get_config("query.default_info_limit", 100),
            max_info_limit=self._get_config("query.max_info_limit", 1000),
            max_rows_preview=self._get_config("query.max_rows_preview", 1000),
            preview_sample_size=self._get_config("query.preview_sample_size", 30),
            max_dax_query_length=self._get_config("query.max_dax_query_length", 50000),
            max_query_timeout=self._get_config("performance.max_query_timeout", 60),
            default_top_n=self._get_config("performance.default_top_n", 1000),
            default_page_size=self._get_config("query.default_page_size", 20),
            max_page_size=self._get_config("query.max_page_size", 200),
            safety_max_rows=10_000,
            default_dependency_depth=self._get_config("query.default_dependency_depth", 2),
            max_dependency_depth=self._get_config("query.max_dependency_depth", 5),
            max_expression_display_length=self._get_config("query.max_expression_display_length", 500),
        )

    def _init_token_limits(self) -> TokenLimits:
        """Initialize token limits from config."""
        defaults = self._get_config("query.describe_table_defaults", {})
        return TokenLimits(
            max_result_tokens=self._get_config("query.max_result_tokens", 100000),
            chars_per_token=4,
            warning_threshold_tokens=80000,
            critical_threshold_tokens=90000,
            describe_table_columns_page_size=defaults.get("columns_page_size", 20),
            describe_table_measures_page_size=defaults.get("measures_page_size", 20),
            describe_table_relationships_page_size=defaults.get("relationships_page_size", 50),
        )

    def _init_rate_limits(self) -> RateLimits:
        """Initialize rate limits from config."""
        return RateLimits(
            enabled=self._get_config("rate_limiting.enabled", True),
            profile=self._get_config("rate_limiting.profile", "balanced"),
            global_calls_per_second=float(self._get_config("rate_limiting.global_calls_per_second", 10)),
            global_burst=int(self._get_config("rate_limiting.global_burst", 20)),
            tool_limits=self._get_config("rate_limiting.tool_limits", {}),
            tool_bursts=self._get_config("rate_limiting.tool_bursts", {}),
        )

    def _init_timeout_limits(self) -> TimeoutLimits:
        """Initialize timeout limits from config."""
        return TimeoutLimits(
            default_timeout=self._get_config("server.timeout_seconds", 60),
            tool_timeouts=self._get_config("tool_timeouts", {}),
        )

    def _init_bpa_limits(self) -> BpaLimits:
        """Initialize BPA limits from config."""
        return BpaLimits(
            max_rules=self._get_config("bpa.max_rules", 120),
            severity_at_least=self._get_config("bpa.severity_at_least", "WARNING"),
            max_tables=self._get_config("bpa.max_tables", 60),
            max_seconds=self._get_config("bpa.max_seconds", 60),
            per_rule_max_ms=self._get_config("bpa.per_rule_max_ms", 500),
            max_columns_per_rule=self._get_config("bpa.max_columns_per_rule", 5000),
            max_measures_per_rule=self._get_config("bpa.max_measures_per_rule", 1000),
            max_relationships_per_rule=self._get_config("bpa.max_relationships_per_rule", 1000),
            adaptive_timeouts=self._get_config("bpa.adaptive_timeouts", True),
            parallel_rules=self._get_config("bpa.parallel_rules", 4),
        )

    def _init_cache_limits(self) -> CacheLimits:
        """Initialize cache limits from config."""
        return CacheLimits(
            ttl_seconds=self._get_config("performance.cache_ttl_seconds", 300),
            max_entries=self._get_config("performance.cache_max_entries", 1000),
            max_size_mb=self._get_config("performance.cache_max_size_mb", 100),
            eviction_policy=self._get_config("performance.cache_eviction_policy", "lru"),
        )

    def _get_config(self, key: str, default: Any) -> Any:
        """Get configuration value with dot notation support."""
        if not self.config:
            return default

        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all configured limits."""
        return {
            "query": {
                "default_info_limit": self.query.default_info_limit,
                "max_info_limit": self.query.max_info_limit,
                "max_rows_preview": self.query.max_rows_preview,
                "default_top_n": self.query.default_top_n,
            },
            "token": {
                "max_result_tokens": self.token.max_result_tokens,
                "warning_threshold": self.token.warning_threshold_tokens,
                "critical_threshold": self.token.critical_threshold_tokens,
            },
            "rate": {
                "enabled": self.rate.enabled,
                "profile": self.rate.profile,
                "global_calls_per_second": self.rate.global_calls_per_second,
                "global_burst": self.rate.global_burst,
                "tool_limits": self.rate.tool_limits,
            },
            "timeout": {
                "default": self.timeout.default_timeout,
                "tool_count": len(self.timeout.tool_timeouts),
            },
            "bpa": {
                "max_rules": self.bpa.max_rules,
                "max_tables": self.bpa.max_tables,
                "max_seconds": self.bpa.max_seconds,
            },
            "cache": {
                "ttl_seconds": self.cache.ttl_seconds,
                "max_entries": self.cache.max_entries,
                "max_size_mb": self.cache.max_size_mb,
            }
        }


# Global singleton (initialized by server on startup)
_limits_manager: Optional[LimitsManager] = None


def init_limits_manager(config: Dict[str, Any]) -> LimitsManager:
    """Initialize the global limits manager."""
    global _limits_manager
    _limits_manager = LimitsManager(config)
    return _limits_manager


def get_limits() -> LimitsManager:
    """Get the global limits manager instance."""
    if _limits_manager is None:
        raise RuntimeError("LimitsManager not initialized. Call init_limits_manager() first.")
    return _limits_manager
