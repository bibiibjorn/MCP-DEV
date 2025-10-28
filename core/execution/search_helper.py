"""Search functionality for measures, columns, and tables."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SearchHelper:
    """Helper for searching across Power BI model objects."""

    @staticmethod
    def search_measures(
        executor_callback,
        table_mapper,
        search_text: str,
        search_in_expression: bool = True,
        search_in_name: bool = True
    ) -> Dict[str, Any]:
        """Search for text in DAX measures."""
        try:
            from core.execution.dmv_helper import DmvHelper
            escaped_text = DmvHelper.escape_dax_string(search_text)
            conditions = []

            if search_in_expression:
                conditions.append(f'SEARCH("{escaped_text}", [Expression], 1, 0) > 0')
            if search_in_name:
                conditions.append(f'SEARCH("{escaped_text}", [Name], 1, 0) > 0')

            filter_expr = ' || '.join(conditions) if conditions else 'TRUE()'
            query = f"EVALUATE FILTER(INFO.MEASURES(), {filter_expr})"

            result = executor_callback(query, 0)
            # Map TableID -> Table name for usability
            if result.get('success'):
                rows = result.get('rows', [])
                for row in rows:
                    if 'TableID' in row and 'Table' not in row:
                        name = table_mapper.get_table_name_from_id(row.get('TableID'), executor_callback)
                        row['Table'] = name or str(row.get('TableID'))
            return result
        except Exception as e:
            logger.error(f"Error searching measures: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def search_objects(
        executor_callback,
        table_mapper,
        pattern: str,
        object_types: List[str]
    ) -> Dict[str, Any]:
        """Search for objects by pattern."""
        try:
            from core.execution.dmv_helper import DmvHelper
            search_text = pattern.replace('*', '').replace('?', '')
            escaped_text = DmvHelper.escape_dax_string(search_text)
            results_list = []

            if "tables" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.TABLES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "table",
                    "Name", [Name],
                    "IsHidden", [IsHidden],
                    "ModifiedTime", [ModifiedTime]
                )
                """
                r = executor_callback(query, 0)
                if r.get('success'):
                    results_list.extend(r['rows'])

            if "columns" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.COLUMNS(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "column",
                    "Name", [Name],
                    "TableID", [TableID],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden]
                )
                """
                r = executor_callback(query, 0)
                if r.get('success'):
                    # Map TableID -> Table name
                    for row in r.get('rows', []):
                        if 'TableID' in row:
                            name = table_mapper.get_table_name_from_id(row.get('TableID'), executor_callback)
                            row['Table'] = name or str(row.get('TableID'))
                    results_list.extend(r['rows'])

            if "measures" in object_types:
                query = f"""
                EVALUATE SELECTCOLUMNS(
                    FILTER(INFO.MEASURES(), SEARCH("{escaped_text}", [Name], 1, 0) > 0),
                    "type", "measure",
                    "Name", [Name],
                    "TableID", [TableID],
                    "DataType", [DataType],
                    "IsHidden", [IsHidden],
                    "DisplayFolder", [DisplayFolder]
                )
                """
                r = executor_callback(query, 0)
                if r.get('success'):
                    for row in r.get('rows', []):
                        if 'TableID' in row:
                            name = table_mapper.get_table_name_from_id(row.get('TableID'), executor_callback)
                            row['Table'] = name or str(row.get('TableID'))
                    results_list.extend(r['rows'])

            return {
                'success': True,
                'rows': results_list,
                'results': results_list,
                'row_count': len(results_list),
                'count': len(results_list)
            }
        except Exception as e:
            logger.error(f"Error searching objects: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def is_table_expression(query: str) -> bool:
        """Check if query is a table expression."""
        table_keywords = [
            'SELECTCOLUMNS', 'ADDCOLUMNS', 'SUMMARIZE', 'FILTER',
            'VALUES', 'ALL', 'INFO.', 'TOPN', 'SAMPLE', 'SUMMARIZECOLUMNS'
        ]
        return any(kw in query.upper() for kw in table_keywords)
