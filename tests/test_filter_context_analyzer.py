"""
Unit tests for Filter Context Analyzer Module

Tests the analysis of filter context for Power BI visuals to determine
aggregation level based on columns in context.
"""

import pytest
from core.aggregation.filter_context_analyzer import (
    FilterContextAnalyzer,
    FilterContext,
    ColumnContext,
    FilterSourceType,
    SlicerInfo,
    extract_slicers_from_page,
    extract_page_filters,
)
from core.aggregation.aggregation_detector import AggLevelMeasure, AggregationTable


class TestFilterContextAnalyzer:
    """Tests for FilterContextAnalyzer class."""

    @pytest.fixture
    def sample_agg_level_measure(self):
        """Create a sample aggregation level measure for testing."""
        return AggLevelMeasure(
            table="Measures",
            name="_AggLevel",
            expression="",
            detail_trigger_columns=[
                "Sales[Key]",
                "Product[ProductKey]",
                "Customer[CustomerKey]",
            ],
            mid_level_trigger_columns=[
                "Calendar[Month]",
                "Product[Category]",
            ],
            high_level_trigger_columns=["Calendar[Year]"],
            levels={1: "Base", 2: "Mid", 3: "High"},
            level_var_mapping={},
        )

    @pytest.fixture
    def sample_agg_tables(self):
        """Create sample aggregation tables for testing."""
        return [
            AggregationTable(
                name="Agg_Monthly",
                level=2,
                level_name="Mid-Level",
                is_hidden=True,
                source_expression=None,
                grain_columns=["Calendar[Month]"],
                aggregated_columns=[],
                related_dimensions=[],
            ),
            AggregationTable(
                name="Agg_Yearly",
                level=3,
                level_name="High-Level",
                is_hidden=True,
                source_expression=None,
                grain_columns=["Calendar[Year]"],
                aggregated_columns=[],
                related_dimensions=[],
            ),
        ]

    def test_analyzer_initialization(self, sample_agg_level_measure, sample_agg_tables):
        """Test analyzer initialization with rules."""
        analyzer = FilterContextAnalyzer(
            agg_level_measure=sample_agg_level_measure,
            agg_tables=sample_agg_tables,
        )

        assert analyzer.agg_level_measure is not None
        assert len(analyzer.detail_triggers) == 3
        assert len(analyzer.mid_level_triggers) == 2

    def test_determine_level_detail_trigger(self, sample_agg_level_measure, sample_agg_tables):
        """Test level determination when detail trigger column is present."""
        analyzer = FilterContextAnalyzer(
            agg_level_measure=sample_agg_level_measure,
            agg_tables=sample_agg_tables,
        )

        filter_context = FilterContext(
            visual_id="v1",
            page_id="p1",
            all_columns=[
                ColumnContext(
                    table="Sales",
                    column="Key",
                    source_type=FilterSourceType.VISUAL_FIELD,
                    source_description="Visual field",
                    triggers_detail=True,
                )
            ],
            filter_sources=[],
            has_detail_triggers=True,
            has_mid_level_triggers=False,
            detail_trigger_columns=["Sales[Key]"],
        )

        level, level_name, reasoning = analyzer.determine_aggregation_level(filter_context)

        assert level == 1
        assert "Base" in level_name
        assert "Sales[Key]" in reasoning

    def test_determine_level_mid_trigger(self, sample_agg_level_measure, sample_agg_tables):
        """Test level determination when mid-level trigger column is present."""
        analyzer = FilterContextAnalyzer(
            agg_level_measure=sample_agg_level_measure,
            agg_tables=sample_agg_tables,
        )

        filter_context = FilterContext(
            visual_id="v1",
            page_id="p1",
            all_columns=[
                ColumnContext(
                    table="Calendar",
                    column="Month",
                    source_type=FilterSourceType.SLICER,
                    source_description="Slicer",
                    triggers_mid_level=True,
                )
            ],
            filter_sources=[],
            has_detail_triggers=False,
            has_mid_level_triggers=True,
            mid_level_trigger_columns=["Calendar[Month]"],
        )

        level, level_name, reasoning = analyzer.determine_aggregation_level(filter_context)

        assert level == 2
        assert "Mid" in level_name

    def test_determine_level_high_default(self, sample_agg_level_measure, sample_agg_tables):
        """Test that high level is default when no triggers present."""
        analyzer = FilterContextAnalyzer(
            agg_level_measure=sample_agg_level_measure,
            agg_tables=sample_agg_tables,
        )

        filter_context = FilterContext(
            visual_id="v1",
            page_id="p1",
            all_columns=[],
            filter_sources=[],
            has_detail_triggers=False,
            has_mid_level_triggers=False,
        )

        level, level_name, reasoning = analyzer.determine_aggregation_level(filter_context)

        assert level == 3
        assert "High" in level_name

    def test_get_aggregation_table_for_level(self, sample_agg_level_measure, sample_agg_tables):
        """Test getting aggregation table name by level."""
        analyzer = FilterContextAnalyzer(
            agg_level_measure=sample_agg_level_measure,
            agg_tables=sample_agg_tables,
        )

        assert analyzer.get_aggregation_table_for_level(1) is None  # Base table
        assert analyzer.get_aggregation_table_for_level(2) == "Agg_Monthly"
        assert analyzer.get_aggregation_table_for_level(3) == "Agg_Yearly"

    def test_analyze_visual_context(self, sample_agg_level_measure, sample_agg_tables):
        """Test complete visual context analysis."""
        analyzer = FilterContextAnalyzer(
            agg_level_measure=sample_agg_level_measure,
            agg_tables=sample_agg_tables,
        )

        visual_data = {
            "name": "visual_123",
            "visual": {
                "visualType": "barChart",
                "query": {
                    "queryState": {
                        "Category": {
                            "projections": [
                                {
                                    "field": {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Entity": "Product"}},
                                            "Property": "Category",
                                        }
                                    }
                                }
                            ]
                        },
                        "Values": {
                            "projections": [
                                {
                                    "field": {
                                        "Measure": {
                                            "Expression": {"SourceRef": {"Entity": "Sales"}},
                                            "Property": "Total Sales",
                                        }
                                    }
                                }
                            ]
                        },
                    }
                },
            },
        }

        context = analyzer.analyze_visual_context(
            visual_data,
            page_id="page1",
        )

        assert context.visual_id == "visual_123"
        assert context.page_id == "page1"
        # Should have found the Category column
        assert len(context.all_columns) >= 1


