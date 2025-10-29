"""
Performance Tracing Handler
Handles advanced performance analysis with SE/FE breakdown, query plans, and batch profiling
"""
from typing import Dict, Any
import logging
import os
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


def handle_profile_query_detailed(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform detailed query performance analysis with SE/FE breakdown.

    Uses AMO/XMLA tracing to provide Storage Engine vs Formula Engine timing,
    event counts, and visualization data for waterfall charts.
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    query_executor = connection_state.query_executor
    if not query_executor:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    query = args.get('query')
    if not query:
        return {'success': False, 'error': 'query parameter required'}

    runs = args.get('runs', 3)
    clear_cache = args.get('clear_cache', True)
    capture_query_plan = args.get('capture_query_plan', False)
    export_html = args.get('export_html', False)
    export_path = args.get('export_path')

    try:
        # Import performance analyzer v2
        from core.performance.performance_analyzer_v2 import PerformanceAnalyzerV2

        # Create analyzer
        connection_string = query_executor.connection.ConnectionString
        analyzer = PerformanceAnalyzerV2(connection_string, query_executor)

        # Analyze query
        result = analyzer.analyze_query_detailed(
            query=query,
            runs=runs,
            clear_cache=clear_cache,
            capture_query_plan=capture_query_plan,
            event_timeout=30.0,
        )

        # Export HTML visualization if requested
        if export_html and result.get('success'):
            try:
                from core.performance.performance_visualizer import PerformanceVisualizer
                visualizer = PerformanceVisualizer()

                html_content = visualizer.generate_waterfall_chart(result)

                if export_path:
                    # Use provided path
                    output_path = export_path
                else:
                    # Default to exports directory
                    exports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'exports')
                    os.makedirs(exports_dir, exist_ok=True)
                    output_path = os.path.join(exports_dir, 'performance_analysis.html')

                visualizer.export_visualization(html_content, output_path)
                result['visualization_exported'] = True
                result['visualization_path'] = output_path

            except Exception as exc:
                logger.warning(f"Failed to export visualization: {exc}")
                result['visualization_exported'] = False
                result['visualization_error'] = str(exc)

        # Cleanup
        analyzer.close()

        return result

    except Exception as exc:
        logger.error(f"Detailed query profiling failed: {exc}")
        return {
            'success': False,
            'error': f'Performance analysis failed: {str(exc)}'
        }


def handle_batch_profile_queries(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Profile multiple queries in a single trace session.

    Provides comparative analysis and identifies performance bottlenecks
    across multiple queries.
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    query_executor = connection_state.query_executor
    if not query_executor:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    queries = args.get('queries')
    if not queries or not isinstance(queries, list):
        return {
            'success': False,
            'error': 'queries parameter required (list of {name, query} objects)'
        }

    runs_per_query = args.get('runs_per_query', 1)
    clear_cache = args.get('clear_cache', True)
    export_html = args.get('export_html', False)
    export_path = args.get('export_path')

    try:
        # Import performance analyzer v2
        from core.performance.performance_analyzer_v2 import PerformanceAnalyzerV2

        # Create analyzer
        connection_string = query_executor.connection.ConnectionString
        analyzer = PerformanceAnalyzerV2(connection_string, query_executor)

        # Batch profile queries
        result = analyzer.batch_profile_queries(
            queries=queries,
            runs_per_query=runs_per_query,
            clear_cache=clear_cache,
        )

        # Export HTML report if requested
        if export_html and result.get('success'):
            try:
                from core.performance.performance_visualizer import PerformanceVisualizer
                visualizer = PerformanceVisualizer()

                html_content = visualizer.generate_batch_profiling_report(result)

                if export_path:
                    output_path = export_path
                else:
                    exports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'exports')
                    os.makedirs(exports_dir, exist_ok=True)
                    output_path = os.path.join(exports_dir, 'batch_profiling_report.html')

                visualizer.export_visualization(html_content, output_path)
                result['visualization_exported'] = True
                result['visualization_path'] = output_path

            except Exception as exc:
                logger.warning(f"Failed to export visualization: {exc}")
                result['visualization_exported'] = False
                result['visualization_error'] = str(exc)

        # Cleanup
        analyzer.close()

        return result

    except Exception as exc:
        logger.error(f"Batch query profiling failed: {exc}")
        return {
            'success': False,
            'error': f'Batch profiling failed: {str(exc)}'
        }


