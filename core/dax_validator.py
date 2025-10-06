"""
DAX Validation and Analysis - Enhanced

Advanced DAX syntax validation, complexity analysis, and optimization suggestions.
Based on tabular-mcp best practices.
"""

import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DaxValidator:
    """
    Advanced DAX validation with syntax checking, complexity analysis,
    and performance recommendations.
    """

    # Table expression patterns
    TABLE_FUNCTIONS = [
        'SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER', 'VALUES', 'ALL',
        'DISTINCT', 'UNION', 'INTERSECT', 'EXCEPT', 'CROSSJOIN', 'NATURALINNERJOIN',
        'NATURALLEFTOUTERJOIN', 'TOPN', 'SAMPLE', 'DATATABLE', 'SUBSTITUTEWITHINDEX',
        'GROUPBY', 'SUMMARIZECOLUMNS', 'TREATAS', 'CALCULATETABLE'
    ]

    @staticmethod
    def validate_identifier(identifier: str) -> bool:
        """
        Validate DAX identifier is safe.

        Args:
            identifier: Identifier to validate

        Returns:
            True if valid and safe
        """
        return (
            identifier and
            len(identifier.strip()) > 0 and
            len(identifier) <= 128 and
            '\0' not in identifier
        )

    @staticmethod
    def escape_identifier(identifier: str) -> str:
        """
        Escape DAX identifier for safe use.

        Args:
            identifier: Identifier to escape

        Returns:
            Escaped identifier wrapped in quotes
        """
        if not DaxValidator.validate_identifier(identifier):
            raise ValueError(f"Invalid identifier: {identifier}")
        return f"'{identifier.replace(chr(39), chr(39) + chr(39))}'"

    @staticmethod
    def check_balanced_delimiters(query: str, open_char: str, close_char: str, name: str) -> List[str]:
        """Check balanced delimiters (parentheses, brackets)."""
        errors = []
        balance = 0
        in_string = False
        string_delimiter = None

        for i, c in enumerate(query):
            if in_string:
                if c == string_delimiter:
                    if i + 1 < len(query) and query[i + 1] == string_delimiter:
                        continue  # Escaped quote
                    else:
                        in_string = False
                        string_delimiter = None
            else:
                if c in ('"', "'"):
                    in_string = True
                    string_delimiter = c
                elif c == open_char:
                    balance += 1
                elif c == close_char:
                    balance -= 1
                    if balance < 0:
                        errors.append(f"Unbalanced {name}: extra '{close_char}' at position {i}")
                        return errors

        if balance > 0:
            errors.append(f"Unbalanced {name}: {balance} '{open_char}' not closed")

        return errors

    @staticmethod
    def check_balanced_quotes(query: str) -> List[str]:
        """Check balanced quotes."""
        errors = []
        in_double_quote = False
        in_single_quote = False

        i = 0
        while i < len(query):
            c = query[i]

            if c == '"':
                if in_single_quote:
                    i += 1
                    continue
                # Check for escaped ""
                if i + 1 < len(query) and query[i + 1] == '"':
                    i += 2
                    continue
                else:
                    in_double_quote = not in_double_quote

            elif c == "'":
                if in_double_quote:
                    i += 1
                    continue
                in_single_quote = not in_single_quote

            i += 1

        if in_double_quote:
            errors.append("Unbalanced double quotes: string literal not closed")
        if in_single_quote:
            errors.append("Unbalanced single quotes: identifier not closed")

        return errors

    @staticmethod
    def validate_query_syntax(query: str) -> List[str]:
        """
        Validate basic DAX syntax.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not query or not query.strip():
            errors.append("Query cannot be empty")
            return errors

        # Check balanced delimiters
        errors.extend(DaxValidator.check_balanced_delimiters(query, '(', ')', 'parentheses'))
        errors.extend(DaxValidator.check_balanced_delimiters(query, '[', ']', 'brackets'))
        errors.extend(DaxValidator.check_balanced_quotes(query))

        return errors

    @staticmethod
    def is_table_expression(query: str) -> bool:
        """Determine if expression is table or scalar."""
        if not query:
            return False

        query = query.strip()

        # Table reference with quotes
        if query.startswith("'") and query.endswith("'"):
            return True

        # Check for table functions
        query_upper = query.upper()
        for func in DaxValidator.TABLE_FUNCTIONS:
            if query_upper.startswith(func):
                return True

        # Calculated table {  }
        if query.startswith('{') and query.endswith('}'):
            return True

        return False

    @staticmethod
    def analyze_complexity(expression: str) -> Dict[str, Any]:
        """
        Analyze DAX expression complexity.

        Returns:
            Complexity metrics and rating
        """
        if not expression:
            return {'complexity_score': 0, 'level': 'None'}

        # Count functions
        function_count = len(re.findall(r'\b[A-Z]+\s*\(', expression, re.IGNORECASE))

        # Count nesting level
        max_nesting = DaxValidator._count_max_nesting(expression)

        # Count specific patterns
        filter_count = len(re.findall(r'\bFILTER\b', expression, re.IGNORECASE))
        calculate_count = len(re.findall(r'\bCALCULATE\b', expression, re.IGNORECASE))

        # Calculate complexity score
        complexity_score = (function_count * 2) + (max_nesting * 3) + (filter_count * 4) + (calculate_count * 2)

        # Determine level
        if complexity_score <= 5:
            level = 'Low'
        elif complexity_score <= 15:
            level = 'Medium'
        elif complexity_score <= 30:
            level = 'High'
        else:
            level = 'Very High'

        return {
            'complexity_score': complexity_score,
            'level': level,
            'function_count': function_count,
            'max_nesting_level': max_nesting,
            'filter_count': filter_count,
            'calculate_count': calculate_count,
            'expression_length': len(expression)
        }

    @staticmethod
    def _count_max_nesting(expression: str) -> int:
        """Count maximum nesting level of parentheses."""
        max_level = 0
        current_level = 0
        in_string = False

        for c in expression:
            if c == '"' and not in_string:
                in_string = True
            elif c == '"' and in_string:
                in_string = False
            elif not in_string:
                if c == '(':
                    current_level += 1
                    max_level = max(max_level, current_level)
                elif c == ')':
                    current_level -= 1

        return max_level

    @staticmethod
    def analyze_patterns(expression: str) -> Tuple[List[str], List[str]]:
        """
        Analyze DAX for anti-patterns and provide recommendations.

        Returns:
            Tuple of (warnings, recommendations)
        """
        warnings = []
        recommendations = []

        if not expression:
            return warnings, recommendations

        expr_upper = expression.upper()

        # Check for anti-patterns
        if 'SUMX' in expr_upper and 'FILTER' in expr_upper:
            warnings.append("SUMX with FILTER detected - consider using CALCULATE for better performance")

        if re.search(r'CALCULATE\s*\(\s*CALCULATE', expression, re.IGNORECASE):
            warnings.append("Nested CALCULATE functions detected - may cause unexpected results")

        calculate_count = len(re.findall(r'\bCALCULATE\b', expression, re.IGNORECASE))
        if calculate_count > 3:
            warnings.append(f"High number of CALCULATE functions ({calculate_count}) - consider simplifying")

        # Recommendations
        if 'SUM' in expr_upper and 'CALCULATE' not in expr_upper:
            recommendations.append("Consider using CALCULATE with filters for more flexibility")

        if len(expression) > 500:
            recommendations.append("Long expression - consider breaking into multiple measures")

        if ('/' in expression or 'DIVIDE' in expr_upper) and 'FORMAT' not in expr_upper:
            recommendations.append("Consider using FORMAT function for better number presentation")

        return warnings, recommendations

    @staticmethod
    def generate_optimization_suggestions(query: str) -> List[str]:
        """Generate optimization suggestions for query."""
        suggestions = []

        query_upper = query.upper()

        if 'SUMX' in query_upper and 'FILTER' in query_upper:
            suggestions.append("Replace SUMX(FILTER(...)) with CALCULATE(SUM(...), Filter)")

        if len(re.findall(r'\bCALCULATE\b', query, re.IGNORECASE)) > 2:
            suggestions.append("Consolidate multiple CALCULATE functions to reduce complexity")

        if 'ALL(' in query_upper and 'CALCULATE' not in query_upper:
            suggestions.append("Using ALL() without CALCULATE may not provide expected results")

        if len(query) > 1000:
            suggestions.append("Break down large query into smaller, manageable parts")

        iterator_count = len(re.findall(r'\b(SUMX|AVERAGEX|COUNTX|MAXX|MINX)\b', query, re.IGNORECASE))
        if iterator_count > 2:
            suggestions.append("Multiple iterator functions detected - ensure they are necessary")

        return suggestions
