import unittest
from core.input_validator import InputValidator, validate_and_sanitize_identifier


class InputValidatorTests(unittest.TestCase):
    def test_validate_and_sanitize_identifier(self):
        s = validate_and_sanitize_identifier(" Sales--Table ")
        self.assertEqual(s, "Sales--Table")

    def test_path_traversal_blocked(self):
        ok, err = InputValidator.validate_export_path("..\\secret.txt", base_dir="C:/temp")
        self.assertFalse(ok)
        self.assertIsNotNone(err)
        self.assertIn("Path traversal", str(err))

    def test_disallowed_extension(self):
        ok, err = InputValidator.validate_export_path("report.exe")
        self.assertFalse(ok)
        self.assertIsNotNone(err)
        self.assertIn("not allowed", str(err))

    def test_validate_page_size_bounds(self):
        ok, err, val = InputValidator.validate_page_size(0)
        self.assertFalse(ok)
        ok2, err2, val2 = InputValidator.validate_page_size(10001)
        self.assertFalse(ok2)


if __name__ == "__main__":
    unittest.main()
