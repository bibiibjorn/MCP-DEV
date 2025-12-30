"""
Unit tests for Aggregation Report Builder Module

Tests the generation of HTML, JSON, and text reports for aggregation analysis.
"""

import pytest
import json
from core.aggregation.aggregation_report_builder import AggregationReportBuilder
from core.aggregation.aggregation_analyzer import (
    AggregationAnalysisResult,
    ReportAggregationSummary,
    PageAggregationSummary,
    VisualAggregationAnalysis,
)
from core.aggregation.aggregation_detector import (
    AggregationTable,
    AggLevelMeasure,
    AggAwareMeasure,
    AggregatedColumn,
)
from core.aggregation.row_savings_estimator import RowSavingsResult, TableRowEstimate, PageSavings
from core.aggregation.filter_context_analyzer import FilterContext


class TestAggregationReportBuilder:
    """Tests for AggregationReportBuilder class."""

    @pytest.fixture
    def sample_analysis_result(self):
        """Create a sample analysis result for testing."""
        filter_context = FilterContext(
            visual_id="v1",
            page_id="p1",
            all_columns=[],
            filter_sources=[],
        )

        visual = VisualAggregationAnalysis(
            visual_id="visual_1",
            visual_type="barChart",
            visual_title="Sales by Category",
            page_id="page1",
            page_name="Overview",
            measures_used=["Total Sales"],
            agg_aware_measures_used=["Total Sales"],
            columns_in_context=[],
            filter_context=filter_context,
            determined_agg_level=2,
            determined_agg_level_name="Mid-Level Aggregation",
            determined_agg_table="Agg_Monthly",
            reasoning="Month filter present",
        )

        page = PageAggregationSummary(
            page_id="page1",
            page_name="Overview",
            total_visuals=5,
            visuals_analyzed=3,
            agg_table_breakdown={"Agg_Monthly": 2, "Base Table": 1},
            agg_level_breakdown={1: 1, 2: 2},
            agg_table_percentages={"Agg_Monthly": 66.7, "Base Table": 33.3},
            visuals=[visual],
            slicers=[],
            optimization_opportunities=["Consider adding Product dimension to mid-level aggregation"],
        )

        report_summary = ReportAggregationSummary(
            total_pages=2,
            total_visuals=10,
            visuals_analyzed=6,
            agg_table_breakdown={"Agg_Monthly": 4, "Base Table": 2},
            agg_level_breakdown={1: 2, 2: 4},
            agg_table_percentages={"Agg_Monthly": 66.7, "Base Table": 33.3},
            optimization_score=66.7,
            pages=[page],
            recommendations=["Good aggregation usage!", "Consider reviewing page 'Details'"],
        )

        return AggregationAnalysisResult(
            model_name="Test Model",
            model_path="/path/to/model",
            aggregation_tables=[
                AggregationTable(
                    name="Agg_Monthly",
                    level=2,
                    level_name="Mid-Level",
                    is_hidden=True,
                    source_expression="SUMMARIZECOLUMNS(...)",
                    grain_columns=["Calendar[Month]", "Product[Category]"],
                    aggregated_columns=[
                        AggregatedColumn(name="TotalSales", aggregation_function="SUM")
                    ],
                    related_dimensions=["Calendar", "Product"],
                    detection_confidence=0.9,
                    detection_reasons=["Name pattern", "SUMMARIZECOLUMNS"],
                )
            ],
            base_fact_tables=["Sales"],
            agg_level_measures=[
                AggLevelMeasure(
                    table="Measures",
                    name="_AggregationLevel",
                    expression="SWITCH(...)",
                    detail_trigger_columns=["Sales[Key]"],
                    mid_level_trigger_columns=["Calendar[Month]"],
                    high_level_trigger_columns=["Calendar[Year]"],
                    levels={1: "Base", 2: "Mid", 3: "High"},
                    level_var_mapping={},
                )
            ],
            agg_aware_measures=[
                AggAwareMeasure(
                    table="Sales",
                    name="Total Sales",
                    expression="SWITCH([_AggregationLevel]...)",
                    uses_agg_level_measure="_AggregationLevel",
                    table_switches={1: "Sales", 2: "Agg_Monthly"},
                    column_switches={},
                    dependencies=["_AggregationLevel"],
                )
            ],
            report_summary=report_summary,
            estimated_base_rows=10_000_000,
            estimated_row_savings=8_000_000,
            row_savings_percentage=80.0,
            analysis_timestamp="2025-01-15T10:30:00",
            has_report=True,
        )

    def test_builder_initialization(self, sample_analysis_result):
        """Test builder initialization."""
        builder = AggregationReportBuilder(sample_analysis_result)

        assert builder.result == sample_analysis_result
        assert builder.row_savings is None

    def test_set_row_savings(self, sample_analysis_result):
        """Test setting row savings data."""
        builder = AggregationReportBuilder(sample_analysis_result)

        row_savings = RowSavingsResult(
            base_table_name="Sales",
            base_table_rows=10_000_000,
            row_estimation_source="provided",
            table_estimates=[],
            total_visual_queries=6,
            total_rows_if_all_base=60_000_000,
            total_rows_with_aggregation=12_000_000,
            total_rows_saved=48_000_000,
            overall_savings_percentage=80.0,
            page_savings=[],
            best_case_savings=59_000_000,
            worst_case_savings=48_000_000,
            avg_rows_per_query_base=10_000_000,
            avg_rows_per_query_actual=2_000_000,
        )

        builder.set_row_savings(row_savings)

        assert builder.row_savings is not None
        assert builder.row_savings.total_rows_saved == 48_000_000

    def test_build_summary_text(self, sample_analysis_result):
        """Test building summary text report."""
        builder = AggregationReportBuilder(sample_analysis_result)
        summary = builder.build_summary_text()

        assert "AGGREGATION ANALYSIS SUMMARY" in summary
        assert "Test Model" in summary
        assert "Agg_Monthly" in summary
        assert "Total Sales" in summary
        assert "OPTIMIZATION SCORE" in summary

    def test_build_detailed_text(self, sample_analysis_result):
        """Test building detailed text report."""
        builder = AggregationReportBuilder(sample_analysis_result)
        detailed = builder.build_detailed_text()

        assert "AGGREGATION ANALYSIS SUMMARY" in detailed
        assert "DETAILED VISUAL ANALYSIS" in detailed
        assert "PAGE: Overview" in detailed
        assert "visual_1" in detailed

    def test_build_json_export(self, sample_analysis_result):
        """Test building JSON export."""
        builder = AggregationReportBuilder(sample_analysis_result)
        json_data = builder.build_json_export()

        assert isinstance(json_data, dict)
        assert json_data["model_name"] == "Test Model"
        assert "aggregation_tables" in json_data
        assert len(json_data["aggregation_tables"]) == 1
        assert json_data["aggregation_tables"][0]["name"] == "Agg_Monthly"
        assert "report_summary" in json_data

    def test_build_json_export_is_serializable(self, sample_analysis_result):
        """Test that JSON export is serializable."""
        builder = AggregationReportBuilder(sample_analysis_result)
        json_data = builder.build_json_export()

        # Should not raise exception
        serialized = json.dumps(json_data)
        assert isinstance(serialized, str)

        # Should be deserializable
        deserialized = json.loads(serialized)
        assert deserialized["model_name"] == "Test Model"

    def test_build_html_report(self, sample_analysis_result):
        """Test building HTML report."""
        builder = AggregationReportBuilder(sample_analysis_result)
        html = builder.build_html_report()

        assert "<!DOCTYPE html>" in html
        assert "Aggregation Analysis Report" in html
        assert "Test Model" in html
        assert "Agg_Monthly" in html
        assert "Optimization Score" in html
        assert "</html>" in html

    def test_build_html_report_with_row_savings(self, sample_analysis_result):
        """Test HTML report includes row savings section."""
        builder = AggregationReportBuilder(sample_analysis_result)

        row_savings = RowSavingsResult(
            base_table_name="Sales",
            base_table_rows=10_000_000,
            row_estimation_source="provided",
            table_estimates=[],
            total_visual_queries=6,
            total_rows_if_all_base=60_000_000,
            total_rows_with_aggregation=12_000_000,
            total_rows_saved=48_000_000,
            overall_savings_percentage=80.0,
            page_savings=[],
            best_case_savings=59_000_000,
            worst_case_savings=48_000_000,
            avg_rows_per_query_base=10_000_000,
            avg_rows_per_query_actual=2_000_000,
        )

        builder.set_row_savings(row_savings)
        html = builder.build_html_report()

        assert "Row Savings" in html or "Rows Saved" in html
        assert "80" in html  # Percentage

    def test_build_html_report_with_recommendations(self, sample_analysis_result):
        """Test HTML report includes recommendations."""
        builder = AggregationReportBuilder(sample_analysis_result)
        html = builder.build_html_report()

        assert "Recommendations" in html
        assert "Good aggregation usage" in html


