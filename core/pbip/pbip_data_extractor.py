"""
PBIP Data Extractor - Separates data retrieval from HTML generation.

This module is responsible for extracting and transforming data from PBIP folders
into a structured format that can be used by the HTML generator.

Architecture:
- PbipDataExtractor: Main class that orchestrates data extraction
- Each section has dedicated extraction methods
- Data is returned in a standardized format ready for template rendering
"""

import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class PbipDataExtractor:
    """
    Extracts and transforms PBIP data for HTML report generation.

    This class separates the data retrieval logic from the HTML template generation,
    making debugging and maintenance easier.
    """

    def __init__(
        self,
        model_data: Dict[str, Any],
        report_data: Optional[Dict[str, Any]],
        dependencies: Dict[str, Any],
        enhanced_results: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the data extractor.

        Args:
            model_data: Parsed model data from TmdlModelAnalyzer
            report_data: Optional parsed report data from PbirReportAnalyzer
            dependencies: Dependency analysis results from PbipDependencyEngine
            enhanced_results: Optional enhanced analysis results from EnhancedPbipAnalyzer
        """
        self.model_data = model_data or {}
        self.report_data = report_data
        self.dependencies = dependencies or {}
        self.enhanced_results = enhanced_results or {}
        self.logger = logger

    def extract_all_data(self) -> Dict[str, Any]:
        """
        Extract all data needed for the HTML report.

        Returns:
            Dictionary containing all extracted data organized by section
        """
        self.logger.info("Extracting all PBIP data for HTML report")

        return {
            "metadata": self._extract_metadata(),
            "overview": self._extract_overview_data(),
            "model": self._extract_model_data(),
            "report": self._extract_report_data(),
            "dependencies": self._extract_dependency_data(),
            "bpa": self._extract_bpa_data(),
            "perspectives": self._extract_perspectives_data(),
            "data_types": self._extract_data_types_data(),
        }

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata about the extraction."""
        return {
            "extracted_at": datetime.now().isoformat(),
            "extractor_version": "2.0.0",
            "has_model": bool(self.model_data),
            "has_report": bool(self.report_data),
            "has_enhanced": bool(self.enhanced_results),
        }

    def _extract_overview_data(self) -> Dict[str, Any]:
        """Extract overview/summary data."""
        tables = self.model_data.get("tables", [])
        relationships = self.model_data.get("relationships", [])

        # Count measures and columns
        total_measures = 0
        total_columns = 0
        for table in tables:
            total_measures += len(table.get("measures", []))
            total_columns += len(table.get("columns", []))

        # Report stats
        pages = []
        total_visuals = 0
        if self.report_data:
            pages = self.report_data.get("pages", [])
            for page in pages:
                total_visuals += len(page.get("visuals", []))

        return {
            "tables_count": len(tables),
            "measures_count": total_measures,
            "columns_count": total_columns,
            "relationships_count": len(relationships),
            "pages_count": len(pages),
            "visuals_count": total_visuals,
            "unused_columns_count": len(self.dependencies.get("unused_columns", [])),
            "unused_measures_count": len(self.dependencies.get("unused_measures", [])),
        }

    def _extract_model_data(self) -> Dict[str, Any]:
        """Extract model structure data."""
        return {
            "tables": self.model_data.get("tables", []),
            "relationships": self.model_data.get("relationships", []),
            "roles": self.model_data.get("roles", []),
            "cultures": self.model_data.get("cultures", []),
            "calculation_groups": self.model_data.get("calculation_groups", []),
        }

    def _extract_report_data(self) -> Dict[str, Any]:
        """Extract report structure data."""
        if not self.report_data:
            return {"pages": [], "has_report": False}

        return {
            "pages": self.report_data.get("pages", []),
            "has_report": True,
            "report_name": self.report_data.get("name", ""),
            "theme": self.report_data.get("theme", {}),
        }

    def _extract_dependency_data(self) -> Dict[str, Any]:
        """Extract dependency analysis data."""
        return {
            "measure_dependencies": self.dependencies.get("measure_dependencies", {}),
            "column_to_measure": self.dependencies.get("column_to_measure", {}),
            "unused_columns": self.dependencies.get("unused_columns", []),
            "unused_measures": self.dependencies.get("unused_measures", []),
            "visual_dependencies": self.dependencies.get("visual_dependencies", {}),
        }

    # ============================================================================
    # BPA DATA EXTRACTION
    # ============================================================================

    def _extract_bpa_data(self) -> Dict[str, Any]:
        """Extract Best Practice Analysis data."""
        bpa = self.enhanced_results.get("analyses", {}).get("bpa", {})

        return {
            "rules": bpa.get("rules", []),
            "violations": bpa.get("violations", []),
            "summary": bpa.get("summary", {}),
            "has_data": len(bpa.get("violations", [])) > 0,
        }

    # ============================================================================
    # PERSPECTIVES DATA EXTRACTION
    # ============================================================================

    def _extract_perspectives_data(self) -> Dict[str, Any]:
        """Extract perspectives analysis data."""
        perspectives = self.enhanced_results.get("analyses", {}).get("perspectives", {})

        return {
            "has_perspectives": perspectives.get("has_perspectives", False),
            "perspectives": perspectives.get("perspectives", []),
            "perspective_count": perspectives.get("perspective_count", 0),
            "message": perspectives.get("message", ""),
        }

    # ============================================================================
    # DATA TYPES DATA EXTRACTION
    # ============================================================================

    def _extract_data_types_data(self) -> Dict[str, Any]:
        """Extract data type analysis data."""
        data_types = self.enhanced_results.get("analyses", {}).get("data_types", {})

        return {
            "issues": data_types.get("issues", []),
            "summary": data_types.get("summary", {}),
            "has_data": len(data_types.get("issues", [])) > 0,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def extract_pbip_data(
    model_data: Dict[str, Any],
    report_data: Optional[Dict[str, Any]],
    dependencies: Dict[str, Any],
    enhanced_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to extract all PBIP data.

    Args:
        model_data: Parsed model data
        report_data: Optional parsed report data
        dependencies: Dependency analysis results
        enhanced_results: Optional enhanced analysis results

    Returns:
        Dictionary containing all extracted data
    """
    extractor = PbipDataExtractor(
        model_data=model_data,
        report_data=report_data,
        dependencies=dependencies,
        enhanced_results=enhanced_results
    )
    return extractor.extract_all_data()
