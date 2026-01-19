# Debug Tools Enhancement - Full Implementation Specification

## Overview

Enhance the MCP PowerBI debug tools by integrating 8 new features INTO the existing 12 tools (no new tools added).

---

## Table of Contents

1. [Module Organization](#module-organization)
2. [Feature 1: PBIP Freshness Warning](#feature-1-pbip-freshness-warning)
3. [Feature 2: Measure Expression Truncation Fix](#feature-2-measure-expression-truncation-fix)
4. [Feature 3: Auto-Retry with Filter Exclusion](#feature-3-auto-retry-with-filter-exclusion)
5. [Feature 4: Semantic Filter Classification](#feature-4-semantic-filter-classification)
6. [Feature 5: Anomaly Detection](#feature-5-anomaly-detection)
7. [Feature 6: Parallel Visual Profiling](#feature-6-parallel-visual-profiling)
8. [Feature 7: Relationship-Aware Query Generation](#feature-7-relationship-aware-query-generation)
9. [Feature 8: Aggregation Support](#feature-8-aggregation-support)
10. [Integration Changes](#integration-changes)
11. [Testing Strategy](#testing-strategy)

---

## Module Organization

### New Files to Create

```
core/debug/
├── semantic_classifier.py    # DMV-based field parameter detection
├── anomaly_detector.py       # Statistical anomaly detection
├── relationship_resolver.py  # Relationship-aware query generation
└── aggregation_matcher.py    # Aggregation table matching
```

### Existing Files to Modify

```
server/handlers/debug_handler.py   # Freshness, truncation, anomaly integration
core/debug/debug_operations.py     # Parallel profiling, auto-retry logic
core/debug/filter_to_dax.py        # Semantic classifier integration
core/debug/visual_query_builder.py # Relationship + aggregation integration
core/debug/__init__.py             # Export new modules
```

---

## Feature 1: PBIP Freshness Warning

### File: `server/handlers/debug_handler.py`

Add after line 89 (after `_compact_filter_context`):

```python
import os
import time
from pathlib import Path


def _check_pbip_freshness(pbip_folder: str, threshold_minutes: int = 5) -> Optional[Dict[str, Any]]:
    """
    Check if PBIP files have been modified recently.

    Args:
        pbip_folder: Path to the PBIP folder
        threshold_minutes: Warn if files are older than this (default 5 minutes)

    Returns:
        Warning dict if stale, None if fresh
    """
    if not pbip_folder or not os.path.exists(pbip_folder):
        return None

    pbip_path = Path(pbip_folder)
    latest_mtime = 0

    # Check key PBIP files for most recent modification
    patterns = ['**/*.json', '**/*.tmdl']

    for pattern in patterns:
        for file_path in pbip_path.rglob(pattern):
            try:
                mtime = file_path.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
            except OSError:
                continue

    if latest_mtime == 0:
        return None

    age_seconds = time.time() - latest_mtime
    age_minutes = age_seconds / 60

    if age_minutes > threshold_minutes:
        return {
            'stale': True,
            'age_minutes': round(age_minutes, 1),
            'message': f'PBIP files are {round(age_minutes, 1)} minutes old. Save your report for accurate slicer state.',
            'hint': 'Use filters parameter to override with current values if needed.'
        }

    return None
```

### Integration in `handle_debug_visual()`:

After line 126 (after `builder, error = _get_visual_query_builder()`):

```python
        # Check PBIP freshness
        pbip_freshness = _check_pbip_freshness(connection_state.get_pbip_folder_path())
```

In response building (around line 242), add:

```python
        # Add PBIP freshness warning if applicable
        if pbip_freshness:
            response['pbip_warning'] = pbip_freshness
```

---

## Feature 2: Measure Expression Truncation Fix

### File: `server/handlers/debug_handler.py`

#### Update `_compact_response()` (lines 18-51):

Replace the function with:

```python
def _compact_response(data: Dict[str, Any], compact: bool = True) -> Dict[str, Any]:
    """
    Optimize response for token usage when compact=True.
    Removes empty values, shortens verbose fields, removes redundant data.
    Preserves important diagnostic fields like anomalies and warnings.
    """
    if not compact:
        return data

    # Fields to preserve even in compact mode (important diagnostic info)
    PRESERVE_FIELDS = {
        'anomalies', 'pbip_warning', 'relationship_hints',
        'aggregation_info', 'retry_info', 'execution_mode'
    }

    # Fields to skip in compact mode (verbose/redundant)
    SKIP_FIELDS = {'original', 'selected_values_raw', 'hint', 'recommendations'}

    def clean_dict(d: Dict) -> Dict:
        """Recursively remove empty/None values and shorten verbose fields."""
        result = {}
        for k, v in d.items():
            # Skip empty values
            if v is None or v == '' or v == [] or v == {}:
                continue

            # Always preserve important diagnostic fields
            if k in PRESERVE_FIELDS:
                result[k] = v
                continue

            # Skip redundant/verbose fields in compact mode
            if k in SKIP_FIELDS:
                continue

            # Recursively clean nested dicts
            if isinstance(v, dict):
                cleaned = clean_dict(v)
                if cleaned:  # Only include non-empty dicts
                    result[k] = cleaned
            # Clean lists of dicts
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                cleaned_list = [clean_dict(item) for item in v]
                cleaned_list = [item for item in cleaned_list if item]
                if cleaned_list:
                    result[k] = cleaned_list
            else:
                result[k] = v
        return result

    return clean_dict(data)
```

#### Update expression truncation in `handle_analyze_measure()`:

Find the line with expression truncation (around line 1070) and change:

```python
# Before:
'expression': expression[:300] + '...' if len(expression) > 300 else expression

# After:
'expression': expression[:800] + '... [truncated]' if len(expression) > 800 else expression
```

---

## Feature 3: Auto-Retry with Filter Exclusion

### File: `core/debug/debug_operations.py`

Add this method to the `DebugOperations` class (after line 175):

```python
    def _execute_with_smart_retry(
        self,
        query: str,
        filters: List,
        rebuild_query_func,
        top_n: int = 100
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Execute query with automatic retry on composite key error.

        On composite key error:
        1. Identify field_parameter filters
        2. Rebuild query excluding them
        3. Retry execution
        4. Return result with retry info

        Args:
            query: DAX query to execute
            filters: List of FilterExpression objects
            rebuild_query_func: Function to rebuild query with reduced filters
            top_n: Max rows to return

        Returns:
            Tuple of (execution_result, retry_info or None)
        """
        from .filter_to_dax import FilterClassification

        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}, None

        # First attempt with full query
        exec_result = self.qe.validate_and_execute_dax(query, top_n=top_n)

        if exec_result.get('success'):
            return exec_result, None

        error_msg = exec_result.get('error', '').lower()

        # Check for composite key / ambiguous relationship errors
        retry_patterns = [
            'composite',
            'multiple columns',
            'ambiguous',
            'cannot determine',
            'more than one',
            'duplicate key'
        ]

        should_retry = any(pattern in error_msg for pattern in retry_patterns)

        if not should_retry:
            return exec_result, None

        # Identify field parameter filters to exclude
        field_param_filters = [
            f for f in filters
            if getattr(f, 'classification', '') == FilterClassification.FIELD_PARAMETER
            or getattr(f, 'is_field_parameter', False)
        ]

        if not field_param_filters:
            # No field parameters to exclude, can't help
            return exec_result, None

        # Build excluded filter descriptions for reporting
        excluded_descriptions = [
            f"'{f.table}'[{f.column}]" for f in field_param_filters
        ]

        self.logger.info(
            f"Composite key error detected, retrying without {len(field_param_filters)} "
            f"field parameter filters: {excluded_descriptions}"
        )

        # Filter out field parameter filters
        reduced_filters = [
            f for f in filters
            if f not in field_param_filters
        ]

        # Rebuild query with reduced filters
        try:
            reduced_query = rebuild_query_func(reduced_filters)
        except Exception as e:
            self.logger.warning(f"Failed to rebuild query: {e}")
            return exec_result, None

        # Retry with reduced query
        retry_result = self.qe.validate_and_execute_dax(reduced_query, top_n=top_n)

        retry_info = {
            'retried': True,
            'original_error': exec_result.get('error'),
            'excluded_filters': excluded_descriptions,
            'reason': 'Composite key error resolved by excluding field parameter filters'
        }

        if retry_result.get('success'):
            retry_info['success'] = True
            retry_info['note'] = 'Results may differ from visual due to excluded field parameters'
        else:
            retry_info['success'] = False
            retry_info['retry_error'] = retry_result.get('error')

        return retry_result, retry_info
```

---

## Feature 4: Semantic Filter Classification

### New File: `core/debug/semantic_classifier.py`

```python
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
            # Step 1: Query columns to detect composite keys
            self._detect_composite_key_tables()

            # Step 2: Query measures for SWITCH(SELECTEDVALUE(...)) patterns
            self._detect_field_params_from_measures()

            # Step 3: Query calculated tables for NAMEOF patterns
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

        # Check composite key tables (high confidence)
        if table_clean in self._composite_key_tables:
            result = SemanticClassification(
                table=table,
                column=column,
                classification='field_parameter',
                confidence=0.85,
                detection_method='composite_key',
                references=[]
            )
            self._cache[cache_key] = result
            return result

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
```

---

## Feature 5: Anomaly Detection

### New File: `core/debug/anomaly_detector.py`

```python
"""
Anomaly Detection for Debug Results

Detects statistical outliers, unexpected nulls, value distribution anomalies,
and semantically unexpected values in query results.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Represents a detected anomaly in query results."""
    type: str           # 'outlier', 'null_concentration', 'unexpected_value', 'empty_result', 'variance'
    severity: str       # 'info', 'warning', 'critical'
    column: str         # Column where anomaly was detected ('*' for row-level)
    description: str    # Human-readable description
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyReport:
    """Complete anomaly analysis report."""
    anomalies: List[Anomaly] = field(default_factory=list)
    stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Per-column statistics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        if not self.anomalies:
            return {}

        return {
            'count': len(self.anomalies),
            'by_severity': {
                'critical': len([a for a in self.anomalies if a.severity == 'critical']),
                'warning': len([a for a in self.anomalies if a.severity == 'warning']),
                'info': len([a for a in self.anomalies if a.severity == 'info'])
            },
            'items': [
                {
                    'type': a.type,
                    'severity': a.severity,
                    'column': a.column,
                    'description': a.description
                }
                for a in self.anomalies
            ]
        }

    def has_issues(self) -> bool:
        """Check if any significant anomalies were found."""
        return any(a.severity in ('warning', 'critical') for a in self.anomalies)


class AnomalyDetector:
    """
    Detects anomalies in query result sets.

    Detection types:
    - Empty results
    - Statistical outliers (IQR method)
    - Null concentration (>50% nulls)
    - Unexpected values (negative amounts, etc.)
    - High variance in numeric columns
    """

    # Configurable thresholds
    NULL_THRESHOLD_PCT = 0.5      # Warn if >50% nulls
    IQR_MULTIPLIER = 1.5          # Standard IQR outlier detection
    MIN_ROWS_FOR_STATS = 5        # Minimum rows for statistical analysis
    HIGH_VARIANCE_CV = 2.0        # Coefficient of variation threshold

    # Columns that should typically be non-negative
    NON_NEGATIVE_KEYWORDS = [
        'sales', 'revenue', 'amount', 'count', 'quantity', 'total',
        'price', 'cost', 'profit', 'units', 'volume'
    ]

    def __init__(self):
        """Initialize the anomaly detector."""
        pass

    def analyze(
        self,
        rows: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> AnomalyReport:
        """
        Analyze query results for anomalies.

        Args:
            rows: Query result rows
            context: Optional context (measure name, expected range, etc.)

        Returns:
            AnomalyReport with detected anomalies and statistics
        """
        report = AnomalyReport()

        # Check for empty results
        if not rows:
            report.anomalies.append(Anomaly(
                type='empty_result',
                severity='warning',
                column='*',
                description='Query returned no rows',
                details={'row_count': 0}
            ))
            return report

        # Analyze each column
        columns = list(rows[0].keys())

        for col_name in columns:
            values = [row.get(col_name) for row in rows]

            # Check for null concentration
            null_anomaly = self._check_null_concentration(col_name, values)
            if null_anomaly:
                report.anomalies.append(null_anomaly)

            # Extract numeric values for statistical analysis
            numeric_values = [
                v for v in values
                if isinstance(v, (int, float)) and v is not None
            ]

            if len(numeric_values) >= self.MIN_ROWS_FOR_STATS:
                # Compute and store statistics
                stats = self._compute_stats(numeric_values)
                report.stats[col_name] = stats

                # Check for statistical outliers
                outlier_anomalies = self._check_outliers(col_name, numeric_values, stats)
                report.anomalies.extend(outlier_anomalies)

                # Check for high variance
                variance_anomaly = self._check_high_variance(col_name, stats)
                if variance_anomaly:
                    report.anomalies.append(variance_anomaly)

            # Check for semantically unexpected values
            unexpected = self._check_unexpected_values(col_name, values, context)
            report.anomalies.extend(unexpected)

        return report

    def _check_null_concentration(
        self,
        col_name: str,
        values: List[Any]
    ) -> Optional[Anomaly]:
        """Check if column has unexpected null concentration."""
        if not values:
            return None

        null_count = sum(1 for v in values if v is None)
        total = len(values)
        null_pct = null_count / total

        if null_count == total:
            return Anomaly(
                type='null_concentration',
                severity='critical',
                column=col_name,
                description=f'All {total} values are NULL',
                details={'null_count': null_count, 'null_pct': 1.0, 'total': total}
            )
        elif null_pct > self.NULL_THRESHOLD_PCT:
            return Anomaly(
                type='null_concentration',
                severity='warning',
                column=col_name,
                description=f'{null_count}/{total} ({null_pct:.0%}) values are NULL',
                details={'null_count': null_count, 'null_pct': round(null_pct, 2), 'total': total}
            )

        return None

    def _check_outliers(
        self,
        col_name: str,
        values: List[float],
        stats: Dict[str, Any]
    ) -> List[Anomaly]:
        """Detect statistical outliers using IQR method."""
        anomalies = []

        if len(values) < self.MIN_ROWS_FOR_STATS:
            return anomalies

        q1 = stats.get('q1', 0)
        q3 = stats.get('q3', 0)
        iqr = q3 - q1

        if iqr == 0:
            return anomalies  # All values are the same, no outliers

        lower_bound = q1 - (self.IQR_MULTIPLIER * iqr)
        upper_bound = q3 + (self.IQR_MULTIPLIER * iqr)

        outliers_low = [v for v in values if v < lower_bound]
        outliers_high = [v for v in values if v > upper_bound]
        outliers = outliers_low + outliers_high

        if outliers:
            # Determine severity based on outlier count
            outlier_pct = len(outliers) / len(values)
            severity = 'warning' if outlier_pct > 0.1 else 'info'

            anomalies.append(Anomaly(
                type='outlier',
                severity=severity,
                column=col_name,
                description=f'{len(outliers)} outliers ({outlier_pct:.0%}) outside IQR bounds',
                details={
                    'outlier_count': len(outliers),
                    'bounds': {'lower': round(lower_bound, 2), 'upper': round(upper_bound, 2)},
                    'examples_low': sorted(outliers_low)[:3] if outliers_low else [],
                    'examples_high': sorted(outliers_high, reverse=True)[:3] if outliers_high else []
                }
            ))

        return anomalies

    def _check_high_variance(
        self,
        col_name: str,
        stats: Dict[str, Any]
    ) -> Optional[Anomaly]:
        """Check for unusually high variance (coefficient of variation)."""
        mean = stats.get('mean', 0)
        stdev = stats.get('stdev', 0)

        if mean == 0 or stdev == 0:
            return None

        cv = abs(stdev / mean)  # Coefficient of variation

        if cv > self.HIGH_VARIANCE_CV:
            return Anomaly(
                type='variance',
                severity='info',
                column=col_name,
                description=f'High variance detected (CV={cv:.2f})',
                details={
                    'coefficient_of_variation': round(cv, 2),
                    'mean': round(mean, 2),
                    'stdev': round(stdev, 2)
                }
            )

        return None

    def _check_unexpected_values(
        self,
        col_name: str,
        values: List[Any],
        context: Optional[Dict[str, Any]]
    ) -> List[Anomaly]:
        """Check for semantically unexpected values based on column name."""
        anomalies = []
        col_lower = col_name.lower()

        # Get numeric values
        numeric_values = [
            v for v in values
            if isinstance(v, (int, float)) and v is not None
        ]

        if not numeric_values:
            return anomalies

        # Check for negative values in columns that should be non-negative
        should_be_positive = any(kw in col_lower for kw in self.NON_NEGATIVE_KEYWORDS)

        if should_be_positive:
            negative_values = [v for v in numeric_values if v < 0]

            if negative_values:
                anomalies.append(Anomaly(
                    type='unexpected_value',
                    severity='warning',
                    column=col_name,
                    description=f'{len(negative_values)} negative values in {col_name}',
                    details={
                        'negative_count': len(negative_values),
                        'examples': sorted(negative_values)[:5]
                    }
                ))

        return anomalies

    def _compute_stats(self, values: List[float]) -> Dict[str, Any]:
        """Compute basic statistics for a numeric column."""
        if not values:
            return {}

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        # Calculate mean
        mean = sum(values) / n

        # Calculate standard deviation
        if n > 1:
            variance = sum((x - mean) ** 2 for x in values) / (n - 1)
            stdev = variance ** 0.5
        else:
            stdev = 0

        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = (3 * n) // 4
        median_idx = n // 2

        return {
            'min': sorted_vals[0],
            'max': sorted_vals[-1],
            'mean': round(mean, 4),
            'median': sorted_vals[median_idx],
            'stdev': round(stdev, 4),
            'q1': sorted_vals[q1_idx],
            'q3': sorted_vals[q3_idx],
            'count': n
        }


def analyze_results(rows: List[Dict], context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze results and return dict.

    Args:
        rows: Query result rows
        context: Optional context

    Returns:
        Anomaly report as dictionary (empty dict if no anomalies)
    """
    detector = AnomalyDetector()
    report = detector.analyze(rows, context)
    return report.to_dict()
```

---

## Feature 6: Parallel Visual Profiling

### File: `core/debug/debug_operations.py`

Replace the `profile_page()` method (lines 503-625) with:

```python
    def profile_page(
        self,
        page_name: str,
        iterations: int = 3,
        include_slicers: bool = True,
        parallel: bool = True,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Profile all visuals on a page to identify slow visuals.

        Args:
            page_name: Page to profile
            iterations: Number of times to run each visual for averaging
            include_slicers: Include slicer filters
            parallel: Use parallel execution (default True)
            max_workers: Max concurrent queries (default 4)

        Returns:
            Page profile with timing and issues
        """
        if not self.qe:
            return {'success': False, 'error': 'Not connected to Power BI model'}

        visuals = self.builder.list_visuals(page_name)
        if not visuals:
            return {'success': False, 'error': f'No visuals found on page "{page_name}"'}

        # Filter to data visuals only (exclude slicers)
        data_visuals = [v for v in visuals if not v.get('is_slicer')]

        if not data_visuals:
            return {
                'success': True,
                'page': page_name,
                'visuals_profiled': 0,
                'message': 'No data visuals to profile (page contains only slicers/UI elements)'
            }

        results: List[ProfileResult] = []

        def _profile_single_visual(visual: Dict) -> Optional[ProfileResult]:
            """Profile a single visual (thread-safe)."""
            try:
                query_result = self.builder.build_visual_query(
                    page_name=page_name,
                    visual_id=visual['id'],
                    include_slicers=include_slicers
                )

                if not query_result or not query_result.dax_query:
                    return None

                times = []
                row_count = 0

                for _ in range(iterations):
                    exec_result = self.qe.validate_and_execute_dax(
                        query_result.dax_query, top_n=100
                    )
                    if exec_result.get('success'):
                        times.append(exec_result.get('execution_time_ms', 0))
                        row_count = max(row_count, len(exec_result.get('rows', [])))

                if not times:
                    return None

                avg_time = sum(times) / len(times)

                # Identify issues
                issues = []
                if avg_time > 2000:
                    issues.append(f'Slow query ({avg_time:.0f}ms > 2000ms)')
                if row_count > 1000:
                    issues.append(f'Large result set ({row_count} rows)')
                if max(times) > min(times) * 2 and len(times) > 1:
                    issues.append(f'High variance ({min(times):.0f}-{max(times):.0f}ms)')

                return ProfileResult(
                    visual_id=visual['id'],
                    visual_name=visual.get('friendly_name', visual['id']),
                    visual_type=visual.get('type', 'unknown'),
                    page_name=page_name,
                    measures=visual.get('measures', []),
                    avg_time_ms=avg_time,
                    min_time_ms=min(times),
                    max_time_ms=max(times),
                    row_count=row_count,
                    filter_count=len(query_result.filter_context.all_filters()),
                    issues=issues
                )
            except Exception as e:
                self.logger.warning(f"Error profiling visual {visual['id']}: {e}")
                return None

        # Execute profiling
        execution_mode = 'sequential'

        if parallel and len(data_visuals) > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            execution_mode = 'parallel'

            with ThreadPoolExecutor(max_workers=min(max_workers, len(data_visuals))) as executor:
                futures = {
                    executor.submit(_profile_single_visual, v): v
                    for v in data_visuals
                }

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        visual = futures[future]
                        self.logger.warning(f"Future failed for visual {visual.get('id')}: {e}")
        else:
            # Sequential execution
            for visual in data_visuals:
                result = _profile_single_visual(visual)
                if result:
                    results.append(result)

        # Sort by avg time descending
        results.sort(key=lambda x: x.avg_time_ms, reverse=True)

        total_time = sum(r.avg_time_ms for r in results)

        # Generate recommendations
        recommendations = []
        slow_visuals = [r for r in results if r.avg_time_ms > 1000]

        if slow_visuals:
            recommendations.append(
                f'Optimize {len(slow_visuals)} slow visual(s): ' +
                ', '.join(r.visual_name for r in slow_visuals[:3])
            )

        if total_time > 5000:
            recommendations.append(
                f'Page total load time ({total_time:.0f}ms) exceeds 5s target'
            )

        large_results = [r for r in results if r.row_count > 500]
        if large_results:
            recommendations.append(
                f'{len(large_results)} visual(s) return large result sets - consider aggregation'
            )

        return {
            'success': True,
            'page': page_name,
            'visuals_profiled': len(results),
            'total_time_ms': round(total_time, 1),
            'avg_time_per_visual_ms': round(total_time / len(results), 1) if results else 0,
            'execution_mode': execution_mode,
            'results': [
                {
                    'visual_id': r.visual_id,
                    'visual_name': r.visual_name,
                    'visual_type': r.visual_type,
                    'measures': r.measures,
                    'avg_time_ms': round(r.avg_time_ms, 1),
                    'min_time_ms': round(r.min_time_ms, 1),
                    'max_time_ms': round(r.max_time_ms, 1),
                    'row_count': r.row_count,
                    'filter_count': r.filter_count,
                    'issues': r.issues
                }
                for r in results
            ],
            'recommendations': recommendations
        }
```

---

## Feature 7: Relationship-Aware Query Generation

### New File: `core/debug/relationship_resolver.py`

```python
"""
Relationship-Aware Query Generation

Analyzes model relationships and suggests DAX modifiers (USERELATIONSHIP, CROSSFILTER)
when queries involve inactive relationships or need bidirectional filtering.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RelationshipInfo:
    """Information about a model relationship."""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    is_active: bool
    cross_filter_direction: str  # 'Single', 'Both', 'None'
    cardinality: str  # 'OneToMany', 'ManyToOne', 'ManyToMany', 'OneToOne'


@dataclass
class RelationshipHint:
    """Suggestion for relationship handling in a query."""
    type: str               # 'use_relationship', 'crossfilter_both', 'ambiguous_path'
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    dax_modifier: str       # DAX to add to CALCULATE
    reason: str             # Human-readable explanation
    severity: str = 'info'  # 'info', 'warning'


class RelationshipResolver:
    """
    Analyzes relationships and generates appropriate DAX modifiers.

    Detects:
    1. Inactive relationships that may need activation (USERELATIONSHIP)
    2. Single-direction relationships that may need bidirectional (CROSSFILTER)
    3. Ambiguous relationship paths
    """

    def __init__(self, query_executor=None):
        """
        Initialize the resolver.

        Args:
            query_executor: QueryExecutor for DMV queries
        """
        self.qe = query_executor
        self._relationships: List[RelationshipInfo] = []
        self._loaded = False

        # Index for quick lookup
        self._by_from_table: Dict[str, List[RelationshipInfo]] = {}
        self._by_to_table: Dict[str, List[RelationshipInfo]] = {}
        self._inactive_pairs: Set[Tuple[str, str]] = set()  # (from_table, to_table)

    def load_relationships(self) -> bool:
        """
        Load relationships from the model.

        Returns:
            True if relationships were loaded successfully
        """
        if self._loaded:
            return True

        if not self.qe:
            logger.debug("No query executor available for relationship loading")
            return False

        try:
            result = self.qe.execute_info_query("RELATIONSHIPS")

            if not result.get('success'):
                logger.warning(f"Failed to load relationships: {result.get('error')}")
                return False

            for row in result.get('rows', []):
                rel = RelationshipInfo(
                    from_table=row.get('FromTable', row.get('[FromTable]', '')),
                    from_column=row.get('FromColumn', row.get('[FromColumn]', '')),
                    to_table=row.get('ToTable', row.get('[ToTable]', '')),
                    to_column=row.get('ToColumn', row.get('[ToColumn]', '')),
                    is_active=row.get('IsActive', row.get('[IsActive]', True)),
                    cross_filter_direction=row.get('CrossFilterDirection', row.get('[CrossFilterDirection]', 'Single')),
                    cardinality=row.get('Cardinality', row.get('[Cardinality]', 'OneToMany'))
                )

                self._relationships.append(rel)

                # Build indexes
                if rel.from_table not in self._by_from_table:
                    self._by_from_table[rel.from_table] = []
                self._by_from_table[rel.from_table].append(rel)

                if rel.to_table not in self._by_to_table:
                    self._by_to_table[rel.to_table] = []
                self._by_to_table[rel.to_table].append(rel)

                if not rel.is_active:
                    self._inactive_pairs.add((rel.from_table, rel.to_table))

            self._loaded = True
            logger.info(f"Loaded {len(self._relationships)} relationships ({len(self._inactive_pairs)} inactive)")
            return True

        except Exception as e:
            logger.warning(f"Error loading relationships: {e}")
            return False

    def analyze_query_tables(
        self,
        measure_tables: List[str],
        filter_tables: List[str],
        grouping_tables: List[str]
    ) -> List[RelationshipHint]:
        """
        Analyze tables involved in a query and suggest relationship modifiers.

        Args:
            measure_tables: Tables referenced by measures
            filter_tables: Tables used in filters
            grouping_tables: Tables used for grouping (columns in SUMMARIZE)

        Returns:
            List of RelationshipHint suggestions
        """
        self.load_relationships()
        hints = []

        # Combine all tables involved in the query
        all_tables = set(measure_tables + filter_tables + grouping_tables)

        # Check for inactive relationships between query tables
        for rel in self._relationships:
            if not rel.is_active:
                # Check if both ends of the relationship are in the query
                if rel.from_table in all_tables and rel.to_table in all_tables:
                    hints.append(RelationshipHint(
                        type='use_relationship',
                        from_table=rel.from_table,
                        from_column=rel.from_column,
                        to_table=rel.to_table,
                        to_column=rel.to_column,
                        dax_modifier=f"USERELATIONSHIP('{rel.from_table}'[{rel.from_column}], '{rel.to_table}'[{rel.to_column}])",
                        reason=f"Inactive relationship between {rel.from_table} and {rel.to_table} may need activation",
                        severity='warning'
                    ))

        # Check for potential bidirectional filter needs
        for rel in self._relationships:
            if not rel.is_active:
                continue

            if rel.cross_filter_direction == 'Single':
                # Check if filtering from "many" side to "one" side
                # In Power BI, relationships typically filter from "one" (to_table) to "many" (from_table)

                # If we're filtering by from_table and need to affect to_table measures
                if rel.from_table in filter_tables and rel.to_table in measure_tables:
                    hints.append(RelationshipHint(
                        type='crossfilter_both',
                        from_table=rel.from_table,
                        from_column=rel.from_column,
                        to_table=rel.to_table,
                        to_column=rel.to_column,
                        dax_modifier=f"CROSSFILTER('{rel.from_table}'[{rel.from_column}], '{rel.to_table}'[{rel.to_column}], BOTH)",
                        reason=f"Filter on {rel.from_table} may need bidirectional propagation to {rel.to_table}",
                        severity='info'
                    ))

        # Check for ambiguous paths (multiple relationships between same tables)
        table_pairs = {}
        for rel in self._relationships:
            pair = (min(rel.from_table, rel.to_table), max(rel.from_table, rel.to_table))
            if pair not in table_pairs:
                table_pairs[pair] = []
            table_pairs[pair].append(rel)

        for pair, rels in table_pairs.items():
            if len(rels) > 1:
                from_t, to_t = pair
                if from_t in all_tables and to_t in all_tables:
                    active_rels = [r for r in rels if r.is_active]
                    inactive_rels = [r for r in rels if not r.is_active]

                    if active_rels and inactive_rels:
                        hints.append(RelationshipHint(
                            type='ambiguous_path',
                            from_table=from_t,
                            from_column='',
                            to_table=to_t,
                            to_column='',
                            dax_modifier='',
                            reason=f"Multiple relationships between {from_t} and {to_t}. "
                                   f"Using active relationship on [{active_rels[0].from_column}]. "
                                   f"Consider USERELATIONSHIP if different path needed.",
                            severity='info'
                        ))

        return hints

    def get_dax_modifiers(
        self,
        measure_tables: List[str],
        filter_tables: List[str],
        grouping_tables: List[str]
    ) -> Tuple[List[str], List[RelationshipHint]]:
        """
        Get DAX modifiers and hints for a query.

        Args:
            measure_tables: Tables referenced by measures
            filter_tables: Tables used in filters
            grouping_tables: Tables used for grouping

        Returns:
            Tuple of (list of DAX modifiers to add, list of hints for user)
        """
        hints = self.analyze_query_tables(measure_tables, filter_tables, grouping_tables)

        # Only return modifiers for high-confidence suggestions
        modifiers = [
            h.dax_modifier
            for h in hints
            if h.dax_modifier and h.type == 'use_relationship'
        ]

        return modifiers, hints

    def get_relationships_for_tables(self, tables: List[str]) -> List[RelationshipInfo]:
        """Get all relationships involving the specified tables."""
        self.load_relationships()

        result = []
        for rel in self._relationships:
            if rel.from_table in tables or rel.to_table in tables:
                result.append(rel)

        return result

    def has_inactive_relationships(self, tables: List[str]) -> bool:
        """Check if any inactive relationships exist between the given tables."""
        self.load_relationships()

        table_set = set(tables)
        for from_t, to_t in self._inactive_pairs:
            if from_t in table_set and to_t in table_set:
                return True
        return False
```

---

## Feature 8: Aggregation Support

### New File: `core/debug/aggregation_matcher.py`

```python
"""
Aggregation Table Detection and Matching

Detects aggregation tables in the model and suggests their use when the query
grain matches the aggregation grain.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AggregationTableInfo:
    """Information about a detected aggregation table."""
    name: str
    grain_columns: List[str]
    source_table: Optional[str]
    detection_method: str  # 'pattern', 'expression', 'structure'
    confidence: float


@dataclass
class AggregationMatch:
    """Result of aggregation table matching for a query."""
    agg_table: str
    grain_columns: List[str]
    match_confidence: float
    query_columns: List[str]
    recommendation: str


class AggregationMatcher:
    """
    Detects aggregation tables and suggests their use based on query grain.

    Detection methods:
    1. Naming patterns (Agg_, _Summary, PreAgg, etc.)
    2. Calculated table expressions (SUMMARIZE, GROUPBY)
    3. Table structure (few columns, no detail rows)
    """

    # Naming patterns for aggregation tables
    AGG_NAME_PATTERNS = [
        re.compile(r'^Agg[_\s]', re.IGNORECASE),
        re.compile(r'[_\s]Agg$', re.IGNORECASE),
        re.compile(r'^Aggregat', re.IGNORECASE),
        re.compile(r'^Summary[_\s]', re.IGNORECASE),
        re.compile(r'[_\s]Summary$', re.IGNORECASE),
        re.compile(r'^Pre[_\s]?Agg', re.IGNORECASE),
        re.compile(r'^Fact[_\s]Agg', re.IGNORECASE),
    ]

    # Patterns in calculated table expressions that indicate aggregation
    AGG_EXPRESSION_PATTERNS = [
        re.compile(r'\bSUMMARIZECOLUMNS\s*\(', re.IGNORECASE),
        re.compile(r'\bSUMMARIZE\s*\(', re.IGNORECASE),
        re.compile(r'\bGROUPBY\s*\(', re.IGNORECASE),
        re.compile(r'\bADDCOLUMNS\s*\(\s*SUMMARIZE', re.IGNORECASE),
    ]

    def __init__(self, query_executor=None, aggregation_detector=None):
        """
        Initialize the matcher.

        Args:
            query_executor: QueryExecutor for DMV queries
            aggregation_detector: Existing AggregationTableDetector instance (optional)
        """
        self.qe = query_executor
        self.detector = aggregation_detector
        self._agg_tables: Dict[str, AggregationTableInfo] = {}
        self._loaded = False

    def detect_aggregation_tables(self) -> Dict[str, AggregationTableInfo]:
        """
        Detect aggregation tables in the model.

        Returns:
            Dict mapping table name to AggregationTableInfo
        """
        if self._loaded:
            return self._agg_tables

        # Try using existing detector first
        if self.detector:
            try:
                agg_tables = self.detector.detect_aggregation_tables()
                for agg in agg_tables:
                    self._agg_tables[agg.name] = AggregationTableInfo(
                        name=agg.name,
                        grain_columns=getattr(agg, 'grain_columns', []),
                        source_table=getattr(agg, 'source_table', None),
                        detection_method='detector',
                        confidence=0.90
                    )
                self._loaded = True
                return self._agg_tables
            except Exception as e:
                logger.debug(f"AggregationTableDetector failed: {e}")

        # Fall back to our own detection
        if self.qe:
            self._detect_by_naming()
            self._detect_by_expression()

        self._loaded = True
        return self._agg_tables

    def _detect_by_naming(self) -> None:
        """Detect aggregation tables by naming patterns."""
        try:
            result = self.qe.execute_info_query("TABLES")
            if not result.get('success'):
                return

            for table in result.get('rows', []):
                name = table.get('Name', table.get('[Name]', ''))

                for pattern in self.AGG_NAME_PATTERNS:
                    if pattern.search(name):
                        self._agg_tables[name] = AggregationTableInfo(
                            name=name,
                            grain_columns=[],
                            source_table=None,
                            detection_method='pattern',
                            confidence=0.70
                        )
                        logger.debug(f"Detected aggregation table by name: {name}")
                        break

        except Exception as e:
            logger.debug(f"Error detecting aggregations by naming: {e}")

    def _detect_by_expression(self) -> None:
        """Detect aggregation tables by calculated table expressions."""
        try:
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

                # Check for aggregation patterns
                for pattern in self.AGG_EXPRESSION_PATTERNS:
                    if pattern.search(source):
                        # Extract grain columns from expression
                        grain_cols = self._extract_grain_columns(source)

                        self._agg_tables[table_name] = AggregationTableInfo(
                            name=table_name,
                            grain_columns=grain_cols,
                            source_table=self._extract_source_table(source),
                            detection_method='expression',
                            confidence=0.85
                        )
                        logger.debug(f"Detected aggregation table by expression: {table_name} (grain: {grain_cols})")
                        break

        except Exception as e:
            logger.debug(f"Error detecting aggregations by expression: {e}")

    def _extract_grain_columns(self, expression: str) -> List[str]:
        """Extract grain columns from aggregation expression."""
        columns = []

        # Match 'Table'[Column] patterns
        col_pattern = re.compile(r"['\"]?([^'\"[\s]+)['\"]?\s*\[\s*([^\]]+)\s*\]")
        matches = col_pattern.findall(expression)

        for table, column in matches:
            # Skip measures (typically in CALCULATE or aggregate functions)
            col_ref = f"'{table}'[{column}]"
            columns.append(col_ref)

        # Return unique columns (first 10)
        return list(dict.fromkeys(columns))[:10]

    def _extract_source_table(self, expression: str) -> Optional[str]:
        """Extract source table name from aggregation expression."""
        # Look for first table reference that's likely the source
        table_pattern = re.compile(r"(?:SUMMARIZE|GROUPBY|ALL)\s*\(\s*['\"]?([^'\"(,\s]+)['\"]?")
        match = table_pattern.search(expression)

        return match.group(1) if match else None

    def find_matching_aggregation(
        self,
        grouping_columns: List[str],
        filter_columns: List[str]
    ) -> Optional[AggregationMatch]:
        """
        Find an aggregation table that matches the query grain.

        Args:
            grouping_columns: Columns used for grouping in the query
            filter_columns: Columns used in filters

        Returns:
            AggregationMatch if a suitable table is found, None otherwise
        """
        self.detect_aggregation_tables()

        if not self._agg_tables:
            return None

        # Normalize column references
        def normalize_col(col: str) -> str:
            """Normalize column reference for comparison."""
            return col.lower().strip("'\"")

        query_cols = set(normalize_col(c) for c in grouping_columns + filter_columns)

        best_match = None
        best_score = 0

        for agg_name, agg_info in self._agg_tables.items():
            if not agg_info.grain_columns:
                continue

            grain_cols = set(normalize_col(c) for c in agg_info.grain_columns)

            # Check if query columns are a subset of aggregation grain
            if query_cols.issubset(grain_cols):
                # Score based on grain specificity (prefer smaller grain)
                score = agg_info.confidence * (1 / (len(grain_cols) + 1))

                if score > best_score:
                    best_score = score
                    best_match = AggregationMatch(
                        agg_table=agg_name,
                        grain_columns=agg_info.grain_columns,
                        match_confidence=agg_info.confidence,
                        query_columns=list(query_cols),
                        recommendation=f"Query grain matches aggregation table '{agg_name}'. "
                                       f"Consider using for better performance."
                    )

        return best_match

    def get_aggregation_info(self) -> Dict[str, Any]:
        """Get summary of detected aggregation tables."""
        self.detect_aggregation_tables()

        return {
            'count': len(self._agg_tables),
            'tables': [
                {
                    'name': info.name,
                    'grain_columns': info.grain_columns[:5],  # Limit for brevity
                    'source': info.source_table,
                    'detection': info.detection_method
                }
                for info in self._agg_tables.values()
            ]
        }
```

---

## Integration Changes

### File: `core/debug/__init__.py`

Add exports for new modules:

```python
# Add at the end of the file
from .semantic_classifier import SemanticFilterClassifier, SemanticClassification
from .anomaly_detector import AnomalyDetector, AnomalyReport, Anomaly, analyze_results
from .relationship_resolver import RelationshipResolver, RelationshipHint, RelationshipInfo
from .aggregation_matcher import AggregationMatcher, AggregationMatch, AggregationTableInfo

__all__ = [
    # Existing exports...

    # New exports
    'SemanticFilterClassifier',
    'SemanticClassification',
    'AnomalyDetector',
    'AnomalyReport',
    'Anomaly',
    'analyze_results',
    'RelationshipResolver',
    'RelationshipHint',
    'RelationshipInfo',
    'AggregationMatcher',
    'AggregationMatch',
    'AggregationTableInfo',
]
```

### File: `core/debug/visual_query_builder.py`

Add initialization of new components in `__init__`:

```python
# After line 192 (after self._all_measures_loaded = False)

        # Advanced analysis components (lazy initialized)
        self._semantic_classifier: Optional['SemanticFilterClassifier'] = None
        self._relationship_resolver: Optional['RelationshipResolver'] = None
        self._aggregation_matcher: Optional['AggregationMatcher'] = None
```

Add initialization methods:

```python
    def _init_semantic_classifier(self) -> Optional['SemanticFilterClassifier']:
        """Lazy initialize semantic classifier."""
        if self._semantic_classifier is None and self._query_executor:
            from .semantic_classifier import SemanticFilterClassifier
            self._semantic_classifier = SemanticFilterClassifier(self._query_executor)
        return self._semantic_classifier

    def _init_relationship_resolver(self) -> Optional['RelationshipResolver']:
        """Lazy initialize relationship resolver."""
        if self._relationship_resolver is None and self._query_executor:
            from .relationship_resolver import RelationshipResolver
            self._relationship_resolver = RelationshipResolver(self._query_executor)
        return self._relationship_resolver

    def _init_aggregation_matcher(self) -> Optional['AggregationMatcher']:
        """Lazy initialize aggregation matcher."""
        if self._aggregation_matcher is None and self._query_executor:
            from .aggregation_matcher import AggregationMatcher
            self._aggregation_matcher = AggregationMatcher(self._query_executor)
        return self._aggregation_matcher
```

### File: `server/handlers/debug_handler.py`

Add anomaly detection integration in `handle_debug_visual()` after query execution (around line 399):

```python
                        # Anomaly detection on results
                        if rows and len(rows) > 1:
                            try:
                                from core.debug.anomaly_detector import analyze_results
                                anomaly_report = analyze_results(rows)
                                if anomaly_report:
                                    response['anomalies'] = anomaly_report
                            except Exception as ae:
                                logger.debug(f"Anomaly detection skipped: {ae}")
```

---

## Testing Strategy

### Unit Tests

1. **test_semantic_classifier.py**
   - Test NAMEOF pattern detection
   - Test SWITCH(SELECTEDVALUE) pattern detection
   - Test composite key detection
   - Test classification caching
   - Test fallback to naming convention

2. **test_anomaly_detector.py**
   - Test empty result detection
   - Test null concentration detection
   - Test IQR outlier detection
   - Test high variance detection
   - Test negative value detection
   - Test statistics computation

3. **test_relationship_resolver.py**
   - Test inactive relationship detection
   - Test USERELATIONSHIP modifier generation
   - Test CROSSFILTER suggestions
   - Test ambiguous path detection
   - Test relationship indexing

4. **test_aggregation_matcher.py**
   - Test naming pattern detection
   - Test expression-based detection
   - Test grain column extraction
   - Test aggregation matching
   - Test match scoring

### Integration Tests

1. **test_debug_visual_integration.py**
   - Test PBIP freshness warning with stale files
   - Test anomaly detection in query results
   - Test auto-retry on composite key error

2. **test_profile_page_parallel.py**
   - Test parallel vs sequential correctness
   - Test thread safety
   - Test max_workers limit
   - Test execution mode reporting

### Manual Verification Scenarios

1. Open PBIP, wait 6 minutes, run `09_Debug_Visual` - verify freshness warning
2. Create field parameter slicer, debug visual - verify auto-exclusion on error
3. Profile page with 10+ visuals - verify parallel execution and speedup
4. Query across inactive relationship - verify hint is generated
5. Query at aggregation grain - verify aggregation recommendation

---

## Backward Compatibility

- All new parameters have defaults matching current behavior
- `parallel=True` by default but falls back to sequential if needed
- Semantic classifier falls back to pattern matching when DMV unavailable
- New response fields are additive, not breaking existing parsers
- Compact mode preserved as default with new fields preserved

---

## Implementation Order

```
Phase 1 (Quick wins):
├── Feature 1: PBIP Freshness Warning
└── Feature 2: Truncation Fix

Phase 2 (New modules):
├── Feature 4: semantic_classifier.py
└── Feature 5: anomaly_detector.py

Phase 3 (Integration):
├── Feature 3: Auto-Retry Logic (uses semantic classifier)
└── Feature 6: Parallel Profiling

Phase 4 (Advanced):
├── Feature 7: relationship_resolver.py
└── Feature 8: aggregation_matcher.py

Phase 5 (Final integration):
├── Update __init__.py exports
├── Integration in debug_handler.py
└── Integration in visual_query_builder.py
```
