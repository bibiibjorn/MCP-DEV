"""
AI Model Exporter for MCP-PowerBi-Finvision
Exports complete Power BI model in AI-optimized JSON format for comprehensive analysis.

This module creates a unified, structured export of the entire Power BI model including:
- All measures with DAX expressions
- Measure dependencies (upstream/downstream)
- Tables and columns with metadata
- Sample data (configurable rows per table)
- Relationships with full details
- Calculation groups with calculation items
- Row-level security rules
- Best practice analysis results
- DAX pattern detection
- Column lineage (usage tracking)
"""

import json
import gzip
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to load AMO for TOM access
AMO_AVAILABLE = False
AMOServer = None

try:
    import clr  # type: ignore
    import os as _os

    script_dir = _os.path.dirname(_os.path.abspath(__file__))
    parent_dir = _os.path.dirname(script_dir)  # core/model -> core
    root_dir = _os.path.dirname(parent_dir)     # core -> root
    dll_folder = _os.path.join(root_dir, "lib", "dotnet")

    core_dll = _os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
    amo_dll = _os.path.join(dll_folder, "Microsoft.AnalysisServices.dll")
    tabular_dll = _os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")

    if _os.path.exists(core_dll):
        clr.AddReference(core_dll)  # type: ignore[attr-defined]
    if _os.path.exists(amo_dll):
        clr.AddReference(amo_dll)  # type: ignore[attr-defined]
    if _os.path.exists(tabular_dll):
        clr.AddReference(tabular_dll)  # type: ignore[attr-defined]

    from Microsoft.AnalysisServices.Tabular import Server as AMOServer  # type: ignore
    AMO_AVAILABLE = True
    logger.info("AMO available for AI model export")

except Exception as e:
    logger.warning(f"AMO not available for AI export: {e}")