def handle_compare_query_performance(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare performance of two query versions (before/after optimization).

    Provides side-by-side comparison with improvement metrics and verdict.
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    query_executor = connection_state.query_executor
    if not query_executor:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    query_before = args.get('query_before')
    query_after = args.get('query_after')

    if not query_before or not query_after:
        return {
            'success': False,
            'error': 'Both query_before and query_after parameters required'
        }

    runs = args.get('runs', 3)
    export_html = args.get('export_html', False)
    export_path = args.get('export_path')

    try:
        # Import performance analyzer v2
        from core.performance.performance_analyzer_v2 import PerformanceAnalyzerV2

        # Create analyzer
        connection_string = query_executor.connection.ConnectionString
        analyzer = PerformanceAnalyzerV2(connection_string, query_executor)

        # Compare queries
        result = analyzer.compare_query_performance(
            query_before=query_before,
            query_after=query_after,
            runs=runs,
        )

        # Export HTML comparison if requested
        if export_html and result.get('success'):
            try:
                from core.performance.performance_visualizer import PerformanceVisualizer
                visualizer = PerformanceVisualizer()

                html_content = visualizer.generate_comparison_chart(result)

                if export_path:
                    output_path = export_path
                else:
                    exports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'exports')
                    os.makedirs(exports_dir, exist_ok=True)
                    output_path = os.path.join(exports_dir, 'performance_comparison.html')

                visualizer.export_visualization(html_content, output_path)
                result['visualization_exported'] = True
                result['visualization_path'] = output_path

            except Exception as exc:
                logger.warning(f"Failed to export visualization: {exc}")
                result['visualization_exported'] = False
                result['visualization_error'] = str(exc)

        # Cleanup
        analyzer.close()

        return result

    except Exception as exc:
        logger.error(f"Performance comparison failed: {exc}")
        return {
            'success': False,
            'error': f'Performance comparison failed: {str(exc)}'
        }


