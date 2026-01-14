"""
SVG Operations Handler
Unified handler for all SVG template operations

Operations:
- list_templates: List templates with optional category filter
- get_template: Get full template details
- preview_template: Get static SVG preview
- generate_measure: Generate DAX code from template
- inject_measure: Create measure directly in model
- list_categories: List all template categories
- search_templates: Search templates by keyword
- validate_svg: Validate SVG for Power BI compatibility
- create_custom: Build custom SVG measure from scratch
"""
from typing import Dict, Any, List
import logging
import re

from core.operations.base_operations import BaseOperationsHandler
from core.validation.param_validators import validate_required, validate_required_params
from core.validation.manager_decorators import get_manager_or_error
from core.svg.template_database import TemplateDatabase
from core.svg.template_engine import DAXGenerator
from core.svg.svg_validator import SVGValidator
from core.svg.parameter_resolver import ContextAwareResolver

logger = logging.getLogger(__name__)


class SVGOperationsHandler(BaseOperationsHandler):
    """Handles all SVG template operations"""

    def __init__(self):
        super().__init__("svg_operations")

        # Initialize template database and engine
        self.template_db = TemplateDatabase()
        self.generator = DAXGenerator(self.template_db)
        self.validator = SVGValidator()

        # Register all operations
        self.register_operation('list_templates', self._list_templates)
        self.register_operation('get_template', self._get_template)
        self.register_operation('preview_template', self._preview_template)
        self.register_operation('generate_measure', self._generate_measure)
        self.register_operation('inject_measure', self._inject_measure)
        self.register_operation('list_categories', self._list_categories)
        self.register_operation('search_templates', self._search_templates)
        self.register_operation('validate_svg', self._validate_svg)
        self.register_operation('create_custom', self._create_custom)

        logger.info(f"SVGOperationsHandler initialized with {self.template_db.get_template_count()} templates")

    def _list_templates(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available templates with optional category filter"""
        category = args.get('category')
        complexity = args.get('complexity')

        if complexity:
            templates = self.template_db.get_templates_by_complexity(complexity)
        else:
            templates = self.template_db.list_templates(category)

        return {
            'success': True,
            'templates': templates,
            'count': len(templates),
            'category_filter': category,
            'complexity_filter': complexity
        }

    def _get_template(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get full template details including parameters"""
        template_id = args.get('template_id')
        if error := validate_required(template_id, 'template_id', 'get_template'):
            return error

        template = self.template_db.get_template(template_id)
        if not template:
            return {
                'success': False,
                'error': f'Template not found: {template_id}',
                'suggestion': 'Use list_templates operation to see available templates'
            }

        # Build response with template details
        result = {
            'success': True,
            'template': {
                'template_id': template.template_id,
                'name': template.name,
                'category': template.category,
                'subcategory': template.subcategory,
                'description': template.description,
                'complexity': template.complexity,
                'parameters': [p.to_dict() for p in template.parameters],
                'supported_visuals': template.supported_visuals,
                'tags': template.tags,
                'source': template.source,
                'version': template.version
            }
        }

        # Add context-aware suggestions if connected and requested
        if args.get('context_aware', True):
            qe = get_manager_or_error('query_executor')
            if not isinstance(qe, dict):  # Not an error response
                try:
                    resolver = ContextAwareResolver(qe)
                    suggestions = resolver.suggest_parameters_for_template(
                        template_id,
                        [p.to_dict() for p in template.parameters]
                    )
                    if suggestions:
                        result['parameter_suggestions'] = suggestions
                except Exception as e:
                    logger.warning(f"Could not generate suggestions: {e}")

        return result

    def _preview_template(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get static SVG preview of template"""
        template_id = args.get('template_id')
        if error := validate_required(template_id, 'template_id', 'preview_template'):
            return error

        template = self.template_db.get_template(template_id)
        if not template:
            return {
                'success': False,
                'error': f'Template not found: {template_id}'
            }

        return {
            'success': True,
            'template_id': template_id,
            'name': template.name,
            'preview_svg': template.preview_svg,
            'preview_data_uri': f"data:image/svg+xml;utf8,{template.preview_svg}",
            'supported_visuals': template.supported_visuals,
            'note': 'This is a static preview. Generated measures will be dynamic based on your data.'
        }

    def _generate_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate DAX measure from template"""
        template_id = args.get('template_id')
        parameters = args.get('parameters', {})

        if error := validate_required(template_id, 'template_id', 'generate_measure'):
            return error

        template = self.template_db.get_template(template_id)
        if not template:
            return {
                'success': False,
                'error': f'Template not found: {template_id}'
            }

        # Validate parameters before generation
        param_validation = self.generator.validate_parameters(template, parameters)
        if not param_validation.get('valid'):
            missing = param_validation.get('missing', [])
            invalid = param_validation.get('invalid', [])
            error_parts = []
            if missing:
                error_parts.append(f"Missing required: {', '.join(missing)}")
            if invalid:
                error_parts.append(f"Invalid: {'; '.join(invalid)}")
            return {
                'success': False,
                'error': 'Parameter validation failed: ' + '. '.join(error_parts),
                'missing_parameters': missing,
                'invalid_parameters': invalid,
                'required_parameters': self.generator.get_required_parameters(template_id)
            }

        # Generate DAX
        try:
            dax_code, warnings = self.generator.generate(template_id, parameters)
            validation = self.validator.validate_dax_measure(dax_code)

            return {
                'success': True,
                'dax_code': dax_code,
                'validation': validation,
                'generation_warnings': warnings,
                'template_id': template_id,
                'usage_instructions': self.validator.get_usage_instructions()
            }
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error generating measure: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Generation failed: {str(e)}'
            }

    def _inject_measure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create measure directly in connected model via TOM"""
        # Get DAX injector with connection check
        dax_injector = get_manager_or_error('dax_injector')
        if isinstance(dax_injector, dict):
            return dax_injector

        template_id = args.get('template_id')
        parameters = args.get('parameters', {})
        table_name = args.get('table_name')
        measure_name = args.get('measure_name') or parameters.get('measure_name')

        if error := validate_required_params(
            (template_id, 'template_id'),
            (table_name, 'table_name'),
            (measure_name, 'measure_name'),
            operation='inject_measure'
        ):
            return error

        # Generate DAX first
        gen_result = self._generate_measure(args)
        if not gen_result.get('success'):
            return gen_result

        dax_code = gen_result['dax_code']

        # Extract just the expression (remove measure name assignment if present)
        expression = dax_code
        if '=' in dax_code:
            # Pattern: "MeasureName = \nVAR..." or "MeasureName =\nVAR..."
            match = re.match(r'^[^=]+=\s*', dax_code)
            if match:
                expression = dax_code[match.end():]

        # Inject using DAXInjector.upsert_measure
        try:
            result = dax_injector.upsert_measure(
                table_name=table_name,
                measure_name=measure_name,
                dax_expression=expression,
                description=f"SVG visual measure generated from template: {template_id}",
            )

            if result.get('success'):
                result['template_id'] = template_id
                result['dax_code'] = dax_code
                result['important_note'] = (
                    "IMPORTANT: Set the measure's Data Category to 'Image URL' in Power BI Desktop "
                    "(select measure > Measure tools > Data category > Image URL)"
                )
                result['usage_instructions'] = self.validator.get_usage_instructions()

            return result

        except Exception as e:
            logger.error(f"Error injecting measure: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Injection failed: {str(e)}',
                'dax_code': dax_code,
                'fallback': 'You can manually create the measure using the dax_code provided'
            }

    def _list_categories(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all available categories with template counts"""
        categories = self.template_db.list_categories()
        total_templates = sum(c['template_count'] for c in categories)

        return {
            'success': True,
            'categories': categories,
            'total_templates': total_templates
        }

    def _search_templates(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search templates by keyword"""
        query = args.get('search_query', '')
        if error := validate_required(query, 'search_query', 'search_templates'):
            return error

        results = self.template_db.search_templates(query)
        return {
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        }

    def _validate_svg(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SVG code for Power BI compatibility"""
        svg_code = args.get('svg_code', '')
        if error := validate_required(svg_code, 'svg_code', 'validate_svg'):
            return error

        validation = self.validator.validate(svg_code)
        return {
            'success': True,
            'validation': validation,
            'recommendations': self._get_recommendations(validation)
        }

    def _create_custom(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Build custom SVG measure from scratch"""
        svg_code = args.get('svg_code', '')
        measure_name = args.get('measure_name', 'Custom SVG')
        dynamic_vars = args.get('dynamic_vars', {})

        if error := validate_required(svg_code, 'svg_code', 'create_custom'):
            return error

        # Validate the SVG
        validation = self.validator.validate(svg_code)
        if not validation.get('valid'):
            return {
                'success': False,
                'error': 'SVG validation failed',
                'validation': validation,
                'suggestion': 'Fix the issues listed and try again'
            }

        # Fix hex colors if needed
        fixed_svg = self.validator.fix_hex_colors(svg_code)

        # Build DAX measure
        if dynamic_vars:
            # Build VAR declarations for dynamic values
            var_declarations = []
            for var_name, var_expression in dynamic_vars.items():
                var_declarations.append(f"VAR _{var_name} = {var_expression}")
            var_section = '\n'.join(var_declarations) + '\n'
        else:
            var_section = ''

        # Escape quotes for DAX
        svg_for_dax = fixed_svg.replace('"', '""')

        dax_code = f'''{measure_name} =
{var_section}VAR _svg = "{svg_for_dax}"
RETURN "data:image/svg+xml;utf8," & _svg'''

        # Validate the complete measure
        measure_validation = self.validator.validate_dax_measure(dax_code)

        return {
            'success': True,
            'dax_code': dax_code,
            'validation': measure_validation,
            'usage_instructions': self.validator.get_usage_instructions()
        }

    def _get_recommendations(self, validation: Dict[str, Any]) -> List[str]:
        """Get recommendations based on validation results"""
        recommendations = []

        if not validation.get('valid'):
            recommendations.append("Fix all issues before using this SVG in Power BI")

        if validation.get('warnings'):
            for warning in validation['warnings']:
                if '%23' in warning:
                    recommendations.append(
                        "Use SVGValidator.fix_hex_colors() to automatically convert hex colors"
                    )
                    break

        if validation.get('character_count', 0) > 20000:
            recommendations.append(
                "Consider simplifying the SVG to reduce character count and improve performance"
            )

        if not recommendations:
            recommendations.append("SVG looks good for Power BI usage!")

        return recommendations