class TestSlicerExtraction:
    """Tests for slicer extraction functions."""

    def test_extract_slicers_from_page(self):
        """Test extraction of slicers from page data."""
        page_data = {
            "visuals": [
                {
                    "name": "slicer_1",
                    "visual": {
                        "visualType": "slicer",
                        "query": {
                            "queryState": {
                                "Values": {
                                    "projections": [
                                        {
                                            "field": {
                                                "Column": {
                                                    "Expression": {"SourceRef": {"Entity": "Calendar"}},
                                                    "Property": "Year",
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                    },
                },
                {
                    "name": "chart_1",
                    "visual": {
                        "visualType": "barChart",
                        "query": {"queryState": {}},
                    },
                },
            ]
        }

        slicers = extract_slicers_from_page(page_data, "page1")

        assert len(slicers) == 1
        assert slicers[0].entity == "Calendar"
        assert slicers[0].column == "Year"
        assert slicers[0].page_id == "page1"

    def test_extract_page_filters(self):
        """Test extraction of page filters."""
        page_config = {
            "filterConfig": {
                "filters": [
                    {"field": {"Column": {"Property": "Category"}}},
                    {"field": {"Column": {"Property": "Region"}}},
                ]
            }
        }

        filters = extract_page_filters(page_config)

        assert len(filters) == 2

    def test_empty_page_filters(self):
        """Test extraction when no filters present."""
        page_config = {}

        filters = extract_page_filters(page_config)

        assert filters == []


class TestColumnContext:
    """Tests for ColumnContext data class."""

    def test_column_context_creation(self):
        """Test creating ColumnContext instances."""
        ctx = ColumnContext(
            table="Sales",
            column="Amount",
            source_type=FilterSourceType.VISUAL_FIELD,
            source_description="Values field",
            triggers_detail=False,
            triggers_mid_level=False,
        )

        assert ctx.table == "Sales"
        assert ctx.column == "Amount"
        assert ctx.source_type == FilterSourceType.VISUAL_FIELD

    def test_column_context_with_filter_values(self):
        """Test ColumnContext with filter values."""
        ctx = ColumnContext(
            table="Calendar",
            column="Year",
            source_type=FilterSourceType.SLICER,
            source_description="Year slicer",
            filter_values=[2023, 2024],
        )

        assert ctx.filter_values == [2023, 2024]


class TestFilterSourceType:
    """Tests for FilterSourceType enum."""

    def test_filter_source_types(self):
        """Test all filter source types are defined."""
        assert FilterSourceType.VISUAL_FIELD
        assert FilterSourceType.VISUAL_FILTER
        assert FilterSourceType.PAGE_FILTER
        assert FilterSourceType.REPORT_FILTER
        assert FilterSourceType.SLICER
        assert FilterSourceType.DRILLTHROUGH
        assert FilterSourceType.CROSS_FILTER
