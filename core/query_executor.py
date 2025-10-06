"""
Optimized Query Executor for PBIXRay MCP Server

Enhanced DAX query execution with:
- Better error handling and suggestions
- Table reference support
- Query caching
- DAX-level filtering
- Comprehensive error analysis

Based on fabric-toolbox best practices.
"""

import time
import logging
from typing import Any, Dict, List, Optional
from collections import OrderedDict
from core.dax_validator import DaxValidator

logger = logging.getLogger(__name__)

# Try to load ADOMD.NET
ADOMD_AVAILABLE = False
AdomdConnection = None
AdomdCommand = None

try:
    import clr
    import os

    # Determine DLL path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    # Load ADOMD.NET
    adomd_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.AdomdClient.dll")
    if os.path.exists(adomd_dll):
        clr.AddReference(adomd_dll)
        from Microsoft.AnalysisServices.AdomdClient import AdomdConnection, AdomdCommand
        ADOMD_AVAILABLE = True
        logger.info("ADOMD.NET loaded successfully")
except Exception as e:
    logger.warning(f"ADOMD.NET not available: {e}")


class OptimizedQueryExecutor:
    """
    Optimized query executor with enhanced error handling and DAX query optimization.

    Features:
    - Intelligent table reference handling
    - Comprehensive error analysis with suggestions
    - Query result caching
    - DAX-level filtering for performance
    - Safe execution with multiple fallback strategies
    """

    def __init__(self, connection):
        """
        Initialize the query executor.

        Args:
            connection: Active ADOMD connection
        """
        self.connection = connection
        self.query_cache = OrderedDict()
        self.max_cache_items = 200
        self._table_cache = None

    def _escape_dax_string(self, text: str) -> str:
        """Escape single quotes in DAX strings."""
        return text.replace("'", "''") if text else text

    def _get_info_columns(self, function_name: str) -> List[str]:
        """
        Get available columns for INFO functions.

        Args:
            function_name: Name of INFO function (TABLES, COLUMNS, MEASURES, RELATIONSHIPS)

        Returns:
            List of column names
        """
        column_map = {
            'MEASURES': ['Name', 'Table', 'DataType', 'IsHidden', 'DisplayFolder', 'Expression'],
            'TABLES': ['Name', 'IsHidden', 'ModifiedTime', 'DataCategory'],
            'COLUMNS': ['Name', 'Table', 'DataType', 'IsHidden', 'IsKey', 'Type'],
            'RELATIONSHIPS': ['FromTable', 'FromColumn', 'ToTable', 'ToColumn', 'IsActive', 'CrossFilterDirection', 'Cardinality']
        }
        return column_map.get(function_name, [])

    def _analyze_dax_error(self, error_msg: str, dax_query: str) -> List[str]:
        """
        Analyze DAX error and provide helpful suggestions.

        Args:
            error_msg: Error message from DAX execution
            dax_query: The DAX query that failed

        Returns:
            List of suggestion strings
        """
        suggestions = []
        error_lower = error_msg.lower()

        # Table reference issues
        if "table" in error_lower and ("not found" in error_lower or "doesn't exist" in error_lower):
            suggestions.extend([
                "Check table name spelling and case sensitivity",
                "Use list_tables tool to see available tables",
                "Ensure table name matches exactly as shown in Power BI",
                "Try wrapping table name in single quotes: 'TableName'"
            ])

        # Column reference issues
        if "column" in error_lower and ("not found" in error_lower or "doesn't exist" in error_lower):
            suggestions.extend([
                "Check column name spelling and case sensitivity",
                "Use describe_table tool to see available columns",
                "Try using [Table][Column] syntax",
                "Verify column exists in the specified table"
            ])

        # Syntax issues
        if "syntax" in error_lower:
            suggestions.extend([
                "Check DAX syntax - ensure EVALUATE is used for table expressions",
                "Verify parentheses and brackets are properly matched",
                "Check function parameter count and types",
                "Review DAX function syntax reference"
            ])

        # Function issues
        if "function" in error_lower:
            suggestions.extend([
                "Verify function name spelling",
                "Check function parameter types and count",
                "Some functions may not be available in Power BI Desktop",
                "Review supported DAX functions list"
            ])

        # Measure/calculation errors
        if "error" in error_lower and "measure" in error_lower:
            suggestions.extend([
                "Check for circular dependencies in measures",
                "Verify all referenced measures exist",
                "Test measure expressions individually"
            ])

        if not suggestions:
            suggestions.extend([
                "Check DAX syntax and function usage",
                "Verify all table and column references exist",
                "Try simplifying the query to isolate the issue",
                "Review DAX query best practices"
            ])

        return suggestions

    def execute_info_query(self, function_name: str, filter_expr: str = None, exclude_columns: List[str] = None) -> Dict[str, Any]:
        """
        Execute INFO.* DAX query with optional filtering.

        Args:
            function_name: INFO function name (TABLES, COLUMNS, MEASURES, RELATIONSHIPS)
            filter_expr: Optional DAX filter expression
            exclude_columns: Optional list of columns to exclude

        Returns:
            Query result dictionary
        """
        try:
            if exclude_columns:
                cols = self._get_info_columns(function_name)
                selected = [f'"{col}", [{col}]' for col in cols if col not in exclude_columns]
                query = f"EVALUATE SELECTCOLUMNS(INFO.{function_name}(), {', '.join(selected)})"
            else:
                query = f"EVALUATE INFO.{function_name}()"

            if filter_expr:
                query = f"EVALUATE FILTER(INFO.{function_name}(), {filter_expr})"

            return self.validate_and_execute_dax(query, 0)
        except Exception as e:
            logger.error(f"Error executing INFO query: {e}")
            return {'success': False, 'error': str(e)}

    def search_measures_dax(self, search_text: str, search_in_expression: bool = True, search_in_name: bool = True) -> Dict:
        """
        Search for text in DAX measures.

        Args:
            search_text: Text to search for
            search_in_expression: Whether to search in measure expressions
            search_in_name: Whether to search in measure names

        Returns:
            Search results dictionary
        """
        try:
            escaped_text = self._escape_dax_string(search_text)
            conditions = []

            if search_in_expression:
                conditions.append(f'SEARCH("{escaped_text}", [Expression], 1, 0) > 0')
            if search_in_name:
                conditions.append(f'SEARCH("{escaped_text}", [Name], 1, 0) > 0')

            filter_expr = ' || '.join(conditions) if conditions else 'TRUE()'
            query = f"EVALUATE FILTER(INFO.MEASURES(), {filter_expr})"

            return self.validate_and_execute_dax(query)
        except Exception as e:
            logger.error(f"Error searching measures: {e}")
            return {'success': False, 'error': str(e)}

    def search_objects_dax(self, pattern: str, object_types: List[str]) -> Dict:
        """
        Search for objects by pattern.

        Args:
            pattern: Search pattern (wildcards removed internally)
            object_types: List of object types to search (tables, columns, measures)

        Returns:
            Search results dictionary
        """
        try:
            search_text = pattern.replace('*', '').replace('?', '')
            escaped_text = self._escape_dax_string(search_text)
            results_list = []

            if "tables" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.TABLES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "table",
                    "Name", [Name],
                    "IsHidden", [IsHidden],
                    "ModifiedTime", [ModifiedTime]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])

            if "columns" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.COLUMNS(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "column",
                    "Name", [Name],
                    "Table", [Table],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])

            if "measures" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.MEASURES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "measure",
                    "Name", [Name],
                    "Table", [Table],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden],
                    "DisplayFolder", [DisplayFolder]
                )
                """
                r = self.validate_and_execute_dax(query)
                if r.get('success'):
                    results_list.extend(r['rows'])

            return {'success': True, 'results': results_list, 'count': len(results_list)}
        except Exception as e:
            logger.error(f"Error searching objects: {e}")
            return {'success': False, 'error': str(e)}

    def _is_table_expression(self, query: str) -> bool:
        """Check if query is a table expression."""
        table_keywords = [
            'SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER',
            'VALUES', 'ALL', 'INFO.', 'TOPN', 'SAMPLE', 'SUMMARIZECOLUMNS'
        ]
        return any(kw in query.upper() for kw in table_keywords)

    def validate_and_execute_dax(self, query: str, top_n: int = 0) -> Dict[str, Any]:
        """
        Validate and execute DAX query with comprehensive error handling.

        Args:
            query: DAX query to execute
            top_n: Optional row limit

        Returns:
            Query result dictionary with success status, data, and metadata
        """
        try:
            # Pre-execution syntax validation
            syntax_errors = DaxValidator.validate_query_syntax(query)
            if syntax_errors:
                return {
                    'success': False,
                    'error': f"Query validation failed: {'; '.join(syntax_errors)}",
                    'error_type': 'syntax_validation_error',
                    'query': query,
                    'suggestions': [
                        "Fix syntax errors before executing",
                        "Check for balanced delimiters (parentheses, brackets, quotes)",
                        "Review DAX syntax documentation"
                    ]
                }

            # Auto-add EVALUATE if needed
            if not query.strip().upper().startswith('EVALUATE'):
                if self._is_table_expression(query):
                    query = f"EVALUATE TOPN({top_n}, {query})" if top_n > 0 else f"EVALUATE {query}"
                else:
                    query = f'EVALUATE ROW("Value", {query})'

            start_time = time.time()
            cmd = AdomdCommand(query, self.connection)
            reader = cmd.ExecuteReader()

            # Get columns
            columns = [reader.GetName(i) for i in range(reader.FieldCount)]
            rows = []

            # Read rows with proper error handling
            max_rows = 10000  # Safety limit
            row_count = 0

            while reader.Read() and row_count < max_rows:
                row = {}
                for i, col in enumerate(columns):
                    try:
                        val = reader.GetValue(i)
                        if val is None:
                            row[col] = None
                        elif hasattr(val, 'isoformat'):  # DateTime
                            row[col] = val.isoformat()
                        else:
                            row[col] = str(val)
                    except Exception as col_error:
                        logger.warning(f"Error reading column {col}: {col_error}")
                        row[col] = f"<read_error>"

                rows.append(row)
                row_count += 1

            reader.Close()
            execution_time = (time.time() - start_time) * 1000

            return {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
                'execution_time_ms': round(execution_time, 2),
                'truncated': row_count >= max_rows,
                'query': query
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"DAX query error: {error_msg}")

            suggestions = self._analyze_dax_error(error_msg, query)

            return {
                'success': False,
                'error': error_msg,
                'error_type': 'query_execution_error',
                'query': query,
                'suggestions': suggestions
            }

    def execute_with_table_reference_fallback(self, table_name: str, max_rows: int = 10) -> Dict[str, Any]:
        """
        Execute table query with automatic reference format fallback.

        Tries multiple table reference formats:
        - 'TableName' (single quotes)
        - TableName (direct)
        - [TableName] (brackets)

        Args:
            table_name: Name of table to query
            max_rows: Maximum rows to return

        Returns:
            Query result dictionary
        """
        table_formats = [
            f"'{table_name}'",     # Preferred - single quotes
            table_name,            # Direct name
            f"[{table_name}]",     # Brackets
        ]

        for table_ref in table_formats:
            query = f"EVALUATE TOPN({max_rows}, {table_ref})"
            result = self.validate_and_execute_dax(query)

            if result.get('success'):
                result['table_reference_used'] = table_ref
                result['table_name'] = table_name
                logger.debug(f"Successfully queried table with reference: {table_ref}")
                return result
            else:
                logger.debug(f"Table reference '{table_ref}' failed: {result.get('error')}")

        # All formats failed
        return {
            'success': False,
            'error': f"Could not query table '{table_name}' with any reference format",
            'error_type': 'table_reference_error',
            'attempted_formats': table_formats,
            'suggestions': [
                f"Verify table '{table_name}' exists using list_tables tool",
                "Check if table name has special characters or spaces",
                "Table name may be case-sensitive"
            ]
        }

    def analyze_dax_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze DAX query for complexity, patterns, and optimization opportunities.

        Args:
            query: DAX query or expression to analyze

        Returns:
            Analysis results with complexity metrics and suggestions
        """
        try:
            # Validate syntax first
            syntax_errors = DaxValidator.validate_query_syntax(query)

            # Analyze complexity
            complexity_analysis = DaxValidator.analyze_complexity(query)

            # Analyze patterns
            good_patterns, anti_patterns = DaxValidator.analyze_patterns(query)

            # Generate optimization suggestions
            optimization_suggestions = DaxValidator.generate_optimization_suggestions(query)

            return {
                'success': True,
                'query': query,
                'syntax_valid': len(syntax_errors) == 0,
                'syntax_errors': syntax_errors,
                'complexity': complexity_analysis,
                'good_patterns': good_patterns,
                'anti_patterns': anti_patterns,
                'optimization_suggestions': optimization_suggestions,
                'security_validated': DaxValidator.validate_identifier(query.split()[0]) if query.strip() else True
            }
        except Exception as e:
            logger.error(f"Error analyzing DAX query: {e}")
            return {'success': False, 'error': str(e)}

    def get_tmsl_definition(self) -> Dict:
        """
        Get TMSL definition for BPA analysis.

        Returns:
            TMSL definition dictionary with metadata
        """
        try:
            # Import AMO
            import clr
            import os

            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            dll_folder = os.path.join(parent_dir, "lib", "dotnet")

            core_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
            amo_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.dll")
            tabular_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")

            if os.path.exists(core_dll):
                clr.AddReference(core_dll)
            if os.path.exists(amo_dll):
                clr.AddReference(amo_dll)
            if os.path.exists(tabular_dll):
                clr.AddReference(tabular_dll)

            from Microsoft.AnalysisServices.Tabular import Server as AMOServer, JsonSerializer, SerializeOptions

            # Get database name
            db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            cmd = AdomdCommand(db_query, self.connection)
            reader = cmd.ExecuteReader()

            db_name = None
            if reader.Read():
                db_name = str(reader.GetValue(0))
            reader.Close()

            if not db_name:
                return {'success': False, 'error': 'Could not determine database name'}

            # Connect with AMO
            server = AMOServer()
            server.Connect(self.connection.ConnectionString)
            database = server.Databases.GetByName(db_name)

            # Serialize to TMSL
            options = SerializeOptions()
            options.IgnoreTimestamps = True
            options.IgnoreInferredObjects = True
            options.IgnoreInferredProperties = True

            tmsl_json = JsonSerializer.SerializeDatabase(database, options)
            server.Disconnect()

            return {
                'success': True,
                'tmsl': tmsl_json,
                'database_name': db_name,
                'method': 'TMSL extraction via AMO'
            }

        except Exception as e:
            logger.error(f"Error getting TMSL: {e}")
            return {'success': False, 'error': str(e)}
