"""
Enhanced error handler with categorization, retry logic, and telemetry.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger("mcp_powerbi_finvision.enhanced_error_handler")


class ErrorCategory:
    """Error categories for better handling and reporting."""
    CONNECTION = "connection"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    RATE_LIMIT = "rate_limit"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    SYNTAX = "syntax"
    RESOURCE = "resource"
    UNEXPECTED = "unexpected"


class EnhancedErrorHandler:
    """
    Enhanced error handling with categorization, retry suggestions, and telemetry.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize error handler."""
        self.config = config or {}
        
        # Error telemetry
        self.error_counts = defaultdict(int)
        self.error_history = deque(maxlen=1000)
        self.last_errors_by_tool = {}
        
        # Retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delays = self.config.get('retry_delays', [1, 2, 5])  # seconds
        
        logger.info("Enhanced error handler initialized")
    
    def categorize_error(self, error: Exception, context: Optional[str] = None) -> str:
        """
        Categorize an error based on type and message.
        
        Returns:
            Error category string
        """
        error_msg = str(error).lower()
        error_type = type(error).__name__
        
        # Connection errors
        if any(x in error_msg for x in ['connection', 'connect', 'timeout', 'network']):
            return ErrorCategory.CONNECTION
        
        # Timeout errors
        if any(x in error_msg for x in ['timeout', 'time out', 'timed out']):
            return ErrorCategory.TIMEOUT
        
        # Validation errors
        if any(x in error_type.lower() for x in ['validation', 'value']):
            return ErrorCategory.VALIDATION
        
        # Rate limit
        if 'rate limit' in error_msg or 'too many' in error_msg:
            return ErrorCategory.RATE_LIMIT
        
        # Permission/auth errors
        if any(x in error_msg for x in ['permission', 'denied', 'unauthorized', 'forbidden']):
            return ErrorCategory.PERMISSION
        
        # Not found errors
        if any(x in error_msg for x in ['not found', 'does not exist', 'missing']):
            return ErrorCategory.NOT_FOUND
        
        # Syntax errors
        if any(x in error_msg for x in ['syntax', 'parse', 'invalid expression']):
            return ErrorCategory.SYNTAX
        
        # Resource errors
        if any(x in error_msg for x in ['memory', 'resource', 'quota']):
            return ErrorCategory.RESOURCE
        
        # Default
        return ErrorCategory.UNEXPECTED
    
    def should_retry(self, error: Exception, attempt: int, tool_name: str) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (0-indexed)
            tool_name: Name of the tool that failed
        
        Returns:
            True if should retry
        """
        if attempt >= self.max_retries:
            return False
        
        category = self.categorize_error(error)
        
        # Retryable categories
        retryable = {
            ErrorCategory.CONNECTION,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RESOURCE
        }
        
        # Don't retry validation or syntax errors
        non_retryable = {
            ErrorCategory.VALIDATION,
            ErrorCategory.SYNTAX,
            ErrorCategory.NOT_FOUND,
            ErrorCategory.PERMISSION
        }
        
        if category in non_retryable:
            return False
        
        if category in retryable:
            return True
        
        # For unexpected errors, check if transient
        if category == ErrorCategory.UNEXPECTED:
            # Retry if it looks transient
            transient_keywords = ['temporary', 'transient', 'busy', 'locked']
            return any(kw in str(error).lower() for kw in transient_keywords)
        
        return False
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Get delay before retry.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        if attempt < len(self.retry_delays):
            return self.retry_delays[attempt]
        
        # Exponential backoff for attempts beyond configured delays
        return min(60, 2 ** attempt)
    
    def format_error_response(
        self,
        error: Exception,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format error into standardized response.
        
        Args:
            error: The exception
            tool_name: Name of the tool
            context: Optional context dict
        
        Returns:
            Standardized error response dict
        """
        category = self.categorize_error(error, tool_name)
        
        # Record telemetry
        self.error_counts[category] += 1
        self.error_history.append({
            'tool': tool_name,
            'category': category,
            'error': str(error),
            'timestamp': time.time()
        })
        self.last_errors_by_tool[tool_name] = {
            'error': str(error),
            'category': category,
            'timestamp': time.time()
        }
        
        response = {
            'success': False,
            'error': str(error),
            'error_type': category,
            'tool': tool_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add suggestions based on category
        suggestions = self._get_error_suggestions(category, error, tool_name)
        if suggestions:
            response['suggestions'] = suggestions
        
        # Add context if provided
        if context:
            response['context'] = context
        
        return response
    
    def _get_error_suggestions(
        self,
        category: str,
        error: Exception,
        tool_name: str
    ) -> List[str]:
        """Get helpful suggestions based on error category."""
        suggestions = []
        
        if category == ErrorCategory.CONNECTION:
            suggestions.extend([
                "Ensure Power BI Desktop is running and a model is open",
                "Check if the instance is still available with detect_powerbi_desktop",
                "Try reconnecting with connect_to_powerbi"
            ])
        
        elif category == ErrorCategory.TIMEOUT:
            suggestions.extend([
                "Reduce query complexity or row limits",
                "Check if Power BI Desktop is responsive",
                f"Consider increasing timeout for {tool_name} in config"
            ])
        
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Check input parameters for correct format",
                "Verify table/column/measure names exist in the model",
                "Use search_objects to find correct identifiers"
            ])
        
        elif category == ErrorCategory.RATE_LIMIT:
            suggestions.extend([
                "Wait a moment before retrying",
                "Reduce request frequency",
                "Use batch operations where available"
            ])
        
        elif category == ErrorCategory.PERMISSION:
            suggestions.extend([
                "Check if model allows external connections",
                "Verify no admin restrictions on XMLA endpoints",
                "Ensure Power BI Desktop is not in restricted mode"
            ])
        
        elif category == ErrorCategory.NOT_FOUND:
            suggestions.extend([
                "Verify the object name is correct (case-sensitive)",
                "Use list_tables/list_columns/list_measures to find available objects",
                "Check if object is hidden or in a different table"
            ])
        
        elif category == ErrorCategory.SYNTAX:
            suggestions.extend([
                "Validate DAX syntax with validate_dax_query first",
                "Check for unbalanced brackets or quotes",
                "Verify function names and parameter order"
            ])
        
        elif category == ErrorCategory.RESOURCE:
            suggestions.extend([
                "Reduce query complexity or result set size",
                "Clear cache with flush_query_cache",
                "Close unused Power BI Desktop instances"
            ])
        
        return suggestions
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics and trends."""
        now = time.time()
        one_hour_ago = now - 3600
        
        # Recent errors (last hour)
        recent_errors = [e for e in self.error_history if e['timestamp'] > one_hour_ago]
        
        # Error rate
        total_errors = len(self.error_history)
        recent_error_count = len(recent_errors)
        
        # Top failing tools
        tool_failures = defaultdict(int)
        for e in recent_errors:
            tool_failures[e['tool']] += 1
        top_failing_tools = sorted(
            tool_failures.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_errors': total_errors,
            'recent_errors_1h': recent_error_count,
            'error_rate_per_hour': recent_error_count,
            'errors_by_category': dict(self.error_counts),
            'top_failing_tools': dict(top_failing_tools),
            'last_errors_by_tool': {
                tool: {
                    'error': info['error'],
                    'category': info['category'],
                    'timestamp': datetime.fromtimestamp(info['timestamp']).isoformat()
                }
                for tool, info in list(self.last_errors_by_tool.items())[:10]
            }
        }
    
    def clear_stats(self):
        """Clear error statistics."""
        self.error_counts.clear()
        self.error_history.clear()
        self.last_errors_by_tool.clear()
        logger.info("Error statistics cleared")


# Convenience function for quick error responses
def create_error_response(
    error: Exception,
    tool_name: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    handler = EnhancedErrorHandler()
    return handler.format_error_response(error, tool_name, context)
