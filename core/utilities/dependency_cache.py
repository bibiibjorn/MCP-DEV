"""
Dependency Cache System
Stores pre-computed dependencies for all measures/columns in a JSON file
to avoid recomputing dependencies every time the HTML is generated.
"""

import os
import json
import logging
import gzip
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyCache:
    """
    Manages a file-based cache of dependency data for Power BI models.
    Uses gzip compression for efficient storage.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the dependency cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to exports/cache
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default to exports/cache under the project root
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            self.cache_dir = project_root / "exports" / "cache"

        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, model_name: str = "default") -> Path:
        """Get the cache file path for a model."""
        safe_name = model_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"dependencies_{safe_name}.json.gz"

    def save_cache(
        self,
        all_measures: List[Dict[str, Any]],
        all_columns: List[Dict[str, Any]],
        all_dependencies: Dict[str, Any],
        model_name: str = "default"
    ) -> str:
        """
        Save dependency data to cache file.

        Args:
            all_measures: List of all measures in the model
            all_columns: List of all columns in the model
            all_dependencies: Pre-computed dependencies for all items
            model_name: Name of the model (for cache file naming)

        Returns:
            Path to the cache file
        """
        cache_data = {
            "metadata": {
                "model_name": model_name,
                "created_at": datetime.now().isoformat(),
                "measures_count": len(all_measures),
                "columns_count": len(all_columns),
                "dependencies_count": len(all_dependencies)
            },
            "all_measures": all_measures,
            "all_columns": all_columns,
            "all_dependencies": all_dependencies
        }

        cache_path = self._get_cache_path(model_name)

        try:
            # Save as gzip-compressed JSON
            with gzip.open(cache_path, 'wt', encoding='utf-8') as f:
                json.dump(cache_data, f, separators=(',', ':'))  # Compact JSON

            file_size = cache_path.stat().st_size / 1024  # KB
            logger.info(f"Saved dependency cache: {cache_path} ({file_size:.1f} KB)")
            logger.info(f"  - {len(all_measures)} measures, {len(all_columns)} columns, {len(all_dependencies)} dependencies")

            return str(cache_path)

        except Exception as e:
            logger.error(f"Failed to save dependency cache: {e}")
            return None

    def load_cache(self, model_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Load dependency data from cache file.

        Args:
            model_name: Name of the model

        Returns:
            Cache data dict or None if not found/invalid
        """
        cache_path = self._get_cache_path(model_name)

        if not cache_path.exists():
            logger.debug(f"Cache file not found: {cache_path}")
            return None

        try:
            with gzip.open(cache_path, 'rt', encoding='utf-8') as f:
                cache_data = json.load(f)

            metadata = cache_data.get("metadata", {})
            logger.info(f"Loaded dependency cache: {cache_path}")
            logger.info(f"  - Created: {metadata.get('created_at', 'unknown')}")
            logger.info(f"  - {metadata.get('measures_count', 0)} measures, {metadata.get('columns_count', 0)} columns")

            return cache_data

        except Exception as e:
            logger.error(f"Failed to load dependency cache: {e}")
            return None

    def clear_cache(self, model_name: str = "default") -> bool:
        """Clear the cache file for a model."""
        cache_path = self._get_cache_path(model_name)

        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.info(f"Cleared cache: {cache_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to clear cache: {e}")
                return False
        return True


