"""
TMDL Parser Module

Parses TMDL (Tabular Model Definition Language) files into structured Python objects
for analysis, comparison, and manipulation.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TmdlParser:
    """
    Parser for TMDL (Tabular Model Definition Language) files.

    Parses the definition/ folder structure created by TOM SaveToFolder()
    into structured Python dictionaries for analysis and comparison.
    """

    def __init__(self, tmdl_path: str):
        """
        Initialize TMDL parser.

        Args:
            tmdl_path: Path to the root TMDL export (contains definition/ folder)
        """
        self.tmdl_path = Path(tmdl_path)
        self.definition_path = self.tmdl_path / "definition"

        if not self.definition_path.exists():
            raise FileNotFoundError(
                f"Definition folder not found at: {self.definition_path}"
            )

        logger.info(f"Initialized TMDL parser for: {tmdl_path}")

    def parse_full_model(self) -> Dict[str, Any]:
        """
        Parse the complete TMDL model structure.

        Returns:
            Dictionary containing all model components:
            {
                "database": {...},
                "model": {...},
                "tables": [...],
                "relationships": [...],
                "roles": [...],
                "perspectives": [...],
                "expressions": [...],
                "datasources": [...]
            }
        """
        logger.info("Parsing full TMDL model")

        model_data = {
            "database": self._parse_database(),
            "model": self._parse_model(),
            "tables": self._parse_tables(),
            "relationships": self._parse_relationships(),
            "roles": self._parse_roles(),
            "perspectives": self._parse_perspectives(),
            "expressions": self._parse_expressions(),
            "datasources": self._parse_datasources()
        }

        logger.info(
            f"Parsed model: {len(model_data['tables'])} tables, "
            f"{len(model_data['relationships'])} relationships"
        )

        return model_data

    def _parse_database(self) -> Optional[Dict[str, Any]]:
        """Parse database.tmdl file."""
        db_file = self.definition_path / "database.tmdl"
        if not db_file.exists():
            logger.warning("database.tmdl not found")
            return None

        content = db_file.read_text(encoding='utf-8')
        return self._parse_tmdl_content(content, "database")

    def _parse_model(self) -> Optional[Dict[str, Any]]:
        """Parse model.tmdl file."""
        model_file = self.definition_path / "model.tmdl"
        if not model_file.exists():
            logger.warning("model.tmdl not found")
            return None

        content = model_file.read_text(encoding='utf-8')
        return self._parse_tmdl_content(content, "model")

    def _parse_tables(self) -> List[Dict[str, Any]]:
        """Parse all table .tmdl files."""
        tables_dir = self.definition_path / "tables"
        if not tables_dir.exists():
            logger.warning("tables/ directory not found")
            return []

        tables = []
        for table_file in tables_dir.glob("*.tmdl"):
            try:
                content = table_file.read_text(encoding='utf-8')
                table_data = self._parse_table_content(content)
                if table_data:
                    table_data['_source_file'] = table_file.name
                    tables.append(table_data)
            except Exception as e:
                logger.error(f"Error parsing table {table_file.name}: {e}")

        logger.debug(f"Parsed {len(tables)} tables")
        return tables

    def _parse_table_content(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse table TMDL content.

        Extracts table name, columns, measures, hierarchies, and partitions.
        """
        lines = content.split('\n')
        if not lines:
            return None

        # Extract table name from first line: "table 'TableName'" or "table TableName"
        table_match = re.match(r'^table\s+["\']?([^"\']+)["\']?', lines[0].strip())
        if not table_match:
            return None

        table_name = table_match.group(1)

        table_data = {
            "name": table_name,
            "columns": [],
            "measures": [],
            "hierarchies": [],
            "partitions": [],
            "calculation_items": [],
            "properties": {},
            "is_calculation_group": False,
            "is_hidden": False,
            "description": None,
            "annotations": []
        }

        # Parse indented structure
        i = 1
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith('///'):
                i += 1
                continue

            # Check for calculation group
            if line.startswith('calculationGroup'):
                table_data['is_calculation_group'] = True
                i += 1
                continue

            # Parse columns
            if line.startswith('column '):
                column, next_i = self._parse_column(lines, i)
                if column:
                    table_data['columns'].append(column)
                i = next_i
                continue

            # Parse measures
            if line.startswith('measure '):
                measure, next_i = self._parse_measure(lines, i)
                if measure:
                    table_data['measures'].append(measure)
                i = next_i
                continue

            # Parse hierarchies
            if line.startswith('hierarchy '):
                hierarchy, next_i = self._parse_hierarchy(lines, i)
                if hierarchy:
                    table_data['hierarchies'].append(hierarchy)
                i = next_i
                continue

            # Parse partitions
            if line.startswith('partition '):
                partition, next_i = self._parse_partition(lines, i)
                if partition:
                    table_data['partitions'].append(partition)
                i = next_i
                continue

            # Parse calculation items (for calculation groups)
            if line.startswith('calculationItem '):
                calc_item, next_i = self._parse_calculation_item(lines, i)
                if calc_item:
                    if 'calculation_items' not in table_data:
                        table_data['calculation_items'] = []
                    table_data['calculation_items'].append(calc_item)
                i = next_i
                continue

            # Parse properties (lineageTag, isHidden, etc.)
            if ':' in line and not line.startswith(' '):
                key, value = self._parse_property_line(line)
                if key == 'isHidden':
                    table_data['is_hidden'] = value if isinstance(value, bool) else str(value).lower() == 'true'
                elif key == 'description':
                    table_data['description'] = value
                elif key:
                    table_data['properties'][key] = value

            # Parse annotations
            if line.startswith('annotation '):
                annot, annot_end = self._parse_annotation(lines, i)
                if annot:
                    table_data['annotations'].append(annot)
                i = annot_end
                continue

            i += 1

        return table_data

    def _parse_column(self, lines: List[str], start_index: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a column definition."""
        line = lines[start_index].strip()

        # Extract column name: "column 'Name'" or "column Name"
        col_match = re.match(r'^column\s+["\']?([^"\'=]+)["\']?\s*(=)?', line)
        if not col_match:
            return None, start_index + 1

        column_name = col_match.group(1).strip()
        is_calculated = col_match.group(2) == '='

        column = {
            "name": column_name,
            "is_calculated": is_calculated,
            "data_type": None,
            "source_column": None,
            "expression": None,
            "description": None,
            "display_folder": None,
            "format_string": None,
            "data_category": None,
            "summarize_by": None,
            "sort_by_column": None,
            "is_key": False,
            "is_hidden": False,
            "annotations": [],
            "properties": {}
        }

        # If calculated column, extract DAX expression
        if is_calculated:
            expression, next_i = self._extract_expression(lines, start_index)
            column['expression'] = expression
            start_index = next_i

        # Parse column properties
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('///'):
                i += 1
                continue

            # Check if we've reached the next object
            if not line.startswith((' ', '\t')) or any(
                line.startswith(kw) for kw in ['column ', 'measure ', 'hierarchy ', 'partition ', 'calculationItem ']
            ):
                break

            # Parse property
            if ':' in line:
                key, value = self._parse_property_line(line)
                if key == 'dataType':
                    column['data_type'] = value
                elif key == 'sourceColumn':
                    column['source_column'] = value
                elif key == 'description':
                    column['description'] = value
                elif key == 'displayFolder':
                    column['display_folder'] = value
                elif key == 'formatString':
                    column['format_string'] = value
                elif key == 'dataCategory':
                    column['data_category'] = value
                elif key == 'summarizeBy':
                    column['summarize_by'] = value
                elif key == 'sortByColumn':
                    column['sort_by_column'] = value
                elif key == 'isKey':
                    column['is_key'] = value if isinstance(value, bool) else str(value).lower() == 'true'
                elif key == 'isHidden':
                    column['is_hidden'] = value if isinstance(value, bool) else str(value).lower() == 'true'
                elif key:
                    column['properties'][key] = value

            # Parse annotations
            elif line.startswith('annotation '):
                annot, annot_end = self._parse_annotation(lines, i)
                if annot:
                    column['annotations'].append(annot)
                i = annot_end
                continue

            i += 1

        return column, i

    def _parse_measure(self, lines: List[str], start_index: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a measure definition."""
        line = lines[start_index].strip()

        # Extract measure name: "measure 'Name' ="
        measure_match = re.match(r'^measure\s+["\']([^"\']+)["\']\s*=', line)
        if not measure_match:
            return None, start_index + 1

        measure_name = measure_match.group(1)

        measure = {
            "name": measure_name,
            "expression": None,
            "format_string": None,
            "display_folder": None,
            "description": None,
            "is_hidden": False,
            "data_category": None,
            "annotations": [],
            "properties": {}
        }

        # Extract DAX expression
        expression, next_i = self._extract_expression(lines, start_index)
        measure['expression'] = expression

        # Parse measure properties
        i = next_i
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('///'):
                i += 1
                continue

            # Check if we've reached the next object
            if not line.startswith((' ', '\t')) or any(
                line.startswith(kw) for kw in ['column ', 'measure ', 'hierarchy ', 'partition ', 'calculationItem ']
            ):
                break

            # Parse property
            if ':' in line:
                key, value = self._parse_property_line(line)
                if key == 'formatString':
                    measure['format_string'] = value
                elif key == 'displayFolder':
                    measure['display_folder'] = value
                elif key == 'description':
                    measure['description'] = value
                elif key == 'isHidden':
                    measure['is_hidden'] = value if isinstance(value, bool) else str(value).lower() == 'true'
                elif key == 'dataCategory':
                    measure['data_category'] = value
                elif key:
                    measure['properties'][key] = value

            # Parse annotations
            elif line.startswith('annotation '):
                annot, annot_end = self._parse_annotation(lines, i)
                if annot:
                    measure['annotations'].append(annot)
                i = annot_end
                continue

            i += 1

        return measure, i

    def _parse_hierarchy(self, lines: List[str], start_index: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a hierarchy definition."""
        line = lines[start_index].strip()

        # Extract hierarchy name
        hier_match = re.match(r'^hierarchy\s+["\']?([^"\']+)["\']?', line)
        if not hier_match:
            return None, start_index + 1

        hierarchy_name = hier_match.group(1)

        hierarchy = {
            "name": hierarchy_name,
            "levels": [],
            "properties": {}
        }

        # Parse hierarchy levels
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('///'):
                i += 1
                continue

            # Check if we've reached the next object
            if not line.startswith((' ', '\t')) or any(
                line.startswith(kw) for kw in ['column ', 'measure ', 'hierarchy ', 'partition ']
            ):
                break

            # Parse level
            if line.startswith('level '):
                level_match = re.match(r'^level\s+(.+)', line)
                if level_match:
                    level_name = level_match.group(1)
                    level = {"name": level_name, "column": None, "ordinal": None}

                    # Parse level properties
                    j = i + 1
                    while j < len(lines) and lines[j].strip().startswith((' ', '\t')):
                        prop_line = lines[j].strip()
                        if ':' in prop_line:
                            key, value = self._parse_property_line(prop_line)
                            if key == 'column':
                                level['column'] = value
                            elif key == 'ordinal':
                                level['ordinal'] = value
                        j += 1

                    hierarchy['levels'].append(level)
                    i = j
                    continue

            # Parse property
            if ':' in line:
                key, value = self._parse_property_line(line)
                if key:
                    hierarchy['properties'][key] = value

            i += 1

        return hierarchy, i

    def _parse_partition(self, lines: List[str], start_index: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a partition definition."""
        line = lines[start_index].strip()

        # Extract partition name and type: "partition Name = m" or "partition Name = expression"
        partition_match = re.match(r'^partition\s+([^\s=]+)\s*=\s*(\w+)', line)
        if not partition_match:
            return None, start_index + 1

        partition_name = partition_match.group(1)
        partition_type = partition_match.group(2)  # 'm' or 'expression'

        partition = {
            "name": partition_name,
            "type": partition_type,
            "mode": None,
            "source": None,
            "properties": {}
        }

        # Extract source expression
        source, next_i = self._extract_expression(lines, start_index, keyword='source')

        # If no explicit source keyword, try to extract from next lines
        if not source:
            i = start_index + 1
            if i < len(lines) and '=' in lines[i]:
                source, next_i = self._extract_expression(lines, i)
            else:
                next_i = start_index + 1

        partition['source'] = source

        # Parse partition properties
        i = next_i
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('///'):
                i += 1
                continue

            # Check if we've reached the next object
            if not line.startswith((' ', '\t')) or any(
                line.startswith(kw) for kw in ['column ', 'measure ', 'hierarchy ', 'partition ', 'calculationItem ']
            ):
                break

            # Parse property
            if ':' in line:
                key, value = self._parse_property_line(line)
                if key == 'mode':
                    partition['mode'] = value
                elif key:
                    partition['properties'][key] = value

            i += 1

        return partition, i

    def _parse_calculation_item(self, lines: List[str], start_index: int) -> tuple[Optional[Dict[str, Any]], int]:
        """Parse a calculation item (for calculation groups)."""
        line = lines[start_index].strip()

        # Extract calculation item name: "calculationItem Name ="
        item_match = re.match(r'^calculationItem\s+["\']?([^"\'=]+)["\']?\s*=', line)
        if not item_match:
            return None, start_index + 1

        item_name = item_match.group(1)

        calc_item = {
            "name": item_name,
            "expression": None,
            "ordinal": None,
            "format_string_definition": None,
            "description": None,
            "annotations": [],
            "properties": {}
        }

        # Extract DAX expression
        expression, next_i = self._extract_expression(lines, start_index)
        calc_item['expression'] = expression

        # Parse properties
        i = next_i
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('///'):
                i += 1
                continue

            # Check if we've reached the next object
            if not line.startswith((' ', '\t')) or any(
                line.startswith(kw) for kw in ['column ', 'calculationItem ', 'measure ']
            ):
                break

            # Parse property
            if ':' in line:
                key, value = self._parse_property_line(line)
                if key == 'ordinal':
                    calc_item['ordinal'] = value
                elif key == 'description':
                    calc_item['description'] = value
                elif key:
                    calc_item['properties'][key] = value
            elif line.startswith('formatStringDefinition'):
                # Format string definition can be multi-line expression
                expr, expr_end = self._extract_expression(lines, i, keyword='formatStringDefinition')
                calc_item['format_string_definition'] = expr
                i = expr_end
                continue
            elif line.startswith('annotation '):
                annot, annot_end = self._parse_annotation(lines, i)
                if annot:
                    calc_item['annotations'].append(annot)
                i = annot_end
                continue

            i += 1

        return calc_item, i

    def _extract_expression(
        self,
        lines: List[str],
        start_index: int,
        keyword: Optional[str] = None
    ) -> tuple[Optional[str], int]:
        """
        Extract a multi-line DAX or M expression.

        Args:
            lines: All lines of the file
            start_index: Index to start extraction
            keyword: Optional keyword to look for (e.g., 'source', 'formatStringDefinition')

        Returns:
            Tuple of (expression_text, next_line_index)
        """
        expression_lines = []
        i = start_index

        # Check if expression starts on the same line
        line = lines[i].strip()

        if keyword:
            # Look for "keyword =" pattern
            if keyword in line and '=' in line:
                # Extract everything after '='
                parts = line.split('=', 1)
                if len(parts) > 1:
                    expr_start = parts[1].strip()
                    if expr_start:
                        expression_lines.append(expr_start)
                i += 1
        else:
            # Expression starts after '=' on current line
            if '=' in line:
                parts = line.split('=', 1)
                if len(parts) > 1:
                    expr_start = parts[1].strip()
                    if expr_start:
                        expression_lines.append(expr_start)
                i += 1

        # Continue reading indented lines as part of expression
        base_indent = None
        while i < len(lines):
            line = lines[i]

            # Calculate indentation
            stripped = line.lstrip()
            if not stripped or stripped.startswith('///'):
                i += 1
                continue

            indent = len(line) - len(stripped)

            # Set base indent from first non-empty line
            if base_indent is None and stripped:
                base_indent = indent

            # If line has less indentation, we've reached the end of expression
            if base_indent is not None and indent < base_indent and stripped:
                # Check if this is a property line (contains ':')
                if ':' in stripped and not any(kw in stripped for kw in ['CALCULATE(', 'VAR ', 'RETURN', 'let', 'in']):
                    break
                # Check if it's a new object
                if any(stripped.startswith(kw) for kw in ['column ', 'measure ', 'hierarchy ', 'partition ', 'calculationItem ']):
                    break

            # Add line to expression
            expression_lines.append(stripped)
            i += 1

            # Stop if we hit an unindented line that looks like a property
            if not stripped.startswith((' ', '\t')) and ':' in stripped:
                break

        # Join and clean up expression
        if expression_lines:
            expression = '\n'.join(expression_lines).strip()
            return expression, i

        return None, i

    def _parse_property_line(self, line: str) -> tuple[Optional[str], Optional[Any]]:
        """
        Parse a property line: "key: value"

        Returns:
            Tuple of (key, value)
        """
        if ':' not in line:
            return None, None

        parts = line.split(':', 1)
        key = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else None

        # Try to parse value as appropriate type
        if value:
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # Try to parse as number
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string

        return key, value

    def _parse_annotation(self, lines: List[str], start_index: int) -> tuple[Optional[Dict[str, Any]], int]:
        """
        Parse an annotation definition.

        Format: annotation Name = "value" or annotation Name = value

        Returns:
            Tuple of (annotation_dict, next_line_index)
        """
        line = lines[start_index].strip()

        # Extract annotation: "annotation Name = value"
        annot_match = re.match(r'^annotation\s+([^\s=]+)\s*=\s*(.+)', line)
        if not annot_match:
            return None, start_index + 1

        annot_name = annot_match.group(1)
        annot_value = annot_match.group(2).strip()

        # Remove quotes if present
        if annot_value.startswith('"') and annot_value.endswith('"'):
            annot_value = annot_value[1:-1]
        elif annot_value.startswith("'") and annot_value.endswith("'"):
            annot_value = annot_value[1:-1]

        annotation = {
            "name": annot_name,
            "value": annot_value
        }

        return annotation, start_index + 1

    def _parse_relationships(self) -> List[Dict[str, Any]]:
        """Parse relationships.tmdl file."""
        rel_file = self.definition_path / "relationships.tmdl"
        if not rel_file.exists():
            logger.debug("relationships.tmdl not found")
            return []

        content = rel_file.read_text(encoding='utf-8')
        relationships = []

        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith('///'):
                i += 1
                continue

            # Parse relationship: "relationship guid"
            if line.startswith('relationship '):
                rel_match = re.match(r'^relationship\s+(.+)', line)
                if rel_match:
                    rel_id = rel_match.group(1)
                    relationship = {
                        "id": rel_id,
                        "from_column": None,
                        "from_cardinality": None,
                        "to_column": None,
                        "to_cardinality": None,
                        "is_active": True,
                        "cross_filtering_behavior": None,
                        "security_filtering_behavior": None,
                        "rely_on_referential_integrity": False,
                        "annotations": [],
                        "properties": {}
                    }

                    # Parse relationship properties
                    i += 1
                    while i < len(lines):
                        prop_line = lines[i].strip()

                        if not prop_line or prop_line.startswith('///'):
                            i += 1
                            continue

                        # Check if we've reached the next relationship
                        if prop_line.startswith('relationship '):
                            break

                        # Parse property
                        if ':' in prop_line:
                            key, value = self._parse_property_line(prop_line)
                            if key == 'fromColumn':
                                relationship['from_column'] = value
                            elif key == 'fromCardinality':
                                relationship['from_cardinality'] = value
                            elif key == 'toColumn':
                                relationship['to_column'] = value
                            elif key == 'toCardinality':
                                relationship['to_cardinality'] = value
                            elif key == 'crossFilteringBehavior':
                                relationship['cross_filtering_behavior'] = value
                            elif key == 'securityFilteringBehavior':
                                relationship['security_filtering_behavior'] = value
                            elif key == 'relyOnReferentialIntegrity':
                                relationship['rely_on_referential_integrity'] = value if isinstance(value, bool) else str(value).lower() == 'true'
                            elif key == 'isActive':
                                relationship['is_active'] = value if isinstance(value, bool) else True
                            elif key:
                                relationship['properties'][key] = value
                        elif prop_line.startswith('annotation '):
                            annot, annot_end = self._parse_annotation(lines, i)
                            if annot:
                                relationship['annotations'].append(annot)
                            i = annot_end
                            continue

                        i += 1

                    relationships.append(relationship)
                    continue

            i += 1

        logger.debug(f"Parsed {len(relationships)} relationships")
        return relationships

    def _parse_roles(self) -> List[Dict[str, Any]]:
        """Parse role .tmdl files."""
        roles_dir = self.definition_path / "roles"
        if not roles_dir.exists():
            logger.debug("roles/ directory not found")
            return []

        roles = []
        for role_file in roles_dir.glob("*.tmdl"):
            try:
                content = role_file.read_text(encoding='utf-8')
                role_data = self._parse_tmdl_content(content, "role")
                if role_data:
                    role_data['_source_file'] = role_file.name
                    roles.append(role_data)
            except Exception as e:
                logger.error(f"Error parsing role {role_file.name}: {e}")

        logger.debug(f"Parsed {len(roles)} roles")
        return roles

    def _parse_perspectives(self) -> List[Dict[str, Any]]:
        """Parse perspective .tmdl files."""
        perspectives_dir = self.definition_path / "perspectives"
        if not perspectives_dir.exists():
            logger.debug("perspectives/ directory not found")
            return []

        perspectives = []
        for persp_file in perspectives_dir.glob("*.tmdl"):
            try:
                content = persp_file.read_text(encoding='utf-8')
                persp_data = self._parse_tmdl_content(content, "perspective")
                if persp_data:
                    persp_data['_source_file'] = persp_file.name
                    perspectives.append(persp_data)
            except Exception as e:
                logger.error(f"Error parsing perspective {persp_file.name}: {e}")

        logger.debug(f"Parsed {len(perspectives)} perspectives")
        return perspectives

    def _parse_expressions(self) -> List[Dict[str, Any]]:
        """Parse expressions.tmdl file (M expressions and parameters)."""
        expr_file = self.definition_path / "expressions.tmdl"
        if not expr_file.exists():
            logger.debug("expressions.tmdl not found")
            return []

        content = expr_file.read_text(encoding='utf-8')
        # TODO: Implement detailed expression parsing if needed
        return [{"content": content}]

    def _parse_datasources(self) -> List[Dict[str, Any]]:
        """Parse datasources.tmdl file."""
        ds_file = self.definition_path / "datasources.tmdl"
        if not ds_file.exists():
            logger.debug("datasources.tmdl not found")
            return []

        content = ds_file.read_text(encoding='utf-8')
        # TODO: Implement detailed datasource parsing if needed
        return [{"content": content}]

    def _parse_tmdl_content(self, content: str, object_type: str) -> Optional[Dict[str, Any]]:
        """
        Generic TMDL content parser.

        Args:
            content: TMDL file content
            object_type: Type of object (database, model, role, perspective)

        Returns:
            Parsed object dictionary
        """
        lines = content.split('\n')
        if not lines:
            return None

        # Extract object name from first line
        obj_match = re.match(rf'^{object_type}\s+["\']?([^"\']+)["\']?', lines[0].strip())
        if not obj_match:
            return None

        obj_name = obj_match.group(1)

        obj_data = {
            "type": object_type,
            "name": obj_name,
            "properties": {},
            "content": content
        }

        return obj_data


def parse_tmdl_model(tmdl_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse a TMDL model.

    Args:
        tmdl_path: Path to TMDL export directory

    Returns:
        Parsed model dictionary
    """
    parser = TmdlParser(tmdl_path)
    return parser.parse_full_model()
