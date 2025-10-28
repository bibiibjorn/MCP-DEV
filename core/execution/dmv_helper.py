"""DMV and INFO.* query building and execution helpers."""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DmvHelper:
    """Helper for building and executing DMV/INFO.* queries."""

    @staticmethod
    def get_info_columns(function_name: str) -> List[str]:
        """Get expected columns for INFO.* functions."""
        column_map = {
            'MEASURES': ['Name', 'TableID', 'DataType', 'IsHidden', 'DisplayFolder', 'Expression'],
            'TABLES': ['Name', 'IsHidden', 'ModifiedTime', 'DataCategory'],
            'COLUMNS': ['Name', 'TableID', 'DataType', 'IsHidden', 'IsKey', 'Type'],
            'RELATIONSHIPS': ['FromTable', 'FromColumn', 'ToTable', 'ToColumn', 'IsActive', 'CrossFilterDirection', 'Cardinality']
        }
        return column_map.get(function_name, [])

    @staticmethod
    def escape_dax_string(text: str) -> str:
        """Escape single quotes in DAX strings."""
        return text.replace("'", "''") if text else text

    @staticmethod
    def analyze_dax_error(error_msg: str, dax_query: str) -> List[str]:
        """Analyze DAX error and provide suggestions."""
        suggestions: List[str] = []
        error_lower = (error_msg or '').lower()
        
        if "table" in error_lower and ("not found" in error_lower or "doesn't exist" in error_lower):
            suggestions.extend([
                "Verify table exists with list_tables",
                "Check case-sensitive spelling",
                "Try single quotes: 'TableName'"
            ])
        if "column" in error_lower and ("not found" in error_lower or "doesn't exist" in error_lower):
            suggestions.extend([
                "Verify column with describe_table",
                "Check case-sensitive spelling",
                "Try [Table][Column] syntax"
            ])
        if "syntax" in error_lower:
            suggestions.extend([
                "Ensure EVALUATE for table expressions",
                "Check balanced delimiters",
                "Verify function parameters"
            ])
        if "function" in error_lower:
            suggestions.extend([
                "Check function name spelling",
                "Verify parameter types/count"
            ])
        if "error" in error_lower and "measure" in error_lower:
            suggestions.extend([
                "Check for circular dependencies",
                "Test expressions individually"
            ])
        if not suggestions:
            suggestions.extend([
                "Check DAX syntax",
                "Verify references exist",
                "Simplify query to isolate issue"
            ])
        return suggestions

    @staticmethod
    def build_info_query(
        function_name: str,
        filter_expr: Optional[str] = None,
        exclude_columns: Optional[List[str]] = None,
        top_n: int = 100
    ) -> str:
        """Build INFO.* query with optional filtering and column exclusion."""
        inner = f"INFO.{function_name}()"
        
        # Apply TOPN limit
        if filter_expr:
            inner_limited = f"TOPN({top_n}, FILTER({inner}, {filter_expr}))"
        else:
            inner_limited = f"TOPN({top_n}, {inner})"
        
        query = f"EVALUATE {inner_limited}"
        
        # If excluding columns, try SELECTCOLUMNS projection
        if exclude_columns:
            cols = DmvHelper.get_info_columns(function_name)
            selected = [f'"{col}", [{col}]' for col in cols if col not in exclude_columns]
            if selected:
                inner_proj = f"SELECTCOLUMNS({inner}, {', '.join(selected)})"
                if filter_expr:
                    query = f"EVALUATE FILTER({inner_proj}, {filter_expr})"
                else:
                    query = f"EVALUATE {inner_proj}"
        
        return query

    @staticmethod
    def normalize_result_keys(rows: List[Dict[str, Any]]) -> None:
        """Normalize bracketed keys in result rows (in-place)."""
        for row in rows:
            for k in list(row.keys()):
                if k.startswith('[') and k.endswith(']'):
                    row[k[1:-1]] = row.pop(k)

    @staticmethod
    def needs_client_filter(result: Dict[str, Any], table_name: Optional[str]) -> bool:
        """Check if client-side filtering is needed."""
        try:
            if not table_name:
                return False
            if not isinstance(result, dict) or not result.get('success'):
                return True
            rows = result.get('rows') or []
            return len(rows) == 0
        except Exception:
            return True
