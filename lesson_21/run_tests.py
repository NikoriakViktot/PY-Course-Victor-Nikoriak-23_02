import unittest
from pathlib import Path


if __name__ == "__main__":
    current_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(current_dir), pattern="test_file_context_manager.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)
