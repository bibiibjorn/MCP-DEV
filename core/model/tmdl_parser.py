"""
TMDL Parser - Parse TMDL files to extract structured data

Extracts:
- Measure definitions and DAX expressions
- Column definitions
- Relationship details
- Calculation groups
- Table metadata
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TMDLParser:
    """Parser for TMDL (Tabular Model Definition Language) files"""

    @staticmethod
    def parse_measure(tmdl_content: str, measure_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse a specific measure from TMDL content

        Args:
            tmdl_content: TMDL file content
            measure_name: Name of measure to extract

        Returns:
            Measure definition dict or None if not found
        """
        # Pattern to match measure definition
        pattern = rf"measure\s+(?:'|`)?{re.escape(measure_name)}(?:'|`)?\s*="

        match = re.search(pattern, tmdl_content, re.IGNORECASE | re.MULTILINE)
        if not match:
            return None

        start_pos = match.start()
        expr_start = tmdl_content.find('=', start_pos) + 1

        # Find the end of the measure
        next_measure = re.search(r'\n\s*measure\s+', tmdl_content[expr_start:], re.MULTILINE)
        next_section = re.search(r'\n\s*(column|hierarchy|partition|annotation)', tmdl_content[expr_start:], re.MULTILINE)

        if next_measure and next_section:
            end_pos = expr_start + min(next_measure.start(), next_section.start())
        elif next_measure:
            end_pos = expr_start + next_measure.start()
        elif next_section:
            end_pos = expr_start + next_section.start()
        else:
            end_pos = len(tmdl_content)

        expression = tmdl_content[expr_start:end_pos].strip()
        measure_block = tmdl_content[start_pos:end_pos]

        # Extract properties
        format_match = re.search(r'formatString:\s*"([^"]*)"', measure_block)
        desc_match = re.search(r'description:\s*"([^"]*)"', measure_block)
        folder_match = re.search(r'displayFolder:\s*"([^"]*)"', measure_block)
        hidden_match = re.search(r'isHidden:\s*(true|false)', measure_block)

        return {
            "name": measure_name,
            "expression": expression,
            "formatString": format_match.group(1) if format_match else None,
            "description": desc_match.group(1) if desc_match else None,
            "displayFolder": folder_match.group(1) if folder_match else None,
            "isHidden": hidden_match.group(1) == 'true' if hidden_match else False
        }

    @staticmethod
    def parse_all_measures(tmdl_content: str) -> List[Dict[str, Any]]:
        """Parse all measures from TMDL content"""
        measures = []
        measure_pattern = r"measure\s+(?:'([^']+)'|`([^`]+)`|(\S+))\s*="
        matches = re.finditer(measure_pattern, tmdl_content, re.MULTILINE)

        for match in matches:
            measure_name = match.group(1) or match.group(2) or match.group(3)
            measure_def = TMDLParser.parse_measure(tmdl_content, measure_name)
            if measure_def:
                measures.append(measure_def)

        logger.info(f"Parsed {len(measures)} measures from TMDL")
        return measures

    @staticmethod
    def parse_column(tmdl_content: str, column_name: str) -> Optional[Dict[str, Any]]:
        """Parse a specific column from TMDL content"""
        pattern = rf"column\s+(?:'|`)?{re.escape(column_name)}(?:'|`)?"
        match = re.search(pattern, tmdl_content, re.IGNORECASE | re.MULTILINE)
        if not match:
            return None

        start_pos = match.start()
        next_item = re.search(r'\n\s*(column|measure|hierarchy|partition)', tmdl_content[start_pos+1:], re.MULTILINE)
        end_pos = start_pos + next_item.start() if next_item else len(tmdl_content)
        column_block = tmdl_content[start_pos:end_pos]

        # Extract properties
        dtype_match = re.search(r'dataType:\s*(\w+)', column_block)
        source_match = re.search(r'sourceColumn:\s*"([^"]*)"', column_block)
        format_match = re.search(r'formatString:\s*"([^"]*)"', column_block)
        hidden_match = re.search(r'isHidden:\s*(true|false)', column_block)
        key_match = re.search(r'isKey:\s*(true|false)', column_block)
        summarize_match = re.search(r'summarizeBy:\s*(\w+)', column_block)
        desc_match = re.search(r'description:\s*"([^"]*)"', column_block)
        folder_match = re.search(r'displayFolder:\s*"([^"]*)"', column_block)

        return {
            "name": column_name,
            "dataType": dtype_match.group(1) if dtype_match else None,
            "sourceColumn": source_match.group(1) if source_match else None,
            "formatString": format_match.group(1) if format_match else None,
            "isHidden": hidden_match.group(1) == 'true' if hidden_match else False,
            "isKey": key_match.group(1) == 'true' if key_match else False,
            "summarizeBy": summarize_match.group(1) if summarize_match else None,
            "description": desc_match.group(1) if desc_match else None,
            "displayFolder": folder_match.group(1) if folder_match else None
        }

    @staticmethod
    def parse_all_columns(tmdl_content: str) -> List[Dict[str, Any]]:
        """Parse all columns from TMDL content"""
        columns = []
        column_pattern = r"column\s+(?:'([^']+)'|`([^`]+)`|(\S+))"
        matches = re.finditer(column_pattern, tmdl_content, re.MULTILINE)

        for match in matches:
            column_name = match.group(1) or match.group(2) or match.group(3)
            column_def = TMDLParser.parse_column(tmdl_content, column_name)
            if column_def:
                columns.append(column_def)

        logger.info(f"Parsed {len(columns)} columns from TMDL")
        return columns

    @staticmethod
    def parse_relationships(tmdl_content: str) -> List[Dict[str, Any]]:
        """Parse relationships from relationships.tmdl content"""
        relationships = []
        rel_pattern = r"relationship\s+(\w+)\s*\n(.*?)(?=\n\s*relationship|\Z)"
        matches = re.finditer(rel_pattern, tmdl_content, re.DOTALL | re.MULTILINE)

        for match in matches:
            rel_hash = match.group(1)
            rel_block = match.group(2)

            from_match = re.search(r"fromColumn:\s*(['\"]?)([^'\"\n]+)\1", rel_block)
            to_match = re.search(r"toColumn:\s*(['\"]?)([^'\"\n]+)\1", rel_block)
            from_card_match = re.search(r"fromCardinality:\s*(\w+)", rel_block)
            to_card_match = re.search(r"toCardinality:\s*(\w+)", rel_block)
            cross_filter_match = re.search(r"crossFilteringBehavior:\s*(\w+)", rel_block)
            active_match = re.search(r"isActive:\s*(true|false)", rel_block)
            security_match = re.search(r"securityFilteringBehavior:\s*(\w+)", rel_block)

            from_column = from_match.group(2).strip() if from_match else None
            to_column = to_match.group(2).strip() if to_match else None

            # Extract table names
            from_table, from_col = None, None
            if from_column:
                parts = from_column.split('[')
                if len(parts) == 2:
                    from_table = parts[0].strip("' ")
                    from_col = parts[1].strip("] '")

            to_table, to_col = None, None
            if to_column:
                parts = to_column.split('[')
                if len(parts) == 2:
                    to_table = parts[0].strip("' ")
                    to_col = parts[1].strip("] '")

            relationships.append({
                "hash": rel_hash,
                "fromTable": from_table,
                "fromColumn": from_col,
                "toTable": to_table,
                "toColumn": to_col,
                "fromCardinality": from_card_match.group(1) if from_card_match else None,
                "toCardinality": to_card_match.group(1) if to_card_match else None,
                "crossFilteringBehavior": cross_filter_match.group(1) if cross_filter_match else None,
                "isActive": active_match.group(1) == 'true' if active_match else True,
                "securityFilteringBehavior": security_match.group(1) if security_match else None
            })

        logger.info(f"Parsed {len(relationships)} relationships from TMDL")
        return relationships

    @staticmethod
    def parse_table_metadata(tmdl_content: str) -> Dict[str, Any]:
        """Parse table-level metadata from table TMDL content"""
        metadata = {}

        table_match = re.search(r"table\s+(?:'([^']+)'|`([^`]+)`|(\S+))", tmdl_content)
        if table_match:
            metadata["name"] = table_match.group(1) or table_match.group(2) or table_match.group(3)

        desc_match = re.search(r'description:\s*"([^"]*)"', tmdl_content)
        if desc_match:
            metadata["description"] = desc_match.group(1)

        hidden_match = re.search(r'isHidden:\s*(true|false)', tmdl_content)
        if hidden_match:
            metadata["isHidden"] = hidden_match.group(1) == 'true'

        has_partition = re.search(r'\bpartition\s+', tmdl_content) is not None
        metadata["hasPartition"] = has_partition

        columns = TMDLParser.parse_all_columns(tmdl_content)
        measures = TMDLParser.parse_all_measures(tmdl_content)

        metadata["columnCount"] = len(columns)
        metadata["measureCount"] = len(measures)

        return metadata

    @staticmethod
    def parse_calculation_group(tmdl_content: str) -> Optional[Dict[str, Any]]:
        """Parse calculation group from TMDL content"""
        calc_group_match = re.search(r"table\s+(?:'([^']+)'|`([^`]+)`|(\S+))", tmdl_content)
        if not calc_group_match or 'calculationGroup' not in tmdl_content:
            return None

        table_name = calc_group_match.group(1) or calc_group_match.group(2) or calc_group_match.group(3)
        calc_items = []

        calc_item_pattern = r"calculationItem\s+(?:'([^']+)'|`([^`]+)`|(\S+))\s*=\s*(.*?)(?=\n\s*calculationItem|\Z)"
        matches = re.finditer(calc_item_pattern, tmdl_content, re.DOTALL | re.MULTILINE)

        for match in matches:
            item_name = match.group(1) or match.group(2) or match.group(3)
            expression = match.group(4).strip()
            calc_items.append({"name": item_name, "expression": expression})

        return {"name": table_name, "calculationItems": calc_items}

    @staticmethod
    def parse_file(file_path: Path) -> Dict[str, Any]:
        """Parse a TMDL file and extract all relevant information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            result = {"file_path": str(file_path), "file_name": file_path.name}

            if file_path.name == "relationships.tmdl":
                result["type"] = "relationships"
                result["relationships"] = TMDLParser.parse_relationships(content)
            elif file_path.name == "expressions.tmdl":
                result["type"] = "expressions"
                result["measures"] = TMDLParser.parse_all_measures(content)
            elif file_path.parent.name == "tables":
                result["type"] = "table"
                result["metadata"] = TMDLParser.parse_table_metadata(content)
                result["columns"] = TMDLParser.parse_all_columns(content)
                result["measures"] = TMDLParser.parse_all_measures(content)
                calc_group = TMDLParser.parse_calculation_group(content)
                if calc_group:
                    result["calculationGroup"] = calc_group
            else:
                result["type"] = "other"
                result["content"] = content

            return result

        except Exception as e:
            logger.error(f"Error parsing TMDL file {file_path}: {e}")
            raise