class AIModelExporter:
    """Export Power BI models in AI-optimized JSON format."""

    def __init__(self, connection, query_executor=None, calculation_group_manager=None):
        """
        Initialize with ADOMD connection and optional managers.

        Args:
            connection: ADOMD connection object
            query_executor: QueryExecutor instance for DAX queries
            calculation_group_manager: CalculationGroupManager instance
        """
        self.connection = connection
        self.query_executor = query_executor
        self.calculation_group_manager = calculation_group_manager

    def export_for_ai(
        self,
        output_format: str = "json_gzip",
        sample_rows: int = 20,
        include_sample_data: bool = True,
        include_dependencies: bool = True,
        include_bpa_issues: bool = False,
        include_dax_patterns: bool = True,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export complete model analysis in AI-optimized format.

        Args:
            output_format: Format for export (json, json_gzip, markdown)
            sample_rows: Number of sample rows per table
            include_sample_data: Whether to include sample data
            include_dependencies: Whether to include dependency analysis
            include_bpa_issues: Whether to include best practice analysis
            include_dax_patterns: Whether to detect DAX patterns
            output_path: Optional custom output path

        Returns:
            Export result with file path and statistics
        """
        try:
            logger.info(f"Starting AI model export (format={output_format}, sample_rows={sample_rows})")
            start_time = datetime.now()

            # Build comprehensive model data
            model_data = self._build_model_data(
                sample_rows=sample_rows,
                include_sample_data=include_sample_data,
                include_dependencies=include_dependencies,
                include_bpa_issues=include_bpa_issues,
                include_dax_patterns=include_dax_patterns
            )

            if not model_data.get('success'):
                return model_data  # Return error

            # Determine output path
            if output_path is None:
                export_dir = os.path.join(os.getcwd(), 'exports', 'ai_exports')
                os.makedirs(export_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                model_name_safe = model_data['metadata']['model_name'].replace(' ', '_').replace('/', '_')

                if output_format == "json_gzip":
                    output_path = os.path.join(export_dir, f'{model_name_safe}_ai_{timestamp}.json.gz')
                elif output_format == "markdown":
                    output_path = os.path.join(export_dir, f'{model_name_safe}_ai_{timestamp}.md')
                else:  # json
                    output_path = os.path.join(export_dir, f'{model_name_safe}_ai_{timestamp}.json')
            else:
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

            # Export based on format
            if output_format == "markdown":
                file_size = self._export_markdown(model_data, output_path)
                compression_ratio = 1.0
            elif output_format == "json_gzip":
                uncompressed_size, file_size = self._export_json_gzip(model_data, output_path)
                compression_ratio = uncompressed_size / file_size if file_size > 0 else 1.0
            else:  # json
                file_size = self._export_json(model_data, output_path)
                compression_ratio = 1.0

            end_time = datetime.now()
            export_time = (end_time - start_time).total_seconds()

            logger.info(f"AI export completed: {output_path} ({file_size / 1024 / 1024:.2f} MB)")

            return {
                'success': True,
                'export_file': output_path,
                'file_size_mb': round(file_size / 1024 / 1024, 2),
                'compression_ratio': round(compression_ratio, 2),
                'export_time_seconds': round(export_time, 2),
                'format': output_format,
                'statistics': model_data['metadata']['statistics'],
                'message': f'Model exported to {output_path} ({file_size / 1024 / 1024:.2f} MB)'
            }

        except Exception as e:
            logger.error(f"AI export error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _build_model_data(
        self,
        sample_rows: int,
        include_sample_data: bool,
        include_dependencies: bool,
        include_bpa_issues: bool,
        include_dax_patterns: bool
    ) -> Dict[str, Any]:
        """Build comprehensive model data structure."""
        try:
            # Connect to TOM
            if not AMO_AVAILABLE:
                return {
                    'success': False,
                    'error': 'AMO not available. TOM connection required for comprehensive export.'
                }

            server = AMOServer()  # type: ignore[operator]
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            # Build metadata
            metadata = self._build_metadata(db, model)

            # Build model structure
            model_data = {
                'success': True,
                'metadata': metadata,
                'tables': self._build_tables(
                    model,
                    sample_rows=sample_rows if include_sample_data else 0,
                    include_dax_patterns=include_dax_patterns
                ),
                'relationships': self._build_relationships(model),
                'calculation_groups': self._build_calculation_groups(model),
                'roles': self._build_roles(model),
                'm_expressions': self._build_m_expressions(model)
            }

            # Add dependency graph if requested
            if include_dependencies:
                model_data['dependency_graph'] = self._build_dependency_graph(model_data)

            # Add BPA issues if requested
            if include_bpa_issues:
                model_data['best_practice_issues'] = self._build_bpa_issues()

            server.Disconnect()
            return model_data

        except Exception as e:
            logger.error(f"Error building model data: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _build_metadata(self, db, model) -> Dict[str, Any]:
        """Build metadata section with purpose detection."""
        # Count statistics
        table_count = len(model.Tables)
        measure_count = sum(len(table.Measures) for table in model.Tables)
        column_count = sum(len(table.Columns) for table in model.Tables)
        relationship_count = len(model.Relationships)

        # Count calculation groups
        calc_group_count = 0
        try:
            calc_group_count = sum(1 for table in model.Tables
                                  if hasattr(table, 'CalculationGroup') and table.CalculationGroup is not None)
        except Exception:
            pass

        metadata = {
            'export_version': '1.0.0',
            'export_timestamp': datetime.now().isoformat(),
            'source_file': db.Name,
            'compatibility_level': db.CompatibilityLevel,
            'model_name': model.Name if hasattr(model, 'Name') else db.Name,
            'culture': model.Culture if hasattr(model, 'Culture') else 'en-US',
            'exporter': 'MCP-PowerBi-Finvision AI Exporter',
            'statistics': {
                'table_count': table_count,
                'measure_count': measure_count,
                'column_count': column_count,
                'relationship_count': relationship_count,
                'calculation_group_count': calc_group_count
            }
        }

        # Add purpose detection heuristics
        try:
            purpose_info = self._detect_model_purpose(model)
            if purpose_info:
                metadata['purpose'] = purpose_info
        except Exception as e:
            logger.warning(f"Could not detect model purpose: {e}")

        return metadata

    def _build_tables(self, model, sample_rows: int, include_dax_patterns: bool) -> List[Dict[str, Any]]:
        """Build tables section with columns, measures, and sample data."""
        tables = []

        for table in model.Tables:
            # Skip calculation groups (they're in their own section)
            if hasattr(table, 'CalculationGroup') and table.CalculationGroup is not None:
                continue

            table_data = {
                'name': table.Name,
                'type': 'CalculatedTable' if hasattr(table, 'Source') and table.Source and 'calculatedTableExpression' in str(type(table.Source)) else 'Table',
                'is_hidden': table.IsHidden,
                'row_count': None,  # Will be populated if sample data is requested
                'data_category': str(table.DataCategory) if hasattr(table, 'DataCategory') else 'Uncategorized',
                'description': table.Description if hasattr(table, 'Description') and table.Description else None,
                'columns': self._build_columns(table),
                'measures': self._build_measures(table, include_dax_patterns),
                'hierarchies': self._build_hierarchies(table),
                'partitions': self._build_partitions(table)
            }

            # Add sample data if requested
            if sample_rows > 0:
                table_data['sample_data'] = self._get_sample_data(table.Name, sample_rows)
                # Update row count if available
                if table_data['sample_data'] and 'row_count' in table_data['sample_data']:
                    table_data['row_count'] = table_data['sample_data'].get('total_row_count')

            tables.append(table_data)

        return tables

    def _build_columns(self, table) -> List[Dict[str, Any]]:
        """Build columns for a table."""
        columns = []

        for col in table.Columns:
            column_data = {
                'name': col.Name,
                'data_type': str(col.DataType),
                'is_hidden': col.IsHidden,
                'is_key': col.IsKey if hasattr(col, 'IsKey') else False,
                'data_category': str(col.DataCategory) if hasattr(col, 'DataCategory') else None,
                'summarize_by': str(col.SummarizeBy) if hasattr(col, 'SummarizeBy') else 'None',
                'format_string': col.FormatString if hasattr(col, 'FormatString') and col.FormatString else None,
                'sort_by_column': col.SortByColumn.Name if hasattr(col, 'SortByColumn') and col.SortByColumn else None,
                'description': col.Description if hasattr(col, 'Description') and col.Description else None
            }

            # Check if it's a calculated column
            if hasattr(col, 'Type') and str(col.Type) == 'Calculated':
                column_data['expression'] = col.Expression if hasattr(col, 'Expression') else None
                column_data['source_column'] = None
            else:
                column_data['expression'] = None
                column_data['source_column'] = col.SourceColumn if hasattr(col, 'SourceColumn') and col.SourceColumn else None

            columns.append(column_data)

        return columns

    def _build_measures(self, table, include_dax_patterns: bool) -> List[Dict[str, Any]]:
        """Build measures for a table."""
        measures = []

        for measure in table.Measures:
            measure_data = {
                'name': measure.Name,
                'display_folder': measure.DisplayFolder if hasattr(measure, 'DisplayFolder') and measure.DisplayFolder else None,
                'data_type': str(measure.DataType) if hasattr(measure, 'DataType') else None,
                'format_string': measure.FormatString if hasattr(measure, 'FormatString') and measure.FormatString else None,
                'is_hidden': measure.IsHidden if hasattr(measure, 'IsHidden') else False,
                'description': measure.Description if hasattr(measure, 'Description') and measure.Description else None,
                'expression': measure.Expression
            }

            # Detect DAX patterns if requested
            if include_dax_patterns:
                measure_data['dax_patterns'] = self._detect_dax_patterns(measure.Expression)

            measures.append(measure_data)

        return measures

    def _build_hierarchies(self, table) -> List[Dict[str, Any]]:
        """Build hierarchies for a table."""
        hierarchies = []

        for hier in table.Hierarchies:
            levels = []
            for level in hier.Levels:
                levels.append({
                    'name': level.Name,
                    'column': level.Column.Name if level.Column else None,
                    'ordinal': level.Ordinal if hasattr(level, 'Ordinal') else None
                })

            hierarchies.append({
                'name': hier.Name,
                'is_hidden': hier.IsHidden if hasattr(hier, 'IsHidden') else False,
                'levels': levels
            })

        return hierarchies

    def _build_partitions(self, table) -> List[Dict[str, Any]]:
        """Build partitions for a table."""
        partitions = []

        for partition in table.Partitions:
            partition_data = {
                'name': partition.Name,
                'mode': str(partition.Mode) if hasattr(partition, 'Mode') else 'Import',
                'source_type': str(type(partition.Source).__name__) if hasattr(partition, 'Source') else 'Unknown'
            }

            # Add M expression for M partitions
            if hasattr(partition, 'Source') and hasattr(partition.Source, 'Expression'):
                partition_data['expression'] = partition.Source.Expression[:500]  # Truncate long expressions

            partitions.append(partition_data)

        return partitions

    def _build_relationships(self, model) -> List[Dict[str, Any]]:
        """Build relationships section."""
        relationships = []

        for rel in model.Relationships:
            relationships.append({
                'name': rel.Name if hasattr(rel, 'Name') and rel.Name else f"{rel.FromTable.Name}_{rel.ToTable.Name}",
                'from_table': rel.FromTable.Name,
                'from_column': rel.FromColumn.Name,
                'to_table': rel.ToTable.Name,
                'to_column': rel.ToColumn.Name,
                'cardinality': f"{str(rel.FromCardinality)}:{str(rel.ToCardinality)}",
                'cross_filter_direction': str(rel.CrossFilteringBehavior),
                'is_active': rel.IsActive,
                'security_filtering_behavior': str(rel.SecurityFilteringBehavior) if hasattr(rel, 'SecurityFilteringBehavior') else None,
                'rely_on_referential_integrity': rel.RelyOnReferentialIntegrity if hasattr(rel, 'RelyOnReferentialIntegrity') else False
            })

        return relationships

    def _build_calculation_groups(self, model) -> List[Dict[str, Any]]:
        """Build calculation groups section."""
        calc_groups = []

        for table in model.Tables:
            if not (hasattr(table, 'CalculationGroup') and table.CalculationGroup is not None):
                continue

            calc_group = table.CalculationGroup
            items = []

            for item in calc_group.CalculationItems:
                items.append({
                    'name': item.Name,
                    'ordinal': item.Ordinal,
                    'expression': item.Expression,
                    'format_string_expression': item.FormatStringExpression if hasattr(item, 'FormatStringExpression') and item.FormatStringExpression else None
                })

            calc_groups.append({
                'name': table.Name,
                'precedence': calc_group.Precedence if hasattr(calc_group, 'Precedence') else 0,
                'description': table.Description if hasattr(table, 'Description') and table.Description else None,
                'calculation_items': items
            })

        return calc_groups

    def _build_roles(self, model) -> List[Dict[str, Any]]:
        """Build roles section (RLS)."""
        roles = []

        if not hasattr(model, 'Roles'):
            return roles

        for role in model.Roles:
            table_permissions = []

            for perm in role.TablePermissions:
                table_permissions.append({
                    'table': perm.Table.Name,
                    'filter_expression': perm.FilterExpression if hasattr(perm, 'FilterExpression') and perm.FilterExpression else None
                })

            roles.append({
                'name': role.Name,
                'description': role.Description if hasattr(role, 'Description') and role.Description else None,
                'model_permission': str(role.ModelPermission) if hasattr(role, 'ModelPermission') else 'Read',
                'table_permissions': table_permissions
            })

        return roles

    def _build_m_expressions(self, model) -> List[Dict[str, Any]]:
        """Build M expressions section."""
        m_expressions = []

        if not hasattr(model, 'Expressions'):
            return m_expressions

        for expr in model.Expressions:
            m_expressions.append({
                'name': expr.Name,
                'kind': str(expr.Kind) if hasattr(expr, 'Kind') else 'M',
                'expression': expr.Expression[:1000] if hasattr(expr, 'Expression') else None  # Truncate long expressions
            })

        return m_expressions

    def _get_sample_data(self, table_name: str, max_rows: int) -> Optional[Dict[str, Any]]:
        """Get sample data for a table using query executor."""
        if not self.query_executor:
            return None

        try:
            # Create EVALUATE query
            escaped_table = table_name.replace("'", "''")
            query = f'EVALUATE TOPN({max_rows}, \'{escaped_table}\')'

            result = self.query_executor.validate_and_execute_dax(query, top_n=max_rows, bypass_cache=True)

            if not result.get('success'):
                logger.warning(f"Could not get sample data for {table_name}: {result.get('error')}")
                return None

            rows = result.get('rows', [])
            if not rows:
                return {'format': 'columnar', 'row_count': 0, 'columns': [], 'data': {}}

            # Convert to columnar format (more efficient for LLMs)
            columns = list(rows[0].keys())
            data = {}

            for col in columns:
                # Remove brackets from column names
                clean_col = col.strip('[]')
                data[clean_col] = [self._serialize_value(row.get(col)) for row in rows]

            # Get total row count if available
            total_rows = result.get('total_rows')

            return {
                'format': 'columnar',
                'row_count': len(rows),
                'total_row_count': total_rows,
                'columns': [col.strip('[]') for col in columns],
                'data': data
            }

        except Exception as e:
            logger.warning(f"Error getting sample data for {table_name}: {e}")
            return None

    def _serialize_value(self, value) -> Any:
        """Serialize a value for JSON export."""
        if value is None:
            return None

        # Handle .NET DateTime
        try:
            if hasattr(value, 'ToString'):
                return str(value)
        except Exception:
            pass

        # Handle basic types
        if isinstance(value, (str, int, float, bool)):
            return value

        # Default: convert to string
        return str(value)

    def _detect_dax_patterns(self, dax_expression: str) -> List[str]:
        """Detect common DAX patterns in an expression."""
        if not dax_expression:
            return []

        patterns = []
        dax_upper = dax_expression.upper()

        # Time intelligence
        if any(func in dax_upper for func in ['DATEADD', 'SAMEPERIODLASTYEAR', 'PARALLELPERIOD', 'DATESBETWEEN', 'DATESYTD', 'DATESMTD', 'DATESQTD']):
            patterns.append('Time Intelligence')

        # Aggregation
        if any(func in dax_upper for func in ['SUM', 'AVERAGE', 'COUNT', 'MIN', 'MAX', 'DISTINCTCOUNT']):
            patterns.append('Aggregation')

        # Iterator
        if any(func in dax_upper for func in ['SUMX', 'AVERAGEX', 'COUNTX', 'MINX', 'MAXX']):
            patterns.append('Iterator')

        # Filter context
        if any(func in dax_upper for func in ['CALCULATE', 'CALCULATETABLE', 'FILTER', 'ALL', 'ALLSELECTED', 'ALLEXCEPT']):
            patterns.append('Filter Context')

        # Variables
        if 'VAR ' in dax_upper and 'RETURN' in dax_upper:
            patterns.append('Variables')

        # Error handling
        if any(func in dax_upper for func in ['IFERROR', 'ISERROR', 'ISBLANK']):
            patterns.append('Error Handling')

        # Ranking
        if any(func in dax_upper for func in ['RANKX', 'TOPN']):
            patterns.append('Ranking')

        # Parent-Child
        if any(func in dax_upper for func in ['PATH', 'PATHITEM', 'PATHCONTAINS', 'PATHLENGTH']):
            patterns.append('Parent-Child')

        return patterns if patterns else ['Basic']

    def _build_dependency_graph(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build dependency graph for measures and columns."""
        # This is a simplified dependency tracker
        # For full dependency analysis, we'd integrate with pbip_dependency_engine.py

        dependency_graph = {
            'measures': {},
            'columns': {}
        }

        # Build simple dependency tracking
        for table in model_data.get('tables', []):
            table_name = table['name']

            # Track column usage
            for col in table.get('columns', []):
                col_ref = f"{table_name}[{col['name']}]"
                dependency_graph['columns'][col_ref] = {
                    'used_in_measures': [],
                    'used_in_calculated_columns': [],
                    'used_in_rls': False
                }

            # Track measure dependencies
            for measure in table.get('measures', []):
                measure_ref = f"{table_name}[{measure['name']}]"

                # Simple pattern matching for dependencies
                expression = measure.get('expression', '')

                # Find column references
                column_refs = self._extract_column_references(expression, model_data)

                # Find measure references
                measure_refs = self._extract_measure_references(expression, model_data)

                dependency_graph['measures'][measure_ref] = {
                    'direct_dependencies': {
                        'columns': column_refs,
                        'measures': measure_refs
                    },
                    'dependency_depth': 0,  # Would need recursive calculation
                    'complexity_score': len(expression)  # Simple complexity metric
                }

                # Update column usage
                for col_ref in column_refs:
                    if col_ref in dependency_graph['columns']:
                        dependency_graph['columns'][col_ref]['used_in_measures'].append(measure_ref)

        return dependency_graph

    def _extract_column_references(self, dax_expression: str, model_data: Dict[str, Any]) -> List[str]:
        """Extract column references from DAX expression."""
        import re

        column_refs = []

        # Pattern: 'Table'[Column] or Table[Column]
        pattern = r"'?([A-Za-z0-9_\s]+)'?\[([A-Za-z0-9_\s]+)\]"
        matches = re.findall(pattern, dax_expression)

        for table, column in matches:
            table = table.strip()
            column = column.strip()

            # Check if this is a valid column (not a measure)
            for tbl in model_data.get('tables', []):
                if tbl['name'] == table:
                    for col in tbl.get('columns', []):
                        if col['name'] == column:
                            column_refs.append(f"{table}[{column}]")
                            break

        return list(set(column_refs))  # Deduplicate

    def _extract_measure_references(self, dax_expression: str, model_data: Dict[str, Any]) -> List[str]:
        """Extract measure references from DAX expression."""
        import re

        measure_refs = []

        # Pattern: [MeasureName] (without table prefix usually indicates measure)
        pattern = r"\[([A-Za-z0-9_\s]+)\]"
        matches = re.findall(pattern, dax_expression)

        for match in matches:
            match = match.strip()

            # Check if this is a valid measure
            for tbl in model_data.get('tables', []):
                for measure in tbl.get('measures', []):
                    if measure['name'] == match:
                        measure_refs.append(f"{tbl['name']}[{match}]")
                        break

        return list(set(measure_refs))  # Deduplicate

    def _build_bpa_issues(self) -> List[Dict[str, Any]]:
        """Build best practice analysis issues."""
        # This would integrate with the BPA module if available
        # For now, return empty list
        return []

    def _detect_model_purpose(self, model) -> Optional[Dict[str, Any]]:
        """
        Detect model purpose using heuristic analysis of table names and structure.
        Returns purpose information including domains, signals, and descriptive text.
        """
        try:
            # Collect table names
            table_names = set()
            for table in model.Tables:
                table_names.add(table.Name)

            name_str = " ".join(table_names).lower()

            def present(substrs):
                """Check if any substring is present in table names."""
                return any(s.lower() in name_str for s in substrs)

            domains = []
            signals = []

            # Time intelligence
            if any(k in table_names for k in ('d_Date', 'd_Period')) or present(['time', 'period', 'calendar']):
                domains.append('Period/Time')
                signals.append('Time intelligence (Date/Period tables)')

            # Currency conversion
            if present(['currency', 'fx']) or any(k in table_names for k in ('d_Currency_From', 'd_Currency_Report', 'd_Currency_Rates')):
                domains.append('Currency/FX')
                signals.append('Currency conversion present (currency tables)')

            # Scenario/versioning
            if present(['scenario', 'version']):
                domains.append('Scenario/Version')
                signals.append('Scenario/version switching')

            # Financial reporting / GL / P&L / Balance Sheet
            if present(['gl', 'p&l', 'pl', 'balance', 'bs', 'cash flow', 'cf', 'finrep']) or 'f_FINREP' in table_names or 'd_GL Account' in table_names:
                domains.append('Financial Reporting')
                signals.append('General Ledger / P&L / BS indicators detected')

            # Aging / AR / AP
            if present(['aging']) or any(k in table_names for k in ('f_Aging_Customer', 'f_Aging_Vendor')):
                domains.append('Aging/AR/AP')
                signals.append('Accounts receivable/payable aging')

            # RLS
            if present(['rls']) or any(n.startswith('r_RLS_') for n in table_names):
                domains.append('Row-Level Security')
                signals.append('RLS artifacts detected (roles/tables)')

            # Customer/Vendor
            if any(k in table_names for k in ('d_Customer', 'd_Vendor')) or present(['customer', 'vendor', 'supplier']):
                domains.append('Customer/Vendor')

            # Organization (Cost/Profit/Company)
            if any(k in table_names for k in ('d_Company', 'd_CostCenter', 'd_Profit Center')) or present(['company', 'cost center', 'profit center']):
                domains.append('Company/Org')

            # Star schema hint
            star_hint = None
            if any(n.startswith('f_') for n in table_names) and any(n.startswith('d_') for n in table_names):
                star_hint = 'Star-schema oriented (facts linked to multiple dimensions)'
                signals.append(star_hint)

            # Measure hub hint
            if 'm_Measures' in table_names:
                signals.append('Central measure table (m_Measures)')

            # Compose a short purpose text
            lead = []
            if 'Financial Reporting' in domains:
                lead.append('financial reporting')
            if 'Currency/FX' in domains:
                lead.append('currency conversion')
            if 'Row-Level Security' in domains:
                lead.append('row-level security')
            if 'Period/Time' in domains:
                lead.append('time intelligence')

            if lead:
                purpose_text = f"Model geared towards {', '.join(lead[:-1]) + (' and ' if len(lead) > 1 else '') + lead[-1]}"
            else:
                purpose_text = 'General analytics model'

            if star_hint and star_hint not in signals:
                signals.append(star_hint)

            # De-duplicate while preserving order
            seen = set()
            signals = [s for s in signals if not (s in seen or seen.add(s))]
            dom_seen = set()
            domains = [d for d in domains if not (d in dom_seen or dom_seen.add(d))]

            return {
                'text': purpose_text,
                'domains': domains,
                'signals': signals,
            }

        except Exception as e:
            logger.warning(f"Error detecting model purpose: {e}")
            return None

    def _export_json(self, model_data: Dict[str, Any], output_path: str) -> int:
        """Export as JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)

        return os.path.getsize(output_path)

    def _export_json_gzip(self, model_data: Dict[str, Any], output_path: str) -> tuple:
        """Export as gzip-compressed JSON file."""
        # First get uncompressed size
        json_str = json.dumps(model_data, indent=2, ensure_ascii=False)
        uncompressed_size = len(json_str.encode('utf-8'))

        # Write compressed
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)

        compressed_size = os.path.getsize(output_path)

        return uncompressed_size, compressed_size

    def _export_markdown(self, model_data: Dict[str, Any], output_path: str) -> int:
        """Export as Markdown file."""
        lines = []
        metadata = model_data['metadata']

        # Header
        lines.append(f"# Power BI Model Analysis: {metadata['model_name']}")
        lines.append(f"\n**Export Date:** {metadata['export_timestamp']}")
        lines.append(f"**Compatibility Level:** {metadata['compatibility_level']}")
        lines.append("")

        # Statistics
        stats = metadata['statistics']
        lines.append("## Model Statistics")
        lines.append(f"- Tables: {stats['table_count']}")
        lines.append(f"- Measures: {stats['measure_count']}")
        lines.append(f"- Columns: {stats['column_count']}")
        lines.append(f"- Relationships: {stats['relationship_count']}")
        lines.append(f"- Calculation Groups: {stats['calculation_group_count']}")
        lines.append("")

        # Tables
        lines.append("## Tables")
        for table in model_data.get('tables', []):
            lines.append(f"\n### {table['name']}")
            lines.append(f"**Type:** {table['type']} | **Rows:** {table.get('row_count', 'N/A')} | **Hidden:** {'Yes' if table['is_hidden'] else 'No'}")

            # Columns
            if table.get('columns'):
                lines.append("\n#### Columns")
                lines.append("| Name | Type | Key | Hidden |")
                lines.append("|------|------|-----|--------|")
                for col in table['columns'][:20]:  # Limit to first 20
                    lines.append(f"| {col['name']} | {col['data_type']} | {'Yes' if col['is_key'] else 'No'} | {'Yes' if col['is_hidden'] else 'No'} |")

            # Measures
            if table.get('measures'):
                lines.append("\n#### Measures")
                for measure in table['measures'][:10]:  # Limit to first 10
                    lines.append(f"\n**{measure['name']}**")
                    if measure.get('display_folder'):
                        lines.append(f"*Folder: {measure['display_folder']}*")
                    lines.append("```dax")
                    lines.append(measure.get('expression', '')[:300])  # Truncate
                    lines.append("```")

        # Relationships
        if model_data.get('relationships'):
            lines.append("\n## Relationships")
            lines.append("| From | To | Active | Cardinality | Direction |")
            lines.append("|------|-----|--------|-------------|-----------|")
            for rel in model_data['relationships']:
                from_str = f"{rel['from_table']}[{rel['from_column']}]"
                to_str = f"{rel['to_table']}[{rel['to_column']}]"
                active = "Yes" if rel['is_active'] else "No"
                lines.append(f"| {from_str} | {to_str} | {active} | {rel['cardinality']} | {rel['cross_filter_direction']} |")

        # Write to file
        markdown = "\n".join(lines)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return os.path.getsize(output_path)
