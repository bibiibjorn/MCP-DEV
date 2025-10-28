"""
Bulk Operations Manager for PBIXRay MCP Server
Handles batch operations for measures and other objects
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class BulkOperationsManager:
    """Handle bulk operations on measures and other objects."""

    def __init__(self, dax_injector):
        """Initialize with DAX injector."""
        self.dax_injector = dax_injector

    def bulk_create_measures(self, measures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple measures in batch.

        Args:
            measures: List of measure definitions with:
                - table: Table name
                - measure: Measure name
                - expression: DAX expression
                - display_folder: Optional folder
                - description: Optional description
                - format_string: Optional format

        Returns:
            Batch operation results
        """
        if not measures:
            return {
                'success': False,
                'error': 'No measures provided'
            }

        results = []
        success_count = 0
        error_count = 0

        for idx, measure_def in enumerate(measures):
            try:
                table = measure_def.get('table')
                measure = measure_def.get('measure')
                expression = measure_def.get('expression')

                if not all([table, measure, expression]):
                    results.append({
                        'index': idx,
                        'measure': measure,
                        'success': False,
                        'error': 'Missing required fields (table, measure, expression)'
                    })
                    error_count += 1
                    continue

                # Create measure
                result = self.dax_injector.upsert_measure(
                    table_name=table,
                    measure_name=measure,
                    dax_expression=expression,
                    display_folder=measure_def.get('display_folder'),
                    description=measure_def.get('description'),
                    format_string=measure_def.get('format_string')
                )

                if result.get('success'):
                    success_count += 1
                    results.append({
                        'index': idx,
                        'measure': measure,
                        'table': table,
                        'success': True,
                        'action': result.get('action', 'created')
                    })
                else:
                    error_count += 1
                    results.append({
                        'index': idx,
                        'measure': measure,
                        'table': table,
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    })

            except Exception as e:
                error_count += 1
                results.append({
                    'index': idx,
                    'success': False,
                    'error': str(e)
                })

        return {
            'success': error_count == 0,
            'total_measures': len(measures),
            'success_count': success_count,
            'error_count': error_count,
            'results': results,
            'summary': f"Created {success_count}/{len(measures)} measures successfully"
        }

    def bulk_update_display_folders(
        self,
        table: str,
        measures: List[str],
        display_folder: str
    ) -> Dict[str, Any]:
        """
        Update display folder for multiple measures.

        Args:
            table: Table name
            measures: List of measure names
            display_folder: New display folder

        Returns:
            Batch operation results
        """
        results = []
        success_count = 0

        for measure in measures:
            try:
                # Get current measure definition
                # We need to retrieve expression to update
                # For now, just set display folder
                result = self.dax_injector.upsert_measure(
                    table_name=table,
                    measure_name=measure,
                    dax_expression="",  # Will preserve existing
                    display_folder=display_folder
                )

                if result.get('success'):
                    success_count += 1
                    results.append({
                        'measure': measure,
                        'success': True
                    })
                else:
                    results.append({
                        'measure': measure,
                        'success': False,
                        'error': result.get('error')
                    })

            except Exception as e:
                results.append({
                    'measure': measure,
                    'success': False,
                    'error': str(e)
                })

        return {
            'success': success_count == len(measures),
            'total_measures': len(measures),
            'success_count': success_count,
            'display_folder': display_folder,
            'results': results
        }

    def bulk_delete_measures(
        self,
        measures: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Delete multiple measures.

        Args:
            measures: List of dicts with 'table' and 'measure'

        Returns:
            Batch operation results
        """
        results = []
        success_count = 0

        for measure_def in measures:
            table = measure_def.get('table')
            measure = measure_def.get('measure')

            if not table or not measure:
                results.append({
                    'table': table,
                    'measure': measure,
                    'success': False,
                    'error': 'Missing table or measure name'
                })
                continue

            try:
                result = self.dax_injector.delete_measure(table, measure)

                if result.get('success'):
                    success_count += 1
                    results.append({
                        'table': table,
                        'measure': measure,
                        'success': True
                    })
                else:
                    results.append({
                        'table': table,
                        'measure': measure,
                        'success': False,
                        'error': result.get('error')
                    })

            except Exception as e:
                results.append({
                    'table': table,
                    'measure': measure,
                    'success': False,
                    'error': str(e)
                })

        return {
            'success': success_count == len(measures),
            'total_measures': len(measures),
            'success_count': success_count,
            'results': results
        }

    def import_measures_from_json(self, json_data: str) -> Dict[str, Any]:
        """
        Import measures from JSON string.

        Expected format:
        [
            {
                "table": "Sales",
                "measure": "Total Sales",
                "expression": "SUM(Sales[Amount])",
                "display_folder": "Sales KPIs",
                "format_string": "#,##0.00"
            },
            ...
        ]

        Args:
            json_data: JSON string with measure definitions

        Returns:
            Import results
        """
        try:
            measures = json.loads(json_data)

            if not isinstance(measures, list):
                return {
                    'success': False,
                    'error': 'JSON must be an array of measure definitions'
                }

            return self.bulk_create_measures(measures)

        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f"Invalid JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error importing measures: {e}")
            return {
                'success': False,
                'error': str(e)
            }