class TestReportBuilderEdgeCases:
    """Tests for edge cases in report builder."""

    def test_report_without_report_summary(self):
        """Test report building when no report summary available."""
        result = AggregationAnalysisResult(
            model_name="Test Model",
            model_path="/path/to/model",
            aggregation_tables=[],
            base_fact_tables=[],
            agg_level_measures=[],
            agg_aware_measures=[],
            report_summary=None,
            estimated_base_rows=None,
            estimated_row_savings=None,
            row_savings_percentage=None,
            analysis_timestamp="2025-01-15T10:30:00",
            has_report=False,
        )

        builder = AggregationReportBuilder(result)

        # Should not raise exceptions
        summary = builder.build_summary_text()
        assert "Test Model" in summary

        json_data = builder.build_json_export()
        assert json_data["model_name"] == "Test Model"
        assert "report_summary" not in json_data

        html = builder.build_html_report()
        assert "Test Model" in html

    def test_report_with_empty_aggregation_tables(self):
        """Test report building with no aggregation tables detected."""
        result = AggregationAnalysisResult(
            model_name="Test Model",
            model_path="/path/to/model",
            aggregation_tables=[],
            base_fact_tables=["Sales"],
            agg_level_measures=[],
            agg_aware_measures=[],
            report_summary=None,
            estimated_base_rows=None,
            estimated_row_savings=None,
            row_savings_percentage=None,
            analysis_timestamp="2025-01-15T10:30:00",
            has_report=False,
        )

        builder = AggregationReportBuilder(result)

        summary = builder.build_summary_text()
        assert "Aggregation Tables Found: 0" in summary

    def test_report_with_errors_and_warnings(self):
        """Test report includes errors and warnings."""
        result = AggregationAnalysisResult(
            model_name="Test Model",
            model_path="/path/to/model",
            aggregation_tables=[],
            base_fact_tables=[],
            agg_level_measures=[],
            agg_aware_measures=[],
            report_summary=None,
            estimated_base_rows=None,
            estimated_row_savings=None,
            row_savings_percentage=None,
            analysis_timestamp="2025-01-15T10:30:00",
            has_report=False,
            errors=["Error loading report"],
            warnings=["No aggregation tables detected"],
        )

        builder = AggregationReportBuilder(result)
        summary = builder.build_summary_text()

        assert "ERRORS" in summary
        assert "Error loading report" in summary
        assert "WARNINGS" in summary
        assert "No aggregation tables detected" in summary
