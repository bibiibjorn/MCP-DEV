"""
Enhanced error handler with Desktop version context and known issue detection.
Replaces core/error_handler.py
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("mcp_powerbi_finvision.error_handler")


class DesktopVersionInfo:
    """Power BI Desktop version information."""
    
    def __init__(self, version: str = "Unknown", build: str = "Unknown", 
                 release_date: Optional[str] = None):
        self.version = version
        self.build = build
        self.release_date = release_date
    
    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'build': self.build,
            'release_date': self.release_date
        }


class KnownIssueDetector:
    """Detects known issues based on Desktop version and error patterns."""
    
    # Known problematic Desktop versions
    KNOWN_ISSUES = {
        'dmv_table_filter': {
            'description': 'Table-scoped DMV queries fail in some Desktop builds',
            'affected_versions': ['2.120.*', '2.121.*'],
            'workaround': 'Use client-side filtering or upgrade Desktop',
            'severity': 'medium'
        },
        'amo_connection': {
            'description': 'AMO tracing unavailable without proper .NET assemblies',
            'affected_versions': ['*'],
            'workaround': 'Install ADOMD/AMO DLLs in lib/dotnet/',
            'severity': 'low'
        },
        'tmschema_datasources': {
            'description': 'TMSCHEMA_DATA_SOURCES DMV unavailable in older Desktop',
            'affected_versions': ['2.11*', '2.12*'],
            'workaround': 'Use TOM fallback or upgrade Desktop',
            'severity': 'low'
        },
        'calculation_groups': {
            'description': 'Calculation groups not supported in older Desktop',
            'affected_versions': ['2.11*'],
            'workaround': 'Upgrade to Desktop 2.120+',
            'severity': 'high'
        }
    }
    
    @classmethod
    def check_for_known_issues(cls, version_info: DesktopVersionInfo, 
                                error_context: Optional[str] = None) -> list:
        """
        Check if error matches known issues.
        
        Args:
            version_info: Desktop version information
            error_context: Error message or context
        
        Returns:
            List of matching known issues
        """
        matches = []
        
        for issue_id, issue_info in cls.KNOWN_ISSUES.items():
            # Check version match
            if cls._version_matches(version_info.version, issue_info['affected_versions']):
                # Check error context if provided
                if error_context and issue_id in error_context.lower():
                    matches.append({
                        'issue_id': issue_id,
                        **issue_info
                    })
                elif not error_context:
                    # No context, return potential issues
                    matches.append({
                        'issue_id': issue_id,
                        **issue_info,
                        'potential': True
                    })
        
        return matches
    
    @classmethod
    def _version_matches(cls, version: str, patterns: list) -> bool:
        """Check if version matches any pattern."""
        import fnmatch
        for pattern in patterns:
            if pattern == '*' or fnmatch.fnmatch(version, pattern):
                return True
        return False


class EnhancedErrorHandler:
    """Enhanced error handler with rich context."""
    
    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager
        self.error_count = 0
        self.error_history = []
    
    def get_desktop_version(self) -> DesktopVersionInfo:
        """Retrieve Desktop version information from connection."""
        if not self.connection_manager:
            return DesktopVersionInfo()
        
        try:
            conn = self.connection_manager.get_connection()
            if not conn:
                return DesktopVersionInfo()
            
            # Try to get version from connection properties
            version = getattr(conn, 'Version', 'Unknown')
            
            # Parse version string (format: "major.minor.build.revision")
            if isinstance(version, str) and '.' in version:
                parts = version.split('.')
                version_str = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else version
                build_str = parts[2] if len(parts) >= 3 else "Unknown"
            else:
                version_str = str(version)
                build_str = "Unknown"
            
            return DesktopVersionInfo(
                version=version_str,
                build=build_str
            )
        except Exception as e:
            logger.debug(f"Could not retrieve Desktop version: {e}")
            return DesktopVersionInfo()
    
    def handle_dmv_failure(self, error: Exception, dmv_name: str) -> dict:
        """
        Handle DMV query failure with rich context.
        
        Args:
            error: The exception that occurred
            dmv_name: Name of the DMV that failed
        
        Returns:
            Detailed error response
        """
        self.error_count += 1
        version_info = self.get_desktop_version()
        error_msg = str(error)
        
        # Check for known issues
        known_issues = KnownIssueDetector.check_for_known_issues(
            version_info, 
            error_context=f"{dmv_name} {error_msg}"
        )
        
        response = {
            'success': False,
            'error': f"DMV query failed: {dmv_name}",
            'error_type': 'dmv_unavailable',
            'error_detail': error_msg,
            'context': {
                'dmv_name': dmv_name,
                'desktop_version': version_info.to_dict(),
                'timestamp': datetime.utcnow().isoformat(),
                'error_count': self.error_count
            }
        }
        
        if known_issues:
            response['known_issues'] = known_issues
            response['suggestions'] = [issue['workaround'] for issue in known_issues]
        else:
            response['suggestions'] = [
                f"Verify Power BI Desktop is running and model is loaded",
                f"Try upgrading to latest Desktop version",
                f"Check if {dmv_name} is supported in your Desktop version"
            ]
        
        # Log with context
        logger.warning(
            f"DMV failure: {dmv_name} | Desktop: {version_info.version} "
            f"Build: {version_info.build} | Error: {error_msg}"
        )
        
        # Record in history
        self.error_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'dmv_failure',
            'dmv': dmv_name,
            'version': version_info.version
        })
        
        return response
    
    def handle_amo_failure(self, error: Exception, operation: str) -> dict:
        """Handle AMO operation failure."""
        self.error_count += 1
        version_info = self.get_desktop_version()
        
        known_issues = KnownIssueDetector.check_for_known_issues(
            version_info,
            error_context="amo"
        )
        
        return {
            'success': False,
            'error': f"AMO operation failed: {operation}",
            'error_type': 'amo_unavailable',
            'error_detail': str(error),
            'context': {
                'operation': operation,
                'desktop_version': version_info.to_dict(),
                'amo_available': False
            },
            'suggestions': [
                'Check ADOMD.NET and AMO libraries in lib/dotnet/',
                'Verify pythonnet (clr) is properly configured',
                'Performance analysis limited without AMO tracing'
            ] + ([issue['workaround'] for issue in known_issues] if known_issues else [])
        }
    
    def handle_validation_error(self, field: str, value: Any, reason: str) -> dict:
        """Handle input validation error."""
        return {
            'success': False,
            'error': f"Validation failed for {field}",
            'error_type': 'validation_error',
            'error_detail': reason,
            'context': {
                'field': field,
                'value': str(value)[:100],  # Truncate for safety
                'timestamp': datetime.utcnow().isoformat()
            },
            'suggestions': [
                f"Check {field} format and constraints",
                'Refer to tool schema for valid inputs'
            ]
        }
    
    def handle_rate_limit(self, tool_name: str, wait_time: float) -> dict:
        """Handle rate limit exceeded."""
        return {
            'success': False,
            'error': 'Rate limit exceeded',
            'error_type': 'rate_limited',
            'context': {
                'tool': tool_name,
                'retry_after_seconds': round(wait_time, 2),
                'timestamp': datetime.utcnow().isoformat()
            },
            'suggestions': [
                f"Wait {wait_time:.1f} seconds before retrying",
                'Reduce request frequency',
                'Consider batching operations'
            ]
        }
    
    @staticmethod
    def handle_not_connected() -> dict:
        """Handle no connection error."""
        return {
            'success': False,
            'error': 'No Power BI Desktop instance is connected',
            'error_type': 'not_connected',
            'suggestions': [
                'Run "detect_powerbi_desktop" to find instances',
                'Run "connect_to_powerbi" with model_index',
                'Ensure Power BI Desktop is running with model loaded'
            ]
        }
    
    @staticmethod
    def handle_manager_unavailable(manager_name: str) -> dict:
        """Handle manager not initialized."""
        return {
            'success': False,
            'error': f'Required manager unavailable: {manager_name}',
            'error_type': 'manager_unavailable',
            'required_manager': manager_name,
            'suggestions': [
                'Ensure connection is established first',
                'Check manager initialization in logs',
                'Some managers require specific Desktop features'
            ]
        }
    
    @staticmethod
    def handle_unknown_tool(tool_name: str) -> dict:
        """Handle unknown tool."""
        return {
            'success': False,
            'error': f'Unknown tool: {tool_name}',
            'error_type': 'unknown_tool',
            'tool_name': tool_name,
            'suggestions': [
                'Run "list_tools" to see available tools',
                'Check tool name spelling',
                'Consult documentation for valid tool names'
            ]
        }
    
    @staticmethod
    def handle_unexpected_error(tool_name: str, error: Exception) -> dict:
        """Handle unexpected errors."""
        return {
            'success': False,
            'error': 'An unexpected error occurred',
            'error_type': 'unexpected_error',
            'tool_name': tool_name,
            'error_detail': str(error),
            'suggestions': [
                'Check logs with "get_recent_logs" for details',
                'Report issue if problem persists',
                'Try alternative approach if available'
            ]
        }
    
    def get_error_stats(self) -> dict:
        """Get error statistics."""
        return {
            'total_errors': self.error_count,
            'recent_errors': self.error_history[-10:],  # Last 10
            'error_types': self._count_error_types()
        }
    
    def _count_error_types(self) -> dict:
        """Count errors by type."""
        counts = {}
        for err in self.error_history:
            err_type = err.get('type', 'unknown')
            counts[err_type] = counts.get(err_type, 0) + 1
        return counts


# Singleton instance (backward compatibility with old error_handler.py)
_global_handler = EnhancedErrorHandler()

def handle_not_connected():
    return _global_handler.handle_not_connected()

def handle_manager_unavailable(manager_name: str):
    return _global_handler.handle_manager_unavailable(manager_name)

def handle_unknown_tool(tool_name: str):
    return _global_handler.handle_unknown_tool(tool_name)

def handle_unexpected_error(tool_name: str, error: Exception):
    return _global_handler.handle_unexpected_error(tool_name, error)


# Expose as ErrorHandler class for backward compatibility
class ErrorHandler:
    """Wrapper for backward compatibility."""
    
    @staticmethod
    def handle_not_connected():
        return handle_not_connected()
    
    @staticmethod
    def handle_manager_unavailable(manager_name: str):
        return handle_manager_unavailable(manager_name)
    
    @staticmethod
    def handle_unknown_tool(tool_name: str):
        return handle_unknown_tool(tool_name)
    
    @staticmethod
    def handle_unexpected_error(tool_name: str, error: Exception):
        return handle_unexpected_error(tool_name, error)
