"""
DAX Context Handler
Handles DAX context analysis and debugging operations with integrated validation
"""
from typing import Dict, Any, Tuple, Optional
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

# Try to load AMO for TOM access
AMO_AVAILABLE = False
AMOServer = None
AdomdCommand = None

try:
    import clr
    import os

    # Find DLL folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)  # server
    root_dir = os.path.dirname(parent_dir)     # root
    dll_folder = os.path.join(root_dir, "lib", "dotnet")

    # Load AMO DLLs
    core_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
    amo_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.dll")
    tabular_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")
    adomd_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.AdomdClient.dll")

    if os.path.exists(core_dll):
        clr.AddReference(core_dll)
    if os.path.exists(amo_dll):
        clr.AddReference(amo_dll)
    if os.path.exists(tabular_dll):
        clr.AddReference(tabular_dll)
    if os.path.exists(adomd_dll):
        clr.AddReference(adomd_dll)

    from Microsoft.AnalysisServices.Tabular import Server as AMOServer
    from Microsoft.AnalysisServices.AdomdClient import AdomdCommand
    AMO_AVAILABLE = True
    logger.debug("AMO available for DAX context handler")

except Exception as e:
    logger.debug(f"AMO not available for DAX context handler: {e}")


def _get_server_db_model(conn_state):
    """
    Get AMO server, database, and model objects.

    Args:
        conn_state: ConnectionState instance

    Returns:
        Tuple of (server, database, model) or (None, None, None) if unavailable
    """
    if not AMO_AVAILABLE:
        logger.debug("AMO not available - cannot access model")
        return None, None, None

    if not conn_state.connection_manager:
        logger.debug("No connection manager - cannot access model")
        return None, None, None

    connection = conn_state.connection_manager.get_connection()
    if not connection:
        logger.debug("No active connection - cannot access model")
        return None, None, None

    server = AMOServer()
    try:
        server.Connect(connection.ConnectionString)

        # Get database name
        db_name = None
        try:
            db_query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            cmd = AdomdCommand(db_query, connection)
            reader = cmd.ExecuteReader()
            if reader.Read():
                db_name = str(reader.GetValue(0))
            reader.Close()
        except Exception:
            db_name = None

        if not db_name and server.Databases.Count > 0:
            db_name = server.Databases[0].Name

        if not db_name:
            server.Disconnect()
            return None, None, None

        db = server.Databases.GetByName(db_name)
        model = db.Model

        return server, db, model

    except Exception as e:
        try:
            server.Disconnect()
        except Exception:
            pass
        logger.error(f"Error connecting to AMO server: {e}")
        return None, None, None


def _cleanup_amo_connection(server):
    """
    Safely disconnect and cleanup AMO server connection.

    Args:
        server: AMO Server instance
    """
    if server:
        try:
            server.Disconnect()
        except Exception:
            pass


