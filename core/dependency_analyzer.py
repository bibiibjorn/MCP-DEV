"""
Dependency and usage analyzer for Power BI models.
Tracks dependencies and usage patterns across measures, columns, and relationships.
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    from .dax_parser import DaxReferenceIndex, parse_dax_references  # type: ignore
    _DAX_PARSER_AVAILABLE = True
except ImportError as exc:  # pragma: no cover - safety fallback
    logger.warning(
        "core.dax_parser unavailable (%s); using simplified inline DAX parser. "
        "Install the full package for richer dependency detection.",
        exc,
    )
    _DAX_PARSER_AVAILABLE = False

    class DaxReferenceIndex:  # type: ignore[override]
        """Minimal reference index used when the dedicated parser module is missing."""

        def __init__(self, measure_rows=None, column_rows=None) -> None:
            self.measure_keys: Set[str] = set()
            self.measure_names: Dict[str, Set[str]] = {}
            self.column_keys: Set[str] = set()
            if measure_rows:
                for row in measure_rows:
                    table = str(row.get("Table") or "").strip()
                    name = str(row.get("Name") or "").strip()
                    if table and name:
                        key = f"{table.lower()}|{name.lower()}"
                        self.measure_keys.add(key)
                        self.measure_names.setdefault(name.lower(), set()).add(table)
            if column_rows:
                for row in column_rows:
                    table = str(row.get("Table") or "").strip()
                    name = str(row.get("Name") or "").strip()
                    if table and name:
                        self.column_keys.add(f"{table.lower()}|{name.lower()}")

    _QUALIFIED_TOKEN = re.compile(r"'([^']+)'\s*\[([^\]]+)\]")
    _UNQUALIFIED_TOKEN = re.compile(r"(?<!')\[(.+?)\]")

    def parse_dax_references(  # type: ignore[override]
        expression: Optional[str],
        reference_index: Optional[DaxReferenceIndex] = None,
    ) -> Dict[str, List]:
        """Basic fallback parser that keeps initialization working when the full parser is missing."""
        if not isinstance(expression, str) or not expression.strip():
            return {"tables": [], "columns": [], "measures": [], "identifiers": []}

        cleaned = re.sub(r"/\*.*?\*/", "", expression, flags=re.DOTALL)
        cleaned = re.sub(r"//.*?$", "", cleaned, flags=re.MULTILINE)

        tables: Set[str] = set()
        columns: Set[Tuple[str, str]] = set()
        measures: Set[Tuple[str, str]] = set()
        identifiers: Set[str] = set()

        ref_idx = reference_index or DaxReferenceIndex()

        for table, name in _QUALIFIED_TOKEN.findall(cleaned):
            tbl = table.strip()
            obj = name.strip()
            if not obj:
                continue
            identifiers.add(obj)
            key = f"{tbl.lower()}|{obj.lower()}"
            tables.add(tbl)
            if key in ref_idx.measure_keys:
                measures.add((tbl, obj))
            else:
                columns.add((tbl, obj))

        for match in _UNQUALIFIED_TOKEN.finditer(cleaned):
            name = match.group(1).strip()
            if not name or name.startswith("@"):
                continue
            identifiers.add(name)
            owners = ref_idx.measure_names.get(name.lower())
            if owners:
                for tbl in owners:
                    measures.add((tbl, name))
            else:
                measures.add(("", name))

        return {
            "tables": sorted(tables),
            "columns": sorted(columns),
            "measures": sorted(measures),
            "identifiers": sorted(identifiers),
        }

class DependencyAnalyzer:
    """Analyzes usage patterns and dependencies in Power BI models."""
    
    def __init__(self, model):
        """Initialize with model connection."""
        self.model = model
        self._dependency_cache = {}
        self._reference_index: Optional[DaxReferenceIndex] = None
    
    def refresh_metadata(self) -> None:
        """Reset cached DMV metadata and dependency cache."""
        self._reference_index = None
        self._dependency_cache.clear()
    
    def _get_reference_index(self) -> DaxReferenceIndex:
        """Return cached reference metadata, loading it on demand."""
        if self._reference_index is not None:
            return self._reference_index
        
        measure_rows: List[Dict[str, object]] = []
        column_rows: List[Dict[str, object]] = []
        try:
            measures_result = self.model.execute_info_query("MEASURES")
            if measures_result.get("success"):
                measure_rows = measures_result.get("rows", [])
        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.warning(f"Failed to fetch MEASURES for reference index: {e}")
            measure_rows = []
        except Exception as e:
            logger.error(f"Unexpected error fetching MEASURES: {type(e).__name__}: {e}")
            measure_rows = []

        try:
            columns_result = self.model.execute_info_query("COLUMNS")
            if columns_result.get("success"):
                column_rows = columns_result.get("rows", [])
        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.warning(f"Failed to fetch COLUMNS for reference index: {e}")
            column_rows = []
        except Exception as e:
            logger.error(f"Unexpected error fetching COLUMNS: {type(e).__name__}: {e}")
            column_rows = []
        
        self._reference_index = DaxReferenceIndex(measure_rows, column_rows)
        return self._reference_index
    
    def _parse_references(self, expression: Optional[str]) -> Dict[str, List]:
        """Helper to parse an expression using cached metadata."""
        return parse_dax_references(expression, self._get_reference_index())
        
    def analyze_measure_dependencies(
        self, 
        table: str, 
        measure: str, 
        max_depth: int = 3
    ) -> Dict:
        """
        Analyze dependencies for a specific measure.
        
        Args:
            table: Table containing the measure
            measure: Measure name
            max_depth: Maximum recursion depth
            
        Returns:
            Dictionary with dependency tree
        """
        cache_key = f"{table}|{measure}"
        if cache_key in self._dependency_cache:
            return self._dependency_cache[cache_key]
            
        result = {
            "measure": measure,
            "table": table,
            "dependencies": [],
            "depth": 0,
            "circular_reference": False
        }
        
        visited = set()
        result["dependencies"] = self._build_dependency_tree(
            table, measure, max_depth, 0, visited
        )
        
        self._dependency_cache[cache_key] = result
        return result
        
    def _build_dependency_tree(
        self,
        table: str,
        measure: str,
        max_depth: int,
        current_depth: int,
        visited: Set[str]
    ) -> List[Dict]:
        """Recursively build dependency tree."""
        if current_depth >= max_depth:
            return []
            
        node_id = f"{table}|{measure}"
        if node_id in visited:
            return [{"circular_reference": True, "to": node_id}]
            
        visited.add(node_id)
        
        # Get measure details
        measure_data = self.model.get_measure_details(table, measure)
        if not measure_data or not measure_data.get("expression"):
            return []
            
        # Parse references from expression
        refs = self._parse_references(measure_data["expression"])
        
        dependencies = []
        for ref_table, ref_obj in refs.get("measures", []):
            dep = {
                "type": "measure",
                "table": ref_table,
                "name": ref_obj,
                "depth": current_depth + 1
            }
            
            # Recurse if not at max depth
            if current_depth + 1 < max_depth:
                sub_deps = self._build_dependency_tree(
                    ref_table, ref_obj, max_depth, current_depth + 1, visited.copy()
                )
                if sub_deps:
                    dep["dependencies"] = sub_deps
                    
            dependencies.append(dep)
            
        for ref_table, ref_col in refs.get("columns", []):
            dependencies.append({
                "type": "column",
                "table": ref_table,
                "name": ref_col,
                "depth": current_depth + 1
            })
            
        return dependencies
        
    def analyze_column_usage(self, table: str, column: str) -> Dict:
        """
        Analyze where a column is used in the model.

        Args:
            table: Table name
            column: Column name

        Returns:
            Dictionary with usage information
        """
        # Pre-compute lowercase versions for performance
        table_lower = table.lower()
        column_lower = column.lower()

        result = {
            "column": column,
            "table": table,
            "used_in_measures": [],
            "used_in_calculated_columns": [],
            "used_in_relationships": [],
            "summary": {
                "used_in_measures_count": 0,
                "used_in_relationships_count": 0,
                "is_used": False
            }
        }

        # Check measures
        measures = self.model.list_measures()
        for m in measures:
            m_table = m.get("Table", "")
            m_name = m.get("Name", "")
            m_expr = m.get("Expression", "")

            if not m_expr:
                continue

            refs = self._parse_references(m_expr)
            for ref_table, ref_col in refs.get("columns", []):
                if ref_table.lower() == table_lower and ref_col.lower() == column_lower:
                    result["used_in_measures"].append({
                        "table": m_table,
                        "measure": m_name
                    })
                    break
                    
        # Check calculated columns
        columns = self.model.list_columns(table=table)
        for col in columns:
            if col.get("Type") != "Calculated":
                continue

            col_name = col.get("Name", "")
            col_expr = col.get("Expression", "")

            if not col_expr or col_name.lower() == column_lower:
                continue

            refs = self._parse_references(col_expr)
            for ref_table, ref_col in refs.get("columns", []):
                if ref_table.lower() == table_lower and ref_col.lower() == column_lower:
                    result["used_in_calculated_columns"].append({
                        "calculated_column": col_name
                    })
                    break

        # Check relationships
        relationships = self.model.list_relationships()
        for rel in relationships:
            from_table = rel.get("FromTable", "")
            from_col = rel.get("FromColumn", "")
            to_table = rel.get("ToTable", "")
            to_col = rel.get("ToColumn", "")

            # Pre-compute lowercase for comparison
            from_table_lower = from_table.lower()
            from_col_lower = from_col.lower()
            to_table_lower = to_table.lower()
            to_col_lower = to_col.lower()

            if (from_table_lower == table_lower and from_col_lower == column_lower) or \
               (to_table_lower == table_lower and to_col_lower == column_lower):
                result["used_in_relationships"].append({
                    "from": f"{from_table}[{from_col}]",
                    "to": f"{to_table}[{to_col}]",
                    "active": rel.get("IsActive", False)
                })
                
        # Update summary
        result["summary"]["used_in_measures_count"] = len(result["used_in_measures"])
        result["summary"]["used_in_relationships_count"] = len(result["used_in_relationships"])
        result["summary"]["is_used"] = (
            len(result["used_in_measures"]) > 0 or
            len(result["used_in_calculated_columns"]) > 0 or
            len(result["used_in_relationships"]) > 0
        )
        
        return result
        
    def find_where_measure_used(
        self,
        table: str,
        measure: str,
        max_depth: int = 3
    ) -> Dict:
        """
        Find where a measure is used (forward and backward impact).

        Args:
            table: Table containing the measure
            measure: Measure name
            max_depth: Maximum recursion depth

        Returns:
            Dictionary with usage information
        """
        # Pre-compute lowercase versions for performance
        table_lower = table.lower()
        measure_lower = measure.lower()

        result = {
            "measure": measure,
            "table": table,
            "used_by_measures": [],
            "depends_on": {
                "measures": [],
                "columns": []
            },
            "impact_summary": {
                "direct_dependents": 0,
                "total_dependents": 0,
                "direct_dependencies": 0,
                "max_depth_analyzed": max_depth
            }
        }

        # Find measures that reference this measure
        all_measures = self.model.list_measures()
        for m in all_measures:
            m_table = m.get("Table", "")
            m_name = m.get("Name", "")
            m_expr = m.get("Expression", "")

            if not m_expr:
                continue

            # Skip self
            if m_table.lower() == table_lower and m_name.lower() == measure_lower:
                continue

            refs = self._parse_references(m_expr)
            for ref_table, ref_measure in refs.get("measures", []):
                if ref_table.lower() == table_lower and ref_measure.lower() == measure_lower:
                    result["used_by_measures"].append({
                        "table": m_table,
                        "measure": m_name
                    })
                    break
                    
        # Get dependencies (what this measure uses)
        deps = self.analyze_measure_dependencies(table, measure, max_depth)
        if deps.get("dependencies"):
            for dep in deps["dependencies"]:
                if dep.get("type") == "measure":
                    result["depends_on"]["measures"].append({
                        "table": dep.get("table"),
                        "measure": dep.get("name")
                    })
                elif dep.get("type") == "column":
                    result["depends_on"]["columns"].append({
                        "table": dep.get("table"),
                        "column": dep.get("name")
                    })
                    
        # Update summary
        result["impact_summary"]["direct_dependents"] = len(result["used_by_measures"])
        result["impact_summary"]["total_dependents"] = len(result["used_by_measures"])
        result["impact_summary"]["direct_dependencies"] = (
            len(result["depends_on"]["measures"]) + 
            len(result["depends_on"]["columns"])
        )
        
        return result
        
    def find_unused_objects(self) -> Dict:
        """
        Find unused measures, columns, and tables in the model.
        
        Returns:
            Dictionary with lists of unused objects
        """
        result = {
            "unused_measures": [],
            "unused_columns": [],
            "unused_tables": [],
            "summary": {
                "total_unused_measures": 0,
                "total_unused_columns": 0,
                "total_unused_tables": 0
            }
        }
        
        # Get all objects
        measures = self.model.list_measures()
        columns = self.model.list_columns()
        tables = self.model.list_tables()
        relationships = self.model.list_relationships()
        
        try:
            self._reference_index = DaxReferenceIndex(measures, columns)
        except (TypeError, KeyError, AttributeError) as e:
            # Fall back to lazy loading inside _get_reference_index
            logger.warning(f"Failed to build reference index from existing data: {e}")
            self._reference_index = None
        except Exception as e:
            logger.error(f"Unexpected error building reference index: {type(e).__name__}: {e}")
            self._reference_index = None
        
        # Build lowercase reference sets for case-insensitive matching
        referenced_measures_lower = set()
        referenced_columns_lower = set()
        referenced_tables_lower = set()
        
        # Check measure references
        for m in measures:
            expr = m.get("Expression", "")
            if not expr:
                continue
                
            refs = self._parse_references(expr)
            
            # Add referenced measures
            for ref_table, ref_measure in refs.get("measures", []):
                if ref_table and ref_measure:
                    ref_key = f"{ref_table.lower()}|{ref_measure.lower()}"
                    referenced_measures_lower.add(ref_key)
                    referenced_tables_lower.add(ref_table.lower())
                
            # Add referenced columns
            for ref_table, ref_col in refs.get("columns", []):
                if ref_table and ref_col:
                    ref_key = f"{ref_table.lower()}|{ref_col.lower()}"
                    referenced_columns_lower.add(ref_key)
                    referenced_tables_lower.add(ref_table.lower())
        
        # Check calculated column references
        for col in columns:
            if col.get("Type") == "Calculated":
                expr = col.get("Expression", "")
                if expr:
                    refs = self._parse_references(expr)
                    
                    for ref_table, ref_col in refs.get("columns", []):
                        if ref_table and ref_col:
                            ref_key = f"{ref_table.lower()}|{ref_col.lower()}"
                            referenced_columns_lower.add(ref_key)
                            referenced_tables_lower.add(ref_table.lower())
        
        # Check relationship references
        for rel in relationships:
            from_table = rel.get("FromTable", "")
            from_col = rel.get("FromColumn", "")
            to_table = rel.get("ToTable", "")
            to_col = rel.get("ToColumn", "")
            
            if from_table and from_col:
                ref_key = f"{from_table.lower()}|{from_col.lower()}"
                referenced_columns_lower.add(ref_key)
                referenced_tables_lower.add(from_table.lower())
                
            if to_table and to_col:
                ref_key = f"{to_table.lower()}|{to_col.lower()}"
                referenced_columns_lower.add(ref_key)
                referenced_tables_lower.add(to_table.lower())
        
        # Find unused measures
        for m in measures:
            table = m.get("Table", "")
            name = m.get("Name", "")
            
            if not table or not name:
                continue
                
            key = f"{table.lower()}|{name.lower()}"
            
            if key not in referenced_measures_lower:
                result["unused_measures"].append({
                    "table": table,
                    "measure": name,
                    "description": m.get("Description", "")
                })
        
        # Find unused columns (exclude hidden, key columns, and system RowNumber)
        for c in columns:
            table = c.get("Table", "")
            name = c.get("Name", "")
            is_hidden = c.get("IsHidden", False)
            is_key = c.get("IsKey", False)
            
            if not table or not name:
                continue
                
            # Skip hidden, key, and system columns
            if is_hidden or is_key or name.startswith("RowNumber-"):
                continue
            
            key = f"{table.lower()}|{name.lower()}"
            
            if key not in referenced_columns_lower:
                result["unused_columns"].append({
                    "table": table,
                    "column": name,
                    "type": c.get("Type", ""),
                    "data_type": c.get("DataType", "")
                })
        
        # Find unused tables
        tables_with_measures = {m.get("Table", "").lower() for m in measures if m.get("Table")}
        tables_with_columns_used = {c.get("Table", "").lower() for c in columns if c.get("Table")}
        
        for t in tables:
            name = t.get("Name", "")
            is_hidden = t.get("IsHidden", False)
            
            if not name:
                continue
                
            # Skip hidden tables
            if is_hidden:
                continue
            
            name_lower = name.lower()
            
            # Table is used if it has measures, is referenced, or has columns used
            is_used = (
                name_lower in tables_with_measures or
                name_lower in referenced_tables_lower or
                name_lower in tables_with_columns_used
            )
            
            if not is_used:
                result["unused_tables"].append({
                    "table": name,
                    "columns": t.get("Columns", 0),
                    "rows": t.get("RowsCount", 0)
                })
        
        # Update summary
        result["summary"]["total_unused_measures"] = len(result["unused_measures"])
        result["summary"]["total_unused_columns"] = len(result["unused_columns"])
        result["summary"]["total_unused_tables"] = len(result["unused_tables"])
        result["summary"]["columns_analyzed"] = len(columns)
        result["summary"]["columns_referenced"] = len(referenced_columns_lower)
        
        # Limit output
        result["unused_measures"] = result["unused_measures"][:50]
        result["unused_columns"] = result["unused_columns"][:50]
        result["unused_tables"] = result["unused_tables"][:20]
        
        return result
