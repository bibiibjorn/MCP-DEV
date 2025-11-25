"""
Dependencies Handler
Handles measure dependency analysis with professional formatted output
"""
from typing import Dict, Any, List, Tuple
import logging
from server.registry import ToolDefinition
from core.infrastructure.connection_state import connection_state
from core.validation.error_handler import ErrorHandler
from core.utilities.mermaid_renderer import get_mermaid_image_content

logger = logging.getLogger(__name__)


def _format_dependency_analysis_output(
    table: str,
    measure: str,
    deps_result: Dict[str, Any],
    diagram_result: Dict[str, Any] = None
) -> str:
    """
    Format dependency analysis into a professional, readable output.

    Returns a formatted string with clear sections for:
    - Header with measure identification
    - Summary statistics
    - Dependencies breakdown by category
    - Mermaid diagram (if available)
    """
    lines = []

    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    lines.append("═" * 80)
    lines.append("  MEASURE DEPENDENCY ANALYSIS")
    lines.append("═" * 80)
    lines.append("")
    lines.append(f"  Measure: {table}[{measure}]")
    lines.append("")

    # ───────────────────────────────────────────────────────────────────────────
    # SUMMARY STATISTICS
    # ───────────────────────────────────────────────────────────────────────────
    ref_measures = deps_result.get('referenced_measures', [])
    ref_columns = deps_result.get('referenced_columns', [])
    ref_tables = deps_result.get('referenced_tables', [])

    lines.append("─" * 80)
    lines.append("  SUMMARY")
    lines.append("─" * 80)
    lines.append("")
    lines.append(f"  ┌─────────────────────────────────────────────────────────────────┐")
    lines.append(f"  │  Referenced Measures:  {len(ref_measures):>4}                                      │")
    lines.append(f"  │  Referenced Columns:   {len(ref_columns):>4}                                      │")
    lines.append(f"  │  Referenced Tables:    {len(ref_tables):>4}                                      │")
    lines.append(f"  │  Total Dependencies:   {len(ref_measures) + len(ref_columns):>4}                                      │")
    lines.append(f"  └─────────────────────────────────────────────────────────────────┘")
    lines.append("")

    # ───────────────────────────────────────────────────────────────────────────
    # MEASURE EXPRESSION
    # ───────────────────────────────────────────────────────────────────────────
    expression = deps_result.get('expression', '')
    if expression:
        lines.append("─" * 80)
        lines.append("  DAX EXPRESSION")
        lines.append("─" * 80)
        lines.append("")
        # Format expression with indentation
        for expr_line in expression.split('\n'):
            lines.append(f"    {expr_line}")
        lines.append("")

    # ───────────────────────────────────────────────────────────────────────────
    # REFERENCED MEASURES
    # ───────────────────────────────────────────────────────────────────────────
    if ref_measures:
        lines.append("─" * 80)
        lines.append(f"  REFERENCED MEASURES ({len(ref_measures)})")
        lines.append("─" * 80)
        lines.append("")

        # Group by table
        measures_by_table: Dict[str, List[str]] = {}
        for tbl, msr in ref_measures:
            if tbl not in measures_by_table:
                measures_by_table[tbl] = []
            measures_by_table[tbl].append(msr)

        for tbl, measures in sorted(measures_by_table.items()):
            lines.append(f"    {tbl}")
            for msr in sorted(measures):
                lines.append(f"      ├── [{msr}]")
        lines.append("")

    # ───────────────────────────────────────────────────────────────────────────
    # REFERENCED COLUMNS
    # ───────────────────────────────────────────────────────────────────────────
    if ref_columns:
        lines.append("─" * 80)
        lines.append(f"  REFERENCED COLUMNS ({len(ref_columns)})")
        lines.append("─" * 80)
        lines.append("")

        # Group by table
        columns_by_table: Dict[str, List[str]] = {}
        for tbl, col in ref_columns:
            if tbl not in columns_by_table:
                columns_by_table[tbl] = []
            columns_by_table[tbl].append(col)

        for tbl, columns in sorted(columns_by_table.items()):
            lines.append(f"    {tbl}")
            for col in sorted(columns):
                lines.append(f"      ├── [{col}]")
        lines.append("")

    # ───────────────────────────────────────────────────────────────────────────
    # REFERENCED TABLES
    # ───────────────────────────────────────────────────────────────────────────
    if ref_tables:
        lines.append("─" * 80)
        lines.append(f"  REFERENCED TABLES ({len(ref_tables)})")
        lines.append("─" * 80)
        lines.append("")
        for tbl in sorted(ref_tables):
            lines.append(f"    • {tbl}")
        lines.append("")

    # ───────────────────────────────────────────────────────────────────────────
    # DEPENDENCY TREE PREVIEW
    # ───────────────────────────────────────────────────────────────────────────
    dep_tree = deps_result.get('dependency_tree')
    if dep_tree:
        lines.append("─" * 80)
        lines.append("  DEPENDENCY TREE (depth: 3)")
        lines.append("─" * 80)
        lines.append("")
        _format_tree_node(dep_tree, lines, indent=4, is_last=True)
        lines.append("")

    # ═══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════════════════
    lines.append("═" * 80)

    return "\n".join(lines)


