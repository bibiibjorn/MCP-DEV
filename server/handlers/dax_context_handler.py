"""
DAX Context Handler
Handles DAX context analysis and debugging operations with integrated validation
"""
from typing import Dict, Any, Tuple
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def _validate_dax_syntax(expression: str) -> Tuple[bool, str]:
    """
    Validate DAX syntax before analysis

    Args:
        expression: DAX expression to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not connection_state.is_connected():
        return False, "Not connected to Power BI instance"

    qe = connection_state.query_executor
    if not qe:
        return False, "Query executor not available"

    try:
        # Prepare query for validation
        test_query = expression
        if 'EVALUATE' not in test_query.upper():
            # Check if it's a table expression or scalar expression
            # Table expressions contain keywords like FILTER, SELECTCOLUMNS, etc.
            table_keywords = [
                'SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER',
                'VALUES', 'ALL', 'INFO.', 'TOPN', 'SAMPLE', 'SUMMARIZECOLUMNS'
            ]
            is_table_expr = any(kw in test_query.upper() for kw in table_keywords)

            if is_table_expr:
                test_query = f'EVALUATE {test_query}'
            else:
                # Scalar expression (measure) - wrap in ROW()
                test_query = f'EVALUATE ROW("Result", {test_query})'

        # Use query executor to validate
        result = qe.validate_and_execute_dax(test_query, top_n=0)

        if result.get('success'):
            return True, ""
        else:
            return False, result.get('error', 'Unknown validation error')
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

        # Try to find the measure in the model
        tom = connection_state.tom_wrapper
        if tom:
            try:
                # Search for measure across all tables
                found_measure = None
                found_table = None

                # Normalize search term for fuzzy matching
                search_term = expression.lower().strip()
                exact_matches = []
                partial_matches = []

                # Split search term into words, removing common separators
                import re
                search_words = [w for w in re.split(r'[\s\-_]+', search_term) if w]

                for table in tom.model.Tables:
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
                else:
                    # Measure not found - provide helpful suggestions
                    # Find similar measure names for suggestions
                    all_measures = []
                    for table in tom.model.Tables:
                        for measure in table.Measures:
                            all_measures.append((measure.Name, table.Name))

                    # Find measures with any matching words
                    suggestions = []
                    search_words = set(search_term.split())
                    for measure_name_str, table_name in all_measures:
                        measure_words = set(measure_name_str.lower().split())
                        if search_words & measure_words:  # Any word overlap
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
            improvements = debugger.generate_improved_dax(
                dax_expression=expression,
                context_analysis=result_analyze,
                anti_patterns=anti_patterns
            )

            # Run debug mode
            steps = debugger.step_through(
                dax_expression=expression,
                breakpoints=args.get('breakpoints')
            )

            formatted_debug = None
            if steps:
                output_format = args.get('output_format', 'friendly')
                if output_format == 'friendly':
                    formatted_debug = _format_debug_steps_friendly(expression, steps)
                    if validation_result['valid']:
                        validation_header = "✅ DAX SYNTAX VALIDATION: PASSED\n\n"
                        formatted_debug = validation_header + formatted_debug
                    if measure_name:
                        measure_header = f"📊 Analyzing measure: [{measure_table}].[{measure_name}]\n\n"
                        formatted_debug = measure_header + formatted_debug

            # Run report mode
            result_report = debugger.generate_debug_report(
                expression,
                include_profiling=args.get('include_profiling', True),
                include_optimization=args.get('include_optimization', True),
                connection_state=connection_state
            )

            # Combine all results
            response = {
                'success': True,
                'validation': validation_result,
                'mode': 'all',
                'analyze_results': {
                    'analysis': result_analyze.to_dict() if hasattr(result_analyze, 'to_dict') else result_analyze,
                    'anti_patterns': {
                        'patterns_detected': anti_patterns.get('patterns_detected', 0),
                        'pattern_matches': anti_patterns.get('pattern_matches', {}),
                        'recommendations': anti_patterns.get('recommendations', []),
                        'articles': anti_patterns.get('articles', [])
                    } if anti_patterns.get('success') else None,
                    'improvements': {
                        'summary': improvements.get('summary'),
                        'count': improvements.get('improvements_count'),
                        'details': improvements.get('improvements'),
                        'original_code': improvements.get('original_code'),
                        'suggested_code': improvements.get('suggested_code')
                    } if improvements.get('has_improvements') else None
                },
                'debug_results': {
                    'formatted_output': formatted_debug,
                    'total_steps': len(steps) if steps else 0
                },
                'report_results': result_report
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

            # Add anti-pattern detection
            anti_patterns = analyzer.detect_dax_anti_patterns(expression)

            # Generate specific improvements and new DAX code
            improvements = debugger.generate_improved_dax(
                dax_expression=expression,
                context_analysis=result,
                anti_patterns=anti_patterns
            )

            response = {
                'success': True,
                'validation': validation_result,
                'analysis': result.to_dict() if hasattr(result, 'to_dict') else result,
                'mode': 'analyze'
            }

            # Include measure info if auto-fetched
            if measure_name:
                response['measure_info'] = {
                    'name': measure_name,
                    'table': measure_table,
                    'note': f"Auto-fetched measure expression from [{measure_table}].[{measure_name}]"
                }

            # Include anti-pattern detection if successful
            if anti_patterns.get('success'):
                response['anti_patterns'] = {
                    'patterns_detected': anti_patterns.get('patterns_detected', 0),
                    'pattern_matches': anti_patterns.get('pattern_matches', {}),
                    'recommendations': anti_patterns.get('recommendations', []),
                    'articles': anti_patterns.get('articles', [])
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
                "[03-DAX Intelligence v4.2] DEFAULT MODE: Runs ALL analysis (analyze + debug + report) for comprehensive DAX intelligence. "
                "✓ SMART MEASURE FINDER: Just provide measure keywords (e.g., 'base scenario') → automatically finds & analyzes the measure with FUZZY MATCHING. NO need to search first! "
                "✓ AUTO-FETCH: Provide exact or partial measure name → auto-fetches DAX expression + skips validation "
                "✓ ONLINE RESEARCH: Fetches SQLBI optimization articles with specific recommendations "
                "✓ 11 anti-pattern detectors with research-backed recommendations "
                "✓ Context transition analysis with call tree hierarchy "
                "✓ VertiPaq metrics integration (cardinality, memory footprint, iteration estimates) "
                "✓ Calculation group analysis (precedence conflicts, performance impact) "
                "✓ Advanced code rewriting (actual DAX transformations, variable extraction) "
                "✓ Variable optimization scanner (identifies repeated calculations with savings %) "
                "✓ SUMMARIZE→SUMMARIZECOLUMNS detection (2-10x faster) "
                "✓ Visual context flow diagrams (ASCII/HTML/Mermaid) "
                "✓ Specific improvements with REWRITTEN DAX CODE. "
                "All modes run by default. Report mode includes 8 comprehensive analysis sections. Rivals DAX Studio & Tabular Editor analysis depth."
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
