"""
03 · ASSERTIONS — Методи перевірки в unittest.TestCase

Запуск:
    python -m pytest 03_assertions.py -v

Чому не писати просто assert?

    assert a == b                     ← якщо провалиться: "AssertionError"
    self.assertEqual(a, b)            ← якщо провалиться: "1 != 2"

assertEqual дає набагато зрозуміліше повідомлення про помилку.

ДОВІДНИК:
  assertEqual(a, b)         a == b
  assertNotEqual(a, b)      a != b
  assertTrue(x)             bool(x) is True
  assertFalse(x)            bool(x) is False
  assertIsNone(x)           x is None
  assertIsNotNone(x)        x is not None
  assertIn(a, b)            a in b
  assertNotIn(a, b)         a not in b
  assertIs(a, b)            a is b  (тотожність, не рівність)
  assertIsNot(a, b)         a is not b
  assertIsInstance(a, T)    isinstance(a, T)
  assertRaises(Exc, fn, .)  fn(.) кидає Exc
  assertAlmostEqual(a, b)   abs(a-b) <= 1e-7
  assertGreater(a, b)       a > b
  assertLess(a, b)          a < b
  assertGreaterEqual(a, b)  a >= b
  assertLessEqual(a, b)     a <= b
  assertListEqual(a, b)     lists equal (кращий вивід)
  assertDictEqual(a, b)     dicts equal (кращий вивід)
  assertSetEqual(a, b)      sets equal
  assertMultiLineEqual(a,b) strings equal (diff по рядках)
"""

import unittest
import math


