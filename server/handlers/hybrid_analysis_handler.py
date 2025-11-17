"""
Hybrid Analysis MCP Tool Handlers

Provides MCP tool handlers for hybrid analysis operations:
1. export_hybrid_analysis - Export PBIP model to hybrid format
2. analyze_hybrid_model - Analyze hybrid analysis package
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

from core.model.hybrid_analyzer import HybridAnalyzer
from core.model.hybrid_reader import HybridReader
from core.model.hybrid_intelligence import HybridIntelligence
from server.registry import ToolDefinition
from server.tool_schemas import TOOL_SCHEMAS

logger = logging.getLogger(__name__)


def handle_export_hybrid_analysis(
    pbip_folder_path: str,
    output_dir: Optional[str] = None,
    connection_string: Optional[str] = None,
    server: Optional[str] = None,
    database: Optional[str] = None,
    include_sample_data: bool = True,
    sample_rows: int = 1000,
    sample_compression: str = "snappy",
    include_row_counts: bool = True,
    track_column_usage: bool = True,
    track_cardinality: bool = True,
    tmdl_strategy: str = "symlink",
    progress_callback: bool = False
) -> Dict[str, Any]:
    """
    Export Power BI model to hybrid analysis format

    Combines:
    1. TMDL files from specified PBIP folder
    2. Live metadata + sample data from currently open Power BI file (auto-detected)

    Args:
        pbip_folder_path: Path to .SemanticModel folder (for TMDL files)
        output_dir: Optional output directory (defaults to same folder as PBIP with '_analysis' suffix)
        connection_string: Optional connection string (auto-detects if not provided)
        server: Alternative: server name
        database: Alternative: database name
        include_sample_data: Include sample data extraction
        sample_rows: Number of sample rows per table
        sample_compression: Compression for parquet files
        include_row_counts: Include row counts in metadata
        track_column_usage: Track column usage
        track_cardinality: Track cardinality info
        tmdl_strategy: "symlink" or "copy"
        progress_callback: Enable progress tracking

    Returns:
        Export result dictionary
    """
    try:
        # Validate PBIP folder
        pbip_path = Path(pbip_folder_path)
        if not pbip_path.exists():
            return {
                'success': False,
                'error': f'PBIP folder not found: {pbip_folder_path}',
                'error_type': 'not_found'
            }

        # Auto-determine output directory if not provided
        if not output_dir:
            # Use same parent folder as PBIP, add '_analysis' suffix
            model_name = pbip_path.stem.replace('.SemanticModel', '')
            output_dir = str(pbip_path.parent / f"{model_name}_analysis")
            logger.info(f"Output directory not specified, using: {output_dir}")

        logger.info(f"Starting hybrid analysis export:")
        logger.info(f"  - TMDL source: {pbip_folder_path}")
        logger.info(f"  - Output: {output_dir}")
        logger.info(f"  - Live data: Auto-detect from open Power BI file")

        # Initialize analyzer
        analyzer = HybridAnalyzer(
            pbip_folder_path=pbip_folder_path,
            output_dir=output_dir,
            connection_string=connection_string,
            server=server,
            database=database
        )

        # Perform export
        result = analyzer.export(
            include_sample_data=include_sample_data and analyzer.has_connection,
            sample_rows=sample_rows,
            sample_compression=sample_compression,
            include_row_counts=include_row_counts,
            track_column_usage=track_column_usage,
            track_cardinality=track_cardinality,
            tmdl_strategy=tmdl_strategy,
            progress_callback=None  # TODO: Implement progress callback
        )

        logger.info(f"Export completed successfully in {result['generation_time_seconds']}s")
        return result

    except Exception as e:
        logger.error(f"Error in export_hybrid_analysis: {str(e)}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': f"Export failed: {str(e)}",
            'error_type': 'export_error',
            'context': {
                'pbip_folder_path': pbip_folder_path,
                'output_dir': output_dir
            }
        }


def handle_analyze_hybrid_model(
    analysis_path: str,
    operation: str,
    intent: Optional[str] = None,
    object_filter: Optional[Dict[str, Any]] = None,
    format_type: str = "json",
    batch_size: int = 50,
    batch_number: int = 0,
    priority: Optional[str] = None,
    detailed: bool = False,
    include_dependencies: bool = False,
    include_sample_data: bool = False
) -> Dict[str, Any]:
    """
    Read and analyze hybrid analysis package

    Args:
        analysis_path: Path to exported analysis folder
        operation: Operation name or "smart_analyze"
        intent: Natural language intent (for smart_analyze)
        object_filter: Filter for objects
        format_type: "json" or "toon"
        batch_size: Results per page
        batch_number: Page number
        priority: Filter priority
        detailed: Include detailed analysis
        include_dependencies: Include dependency info
        include_sample_data: Include sample data

    Returns:
        Analysis result dictionary
    """
    try:
        logger.info(f"Analyzing hybrid model at: {analysis_path}, operation: {operation}")

        # Validate analysis path
        analysis_path_obj = Path(analysis_path)
        if not analysis_path_obj.exists():
            return {
                'success': False,
                'error': f'Analysis path not found: {analysis_path}',
                'error_type': 'not_found'
            }

        # Initialize reader
        reader = HybridReader(analysis_path)

        # Smart analyze mode - infer operation from intent
        actual_operation = operation
        inferred_params = {}
        if operation == "smart_analyze" and intent:
            actual_operation, inferred_params = HybridIntelligence.infer_operation(intent)
            logger.info(f"Smart analyze inferred: {actual_operation} with params {inferred_params}")

            # Merge inferred params with explicit params
            if not object_filter:
                object_filter = {}
            object_filter.update(inferred_params)

        # Execute operation
        result = None

        if actual_operation == "read_metadata":
            result = _operation_read_metadata(reader)

        elif actual_operation == "find_objects":
            result = _operation_find_objects(
                reader,
                object_filter or {},
                batch_size,
                batch_number
            )

        elif actual_operation == "get_object_definition":
            object_name = (object_filter or {}).get("object_name") or \
                         (object_filter or {}).get("name_pattern")
            object_type = (object_filter or {}).get("object_type", "measure")

            if not object_name:
                return {
                    'success': False,
                    'error': 'object_name required for get_object_definition',
                    'error_type': 'validation_error',
                    'context': {'object_filter': object_filter}
                }

            result = _operation_get_object_definition(
                reader,
                object_name,
                object_type
            )

        elif actual_operation == "analyze_dependencies":
            object_name = (object_filter or {}).get("object_name") or \
                         (object_filter or {}).get("name_pattern")

            if not object_name:
                return {
                    'success': False,
                    'error': 'object_name required for analyze_dependencies',
                    'error_type': 'validation_error',
                    'context': {'object_filter': object_filter}
                }

            result = _operation_analyze_dependencies(
                reader,
                object_name,
                "both"
            )

        elif actual_operation == "get_sample_data":
            table_name = (object_filter or {}).get("table") or \
                        (object_filter or {}).get("table_name")

            if not table_name:
                return {
                    'success': False,
                    'error': 'table_name required for get_sample_data',
                    'error_type': 'validation_error',
                    'context': {'object_filter': object_filter}
                }

            result = _operation_get_sample_data(
                reader,
                table_name,
                batch_size
            )

        elif actual_operation == "analyze_performance":
            result = _operation_analyze_performance(
                reader,
                priority,
                detailed
            )

        else:
            return {
                'success': False,
                'error': f'Unknown operation: {actual_operation}',
                'error_type': 'invalid_operation',
                'context': {'operation': operation}
            }

        # Apply TOON format if needed
        estimated_tokens = HybridIntelligence.estimate_tokens(result)
        result_count = result.get("count", 0)

        if format_type == "toon" or HybridIntelligence.should_use_toon_format(result_count, estimated_tokens):
            format_type = "toon"
            result = HybridIntelligence.convert_to_toon_format(result)

        # Add guidance
        guidance = HybridIntelligence.generate_guidance(
            actual_operation,
            result,
            intent
        )

        # Add token warning
        token_warning = HybridIntelligence.generate_token_warning(
            estimated_tokens,
            format_type
        )

        # Add next steps
        next_steps = HybridIntelligence.generate_next_steps(
            actual_operation,
            result
        )

        # Build response
        response = {
            "success": True,
            "operation": actual_operation,
            "result": result,
            "_guidance": guidance,
            "_token_estimate": token_warning,
            "_performance": {
                "query_time_ms": 0,  # TODO: Track actual time
                "cache_hit": False,
                "cache_type": None,
                "files_loaded": [],
                "selective_loading": True
            }
        }

        if next_steps:
            response["_next_steps"] = next_steps

        logger.info(f"Analysis completed: {actual_operation}")
        return response

    except Exception as e:
        logger.error(f"Error in analyze_hybrid_model: {str(e)}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': f"Analysis failed: {str(e)}",
            'error_type': 'analysis_error',
            'context': {
                'analysis_path': analysis_path,
                'operation': operation
            }
        }


def _operation_read_metadata(reader: HybridReader) -> Dict[str, Any]:
    """Read metadata operation"""
    metadata = reader.read_metadata()

    # Add sample data info if available
    sample_tables = reader.list_sample_data_tables()
    if sample_tables:
        metadata["sample_data_available"] = {
            "tables": sample_tables,
            "table_count": len(sample_tables),
            "note": "Use operation='get_sample_data' with table name to retrieve data"
        }

    # Add format type info
    metadata["_format_type"] = reader.format_type

    return {
        "data": metadata,
        "count": 1
    }


def _operation_find_objects(
    reader: HybridReader,
    object_filter: Dict[str, Any],
    batch_size: int,
    batch_number: int
) -> Dict[str, Any]:
    """Find objects operation"""
    object_type = object_filter.get("object_type", "tables")

    # Extract filters
    filters = {}
    for key in ["name_pattern", "folder", "table", "is_hidden", "complexity"]:
        if key in object_filter:
            filters[key] = object_filter[key]

    # Find objects
    objects = reader.find_objects(object_type, filters)

    # Apply pagination
    total = len(objects)
    start = batch_number * batch_size
    end = start + batch_size
    page_objects = objects[start:end]

    return {
        "object_type": object_type,
        "count": len(page_objects),
        "total": total,
        "batch": {
            "size": batch_size,
            "number": batch_number,
            "total_pages": (total + batch_size - 1) // batch_size
        },
        "objects": page_objects
    }


def _operation_get_object_definition(
    reader: HybridReader,
    object_name: str,
    object_type: str
) -> Dict[str, Any]:
    """Get object definition operation"""
    definition = reader.get_object_definition(object_name, object_type)
    return {
        "data": definition,
        "count": 1
    }


def _operation_analyze_dependencies(
    reader: HybridReader,
    object_name: str,
    direction: str
) -> Dict[str, Any]:
    """Analyze dependencies operation"""
    dependencies = reader.analyze_dependencies(object_name, direction)
    return {
        "data": dependencies,
        "count": 1
    }


def _operation_get_sample_data(
    reader: HybridReader,
    table_name: str,
    max_rows: int
) -> Dict[str, Any]:
    """Get sample data operation"""
    sample_data = reader.read_sample_data(table_name)

    if sample_data is None:
        return {
            "data": None,
            "count": 0,
            "message": "Sample data not available (no connection during export)"
        }

    # Limit rows
    if sample_data.get("data"):
        sample_data["data"] = sample_data["data"][:max_rows]

    return {
        "data": sample_data,
        "count": len(sample_data.get("data", []))
    }


def _operation_analyze_performance(
    reader: HybridReader,
    priority: Optional[str],
    detailed: bool
) -> Dict[str, Any]:
    """Analyze performance operation"""
    # TODO: Implement actual performance analysis
    # This would analyze the model for performance issues

    return {
        "data": {
            "issues": [],
            "recommendations": [],
            "message": "Performance analysis not yet implemented"
        },
        "count": 0
    }



def register_hybrid_analysis_handlers(registry):
    """Register hybrid analysis tool handlers"""

    # Simple wrapper to handle arguments dict
    def make_handler(func):
        def wrapper(args):
            return func(**args)
        return wrapper

    registry.register(ToolDefinition(
        name='export_hybrid_analysis',
        description='Export Power BI model: TMDL from PBIP folder + metadata/sample data from active model (auto-detects Power BI Desktop if no connection provided)',
        handler=make_handler(handle_export_hybrid_analysis),
        input_schema=TOOL_SCHEMAS['export_hybrid_analysis'],
        category='14 - Hybrid Analysis',
        sort_order=140
    ))

    registry.register(ToolDefinition(
        name='analyze_hybrid_model',
        description='Read and analyze hybrid analysis package with intelligent routing and natural language support',
        handler=make_handler(handle_analyze_hybrid_model),
        input_schema=TOOL_SCHEMAS['analyze_hybrid_model'],
        category='14 - Hybrid Analysis',
        sort_order=141
    ))

    logger.info("Registered 2 hybrid analysis handlers")
