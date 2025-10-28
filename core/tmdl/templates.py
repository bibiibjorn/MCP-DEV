"""
TMDL Template Library - Reusable TMDL patterns

Provides templates for:
- Calendar tables (Gregorian, fiscal, ISO 8601)
- Calculation groups (time intelligence, scenarios)
- Common measures
- Data model patterns
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class TemplateInfo:
    """Template metadata"""
    id: str
    name: str
    category: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class TmdlTemplate:
    """Complete TMDL template with content"""
    info: TemplateInfo
    tmdl_content: str

@dataclass
class ApplyResult:
    """Result of applying a template"""
    success: bool
    objects_created: int
    table_name: Optional[str] = None
    columns: List[str] = None
    measures: List[str] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.columns is None:
            self.columns = []
        if self.measures is None:
            self.measures = []
        if self.errors is None:
            self.errors = []


class TmdlTemplateLibrary:
    """
    Template library for common TMDL patterns

    Categories:
    - calendar: Calendar tables (Gregorian, fiscal, ISO 8601)
    - calculation_group: Calculation groups (time intelligence, scenarios)
    - measures: Common measure patterns
    - model_patterns: Data model patterns (bridge tables, SCDs)
    """

    def __init__(self):
        """Initialize template library"""
        self._templates: Dict[str, TmdlTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates"""
        # Calendar - Gregorian
        self._templates["calendar_gregorian"] = TmdlTemplate(
            info=TemplateInfo(
                id="calendar_gregorian",
                name="Gregorian Calendar Table",
                category="calendar",
                description="Standard calendar with Year, Quarter, Month, Week, Day",
                parameters={
                    "table_name": {"type": "string", "default": "Calendar"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"}
                }
            ),
            tmdl_content=self._get_gregorian_calendar_template()
        )

        # Calculation Group - Time Intelligence
        self._templates["calc_group_time_intel"] = TmdlTemplate(
            info=TemplateInfo(
                id="calc_group_time_intel",
                name="Time Intelligence Calculation Group",
                category="calculation_group",
                description="Common time intelligence calculations (YTD, QTD, MTD, PY, YoY%)",
                parameters={
                    "group_name": {"type": "string", "default": "Time Intelligence"},
                    "calendar_table": {"type": "string", "default": "Calendar"},
                    "date_column": {"type": "string", "default": "Date"}
                }
            ),
            tmdl_content=self._get_time_intel_calc_group_template()
        )

        # Common Measures - Basic Aggregations
        self._templates["measures_basic_agg"] = TmdlTemplate(
            info=TemplateInfo(
                id="measures_basic_agg",
                name="Basic Aggregation Measures",
                category="measures",
                description="SUM, AVERAGE, COUNT, MIN, MAX patterns",
                parameters={
                    "target_table": {"type": "string"},
                    "target_column": {"type": "string"},
                    "measure_prefix": {"type": "string", "default": ""}
                }
            ),
            tmdl_content=self._get_basic_agg_measures_template()
        )

        logger.info(f"Loaded {len(self._templates)} built-in templates")

    def list_templates(self, category: Optional[str] = None) -> List[TemplateInfo]:
        """
        List available templates

        Args:
            category: Filter by category (calendar, calculation_group, measures, model_patterns)

        Returns:
            List of template metadata
        """
        templates = []

        for template in self._templates.values():
            if category is None or template.info.category == category:
                templates.append(template.info)

        return templates

    def get_template(self, template_id: str) -> Optional[TmdlTemplate]:
        """
        Get template by ID

        Args:
            template_id: Template identifier

        Returns:
            TmdlTemplate or None if not found
        """
        return self._templates.get(template_id)

    def apply_template(
        self,
        tmdl_path: str,
        template_id: str,
        parameters: Dict[str, Any],
        merge_strategy: str = "fail_if_exists"
    ) -> ApplyResult:
        """
        Apply template to TMDL model

        Args:
            tmdl_path: Path to TMDL folder
            template_id: Template to apply
            parameters: Template parameters
            merge_strategy: "fail_if_exists", "skip_existing", or "overwrite"

        Returns:
            ApplyResult with operation details
        """
        result = ApplyResult(success=False, objects_created=0)

        try:
            template = self.get_template(template_id)
            if not template:
                result.errors.append(f"Template not found: {template_id}")
                return result

            # Validate parameters
            missing = self._validate_parameters(template.info.parameters, parameters)
            if missing:
                result.errors.append(f"Missing required parameters: {', '.join(missing)}")
                return result

            # Render template with parameters
            rendered_content = self._render_template(template.tmdl_content, parameters)

            # Write to TMDL folder
            path = Path(tmdl_path)
            if not path.exists():
                result.errors.append(f"TMDL path does not exist: {tmdl_path}")
                return result

            # Determine target file based on template category
            if template.info.category == "calendar":
                table_name = parameters.get("table_name", "Calendar")
                target_file = path / "tables" / f"{table_name}.tmdl"
                result.table_name = table_name
            elif template.info.category == "calculation_group":
                group_name = parameters.get("group_name", "TimeIntelligence")
                target_file = path / "tables" / f"{group_name}.tmdl"
                result.table_name = group_name
            else:
                result.errors.append(f"Unsupported template category: {template.info.category}")
                return result

            # Check merge strategy
            if target_file.exists():
                if merge_strategy == "fail_if_exists":
                    result.errors.append(f"File already exists: {target_file}")
                    return result
                elif merge_strategy == "skip_existing":
                    result.success = True
                    return result

            # Write file
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(rendered_content, encoding="utf-8")

            result.objects_created = 1
            result.success = True

            logger.info(f"Applied template {template_id} to {target_file}")

        except Exception as e:
            logger.error(f"Error applying template: {e}", exc_info=True)
            result.errors.append(f"Failed to apply template: {str(e)}")

        return result

    def create_custom_template(
        self,
        name: str,
        category: str,
        tmdl_objects: str,
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None
    ) -> TemplateInfo:
        """
        Create custom template from TMDL content

        Args:
            name: Template name
            category: Template category
            tmdl_objects: TMDL content
            description: Template description
            parameters: Template parameters

        Returns:
            TemplateInfo for the new template
        """
        template_id = name.lower().replace(" ", "_")

        template = TmdlTemplate(
            info=TemplateInfo(
                id=template_id,
                name=name,
                category=category,
                description=description,
                parameters=parameters or {}
            ),
            tmdl_content=tmdl_objects
        )

        self._templates[template_id] = template

        logger.info(f"Created custom template: {template_id}")

        return template.info

    def _validate_parameters(
        self,
        template_params: Dict[str, Any],
        provided_params: Dict[str, Any]
    ) -> List[str]:
        """Validate that required parameters are provided"""
        missing = []

        for param_name, param_def in template_params.items():
            if "default" not in param_def and param_name not in provided_params:
                missing.append(param_name)

        return missing

    def _render_template(self, template_content: str, parameters: Dict[str, Any]) -> str:
        """Render template with parameters"""
        rendered = template_content

        # Simple variable substitution {variable_name}
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def _get_gregorian_calendar_template(self) -> str:
        """Gregorian calendar table template"""
        return '''table '{table_name}'
\tlineageTag: calendar-table-gregorian

\tcolumn Date
\t\tdataType: dateTime
\t\tisKey: true
\t\tformatString: Short Date
\t\tlineageTag: date-column

\tcolumn Year
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: year-column
\t\tsummarizeBy: none

\tcolumn Quarter
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: quarter-column
\t\tsummarizeBy: none

\tcolumn Month
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: month-column
\t\tsummarizeBy: none

\tcolumn MonthName
\t\tdataType: string
\t\tlineageTag: monthname-column

\tcolumn DayOfWeek
\t\tdataType: int64
\t\tformatString: 0
\t\tlineageTag: dayofweek-column
\t\tsummarizeBy: none

\tpartition {table_name} = m
\t\tmode: import
\t\tsource =
\t\t\tlet
\t\t\t\tStartDate = #{start_date}#,
\t\t\t\tEndDate = #{end_date}#,
\t\t\t\tDays = Duration.Days(EndDate - StartDate) + 1,
\t\t\t\tCalendar = List.Dates(StartDate, Days, #duration(1,0,0,0)),
\t\t\t\tTable = Table.FromList(Calendar, Splitter.SplitByNothing()),
\t\t\t\tRenamed = Table.RenameColumns(Table,{{"Column1", "Date"}}),
\t\t\t\tYear = Table.AddColumn(Renamed, "Year", each Date.Year([Date]), Int64.Type),
\t\t\t\tQuarter = Table.AddColumn(Year, "Quarter", each Date.QuarterOfYear([Date]), Int64.Type),
\t\t\t\tMonth = Table.AddColumn(Quarter, "Month", each Date.Month([Date]), Int64.Type),
\t\t\t\tMonthName = Table.AddColumn(Month, "MonthName", each Date.MonthName([Date]), type text),
\t\t\t\tDayOfWeek = Table.AddColumn(MonthName, "DayOfWeek", each Date.DayOfWeek([Date]), Int64.Type)
\t\t\tin
\t\t\t\tDayOfWeek
'''

    def _get_time_intel_calc_group_template(self) -> str:
        """Time intelligence calculation group template"""
        return '''table '{group_name}'
\tlineageTag: calc-group-time-intel
\tcalculationGroup

\tcolumn Name
\t\tdataType: string
\t\tisDataTypeInferred: false
\t\tlineageTag: calc-item-name

\tcalculationItem MTD
\t\texpression: CALCULATE(SELECTEDMEASURE(), DATESMTD('{calendar_table}'[{date_column}]))
\t\tordinal: 0

\tcalculationItem YTD
\t\texpression: CALCULATE(SELECTEDMEASURE(), DATESYTD('{calendar_table}'[{date_column}]))
\t\tordinal: 1

\tcalculationItem PY
\t\texpression: CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('{calendar_table}'[{date_column}]))
\t\tordinal: 2

\tcalculationItem "YoY %"
\t\texpression:
\t\t\tVAR Current = SELECTEDMEASURE()
\t\t\tVAR PY = CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR('{calendar_table}'[{date_column}]))
\t\t\tRETURN DIVIDE(Current - PY, PY)
\t\tformatString: 0.0%;-0.0%;0.0%
\t\tordinal: 3
'''

    def _get_basic_agg_measures_template(self) -> str:
        """Basic aggregation measures template"""
        return '''// Add to {target_table} table

measure '{measure_prefix}Total {target_column}'
\texpression: SUM('{target_table}'[{target_column}])
\tformatString: #,0
\tdisplayFolder: Basic Aggregations

measure '{measure_prefix}Average {target_column}'
\texpression: AVERAGE('{target_table}'[{target_column}])
\tformatString: #,0.00
\tdisplayFolder: Basic Aggregations

measure '{measure_prefix}Count {target_column}'
\texpression: COUNT('{target_table}'[{target_column}])
\tformatString: #,0
\tdisplayFolder: Basic Aggregations

measure '{measure_prefix}Min {target_column}'
\texpression: MIN('{target_table}'[{target_column}])
\tformatString: #,0
\tdisplayFolder: Basic Aggregations

measure '{measure_prefix}Max {target_column}'
\texpression: MAX('{target_table}'[{target_column}])
\tformatString: #,0
\tdisplayFolder: Basic Aggregations
'''
