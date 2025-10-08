"""
Model Exporter for PBIXRay MCP Server
Exports models in TMSL, TMDL, and documentation formats
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to load AMO
AMO_AVAILABLE = False
AMOServer = None

try:
    import clr
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    dll_folder = os.path.join(parent_dir, "lib", "dotnet")

    core_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Core.dll")
    amo_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.dll")
    tabular_dll = os.path.join(dll_folder, "Microsoft.AnalysisServices.Tabular.dll")

    if os.path.exists(core_dll):
        clr.AddReference(core_dll)
    if os.path.exists(amo_dll):
        clr.AddReference(amo_dll)
    if os.path.exists(tabular_dll):
        clr.AddReference(tabular_dll)

    from Microsoft.AnalysisServices.Tabular import Server as AMOServer
    AMO_AVAILABLE = True
    logger.info("AMO available for model export")

except Exception as e:
    logger.warning(f"AMO not available for export: {e}")


class ModelExporter:
    """Export Power BI models in various formats."""

    def __init__(self, connection):
        """Initialize with ADOMD connection."""
        self.connection = connection

    def export_tmsl(self, include_full_model: bool = False) -> Dict[str, Any]:
        """
        Export model as TMSL JSON.

        Args:
            include_full_model: If False, returns summary only. If True, includes full model (may be large).
        """
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available for TMSL export'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            # Get database
            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]

            # Get TMSL as JSON using JsonSerializer
            from Microsoft.AnalysisServices.Tabular import JsonSerializer, JsonSerializeOptions

            options = JsonSerializeOptions()
            options.IgnoreInferredObjects = False
            options.IgnoreInferredProperties = False
            options.IgnoreTimestamps = True

            tmsl_json = JsonSerializer.SerializeObject(db.Model, options)
            tmsl_data = json.loads(tmsl_json)

            # Calculate statistics
            stats = {
                'tables': len(tmsl_data.get('tables', [])),
                'relationships': len(tmsl_data.get('relationships', [])),
                'cultures': len(tmsl_data.get('cultures', [])),
                'roles': len(tmsl_data.get('roles', [])),
                'expressions': len(tmsl_data.get('expressions', [])),
            }

            # Count measures across all tables
            measure_count = 0
            column_count = 0
            for table in tmsl_data.get('tables', []):
                measure_count += len(table.get('measures', []))
                column_count += len(table.get('columns', []))

            stats['measures'] = measure_count
            stats['columns'] = column_count

            # Build result
            result = {
                'success': True,
                'format': 'TMSL',
                'database_name': db.Name,
                'compatibility_level': db.CompatibilityLevel,
                'export_timestamp': datetime.now().isoformat(),
                'statistics': stats
            }

            # Only include full model if requested
            if include_full_model:
                result['model'] = tmsl_data
                result['note'] = 'Full model included - may be large'
            else:
                # Include lightweight summary
                result['summary'] = {
                    'table_names': [t.get('name') for t in tmsl_data.get('tables', [])],
                    'note': 'Use include_full_model=true to get complete TMSL'
                }

            logger.info(f"Exported TMSL: {stats['tables']} tables, {stats['measures']} measures")
            return result

        except Exception as e:
            logger.error(f"TMSL export error: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass

    def export_tmdl_structure(self) -> Dict[str, Any]:
        """Export model structure as TMDL-style hierarchy."""
        if not AMO_AVAILABLE:
            return {
                'success': False,
                'error': 'AMO not available for TMDL export'
            }

        server = AMOServer()
        try:
            server.Connect(self.connection.ConnectionString)

            if server.Databases.Count == 0:
                return {'success': False, 'error': 'No database found'}

            db = server.Databases[0]
            model = db.Model

            # Build TMDL structure
            tmdl = {
                'model': {
                    'name': model.Name if hasattr(model, 'Name') else db.Name,
                    'compatibility_level': db.CompatibilityLevel,
                    'default_mode': str(model.DefaultMode) if hasattr(model, 'DefaultMode') else 'Import'
                },
                'tables': {},
                'relationships': [],
                'roles': [],
                'cultures': []
            }

            # Export tables
            for table in model.Tables:
                table_data = {
                    'name': table.Name,
                    'is_hidden': table.IsHidden,
                    'columns': [],
                    'measures': [],
                    'hierarchies': []
                }

                # Columns
                for col in table.Columns:
                    table_data['columns'].append({
                        'name': col.Name,
                        'data_type': str(col.DataType),
                        'is_hidden': col.IsHidden,
                        'source_column': col.SourceColumn if hasattr(col, 'SourceColumn') else None
                    })

                # Measures
                for measure in table.Measures:
                    table_data['measures'].append({
                        'name': measure.Name,
                        'expression': measure.Expression,
                        'display_folder': measure.DisplayFolder,
                        'format_string': measure.FormatString if hasattr(measure, 'FormatString') else None
                    })

                # Hierarchies
                for hier in table.Hierarchies:
                    levels = []
                    for level in hier.Levels:
                        levels.append({
                            'name': level.Name,
                            'column': level.Column.Name if level.Column else None
                        })
                    table_data['hierarchies'].append({
                        'name': hier.Name,
                        'levels': levels
                    })

                tmdl['tables'][table.Name] = table_data

            # Export relationships
            for rel in model.Relationships:
                tmdl['relationships'].append({
                    'name': rel.Name if hasattr(rel, 'Name') else f"{rel.FromTable.Name}_{rel.ToTable.Name}",
                    'from_table': rel.FromTable.Name,
                    'from_column': rel.FromColumn.Name,
                    'to_table': rel.ToTable.Name,
                    'to_column': rel.ToColumn.Name,
                    'is_active': rel.IsActive,
                    'cross_filter_direction': str(rel.CrossFilteringBehavior),
                    'cardinality': str(rel.FromCardinality) + ':' + str(rel.ToCardinality)
                })

            # Export roles
            if hasattr(model, 'Roles'):
                for role in model.Roles:
                    role_data = {
                        'name': role.Name,
                        'table_permissions': []
                    }
                    for perm in role.TablePermissions:
                        role_data['table_permissions'].append({
                            'table': perm.Table.Name,
                            'filter_expression': perm.FilterExpression if hasattr(perm, 'FilterExpression') else None
                        })
                    tmdl['roles'].append(role_data)

            result = {
                'success': True,
                'format': 'TMDL',
                'database_name': db.Name,
                'tmdl': tmdl,
                'export_timestamp': datetime.now().isoformat(),
                'statistics': {
                    'tables': len(tmdl['tables']),
                    'relationships': len(tmdl['relationships']),
                    'roles': len(tmdl['roles'])
                }
            }

            logger.info(f"Exported TMDL structure: {result['statistics']['tables']} tables")
            return result

        except Exception as e:
            logger.error(f"TMDL export error: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                server.Disconnect()
            except:
                pass

    def generate_documentation(self, query_executor) -> Dict[str, Any]:
        """Generate markdown documentation for the model."""
        try:
            doc_lines = []
            doc_lines.append("# Power BI Model Documentation")
            doc_lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

            # Model overview
            tables_result = query_executor.execute_info_query("TABLES")
            measures_result = query_executor.execute_info_query("MEASURES")
            rels_result = query_executor.execute_info_query("RELATIONSHIPS")

            if tables_result.get('success'):
                tables = tables_result['rows']
                measures = measures_result.get('rows', [])
                rels = rels_result.get('rows', [])

                doc_lines.append("## Model Overview\n")
                doc_lines.append(f"- **Tables**: {len(tables)}")
                doc_lines.append(f"- **Measures**: {len(measures)}")
                doc_lines.append(f"- **Relationships**: {len(rels)}")
                doc_lines.append("")

                # Tables section
                doc_lines.append("## Tables\n")
                for table in tables:
                    table_name = table.get('Name', 'Unknown')
                    is_hidden = table.get('IsHidden', False)
                    hidden_tag = " *(hidden)*" if is_hidden else ""

                    doc_lines.append(f"### {table_name}{hidden_tag}\n")

                    # Get columns for this table
                    cols_result = query_executor.execute_info_query("COLUMNS", table_name=table_name)
                    if cols_result.get('success'):
                        doc_lines.append("**Columns:**")
                        for col in cols_result['rows']:
                            col_name = col.get('Name')
                            col_type = col.get('DataType', 'Unknown')
                            col_hidden = " *(hidden)*" if col.get('IsHidden') else ""
                            doc_lines.append(f"- `{col_name}` ({col_type}){col_hidden}")
                        doc_lines.append("")

                    # Get measures for this table
                    table_measures = [m for m in measures if m.get('Table') == table_name]
                    if table_measures:
                        doc_lines.append("**Measures:**")
                        for measure in table_measures[:10]:  # Limit to first 10
                            m_name = measure.get('Name')
                            m_hidden = " *(hidden)*" if measure.get('IsHidden') else ""
                            doc_lines.append(f"- `{m_name}`{m_hidden}")
                        if len(table_measures) > 10:
                            doc_lines.append(f"  *(... and {len(table_measures) - 10} more)*")
                        doc_lines.append("")

                # Relationships section
                if rels:
                    doc_lines.append("## Relationships\n")
                    doc_lines.append("| From | To | Active | Cardinality | Direction |")
                    doc_lines.append("|------|-----|--------|-------------|-----------|")
                    for rel in rels:
                        from_str = f"{rel.get('FromTable')}[{rel.get('FromColumn')}]"
                        to_str = f"{rel.get('ToTable')}[{rel.get('ToColumn')}]"
                        active = "Yes" if rel.get('IsActive') else "No"
                        cardinality = rel.get('Cardinality', 'Unknown')
                        direction = rel.get('CrossFilterDirection', 'Single')
                        doc_lines.append(f"| {from_str} | {to_str} | {active} | {cardinality} | {direction} |")
                    doc_lines.append("")

                # Key measures section
                doc_lines.append("## Key Measures\n")
                visible_measures = [m for m in measures if not m.get('IsHidden')][:20]
                for measure in visible_measures:
                    m_name = measure.get('Name')
                    m_table = measure.get('Table')
                    m_expr = measure.get('Expression', '')

                    doc_lines.append(f"### {m_table}.{m_name}\n")
                    doc_lines.append("```dax")
                    doc_lines.append(m_expr[:300])  # Truncate long expressions
                    if len(m_expr) > 300:
                        doc_lines.append("...")
                    doc_lines.append("```\n")

            markdown = "\n".join(doc_lines)

            return {
                'success': True,
                'format': 'markdown',
                'documentation': markdown,
                'line_count': len(doc_lines),
                'export_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Documentation generation error: {e}")
            return {'success': False, 'error': str(e)}

    def compare_models(self, tmsl_reference: Dict) -> Dict[str, Any]:
        """Compare current model with reference TMSL."""
        try:
            current = self.export_tmsl(include_full_model=True)
            if not current.get('success'):
                return current

            current_model = current['model']
            ref_model = tmsl_reference.get('model', tmsl_reference)

            changes = {
                'tables_added': [],
                'tables_removed': [],
                'tables_modified': [],
                'relationships_added': [],
                'relationships_removed': [],
                'measures_added': [],
                'measures_removed': []
            }

            # Compare tables
            current_tables = {t['name']: t for t in current_model.get('tables', [])}
            ref_tables = {t['name']: t for t in ref_model.get('tables', [])}

            for name in current_tables:
                if name not in ref_tables:
                    changes['tables_added'].append(name)

            for name in ref_tables:
                if name not in current_tables:
                    changes['tables_removed'].append(name)

            # Compare relationships
            current_rels = set()
            for r in current_model.get('relationships', []):
                rel_key = f"{r.get('fromTable')}.{r.get('fromColumn')}->{r.get('toTable')}.{r.get('toColumn')}"
                current_rels.add(rel_key)

            ref_rels = set()
            for r in ref_model.get('relationships', []):
                rel_key = f"{r.get('fromTable')}.{r.get('fromColumn')}->{r.get('toTable')}.{r.get('toColumn')}"
                ref_rels.add(rel_key)

            changes['relationships_added'] = list(current_rels - ref_rels)
            changes['relationships_removed'] = list(ref_rels - current_rels)

            # Summary
            total_changes = sum(len(v) for v in changes.values())

            return {
                'success': True,
                'changes': changes,
                'summary': {
                    'total_changes': total_changes,
                    'tables_changed': len(changes['tables_added']) + len(changes['tables_removed']),
                    'relationships_changed': len(changes['relationships_added']) + len(changes['relationships_removed'])
                }
            }

        except Exception as e:
            logger.error(f"Model comparison error: {e}")
            return {'success': False, 'error': str(e)}

    def get_model_summary(self, query_executor) -> Dict[str, Any]:
        """
        Get a comprehensive but lightweight model summary.
        Useful for comparing large models without exporting full TMSL.
        """
        try:
            summary = {
                'success': True,
                'timestamp': datetime.now().isoformat()
            }

            # Get tables with row counts
            tables_result = query_executor.execute_info_query("TABLES")
            if tables_result.get('success'):
                tables = tables_result['rows']
                summary['tables'] = {
                    'count': len(tables),
                    'list': [{'name': t.get('Name'), 'hidden': t.get('IsHidden', False)}
                             for t in tables]
                }

            # Get measures
            measures_result = query_executor.execute_info_query("MEASURES")
            if measures_result.get('success'):
                measures = measures_result['rows']
                summary['measures'] = {
                    'count': len(measures),
                    'by_table': {}
                }
                for m in measures:
                    table = m.get('Table', 'Unknown')
                    if table not in summary['measures']['by_table']:
                        summary['measures']['by_table'][table] = 0
                    summary['measures']['by_table'][table] += 1

            # Get columns
            columns_result = query_executor.execute_info_query("COLUMNS")
            if columns_result.get('success'):
                columns = columns_result['rows']
                summary['columns'] = {
                    'count': len(columns),
                    'calculated': len([c for c in columns if c.get('Type') == 'Calculated']),
                    'by_table': {}
                }
                for c in columns:
                    table = c.get('Table', 'Unknown')
                    if table not in summary['columns']['by_table']:
                        summary['columns']['by_table'][table] = 0
                    summary['columns']['by_table'][table] += 1

            # Get relationships
            rels_result = query_executor.execute_info_query("RELATIONSHIPS")
            if rels_result.get('success'):
                rels = rels_result['rows']
                summary['relationships'] = {
                    'count': len(rels),
                    'active': len([r for r in rels if r.get('IsActive')]),
                    'inactive': len([r for r in rels if not r.get('IsActive')]),
                    'list': [f"{r.get('FromTable')}[{r.get('FromColumn')}] -> {r.get('ToTable')}[{r.get('ToColumn')}]"
                             for r in rels]
                }

            return summary

        except Exception as e:
            logger.error(f"Error getting model summary: {e}")
            return {'success': False, 'error': str(e)}
