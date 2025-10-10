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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("mcp_powerbi_finvision.visualization")


class VisualizationTools:
    """Prepares Power BI model data for dashboard visualization mockups."""
    
    def __init__(self, connection_state, config):
        self.connection_state = connection_state
        self.config = config
        self._context: Optional[Dict[str, List[str]]] = None
        self._memory_path = Path(__file__).resolve().parent / "viz_memory.json"
        try:
            self._memory_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.debug("Could not ensure viz memory directory", exc_info=True)
        self._memory = self._load_memory()
        self._memo_cache: Dict[str, Any] = {}
    
    @property
    def qe(self):
        if not self.connection_state:
            return None
        return getattr(self.connection_state, 'query_executor', None)
        
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
            self._set_context()
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
            result['layout_pattern']['single_page'] = True
            result['layout_pattern'].setdefault('max_sections', 6)
            self._record_usage('layout', result['layout_pattern'].get('name'))
            result['page_blueprint'] = self._build_page_blueprint(result.get('chart_recommendations', []))
            
            if self._context:
                result['guidance'] = self._context
            result['memory_insights'] = {
                'popular_measures': self._get_top_usage('measure'),
                'popular_dimensions': self._get_top_usage('dimension'),
                'popular_layouts': self._get_top_usage('layout')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error preparing dashboard data: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'visualization_preparation_error'
            }
        finally:
            self._context = None
    
    def _load_memory(self) -> Dict[str, Dict[str, int]]:
        """Load lightweight visualization usage memory from disk."""
        default = {'measure_usage': {}, 'dimension_usage': {}, 'layout_usage': {}}
        try:
            if self._memory_path.exists():
                data = json.loads(self._memory_path.read_text(encoding='utf-8'))
                for key in default:
                    if isinstance(data.get(key), dict):
                        default[key].update({str(k): int(v) for k, v in data[key].items()})
        except Exception:
            logger.debug("Could not load viz memory; continuing with defaults", exc_info=True)
        return default
    
    def _save_memory(self) -> None:
        """Persist lightweight memory to disk."""
        try:
            self._memory_path.write_text(json.dumps(self._memory, indent=2), encoding='utf-8')
        except Exception:
            logger.debug("Could not persist viz memory", exc_info=True)
    
    def _record_usage(self, category: str, key: Optional[str]) -> None:
        """Track usage frequency for measures, dimensions, and layouts."""
        if not key:
            return
        bucket = self._memory.setdefault(f"{category}_usage", {})
        bucket[key] = bucket.get(key, 0) + 1
        # Keep buckets compact
        if len(bucket) > 50:
            # Drop least used entries to avoid unlimited growth
            sorted_items = sorted(bucket.items(), key=lambda item: item[1], reverse=True)[:50]
            self._memory[f"{category}_usage"] = dict(sorted_items)
        self._save_memory()
    
    def _get_top_usage(self, category: str, limit: int = 5) -> List[str]:
        bucket = self._memory.get(f"{category}_usage", {})
        return [name for name, _ in sorted(bucket.items(), key=lambda item: item[1], reverse=True)[:limit]]
    
    def _make_cache_key(self, prefix: str, *parts: Any) -> str:
        safe_parts = []
        for part in parts:
            if isinstance(part, (list, dict)):
                safe_parts.append(json.dumps(part, sort_keys=True))
            else:
                safe_parts.append(str(part))
        return f"{prefix}:{'|'.join(safe_parts)}"
    
    def _cache_get(self, key: str) -> Any:
        return self._memo_cache.get(key)
    
    def _cache_set(self, key: str, value: Any) -> None:
        self._memo_cache[key] = value
        # Simple cap to avoid uncontrolled growth
        if len(self._memo_cache) > 256:
            # Remove oldest inserted item
            oldest_key = next(iter(self._memo_cache))
            self._memo_cache.pop(oldest_key, None)
    
    def _set_context(self) -> None:
        self._context = {'warnings': [], 'suggestions': []}
    
    def _add_guidance(self, warning: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        if self._context is None:
            return
        if warning:
            self._context['warnings'].append(warning)
        if suggestion:
            self._context['suggestions'].append(suggestion)
    
    def _quote_table(self, name: str) -> str:
        norm = (name or "").replace("'", "''")
        return f"'{norm}'"
    
    def _quote_column(self, name: str) -> str:
        norm = (name or "").replace(']', ']]')
        return f"[{norm}]"
    
    def _quote_measure(self, name: str) -> str:
        norm = (name or "").replace(']', ']]')
        return f"[{norm}]"
    
    def _table_column_ref(self, table: str, column: str) -> str:
        return f"{self._quote_table(table)}[{(column or '').replace(']', ']]')}]"
    
    def _normalize_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize keys by stripping brackets and harmonizing casing."""
        normalized = []
        for row in rows or []:
            clean = {}
            for key, value in (row or {}).items():
                if isinstance(key, str) and key.startswith('[') and key.endswith(']'):
                    clean_key = key[1:-1]
                else:
                    clean_key = key
                clean[clean_key] = value
            normalized.append(clean)
        return normalized
    
    def _build_chart_payload(
        self,
        chart_type: str,
        title: str,
        data: Optional[List[Dict[str, Any]]],
        spec: Dict[str, Any],
        reasoning: str,
        render_hints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = {
            'chart_type': chart_type,
            'type': chart_type,
            'title': title,
            'data': data or [],
            'spec': spec,
            'reasoning': reasoning,
            'render_hints': render_hints or {}
        }
        # Ensure one-page guidance always present
        payload['render_hints'].setdefault('single_page', True)
        payload['render_hints'].setdefault('recommended_width', '50%')
        return payload
    
    def _build_page_blueprint(self, charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        sections: Dict[str, Dict[str, Any]] = {}
        for chart in charts or []:
            hints = chart.get('render_hints', {})
            slot = hints.get('recommended_position', 'mid')
            section = sections.setdefault(slot, {'slot': slot, 'charts': [], 'tailwind': None})
            section['charts'].append(chart.get('title'))
            if hints.get('tailwind'):
                section['tailwind'] = hints['tailwind']
        ordered_slots = ['top', 'mid', 'bottom', 'background']
        ordered_sections = [sections[s] for s in ordered_slots if s in sections]
        # Append any other slots deterministically
        for slot, section in sections.items():
            if slot not in ordered_slots:
                ordered_sections.append(section)
        return {
            'single_page': True,
            'max_sections': len(ordered_sections),
            'sections': ordered_sections
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
        if not measures:
            self._add_guidance(
                warning='No executive summary measures detected',
                suggestion='Create measures containing keywords like Total, Revenue, Sales, Profit for richer KPI coverage'
            )
        
        charts: List[Dict[str, Any]] = []
        for measure_info in measures[:6]:  # Top 6 KPIs
            table = measure_info['table']
            measure = measure_info['measure']
            self._record_usage('measure', measure)
            
            # Get current value
            current_value = self._get_measure_value(table, measure)
            
            if current_value:
                kpi_data = {
                    'label': measure,
                    'value': current_value.get('value'),
                    'format': measure_info.get('format'),
                    'table': table,
                    'chart_type': 'kpi_card',
                    'reasoning': f"{measure} matches executive keywords (Total/Revenue/Sales/Profit/Margin).",
                    'render_hints': {
                        'component': 'KpiCard',
                        'tailwind': 'rounded-lg bg-surface shadow-sm p-4 flex flex-col gap-2',
                        'single_page': True
                    }
                }
                data['kpi_cards'].append(kpi_data)
                
                # Try to get trend data if date dimension exists
                trend = self._get_measure_trend(table, measure, sample_rows)
                if trend:
                    data['trend_charts'].append(trend)
                    charts.append(self._build_chart_payload(
                        'line',
                        f"{measure} trend",
                        trend['data'],
                        {
                            'x_field': trend['x_field'],
                            'y_field': trend['y_field'],
                            'series': trend.get('series', 'single'),
                            'time_grain': trend.get('grain', 'month')
                        },
                        trend.get('reasoning', f"Monthly trend for {measure} over time."),
                        trend.get('render_hints')
                    ))
                else:
                    self._add_guidance(
                        warning=f"Trend data unavailable for {measure}",
                        suggestion='Ensure a dedicated Date/Calendar table exists with Year/Month columns.'
                    )
        
        # KPI grid recommendation (single page row)
        if data['kpi_cards']:
            charts.insert(0, self._build_chart_payload(
                'kpi_grid',
                'Executive KPI grid',
                data['kpi_cards'],
                {
                    'layout': 'grid',
                    'columns': min(3, max(1, len(data['kpi_cards']))),
                    'label_field': 'label',
                    'value_field': 'value',
                    'format_field': 'format'
                },
                'Executive dashboards highlight top KPIs in a compact grid to fit a single page.',
                {
                    'component': 'KpiGrid',
                    'tailwind': 'grid gap-4 grid-cols-1 md:grid-cols-3',
                    'recommended_position': 'top',
                    'single_page': True
                }
            ))
        
        return {
            'data': data,
            'chart_recommendations': charts
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
        if not dimension_tables:
            self._add_guidance(
                warning='No dimension tables detected for operational breakdowns',
                suggestion='Add descriptive dimension tables (e.g., Product, Customer) or mark them as such.'
            )
        
        # Find metrics to group
        measures = self._find_key_measures(['count', 'quantity', 'amount'])
        if not measures:
            self._add_guidance(
                warning='No operational measures detected',
                suggestion='Create measures containing Count, Quantity, or Amount keywords to enable operational charts.'
            )
        
        charts: List[Dict[str, Any]] = []
        
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
                    self._record_usage('measure', measure_info['measure'])
                    self._record_usage('dimension', grouped.get('dimension_key', grouped.get('dimension')))
                    chart_title = f"{measure_info['measure']} by {grouped.get('dimension')}"
                    data['bar_charts'].append({
                        'title': chart_title,
                        'data': grouped,
                        'chart_type': 'bar',
                        'x_axis': grouped.get('dimension'),
                        'y_axis': measure_info['measure']
                    })
                    charts.append(self._build_chart_payload(
                        'bar',
                        chart_title,
                        grouped.get('data'),
                        {
                            'x_field': grouped.get('dimension'),
                            'y_field': 'Value',
                            'series': 'single',
                            'sort': 'desc'
                        },
                        f"Grouped {measure_info['measure']} by high-value dimension {grouped.get('dimension')} for operational view.",
                        {
                            'component': 'BarChart',
                            'tailwind': 'w-full lg:w-1/2',
                            'recommended_position': 'mid',
                            'single_page': True
                        }
                    ))
        
        return {
            'data': data,
            'chart_recommendations': charts
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
        if not financial_measures:
            self._add_guidance(
                warning='No financial measures detected',
                suggestion='Ensure measures contain finance keywords (Revenue, Expense, Profit, EBITDA) to populate financial dashboards.'
            )
        
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
        
        charts: List[Dict[str, Any]] = []

        # Create financial statement structure
        for category, items in categories.items():
            if items:
                statement_data = []
                for item in items[:5]:
                    value = self._get_measure_value(item['table'], item['measure'])
                    if value:
                        self._record_usage('measure', item['measure'])
                        statement_data.append({
                            'line_item': item['measure'],
                            'value': value.get('value'),
                            'format': item.get('format'),
                            'reasoning': f"{item['measure']} categorized under {category} based on naming.",
                            'render_hints': {
                                'component': 'FinancialRow',
                                'single_page': True
                            }
                        })
                
                if statement_data:
                    data['financial_statements'].append({
                        'category': category,
                        'items': statement_data
                    })
                    charts.append(self._build_chart_payload(
                        'financial_table',
                        f"{category.title()} summary",
                        statement_data,
                        {
                            'layout': 'table',
                            'columns': ['line_item', 'value'],
                            'format_field': 'format'
                        },
                        f"Arrange {category} metrics in accounting-style table for single-page readability.",
                        {
                            'component': 'FinancialTable',
                            'tailwind': 'grid grid-cols-1 gap-2',
                            'recommended_position': 'full-width',
                            'single_page': True
                        }
                    ))
        
        return {
            'data': data,
            'chart_recommendations': charts,
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
        if not target_tables:
            self._add_guidance(
                warning='No fact tables detected for overview dashboard',
                suggestion='Identify one or more fact tables with measures to populate overview insights.'
            )
        
        charts: List[Dict[str, Any]] = []
        
        for table in target_tables:
            # Get sample data
            preview = self._get_table_preview(table, sample_rows)
            if preview:
                data['sample_data'][table] = preview
                charts.append(self._build_chart_payload(
                    'table',
                    f"{table} sample (top {len(preview.get('rows', []))})",
                    preview.get('rows'),
                    {
                        'layout': 'table',
                        'columns': preview.get('columns', []),
                        'max_rows': sample_rows
                    },
                    f"Provide a concise sample of {table} for one-page context.",
                    {
                        'component': 'DataTable',
                        'tailwind': 'w-full lg:w-1/2',
                        'recommended_position': 'bottom',
                        'single_page': True
                    }
                ))
            
            # Get measures for this table
            table_measures = self._get_table_measures(table)
            for measure_info in table_measures[:3]:
                value = self._get_measure_value(table, measure_info['measure'])
                if value:
                    self._record_usage('measure', measure_info['measure'])
                    data['key_metrics'].append({
                        'table': table,
                        'measure': measure_info['measure'],
                        'value': value.get('value'),
                        'format': measure_info.get('format'),
                        'reasoning': f"{measure_info['measure']} is a primary metric on {table}.",
                        'render_hints': {
                            'component': 'KpiCard',
                            'single_page': True
                        }
                    })
        
        # Get relationships for context
        rels = self._get_relationships(target_tables)
        data['relationships'] = rels
        if rels:
            charts.append(self._build_chart_payload(
                'network',
                'Model relationships snapshot',
                rels[:20],
                {
                    'layout': 'graph',
                    'from_field': 'from_table',
                    'to_field': 'to_table'
                },
                'Include a lightweight relationship graph to anchor overview context on a single page.',
                {
                    'component': 'RelationshipGraph',
                    'tailwind': 'w-full',
                    'recommended_position': 'background',
                    'single_page': True
                }
            ))
        
        if data['key_metrics']:
            charts.insert(0, self._build_chart_payload(
                'kpi_grid',
                'Overview KPI cards',
                data['key_metrics'][:6],
                {
                    'layout': 'grid',
                    'columns': min(3, max(1, len(data['key_metrics'][:6]))),
                    'label_field': 'measure',
                    'value_field': 'value',
                    'format_field': 'format'
                },
                'Condense key metrics to a single-page KPI strip.',
                {
                    'component': 'KpiGrid',
                    'tailwind': 'grid gap-4 grid-cols-1 md:grid-cols-3',
                    'recommended_position': 'top',
                    'single_page': True
                }
            ))
        
        return {
            'data': data,
            'chart_recommendations': charts
        }
    
    def _prepare_custom_measures(self, measures: List[Dict], max_rows: int, sample_rows: int) -> Dict:
        """Prepare data for custom list of measures."""
        data = {
            'measures': [],
            'chart_data': []
        }
        charts: List[Dict[str, Any]] = []
        
        for measure_spec in measures:
            table = measure_spec.get('table')
            measure = measure_spec.get('measure')
            chart_type = measure_spec.get('chart_type', 'auto')
            
            if not table or not measure:
                self._add_guidance(
                    warning='Custom measure entry missing table or measure name',
                    suggestion='Provide both table and measure for custom visualizations.'
                )
                continue
            
            # Get measure value
            value = self._get_measure_value(table, measure)
            
            if value:
                self._record_usage('measure', measure)
                measure_data = {
                    'table': table,
                    'measure': measure,
                    'value': value.get('value'),
                    'chart_type': chart_type
                }
                
                # Get additional data based on chart type
                if chart_type in ['line', 'area', 'trend', 'auto']:
                    trend = self._get_measure_trend(table, measure, sample_rows)
                    if trend:
                        measure_data['trend_data'] = trend
                        charts.append(self._build_chart_payload(
                            'line',
                            f"{measure} trend",
                            trend['data'],
                            {
                                'x_field': trend['x_field'],
                                'y_field': trend['y_field'],
                                'time_grain': trend.get('grain', 'month')
                            },
                            trend.get('reasoning', f"Trend insight for {measure}."),
                            trend.get('render_hints')
                        ))
                    elif chart_type not in ['auto']:
                        self._add_guidance(
                            warning=f"Trend data unavailable for {measure}",
                            suggestion='Ensure a Date dimension with Year/Month exists or choose a categorical visualization.'
                        )
                if chart_type in ['bar', 'column', 'auto']:
                    # Try to find a dimension to group by
                    grouped = self._get_best_grouping(table, measure, sample_rows)
                    if grouped:
                        measure_data['grouped_data'] = grouped
                        self._record_usage('dimension', grouped.get('dimension_key', grouped.get('dimension')))
                        charts.append(self._build_chart_payload(
                            'bar',
                            f"{measure} by {grouped.get('dimension')}",
                            grouped.get('data'),
                            {
                                'x_field': grouped.get('dimension'),
                                'y_field': 'Value',
                                'series': 'single',
                                'sort': 'desc'
                            },
                            grouped.get('reasoning', f"Grouped {measure} by {grouped.get('dimension')} for categorical comparison."),
                            grouped.get('render_hints')
                        ))
                    elif chart_type in ['bar', 'column']:
                        self._add_guidance(
                            warning=f"No grouping found for {measure}",
                            suggestion='Provide a dimension explicitly or ensure descriptive text columns exist in dimension tables.'
                        )
                
                data['measures'].append(measure_data)
        
        charts = charts or self._generate_chart_recommendations(data['measures'])
        
        return {
            'data': data,
            'chart_recommendations': charts
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
            cache_key = self._make_cache_key('measure_value', table, measure)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            query = f"EVALUATE ROW(\"Value\", {self._quote_measure(measure)})"
            result = self.qe.validate_and_execute_dax(query, top_n=1)
            
            if result.get('success') and result.get('rows'):
                row = self._normalize_rows(result['rows'])[0]
                value = row.get('Value') or row.get('value')
                payload = {'value': value}
                self._cache_set(cache_key, payload)
                return payload
            return None
        except Exception as e:
            logger.debug(f"Could not get measure value for {measure}: {e}")
            return None
    
    def _get_measure_trend(self, table: str, measure: str, sample_rows: int) -> Optional[Dict]:
        """Get time-series trend data for measure."""
        try:
            cache_key = self._make_cache_key('measure_trend', table, measure, sample_rows)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            # Find date table
            date_table = self._find_date_table()
            if not date_table:
                self._add_guidance(
                    warning='No date table detected for trend visualizations',
                    suggestion='Mark a Date table or add a Calendar table with Year/Month columns.'
                )
                return None
            
            time_columns = self._detect_time_columns(date_table)
            if not time_columns:
                self._add_guidance(
                    warning=f"Could not detect usable time columns on {date_table}",
                    suggestion='Ensure the date table has Year, Month, and Date columns.'
                )
                return None
            
            measure_expr = self._quote_measure(measure)
            year_col = time_columns.get('year')
            month_num_col = time_columns.get('month_number')
            month_name_col = time_columns.get('month_name')
            date_col = time_columns.get('date')
            
            if year_col and month_num_col and month_name_col:
                year_ref = self._table_column_ref(date_table, year_col)
                month_num_ref = self._table_column_ref(date_table, month_num_col)
                month_name_ref = self._table_column_ref(date_table, month_name_col)
                query = f"""
EVALUATE
VAR __Trend =
    SUMMARIZECOLUMNS(
        {year_ref},
        {month_num_ref},
        "MonthLabel", MAX({month_name_ref}),
        "Value", {measure_expr}
    )
VAR __Limited =
    TOPN({sample_rows}, __Trend, {year_ref}, DESC, {month_num_ref}, DESC)
RETURN
    __Limited
ORDER BY
    {year_ref},
    {month_num_ref}
"""
                x_field = 'MonthLabel'
                grain = 'month'
            elif date_col:
                date_ref = self._table_column_ref(date_table, date_col)
                query = f"""
EVALUATE
VAR __Trend =
    SUMMARIZECOLUMNS(
        {date_ref},
        "Value", {measure_expr}
    )
VAR __Limited =
    TOPN({sample_rows}, __Trend, {date_ref}, DESC)
RETURN
    ADDCOLUMNS(__Limited, "MonthLabel", FORMAT({date_ref}, "MMM yyyy"))
ORDER BY
    {date_ref}
"""
                x_field = 'MonthLabel'
                grain = 'period'
            else:
                self._add_guidance(
                    warning=f"No compatible date column found on {date_table}",
                    suggestion='Add a date column named Date or similar for time-series visuals.'
                )
                return None
            
            result = self.qe.validate_and_execute_dax(query, top_n=sample_rows)
            
            if result.get('success') and result.get('rows'):
                rows = self._normalize_rows(result['rows'])
                payload = {
                    'data': rows,
                    'chart_type': 'line',
                    'x_field': x_field,
                    'y_field': 'Value',
                    'title': f"{measure} Trend",
                    'grain': grain,
                    'series': 'single',
                    'reasoning': f"Detected temporal pattern using {date_table} ({grain}).",
                    'render_hints': {
                        'component': 'LineChart',
                        'tailwind': 'w-full lg:w-1/2',
                        'recommended_position': 'mid',
                        'single_page': True
                    }
                }
                self._cache_set(cache_key, payload)
                return payload
            return None
        except Exception as e:
            logger.debug(f"Could not get trend for {measure}: {e}")
            return None
    
    def _get_grouped_data(
        self,
        table: str,
        measure: str,
        dimension_table: str,
        sample_rows: int,
        preferred_column: Optional[str] = None
    ) -> Optional[Dict]:
        """Get measure grouped by dimension."""
        try:
            cache_key = self._make_cache_key('grouped', table, measure, dimension_table, sample_rows, preferred_column)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            # Find first text column in dimension table
            cols = self.qe.execute_info_query("COLUMNS", table_name=dimension_table)
            if not cols.get('success'):
                return None
            
            text_col = None
            for col in cols.get('rows', []):
                data_type = str(col.get('DataType', col.get('[DataType]', ''))).lower()
                candidate = self._extract_name(col)
                lowered = candidate.lower()
                if preferred_column and candidate.lower() == preferred_column.lower():
                    text_col = candidate
                    break
                if 'string' in data_type or 'text' in data_type or 'name' in lowered:
                    if 'key' in lowered and 'name' not in lowered:
                        continue
                    text_col = self._extract_name(col)
                    break
            
            if not text_col:
                self._add_guidance(
                    warning=f"No descriptive column found on {dimension_table}",
                    suggestion='Add a text column (e.g., Name/Description) for categorical grouping.'
                )
                return None
            
            dim_ref = self._table_column_ref(dimension_table, text_col)
            measure_expr = self._quote_measure(measure)
            query = f"""
EVALUATE
VAR __Agg =
    SUMMARIZECOLUMNS(
        {dim_ref},
        "Value", {measure_expr}
    )
VAR __Limited =
    TOPN({sample_rows}, __Agg, [Value], DESC)
RETURN
    __Limited
ORDER BY
    [Value] DESC
"""
            
            result = self.qe.validate_and_execute_dax(query, top_n=sample_rows)
            
            if result.get('success') and result.get('rows'):
                rows = self._normalize_rows(result['rows'])
                payload = {
                    'data': rows,
                    'dimension': text_col,
                    'dimension_table': dimension_table,
                    'dimension_key': f"{dimension_table}.{text_col}",
                    'measure': measure,
                    'reasoning': f"Detected {text_col} on {dimension_table} with strong variance for {measure}.",
                    'render_hints': {
                        'component': 'BarChart',
                        'tailwind': 'w-full lg:w-1/2',
                        'recommended_position': 'mid',
                        'single_page': True
                    }
                }
                self._cache_set(cache_key, payload)
                return payload
            self._add_guidance(
                warning=f"No grouped rows returned for {measure} on {dimension_table}",
                suggestion='Verify relationships between fact and dimension tables or try a different dimension.'
            )
            return None
        except Exception as e:
            logger.debug(f"Could not get grouped data: {e}")
            return None
    
    def _get_best_grouping(self, table: str, measure: str, sample_rows: int) -> Optional[Dict]:
        """Find best dimension to group measure by."""
        # This is a simplified version - could be enhanced
        dimension_tables = self._find_dimension_tables()
        if not dimension_tables:
            self._add_guidance(
                warning='No dimension tables available for grouping',
                suggestion='Consider adding dimension tables or ensure they are visible.'
            )
            return None
        
        preferred = self._get_top_usage('dimension', limit=10)
        preferred_pairs: List[Tuple[str, Optional[str]]] = []
        ordered_tables: List[str] = []
        for key in preferred:
            if '.' in key:
                table_name, column_name = key.split('.', 1)
            else:
                table_name, column_name = key, None
            preferred_pairs.append((table_name, column_name))
            if table_name in dimension_tables and table_name not in ordered_tables:
                ordered_tables.append(table_name)
        ordered_tables.extend([t for t in dimension_tables if t not in ordered_tables])
        
        # Try memory-based pairs first
        for table_name, column_name in preferred_pairs:
            if table_name in dimension_tables:
                grouped = self._get_grouped_data(table, measure, table_name, sample_rows, preferred_column=column_name)
                if grouped and len(grouped.get('data', [])) > 2:
                    return grouped
        
        for dim_table in ordered_tables[:5]:
            grouped = self._get_grouped_data(table, measure, dim_table, sample_rows)
            if grouped and len(grouped.get('data', [])) > 2:
                return grouped
        
        self._add_guidance(
            warning=f"No suitable grouping found for {measure}",
            suggestion='Specify a dimension manually or review relationships to ensure data can be grouped.'
        )
        
        return None
    
    def _get_table_preview(self, table: str, sample_rows: int) -> Optional[Dict]:
        """Get preview of table data."""
        try:
            cache_key = self._make_cache_key('table_preview', table, sample_rows)
            cached = self._cache_get(cache_key)
            if cached is not None:
                return cached
            table_ref = self._quote_table(table)
            columns_info = self.qe.execute_info_query("COLUMNS", table_name=table)
            columns = []
            if columns_info.get('success'):
                columns = [self._extract_name(c) for c in columns_info.get('rows', [])]
            query = f"EVALUATE SAMPLE({sample_rows}, {table_ref})"
            result = self.qe.validate_and_execute_dax(query, top_n=sample_rows)
            if not result.get('success'):
                order_column = columns[0] if columns else None
                if order_column:
                    order_ref = self._table_column_ref(table, order_column)
                    fallback_query = f"EVALUATE TOPN({sample_rows}, {table_ref}, {order_ref}, ASC)"
                    result = self.qe.validate_and_execute_dax(fallback_query, top_n=sample_rows)
                else:
                    result = {'success': False}
            
            if result.get('success'):
                rows = self._normalize_rows(result.get('rows', []))
                payload = {
                    'rows': rows,
                    'columns': columns[:10],
                    'column_count': len(columns),
                    'reasoning': f"Limited to {len(rows)} rows for single-page preview.",
                    'render_hints': {
                        'component': 'DataTable',
                        'single_page': True
                    }
                }
                self._cache_set(cache_key, payload)
                return payload
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
    
    def _detect_time_columns(self, table: str) -> Dict[str, Optional[str]]:
        """Detect likely time-related columns on the date table."""
        try:
            columns = self.qe.execute_info_query("COLUMNS", table_name=table)
            if not columns.get('success'):
                return {}
            detected = {
                'date': None,
                'year': None,
                'month_number': None,
                'month_name': None,
                'quarter': None
            }
            for row in columns.get('rows', []):
                name = self._extract_name(row)
                lowered = name.lower()
                data_type = str(row.get('DataType', row.get('[DataType]', ''))).lower()
                if not detected['date'] and ('date' in lowered or 'date' in data_type or 'day' in lowered) and 'key' not in lowered:
                    detected['date'] = name
                if not detected['year'] and 'year' in lowered:
                    detected['year'] = name
                if not detected['month_number'] and ('monthnumber' in lowered or 'month_no' in lowered or 'month index' in lowered or ('month' in lowered and 'number' in lowered)):
                    detected['month_number'] = name
                if not detected['month_name'] and 'month' in lowered and 'name' in lowered:
                    detected['month_name'] = name
                if not detected['month_name'] and 'month' in lowered and 'name' not in lowered and 'number' not in lowered:
                    detected['month_name'] = name
                if not detected['quarter'] and 'quarter' in lowered:
                    detected['quarter'] = name
            return detected
        except Exception:
            return {}
    
    def _recommend_chart_libraries(self, result: Dict) -> Dict:
        """Recommend chart libraries based on visualization types."""
        recommendations = {
            'primary': 'Recharts',
            'alternatives': ['Chart.js', 'Plotly'],
            'reasoning': []
        }
        
        chart_types = set()
        for rec in result.get('chart_recommendations', []):
            chart_types.add(rec.get('chart_type') or rec.get('type', ''))
        
        if 'kpi_grid' in chart_types or 'kpi_card' in chart_types:
            recommendations['reasoning'].append(
                'KPI cards work best with native React + Tailwind CSS for clean, responsive design'
            )
        
        if any(t in chart_types for t in ['line', 'line_chart', 'bar', 'bar_chart', 'area', 'area_chart']):
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
            measure_name = measure_data.get('measure')
            trend = measure_data.get('trend_data')
            grouped = measure_data.get('grouped_data')
            value = measure_data.get('value')
            
            if trend:
                recommendations.append(self._build_chart_payload(
                    'line',
                    f"{measure_name} trend",
                    trend.get('data'),
                    {
                        'x_field': trend.get('x_field', 'Month'),
                        'y_field': trend.get('y_field', 'Value'),
                        'time_grain': trend.get('grain', 'month')
                    },
                    trend.get('reasoning', f"Trend insight for {measure_name}."),
                    trend.get('render_hints')
                ))
                continue
            
            if grouped:
                recommendations.append(self._build_chart_payload(
                    'bar',
                    f"{measure_name} by {grouped.get('dimension')}",
                    grouped.get('data'),
                    {
                        'x_field': grouped.get('dimension'),
                        'y_field': 'Value',
                        'series': 'single'
                    },
                    grouped.get('reasoning', f"Categorical comparison for {measure_name}."),
                    grouped.get('render_hints')
                ))
                continue
            
            if value is not None:
                recommendations.append(self._build_chart_payload(
                    'kpi_card',
                    f"{measure_name} snapshot",
                    [{
                        'label': measure_name,
                        'value': value,
                        'format': measure_data.get('format')
                    }],
                    {
                        'layout': 'card',
                        'value_field': 'value',
                        'label_field': 'label'
                    },
                    f"Single KPI card for {measure_name}.",
                    {
                        'component': 'KpiCard',
                        'tailwind': 'w-full md:w-1/3',
                        'single_page': True
                    }
                ))
        
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
    
    def _require_connection() -> Optional[Dict[str, Any]]:
        try:
            if connection_state and connection_state.is_connected():
                return None
        except Exception:
            pass
        return {
            'success': False,
            'error': 'Not connected to a Power BI Desktop model',
            'error_type': 'not_connected',
            'suggestions': [
                'Run tool: connection: detect powerbi desktop',
                'Then run: connection: connect to powerbi',
                'Retry the visualization request afterward'
            ]
        }
    
    def handle_prepare_dashboard_data(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for dashboard mockup generation."""
        connection_issue = _require_connection()
        if connection_issue:
            return connection_issue
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
        connection_issue = _require_connection()
        if connection_issue:
            return connection_issue
        if not table or not measure:
            return {
                'success': False,
                'error': 'Both table and measure are required',
                'error_type': 'invalid_input'
            }
        
        viz_tools._set_context()
        chart_payload: Optional[Dict[str, Any]] = None
        try:
            if chart_type in ['kpi_card', 'card']:
                value = viz_tools._get_measure_value(table, measure)
                if not value:
                    return {'success': False, 'error': f'No value returned for measure {measure}', 'error_type': 'no_data'}
                viz_tools._record_usage('measure', measure)
                chart_payload = viz_tools._build_chart_payload(
                    'kpi_card',
                    f"{measure} snapshot",
                    [{
                        'label': measure,
                        'value': value.get('value')
                    }],
                    {
                        'layout': 'card',
                        'value_field': 'value',
                        'label_field': 'label'
                    },
                    f"Direct KPI card for {measure}.",
                    {
                        'component': 'KpiCard',
                        'tailwind': 'w-full md:w-1/3',
                        'single_page': True
                    }
                )
            elif chart_type in ['line', 'area', 'trend']:
                trend = viz_tools._get_measure_trend(table, measure, sample_rows)
                if not trend:
                    return {
                        'success': False,
                        'error': f'No trend data available for {measure}',
                        'error_type': 'no_data',
                        'guidance': viz_tools._context
                    }
                viz_tools._record_usage('measure', measure)
                chart_payload = viz_tools._build_chart_payload(
                    'line',
                    f"{measure} trend",
                    trend.get('data'),
                    {
                        'x_field': trend.get('x_field'),
                        'y_field': trend.get('y_field'),
                        'time_grain': trend.get('grain', 'month')
                    },
                    trend.get('reasoning', f"Trend insight for {measure}."),
                    trend.get('render_hints')
                )
            elif chart_type == 'bar':
                preferred_column = None
                dim_table = None
                if dimension:
                    parts = str(dimension).split('.', 1)
                    dim_table = parts[0]
                    if len(parts) > 1:
                        preferred_column = parts[1]
                grouped = None
                if dim_table:
                    grouped = viz_tools._get_grouped_data(table, measure, dim_table, sample_rows, preferred_column=preferred_column)
                if not grouped:
                    grouped = viz_tools._get_best_grouping(table, measure, sample_rows)
                if not grouped:
                    return {
                        'success': False,
                        'error': f'No categorical breakdown available for {measure}',
                        'error_type': 'no_data',
                        'guidance': viz_tools._context
                    }
                viz_tools._record_usage('measure', measure)
                viz_tools._record_usage('dimension', grouped.get('dimension_key', grouped.get('dimension')))
                chart_payload = viz_tools._build_chart_payload(
                    'bar',
                    f"{measure} by {grouped.get('dimension')}",
                    grouped.get('data'),
                    {
                        'x_field': grouped.get('dimension'),
                        'y_field': 'Value',
                        'series': 'single'
                    },
                    grouped.get('reasoning', f"Categorical comparison for {measure}."),
                    grouped.get('render_hints')
                )
            else:
                return {'success': False, 'error': f'Unsupported chart type: {chart_type}'}
        finally:
            guidance = viz_tools._context
            viz_tools._context = None
        
        response = {
            'success': True,
            'chart_type': chart_type,
            'chart': chart_payload,
            'data': chart_payload.get('data') if chart_payload else None
        }
        if guidance:
            response['guidance'] = guidance
        return response
    def handle_recommend_visualizations(arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend visualizations for model or specific measures."""
        measures = arguments.get('measures')
        viz_tools._set_context()
        guidance: Optional[Dict[str, List[str]]] = None
        try:
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
            guidance = viz_tools._context
        finally:
            viz_tools._context = None
        
        charts = result.get('chart_recommendations', [])
        response = {
            'success': True,
            'recommendations': charts,
            'library_recommendations': viz_tools._recommend_chart_libraries(result),
            'layout_pattern': viz_tools._suggest_layout_pattern(result),
            'page_blueprint': viz_tools._build_page_blueprint(charts),
            'memory_insights': {
                'popular_measures': viz_tools._get_top_usage('measure'),
                'popular_dimensions': viz_tools._get_top_usage('dimension'),
                'popular_layouts': viz_tools._get_top_usage('layout')
            }
        }
        if guidance:
            response['guidance'] = guidance
        return response
    
    return {
        'viz_prepare_dashboard_data': handle_prepare_dashboard_data,
        'viz_get_chart_data': handle_get_chart_data,
        'viz_recommend_visualizations': handle_recommend_visualizations
    }