def _validate_dax_syntax(expression: str) -> Tuple[bool, str]:
    """
    Validate DAX syntax before analysis

    FIXED in v6.0.5:
    1. Improved connection error message with actionable guidance
    2. Fixed table expression detection logic that incorrectly classified measure definitions
       - Old logic: Checked if keywords like FILTER/VALUES existed ANYWHERE in expression
       - New logic: Checks if expression STARTS WITH a table-returning function at ROOT level
       - Example: CALCULATE(SUM(...), FILTER(...)) is now correctly identified as scalar (measure)
       - Example: FILTER(Table, ...) is correctly identified as table expression

    Args:
        expression: DAX expression to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not connection_state.is_connected():
        return False, "Not connected to Power BI instance. Please connect using tool 01_connect_to_instance first."

    qe = connection_state.query_executor
    if not qe:
        return False, "Query executor not available"

    try:
        # Prepare query for validation
        test_query = expression.strip()

        # If already an EVALUATE query, use as-is
        if test_query.upper().startswith('EVALUATE'):
            pass
        else:
            # IMPROVED: Check if the expression starts with a table-returning function at the ROOT level
            # This fixes the issue where measure definitions containing FILTER/VALUES were misclassified

            # Extract first function name (before first opening parenthesis)
            first_token = test_query.lstrip().split('(')[0].upper().strip() if '(' in test_query else test_query.upper().strip()

            # Table-returning functions that are ONLY used at root level (definite table expressions)
            root_table_functions = [
                'SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'SUMMARIZECOLUMNS',
                'TOPN', 'SAMPLE', 'ROW', 'DATATABLE', 'CROSSJOIN', 'UNION',
                'INTERSECT', 'EXCEPT', 'GENERATE', 'GENERATEALL', 'GENERATESERIES'
            ]

            # Functions that can appear at root OR nested (ambiguous - need more context)
            ambiguous_functions = ['FILTER', 'VALUES', 'ALL', 'ALLSELECTED', 'DISTINCT', 'CALCULATETABLE']

            # Check if expression definitely starts with a table function
            is_definitely_table = any(first_token == func for func in root_table_functions)

            # Check if it might be a table expression (starts with ambiguous function)
            is_possibly_table = any(first_token == func for func in ambiguous_functions)

            # Aggregation functions indicate this is a measure (scalar expression)
            # Remove spaces to handle cases like "CALCULATE (" or "SUM  ("
            normalized_query = test_query.upper().replace(' ', '')
            has_aggregation = any(agg in normalized_query for agg in [
                'CALCULATE(', 'SUM(', 'SUMX(', 'AVERAGE(', 'AVERAGEX(',
                'COUNT(', 'COUNTX(', 'COUNTROWS(', 'MIN(', 'MINX(',
                'MAX(', 'MAXX(', 'DIVIDE('
            ])

            # Decision logic:
            # 1. If starts with definite table function -> table expression
            # 2. If starts with ambiguous function BUT has aggregation -> scalar (measure)
            # 3. If starts with ambiguous function AND no aggregation -> table expression
            # 4. Default -> scalar (measure definition)

            if is_definitely_table:
                # Definite table expression
                test_query = f'EVALUATE {test_query}'
            elif is_possibly_table and not has_aggregation:
                # Ambiguous function at root without aggregation -> likely table expression
                test_query = f'EVALUATE {test_query}'
            else:
                # Scalar expression (measure definition) - wrap in ROW()
                test_query = f'EVALUATE ROW("Result", {test_query})'

        # Use query executor to validate
        result = qe.validate_and_execute_dax(test_query, top_n=0)

        if result.get('success'):
            return True, ""
        else:
            error_msg = result.get('error', 'Unknown validation error')
            # Clean up error message if it mentions ROW wrapper (user didn't write ROW)
            if 'ROW' in error_msg and 'ROW' not in expression.upper():
                # Try to remove ROW wrapper artifacts from error message
                error_msg = error_msg.replace('ROW("Result",', '').replace('ROW("Result", ', '')
            return False, error_msg
    except Exception as e:
        return False, str(e)

def handle_analyze_dax_context(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze DAX context transitions with integrated syntax validation

    This tool combines:
    1. DAX syntax validation (former tool 03)
    2. Context transition analysis

    Returns validation status + context analysis
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    expression = args.get('expression')
    skip_validation = args.get('skip_validation', False)

    if not expression:
        return {
            'success': False,
            'error': 'expression parameter is required'
        }

    # Step 1: Validate DAX syntax (unless explicitly skipped)
    validation_result = {'valid': True, 'message': 'Validation skipped'}
    if not skip_validation:
        is_valid, error_msg = _validate_dax_syntax(expression)
        validation_result = {
            'valid': is_valid,
            'message': 'DAX syntax is valid' if is_valid else f'DAX syntax error: {error_msg}'
        }

        if not is_valid:
            return {
                'success': True,
                'validation': validation_result,
                'analysis': None,
                'note': 'Analysis skipped due to syntax errors'
            }

    # Step 2: Perform context analysis
    try:
        from core.dax import DaxContextAnalyzer
        analyzer = DaxContextAnalyzer()

        result = analyzer.analyze_context_transitions(expression)

        return {
            'success': True,
            'validation': validation_result,
            'analysis': result.to_dict() if hasattr(result, 'to_dict') else result
        }

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'validation': validation_result,
            'error': 'DaxContextAnalyzer not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except Exception as e:
        logger.error(f"Error analyzing DAX context: {e}", exc_info=True)
        return {
            'success': False,
            'validation': validation_result,
            'error': f'Error analyzing DAX context: {str(e)}'
        }

def handle_debug_dax_context(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Debug DAX step-by-step with integrated syntax validation

    This tool combines:
    1. DAX syntax validation (former tool 03)
    2. Step-by-step DAX debugging with context transitions

    Returns validation status + debugging steps
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    expression = args.get('expression')
    breakpoints = args.get('breakpoints')
    include_profiling = args.get('include_profiling', True)
    include_optimization = args.get('include_optimization', True)
    output_format = args.get('format', 'friendly')  # 'friendly', 'steps', or 'report'
    skip_validation = args.get('skip_validation', False)

    if not expression:
        return {
            'success': False,
            'error': 'expression parameter is required'
        }

    # Step 1: Validate DAX syntax (unless explicitly skipped)
    validation_result = {'valid': True, 'message': 'Validation skipped'}
    if not skip_validation:
        is_valid, error_msg = _validate_dax_syntax(expression)
        validation_result = {
            'valid': is_valid,
            'message': 'DAX syntax is valid' if is_valid else f'DAX syntax error: {error_msg}'
        }

        if not is_valid:
            return {
                'success': True,
                'validation': validation_result,
                'debug_steps': None,
                'note': 'Debugging skipped due to syntax errors. Fix the syntax errors first.'
            }

    # Step 2: Perform debugging
    try:
        from core.dax import DaxContextDebugger
        debugger = DaxContextDebugger()

        if output_format == 'report':
            # Generate full debug report
            result = debugger.generate_debug_report(
                expression,
                include_profiling=include_profiling,
                include_optimization=include_optimization
            )
            return {
                'success': True,
                'validation': validation_result,
                'report': result
            }
        else:
            # Step-through debugging
            steps = debugger.step_through(
                dax_expression=expression,
                breakpoints=breakpoints
            )

            if not steps:
                return {
                    'success': True,
                    'validation': validation_result,
                    'message': '✅ No context transitions detected in this DAX expression.',
                    'explanation': 'This is a simple expression without CALCULATE, iterators, or measure references that would cause context transitions.',
                    'total_steps': 0
                }

            # Format output based on requested format
            if output_format == 'friendly':
                formatted_output = _format_debug_steps_friendly(expression, steps)
                # Add validation header
                if validation_result['valid']:
                    validation_header = "✅ DAX SYNTAX VALIDATION: PASSED\n\n"
                    formatted_output = validation_header + formatted_output

                return {
                    'success': True,
                    'validation': validation_result,
                    'formatted_output': formatted_output,
                    'total_steps': len(steps)
                }
            else:
                # 'steps' format - raw data
                steps_dict = [
                    {
                        'step_number': step.step_number,
                        'code_fragment': step.code_fragment,
                        'filter_context': step.filter_context,
                        'row_context': step.row_context,
                        'intermediate_result': step.intermediate_result,
                        'explanation': step.explanation,
                        'execution_time_ms': step.execution_time_ms
                    }
                    for step in steps
                ]

                return {
                    'success': True,
                    'validation': validation_result,
                    'debug_steps': steps_dict,
                    'total_steps': len(steps_dict)
                }

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'validation': validation_result,
            'error': 'DaxContextDebugger not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except Exception as e:
        logger.error(f"Error debugging DAX: {e}", exc_info=True)
        return {
            'success': False,
            'validation': validation_result,
            'error': f'Error debugging DAX: {str(e)}'
        }


def _format_debug_steps_friendly(expression: str, steps) -> str:
    """Format debug steps in a user-friendly way"""
    lines = []

    lines.append("=" * 80)
    lines.append("🔍 DAX CONTEXT DEBUGGER - STEP-BY-STEP EXECUTION ANALYSIS")
    lines.append("=" * 80)
    lines.append("")

    lines.append("📝 Your DAX Expression:")
    lines.append("-" * 80)
    lines.append(expression)
    lines.append("")

    lines.append("=" * 80)
    lines.append(f"🎯 Found {len(steps)} Context Transitions")
    lines.append("=" * 80)
    lines.append("")

    lines.append("💡 What are Context Transitions?")
    lines.append("   Context transitions occur when DAX switches between filter context and row context.")
    lines.append("   Understanding these is crucial for writing efficient DAX and avoiding common pitfalls.")
    lines.append("")

    for step in steps:
        lines.append("-" * 80)
        lines.append(f"Step {step.step_number} of {len(steps)}")
        lines.append("-" * 80)
        lines.append("")

        # Show code fragment with pointer
        lines.append("📍 Execution Point:")
        lines.append(f"   {step.code_fragment}")
        lines.append("   ⬆️  The ▶ arrow shows exactly where DAX is evaluating")
        lines.append("")

        # Context information
        lines.append("🔄 Context Information:")

        if step.row_context:
            lines.append(f"   • Row Context: {step.row_context.get('type', 'Active')}")
            if 'function' in step.row_context:
                lines.append(f"     Function: {step.row_context['function']}")
            lines.append("     ℹ️  Row context = iterating over rows of a table")
        else:
            lines.append("   • Row Context: None")
            lines.append("     ℹ️  No row iteration at this point")

        if step.filter_context:
            lines.append(f"   • Filter Context: {len(step.filter_context)} active filters")
            for table, filters in step.filter_context.items():
                lines.append(f"     - {table}: {filters}")
        else:
            lines.append("   • Filter Context: Inherited from visual/slicer")
            lines.append("     ℹ️  Using the filter context from your report")

        lines.append("")

        # Explanation
        lines.append("📖 What's Happening:")
        # Wrap explanation text
        explanation_lines = _wrap_text(step.explanation, width=76, indent=3)
        lines.extend(explanation_lines)
        lines.append("")

        # Performance hint
        if step.execution_time_ms:
            lines.append(f"⏱️  Execution Time: {step.execution_time_ms:.2f}ms")
            lines.append("")

        # Visual separation between steps
        lines.append("")

    lines.append("=" * 80)
    lines.append("✅ ANALYSIS COMPLETE")
    lines.append("=" * 80)
    lines.append("")
    lines.append("💡 Key Takeaways:")
    lines.append("   • Context transitions can impact performance - minimize unnecessary transitions")
    lines.append("   • Measure references inside iterators cause row-by-row context transitions")
    lines.append("   • CALCULATE modifies filter context and transitions from row to filter context")
    lines.append("   • Use variables (VAR) to cache values and reduce repeated transitions")
    lines.append("")
    lines.append("📚 Need more details? Use format='report' for optimization suggestions!")
    lines.append("")

    return "\n".join(lines)


def _wrap_text(text: str, width: int = 80, indent: int = 0) -> list:
    """Wrap text to specified width with indentation"""
    import textwrap

    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
        break_long_words=False,
        break_on_hyphens=False
    )

    return wrapper.wrap(text)

def handle_dax_intelligence(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified DAX Intelligence Tool

    Combines validation, analysis, and debugging into a single intelligent tool.

    Modes:
    - 'all' (DEFAULT): Runs ALL analysis modes - analyze + debug + report
    - 'analyze': Context transition analysis with anti-patterns
    - 'debug': Step-by-step debugging with friendly/steps output
    - 'report': Comprehensive report with optimization + profiling

    Smart measure detection: Automatically fetches measure expressions if a measure name is provided.
    Auto-skips validation for auto-fetched measures (already in model, must be valid).
    Online research enabled for DAX optimization articles and recommendations.
    """
    import re  # For fuzzy measure name matching

    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    expression = args.get('expression')
    analysis_mode = args.get('analysis_mode', 'all')  # Default to 'all' mode (analyze + debug + report)
    skip_validation = args.get('skip_validation', False)

    if not expression:
        return {
            'success': False,
            'error': 'expression parameter is required'
        }

    # Smart measure detection: Check if expression looks like a measure name rather than DAX code
    # Measure names are typically short and don't contain DAX keywords/operators
    original_expression = expression
    measure_name = None
    measure_table = None

    dax_keywords = [
        'CALCULATE', 'FILTER', 'SUM', 'SUMX', 'AVERAGE', 'COUNT', 'COUNTROWS',
        'IF', 'SWITCH', 'VAR', 'RETURN', 'ALL', 'VALUES', 'DISTINCT', 'RELATED',
        'SELECTEDVALUE', 'DIVIDE', 'MAX', 'MIN', 'EVALUATE', '=', '+', '-', '*', '/',
        '[', '(', ')', '{', '}', '&&', '||', '<', '>', '<=', '>=', '<>'
    ]

    # Check if this looks like a simple measure name (not a DAX expression)
    is_likely_measure_name = (
        len(expression) < 150 and  # Measure names are typically short
        not any(keyword in expression.upper() for keyword in dax_keywords[:15]) and  # No major DAX keywords
        expression.count('[') == 0 and  # No column references
        expression.count('(') == 0  # No function calls
    )

    if is_likely_measure_name:
        # Try to fetch the measure expression automatically
        logger.info(f"Expression looks like a measure name: '{expression}'. Attempting auto-fetch...")

        # Try to find the measure in the model using AMO
        server, db, model = _get_server_db_model(connection_state)
        if model:
            try:
                # Search for measure across all tables
                found_measure = None
                found_table = None

                # Normalize search term for fuzzy matching
                search_term = expression.lower().strip()
                exact_matches = []
                partial_matches = []

                # Split search term into words, removing common separators
                search_words = [w for w in re.split(r'[\s\-_]+', search_term) if w]

                for table in model.Tables:
                    for measure in table.Measures:
                        measure_name_lower = measure.Name.lower()

                        # Try exact match first (case-insensitive)
                        if measure_name_lower == search_term:
                            exact_matches.append((measure, table.Name))
                        # Try partial/fuzzy match - check if all words in search term appear in measure name
                        # Use word boundary matching to avoid false positives (e.g., "base" shouldn't match "database")
                        else:
                            # Split measure name into words
                            measure_words = set(re.split(r'[\s\-_]+', measure_name_lower))
                            # Check if all search words appear as complete words in measure name
                            if all(
                                any(search_word in measure_word or measure_word in search_word
                                    for measure_word in measure_words)
                                for search_word in search_words
                            ):
                                partial_matches.append((measure, table.Name))

                # Prioritize exact matches, then partial matches
                if exact_matches:
                    found_measure, found_table = exact_matches[0]
                elif partial_matches:
                    # If multiple partial matches, use the shortest one (most specific)
                    partial_matches.sort(key=lambda x: len(x[0].Name))
                    found_measure, found_table = partial_matches[0]
                    logger.info(f"Using fuzzy match: '{found_measure.Name}' for search term '{expression}'")

                if found_measure:
                    expression = found_measure.Expression
                    measure_name = original_expression
                    measure_table = found_table
                    logger.info(f"Auto-fetched measure '{found_measure.Name}' from table '{found_table}'")
                    # Clean up AMO connection
                    _cleanup_amo_connection(server)
                else:
                    # Measure not found - provide helpful suggestions
                    # Find similar measure names for suggestions
                    all_measures = []
                    for table in model.Tables:
                        for measure in table.Measures:
                            all_measures.append((measure.Name, table.Name))

                    # Clean up AMO connection before returning error
                    _cleanup_amo_connection(server)

                    # Find measures with any matching words (using same word-based logic)
                    suggestions = []
                    search_words_set = set(search_words)
                    for measure_name_str, table_name in all_measures:
                        measure_words_set = set(re.split(r'[\s\-_]+', measure_name_str.lower()))
                        # Check if any search word appears in any measure word
                        if any(
                            search_word in measure_word or measure_word in search_word
                            for search_word in search_words_set
                            for measure_word in measure_words_set
                        ):
                            suggestions.append(f"[{table_name}].[{measure_name_str}]")

                    error_msg = f"The expression '{original_expression}' looks like a measure name, but no exact match was found in the model."
                    if suggestions:
                        error_msg += f"\n\nDid you mean one of these measures?\n" + "\n".join(f"  • {s}" for s in suggestions[:5])
                    error_msg += f"\n\nPlease provide either:\n1. The full DAX expression to analyze, or\n2. A valid measure name"

                    return {
                        'success': False,
                        'error': error_msg,
                        'suggestions': suggestions[:10] if suggestions else None,
                        'hint': 'Try using more specific keywords from the measure name'
                    }
            except Exception as e:
                logger.warning(f"Error during auto-fetch: {e}")
                # Clean up AMO connection
                _cleanup_amo_connection(server)
                # Continue with original expression
                pass

    # Step 1: Validate DAX syntax (unless explicitly skipped)
    # IMPORTANT: Auto-skip validation for auto-fetched measures (they're already in the model and must be valid)
    if measure_name and not skip_validation:
        logger.info(f"Auto-fetched measure '{measure_name}' - skipping validation (already in model)")
        skip_validation = True

    validation_result = {'valid': True, 'message': 'Validation skipped'}
    if not skip_validation:
        is_valid, error_msg = _validate_dax_syntax(expression)
        validation_result = {
            'valid': is_valid,
            'message': 'DAX syntax is valid' if is_valid else f'DAX syntax error: {error_msg}'
        }

        if not is_valid:
            return {
                'success': True,
                'validation': validation_result,
                'analysis': None,
                'note': f'{analysis_mode.title()} skipped due to syntax errors. Fix the syntax errors first.'
            }

    # Step 2: Route to appropriate analysis mode
    try:
        if analysis_mode == 'all':
            # Run all modes: analyze, debug, and report
            from core.dax import DaxContextAnalyzer, DaxContextDebugger
            analyzer = DaxContextAnalyzer()
            debugger = DaxContextDebugger()

            # Run analyze mode
            result_analyze = analyzer.analyze_context_transitions(expression)
            anti_patterns = analyzer.detect_dax_anti_patterns(expression)

            # Generate annotated DAX code for visual display
            annotated_dax = analyzer.format_dax_with_annotations(expression, result_analyze.transitions)

            # Get VertiPaq analysis for comprehensive optimization
            vertipaq_analysis = None
            try:
                from core.dax.vertipaq_analyzer import VertiPaqAnalyzer
                vertipaq = VertiPaqAnalyzer(connection_state)
                vertipaq_analysis = vertipaq.analyze_dax_columns(expression)
                if not vertipaq_analysis.get('success'):
                    logger.warning(f"VertiPaq analysis failed: {vertipaq_analysis.get('error', 'Unknown error')}")
            except Exception as e:
                logger.warning(f"VertiPaq analysis not available: {e}")

            # Run comprehensive best practices analysis
            best_practices_result = None
            try:
                from core.dax.dax_best_practices import DaxBestPracticesAnalyzer
                bp_analyzer = DaxBestPracticesAnalyzer()
                best_practices_result = bp_analyzer.analyze(
                    dax_expression=expression,
                    context_analysis=result_analyze.to_dict() if hasattr(result_analyze, 'to_dict') else result_analyze,
                    vertipaq_analysis=vertipaq_analysis
                )
                logger.info(f"Best practices analysis: {best_practices_result.get('total_issues', 0)} issues found")
            except Exception as e:
                logger.warning(f"Best practices analysis not available: {e}")

            improvements = debugger.generate_improved_dax(
                dax_expression=expression,
                context_analysis=result_analyze,
                anti_patterns=anti_patterns,
                vertipaq_analysis=vertipaq_analysis
            )

            # Run debug mode
            steps = debugger.step_through(
                dax_expression=expression,
                breakpoints=args.get('breakpoints')
            )

            debug_steps_data = None
            if steps:
                debug_steps_data = [
                    {
                        'step_number': step.step_number,
                        'code_fragment': step.code_fragment,
                        'filter_context': step.filter_context,
                        'row_context': step.row_context,
                        'intermediate_result': step.intermediate_result,
                        'explanation': step.explanation,
                        'execution_time_ms': step.execution_time_ms
                    }
                    for step in steps
                ]

            # NOTE: We DO NOT generate the full report in 'all' mode to avoid duplication
            # The report duplicates all structured data (context_analysis, anti_patterns, improvements, vertipaq, call_tree)
            # and also re-runs some expensive analyses (context analysis, anti-patterns)
            # If user wants a formatted text report, they should use analysis_mode='report'
            # result_report = debugger.generate_debug_report(...)  # REMOVED to eliminate duplication

            # Get call tree analysis
            call_tree_data = None
            total_iterations = 0
            try:
                from core.dax.call_tree_builder import CallTreeBuilder

                call_tree_builder = CallTreeBuilder()
                if connection_state:
                    try:
                        from core.dax.vertipaq_analyzer import VertiPaqAnalyzer
                        vertipaq = VertiPaqAnalyzer(connection_state)
                        call_tree_builder.vertipaq_analyzer = vertipaq
                    except:
                        pass

                call_tree = call_tree_builder.build_call_tree(expression)
                tree_viz = call_tree_builder.visualize_tree(call_tree)

                # Calculate total iterations
                def count_iterations(node):
                    total = node.estimated_iterations or 0
                    for child in node.children:
                        total += count_iterations(child)
                    return total

                total_iterations = count_iterations(call_tree)

                call_tree_data = {
                    'visualization': tree_viz,
                    'total_iterations': total_iterations,
                    'performance_warning': (
                        'CRITICAL: Over 1 million iterations - severe performance impact!' if total_iterations >= 1_000_000
                        else 'WARNING: Over 100,000 iterations - consider optimization' if total_iterations >= 100_000
                        else None
                    )
                }

            except Exception as e:
                logger.warning(f"Call tree analysis failed: {e}")
                call_tree_data = {
                    'error': f"Call tree could not be generated: {str(e)}"
                }

            # Combine all articles from various sources
            all_articles = []

            # From anti-pattern detection
            if anti_patterns.get('articles'):
                all_articles.extend(anti_patterns['articles'])

            # From best practices analyzer
            if best_practices_result and best_practices_result.get('articles_referenced'):
                all_articles.extend(best_practices_result['articles_referenced'])

            # Deduplicate articles by URL
            seen_urls = set()
            unique_articles = []
            for article in all_articles:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)

            # Combine all results in structured format
            response = {
                'success': True,
                'validation': validation_result,
                'mode': 'all',

                # ============================================
                # 🚨 CRITICAL AI INSTRUCTIONS - READ FIRST 🚨
                # ============================================
                'AI_INSTRUCTIONS': {
                    'READ_THIS_FIRST': '🚨 This response contains ONLY structured data fields. There is NO text report field. You must read and present the structured fields below.',

                    'PRIORITY_1_SHOW_ANNOTATED_CODE_FIRST': '🚨 MANDATORY: Display the annotated_dax_code.code field FIRST at the very beginning of your response. Show the complete annotated code with the legend. This gives users immediate visual understanding of WHERE context transitions occur (🔄 = Iterator, 📊 = Measure Ref, ⚡ = CALCULATE, 🔴🟡🟢 = Impact).',

                    'PRIORITY_2_PRESENT_ANALYSIS_SUMMARY': 'After annotated code, show the analysis_summary field as a quick overview of findings (complexity score, total transitions, patterns detected, improvements available).',

                    'PRIORITY_3_PRESENT_DETAILED_SECTIONS': 'Then present these sections in order: (1) best_practices_analysis - violations found, (2) anti_patterns - pattern matches with articles, (3) context_analysis.transitions - detailed transition info, (4) improvements.details - specific improvement opportunities, (5) vertipaq_analysis - column metrics if available, (6) call_tree - iteration estimates if available.',

                    'PRIORITY_4_WRITE_OPTIMIZED_CODE': '🚨 CRITICAL: After presenting all analysis, YOU (the AI) MUST write the complete optimized DAX measure. Check optimized_measure.code field - if NULL, YOU must manually write the complete optimized code by applying ALL improvements from improvements.details list. This is NOT optional. Write the FULL measure code, not snippets. The user needs production-ready code to copy-paste into Power BI.',

                    'PRIORITY_5_EXPLAIN_CHANGES': 'After writing optimized code, explain what specific optimizations you applied and WHY they improve performance. Reference specific items from improvements.details and cite articles_referenced when relevant.',

                    'DATA_STRUCTURE_GUIDE': 'Key fields: annotated_dax_code.code (visual code), analysis_summary (quick stats), best_practices_analysis.issues (violations), anti_patterns.pattern_matches (patterns found), context_analysis.transitions (detailed transitions), improvements.details (improvement list), improvements.suggested_code (auto-generated if available), vertipaq_analysis.column_analysis (column metrics), call_tree.visualization (call tree), articles_referenced.articles (research articles)',

                    'WORKFLOW_SUMMARY': 'STEP 1: Show annotated_dax_code → STEP 2: Show analysis_summary → STEP 3: Present detailed sections → STEP 4: Write complete optimized DAX code → STEP 5: Explain changes with article references'
                },

                # ============================================
                # ANNOTATED DAX CODE - SHOW THIS FIRST!
                # ============================================
                'annotated_dax_code': {
                    'code': annotated_dax,
                    'legend': {
                        '🔄': 'Iterator function (creates row context)',
                        '📊': 'Measure reference (implicit CALCULATE)',
                        '⚡': 'Explicit CALCULATE/CALCULATETABLE',
                        '🔴': 'HIGH performance impact',
                        '🟡': 'MEDIUM performance impact',
                        '🟢': 'LOW performance impact'
                    },
                    'note': '🚨 AI: Display this annotated code at the VERY BEGINNING of your response, before any other analysis. The annotations show WHERE each context transition occurs inline in the code. Users need to see this FIRST to understand the problem areas before reading the detailed analysis.'
                },
                'analysis_summary': {
                    'complexity_score': result_analyze.complexity_score,
                    'max_nesting_level': result_analyze.max_nesting_level,
                    'total_transitions': len(result_analyze.transitions),
                    'patterns_detected': anti_patterns.get('patterns_detected', 0),
                    'improvements_available': improvements.get('has_improvements', False),
                    'improvements_count': improvements.get('improvements_count', 0),
                    'best_practices_score': best_practices_result.get('overall_score', 0) if best_practices_result else None,
                    'best_practices_issues': best_practices_result.get('total_issues', 0) if best_practices_result else 0
                },
                'context_analysis': {
                    'summary': result_analyze.summary,
                    'complexity_score': result_analyze.complexity_score,
                    'max_nesting_level': result_analyze.max_nesting_level,
                    'transitions': [
                        {
                            'function': t.function,
                            'line': t.line,
                            'column': t.column,
                            'type': t.type.value,
                            'performance_impact': t.performance_impact.value,
                            'explanation': t.explanation
                        }
                        for t in result_analyze.transitions
                    ]
                },
                'best_practices_analysis': best_practices_result if best_practices_result else {'note': 'Best practices analysis not available'},
                'anti_patterns': {
                    'success': anti_patterns.get('success', False),
                    'patterns_detected': anti_patterns.get('patterns_detected', 0),
                    'pattern_matches': anti_patterns.get('pattern_matches', {}),
                    'recommendations': anti_patterns.get('recommendations', []),
                    'articles': anti_patterns.get('articles', []),
                    'error': anti_patterns.get('error') if not anti_patterns.get('success') else None
                },
                'improvements': {
                    'has_improvements': improvements.get('has_improvements', False),
                    'summary': improvements.get('summary', 'No improvements suggested'),
                    'count': improvements.get('improvements_count', 0),
                    'details': improvements.get('improvements', []),
                    'original_code': expression,
                    'suggested_code': improvements.get('suggested_code')
                },
                'vertipaq_analysis': vertipaq_analysis if vertipaq_analysis and vertipaq_analysis.get('success') else {
                    'note': 'VertiPaq analysis not available',
                    'reason': vertipaq_analysis.get('error') if vertipaq_analysis else 'Analysis failed or not connected to model'
                },
                'call_tree': call_tree_data,
                'debug_steps': debug_steps_data,

                # NOTE: 'report' field removed from 'all' mode to eliminate massive duplication
                # All data is already available in structured fields above
                # If user wants formatted text report, use analysis_mode='report'

                # ============================================
                # 🚨 FINAL OPTIMIZED MEASURE - AI MUST WRITE THIS! 🚨
                # ============================================
                'optimized_measure': {
                    'code': improvements.get('suggested_code'),
                    'code_actually_transformed': improvements.get('code_actually_transformed', False),
                    'has_optimization_opportunities': improvements.get('has_improvements', False),
                    'opportunities_count': improvements.get('improvements_count', 0),
                    'AI_INSTRUCTION': '🚨 CRITICAL: If the code field above is NULL/None, YOU (the AI) MUST write the complete optimized DAX measure by applying ALL improvements from the improvements.details list. Do NOT just describe the improvements - write the ACTUAL working DAX code that implements all optimizations. The user expects to copy-paste this optimized measure directly into Power BI.',
                    'note': improvements.get('note') or (
                        '✅ Automatic transformation applied - this code is ready to use!' if improvements.get('code_actually_transformed')
                        else '⚠️ ATTENTION AI: The code field is NULL because automatic transformation is not available. YOU MUST manually write the complete optimized DAX code by applying ALL improvements listed in the "improvements" section. Write the COMPLETE measure, not just snippets. The user needs the full, production-ready optimized measure.'
                    )
                },
                # PROMINENT ARTICLE REFERENCES SECTION
                'articles_referenced': {
                    'total_count': len(unique_articles),
                    'articles': unique_articles,
                    'note': 'These articles were referenced during the analysis and provide detailed explanations of the patterns detected'
                }
            }

            if measure_name:
                response['measure_info'] = {
                    'name': measure_name,
                    'table': measure_table,
                    'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                }

            return response

        elif analysis_mode == 'analyze':
            # Context transition analysis with anti-pattern detection
            from core.dax import DaxContextAnalyzer, DaxContextDebugger
            analyzer = DaxContextAnalyzer()
            debugger = DaxContextDebugger()

            result = analyzer.analyze_context_transitions(expression)

            # Generate annotated DAX code for visual display
            annotated_dax = analyzer.format_dax_with_annotations(expression, result.transitions)

            # Add anti-pattern detection
            anti_patterns = analyzer.detect_dax_anti_patterns(expression)

            # Get VertiPaq analysis for comprehensive optimization
            vertipaq_analysis = None
            try:
                from core.dax.vertipaq_analyzer import VertiPaqAnalyzer
                vertipaq = VertiPaqAnalyzer(connection_state)
                vertipaq_analysis = vertipaq.analyze_dax_columns(expression)
                if not vertipaq_analysis.get('success'):
                    logger.warning(f"VertiPaq analysis failed: {vertipaq_analysis.get('error', 'Unknown error')}")
            except Exception as e:
                logger.warning(f"VertiPaq analysis not available: {e}")

            # Run comprehensive best practices analysis
            best_practices_result = None
            try:
                from core.dax.dax_best_practices import DaxBestPracticesAnalyzer
                bp_analyzer = DaxBestPracticesAnalyzer()
                best_practices_result = bp_analyzer.analyze(
                    dax_expression=expression,
                    context_analysis=result.to_dict() if hasattr(result, 'to_dict') else result,
                    vertipaq_analysis=vertipaq_analysis
                )
                logger.info(f"Best practices analysis: {best_practices_result.get('total_issues', 0)} issues found")
            except Exception as e:
                logger.warning(f"Best practices analysis not available: {e}")

            # Generate specific improvements and new DAX code
            improvements = debugger.generate_improved_dax(
                dax_expression=expression,
                context_analysis=result,
                anti_patterns=anti_patterns,
                vertipaq_analysis=vertipaq_analysis
            )

            # Combine all articles
            all_articles = []
            if anti_patterns.get('articles'):
                all_articles.extend(anti_patterns['articles'])
            if best_practices_result and best_practices_result.get('articles_referenced'):
                all_articles.extend(best_practices_result['articles_referenced'])

            # Deduplicate
            seen_urls = set()
            unique_articles = []
            for article in all_articles:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)

            response = {
                'success': True,
                'validation': validation_result,
                'mode': 'analyze',

                # ============================================
                # 🚨 CRITICAL AI INSTRUCTIONS - READ FIRST 🚨
                # ============================================
                'AI_INSTRUCTIONS': {
                    'READ_THIS_FIRST': '🚨 This response contains ONLY structured data fields. You must read and present the structured fields below.',

                    'PRIORITY_1_SHOW_ANNOTATED_CODE_FIRST': '🚨 MANDATORY: Display the annotated_dax_code.code field FIRST at the very beginning of your response. Show the complete annotated code with the legend. This gives users immediate visual understanding of WHERE context transitions occur (🔄 = Iterator, 📊 = Measure Ref, ⚡ = CALCULATE, 🔴🟡🟢 = Impact).',

                    'PRIORITY_2_PRESENT_DETAILED_SECTIONS': 'After annotated code, present: (1) best_practices_analysis - violations found, (2) anti_patterns - pattern matches with articles, (3) analysis.transitions - detailed transition info, (4) improvements.details - specific improvement opportunities, (5) vertipaq_analysis - column metrics if available.',

                    'PRIORITY_3_WRITE_OPTIMIZED_CODE': '🚨 CRITICAL: After presenting all analysis, YOU (the AI) MUST write the complete optimized DAX measure. Check final_optimized_measure.code field - if NULL, YOU must manually write the complete optimized code by applying ALL improvements from improvements.details list. This is NOT optional. Write the FULL measure code, not snippets. The user needs production-ready code to copy-paste into Power BI.',

                    'PRIORITY_4_EXPLAIN_CHANGES': 'After writing optimized code, explain what specific optimizations you applied and WHY they improve performance. Reference specific items from improvements.details and cite articles_referenced when relevant.',

                    'DATA_STRUCTURE_GUIDE': 'Key fields: annotated_dax_code.code (visual code), best_practices_analysis.issues (violations), anti_patterns.pattern_matches (patterns found), analysis.transitions (detailed transitions), improvements.details (improvement list), improvements.suggested_code (auto-generated if available), vertipaq_analysis.column_analysis (column metrics), articles_referenced.articles (research articles)',

                    'WORKFLOW_SUMMARY': 'STEP 1: Show annotated_dax_code → STEP 2: Present detailed sections → STEP 3: Write complete optimized DAX code → STEP 4: Explain changes with article references'
                },

                # ============================================
                # ANNOTATED DAX CODE - SHOW THIS FIRST!
                # ============================================
                'annotated_dax_code': {
                    'code': annotated_dax,
                    'legend': {
                        '🔄': 'Iterator function (creates row context)',
                        '📊': 'Measure reference (implicit CALCULATE)',
                        '⚡': 'Explicit CALCULATE/CALCULATETABLE',
                        '🔴': 'HIGH performance impact',
                        '🟡': 'MEDIUM performance impact',
                        '🟢': 'LOW performance impact'
                    },
                    'note': '🚨 AI: Display this annotated code at the VERY BEGINNING of your response, before any other analysis. The annotations show WHERE each context transition occurs inline in the code. Users need to see this FIRST to understand the problem areas before reading the detailed analysis.'
                },
                'analysis': result.to_dict() if hasattr(result, 'to_dict') else result
            }

            # Include measure info if auto-fetched
            if measure_name:
                response['measure_info'] = {
                    'name': measure_name,
                    'table': measure_table,
                    'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                }

            # Include best practices analysis
            response['best_practices_analysis'] = best_practices_result if best_practices_result else {'note': 'Best practices analysis not available'}

            # ALWAYS include anti-pattern detection results (even if failed or no patterns found)
            response['anti_patterns'] = {
                'success': anti_patterns.get('success', False),
                'patterns_detected': anti_patterns.get('patterns_detected', 0),
                'pattern_matches': anti_patterns.get('pattern_matches', {}),
                'recommendations': anti_patterns.get('recommendations', []),
                'articles': anti_patterns.get('articles', []),
                'error': anti_patterns.get('error') if not anti_patterns.get('success') else None
            }

            # Include VertiPaq analysis
            response['vertipaq_analysis'] = vertipaq_analysis if vertipaq_analysis and vertipaq_analysis.get('success') else {
                'note': 'VertiPaq analysis not available',
                'reason': vertipaq_analysis.get('error') if vertipaq_analysis else 'Analysis failed or not connected to model'
            }

            # Include specific improvements with new DAX code
            if improvements.get('has_improvements'):
                response['improvements'] = {
                    'summary': improvements.get('summary'),
                    'count': improvements.get('improvements_count'),
                    'details': improvements.get('improvements'),
                    'original_code': improvements.get('original_code'),
                    'suggested_code': improvements.get('suggested_code')
                }

            # ============================================
            # 🚨 FINAL OPTIMIZED MEASURE - AI MUST WRITE THIS! 🚨
            # ============================================
            response['final_optimized_measure'] = {
                'code': improvements.get('suggested_code'),
                'code_actually_transformed': improvements.get('code_actually_transformed', False),
                'has_optimization_opportunities': improvements.get('has_improvements', False),
                'opportunities_count': improvements.get('improvements_count', 0),
                'AI_INSTRUCTION': '🚨 CRITICAL: If the code field above is NULL/None, YOU (the AI) MUST write the complete optimized DAX measure by applying ALL improvements from the improvements.details list. Do NOT just describe the improvements - write the ACTUAL working DAX code that implements all optimizations. The user expects to copy-paste this optimized measure directly into Power BI.',
                'note': improvements.get('note') or (
                    '✅ Automatic transformation applied - this code is ready to use!' if improvements.get('code_actually_transformed')
                    else '⚠️ ATTENTION AI: The code field is NULL because automatic transformation is not available. YOU MUST manually write the complete optimized DAX code by applying ALL improvements listed in the "improvements" section. Write the COMPLETE measure, not just snippets. The user needs the full, production-ready optimized measure.'
                )
            }

            # PROMINENT ARTICLE REFERENCES
            response['articles_referenced'] = {
                'total_count': len(unique_articles),
                'articles': unique_articles,
                'note': 'These articles were referenced during the analysis and provide detailed explanations of the patterns detected'
            }

            return response

        elif analysis_mode == 'debug':
            # Step-by-step debugging
            from core.dax import DaxContextDebugger
            debugger = DaxContextDebugger()

            output_format = args.get('output_format', 'friendly')
            breakpoints = args.get('breakpoints')

            steps = debugger.step_through(
                dax_expression=expression,
                breakpoints=breakpoints
            )

            if not steps:
                result = {
                    'success': True,
                    'validation': validation_result,
                    'message': '✅ No context transitions detected in this DAX expression.',
                    'explanation': 'This is a simple expression without CALCULATE, iterators, or measure references that would cause context transitions.',
                    'total_steps': 0,
                    'mode': 'debug'
                }
                if measure_name:
                    result['measure_info'] = {
                        'name': measure_name,
                        'table': measure_table,
                        'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                    }
                return result

            # Format output based on requested format
            if output_format == 'friendly':
                formatted_output = _format_debug_steps_friendly(expression, steps)
                # Add validation header
                if validation_result['valid']:
                    validation_header = "✅ DAX SYNTAX VALIDATION: PASSED\n\n"
                    formatted_output = validation_header + formatted_output

                # Add measure info header if auto-fetched
                if measure_name:
                    measure_header = f"📊 Analyzing measure: [{measure_table}].[{measure_name}]\n\n"
                    formatted_output = measure_header + formatted_output

                result = {
                    'success': True,
                    'validation': validation_result,
                    'formatted_output': formatted_output,
                    'total_steps': len(steps),
                    'mode': 'debug'
                }
                if measure_name:
                    result['measure_info'] = {
                        'name': measure_name,
                        'table': measure_table,
                        'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                    }
                return result
            else:
                # 'steps' format - raw data
                steps_dict = [
                    {
                        'step_number': step.step_number,
                        'code_fragment': step.code_fragment,
                        'filter_context': step.filter_context,
                        'row_context': step.row_context,
                        'intermediate_result': step.intermediate_result,
                        'explanation': step.explanation,
                        'execution_time_ms': step.execution_time_ms
                    }
                    for step in steps
                ]

                result = {
                    'success': True,
                    'validation': validation_result,
                    'debug_steps': steps_dict,
                    'total_steps': len(steps_dict),
                    'mode': 'debug'
                }
                if measure_name:
                    result['measure_info'] = {
                        'name': measure_name,
                        'table': measure_table,
                        'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                    }
                return result

        elif analysis_mode == 'report':
            # Comprehensive debug report with all enhancements
            from core.dax import DaxContextDebugger
            debugger = DaxContextDebugger()

            include_profiling = args.get('include_profiling', True)
            include_optimization = args.get('include_optimization', True)

            result = debugger.generate_debug_report(
                expression,
                include_profiling=include_profiling,
                include_optimization=include_optimization,
                connection_state=connection_state  # Pass connection state for enhanced analysis
            )

            response = {
                'success': True,
                'validation': validation_result,
                'report': result,
                'mode': 'report'
            }

            # Extract optimized code from report if available
            # The report already includes the optimized measure in the text
            # Let's also provide it in structured format
            try:
                # Try to get the improvements from the report generation
                from core.dax import DaxContextAnalyzer
                analyzer = DaxContextAnalyzer()
                result_analyze = analyzer.analyze_context_transitions(expression)
                anti_patterns = analyzer.detect_dax_anti_patterns(expression)

                from core.dax import DaxContextDebugger
                debugger_temp = DaxContextDebugger()

                # Get VertiPaq analysis for comprehensive optimization
                vertipaq_analysis = None
                try:
                    from core.dax.vertipaq_analyzer import VertiPaqAnalyzer
                    vertipaq = VertiPaqAnalyzer(connection_state)
                    vertipaq_analysis = vertipaq.analyze_dax_columns(expression)
                except:
                    pass

                improvements = debugger_temp.generate_improved_dax(
                    dax_expression=expression,
                    context_analysis=result_analyze,
                    anti_patterns=anti_patterns,
                    vertipaq_analysis=vertipaq_analysis
                )

                response['final_optimized_measure'] = {
                    'code': improvements.get('suggested_code'),
                    'code_actually_transformed': improvements.get('code_actually_transformed', False),
                    'has_optimization_opportunities': improvements.get('has_improvements', False),
                    'opportunities_count': improvements.get('improvements_count', 0),
                    'AI_INSTRUCTION': '🚨 CRITICAL: If the code field above is NULL/None, YOU (the AI) MUST write the complete optimized DAX measure by applying ALL improvements from the report. Do NOT just describe the improvements - write the ACTUAL working DAX code that implements all optimizations. The user expects to copy-paste this optimized measure directly into Power BI.',
                    'note': improvements.get('note') or (
                        '✅ Automatic transformation applied - this code is ready to use!' if improvements.get('code_actually_transformed')
                        else '⚠️ ATTENTION AI: The code field is NULL because automatic transformation is not available. YOU MUST manually write the complete optimized DAX code by applying ALL improvements listed in the report. Write the COMPLETE measure, not just snippets. The user needs the full, production-ready optimized measure.'
                    )
                }
            except Exception as e:
                logger.warning(f"Could not extract optimized measure: {e}")

            if measure_name:
                response['measure_info'] = {
                    'name': measure_name,
                    'table': measure_table,
                    'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                }
            return response
        else:
            return {
                'success': False,
                'error': f"Invalid analysis_mode: {analysis_mode}. Use 'all' (default), 'analyze', 'debug', or 'report'."
            }

    except ImportError as ie:
        logger.error(f"Import error: {ie}", exc_info=True)
        return {
            'success': False,
            'validation': validation_result,
            'error': f'DAX Intelligence components not available. This is an internal error.',
            'error_type': 'import_error'
        }
    except Exception as e:
        logger.error(f"Error in DAX Intelligence ({analysis_mode} mode): {e}", exc_info=True)
        return {
            'success': False,
            'validation': validation_result,
            'error': f'Error in DAX Intelligence ({analysis_mode} mode): {str(e)}'
        }


def register_dax_handlers(registry):
    """Register unified DAX Intelligence handler (Tool 03)"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="dax_intelligence",
            description=(
                "[03-DAX Intelligence] Comprehensive DAX analysis with optimization recommendations.\n\n"
                "Provides complete analysis including:\n"
                "• Context Transition Analysis: Complexity scores, nesting levels, transition details\n"
                "• Anti-Pattern Detection: SQLBI research articles, pattern matches, recommendations\n"
                "• Code Improvements: Before/after examples with specific transformations\n"
                "• VertiPaq Analysis: Column cardinality, size metrics, performance impact\n"
                "• Call Tree Hierarchy: Function call visualization with iteration estimates\n"
                "• Optimized Code: Production-ready DAX with all improvements applied\n\n"
                "Features:\n"
                "- Smart measure finder with fuzzy matching\n"
                "- Online research integration for best practices\n"
                "- Automatic syntax validation\n"
                "- Single comprehensive output with all analysis results\n\n"
                "Default mode: Runs complete analysis (all sections). Use analysis_mode parameter for specific modes."
            ),
            handler=handle_dax_intelligence,
            input_schema=TOOL_SCHEMAS.get('dax_intelligence', {}),
            category="dax",
            sort_order=21
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} DAX Intelligence handler (Tool 03)")
