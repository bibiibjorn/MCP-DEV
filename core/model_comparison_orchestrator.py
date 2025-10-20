"""
Model Comparison Orchestrator

High-level orchestration for comparing two Power BI models using TMDL export,
parsing, diffing, and report generation.
"""

import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from core.model_diff_engine import ModelDiffer
from core.model_diff_report import ModelDiffReportGenerator
from core.multi_instance_manager import multi_instance_manager
from core.connection_manager import ConnectionManager
import json

logger = logging.getLogger(__name__)


class ModelComparisonOrchestrator:
    """
    Orchestrates the complete model comparison workflow.

    Workflow:
    1. Connect to two Power BI Desktop instances
    2. Export both models to TMDL format
    3. Parse TMDL structures
    4. Run comparison engine
    5. Generate HTML report
    6. Cleanup temporary files
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.temp_files: list[str] = []

    def compare_models(
        self,
        port1: int,
        port2: int,
        output_path: Optional[str] = None,
        include_restricted: bool = False,
        generate_json: bool = False,
        model1_label: Optional[str] = None,
        model2_label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare two Power BI models and generate diff report.

        Args:
            port1: Port of first Power BI Desktop instance (BASE/OLD model)
            port2: Port of second Power BI Desktop instance (NEW model)
            output_path: Optional custom output path for HTML report
            include_restricted: Include restricted information in TMDL export
            generate_json: Also generate JSON export of diff data
            model1_label: Optional label for model 1 (e.g., "Sales_Model_v1.pbix" or "BASE")
            model2_label: Optional label for model 2 (e.g., "Sales_Model_v2.pbix" or "NEW")

        Returns:
            Comparison result dictionary with report paths and summary
        """
        logger.info(f"Starting model comparison: port {port1} vs port {port2}")

        try:
            # Step 1: Connect to both instances
            conn_result1 = multi_instance_manager.connect_to_instance(port1)
            if not conn_result1.get('success'):
                raise RuntimeError(
                    f"Failed to connect to instance 1 (port {port1}): "
                    f"{conn_result1.get('error')}"
                )

            conn_result2 = multi_instance_manager.connect_to_instance(port2)
            if not conn_result2.get('success'):
                raise RuntimeError(
                    f"Failed to connect to instance 2 (port {port2}): "
                    f"{conn_result2.get('error')}"
                )

            logger.info("Successfully connected to both instances")

            # Step 2: Export both models using model_exporter (JSON TMDL structure)
            logger.info("Exporting models to TMDL structure...")

            # Get model exporters for each instance
            from core.model_exporter import ModelExporter

            conn_manager1 = multi_instance_manager.get_instance(port1)
            conn_manager2 = multi_instance_manager.get_instance(port2)

            if not conn_manager1 or not conn_manager2:
                raise RuntimeError("Failed to get connection managers")

            # Create model exporters with connections
            exporter1 = ModelExporter(conn_manager1.get_connection())
            exporter2 = ModelExporter(conn_manager2.get_connection())

            # Export to files (export_to_file=True by default)
            tmdl_export1 = exporter1.export_tmdl_structure(export_to_file=True)
            tmdl_export2 = exporter2.export_tmdl_structure(export_to_file=True)

            if not tmdl_export1.get('success') or not tmdl_export2.get('success'):
                raise RuntimeError(
                    f"TMDL export failed: "
                    f"Model 1: {tmdl_export1.get('error', 'Unknown')}, "
                    f"Model 2: {tmdl_export2.get('error', 'Unknown')}"
                )

            logger.info(
                f"TMDL exports complete: "
                f"{tmdl_export1['statistics']['tables']} tables (model 1), "
                f"{tmdl_export2['statistics']['tables']} tables (model 2)"
            )

            # Store file paths for cleanup
            self.temp_files.append(tmdl_export1['export_file'])
            self.temp_files.append(tmdl_export2['export_file'])

            # Step 3: Load TMDL structures from exported JSON files
            logger.info("Loading TMDL structures from files...")

            with open(tmdl_export1['export_file'], 'r', encoding='utf-8') as f:
                export1_data = json.load(f)
                model1 = export1_data['tmdl']

            with open(tmdl_export2['export_file'], 'r', encoding='utf-8') as f:
                export2_data = json.load(f)
                model2 = export2_data['tmdl']

            # Convert tables dict to list (differ expects list format)
            if isinstance(model1.get('tables'), dict):
                model1['tables'] = list(model1['tables'].values())
            if isinstance(model2.get('tables'), dict):
                model2['tables'] = list(model2['tables'].values())

            logger.info(
                f"Loaded structures: "
                f"{len(model1.get('tables', []))} tables (model 1), "
                f"{len(model2.get('tables', []))} tables (model 2)"
            )

            # Step 4: Run comparison engine
            logger.info("Running comparison engine...")

            differ = ModelDiffer(model1, model2)
            diff_result = differ.compare()

            # Override model names with user-provided labels if given
            if model1_label:
                diff_result['summary']['model1_name'] = model1_label
            if model2_label:
                diff_result['summary']['model2_name'] = model2_label

            total_changes = diff_result['summary']['total_changes']

            logger.info(f"Comparison complete: {total_changes} total changes detected")

            # Step 5: Generate HTML report
            logger.info("Generating HTML report...")

            if output_path is None:
                # Generate default output path in project exports directory
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                project_root = Path(__file__).parent.parent  # Go up from core/ to project root
                output_dir = project_root / "exports" / "model_diffs"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"model_diff_{timestamp}.html")

            report_generator = ModelDiffReportGenerator(diff_result)
            html_report_path = report_generator.generate_html_report(output_path)

            logger.info(f"HTML report generated: {html_report_path}")

            # Step 6: Generate JSON export if requested
            json_report_path = None
            if generate_json:
                json_path = Path(html_report_path).with_suffix('.json')
                self._write_json_export(diff_result, str(json_path))
                json_report_path = str(json_path)
                logger.info(f"JSON export generated: {json_report_path}")

            # Return result
            result = {
                "success": True,
                "summary": {
                    "model1_name": diff_result['summary']['model1_name'],
                    "model2_name": diff_result['summary']['model2_name'],
                    "total_changes": total_changes,
                    "changes_by_category": diff_result['summary']['changes_by_category']
                },
                "reports": {
                    "html": html_report_path,
                    "json": json_report_path
                },
                "tmdl_exports": {
                    "model1": {
                        "path": tmdl_export1['export_file'],
                        "statistics": tmdl_export1['statistics']
                    },
                    "model2": {
                        "path": tmdl_export2['export_file'],
                        "statistics": tmdl_export2['statistics']
                    }
                }
            }

            logger.info("Model comparison completed successfully")

            return result

        except Exception as e:
            logger.error(f"Model comparison failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

        finally:
            # Cleanup: disconnect instances
            try:
                if port1 in multi_instance_manager.instances:
                    multi_instance_manager.disconnect_instance(port1)
                if port2 in multi_instance_manager.instances:
                    multi_instance_manager.disconnect_instance(port2)
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")

    def _write_json_export(self, diff_result: Dict[str, Any], json_path: str) -> None:
        """Write diff result to JSON file."""
        import json

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(diff_result, f, indent=2, ensure_ascii=False)

        logger.debug(f"JSON export written: {json_path}")

    def compare_with_detected_instances(
        self,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect and compare two available Power BI Desktop instances.

        Automatically detects running instances and compares the first two found.

        Args:
            output_path: Optional custom output path for HTML report

        Returns:
            Comparison result dictionary
        """
        try:
            # Detect instances
            from core.connection_manager import PowerBIDesktopDetector

            detector = PowerBIDesktopDetector()
            instances = detector.find_powerbi_instances()

            if len(instances) < 2:
                return {
                    "success": False,
                    "error": f"Need at least 2 Power BI Desktop instances running. Found: {len(instances)}"
                }

            # Get first two instances
            instance1 = instances[0]
            instance2 = instances[1]

            port1 = instance1['port']
            port2 = instance2['port']

            logger.info(f"Auto-detected instances: ports {port1} and {port2}")

            # Perform comparison
            return self.compare_models(port1, port2, output_path)

        except Exception as e:
            logger.error(f"Auto-detection comparison failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Convenience function
def compare_pbi_models(
    port1: int,
    port2: int,
    output_path: Optional[str] = None,
    include_restricted: bool = False,
    generate_json: bool = False,
    model1_label: Optional[str] = None,
    model2_label: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to compare two Power BI models.

    Args:
        port1: Port of first Power BI Desktop instance (BASE/OLD)
        port2: Port of second Power BI Desktop instance (NEW)
        output_path: Optional custom output path for HTML report
        include_restricted: Include restricted information
        generate_json: Also generate JSON export
        model1_label: Label for base model (e.g., "Sales_v1.pbix" or "BASE")
        model2_label: Label for new model (e.g., "Sales_v2.pbix" or "NEW")

    Returns:
        Comparison result dictionary
    """
    orchestrator = ModelComparisonOrchestrator()
    return orchestrator.compare_models(port1, port2, output_path, include_restricted, generate_json, model1_label, model2_label)