def handle_analyze_query_plan(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze query execution plan and identify bottlenecks.

    NOTE: Query plan analysis has limited support in Power BI Desktop.
    Full query plan details are only available in SQL Server Analysis Services.
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    query_executor = connection_state.query_executor
    if not query_executor:
        return ErrorHandler.handle_manager_unavailable('query_executor')

    query = args.get('query')
    if not query:
        return {'success': False, 'error': 'query parameter required'}

    try:
        # Import analyzers
        from core.performance.performance_analyzer_v2 import PerformanceAnalyzerV2
        from core.performance.query_plan_analyzer import QueryPlanAnalyzer

        # Create performance analyzer with trace
        connection_string = query_executor.connection.ConnectionString
        perf_analyzer = PerformanceAnalyzerV2(connection_string, query_executor)

        # Analyze query with plan capture
        result = perf_analyzer.analyze_query_detailed(
            query=query,
            runs=1,
            clear_cache=True,
            capture_query_plan=True,
            event_timeout=30.0,
        )

        if not result.get('success'):
            return result

        # Get trace events for plan analysis
        trace_mgr = perf_analyzer._get_trace_manager()
        if not trace_mgr:
            return {
                'success': False,
                'error': 'Query plan analysis requires trace support (AMO/XMLA)',
                'note': 'Power BI Desktop has limited query plan support. Use DAX Studio for full query plan analysis.'
            }

        # Analyze query plan
        plan_analyzer = QueryPlanAnalyzer()
        trace_events = trace_mgr.get_events() if hasattr(trace_mgr, 'get_events') else []

        plan_analysis = plan_analyzer.analyze_query_plan(trace_events)

        if not plan_analysis:
            return {
                'success': True,
                'has_plan': False,
                'message': 'No query plan data captured. Power BI Desktop provides limited query plan information.',
                'note': 'For detailed query plan analysis, use SQL Server Analysis Services or DAX Studio.',
                'performance_summary': result.get('summary', {}),
            }

        # Add visualization data
        plan_analysis['visualization'] = plan_analyzer.generate_plan_tree_visualization(plan_analysis)

        # Cleanup
        perf_analyzer.close()

        return {
            'success': True,
            'has_plan': True,
            'query_plan': plan_analysis,
            'performance_summary': result.get('summary', {}),
        }

    except Exception as exc:
        logger.error(f"Query plan analysis failed: {exc}")
        return {
            'success': False,
            'error': f'Query plan analysis failed: {str(exc)}'
        }


def register_performance_tracing_handlers(registry):
    """Register all performance tracing handlers"""
    tools = [
        ToolDefinition(
            name="profile_query_detailed",
            description="Detailed query performance analysis with SE/FE breakdown, timing metrics, and optional HTML visualization",
            handler=handle_profile_query_detailed,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "DAX query to analyze"
                    },
                    "runs": {
                        "type": "integer",
                        "description": "Number of execution runs (default: 3)",
                        "default": 3
                    },
                    "clear_cache": {
                        "type": "boolean",
                        "description": "Clear cache before first run (default: true)",
                        "default": True
                    },
                    "capture_query_plan": {
                        "type": "boolean",
                        "description": "Capture query plan if available (default: false)",
                        "default": False
                    },
                    "export_html": {
                        "type": "boolean",
                        "description": "Export results as HTML visualization (default: false)",
                        "default": False
                    },
                    "export_path": {
                        "type": "string",
                        "description": "Optional path for HTML export (default: exports/performance_analysis.html)"
                    }
                },
                "required": ["query"]
            },
            category="performance",
            sort_order=50
        ),
        ToolDefinition(
            name="batch_profile_queries",
            description="Profile multiple queries in one session with comparative analysis and bottleneck identification",
            handler=handle_batch_profile_queries,
            input_schema={
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "description": "List of queries to profile, each with 'name' and 'query' fields",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "query": {"type": "string"}
                            },
                            "required": ["name", "query"]
                        }
                    },
                    "runs_per_query": {
                        "type": "integer",
                        "description": "Runs per query (default: 1)",
                        "default": 1
                    },
                    "clear_cache": {
                        "type": "boolean",
                        "description": "Clear cache before each query (default: true)",
                        "default": True
                    },
                    "export_html": {
                        "type": "boolean",
                        "description": "Export batch report as HTML (default: false)",
                        "default": False
                    },
                    "export_path": {
                        "type": "string",
                        "description": "Optional path for HTML export"
                    }
                },
                "required": ["queries"]
            },
            category="performance",
            sort_order=51
        ),
        ToolDefinition(
            name="compare_query_performance",
            description="Compare two query versions (before/after) with improvement metrics and performance verdict",
            handler=handle_compare_query_performance,
            input_schema={
                "type": "object",
                "properties": {
                    "query_before": {
                        "type": "string",
                        "description": "Original query (before optimization)"
                    },
                    "query_after": {
                        "type": "string",
                        "description": "Optimized query (after optimization)"
                    },
                    "runs": {
                        "type": "integer",
                        "description": "Number of runs per query (default: 3)",
                        "default": 3
                    },
                    "export_html": {
                        "type": "boolean",
                        "description": "Export comparison as HTML (default: false)",
                        "default": False
                    },
                    "export_path": {
                        "type": "string",
                        "description": "Optional path for HTML export"
                    }
                },
                "required": ["query_before", "query_after"]
            },
            category="performance",
            sort_order=52
        ),
        ToolDefinition(
            name="analyze_query_plan",
            description="Analyze query execution plan to identify table scans, joins, aggregations, and bottlenecks (limited support in Desktop)",
            handler=handle_analyze_query_plan,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "DAX query to analyze"
                    }
                },
                "required": ["query"]
            },
            category="performance",
            sort_order=53
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} performance tracing tools")
