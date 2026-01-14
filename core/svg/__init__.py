"""
SVG Visual Generation Module

This module provides SVG template management and DAX measure generation
for creating inline SVG visuals in Power BI.

Main components:
- TemplateDatabase: Loads and manages SVG templates from JSON files
- DAXGenerator: Generates DAX code from templates with parameter substitution
- SVGValidator: Validates SVG code for Power BI compatibility
- ContextAwareResolver: Suggests parameters from connected model context
- SVGOperationsHandler: Main operations handler for MCP tool
"""

from core.svg.template_database import (
    SVGParameter,
    SVGTemplate,
    TemplateDatabase,
)
from core.svg.template_engine import DAXGenerator
from core.svg.svg_validator import SVGValidator
from core.svg.svg_operations import SVGOperationsHandler

__all__ = [
    'SVGParameter',
    'SVGTemplate',
    'TemplateDatabase',
    'DAXGenerator',
    'SVGValidator',
    'SVGOperationsHandler',
]
