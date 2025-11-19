"""
Analysis Handler
Handles model analysis tools including simple analysis, full analysis, BPA, performance, and validation
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.utilities.business_impact import enrich_issue_with_impact, add_impact_summary

logger = logging.getLogger(__name__)

def _generate_operation_analysis(op_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate AI-optimized analysis summary for each operation.
    Provides insights, patterns, and recommendations specific to each operation.
    """
    if not result.get('success'):
        return {
            'status': 'failed',
            'insights': [],
            'recommendations': []
        }

    analysis = {
        'status': 'success',
        'insights': [],
        'recommendations': [],
        'key_findings': []
    }

    try:
        # Database operation analysis
        if op_id == '01_database':
            data = result.get('data', [{}])[0]
            compat = data.get('compatibilityLevel', 0)
            size_mb = round(data.get('estimatedSize', 0) / (1024 * 1024), 2) if data.get('estimatedSize') else 0

            analysis['insights'].append(f"Database compatibility level: {compat}")
            if compat >= 1600:
                analysis['insights'].append("Power BI Desktop format (modern)")
            elif compat >= 1500:
                analysis['insights'].append("Azure Analysis Services format")

            if size_mb > 0:
                analysis['key_findings'].append(f"Model size: {size_mb} MB")
                if size_mb > 1000:
                    analysis['recommendations'].append("Large model - consider incremental refresh and data reduction strategies")
                elif size_mb > 500:
                    analysis['recommendations'].append("Medium-sized model - monitor refresh times and consider optimization")

        # Stats operation analysis
        elif op_id == '02_stats':
            counts = result.get('counts', {})
            tables = counts.get('tables', 0)
            measures = counts.get('measures', 0)
            columns = counts.get('columns', 0)
            rels = counts.get('relationships', 0)
            calc_groups = counts.get('calculation_groups', 0)

            analysis['key_findings'] = [
                f"{tables} tables",
                f"{columns} columns",
                f"{measures} measures",
                f"{rels} relationships"
            ]

            # Complexity assessment
            if tables > 100:
                analysis['insights'].append("Large model with many tables - ensure proper naming conventions")
            if measures > 200:
                analysis['insights'].append("High measure count - use display folders for organization")
            if calc_groups > 0:
                analysis['insights'].append(f"Using {calc_groups} calculation groups - advanced time intelligence pattern")

            # Ratio analysis
            if tables > 0:
                cols_per_table = round(columns / tables, 1)
                measures_per_table = round(measures / tables, 1)
                analysis['insights'].append(f"Average {cols_per_table} columns and {measures_per_table} measures per table")

        # Tables operation analysis
        elif op_id == '03_tables':
            data = result.get('data', [])
            table_count = len(data)

            # Identify measure tables
            measure_tables = [t for t in data if t.get('measureCount', 0) > 10 and t.get('columnCount', 0) < 5]
            large_tables = [t for t in data if t.get('columnCount', 0) > 50]

            analysis['key_findings'].append(f"{table_count} tables in model")
            if measure_tables:
                analysis['insights'].append(f"{len(measure_tables)} dedicated measure tables (best practice)")
            if large_tables:
                analysis['insights'].append(f"{len(large_tables)} tables with >50 columns - review for normalization")

        # Measures operation analysis
        elif op_id == '04_measures':
            data = result.get('data', [])
            measure_count = len(data)

            # Analyze display folders
            with_folders = [m for m in data if m.get('displayFolder')]
            folder_usage = round(len(with_folders) / measure_count * 100, 1) if measure_count > 0 else 0

            analysis['key_findings'].append(f"{measure_count} measures analyzed")
            if folder_usage > 80:
                analysis['insights'].append(f"{folder_usage}% measures use display folders - excellent organization")
            elif folder_usage > 50:
                analysis['insights'].append(f"{folder_usage}% measures use display folders - good organization")
            else:
                analysis['recommendations'].append("Consider organizing measures with display folders for better UX")

        # Columns operation analysis
        elif op_id == '05_columns':
            data = result.get('data', [])
            total_columns = sum(len(t.get('columns', [])) for t in data)
            table_count = len(data)

            analysis['key_findings'].append(f"{total_columns} columns across {table_count} tables")

            # Data type analysis
            all_columns = [col for table in data for col in table.get('columns', [])]
            data_types = {}
            for col in all_columns:
                dt = col.get('dataType', 'Unknown')
                data_types[dt] = data_types.get(dt, 0) + 1

            if data_types:
                top_type = max(data_types.items(), key=lambda x: x[1])
                analysis['insights'].append(f"Most common data type: {top_type[0]} ({top_type[1]} columns)")

        # Relationships operation analysis - ENHANCED with detailed cardinality patterns
        elif op_id == '06_relationships':
            data = result.get('data', [])
            total_rels = len(data)

            # Analyze ALL cardinality patterns
            one_to_one = [r for r in data if r.get('fromCardinality') == 'One' and r.get('toCardinality') == 'One']
            one_to_many = [r for r in data if r.get('fromCardinality') == 'One' and r.get('toCardinality') == 'Many']
            many_to_one = [r for r in data if r.get('fromCardinality') == 'Many' and r.get('toCardinality') == 'One']
            many_to_many = [r for r in data if r.get('fromCardinality') == 'Many' and r.get('toCardinality') == 'Many']

            bidirectional = [r for r in data if r.get('crossFilteringBehavior') == 'BothDirections']
            inactive = [r for r in data if not r.get('isActive')]

            # Key findings with cardinality breakdown
            analysis['key_findings'].append(f"{total_rels} relationships total")

            cardinality_breakdown = []
            if many_to_one:
                cardinality_breakdown.append(f"{len(many_to_one)} Many:One (standard)")
            if one_to_many:
                cardinality_breakdown.append(f"{len(one_to_many)} One:Many")
            if many_to_many:
                cardinality_breakdown.append(f"{len(many_to_many)} Many:Many")
            if one_to_one:
                cardinality_breakdown.append(f"{len(one_to_one)} One:One")

            if cardinality_breakdown:
                analysis['key_findings'].append("Cardinality: " + ", ".join(cardinality_breakdown))

            # PROMINENT warnings for problematic patterns
            if many_to_many:
                analysis['insights'].append(f"⚠️ {len(many_to_many)} MANY-TO-MANY relationships detected")

                # Show examples of M:M relationships
                m2m_examples = [f"{r.get('fromTable')} ↔ {r.get('toTable')}" for r in many_to_many[:3]]
                if m2m_examples:
                    analysis['insights'].append(f"   Examples: {', '.join(m2m_examples)}")

                if len(many_to_many) > 10:
                    analysis['recommendations'].append("⚠️ HIGH: Consider bridge tables for M:M relationships to improve performance")
                elif len(many_to_many) > 5:
                    analysis['recommendations'].append("MEDIUM: Review M:M relationships for potential optimization")
                else:
                    analysis['recommendations'].append("LOW: Monitor M:M relationship performance")

            if bidirectional:
                analysis['insights'].append(f"⚠️ {len(bidirectional)} BI-DIRECTIONAL relationships found")

                # Show examples of bidirectional relationships
                bidir_examples = [f"{r.get('fromTable')} ↔ {r.get('toTable')}" for r in bidirectional[:3]]
                if bidir_examples:
                    analysis['insights'].append(f"   Examples: {', '.join(bidir_examples)}")

                analysis['recommendations'].append("⚠️ Review bidirectional filters - can cause ambiguity and performance issues")

            if inactive:
                analysis['insights'].append(f"ℹ️ {len(inactive)} INACTIVE relationships (likely used with USERELATIONSHIP)")

                # Show examples of inactive relationships
                inactive_examples = [f"{r.get('fromTable')} → {r.get('toTable')}" for r in inactive[:3]]
                if inactive_examples:
                    analysis['insights'].append(f"   Examples: {', '.join(inactive_examples)}")

            # Positive insights
            if not many_to_many and not bidirectional:
                analysis['insights'].append("✅ Clean relationship model - no M:M or bidirectional relationships")

            if many_to_one and len(many_to_one) == total_rels - len(inactive):
                analysis['insights'].append("✅ Standard star schema pattern - all active relationships are Many:One")

        # Calculation groups analysis
        elif op_id == '07_calculation_groups':
            data = result.get('data', [])
            group_count = len(data)
            total_items = sum(len(cg.get('calculationItems', [])) for cg in data)

            if group_count > 0:
                analysis['key_findings'].append(f"{group_count} calculation groups with {total_items} items")
                analysis['insights'].append("Using calculation groups - advanced DAX pattern for time intelligence")

                # Analyze group names for patterns
                group_names = [cg.get('name', '') for cg in data]
                if any('time' in name.lower() for name in group_names):
                    analysis['insights'].append("Time-based calculation groups detected")
                if any('currency' in name.lower() or 'fx' in name.lower() for name in group_names):
                    analysis['insights'].append("Currency conversion calculation groups detected")
            else:
                analysis['insights'].append("No calculation groups - consider using them for time intelligence patterns")

        # Roles analysis
        elif op_id == '08_roles':
            data = result.get('data', [])
            role_count = len(data)

            if role_count > 0:
                analysis['key_findings'].append(f"{role_count} security roles configured")
                analysis['insights'].append("Row-level security (RLS) is implemented")

                # Check for table permissions
                with_permissions = [r for r in data if r.get('tablePermissionCount', 0) > 0]
                if with_permissions:
                    avg_perms = round(sum(r.get('tablePermissionCount', 0) for r in with_permissions) / len(with_permissions), 1)
                    analysis['insights'].append(f"Average {avg_perms} table permissions per role")
            else:
                analysis['insights'].append("No security roles - model is open to all users")
                analysis['recommendations'].append("Consider implementing RLS if data access should be restricted")

    except Exception as e:
        logger.error(f"Error generating analysis for {op_id}: {e}")
        analysis['insights'].append("Analysis generation encountered an error")

    return analysis

