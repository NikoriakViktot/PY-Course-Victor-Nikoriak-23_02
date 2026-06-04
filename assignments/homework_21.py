# Task 1
# Клас-менеджер контексту файлу
# Створіть власний клас, який буде працювати аналогічно вбудованій функції «open». Крім того,
# вам потрібно розширити його функціональність за допомогою лічильника та ведення журналу.
# Зверніть особливу увагу на реалізацію методу «__exit__», який повинен відповідати всім
# вимогам до менеджерів контексту, зазначеним тут:
# Context Manager Types
# The with statement

import sys
class CustomOpen:
    # Класовий атрибут (лічильник) для відстеження загальної кількості відкриттів файлів
    execution_counter = 0
    def __init__(self, filename, mode='r', encoding='utf-8'):
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.file = None
    def __enter__(self):
        # Збільшуємо лічильник відкриттів
        CustomOpen.execution_counter += 1
        # Логування початку роботи
        print(f"[LOG] Спроба відкрити файл '{self.filename}' у режимі '{self.mode}'. "
              f"Загальний лічильник відкриттів: {CustomOpen.execution_counter}")
        # Відкриваємо реальний файл
        self.file = open(self.filename, self.mode, encoding=self.encoding)
        # Повертаємо об'єкт файлу у блок `with ... as`
        return self.file
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Логування завершення роботи блоку with
        print(f"[LOG] Завершення роботи з файлом '{self.filename}'.")
        # Гарантовано закриваємо файл, якщо він був відкритий
        if self.file:
            self.file.close()
            print(f"[LOG] Файл '{self.filename}' успішно закрито.")
        # Обробка та логування помилок, якщо вони виникли всередині блоку with
        if exc_type is not None:
            print(f"[LOG] [УВАГА] У блоці 'with' виникло виключення!")
            print(f"      Тип помилки: {exc_type.__name__}")
            print(f"      Значення: {exc_val}")
            # Повертаємо False, щоб Python прокинув (raise) помилку далі по стеку.
            # Якщо повернути True, помилка буде "пригнічена" (suppressed),
            # що суперечить стандартній поведінці вбудованого `open`.
            return False
        # Повернення None (або False) сигналізує, що все пройшло без помилок
        return True
# Успішний сценарій (Запис та читання)
# Запис у файл
with CustomOpen("demo.txt", "w") as file:
    file.write("Привіт, це тест власного менеджера контексту!\n")
    file.write("Python працює чудово.")
print("-" * 50)
# Читання з файлу
with CustomOpen("demo.txt", "r") as file:
    content = file.read()
    print(f"\nЗміст файлу:\n{content}\n")
print("-" * 50)
# Сценарій з виникненням помилки всередині блоку
try:
    with CustomOpen("demo.txt", "r") as file:
        print("Спробуємо виконати помилкову операцію...")
        # Викличемо помилку ZeroDivisionError всередині блоку
        result = 10 / 0
except ZeroDivisionError:
    print("\n[СИСТЕМА] Помилку ZeroDivisionError було успішно перехоплено ззовні.")

