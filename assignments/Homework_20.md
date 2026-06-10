## Task 1: Тестування класу `Fraction` за допомогою `unittest`

Спочатку збережемо логіку класу `Fraction` у тестовому файлі (або уявимо, що вона імпортується), а нижче напишемо тестовий клас `TestFraction`, який перевіряє арифметику, порівняння та обробку помилок (наприклад, ділення на нуль).

Python

```
import unittest
import math

# --- Клас, який ми тестуємо (з Module 10, Task 3) ---
class Fraction:
    def __init__(self, numerator: int, denominator: int):
        if denominator == 0:
            raise ValueError("Знаменник не може дорівнювати нулю.")
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        self.numerator = numerator
        self.denominator = denominator
        self._reduce()

    def _reduce(self):
        gcd = math.gcd(self.numerator, self.denominator)
        self.numerator //= gcd
        self.denominator //= gcd

    def __add__(self, other):
        return Fraction(self.numerator * other.denominator + other.numerator * self.denominator, 
                        self.denominator * other.denominator)

    def __sub__(self, other):
        return Fraction(self.numerator * other.denominator - other.numerator * self.denominator, 
                        self.denominator * other.denominator)

    def __eq__(self, other):
        if not isinstance(other, Fraction):
            return False
        return self.numerator == other.numerator and self.denominator == other.denominator

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"


# --- Самі тести ---
class TestFraction(unittest.TestCase):
    
    def setUp(self):
        """Викликається перед кожним тестом. Створюємо базові дроби."""
        self.f1 = Fraction(1, 2)
        self.f2 = Fraction(1, 4)
        self.f3 = Fraction(2, 4)  # Після скорочення стане 1/2

    def test_initialization_and_reduction(self):
        """Перевірка створення дробу та його автоматичного скорочення."""
        self.assertEqual(self.f3.numerator, 1)
        self.assertEqual(self.f3.denominator, 2)

    def test_zero_denominator_raises_value_error(self):
        """Перевірка, що створення дробу з нульовим знаменником викликає помилку."""
        with self.assertRaises(ValueError):
            Fraction(5, 0)

    def test_addition(self):
        """Перевірка додавання дробів (1/2 + 1/4 = 3/4)."""
        result = self.f1 + self.f2
        expected = Fraction(3, 4)
        self.assertEqual(result, expected)

    def test_subtraction(self):
        """Перевірка віднімання дробів (1/2 - 1/4 = 1/4)."""
        result = self.f1 - self.f2
        expected = Fraction(1, 4)
        self.assertEqual(result, expected)

    def test_equality(self):
        """Перевірка логіки порівняння дробів."""
        self.assertTrue(self.f1 == self.f3)
        self.assertFalse(self.f1 == self.f2)

    def test_string_representation(self):
        """Перевірка магічного методу __str__."""
        self.assertEqual(str(self.f1), "1/2")

if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)
```

## Task 2: Тестування додатку `Phonebook`

Для тестування телефонної книги нам потрібно перевірити базовий CRUD (Create, Read, Update, Delete). Оскільки реальна програма з модуля 1 зазвичай працює з JSON-файлом, ми реалізуємо клас `Phonebook` так, щоб під час тестів він працював у пам'яті (чи з тимчасовим списком), аби тести не затирали твої справжні контакти.

Python

```
import unittest

# --- Модель додатку Phonebook ---
class Phonebook:
    def __init__(self):
        # Ініціалізуємо порожній список контактів для чистоти тестів
        self.contacts = []

    def add_contact(self, first_name: str, last_name: str, phone: str) -> dict:
        """Додає новий контакт і повертає його."""
        if not first_name or not last_name or not phone:
            raise ValueError("Всі поля мають бути заповнені.")
            
        contact = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone
        }
        self.contacts.append(contact)
        return contact

    def find_by_name(self, name: str) -> list:
        """Шукає контакти за ім'ям або прізвищем."""
        return [c for c in self.contacts if name.lower() in c["first_name"].lower() or name.lower() in c["last_name"].lower()]

    def delete_by_phone(self, phone: str) -> bool:
        """Видаляє контакт за номером телефону. Повертає True, якщо видалено."""
        for contact in self.contacts:
            if contact["phone"] == phone:
                self.contacts.remove(contact)
                return True
        return False


# --- Тести для Phonebook ---
class TestPhonebook(unittest.TestCase):

    def setUp(self):
        """Створюємо чистий екземпляр телефонної книги перед кожним тестом."""
        self.phonebook = Phonebook()
        # Додамо один базовий контакт для тестів пошуку та видалення
        self.phonebook.add_contact("John", "Doe", "+380501112233")

    def test_add_contact_success(self):
        """Перевірка успішного додавання контакту."""
        initial_count = len(self.phonebook.contacts)
        new_contact = self.phonebook.add_contact("Jane", "Smith", "+380674445566")
        
        self.assertEqual(len(self.phonebook.contacts), initial_count + 1)
        self.assertIn(new_contact, self.phonebook.contacts)

    def test_add_contact_missing_fields_raises_error(self):
        """Перевірка, що додавання контакту з порожніми полями викликає ValueError."""
        with self.assertRaises(ValueError):
            self.phonebook.add_contact("", "Doe", "+38000")

    def test_find_by_name_found(self):
        """Перевірка успішного пошуку контакту за ім'ям."""
        results = self.phonebook.find_by_name("John")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["last_name"], "Doe")

    def test_find_by_name_not_found(self):
        """Перевірка пошуку, якщо такого імені немає в книзі."""
        results = self.phonebook.find_by_name("Alex")
        self.assertEqual(len(results), 0)

    def test_delete_contact_success(self):
        """Перевірка успішного видалення контакту за номером телефону."""
        # Перевіряємо, що видалення повернуло True
        self.assertTrue(self.phonebook.delete_by_phone("+380501112233"))
        # Перевіряємо, що список контактів тепер порожній
        self.assertEqual(len(self.phonebook.contacts), 0)

    def test_delete_contact_not_exists(self):
        """Перевірка видалення номера, якого не існує."""
        self.assertFalse(self.phonebook.delete_by_phone("+000000000000"))


if __name__ == "__main__":
    # Запуск усіх тестів у файлі
    unittest.main(argv=[''], exit=False)
```