def handle_simple_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fast model operations based on Microsoft Official MCP Server operations.

    Modes:
    - 'all': Run ALL 10 Microsoft MCP operations in sequence (comprehensive overview)
    - 'tables': Ultra-fast table list (< 500ms) - Microsoft MCP List operation
    - 'stats': Fast model statistics (< 1s) - Microsoft MCP GetStats operation
    - 'measures': List measures (optional table filter) - Microsoft MCP Measure List operation
    - 'measure': Get measure details (requires table + measure_name) - Microsoft MCP Measure Get operation
    - 'columns': List columns (optional table filter) - Microsoft MCP Column List operation
    - 'relationships': List relationships - Microsoft MCP Relationship List operation
    - 'partitions': List partitions (optional table filter) - Microsoft MCP Partition List operation
    - 'roles': List security roles - Microsoft MCP Role List operation
    - 'database': List databases - Microsoft MCP Database List operation
    - 'calculation_groups': List calculation groups - Microsoft MCP ListGroups operation
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    # Extract mode parameter (default: all - runs all 8 auto-executable operations)
    mode = args.get('mode', 'all')

    # Special mode: Run ALL 8 auto-executable core operations (excluding partitions and measure get)
    if mode == 'all':
        import time
        start_time = time.time()

        # Initialize with prominent execution header
        execution_log = []
        execution_log.append('='*80)
        execution_log.append('>>> MICROSOFT MCP OPERATIONS - SEQUENTIAL EXECUTION <<<')
        execution_log.append('='*80)
        execution_log.append('')

        # Define all operations to execute
        operations = [
            ('01_database', 'Database Info', lambda: agent_policy.analysis_orch.list_databases_simple(connection_state)),
            ('02_stats', 'Model Statistics (GetStats)', lambda: agent_policy.analysis_orch.simple_model_analysis(connection_state)),
            ('03_tables', 'Tables List', lambda: agent_policy.analysis_orch.list_tables_simple(connection_state)),
            ('04_measures', 'Measures List (500 max)', lambda: agent_policy.analysis_orch.list_measures_simple(connection_state, None, 500)),
            ('05_columns', 'Columns List (1000 max)', lambda: agent_policy.analysis_orch.list_columns_simple(connection_state, None, 1000)),
            ('06_relationships', 'Relationships', lambda: agent_policy.analysis_orch.list_relationships_simple(connection_state, False)),
            ('07_calculation_groups', 'Calculation Groups', lambda: agent_policy.analysis_orch.list_calculation_groups_simple(connection_state)),
            ('08_roles', 'Security Roles', lambda: agent_policy.analysis_orch.list_roles_simple(connection_state)),
        ]

        operations_results = {}

        # Execute each operation with prominent visual progress
        for idx, (op_id, op_name, op_func) in enumerate(operations, 1):
            # PROMINENTLY show operation start
            execution_log.append(f'[{idx}/{len(operations)}] >>> EXECUTING: {op_name}')
            execution_log.append('-' * 80)

            op_start = time.time()
            logger.info(f'[{idx}/{len(operations)}] Executing {op_name}')

            # Execute operation
            op_result = op_func()
            op_time = round(time.time() - op_start, 3)

            # Generate operation-specific analysis summary
            op_analysis = _generate_operation_analysis(op_id, op_result)

            # Add analysis summary and timing to operation result
            op_result_enhanced = dict(op_result)
            op_result_enhanced['execution_time_seconds'] = op_time
            op_result_enhanced['analysis_summary'] = op_analysis

            # Store enhanced result
            operations_results[op_id] = op_result_enhanced

            # PROMINENTLY show operation completion with details
            if op_result.get('success'):
                # Extract key metrics from result
                if op_id == '01_database':
                    db_data = op_result.get('data', [{}])[0]
                    msg = f"[OK] SUCCESS: {db_data.get('name', 'N/A')} (Compatibility: {db_data.get('compatibilityLevel', 0)})"
                    execution_log.append(msg)
                elif op_id == '02_stats':
                    counts = op_result.get('counts', {})
                    msg = f"[OK] SUCCESS: {counts.get('tables', 0)} tables, {counts.get('measures', 0)} measures, {counts.get('columns', 0)} columns"
                    execution_log.append(msg)
                elif op_id == '03_tables':
                    table_count = op_result.get('table_count', 0)
                    msg = f"[OK] SUCCESS: Found {table_count} tables"
                    execution_log.append(msg)
                elif op_id == '04_measures':
                    data = op_result.get('data', [])
                    msg = f"[OK] SUCCESS: Retrieved {len(data)} measures"
                    execution_log.append(msg)
                elif op_id == '05_columns':
                    data = op_result.get('data', [])
                    col_count = sum(len(t.get('columns', [])) for t in data)
                    msg = f"[OK] SUCCESS: Retrieved {col_count} columns across {len(data)} tables"
                    execution_log.append(msg)
                elif op_id == '06_relationships':
                    data = op_result.get('data', [])
                    msg = f"[OK] SUCCESS: Found {len(data)} relationships"
                    execution_log.append(msg)
                elif op_id == '07_calculation_groups':
                    data = op_result.get('data', [])
                    total_items = sum(len(cg.get('calculationItems', [])) for cg in data)
                    msg = f"[OK] SUCCESS: Found {len(data)} calculation groups with {total_items} items"
                    execution_log.append(msg)
                elif op_id == '08_roles':
                    data = op_result.get('data', [])
                    msg = f"[OK] SUCCESS: Found {len(data)} security roles"
                    execution_log.append(msg)
                else:
                    msg = f"[OK] SUCCESS: Operation completed"
                    execution_log.append(msg)

                # Add DETAILED analysis insights to execution log
                execution_log.append("")
                execution_log.append(f"   === ANALYSIS SUMMARY FOR {op_name.upper()} ===")

                if op_analysis.get('key_findings'):
                    execution_log.append("   Key Findings:")
                    for finding in op_analysis['key_findings']:
                        execution_log.append(f"     * {finding}")

                if op_analysis.get('insights'):
                    execution_log.append("   Insights:")
                    for insight in op_analysis['insights']:
                        execution_log.append(f"     - {insight}")

                if op_analysis.get('recommendations'):
                    execution_log.append("   Recommendations:")
                    for rec in op_analysis['recommendations']:
                        execution_log.append(f"     ! {rec}")

                execution_log.append(f"   [TIME] Execution time: {op_time}s")
                execution_log.append("   " + "=" * 70)
            else:
                error_msg = op_result.get('error', 'Unknown error')
                execution_log.append(f"[FAIL] ERROR: {error_msg}")
                execution_log.append(f"   [TIME] Execution time: {op_time}s")
                logger.error(f'{op_name} FAILED: {error_msg}')

            execution_log.append('')  # Blank line for separation

        # Calculate total execution time
        execution_time = round(time.time() - start_time, 2)

        # Count successful operations
        successful = sum(1 for op in operations_results.values() if op.get('success'))

        # Add prominent execution summary
        execution_log.append('='*80)
        execution_log.append('EXECUTION SUMMARY')
        execution_log.append('='*80)
        execution_log.append(f'[OK] Successful operations: {successful}/{len(operations)}')
        execution_log.append(f'[TIME] Total execution time: {execution_time}s')
        execution_log.append(f'[AVG] Average time per operation: {round(execution_time/len(operations), 2)}s')
        execution_log.append('')

        # Generate detailed Power BI expert analysis
        execution_log.append('='*80)
        execution_log.append('GENERATING POWER BI EXPERT ANALYSIS')
        execution_log.append('='*80)

        temp_results = {'operations': operations_results}
        analysis = agent_policy.analysis_orch.generate_expert_analysis(temp_results)

        execution_log.append('[OK] Expert analysis complete!')
        execution_log.append('')

        # Build final response with execution log at the TOP for prominence
        # CRITICAL: Format execution_log as a string so AI displays it properly
        formatted_execution_output = '\n'.join(execution_log)

        results = {
            'success': True,
            'mode': 'all',
            'operations_count': 8,
            'successful_operations': successful,
            'execution_time_seconds': execution_time,

            # FORMATTED OUTPUT - This is what the AI should show to the user
            # Single string containing the complete operation-by-operation breakdown
            'formatted_output': formatted_execution_output,

            # IMPORTANT: Show this message FIRST to direct the AI to display formatted_output
            'message': f'Completed {successful}/{len(operations)} Microsoft MCP operations. OPERATION-BY-OPERATION RESULTS (see formatted_output below):',

            # Raw execution log (array of strings) - kept for backward compatibility
            'execution_log': execution_log,

            # Individual operation results (optimized Microsoft MCP format)
            'operations': operations_results,

            # Expert analysis
            'expert_analysis': analysis,

            # Summary (high-level only)
            'summary': f'Successfully executed {successful}/{len(operations)} operations in {execution_time}s with detailed expert analysis and operation-by-operation breakdowns'
        }

        return results

    # Route to appropriate function based on mode
    if mode == 'tables':
        result = agent_policy.analysis_orch.list_tables_simple(connection_state)
    elif mode == 'stats':
        result = agent_policy.analysis_orch.simple_model_analysis(connection_state)
    elif mode == 'measures':
        # Measure List operation
        table_name = args.get('table')
        max_results = args.get('max_results')
        result = agent_policy.analysis_orch.list_measures_simple(connection_state, table_name, max_results)
    elif mode == 'measure':
        # Measure Get operation - requires table and measure_name
        table_name = args.get('table')
        measure_name = args.get('measure_name')
        if not table_name or not measure_name:
            return {
                'success': False,
                'error': 'mode="measure" requires both table and measure_name parameters'
            }
        result = agent_policy.analysis_orch.get_measure_simple(connection_state, table_name, measure_name)
    elif mode == 'columns':
        # Column List operation
        table_name = args.get('table')
        max_results = args.get('max_results')
        result = agent_policy.analysis_orch.list_columns_simple(connection_state, table_name, max_results)
    elif mode == 'relationships':
        # Relationship List operation
        active_only = args.get('active_only', False)
        result = agent_policy.analysis_orch.list_relationships_simple(connection_state, active_only)
    elif mode == 'roles':
        # Role List operation
        result = agent_policy.analysis_orch.list_roles_simple(connection_state)
    elif mode == 'database':
        # Database List operation
        result = agent_policy.analysis_orch.list_databases_simple(connection_state)
    elif mode == 'calculation_groups':
        # Calculation Group ListGroups operation
        result = agent_policy.analysis_orch.list_calculation_groups_simple(connection_state)
    else:
        return {
            'success': False,
            'error': f'Unknown mode: {mode}. Valid modes: all, tables, stats, measures, measure, columns, relationships, roles, database, calculation_groups'
        }

    return result

