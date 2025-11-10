"""
Export Handler
Handles TMSL, TMDL, and schema export operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler

logger = logging.getLogger(__name__)

def handle_export_tmsl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export TMSL definition"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    file_path = args.get('file_path')

    return model_exporter.export_tmsl(file_path)

def handle_export_tmdl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export TMDL definition"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    output_dir = args.get('output_dir')

    return model_exporter.export_tmdl(output_dir)

def handle_export_model_schema(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export model schema by section"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    model_exporter = connection_state.model_exporter
    if not model_exporter:
        return ErrorHandler.handle_manager_unavailable('model_exporter')

    section = args.get('section', 'all')
    output_path = args.get('output_path')

    return model_exporter.export_schema(section, output_path)

def handle_analyze_model_for_ai(args: Dict[str, Any]) -> Dict[str, Any]:
    """Export complete Power BI model in AI-optimized format for comprehensive analysis"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    # Import AIModelExporter
    try:
        from core.model.ai_exporter import AIModelExporter
    except ImportError as e:
        return {'success': False, 'error': f'AI exporter not available: {e}'}

    # Get connection from connection manager
    connection = connection_state.connection_manager.get_connection()
    if not connection:
        return {'success': False, 'error': 'No active connection available'}

    # Create exporter with connection and managers
    exporter = AIModelExporter(
        connection=connection,
        query_executor=connection_state.query_executor,
        calculation_group_manager=connection_state.calc_group_manager
    )

    # Get parameters
    output_format = args.get('output_format', 'json_gzip')
    sample_rows = args.get('sample_rows', 20)
    include_sample_data = args.get('include_sample_data', True)
    include_dependencies = args.get('include_dependencies', True)
    include_bpa_issues = args.get('include_bpa_issues', False)
    include_dax_patterns = args.get('include_dax_patterns', True)
    output_path = args.get('output_path')

    # Export
    result = exporter.export_for_ai(
        output_format=output_format,
        sample_rows=sample_rows,
        include_sample_data=include_sample_data,
        include_dependencies=include_dependencies,
        include_bpa_issues=include_bpa_issues,
        include_dax_patterns=include_dax_patterns,
        output_path=output_path
    )

    # Add user prompt to result if export was successful
    if result.get('success'):
        result['user_prompt'] = {
            'message': f"""
Model export completed successfully!

Export Details:
- Format: {result.get('format', 'N/A')}
- File: {result.get('export_file', 'N/A')}
- Size: {result.get('file_size_mb', 0)} MB
- Export Time: {result.get('export_time_seconds', 0)}s

This comprehensive export includes:
- All measures with DAX expressions
- Measure dependencies (upstream/downstream)
- Tables and columns with full metadata
- Sample data ({sample_rows} rows per table)
- Relationships
- Calculation groups
- Row-level security rules
- DAX pattern detection

Would you like me to analyze this export for:
1. Model optimization opportunities
2. DAX performance improvements
3. Data model best practices
4. Relationship and cardinality issues
5. Security and RLS recommendations
6. Overall model health assessment

Or would you prefer a specific type of analysis?
""",
            'export_path': result.get('export_file'),
            'suggested_actions': [
                'Analyze for model optimization',
                'Review DAX measures for performance',
                'Check data model best practices',
                'Audit relationships and cardinality',
                'Review security and RLS setup',
                'Generate comprehensive model report'
            ]
        }

    return result

def register_export_handlers(registry):
    """Register all export handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="export_model_schema",
            description="Export model schema by section",
            handler=handle_export_model_schema,
            input_schema=TOOL_SCHEMAS.get('export_model_schema', {}),
            category="export",
            sort_order=34
        ),
        ToolDefinition(
            name="export_tmsl",
            description="Export TMSL definition",
            handler=handle_export_tmsl,
            input_schema=TOOL_SCHEMAS.get('export_tmsl', {}),
            category="export",
            sort_order=35
        ),
        ToolDefinition(
            name="export_tmdl",
            description="Export TMDL definition",
            handler=handle_export_tmdl,
            input_schema=TOOL_SCHEMAS.get('export_tmdl', {}),
            category="export",
            sort_order=36
        ),
        ToolDefinition(
            name="analyze_model_for_ai",
            description="Export complete Power BI model in AI-optimized format for comprehensive analysis. Includes all measures with DAX, dependencies, sample data, relationships, calculation groups, and more. Perfect for AI-driven model optimization, DAX analysis, and comprehensive model review.",
            handler=handle_analyze_model_for_ai,
            input_schema=TOOL_SCHEMAS.get('analyze_model_for_ai', {}),
            category="export",
            sort_order=33
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} export handlers")
