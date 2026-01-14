# Power BI DAX SVG Visuals - Technical Specification

## Executive Summary

This document provides a comprehensive technical specification for implementing inline DAX SVG visual generation tools within the MCP-PowerBi-Finvision server. The solution enables AI-assisted creation of dynamic, context-aware SVG visuals that can be directly injected into Power BI semantic models.

---

## Table of Contents

1. [Overview & Background](#1-overview--background)
2. [DAX SVG Fundamentals](#2-dax-svg-fundamentals)
3. [SVG Template Categories](#3-svg-template-categories)
4. [Template Database Design](#4-template-database-design)
5. [MCP Tool Architecture](#5-mcp-tool-architecture)
6. [Dynamic Data Integration](#6-dynamic-data-integration)
7. [Implementation Phases](#7-implementation-phases)
8. [API Reference](#8-api-reference)
9. [Code Examples Library](#9-code-examples-library)
10. [Testing & Validation](#10-testing--validation)

---

## 1. Overview & Background

### 1.1 What is DAX SVG?

DAX SVG is a technique where Scalable Vector Graphics (SVG) markup is embedded within DAX measure expressions. When configured correctly, Power BI renders these as visual images within supported visuals.

### 1.2 Key Benefits

- **No external dependencies**: No custom visuals, AppSource downloads, or external URLs
- **Full DAX integration**: Responds to filter context, slicers, and cross-filtering
- **Pixel-perfect control**: Complete control over colors, shapes, sizes, and positioning
- **Lightweight**: SVG is text-based and scales without quality loss
- **Universal support**: Works in tables, matrices, cards, slicers, and images

### 1.3 Supported Power BI Visuals (As of 2025)

| Visual Type | Support Level | Notes |
|-------------|---------------|-------|
| Table | Full | Best support, recommended |
| Matrix | Full | Best support, recommended |
| New Card | Good | May have sizing limitations |
| Button Slicer | Good | Works well for KPI indicators |
| List Slicer | Good | Works well for KPI indicators |
| Image | Full | Great for standalone SVGs |
| Scatterplot | Partial | Background images only |

### 1.4 Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| ~32K character limit per measure | Complex SVGs may hit limit | Simplify or split into multiple measures |
| Square aspect ratio default | Data bars may appear compressed | Adjust viewBox and visual settings |
| Tooltips show raw code | Poor UX without customization | Use custom tooltips or suppress |
| Firefox color encoding | `#` may not render correctly | Use `%23` URL encoding for hex colors |
| Large dataset overhead | Performance degradation | Limit row count, use aggregations |

---

## 2. DAX SVG Fundamentals

### 2.1 Core Syntax Pattern

Every DAX SVG measure follows this structure:

```dax
Measure Name =
VAR _dynamicValues = [Your Calculations]
VAR _svgContent = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
    <!-- SVG elements with dynamic values -->
</svg>"
RETURN "data:image/svg+xml;utf8," & _svgContent
```

### 2.2 Critical Requirements

1. **Prefix**: `"data:image/svg+xml;utf8,"` - Required for browser interpretation
2. **Namespace**: `xmlns='http://www.w3.org/2000/svg'` - Required in SVG tag
3. **Data Category**: Set to **"Image URL"** in measure properties
4. **Quote escaping**: Use single quotes `'` inside SVG, or escape double quotes as `""`

### 2.3 SVG Coordinate System

```
┌───────────────────────────────────────┐
│ viewBox="0 0 width height"            │
│                                       │
│   (0,0) ─────────────────── (width,0) │
│     │                           │     │
│     │    SVG Drawing Area       │     │
│     │                           │     │
│   (0,height) ──────────── (width,height)
└───────────────────────────────────────┘
```

### 2.4 Essential SVG Elements

| Element | Purpose | Key Attributes |
|---------|---------|----------------|
| `<rect>` | Rectangles, bars | x, y, width, height, fill, stroke, rx (rounded) |
| `<circle>` | Circles, dots | cx, cy, r, fill, stroke |
| `<line>` | Lines, connectors | x1, y1, x2, y2, stroke, stroke-width |
| `<path>` | Complex shapes, arcs | d (path data), fill, stroke |
| `<polyline>` | Connected lines | points, fill, stroke |
| `<polygon>` | Closed shapes | points, fill |
| `<text>` | Labels, values | x, y, font-family, font-size, fill, text-anchor |
| `<g>` | Grouping | transform |

### 2.5 Color Encoding for Cross-Browser Compatibility

```dax
// Standard hex (may fail in Firefox)
VAR _color = "#448FD6"

// URL-encoded hex (recommended)
VAR _color = "%23448FD6"

// Named colors (always safe)
VAR _color = "steelblue"

// RGB (always safe)
VAR _color = "rgb(68,143,214)"

// HSL (supported, great for gradients)
VAR _color = "hsl(210,65%,55%)"
```

---

## 3. SVG Template Categories

### 3.1 Category Overview

```
SVG Templates
├── KPI Indicators
│   ├── Traffic Lights (circles)
│   ├── Status Dots (filled/outline)
│   ├── Directional Arrows (up/down/flat)
│   ├── Rating Stars (1-5)
│   ├── Checkmarks & Crosses
│   └── Custom Status Icons
│
├── Sparklines & Mini Charts
│   ├── Line Sparklines
│   ├── Area Sparklines (with gradient)
│   ├── Bar Sparklines (vertical/horizontal)
│   ├── Win/Loss Charts
│   └── Dot Plots
│
├── Gauges & Progress
│   ├── Linear Progress Bars
│   ├── Circular/Radial Gauges
│   ├── Donut Charts
│   ├── Speedometer Gauges
│   └── Battery Indicators
│
├── Data Bars & Comparisons
│   ├── Simple Data Bars
│   ├── Variance Bars (positive/negative)
│   ├── Bullet Charts
│   ├── Actual vs Target
│   └── Lollipop Charts
│
├── Heatmaps & Gradients
│   ├── Single-Color Gradients
│   ├── Multi-Color Gradients
│   ├── Diverging Scales
│   └── Cell Background Colors
│
└── Advanced
    ├── Waffle Charts
    ├── Pictograms
    ├── Timeline Indicators
    ├── Trend Arrows with Values
    └── Composite KPI Cards
```

### 3.2 Template Complexity Levels

| Level | Description | Example |
|-------|-------------|---------|
| **Basic** | Static shapes with conditional colors | Traffic light dot |
| **Intermediate** | Dynamic sizing based on values | Data bar, progress bar |
| **Advanced** | Multiple data points, calculations | Sparklines, bullet charts |
| **Complex** | Full charts with axes, labels | Bar charts, gauges with text |

---

## 4. Template Database Design

### 4.1 Database Schema

```json
{
  "templates": {
    "template_id": "string (unique)",
    "name": "string",
    "category": "string",
    "subcategory": "string",
    "description": "string",
    "complexity": "basic|intermediate|advanced|complex",
    "preview_svg": "string (static preview)",
    "dax_template": "string (DAX with placeholders)",
    "parameters": [
      {
        "name": "string",
        "type": "measure|column|scalar|color",
        "required": "boolean",
        "default": "any",
        "description": "string"
      }
    ],
    "supported_visuals": ["table", "matrix", "card", "slicer", "image"],
    "tags": ["string"],
    "source": "string (attribution)",
    "created_date": "ISO date",
    "version": "semver"
  }
}
```

### 4.2 File Structure

```
core/
└── svg/
    ├── __init__.py
    ├── template_database.py      # Template loading and management
    ├── template_engine.py        # DAX generation from templates
    ├── svg_validator.py          # SVG syntax validation
    ├── parameter_resolver.py     # Dynamic parameter resolution
    │
    ├── templates/
    │   ├── templates.json        # Main template database
    │   │
    │   ├── kpi/
    │   │   ├── traffic_lights.json
    │   │   ├── status_dots.json
    │   │   ├── arrows.json
    │   │   ├── stars.json
    │   │   └── checkmarks.json
    │   │
    │   ├── sparklines/
    │   │   ├── line_sparkline.json
    │   │   ├── area_sparkline.json
    │   │   ├── bar_sparkline.json
    │   │   └── win_loss.json
    │   │
    │   ├── gauges/
    │   │   ├── progress_bar.json
    │   │   ├── radial_gauge.json
    │   │   ├── donut.json
    │   │   └── battery.json
    │   │
    │   ├── databars/
    │   │   ├── simple_databar.json
    │   │   ├── variance_bar.json
    │   │   ├── bullet_chart.json
    │   │   └── lollipop.json
    │   │
    │   └── advanced/
    │       ├── waffle.json
    │       ├── timeline.json
    │       └── composite_kpi.json
    │
    └── udf/
        ├── svg_functions.json    # Reusable UDF templates
        └── calculation_groups.json
```

### 4.3 Template JSON Format Example

```json
{
  "template_id": "kpi_traffic_light_3",
  "name": "Three-State Traffic Light",
  "category": "kpi",
  "subcategory": "traffic_lights",
  "description": "Circle that changes color based on three threshold values (red/yellow/green)",
  "complexity": "basic",
  "preview_svg": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='green'/></svg>",
  "dax_template": "{{measure_name}} = \nVAR _value = {{value_measure}}\nVAR _threshold_low = {{threshold_low}}\nVAR _threshold_high = {{threshold_high}}\nVAR _color = \n    SWITCH(\n        TRUE(),\n        _value < _threshold_low, \"{{color_bad}}\",\n        _value < _threshold_high, \"{{color_warning}}\",\n        \"{{color_good}}\"\n    )\nVAR _svg = \"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='\" & _color & \"'/></svg>\"\nRETURN \"data:image/svg+xml;utf8,\" & _svg",
  "parameters": [
    {
      "name": "measure_name",
      "type": "string",
      "required": true,
      "description": "Name for the new SVG measure"
    },
    {
      "name": "value_measure",
      "type": "measure",
      "required": true,
      "description": "Measure to evaluate (e.g., [Profit Margin])"
    },
    {
      "name": "threshold_low",
      "type": "scalar",
      "required": true,
      "default": 0.5,
      "description": "Below this = bad (red)"
    },
    {
      "name": "threshold_high",
      "type": "scalar",
      "required": true,
      "default": 0.8,
      "description": "Above this = good (green)"
    },
    {
      "name": "color_bad",
      "type": "color",
      "required": false,
      "default": "%23DC2626",
      "description": "Color for bad state (red)"
    },
    {
      "name": "color_warning",
      "type": "color",
      "required": false,
      "default": "%23F59E0B",
      "description": "Color for warning state (yellow)"
    },
    {
      "name": "color_good",
      "type": "color",
      "required": false,
      "default": "%2316A34A",
      "description": "Color for good state (green)"
    }
  ],
  "supported_visuals": ["table", "matrix", "card", "slicer"],
  "tags": ["kpi", "conditional", "status", "traffic-light", "three-state"],
  "source": "Hat Full of Data / SQLBI patterns",
  "created_date": "2025-01-14",
  "version": "1.0.0"
}
```

---

## 5. MCP Tool Architecture

### 5.1 New Handler Module

Create a new handler at `server/handlers/svg_handler.py`:

```python
"""
SVG Operations Handler
Unified handler for SVG template operations
"""
from typing import Dict, Any
import logging
from server.registry import ToolDefinition
from core.svg.svg_operations import SVGOperationsHandler

logger = logging.getLogger(__name__)

_svg_ops_handler = SVGOperationsHandler()

def handle_svg_operations(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle unified SVG operations"""
    return _svg_ops_handler.execute(args)

def register_svg_operations_handler(registry):
    """Register SVG operations handler"""

    tool = ToolDefinition(
        name="SVG_Visual_Operations",
        description="SVG visual generation: list templates, preview, generate DAX measures, inject into model. Creates inline DAX SVG visuals for KPIs, sparklines, gauges, data bars.",
        handler=handle_svg_operations,
        input_schema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "list_templates",
                        "get_template",
                        "preview_template",
                        "generate_measure",
                        "inject_measure",
                        "list_categories",
                        "search_templates",
                        "validate_svg",
                        "create_custom"
                    ],
                    "description": "Operation to perform"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category (kpi, sparklines, gauges, databars, advanced)"
                },
                "template_id": {
                    "type": "string",
                    "description": "Template ID for get/preview/generate operations"
                },
                "parameters": {
                    "type": "object",
                    "description": "Template parameters for generation"
                },
                "table_name": {
                    "type": "string",
                    "description": "Target table for inject operation"
                },
                "measure_name": {
                    "type": "string",
                    "description": "Name for the generated measure"
                },
                "search_query": {
                    "type": "string",
                    "description": "Search term for template search"
                },
                "svg_code": {
                    "type": "string",
                    "description": "SVG code for validation or custom creation"
                },
                "context_aware": {
                    "type": "boolean",
                    "description": "Use connected model context for parameter suggestions",
                    "default": true
                }
            },
            "required": ["operation"]
        },
        category="visualization",
        sort_order=50
    )

    registry.register(tool)
```

### 5.2 Core Operations Module

Create `core/svg/svg_operations.py`:

```python
"""
SVG Operations Handler
Core logic for SVG template operations
"""
from typing import Dict, Any, List, Optional
import json
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SVGTemplate:
    template_id: str
    name: str
    category: str
    subcategory: str
    description: str
    complexity: str
    preview_svg: str
    dax_template: str
    parameters: List[Dict[str, Any]]
    supported_visuals: List[str]
    tags: List[str]
    source: str
    version: str

class TemplateDatabase:
    """Manages SVG template loading and retrieval"""

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self._templates: Dict[str, SVGTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Load all templates from JSON files"""
        # Implementation loads from templates/*.json
        pass

    def list_templates(self, category: Optional[str] = None) -> List[Dict]:
        """List available templates with optional category filter"""
        pass

    def get_template(self, template_id: str) -> Optional[SVGTemplate]:
        """Get a specific template by ID"""
        pass

    def search_templates(self, query: str) -> List[Dict]:
        """Search templates by name, description, or tags"""
        pass

class DAXGenerator:
    """Generates DAX measures from templates"""

    def __init__(self, template_db: TemplateDatabase):
        self.template_db = template_db

    def generate(self, template_id: str, parameters: Dict[str, Any]) -> str:
        """Generate DAX code from template with parameters"""
        template = self.template_db.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        dax_code = template.dax_template
        for param_name, param_value in parameters.items():
            placeholder = "{{" + param_name + "}}"
            dax_code = dax_code.replace(placeholder, str(param_value))

        return dax_code

    def validate_parameters(self, template_id: str, parameters: Dict) -> Dict:
        """Validate parameters against template requirements"""
        pass

class SVGValidator:
    """Validates SVG syntax and Power BI compatibility"""

    @staticmethod
    def validate(svg_code: str) -> Dict[str, Any]:
        """Validate SVG code for Power BI compatibility"""
        issues = []
        warnings = []

        # Check for required namespace
        if "xmlns='http://www.w3.org/2000/svg'" not in svg_code:
            issues.append("Missing SVG namespace declaration")

        # Check for double quotes (should use single quotes)
        if '"' in svg_code and "'" not in svg_code:
            warnings.append("Consider using single quotes for easier DAX embedding")

        # Check for Firefox-incompatible color codes
        if "#" in svg_code and "%23" not in svg_code:
            warnings.append("Use %23 instead of # for hex colors (Firefox compatibility)")

        # Check approximate length
        if len(svg_code) > 25000:
            warnings.append(f"SVG length ({len(svg_code)}) approaching 32K limit")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "character_count": len(svg_code)
        }

class SVGOperationsHandler:
    """Main handler for SVG operations"""

    def __init__(self):
        templates_path = Path(__file__).parent / "templates"
        self.template_db = TemplateDatabase(templates_path)
        self.generator = DAXGenerator(self.template_db)
        self.validator = SVGValidator()

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SVG operation based on args"""
        operation = args.get("operation")

        operations = {
            "list_templates": self._list_templates,
            "get_template": self._get_template,
            "preview_template": self._preview_template,
            "generate_measure": self._generate_measure,
            "inject_measure": self._inject_measure,
            "list_categories": self._list_categories,
            "search_templates": self._search_templates,
            "validate_svg": self._validate_svg,
            "create_custom": self._create_custom
        }

        handler = operations.get(operation)
        if not handler:
            return {"success": False, "error": f"Unknown operation: {operation}"}

        return handler(args)

    def _list_templates(self, args: Dict) -> Dict:
        """List available templates"""
        category = args.get("category")
        templates = self.template_db.list_templates(category)
        return {
            "success": True,
            "templates": templates,
            "count": len(templates)
        }

    def _generate_measure(self, args: Dict) -> Dict:
        """Generate DAX measure from template"""
        template_id = args.get("template_id")
        parameters = args.get("parameters", {})

        try:
            dax_code = self.generator.generate(template_id, parameters)
            validation = self.validator.validate(dax_code)

            return {
                "success": True,
                "dax_code": dax_code,
                "validation": validation,
                "usage_instructions": [
                    "1. Copy the DAX code to Power BI Desktop",
                    "2. Create a new measure with this code",
                    "3. Select the measure and set Data Category to 'Image URL'",
                    "4. Add the measure to a Table, Matrix, or Card visual"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Additional operation implementations...
```

### 5.3 Tool Operations Summary

| Operation | Description | Required Parameters |
|-----------|-------------|-------------------|
| `list_templates` | List all templates with optional category filter | category (optional) |
| `get_template` | Get full template details including parameters | template_id |
| `preview_template` | Get static SVG preview of template | template_id |
| `generate_measure` | Generate DAX code from template | template_id, parameters |
| `inject_measure` | Create measure directly in connected model | template_id, parameters, table_name |
| `list_categories` | List all available categories | none |
| `search_templates` | Search templates by keyword | search_query |
| `validate_svg` | Validate SVG code for Power BI | svg_code |
| `create_custom` | Create custom SVG from scratch | svg_code, measure_name |

---

## 6. Dynamic Data Integration

### 6.1 Context-Aware Parameter Resolution

When connected to a Power BI model, the MCP server can suggest and auto-fill parameters:

```python
class ContextAwareResolver:
    """Resolves template parameters from connected model"""

    def __init__(self, connection_manager):
        self.connection = connection_manager

    def suggest_measures(self, expected_type: str) -> List[Dict]:
        """Suggest measures based on expected type"""
        measures = self.connection.get_all_measures()

        suggestions = []
        for measure in measures:
            # Analyze DAX to determine measure type
            if expected_type == "percentage":
                if "%" in measure.get("format_string", "") or \
                   "DIVIDE" in measure.get("expression", ""):
                    suggestions.append({
                        "name": measure["name"],
                        "table": measure["table"],
                        "reference": f"[{measure['name']}]"
                    })
            elif expected_type == "numeric":
                # Any numeric measure
                suggestions.append({
                    "name": measure["name"],
                    "table": measure["table"],
                    "reference": f"[{measure['name']}]"
                })

        return suggestions

    def suggest_columns(self, expected_type: str) -> List[Dict]:
        """Suggest columns for categorization"""
        pass

    def calculate_scale_factors(self, measure_name: str) -> Dict:
        """Calculate appropriate min/max for scale parameters"""
        # Execute MINX/MAXX queries to determine data range
        pass
```

### 6.2 Filter Context Handling in Generated DAX

Templates should use appropriate DAX patterns for filter context:

```dax
// Pattern 1: Respect current filter context (default)
VAR _value = [My Measure]

// Pattern 2: Compare against all data (for percentage bars)
VAR _maxInAll = CALCULATE([My Measure], ALLSELECTED('Table'))
VAR _percentage = DIVIDE(_value, _maxInAll)

// Pattern 3: Row-level evaluation for sparklines
VAR _dataPoints =
    ADDCOLUMNS(
        SUMMARIZE('Date', 'Date'[Month]),
        "@Value", [My Measure]
    )

// Pattern 4: Compare across dimension (for heatmaps)
VAR _maxInRow =
    MAXX(
        ALLSELECTED('Category'),
        CALCULATE([My Measure])
    )
```

### 6.3 Dynamic Axis Scaling

For charts with multiple data points:

```dax
// Auto-scaling based on data range
VAR _allValues =
    SUMMARIZE('Table', 'Table'[Category], "@Val", [Measure])

VAR _minVal = MINX(_allValues, [@Val])
VAR _maxVal = MAXX(_allValues, [@Val])
VAR _range = _maxVal - _minVal

// Normalize to 0-100 scale for SVG viewBox
VAR _normalizedValue =
    DIVIDE(
        [Measure] - _minVal,
        _range
    ) * 100
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Core Infrastructure)

**Deliverables:**
- [ ] Template database schema and loader
- [ ] Basic template JSON files (10 templates)
- [ ] SVG validator module
- [ ] DAX generator with parameter substitution
- [ ] MCP handler registration

**Templates to Include:**
1. Traffic Light (3-state)
2. Status Dot (2-state)
3. Up/Down Arrow
4. Simple Progress Bar
5. Simple Data Bar
6. Bullet Chart (basic)
7. Line Sparkline
8. Star Rating (1-5)
9. Checkmark/Cross
10. Percentage Circle

### Phase 2: Expanded Library (30+ Templates)

**Deliverables:**
- [ ] Complete KPI indicator set (10 templates)
- [ ] Full sparkline collection (8 templates)
- [ ] Gauge/progress variants (8 templates)
- [ ] Data bar/comparison charts (10 templates)
- [ ] Advanced templates (5 templates)

**Additional Features:**
- [ ] Template preview generation
- [ ] Parameter validation
- [ ] Usage documentation per template

### Phase 3: Context-Aware Generation

**Deliverables:**
- [ ] Integration with connection manager
- [ ] Measure suggestion engine
- [ ] Automatic scale calculation
- [ ] PBIP model integration
- [ ] Direct measure injection via TOM

### Phase 4: Advanced Features

**Deliverables:**
- [ ] UDF template generation (DAX User-Defined Functions)
- [ ] Responsive SVG with CSS variables
- [ ] Multi-measure composite visuals
- [ ] Custom template creation wizard
- [ ] Template versioning and updates

### Phase 5: AI Enhancement

**Deliverables:**
- [ ] Natural language template selection
- [ ] AI-assisted parameter tuning
- [ ] Automatic color palette suggestions
- [ ] Best practice recommendations
- [ ] Performance optimization hints

---

## 8. API Reference

### 8.1 List Templates

```json
{
  "operation": "list_templates",
  "category": "kpi"
}
```

**Response:**
```json
{
  "success": true,
  "templates": [
    {
      "template_id": "kpi_traffic_light_3",
      "name": "Three-State Traffic Light",
      "category": "kpi",
      "complexity": "basic",
      "description": "Circle that changes color based on thresholds"
    }
  ],
  "count": 10
}
```

### 8.2 Generate Measure

```json
{
  "operation": "generate_measure",
  "template_id": "kpi_traffic_light_3",
  "parameters": {
    "measure_name": "Status Indicator",
    "value_measure": "[Profit Margin]",
    "threshold_low": 0.1,
    "threshold_high": 0.25,
    "color_bad": "%23DC2626",
    "color_warning": "%23F59E0B",
    "color_good": "%2316A34A"
  }
}
```

**Response:**
```json
{
  "success": true,
  "dax_code": "Status Indicator = \nVAR _value = [Profit Margin]\n...",
  "validation": {
    "valid": true,
    "issues": [],
    "warnings": [],
    "character_count": 524
  },
  "usage_instructions": [...]
}
```

### 8.3 Inject Measure

```json
{
  "operation": "inject_measure",
  "template_id": "kpi_traffic_light_3",
  "parameters": {...},
  "table_name": "_Measures",
  "measure_name": "Status Indicator"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Measure 'Status Indicator' created in table '_Measures'",
  "measure_details": {
    "name": "Status Indicator",
    "table": "_Measures",
    "data_category": "ImageUrl",
    "expression_length": 524
  }
}
```

### 8.4 Context-Aware Suggestions

```json
{
  "operation": "generate_measure",
  "template_id": "databar_variance",
  "context_aware": true,
  "parameters": {
    "measure_name": "Sales Variance Bar"
  }
}
```

**Response includes suggestions:**
```json
{
  "success": true,
  "parameter_suggestions": {
    "value_measure": {
      "recommended": "[Total Sales]",
      "alternatives": ["[Revenue]", "[Net Sales]", "[Gross Sales]"],
      "reason": "Numeric measures detected in model"
    },
    "comparison_measure": {
      "recommended": "[Total Sales LY]",
      "alternatives": ["[Budget Sales]", "[Target]"],
      "reason": "Related measures with similar naming patterns"
    }
  },
  "scale_suggestions": {
    "min_value": -15000,
    "max_value": 50000,
    "reason": "Based on current data range in model"
  }
}
```

---

## 9. Code Examples Library

### 9.1 KPI Indicators

#### Traffic Light (3-State)

```dax
Traffic Light =
VAR _value = [Profit Margin]
VAR _color =
    SWITCH(
        TRUE(),
        _value < 0.1, "%23DC2626",  -- Red
        _value < 0.25, "%23F59E0B", -- Yellow
        "%2316A34A"                  -- Green
    )
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
    <circle cx='50' cy='50' r='40' fill='" & _color & "'/>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Directional Arrow

```dax
Trend Arrow =
VAR _growth = [YoY Growth %]
VAR _upArrow = "<path d='M50 10 L90 70 L65 70 L65 90 L35 90 L35 70 L10 70 Z' fill='%2316A34A'/>"
VAR _downArrow = "<path d='M50 90 L90 30 L65 30 L65 10 L35 10 L35 30 L10 30 Z' fill='%23DC2626'/>"
VAR _flatArrow = "<rect x='10' y='40' width='80' height='20' fill='%236B7280'/>"
VAR _arrow =
    SWITCH(
        TRUE(),
        _growth > 0.01, _upArrow,
        _growth < -0.01, _downArrow,
        _flatArrow
    )
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    & _arrow &
"</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Star Rating

```dax
Star Rating =
VAR _rating = ROUND([Average Score], 0)
VAR _fullStar = "<polygon points='12,2 15,8 22,9 17,14 18,21 12,17 6,21 7,14 2,9 9,8' fill='%23FBBF24' transform='translate({{x}},0)'/>"
VAR _emptyStar = "<polygon points='12,2 15,8 22,9 17,14 18,21 12,17 6,21 7,14 2,9 9,8' fill='%23E5E7EB' transform='translate({{x}},0)'/>"
VAR _stars =
    SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(
        IF(_rating >= 1, _fullStar, _emptyStar) &
        IF(_rating >= 2, _fullStar, _emptyStar) &
        IF(_rating >= 3, _fullStar, _emptyStar) &
        IF(_rating >= 4, _fullStar, _emptyStar) &
        IF(_rating >= 5, _fullStar, _emptyStar),
        "{{x}}", "0", 1), "{{x}}", "24", 1), "{{x}}", "48", 1), "{{x}}", "72", 1), "{{x}}", "96", 1)
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 24'>"
    & _stars &
"</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

### 9.2 Sparklines

#### Line Sparkline

```dax
Sales Sparkline =
VAR _lineColor = "%230EA5E9"
VAR _minDate = MIN('Date'[Date])
VAR _maxDate = MAX('Date'[Date])
VAR _values =
    ADDCOLUMNS(
        SUMMARIZE('Date', 'Date'[Date]),
        "@Value", [Total Sales]
    )
VAR _minVal = MINX(_values, [@Value])
VAR _maxVal = MAXX(_values, [@Value])
VAR _dataPoints =
    ADDCOLUMNS(
        _values,
        "@X", INT(100 * DIVIDE('Date'[Date] - _minDate, _maxDate - _minDate)),
        "@Y", 100 - INT(100 * DIVIDE([@Value] - _minVal, _maxVal - _minVal))
    )
VAR _points = CONCATENATEX(_dataPoints, [@X] & "," & [@Y], " ", [Date])
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
    <polyline
        fill='none'
        stroke='" & _lineColor & "'
        stroke-width='2'
        points='" & _points & "'/>
</svg>"
RETURN
IF(
    HASONEVALUE('Category'[Category]),
    "data:image/svg+xml;utf8," & _svg,
    BLANK()
)
```

#### Area Sparkline with Gradient

```dax
Area Sparkline =
VAR _fillColor = "%230EA5E9"
VAR _values =
    ADDCOLUMNS(
        SUMMARIZE('Date', 'Date'[Month]),
        "@Value", [Total Sales]
    )
VAR _minVal = MINX(_values, [@Value])
VAR _maxVal = MAXX(_values, [@Value])
VAR _normalized =
    ADDCOLUMNS(
        _values,
        "@X", (RANKX(_values, [Month], , ASC) - 1) * (100 / (COUNTROWS(_values) - 1)),
        "@Y", 100 - INT(90 * DIVIDE([@Value] - _minVal, _maxVal - _minVal + 0.001))
    )
VAR _linePoints = CONCATENATEX(_normalized, [@X] & "," & [@Y], " ", [Month])
VAR _areaPoints = "0,100 " & _linePoints & " 100,100"
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
    <defs>
        <linearGradient id='grad' x1='0%' y1='0%' x2='0%' y2='100%'>
            <stop offset='0%' style='stop-color:" & _fillColor & ";stop-opacity:0.6'/>
            <stop offset='100%' style='stop-color:" & _fillColor & ";stop-opacity:0.1'/>
        </linearGradient>
    </defs>
    <polygon points='" & _areaPoints & "' fill='url(%23grad)'/>
    <polyline fill='none' stroke='" & _fillColor & "' stroke-width='2' points='" & _linePoints & "'/>
</svg>"
RETURN
IF(HASONEVALUE('Product'[Category]), "data:image/svg+xml;utf8," & _svg, BLANK())
```

### 9.3 Gauges & Progress

#### Linear Progress Bar

```dax
Progress Bar =
VAR _percentage = MIN([Completion %], 1)
VAR _barWidth = _percentage * 100
VAR _color =
    SWITCH(
        TRUE(),
        _percentage < 0.5, "%23DC2626",
        _percentage < 0.8, "%23F59E0B",
        "%2316A34A"
    )
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 20'>
    <rect x='0' y='0' width='100' height='20' rx='4' fill='%23E5E7EB'/>
    <rect x='0' y='0' width='" & _barWidth & "' height='20' rx='4' fill='" & _color & "'/>
    <text x='50' y='14' font-family='Segoe UI' font-size='12' fill='white' text-anchor='middle'>"
        & FORMAT(_percentage, "0%") &
    "</text>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Radial Gauge (Pie Chart Style)

```dax
Radial Gauge =
VAR _percentage = MIN([Achievement %], 0.9999)
VAR _circlePercent = 180 - (_percentage * 360)
VAR _shortDistance = IF(_circlePercent < 0, 1, 0)
VAR _radians = RADIANS(_circlePercent)
VAR _xEnd = SIN(_radians) * 0.8
VAR _yEnd = COS(_radians) * 0.8
VAR _fillColor =
    IF(_percentage >= 1, "%2316A34A",
    IF(_percentage >= 0.8, "%23F59E0B", "%23DC2626"))
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='-1 -1 2 2'>
    <path d='M 0 -0.8 A 0.8 0.8 0 1 1 " & SIN(RADIANS(-179.99))*0.8 & " " & COS(RADIANS(-179.99))*0.8 & " L 0 0 z' fill='%23E5E7EB'/>
    <path d='M 0 -0.8 A 0.8 0.8 0 " & _shortDistance & " 1 " & _xEnd & " " & _yEnd & " L 0 0 z' fill='" & _fillColor & "'/>
    <circle cx='0' cy='0' r='0.5' fill='white'/>
    <text x='0' y='0.1' font-family='Segoe UI' font-size='0.4' fill='%23374151' text-anchor='middle'>"
        & FORMAT(_percentage, "0%") &
    "</text>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Donut Chart

```dax
Donut Progress =
VAR _percentage = [Completion %]
VAR _circumference = 2 * PI() * 40
VAR _dashOffset = _circumference * (1 - _percentage)
VAR _color = IF(_percentage >= 0.8, "%2316A34A", IF(_percentage >= 0.5, "%23F59E0B", "%23DC2626"))
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
    <circle cx='50' cy='50' r='40' fill='none' stroke='%23E5E7EB' stroke-width='10'/>
    <circle cx='50' cy='50' r='40' fill='none' stroke='" & _color & "' stroke-width='10'
        stroke-dasharray='" & _circumference & "'
        stroke-dashoffset='" & _dashOffset & "'
        transform='rotate(-90 50 50)'/>
    <text x='50' y='55' font-family='Segoe UI' font-size='16' fill='%23374151' text-anchor='middle'>"
        & FORMAT(_percentage, "0%") &
    "</text>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

### 9.4 Data Bars & Comparisons

#### Simple Data Bar

```dax
Data Bar =
VAR _value = [Total Sales]
VAR _maxValue = CALCULATE([Total Sales], ALLSELECTED('Product'))
VAR _barWidth = DIVIDE(_value, _maxValue) * 100
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 150 30'>
    <rect x='0' y='5' width='" & _barWidth & "' height='20' fill='%230EA5E9' fill-opacity='0.7'/>
    <text x='5' y='20' font-family='Segoe UI' font-size='12' fill='%23374151'>"
        & FORMAT(_value, "#,##0") &
    "</text>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Variance Bar (Positive/Negative)

```dax
Variance Bar =
VAR _actual = [Total Sales]
VAR _target = [Target Sales]
VAR _variance = _actual - _target
VAR _variancePct = DIVIDE(_variance, _target)
VAR _maxVariance = 0.5  -- 50% max deviation
VAR _barLength = MIN(ABS(_variancePct) / _maxVariance, 1) * 45
VAR _isPositive = _variance >= 0
VAR _color = IF(_isPositive, "%2316A34A", "%23DC2626")
VAR _xStart = IF(_isPositive, 50, 50 - _barLength)
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 30'>
    <line x1='50' y1='0' x2='50' y2='30' stroke='%23D1D5DB' stroke-width='1'/>
    <rect x='" & _xStart & "' y='8' width='" & _barLength & "' height='14' fill='" & _color & "'/>
    <text x='" & IF(_isPositive, 96, 4) & "' y='20' font-family='Segoe UI' font-size='10' fill='" & _color & "' text-anchor='" & IF(_isPositive, "end", "start") & "'>"
        & FORMAT(_variancePct, "+0%;-0%") &
    "</text>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Bullet Chart

```dax
Bullet Chart =
VAR _actual = [Current Rate]
VAR _target = [Target Rate]
VAR _max = 1.1  -- 110% for scale
VAR _actualWidth = (_actual / _max) * 100
VAR _targetPos = (_target / _max) * 100
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 150 20'>
    <rect x='0' y='0' width='150' height='20' fill='%23E5E7EB'/>
    <rect x='0' y='4' width='" & _actualWidth & "' height='12' fill='%23374151'/>
    <rect x='" & _targetPos & "' y='0' width='2' height='20' fill='%23EF4444'/>
</svg>"
RETURN
IF(HASONEVALUE('Employee'[Name]), "data:image/svg+xml;utf8," & _svg, BLANK())
```

### 9.5 Advanced Templates

#### Timeline Indicator

```dax
Timeline =
VAR _actual = [Days to Deliver]
VAR _target = [Target Days]
VAR _svgWidth = 100
VAR _axisMax = _svgWidth / 2
VAR _isLate = _actual > _target
VAR _fillColor = IF(_isLate, "%23DC2626", "%230EA5E9")
VAR _strokeColor = IF(_isLate, "%23991B1B", "%230369A1")
VAR _actualPos = MIN(DIVIDE(_actual, _target) * _axisMax + 10, 95)
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 " & _svgWidth & " 24'>
    <line x1='10' y1='12' x2='" & _axisMax & "' y2='12' stroke='%23D1D5DB' stroke-width='2'/>
    <circle cx='10' cy='12' r='4' fill='white' stroke='%23D1D5DB'/>
    <line x1='" & _axisMax & "' y1='12' x2='" & _actualPos & "' y2='12' stroke='" & _strokeColor & "' stroke-width='3'/>
    <circle cx='" & _axisMax & "' cy='12' r='4' fill='%23F3F4F6' stroke='%23D1D5DB'/>
    <circle cx='" & _actualPos & "' cy='12' r='5' fill='" & _fillColor & "' stroke='" & _strokeColor & "'/>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

#### Composite KPI Card

```dax
KPI Card =
VAR _value = [Total Revenue]
VAR _target = [Target Revenue]
VAR _lastPeriod = [Revenue LY]
VAR _achievementPct = DIVIDE(_value, _target)
VAR _growthPct = DIVIDE(_value - _lastPeriod, _lastPeriod)
VAR _achievementColor = IF(_achievementPct >= 1, "%2316A34A", IF(_achievementPct >= 0.8, "%23F59E0B", "%23DC2626"))
VAR _growthArrow = IF(_growthPct >= 0, "&#9650;", "&#9660;")
VAR _growthColor = IF(_growthPct >= 0, "%2316A34A", "%23DC2626")
VAR _svg = "
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 60'>
    <!-- Value -->
    <text x='10' y='25' font-family='Segoe UI' font-size='20' font-weight='bold' fill='%23111827'>"
        & FORMAT(_value/1000000, "$#,##0.0M") &
    "</text>
    <!-- Achievement -->
    <rect x='10' y='35' width='60' height='8' rx='2' fill='%23E5E7EB'/>
    <rect x='10' y='35' width='" & MIN(_achievementPct, 1) * 60 & "' height='8' rx='2' fill='" & _achievementColor & "'/>
    <text x='75' y='42' font-family='Segoe UI' font-size='10' fill='" & _achievementColor & "'>"
        & FORMAT(_achievementPct, "0%") &
    "</text>
    <!-- Growth -->
    <text x='10' y='55' font-family='Segoe UI' font-size='11' fill='" & _growthColor & "'>"
        & _growthArrow & " " & FORMAT(ABS(_growthPct), "0.0%") & " vs LY" &
    "</text>
</svg>"
RETURN "data:image/svg+xml;utf8," & _svg
```

---

## 10. Testing & Validation

### 10.1 Unit Tests

```python
# tests/test_svg_operations.py

import pytest
from core.svg.svg_operations import SVGValidator, DAXGenerator

class TestSVGValidator:
    def test_valid_svg(self):
        svg = "<svg xmlns='http://www.w3.org/2000/svg'><circle cx='50' cy='50' r='40'/></svg>"
        result = SVGValidator.validate(svg)
        assert result["valid"] == True
        assert len(result["issues"]) == 0

    def test_missing_namespace(self):
        svg = "<svg><circle cx='50' cy='50' r='40'/></svg>"
        result = SVGValidator.validate(svg)
        assert result["valid"] == False
        assert "namespace" in result["issues"][0].lower()

    def test_color_warning(self):
        svg = "<svg xmlns='http://www.w3.org/2000/svg'><circle fill='#FF0000'/></svg>"
        result = SVGValidator.validate(svg)
        assert any("%23" in w for w in result["warnings"])

    def test_length_warning(self):
        svg = "<svg xmlns='http://www.w3.org/2000/svg'>" + "x" * 26000 + "</svg>"
        result = SVGValidator.validate(svg)
        assert any("32K" in w for w in result["warnings"])

class TestDAXGenerator:
    def test_parameter_substitution(self):
        template = "VAR _val = {{measure}}\nVAR _color = '{{color}}'"
        params = {"measure": "[Sales]", "color": "%23FF0000"}
        # Test implementation
        pass

    def test_missing_required_param(self):
        # Should raise error for missing required parameters
        pass
```

### 10.2 Integration Tests

```python
# tests/test_svg_integration.py

class TestSVGIntegration:
    def test_generate_and_validate_traffic_light(self):
        """Generate traffic light and validate output"""
        result = svg_handler.execute({
            "operation": "generate_measure",
            "template_id": "kpi_traffic_light_3",
            "parameters": {
                "measure_name": "Test Status",
                "value_measure": "[Profit Margin]",
                "threshold_low": 0.1,
                "threshold_high": 0.25
            }
        })

        assert result["success"] == True
        assert "data:image/svg+xml;utf8," in result["dax_code"]
        assert result["validation"]["valid"] == True

    def test_inject_measure_to_model(self):
        """Test direct injection to connected Power BI model"""
        # Requires active connection
        pass
```

### 10.3 Visual Testing Checklist

| Test Case | Verification |
|-----------|--------------|
| SVG renders in Table | Place measure in table, verify image displays |
| SVG renders in Matrix | Place measure in matrix values, verify image displays |
| SVG renders in Card | Use new card visual, verify image displays |
| Colors respond to data | Change underlying data, verify color changes |
| Sizes respond to data | Change underlying data, verify bar/gauge sizes change |
| Filter context works | Apply slicer, verify SVG updates |
| Cross-filter works | Click related visual, verify SVG updates |
| Tooltip is clean | Hover over SVG, verify no raw code in tooltip |
| Performance acceptable | 1000+ rows, verify no significant lag |

---

## Appendix A: Color Palette Reference

### Semantic Colors

| Purpose | Hex | URL-Encoded | RGB |
|---------|-----|-------------|-----|
| Success/Good | #16A34A | %2316A34A | rgb(22,163,74) |
| Warning | #F59E0B | %23F59E0B | rgb(245,158,11) |
| Error/Bad | #DC2626 | %23DC2626 | rgb(220,38,38) |
| Info/Neutral | #0EA5E9 | %230EA5E9 | rgb(14,165,233) |
| Background | #E5E7EB | %23E5E7EB | rgb(229,231,235) |
| Text Dark | #111827 | %23111827 | rgb(17,24,39) |
| Text Light | #6B7280 | %236B7280 | rgb(107,114,128) |

### Extended Palette (Tailwind-inspired)

```json
{
  "gray": {
    "50": "%23F9FAFB", "100": "%23F3F4F6", "200": "%23E5E7EB",
    "300": "%23D1D5DB", "400": "%239CA3AF", "500": "%236B7280",
    "600": "%234B5563", "700": "%23374151", "800": "%231F2937", "900": "%23111827"
  },
  "red": {
    "500": "%23EF4444", "600": "%23DC2626", "700": "%23B91C1C"
  },
  "green": {
    "500": "%2322C55E", "600": "%2316A34A", "700": "%2315803D"
  },
  "blue": {
    "500": "%233B82F6", "600": "%232563EB", "700": "%231D4ED8"
  },
  "yellow": {
    "400": "%23FACC15", "500": "%23EAB308", "600": "%23CA8A04"
  },
  "orange": {
    "500": "%23F97316", "600": "%23EA580C"
  }
}
```

---

## Appendix B: DAX Functions Reference

### Essential Functions for SVG Generation

| Function | Purpose | Example |
|----------|---------|---------|
| `CONCATENATE` | Join strings | `CONCATENATE("a", "b")` |
| `CONCATENATEX` | Iterate and join | `CONCATENATEX(Table, [X] & "," & [Y], " ")` |
| `FORMAT` | Format numbers | `FORMAT([Value], "0%")` |
| `DIVIDE` | Safe division | `DIVIDE([A], [B], 0)` |
| `SWITCH` | Multi-condition | `SWITCH(TRUE(), cond1, val1, ...)` |
| `IF` | Conditional | `IF([Value] > 0, "green", "red")` |
| `MIN/MAX` | Bounds | `MIN([Value], 1)` |
| `RADIANS` | Degree to radians | `RADIANS(180)` |
| `SIN/COS` | Trigonometry | `SIN(RADIANS(45))` |
| `HASONEVALUE` | Context check | `IF(HASONEVALUE('Table'[Col]), ...)` |
| `SELECTEDVALUE` | Get single value | `SELECTEDVALUE('Table'[Col])` |
| `ALLSELECTED` | Respect slicers | `CALCULATE([M], ALLSELECTED('Table'))` |

---

## Appendix C: Resources & Attribution

### Key Sources

- **SQLBI** - [Creating custom visuals in Power BI with DAX](https://www.sqlbi.com/articles/creating-custom-visuals-in-power-bi-with-dax/)
- **Kerry Kolosko** - [Sparklines Portfolio](https://kerrykolosko.com/portfolio/sparklines/)
- **Hat Full of Data** - [SVG in Power BI](https://hatfullofdata.blog/svg-in-power-bi-part-2/)
- **BIBB** - [DAX and UDF SVG Charts Guide](https://bibb.pro/post/dax-and-udf-svg-charts-power-bi-guide/)
- **Power of BI** - [Responsive SVG Charts](https://www.powerofbi.org/2025/11/24/responsive-svg-charts-in-power-bi-core-visuals/)
- **David Eldersveld** - [Sparkline DAX Gist](https://gist.github.com/deldersveld/62523ca8350ac97797131560cb317677)
- **Darren Gosbell** - [Custom Data Bars](https://darren.gosbell.com/2019/11/building-custom-data-bars-in-power-bi-using-svg-measures/)
- **Data Meerkat** - [Multi-Color Gradient DAX](https://datameerkat.com/multi-color-gradient-dax-power-bi)

### Community Contributors

- Kerry Kolosko
- David Eldersveld
- Reed Haven
- Darren Gosbell
- Marco Russo & Alberto Ferrari (SQLBI)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-14 | MCP Team | Initial specification |

---

*This document is part of the MCP-PowerBi-Finvision project.*
