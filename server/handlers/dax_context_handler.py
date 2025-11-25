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
        return False, "Not connected to Power BI instance. Please connect using tool '01_Connect_To_Instance' first."

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

def _find_measure_in_model(expression: str, connection_state) -> Dict[str, Any]:
    """
    Find and verify a measure in the model before analysis.

    ALWAYS runs first when expression looks like a measure name.
    Returns measure info if found, or error with suggestions.

    Args:
        expression: The measure name or DAX expression
        connection_state: The connection state

    Returns:
        Dictionary with:
        - found: True if measure was found
        - expression: The DAX expression (either original or fetched)
        - measure_name: The original measure name (if it was a name lookup)
        - measure_table: The table containing the measure
        - error: Error message if not found
        - suggestions: List of similar measures if not found
    """
    import re

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

    if not is_likely_measure_name:
        # This is a DAX expression, not a measure name
        return {
            'found': True,
            'expression': expression,
            'measure_name': None,
            'measure_table': None,
            'is_dax_expression': True
        }

    # This looks like a measure name - must find it first
    logger.info(f"Expression looks like a measure name: '{expression}'. Finding measure FIRST...")

    server, db, model = _get_server_db_model(connection_state)
    if not model:
        return {
            'found': False,
            'error': f"Cannot verify measure '{expression}' - not connected to model via AMO",
            'expression': expression,
            'measure_name': None,
            'measure_table': None
        }

    try:
        # Search for measure across all tables
        found_measure = None
        found_table = None

        # Normalize search term for fuzzy matching
        search_term = expression.lower().strip()
        exact_matches = []
        partial_matches = []
        all_measures = []

        # Split search term into words, removing common separators
        search_words = [w for w in re.split(r'[\s\-_]+', search_term) if w]

        for table in model.Tables:
            for measure in table.Measures:
                measure_name_lower = measure.Name.lower()
                all_measures.append((measure.Name, table.Name, measure.Expression))

                # Try exact match first (case-insensitive)
                if measure_name_lower == search_term:
                    exact_matches.append((measure, table.Name))
                # Try partial/fuzzy match
                else:
                    measure_words = set(re.split(r'[\s\-_]+', measure_name_lower))
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
            partial_matches.sort(key=lambda x: len(x[0].Name))
            found_measure, found_table = partial_matches[0]
            logger.info(f"Using fuzzy match: '{found_measure.Name}' for search term '{expression}'")

        _cleanup_amo_connection(server)

        if found_measure:
            return {
                'found': True,
                'expression': found_measure.Expression,
                'measure_name': found_measure.Name,
                'measure_table': found_table,
                'is_dax_expression': False,
                'actual_name': found_measure.Name  # The real name (may differ from search)
            }
        else:
            # Find suggestions
            suggestions = []
            search_words_set = set(search_words)
            for measure_name_str, table_name, _ in all_measures:
                measure_words_set = set(re.split(r'[\s\-_]+', measure_name_str.lower()))
                if any(
                    search_word in measure_word or measure_word in search_word
                    for search_word in search_words_set
                    for measure_word in measure_words_set
                ):
                    suggestions.append(f"[{table_name}].[{measure_name_str}]")

            return {
                'found': False,
                'error': f"Measure '{expression}' not found in model",
                'expression': expression,
                'measure_name': None,
                'measure_table': None,
                'suggestions': suggestions[:10] if suggestions else None
            }

    except Exception as e:
        _cleanup_amo_connection(server)
        logger.warning(f"Error during measure lookup: {e}")
        return {
            'found': False,
            'error': f"Error finding measure: {str(e)}",
            'expression': expression,
            'measure_name': None,
            'measure_table': None
        }


