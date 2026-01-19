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
    NULL_PRESENCE_PCT = 0.1       # Info if >10% nulls (presence check)
    IQR_MULTIPLIER = 1.5          # Standard IQR outlier detection
    MIN_ROWS_FOR_STATS = 5        # Minimum rows for statistical analysis
    HIGH_VARIANCE_CV = 2.0        # Coefficient of variation threshold

    # Columns that should typically be non-negative
    NON_NEGATIVE_KEYWORDS = [
        'sales', 'revenue', 'amount', 'count', 'quantity', 'total',
        'price', 'cost', 'profit', 'units', 'volume',
        # Financial keywords
        'nav', 'asset', 'balance', 'aum', 'market value', 'net asset'
    ]

    # Columns that represent percentages/rates (should typically be bounded)
    PERCENTAGE_KEYWORDS = [
        '%', 'pct', 'percent', 'return', 'rate', 'yield', 'growth',
        'mwr', 'twr', 'irr', 'margin', 'ratio'
    ]

    # Reasonable bounds for percentage values (in decimal form, e.g., 1.0 = 100%)
    PERCENTAGE_LOWER_BOUND = -2.0   # -200% (extreme but possible for some metrics)
    PERCENTAGE_UPPER_BOUND = 5.0    # 500% (very extreme return)

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
        elif null_pct > self.NULL_PRESENCE_PCT:
            # Info-level alert for notable null presence (>10%)
            return Anomaly(
                type='null_presence',
                severity='info',
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

        # Check for extreme percentage values
        is_percentage = any(kw in col_lower for kw in self.PERCENTAGE_KEYWORDS)

        if is_percentage:
            extreme_low = [v for v in numeric_values if v < self.PERCENTAGE_LOWER_BOUND]
            extreme_high = [v for v in numeric_values if v > self.PERCENTAGE_UPPER_BOUND]

            if extreme_low or extreme_high:
                anomalies.append(Anomaly(
                    type='extreme_percentage',
                    severity='warning',
                    column=col_name,
                    description=f'Extreme percentage values detected: {len(extreme_low)} below {self.PERCENTAGE_LOWER_BOUND*100:.0f}%, {len(extreme_high)} above {self.PERCENTAGE_UPPER_BOUND*100:.0f}%',
                    details={
                        'extreme_low_count': len(extreme_low),
                        'extreme_high_count': len(extreme_high),
                        'examples_low': sorted(extreme_low)[:5] if extreme_low else [],
                        'examples_high': sorted(extreme_high, reverse=True)[:5] if extreme_high else [],
                        'bounds': {'lower': self.PERCENTAGE_LOWER_BOUND, 'upper': self.PERCENTAGE_UPPER_BOUND}
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
