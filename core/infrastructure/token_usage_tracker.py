"""
Token Usage Tracker for MCP Server

Tracks token usage across all tool calls in the session.
Provides statistics and usage history for monitoring.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading


class TokenUsageEntry:
    """Single token usage entry"""

    def __init__(self, tool_name: str, tokens: int, max_tokens: int, percentage: str, level: str):
        self.tool_name = tool_name
        self.tokens = tokens
        self.max_tokens = max_tokens
        self.percentage = percentage
        self.level = level
        self.timestamp = time.time()
        self.datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'tool_name': self.tool_name,
            'tokens': self.tokens,
            'max_tokens': self.max_tokens,
            'percentage': self.percentage,
            'level': self.level,
            'timestamp': self.timestamp,
            'datetime': self.datetime_str
        }


class TokenUsageTracker:
    """
    Singleton tracker for token usage across the MCP server session.
    Thread-safe implementation.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._entries: List[TokenUsageEntry] = []
        self._session_start = time.time()
        self._total_tokens = 0
        self._tool_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def track(self, tool_name: str, tokens: int, max_tokens: int, percentage: str, level: str):
        """
        Track a token usage event.

        Args:
            tool_name: Name of the tool
            tokens: Number of tokens used
            max_tokens: Maximum tokens allowed
            percentage: Percentage string (e.g., "7.6%")
            level: Usage level (ok, warning, critical, over)
        """
        with self._lock:
            entry = TokenUsageEntry(tool_name, tokens, max_tokens, percentage, level)
            self._entries.append(entry)
            self._total_tokens += tokens

            # Update tool-specific stats
            if tool_name not in self._tool_stats:
                self._tool_stats[tool_name] = {
                    'count': 0,
                    'total_tokens': 0,
                    'min_tokens': tokens,
                    'max_tokens': tokens,
                    'levels': {'ok': 0, 'warning': 0, 'critical': 0, 'over': 0}
                }

            stats = self._tool_stats[tool_name]
            stats['count'] += 1
            stats['total_tokens'] += tokens
            stats['min_tokens'] = min(stats['min_tokens'], tokens)
            stats['max_tokens'] = max(stats['max_tokens'], tokens)
            stats['levels'][level] = stats['levels'].get(level, 0) + 1

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.

        Returns:
            Dictionary with session statistics
        """
        with self._lock:
            session_duration = time.time() - self._session_start

            # Calculate per-tool averages
            tool_breakdown = {}
            for tool_name, stats in self._tool_stats.items():
                avg_tokens = stats['total_tokens'] / stats['count'] if stats['count'] > 0 else 0
                tool_breakdown[tool_name] = {
                    'calls': stats['count'],
                    'total_tokens': stats['total_tokens'],
                    'avg_tokens': round(avg_tokens, 1),
                    'min_tokens': stats['min_tokens'],
                    'max_tokens': stats['max_tokens'],
                    'levels': stats['levels']
                }

            # Sort by total tokens used
            tool_breakdown = dict(sorted(
                tool_breakdown.items(),
                key=lambda x: x[1]['total_tokens'],
                reverse=True
            ))

            # Get recent history (last 10 calls)
            recent_history = [entry.to_dict() for entry in self._entries[-10:]]

            return {
                'session': {
                    'start_time': datetime.fromtimestamp(self._session_start).strftime("%Y-%m-%d %H:%M:%S"),
                    'duration_seconds': round(session_duration, 1),
                    'duration_minutes': round(session_duration / 60, 1),
                },
                'summary': {
                    'total_tokens_used': self._total_tokens,
                    'total_calls': len(self._entries),
                    'avg_tokens_per_call': round(self._total_tokens / len(self._entries), 1) if self._entries else 0,
                    'unique_tools_used': len(self._tool_stats)
                },
                'by_tool': tool_breakdown,
                'recent_history': recent_history
            }

    def get_resource_content(self) -> str:
        """
        Get formatted content for MCP resource display.

        Returns:
            Markdown-formatted string
        """
        stats = self.get_statistics()

        lines = [
            "# Token Usage Report",
            "",
            f"**Session Start**: {stats['session']['start_time']}",
            f"**Duration**: {stats['session']['duration_minutes']} minutes",
            "",
            "## Summary",
            "",
            f"- **Total Tokens Used**: {stats['summary']['total_tokens_used']:,}",
            f"- **Total Tool Calls**: {stats['summary']['total_calls']}",
            f"- **Average Tokens per Call**: {stats['summary']['avg_tokens_per_call']:,.1f}",
            f"- **Unique Tools Used**: {stats['summary']['unique_tools_used']}",
            "",
            "## Usage by Tool",
            ""
        ]

        # Add tool breakdown table
        if stats['by_tool']:
            lines.append("| Tool | Calls | Total Tokens | Avg | Min | Max | Warnings |")
            lines.append("|------|-------|--------------|-----|-----|-----|----------|")

            for tool_name, tool_stats in stats['by_tool'].items():
                warnings = tool_stats['levels'].get('warning', 0) + \
                          tool_stats['levels'].get('critical', 0) + \
                          tool_stats['levels'].get('over', 0)

                lines.append(
                    f"| {tool_name} | {tool_stats['calls']} | "
                    f"{tool_stats['total_tokens']:,} | "
                    f"{tool_stats['avg_tokens']:,.0f} | "
                    f"{tool_stats['min_tokens']:,} | "
                    f"{tool_stats['max_tokens']:,} | "
                    f"{warnings} |"
                )
        else:
            lines.append("*No tools called yet*")

        lines.append("")
        lines.append("## Recent History (Last 10 Calls)")
        lines.append("")

        if stats['recent_history']:
            lines.append("| Time | Tool | Tokens | Level |")
            lines.append("|------|------|--------|-------|")

            for entry in stats['recent_history']:
                level_emoji = {
                    'ok': '✓',
                    'warning': '⚠️',
                    'critical': '🔴',
                    'over': '🚫'
                }.get(entry['level'], '?')

                lines.append(
                    f"| {entry['datetime']} | {entry['tool_name']} | "
                    f"{entry['tokens']:,} | {level_emoji} {entry['level']} |"
                )
        else:
            lines.append("*No history yet*")

        return "\n".join(lines)

    def reset(self):
        """Reset all tracking data (for testing or new session)"""
        with self._lock:
            self._entries.clear()
            self._session_start = time.time()
            self._total_tokens = 0
            self._tool_stats.clear()


# Global singleton instance
_tracker = TokenUsageTracker()


def get_token_tracker() -> TokenUsageTracker:
    """Get the global token usage tracker instance"""
    return _tracker
