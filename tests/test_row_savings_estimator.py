"""
Unit tests for Row Savings Estimator Module

Tests the estimation of row savings from aggregation table usage.
"""

import pytest
from core.aggregation.row_savings_estimator import (
    RowSavingsEstimator,
    RowSavingsResult,
    TableRowEstimate,
    VisualSavings,
    PageSavings,
    estimate_grain_cardinality,
)
from core.aggregation.aggregation_detector import AggregationTable, AggregatedColumn
from core.aggregation.aggregation_analyzer import (
    ReportAggregationSummary,
    PageAggregationSummary,
    VisualAggregationAnalysis,
)
from core.aggregation.filter_context_analyzer import FilterContext


class TestRowSavingsEstimator:
    """Tests for RowSavingsEstimator class."""

    @pytest.fixture
    def sample_agg_tables(self):
        """Create sample aggregation tables."""
        return [
            AggregationTable(
                name="Agg_Monthly",
                level=2,
                level_name="Mid-Level",
                is_hidden=True,
                source_expression=None,
                grain_columns=["Calendar[Month]", "Product[Category]"],
                aggregated_columns=[
                    AggregatedColumn(name="TotalSales", aggregation_function="SUM")
                ],
                related_dimensions=[],
            ),
            AggregationTable(
                name="Agg_Yearly",
                level=3,
                level_name="High-Level",
                is_hidden=True,
                source_expression=None,
                grain_columns=["Calendar[Year]"],
                aggregated_columns=[
                    AggregatedColumn(name="TotalSales", aggregation_function="SUM")
                ],
                related_dimensions=[],
            ),
        ]

    def test_estimator_initialization_with_rows(self, sample_agg_tables):
        """Test initialization with provided row count."""
        estimator = RowSavingsEstimator(
            agg_tables=sample_agg_tables,
            base_table_name="Sales",
            base_table_rows=10_000_000,
        )

        assert estimator.base_table_rows == 10_000_000
        assert estimator.row_estimation_source == "provided"
        assert "Sales" in estimator.table_estimates

    def test_estimator_initialization_default_rows(self, sample_agg_tables):
        """Test initialization without provided row count."""
        estimator = RowSavingsEstimator(
            agg_tables=sample_agg_tables,
            base_table_name="Sales",
        )

        assert estimator.base_table_rows == 10_000_000  # Default
        assert estimator.row_estimation_source == "estimated"

    def test_table_row_estimates(self, sample_agg_tables):
        """Test that aggregation table rows are estimated."""
        estimator = RowSavingsEstimator(
            agg_tables=sample_agg_tables,
            base_table_rows=10_000_000,
        )

        # Aggregation tables should have fewer rows
        agg_monthly_est = estimator.table_estimates.get("Agg_Monthly")
        agg_yearly_est = estimator.table_estimates.get("Agg_Yearly")

        assert agg_monthly_est is not None
        assert agg_yearly_est is not None
        assert agg_monthly_est.estimated_rows < 10_000_000
        assert agg_yearly_est.estimated_rows < agg_monthly_est.estimated_rows

    def test_get_table_rows(self, sample_agg_tables):
        """Test getting rows for specific table."""
        estimator = RowSavingsEstimator(
            agg_tables=sample_agg_tables,
            base_table_name="Sales",
            base_table_rows=10_000_000,
        )

        assert estimator.get_table_rows("Sales") == 10_000_000
        assert estimator.get_table_rows("Agg_Monthly") < 10_000_000
        assert estimator.get_table_rows("Unknown_Table") == 10_000_000  # Default to base

    def test_format_row_count(self, sample_agg_tables):
        """Test row count formatting."""
        estimator = RowSavingsEstimator(
            agg_tables=sample_agg_tables,
            base_table_rows=10_000_000,
        )

        assert estimator.format_row_count(1_000_000_000) == "1.0B"
        assert estimator.format_row_count(10_000_000) == "10.0M"
        assert estimator.format_row_count(150_000) == "150.0K"
        assert estimator.format_row_count(500) == "500"

    def test_estimate_savings(self, sample_agg_tables):
        """Test complete savings estimation."""
        estimator = RowSavingsEstimator(
            agg_tables=sample_agg_tables,
            base_table_name="Sales",
            base_table_rows=10_000_000,
        )

        # Create a sample filter context for visual analysis
        filter_context = FilterContext(
            visual_id="v1",
            page_id="p1",
            all_columns=[],
            filter_sources=[],
        )

        # Create sample report summary
        visual_analysis = VisualAggregationAnalysis(
            visual_id="visual_1",
            visual_type="barChart",
            visual_title="Sales Chart",
            page_id="page1",
            page_name="Overview",
            measures_used=["Total Sales"],
            agg_aware_measures_used=["Total Sales"],
            columns_in_context=[],
            filter_context=filter_context,
            determined_agg_level=2,
            determined_agg_level_name="Mid-Level",
            determined_agg_table="Agg_Monthly",
            reasoning="Month filter present",
        )

        page_summary = PageAggregationSummary(
            page_id="page1",
            page_name="Overview",
            total_visuals=1,
            visuals_analyzed=1,
            agg_table_breakdown={"Agg_Monthly": 1},
            agg_level_breakdown={2: 1},
            agg_table_percentages={"Agg_Monthly": 100.0},
            visuals=[visual_analysis],
            slicers=[],
            optimization_opportunities=[],
        )

        report_summary = ReportAggregationSummary(
            total_pages=1,
            total_visuals=1,
            visuals_analyzed=1,
            agg_table_breakdown={"Agg_Monthly": 1},
            agg_level_breakdown={2: 1},
            agg_table_percentages={"Agg_Monthly": 100.0},
            optimization_score=50.0,
            pages=[page_summary],
            recommendations=[],
        )

        result = estimator.estimate_savings(report_summary)

        assert isinstance(result, RowSavingsResult)
        assert result.base_table_rows == 10_000_000
        assert result.total_rows_saved > 0
        assert result.overall_savings_percentage > 0


