# Писав за допомогою ШІ

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



with FileContextManager('example.txt', 'w') as f:
    f.write('Hello World!')