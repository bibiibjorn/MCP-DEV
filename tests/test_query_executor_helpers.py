import unittest
from typing import Any, Dict

from core.query_executor import OptimizedQueryExecutor


class DummyConn:
    ConnectionString = ""  # not used in these tests


class QEHelperTests(unittest.TestCase):
    def test_get_measure_details_helper_exists(self):
        # Ensure method exists and can be invoked without raising when ADOMD not available.
        qe = OptimizedQueryExecutor(DummyConn())
        # Monkeypatch ADOMD availability to avoid actual execution
        from core import query_executor as mod
        mod.ADOMD_AVAILABLE = False
        res = qe.get_measure_details_with_fallback("T", "M")
        self.assertIsInstance(res, dict)

    def test_table_mapping_bracketed_id_precedence(self):
        # Create a dummy QE that returns bracketed keys for INFO.TABLES()
        class DummyQE(OptimizedQueryExecutor):
            def validate_and_execute_dax(self, query: str, top_n: int = 0, bypass_cache: bool = False) -> Dict[str, Any]:
                q = (query or "").upper()
                if "INFO.TABLES" in q:
                    return {
                        'success': True,
                        'rows': [
                            {'[Name]': 'Sales', '[ID]': 42},
                            {'[Name]': 'Dates', '[ID]': 7},
                        ]
                    }
                return {'success': False, 'error': 'not implemented'}

        qe = DummyQE(DummyConn())
        # This should use [ID] first when building the map
        tid = qe._get_table_id_from_name('Sales')
        self.assertEqual(tid, 42)
        name = qe._get_table_name_from_id(7)
        self.assertEqual(name, 'Dates')


if __name__ == "__main__":
    unittest.main()
