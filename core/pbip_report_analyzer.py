"""
PBIR Report Analyzer - Parses PBIR report definitions and extracts visual metadata.

This module provides comprehensive parsing of Power BI Report (PBIR) definitions
including pages, visuals, bookmarks, and field references.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Use orjson for 2-5x faster JSON parsing
try:
    import orjson
    def load_json(file_path: str) -> Dict:
        """Load JSON using orjson for performance."""
        with open(file_path, 'rb') as f:
            return orjson.loads(f.read())
except ImportError:
    import json
    def load_json(file_path: str) -> Dict:
        """Fallback to standard json library."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

logger = logging.getLogger(__name__)


class PbirReportAnalyzer:
    """Parses PBIR report definitions and extracts visual metadata."""

    def __init__(self):
        """Initialize the report analyzer."""
        self.logger = logger

    def analyze_report(self, report_folder: str) -> Dict[str, Any]:
        """
        Parse all report definition files.

        Args:
            report_folder: Path to the .Report folder

        Returns:
            Dictionary with complete report structure

        Raises:
            FileNotFoundError: If report folder doesn't exist
            ValueError: If report format is invalid
        """
        if not os.path.exists(report_folder):
            raise FileNotFoundError(f"Report folder not found: {report_folder}")

        definition_path = os.path.join(report_folder, "definition")
        if not os.path.isdir(definition_path):
            raise ValueError(
                f"No definition folder found in {report_folder}"
            )

        self.logger.info(f"Analyzing report: {report_folder}")

        result = {
            "report_folder": report_folder,
            "report": {},
            "pages": [],
            "bookmarks": [],
            "filters": []
        }

        try:
            # Parse report.json
            report_file = os.path.join(definition_path, "report.json")
            if os.path.exists(report_file):
                result["report"] = self._parse_report_json(report_file)

            # Parse pages
            pages_path = os.path.join(definition_path, "pages")
            if os.path.isdir(pages_path):
                result["pages"] = self._parse_pages(pages_path)

            # Parse bookmarks
            bookmarks_path = os.path.join(definition_path, "bookmarks")
            if os.path.isdir(bookmarks_path):
                result["bookmarks"] = self._parse_bookmarks(bookmarks_path)

            self.logger.info(
                f"Report analysis complete: {len(result['pages'])} pages, "
                f"{sum(len(p.get('visuals', [])) for p in result['pages'])} visuals"
            )

        except Exception as e:
            self.logger.error(f"Error analyzing report: {e}")
            raise

        return result

    def _parse_report_json(self, file_path: str) -> Dict[str, Any]:
        """Parse report.json file."""
        try:
            data = load_json(file_path)

            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "version": data.get("$schema", ""),
                "config": data.get("config", {})
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse report.json: {e}")
            return {}

    def _parse_pages(self, pages_path: str) -> List[Dict[str, Any]]:
        """Parse all page definitions."""
        pages = []

        try:
            # Each page has its own folder with page.json and visuals/
            for page_id in os.listdir(pages_path):
                page_folder = os.path.join(pages_path, page_id)

                if not os.path.isdir(page_folder):
                    continue

                page_json = os.path.join(page_folder, "page.json")
                if not os.path.exists(page_json):
                    continue

                page_data = self._parse_page_json(page_json, page_folder)
                if page_data:
                    pages.append(page_data)

        except Exception as e:
            self.logger.error(f"Error parsing pages: {e}")

        return pages

    def _parse_page_json(
        self,
        page_json: str,
        page_folder: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single page JSON file."""
        try:
            data = load_json(page_json)

            page = {
                "id": data.get("name", ""),
                "display_name": data.get("displayName", ""),
                "width": data.get("width", 1280),
                "height": data.get("height", 720),
                "display_option": data.get("displayOption", ""),
                "filters": self._extract_page_filters(data),
                "visuals": []
            }

            # Parse visuals
            visuals_path = os.path.join(page_folder, "visuals")
            if os.path.isdir(visuals_path):
                page["visuals"] = self._parse_visuals(visuals_path)

            return page

        except Exception as e:
            self.logger.error(f"Error parsing page {page_json}: {e}")
            return None

    def _extract_page_filters(self, page_data: Dict) -> List[Dict[str, Any]]:
        """Extract filters from page configuration."""
        filters = []

        try:
            filter_config = page_data.get("filterConfig", {})
            page_filters = filter_config.get("filters", [])

            for filt in page_filters:
                filter_info = {
                    "name": filt.get("name", ""),
                    "field": self._extract_filter_field(filt.get("field", {})),
                    "how_created": filt.get("howCreated", "")
                }
                filters.append(filter_info)

        except Exception as e:
            self.logger.warning(f"Error extracting page filters: {e}")

        return filters

    def _extract_filter_field(self, field: Dict) -> Dict[str, str]:
        """Extract field information from filter definition."""
        try:
            if "Column" in field:
                column = field["Column"]
                entity = column.get("Expression", {}).get(
                    "SourceRef", {}
                ).get("Entity", "")
                prop = column.get("Property", "")
                return {"type": "Column", "table": entity, "name": prop}

            elif "Measure" in field:
                measure = field["Measure"]
                entity = measure.get("Expression", {}).get(
                    "SourceRef", {}
                ).get("Entity", "")
                prop = measure.get("Property", "")
                return {"type": "Measure", "table": entity, "name": prop}

        except Exception as e:
            self.logger.warning(f"Error extracting filter field: {e}")

        return {"type": "Unknown", "table": "", "name": ""}

    def _parse_visuals(self, visuals_path: str) -> List[Dict[str, Any]]:
        """Parse all visuals in a page with parallel processing."""
        visual_files = []

        try:
            # Collect all visual.json paths first
            for visual_id in os.listdir(visuals_path):
                visual_folder = os.path.join(visuals_path, visual_id)

                if not os.path.isdir(visual_folder):
                    continue

                visual_json = os.path.join(visual_folder, "visual.json")
                if os.path.exists(visual_json):
                    visual_files.append(visual_json)

            # Parse in parallel (I/O bound operation) with progress bar
            visuals = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {executor.submit(self._parse_visual_json, vf): vf
                          for vf in visual_files}

                # Add progress bar for visual parsing
                with tqdm(total=len(futures), desc="Parsing visuals", unit="visual", leave=False) as pbar:
                    for future in as_completed(futures):
                        try:
                            visual_data = future.result()
                            if visual_data:
                                visuals.append(visual_data)
                        except Exception as e:
                            visual_file = futures[future]
                            self.logger.error(f"Error parsing {visual_file}: {e}")
                        pbar.update(1)

        except Exception as e:
            self.logger.error(f"Error parsing visuals: {e}")

        return visuals

    def _parse_visual_json(self, visual_json: str) -> Optional[Dict[str, Any]]:
        """Parse a single visual JSON file."""
        try:
            data = load_json(visual_json)

            visual = {
                "id": data.get("name", ""),
                "visual_type": data.get("visual", {}).get("visualType", ""),
                "position": data.get("position", {}),
                "fields": {"columns": [], "measures": [], "hierarchies": []},
                "filters": []
            }

            # Extract field references
            visual_data = data.get("visual", {})
            query = visual_data.get("query", {})

            visual["fields"] = self._extract_visual_fields(query)

            # Extract visual title/name
            visual["visual_name"] = self._extract_visual_title(data)

            # Extract visual-level filters
            filters = visual_data.get("filters", [])
            for filt in filters:
                filter_info = {
                    "field": self._extract_filter_field(filt.get("field", {})),
                    "type": filt.get("type", "")
                }
                visual["filters"].append(filter_info)

            return visual

        except Exception as e:
            self.logger.error(f"Error parsing visual {visual_json}: {e}")
            return None

    def _extract_visual_fields(self, query: Dict) -> Dict[str, List]:
        """
        Recursively extract field references from visual query definition.

        Args:
            query: Visual query object

        Returns:
            Dictionary with columns, measures, and hierarchies
        """
        # Use sets for O(1) lookups during collection
        field_sets = {
            "columns": set(),
            "measures": set(),
            "hierarchies": set()
        }

        try:
            # Process query state projections
            query_state = query.get("queryState", {})

            # Common projection types
            projection_types = [
                "Category", "Y", "Values", "Rows", "Columns",
                "Legend", "Tooltips", "Details", "X", "Size",
                "Gradient", "Play", "SecondaryValues"
            ]

            for proj_type in projection_types:
                if proj_type in query_state:
                    projections = query_state[proj_type].get("projections", [])
                    for proj in projections:
                        field = proj.get("field", {})
                        self._extract_field_from_projection(field, field_sets)

            # Also check bindings (for certain visual types)
            bindings = query.get("Binding", {})
            for binding_key, binding_value in bindings.items():
                if isinstance(binding_value, dict):
                    projections = binding_value.get("Projections", [])
                    for proj in projections:
                        self._extract_field_from_projection(proj, field_sets)

        except Exception as e:
            self.logger.warning(f"Error extracting visual fields: {e}")

        # Convert sets back to lists for JSON serialization
        return {
            "columns": [{"table": t, "column": c} for t, c in field_sets["columns"]],
            "measures": [{"table": t, "measure": m} for t, m in field_sets["measures"]],
            "hierarchies": [{"table": t, "hierarchy": h} for t, h in field_sets["hierarchies"]]
        }

    def _extract_field_from_projection(
        self,
        field: Dict,
        field_sets: Dict[str, set]
    ) -> None:
        """Extract field information from a projection using sets for O(1) add."""
        try:
            if "Column" in field:
                column = field["Column"]
                entity = column.get("Expression", {}).get(
                    "SourceRef", {}
                ).get("Entity", "")
                prop = column.get("Property", "")

                if entity and prop:
                    field_sets["columns"].add((entity, prop))  # O(1) add

            elif "Measure" in field:
                measure = field["Measure"]
                entity = measure.get("Expression", {}).get(
                    "SourceRef", {}
                ).get("Entity", "")
                prop = measure.get("Property", "")

                if entity and prop:
                    field_sets["measures"].add((entity, prop))  # O(1) add

            elif "Hierarchy" in field:
                hierarchy = field["Hierarchy"]
                entity = hierarchy.get("Expression", {}).get(
                    "SourceRef", {}
                ).get("Entity", "")
                prop = hierarchy.get("Property", "")

                if entity and prop:
                    field_sets["hierarchies"].add((entity, prop))  # O(1) add

            # Recursively check for nested aggregation
            elif "Aggregation" in field:
                agg = field["Aggregation"]
                self._extract_field_from_projection(
                    agg.get("Expression", {}),
                    field_sets
                )

        except Exception as e:
            self.logger.warning(f"Error extracting field from projection: {e}")

    def _extract_visual_title(self, visual_data: Dict) -> Optional[str]:
        """
        Extract visual title from multiple possible locations.

        Visual titles can be stored in different formats:
        0. visualGroup.displayName (visual group name)
        1. title.text (simple string)
        2. properties.text.expr.Literal.Value (DAX literal)
        3. config.singleVisual.vcObjects.title[0].properties.text.expr.Literal.Value

        Args:
            visual_data: The visual JSON data

        Returns:
            The visual title/name or None if not found
        """
        try:
            # Method 0: Check visualGroup.displayName (highest priority for grouped visuals)
            visual_group = visual_data.get("visualGroup", {})
            if visual_group:
                display_name = visual_group.get("displayName")
                if display_name:
                    return display_name

            # Method 1: Check title.text (simple format)
            title = visual_data.get("title", {})
            if isinstance(title, list) and len(title) > 0:
                title_text = title[0].get("text")
                if title_text:
                    return title_text
            elif isinstance(title, dict):
                title_text = title.get("text")
                if title_text:
                    return title_text

            # Method 2: Check properties.text.expr.Literal.Value
            properties = visual_data.get("properties", {})
            text_expr = properties.get("text", {}).get("expr", {})
            if text_expr:
                literal = text_expr.get("Literal", {})
                if literal:
                    value = literal.get("Value", "")
                    # Remove surrounding quotes if present
                    if value:
                        return value.strip("'\"")

            # Method 3: Check config.singleVisual.vcObjects.title
            config = visual_data.get("config", {})
            single_visual = config.get("singleVisual", {})
            vc_objects = single_visual.get("vcObjects", {})
            title_objects = vc_objects.get("title", [])
            if isinstance(title_objects, list) and len(title_objects) > 0:
                title_props = title_objects[0].get("properties", {})
                text_expr = title_props.get("text", {}).get("expr", {})
                if text_expr:
                    literal = text_expr.get("Literal", {})
                    if literal:
                        value = literal.get("Value", "")
                        if value:
                            return value.strip("'\"")

            # Method 4: Check visual.vcObjects.title
            visual = visual_data.get("visual", {})
            vc_objects = visual.get("vcObjects", {})
            title_objects = vc_objects.get("title", [])
            if isinstance(title_objects, list) and len(title_objects) > 0:
                title_props = title_objects[0].get("properties", {})
                text_expr = title_props.get("text", {}).get("expr", {})
                if text_expr:
                    literal = text_expr.get("Literal", {})
                    if literal:
                        value = literal.get("Value", "")
                        if value:
                            return value.strip("'\"")
                # Also check for simple text property
                text_value = title_props.get("text")
                if text_value and isinstance(text_value, str):
                    return text_value

            return None

        except Exception as e:
            self.logger.warning(f"Error extracting visual title: {e}")
            return None

    def _parse_bookmarks(self, bookmarks_path: str) -> List[Dict[str, Any]]:
        """Parse bookmark definitions."""
        bookmarks = []

        try:
            for filename in os.listdir(bookmarks_path):
                if filename.endswith('.bookmark.json'):
                    bookmark_file = os.path.join(bookmarks_path, filename)
                    bookmark = self._parse_bookmark_json(bookmark_file)
                    if bookmark:
                        bookmarks.append(bookmark)

        except Exception as e:
            self.logger.warning(f"Error parsing bookmarks: {e}")

        return bookmarks

    def _parse_bookmark_json(
        self,
        bookmark_file: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single bookmark JSON file."""
        try:
            data = load_json(bookmark_file)

            return {
                "id": data.get("name", ""),
                "display_name": data.get("displayName", ""),
                "state": data.get("state", {})
            }

        except Exception as e:
            self.logger.warning(f"Error parsing bookmark {bookmark_file}: {e}")
            return None

    def extract_all_field_references(
        self,
        report_data: Dict
    ) -> Dict[str, Set[str]]:
        """
        Extract all unique field references across the entire report.

        Args:
            report_data: Parsed report data

        Returns:
            Dictionary with sets of unique columns, measures, and tables used
        """
        all_refs = {
            "columns": set(),
            "measures": set(),
            "tables": set()
        }

        for page in report_data.get("pages", []):
            # Page filters
            for filt in page.get("filters", []):
                field = filt.get("field", {})
                table = field.get("table", "")
                name = field.get("name", "")

                if table and name:
                    all_refs["tables"].add(table)
                    field_type = field.get("type", "")

                    if field_type == "Column":
                        all_refs["columns"].add(f"{table}[{name}]")
                    elif field_type == "Measure":
                        all_refs["measures"].add(f"{table}[{name}]")

            # Visuals
            for visual in page.get("visuals", []):
                fields = visual.get("fields", {})

                for col in fields.get("columns", []):
                    table = col.get("table", "")
                    column = col.get("column", "")
                    if table and column:
                        all_refs["tables"].add(table)
                        all_refs["columns"].add(f"{table}[{column}]")

                for meas in fields.get("measures", []):
                    table = meas.get("table", "")
                    measure = meas.get("measure", "")
                    if table and measure:
                        all_refs["tables"].add(table)
                        all_refs["measures"].add(f"{table}[{measure}]")

        return all_refs
