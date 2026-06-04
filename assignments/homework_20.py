# Task 1
# Оберіть варіант вирішення одного із завдань цього модуля. Розробіть тести для цього рішення
# та напишіть їх, використовуючи бібліотеку unittest.
import unittest
# --- Наше рішення, яке ми тестуємо ---
def in_range(start, end, step=1):
    if step == 0:
        raise ValueError("in_range() step argument must not be zero")
    current = start
    if step > 0:
        while current < end:
            yield current
            current += step
    else:  # Якщо крок від'ємний (step < 0)
        while current > end:
            yield current
            current += step
# --- Тестовий сценарій (Test Case) ---
class TestInRange(unittest.TestCase):
    def setUp(self):
        """Метод setUp запускається перед КОЖНИМ тестом."""
        # Готуємо тестові дані або повідомлення, якщо необхідно
        self.error_message = "in_range() step argument must not be zero"
    def test_positive_step(self):
        """Тест звичайного кроку вперед"""
        result = list(in_range(1, 5, 1))
        self.assertEqual(result, [1, 2, 3, 4])
    def test_large_step(self):
        """Тест кроку, який більший за одиницю"""
        result = list(in_range(2, 10, 2))
        self.assertEqual(result, [2, 4, 6, 8])
    def test_negative_step(self):
        """Тест зворотного відліку (від'ємний крок)"""
        result = list(in_range(5, 1, -1))
        self.assertEqual(result, [5, 4, 3, 2])
    def test_step_zero_raises_error(self):
        """Граничний випадок: тест на викидання помилки ValueError при step=0"""
        with self.assertRaises(ValueError) as context:
            list(in_range(1, 5, 0))
        # Додатково перевіряємо, чи правильний текст помилки повернувся
        self.assertEqual(str(context.exception), self.error_message)
    def test_empty_range(self):
        """Граничний випадок: старт вже більший за кінець при додатному кроці"""
        result = list(in_range(5, 1, 1))
        self.assertEqual(result, [])
# --- Запуск тестів ---
if __name__ == "__main__":
    unittest.main()

# Task 2
# Напишіть тести для програми «Phonebook», яку ви реалізували в модулі 1. Розробіть тести для
# цього рішення та напишіть їх, використовуючи бібліотеку unittest
import unittest
# ==========================================
# 1. ПРОГРАМА "PHONEBOOK" (ОБ'ЄКТ ТЕСТУВАННЯ)
# ==========================================
class Phonebook:
    def __init__(self):
        # Зберігаємо контакти у вигляді словника {Ім'я: Телефон}
        self.contacts = {}
    def add_contact(self, name, phone):
        if not name or not phone:
            raise ValueError("Ім'я та телефон не можуть бути порожніми")
        if name in self.contacts:
            return f"Контакт {name} вже існує."
        self.contacts[name] = phone
        return f"Контакт {name} успішно додано."
    def find_contact(self, name):
        return self.contacts.get(name, "Контакт не знайдено.")
    def delete_contact(self, name):
        if name in self.contacts:
            del self.contacts[name]
            return f"Контакт {name} видалено."
        return "Контакт не знайдено."
    def get_all_contacts(self):
        return self.contacts
# ==========================================
# 2. МОДУЛЬНІ ТЕСТИ (UNIT TESTS)
# ==========================================
class TestPhonebook(unittest.TestCase):
    def setUp(self):
        """Метод setUp запускається перед КОЖНИМ окремим тестом."""
        # Створюємо новий чистий об'єкт телефонної книги перед кожним тестом,
        # щоб тести були ізольованими та не впливали один на одного.
        self.phonebook = Phonebook()
    def test_add_contact_success(self):
        """Тест успішного додавання нового контакту"""
        message = self.phonebook.add_contact("Олексій", "+380501112233")
        # Перевіряємо повідомлення про успіх
        self.assertEqual(message, "Контакт Олексій успішно додано.")
        # Перевіряємо, чи з'явився запис у базі даних книги
        self.assertIn("Олексій", self.phonebook.get_all_contacts())
        self.assertEqual(self.phonebook.contacts["Олексій"], "+380501112233")
    def test_add_duplicate_contact(self):
        """Тест спроби додати контакт, який вже існує (дублікат)"""
        self.phonebook.add_contact("Марія", "+380674445566")
        # Намагаємося додати Марію знову
        message = self.phonebook.add_contact("Марія", "+380999999999")
        self.assertEqual(message, "Контакт Марія вже існує.")
        # Перевіряємо, що номер телефону НЕ змінився на новий
        self.assertEqual(self.phonebook.find_contact("Марія"), "+380674445566")
    def test_add_contact_invalid_data(self):
        """Граничний випадок: тест на викидання помилки ValueError при порожніх полях"""
        with self.assertRaises(ValueError):
            self.phonebook.add_contact("", "+380000000")
        with self.assertRaises(ValueError):
            self.phonebook.add_contact("Іван", "")
    def test_find_contact_existing(self):
        """Тест успішного пошуку існуючого контакту"""
        self.phonebook.add_contact("Влад", "+380637778899")
        result = self.phonebook.find_contact("Влад")
        self.assertEqual(result, "+380637778899")
    def test_find_contact_not_found(self):
        """Тест пошуку контакту, якого немає в телефонній книзі"""
        result = self.phonebook.find_contact("Олена")
        self.assertEqual(result, "Контакт не знайдено.")
    def test_delete_contact_success(self):
        """Тест успішного видалення контакту"""
        self.phonebook.add_contact("Дмитро", "+380931111111")
        message = self.phonebook.delete_contact("Дмитро")
        self.assertEqual(message, "Контакт Дмитро видалено.")
        self.assertNotIn("Дмитро", self.phonebook.get_all_contacts())
    def test_delete_contact_not_found(self):
        """Тест спроби видалити неіснуючий контакт"""
        message = self.phonebook.delete_contact("Петро")
        self.assertEqual(message, "Контакт не знайдено.")
if __name__ == "__main__":
    # Запуск усіх тестів
    unittest.main()