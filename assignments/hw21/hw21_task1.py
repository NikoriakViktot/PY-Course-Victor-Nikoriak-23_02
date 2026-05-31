import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class FileContextManager:
    counter = 0

    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        FileContextManager.counter += 1
        logging.info(f"[{datetime.now()}] Opening file: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.info(f"[{datetime.now()}] Closing file: {self.filename}")

        if self.file:
            self.file.close()

        if exc_type:
            logging.error(f"Exception: {exc_type}, {exc_val}")
            return False  # не приглушуємо помилку

        return True