class TestGrainCardinalityEstimation:
    """Tests for grain cardinality estimation function."""

    def test_estimate_grain_cardinality_year(self):
        """Test estimation for year grain."""
        rows = estimate_grain_cardinality(
            grain_columns=["Calendar[Year]"],
            base_rows=10_000_000,
        )

        assert rows < 100  # Should be very few years

    def test_estimate_grain_cardinality_month(self):
        """Test estimation for month grain."""
        rows = estimate_grain_cardinality(
            grain_columns=["Calendar[Month]"],
            base_rows=10_000_000,
        )

        assert rows < 1000  # Should be ~60 months

    def test_estimate_grain_cardinality_multiple_columns(self):
        """Test estimation for multiple grain columns."""
        rows = estimate_grain_cardinality(
            grain_columns=["Calendar[Month]", "Product[Category]"],
            base_rows=10_000_000,
        )

        # Should be months * categories
        assert rows < 5000

    def test_estimate_grain_cardinality_caps_at_base(self):
        """Test that cardinality is capped at base rows."""
        rows = estimate_grain_cardinality(
            grain_columns=["Customer[ID]", "Product[SKU]", "Store[ID]"],
            base_rows=1000,
        )

        assert rows <= 1000

    def test_estimate_grain_cardinality_with_known(self):
        """Test estimation with known cardinalities."""
        rows = estimate_grain_cardinality(
            grain_columns=["Calendar[Year]", "Region[Name]"],
            base_rows=10_000_000,
            dimension_cardinalities={
                "Calendar[Year]": 3,
                "Region[Name]": 10,
            },
        )

        assert rows == 30  # 3 * 10


class TestDataClasses:
    """Tests for data class definitions."""

    def test_table_row_estimate(self):
        """Test TableRowEstimate creation."""
        estimate = TableRowEstimate(
            table_name="Sales",
            estimated_rows=10_000_000,
            confidence="actual",
            estimation_method="User provided",
        )

        assert estimate.table_name == "Sales"
        assert estimate.estimated_rows == 10_000_000

    def test_visual_savings(self):
        """Test VisualSavings creation."""
        savings = VisualSavings(
            visual_id="v1",
            visual_title="Chart",
            page_name="Overview",
            agg_level=2,
            table_used="Agg_Monthly",
            rows_if_base=10_000_000,
            rows_actual=200_000,
            rows_saved=9_800_000,
            savings_percentage=98.0,
        )

        assert savings.rows_saved == 9_800_000
        assert savings.savings_percentage == 98.0

    def test_page_savings(self):
        """Test PageSavings creation."""
        savings = PageSavings(
            page_id="p1",
            page_name="Overview",
            total_visuals=5,
            total_rows_if_base=50_000_000,
            total_rows_actual=1_000_000,
            total_rows_saved=49_000_000,
            savings_percentage=98.0,
            visual_savings=[],
        )

        assert savings.total_rows_saved == 49_000_000
