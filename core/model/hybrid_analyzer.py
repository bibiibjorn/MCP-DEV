"""
Hybrid Analyzer - Export and analyze Power BI models in hybrid format

Combines PBIP TMDL files with JSON analysis and sample data for efficient analysis.

Data Sources:
- TMDL: From PBIP folder (offline, no connection needed)
- JSON Analysis (metadata, statistics): From active model via DMV queries (requires connection)
- Sample Data: From active model via DAX queries (requires connection)
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import os

from .pbip_reader import PBIPReader
from .hybrid_structures import *

# Try to import orjson for faster JSON serialization
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    logging.warning("orjson not available, using standard json (slower)")

logger = logging.getLogger(__name__)

# File size limit for MCP compatibility (900KB with 10% safety margin)
MAX_FILE_SIZE = 900_000  # 900 KB


class HybridAnalyzer:
    """Export Power BI model to hybrid analysis format"""

    def __init__(
        self,
        pbip_folder_path: str,
        output_dir: str,
        connection_string: Optional[str] = None,
        server: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        Initialize hybrid analyzer

        Args:
            pbip_folder_path: Path to .SemanticModel folder (for TMDL files)
            output_dir: Output directory for analysis package
            connection_string: Connection to active model for JSON analysis & sample data
            server: Alternative: server name (for active model connection)
            database: Alternative: database name (for active model connection)

        Data Sources:
            - TMDL files: Read from pbip_folder_path (offline)
            - JSON analysis (metadata, statistics, row counts): Extracted from active model via connection
            - Sample data: Extracted from active model via connection
        """
        self.pbip_reader = PBIPReader(pbip_folder_path)
        self.output_dir = Path(output_dir)
        self.connection_string = connection_string
        self.server = server
        self.database = database

        # Connection for querying active model (for JSON analysis & sample data)
        self.query_executor = None
        self.has_connection = False

        # Step 1: Try to establish connection
        if connection_string or (server and database):
            # User provided connection explicitly
            logger.info("Using provided connection parameters")
            if connection_string:
                logger.info(f"Connection string: {connection_string[:50]}...")
            else:
                logger.info(f"Server: {server}, Database: {database}")
            self.has_connection = True
        else:
            # Auto-detect Power BI Desktop instance
            logger.info("No connection provided - attempting to auto-detect Power BI Desktop...")
            try:
                from core.infrastructure.multi_instance_manager import MultiInstanceManager
                manager = MultiInstanceManager()
                instances = manager.detect_instances()

                if instances:
                    # Use the first detected instance
                    instance = instances[0]
                    self.server = f"localhost:{instance['port']}"
                    # Note: detection returns 'database' not 'database_name'
                    self.database = instance.get('database') or instance.get('database_name')

                    if not self.database:
                        logger.warning("✗ No database name found in detected instance. Will use basic metadata from TMDL only.")
                        logger.warning(f"  Instance details: {instance}")
                        self.has_connection = False
                    else:
                        self.has_connection = True
                        logger.info(f"✓ Auto-detected Power BI Desktop: {self.server} / {self.database}")
                        logger.info(f"  Instance details: Port={instance.get('port')}, PID={instance.get('pid', 'N/A')}")
                else:
                    logger.warning("✗ No Power BI Desktop instances detected. Will use basic metadata from TMDL only.")
                    logger.warning("  Make sure Power BI Desktop is running with a PBIX/PBIP file open.")
            except Exception as e:
                logger.warning(f"✗ Could not auto-detect Power BI Desktop: {e}. Will use basic metadata from TMDL only.")
                logger.debug(f"  Auto-detection error details:", exc_info=True)

        # Step 2: Connect to the model (if we have connection info)
        if self.has_connection:
            try:
                # Import ADOMD
                logger.info("Attempting to connect to active model via ADOMD...")
                from core.infrastructure.query_executor import OptimizedQueryExecutor, ADOMD_AVAILABLE, AdomdConnection

                if not ADOMD_AVAILABLE or not AdomdConnection:
                    raise RuntimeError("ADOMD.NET not available - ensure Python.NET and ADOMD.NET are installed")

                # Build connection string
                if connection_string:
                    conn_str = connection_string
                else:
                    # Step 2a: Connect without database to get actual GUID database name
                    # Power BI uses GUID database names internally, not file names
                    temp_conn_str = f"Provider=MSOLAP;Data Source={self.server}"
                    logger.info(f"  Querying actual database name from {self.server}...")

                    temp_conn = AdomdConnection(temp_conn_str)
                    temp_conn.Open()

                    # Query the catalog to get the actual database GUID
                    cmd = temp_conn.CreateCommand()
                    cmd.CommandText = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
                    reader = cmd.ExecuteReader()

                    actual_database = None
                    if reader.Read():
                        actual_database = reader[0]
                    reader.Close()
                    temp_conn.Close()

                    if not actual_database:
                        raise RuntimeError(f"Could not find database on {self.server}")

                    logger.info(f"  ✓ Found database: {actual_database}")
                    self.database = actual_database

                    # Build final connection string with actual database GUID
                    conn_str = f"Provider=MSOLAP;Data Source={self.server};Initial Catalog={actual_database}"

                logger.info(f"  Connection string: Provider=MSOLAP;Data Source={self.server};Initial Catalog=...")

                # Create and open ADOMD connection
                connection = AdomdConnection(conn_str)
                connection.Open()

                # Create query executor with active connection
                self.query_executor = OptimizedQueryExecutor(connection)
                logger.info("✓ Successfully connected to active model!")
                logger.info("  - Metadata extraction: ENABLED (DMV queries)")
                logger.info("  - Sample data extraction: ENABLED (DAX queries)")
            except Exception as e:
                logger.warning(f"✗ Could not connect to active model: {e}")
                logger.warning("  Will use basic metadata from TMDL only (no row counts, no sample data)")
                logger.debug("  Connection error details:", exc_info=True)
                self.has_connection = False
                self.query_executor = None

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir = self.output_dir / "analysis"
        self.analysis_dir.mkdir(exist_ok=True)
        self.sample_data_dir = self.output_dir / "sample_data"
        if self.has_connection:
            self.sample_data_dir.mkdir(exist_ok=True)

    def export(
        self,
        include_sample_data: bool = True,
        sample_rows: int = 1000,
        sample_compression: str = "snappy",
        include_row_counts: bool = True,
        track_column_usage: bool = True,
        track_cardinality: bool = True,
        tmdl_strategy: str = "symlink",
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Export model to hybrid analysis format

        Args:
            include_sample_data: Include sample data extraction
            sample_rows: Number of sample rows per table
            sample_compression: Compression for parquet files
            include_row_counts: Include row counts in metadata
            track_column_usage: Track column usage
            track_cardinality: Track cardinality info
            tmdl_strategy: "symlink" or "copy"
            progress_callback: Optional progress callback

        Returns:
            Export result dictionary
        """
        start_time = time.time()

        # Step 1: Copy or symlink TMDL files
        logger.info("Step 1: Copying/symlinking TMDL files...")
        tmdl_path = self.output_dir / "tmdl"
        tmdl_result = self.pbip_reader.copy_or_symlink_tmdl(
            tmdl_path,
            strategy=tmdl_strategy
        )

        # Step 2: Generate PBIP source info
        logger.info("Step 2: Generating PBIP source info...")
        pbip_metadata = self.pbip_reader.get_pbip_metadata()
        pbip_source_info = PBIPSourceInfo(
            source_pbip_path=pbip_metadata["source_pbip_path"],
            source_pbip_absolute=pbip_metadata["source_pbip_absolute"],
            pbip_last_modified=pbip_metadata["pbip_last_modified"],
            model_name=pbip_metadata["model_name"],
            export_timestamp=datetime.now().isoformat(),
            export_version="4.1-pbip",
            tmdl_strategy=tmdl_result["strategy"],
            tmdl_file_count=pbip_metadata["tmdl_file_count"],
            tmdl_total_size_bytes=pbip_metadata["tmdl_total_size_bytes"],
            connection_used=self.has_connection,
            sample_data_extracted=include_sample_data and self.has_connection
        )

        # Write pbip_source_info.json
        self._write_json(
            self.output_dir / "pbip_source_info.json",
            pbip_source_info.to_dict()
        )

        # Step 3: Generate analysis files from active model (if connected)
        logger.info("Step 3: Generating analysis files...")

        # Discover structure from PBIP
        tables = self.pbip_reader.discover_tables()
        roles = self.pbip_reader.discover_roles()

        # Generate metadata (uses connection if available for row counts, statistics)
        metadata = self._generate_metadata(
            pbip_source_info.model_name,
            tables,
            roles,
            time.time() - start_time
        )
        self._write_json(self.analysis_dir / "metadata.json", metadata.to_dict())

        # Generate catalog
        catalog = self._generate_catalog(tables, roles)
        self._write_json_with_splitting(
            self.analysis_dir / "catalog.json",
            catalog.to_dict(),
            "catalog"
        )

        # Generate dependencies
        dependencies = self._generate_dependencies(tables)
        self._write_json_with_splitting(
            self.analysis_dir / "dependencies.json",
            dependencies.to_dict(),
            "dependencies"
        )

        # Step 4: Extract sample data (ALWAYS extract when connection is available)
        parquet_file_count = 0
        if self.has_connection:
            logger.info("Step 4: Extracting sample data (ALWAYS when connected)...")
            if not include_sample_data:
                logger.info("  Note: include_sample_data=False but extracting anyway (always extract when connected)")
            parquet_file_count = self._extract_sample_data(
                tables,
                sample_rows,
                sample_compression
            )

        export_time = time.time() - start_time

        # Extract statistics from metadata for return value
        metadata_dict = metadata.to_dict()
        row_counts = metadata_dict.get("row_counts", {})
        statistics_summary = metadata_dict.get("statistics", {})

        return {
            "success": True,
            "output_path": str(self.output_dir),
            "structure": {
                "pbip_source_path": pbip_source_info.source_pbip_path,
                "tmdl_path": "tmdl/",
                "tmdl_strategy": tmdl_result["strategy"],
                "analysis_path": "analysis/",
                "sample_data_path": "sample_data/" if self.has_connection else None,
                "file_counts": {
                    "tmdl_files": tmdl_result["file_count"],
                    "json_files": 3,  # metadata, catalog, dependencies (or their manifests)
                    "parquet_files": parquet_file_count,
                    "total": tmdl_result["file_count"] + 3 + parquet_file_count
                }
            },
            "statistics": {
                "tables": len(tables),
                "measures": statistics_summary.get("measures", {}).get("total", 0),
                "relationships": statistics_summary.get("relationships", {}).get("total", 0),
                "columns": statistics_summary.get("columns", {}).get("total", 0),
                "roles": len(roles),
                "total_rows": row_counts.get("total_rows", 0)
            },
            "generation_time_seconds": round(export_time, 2),
            "export_version": "4.1-pbip",
            "optimizations_enabled": {
                "pbip_source": True,
                "orjson": HAS_ORJSON,
                "optimized_dmv": False,  # Not applicable for PBIP export
                "dynamic_workers": True,
                "file_splitting": True,
                "tmdl_strategy": tmdl_result["strategy"]
            }
        }

    def _generate_metadata(
        self,
        model_name: str,
        tables: List[str],
        roles: List[str],
        export_time: float
    ) -> Metadata:
        """Generate metadata.json structure (with comprehensive metadata from active model if connected)"""
        model_metadata = ModelMetadata(
            name=model_name,
            compatibility_level=1600,
            default_mode="Import",
            culture="en-US",
            analysis_timestamp=datetime.now().isoformat()
        )

        # Initialize counters
        total_measures = 0
        total_columns = 0
        total_relationships = 0
        active_relationships = 0
        inactive_relationships = 0
        bidirectional_relationships = 0

        # Get comprehensive metadata from active model if connected
        row_counts_data = {"by_table": [], "total_rows": 0, "largest_fact_tables": []}

        if self.query_executor:
            # EXACT CODE FROM test_metadata_extraction (tool 015) - VERIFIED WORKING

            # Step 1: Get table names from live model using INFO.TABLES() - most reliable!
            logger.info("  - Extracting tables from live model...")
            tables_query = "EVALUATE INFO.TABLES()"
            tables_result = self.query_executor.validate_and_execute_dax(tables_query, top_n=0, bypass_cache=True)

            table_names = []
            if tables_result.get('success'):
                table_rows = tables_result.get('rows', [])
                table_names = [row.get('[Name]', row.get('Name', '')) for row in table_rows if row.get('[Name]') or row.get('Name')]
                logger.info(f"    ✓ Found {len(table_names)} tables")
            else:
                logger.warning(f"    ✗ Could not extract tables: {tables_result.get('error')}")
                # Fallback to TMDL table names
                table_names = tables

            # Step 2: Get row counts using COUNTROWS for each table (most reliable method)
            logger.info("  - Extracting row counts (using COUNTROWS per table)...")

            row_count_dict = {}
            total_rows = 0

            if table_names:
                for idx, table_name in enumerate(table_names, 1):
                    try:
                        escaped_table = table_name.replace("'", "''")
                        count_query = f"EVALUATE {{ COUNTROWS('{escaped_table}') }}"

                        result = self.query_executor.validate_and_execute_dax(count_query, top_n=0, bypass_cache=True)

                        if result.get('success') and result.get('rows'):
                            # Get the count value from first row, first column
                            row_count = int(list(result['rows'][0].values())[0])
                            row_count_dict[table_name] = row_count
                            total_rows += row_count

                            row_counts_data["by_table"].append({
                                "table": table_name,
                                "row_count": row_count,
                                "last_refresh": datetime.now().isoformat()
                            })

                            if idx % 20 == 0:
                                logger.info(f"    Progress: {idx}/{len(table_names)} tables")
                        else:
                            logger.warning(f"    Could not get count for {table_name}: {result.get('error', 'Unknown error')}")
                            row_count_dict[table_name] = 0
                            row_counts_data["by_table"].append({
                                "table": table_name,
                                "row_count": 0,
                                "last_refresh": datetime.now().isoformat()
                            })
                    except Exception as e:
                        logger.warning(f"    Error counting rows in {table_name}: {e}")
                        row_count_dict[table_name] = 0
                        row_counts_data["by_table"].append({
                            "table": table_name,
                            "row_count": 0,
                            "last_refresh": datetime.now().isoformat()
                        })

                row_counts_data["total_rows"] = total_rows

                # Get largest tables
                row_counts_data["largest_fact_tables"] = [
                    {"name": item["table"], "rows": item["row_count"]}
                    for item in sorted(row_counts_data["by_table"],
                                     key=lambda x: x["row_count"],
                                     reverse=True)[:5]
                ]

                logger.info(f"    ✓ Found row counts for {len(row_count_dict)} tables (total: {total_rows:,} rows)")
                if row_counts_data['largest_fact_tables']:
                    logger.info(f"      Top 3 tables: {', '.join([f'{t['name']} ({t['rows']:,})' for t in row_counts_data['largest_fact_tables'][:3]])}")
            else:
                logger.warning("    ✗ No tables found, skipping row count extraction")

            # Get measures
            logger.info("  - Extracting measures...")
            measures_result = self.query_executor.validate_and_execute_dax("EVALUATE INFO.MEASURES()", top_n=0, bypass_cache=True)
            if measures_result.get('success'):
                total_measures = len(measures_result.get('rows', []))
                logger.info(f"    ✓ Found {total_measures} measures")
            else:
                total_measures = 0
                logger.warning("    ✗ Could not extract measures")

            # Get columns
            logger.info("  - Extracting columns...")
            columns_result = self.query_executor.validate_and_execute_dax("EVALUATE INFO.COLUMNS()", top_n=0, bypass_cache=True)
            if columns_result.get('success'):
                total_columns = len(columns_result.get('rows', []))
                logger.info(f"    ✓ Found {total_columns} columns")
            else:
                total_columns = 0
                logger.warning("    ✗ Could not extract columns")

            # Get relationships
            logger.info("  - Extracting relationships...")
            relationships_query = "EVALUATE INFO.RELATIONSHIPS()"
            relationships_result = self.query_executor.validate_and_execute_dax(relationships_query, top_n=0, bypass_cache=True)
            if relationships_result.get('success'):
                rel_rows = relationships_result.get('rows', [])
                total_relationships = len(rel_rows)
                # Extract IsActive and CrossFilterDirection with column name variations
                active_relationships = 0
                inactive_relationships = 0
                bidirectional_relationships = 0

                for r in rel_rows:
                    # Try different column name variations
                    is_active = r.get('[IsActive]', r.get('IsActive', False))
                    cross_filter = r.get('[CrossFilterDirection]', r.get('CrossFilterDirection', ''))

                    # Convert to boolean if string
                    if isinstance(is_active, str):
                        is_active = is_active.lower() == 'true'

                    if is_active:
                        active_relationships += 1
                    else:
                        inactive_relationships += 1

                    if str(cross_filter).lower() == 'both':
                        bidirectional_relationships += 1

                logger.info(f"    ✓ Found {total_relationships} relationships ({active_relationships} active)")
            else:
                total_relationships = 0
                logger.warning(f"    ✗ Could not extract relationships: {relationships_result.get('error')}")

        statistics = StatisticsSummary(
            tables={
                "total": len(tables),
                "fact_tables": 0,
                "dimension_tables": len(tables),
                "calculation_tables": 0
            },
            columns={
                "total": total_columns,
                "calculated": 0,
                "hidden": 0,
                "unused": 0
            },
            measures={
                "total": total_measures,
                "by_complexity": {
                    "simple": 0,
                    "medium": 0,
                    "complex": 0
                },
                "by_folder": {}
            },
            relationships={
                "total": total_relationships,
                "active": active_relationships,
                "inactive": inactive_relationships,
                "bidirectional": bidirectional_relationships,
                "many_to_many": 0
            },
            security={
                "roles": len(roles),
                "rls_tables": 0,
                "ols_objects": 0
            }
        )

        export_performance = ExportPerformance(
            export_time_seconds=round(export_time, 2),
            json_library="orjson" if HAS_ORJSON else "json",
            tmdl_strategy="symlink"
        )

        return Metadata(
            model=model_metadata,
            statistics=statistics,
            row_counts=row_counts_data,
            cardinality_summary={
                "high_cardinality_columns": 0,
                "total_distinct_values": 0,
                "cardinality_ratio_avg": 0.0
            },
            export_performance=export_performance
        )

    def _generate_catalog(self, tables: List[str], roles: List[str]) -> Catalog:
        """Generate catalog.json structure"""
        table_infos = []
        for table in tables:
            table_info = TableInfo(
                name=table,
                type="dimension",  # TODO: Detect fact vs dimension
                tmdl_path=f"tmdl/tables/{table}.tmdl",
                column_count=0,  # TODO: Parse from TMDL
                relationship_count=0,
                has_sample_data=self.has_connection
            )
            if self.has_connection:
                table_info.sample_data_path = f"sample_data/{table}.parquet"
            table_infos.append(table_info)

        role_infos = []
        for role in roles:
            role_info = RoleInfo(
                name=role,
                tmdl_path=f"tmdl/roles/{role}.tmdl",
                table_count=0
            )
            role_infos.append(role_info)

        return Catalog(
            tables=table_infos,
            measures=[],  # TODO: Parse from expressions.tmdl
            relationships_path="tmdl/relationships.tmdl",
            roles=role_infos,
            optimization_summary={
                "total_unused_columns": 0,
                "total_memory_potential_mb": 0,
                "high_priority_optimizations": 0,
                "estimated_performance_gain": "0%"
            }
        )

    def _generate_dependencies(self, tables: List[str]) -> Dependencies:
        """Generate dependencies.json structure"""
        return Dependencies(
            measures={},  # TODO: Parse measure dependencies
            columns={},
            tables={},
            summary={
                "total_measures": 0,
                "max_dependency_depth": 0,
                "circular_references": [],
                "orphan_measures": [],
                "critical_objects": []
            }
        )

    def _extract_sample_data(
        self,
        tables: List[str],
        sample_rows: int,
        compression: str
    ) -> int:
        """
        Extract sample data for tables

        Args:
            tables: List of table names
            sample_rows: Number of rows to extract
            compression: Compression algorithm

        Returns:
            Number of parquet files created
        """
        if not self.query_executor:
            logger.warning("✗ No query executor available - skipping sample data extraction")
            logger.warning("  (Connection to active model was not established)")
            return 0

        try:
            import polars as pl
        except ImportError:
            logger.warning("✗ Polars library not available - skipping sample data extraction")
            logger.warning("  Install polars with: pip install polars")
            return 0

        parquet_count = 0
        failed_count = 0
        logger.info(f"Extracting sample data for {len(tables)} tables (max {sample_rows} rows per table)...")

        for idx, table in enumerate(tables, 1):
            try:
                # Escape single quotes in table name
                escaped_table = table.replace("'", "''")

                # Build DAX query - use simple EVALUATE and let top_n parameter handle row limiting
                dax_query = f"EVALUATE '{escaped_table}'"

                # Execute query
                result = self.query_executor.validate_and_execute_dax(dax_query, top_n=sample_rows, bypass_cache=True)

                if not result.get('success'):
                    logger.warning(f"  [{idx}/{len(tables)}] ✗ Failed to extract from '{table}': {result.get('error')}")
                    failed_count += 1
                    continue

                rows = result.get('rows', [])
                if not rows:
                    logger.debug(f"  [{idx}/{len(tables)}] - Table '{table}' is empty")
                    continue

                # Convert to polars DataFrame (scan all rows for schema inference)
                df = pl.DataFrame(rows, infer_schema_length=None)

                # Write to parquet file
                parquet_path = self.sample_data_dir / f"{table}.parquet"
                df.write_parquet(
                    parquet_path,
                    compression=compression,
                    use_pyarrow=False  # Use polars native writer (faster)
                )

                parquet_count += 1
                if idx % 10 == 0:
                    logger.info(f"  Progress: {idx}/{len(tables)} tables processed, {parquet_count} files created")

            except Exception as e:
                logger.warning(f"  [{idx}/{len(tables)}] ✗ Error extracting from '{table}': {e}")
                failed_count += 1
                continue

        logger.info(f"✓ Sample data extraction complete:")
        logger.info(f"  - Successfully extracted: {parquet_count} parquet files")
        logger.info(f"  - Failed/empty tables: {failed_count}")
        logger.info(f"  - Total tables: {len(tables)}")
        return parquet_count

    def _write_json(self, path: Path, data: Dict[str, Any]):
        """Write JSON file using orjson if available"""
        if HAS_ORJSON:
            with open(path, 'wb') as f:
                f.write(orjson.dumps(
                    data,
                    option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
                ))
        else:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)

    def _write_json_with_splitting(
        self,
        path: Path,
        data: Dict[str, Any],
        file_type: str
    ):
        """
        Write JSON file with automatic splitting if size exceeds limit

        Args:
            path: Output file path
            data: Data to write
            file_type: "catalog" or "dependencies"
        """
        # Serialize to check size
        if HAS_ORJSON:
            serialized = orjson.dumps(
                data,
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
            )
        else:
            serialized = json.dumps(data, indent=2, sort_keys=True).encode('utf-8')

        size_bytes = len(serialized)

        if size_bytes < MAX_FILE_SIZE:
            # Write single file
            with open(path, 'wb') as f:
                f.write(serialized)
            logger.info(f"Wrote {path.name}: {size_bytes:,} bytes (single file)")
        else:
            # Split into multiple parts
            logger.info(f"Splitting {path.name}: {size_bytes:,} bytes exceeds limit")
            self._split_and_write(path, data, file_type, size_bytes)

    def _split_and_write(
        self,
        base_path: Path,
        data: Dict[str, Any],
        file_type: str,
        total_size: int
    ):
        """
        Split large JSON file into multiple parts

        Args:
            base_path: Base file path (e.g., catalog.json)
            data: Data to split
            file_type: "catalog" or "dependencies"
            total_size: Total size in bytes
        """
        parts = []
        part_num = 1

        if file_type == "catalog":
            # Split by tables
            tables = data.get("tables", [])
            items_per_part = max(1, len(tables) // ((total_size // MAX_FILE_SIZE) + 1))

            for i in range(0, len(tables), items_per_part):
                part_data = {
                    "tables": tables[i:i + items_per_part],
                    "measures": data.get("measures", []) if i == 0 else [],
                    "relationships_path": data.get("relationships_path", ""),
                    "roles": data.get("roles", []) if i == 0 else [],
                    "optimization_summary": data.get("optimization_summary", {}) if i == 0 else {}
                }

                part_path = base_path.parent / f"{base_path.stem}.part{part_num}.json"
                self._write_json(part_path, part_data)

                part_size = part_path.stat().st_size
                parts.append(FilePart(
                    part_number=part_num,
                    filename=part_path.name,
                    size_bytes=part_size,
                    content_range=f"tables[{i}:{i+items_per_part}]"
                ))
                part_num += 1

        elif file_type == "dependencies":
            # Split by measures
            measures = data.get("measures", {})
            measure_items = list(measures.items())
            items_per_part = max(1, len(measure_items) // ((total_size // MAX_FILE_SIZE) + 1))

            for i in range(0, len(measure_items), items_per_part):
                part_measures = dict(measure_items[i:i + items_per_part])
                part_data = {
                    "measures": part_measures,
                    "columns": data.get("columns", {}) if i == 0 else {},
                    "tables": data.get("tables", {}) if i == 0 else {},
                    "summary": data.get("summary", {}) if i == 0 else {}
                }

                part_path = base_path.parent / f"{base_path.stem}.part{part_num}.json"
                self._write_json(part_path, part_data)

                part_size = part_path.stat().st_size
                parts.append(FilePart(
                    part_number=part_num,
                    filename=part_path.name,
                    size_bytes=part_size,
                    content_range=f"measures[{i}:{i+items_per_part}]"
                ))
                part_num += 1

        # Write manifest
        manifest = FileManifest(
            file_type=file_type,
            total_parts=len(parts),
            total_size_bytes=total_size,
            split_strategy="table_boundary" if file_type == "catalog" else "measure_boundary",
            parts=parts,
            reassembly_instructions=f"Load all parts and merge arrays/objects"
        )

        manifest_path = base_path.parent / f"{base_path.stem}.manifest.json"
        self._write_json(manifest_path, manifest.to_dict())
        logger.info(f"Created {len(parts)} parts with manifest: {manifest_path.name}")
