"""
PBIP Model Analyzer - Parses TMDL files and builds semantic model object graph.

This module provides comprehensive parsing of TMDL (Tabular Model Definition Language)
files including tables, measures, columns, relationships, and metadata.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class TmdlParser:
    """Parser for TMDL (Tabular Model Definition Language) files."""

    def __init__(self):
        """Initialize the TMDL parser."""
        self.logger = logger

    def parse_tmdl(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a TMDL file into a Python dictionary.

        Args:
            file_path: Path to the TMDL file

        Returns:
            Parsed TMDL structure as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"TMDL file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self._parse_content(content)

        except Exception as e:
            self.logger.error(f"Error parsing TMDL file {file_path}: {e}")
            raise ValueError(f"Failed to parse TMDL: {e}")

    def _parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse TMDL content using indentation-based parsing.

        Args:
            content: TMDL file content

        Returns:
            Parsed structure
        """
        lines = content.split('\n')
        root = {}
        stack = [(root, -1)]  # (current_dict, indent_level)

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip empty lines
            if not line.strip():
                i += 1
                continue

            indent = self._get_indent_level(line)
            content_line = line.strip()

            # Pop stack until we find the right parent level
            while stack and stack[-1][1] >= indent:
                stack.pop()

            current_parent, _ = stack[-1]

            # Check for object declarations (table, column, measure, relationship, etc.)
            if self._is_object_declaration(content_line):
                # First extract inline expression if present (before _parse_object_declaration modifies it)
                inline_expression = None
                has_equals = '=' in content_line

                if has_equals:
                    # Split on first '=' to separate declaration from expression
                    # e.g., "measure Period = SELECTEDVALUE(...)" -> ["measure Period ", " SELECTEDVALUE(...)"]
                    parts = content_line.split('=', 1)
                    if len(parts) == 2 and parts[1].strip():
                        potential_expr = parts[1].strip()
                        # Check if it ends with '=' (indicating multi-line) or has content
                        if not potential_expr.endswith('='):
                            inline_expression = potential_expr

                obj_type, obj_name = self._parse_object_declaration(content_line)
                new_obj = {"_type": obj_type, "_name": obj_name}

                # Handle multi-line expressions for measures/columns with '='
                # But DON'T advance i - let the normal loop process properties that follow
                if has_equals and (obj_type == 'measure' or obj_type == 'column'):
                    expr_lines = [inline_expression] if inline_expression else []
                    peek_idx = i + 1

                    while peek_idx < len(lines):
                        peek_line = lines[peek_idx]
                        peek_indent = self._get_indent_level(peek_line)
                        peek_stripped = peek_line.strip()

                        # Skip completely empty lines but continue checking
                        if not peek_stripped:
                            # If line has more indentation than declaration, include it as blank line
                            if peek_indent > indent:
                                expr_lines.append(peek_line.rstrip())
                                peek_idx += 1
                                continue
                            else:
                                # Empty line at same or less indent means end of expression
                                break

                        # Check if this is a property line (displayFolder:, formatString:, etc.)
                        # Properties come AFTER the expression
                        if ':' in peek_stripped and peek_indent == indent + 1:
                            # This is a property, stop collecting expression
                            break

                        # If next line is indented more than parent level (indent + 1), it's part of the expression
                        if peek_indent > indent + 1:
                            expr_lines.append(peek_line.rstrip())
                            peek_idx += 1
                        # If next line is at child level (indent + 1) but not a property, include it
                        elif peek_indent == indent + 1 and not self._is_new_property(peek_stripped):
                            expr_lines.append(peek_line.rstrip())
                            peek_idx += 1
                        else:
                            break

                    # Set expression if we found any lines
                    if expr_lines:
                        new_obj["expression"] = '\n'.join(expr_lines)
                    # DON'T advance i here - let the loop process properties

                # Add to parent
                if obj_type not in current_parent:
                    current_parent[obj_type] = []
                current_parent[obj_type].append(new_obj)

                stack.append((new_obj, indent))

            # Check for multi-line expressions
            elif '=' in content_line and not content_line.startswith('annotation'):
                key, value, is_multiline = self._parse_property_line(content_line)

                if is_multiline:
                    # Collect multi-line content
                    expr_lines = [value] if value else []
                    i += 1

                    while i < len(lines):
                        next_line = lines[i]
                        next_indent = self._get_indent_level(next_line)

                        # Check if we're still in the expression
                        if next_indent > indent or (
                            next_indent == indent and
                            not self._is_new_property(next_line.strip())
                        ):
                            expr_lines.append(next_line.rstrip())
                            i += 1
                        else:
                            break

                    current_parent[key] = '\n'.join(expr_lines)
                    i -= 1  # Back up one line for outer loop
                else:
                    current_parent[key] = value

            # Simple property (key: value)
            elif ':' in content_line and not content_line.startswith('annotation'):
                key, value = self._parse_simple_property(content_line)
                current_parent[key] = value

            i += 1

        return root

    def _get_indent_level(self, line: str) -> int:
        """Get indentation level (number of tabs)."""
        count = 0
        for char in line:
            if char == '\t':
                count += 1
            elif char != ' ':
                break
        return count

    def _is_object_declaration(self, line: str) -> bool:
        """Check if line is an object declaration."""
        patterns = [
            r'^table\s+',
            r'^column\s+',
            r'^measure\s+',
            r'^relationship\s+',
            r'^partition\s+',
            r'^annotation\s+',
            r'^role\s+',
            r'^culture\s+',
        ]
        return any(re.match(pattern, line) for pattern in patterns)

    def _parse_object_declaration(self, line: str) -> Tuple[str, str]:
        """
        Parse object declaration line.

        Returns:
            Tuple of (object_type, object_name)
        """
        match = re.match(r"^(\w+)\s+(.+)$", line)
        if match:
            obj_type = match.group(1)
            obj_name = match.group(2).strip()

            # For measure/column declarations, split on '=' and take only the name part
            if '=' in obj_name:
                obj_name = obj_name.split('=')[0].strip()

            # Remove quotes
            obj_name = obj_name.strip("'\"")
            return obj_type, obj_name
        return "unknown", line

    def _parse_property_line(
        self,
        line: str
    ) -> Tuple[str, Optional[str], bool]:
        """
        Parse a property line with '=' assignment.

        Returns:
            Tuple of (key, value, is_multiline)
        """
        parts = line.split('=', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()

            # Check if this is a multi-line expression (no value on same line)
            is_multiline = not value or value == ""

            return key, value if value else None, is_multiline

        return line, None, False

    def _parse_simple_property(self, line: str) -> Tuple[str, str]:
        """Parse simple property (key: value)."""
        parts = line.split(':', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            return key, value
        return line, ""

    def _is_new_property(self, line: str) -> bool:
        """Check if line starts a new property."""
        return (
            self._is_object_declaration(line) or
            (':' in line and not line.startswith(' ')) or
            ('=' in line and not line.startswith(' '))
        )


class TmdlModelAnalyzer:
    """Analyzes TMDL files and builds semantic model object graph."""

    def __init__(self):
        """Initialize the model analyzer."""
        self.logger = logger
        self.parser = TmdlParser()

    def analyze_model(self, model_folder: str) -> Dict[str, Any]:
        """
        Parse all TMDL files in the semantic model folder.

        Args:
            model_folder: Path to the .SemanticModel folder

        Returns:
            Dictionary with complete model structure

        Raises:
            FileNotFoundError: If model folder doesn't exist
            ValueError: If model format is invalid
        """
        if not os.path.exists(model_folder):
            raise FileNotFoundError(f"Model folder not found: {model_folder}")

        definition_path = os.path.join(model_folder, "definition")
        if not os.path.isdir(definition_path):
            raise ValueError(
                f"No definition folder found in {model_folder}"
            )

        self.logger.info(f"Analyzing model: {model_folder}")

        result = {
            "model_folder": model_folder,
            "database": {},
            "model": {},
            "expressions": [],
            "tables": [],
            "relationships": [],
            "roles": [],
            "cultures": []
        }

        try:
            # Parse database.tmdl
            database_file = os.path.join(definition_path, "database.tmdl")
            if os.path.exists(database_file):
                result["database"] = self._parse_database(database_file)

            # Parse model.tmdl
            model_file = os.path.join(definition_path, "model.tmdl")
            if os.path.exists(model_file):
                result["model"] = self._parse_model(model_file)

            # Parse expressions.tmdl
            expressions_file = os.path.join(definition_path, "expressions.tmdl")
            if os.path.exists(expressions_file):
                result["expressions"] = self._parse_expressions(expressions_file)

            # Parse relationships.tmdl
            relationships_file = os.path.join(definition_path, "relationships.tmdl")
            if os.path.exists(relationships_file):
                result["relationships"] = self._parse_relationships(
                    relationships_file
                )

            # Parse tables
            tables_path = os.path.join(definition_path, "tables")
            if os.path.isdir(tables_path):
                result["tables"] = self._parse_tables(tables_path)

            # Parse roles
            roles_path = os.path.join(definition_path, "roles")
            if os.path.isdir(roles_path):
                result["roles"] = self._parse_roles(roles_path)

            # Parse cultures
            cultures_path = os.path.join(definition_path, "cultures")
            if os.path.isdir(cultures_path):
                result["cultures"] = self._parse_cultures(cultures_path)

            self.logger.info(
                f"Model analysis complete: {len(result['tables'])} tables, "
                f"{sum(len(t.get('measures', [])) for t in result['tables'])} measures"
            )

        except Exception as e:
            self.logger.error(f"Error analyzing model: {e}")
            raise

        return result

    def _parse_database(self, file_path: str) -> Dict[str, Any]:
        """Parse database.tmdl file."""
        try:
            content = self.parser.parse_tmdl(file_path)
            return content
        except Exception as e:
            self.logger.warning(f"Failed to parse database.tmdl: {e}")
            return {}

    def _parse_model(self, file_path: str) -> Dict[str, Any]:
        """Parse model.tmdl file."""
        try:
            content = self.parser.parse_tmdl(file_path)
            return content
        except Exception as e:
            self.logger.warning(f"Failed to parse model.tmdl: {e}")
            return {}

    def _parse_expressions(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse expressions.tmdl file (M expressions)."""
        try:
            # Read file directly since the parser doesn't group expressions properly
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            expressions = []
            lines = content.split('\n')

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Look for expression declarations: "expression <name> ="
                if line.startswith('expression ') and '=' in line:
                    # Extract expression name
                    name_part = line[len('expression '):].split('=')[0].strip()

                    # Check if expression is on same line (single-line expression like parameters)
                    after_equals = line.split('=', 1)[1].strip()
                    expression_text = ""

                    if after_equals and not after_equals.endswith('='):
                        # Single-line expression (e.g., parameter)
                        # Remove metadata like 'meta [...]' from the expression
                        if ' meta ' in after_equals:
                            expression_text = after_equals.split(' meta ')[0].strip()
                        else:
                            expression_text = after_equals
                        i += 1
                    else:
                        # Multi-line expression - collect indented lines
                        expression_lines = []
                        i += 1

                        # Find the indentation level of the first expression line
                        while i < len(lines) and not lines[i].strip():
                            i += 1  # Skip empty lines

                        if i < len(lines):
                            first_line = lines[i]
                            indent_level = len(first_line) - len(first_line.lstrip())

                            # Collect all indented lines
                            while i < len(lines):
                                curr_line = lines[i]
                                curr_indent = len(curr_line) - len(curr_line.lstrip())
                                curr_stripped = curr_line.strip()

                                # Stop if we hit a non-indented line that's not empty
                                if curr_stripped and curr_indent < indent_level:
                                    break

                                # Stop if we hit metadata or another expression
                                if curr_stripped.startswith(('lineageTag:', 'queryGroup:', 'annotation ', 'expression ')):
                                    break

                                if curr_stripped:  # Only add non-empty lines
                                    expression_lines.append(curr_line.rstrip())

                                i += 1

                        # Join expression lines
                        expression_text = '\n'.join(expression_lines).strip()

                    if expression_text:
                        expressions.append({
                            "name": name_part,
                            "expression": expression_text,
                            "kind": "m"
                        })
                else:
                    i += 1

            return expressions
        except Exception as e:
            self.logger.warning(f"Failed to parse expressions.tmdl: {e}")
            return []

    def _parse_relationships(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse relationships.tmdl file."""
        try:
            content = self.parser.parse_tmdl(file_path)
            relationships = []

            if "relationship" in content:
                for rel in content["relationship"]:
                    rel_dict = {
                        "name": rel.get("_name", ""),
                        "from_column": rel.get("fromColumn", ""),
                        "to_column": rel.get("toColumn", ""),
                        "cross_filtering_behavior": rel.get(
                            "crossFilteringBehavior",
                            "oneDirection"
                        ),
                        "is_active": rel.get("isActive", True),
                        "security_filtering_behavior": rel.get(
                            "securityFilteringBehavior",
                            "oneDirection"
                        )
                    }

                    # Parse from/to table and column
                    from_parts = self._parse_column_reference(
                        rel_dict["from_column"]
                    )
                    to_parts = self._parse_column_reference(
                        rel_dict["to_column"]
                    )

                    rel_dict["from_table"] = from_parts[0]
                    rel_dict["from_column_name"] = from_parts[1]
                    rel_dict["to_table"] = to_parts[0]
                    rel_dict["to_column_name"] = to_parts[1]

                    relationships.append(rel_dict)

            return relationships

        except Exception as e:
            self.logger.warning(f"Failed to parse relationships.tmdl: {e}")
            return []

    def _parse_column_reference(self, ref: str) -> Tuple[str, str]:
        """
        Parse column reference like 'd Family'.'Family Key' or 'd Date'.'Date Nr'.

        Returns:
            Tuple of (table_name, column_name)
        """
        # Pattern: 'TableName'.'ColumnName' or 'TableName'.ColumnName
        match = re.match(r"'([^']+)'\.(?:'([^']+)'|(\w+))", ref)
        if match:
            table = match.group(1)
            column = match.group(2) or match.group(3)
            return table, column
        return "", ref

    def _parse_tables(self, tables_path: str) -> List[Dict[str, Any]]:
        """Parse all table TMDL files."""
        tables = []

        try:
            for filename in os.listdir(tables_path):
                if filename.endswith('.tmdl'):
                    file_path = os.path.join(tables_path, filename)
                    table = self._parse_table_file(file_path)
                    if table:
                        tables.append(table)

        except Exception as e:
            self.logger.error(f"Error parsing tables: {e}")

        return tables

    def _parse_table_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse a single table TMDL file."""
        try:
            content = self.parser.parse_tmdl(file_path)

            if "table" not in content:
                return None

            # Get the first (and usually only) table
            table_data = content["table"][0] if content["table"] else {}

            table = {
                "name": table_data.get("_name", ""),
                "lineage_tag": table_data.get("lineageTag", ""),
                "is_hidden": table_data.get("isHidden", False),
                "columns": [],
                "measures": [],
                "partitions": []
            }

            # Extract columns
            if "column" in table_data:
                for col in table_data["column"]:
                    column = {
                        "name": col.get("_name", ""),
                        "data_type": col.get("dataType", ""),
                        "lineage_tag": col.get("lineageTag", ""),
                        "source_column": col.get("sourceColumn", ""),
                        "summarize_by": col.get("summarizeBy", ""),
                        "is_hidden": col.get("isHidden", False),
                        "display_folder": col.get("displayFolder", ""),
                        "format_string": col.get("formatString", ""),
                        "expression": col.get("expression", "")
                    }
                    table["columns"].append(column)

            # Extract measures
            if "measure" in table_data:
                for meas in table_data["measure"]:
                    # Get the expression - could be under various keys
                    expression = ""

                    # First, check for explicit 'expression' key
                    if "expression" in meas:
                        expression = meas["expression"]

                    # Otherwise, look for any string value that looks like DAX
                    if not expression:
                        for key, value in meas.items():
                            if key.startswith("_"):
                                continue
                            if isinstance(value, str) and len(value.strip()) > 0:
                                # Check if it looks like DAX/expression
                                value_upper = value.upper()
                                is_dax = (
                                    len(value) > 50 or  # Long text likely to be DAX
                                    "VAR" in value_upper or
                                    "RETURN" in value_upper or
                                    "CALCULATE" in value_upper or
                                    "SELECTEDVALUE" in value_upper or
                                    "SWITCH" in value_upper or
                                    "IF(" in value_upper or
                                    value.strip().startswith('"') or  # String literal
                                    value.strip() == '""' or  # Empty string
                                    any(func in value_upper for func in [
                                        "SUM(", "COUNT(", "AVERAGE(", "MAX(", "MIN(",
                                        "DIVIDE(", "FILTER(", "ALL(", "BLANK()", "USERNAME()"
                                    ])
                                )
                                if is_dax:
                                    expression = value
                                    break

                    measure = {
                        "name": meas.get("_name", ""),
                        "expression": expression,
                        "display_folder": meas.get("displayFolder", ""),
                        "format_string": meas.get("formatString", ""),
                        "format_string_definition": meas.get(
                            "formatStringDefinition",
                            ""
                        ),
                        "lineage_tag": meas.get("lineageTag", ""),
                        "is_hidden": meas.get("isHidden", False),
                        "data_category": meas.get("dataCategory", "")
                    }
                    table["measures"].append(measure)

            # Extract partitions
            if "partition" in table_data:
                for part in table_data["partition"]:
                    partition = {
                        "name": part.get("_name", ""),
                        "mode": part.get("mode", ""),
                        "source": part.get("source", ""),
                        "query_group": part.get("queryGroup", "")
                    }
                    table["partitions"].append(partition)

            return table

        except Exception as e:
            self.logger.error(f"Error parsing table file {file_path}: {e}")
            return None

    def _parse_roles(self, roles_path: str) -> List[Dict[str, Any]]:
        """Parse role TMDL files."""
        roles = []
        try:
            for filename in os.listdir(roles_path):
                if filename.endswith('.tmdl'):
                    file_path = os.path.join(roles_path, filename)
                    role_data = self.parser.parse_tmdl(file_path)
                    if role_data:
                        roles.append(role_data)
        except Exception as e:
            self.logger.warning(f"Error parsing roles: {e}")
        return roles

    def _parse_cultures(self, cultures_path: str) -> List[Dict[str, Any]]:
        """Parse culture TMDL files."""
        cultures = []
        try:
            for filename in os.listdir(cultures_path):
                if filename.endswith('.tmdl'):
                    file_path = os.path.join(cultures_path, filename)
                    culture_data = self.parser.parse_tmdl(file_path)
                    if culture_data:
                        cultures.append({
                            "name": filename.replace('.tmdl', ''),
                            "data": culture_data
                        })
        except Exception as e:
            self.logger.warning(f"Error parsing cultures: {e}")
        return cultures
