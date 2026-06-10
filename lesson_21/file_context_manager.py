from datetime import datetime


class FileContextManager:
    open_counter = 0
    close_counter = 0
    log_file = "context_manager_logs.txt"

    def __init__(self, filename, mode="r", encoding="utf-8"):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.file = None

    @classmethod
    def reset_counters(cls):
        cls.open_counter = 0
        cls.close_counter = 0

    @classmethod
    def write_log(cls, message):
        with open(cls.log_file, "a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

    def __enter__(self):
        self.file = open(self.filename, self.mode, encoding=self.encoding)
        type(self).open_counter += 1
        type(self).write_log(f"Opened file: {self.filename}")
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        if self.file and not self.file.closed:
            self.file.close()
            type(self).close_counter += 1
            type(self).write_log(f"Closed file: {self.filename}")

        if exc_type is not None:
            type(self).write_log(f"Error: {exc_type.__name__}: {exc_value}")

        return False
