"""
Integration tests for Aggregation Analysis Module

Tests the complete aggregation analysis workflow with the Contoso Sales Sample PBIP model.
"""

import pytest
import os
from pathlib import Path


# Path to the Contoso Sales Sample PBIP model for integration testing
CONTOSO_PBIP_PATH = r"C:\Users\bjorn.braet\OneDrive - Finvision\FINTICX - Documenten\M01 - Wealth Reporting\04-Analytics\Aggregation Analysis MCP"


def is_contoso_available():
    """Check if the Contoso PBIP model is available for testing."""
    path = Path(CONTOSO_PBIP_PATH)
    return path.exists() and any(
        d.name.endswith(".SemanticModel") for d in path.iterdir() if d.is_dir()
    )


@pytest.mark.skipif(not is_contoso_available(), reason="Contoso PBIP model not available")
class TestContosoAggregationAnalysis:
    """Integration tests using the Contoso Sales Sample PBIP model."""

    @pytest.fixture
    def analyzer(self):
        """Create an analyzer for the Contoso model."""
        from core.aggregation import AggregationAnalyzer
        return AggregationAnalyzer(CONTOSO_PBIP_PATH)

    def test_model_path_resolution(self, analyzer):
        """Test that model path is correctly resolved."""
        assert analyzer.model_path is not None
        assert analyzer.model_path.exists()
        assert analyzer.model_path.name.endswith(".SemanticModel")

    def test_load_model_data(self, analyzer):
        """Test loading model data from TMDL files."""
        model_data = analyzer._load_model_data()

        assert model_data is not None
        assert "tables" in model_data
        assert len(model_data["tables"]) > 0

    def test_detect_aggregation_tables(self, analyzer):
        """Test detection of aggregation tables in Contoso model."""
        model_data = analyzer._load_model_data()

        from core.aggregation import AggregationTableDetector
        detector = AggregationTableDetector(model_data)
        tables = detector.detect_aggregation_tables()

        # Contoso model should have aggregation tables
        assert len(tables) >= 2  # At least Agg_Sales_YearMonth_Category and Agg_Sales_YearQuarter

        # Check for expected tables
        table_names = [t.name for t in tables]
        print(f"Detected aggregation tables: {table_names}")

        # Should find tables with Agg_ prefix or similar
        has_agg_tables = any("Agg" in name for name in table_names)
        assert has_agg_tables, f"Expected Agg tables, found: {table_names}"

    def test_detect_aggregation_level_measure(self, analyzer):
        """Test detection of aggregation level measure."""
        model_data = analyzer._load_model_data()

        from core.aggregation import AggregationTableDetector
        detector = AggregationTableDetector(model_data)
        measures = detector.detect_aggregation_level_measures()

        print(f"Detected aggregation level measures: {[m.name for m in measures]}")

        # Contoso model should have _AggregationLevel measure
        if measures:
            assert len(measures[0].detail_trigger_columns) > 0
            print(f"Detail triggers: {measures[0].detail_trigger_columns[:5]}")
            print(f"Mid-level triggers: {measures[0].mid_level_trigger_columns[:5]}")

    def test_detect_aggregation_aware_measures(self, analyzer):
        """Test detection of aggregation-aware measures."""
        model_data = analyzer._load_model_data()

        from core.aggregation import AggregationTableDetector
        detector = AggregationTableDetector(model_data)
        agg_tables = detector.detect_aggregation_tables()
        agg_level_measures = detector.detect_aggregation_level_measures()
        agg_aware = detector.detect_aggregation_aware_measures(agg_tables, agg_level_measures)

        print(f"Detected {len(agg_aware)} aggregation-aware measures")
        for m in agg_aware[:5]:
            print(f"  - {m.name}")

        # Should find some aggregation-aware measures
        assert len(agg_aware) >= 1

    def test_full_analysis_without_report(self, analyzer):
        """Test full analysis without report analysis."""
        result = analyzer.analyze(include_report=False)

        assert result is not None
        assert result.model_name != ""
        assert len(result.aggregation_tables) >= 1

        print(f"\nAnalysis Summary:")
        print(f"  Model: {result.model_name}")
        print(f"  Aggregation tables: {len(result.aggregation_tables)}")
        print(f"  Agg level measures: {len(result.agg_level_measures)}")
        print(f"  Agg-aware measures: {len(result.agg_aware_measures)}")

    def test_full_analysis_with_report(self, analyzer):
        """Test full analysis including report analysis."""
        # Skip if no report folder
        if analyzer.report_path is None:
            pytest.skip("No report folder found")

        result = analyzer.analyze(include_report=True)

        assert result is not None
        assert result.has_report or result.report_summary is not None

        if result.report_summary:
            print(f"\nReport Analysis:")
            print(f"  Pages: {result.report_summary.total_pages}")
            print(f"  Visuals: {result.report_summary.visuals_analyzed}")
            print(f"  Score: {result.report_summary.optimization_score:.1f}")


