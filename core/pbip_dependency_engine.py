"""
PBIP Dependency Engine - Comprehensive dependency analysis for PBIP projects.

This module analyzes dependencies between measures, columns, and visuals, building
a complete dependency graph for the Power BI model and report.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional, Any

# Import existing DAX parser
try:
    from .dax_parser import DaxReferenceIndex, parse_dax_references
    DAX_PARSER_AVAILABLE = True
except ImportError:
    DAX_PARSER_AVAILABLE = False
    logging.warning("DAX parser not available; dependency analysis will be limited")

logger = logging.getLogger(__name__)


class PbipDependencyEngine:
    """Comprehensive dependency analysis for PBIP projects."""

    def __init__(self, model_data: Dict, report_data: Optional[Dict] = None):
        """
        Initialize with parsed model and optional report data.

        Args:
            model_data: Parsed model data from TmdlModelAnalyzer
            report_data: Optional parsed report data from PbirReportAnalyzer
        """
        self.model = model_data
        self.report = report_data
        self.logger = logger

        # Dependency maps
        self.measure_to_measure: Dict[str, List[str]] = {}  # Forward: measure -> measures it depends on
        self.measure_to_measure_reverse: Dict[str, List[str]] = {}  # Reverse: measure -> measures that depend on it
        self.measure_to_column: Dict[str, List[str]] = {}
        self.column_to_measure: Dict[str, List[str]] = {}
        self.visual_dependencies: Dict[str, Dict[str, List[str]]] = {}
        self.page_dependencies: Dict[str, Dict[str, Any]] = {}

        # Build reference index for DAX parsing
        self.reference_index: Optional[DaxReferenceIndex] = None
        if DAX_PARSER_AVAILABLE:
            self._build_reference_index()

    def _build_reference_index(self) -> None:
        """Build reference index from model data for DAX parsing."""
        if not DAX_PARSER_AVAILABLE:
            return

        measure_rows = []
        column_rows = []

        # Extract measures
        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for measure in table.get("measures", []):
                measure_rows.append({
                    "Table": table_name,
                    "Name": measure.get("name", "")
                })

            for column in table.get("columns", []):
                column_rows.append({
                    "Table": table_name,
                    "Name": column.get("name", "")
                })

        self.reference_index = DaxReferenceIndex(measure_rows, column_rows)

    def analyze_all_dependencies(self) -> Dict[str, Any]:
        """
        Perform comprehensive dependency analysis.

        Returns:
            Dictionary with all dependency information
        """
        self.logger.info("Starting comprehensive dependency analysis")

        # Analyze model dependencies
        self._analyze_measure_dependencies()
        self._analyze_column_usage()
        self._build_reverse_indices()

        # Analyze report dependencies (if report data available)
        if self.report:
            self._analyze_visual_dependencies()
            self._analyze_page_dependencies()

        # Find unused objects
        unused = self._find_unused_objects()

        result = {
            "measure_to_measure": self.measure_to_measure,
            "measure_to_measure_reverse": self.measure_to_measure_reverse,
            "measure_to_column": self.measure_to_column,
            "column_to_measure": self.column_to_measure,
            "visual_dependencies": self.visual_dependencies,
            "page_dependencies": self.page_dependencies,
            "unused_measures": unused["measures"],
            "unused_columns": unused["columns"],
            "summary": {
                "total_measures": self._count_measures(),
                "total_columns": self._count_columns(),
                "total_tables": len(self.model.get("tables", [])),
                "total_relationships": len(self.model.get("relationships", [])),
                "measures_with_dependencies": len(self.measure_to_measure),
                "columns_used_in_measures": len(self.column_to_measure),
                "unused_measures": len(unused["measures"]),
                "unused_columns": len(unused["columns"])
            }
        }

        if self.report:
            result["summary"]["total_pages"] = len(self.report.get("pages", []))
            result["summary"]["total_visuals"] = sum(
                len(p.get("visuals", []))
                for p in self.report.get("pages", [])
            )

        self.logger.info(
            f"Dependency analysis complete: "
            f"{result['summary']['total_measures']} measures, "
            f"{result['summary']['total_columns']} columns"
        )

        return result

    def _analyze_measure_dependencies(self) -> None:
        """Analyze measure-to-measure and measure-to-column dependencies."""
        if not DAX_PARSER_AVAILABLE:
            self.logger.warning(
                "DAX parser not available; skipping measure dependency analysis"
            )
            return

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for measure in table.get("measures", []):
                measure_name = measure.get("name", "")
                measure_key = f"{table_name}[{measure_name}]"
                expression = measure.get("expression", "")

                if not expression:
                    continue

                # Parse DAX expression
                refs = parse_dax_references(expression, self.reference_index)

                # Extract measure dependencies
                measure_deps = []
                for ref_table, ref_measure in refs.get("measures", []):
                    if ref_table and ref_measure:
                        ref_key = f"{ref_table}[{ref_measure}]"
                        # Don't add self-references
                        if ref_key != measure_key:
                            measure_deps.append(ref_key)

                if measure_deps:
                    self.measure_to_measure[measure_key] = measure_deps

                # Extract column dependencies
                column_deps = []
                for ref_table, ref_column in refs.get("columns", []):
                    if ref_table and ref_column:
                        ref_key = f"{ref_table}[{ref_column}]"
                        column_deps.append(ref_key)

                if column_deps:
                    self.measure_to_column[measure_key] = column_deps

    def _analyze_column_usage(self) -> None:
        """Analyze calculated column dependencies."""
        if not DAX_PARSER_AVAILABLE:
            return

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for column in table.get("columns", []):
                expression = column.get("expression", "")

                if not expression:
                    continue

                column_name = column.get("name", "")
                column_key = f"{table_name}[{column_name}]"

                # Parse expression
                refs = parse_dax_references(expression, self.reference_index)

                # Track column-to-column dependencies
                for ref_table, ref_column in refs.get("columns", []):
                    if ref_table and ref_column:
                        ref_key = f"{ref_table}[{ref_column}]"
                        if ref_key != column_key:
                            # Store in column_to_measure for now
                            # (could create separate column_to_column map)
                            if ref_key not in self.column_to_measure:
                                self.column_to_measure[ref_key] = []
                            if column_key not in self.column_to_measure[ref_key]:
                                self.column_to_measure[ref_key].append(column_key)

    def _build_reverse_indices(self) -> None:
        """Build reverse indices for dependency lookups."""
        # Build measure_to_measure_reverse index (used by)
        for measure_key, deps in self.measure_to_measure.items():
            for dep_measure_key in deps:
                if dep_measure_key not in self.measure_to_measure_reverse:
                    self.measure_to_measure_reverse[dep_measure_key] = []
                if measure_key not in self.measure_to_measure_reverse[dep_measure_key]:
                    self.measure_to_measure_reverse[dep_measure_key].append(measure_key)

        # Build column_to_measure reverse index
        for measure_key, column_deps in self.measure_to_column.items():
            for column_key in column_deps:
                if column_key not in self.column_to_measure:
                    self.column_to_measure[column_key] = []
                if measure_key not in self.column_to_measure[column_key]:
                    self.column_to_measure[column_key].append(measure_key)

    def _analyze_visual_dependencies(self) -> None:
        """Analyze visual-level field usage."""
        if not self.report:
            return

        for page in self.report.get("pages", []):
            page_name = page.get("display_name", page.get("id", ""))

            for visual in page.get("visuals", []):
                visual_id = visual.get("id", "")
                visual_type = visual.get("visual_type", "")
                visual_key = f"{page_name}/{visual_id}"

                fields = visual.get("fields", {})

                visual_deps = {
                    "page": page_name,
                    "visual_id": visual_id,
                    "visual_type": visual_type,
                    "measures": [],
                    "columns": [],
                    "tables": set()
                }

                # Extract columns
                for col in fields.get("columns", []):
                    table = col.get("table", "")
                    column = col.get("column", "")
                    if table and column:
                        col_key = f"{table}[{column}]"
                        visual_deps["columns"].append(col_key)
                        visual_deps["tables"].add(table)

                # Extract measures
                for meas in fields.get("measures", []):
                    table = meas.get("table", "")
                    measure = meas.get("measure", "")
                    if table and measure:
                        meas_key = f"{table}[{measure}]"
                        visual_deps["measures"].append(meas_key)
                        visual_deps["tables"].add(table)

                # Convert set to list for JSON serialization
                visual_deps["tables"] = list(visual_deps["tables"])

                self.visual_dependencies[visual_key] = visual_deps

    def _analyze_page_dependencies(self) -> None:
        """Analyze page-level dependencies (aggregate of all visuals)."""
        if not self.report:
            return

        for page in self.report.get("pages", []):
            page_name = page.get("display_name", page.get("id", ""))

            page_deps = {
                "measures": set(),
                "columns": set(),
                "tables": set(),
                "visual_count": len(page.get("visuals", [])),
                "filter_count": len(page.get("filters", []))
            }

            # Aggregate from visuals
            for visual in page.get("visuals", []):
                fields = visual.get("fields", {})

                for col in fields.get("columns", []):
                    table = col.get("table", "")
                    column = col.get("column", "")
                    if table and column:
                        page_deps["columns"].add(f"{table}[{column}]")
                        page_deps["tables"].add(table)

                for meas in fields.get("measures", []):
                    table = meas.get("table", "")
                    measure = meas.get("measure", "")
                    if table and measure:
                        page_deps["measures"].add(f"{table}[{measure}]")
                        page_deps["tables"].add(table)

            # Add page filters
            for filt in page.get("filters", []):
                field = filt.get("field", {})
                table = field.get("table", "")
                name = field.get("name", "")
                field_type = field.get("type", "")

                if table and name:
                    page_deps["tables"].add(table)
                    if field_type == "Column":
                        page_deps["columns"].add(f"{table}[{name}]")
                    elif field_type == "Measure":
                        page_deps["measures"].add(f"{table}[{name}]")

            # Convert sets to lists
            self.page_dependencies[page_name] = {
                "measures": list(page_deps["measures"]),
                "columns": list(page_deps["columns"]),
                "tables": list(page_deps["tables"]),
                "visual_count": page_deps["visual_count"],
                "filter_count": page_deps["filter_count"]
            }

    def _find_unused_objects(self) -> Dict[str, List[str]]:
        """Find measures and columns not used anywhere."""
        # Build set of used measures
        used_measures = set()

        # Used in other measures
        for deps in self.measure_to_measure.values():
            used_measures.update(deps)

        # Used in visuals
        if self.report:
            for visual_deps in self.visual_dependencies.values():
                used_measures.update(visual_deps.get("measures", []))

        # Build set of used columns
        used_columns = set()

        # Used in measures (from DAX expressions)
        for deps in self.measure_to_column.values():
            used_columns.update(deps)

        # Used by other columns (calculated columns)
        for column_key, measure_deps in self.column_to_measure.items():
            if measure_deps:  # If this column is referenced by any measure/column
                used_columns.add(column_key)

        # Used in relationships
        for rel in self.model.get("relationships", []):
            from_table = rel.get("from_table", "")
            from_col = rel.get("from_column_name", "")
            to_table = rel.get("to_table", "")
            to_col = rel.get("to_column_name", "")

            if from_table and from_col:
                used_columns.add(f"{from_table}[{from_col}]")
            if to_table and to_col:
                used_columns.add(f"{to_table}[{to_col}]")

        # Used in visuals (directly in visual fields)
        if self.report:
            for visual_deps in self.visual_dependencies.values():
                used_columns.update(visual_deps.get("columns", []))

        # Also check page filters for column usage
        if self.report:
            for page_deps in self.page_dependencies.values():
                for filter_info in page_deps.get("filters", []):
                    field = filter_info.get("field", {})
                    table = field.get("table", "")
                    column = field.get("name", "")
                    if table and column:
                        used_columns.add(f"{table}[{column}]")

        # Find unused
        all_measures = []
        all_columns = []

        for table in self.model.get("tables", []):
            table_name = table.get("name", "")

            for measure in table.get("measures", []):
                measure_key = f"{table_name}[{measure.get('name', '')}]"
                all_measures.append(measure_key)

            for column in table.get("columns", []):
                column_name = column.get("name", "")
                column_key = f"{table_name}[{column_name}]"

                # Always include columns in the check (don't skip hidden or key columns)
                # They may still be used in relationships or calculations
                all_columns.append(column_key)

        unused_measures = [m for m in all_measures if m not in used_measures]
        unused_columns = [c for c in all_columns if c not in used_columns]

        return {
            "measures": unused_measures,
            "columns": unused_columns
        }

    def _count_measures(self) -> int:
        """Count total measures in model."""
        return sum(
            len(table.get("measures", []))
            for table in self.model.get("tables", [])
        )

    def _count_columns(self) -> int:
        """Count total columns in model."""
        return sum(
            len(table.get("columns", []))
            for table in self.model.get("tables", [])
        )

    def get_measure_impact(self, measure_key: str) -> Dict[str, Any]:
        """
        Calculate impact of a specific measure (what depends on it).

        Args:
            measure_key: Measure identifier (e.g., "Table[Measure]")

        Returns:
            Dictionary with impact analysis
        """
        impact = {
            "measure": measure_key,
            "used_by_measures": [],
            "used_in_visuals": [],
            "used_in_pages": set(),
            "total_impact": 0
        }

        # Find measures that depend on this one
        for meas_key, deps in self.measure_to_measure.items():
            if measure_key in deps:
                impact["used_by_measures"].append(meas_key)

        # Find visuals using this measure
        for visual_key, visual_deps in self.visual_dependencies.items():
            if measure_key in visual_deps.get("measures", []):
                impact["used_in_visuals"].append(visual_key)
                page = visual_deps.get("page", "")
                if page:
                    impact["used_in_pages"].add(page)

        impact["used_in_pages"] = list(impact["used_in_pages"])
        impact["total_impact"] = (
            len(impact["used_by_measures"]) + len(impact["used_in_visuals"])
        )

        return impact

    def calculate_dependency_depth(self, measure_key: str) -> int:
        """
        Calculate maximum dependency depth for a measure.

        Args:
            measure_key: Measure identifier

        Returns:
            Maximum depth (0 if no dependencies)
        """
        visited = set()

        def dfs(key: str, depth: int) -> int:
            if key in visited:
                return depth
            visited.add(key)

            deps = self.measure_to_measure.get(key, [])
            if not deps:
                return depth

            max_depth = depth
            for dep in deps:
                max_depth = max(max_depth, dfs(dep, depth + 1))

            return max_depth

        return dfs(measure_key, 0)