def compute_all_dependencies(
    query_executor,
    dependency_analyzer,
    model_name: str = "default",
    save_to_cache: bool = True
) -> Dict[str, Any]:
    """
    Compute dependencies for ALL measures and columns in the model.

    This function performs a comprehensive analysis of the entire model
    and can optionally save the results to a cache file.

    Args:
        query_executor: QueryExecutor instance for fetching model data
        dependency_analyzer: DependencyAnalyzer instance for analyzing dependencies
        model_name: Name of the model (for cache naming)
        save_to_cache: Whether to save results to cache file

    Returns:
        Dict containing all_measures, all_columns, and all_dependencies
    """
    logger.info(f"Computing all dependencies for model: {model_name}")

    all_measures = []
    all_columns = []
    all_dependencies = {}

    # Build measure lookup for resolving unqualified measure references
    measure_name_to_table = {}

    # Fetch all measures (no TOP limit)
    measures_result = query_executor.execute_info_query("MEASURES")
    if measures_result.get('success'):
        rows = measures_result.get('rows', [])
        logger.info(f"MEASURES query returned {len(rows)} rows")
        for m in rows:
            m_table = m.get('Table', '') or ''
            m_name = m.get('Name', '') or ''
            m_expr = m.get('Expression', '') or ''
            if m_table and m_name:
                all_measures.append({
                    'table': m_table,
                    'name': m_name,
                    'expression': m_expr
                })
                # Build lookup for resolving unqualified references
                name_key = m_name.lower().strip()
                if name_key not in measure_name_to_table:
                    measure_name_to_table[name_key] = m_table
    else:
        logger.warning(f"MEASURES query failed: {measures_result.get('error', 'unknown')}")

    logger.info(f"Found {len(all_measures)} measures")

    # Fetch all columns (no TOP limit)
    columns_result = query_executor.execute_info_query("COLUMNS")
    if columns_result.get('success'):
        rows = columns_result.get('rows', [])
        logger.info(f"COLUMNS query returned {len(rows)} rows")
        for c in rows:
            c_table = c.get('Table', '') or ''
            # Try different field names for column name
            c_name = c.get('Name', '') or c.get('Column', '') or c.get('ExplicitName', '') or ''
            # Skip system columns
            c_type = c.get('Type', 0)
            if c_table and c_name and c_type != 2:  # Type 2 is RowNumber
                all_columns.append({
                    'table': c_table,
                    'name': c_name
                })
    else:
        logger.warning(f"COLUMNS query failed: {columns_result.get('error', 'unknown')}")

    logger.info(f"Found {len(all_columns)} columns")

    # Helper function to resolve unqualified measure references
    def resolve_measure_ref(table: str, name: str) -> str:
        """Resolve a measure reference, filling in table name if missing."""
        if table:
            return f"{table}[{name}]"
        # Look up table from measure name
        name_key = name.lower().strip()
        resolved_table = measure_name_to_table.get(name_key, '')
        if resolved_table:
            return f"{resolved_table}[{name}]"
        # Fallback: return without table (shouldn't happen often)
        return f"[{name}]"

    # Compute dependencies for each measure
    logger.info(f"Computing dependencies for {len(all_measures)} measures...")
    for idx, m_data in enumerate(all_measures):
        m_table = m_data['table']
        m_name = m_data['name']
        m_key = f"{m_table}[{m_name}]"

        if idx > 0 and idx % 50 == 0:
            logger.info(f"  Progress: {idx}/{len(all_measures)} measures...")

        try:
            # Get dependencies for this measure
            m_deps = dependency_analyzer.analyze_dependencies(m_table, m_name, include_diagram=False)
            if m_deps.get('success'):
                # Get what uses this measure
                m_usage = dependency_analyzer.find_measure_usage(m_table, m_name)
                m_used_by = m_usage.get('used_by', []) if m_usage.get('success') else []

                # Resolve measure references (some may have empty table names)
                upstream_measures = []
                for t, n in m_deps.get('referenced_measures', []):
                    ref = resolve_measure_ref(t, n)
                    if ref not in upstream_measures:
                        upstream_measures.append(ref)

                # Columns should always have table names
                upstream_columns = []
                for t, n in m_deps.get('referenced_columns', []):
                    if t and n:
                        col_ref = f"{t}[{n}]"
                        if col_ref not in upstream_columns:
                            upstream_columns.append(col_ref)

                all_dependencies[m_key] = {
                    'key': m_key,
                    'type': 'measure',
                    'table': m_table,
                    'name': m_name,
                    'upstream': {
                        'measures': upstream_measures,
                        'columns': upstream_columns
                    },
                    'downstream': {
                        'measures': [f"{item.get('table', '')}[{item.get('measure', '')}]"
                                   for item in m_used_by if item.get('table') and item.get('measure')],
                        'visuals': []
                    }
                }
        except Exception as e:
            logger.debug(f"Could not compute dependencies for {m_key}: {e}")
            all_dependencies[m_key] = {
                'key': m_key,
                'type': 'measure',
                'table': m_table,
                'name': m_name,
                'upstream': {'measures': [], 'columns': []},
                'downstream': {'measures': [], 'visuals': []}
            }

    logger.info(f"Computed dependencies for {len(all_dependencies)} measures")

    # Add columns to dependencies
    for c_data in all_columns:
        c_table = c_data['table']
        c_name = c_data['name']
        c_key = f"{c_table}[{c_name}]"

        if c_key not in all_dependencies:
            # Find which measures use this column
            using_measures = []
            for m_key, m_deps in all_dependencies.items():
                if m_deps.get('type') == 'measure':
                    if c_key in m_deps.get('upstream', {}).get('columns', []):
                        using_measures.append(m_key)

            all_dependencies[c_key] = {
                'key': c_key,
                'type': 'column',
                'table': c_table,
                'name': c_name,
                'upstream': {'measures': [], 'columns': []},
                'downstream': {'measures': using_measures, 'visuals': []}
            }

    logger.info(f"Total items with dependencies: {len(all_dependencies)}")

    # Save to cache if requested
    if save_to_cache:
        cache = DependencyCache()
        cache.save_cache(all_measures, all_columns, all_dependencies, model_name)

    return {
        'all_measures': all_measures,
        'all_columns': all_columns,
        'all_dependencies': all_dependencies
    }
