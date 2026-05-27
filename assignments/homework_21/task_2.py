import unittest
import os


class FileContextManager:
    file_counter = 0

    def __init__(self, filename, mode='r', encoding='utf-8'):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.file = None

    def _write_log(self, message):
        with open('magazin.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(message + '\n')

    def __enter__(self):
        try:
            self.file = open(self.filename, self.mode, encoding=self.encoding)
            FileContextManager.file_counter += 1
            self._write_log(f"Відкрит: файл '{self.filename}'. Всього відкрито: {FileContextManager.file_counter}")
            return self.file
        except Exception as error:
            self._write_log(f"Помилка: не вдалося відкрити файл '{self.filename}': {error}")
            raise error

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
            self._write_log(f"Закрит: файл '{self.filename}'")

        if exc_type is not None:
            self._write_log(f"Помилка: в середині блока виключення {exc_type.__name__}: {exc_val}")
            return False

        return True


class Test(unittest.TestCase):
    def setUp(self):
        FileContextManager.file_counter = 0
        with open('example.txt', 'w', encoding='utf-8') as f:
            f.write("hello world")
        with open('magazin.txt', 'w', encoding='utf-8') as f:
            f.write("")

    def test_file_context_success(self):
        with FileContextManager('example.txt', 'r') as f:
            content = f.read()
            self.assertEqual(content, "hello world")
        with self.assertRaises(ValueError):
            f.read()

    def test_logging_and_counter(self):
        with FileContextManager('example.txt', 'r'):
            pass

        self.assertEqual(FileContextManager.file_counter, 1)

        with open('magazin.txt', 'r', encoding='utf-8') as log:
            logs = log.read()
            self.assertIn("Відкрит: файл 'example.txt'", logs)
            self.assertIn("Закрит: файл 'example.txt'", logs)

    def test_open_failure_logging(self):
        if os.path.exists('non_existent.txt'):
            os.remove('non_existent.txt')

        with self.assertRaises(FileNotFoundError):
            with FileContextManager('non_existent.txt', 'r'):
                pass

        self.assertEqual(FileContextManager.file_counter, 0)

        with open('magazin.txt', 'r', encoding='utf-8') as log:
            logs = log.read()
            self.assertIn("Помилка: не вдалося відкрити файл 'non_existent.txt'", logs)

    def test_exception_inside_context(self):
        with self.assertRaises(IndexError):
            with FileContextManager('example.txt', 'r'):
                raise IndexError("Custom crash")

        with open('magazin.txt', 'r', encoding='utf-8') as log:
            logs = log.read()
            self.assertIn("Помилка: в середині блока виключення IndexError: Custom crash", logs)


if __name__ == '__main__':
    unittest.main()
