"""
Hybrid Reader - Read and analyze hybrid analysis packages

Provides efficient reading of hybrid analysis packages with automatic
multi-part file reassembly and intelligent caching.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Try to import orjson for faster JSON parsing
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

logger = logging.getLogger(__name__)


class HybridReader:
    """Read and analyze hybrid analysis package"""

    def __init__(self, analysis_path: str):
        """
        Initialize hybrid reader

        Args:
            analysis_path: Path to exported analysis folder
        """
        self.analysis_path = Path(analysis_path)
        self.analysis_dir = self.analysis_path / "analysis"
        self.tmdl_dir = self.analysis_path / "tmdl"
        self.sample_data_dir = self.analysis_path / "sample_data"

        # Validate structure
        if not self.analysis_path.exists():
            raise ValueError(f"Analysis path not found: {analysis_path}")

        # Detect format type
        test_metadata_path = self.analysis_path / "test_metadata.json"
        if test_metadata_path.exists():
            # test_metadata_extraction format
            self.format_type = "test_metadata"
            logger.info(f"Detected test_metadata format at {analysis_path}")
        elif self.analysis_dir.exists():
            # Full hybrid analysis format
            self.format_type = "hybrid_analysis"
            logger.info(f"Detected hybrid_analysis format at {analysis_path}")
        else:
            raise ValueError(f"Invalid analysis structure - expected either test_metadata.json or analysis/ folder at {analysis_path}")

        # Cache for loaded files
        self._cache = {}

    def read_metadata(self) -> Dict[str, Any]:
        """
        Read metadata.json (supports both formats)

        Returns:
            Metadata dictionary
        """
        if "metadata" not in self._cache:
            if self.format_type == "test_metadata":
                # Read test_metadata.json
                metadata_path = self.analysis_path / "test_metadata.json"
                self._cache["metadata"] = self._read_json(metadata_path)
            else:
                # Read analysis/metadata.json
                metadata_path = self.analysis_dir / "metadata.json"
                self._cache["metadata"] = self._read_json(metadata_path)
        return self._cache["metadata"]

    def read_catalog(self, object_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Read catalog.json (with automatic multi-part reassembly)
        For test_metadata format, returns minimal catalog with table names and row counts

        Args:
            object_filter: Optional filter for selective loading

        Returns:
            Catalog dictionary
        """
        if "catalog" not in self._cache:
            if self.format_type == "test_metadata":
                # Build minimal catalog from test_metadata.json
                metadata = self.read_metadata()
                row_counts = metadata.get("row_counts", {})

                # Create minimal catalog with table info
                tables = []
                for table_name, row_count in row_counts.items():
                    tables.append({
                        "name": table_name,
                        "row_count": row_count,
                        "type": "table"
                    })

                self._cache["catalog"] = {
                    "tables": tables,
                    "measures": [],  # Not available in test_metadata
                    "columns": [],   # Not available in test_metadata
                    "summary": {
                        "total_tables": len(tables),
                        "total_measures": metadata.get("measures_count", 0),
                        "total_columns": metadata.get("columns_count", 0),
                        "total_rows": metadata.get("total_rows", 0),
                        "note": "Limited catalog from test_metadata format - only table names and row counts available"
                    }
                }
            else:
                # Full hybrid analysis format
                catalog_path = self.analysis_dir / "catalog.json"
                manifest_path = self.analysis_dir / "catalog.manifest.json"

                if catalog_path.exists():
                    # Single file
                    self._cache["catalog"] = self._read_json(catalog_path)
                elif manifest_path.exists():
                    # Multi-part file - reassemble
                    self._cache["catalog"] = self._reassemble_multipart("catalog")
                else:
                    raise ValueError("Catalog file not found (neither single file nor manifest)")

        # Apply filter if provided
        if object_filter:
            return self._filter_catalog(self._cache["catalog"], object_filter)

        return self._cache["catalog"]

    def read_dependencies(self) -> Dict[str, Any]:
        """
        Read dependencies.json (with automatic multi-part reassembly)
        For test_metadata format, returns empty dependencies

        Returns:
            Dependencies dictionary
        """
        if "dependencies" not in self._cache:
            if self.format_type == "test_metadata":
                # test_metadata format doesn't include dependencies
                self._cache["dependencies"] = {
                    "dependencies": [],
                    "note": "Dependencies not available in test_metadata format"
                }
            else:
                # Full hybrid analysis format
                dependencies_path = self.analysis_dir / "dependencies.json"
                manifest_path = self.analysis_dir / "dependencies.manifest.json"

                if dependencies_path.exists():
                    # Single file
                    self._cache["dependencies"] = self._read_json(dependencies_path)
                elif manifest_path.exists():
                    # Multi-part file - reassemble
                    self._cache["dependencies"] = self._reassemble_multipart("dependencies")
                else:
                    raise ValueError("Dependencies file not found (neither single file nor manifest)")

        return self._cache["dependencies"]

    def read_tmdl_file(self, relative_path: str) -> str:
        """
        Read TMDL file content
        Not available for test_metadata format

        Args:
            relative_path: Relative path from tmdl directory (e.g., "tables/DimDate.tmdl")

        Returns:
            TMDL file content
        """
        if self.format_type == "test_metadata":
            raise ValueError("TMDL files not available in test_metadata format. Use full hybrid analysis export for TMDL access.")

        tmdl_path = self.tmdl_dir / relative_path
        if not tmdl_path.exists():
            raise ValueError(f"TMDL file not found: {relative_path}")

        with open(tmdl_path, 'r', encoding='utf-8') as f:
            return f.read()

    def list_sample_data_tables(self) -> List[str]:
        """
        List tables with available sample data (parquet files)

        Returns:
            List of table names with sample data
        """
        if not self.sample_data_dir.exists():
            return []

        # Find all .parquet files in sample_data directory
        parquet_files = list(self.sample_data_dir.glob("*.parquet"))
        return [f.stem for f in parquet_files]

    def read_sample_data(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Read sample data for table (parquet file)

        Args:
            table_name: Table name

        Returns:
            Sample data as dictionary or None if not available
        """
        if not self.sample_data_dir.exists():
            return None

        parquet_path = self.sample_data_dir / f"{table_name}.parquet"
        if not parquet_path.exists():
            return None

        try:
            import polars as pl
            df = pl.read_parquet(parquet_path)
            return {
                "columns": df.columns,
                "row_count": len(df),
                "data": df.to_dicts()[:100]  # Limit to 100 rows for MCP response
            }
        except ImportError:
            logger.warning("Polars not available, cannot read sample data")
            return None
        except Exception as e:
            logger.error(f"Error reading sample data for {table_name}: {e}")
            return None

    def find_objects(
        self,
        object_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find objects matching filters

        Args:
            object_type: "tables" | "measures" | "relationships" | "roles"
            filters: Optional filters (name_pattern, folder, etc.)

        Returns:
            List of matching objects
        """
        catalog = self.read_catalog()

        if object_type == "tables":
            objects = catalog.get("tables", [])
        elif object_type == "measures":
            objects = catalog.get("measures", [])
        elif object_type == "roles":
            objects = catalog.get("roles", [])
        else:
            return []

        # Apply filters
        if filters:
            objects = self._apply_filters(objects, filters)

        return objects

    def get_object_definition(
        self,
        object_name: str,
        object_type: str
    ) -> Dict[str, Any]:
        """
        Get full TMDL definition for an object

        Args:
            object_name: Object name
            object_type: "table" | "measure" | "role"

        Returns:
            Object definition with TMDL content
        """
        catalog = self.read_catalog()

        if object_type == "table":
            tables = catalog.get("tables", [])
            for table in tables:
                if table["name"] == object_name:
                    tmdl_content = self.read_tmdl_file(table["tmdl_path"].replace("tmdl/", ""))
                    return {
                        "name": object_name,
                        "type": "table",
                        "metadata": table,
                        "tmdl": tmdl_content
                    }

        elif object_type == "measure":
            measures = catalog.get("measures", [])
            for measure in measures:
                if measure["name"] == object_name:
                    tmdl_content = self.read_tmdl_file(measure["tmdl_path"].replace("tmdl/", ""))
                    return {
                        "name": object_name,
                        "type": "measure",
                        "metadata": measure,
                        "tmdl": tmdl_content
                    }

        raise ValueError(f"{object_type} '{object_name}' not found")

    def analyze_dependencies(
        self,
        object_name: str,
        direction: str = "both"
    ) -> Dict[str, Any]:
        """
        Analyze dependencies for an object

        Args:
            object_name: Object name (table, measure, column)
            direction: "dependencies" | "referenced_by" | "both"

        Returns:
            Dependency information
        """
        dependencies = self.read_dependencies()

        # Search in measures, columns, tables
        for category in ["measures", "columns", "tables"]:
            if object_name in dependencies.get(category, {}):
                dep_info = dependencies[category][object_name]

                result = {
                    "object": object_name,
                    "category": category
                }

                if direction in ["dependencies", "both"]:
                    result["dependencies"] = dep_info.get("dependencies", {})

                if direction in ["referenced_by", "both"]:
                    result["referenced_by"] = dep_info.get("referenced_by", {})

                return result

        return {
            "object": object_name,
            "found": False,
            "message": f"Object '{object_name}' not found in dependencies"
        }

    def _read_json(self, path: Path) -> Dict[str, Any]:
        """Read JSON file using orjson if available"""
        if HAS_ORJSON:
            with open(path, 'rb') as f:
                return orjson.loads(f.read())
        else:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _reassemble_multipart(self, file_type: str) -> Dict[str, Any]:
        """
        Reassemble multi-part file

        Args:
            file_type: "catalog" or "dependencies"

        Returns:
            Complete reassembled dictionary
        """
        manifest_path = self.analysis_dir / f"{file_type}.manifest.json"
        manifest = self._read_json(manifest_path)

        logger.info(f"Reassembling {file_type} from {manifest['total_parts']} parts")

        # Load all parts
        parts_data = []
        for part_info in manifest["parts"]:
            part_path = self.analysis_dir / part_info["filename"]
            part_data = self._read_json(part_path)
            parts_data.append(part_data)

        # Merge based on file type
        if file_type == "catalog":
            return self._merge_catalog_parts(parts_data)
        elif file_type == "dependencies":
            return self._merge_dependencies_parts(parts_data)
        else:
            raise ValueError(f"Unknown file type: {file_type}")

    def _merge_catalog_parts(self, parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge catalog parts into single structure"""
        merged = {
            "tables": [],
            "measures": [],
            "relationships_path": "",
            "roles": [],
            "optimization_summary": {}
        }

        for part in parts:
            merged["tables"].extend(part.get("tables", []))
            # Only take measures, roles, etc. from first part
            if part.get("measures"):
                merged["measures"] = part["measures"]
            if part.get("relationships_path"):
                merged["relationships_path"] = part["relationships_path"]
            if part.get("roles"):
                merged["roles"] = part["roles"]
            if part.get("optimization_summary"):
                merged["optimization_summary"] = part["optimization_summary"]

        return merged

    def _merge_dependencies_parts(self, parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge dependencies parts into single structure"""
        merged = {
            "measures": {},
            "columns": {},
            "tables": {},
            "summary": {}
        }

        for part in parts:
            merged["measures"].update(part.get("measures", {}))
            # Only take columns, tables, summary from first part
            if part.get("columns"):
                merged["columns"] = part["columns"]
            if part.get("tables"):
                merged["tables"] = part["tables"]
            if part.get("summary"):
                merged["summary"] = part["summary"]

        return merged

    def _filter_catalog(
        self,
        catalog: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply filters to catalog"""
        # TODO: Implement filtering logic
        return catalog

    def _apply_filters(
        self,
        objects: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to object list"""
        result = objects

        # Filter by name pattern
        if "name_pattern" in filters:
            import re
            pattern = re.compile(filters["name_pattern"])
            result = [obj for obj in result if pattern.search(obj.get("name", ""))]

        # Filter by folder (for measures)
        if "folder" in filters:
            result = [obj for obj in result if obj.get("display_folder") == filters["folder"]]

        # Filter by table
        if "table" in filters:
            result = [obj for obj in result if obj.get("table") == filters["table"]]

        # Filter by hidden
        if "is_hidden" in filters:
            result = [obj for obj in result if obj.get("is_hidden") == filters["is_hidden"]]

        return result