def _format_tree_node(node: Dict[str, Any], lines: List[str], indent: int = 0, is_last: bool = True) -> None:
    """Recursively format a dependency tree node."""
    prefix = " " * indent
    connector = "└── " if is_last else "├── "

    tbl = node.get('table', '')
    msr = node.get('measure', '')

    # Add node
    node_str = f"{tbl}[{msr}]"
    if node.get('circular'):
        node_str += " (circular reference)"
    if node.get('max_depth_reached'):
        node_str += " (max depth)"
    if node.get('error'):
        node_str += f" (error: {node['error']})"

    lines.append(f"{prefix}{connector}{node_str}")

    # Process children
    children = node.get('dependencies', [])
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        child_indent = indent + 4
        _format_tree_node(child, lines, child_indent, is_last_child)


def _generate_mermaid_markdown(diagram_result: Dict[str, Any], table: str, measure: str) -> str:
    """
    Generate a complete Mermaid diagram in markdown format.
    This is returned as a SEPARATE response item for proper rendering.
    """
    if not diagram_result or not diagram_result.get('success'):
        return ""

    mermaid_code = diagram_result.get('mermaid', '')
    if not mermaid_code:
        return ""

    lines = []
    lines.append("")
    lines.append("═" * 80)
    lines.append("  DEPENDENCY DIAGRAM")
    lines.append("═" * 80)
    lines.append("")
    lines.append(f"  Measure: {table}[{measure}]")
    lines.append(f"  Direction: {diagram_result.get('direction', 'upstream')}")
    lines.append(f"  Depth: {diagram_result.get('depth', 3)}")
    lines.append(f"  Nodes: {diagram_result.get('node_count', 0)}")
    lines.append(f"  Edges: {diagram_result.get('edge_count', 0)}")
    lines.append("")
    lines.append("─" * 80)
    lines.append("")
    lines.append("```mermaid")
    lines.append(mermaid_code)
    lines.append("```")
    lines.append("")
    lines.append("─" * 80)
    lines.append("  Legend:")
    lines.append("    • Blue boxes = Measures")
    lines.append("    • Purple boxes = Columns")
    lines.append("    • Orange boxes = Table subgraphs")
    lines.append("    • Arrows show dependency flow (dependency → consumer)")
    lines.append("─" * 80)

    return "\n".join(lines)


