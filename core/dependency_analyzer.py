"""
Dependency Analyzer for PBIXRay MCP Server
Analyzes measure and column dependencies across the model
"""

import re
import logging
from typing import Dict, Any, List, Set, Optional
from core.query_executor import COLUMN_TYPE_CALCULATED

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes dependencies between measures, columns, and tables."""

    def __init__(self, query_executor):
        """Initialize with query executor."""
        self.executor = query_executor
        self._dependency_cache = {}
        self._columns_by_table_cache: Optional[Dict[str, Set[str]]] = None

    # -----------------------------
    # Internal helpers for measure graph/index
    # -----------------------------
    def _get_all_measures(self) -> List[Dict[str, Any]]:
        """Return all measures with (Table, Name, Expression). Cached implicitly by caller indexes."""
        try:
            # FIX: Use execute_info_query() which handles TableID->Table conversion automatically
            res = self.executor.execute_info_query("MEASURES")
            if res.get('success'):
                rows = res.get('rows', [])
                # Ensure all rows have Table field (should be set by execute_info_query)
                for row in rows:
                    if 'Table' not in row:
                        row['Table'] = ''
                return rows
            # Fallback to TOM when DMV blocked
            tom = getattr(self.executor, 'enumerate_measures_tom', None)
            if tom:
                tr = tom()
                if tr.get('success'):
                    return tr.get('rows', [])
        except Exception as e:
            logger.debug(f"_get_all_measures fallback: {e}")
            # Last resort: try TOM
            tom = getattr(self.executor, 'enumerate_measures_tom', None)
            if tom:
                tr = tom()
                if tr.get('success'):
                    return tr.get('rows', [])
        return []

    def _normalize_identifier(self, val: Any) -> str:
        """Normalize identifiers by stripping brackets, quotes, and whitespace."""
        try:
            s = str(val or "").strip()
            # Remove wrapping brackets
            if s.startswith("[") and s.endswith("]"):
                s = s[1:-1]
            # Remove wrapping quotes
            if s.startswith("'") and s.endswith("'"):
                s = s[1:-1]
            if s.startswith('"') and s.endswith('"'):
                s = s[1:-1]
            return s.strip()
        except Exception:
            return ""

    def _extract_table_name(self, row: dict) -> str:
        """Extract table name from a DMV row, trying multiple field name variants."""
        for key in ['Table', 'TABLE_NAME', 'TableName', 'table', '[Table]', 'TABLE', '[TABLE_NAME]']:
            if key in row and row[key] not in (None, ""):
                return self._normalize_identifier(row[key])
        return ""

    def _extract_measure_name(self, row: dict) -> str:
        """Extract measure name from a DMV row, trying multiple field name variants."""
        for key in ['Name', 'MEASURE_NAME', 'MeasureName', '[Name]', '[MEASURE_NAME]']:
            if key in row and row[key] not in (None, ""):
                return self._normalize_identifier(row[key])
        return ""

    def _measure_full_name(self, table: Optional[str], name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        t = self._normalize_identifier(table or '')
        n = self._normalize_identifier(name or '')
        if not n:
            return None
        # Always return Table[Measure] format for consistent parsing
        # Use empty string as table when unknown (will be resolved during build)
        return f"{t}[{n}]"

    def _build_measure_dependency_index(self) -> Dict[str, Set[str]]:
        """Build a graph mapping measure full name -> referenced measure full names.

        We detect measure references in two ways:
        - Bare [Measure] tokens (assumed to refer to current-table scope)
        - Qualified 'Table'[Measure] tokens when they exist as measures
        Columns with the same token shape are filtered by checking against the measure catalog.
        """
        measures = self._get_all_measures()
        # Catalog of known measures for disambiguation
        by_table: Dict[str, Set[str]] = {}
        all_full: Set[str] = set()
        for m in measures:
            tbl = self._extract_table_name(m)
            nm = self._extract_measure_name(m)
            if nm:
                by_table.setdefault(tbl, set()).add(nm)
                fn = self._measure_full_name(tbl, nm)
                if fn:
                    all_full.add(fn)

        dep_index: Dict[str, Set[str]] = {}
        for m in measures:
            nm = self._extract_measure_name(m)
            if not nm:
                continue
            key = self._measure_full_name(self._extract_table_name(m), nm)
            if key is None:
                continue
            dep_index[key] = set()
        
        # Regexes
        bare_measure = re.compile(r"(?<!['\w])\[([^\]]+)\]")
        qualified = re.compile(r"(?:'([^']+)'|\b(\w+))\[([^\]]+)\]")

        for m in measures:
            tbl = self._extract_table_name(m)
            nm = self._extract_measure_name(m)
            # Try multiple expression field names
            expr = None
            for key in ['Expression', '[Expression]', 'EXPRESSION']:
                if key in m:
                    expr = m.get(key)
                    break
            if not expr:
                expr = ""
            me_key = self._measure_full_name(tbl, nm)
            if not me_key:
                continue
            refs: Set[str] = set()
            # 1) Bare [Measure] references -> current table
            for bm in bare_measure.findall(expr):
                if bm in by_table.get(tbl, set()):
                    fn = self._measure_full_name(tbl, bm)
                    if fn:
                        refs.add(fn)
            # 2) Qualified 'Table'[Name] tokens; keep only those that are known measures
            for q in qualified.findall(expr):
                qtable = q[0] or q[1] or ''
                qname = q[2]
                if qname in by_table.get(qtable, set()):
                    fn = self._measure_full_name(qtable, qname)
                    if fn:
                        refs.add(fn)
            dep_index.setdefault(me_key, set()).update(refs)
        return dep_index

    def _build_measure_columns_direct(self) -> Dict[str, Set[str]]:
        """Return direct column references per measure as a map measure_full_name -> {table[col]}"""
        measures = self._get_all_measures()
        direct: Dict[str, Set[str]] = {}
        # Build catalogs to disambiguate bare or qualified tokens
        by_table_measures: Dict[str, Set[str]] = {}
        for m in measures:
            mt = self._extract_table_name(m)
            mn = self._extract_measure_name(m)
            if mn:
                by_table_measures.setdefault(mt, set()).add(mn)
        by_table_columns = self._get_columns_by_table()
        for m in measures:
            tbl = self._extract_table_name(m)
            nm = self._extract_measure_name(m)
            key = self._measure_full_name(tbl, nm)
            if not key:
                continue
            # Try multiple expression field names
            expr = None
            for field in ['Expression', '[Expression]', 'EXPRESSION']:
                if field in m:
                    expr = m.get(field)
                    break
            if not expr:
                expr = ""
            refs = self._extract_dax_references(expr, current_table=tbl, measures_by_table=by_table_measures, columns_by_table=by_table_columns)
            cols = set(refs.get('columns', []) or [])
            direct[key] = cols
        return direct

    def _get_columns_by_table(self) -> Dict[str, Set[str]]:
        """Build or return a catalog of column names per table for disambiguation."""
        if isinstance(self._columns_by_table_cache, dict) and self._columns_by_table_cache:
            return self._columns_by_table_cache
        catalog: Dict[str, Set[str]] = {}
        try:
            cols_res = self.executor.execute_info_query("COLUMNS")
            rows = cols_res.get('rows', []) if cols_res.get('success') else []
            if not rows:
                # TOM fallback
                tom_cols = getattr(self.executor, 'enumerate_columns_tom', None)
                if callable(tom_cols):
                    tr = tom_cols()
                    if isinstance(tr, dict) and tr.get('success'):
                        rows = tr.get('rows', []) or []
            for r in rows or []:
                # Try multiple table field variants
                t = None
                for tkey in ['Table', '[Table]', 'TABLE_NAME', '[TABLE_NAME]', 'TableName']:
                    if tkey in r and r[tkey]:
                        t = self._normalize_identifier(r[tkey])
                        break
                # Try multiple column field variants
                n = None
                for ckey in ['Name', '[Name]', 'COLUMN_NAME', '[COLUMN_NAME]', 'ColumnName']:
                    if ckey in r and r[ckey]:
                        n = self._normalize_identifier(r[ckey])
                        break
                if t and n:
                    catalog.setdefault(t, set()).add(n)
        except Exception:
            pass
        self._columns_by_table_cache = catalog
        return catalog

    def _get_measure_columns_index(self) -> Dict[str, Set[str]]:
        """Compute or return cached transitive columns used by each measure."""
        cache_key = 'measure_columns_index'
        idx = self._dependency_cache.get(cache_key)
        if isinstance(idx, dict) and idx:
            return idx
        graph = self._build_measure_dependency_index()
        direct = self._build_measure_columns_direct()

        # DFS with memoization to accumulate columns
        memo: Dict[str, Set[str]] = {}
        visiting: Set[str] = set()

        def dfs(measure_key: str) -> Set[str]:
            if measure_key in memo:
                return memo[measure_key]
            if measure_key in visiting:
                # cycle detected; return current direct set to break the loop
                return direct.get(measure_key, set())
            visiting.add(measure_key)
            cols = set(direct.get(measure_key, set()))
            for dep in graph.get(measure_key, set()):
                cols.update(dfs(dep))
            visiting.remove(measure_key)
            memo[measure_key] = cols
            return cols

        # Build index for all known measures
        all_keys = set(direct.keys()) | set(graph.keys())
        for k in all_keys:
            dfs(k)
        self._dependency_cache[cache_key] = memo
        return memo

    def _extract_dax_references(
        self,
        expression: str,
        current_table: Optional[str] = None,
        measures_by_table: Optional[Dict[str, Set[str]]] = None,
        columns_by_table: Optional[Dict[str, Set[str]]] = None,
    ) -> Dict[str, List[str]]:
        """Extract table, column, and measure references from DAX expression.

        - Disambiguates qualified tokens 'Table'[Name] as measures vs columns based on catalogs
        - Classifies bare [Name] as column if it exists in current_table's columns; else as measure if in measures
        """
        if not expression:
            return {"tables": [], "columns": [], "measures": []}

        # Remove comments and strings to avoid false positives
        clean_expr = re.sub(r'--[^\n]*', '', expression)
        clean_expr = re.sub(r'"[^"]*"', '', clean_expr)

        tables = set()
        columns = set()
        measures = set()

        # Qualified tokens: 'Table'[Name] or Table[Name]
        qual_tokens = re.findall(r"(?:'([^']+)'|\b(\w+))\[([^\]]+)\]", clean_expr)
        for q in qual_tokens:
            table = self._normalize_identifier(q[0] or q[1] or '')
            name = self._normalize_identifier(q[2])
            if table:
                tables.add(table)
            if measures_by_table and name in measures_by_table.get(table, set()):
                measures.add(name)
            elif columns_by_table and name in columns_by_table.get(table, set()):
                columns.add(f"{table}[{name}]")
            else:
                # Default to column when unknown to not undercount column usage
                columns.add(f"{table}[{name}]")

        # Bare tokens: [Name] not preceded by table identifier
        bare_tokens = re.findall(r"(?<!['\w])\[([^\]]+)\]", clean_expr)
        for name in bare_tokens:
            name = self._normalize_identifier(name)
            # Prefer column in current table if known; else a measure if known
            if current_table and columns_by_table and name in columns_by_table.get(current_table, set()):
                columns.add(f"{current_table}[{name}]")
            elif current_table and measures_by_table and name in measures_by_table.get(current_table, set()):
                measures.add(name)
            else:
                # Unknown scope: assume it's a measure to avoid fabricating column refs
                measures.add(name)

        # RELATED, RELATEDTABLE functions
        related_refs = re.findall(r"RELATED(?:TABLE)?\s*\(\s*(?:'([^']+)'|(\w+))\[([^\]]+)\]", clean_expr)
        for match in related_refs:
            table = self._normalize_identifier(match[0] or match[1])
            column = self._normalize_identifier(match[2])
            if table:
                tables.add(table)
            if table and column:
                columns.add(f"{table}[{column}]")

        return {
            "tables": sorted(list(tables)),
            "columns": sorted(list(columns)),
            "measures": sorted(list(measures))
        }

    def analyze_measure_dependencies(
        self,
        table: str,
        measure: str,
        depth: int = 3,
        include_upstream: bool = True,
        include_downstream: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze dependencies for a measure.

        Args:
            table: Table containing the measure
            measure: Measure name
            depth: Maximum depth to traverse
            include_upstream: Include what this measure depends on
            include_downstream: Include what depends on this measure

        Returns:
            Dependency analysis results
        """
        try:
            # Get measure details
            measure_result = self.executor.execute_info_query(
                "MEASURES",
                filter_expr=f'[Name] = "{measure}"',
                table_name=table
            )

            # Some Desktop builds regress on table-scoped DMV filters; fallback to client-side filter
            if not (measure_result.get('success') and measure_result.get('rows')):
                all_measures = self.executor.execute_info_query("MEASURES")
                if not all_measures.get('success'):
                    # TOM fallback
                    tom_meas = getattr(self.executor, 'enumerate_measures_tom', None)
                    if tom_meas:
                        tr = tom_meas()
                        if tr.get('success'):
                            all_measures = tr
                if all_measures.get('success'):
                    t_norm = self._normalize_identifier(table)
                    m_norm = self._normalize_identifier(measure)
                    rows = []
                    for r in all_measures.get('rows', []) or []:
                        rt = self._extract_table_name(r)
                        rn = self._extract_measure_name(r)
                        if rt == t_norm and rn == m_norm:
                            rows.append(r)
                    if rows:
                        measure_result = {'success': True, 'rows': rows, 'row_count': len(rows)}
                # If still no rows, return not-found error
                if not (measure_result.get('success') and measure_result.get('rows')):
                    return {
                        'success': False,
                        'error': f"Measure '{measure}' not found in table '{table}'"
                    }

            measure_data = measure_result['rows'][0]
            expression = None
            for key in ['Expression', '[Expression]', 'EXPRESSION']:
                if key in measure_data:
                    expression = measure_data.get(key, '') or ''
                    break
            if expression is None:
                expression = ''

            # Extract direct dependencies with disambiguation catalogs
            by_table_measures: Dict[str, Set[str]] = {}
            try:
                all_meas = self._get_all_measures()
                for mm in all_meas:
                    mt = self._extract_table_name(mm)
                    mn = self._extract_measure_name(mm)
                    if mn:
                        by_table_measures.setdefault(mt, set()).add(mn)
            except Exception:
                pass
            by_table_columns = self._get_columns_by_table()
            direct_deps = self._extract_dax_references(expression, current_table=table, measures_by_table=by_table_measures, columns_by_table=by_table_columns)

            result = {
                'success': True,
                'measure': measure,
                'table': table,
                'expression': expression,
                'direct_dependencies': direct_deps
            }

            # Get all measures for downstream analysis
            if include_downstream:
                all_measures_result = self.executor.execute_info_query("MEASURES")
                if all_measures_result.get('success'):
                    downstream = self._find_downstream_dependencies(
                        measure,
                        all_measures_result['rows'],
                        depth
                    )
                    result['downstream_dependencies'] = downstream

            # Get upstream chain
            if include_upstream:
                upstream = self._build_upstream_chain(direct_deps, depth)
                result['upstream_dependencies'] = upstream

            return result

        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return {'success': False, 'error': str(e)}

    def _find_downstream_dependencies(
        self,
        measure_name: str,
        all_measures: List[Dict],
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """Find measures that depend on the given measure."""
        downstream = []

        for m in all_measures:
            expr = None
            for key in ['Expression', '[Expression]', 'EXPRESSION']:
                if key in m:
                    expr = m.get(key, '') or ''
                    break
            if not expr:
                continue

            # Check if this measure references the target measure (bare or qualified)
            refs = self._extract_dax_references(expr)
            if measure_name in refs['measures']:
                downstream.append({
                    'measure': self._extract_measure_name(m),
                    'table': self._extract_table_name(m),
                    'expression': expr[:200]  # Truncate for readability
                })

        return downstream

    def _build_upstream_chain(
        self,
        dependencies: Dict[str, List[str]],
        max_depth: int,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """Build upstream dependency chain."""
        if current_depth >= max_depth:
            return dependencies

        # For now, return direct dependencies
        # Full recursive chain would require querying each dependent measure
        return dependencies

    def find_unused_objects(self) -> Dict[str, Any]:
        """Find unused tables, columns, and measures."""
        try:
            # Get all measures
            measures_result = self.executor.execute_info_query("MEASURES")
            if not measures_result.get('success'):
                # Try TOM fallback
                tom_meas = getattr(self.executor, 'enumerate_measures_tom', None)
                if tom_meas:
                    tr = tom_meas()
                    if tr.get('success'):
                        measures_result = tr
                if not measures_result.get('success'):
                    return {'success': False, 'error': 'Failed to get measures'}

            measures = measures_result['rows']

            # Get all columns
            columns_result = self.executor.execute_info_query("COLUMNS")
            if not columns_result.get('success'):
                tom_cols = getattr(self.executor, 'enumerate_columns_tom', None)
                if tom_cols:
                    tr = tom_cols()
                    if tr.get('success'):
                        columns_result = tr
                if not columns_result.get('success'):
                    return {'success': False, 'error': 'Failed to get columns'}

            columns = columns_result['rows']

            # Get all tables
            tables_result = self.executor.execute_info_query("TABLES")
            if not tables_result.get('success'):
                return {'success': False, 'error': 'Failed to get tables'}

            tables = tables_result['rows']

            # Build reference sets
            referenced_measures = set()
            referenced_columns = set()
            referenced_tables = set()

            # Analyze all measure expressions with catalogs
            by_table_measures: Dict[str, Set[str]] = {}
            for mm in measures:
                mt = self._extract_table_name(mm)
                mn = self._extract_measure_name(mm)
                if mn:
                    by_table_measures.setdefault(mt, set()).add(mn)
            by_table_columns = self._get_columns_by_table()
            
            for m in measures:
                expr = None
                for key in ['Expression', '[Expression]', 'EXPRESSION']:
                    if key in m:
                        expr = m.get(key, '') or ''
                        break
                if not expr:
                    expr = ''
                current_tbl = self._extract_table_name(m)
                refs = self._extract_dax_references(expr, current_table=current_tbl, measures_by_table=by_table_measures, columns_by_table=by_table_columns)

                referenced_measures.update(refs['measures'])
                referenced_columns.update(refs['columns'])
                referenced_tables.update(refs['tables'])

            # Check relationships for table/column usage
            rels_result = self.executor.execute_info_query("RELATIONSHIPS")
            if rels_result.get('success'):
                for rel in rels_result['rows']:
                    # Try to extract from/to table and column names with normalization
                    ft = None
                    for key in ['FromTable', '[FromTable]']:
                        if key in rel and rel[key]:
                            ft = self._normalize_identifier(rel[key])
                            break
                    tt = None
                    for key in ['ToTable', '[ToTable]']:
                        if key in rel and rel[key]:
                            tt = self._normalize_identifier(rel[key])
                            break
                    fc = None
                    for key in ['FromColumn', '[FromColumn]']:
                        if key in rel and rel[key]:
                            fc = self._normalize_identifier(rel[key])
                            break
                    tc = None
                    for key in ['ToColumn', '[ToColumn]']:
                        if key in rel and rel[key]:
                            tc = self._normalize_identifier(rel[key])
                            break
                    
                    # Only add when we have at least the table names
                    if ft:
                        referenced_tables.add(ft)
                    if tt:
                        referenced_tables.add(tt)
                    if ft and fc:
                        referenced_columns.add(f"{ft}[{fc}]")
                    if tt and tc:
                        referenced_columns.add(f"{tt}[{tc}]")
            else:
                # Try TOM fallback
                tom_rels = getattr(self.executor, 'list_relationships_tom', None)
                if tom_rels:
                    rr = tom_rels()
                    if rr.get('success'):
                        for rel in rr['rows']:
                            ft = self._normalize_identifier(rel.get('FromTable', ''))
                            tt = self._normalize_identifier(rel.get('ToTable', ''))
                            fc = self._normalize_identifier(rel.get('FromColumn', ''))
                            tc = self._normalize_identifier(rel.get('ToColumn', ''))
                            if ft:
                                referenced_tables.add(ft)
                            if tt:
                                referenced_tables.add(tt)
                            if ft and fc:
                                referenced_columns.add(f"{ft}[{fc}]")
                            if tt and tc:
                                referenced_columns.add(f"{tt}[{tc}]")

            # Find unused objects
            unused_measures = []
            for m in measures:
                mname = self._extract_measure_name(m)
                if mname not in referenced_measures:
                    # Skip if it's hidden (likely internal)
                    hidden = bool(m.get('IsHidden')) if 'IsHidden' in m else False
                    if not hidden:
                        unused_measures.append({
                            'name': mname,
                            'table': self._extract_table_name(m)
                        })

            unused_columns = []
            for c in columns:
                tbl = self._extract_table_name(c)
                name = None
                for key in ['Name', '[Name]', 'COLUMN_NAME', '[COLUMN_NAME]']:
                    if key in c and c[key]:
                        name = self._normalize_identifier(c[key])
                        break
                
                col_ref = f"{tbl}[{name}]" if tbl and name else f"[${name}]"
                if col_ref not in referenced_columns:
                    # Skip hidden and key columns
                    hidden = bool(c.get('IsHidden')) if 'IsHidden' in c else False
                    is_key = bool(c.get('IsKey')) if 'IsKey' in c else False
                    if not hidden and not is_key:
                        unused_columns.append({
                            'name': name if name else '',
                            'table': tbl if tbl else '',
                            'type': c.get('Type')
                        })

            unused_tables = []
            for t in tables:
                tname = self._extract_table_name(t)
                if tname not in referenced_tables:
                    # Check if table has any non-calculated columns (data table)
                    table_cols = [col for col in columns if self._extract_table_name(col) == tname]
                    hidden = bool(t.get('IsHidden')) if 'IsHidden' in t else False
                    if table_cols and not hidden:
                        unused_tables.append({
                            'name': tname
                        })

            return {
                'success': True,
                'unused_measures': unused_measures,
                'unused_columns': unused_columns[:50],  # Limit for readability
                'unused_tables': unused_tables,
                'summary': {
                    'total_unused_measures': len(unused_measures),
                    'total_unused_columns': len(unused_columns),
                    'total_unused_tables': len(unused_tables)
                }
            }

        except Exception as e:
            logger.error(f"Error finding unused objects: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_column_usage(self, table: str, column: str) -> Dict[str, Any]:
        """Analyze where a column is used in the model."""
        try:
            t_norm = self._normalize_identifier(table)
            c_norm = self._normalize_identifier(column)
            col_ref = f"{t_norm}[{c_norm}]"

            usage = {
                'success': True,
                'column': column,
                'table': table,
                'used_in_measures': [],
                'used_in_calculated_columns': [],
                'used_in_relationships': []
            }

            # Check measures (transitively) using computed index
            idx = self._get_measure_columns_index()
            for me_key, cols in idx.items():
                if col_ref in cols or f"{t_norm}[{c_norm}]" in cols:
                    # me_key format: Table[Measure] - extract both parts
                    try:
                        if '[' in me_key and me_key.endswith(']'):
                            # Split on last [ to handle edge cases
                            bracket_pos = me_key.rfind('[')
                            table_part = me_key[:bracket_pos] if bracket_pos > 0 else ''
                            measure_part = me_key[bracket_pos+1:-1] if bracket_pos >= 0 else me_key
                        else:
                            table_part = ''
                            measure_part = me_key
                        usage['used_in_measures'].append({'measure': measure_part, 'table': table_part})
                    except Exception:
                        usage['used_in_measures'].append({'measure': me_key, 'table': ''})

            # Fallback: direct regex search in measure expressions for environments where
            # INFO.MEASURES()/TOM normalization mismatches lead to empty transitive results
            if not usage['used_in_measures']:
                measures = self._get_all_measures()
                # Pattern that tolerates quotes around table name and escapes brackets
                import re as _re
                pattern = _re.compile(r"(?:'" + _re.escape(t_norm) + r"'|" + _re.escape(t_norm) + r")\[" + _re.escape(c_norm) + r"\]", _re.IGNORECASE)
                for m in measures:
                    expr = None
                    for key in ['Expression', '[Expression]', 'EXPRESSION']:
                        if key in m:
                            expr = str(m.get(key, '') or '')
                            break
                    if not expr:
                        expr = ''
                    if pattern.search(expr):
                        usage['used_in_measures'].append({
                            'measure': self._extract_measure_name(m),
                            'table': self._extract_table_name(m)
                        })

            # Check calculated columns
            calc_cols_query = f'EVALUATE FILTER(INFO.COLUMNS(), [Type] = {COLUMN_TYPE_CALCULATED})'
            calc_result = self.executor.validate_and_execute_dax(calc_cols_query)
            if calc_result.get('success'):
                for row in calc_result.get('rows', []):
                    # Would need expression to check, skip for now
                    pass

            # Check relationships
            rels_result = self.executor.execute_info_query("RELATIONSHIPS")
            if rels_result.get('success'):
                for rel in rels_result['rows']:
                    # Accept several key variants and compare using normalized strings
                    ft = None
                    for key in ['FromTable', '[FromTable]']:
                        if key in rel and rel[key]:
                            ft = self._normalize_identifier(rel[key])
                            break
                    fc = None
                    for key in ['FromColumn', '[FromColumn]']:
                        if key in rel and rel[key]:
                            fc = self._normalize_identifier(rel[key])
                            break
                    tt = None
                    for key in ['ToTable', '[ToTable]']:
                        if key in rel and rel[key]:
                            tt = self._normalize_identifier(rel[key])
                            break
                    tc = None
                    for key in ['ToColumn', '[ToColumn]']:
                        if key in rel and rel[key]:
                            tc = self._normalize_identifier(rel[key])
                            break
                    
                    if ((ft and ft.lower() == t_norm.lower() and fc and fc.lower() == c_norm.lower()) or
                        (tt and tt.lower() == t_norm.lower() and tc and tc.lower() == c_norm.lower())):
                        usage['used_in_relationships'].append({
                            'from': f"{ft}[{fc}]",
                            'to': f"{tt}[{tc}]",
                            'active': rel.get('IsActive')
                        })
            else:
                # TOM fallback
                tom_rels = getattr(self.executor, 'list_relationships_tom', None)
                if tom_rels:
                    rr = tom_rels()
                    if rr.get('success'):
                        for rel in rr['rows']:
                            ft = self._normalize_identifier(rel.get('FromTable', ''))
                            fc = self._normalize_identifier(rel.get('FromColumn', ''))
                            tt = self._normalize_identifier(rel.get('ToTable', ''))
                            tc = self._normalize_identifier(rel.get('ToColumn', ''))
                            if ((ft and ft.lower() == t_norm.lower() and fc and fc.lower() == c_norm.lower()) or
                                (tt and tt.lower() == t_norm.lower() and tc and tc.lower() == c_norm.lower())):
                                usage['used_in_relationships'].append({
                                    'from': f"{ft}[{fc}]",
                                    'to': f"{tt}[{tc}]",
                                    'active': rel.get('IsActive')
                                })

            usage['summary'] = {
                'used_in_measures_count': len(usage['used_in_measures']),
                'used_in_relationships_count': len(usage['used_in_relationships']),
                'is_used': (len(usage['used_in_measures']) +
                           len(usage['used_in_relationships'])) > 0
            }

            return usage

        except Exception as e:
            logger.error(f"Error analyzing column usage: {e}")
            return {'success': False, 'error': str(e)}