def handle_dax_intelligence(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified DAX Intelligence Tool - Complete DAX analysis with optimization.

    WORKFLOW:
    1. MEASURE VERIFICATION: Always finds and verifies the measure FIRST
    2. ANALYSIS: Runs comprehensive context transition and pattern analysis
    3. OUTPUT: Returns structured data for AI to present naturally

    The AI should present results as normal text/markdown with only
    DAX code, tree hierarchies, and technical output in code blocks.
    """
    import re

    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    expression = args.get('expression')
    analysis_mode = args.get('analysis_mode', 'all')
    skip_validation = args.get('skip_validation', False)

    if not expression:
        return {
            'success': False,
            'error': 'expression parameter is required'
        }

    # ============================================
    # STEP 1: FIND AND VERIFY MEASURE FIRST
    # ============================================
    # This MUST happen before any analysis to ensure we have the right measure
    measure_lookup = _find_measure_in_model(expression, connection_state)

    if not measure_lookup['found']:
        # Measure not found - return helpful error with suggestions
        error_response = {
            'success': False,
            'error': measure_lookup['error'],
            'hint': 'Use search_objects or search_string tool to find the correct measure name first'
        }
        if measure_lookup.get('suggestions'):
            error_response['similar_measures'] = measure_lookup['suggestions']
            error_response['suggestion'] = f"Did you mean one of these? Try with the exact name."
        return error_response

    # Update expression with the actual DAX (if measure was looked up)
    original_expression = expression
    expression = measure_lookup['expression']
    measure_name = measure_lookup.get('measure_name')
    measure_table = measure_lookup.get('measure_table')
    actual_measure_name = measure_lookup.get('actual_name', measure_name)

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

            # ============================================
            # BUILD CLEAN RESPONSE - STRUCTURED DATA ONLY
            # ============================================
            # The AI will present this as normal markdown text with code blocks
            # for DAX code, tree hierarchies, and technical elements only.

            response = {
                'success': True,
                'validation': validation_result,
                'mode': 'all',

                # Measure info (if looked up by name)
                'measure': {
                    'name': actual_measure_name or 'Custom DAX Expression',
                    'table': measure_table,
                    'searched_as': original_expression if measure_name else None
                } if measure_name else None,

                # SECTION 1: Original DAX Code (for code block display)
                'original_dax': expression.strip(),

                # SECTION 2: Annotated Code with Context Transitions (for code block)
                'annotated_code': annotated_dax,

                # SECTION 3: Key Metrics (present as bullet points, NOT code block)
                'metrics': {
                    'complexity_score': result_analyze.complexity_score,
                    'complexity_level': 'Low' if result_analyze.complexity_score < 20 else 'Moderate' if result_analyze.complexity_score < 50 else 'High' if result_analyze.complexity_score < 80 else 'Very High',
                    'max_nesting_level': result_analyze.max_nesting_level,
                    'context_transitions': len(result_analyze.transitions),
                    'patterns_detected': anti_patterns.get('patterns_detected', 0),
                    'best_practices_score': best_practices_result.get('overall_score', 0) if best_practices_result else None,
                    'issues_found': best_practices_result.get('total_issues', 0) if best_practices_result else 0,
                    'improvements_available': improvements.get('improvements_count', 0)
                },

                # SECTION 4: Quick Assessment (present as checkmarks/warnings, NOT code block)
                'quick_assessment': result_analyze.summary,

                # SECTION 5: Context Transitions Detail (present as numbered list)
                'transitions': [
                    {
                        'function': t.function,
                        'line': t.line,
                        'type': t.type.value,
                        'impact': t.performance_impact.value,
                        'explanation': t.explanation
                    }
                    for t in result_analyze.transitions
                ],

                # SECTION 6: Best Practices Issues (present as prioritized list)
                'best_practices': {
                    'score': best_practices_result.get('overall_score', 0) if best_practices_result else None,
                    'issues': best_practices_result.get('issues', []) if best_practices_result else [],
                    'critical_count': len([i for i in (best_practices_result.get('issues', []) if best_practices_result else []) if i.get('severity') == 'critical']),
                    'high_count': len([i for i in (best_practices_result.get('issues', []) if best_practices_result else []) if i.get('severity') == 'high']),
                    'medium_count': len([i for i in (best_practices_result.get('issues', []) if best_practices_result else []) if i.get('severity') == 'medium'])
                },

                # SECTION 7: Anti-Patterns (present with article references)
                'anti_patterns': {
                    'count': anti_patterns.get('patterns_detected', 0),
                    'patterns': anti_patterns.get('pattern_matches', {}),
                    'recommendations': anti_patterns.get('recommendations', [])
                },

                # SECTION 8: Call Tree (for code block display - technical)
                'call_tree': call_tree_data.get('visualization') if call_tree_data and not call_tree_data.get('error') else None,
                'iterations': {
                    'total': total_iterations,
                    'warning': call_tree_data.get('performance_warning') if call_tree_data else None
                },

                # SECTION 9: Improvements (present as actionable list)
                'improvements': {
                    'count': improvements.get('improvements_count', 0),
                    'summary': improvements.get('summary', 'No improvements needed'),
                    'details': improvements.get('improvements', [])
                },

                # SECTION 10: Optimized Code (for code block display)
                # If auto-generated, show it. Otherwise AI writes it based on improvements.
                'optimized_code': improvements.get('suggested_code'),
                'optimization_applied': improvements.get('code_actually_transformed', False),

                # SECTION 11: Research References (present as linked list)
                'articles': unique_articles,

                # Debug steps (if needed for detailed debugging view)
                'debug_steps': debug_steps_data
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

            # Clean response structure for 'analyze' mode
            response = {
                'success': True,
                'validation': validation_result,
                'mode': 'analyze',

                # Measure info (if looked up by name)
                'measure': {
                    'name': actual_measure_name or 'Custom DAX Expression',
                    'table': measure_table,
                    'searched_as': original_expression if measure_name else None
                } if measure_name else None,

                # Original DAX Code (for code block display)
                'original_dax': expression.strip(),

                # Annotated Code with Context Transitions (for code block)
                'annotated_code': annotated_dax,

                # Analysis results
                'analysis': result.to_dict() if hasattr(result, 'to_dict') else result,

                # Best practices
                'best_practices': {
                    'score': best_practices_result.get('overall_score', 0) if best_practices_result else None,
                    'issues': best_practices_result.get('issues', []) if best_practices_result else []
                },

                # Anti-patterns
                'anti_patterns': {
                    'count': anti_patterns.get('patterns_detected', 0),
                    'patterns': anti_patterns.get('pattern_matches', {}),
                    'recommendations': anti_patterns.get('recommendations', [])
                },

                # Improvements
                'improvements': {
                    'count': improvements.get('improvements_count', 0),
                    'summary': improvements.get('summary', 'No improvements needed'),
                    'details': improvements.get('improvements', [])
                },

                # Optimized Code (for code block display)
                'optimized_code': improvements.get('suggested_code'),
                'optimization_applied': improvements.get('code_actually_transformed', False),

                # Research References
                'articles': unique_articles
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

                response['optimized_code'] = improvements.get('suggested_code')
                response['optimization_applied'] = improvements.get('code_actually_transformed', False)
                response['improvements_count'] = improvements.get('improvements_count', 0)
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
                "[03-DAX Intelligence] Comprehensive DAX analysis with optimization.\n\n"
                "WORKFLOW:\n"
                "1. MEASURE LOOKUP: Automatically finds and verifies measure before analysis\n"
                "2. ANALYSIS: Runs context, pattern, and best practices analysis\n"
                "3. OPTIMIZATION: Generates or guides creation of optimized DAX\n\n"
                "RESPONSE FORMAT:\n"
                "• 'original_dax' and 'annotated_code': Show in code blocks\n"
                "• 'metrics', 'quick_assessment': Present as bullet points (NOT code blocks)\n"
                "• 'transitions', 'best_practices', 'improvements': Present as lists\n"
                "• 'call_tree': Show in code block (technical hierarchy)\n"
                "• 'optimized_code': Show in code block - if null, AI writes optimized version\n"
                "• 'articles': Present as references with links\n\n"
                "Analysis includes:\n"
                "• Context Transition Analysis: Complexity scores, nesting levels\n"
                "• Anti-Pattern Detection: SQLBI research, pattern matches\n"
                "• Best Practices: Issues with severity levels\n"
                "• Call Tree: Iteration estimates\n"
                "• Optimized Code: Production-ready DAX\n\n"
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
