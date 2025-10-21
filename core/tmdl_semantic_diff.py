"""
TMDL Semantic Diff Analyzer

Analyzes TMDL differences at a semantic level, categorizing changes
by object type (tables, measures, columns, relationships, etc.)
for better readability.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import difflib

logger = logging.getLogger(__name__)


class TmdlSemanticDiff:
    """
    Analyzes TMDL differences semantically, grouping changes by object type.
    """

    def __init__(self, model1_data: Dict[str, Any], model2_data: Dict[str, Any]):
        """
        Initialize semantic diff analyzer.

        Args:
            model1_data: Parsed TMDL structure for model 1
            model2_data: Parsed TMDL structure for model 2
        """
        self.model1 = model1_data
        self.model2 = model2_data

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze differences and categorize by object type.

        Returns:
            Dictionary with categorized changes
        """
        result = {
            'model_properties': self._diff_model_properties(),
            'tables': self._diff_tables(),
            'columns': self._diff_columns(),
            'measures': self._diff_measures(),
            'relationships': self._diff_relationships(),
            'roles': self._diff_roles(),
            'has_changes': False
        }

        # Check if any changes exist
        for key, value in result.items():
            if key != 'has_changes' and value:
                if isinstance(value, dict):
                    if any(v for v in value.values() if v):
                        result['has_changes'] = True
                        break
                elif value:
                    result['has_changes'] = True
                    break

        return result

    def _diff_model_properties(self) -> Dict[str, Any]:
        """Compare model-level properties."""
        changes = {}

        model1_props = self.model1.get('model', {})
        model2_props = self.model2.get('model', {})

        for key in ['name', 'compatibility_level', 'default_mode']:
            val1 = model1_props.get(key)
            val2 = model2_props.get(key)
            if val1 != val2:
                changes[key] = {'from': val1, 'to': val2}

        return changes

    def _diff_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compare tables."""
        tables1 = self._get_tables_dict(self.model1)
        tables2 = self._get_tables_dict(self.model2)

        names1 = set(tables1.keys())
        names2 = set(tables2.keys())

        result = {
            'added': [{'name': name, 'columns_count': len(tables2[name].get('columns', [])),
                      'measures_count': len(tables2[name].get('measures', []))}
                     for name in sorted(names2 - names1)],
            'removed': [{'name': name, 'columns_count': len(tables1[name].get('columns', [])),
                        'measures_count': len(tables1[name].get('measures', []))}
                       for name in sorted(names1 - names2)],
            'modified': []
        }

        # Check for modified tables (property changes only, not columns/measures)
        for name in sorted(names1 & names2):
            table1 = tables1[name]
            table2 = tables2[name]

            changes = {}
            if table1.get('is_hidden') != table2.get('is_hidden'):
                changes['is_hidden'] = {
                    'from': table1.get('is_hidden', False),
                    'to': table2.get('is_hidden', False)
                }
            if table1.get('description') != table2.get('description'):
                changes['description'] = {
                    'from': table1.get('description'),
                    'to': table2.get('description')
                }

            if changes:
                result['modified'].append({
                    'name': name,
                    'changes': changes
                })

        return result

    def _diff_columns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compare columns across all tables."""
        columns1 = self._get_all_columns(self.model1)
        columns2 = self._get_all_columns(self.model2)

        keys1 = set(columns1.keys())
        keys2 = set(columns2.keys())

        result = {
            'added': [],
            'removed': [],
            'modified': []
        }

        # Added columns
        for key in sorted(keys2 - keys1):
            col = columns2[key]
            table_name, col_name = key.split('|||')
            result['added'].append({
                'table': table_name,
                'name': col_name,
                'data_type': col.get('data_type'),
                'is_calculated': col.get('is_calculated', False),
                'source_column': col.get('source_column')
            })

        # Removed columns
        for key in sorted(keys1 - keys2):
            col = columns1[key]
            table_name, col_name = key.split('|||')
            result['removed'].append({
                'table': table_name,
                'name': col_name,
                'data_type': col.get('data_type'),
                'is_calculated': col.get('is_calculated', False)
            })

        # Modified columns
        for key in sorted(keys1 & keys2):
            col1 = columns1[key]
            col2 = columns2[key]
            table_name, col_name = key.split('|||')

            changes = {}

            # Check important properties
            for prop in ['data_type', 'source_column', 'is_calculated', 'is_hidden',
                        'format_string', 'display_folder', 'description']:
                val1 = col1.get(prop)
                val2 = col2.get(prop)
                if val1 != val2:
                    changes[prop] = {'from': val1, 'to': val2}

            # Check expression changes for calculated columns
            if col1.get('expression') != col2.get('expression'):
                changes['expression'] = {
                    'from': col1.get('expression', ''),
                    'to': col2.get('expression', '')
                }

            if changes:
                result['modified'].append({
                    'table': table_name,
                    'name': col_name,
                    'changes': changes
                })

        return result

    def _diff_measures(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compare measures across all tables."""
        measures1 = self._get_all_measures(self.model1)
        measures2 = self._get_all_measures(self.model2)

        keys1 = set(measures1.keys())
        keys2 = set(measures2.keys())

        result = {
            'added': [],
            'removed': [],
            'modified': []
        }

        # Added measures
        for key in sorted(keys2 - keys1):
            meas = measures2[key]
            table_name, meas_name = key.split('|||')
            result['added'].append({
                'table': table_name,
                'name': meas_name,
                'expression': meas.get('expression'),
                'format_string': meas.get('format_string'),
                'display_folder': meas.get('display_folder')
            })

        # Removed measures
        for key in sorted(keys1 - keys2):
            meas = measures1[key]
            table_name, meas_name = key.split('|||')
            result['removed'].append({
                'table': table_name,
                'name': meas_name,
                'expression': meas.get('expression'),
                'format_string': meas.get('format_string')
            })

        # Modified measures
        for key in sorted(keys1 & keys2):
            meas1 = measures1[key]
            meas2 = measures2[key]
            table_name, meas_name = key.split('|||')

            changes = {}

            # Check expression (most important)
            if self._normalize_dax(meas1.get('expression', '')) != self._normalize_dax(meas2.get('expression', '')):
                changes['expression'] = {
                    'from': meas1.get('expression', ''),
                    'to': meas2.get('expression', '')
                }

            # Check other properties
            for prop in ['format_string', 'display_folder', 'description', 'is_hidden']:
                val1 = meas1.get(prop)
                val2 = meas2.get(prop)
                if val1 != val2:
                    changes[prop] = {'from': val1, 'to': val2}

            if changes:
                result['modified'].append({
                    'table': table_name,
                    'name': meas_name,
                    'changes': changes
                })

        return result

    def _diff_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compare relationships."""
        rels1 = {self._rel_key(r): r for r in self.model1.get('relationships', [])}
        rels2 = {self._rel_key(r): r for r in self.model2.get('relationships', [])}

        keys1 = set(rels1.keys())
        keys2 = set(rels2.keys())

        result = {
            'added': [],
            'removed': [],
            'modified': []
        }

        # Added relationships
        for key in sorted(keys2 - keys1):
            rel = rels2[key]
            result['added'].append({
                'from_column': rel.get('from_column'),
                'to_column': rel.get('to_column'),
                'from_cardinality': rel.get('from_cardinality'),
                'to_cardinality': rel.get('to_cardinality'),
                'is_active': rel.get('is_active', True),
                'cross_filtering_behavior': rel.get('cross_filtering_behavior')
            })

        # Removed relationships
        for key in sorted(keys1 - keys2):
            rel = rels1[key]
            result['removed'].append({
                'from_column': rel.get('from_column'),
                'to_column': rel.get('to_column'),
                'from_cardinality': rel.get('from_cardinality'),
                'to_cardinality': rel.get('to_cardinality')
            })

        # Modified relationships
        for key in sorted(keys1 & keys2):
            rel1 = rels1[key]
            rel2 = rels2[key]

            changes = {}
            for prop in ['is_active', 'cross_filtering_behavior', 'from_cardinality', 'to_cardinality']:
                val1 = rel1.get(prop)
                val2 = rel2.get(prop)
                if val1 != val2:
                    changes[prop] = {'from': val1, 'to': val2}

            if changes:
                result['modified'].append({
                    'from_column': rel1.get('from_column'),
                    'to_column': rel1.get('to_column'),
                    'changes': changes
                })

        return result

    def _diff_roles(self) -> Dict[str, List[Any]]:
        """Compare roles."""
        roles1 = {r.get('name'): r for r in self.model1.get('roles', [])}
        roles2 = {r.get('name'): r for r in self.model2.get('roles', [])}

        names1 = set(roles1.keys())
        names2 = set(roles2.keys())

        return {
            'added': sorted(list(names2 - names1)),
            'removed': sorted(list(names1 - names2)),
            'modified': []  # Could be enhanced to show RLS changes
        }

    def _get_tables_dict(self, model: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get tables as a dictionary keyed by name."""
        tables = model.get('tables', {})
        if isinstance(tables, dict):
            return tables
        elif isinstance(tables, list):
            return {t['name']: t for t in tables}
        return {}

    def _get_all_columns(self, model: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get all columns from all tables, keyed by 'table|||column'."""
        columns = {}
        tables = self._get_tables_dict(model)

        for table_name, table in tables.items():
            for col in table.get('columns', []):
                # Use ||| as separator to avoid issues with dots in names
                key = f"{table_name}|||{col['name']}"
                columns[key] = col

        return columns

    def _get_all_measures(self, model: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get all measures from all tables, keyed by 'table|||measure'."""
        measures = {}
        tables = self._get_tables_dict(model)

        for table_name, table in tables.items():
            for meas in table.get('measures', []):
                # Use ||| as separator to avoid issues with dots in names
                key = f"{table_name}|||{meas['name']}"
                measures[key] = meas

        return measures

    def _rel_key(self, rel: Dict[str, Any]) -> str:
        """Generate unique key for relationship."""
        from_col = rel.get('from_column', '')
        to_col = rel.get('to_column', '')
        return f"{from_col}|{to_col}"

    def _normalize_dax(self, dax: str) -> str:
        """Normalize DAX for comparison."""
        if not dax:
            return ""
        return ' '.join(dax.split()).strip()
