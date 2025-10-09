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
            res = self.executor.execute_info_query("MEASURES")
            if res.get('success'):
                return res.get('rows', [])
            # Fallback to TOM when DMV blocked
            tom = getattr(self.executor, 'enumerate_measures_tom', None)
            if tom:
                tr = tom()
                if tr.get('success'):
                    return tr.get('rows', [])
        except Exception:
            pass
        return []

    def _measure_full_name(self, table: Optional[str], name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        t = (table or '').strip()
        n = (name or '').strip()
        if not n:
            return None
        return f"{t}[{n}]" if t else n

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
            tbl = m.get('Table') or ''
            nm = m.get('Name')
            if nm:
                by_table.setdefault(tbl, set()).add(nm)
                fn = self._measure_full_name(tbl, nm)
                if fn:
                    all_full.add(fn)

        dep_index: Dict[str, Set[str]] = {}
        for m in measures:
            if not m.get('Name'):
                continue
            key = self._measure_full_name(m.get('Table') or '', m.get('Name'))
            if key is None:
                continue
            dep_index[key] = set()
        # Regexes
        bare_measure = re.compile(r"(?<!['\w])\[([^\]]+)\]")
        qualified = re.compile(r"(?:'([^']+)'|\b(\w+))\[([^\]]+)\]")

        for m in measures:
            tbl = m.get('Table') or ''
            nm = m.get('Name')
            expr = m.get('Expression') or ''
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
            mt = (m.get('Table') or '')
            mn = m.get('Name')
            if mn:
                by_table_measures.setdefault(mt, set()).add(mn)
        by_table_columns = self._get_columns_by_table()
        for m in measures:
            tbl = m.get('Table') or ''
            nm = m.get('Name')
            key = self._measure_full_name(tbl, nm)
            if not key:
                continue
            expr = m.get('Expression') or ''
            refs = self._extract_dax_references(expr, current_table=tbl, measures_by_table=by_table_measures, columns_by_table=by_table_columns)
            cols = set(refs.get('columns', []) or [])
            # Some expressions include table name without columns; ignore here for precision
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
                t = r.get('Table') or r.get('[Table]') or r.get('TABLE_NAME') or r.get('[TABLE_NAME]') or ''
                n = r.get('Name') or r.get('[Name]') or r.get('COLUMN_NAME') or r.get('[COLUMN_NAME]') or ''
                if t and n:
                    catalog.setdefault(str(t), set()).add(str(n))
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
            table = (q[0] or q[1]) or ''
            name = q[2]
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
            table = match[0] or match[1]
            column = match[2]
            tables.add(table)
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
                    def _norm(s: str | None) -> str:
                        if not s:
                            return ""
                        s = str(s)
                        if s.startswith('[') and s.endswith(']'):
                            s = s[1:-1]
                        if s.startswith('"') and s.endswith('"'):
                            s = s[1:-1]
                        return s
                    t_norm = _norm(table)
                    m_norm = _norm(measure)
                    rows = []
                    for r in all_measures.get('rows', []) or []:
                        rt = _norm(r.get('Table') or r.get('TableName') or r.get('TABLE_NAME') or r.get('[TABLE_NAME]'))
                        rn = _norm(r.get('Name') or r.get('MEASURE_NAME') or r.get('[MEASURE_NAME]') or r.get('[Name]'))
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
            expression = measure_data.get('Expression', '') or measure_data.get('[Expression]', '')

            # Extract direct dependencies with disambiguation catalogs
            by_table_measures: Dict[str, Set[str]] = {}
            try:
                all_meas = self._get_all_measures()
                for mm in all_meas:
                    mt = (mm.get('Table') or '')
                    mn = mm.get('Name')
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
            expr = m.get('Expression', '')
            if not expr:
                continue

            # Check if this measure references the target measure (bare or qualified)
            refs = self._extract_dax_references(expr)
            if measure_name in refs['measures']:
                downstream.append({
                    'measure': m.get('Name'),
                    'table': m.get('Table'),
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

            # Helper maps to resolve IDs -> names when Desktop returns only ID fields
            tables_by_id = {}
            try:
                for t in tables:
                    tid = t.get('ID') or t.get('TableID') or t.get('[ID]') or t.get('[TableID]')
                    nm = t.get('Name') or t.get('[Name]')
                    if tid is not None and nm:
                        tables_by_id[str(tid)] = str(nm)
            except Exception:
                pass
            columns_by_id = {}
            try:
                for c in columns:
                    cid = c.get('ID') or c.get('ColumnID') or c.get('[ID]') or c.get('[ColumnID]')
                    table_name = c.get('Table') or c.get('[Table]')
                    name = c.get('Name') or c.get('[Name]')
                    if cid is not None:
                        columns_by_id[str(cid)] = {
                            'table': str(table_name) if table_name else None,
                            'name': str(name) if name else None,
                        }
            except Exception:
                pass

            # Normalize helper
            def _norm_name(v: Any) -> str:
                s = str(v or '')
                if s.startswith('[') and s.endswith(']'):
                    s = s[1:-1]
                if s.startswith('"') and s.endswith('"'):
                    s = s[1:-1]
                return s

            # Analyze all measure expressions with catalogs
            by_table_measures: Dict[str, Set[str]] = {}
            for mm in measures:
                mt = (mm.get('Table') or '')
                mn = mm.get('Name')
                if mn:
                    by_table_measures.setdefault(mt, set()).add(mn)
            by_table_columns = self._get_columns_by_table()
            for m in measures:
                expr = m.get('Expression', '')
                current_tbl = m.get('Table') or ''
                refs = self._extract_dax_references(expr, current_table=current_tbl, measures_by_table=by_table_measures, columns_by_table=by_table_columns)

                referenced_measures.update(refs['measures'])
                referenced_columns.update(refs['columns'])
                referenced_tables.update(refs['tables'])

            # Also count columns participating in relationships as used tables

            # Check relationships for table/column usage (resolve IDs when names absent)
            rels_result = self.executor.execute_info_query("RELATIONSHIPS")
            if rels_result.get('success'):
                for rel in rels_result['rows']:
                    ft = rel.get('FromTable') or rel.get('[FromTable]')
                    tt = rel.get('ToTable') or rel.get('[ToTable]')
                    fc = rel.get('FromColumn') or rel.get('[FromColumn]')
                    tc = rel.get('ToColumn') or rel.get('[ToColumn]')
                    # Resolve via IDs if names missing
                    if not ft:
                        ftid = rel.get('FromTableID') or rel.get('[FromTableID]')
                        if ftid is not None and str(ftid) in tables_by_id:
                            ft = tables_by_id[str(ftid)]
                    if not tt:
                        ttid = rel.get('ToTableID') or rel.get('[ToTableID]')
                        if ttid is not None and str(ttid) in tables_by_id:
                            tt = tables_by_id[str(ttid)]
                    if not fc:
                        fcid = rel.get('FromColumnID') or rel.get('[FromColumnID]')
                        if fcid is not None and str(fcid) in columns_by_id:
                            fc = columns_by_id[str(fcid)].get('name')
                        # also try to pick table for this column if table still empty
                        if not ft and fcid is not None and str(fcid) in columns_by_id:
                            ft = columns_by_id[str(fcid)].get('table')
                    if not tc:
                        tcid = rel.get('ToColumnID') or rel.get('[ToColumnID]')
                        if tcid is not None and str(tcid) in columns_by_id:
                            tc = columns_by_id[str(tcid)].get('name')
                        if not tt and tcid is not None and str(tcid) in columns_by_id:
                            tt = columns_by_id[str(tcid)].get('table')

                    # Only add when we have at least the table names
                    if ft:
                        referenced_tables.add(str(ft))
                    if tt:
                        referenced_tables.add(str(tt))
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
                            ft = rel.get('FromTable')
                            tt = rel.get('ToTable')
                            fc = rel.get('FromColumn')
                            tc = rel.get('ToColumn')
                            if ft:
                                referenced_tables.add(str(ft))
                            if tt:
                                referenced_tables.add(str(tt))
                            if ft and fc:
                                referenced_columns.add(f"{ft}[{fc}]")
                            if tt and tc:
                                referenced_columns.add(f"{tt}[{tc}]")

            # Find unused objects
            unused_measures = []
            for m in measures:
                mname = _norm_name(m.get('Name') or m.get('[Name]') or m.get('MEASURE_NAME') or m.get('[MEASURE_NAME]'))
                if mname not in referenced_measures:
                    # Skip if it's hidden (likely internal)
                    hidden = bool(m.get('IsHidden')) if 'IsHidden' in m else False
                    if not hidden:
                        unused_measures.append({
                            'name': mname,
                            'table': _norm_name(m.get('Table') or m.get('[Table]') or m.get('TableName') or m.get('[TableName]'))
                        })

            unused_columns = []
            for c in columns:
                # Coalesce to safe strings; attempt to resolve table via ID map
                tbl = _norm_name(c.get('Table') or c.get('[Table]') or c.get('TABLE_NAME') or c.get('[TABLE_NAME]'))
                if not tbl:
                    tid = c.get('TableID') or c.get('ID') or c.get('[TableID]') or c.get('[ID]')
                    if tid is not None and str(tid) in tables_by_id:
                        tbl = tables_by_id[str(tid)]
                name = _norm_name(c.get('Name') or c.get('[Name]') or c.get('COLUMN_NAME') or c.get('[COLUMN_NAME]') or '')
                col_ref = f"{tbl}[{name}]" if tbl else f"[${name}]"
                if col_ref not in referenced_columns:
                    # Skip hidden and key columns
                    hidden = bool(c.get('IsHidden')) if 'IsHidden' in c else False
                    is_key = bool(c.get('IsKey')) if 'IsKey' in c else False
                    if not hidden and not is_key:
                        unused_columns.append({
                            'name': name,
                            'table': tbl,
                            'type': c.get('Type')
                        })

            unused_tables = []
            for t in tables:
                tname = _norm_name(t.get('Name') or t.get('[Name]') or t.get('TABLE_NAME') or t.get('[TABLE_NAME]'))
                if tname not in referenced_tables:
                    # Check if table has any non-calculated columns (data table)
                    table_cols = [col for col in columns if _norm_name(col.get('Table') or col.get('[Table]') or col.get('TABLE_NAME') or col.get('[TABLE_NAME]')) == tname]
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
            # Normalize identifiers for robust matching across DMV/TOM variants
            def _norm(s: Optional[str]) -> str:
                x = str(s or '')
                if x.startswith('[') and x.endswith(']'):
                    x = x[1:-1]
                if x.startswith("'") and x.endswith("'"):
                    x = x[1:-1]
                return x

            t_norm = _norm(table)
            c_norm = _norm(column)
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
                    # me_key format: Table[Measure]
                    try:
                        t, rest = me_key.split('[', 1)
                        mname = rest[:-1]
                    except Exception:
                        t, mname = '', me_key
                    usage['used_in_measures'].append({'measure': mname, 'table': t})

            # Fallback: direct regex search in measure expressions for environments where
            # INFO.MEASURES()/TOM normalization mismatches lead to empty transitive results
            if not usage['used_in_measures']:
                measures = self._get_all_measures()
                # Pattern that tolerates quotes around table name and escapes brackets
                import re as _re
                pattern = _re.compile(r"(?:'" + _re.escape(t_norm) + r"'|" + _re.escape(t_norm) + r")\[" + _re.escape(c_norm) + r"\]", _re.IGNORECASE)
                for m in measures:
                    expr = str(m.get('Expression') or '')
                    if pattern.search(expr):
                        usage['used_in_measures'].append({'measure': m.get('Name', ''), 'table': m.get('Table', '')})

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
                    ft = rel.get('FromTable') or rel.get('[FromTable]')
                    fc = rel.get('FromColumn') or rel.get('[FromColumn]')
                    tt = rel.get('ToTable') or rel.get('[ToTable]')
                    tc = rel.get('ToColumn') or rel.get('[ToColumn]')
                    if ((str(ft or '').strip().lower() == t_norm.lower() and str(fc or '').strip().lower() == c_norm.lower()) or
                        (str(tt or '').strip().lower() == t_norm.lower() and str(tc or '').strip().lower() == c_norm.lower())):
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
                            ft = rel.get('FromTable'); fc = rel.get('FromColumn')
                            tt = rel.get('ToTable'); tc = rel.get('ToColumn')
                            if ((str(ft or '').strip().lower() == t_norm.lower() and str(fc or '').strip().lower() == c_norm.lower()) or
                                (str(tt or '').strip().lower() == t_norm.lower() and str(tc or '').strip().lower() == c_norm.lower())):
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