# Task 2
# Написання тестів для менеджера контексту
# Візьміть свою реалізацію класу менеджера контексту з Завдання 1 і напишіть для неї тести.
# Спробуйте охопити якомога більше варіантів використання: як успішні, коли файл існує і все
# працює за задумом, так і ті, коли ваш клас генерує помилки або у наборі контекстів виконання
# трапляються помилки.
import unittest
from unittest.mock import patch, mock_open
# Імпортуємо наш клас (припустимо, він у файлі custom_open_module.py)
# Якщо код в одному файлі, імпорт не потрібен
from custom_open_module import CustomOpen
class TestCustomOpen(unittest.TestCase):
    def setUp(self):
        """Скидаємо лічильник відкриттів перед кожним тестом для ізоляції."""
        CustomOpen.execution_counter = 0
    def test_successful_open_and_write(self):
        """1. Тест успішного відкриття, запису та закриття файлу (без помилок)"""
        m_open = mock_open()
        # Підміняємо вбудований open на mock-об'єкт
        with patch('builtins.open', m_open):
            with CustomOpen("test.txt", "w") as file:
                file.write("hello")
        # Перевіряємо, чи викликався вбудований open з правильними параметрами
        m_open.assert_called_once_with("test.txt", "w", encoding="utf-8")
        # Перевіряємо, чи записалися дані
        m_open().write.assert_called_once_with("hello")
        # Перевіряємо, чи файл був гарантовано закритий
        m_open().close.assert_called_once()
        # Перевіряємо роботу нашого лічильника
        self.assertEqual(CustomOpen.execution_counter, 1)
    def test_exception_inside_with_block(self):
        """2. Тест ситуації, коли помилка виникає ВСЕРЕДИНІ блоку with.
        Файл має закритися, а помилка — прокинутися далі."""
        m_open = mock_open()
        with patch('builtins.open', m_open):
            # Перевіряємо, чи прокинеться ZeroDivisionError назовні
            with self.assertRaises(ZeroDivisionError):
                with CustomOpen("test.txt", "r") as file:
                    result = 10 / 0  # Штучна помилка всередині блоку
        # Головна перевірка: файл ВСЕ ОДНО має бути закритий методом __exit__
        m_open().close.assert_called_once()
        self.assertEqual(CustomOpen.execution_counter, 1)
    def test_file_not_found_exception(self):
        """3. Тест ситуації, коли сама функція open генерує помилку (наприклад, файл не знайдено)"""
        # Налаштовуємо вбудований open так, щоб він одразу викидав FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError("Файл не знайдено")):
            with self.assertRaises(FileNotFoundError):
                with CustomOpen("missing.txt", "r") as file:
                    file.read()
        # Оскільки open зламався, лічильник все одно збільшився під час входу,
        # але метод __exit__ не повинен ламатися через відсутність об'єкта файлу.
        self.assertEqual(CustomOpen.execution_counter, 1)
    def test_execution_counter_multiple_opens(self):
        """4. Тест послідовного збільшення глобального лічильника відкриттів"""
        m_open = mock_open()
        with patch('builtins.open', m_open):
            with CustomOpen("file1.txt", "r"):
                pass
            with CustomOpen("file2.txt", "w"):
                pass
        # Перевіряємо, що лічильник зафіксував рівно 2 відкриття
        self.assertEqual(CustomOpen.execution_counter, 2)
if __name__ == "__main__":
    unittest.main()

# Task 3 (Optional)
# Фікстури Pytest із менеджером контексту
# Створіть просту функцію, яка виконує довільну логіку з текстовими даними, отриманими з об’єкта
# файлу, переданого цій функції (def test(file_obj)).
# Створіть тестовий випадок для цієї функції, використовуючи бібліотеку pytest (Повна
# документація pytest).
# Створіть фіксацію pytest, яка використовує вашу реалізацію менеджера контексту для повернення
# об'єкта файлу, який можна використовувати всередині вашої функції.
import os
import pytest
from custom_open_module import CustomOpen  # Імпортуємо ваш менеджер контексту
# ==========================================
# 1. ФУНКЦІЯ, ЯКУ МИ ТЕСТУЄМО
# ==========================================
def process_text_file(file_obj):
    """
    Функція зчитує дані з файлового об'єкта, видаляє зайві пробіли,
    переводить текст у верхній регістр (UPPERCASE) та рахує кількість слів.
    """
    content = file_obj.read().strip()
    if not content:
        return "", 0
    processed_text = content.upper()
    word_count = len(processed_text.split())
    return processed_text, word_count
# ==========================================
# 2. ФІКСТУРА PYTEST
# ==========================================
@pytest.fixture
def temp_file_fixture():
    """
    Фікстура створює тимчасовий файл за допомогою CustomOpen,
    передає файловий об'єкт у тест, а після завершення тесту
    гарантовано видаляє цей файл із диска.
    """
    filename = "temp_pytest_demo.txt"
    # Створюємо файл із початковими даними для тесту
    with CustomOpen(filename, "w") as f:
        f.write("hello world from pytest fixture")
    # Відкриваємо файл для читання за допомогою нашого менеджера контексту
    manager = CustomOpen(filename, "r")
    file_obj = manager.__enter__()
    try:
        # Передаємо об'єкт файлу безпосередньо в тестову функцію
        yield file_obj
    finally:
        # Код після yield виконується після завершення тесту (Teardown)
        # Спочатку закриваємо файл через __exit__ нашого менеджера
        manager.__exit__(None, None, None)
        # Видаляємо тимчасовий файл із диска, щоб не залишати сміття
        if os.path.exists(filename):
            os.remove(filename)
# ==========================================
# 3. ТЕСТОВИЙ ВИПАДОК (TEST CASE)
# ==========================================
def test_process_text_file(temp_file_fixture):
    """
    Тест приймає фікстуру 'temp_file_fixture' як аргумент.
    Pytest автоматично підставить туди значення, яке повернув yield.
    """
    # Викликаємо нашу функцію, передаючи їй отриманий файловий об'єкт
    text, count = process_text_file(temp_file_fixture)
    # Перевіряємо логіку роботи функції
    assert text == "HELLO WORLD FROM PYTEST FIXTURE"
    assert count == 5
# pip install pytest
# pytest test_pytest_context.py -v

# Task 4
#