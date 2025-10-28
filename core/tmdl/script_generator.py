"""
TMDL Script Generator - Programmatic TMDL generation

Generate TMDL scripts for:
- Tables with columns and partitions
- Measures
- Relationships
- Calculation groups
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ColumnDef:
    """Column definition"""
    name: str
    data_type: str
    format_string: Optional[str] = None
    is_hidden: bool = False
    display_folder: Optional[str] = None
    summarize_by: str = "sum"


@dataclass
class PartitionDef:
    """Partition definition"""
    name: str
    mode: str = "import"  # import, directQuery, dual
    source_expression: str = ""


@dataclass
class CalcItemDef:
    """Calculation item definition"""
    name: str
    expression: str
    ordinal: int
    format_string: Optional[str] = None


class TmdlScriptGenerator:
    """
    Generate TMDL scripts programmatically

    Supports:
    - Table generation with columns and partitions
    - Measure generation
    - Relationship generation
    - Calculation group generation
    """

    def __init__(self):
        """Initialize script generator"""
        pass

    def generate_table(
        self,
        name: str,
        columns: List[ColumnDef],
        partitions: Optional[List[PartitionDef]] = None,
        description: Optional[str] = None,
    ) -> str:
        """
        Generate TMDL script for a table

        Args:
            name: Table name
            columns: List of column definitions
            partitions: List of partition definitions
            description: Table description

        Returns:
            TMDL script as string
        """
        script_parts = []

        # Table header
        script_parts.append(f"table '{name}'")
        script_parts.append(f"\tlineageTag: {self._generate_lineage_tag()}")

        if description:
            script_parts.append(f"\tdescription: \"{description}\"")

        # Columns
        for col in columns:
            script_parts.append("")
            script_parts.extend(self._generate_column(col))

        # Partitions
        if partitions:
            for partition in partitions:
                script_parts.append("")
                script_parts.extend(self._generate_partition(partition))

        return "\n".join(script_parts)

    def _generate_column(self, col: ColumnDef) -> List[str]:
        """Generate column TMDL"""
        lines = [f"\tcolumn '{col.name}'"]
        lines.append(f"\t\tdataType: {col.data_type}")

        if col.format_string:
            lines.append(f"\t\tformatString: {col.format_string}")

        if col.is_hidden:
            lines.append("\t\tisHidden")

        if col.display_folder:
            lines.append(f"\t\tdisplayFolder: \"{col.display_folder}\"")

        lines.append(f"\t\tsummarizeBy: {col.summarize_by}")
        lines.append(f"\t\tlineageTag: {self._generate_lineage_tag()}")

        return lines

    def _generate_partition(self, partition: PartitionDef) -> List[str]:
        """Generate partition TMDL"""
        lines = [f"\tpartition {partition.name} = m"]
        lines.append(f"\t\tmode: {partition.mode}")

        if partition.source_expression:
            lines.append("\t\tsource =")
            # Indent source expression
            for line in partition.source_expression.split("\n"):
                lines.append(f"\t\t\t{line}")

        return lines

    def generate_measure(
        self,
        table: str,
        name: str,
        expression: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate TMDL script for a measure

        Args:
            table: Table containing the measure
            name: Measure name
            expression: DAX expression
            properties: Additional properties (formatString, displayFolder, etc.)

        Returns:
            TMDL script as string
        """
        props = properties or {}

        lines = [f"measure '{name}'"]
        lines.append(f"\texpression:")

        # Indent expression
        for line in expression.split("\n"):
            lines.append(f"\t\t{line}")

        if "formatString" in props:
            lines.append(f"\tformatString: {props['formatString']}")

        if "displayFolder" in props:
            lines.append(f"\tdisplayFolder: \"{props['displayFolder']}\"")

        if "isHidden" in props and props["isHidden"]:
            lines.append("\tisHidden")

        if "description" in props:
            lines.append(f"\tdescription: \"{props['description']}\"")

        lines.append(f"\tlineageTag: {self._generate_lineage_tag()}")

        return "\n".join(lines)

    def generate_relationship(
        self,
        from_table: str,
        from_column: str,
        to_table: str,
        to_column: str,
        cardinality: str = "many-to-one",
        cross_filter_direction: str = "single",
        is_active: bool = True,
    ) -> str:
        """
        Generate TMDL script for a relationship

        Args:
            from_table: From table name
            from_column: From column name
            to_table: To table name
            to_column: To column name
            cardinality: "one-to-one", "many-to-one", "one-to-many", "many-to-many"
            cross_filter_direction: "single", "both"
            is_active: Whether relationship is active

        Returns:
            TMDL script as string
        """
        lines = [
            f"relationship {self._generate_relationship_name(from_table, to_table)}",
            f"\tfromColumn: '{from_table}'.'{from_column}'",
            f"\ttoColumn: '{to_table}'.'{to_column}'",
        ]

        # Parse cardinality
        if cardinality == "many-to-one":
            lines.append("\tfromCardinality: many")
            lines.append("\ttoCardinality: one")
        elif cardinality == "one-to-many":
            lines.append("\tfromCardinality: one")
            lines.append("\ttoCardinality: many")
        elif cardinality == "one-to-one":
            lines.append("\tfromCardinality: one")
            lines.append("\ttoCardinality: one")
        elif cardinality == "many-to-many":
            lines.append("\tfromCardinality: many")
            lines.append("\ttoCardinality: many")

        if cross_filter_direction == "both":
            lines.append("\tcrossFilteringBehavior: bothDirections")

        if not is_active:
            lines.append("\tisActive: false")

        return "\n".join(lines)

    def generate_calculation_group(
        self,
        name: str,
        items: List[CalcItemDef],
        description: Optional[str] = None,
    ) -> str:
        """
        Generate TMDL script for a calculation group

        Args:
            name: Calculation group name
            items: List of calculation items
            description: Group description

        Returns:
            TMDL script as string
        """
        lines = [
            f"table '{name}'",
            f"\tlineageTag: {self._generate_lineage_tag()}",
            "\tcalculationGroup",
        ]

        if description:
            lines.append(f"\tdescription: \"{description}\"")

        # Name column (required for calculation groups)
        lines.append("")
        lines.append("\tcolumn Name")
        lines.append("\t\tdataType: string")
        lines.append("\t\tisDataTypeInferred: false")
        lines.append(f"\t\tlineageTag: {self._generate_lineage_tag()}")

        # Calculation items
        for item in sorted(items, key=lambda x: x.ordinal):
            lines.append("")
            lines.extend(self._generate_calculation_item(item))

        return "\n".join(lines)

    def _generate_calculation_item(self, item: CalcItemDef) -> List[str]:
        """Generate calculation item TMDL"""
        lines = [f"\tcalculationItem {item.name}"]

        # Expression
        lines.append("\t\texpression:")
        for line in item.expression.split("\n"):
            lines.append(f"\t\t\t{line}")

        if item.format_string:
            lines.append(f"\t\tformatString: {item.format_string}")

        lines.append(f"\t\tordinal: {item.ordinal}")

        return lines

    def generate_from_definition(
        self,
        object_type: str,
        definition: Dict[str, Any]
    ) -> str:
        """
        Generate TMDL script from a definition dictionary

        Args:
            object_type: "table", "measure", "relationship", "calculation_group"
            definition: Object definition as dictionary

        Returns:
            TMDL script as string
        """
        if object_type == "table":
            columns = [
                ColumnDef(**col) for col in definition.get("columns", [])
            ]
            partitions = None
            if "partitions" in definition:
                partitions = [
                    PartitionDef(**part) for part in definition["partitions"]
                ]

            return self.generate_table(
                name=definition["name"],
                columns=columns,
                partitions=partitions,
                description=definition.get("description")
            )

        elif object_type == "measure":
            return self.generate_measure(
                table=definition["table"],
                name=definition["name"],
                expression=definition["expression"],
                properties=definition.get("properties", {})
            )

        elif object_type == "relationship":
            return self.generate_relationship(
                from_table=definition["from_table"],
                from_column=definition["from_column"],
                to_table=definition["to_table"],
                to_column=definition["to_column"],
                cardinality=definition.get("cardinality", "many-to-one"),
                cross_filter_direction=definition.get("cross_filter_direction", "single"),
                is_active=definition.get("is_active", True)
            )

        elif object_type == "calculation_group":
            items = [
                CalcItemDef(**item) for item in definition.get("items", [])
            ]

            return self.generate_calculation_group(
                name=definition["name"],
                items=items,
                description=definition.get("description")
            )

        else:
            raise ValueError(f"Unsupported object type: {object_type}")

    def _generate_lineage_tag(self) -> str:
        """Generate unique lineage tag"""
        return str(uuid.uuid4())

    def _generate_relationship_name(self, from_table: str, to_table: str) -> str:
        """Generate relationship name"""
        # Simplified naming
        return f"{from_table}_{to_table}"
