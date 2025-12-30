"""
Unit tests for Aggregation Detector Module

Tests the detection of aggregation tables, aggregation level measures,
and aggregation-aware measures in Power BI models.
"""

import pytest
from core.aggregation.aggregation_detector import (
    AggregationTableDetector,
    AggregationTable,
    AggLevelMeasure,
    AggAwareMeasure,
    AggregatedColumn,
)


class TestAggregationTableDetection:
    """Tests for aggregation table detection."""

    def test_detect_by_name_pattern_agg_prefix(self):
        """Test detection of tables with Agg_ prefix."""
        model_data = {
            "tables": [
                {
                    "name": "Agg_Sales_Monthly",
                    "is_hidden": True,
                    "columns": [
                        {"name": "YearMonth", "summarize_by": None},
                        {"name": "TotalAmount", "summarize_by": "sum"},
                    ],
                    "measures": [],
                    "partitions": [],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        assert len(tables) >= 1
        assert tables[0].name == "Agg_Sales_Monthly"
        # Check that name pattern detection reason is present in any position
        assert any("pattern" in reason.lower() for reason in tables[0].detection_reasons)

    def test_detect_by_name_pattern_summary_suffix(self):
        """Test detection of tables with _Summary suffix."""
        model_data = {
            "tables": [
                {
                    "name": "Sales_Summary",
                    "is_hidden": True,
                    "columns": [],
                    "measures": [],
                    "partitions": [],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        assert len(tables) >= 1
        assert tables[0].name == "Sales_Summary"

    def test_detect_by_summarizecolumns_expression(self):
        """Test detection by SUMMARIZECOLUMNS in partition source."""
        model_data = {
            "tables": [
                {
                    "name": "Agg_YearMonth",
                    "is_hidden": True,
                    "columns": [],
                    "measures": [],
                    "partitions": [
                        {
                            "source": """
                                SUMMARIZECOLUMNS(
                                    'Calendar'[YearMonth],
                                    'Product'[Category],
                                    "TotalSales", SUM('Sales'[Amount])
                                )
                            """
                        }
                    ],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        assert len(tables) >= 1
        # Check for SUMMARIZECOLUMNS in any detection reason
        assert any("SUMMARIZECOLUMNS" in reason for reason in tables[0].detection_reasons)

    def test_skip_system_tables(self):
        """Test that system tables are skipped."""
        model_data = {
            "tables": [
                {"name": "LocalDateTable_12345", "columns": [], "measures": [], "partitions": []},
                {"name": "DateTableTemplate_67890", "columns": [], "measures": [], "partitions": []},
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        assert len(tables) == 0

    def test_detection_confidence_score(self):
        """Test that detection confidence is calculated correctly."""
        model_data = {
            "tables": [
                {
                    "name": "Agg_Sales",  # 0.4 for name pattern
                    "is_hidden": True,  # 0.2 for hidden
                    "columns": [],
                    "measures": [],
                    "partitions": [
                        {"source": "SUMMARIZECOLUMNS(...)"}  # 0.4 for expression
                    ],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        assert len(tables) == 1
        # Should have high confidence (1.0 capped)
        assert tables[0].detection_confidence >= 0.8

    def test_aggregation_level_estimation(self):
        """Test aggregation level estimation from grain."""
        model_data = {
            "tables": [
                {
                    "name": "Agg_YearQuarter",
                    "is_hidden": True,
                    "columns": [],
                    "measures": [],
                    "partitions": [],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        # YearQuarter suggests high-level aggregation
        assert len(tables) == 1
        level = tables[0].level
        # Level should be 2 or 3 (both are valid interpretations)
        assert level in [2, 3]


class TestAggLevelMeasureDetection:
    """Tests for aggregation level measure detection."""

    def test_detect_agg_level_measure_with_isfiltered(self):
        """Test detection of aggregation level measures using ISFILTERED pattern."""
        model_data = {
            "tables": [
                {
                    "name": "Measures",
                    "columns": [],
                    "partitions": [],
                    "measures": [
                        {
                            "name": "_AggregationLevel",
                            "expression": """
                                VAR _D =
                                    ISFILTERED('Sales'[Key]) ||
                                    ISFILTERED('Product'[ProductKey]) ||
                                    ISFILTERED('Customer'[CustomerKey])
                                VAR _M =
                                    ISFILTERED('Calendar'[Month])
                                RETURN
                                    SWITCH(TRUE(), _D, 1, _M, 2, 3)
                            """,
                        }
                    ],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        measures = detector.detect_aggregation_level_measures()

        assert len(measures) == 1
        assert measures[0].name == "_AggregationLevel"
        assert len(measures[0].detail_trigger_columns) >= 1
        assert any("Sales" in col for col in measures[0].detail_trigger_columns)

    def test_detect_multiple_isfiltered_patterns(self):
        """Test detection with complex ISFILTERED patterns."""
        model_data = {
            "tables": [
                {
                    "name": "Measures",
                    "columns": [],
                    "partitions": [],
                    "measures": [
                        {
                            "name": "_AggLevel",
                            "expression": """
                                VAR _Detail =
                                    ISFILTERED('Sales'[Key]) ||
                                    ISFILTERED('Sales'[Date]) ||
                                    ISFILTERED('Product'[SKU]) ||
                                    ISFILTERED('Customer'[ID])
                                VAR _Mid =
                                    ISFILTERED('Calendar'[Month]) ||
                                    ISFILTERED('Product'[Category])
                                VAR _High =
                                    ISFILTERED('Calendar'[Year])
                                RETURN
                                    SWITCH(TRUE(), _Detail, 1, _Mid, 2, 3)
                            """,
                        }
                    ],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        measures = detector.detect_aggregation_level_measures()

        assert len(measures) == 1
        assert len(measures[0].detail_trigger_columns) >= 3

    def test_no_detection_for_simple_isfiltered(self):
        """Test that simple ISFILTERED usage is not detected as level measure."""
        model_data = {
            "tables": [
                {
                    "name": "Measures",
                    "columns": [],
                    "partitions": [],
                    "measures": [
                        {
                            "name": "FilteredSales",
                            "expression": """
                                IF(ISFILTERED('Product'[Category]),
                                   SUM('Sales'[Amount]),
                                   BLANK())
                            """,
                        }
                    ],
                }
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        measures = detector.detect_aggregation_level_measures()

        # Only 1 ISFILTERED, should not be detected as agg level measure
        assert len(measures) == 0


class TestAggAwareMeasureDetection:
    """Tests for aggregation-aware measure detection."""

    def test_detect_agg_aware_measure_referencing_level(self):
        """Test detection of measures that reference aggregation level measure."""
        # Create a level measure expression with enough ISFILTERED patterns
        level_measure_expr = """
            VAR _D =
                ISFILTERED('Sales'[Key]) ||
                ISFILTERED('Product'[ProductKey]) ||
                ISFILTERED('Customer'[CustomerKey])
            VAR _M =
                ISFILTERED('Calendar'[Month])
            RETURN
                SWITCH(TRUE(), _D, 1, _M, 2, 3)
        """

        model_data = {
            "tables": [
                {
                    "name": "Measures",
                    "columns": [],
                    "partitions": [],
                    "measures": [
                        {
                            "name": "_AggLevel",
                            "expression": level_measure_expr,
                        },
                        {
                            "name": "Total Sales",
                            "expression": """
                                SWITCH(
                                    [_AggLevel],
                                    1, SUM('Sales'[Amount]),
                                    2, SUM('Agg_Monthly'[Amount]),
                                    3, SUM('Agg_Yearly'[Amount])
                                )
                            """,
                        },
                    ],
                },
                {
                    "name": "Agg_Monthly",
                    "is_hidden": True,
                    "columns": [{"name": "Amount", "summarize_by": "sum"}],
                    "measures": [],
                    "partitions": [],
                },
                {
                    "name": "Agg_Yearly",
                    "is_hidden": True,
                    "columns": [{"name": "Amount", "summarize_by": "sum"}],
                    "measures": [],
                    "partitions": [],
                },
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        agg_tables = detector.detect_aggregation_tables()
        agg_level_measures = detector.detect_aggregation_level_measures()
        agg_aware = detector.detect_aggregation_aware_measures(agg_tables, agg_level_measures)

        assert len(agg_aware) >= 1
        total_sales_measures = [m for m in agg_aware if m.name == "Total Sales"]
        assert len(total_sales_measures) == 1
        assert total_sales_measures[0].uses_agg_level_measure is not None


class TestFullDetection:
    """Tests for full detection workflow."""

    def test_detect_all(self):
        """Test complete detection workflow."""
        model_data = {
            "tables": [
                {
                    "name": "Sales",
                    "columns": [
                        {"name": "Amount", "summarize_by": "sum"},
                        {"name": "Key"},
                    ],
                    "measures": [],
                    "partitions": [],
                },
                {
                    "name": "Agg_Sales_Monthly",
                    "is_hidden": True,
                    "columns": [{"name": "TotalAmount", "summarize_by": "sum"}],
                    "measures": [],
                    "partitions": [{"source": "SUMMARIZECOLUMNS('Calendar'[Month], 'Sales')"}],
                },
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        results = detector.detect_all()

        assert "aggregation_tables" in results
        assert "base_fact_tables" in results
        assert "agg_level_measures" in results
        assert "agg_aware_measures" in results
        assert len(results["aggregation_tables"]) >= 1


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_model(self):
        """Test with empty model."""
        model_data = {"tables": [], "relationships": []}

        detector = AggregationTableDetector(model_data)
        results = detector.detect_all()

        assert results["aggregation_tables"] == []
        assert results["agg_level_measures"] == []
        assert results["agg_aware_measures"] == []

    def test_missing_keys(self):
        """Test with missing optional keys in model data."""
        model_data = {
            "tables": [
                {"name": "Agg_Test"}  # Missing columns, measures, partitions
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        # Should not raise exception
        tables = detector.detect_aggregation_tables()
        assert isinstance(tables, list)

    def test_table_without_name(self):
        """Test handling of table without name."""
        model_data = {
            "tables": [
                {"columns": [], "measures": [], "partitions": []}
            ],
            "relationships": [],
        }

        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()
        assert len(tables) == 0
