import tempfile
import unittest
from pathlib import Path

try:
    from file_context_manager import FileContextManager
except ImportError:
    from lesson_21.file_context_manager import FileContextManager


class TestFileContextManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_file = self.temp_path / "sample.txt"
        self.log_file = self.temp_path / "logs.txt"

        FileContextManager.log_file = self.log_file
        FileContextManager.reset_counters()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_and_read_file(self):
        with FileContextManager(self.test_file, "w") as file:
            file.write("Hello world")

        with FileContextManager(self.test_file, "r") as file:
            result = file.read()

        self.assertEqual(result, "Hello world")
        self.assertEqual(FileContextManager.open_counter, 2)
        self.assertEqual(FileContextManager.close_counter, 2)

    def test_file_is_closed_after_context(self):
        with FileContextManager(self.test_file, "w") as file:
            file.write("Some text")

        self.assertTrue(file.closed)

    def test_log_file_created(self):
        with FileContextManager(self.test_file, "w") as file:
            file.write("Some text")

        self.assertTrue(self.log_file.exists())

        log_content = self.log_file.read_text(encoding="utf-8")

        self.assertIn("Opened file", log_content)
        self.assertIn("Closed file", log_content)

    def test_file_not_found_error(self):
        missing_file = self.temp_path / "missing.txt"

        with self.assertRaises(FileNotFoundError):
            with FileContextManager(missing_file, "r") as file:
                file.read()

        self.assertEqual(FileContextManager.open_counter, 0)
        self.assertEqual(FileContextManager.close_counter, 0)

    def test_runtime_error_is_not_suppressed(self):
        context_manager = FileContextManager(self.test_file, "w")

        with self.assertRaises(RuntimeError):
            with context_manager as file:
                file.write("Some text")
                raise RuntimeError("Runtime problem")

        self.assertTrue(context_manager.file.closed)

        log_content = self.log_file.read_text(encoding="utf-8")

        self.assertIn("Error: RuntimeError", log_content)
        self.assertIn("Runtime problem", log_content)

    def test_invalid_mode_error(self):
        with self.assertRaises(ValueError):
            with FileContextManager(self.test_file, "wrong_mode") as file:
                file.write("Some text")


if __name__ == "__main__":
    unittest.main()
