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


def handle_test_metadata_extraction(
    model_index: int = 0,
    connection_string: Optional[str] = None,
    server: Optional[str] = None,
    database: Optional[str] = None,
    output_dir: Optional[str] = None,
    include_sample_data: bool = True,
    sample_rows: int = 100,
    sample_tables: Optional[list] = None
) -> Dict[str, Any]:
    """
    Test metadata and sample data extraction from open Power BI model

    This tool connects to an open Power BI Desktop instance and extracts:
    1. Model metadata (tables, measures, columns, relationships, row counts)
    2. Sample data from tables (optional)

    Args:
        model_index: Index of Power BI instance (0 for first)
        connection_string: Optional connection string
        server: Optional server name (e.g., 'localhost:49200')
        database: Optional database name
        include_sample_data: Extract sample data (default: True)
        sample_rows: Number of rows per table (default: 100)
        sample_tables: Optional list of specific tables to sample

    Returns:
        Extraction result with metadata and sample data
    """
    try:
        import time
        from core.infrastructure.multi_instance_manager import MultiInstanceManager
        from core.infrastructure.query_executor import OptimizedQueryExecutor, ADOMD_AVAILABLE, AdomdConnection

        logger.info("=" * 80)
        logger.info("TEST METADATA EXTRACTION")
        logger.info("=" * 80)

        # Step 1: Connect to Power BI instance
        if not connection_string and not (server and database):
            logger.info("Step 1: Auto-detecting Power BI Desktop instances...")
            manager = MultiInstanceManager()
            instances = manager.detect_instances()

            if not instances:
                return {
                    'success': False,
                    'error': 'No Power BI Desktop instances detected. Please open a PBIX/PBIP file.',
                    'error_type': 'no_instances'
                }

            if model_index >= len(instances):
                return {
                    'success': False,
                    'error': f'Model index {model_index} out of range. Found {len(instances)} instance(s).',
                    'error_type': 'invalid_index',
                    'available_instances': len(instances)
                }

            instance = instances[model_index]
            server = f"localhost:{instance['port']}"
            database = instance.get('database') or instance.get('database_name')

            logger.info(f"✓ Selected instance {model_index}: {database}")
            logger.info(f"  Server: {server}")
            logger.info(f"  PID: {instance.get('pid', 'N/A')}")

        # Step 2: Connect via ADOMD
        if not ADOMD_AVAILABLE or not AdomdConnection:
            return {
                'success': False,
                'error': 'ADOMD.NET not available - ensure Python.NET and ADOMD.NET are installed',
                'error_type': 'adomd_not_available'
            }

        logger.info("Step 2: Connecting to Power BI model via ADOMD...")

        if connection_string:
            conn_str = connection_string
        else:
            # Query actual database GUID
            temp_conn_str = f"Provider=MSOLAP;Data Source={server}"
            temp_conn = AdomdConnection(temp_conn_str)
            temp_conn.Open()

            cmd = temp_conn.CreateCommand()
            cmd.CommandText = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
            reader = cmd.ExecuteReader()

            actual_database = None
            if reader.Read():
                actual_database = reader[0]
            reader.Close()
            temp_conn.Close()

            if not actual_database:
                return {
                    'success': False,
                    'error': f'Could not find database on {server}',
                    'error_type': 'database_not_found'
                }

            database = actual_database
            conn_str = f"Provider=MSOLAP;Data Source={server};Initial Catalog={actual_database}"

        connection = AdomdConnection(conn_str)
        connection.Open()
        query_executor = OptimizedQueryExecutor(connection)

        logger.info(f"✓ Connected to: {database}")

        # Step 3: Extract metadata
        logger.info("Step 3: Extracting metadata...")
        metadata = {
            "model_name": database,
            "server": server,
            "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Get tables first
        logger.info("  - Extracting tables...")
        tables_query = "EVALUATE INFO.TABLES()"
        tables_result = query_executor.validate_and_execute_dax(tables_query, top_n=0, bypass_cache=True)

        table_names = []
        if tables_result.get('success'):
            table_rows = tables_result.get('rows', [])
            table_names = [row.get('[Name]', row.get('Name', '')) for row in table_rows if row.get('[Name]') or row.get('Name')]
            logger.info(f"    ✓ Found {len(table_names)} tables")
        else:
            logger.warning(f"    ✗ Could not extract tables: {tables_result.get('error')}")

        # Get row counts using COUNTROWS for each table (most reliable method)
        logger.info("  - Extracting row counts (using COUNTROWS per table)...")
        metadata["row_counts"] = {}
        metadata["total_rows"] = 0

        if table_names:
            row_count_dict = {}
            for idx, table_name in enumerate(table_names, 1):
                try:
                    escaped_table = table_name.replace("'", "''")
                    count_query = f"EVALUATE {{ COUNTROWS('{escaped_table}') }}"

                    result = query_executor.validate_and_execute_dax(count_query, top_n=0, bypass_cache=True)

                    if result.get('success') and result.get('rows'):
                        # Get the count value from first row, first column
                        row_count = int(list(result['rows'][0].values())[0])
                        row_count_dict[table_name] = row_count

                        if idx % 20 == 0:
                            logger.info(f"    Progress: {idx}/{len(table_names)} tables")
                    else:
                        logger.warning(f"    Could not get count for {table_name}: {result.get('error', 'Unknown error')}")
                        row_count_dict[table_name] = 0
                except Exception as e:
                    logger.warning(f"    Error counting rows in {table_name}: {e}")
                    row_count_dict[table_name] = 0

            metadata["row_counts"] = row_count_dict
            metadata["total_rows"] = sum(row_count_dict.values())
            logger.info(f"    ✓ Found row counts for {len(row_count_dict)} tables (total: {metadata['total_rows']:,} rows)")
        else:
            logger.warning("    ✗ No tables found, skipping row count extraction")

        # Get measures
        logger.info("  - Extracting measures...")
        measures_result = query_executor.validate_and_execute_dax("EVALUATE INFO.MEASURES()", top_n=0, bypass_cache=True)
        if measures_result.get('success'):
            metadata["measures_count"] = len(measures_result.get('rows', []))
            logger.info(f"    ✓ Found {metadata['measures_count']} measures")
        else:
            metadata["measures_count"] = 0
            logger.warning("    ✗ Could not extract measures")

        # Get columns
        logger.info("  - Extracting columns...")
        columns_result = query_executor.validate_and_execute_dax("EVALUATE INFO.COLUMNS()", top_n=0, bypass_cache=True)
        if columns_result.get('success'):
            metadata["columns_count"] = len(columns_result.get('rows', []))
            logger.info(f"    ✓ Found {metadata['columns_count']} columns")
        else:
            metadata["columns_count"] = 0
            logger.warning("    ✗ Could not extract columns")

        # Get relationships
        logger.info("  - Extracting relationships...")
        relationships_query = "EVALUATE INFO.RELATIONSHIPS()"
        relationships_result = query_executor.validate_and_execute_dax(relationships_query, top_n=0, bypass_cache=True)
        if relationships_result.get('success'):
            rel_rows = relationships_result.get('rows', [])
            # Extract IsActive and CrossFilterDirection with column name variations
            active_count = 0
            inactive_count = 0
            bidirectional_count = 0

            for r in rel_rows:
                # Try different column name variations
                is_active = r.get('[IsActive]', r.get('IsActive', False))
                cross_filter = r.get('[CrossFilterDirection]', r.get('CrossFilterDirection', ''))

                # Convert to boolean if string
                if isinstance(is_active, str):
                    is_active = is_active.lower() == 'true'

                if is_active:
                    active_count += 1
                else:
                    inactive_count += 1

                if str(cross_filter).lower() == 'both':
                    bidirectional_count += 1

            metadata["relationships"] = {
                "total": len(rel_rows),
                "active": active_count,
                "inactive": inactive_count,
                "bidirectional": bidirectional_count
            }
            logger.info(f"    ✓ Found {metadata['relationships']['total']} relationships ({metadata['relationships']['active']} active)")
        else:
            metadata["relationships"] = {"total": 0, "active": 0, "inactive": 0, "bidirectional": 0}
            logger.warning(f"    ✗ Could not extract relationships: {relationships_result.get('error')}")

        # Step 4: Extract sample data (controlled by include_sample_data parameter)
        sample_data = {}
        extraction_logs = []

        if not include_sample_data:
            log_msg = "Step 4: Skipping sample data extraction (include_sample_data=False)"
            logger.info(log_msg)
            extraction_logs.append(log_msg)
        else:
            log_msg = f"Step 4: Extracting sample data ({sample_rows} rows per table)..."
            logger.info(log_msg)
            extraction_logs.append(log_msg)

            # Determine which tables to sample - use table_names from INFO.TABLES()
            tables_to_sample = sample_tables if sample_tables else table_names

            if not tables_to_sample:
                log_msg = "  ✗ No tables found for sampling"
                logger.warning(log_msg)
                extraction_logs.append(log_msg)
            else:
                successful_samples = 0
                failed_samples = 0

                # Extract from ALL tables if no specific tables provided, otherwise respect the limit
                max_tables = len(tables_to_sample) if sample_tables else len(tables_to_sample)
                log_msg = f"  Sampling {max_tables} tables..."
                logger.info(log_msg)
                extraction_logs.append(log_msg)

                for idx, table_name in enumerate(tables_to_sample[:max_tables], 1):
                    try:
                        escaped_table = table_name.replace("'", "''")
                        # Use simple EVALUATE and let top_n parameter handle row limiting
                        dax_query = f"EVALUATE '{escaped_table}'"

                        result = query_executor.validate_and_execute_dax(dax_query, top_n=sample_rows, bypass_cache=True)

                        if result.get('success'):
                            rows = result.get('rows', [])[:sample_rows]
                            sample_data[table_name] = {
                                "rows": rows,
                                "row_count": len(rows),
                                "columns": result.get('columns', [])
                            }
                            successful_samples += 1
                            log_msg = f"  [{idx}/{max_tables}] ✓ {table_name}: {len(rows)} rows"
                            logger.info(log_msg)
                            extraction_logs.append(log_msg)
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            log_msg = f"  [{idx}/{max_tables}] ✗ {table_name}: {error_msg}"
                            logger.warning(log_msg)
                            extraction_logs.append(log_msg)
                            failed_samples += 1
                    except Exception as e:
                        log_msg = f"  [{idx}/{max_tables}] ✗ {table_name}: {str(e)}"
                        logger.warning(log_msg)
                        extraction_logs.append(log_msg)
                        failed_samples += 1

                log_msg = f"  Sample extraction complete: {successful_samples} successful, {failed_samples} failed"
                logger.info(log_msg)
                extraction_logs.append(log_msg)

        # Step 5: ALWAYS save to files (create temp dir if not specified)
        from pathlib import Path
        import json
        import tempfile

        if not output_dir:
            # Create temp directory if no output_dir specified
            output_dir = tempfile.mkdtemp(prefix="powerbi_metadata_")
            logger.info(f"No output_dir specified, using temp directory: {output_dir}")

        logger.info(f"Step 5: Saving files to {output_dir}...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save metadata JSON
        metadata_file = output_path / "test_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        saved_files = {"metadata": str(metadata_file)}
        logger.info(f"  ✓ Saved metadata: {metadata_file}")

        # Save sample data as parquet files (when sample_data exists)
        sample_data_summary = {}
        log_msg = f"  Checking sample data: {len(sample_data)} tables extracted"
        logger.info(log_msg)
        extraction_logs.append(log_msg)

        if sample_data:
            try:
                import polars as pl
                log_msg = "  ✓ Polars available"
                logger.info(log_msg)
                extraction_logs.append(log_msg)

                sample_data_dir = output_path / "sample_data"
                sample_data_dir.mkdir(exist_ok=True)
                log_msg = f"  ✓ Created directory: {sample_data_dir}"
                logger.info(log_msg)
                extraction_logs.append(log_msg)

                parquet_files = []
                tables_with_data = 0
                tables_without_data = 0

                for table_name, table_data in sample_data.items():
                    rows = table_data.get('rows', [])

                    if rows:
                        tables_with_data += 1
                        try:
                            # Convert rows to DataFrame (scan all rows for schema inference)
                            df = pl.DataFrame(rows, infer_schema_length=None)

                            parquet_path = sample_data_dir / f"{table_name}.parquet"
                            df.write_parquet(parquet_path, compression="snappy", use_pyarrow=False)
                            parquet_files.append(str(parquet_path))

                            # Verify file was created
                            if parquet_path.exists():
                                file_size = parquet_path.stat().st_size
                                log_msg = f"  ✓ Saved: {table_name}.parquet ({len(rows)} rows, {file_size:,} bytes)"
                                logger.info(log_msg)
                                extraction_logs.append(log_msg)
                            else:
                                log_msg = f"  ✗ File not found after write: {parquet_path}"
                                logger.error(log_msg)
                                extraction_logs.append(log_msg)

                            # Store summary info instead of full data
                            sample_data_summary[table_name] = {
                                "file": str(parquet_path),
                                "row_count": len(rows),
                                "column_count": len(table_data.get('columns', []))
                            }
                        except Exception as e:
                            log_msg = f"  ✗ Error saving {table_name}.parquet: {e}"
                            logger.error(log_msg)
                            extraction_logs.append(log_msg)
                    else:
                        tables_without_data += 1

                saved_files["sample_data_dir"] = str(sample_data_dir)
                saved_files["parquet_files"] = parquet_files
                saved_files["parquet_count"] = len(parquet_files)
                log_msg = f"  ✓ Saved {len(parquet_files)} parquet files to {sample_data_dir}"
                logger.info(log_msg)
                extraction_logs.append(log_msg)
                log_msg = f"    Tables with data: {tables_with_data}, without data: {tables_without_data}"
                logger.info(log_msg)
                extraction_logs.append(log_msg)
            except ImportError as e:
                log_msg = f"  ✗ Polars not available: {e}"
                logger.error(log_msg)
                extraction_logs.append(log_msg)
                extraction_logs.append("    Install polars with: pip install polars")
            except Exception as e:
                log_msg = f"  ✗ Unexpected error saving parquet files: {e}"
                logger.error(log_msg)
                extraction_logs.append(log_msg)
        else:
            log_msg = "  ℹ No sample data extracted - sample_data dict is empty!"
            logger.warning(log_msg)
            extraction_logs.append(log_msg)

        # Close connection
        connection.Close()

        logger.info("=" * 80)
        logger.info("EXTRACTION COMPLETE")
        logger.info("=" * 80)

        result = {
            "success": True,
            "output_dir": output_dir,
            "saved_files": saved_files,
            "metadata_summary": {
                "model_name": metadata.get("model_name"),
                "server": metadata.get("server"),
                "extraction_time": metadata.get("extraction_time"),
                "tables": len(table_names),
                "measures": metadata.get("measures_count", 0),
                "columns": metadata.get("columns_count", 0),
                "relationships": metadata.get("relationships", {}).get("total", 0),
                "total_rows": metadata.get("total_rows", 0)
            },
            "sample_data_summary": sample_data_summary,
            "extraction_logs": extraction_logs,
            "message": f"All data saved to: {output_dir}"
        }

        return result

    except Exception as e:
        logger.error(f"Error in test_metadata_extraction: {str(e)}\n{traceback.format_exc()}")
        return {
            'success': False,
            'error': f"Extraction failed: {str(e)}",
            'error_type': 'extraction_error'
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

    registry.register(ToolDefinition(
        name='test_metadata_extraction',
        description='Test metadata and sample data extraction from open Power BI Desktop instance (auto-connects and extracts comprehensive model information)',
        handler=make_handler(handle_test_metadata_extraction),
        input_schema=TOOL_SCHEMAS['test_metadata_extraction'],
        category='15 - Testing & Diagnostics',
        sort_order=150
    ))

    logger.info("Registered 3 hybrid analysis handlers")