class AssertionDemoTest(unittest.TestCase):
    """
    Клас демонструє різні assert-методи.

    Кожен метод test_* — окремий тест.
    Тест показує конкретний тип перевірки:
        - рівність;
        - нерівність;
        - True / False;
        - None / not None;
        - входження в колекцію;
        - тип даних;
        - числове порівняння;
        - приблизну рівність;
        - винятки;
        - списки, словники, множини;
        - багаторядкові рядки.
    """

    # ── Рівність ──────────────────────────────────────────────────────────────

    def test_assertEqual(self):
        """
        Тест: assertEqual(a, b)

        Для чого:
            Перевіряє, що два значення рівні.

        Синтаксис:
            self.assertEqual(actual, expected)

        Якщо значення різні, тест впаде і покаже зрозуміле повідомлення,
        наприклад:
            AssertionError: 3 != 4
        """

        # Arrange
        first_result = 2 + 2
        second_result = "hello".upper()
        third_result = [1, 2, 3]

        # Act
        expected_number = 4
        expected_text = "HELLO"
        expected_list = [1, 2, 3]

        # Assert
        self.assertEqual(first_result, expected_number)
        self.assertEqual(second_result, expected_text)
        self.assertEqual(third_result, expected_list)

    def test_assertNotEqual(self):
        """
        Тест: assertNotEqual(a, b)

        Для чого:
            Перевіряє, що два значення НЕ рівні.

        Приклад:
            2 + 2 не дорівнює 5.
            "hello" не дорівнює "world".
        """

        # Arrange
        number_result = 2 + 2
        text_result = "hello"

        # Act
        wrong_number = 5
        other_text = "world"

        # Assert
        self.assertNotEqual(number_result, wrong_number)
        self.assertNotEqual(text_result, other_text)

    # ── Булеві значення ───────────────────────────────────────────────────────

    def test_assertTrue(self):
        """
        Тест: assertTrue(x)

        Для чого:
            Перевіряє, що значення є truthy.

        Truthy — це значення, яке Python сприймає як True.

        Приклади truthy:
            True
            1
            непорожній список
            непорожній рядок
            непорожній словник
        """

        # Arrange
        boolean_value = True
        number_value = 1
        list_value = [1, 2]

        # Act
        first_check = boolean_value
        second_check = number_value
        third_check = list_value

        # Assert
        self.assertTrue(first_check)
        self.assertTrue(second_check)
        self.assertTrue(third_check)

    def test_assertFalse(self):
        """
        Тест: assertFalse(x)

        Для чого:
            Перевіряє, що значення є falsy.

        Falsy — це значення, яке Python сприймає як False.

        Приклади falsy:
            False
            0
            порожній список []
            порожній рядок ""
            None
        """

        # Arrange
        boolean_value = False
        number_value = 0
        list_value = []
        string_value = ""

        # Act
        first_check = boolean_value
        second_check = number_value
        third_check = list_value
        fourth_check = string_value

        # Assert
        self.assertFalse(first_check)
        self.assertFalse(second_check)
        self.assertFalse(third_check)
        self.assertFalse(fourth_check)

    # ── None ─────────────────────────────────────────────────────────────────

    def test_assertIsNone(self):
        """
        Тест: assertIsNone(x)

        Для чого:
            Перевіряє, що значення є саме None.

        None означає:
            - відсутність значення;
            - функція нічого не повернула;
            - результат ще не визначений.
        """

        # Arrange
        result = None

        def returns_none():
            """
            Функція без return автоматично повертає None.
            """
            pass

        # Act
        direct_none_result = result
        function_result = returns_none()

        # Assert
        self.assertIsNone(direct_none_result)
        self.assertIsNone(function_result)

    def test_assertIsNotNone(self):
        """
        Тест: assertIsNotNone(x)

        Для чого:
            Перевіряє, що значення НЕ є None.

        Це корисно, коли ми хочемо переконатися,
        що функція або об'єкт реально щось повернули.
        """

        # Arrange
        result = 42

        # Act
        actual_result = result

        # Assert
        self.assertIsNotNone(actual_result)

    # ── Приналежність ─────────────────────────────────────────────────────────

    def test_assertIn(self):
        """
        Тест: assertIn(a, b)

        Для чого:
            Перевіряє, що елемент a міститься всередині b.

        Може працювати з:
            - списками;
            - рядками;
            - словниками;
            - множинами;
            - іншими контейнерами.
        """

        # Arrange
        fruits = ["apple", "banana", "cherry"]
        word = "cat"
        user = {"name": "Alice"}

        # Act
        fruit_to_find = "banana"
        letter_to_find = "a"
        key_to_find = "name"

        # Assert
        self.assertIn(fruit_to_find, fruits)
        self.assertIn(letter_to_find, word)
        self.assertIn(key_to_find, user)

    def test_assertNotIn(self):
        """
        Тест: assertNotIn(a, b)

        Для чого:
            Перевіряє, що елемент a НЕ міститься всередині b.

        У цьому тесті ми перевіряємо,
        що 'grape' відсутній у списку fruits.
        """

        # Arrange
        fruits = ["apple", "banana"]

        # Act
        fruit_to_check = "grape"

        # Assert
        self.assertNotIn(fruit_to_check, fruits)

    # ── Тип даних ─────────────────────────────────────────────────────────────

    def test_assertIsInstance(self):
        """
        Тест: assertIsInstance(a, T)

        Для чого:
            Перевіряє, що об'єкт a є екземпляром типу T.

        Це аналог:
            isinstance(a, T)

        Важливий момент:
            bool у Python є підкласом int.

        Тому:
            isinstance(True, int) == True
        """

        # Arrange
        integer_value = 42
        float_value = 3.14
        string_value = "hello"
        list_value = [1, 2]
        boolean_value = True

        # Act + Assert
        self.assertIsInstance(integer_value, int)
        self.assertIsInstance(float_value, float)
        self.assertIsInstance(string_value, str)
        self.assertIsInstance(list_value, list)
        self.assertIsInstance(boolean_value, bool)

        # bool є підкласом int, тому ця перевірка також проходить
        self.assertIsInstance(boolean_value, int)

    def test_assertIsInstance_with_tuple(self):
        """
        Тест: assertIsInstance(a, (T1, T2, ...))

        Для чого:
            Перевіряє, що значення належить хоча б до одного з типів.

        Наприклад:
            value може бути або int, або float.
        """

        # Arrange
        value = 42
        allowed_types = (int, float)

        # Act
        actual_value = value

        # Assert
        self.assertIsInstance(actual_value, allowed_types)

    # ── Порівняння чисел ──────────────────────────────────────────────────────

    def test_assertGreater(self):
        """
        Тест: assertGreater(a, b)

        Для чого:
            Перевіряє, що a більше за b.

        Тобто:
            a > b
        """

        # Arrange
        first_value = 5
        second_value = 3

        float_value = 0.1
        zero_value = 0.0

        # Act + Assert
        self.assertGreater(first_value, second_value)
        self.assertGreater(float_value, zero_value)

    def test_assertLess(self):
        """
        Тест: assertLess(a, b)

        Для чого:
            Перевіряє, що a менше за b.

        Тобто:
            a < b
        """

        # Arrange
        smaller_value = 3
        bigger_value = 5

        # Act + Assert
        self.assertLess(smaller_value, bigger_value)

    def test_assertGreaterEqual(self):
        """
        Тест: assertGreaterEqual(a, b)

        Для чого:
            Перевіряє, що a більше або дорівнює b.

        Тобто:
            a >= b

        Цей метод проходить у двох випадках:
            - коли числа рівні;
            - коли перше число більше.
        """

        # Arrange
        equal_left = 5
        equal_right = 5

        bigger_value = 6
        smaller_value = 5

        # Act + Assert
        self.assertGreaterEqual(equal_left, equal_right)
        self.assertGreaterEqual(bigger_value, smaller_value)

    def test_assertLessEqual(self):
        """
        Тест: assertLessEqual(a, b)

        Для чого:
            Перевіряє, що a менше або дорівнює b.

        Тобто:
            a <= b

        Цей метод проходить у двох випадках:
            - коли числа рівні;
            - коли перше число менше.
        """

        # Arrange
        equal_left = 5
        equal_right = 5

        smaller_value = 4
        bigger_value = 5

        # Act + Assert
        self.assertLessEqual(equal_left, equal_right)
        self.assertLessEqual(smaller_value, bigger_value)

    # ── Числа з плаваючою точкою ──────────────────────────────────────────────

    def test_assertAlmostEqual(self):
        """
        Тест: assertAlmostEqual(a, b)

        Для чого:
            Перевіряє, що два числа майже рівні.

        Це потрібно для float-чисел.

        Чому?
            У Python 0.1 + 0.2 не дорівнює точно 0.3
            через особливості зберігання чисел з плаваючою точкою.

        Приклад:
            0.1 + 0.2 дає приблизно:
                0.30000000000000004

        Тому для float часто не можна писати:
            self.assertEqual(0.1 + 0.2, 0.3)

        Краще писати:
            self.assertAlmostEqual(0.1 + 0.2, 0.3, places=10)
        """

        # Arrange
        first_float_result = 0.1 + 0.2
        expected_float_result = 0.3

        second_float_result = math.sqrt(2) ** 2
        expected_second_result = 2.0

        # Act + Assert
        # Спочатку показуємо, що точна рівність не працює
        self.assertNotEqual(first_float_result, expected_float_result)

        # Потім правильно порівнюємо з точністю до 10 знаків
        self.assertAlmostEqual(first_float_result, expected_float_result, places=10)
        self.assertAlmostEqual(second_float_result, expected_second_result, places=10)

    def test_assertAlmostEqual_custom_delta(self):
        """
        Тест: assertAlmostEqual(a, b, delta=...)

        Для чого:
            Перевіряє, що різниця між a і b не перевищує delta.

        Тут:
            100.05 і 100.0 відрізняються на 0.05.

        delta = 0.1

        Оскільки:
            0.05 <= 0.1

        тест проходить.
        """

        # Arrange
        actual_value = 100.05
        expected_value = 100.0
        allowed_difference = 0.1

        # Act + Assert
        self.assertAlmostEqual(
            actual_value,
            expected_value,
            delta=allowed_difference,
        )

    # ── Винятки ───────────────────────────────────────────────────────────────

    def test_assertRaises_context_manager(self):
        """
        Тест: assertRaises як context manager.

        Для чого:
            Перевіряє, що певний код викликає очікувану помилку.

        У цьому прикладі:
            1 / 0

        викликає:
            ZeroDivisionError

        Це рекомендований спосіб перевіряти винятки.
        """

        # Arrange
        numerator = 1
        denominator = 0

        # Act + Assert
        with self.assertRaises(ZeroDivisionError):
            _ = numerator / denominator

    def test_assertRaises_with_message(self):
        """
        Тест: assertRaises з перевіркою тексту помилки.

        Для чого:
            Іноді важливо перевірити не тільки тип помилки,
            а й повідомлення всередині цієї помилки.

        У цьому прикладі:
            int("not a number")

        не може перетворити текст у число,
        тому виникає ValueError.
        """

        # Arrange
        invalid_number_text = "not a number"

        # Act + Assert
        with self.assertRaises(ValueError) as ctx:
            int(invalid_number_text)

        # Assert
        # ctx.exception — це об'єкт помилки
        error_message = str(ctx.exception)

        self.assertIn("invalid literal", error_message)

    def test_assertRaises_callable(self):
        """
        Тест: assertRaises у callable-формі.

        Для чого:
            Це альтернативний синтаксис перевірки винятків.

        Синтаксис:
            self.assertRaises(ExceptionType, function, arg1, arg2, ...)

        У цьому прикладі:
            int([1, 2, 3])

        викликає TypeError,
        бо int() не може перетворити список у число.

        Цей стиль працює,
        але context manager зазвичай читається краще.
        """

        # Arrange
        invalid_value = [1, 2, 3]

        # Act + Assert
        self.assertRaises(TypeError, int, invalid_value)

    # ── Колекції ──────────────────────────────────────────────────────────────

    def test_assertListEqual(self):
        """
        Тест: assertListEqual(a, b)

        Для чого:
            Перевіряє, що два списки однакові.

        Важливо:
            Для списків порядок має значення.

        Тобто:
            [1, 2, 3] == [1, 2, 3]  → True
            [1, 2, 3] == [3, 2, 1]  → False

        assertListEqual дає кращий diff,
        якщо списки відрізняються.
        """

        # Arrange
        actual_list = [1, 2, 3]
        expected_list = [1, 2, 3]

        # Act + Assert
        self.assertListEqual(actual_list, expected_list)

    def test_assertDictEqual(self):
        """
        Тест: assertDictEqual(a, b)

        Для чого:
            Перевіряє, що два словники однакові.

        Важливо:
            У словниках порядок ключів не має значення.

        Тобто:
            {'name': 'Alice', 'age': 30}

        і:

            {'age': 30, 'name': 'Alice'}

        вважаються однаковими словниками.
        """

        # Arrange
        expected = {"name": "Alice", "age": 30}
        actual = {"age": 30, "name": "Alice"}

        # Act + Assert
        self.assertDictEqual(expected, actual)

    def test_assertSetEqual(self):
        """
        Тест: assertSetEqual(a, b)

        Для чого:
            Перевіряє, що дві множини однакові.

        Важливо:
            У множинах порядок не має значення.

        Тобто:
            {1, 2, 3}

        і:

            {3, 1, 2}

        є однаковими множинами.
        """

        # Arrange
        expected_set = {1, 2, 3}
        actual_set = {3, 1, 2}

        # Act + Assert
        self.assertSetEqual(expected_set, actual_set)

    # ── Рядки ────────────────────────────────────────────────────────────────

    def test_assertIn_substring(self):
        """
        Тест: assertIn для підрядка.

        Для чого:
            Перевіряє, що один текст міститься всередині іншого тексту.

        Це часто використовують для перевірки:
            - повідомлень про помилки;
            - логів;
            - HTML-відповідей;
            - текстових повідомлень API.
        """

        # Arrange
        error_message = "ValueError: Invalid priority value 5"

        # Act
        first_expected_part = "priority"
        second_expected_part = "Invalid"

        # Assert
        self.assertIn(first_expected_part, error_message)
        self.assertIn(second_expected_part, error_message)

    def test_assertMultiLineEqual(self):
        """
        Тест: assertMultiLineEqual(a, b)

        Для чого:
            Перевіряє, що два багаторядкові рядки однакові.

        Перевага:
            Якщо рядки відрізняються,
            unittest покаже різницю по рядках.

        Це зручно для перевірки:
            - шаблонів;
            - великих текстів;
            - HTML;
            - Markdown;
            - конфігураційних файлів.
        """

        # Arrange
        text1 = "Hello\nWorld\n"
        text2 = "Hello\nWorld\n"

        # Act
        actual_text = text1
        expected_text = text2

        # Assert
        self.assertMultiLineEqual(actual_text, expected_text)

if __name__ == '__main__':
    unittest.main(verbosity=2)