def handle_full_analysis(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified comprehensive model analysis combining best practices, performance, and integrity.

    Formerly known as comprehensive_analysis.
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    agent_policy = connection_state.agent_policy
    if not agent_policy:
        return ErrorHandler.handle_manager_unavailable('agent_policy')

    # Extract parameters with defaults
    scope = args.get('scope', 'all')
    depth = args.get('depth', 'balanced')
    include_bpa = args.get('include_bpa', True)
    include_performance = args.get('include_performance', True)
    include_integrity = args.get('include_integrity', True)
    max_seconds = args.get('max_seconds', None)

    # Run the analysis
    result = agent_policy.analysis_orch.comprehensive_analysis(
        connection_state,
        scope=scope,
        depth=depth,
        include_bpa=include_bpa,
        include_performance=include_performance,
        include_integrity=include_integrity,
        max_seconds=max_seconds
    )

    # Enrich issues with business impact context
    if result.get('success') and result.get('issues'):
        try:
            enriched_issues = []
            for issue in result['issues']:
                enriched_issue = enrich_issue_with_impact(issue)
                enriched_issues.append(enriched_issue)

            result['issues'] = enriched_issues

            # Add overall impact summary
            result = add_impact_summary(result)

        except Exception as e:
            logger.error(f"Error enriching issues with business impact: {e}", exc_info=True)
            # Don't fail the analysis if enrichment fails

    return result

def register_analysis_handlers(registry):
    """Register all analysis handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="simple_analysis",
            description="Fast Microsoft MCP operations with Power BI expert analysis: Runs 8 core operations (database, stats, tables, measures, columns, relationships, calculation groups, roles) + generates detailed insights and recommendations",
            handler=handle_simple_analysis,
            input_schema=TOOL_SCHEMAS.get('simple_analysis', {}),
            category="analysis",
            sort_order=26
        ),
        ToolDefinition(
            name="full_analysis",
            description="Comprehensive analysis: best practices (BPA), performance, and integrity validation (10-180s)",
            handler=handle_full_analysis,
            input_schema=TOOL_SCHEMAS.get('full_analysis', {}),
            category="analysis",
            sort_order=27
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} analysis handlers")
