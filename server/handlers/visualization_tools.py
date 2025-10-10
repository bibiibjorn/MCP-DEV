"""
visualization_tools.py

Dashboard visualization mockup tools for MCP-PowerBi-Finvision server.
Provides data formatting and metadata tools optimized for Claude AI agent
to generate high-quality React artifact-based dashboard mockups.

Key Features:
- Smart data formatting for Recharts, Chart.js, Plotly, D3
- Automatic chart type recommendations based on data characteristics
- Multiple dashboard layout patterns (KPI grid, executive summary, operational)
- Sample data extraction with proper typing and formatting
- Metadata enrichment for intelligent visualization selection

Usage in MCP server:
    from server.handlers.visualization_tools import VisualizationTools
    viz_tools = VisualizationTools(connection_state, config)
    result = viz_tools.prepare_dashboard_data(request_type='executive_summary')
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger("mcp_powerbi_finvision.visualization")


class VisualizationTools:
    """Prepares Power BI model data for dashboard visualization mockups."""
    
    def __init__(self, connection_state, config):
        self.connection_state = connection_state
        self.config = config
        self.qe = connection_state.query_executor if connection_state else None
        
    def prepare_dashboard_data(
        self,
        request_type: str = 'overview',
        tables: Optional[List[str]] = None,
        measures: Optional[List[Dict]] = None,
        max_rows: int = 100,
        sample_rows: int = 20
    ) -> Dict[str, Any]:
        """
        Prepare data for dashboard mockup generation.
        
        Args:
            request_type: Type of dashboard ('overview', 'executive_summary', 
                         'operational', 'financial', 'custom')
            tables: Specific tables to include (None = auto-select)
            measures: Specific measures to visualize [{table, measure, chart_type}]
            max_rows: Maximum rows per query
            sample_rows: Sample size for data preview
            
        Returns:
            Dict with formatted data, metadata, and chart recommendations
        """
        if not self.qe:
            return {
                'success': False,
                'error': 'Query executor not available',
                'error_type': 'manager_unavailable'
            }
            
        try:
            result = {
                'success': True,
                'request_type': request_type,
                'timestamp': datetime.now().isoformat(),
                'data': {},
                'metadata': {},
                'chart_recommendations': [],
                'layout_suggestion': None
            }
            
            # Get model summary
            summary = self._get_model_summary()
            result['metadata']['model'] = summary
            
            # Determine which data to include
            if request_type == 'executive_summary':
                result.update(self._prepare_executive_summary(max_rows, sample_rows))
            elif request_type == 'operational':
                result.update(self._prepare_operational_dashboard(max_rows, sample_rows))
            elif request_type == 'financial':
                result.update(self._prepare_financial_dashboard(max_rows, sample_rows))
            elif measures:
                result.update(self._prepare_custom_measures(measures, max_rows, sample_rows))
            else:
                result.update(self._prepare_overview_dashboard(tables, max_rows, sample_rows))
                
            # Add chart library recommendations
            result['library_recommendations'] = self._recommend_chart_libraries(result)
            
            # Add layout pattern
            result['layout_pattern'] = self._suggest_layout_pattern(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error preparing dashboard data: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'visualization_preparation_error'
            }
    
    def _get_model_summary(self) -> Dict:
        """Get compact model summary."""
        try:
            tables_result = self.qe.execute_info_query("TABLES")
            measures_result = self.qe.execute_info_query("MEASURES", exclude_columns=['Expression'])
            
            tables = tables_result.get('rows', []) if tables_result.get('success') else []
            measures = measures_result.get('rows', []) if measures_result.get('success') else []
            
            return {
                'table_count': len(tables),
                'measure_count': len(measures),
                'tables': [self._extract_name(t) for t in tables[:10]],
                'has_date_table': any('date' in self._extract_name(t).lower() or 'calendar' in self._extract_name(t).lower() for t in tables)
            }
        except Exception as e:
            logger.warning(f"Could not get model summary: {e}")
            return {}
    
    def _prepare_executive_summary(self, max_rows: int, sample_rows: int) -> Dict:
        """Prepare data for executive summary dashboard (KPIs + trends)."""
        data = {
            'kpi_cards': [],
            'trend_charts': [],
            'comparison_charts': []
        }
        
        # Find key measures (look for Total, Revenue, Sales, Profit patterns)
        measures = self._find_key_measures(['total', 'revenue', 'sales', 'profit', 'margin'])
        
        for measure_info in measures[:6]:  # Top 6 KPIs
            table = measure_info['table']
            measure = measure_info['measure']
            
            # Get current value
            current_value = self._get_measure_value(table, measure)
            
            if current_value:
                kpi_data = {
                    'label': measure,
                    'value': current_value.get('value'),
                    'format': measure_info.get('format'),
                    'table': table,
                    'chart_type': 'kpi_card'
                }
                data['kpi_cards'].append(kpi_data)
                
                # Try to get trend data if date dimension exists
                trend = self._get_measure_trend(table, measure, sample_rows)
                if trend:
                    data['trend_charts'].append(trend)
        
        # Chart recommendations
        recommendations = [
            {
                'type': 'kpi_grid',
                'library': 'react + tailwind',
                'components': len(data['kpi_cards']),
                'layout': '3-column grid'
            }
        ]
        
        if data['trend_charts']:
            recommendations.append({
                'type': 'line_chart',
                'library': 'Recharts',
                'data_key': 'trend_charts',
                'description': 'Time series trends for KPIs'
            })
        
        return {
            'data': data,
            'chart_recommendations': recommendations
        }
    
    def _prepare_operational_dashboard(self, max_rows: int, sample_rows: int) -> Dict:
        """Prepare operational metrics (tables, bar charts, progress indicators)."""
        data = {
            'summary_tables': [],
            'bar_charts': [],
            'progress_metrics': []
        }
        
        # Find dimension tables for grouping
        dimension_tables = self._find_dimension_tables()
        
        # Find metrics to group
        measures = self._find_key_measures(['count', 'quantity', 'amount'])
        
        for measure_info in measures[:4]:
            for dim_table in dimension_tables[:2]:
                # Group measure by dimension
                grouped = self._get_grouped_data(
                    measure_info['table'],
                    measure_info['measure'],
                    dim_table,
                    sample_rows
                )
                
                if grouped:
                    data['bar_charts'].append({
                        'title': f"{measure_info['measure']} by {dim_table}",
                        'data': grouped,
                        'chart_type': 'bar',
                        'x_axis': dim_table,
                        'y_axis': measure_info['measure']
                    })
        
        recommendations = [
            {
                'type': 'bar_chart',
                'library': 'Recharts or Chart.js',
                'data_key': 'bar_charts',
                'responsive': True
            }
        ]
        
        return {
            'data': data,
            'chart_recommendations': recommendations
        }
    
    def _prepare_financial_dashboard(self, max_rows: int, sample_rows: int) -> Dict:
        """Prepare financial dashboard (P&L, balance sheet, cash flow patterns)."""
        data = {
            'financial_statements': [],
            'variance_analysis': [],
            'waterfall_charts': []
        }
        
        # Look for financial measures
        financial_measures = self._find_key_measures([
            'revenue', 'cost', 'expense', 'profit', 'ebitda',
            'assets', 'liabilities', 'equity', 'cash'
        ])
        
        # Group by financial categories
        categories = {
            'revenue': [],
            'expenses': [],
            'profitability': [],
            'balance_sheet': []
        }
        
        for measure_info in financial_measures:
            measure_lower = measure_info['measure'].lower()
            if any(k in measure_lower for k in ['revenue', 'sales', 'income']):
                categories['revenue'].append(measure_info)
            elif any(k in measure_lower for k in ['cost', 'expense', 'opex']):
                categories['expenses'].append(measure_info)
            elif any(k in measure_lower for k in ['profit', 'margin', 'ebitda']):
                categories['profitability'].append(measure_info)
            elif any(k in measure_lower for k in ['asset', 'liability', 'equity']):
                categories['balance_sheet'].append(measure_info)
        
        # Create financial statement structure
        for category, items in categories.items():
            if items:
                statement_data = []
                for item in items[:5]:
                    value = self._get_measure_value(item['table'], item['measure'])
                    if value:
                        statement_data.append({
                            'line_item': item['measure'],
                            'value': value.get('value'),
                            'format': item.get('format')
                        })
                
                if statement_data:
                    data['financial_statements'].append({
                        'category': category,
                        'items': statement_data
                    })
        
        recommendations = [
            {
                'type': 'financial_table',
                'library': 'react + tailwind',
                'data_key': 'financial_statements',
                'formatting': 'currency with accounting style'
            }
        ]
        
        return {
            'data': data,
            'chart_recommendations': recommendations,
            'layout_pattern': 'financial_statements'
        }
    
    def _prepare_overview_dashboard(self, tables: Optional[List[str]], max_rows: int, sample_rows: int) -> Dict:
        """Prepare general overview dashboard."""
        data = {
            'key_metrics': [],
            'sample_data': {},
            'relationships': []
        }
        
        # Get key tables
        target_tables = tables if tables else self._find_fact_tables()[:3]
        
        for table in target_tables:
            # Get sample data
            preview = self._get_table_preview(table, sample_rows)
            if preview:
                data['sample_data'][table] = preview
            
            # Get measures for this table
            table_measures = self._get_table_measures(table)
            for measure_info in table_measures[:3]:
                value = self._get_measure_value(table, measure_info['measure'])
                if value:
                    data['key_metrics'].append({
                        'table': table,
                        'measure': measure_info['measure'],
                        'value': value.get('value'),
                        'format': measure_info.get('format')
                    })
        
        # Get relationships for context
        rels = self._get_relationships(target_tables)
        data['relationships'] = rels
        
        recommendations = [
            {
                'type': 'mixed_dashboard',
                'components': ['kpi_cards', 'data_table', 'simple_charts'],
                'library': 'Recharts for charts, native React for tables'
            }
        ]
        
        return {
            'data': data,
            'chart_recommendations': recommendations
        }
    
    def _prepare_custom_measures(self, measures: List[Dict], max_rows: int, sample_rows: int) -> Dict:
        """Prepare data for custom list of measures."""
        data = {
            'measures': [],
            'chart_data': []
        }
        
        for measure_spec in measures:
            table = measure_spec.get('table')
            measure = measure_spec.get('measure')
            chart_type = measure_spec.get('chart_type', 'auto')
            
            if not table or not measure:
                continue
            
            # Get measure value
            value = self._get_measure_value(table, measure)
            
            if value:
                measure_data = {
                    'table': table,
                    'measure': measure,
                    'value': value.get('value'),
                    'chart_type': chart_type
                }
                
                # Get additional data based on chart type
                if chart_type in ['line', 'area', 'trend']:
                    trend = self._get_measure_trend(table, measure, sample_rows)
                    if trend:
                        measure_data['trend_data'] = trend
                elif chart_type in ['bar', 'column']:
                    # Try to find a dimension to group by
                    grouped = self._get_best_grouping(table, measure, sample_rows)
                    if grouped:
                        measure_data['grouped_data'] = grouped
                
                data['measures'].append(measure_data)
        
        # Generate recommendations
        recommendations = self._generate_chart_recommendations(data['measures'])
        
        return {
            'data': data,
            'chart_recommendations': recommendations
        }
    
    # Helper methods for data extraction
    
    def _extract_name(self, obj: Dict) -> str:
        """Extract name from object, handling various field names."""
        for key in ['Name', 'name', '[Name]', 'TABLE_NAME', 'TableName']:
            if key in obj and obj[key]:
                name = str(obj[key])
                # Remove brackets/quotes
                name = name.strip('[]"\'')
                return name
        return ''
    
    def _get_measure_value(self, table: str, measure: str) -> Optional[Dict]:
        """Execute measure to get single value."""
        try:
            query = f"EVALUATE ROW(\"Value\", [{measure}])"
            result = self.qe.validate_and_execute_dax(query, top_n=1)
            
            if result.get('success') and result.get('rows'):
                row = result['rows'][0]
                value = row.get('Value') or row.get('[Value]')
                return {'value': value}
            return None
        except Exception as e:
            logger.debug(f"Could not get measure value for {measure}: {e}")
            return None
    
    def _get_measure_trend(self, table: str, measure: str, sample_rows: int) -> Optional[Dict]:
        """Get time-series trend data for measure."""
        try:
            # Find date table
            date_table = self._find_date_table()
            if not date_table:
                return None
            
            # Try to get monthly trend
            query = f"""
            EVALUATE
            TOPN({sample_rows},
                SUMMARIZE(
                    '{date_table}',
                    '{date_table}'[Year],
                    '{date_table}'[Month],
                    "Value", [{measure}]
                ),
                '{date_table}'[Year], ASC,
                '{date_table}'[Month], ASC
            )
            """
            
            result = self.qe.validate_and_execute_dax(query, top_n=sample_rows)
            
            if result.get('success') and result.get('rows'):
                return {
                    'data': result['rows'],
                    'chart_type': 'line',
                    'x_field': 'Month',
                    'y_field': 'Value',
                    'title': f"{measure} Trend"
                }
            return None
        except Exception as e:
            logger.debug(f"Could not get trend for {measure}: {e}")
            return None
    
    def _get_grouped_data(self, table: str, measure: str, dimension_table: str, sample_rows: int) -> Optional[Dict]:
        """Get measure grouped by dimension."""
        try:
            # Find first text column in dimension table
            cols = self.qe.execute_info_query("COLUMNS", table_name=dimension_table)
            if not cols.get('success'):
                return None
            
            text_col = None
            for col in cols.get('rows', []):
                data_type = col.get('DataType', col.get('[DataType]', ''))
                if 'string' in str(data_type).lower() or 'text' in str(data_type).lower():
                    text_col = self._extract_name(col)
                    break
            
            if not text_col:
                return None
            
            query = f"""
            EVALUATE
            TOPN({sample_rows},
                SUMMARIZE(
                    '{dimension_table}',
                    '{dimension_table}'[{text_col}],
                    "Value", [{measure}]
                ),
                [Value], DESC
            )
            """
            
            result = self.qe.validate_and_execute_dax(query, top_n=sample_rows)
            
            if result.get('success') and result.get('rows'):
                return {
                    'data': result['rows'],
                    'dimension': text_col,
                    'measure': measure
                }
            return None
        except Exception as e:
            logger.debug(f"Could not get grouped data: {e}")
            return None
    
    def _get_best_grouping(self, table: str, measure: str, sample_rows: int) -> Optional[Dict]:
        """Find best dimension to group measure by."""
        # This is a simplified version - could be enhanced
        dimension_tables = self._find_dimension_tables()
        
        for dim_table in dimension_tables[:3]:
            grouped = self._get_grouped_data(table, measure, dim_table, sample_rows)
            if grouped and len(grouped.get('data', [])) > 2:
                return grouped
        
        return None
    
    def _get_table_preview(self, table: str, sample_rows: int) -> Optional[Dict]:
        """Get preview of table data."""
        try:
            query = f"EVALUATE TOPN({sample_rows}, '{table}')"
            result = self.qe.validate_and_execute_dax(query, top_n=sample_rows)
            
            if result.get('success'):
                return {
                    'rows': result.get('rows', []),
                    'column_count': len(result.get('rows', [[]])[0]) if result.get('rows') else 0
                }
            return None
        except Exception as e:
            logger.debug(f"Could not preview table {table}: {e}")
            return None
    
    def _get_table_measures(self, table: str) -> List[Dict]:
        """Get measures for a table."""
        try:
            result = self.qe.execute_info_query_with_fallback("MEASURES", table_name=table, exclude_columns=['Expression'])
            
            if result.get('success'):
                measures = []
                for row in result.get('rows', []):
                    measures.append({
                        'measure': self._extract_name(row),
                        'format': row.get('FormatString', row.get('[FormatString]'))
                    })
                return measures
            return []
        except Exception:
            return []
    
    def _get_relationships(self, tables: List[str]) -> List[Dict]:
        """Get relationships involving specified tables."""
        try:
            result = self.qe.execute_info_query("RELATIONSHIPS")
            
            if not result.get('success'):
                return []
            
            filtered_rels = []
            for rel in result.get('rows', []):
                from_table = rel.get('FromTable', rel.get('[FromTable]', ''))
                to_table = rel.get('ToTable', rel.get('[ToTable]', ''))
                
                if any(t in str(from_table) or t in str(to_table) for t in tables):
                    filtered_rels.append({
                        'from_table': from_table,
                        'to_table': to_table,
                        'from_column': rel.get('FromColumn', rel.get('[FromColumn]', '')),
                        'to_column': rel.get('ToColumn', rel.get('[ToColumn]', ''))
                    })
            
            return filtered_rels
        except Exception:
            return []
    
    def _find_key_measures(self, keywords: List[str]) -> List[Dict]:
        """Find measures matching keywords."""
        try:
            result = self.qe.execute_info_query("MEASURES", exclude_columns=['Expression'])
            
            if not result.get('success'):
                return []
            
            matches = []
            for row in result.get('rows', []):
                measure_name = self._extract_name(row).lower()
                table_name = row.get('Table', row.get('[Table]', ''))
                
                if any(keyword in measure_name for keyword in keywords):
                    matches.append({
                        'table': table_name,
                        'measure': self._extract_name(row),
                        'format': row.get('FormatString', row.get('[FormatString]'))
                    })
            
            return matches
        except Exception:
            return []
    
    def _find_fact_tables(self) -> List[str]:
        """Identify likely fact tables (tables with many measures)."""
        try:
            measures_result = self.qe.execute_info_query("MEASURES", exclude_columns=['Expression'])
            
            if not measures_result.get('success'):
                return []
            
            # Count measures per table
            table_counts = {}
            for row in measures_result.get('rows', []):
                table = row.get('Table', row.get('[Table]', ''))
                table_counts[table] = table_counts.get(table, 0) + 1
            
            # Return tables with most measures
            sorted_tables = sorted(table_counts.items(), key=lambda x: x[1], reverse=True)
            return [t[0] for t in sorted_tables if t[1] > 0]
        except Exception:
            return []
    
    def _find_dimension_tables(self) -> List[str]:
        """Identify likely dimension tables."""
        try:
            tables_result = self.qe.execute_info_query("TABLES")
            measures_result = self.qe.execute_info_query("MEASURES", exclude_columns=['Expression'])
            
            if not tables_result.get('success'):
                return []
            
            # Tables with few/no measures are likely dimensions
            measure_tables = set()
            if measures_result.get('success'):
                for row in measures_result.get('rows', []):
                    table = row.get('Table', row.get('[Table]', ''))
                    measure_tables.add(table)
            
            all_tables = [self._extract_name(t) for t in tables_result.get('rows', [])]
            
            # Dimension tables are those without many measures
            dimension_tables = [t for t in all_tables if t not in measure_tables]
            
            # Also look for naming patterns
            dimension_keywords = ['dim', 'dimension', 'category', 'type', 'status', 'customer', 'product', 'location']
            dimension_tables.extend([
                t for t in all_tables 
                if any(kw in t.lower() for kw in dimension_keywords) and t not in dimension_tables
            ])
            
            return dimension_tables[:10]  # Limit to reasonable number
        except Exception:
            return []
    
    def _find_date_table(self) -> Optional[str]:
        """Find the date/calendar table."""
        try:
            tables_result = self.qe.execute_info_query("TABLES")
            
            if not tables_result.get('success'):
                return None
            
            for table in tables_result.get('rows', []):
                name = self._extract_name(table).lower()
                if 'date' in name or 'calendar' in name or 'time' in name:
                    return self._extract_name(table)
            
            return None
        except Exception:
            return None
    
    def _recommend_chart_libraries(self, result: Dict) -> Dict:
        """Recommend chart libraries based on visualization types."""
        recommendations = {
            'primary': 'Recharts',
            'alternatives': ['Chart.js', 'Plotly'],
            'reasoning': []
        }
        
        chart_types = set()
        for rec in result.get('chart_recommendations', []):
            chart_types.add(rec.get('type', ''))
        
        if 'kpi_grid' in chart_types or 'kpi_card' in chart_types:
            recommendations['reasoning'].append(
                'KPI cards work best with native React + Tailwind CSS for clean, responsive design'
            )
        
        if any(t in chart_types for t in ['line_chart', 'bar_chart', 'area_chart']):
            recommendations['reasoning'].append(
                'Recharts recommended for standard BI charts - good balance of simplicity and customization'
            )
        
        if 'financial_table' in chart_types:
            recommendations['reasoning'].append(
                'Financial tables best implemented with native React for precise formatting control'
            )
        
        return recommendations
    
    def _suggest_layout_pattern(self, result: Dict) -> Dict:
        """Suggest dashboard layout pattern."""
        request_type = result.get('request_type', 'overview')
        
        patterns = {
            'executive_summary': {
                'name': 'Executive KPI Grid + Trends',
                'structure': '3-column KPI grid at top, 2-column charts below',
                'tailwind_classes': 'grid grid-cols-3 gap-4 for KPIs, grid grid-cols-2 gap-6 for charts'
            },
            'operational': {
                'name': 'Operational Dashboard',
                'structure': 'Summary metrics bar, main content area with tabs',
                'tailwind_classes': 'flex flex-col, use tabs for different metric groups'
            },
            'financial': {
                'name': 'Financial Statements',
                'structure': 'Side-by-side financial tables with variance columns',
                'tailwind_classes': 'grid grid-cols-2 gap-8 for statement comparison'
            },
            'overview': {
                'name': 'Mixed Dashboard',
                'structure': 'KPI row at top, mixed chart/table grid below',
                'tailwind_classes': 'flex flex-col gap-6, grid for content area'
            }
        }
        
        return patterns.get(request_type, patterns['overview'])
    
    def _generate_chart_recommendations(self, measures: List[Dict]) -> List[Dict]:
        """Generate chart recommendations for measures."""
        recommendations = []
        
        for measure_data in measures:
            chart_type = measure_data.get('chart_type', 'auto')
            
            if chart_type == 'auto':
                # Auto-detect based on data
                if 'trend_data' in measure_data:
                    chart_type = 'line'
                elif 'grouped_data' in measure_data:
                    chart_type = 'bar'
                else:
                    chart_type = 'kpi_card'
            
            recommendations.append({
                'measure': measure_data['measure'],
                'chart_type': chart_type,
                'library': 'Recharts' if chart_type in ['line', 'bar', 'area'] else 'native React'
            })
        
        return recommendations


# Tool registration helpers for MCP server integration

def create_viz_tool_handlers(connection_state, config):
    """
    Create tool handler functions for MCP server registration.
    
    Usage in pbixray_server_enhanced.py:
        from server.handlers.visualization_tools import create_viz_tool_handlers
        viz_handlers = create_viz_tool_handlers(connection_state, config)
        # Register handlers in tool dispatch
    """
    viz_tools = VisualizationTools(connection_state, config)
    
    def handle_prepare_dashboard_data(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for dashboard mockup generation."""
        return viz_tools.prepare_dashboard_data(
            request_type=arguments.get('request_type', 'overview'),
            tables=arguments.get('tables'),
            measures=arguments.get('measures'),
            max_rows=int(arguments.get('max_rows', 100)),
            sample_rows=int(arguments.get('sample_rows', 20))
        )
    
    def handle_get_chart_data(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get formatted data for specific chart type."""
        chart_type = arguments.get('chart_type', 'line')
        table = arguments.get('table')
        measure = arguments.get('measure')
        dimension = arguments.get('dimension')
        sample_rows = int(arguments.get('sample_rows', 20))
        
        if chart_type == 'kpi_card':
            value = viz_tools._get_measure_value(table, measure)
            return {'success': True, 'data': value, 'chart_type': 'kpi_card'}
        elif chart_type in ['line', 'area']:
            trend = viz_tools._get_measure_trend(table, measure, sample_rows)
            return {'success': True, 'data': trend, 'chart_type': chart_type}
        elif chart_type == 'bar':
            if dimension:
                grouped = viz_tools._get_grouped_data(table, measure, dimension, sample_rows)
            else:
                grouped = viz_tools._get_best_grouping(table, measure, sample_rows)
            return {'success': True, 'data': grouped, 'chart_type': 'bar'}
        else:
            return {'success': False, 'error': f'Unsupported chart type: {chart_type}'}
    
    def handle_recommend_visualizations(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend visualizations for model or specific measures."""
        measures = arguments.get('measures')
        
        if measures:
            # Custom measures
            result = viz_tools._prepare_custom_measures(measures, 100, 20)
        else:
            # Model-wide recommendations
            key_measures = viz_tools._find_key_measures(['total', 'revenue', 'sales', 'profit', 'count'])
            recommendations = viz_tools._generate_chart_recommendations([
                {**m, 'chart_type': 'auto'} for m in key_measures[:10]
            ])
            result = {
                'data': {'recommendations': recommendations},
                'chart_recommendations': recommendations
            }
        
        return {
            'success': True,
            'recommendations': result.get('chart_recommendations', []),
            'library_recommendations': viz_tools._recommend_chart_libraries(result),
            'layout_pattern': viz_tools._suggest_layout_pattern(result)
        }
    
    return {
        'viz_prepare_dashboard_data': handle_prepare_dashboard_data,
        'viz_get_chart_data': handle_get_chart_data,
        'viz_recommend_visualizations': handle_recommend_visualizations
    }
