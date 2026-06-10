## Task 1: File Context Manager Class

Для створення контекстного менеджера нам потрібно реалізувати магічні методи `__enter__` та `__exit__`. Ми додамо логування за допомогою стандартного модуля `logging` та статичні лічильники для відстеження кількості відкритих і закритих файлів.

Python

```
import logging
import sys

# Налаштування базового логування у консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class MonitoredFileCM:
    # Статичні лічильники для розширеного функціоналу
    total_opened = 0
    total_closed = 0

    def __init__(self, filename, mode="r", encoding="utf-8"):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.file_obj = None

    def __enter__(self):
        logging.info(f"Спроба відкрити файл: '{self.filename}' у режимі '{self.mode}'")
        try:
            self.file_obj = open(self.filename, self.mode, encoding=self.encoding)
            MonitoredFileCM.total_opened += 1
            logging.info(f"Файл '{self.filename}' успішно відкрито. Активно відкритих: {MonitoredFileCM.total_opened - MonitoredFileCM.total_closed}")
            return self.file_obj
        except Exception as e:
            logging.error(f"Не вдалося відкрити файл '{self.filename}': {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_obj:
            self.file_obj.close()
            MonitoredFileCM.total_closed += 1
            logging.info(f"Файл '{self.filename}' закрито. Всього закрито за сесію: {MonitoredFileCM.total_closed}")

        if exc_type is not None:
            # Логуємо помилку, яка виникла всередині блоку with
            logging.error(f"У контексті файлу '{self.filename}' виникло виключення: {exc_type.__name__}: {exc_val}")
            # Повертаємо False, щоб помилка прокинулася далі (стандартна поведінка для open)
            return False
        
        return True
```

## Task 2: Writing Tests for Context Manager

Використаємо бібліотеку `unittest`. Тут ми протестуємо:

1. Успішне читання/запис.
    
2. Поведінку при спробі відкрити неіснуючий файл.
    
3. Обробку та прокидання помилок, що виникають _всередині_ блоку `with`.
    
4. Роботу лічильників.
    

Python

```
import os
import unittest
from monitored_file import MonitoredFileCM  # Припустимо, код вище збережено у monitored_file.py

class TestMonitoredFileCM(unittest.TestCase):
    def setUp(self):
        self.test_filename = "test_sandbox.txt"
        self.content = "Привіт, світе! Тестовий рядок."
        # Скидаємо лічильники перед кожним тестом
        MonitoredFileCM.total_opened = 0
        MonitoredFileCM.total_closed = 0

    def tearDown(self):
        # Прибираємо за собою тестовий файл
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_positive_write_and_read(self):
        """Перевірка базового успішного запису та читання"""
        # Запис
        with MonitoredFileCM(self.test_filename, "w") as f:
            f.write(self.content)
        
        # Читання
        with MonitoredFileCM(self.test_filename, "r") as f:
            data = f.read()
        
        self.assertEqual(data, self.content)
        self.assertEqual(MonitoredFileCM.total_opened, 2)
        self.assertEqual(MonitoredFileCM.total_closed, 2)

    def test_file_not_found_raises_error(self):
        """Перевірка виникнення помилки, якщо файлу не існує для читання"""
        with self.assertRaises(FileNotFoundError):
            with MonitoredFileCM("non_existent_file.txt", "r") as f:
                f.read()

    def test_exception_inside_context_is_propagated(self):
        """Перевірка, що помилка всередині блоку with коректно спливає далі, але файл закривається"""
        with self.assertRaises(ZeroDivisionError):
            with MonitoredFileCM(self.test_filename, "w") as f:
                f.write("Текст")
                1 / 0  # Штучна помилка всередині контексту

        # Перевіряємо, що файл все одно закрився
        self.assertEqual(MonitoredFileCM.total_opened, 1)
        self.assertEqual(MonitoredFileCM.total_closed, 1)

if __name__ == "__main__":
    unittest.main()
```

## Task 3: Pytest Fixtures with Context Manager

Для запуску цього коду тобі знадобиться встановлений `pytest` (`pip install pytest`). Тут ми створюємо функцію `process_file_data`, фікстуру, яка готує файл через наш контекстний менеджер, і сам тест.

Python

```
import pytest
import os
from monitored_file import MonitoredFileCM

# Функція, яку ми тестуємо за умовою Task 3
def process_file_data(file_obj):
    """Приймає файловий об'єкт, читає дані та повертає їх у верхньому регістрі (UPPERCASE)"""
    data = file_obj.read()
    return data.upper()

# Pytest фікстура
@pytest.fixture
def temp_file_fixture():
    filename = "pytest_temp.txt"
    # Готуємо файл з даними
    with open(filename, "w", encoding="utf-8") as f:
        f.write("hello from pytest fixture")
    
    # Використовуємо наш кастомний CM для передачі об'єкта в тест
    with MonitoredFileCM(filename, "r") as f_obj:
        yield f_obj  # Тест виконається тут
    
    # Сcleanup після завершення тесту
    if os.path.exists(filename):
        os.remove(filename)

# Тест-кейс
def test_process_file_data(temp_file_fixture):
    # Передаємо фікстуру як аргумент
    result = process_file_data(temp_file_fixture)
    assert result == "HELLO FROM PYTEST FIXTURE"
```