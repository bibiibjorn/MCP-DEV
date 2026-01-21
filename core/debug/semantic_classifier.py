"""
Semantic Filter Classification

Uses DMV queries to detect field parameters via NAMEOF patterns, composite keys,
and structural analysis. Provides higher-confidence classification than pattern matching.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SemanticClassification:
    """Result of semantic classification for a table/column."""
    table: str
    column: str
    classification: str  # 'data', 'field_parameter', 'ui_control'
    confidence: float  # 0.0 - 1.0
    detection_method: str  # 'nameof_pattern', 'composite_key', 'switch_pattern', 'naming_convention'
    references: List[str] = field(default_factory=list)  # Referenced columns for field params


class SemanticFilterClassifier:
    """
    Classifies filters using DMV queries and semantic analysis.

    Detection methods (in order of confidence):
    1. NAMEOF pattern in calculated table expression (0.95)
    2. SWITCH(SELECTEDVALUE(...)) pattern in measures (0.90)
    3. Composite key detection - multiple IsKey columns (0.85)
    4. Naming convention fallback (0.70)
    """

    # Regex patterns for detection
    NAMEOF_PATTERN = re.compile(
        r"NAMEOF\s*\(\s*['\"]?([^'\"\[\s]+)['\"]?\s*\[\s*([^\]]+)\s*\]\s*\)",
        re.IGNORECASE
    )

    SWITCH_SELECTEDVALUE_PATTERN = re.compile(
        r"SWITCH\s*\(\s*(?:TRUE\s*\(\s*\)\s*,\s*)?SELECTEDVALUE\s*\(\s*['\"]?([^'\"\[\s]+)['\"]?\s*\[\s*([^\]]+)\s*\]",
        re.IGNORECASE
    )

    def __init__(self, query_executor=None):
        """
        Initialize the classifier.

        Args:
            query_executor: QueryExecutor for DMV queries (optional, enables semantic detection)
        """
        self.qe = query_executor
        self._cache: Dict[str, SemanticClassification] = {}
        self._model_analyzed = False

        # Detected tables by category
        self._field_param_tables: Set[str] = set()
        self._composite_key_tables: Set[str] = set()
        self._ui_control_tables: Set[str] = set()

        # Table references (for field params: what columns they reference)
        self._table_references: Dict[str, List[str]] = {}

    def analyze_model(self) -> bool:
        """
        Analyze model metadata to identify field parameter and UI control tables.

        Returns:
            True if analysis succeeded, False otherwise
        """
        if self._model_analyzed:
            return True

        if not self.qe:
            logger.debug("No query executor available for semantic analysis")
            return False

        try:
            # Step 1: Query tables for SystemFlags=2 (definitive field parameter indicator)
            self._detect_field_params_from_system_flags()

            # Step 2: Query columns to detect composite keys
            self._detect_composite_key_tables()

            # Step 3: Query measures for SWITCH(SELECTEDVALUE(...)) patterns
            self._detect_field_params_from_measures()

            # Step 4: Query calculated tables for NAMEOF patterns
            self._detect_field_params_from_expressions()

            self._model_analyzed = True
            logger.info(
                f"Semantic analysis complete: {len(self._field_param_tables)} field param tables, "
                f"{len(self._composite_key_tables)} composite key tables"
            )
            return True

        except Exception as e:
            logger.warning(f"Error during semantic model analysis: {e}")
            return False

    def _detect_field_params_from_system_flags(self) -> None:
        """Detect field parameter tables using SystemFlags=2 from TABLES DMV."""
        try:
            result = self.qe.execute_info_query("TABLES")
            if not result.get('success'):
                return

            for table in result.get('rows', []):
                table_name = table.get('Name', table.get('[Name]', ''))
                # SystemFlags=2 is the definitive indicator of a field parameter table
                system_flags = table.get('SystemFlags', table.get('[SystemFlags]', 0))

                if system_flags == 2 and table_name:
                    self._field_param_tables.add(table_name)
                    logger.debug(f"Detected field param table (SystemFlags=2): {table_name}")

        except Exception as e:
            logger.debug(f"Error detecting field params from SystemFlags: {e}")

    def _detect_composite_key_tables(self) -> None:
        """Detect tables with composite keys from column metadata."""
        try:
            result = self.qe.execute_info_query("COLUMNS")
            if not result.get('success'):
                return

            # Group key columns by table
            key_columns_by_table: Dict[str, List[str]] = {}

            for col in result.get('rows', []):
                table_name = col.get('Table', col.get('[Table]', ''))
                is_key = col.get('IsKey', col.get('[IsKey]', False))
                col_name = col.get('Name', col.get('[Name]', ''))

                if is_key and table_name:
                    if table_name not in key_columns_by_table:
                        key_columns_by_table[table_name] = []
                    key_columns_by_table[table_name].append(col_name)

            # Tables with multiple key columns have composite keys
            for table_name, key_cols in key_columns_by_table.items():
                if len(key_cols) > 1:
                    self._composite_key_tables.add(table_name)
                    logger.debug(f"Detected composite key table: {table_name} (keys: {key_cols})")

        except Exception as e:
            logger.debug(f"Error detecting composite keys: {e}")

    def _detect_field_params_from_measures(self) -> None:
        """Detect field parameter tables from SWITCH(SELECTEDVALUE(...)) patterns in measures."""
        try:
            result = self.qe.execute_info_query("MEASURES")
            if not result.get('success'):
                return

            for measure in result.get('rows', []):
                expression = measure.get('Expression', measure.get('[Expression]', ''))
                if not expression:
                    continue

                # Find SWITCH(SELECTEDVALUE('Table'[Column])) patterns
                matches = self.SWITCH_SELECTEDVALUE_PATTERN.findall(expression)

                for table, column in matches:
                    table_clean = table.strip("'\"")
                    self._field_param_tables.add(table_clean)

                    # Extract referenced columns from the SWITCH branches
                    refs = self._extract_switch_references(expression)
                    if refs:
                        self._table_references[table_clean] = refs

                    logger.debug(f"Detected field param from measure: {table_clean}")

        except Exception as e:
            logger.debug(f"Error detecting field params from measures: {e}")

    def _extract_switch_references(self, expression: str) -> List[str]:
        """Extract column references from SWITCH branches."""
        refs = []
        # Match patterns like "Column Name", [Measure Name]
        col_pattern = re.compile(r"\[([^\]]+)\]")
        matches = col_pattern.findall(expression)
        # Return unique references (limit to first 10)
        return list(set(matches))[:10]

    def _detect_field_params_from_expressions(self) -> None:
        """Detect field parameter tables from NAMEOF patterns in calculated tables."""
        try:
            # Query partitions for calculated table expressions
            query = """
            EVALUATE
            SELECTCOLUMNS(
                INFO.PARTITIONS(),
                "Table", [TableName],
                "Source", [QueryDefinition]
            )
            """
            result = self.qe.validate_and_execute_dax(query, top_n=500)

            if not result.get('success'):
                return

            for row in result.get('rows', []):
                table_name = row.get('Table', '')
                source = row.get('Source', '')

                if not source or not table_name:
                    continue

                # Check for NAMEOF pattern
                if 'NAMEOF' in source.upper():
                    self._field_param_tables.add(table_name)

                    # Extract referenced columns
                    matches = self.NAMEOF_PATTERN.findall(source)
                    refs = [f"'{t}'[{c}]" for t, c in matches]
                    if refs:
                        self._table_references[table_name] = refs

                    logger.debug(f"Detected field param table: {table_name} -> {refs}")

        except Exception as e:
            logger.debug(f"Error detecting field params from expressions: {e}")

    def classify(self, table: str, column: str = '') -> SemanticClassification:
        """
        Classify a filter by table and column.

        Args:
            table: Table name
            column: Column name (optional)

        Returns:
            SemanticClassification with classification and confidence
        """
        cache_key = f"'{table}'[{column}]"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Ensure model is analyzed (lazy)
        if not self._model_analyzed:
            self.analyze_model()

        # Normalize table name
        table_clean = table.strip("'\"")

        # Check DMV-detected field parameters (highest confidence)
        if table_clean in self._field_param_tables:
            result = SemanticClassification(
                table=table,
                column=column,
                classification='field_parameter',
                confidence=0.95,
                detection_method='nameof_pattern' if table_clean in self._table_references else 'switch_pattern',
                references=self._table_references.get(table_clean, [])
            )
            self._cache[cache_key] = result
            return result

        # Note: Composite key detection is NO LONGER used for field parameter classification
        # Many dimension tables (d Family, d Asset, etc.) have composite keys legitimately
        # and should NOT be classified as field parameters.
        # Composite keys are only relevant when combined with other signals (NAMEOF, SWITCH).
        # The code below is kept for reference but disabled:
        #
        # if table_clean in self._composite_key_tables:
        #     result = SemanticClassification(...)
        #     return result

        # Check UI control tables
        if table_clean in self._ui_control_tables:
            result = SemanticClassification(
                table=table,
                column=column,
                classification='ui_control',
                confidence=0.80,
                detection_method='ui_pattern',
                references=[]
            )
            self._cache[cache_key] = result
            return result

        # Fallback to pattern-based classification
        from .filter_to_dax import is_field_parameter_table, is_ui_control_table, FilterClassification

        if is_field_parameter_table(table):
            classification = FilterClassification.FIELD_PARAMETER
            confidence = 0.70
        elif is_ui_control_table(table):
            classification = FilterClassification.UI_CONTROL
            confidence = 0.70
        else:
            classification = FilterClassification.DATA
            confidence = 0.50

        result = SemanticClassification(
            table=table,
            column=column,
            classification=classification,
            confidence=confidence,
            detection_method='naming_convention',
            references=[]
        )
        self._cache[cache_key] = result
        return result

    def get_field_param_tables(self) -> Set[str]:
        """Get all detected field parameter tables."""
        if not self._model_analyzed:
            self.analyze_model()
        return self._field_param_tables.copy()

    def clear_cache(self) -> None:
        """Clear the classification cache."""
        self._cache.clear()
        self._model_analyzed = False
        self._field_param_tables.clear()
        self._composite_key_tables.clear()
        self._ui_control_tables.clear()
        self._table_references.clear()
