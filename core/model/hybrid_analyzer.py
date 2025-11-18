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
from core.utilities.json_utils import dumps_json, HAS_ORJSON

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

        # Step 1: Try to establish connection (ALWAYS auto-detect if not explicitly provided)
        if connection_string or (server and database):
            # User provided connection explicitly
            logger.info("Using provided connection parameters")
            if connection_string:
                logger.info(f"Connection string: {connection_string[:50]}...")
            else:
                logger.info(f"Server: {server}, Database: {database}")
            self.has_connection = True
        else:
            # Auto-detect Power BI Desktop instance (ALWAYS try this)
            logger.info("=" * 80)
            logger.info("AUTO-DETECTING Power BI Desktop...")
            logger.info("=" * 80)
            try:
                from core.infrastructure.multi_instance_manager import MultiInstanceManager
                manager = MultiInstanceManager()
                instances = manager.detect_instances()

                if instances:
                    # Use the first detected instance
                    instance = instances[0]
                    self.server = f"localhost:{instance['port']}"
                    # Detection returns 'database' field (filename like "Test.pbix")
                    detected_db_name = instance.get('database') or instance.get('database_name')

                    logger.info(f"✓ DETECTED Power BI Desktop Instance:")
                    logger.info(f"  - Port: {instance.get('port')}")
                    logger.info(f"  - PID: {instance.get('pid', 'N/A')}")
                    logger.info(f"  - Database (filename): {detected_db_name}")
                    logger.info(f"  - Server: {self.server}")

                    # We'll resolve the actual GUID database name when connecting
                    # For now, mark that we found an instance
                    self.has_connection = True
                    logger.info("  - Connection: Will attempt to connect and resolve actual database GUID")
                else:
                    logger.warning("=" * 80)
                    logger.warning("✗ NO Power BI Desktop instances detected")
                    logger.warning("  Make sure Power BI Desktop is running with a PBIX/PBIP file open")
                    logger.warning("  Will use basic metadata from TMDL only (no connection)")
                    logger.warning("=" * 80)
                    self.has_connection = False
            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"✗ ERROR during auto-detection: {e}")
                logger.error("  Will use basic metadata from TMDL only")
                logger.error("=" * 80)
                logger.debug("  Auto-detection error details:", exc_info=True)
                self.has_connection = False

        # Step 2: Connect to the model (if we detected an instance)
        if self.has_connection:
            try:
                # Import ADOMD
                logger.info("=" * 80)
                logger.info("CONNECTING to active Power BI model via ADOMD.NET...")
                logger.info("=" * 80)
                from core.infrastructure.query_executor import OptimizedQueryExecutor, ADOMD_AVAILABLE, AdomdConnection

                if not ADOMD_AVAILABLE or not AdomdConnection:
                    raise RuntimeError("ADOMD.NET not available - ensure Python.NET and ADOMD.NET are installed")

                # Build connection string
                if connection_string:
                    conn_str = connection_string
                    logger.info(f"Using explicit connection string: {conn_str[:60]}...")
                else:
                    # Step 2a: Connect without database to get actual GUID database name
                    # Power BI uses GUID database names internally, not file names
                    temp_conn_str = f"Provider=MSOLAP;Data Source={self.server}"
                    logger.info(f"Step 1/3: Opening temporary connection to {self.server}...")
                    logger.info(f"  Connection string: {temp_conn_str}")

                    temp_conn = AdomdConnection(temp_conn_str)
                    temp_conn.Open()
                    logger.info(f"  ✓ Temporary connection opened")

                    # Query the catalog to get the actual database GUID
                    logger.info(f"Step 2/3: Querying for actual database GUID...")
                    cmd = temp_conn.CreateCommand()
                    cmd.CommandText = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
                    reader = cmd.ExecuteReader()

                    actual_database = None
                    if reader.Read():
                        actual_database = reader[0]
                        logger.info(f"  ✓ Found database GUID: {actual_database}")
                    else:
                        logger.warning(f"  ✗ No database found in catalog query")

                    reader.Close()
                    temp_conn.Close()
                    logger.info(f"  ✓ Temporary connection closed")

                    if not actual_database:
                        raise RuntimeError(f"Could not find database on {self.server}. Make sure a PBIX/PBIP file is open in Power BI Desktop.")

                    self.database = actual_database

                    # Build final connection string with actual database GUID
                    conn_str = f"Provider=MSOLAP;Data Source={self.server};Initial Catalog={actual_database}"
                    logger.info(f"Step 3/3: Opening final connection with database...")
                    logger.info(f"  Connection string: Provider=MSOLAP;Data Source={self.server};Initial Catalog={actual_database[:40]}...")

                # Create and open ADOMD connection
                connection = AdomdConnection(conn_str)
                connection.Open()
                logger.info(f"  ✓ Final connection opened successfully")

                # Create query executor with active connection
                self.query_executor = OptimizedQueryExecutor(connection)

                logger.info("=" * 80)
                logger.info("✓✓✓ CONNECTION SUCCESSFUL ✓✓✓")
                logger.info("=" * 80)
                logger.info("  - Server: " + self.server)
                logger.info("  - Database: " + (self.database[:60] if self.database else "N/A"))
                logger.info("  - Metadata extraction: ENABLED (DMV queries via query_executor)")
                logger.info("  - Sample data extraction: ENABLED (DAX queries via query_executor)")
                logger.info("=" * 80)

            except Exception as e:
                logger.error("=" * 80)
                logger.error(f"✗✗✗ CONNECTION FAILED ✗✗✗")
                logger.error("=" * 80)
                logger.error(f"Error: {e}")
                logger.error("Will use basic metadata from TMDL only (no row counts, no sample data)")
                logger.error("=" * 80)
                logger.debug("Connection error details:", exc_info=True)
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

        # Generate measures (separate from catalog)
        measures = self._generate_measures()
        self._write_json_with_splitting(
            self.analysis_dir / "measures.json",
            measures.to_dict(),
            "measures"
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

        # Prepare connection status for result
        connection_status = {
            "connected_to_live_model": self.has_connection,
            "connection_method": "none",
            "server": None,
            "database": None
        }

        if self.has_connection and self.query_executor:
            if self.connection_string:
                connection_status["connection_method"] = "explicit_connection_string"
            elif self.server and self.database:
                connection_status["connection_method"] = "auto_detected"
                connection_status["server"] = self.server
                connection_status["database"] = self.database[:60] + "..." if len(self.database or "") > 60 else self.database

        return {
            "success": True,
            "output_path": str(self.output_dir),
            "connection_status": connection_status,
            "structure": {
                "pbip_source_path": pbip_source_info.source_pbip_path,
                "tmdl_path": "tmdl/",
                "tmdl_strategy": tmdl_result["strategy"],
                "analysis_path": "analysis/",
                "sample_data_path": "sample_data/" if self.has_connection else None,
                "file_counts": {
                    "tmdl_files": tmdl_result["file_count"],
                    "json_files": 4,  # metadata, catalog, measures, dependencies (or their manifests)
                    "parquet_files": parquet_file_count,
                    "total": tmdl_result["file_count"] + 4 + parquet_file_count
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
            "data_extraction_summary": {
                "tmdl_extracted": True,
                "metadata_extracted": self.has_connection,
                "row_counts_extracted": self.has_connection and row_counts.get("total_rows", 0) > 0,
                "sample_data_extracted": self.has_connection and parquet_file_count > 0,
                "note": "Full metadata requires connection to active Power BI Desktop instance" if not self.has_connection else "Successfully extracted all metadata from active model"
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

    def _generate_measures(self) -> Measures:
        """Generate measures.json structure with all measure details"""
        all_measures = []

        if self.query_executor:
            # Get all measures
            logger.info("  - Extracting measures for measures.json...")
            measures_result = self.query_executor.validate_and_execute_dax("EVALUATE INFO.MEASURES()", top_n=0, bypass_cache=True)
            if measures_result.get('success'):
                for row in measures_result.get('rows', []):
                    measure_name = row.get('[Name]', row.get('Name', ''))
                    table_name = row.get('[TableName]', row.get('TableName', ''))
                    display_folder = row.get('[DisplayFolder]', row.get('DisplayFolder', ''))

                    measure_info = MeasureInfo(
                        name=measure_name,
                        table=table_name,
                        display_folder=display_folder if display_folder else None,
                        tmdl_path=f"tmdl/tables/{table_name}.tmdl"
                    )
                    all_measures.append(measure_info)
                logger.info(f"    ✓ Extracted {len(all_measures)} measures")

        return Measures(
            measures=all_measures,
            total_count=len(all_measures)
        )

    def _generate_catalog(self, tables: List[str], roles: List[str]) -> Catalog:
        """Generate catalog.json structure with table and column details (measures moved to separate file)"""
        table_infos = []

        # Extract columns from live model if connected
        columns_by_table = {}

        if self.query_executor:
            # Get all columns
            logger.info("  - Extracting columns for catalog...")
            columns_result = self.query_executor.validate_and_execute_dax("EVALUATE INFO.COLUMNS()", top_n=0, bypass_cache=True)
            if columns_result.get('success'):
                for row in columns_result.get('rows', []):
                    table_name = row.get('[TableName]', row.get('TableName', ''))
                    column_name = row.get('[Name]', row.get('Name', ''))
                    data_type = row.get('[DataType]', row.get('DataType', 'Unknown'))
                    is_hidden = row.get('[IsHidden]', row.get('IsHidden', False))
                    is_key = row.get('[IsKey]', row.get('IsKey', False))

                    # Convert string boolean to bool
                    if isinstance(is_hidden, str):
                        is_hidden = is_hidden.lower() == 'true'
                    if isinstance(is_key, str):
                        is_key = is_key.lower() == 'true'

                    if table_name not in columns_by_table:
                        columns_by_table[table_name] = []

                    column_info = ColumnInfo(
                        name=column_name,
                        data_type=data_type,
                        is_key=is_key,
                        is_hidden=is_hidden
                    )
                    columns_by_table[table_name].append(column_info)
                logger.info(f"    ✓ Extracted {sum(len(cols) for cols in columns_by_table.values())} columns across {len(columns_by_table)} tables")

        # Build table infos
        for table in tables:
            columns = columns_by_table.get(table, [])

            table_info = TableInfo(
                name=table,
                type="dimension",  # Can be enhanced to detect fact vs dimension
                tmdl_path=f"tmdl/tables/{table}.tmdl",
                column_count=len(columns),
                relationship_count=0,  # TODO: Count from relationships
                has_sample_data=self.has_connection,
                columns=columns
            )
            if self.has_connection:
                table_info.sample_data_path = f"sample_data/{table}.parquet"
            table_infos.append(table_info)

        # Build role infos
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
        """Generate dependencies.json structure with measure and column dependencies"""
        measure_deps = {}
        column_deps = {}
        table_deps = {}

        if self.query_executor:
            # Get all measures with expressions
            logger.info("  - Extracting measure dependencies...")
            measures_result = self.query_executor.validate_and_execute_dax("EVALUATE INFO.MEASURES()", top_n=0, bypass_cache=True)

            if measures_result.get('success'):
                import re

                for row in measures_result.get('rows', []):
                    measure_name = row.get('[Name]', row.get('Name', ''))
                    table_name = row.get('[TableName]', row.get('TableName', ''))
                    expression = row.get('[Expression]', row.get('Expression', ''))

                    # Simple dependency extraction using regex
                    # Find measure references like [MeasureName] or 'Table'[Measure]
                    measure_refs = set()
                    column_refs = set()  # Now stores "Table[Column]" format

                    if expression:
                        # First, find column references: 'Table'[Column] or Table[Column]
                        # This pattern captures both the table and column name
                        column_pattern = r"(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_\s]*))\[([^\]]+)\]"
                        column_matches = re.findall(column_pattern, expression)

                        for match in column_matches:
                            table_ref = match[0] or match[1]
                            column_name = match[2]

                            # Only add as column if the table reference is actually a known table
                            # This prevents function names like MAX, SELECTEDVALUE from being treated as tables
                            if table_ref and table_ref.strip() in tables:
                                # Add to column references in "Table[Column]" format
                                if column_name and column_name != measure_name:
                                    full_column_ref = f"{table_ref.strip()}[{column_name}]"
                                    column_refs.add(full_column_ref)

                        # Now find standalone measure references: [MeasureName]
                        # These are brackets NOT preceded by a table name or apostrophe
                        # Use negative lookbehind to exclude Table[...] patterns
                        measure_pattern = r"(?<![\w'])\[([^\]]+)\]"
                        measure_matches = re.findall(measure_pattern, expression)

                        # Get all column names from column_refs to check against
                        column_names_only = {ref.split('[')[1].rstrip(']') for ref in column_refs}

                        for match in measure_matches:
                            # Skip if this is the measure itself or if we already found it as a column
                            if match != measure_name and match not in column_names_only:
                                measure_refs.add(match)

                    # Create dependency info
                    full_measure_name = f"{table_name}[{measure_name}]"
                    # Handle None expressions - ensure we have a string
                    safe_expression = expression if expression else ""
                    truncated_expression = safe_expression[:200] + "..." if len(safe_expression) > 200 else safe_expression

                    measure_deps[full_measure_name] = MeasureDependency(
                        expression=truncated_expression,
                        table=table_name,
                        dependencies=DependencyInfo(
                            measures=list(measure_refs),
                            columns=list(column_refs)  # Already in "Table[Column]" format
                        ),
                        referenced_by=ReferencedBy(measures=[], count=0)
                    )

                logger.info(f"    ✓ Extracted {len(measure_deps)} measure dependencies")

            # Get all columns
            logger.info("  - Extracting column dependencies...")
            columns_result = self.query_executor.validate_and_execute_dax("EVALUATE INFO.COLUMNS()", top_n=0, bypass_cache=True)

            if columns_result.get('success'):
                for row in columns_result.get('rows', []):
                    table_name = row.get('[TableName]', row.get('TableName', ''))
                    column_name = row.get('[Name]', row.get('Name', ''))
                    data_type = row.get('[DataType]', row.get('DataType', 'Unknown'))

                    full_column_name = f"{table_name}[{column_name}]"
                    column_deps[full_column_name] = ColumnDependency(
                        table=table_name,
                        data_type=data_type,
                        used_in_measures=[],  # TODO: Parse from measure expressions
                        used_in_relationships=False,  # TODO: Check relationships
                        used_in_rls=False,  # TODO: Check RLS
                        usage_count=0
                    )

                logger.info(f"    ✓ Extracted {len(column_deps)} column dependencies")

            # Get table dependencies
            logger.info("  - Extracting table dependencies...")
            for table in tables:
                table_deps[table] = TableDependency(
                    type="dimension",  # TODO: Detect fact vs dimension
                    relationships={},
                    used_in_measures=0,  # TODO: Count from measure dependencies
                    used_in_rls=False,
                    critical=False
                )

        return Dependencies(
            measures=measure_deps,
            columns=column_deps,
            tables=table_deps,
            summary={
                "total_measures": len(measure_deps),
                "max_dependency_depth": 0,  # TODO: Calculate actual depth
                "circular_references": [],  # TODO: Detect circular refs
                "orphan_measures": [],  # TODO: Find orphaned measures
                "critical_objects": []  # TODO: Identify critical objects
            }
        )

    def _get_physical_columns(self, table_name: str) -> List[str]:
        """
        Get list of physical columns (exclude calculated columns) from TMDL

        Args:
            table_name: Table name

        Returns:
            List of physical column names (empty list means fallback to querying all columns)
        """
        try:
            # Try method 1: Parse TMDL file for sourceColumn properties
            if hasattr(self, 'tmdl_dir') and self.tmdl_dir:
                table_tmdl_path = self.tmdl_dir / "tables" / f"{table_name}.tmdl"
                if table_tmdl_path.exists():
                    physical_columns = []
                    with open(table_tmdl_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Parse columns with sourceColumn property (physical columns)
                    import re
                    # Pattern: column '<name>' or column <name> followed by sourceColumn: <name>
                    pattern = r"column\s+(?:'([^']+)'|([^\s=]+))\s*\n(?:.*\n)*?\s*sourceColumn:"
                    matches = re.finditer(pattern, content, re.MULTILINE)

                    for match in matches:
                        col_name = match.group(1) or match.group(2)
                        if col_name and col_name not in physical_columns:
                            physical_columns.append(col_name)

                    if physical_columns:
                        return physical_columns

            # Method 2: Use catalog metadata if available
            if hasattr(self, '_catalog') and self._catalog:
                table_info = next((t for t in self._catalog.get('tables', []) if t.get('name') == table_name), None)
                if table_info:
                    columns = table_info.get('columns', [])
                    # Filter out calculated columns
                    physical_cols = [c.get('name') for c in columns if not c.get('is_calculated', False)]
                    if physical_cols:
                        return physical_cols

            # Fallback: return empty list (will query all columns or skip if measures-only)
            return []

        except Exception as e:
            logger.debug(f"Error getting physical columns for '{table_name}': {e}")
            return []  # Return empty list on error

    def _extract_sample_data(
        self,
        tables: List[str],
        sample_rows: int,
        compression: str
    ) -> int:
        """
        Extract sample data for tables with file size management

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
        skipped_tables = {
            "measures_only": [],
            "empty": [],
            "failed": [],
            "too_large": []
        }
        logger.info(f"Extracting sample data for {len(tables)} tables (max {sample_rows} rows per table)...")

        for idx, table in enumerate(tables, 1):
            try:
                # Escape single quotes in table and column names
                escaped_table = table.replace("'", "''")

                # Get physical columns (exclude calculated columns) to avoid calculated column errors
                physical_columns = self._get_physical_columns(table)

                # Build DAX query
                if physical_columns:
                    # Use SELECTCOLUMNS with only physical columns to avoid calculated column errors
                    # Limit to first 50 columns to avoid query length issues
                    columns_to_query = physical_columns[:50]
                    column_selects = ", ".join([f'"{col}", [{col}]' for col in columns_to_query])
                    dax_query = f"EVALUATE SELECTCOLUMNS('{escaped_table}', {column_selects})"
                else:
                    # Fallback to simple EVALUATE (for tables where we couldn't get column info)
                    dax_query = f"EVALUATE '{escaped_table}'"

                # Execute query
                result = self.query_executor.validate_and_execute_dax(dax_query, top_n=sample_rows, bypass_cache=True)

                if not result.get('success'):
                    error_msg = result.get('error', '')

                    # Check if it's a measures-only table (no columns)
                    if 'cannot be used in computations because it does not have any columns' in error_msg:
                        logger.debug(f"  [{idx}/{len(tables)}] - Skipping '{table}' (measures-only table)")
                        skipped_tables["measures_only"].append(table)
                        continue

                    # If SELECTCOLUMNS failed, try simple EVALUATE as fallback
                    if physical_columns and ('SELECTCOLUMNS' in error_msg or 'syntax' in error_msg.lower()):
                        logger.debug(f"  [{idx}/{len(tables)}] - SELECTCOLUMNS failed, trying simple EVALUATE...")
                        dax_query = f"EVALUATE '{escaped_table}'"
                        result = self.query_executor.validate_and_execute_dax(dax_query, top_n=sample_rows, bypass_cache=True)

                    if not result.get('success'):
                        logger.warning(f"  [{idx}/{len(tables)}] ✗ Failed to extract from '{table}': {result.get('error')}")
                        skipped_tables["failed"].append(f"{table}: {result.get('error', 'Unknown error')[:100]}")
                        continue

                rows = result.get('rows', [])
                if not rows:
                    logger.debug(f"  [{idx}/{len(tables)}] - Table '{table}' is empty")
                    skipped_tables["empty"].append(table)
                    continue

                # Convert to polars DataFrame (scan all rows for schema inference)
                df = pl.DataFrame(rows, infer_schema_length=None)

                # Write to parquet file (with file size checking)
                parquet_path = self.sample_data_dir / f"{table}.parquet"
                df.write_parquet(
                    parquet_path,
                    compression=compression,
                    use_pyarrow=False  # Use polars native writer (faster)
                )

                # Check file size and split if too large
                file_size = parquet_path.stat().st_size
                max_size = 50 * 1024 * 1024  # 50 MB limit for parquet files

                if file_size > max_size:
                    logger.info(f"  [{idx}/{len(tables)}] Table '{table}' is too large ({file_size / 1024 / 1024:.1f}MB), splitting...")
                    try:
                        self._split_large_parquet(table, df, parquet_path, max_size, compression)
                        parquet_count += 1  # Count split files as successful
                    except Exception as split_error:
                        logger.warning(f"  [{idx}/{len(tables)}] ✗ Failed to split '{table}': {split_error}")
                        skipped_tables["too_large"].append(f"{table}: {file_size / 1024 / 1024:.1f}MB")
                        # Remove the original large file
                        if parquet_path.exists():
                            parquet_path.unlink()
                else:
                    parquet_count += 1
                    logger.debug(f"  [{idx}/{len(tables)}] ✓ Extracted '{table}' ({len(rows)} rows, {file_size / 1024:.1f}KB)")

                if idx % 10 == 0:
                    logger.info(f"  Progress: {idx}/{len(tables)} tables processed, {parquet_count} files created")

            except Exception as e:
                logger.warning(f"  [{idx}/{len(tables)}] ✗ Error extracting from '{table}': {e}")
                skipped_tables["failed"].append(f"{table}: {str(e)[:100]}")
                continue

        # Summary report
        logger.info(f"✓ Sample data extraction complete:")
        logger.info(f"  - Successfully extracted: {parquet_count} parquet files")
        total_skipped = sum(len(v) for v in skipped_tables.values())
        logger.info(f"  - Skipped tables: {total_skipped}")

        if skipped_tables["measures_only"]:
            logger.info(f"    • Measures-only: {len(skipped_tables['measures_only'])} tables")
        if skipped_tables["empty"]:
            logger.info(f"    • Empty: {len(skipped_tables['empty'])} tables")
        if skipped_tables["failed"]:
            logger.info(f"    • Failed: {len(skipped_tables['failed'])} tables")
            for failure in skipped_tables["failed"][:5]:  # Show first 5
                logger.info(f"      - {failure}")
            if len(skipped_tables["failed"]) > 5:
                logger.info(f"      ... and {len(skipped_tables['failed']) - 5} more")
        if skipped_tables["too_large"]:
            logger.info(f"    • Too large: {len(skipped_tables['too_large'])} tables")
            for large in skipped_tables["too_large"]:
                logger.info(f"      - {large}")

        logger.info(f"  - Total tables: {len(tables)}")
        return parquet_count

    def _split_large_parquet(
        self,
        table_name: str,
        df,
        original_path: Path,
        max_size: int,
        compression: str
    ):
        """
        Split large parquet file into multiple smaller files

        Args:
            table_name: Table name
            df: Polars DataFrame
            original_path: Path to original (large) parquet file
            max_size: Maximum file size in bytes
            compression: Compression algorithm
        """
        import polars as pl

        # Get file size before removing it
        file_size = original_path.stat().st_size if original_path.exists() else max_size

        # Remove original large file
        if original_path.exists():
            original_path.unlink()

        # Calculate rows per chunk (estimate)
        total_rows = len(df)
        estimated_rows_per_chunk = max(100, int((max_size / file_size) * total_rows * 0.8))  # 80% safety margin

        logger.info(f"    Splitting {total_rows} rows into chunks of ~{estimated_rows_per_chunk} rows")

        # Split into chunks
        chunk_num = 0
        for start_idx in range(0, total_rows, estimated_rows_per_chunk):
            end_idx = min(start_idx + estimated_rows_per_chunk, total_rows)
            chunk_df = df[start_idx:end_idx]

            chunk_path = self.sample_data_dir / f"{table_name}_part{chunk_num}.parquet"
            chunk_df.write_parquet(
                chunk_path,
                compression=compression,
                use_pyarrow=False
            )

            chunk_size = chunk_path.stat().st_size
            logger.info(f"    Created {chunk_path.name} ({chunk_size / 1024:.1f}KB, {len(chunk_df)} rows)")
            chunk_num += 1

        logger.info(f"    ✓ Split into {chunk_num} files")

    def _write_json(self, path: Path, data: Dict[str, Any]):
        """Write JSON file using orjson if available"""
        # Use centralized JSON utility with orjson optimization
        json_str = dumps_json(data)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json_str)

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
        # Serialize to check size using centralized JSON utility
        serialized = dumps_json(data).encode('utf-8')
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
            file_type: "catalog", "measures", or "dependencies"
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

        elif file_type == "measures":
            # Split by measures
            measures = data.get("measures", [])
            items_per_part = max(1, len(measures) // ((total_size // MAX_FILE_SIZE) + 1))

            for i in range(0, len(measures), items_per_part):
                part_data = {
                    "measures": measures[i:i + items_per_part],
                    "total_count": data.get("total_count", 0) if i == 0 else 0
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