@pytest.mark.skipif(not is_contoso_available(), reason="Contoso PBIP model not available")
class TestContosoReportBuilding:
    """Integration tests for report building with Contoso model."""

    @pytest.fixture
    def analysis_result(self):
        """Run analysis and return result."""
        from core.aggregation import AggregationAnalyzer
        analyzer = AggregationAnalyzer(CONTOSO_PBIP_PATH)
        return analyzer.analyze(include_report=True)

    def test_build_summary_text(self, analysis_result):
        """Test building summary text report."""
        from core.aggregation import AggregationReportBuilder
        builder = AggregationReportBuilder(analysis_result)
        summary = builder.build_summary_text()

        assert len(summary) > 100
        assert "AGGREGATION ANALYSIS SUMMARY" in summary
        print(f"\n{summary[:1000]}...")

    def test_build_json_export(self, analysis_result):
        """Test building JSON export."""
        from core.aggregation import AggregationReportBuilder
        import json

        builder = AggregationReportBuilder(analysis_result)
        json_data = builder.build_json_export()

        # Should be serializable
        json_str = json.dumps(json_data, indent=2)
        assert len(json_str) > 100

        # Should contain expected keys
        assert "model_name" in json_data
        assert "aggregation_tables" in json_data

    def test_build_html_report(self, analysis_result):
        """Test building HTML report."""
        from core.aggregation import AggregationReportBuilder
        builder = AggregationReportBuilder(analysis_result)
        html = builder.build_html_report()

        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert len(html) > 1000


@pytest.mark.skipif(not is_contoso_available(), reason="Contoso PBIP model not available")
class TestContosoHandler:
    """Integration tests for the MCP handler."""

    @pytest.mark.asyncio
    async def test_handler_summary_format(self):
        """Test handler with summary format."""
        from server.handlers.aggregation_handler import handle_aggregation_analysis

        result = await handle_aggregation_analysis({
            "pbip_path": CONTOSO_PBIP_PATH,
            "output_format": "summary",
        })

        assert result["success"] is True
        assert "report" in result  # Handler uses "report" key for summary text
        assert result["format"] == "summary"
        print(result["report"][:500])

    @pytest.mark.asyncio
    async def test_handler_json_format(self):
        """Test handler with JSON format."""
        from server.handlers.aggregation_handler import handle_aggregation_analysis

        result = await handle_aggregation_analysis({
            "pbip_path": CONTOSO_PBIP_PATH,
            "output_format": "json",
        })

        assert result["success"] is True
        assert "data" in result  # Handler uses "data" key for JSON data
        assert result["format"] == "json"
        data = result["data"]
        assert "model_name" in data

    @pytest.mark.asyncio
    async def test_handler_invalid_path(self):
        """Test handler with invalid path."""
        from server.handlers.aggregation_handler import handle_aggregation_analysis

        result = await handle_aggregation_analysis({
            "pbip_path": "/nonexistent/path",
            "output_format": "summary",
        })

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_handler_missing_path(self):
        """Test handler with missing path parameter."""
        from server.handlers.aggregation_handler import handle_aggregation_analysis

        result = await handle_aggregation_analysis({
            "output_format": "summary",
        })

        assert result["success"] is False
        assert "error" in result


class TestTmdlParserForAggregation:
    """Tests for TMDL parser functionality needed by aggregation analysis."""

    @pytest.mark.skipif(not is_contoso_available(), reason="Contoso PBIP model not available")
    def test_parse_tables_with_leading_comments(self):
        """Test that tables with leading comments are parsed correctly."""
        from core.tmdl.tmdl_parser import TmdlParser

        # Find the semantic model path
        pbip_path = Path(CONTOSO_PBIP_PATH)
        model_path = None
        for item in pbip_path.iterdir():
            if item.is_dir() and item.name.endswith(".SemanticModel"):
                model_path = item
                break

        assert model_path is not None

        parser = TmdlParser(str(model_path))
        model = parser.parse_full_model()

        # Check that all tables have names
        for table in model["tables"]:
            assert "name" in table
            assert table["name"] != ""

        # Check specifically for aggregation tables
        table_names = [t["name"] for t in model["tables"]]
        print(f"All table names: {table_names}")

        # Should find tables starting with Agg_ or similar
        agg_tables = [n for n in table_names if "Agg" in n]
        print(f"Aggregation tables: {agg_tables}")

    @pytest.mark.skipif(not is_contoso_available(), reason="Contoso PBIP model not available")
    def test_parse_measures_with_isfiltered(self):
        """Test that measures with ISFILTERED patterns are parsed correctly."""
        from core.tmdl.tmdl_parser import TmdlParser

        # Find the semantic model path
        pbip_path = Path(CONTOSO_PBIP_PATH)
        model_path = None
        for item in pbip_path.iterdir():
            if item.is_dir() and item.name.endswith(".SemanticModel"):
                model_path = item
                break

        assert model_path is not None

        parser = TmdlParser(str(model_path))
        model = parser.parse_full_model()

        # Find measures with ISFILTERED
        isfiltered_measures = []
        for table in model["tables"]:
            for measure in table.get("measures", []):
                expr = measure.get("expression", "")
                if "ISFILTERED" in expr:
                    isfiltered_measures.append(measure["name"])

        print(f"Measures with ISFILTERED: {isfiltered_measures}")

    @pytest.mark.skipif(not is_contoso_available(), reason="Contoso PBIP model not available")
    def test_parse_hidden_tables(self):
        """Test that hidden tables are detected correctly."""
        from core.tmdl.tmdl_parser import TmdlParser

        # Find the semantic model path
        pbip_path = Path(CONTOSO_PBIP_PATH)
        model_path = None
        for item in pbip_path.iterdir():
            if item.is_dir() and item.name.endswith(".SemanticModel"):
                model_path = item
                break

        assert model_path is not None

        parser = TmdlParser(str(model_path))
        model = parser.parse_full_model()

        hidden_tables = [t["name"] for t in model["tables"] if t.get("is_hidden", False)]
        print(f"Hidden tables: {hidden_tables}")

        # Aggregation tables are typically hidden
        for table in model["tables"]:
            if "Agg" in table.get("name", ""):
                print(f"  {table['name']}: is_hidden={table.get('is_hidden', False)}")
