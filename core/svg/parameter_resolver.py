"""
Parameter Resolver - Context-aware parameter suggestions

This module provides intelligent parameter suggestions based on
the connected Power BI model's measures and columns.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ContextAwareResolver:
    """Resolves template parameters from connected model context"""

    def __init__(self, query_executor):
        """
        Initialize with query executor for model introspection.

        Args:
            query_executor: OptimizedQueryExecutor instance
        """
        self.qe = query_executor

    def suggest_measures(self, expected_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Suggest measures from connected model.

        Args:
            expected_type: Filter by measure type
                - 'percentage': Measures with % format or DIVIDE pattern
                - 'numeric': Any numeric measure
                - 'currency': Measures with currency format
                - None: All measures

        Returns:
            List of measure suggestions with reference format
        """
        try:
            result = self.qe.execute_info_query("MEASURES")
            if not result.get('success'):
                return []

            measures = result.get('rows', [])
            suggestions = []

            for measure in measures:
                name = measure.get('Name', measure.get('measure_name', ''))
                table = measure.get('Table', measure.get('table_name', ''))
                expression = measure.get('Expression', '')
                format_string = measure.get('FormatString', '')

                # Filter by expected type if specified
                if expected_type:
                    if expected_type == 'percentage':
                        if not self._is_percentage_measure(format_string, expression):
                            continue
                    elif expected_type == 'currency':
                        if not self._is_currency_measure(format_string):
                            continue
                    # 'numeric' includes all measures

                suggestions.append({
                    'name': name,
                    'table': table,
                    'reference': f'[{name}]',
                    'format': format_string or 'General',
                    'type_hint': self._infer_measure_type(format_string, expression)
                })

            return suggestions

        except Exception as e:
            logger.error(f"Error getting measure suggestions: {e}")
            return []

    def suggest_columns(self, expected_type: Optional[str] = None, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Suggest columns for template parameters.

        Args:
            expected_type: Filter by column data type
                - 'date': Date/DateTime columns
                - 'numeric': Numeric columns
                - 'text': Text columns
                - None: All columns
            table_name: Filter by specific table

        Returns:
            List of column suggestions
        """
        try:
            result = self.qe.execute_info_query("COLUMNS", table_name=table_name)
            if not result.get('success'):
                return []

            columns = result.get('rows', [])
            suggestions = []

            for column in columns:
                name = column.get('Name', column.get('column_name', ''))
                table = column.get('Table', column.get('table_name', ''))
                data_type = column.get('DataType', column.get('data_type', ''))

                # Skip calculated columns for some use cases
                is_calculated = column.get('IsCalculated', column.get('is_calculated', False))

                # Filter by expected type
                if expected_type:
                    if expected_type == 'date' and 'date' not in data_type.lower():
                        continue
                    elif expected_type == 'numeric' and not self._is_numeric_type(data_type):
                        continue
                    elif expected_type == 'text' and 'string' not in data_type.lower():
                        continue

                suggestions.append({
                    'name': name,
                    'table': table,
                    'reference': f"'{table}'[{name}]",
                    'data_type': data_type,
                    'is_calculated': is_calculated
                })

            return suggestions

        except Exception as e:
            logger.error(f"Error getting column suggestions: {e}")
            return []

    def calculate_scale_factors(self, measure_reference: str) -> Dict[str, Any]:
        """
        Calculate min/max scale factors for a measure.

        Executes MINX/MAXX style queries to determine data range.

        Args:
            measure_reference: The measure in [MeasureName] format

        Returns:
            Dict with min_value, max_value, suggested_thresholds
        """
        try:
            # Extract measure name from reference
            measure_name = measure_reference.strip('[]')

            # Try to get measure statistics through DMV or DAX query
            # This is a simplified version - actual implementation would
            # need to query the model appropriately
            return {
                'min_value': 0,
                'max_value': 1,
                'suggested_thresholds': {
                    'low': 0.33,
                    'high': 0.67
                },
                'note': 'Default scale factors. Adjust based on your data range.'
            }

        except Exception as e:
            logger.error(f"Error calculating scale factors: {e}")
            return {
                'min_value': 0,
                'max_value': 1,
                'error': str(e)
            }

    def suggest_parameters_for_template(self, template_id: str, template_params: List[Dict]) -> Dict[str, Any]:
        """
        Generate complete parameter suggestions for a template.

        Args:
            template_id: The template identifier
            template_params: List of parameter definitions from template

        Returns:
            Dict with parameter suggestions
        """
        suggestions = {}

        for param in template_params:
            param_name = param.get('name', '')
            param_type = param.get('type', 'string')

            if param_type == 'measure':
                # Suggest measures based on parameter name hints
                expected_type = self._infer_expected_type(param_name)
                measures = self.suggest_measures(expected_type)
                if measures:
                    suggestions[param_name] = {
                        'recommended': measures[0]['reference'] if measures else None,
                        'alternatives': [m['reference'] for m in measures[1:5]],
                        'reason': f"Measures matching '{expected_type or 'any'}' type"
                    }

            elif param_type == 'column':
                columns = self.suggest_columns()
                if columns:
                    suggestions[param_name] = {
                        'recommended': columns[0]['reference'] if columns else None,
                        'alternatives': [c['reference'] for c in columns[1:5]],
                        'reason': "Available columns in model"
                    }

            elif param_type == 'scalar':
                # For scalar parameters, suggest based on name patterns
                if 'threshold' in param_name.lower():
                    suggestions[param_name] = {
                        'recommended': param.get('default', 0.5),
                        'alternatives': [0.25, 0.5, 0.75, 1.0],
                        'reason': "Common threshold values"
                    }

            elif param_type == 'color':
                # Suggest semantic colors
                suggestions[param_name] = {
                    'recommended': param.get('default'),
                    'alternatives': self._get_color_suggestions(param_name),
                    'reason': "Semantic color based on parameter purpose"
                }

        return suggestions

    def _is_percentage_measure(self, format_string: str, expression: str) -> bool:
        """Check if measure appears to be a percentage"""
        format_lower = format_string.lower() if format_string else ''
        expr_upper = expression.upper() if expression else ''
        return '%' in format_lower or 'DIVIDE' in expr_upper or 'percent' in format_lower

    def _is_currency_measure(self, format_string: str) -> bool:
        """Check if measure appears to be currency"""
        format_lower = format_string.lower() if format_string else ''
        return any(c in format_lower for c in ['$', '€', '£', 'currency'])

    def _is_numeric_type(self, data_type: str) -> bool:
        """Check if data type is numeric"""
        numeric_types = ['int', 'decimal', 'double', 'float', 'currency', 'number']
        return any(nt in data_type.lower() for nt in numeric_types)

    def _infer_measure_type(self, format_string: str, expression: str) -> str:
        """Infer the measure type from format and expression"""
        if self._is_percentage_measure(format_string, expression):
            return 'percentage'
        if self._is_currency_measure(format_string):
            return 'currency'
        return 'numeric'

    def _infer_expected_type(self, param_name: str) -> Optional[str]:
        """Infer expected measure type from parameter name"""
        name_lower = param_name.lower()
        if any(hint in name_lower for hint in ['percent', 'pct', 'rate', 'ratio', 'margin']):
            return 'percentage'
        if any(hint in name_lower for hint in ['amount', 'revenue', 'cost', 'price', 'sales']):
            return 'currency'
        return None

    def _get_color_suggestions(self, param_name: str) -> List[str]:
        """Get color suggestions based on parameter name"""
        name_lower = param_name.lower()

        # Semantic color mappings
        if any(word in name_lower for word in ['good', 'success', 'positive', 'green']):
            return ['%2316A34A', '%2322C55E', '%2310B981']  # Greens
        if any(word in name_lower for word in ['bad', 'error', 'negative', 'red']):
            return ['%23DC2626', '%23EF4444', '%23F87171']  # Reds
        if any(word in name_lower for word in ['warning', 'caution', 'yellow', 'amber']):
            return ['%23F59E0B', '%23FBBF24', '%23FCD34D']  # Yellows/Ambers
        if any(word in name_lower for word in ['info', 'primary', 'blue']):
            return ['%230EA5E9', '%233B82F6', '%236366F1']  # Blues

        # Default palette
        return ['%230EA5E9', '%2316A34A', '%23F59E0B', '%23DC2626']
