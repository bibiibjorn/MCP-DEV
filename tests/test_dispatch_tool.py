import unittest

from src.pbixray_server_enhanced import _dispatch_tool


class DispatchToolTests(unittest.TestCase):
    def test_unknown_tool(self):
        res = _dispatch_tool("__no_such_tool__", {})
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get("success", True))
        self.assertEqual(res.get("error_type"), "unknown_tool")

    def test_get_server_info_contains_error_schema_and_telemetry(self):
        # Synchronous wrapper around call_tool path isn't needed; we call dispatcher directly
        res = _dispatch_tool("get_server_info", {})
        self.assertTrue(res.get("success"))
        self.assertIn("error_schema", res)
        self.assertIn("telemetry", res)
        tele = res.get("telemetry", {})
        self.assertIn("total_calls", tele)

    def test_connection_gating_when_not_connected(self):
        # Without a connection, list_tables should return not_connected error
        res = _dispatch_tool("list_tables", {})
        self.assertFalse(res.get("success", True))
        self.assertEqual(res.get("error_type"), "not_connected")

    def test_apply_tmdl_patch_validation(self):
        # Missing updates array
        res = _dispatch_tool("apply_tmdl_patch", {})
        self.assertFalse(res.get("success", True))
        self.assertEqual(res.get("error_type"), "invalid_input")
        # Invalid update item: no fields to change
        res2 = _dispatch_tool("apply_tmdl_patch", {"updates": [{"table": "T", "measure": "M"}]})
        self.assertFalse(res2.get("success", True))
        # Manager may be unavailable; ensure we get item-level error in results for dry-run, so force dry_run True
        res3 = _dispatch_tool("apply_tmdl_patch", {"updates": [{"table": "T", "measure": "M", "description": "d"}], "dry_run": True})
        self.assertTrue(res3.get("success", False))
        self.assertTrue(res3.get("dry_run", False))
        self.assertGreaterEqual(res3.get("count", 0), 1)


if __name__ == "__main__":
    unittest.main()