def handle_analyze_measure_dependencies(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze measure dependencies tree with professional formatted output.

    Returns a structured response with:
    - formatted_output: Professional text-based analysis summary
    - mermaid_diagram_output: Separate markdown block with Mermaid diagram
    - Raw data fields for programmatic access
    """
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    dependency_analyzer = connection_state.dependency_analyzer
    if not dependency_analyzer:
        return ErrorHandler.handle_manager_unavailable('dependency_analyzer')

    table = args.get('table')
    measure = args.get('measure')
    include_diagram = args.get('include_diagram', True)  # Default to True

    if not table or not measure:
        return {
            'success': False,
            'error': 'table and measure parameters are required'
        }

    # Get the base dependency analysis
    deps_result = dependency_analyzer.analyze_dependencies(table, measure, include_diagram=False)

    if not deps_result.get('success'):
        return deps_result

    # Get the Mermaid diagram separately if requested
    diagram_result = None
    if include_diagram:
        diagram_result = dependency_analyzer.generate_dependency_mermaid(
            table, measure, direction="upstream", depth=3, include_columns=True
        )

    # Generate formatted outputs
    formatted_analysis = _format_dependency_analysis_output(table, measure, deps_result, diagram_result)
    mermaid_output = _generate_mermaid_markdown(diagram_result, table, measure) if include_diagram else ""

    # Build the response with clear separation
    response = {
        'success': True,
        'measure': {'table': table, 'name': measure},

        # PRIMARY OUTPUT - Text analysis (display this first)
        'formatted_output': formatted_analysis,

        # DIAGRAM OUTPUT - Separate markdown with Mermaid (display after analysis)
        'mermaid_diagram_output': mermaid_output,

        # Instruction for AI/client on how to display
        'display_instructions': 'Display formatted_output first, then mermaid_diagram_output as a separate code block.',

        # Raw data for programmatic access
        'expression': deps_result.get('expression', ''),
        'referenced_measures': deps_result.get('referenced_measures', []),
        'referenced_columns': deps_result.get('referenced_columns', []),
        'referenced_tables': deps_result.get('referenced_tables', []),
        'dependency_tree': deps_result.get('dependency_tree'),

        # Summary stats
        'summary': {
            'measure_count': len(deps_result.get('referenced_measures', [])),
            'column_count': len(deps_result.get('referenced_columns', [])),
            'table_count': len(deps_result.get('referenced_tables', [])),
            'total_dependencies': len(deps_result.get('referenced_measures', [])) + len(deps_result.get('referenced_columns', []))
        }
    }

    # Include raw mermaid code for clients that want to render it themselves
    if diagram_result and diagram_result.get('success'):
        mermaid_code = diagram_result.get('mermaid', '')
        response['mermaid_raw'] = mermaid_code
        response['diagram_metadata'] = {
            'direction': diagram_result.get('direction', 'upstream'),
            'depth': diagram_result.get('depth', 3),
            'node_count': diagram_result.get('node_count', 0),
            'edge_count': diagram_result.get('edge_count', 0)
        }

        # Render Mermaid diagram to PNG image for visual display
        # The _image_content field triggers special handling in the MCP server
        # to return the image as ImageContent alongside the text response
        if mermaid_code:
            image_result = get_mermaid_image_content(mermaid_code, theme="default")
            if image_result.get('success'):
                response['_image_content'] = {
                    'data': image_result['data'],
                    'mimeType': image_result['mimeType']
                }
                # Include mermaid code for HTML generation
                response['_mermaid_code'] = mermaid_code
                # Remove text-based mermaid output
                if 'mermaid_diagram_output' in response:
                    del response['mermaid_diagram_output']
                if 'mermaid_raw' in response:
                    del response['mermaid_raw']
                response['display_instructions'] = 'Interactive diagram will open in browser.'
                response['diagram_rendered'] = True
                logger.info("Mermaid diagram ready for HTML generation")
            else:
                # If image rendering fails, log it but continue with text output
                logger.warning(f"Mermaid image rendering failed: {image_result.get('error')}")
                response['image_render_error'] = image_result.get('error')

    return response

def handle_get_measure_impact(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get measure usage impact"""
    if not connection_state.is_connected():
        return ErrorHandler.handle_not_connected()

    dependency_analyzer = connection_state.dependency_analyzer
    if not dependency_analyzer:
        return ErrorHandler.handle_manager_unavailable('dependency_analyzer')

    table = args.get('table')
    measure = args.get('measure')

    if not table or not measure:
        return {
            'success': False,
            'error': 'table and measure parameters are required'
        }

    return dependency_analyzer.get_measure_impact(table, measure)

def register_dependencies_handlers(registry):
    """Register all dependency analysis handlers"""
    from server.tool_schemas import TOOL_SCHEMAS

    tools = [
        ToolDefinition(
            name="analyze_measure_dependencies",
            description="Analyze measure dependencies with formatted text output and rendered diagram image. Returns formatted_output (text analysis) and a visual dependency diagram as PNG image.",
            handler=handle_analyze_measure_dependencies,
            input_schema=TOOL_SCHEMAS.get('analyze_measure_dependencies', {}),
            category="dependencies",
            sort_order=22
        ),
        ToolDefinition(
            name="get_measure_impact",
            description="Get measure usage impact - shows what depends on this measure",
            handler=handle_get_measure_impact,
            input_schema=TOOL_SCHEMAS.get('get_measure_impact', {}),
            category="dependencies",
            sort_order=23
        ),
    ]

    for tool in tools:
        registry.register(tool)

    logger.info(f"Registered {len(tools)} dependency handlers")
