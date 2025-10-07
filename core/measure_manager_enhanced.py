"""
Enhanced Measure Manager with Detailed Property Support
Supports formatString, description, isHidden, newName similar to MCP Desktop
"""

from typing import Dict, Any, Optional
import json


class EnhancedMeasureManager:
    """
    Enhanced measure manager supporting detailed measure properties including
    formatString, description, isHidden, and rename operations
    """

    def __init__(self, dax_injector):
        """
        Initialize the enhanced measure manager

        Args:
            dax_injector: DAXInjector instance for TMSL operations
        """
        self.dax_injector = dax_injector

    def create_measure(self, table: str, measure: str, expression: str,
                      format_string: Optional[str] = None,
                      description: Optional[str] = None,
                      is_hidden: Optional[bool] = None,
                      display_folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new measure with detailed properties

        Args:
            table: Table name
            measure: Measure name
            expression: DAX expression
            format_string: Format string (e.g., "#,0", "0.00%")
            description: Measure description
            is_hidden: Whether the measure is hidden
            display_folder: Display folder path

        Returns:
            Result dictionary
        """
        try:
            # Get current model definition
            tmsl_result = self.dax_injector.query_executor.get_tmsl_definition()
            if not tmsl_result.get('success'):
                return {'success': False, 'error': 'Failed to get model definition'}

            model_def = tmsl_result['tmsl']['model']

            # Find the table
            target_table = None
            for tbl in model_def.get('tables', []):
                if tbl.get('name') == table:
                    target_table = tbl
                    break

            if not target_table:
                return {'success': False, 'error': f'Table {table} not found'}

            # Check if measure already exists
            if 'measures' not in target_table:
                target_table['measures'] = []

            for existing_measure in target_table['measures']:
                if existing_measure.get('name') == measure:
                    return {'success': False, 'error': f'Measure {measure} already exists. Use update_measure to modify.'}

            # Create new measure object
            new_measure = {
                'name': measure,
                'expression': expression
            }

            # Add optional properties
            if format_string is not None:
                new_measure['formatString'] = format_string

            if description is not None:
                new_measure['description'] = description

            if is_hidden is not None:
                new_measure['isHidden'] = is_hidden

            if display_folder is not None:
                new_measure['displayFolder'] = display_folder

            # Add measure to table
            target_table['measures'].append(new_measure)

            # Apply changes via TMSL
            tmsl_script = {
                "createOrReplace": {
                    "object": {
                        "database": model_def.get('name', 'SemanticModel')
                    },
                    "database": model_def
                }
            }

            result = self.dax_injector.execute_tmsl(json.dumps(tmsl_script))
            if result.get('success'):
                return {
                    'success': True,
                    'message': f'Measure {measure} created successfully',
                    'measure': measure,
                    'table': table,
                    'properties': {
                        'formatString': format_string,
                        'description': description,
                        'isHidden': is_hidden,
                        'displayFolder': display_folder
                    }
                }
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_measure(self, table: str, measure: str,
                      expression: Optional[str] = None,
                      format_string: Optional[str] = None,
                      description: Optional[str] = None,
                      is_hidden: Optional[bool] = None,
                      display_folder: Optional[str] = None,
                      new_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing measure with detailed properties

        Args:
            table: Table name
            measure: Current measure name
            expression: New DAX expression (optional)
            format_string: New format string (optional)
            description: New description (optional)
            is_hidden: New hidden status (optional)
            display_folder: New display folder (optional)
            new_name: New measure name for renaming (optional)

        Returns:
            Result dictionary
        """
        try:
            # Get current model definition
            tmsl_result = self.dax_injector.query_executor.get_tmsl_definition()
            if not tmsl_result.get('success'):
                return {'success': False, 'error': 'Failed to get model definition'}

            model_def = tmsl_result['tmsl']['model']

            # Find the table
            target_table = None
            for tbl in model_def.get('tables', []):
                if tbl.get('name') == table:
                    target_table = tbl
                    break

            if not target_table:
                return {'success': False, 'error': f'Table {table} not found'}

            # Find the measure
            target_measure = None
            for m in target_table.get('measures', []):
                if m.get('name') == measure:
                    target_measure = m
                    break

            if not target_measure:
                return {'success': False, 'error': f'Measure {measure} not found in table {table}'}

            # Update properties
            updated_properties = {}

            if expression is not None:
                target_measure['expression'] = expression
                updated_properties['expression'] = 'updated'

            if format_string is not None:
                target_measure['formatString'] = format_string
                updated_properties['formatString'] = format_string

            if description is not None:
                target_measure['description'] = description
                updated_properties['description'] = description

            if is_hidden is not None:
                target_measure['isHidden'] = is_hidden
                updated_properties['isHidden'] = is_hidden

            if display_folder is not None:
                target_measure['displayFolder'] = display_folder
                updated_properties['displayFolder'] = display_folder

            if new_name is not None:
                target_measure['name'] = new_name
                updated_properties['name'] = new_name

            # Apply changes via TMSL
            tmsl_script = {
                "createOrReplace": {
                    "object": {
                        "database": model_def.get('name', 'SemanticModel')
                    },
                    "database": model_def
                }
            }

            result = self.dax_injector.execute_tmsl(json.dumps(tmsl_script))
            if result.get('success'):
                return {
                    'success': True,
                    'message': f'Measure {measure} updated successfully',
                    'measure': new_name if new_name else measure,
                    'table': table,
                    'updated_properties': updated_properties
                }
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_measures_table(self, table_name: str = "_Measures") -> Dict[str, Any]:
        """
        Create a dedicated measures table for organizing measures

        Args:
            table_name: Name of the measures table (default: "_Measures")

        Returns:
            Result dictionary
        """
        try:
            # Get current model definition
            tmsl_result = self.dax_injector.query_executor.get_tmsl_definition()
            if not tmsl_result.get('success'):
                return {'success': False, 'error': 'Failed to get model definition'}

            model_def = tmsl_result['tmsl']['model']

            # Check if table already exists
            for tbl in model_def.get('tables', []):
                if tbl.get('name') == table_name:
                    return {'success': False, 'error': f'Table {table_name} already exists'}

            # Create new measures table
            new_table = {
                "name": table_name,
                "columns": [
                    {
                        "name": "_MeasureHelper",
                        "dataType": "int64",
                        "isHidden": True,
                        "sourceColumn": "_MeasureHelper"
                    }
                ],
                "partitions": [
                    {
                        "name": "Partition",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": "#table(type table[_MeasureHelper = Int64.Type], {{1}})"
                        }
                    }
                ],
                "measures": [],
                "isHidden": False
            }

            # Add table to model
            if 'tables' not in model_def:
                model_def['tables'] = []
            model_def['tables'].append(new_table)

            # Apply changes via TMSL
            tmsl_script = {
                "createOrReplace": {
                    "object": {
                        "database": model_def.get('name', 'SemanticModel')
                    },
                    "database": model_def
                }
            }

            result = self.dax_injector.execute_tmsl(json.dumps(tmsl_script))
            if result.get('success'):
                return {
                    'success': True,
                    'message': f'Measures table {table_name} created successfully',
                    'table_name': table_name,
                    'description': 'Dedicated table for organizing measures without data dependencies'
                }
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_measure_properties(self, table: str, measure: str) -> Dict[str, Any]:
        """
        Get detailed properties of a measure

        Args:
            table: Table name
            measure: Measure name

        Returns:
            Measure properties dictionary
        """
        try:
            # Use INFO.MEASURES() to get all measure properties
            query = f"""
            EVALUATE
            FILTER(
                INFO.VIEW.MEASURES(),
                [Table] = "{table}" && [Name] = "{measure}"
            )
            """
            result = self.dax_injector.query_executor.validate_and_execute_dax(query)

            if result.get('success') and result.get('rows'):
                measure_props = result['rows'][0]
                return {
                    'success': True,
                    'table': table,
                    'measure': measure,
                    'properties': measure_props
                }
            else:
                return {'success': False, 'error': f'Measure {measure} not found in table {table}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}
