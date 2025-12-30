"""
Row Savings Estimator Module

Estimates the number of rows saved by using aggregation tables instead of
querying the base fact table directly.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

from .aggregation_detector import AggregationTable
from .aggregation_analyzer import (
    ReportAggregationSummary,
    PageAggregationSummary,
    VisualAggregationAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass
class TableRowEstimate:
    """Estimated row count for a table."""
    table_name: str
    estimated_rows: int
    confidence: str  # "actual", "estimated", "default"
    estimation_method: str


@dataclass
class VisualSavings:
    """Row savings for a single visual."""
    visual_id: str
    visual_title: Optional[str]
    page_name: str
    agg_level: int
    table_used: str
    rows_if_base: int
    rows_actual: int
    rows_saved: int
    savings_percentage: float


@dataclass
class PageSavings:
    """Row savings summary for a page."""
    page_id: str
    page_name: str
    total_visuals: int
    total_rows_if_base: int
    total_rows_actual: int
    total_rows_saved: int
    savings_percentage: float
    visual_savings: List[VisualSavings]


@dataclass
class RowSavingsResult:
    """Complete row savings analysis result."""
    base_table_name: str
    base_table_rows: int
    row_estimation_source: str  # "provided", "metadata", "estimated"

    # Per-table estimates
    table_estimates: List[TableRowEstimate]

    # Aggregation savings
    total_visual_queries: int
    total_rows_if_all_base: int
    total_rows_with_aggregation: int
    total_rows_saved: int
    overall_savings_percentage: float

    # Per-page breakdown
    page_savings: List[PageSavings]

    # Summary statistics
    best_case_savings: int  # If all queries used highest agg
    worst_case_savings: int  # Current state
    avg_rows_per_query_base: int
    avg_rows_per_query_actual: int


class RowSavingsEstimator:
    """Estimates row savings from aggregation table usage."""

    # Default compression ratios for different aggregation levels
    # Based on typical Power BI model patterns
    DEFAULT_COMPRESSION_RATIOS = {
        1: 1.0,      # Base table - no compression
        2: 0.02,     # Mid-level (e.g., monthly) - ~2% of base
        3: 0.001,    # High-level (e.g., quarterly/yearly) - ~0.1% of base
        4: 0.0001,   # Very high aggregation
    }

    def __init__(
        self,
        agg_tables: List[AggregationTable],
        base_table_name: Optional[str] = None,
        base_table_rows: Optional[int] = None,
    ):
        """
        Initialize the estimator.

        Args:
            agg_tables: List of detected aggregation tables
            base_table_name: Name of the base fact table
            base_table_rows: Known row count of base table (if available)
        """
        self.agg_tables = agg_tables
        self.base_table_name = base_table_name or "Base Table"
        self.base_table_rows = base_table_rows
        self.row_estimation_source = "estimated"

        # Build table row estimates
        self.table_estimates: Dict[str, TableRowEstimate] = {}
        self._build_table_estimates()

    def _build_table_estimates(self) -> None:
        """Build row estimates for all tables."""
        # Base table
        if self.base_table_rows:
            self.row_estimation_source = "provided"
            self.table_estimates[self.base_table_name] = TableRowEstimate(
                table_name=self.base_table_name,
                estimated_rows=self.base_table_rows,
                confidence="actual" if self.base_table_rows else "default",
                estimation_method="User provided" if self.base_table_rows else "Default estimate",
            )
        else:
            # Default base table estimate
            self.base_table_rows = 10_000_000  # Default 10M rows
            self.table_estimates[self.base_table_name] = TableRowEstimate(
                table_name=self.base_table_name,
                estimated_rows=self.base_table_rows,
                confidence="default",
                estimation_method="Default estimate (10M rows)",
            )

        # Aggregation tables
        for agg_table in self.agg_tables:
            ratio = self.DEFAULT_COMPRESSION_RATIOS.get(agg_table.level, 0.01)

            # Refine estimate based on grain columns
            if agg_table.grain_columns:
                # More grain columns = more rows
                grain_factor = len(agg_table.grain_columns)
                ratio = ratio * (1 + (grain_factor - 1) * 0.5)

            estimated_rows = int(self.base_table_rows * ratio)

            # Use actual row count if available
            if agg_table.estimated_row_count:
                estimated_rows = agg_table.estimated_row_count
                confidence = "actual"
                method = "From model metadata"
            else:
                confidence = "estimated"
                method = f"Estimated from level {agg_table.level} ratio ({ratio:.4f})"

            self.table_estimates[agg_table.name] = TableRowEstimate(
                table_name=agg_table.name,
                estimated_rows=estimated_rows,
                confidence=confidence,
                estimation_method=method,
            )

    def estimate_savings(
        self,
        report_summary: ReportAggregationSummary
    ) -> RowSavingsResult:
        """
        Estimate row savings for the entire report.

        Args:
            report_summary: Analyzed report summary

        Returns:
            Complete RowSavingsResult
        """
        page_savings_list = []
        total_rows_base = 0
        total_rows_actual = 0

        for page in report_summary.pages:
            page_savings = self._estimate_page_savings(page)
            page_savings_list.append(page_savings)
            total_rows_base += page_savings.total_rows_if_base
            total_rows_actual += page_savings.total_rows_actual

        total_saved = total_rows_base - total_rows_actual
        savings_percentage = (total_saved / total_rows_base * 100) if total_rows_base > 0 else 0

        # Calculate best case (if all used highest aggregation)
        highest_agg_rows = self._get_highest_agg_rows()
        best_case_rows = report_summary.visuals_analyzed * highest_agg_rows
        best_case_savings = (report_summary.visuals_analyzed * self.base_table_rows) - best_case_rows

        return RowSavingsResult(
            base_table_name=self.base_table_name,
            base_table_rows=self.base_table_rows,
            row_estimation_source=self.row_estimation_source,
            table_estimates=list(self.table_estimates.values()),
            total_visual_queries=report_summary.visuals_analyzed,
            total_rows_if_all_base=total_rows_base,
            total_rows_with_aggregation=total_rows_actual,
            total_rows_saved=total_saved,
            overall_savings_percentage=savings_percentage,
            page_savings=page_savings_list,
            best_case_savings=best_case_savings,
            worst_case_savings=total_saved,
            avg_rows_per_query_base=self.base_table_rows,
            avg_rows_per_query_actual=int(total_rows_actual / report_summary.visuals_analyzed)
                if report_summary.visuals_analyzed > 0 else 0,
        )

    def _estimate_page_savings(self, page: PageAggregationSummary) -> PageSavings:
        """Estimate savings for a single page."""
        visual_savings_list = []
        total_base = 0
        total_actual = 0

        for visual in page.visuals:
            vs = self._estimate_visual_savings(visual, page.page_name)
            visual_savings_list.append(vs)
            total_base += vs.rows_if_base
            total_actual += vs.rows_actual

        total_saved = total_base - total_actual
        savings_pct = (total_saved / total_base * 100) if total_base > 0 else 0

        return PageSavings(
            page_id=page.page_id,
            page_name=page.page_name,
            total_visuals=page.visuals_analyzed,
            total_rows_if_base=total_base,
            total_rows_actual=total_actual,
            total_rows_saved=total_saved,
            savings_percentage=savings_pct,
            visual_savings=visual_savings_list,
        )

    def _estimate_visual_savings(
        self,
        visual: VisualAggregationAnalysis,
        page_name: str
    ) -> VisualSavings:
        """Estimate savings for a single visual."""
        rows_base = self.base_table_rows

        # Get rows for the table this visual uses
        if visual.determined_agg_table:
            table_estimate = self.table_estimates.get(visual.determined_agg_table)
            rows_actual = table_estimate.estimated_rows if table_estimate else rows_base
        else:
            rows_actual = rows_base

        rows_saved = rows_base - rows_actual
        savings_pct = (rows_saved / rows_base * 100) if rows_base > 0 else 0

        return VisualSavings(
            visual_id=visual.visual_id,
            visual_title=visual.visual_title,
            page_name=page_name,
            agg_level=visual.determined_agg_level,
            table_used=visual.determined_agg_table or self.base_table_name,
            rows_if_base=rows_base,
            rows_actual=rows_actual,
            rows_saved=rows_saved,
            savings_percentage=savings_pct,
        )

    def _get_highest_agg_rows(self) -> int:
        """Get row count for the highest aggregation table."""
        if not self.agg_tables:
            return self.base_table_rows

        # Find highest level aggregation
        highest_level = max(t.level for t in self.agg_tables)
        for table in self.agg_tables:
            if table.level == highest_level:
                estimate = self.table_estimates.get(table.name)
                return estimate.estimated_rows if estimate else self.base_table_rows

        return self.base_table_rows

    def get_table_rows(self, table_name: str) -> int:
        """Get estimated rows for a specific table."""
        estimate = self.table_estimates.get(table_name)
        return estimate.estimated_rows if estimate else self.base_table_rows

    def format_row_count(self, rows: int) -> str:
        """Format row count for display."""
        if rows >= 1_000_000_000:
            return f"{rows / 1_000_000_000:.1f}B"
        elif rows >= 1_000_000:
            return f"{rows / 1_000_000:.1f}M"
        elif rows >= 1_000:
            return f"{rows / 1_000:.1f}K"
        else:
            return str(rows)


def estimate_grain_cardinality(
    grain_columns: List[str],
    base_rows: int,
    dimension_cardinalities: Optional[Dict[str, int]] = None
) -> int:
    """
    Estimate the cardinality (row count) of an aggregation based on grain columns.

    Args:
        grain_columns: List of grain column references (Table[Column])
        base_rows: Row count of the base table
        dimension_cardinalities: Optional known cardinalities for dimensions

    Returns:
        Estimated row count for the aggregation
    """
    if not grain_columns:
        return base_rows

    # Default cardinality estimates by column type
    DEFAULT_CARDINALITIES = {
        "year": 5,
        "quarter": 20,  # 5 years * 4 quarters
        "month": 60,    # 5 years * 12 months
        "week": 260,    # 5 years * 52 weeks
        "day": 1825,    # 5 years * 365 days
        "category": 20,
        "subcategory": 100,
        "product": 1000,
        "customer": 10000,
        "store": 100,
        "region": 20,
        "country": 50,
        "channel": 5,
    }

    estimated_rows = 1

    for col in grain_columns:
        # Extract column name from reference
        col_name = col.split("[")[-1].rstrip("]").lower() if "[" in col else col.lower()

        # Check if we have known cardinality
        if dimension_cardinalities and col in dimension_cardinalities:
            cardinality = dimension_cardinalities[col]
        else:
            # Estimate based on column name patterns
            cardinality = 100  # Default
            for pattern, card in DEFAULT_CARDINALITIES.items():
                if pattern in col_name:
                    cardinality = card
                    break

        estimated_rows *= cardinality

    # Cap at base table rows
    return min(estimated_rows, base_rows)
