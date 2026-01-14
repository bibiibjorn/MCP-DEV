"""
SVG Template Engine - DAX generation from templates

This module handles parameter substitution and DAX code generation
from SVG templates.
"""
import re
import logging
from typing import Dict, Any, List, Tuple, Optional

from core.svg.template_database import TemplateDatabase, SVGTemplate, SVGParameter

logger = logging.getLogger(__name__)


class DAXGenerator:
    """Generates DAX measures from SVG templates"""

    # Pattern for template placeholders: {{parameter_name}}
    PLACEHOLDER_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def __init__(self, template_db: TemplateDatabase):
        """
        Initialize DAX generator.

        Args:
            template_db: TemplateDatabase instance for template retrieval
        """
        self.template_db = template_db

    def generate(self, template_id: str, parameters: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Generate DAX code from template with parameters.

        Args:
            template_id: The template identifier
            parameters: Dictionary of parameter values

        Returns:
            Tuple of (dax_code, warnings_list)

        Raises:
            ValueError: If template not found or required parameters missing
        """
        template = self.template_db.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        warnings: List[str] = []

        # Apply defaults for missing optional parameters
        full_params = self._apply_defaults(template, parameters)

        # Validate parameters
        validation = self.validate_parameters(template, full_params)
        if not validation.get('valid'):
            missing = validation.get('missing', [])
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        # Add any validation warnings
        if validation.get('warnings'):
            warnings.extend(validation['warnings'])

        # Perform parameter substitution
        dax_code = self._substitute_parameters(template.dax_template, full_params)

        # Check for any remaining unsubstituted placeholders
        remaining = self.PLACEHOLDER_PATTERN.findall(dax_code)
        if remaining:
            warnings.append(f"Unsubstituted placeholders remain: {remaining}")

        return dax_code, warnings

    def validate_parameters(self, template: SVGTemplate, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against template requirements.

        Args:
            template: The SVGTemplate to validate against
            parameters: Dictionary of provided parameter values

        Returns:
            Dict with 'valid', 'missing', 'invalid', 'warnings' keys
        """
        missing: List[str] = []
        invalid: List[str] = []
        warnings: List[str] = []

        for param in template.parameters:
            value = parameters.get(param.name)

            # Check required parameters
            if param.required and value is None:
                missing.append(param.name)
                continue

            # Skip validation for missing optional parameters
            if value is None:
                continue

            # Type validation
            type_valid, type_warning = self._validate_parameter_type(param, value)
            if not type_valid:
                invalid.append(f"{param.name}: {type_warning}")
            elif type_warning:
                warnings.append(type_warning)

        return {
            'valid': len(missing) == 0 and len(invalid) == 0,
            'missing': missing,
            'invalid': invalid,
            'warnings': warnings
        }

    def _validate_parameter_type(self, param: SVGParameter, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a parameter value against its expected type.

        Returns:
            Tuple of (is_valid, warning_or_error_message)
        """
        param_type = param.type.lower()

        if param_type == 'measure':
            # Measures should be in [MeasureName] format
            if isinstance(value, str):
                if not (value.startswith('[') and value.endswith(']')):
                    return True, f"Parameter '{param.name}' should be in [MeasureName] format"
            return True, None

        elif param_type == 'column':
            # Columns should be in 'Table'[Column] or [Column] format
            if isinstance(value, str):
                if not ('[' in value and ']' in value):
                    return True, f"Parameter '{param.name}' should be in 'Table'[Column] or [Column] format"
            return True, None

        elif param_type == 'scalar':
            # Scalars should be numeric
            try:
                float(value)
                return True, None
            except (ValueError, TypeError):
                return False, f"Expected numeric value for '{param.name}', got: {type(value).__name__}"

        elif param_type == 'color':
            # Colors should be valid CSS color or %23 encoded hex
            if isinstance(value, str):
                # Check for common color formats
                if value.startswith('%23') or value.startswith('#'):
                    return True, None
                if value.startswith('rgb') or value.startswith('hsl'):
                    return True, None
                if value.lower() in self._get_named_colors():
                    return True, None
                # Could be a valid CSS color name we don't know
                return True, f"Color '{value}' may not be a valid CSS color"
            return False, f"Color parameter '{param.name}' should be a string"

        elif param_type == 'string':
            # Strings just need to be convertible to string
            return True, None

        # Unknown type, allow but warn
        return True, f"Unknown parameter type '{param_type}' for '{param.name}'"

    def _apply_defaults(self, template: SVGTemplate, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values for missing optional parameters.

        Args:
            template: The SVGTemplate with parameter definitions
            parameters: Provided parameter values

        Returns:
            Dictionary with defaults applied
        """
        result = dict(parameters)

        for param in template.parameters:
            if param.name not in result or result[param.name] is None:
                if param.default is not None:
                    result[param.name] = param.default

        return result

    def _substitute_parameters(self, template_content: str, parameters: Dict[str, Any]) -> str:
        """
        Replace {{placeholder}} with parameter values.

        Args:
            template_content: The template string with placeholders
            parameters: Dictionary of parameter values

        Returns:
            String with placeholders replaced
        """
        def replace_placeholder(match):
            param_name = match.group(1)
            value = parameters.get(param_name)
            if value is not None:
                return str(value)
            return match.group(0)  # Return original if no value

        return self.PLACEHOLDER_PATTERN.sub(replace_placeholder, template_content)

    def get_required_parameters(self, template_id: str) -> List[Dict[str, Any]]:
        """
        Get list of required parameters for a template.

        Args:
            template_id: The template identifier

        Returns:
            List of required parameter info dictionaries
        """
        template = self.template_db.get_template(template_id)
        if not template:
            return []

        return [
            param.to_dict()
            for param in template.parameters
            if param.required
        ]

    def get_all_parameters(self, template_id: str) -> List[Dict[str, Any]]:
        """
        Get all parameters for a template.

        Args:
            template_id: The template identifier

        Returns:
            List of all parameter info dictionaries
        """
        template = self.template_db.get_template(template_id)
        if not template:
            return []

        return [param.to_dict() for param in template.parameters]

    def preview_with_sample_values(self, template_id: str) -> Optional[str]:
        """
        Generate DAX code with sample values for preview.

        Args:
            template_id: The template identifier

        Returns:
            DAX code with sample values, or None if template not found
        """
        template = self.template_db.get_template(template_id)
        if not template:
            return None

        # Generate sample values based on parameter types
        sample_params = {}
        for param in template.parameters:
            if param.default is not None:
                sample_params[param.name] = param.default
            else:
                sample_params[param.name] = self._get_sample_value(param)

        try:
            dax_code, _ = self.generate(template_id, sample_params)
            return dax_code
        except ValueError:
            return None

    def _get_sample_value(self, param: SVGParameter) -> Any:
        """Get a sample value for a parameter based on its type"""
        param_type = param.type.lower()

        if param_type == 'measure':
            return '[Sample Measure]'
        elif param_type == 'column':
            return "'Table'[Column]"
        elif param_type == 'scalar':
            return 0.5
        elif param_type == 'color':
            return '%230EA5E9'  # Nice blue
        elif param_type == 'string':
            return param.name.replace('_', ' ').title()
        else:
            return 'sample_value'

    @staticmethod
    def _get_named_colors() -> set:
        """Get set of common CSS named colors"""
        return {
            'black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta',
            'gray', 'grey', 'orange', 'purple', 'pink', 'brown', 'gold', 'silver',
            'navy', 'teal', 'maroon', 'olive', 'lime', 'aqua', 'fuchsia',
            'transparent', 'currentcolor',
            # Tailwind-style colors
            'steelblue', 'tomato', 'coral', 'crimson', 'darkgreen', 'darkblue',
            'lightgray', 'lightgrey', 'darkgray', 'darkgrey', 'slategray', 'slategrey'
        }
