"""
Advanced DAX Validator with Enhanced Syntax Checking and Complexity Analysis
Based on Tabular MCP's comprehensive validation approach
"""

import re
from typing import List, Dict, Any, Tuple


class AdvancedDAXValidator:
    """
    Advanced DAX validator with balanced delimiter detection, complexity metrics,
    and optimization suggestions similar to Tabular MCP
    """

    def __init__(self):
        self.table_expression_patterns = [
            "SELECTCOLUMNS", "ADDCOLUMNS", "SUMMARIZE", "FILTER", "VALUES", "ALL",
            "DISTINCT", "UNION", "INTERSECT", "EXCEPT", "CROSSJOIN", "NATURALINNERJOIN",
            "NATURALLEFTOUTERJOIN", "TOPN", "SAMPLE", "DATATABLE", "SUBSTITUTEWITHINDEX",
            "GROUPBY", "SUMMARIZECOLUMNS", "TREATAS", "CALCULATETABLE"
        ]

    def validate_dax_syntax(self, dax_expression: str, include_recommendations: bool = True) -> Dict[str, Any]:
        """
        Validate DAX syntax with enhanced error analysis

        Args:
            dax_expression: DAX expression to validate
            include_recommendations: Include performance and best practice recommendations

        Returns:
            Validation result with errors, warnings, recommendations, and complexity metrics
        """
        if not dax_expression or not dax_expression.strip():
            return {
                'expression': '',
                'is_valid': False,
                'syntax_errors': ['DAX expression cannot be empty'],
                'warnings': [],
                'recommendations': [],
                'complexity_metrics': {'complexity_score': 0, 'level': 'None'}
            }

        syntax_errors = []
        warnings = []
        recommendations = []

        # Check balanced delimiters
        self._check_balanced_delimiters(dax_expression, '(', ')', 'parentheses', syntax_errors)
        self._check_balanced_delimiters(dax_expression, '[', ']', 'brackets', syntax_errors)
        self._check_balanced_quotes(dax_expression, syntax_errors)

        # Check for common DAX patterns and issues
        if include_recommendations:
            self._analyze_dax_patterns(dax_expression, warnings, recommendations)

        # Calculate complexity metrics
        complexity_metrics = self._calculate_dax_complexity(dax_expression)

        return {
            'expression': dax_expression.strip(),
            'is_valid': len(syntax_errors) == 0,
            'syntax_errors': syntax_errors,
            'warnings': warnings,
            'recommendations': recommendations if include_recommendations else [],
            'complexity_metrics': complexity_metrics
        }

    def validate_complete_dax_query(self, query: str) -> Dict[str, Any]:
        """
        Validates the structure of a complete DAX query according to proper syntax rules

        Args:
            query: The complete DAX query to validate

        Returns:
            Validation result
        """
        errors = []

        if not query or not query.strip():
            errors.append("Query cannot be empty")
            return {'is_valid': False, 'errors': errors}

        normalized_query = self._normalize_dax_query(query)

        if "EVALUATE" not in normalized_query.upper():
            errors.append("DAX query must contain at least one EVALUATE statement")

        if "DEFINE" in normalized_query.upper():
            define_pos = normalized_query.upper().find("DEFINE")
            evaluate_pos = normalized_query.upper().find("EVALUATE")

            if evaluate_pos != -1 and define_pos > evaluate_pos:
                errors.append("DEFINE statement must come before any EVALUATE statement")

            define_matches = re.findall(r'\bDEFINE\b', normalized_query, re.IGNORECASE)
            if len(define_matches) > 1:
                errors.append("Only one DEFINE block is allowed in a DAX query")

            # Check DEFINE block content
            define_content_match = re.search(
                r'\bDEFINE\b\s*(?:MEASURE|VAR|TABLE|COLUMN)\s+',
                normalized_query,
                re.IGNORECASE | re.DOTALL
            )

            if not define_content_match:
                errors.append("DEFINE block must contain at least one definition (MEASURE, VAR, TABLE, or COLUMN)")

        # Check balanced delimiters
        self._check_balanced_delimiters(normalized_query, '(', ')', 'parentheses', errors)
        self._check_balanced_delimiters(normalized_query, '[', ']', 'brackets', errors)
        self._check_balanced_quotes(normalized_query, errors)

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'normalized_query': normalized_query
        }

    def analyze_query_structure(self, query: str) -> Dict[str, Any]:
        """
        Analyze the structure of a DAX query

        Args:
            query: DAX query to analyze

        Returns:
            Structure analysis results
        """
        if not query:
            return {}

        has_define = 'DEFINE' in query.upper()
        has_evaluate = 'EVALUATE' in query.upper()
        measure_count = len(re.findall(r'\bMEASURE\b', query, re.IGNORECASE))
        table_count = len(re.findall(r'\bTABLE\b', query, re.IGNORECASE))

        return {
            'has_define_block': has_define,
            'has_evaluate_statement': has_evaluate,
            'measure_definitions': measure_count,
            'table_definitions': table_count,
            'query_type': 'Complex Query' if has_define else ('Table Query' if has_evaluate else 'Expression'),
            'estimated_complexity': (measure_count * 2) + (table_count * 3) + (5 if has_define else 0)
        }

    def generate_optimization_suggestions(self, query: str, complexity_analysis: Dict = None) -> List[str]:
        """
        Generate optimization suggestions for a DAX query

        Args:
            query: DAX query to analyze
            complexity_analysis: Optional pre-computed complexity analysis

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Anti-pattern: SUMX with FILTER
        if 'SUMX' in query.upper() and 'FILTER' in query.upper():
            suggestions.append("Replace SUMX(FILTER(...)) with CALCULATE(SUM(...), Filter) for better performance")

        # Multiple CALCULATE functions
        calculate_count = len(re.findall(r'\bCALCULATE\b', query, re.IGNORECASE))
        if calculate_count > 2:
            suggestions.append("Consider consolidating multiple CALCULATE functions to reduce complexity")

        # ALL without CALCULATE
        if 'ALL(' in query.upper() and 'CALCULATE' not in query.upper():
            suggestions.append("Using ALL() without CALCULATE may not provide expected results - consider wrapping in CALCULATE")

        # Large query
        if len(query) > 1000:
            suggestions.append("Consider breaking down this large query into smaller, more manageable parts")

        # Multiple iterator functions
        iterator_functions = len(re.findall(r'\b(SUMX|AVERAGEX|COUNTX|MAXX|MINX)\b', query, re.IGNORECASE))
        if iterator_functions > 2:
            suggestions.append("Multiple iterator functions detected - ensure they are necessary and consider alternatives")

        # Nested CALCULATE
        if re.search(r'CALCULATE\s*\(\s*CALCULATE', query, re.IGNORECASE):
            suggestions.append("Nested CALCULATE functions detected - this may cause unexpected results")

        return suggestions

    def is_table_expression(self, query: str) -> bool:
        """
        Determines if a DAX expression is a table expression or a scalar expression

        Args:
            query: The DAX expression to analyze

        Returns:
            True if the expression is likely a table expression, false if it's a scalar expression
        """
        if not query or not query.strip():
            return False

        query = query.strip()

        # Check for table reference patterns
        if query.startswith("'") and query.endswith("'"):
            return True

        # Check for common table functions
        for pattern in self.table_expression_patterns:
            if query.upper().startswith(pattern):
                return True

        # Check for calculated table patterns like { ... }
        if query.startswith("{") and query.endswith("}"):
            return True

        return False

    # Private helper methods

    def _check_balanced_delimiters(self, query: str, open_char: str, close_char: str,
                                   delimiter_name: str, errors: List[str]) -> None:
        """
        Checks if delimiters like parentheses and brackets are properly balanced
        Skips delimiters found within string literals
        """
        balance = 0
        in_string = False
        string_delimiter = None

        i = 0
        while i < len(query):
            c = query[i]

            if in_string:
                if c == string_delimiter:
                    # Check for escaped delimiter
                    if i + 1 < len(query) and query[i + 1] == string_delimiter:
                        i += 1  # Skip escaped delimiter
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
                        errors.append(f"DAX query has unbalanced {delimiter_name}: extra '{close_char}' found")
                        return

            i += 1

        if balance > 0:
            errors.append(f"DAX query has unbalanced {delimiter_name}: {balance} '{open_char}' not closed")

    def _check_balanced_quotes(self, query: str, errors: List[str]) -> None:
        """
        Checks if string delimiters (quotes) are properly balanced
        DAX uses " for string literals and ' for table/column names
        """
        in_double_quote_string = False
        in_single_quote_identifier = False

        i = 0
        while i < len(query):
            c = query[i]

            if c == '"':
                if not in_single_quote_identifier:
                    # Check for escaped quote
                    if i + 1 < len(query) and query[i + 1] == '"':
                        i += 1  # Skip escaped quote
                    else:
                        in_double_quote_string = not in_double_quote_string
            elif c == "'":
                if not in_double_quote_string:
                    in_single_quote_identifier = not in_single_quote_identifier

            i += 1

        if in_double_quote_string:
            errors.append("DAX query has unbalanced double quotes: a string literal is not properly closed")
        if in_single_quote_identifier:
            errors.append("DAX query has unbalanced single quotes: a table/column identifier might not be properly closed")

    def _normalize_dax_query(self, query: str) -> str:
        """
        Normalizes a DAX query by standardizing whitespace and line endings
        """
        normalized = re.sub(r'\r\n?|\n', '\n', query)
        normalized = self._normalize_whitespace_preserving_strings(normalized)
        return normalized.strip()

    def _normalize_whitespace_preserving_strings(self, input_str: str) -> str:
        """
        Helper to normalize whitespace while preserving strings
        Collapses multiple whitespace characters into a single space outside of strings
        """
        result = []
        in_string = False
        string_delimiter = '"'
        last_char_was_whitespace = False

        i = 0
        while i < len(input_str):
            c = input_str[i]

            if not in_string and c in ('"', "'"):
                # Check for single quote patterns (skip if double single quote)
                if c == "'" and i + 1 < len(input_str) and input_str[i + 1] == "'":
                    pass  # Skip this check for doubled single quotes

                if c == '"':
                    in_string = True
                    string_delimiter = c
                    result.append(c)
                    last_char_was_whitespace = False
                    i += 1
                    continue
            elif in_string and c == string_delimiter:
                # Check for escaped delimiter
                if c == '"' and i + 1 < len(input_str) and input_str[i + 1] == '"':
                    result.append(c)
                    result.append(input_str[i + 1])
                    i += 2
                    last_char_was_whitespace = False
                    continue
                in_string = False
                result.append(c)
                last_char_was_whitespace = False
                i += 1
                continue

            if in_string:
                result.append(c)
                last_char_was_whitespace = False
            else:
                if c.isspace():
                    if not last_char_was_whitespace:
                        result.append(' ')
                        last_char_was_whitespace = True
                else:
                    result.append(c)
                    last_char_was_whitespace = False

            i += 1

        return ''.join(result)

    def _analyze_dax_patterns(self, expression: str, warnings: List[str], recommendations: List[str]) -> None:
        """
        Analyze DAX patterns for common anti-patterns and provide recommendations
        """
        # Check for common anti-patterns
        if 'SUMX' in expression.upper() and 'FILTER' in expression.upper():
            warnings.append("SUMX with FILTER detected - consider using CALCULATE for better performance")

        if re.search(r'CALCULATE\s*\(\s*CALCULATE', expression, re.IGNORECASE):
            warnings.append("Nested CALCULATE functions detected - this may cause unexpected results")

        calculate_count = len(re.findall(r'\bCALCULATE\b', expression, re.IGNORECASE))
        if calculate_count > 3:
            warnings.append(f"High number of CALCULATE functions ({calculate_count}) - consider simplifying the expression")

        # Recommendations
        if 'SUM' in expression.upper() and 'CALCULATE' not in expression.upper():
            recommendations.append("Consider using CALCULATE with filters instead of basic aggregation for more flexibility")

        if len(expression) > 500:
            recommendations.append("Long expression detected - consider breaking into multiple measures for better maintainability")

        if ('/' in expression or 'DIVIDE' in expression.upper()) and 'FORMAT' not in expression.upper():
            recommendations.append("Consider using FORMAT function for better number presentation in reports")

    def _calculate_dax_complexity(self, expression: str) -> Dict[str, Any]:
        """
        Calculate complexity metrics for a DAX expression
        """
        if not expression:
            return {'complexity_score': 0, 'level': 'None'}

        function_count = len(re.findall(r'\b[A-Z]+\s*\(', expression, re.IGNORECASE))
        nested_levels = self._count_max_nesting_level(expression)
        filter_count = len(re.findall(r'\bFILTER\b', expression, re.IGNORECASE))
        calculate_count = len(re.findall(r'\bCALCULATE\b', expression, re.IGNORECASE))

        complexity_score = (function_count * 2) + (nested_levels * 3) + (filter_count * 4) + (calculate_count * 2)

        if complexity_score <= 5:
            level = "Low"
        elif complexity_score <= 15:
            level = "Medium"
        elif complexity_score <= 30:
            level = "High"
        else:
            level = "Very High"

        return {
            'complexity_score': complexity_score,
            'level': level,
            'function_count': function_count,
            'max_nesting_level': nested_levels,
            'filter_count': filter_count,
            'calculate_count': calculate_count,
            'expression_length': len(expression)
        }

    def _count_max_nesting_level(self, expression: str) -> int:
        """
        Count the maximum nesting level of parentheses in an expression
        """
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
