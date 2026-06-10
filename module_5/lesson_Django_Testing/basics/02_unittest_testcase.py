"""
02 · UNITTEST.TESTCASE

Запуск:
    python -m pytest 02_unittest_testcase.py -v
    # або
    python -m unittest 02_unittest_testcase -v

unittest.TestCase — базовий клас для організованих тестів.
Переваги:
  - setUp() / tearDown() — код що виконується до/після кожного тесту
  - setUpClass() / tearDownClass() — один раз на весь клас
  - Багато методів assert* з кращими повідомленнями про помилки

Django використовує django.test.TestCase — підклас unittest.TestCase.
"""

import unittest


# ─────────────────────────────────────────────────────────────────────────────
# Клас що тестуємо (імітує модель або сервіс)
# ─────────────────────────────────────────────────────────────────────────────

class BankAccount:
    """Проста модель банківського рахунку для демонстрації."""

    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Сума поповнення має бути > 0")
        self.balance += amount
        self.transactions.append(('deposit', amount))

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Сума зняття має бути > 0")
        if amount > self.balance:
            raise ValueError("Недостатньо коштів")
        self.balance -= amount
        self.transactions.append(('withdraw', amount))

    def __str__(self):
        return f"BankAccount({self.owner}, {self.balance} грн)"


# ─────────────────────────────────────────────────────────────────────────────
# Тестовий клас
# ─────────────────────────────────────────────────────────────────────────────

class BankAccountTest(unittest.TestCase):
    """
    Кожен метод test_* — окремий тест.
    setUp() виконується ПЕРЕД кожним тестом.
    tearDown() виконується ПІСЛЯ кожного тесту.
       Це означає, що кожен тест отримує новий чистий рахунок:
        owner = "Alice"
        balance = 100
        transactions = []
    """

    def setUp(self):
        """
         Arrange для більшості тестів.
        Готуємо стан перед кожним тестом.
        Після кожного тесту Python створює новий екземпляр класу BankAccountTest,
        тому self.account завжди свіжий (balance=100).
        """
        self.account = BankAccount(owner='Alice', balance=100)

    def tearDown(self):
        """
        Очищення після тесту.
        Тут можна закрити файл, з'єднання з БД, тощо.
        Для простих unit-тестів часто не потрібний.
        """
        pass  # Нічого не потрібно очищати

    # ── Базові тести ──────────────────────────────────────────────────────────

    def test_initial_balance(self):
        """
        Тест: початковий баланс рахунку.

        Перевіряємо, що після створення рахунку баланс дорівнює 100.
        """

        # Arrange
        # Рахунок уже створено в setUp():
        # self.account = BankAccount(owner="Alice", balance=100)

        # Act
        actual_balance = self.account.balance

        # Assert
        self.assertEqual(actual_balance, 100)

    def test_owner_name(self):
        """
        Тест: ім'я власника рахунку.

        Перевіряємо, що owner правильно зберігається в об'єкті.
        """

        # Arrange
        # Рахунок уже створено в setUp().

        # Act
        actual_owner = self.account.owner

        # Assert
        self.assertEqual(actual_owner, "Alice")

    def test_str_representation(self):
        """
        Тест: текстове представлення рахунку.

        Перевіряємо, що метод __str__() повертає очікуваний рядок.
        """

        # Arrange
        # Рахунок уже створено в setUp().

        # Act
        account_as_text = str(self.account)

        # Assert
        self.assertEqual(account_as_text, "BankAccount(Alice, 100 грн)")

    def test_deposit_increases_balance(self):
        """
        Тест: deposit() збільшує баланс.

        Початковий баланс: 100
        Поповнення: 50
        Очікуваний баланс: 150
        """

        # Arrange
        amount = 50

        # Act
        self.account.deposit(amount)

        # Assert
        self.assertEqual(self.account.balance, 150)

    def test_deposit_records_transaction(self):
        """
        Тест: deposit() записує транзакцію.

        Після поповнення на 50 у списку transactions
        має з'явитися запис:
            ("deposit", 50)
        """

        # Arrange
        amount = 50

        # Act
        self.account.deposit(amount)

        # Assert
        self.assertIn(("deposit", 50), self.account.transactions)

    def test_deposit_zero_raises_error(self):
        """
        Тест: deposit(0) викликає помилку.

        Поповнення на 0 заборонене.
        Очікуємо ValueError.
        """

        # Arrange
        amount = 0

        # Act + Assert
        with self.assertRaises(ValueError):
            self.account.deposit(amount)

    def test_deposit_negative_raises_error(self):
        """
        Тест: deposit(-10) викликає помилку.

        Від'ємна сума поповнення заборонена.
        Додатково перевіряємо текст помилки.
        """

        # Arrange
        amount = -10

        # Act + Assert
        with self.assertRaises(ValueError) as context:
            self.account.deposit(amount)

        # Assert
        self.assertIn("має бути > 0", str(context.exception))

    def test_withdraw_decreases_balance(self):
        """
        Тест: withdraw() зменшує баланс.

        Початковий баланс: 100
        Зняття: 30
        Очікуваний баланс: 70
        """

        # Arrange
        amount = 30

        # Act
        self.account.withdraw(amount)

        # Assert
        self.assertEqual(self.account.balance, 70)

    def test_withdraw_insufficient_funds(self):
        """
        Тест: не можна зняти більше, ніж є на рахунку.

        Початковий баланс: 100
        Спроба зняти: 200
        Очікуємо ValueError з текстом "Недостатньо коштів".
        """

        # Arrange
        amount = 200

        # Act + Assert
        with self.assertRaises(ValueError) as context:
            self.account.withdraw(amount)

        # Assert
        self.assertIn("Недостатньо коштів", str(context.exception))

    def test_withdraw_exact_balance(self):
        """
        Тест: можна зняти рівно весь баланс.

        Початковий баланс: 100
        Зняття: 100
        Очікуваний баланс: 0
        """

        # Arrange
        amount = 100

        # Act
        self.account.withdraw(amount)

        # Assert
        self.assertEqual(self.account.balance, 0)

    def test_multiple_transactions(self):
        """
        Тест: кілька транзакцій підряд.

        Початковий баланс: 100

        Операції:
            deposit(200)  -> 300
            withdraw(50)  -> 250
            withdraw(100) -> 150

        Очікуємо:
            balance = 150
            кількість транзакцій = 3
        """

        # Arrange
        deposit_amount = 200
        first_withdraw = 50
        second_withdraw = 100

        # Act
        self.account.deposit(deposit_amount)
        self.account.withdraw(first_withdraw)
        self.account.withdraw(second_withdraw)

        # Assert
        self.assertEqual(self.account.balance, 150)
        self.assertEqual(len(self.account.transactions), 3)

    def test_fresh_account_has_no_transactions(self):
        """
        Тест: новий рахунок не має транзакцій.

        Цей тест показує, що setUp() створює новий об'єкт
        перед кожним тестом.

        Навіть якщо інші тести додавали транзакції,
        тут transactions знову порожній.
        """

        # Arrange
        # Новий рахунок уже створено в setUp().

        # Act
        transactions_count = len(self.account.transactions)

        # Assert
        self.assertEqual(transactions_count, 0)


# ─────────────────────────────────────────────────────────────────────────────
# SETUPTESTCASE — один раз на клас (дорогі ресурси)
# ─────────────────────────────────────────────────────────────────────────────

class ExpensiveSetupTest(unittest.TestCase):
    """
    Тестовий клас для демонстрації setUpClass() і tearDownClass().

    setUpClass() виконується один раз перед усіма тестами класу.
    tearDownClass() виконується один раз після всіх тестів класу.

    Це корисно для дорогих операцій:
        - підключення до бази даних;
        - читання великого файлу;
        - створення великого набору даних.
    """

    @classmethod
    def setUpClass(cls):
        """
        Arrange для всього класу.

        Створюємо спільний список shared_data один раз,
        а не перед кожним тестом.
        """
        print("\n[setUpClass] Виконується один раз")
        cls.shared_data = list(range(1000))

    @classmethod
    def tearDownClass(cls):
        """
        Очищення після всіх тестів класу.

        Видаляємо посилання на shared_data.
        """
        print("\n[tearDownClass] Виконується один раз")
        cls.shared_data = None

    def test_data_length(self):
        """
        Тест: довжина shared_data.

        Перевіряємо, що список має 1000 елементів.
        """

        # Arrange
        # Дані створено один раз у setUpClass():
        # cls.shared_data = list(range(1000))

        # Act
        actual_length = len(self.shared_data)

        # Assert
        self.assertEqual(actual_length, 1000)

    def test_data_first_element(self):
        """
        Тест: перший елемент shared_data.

        list(range(1000)) створює список від 0 до 999.
        Перший елемент має бути 0.
        """

        # Arrange
        # Дані створено в setUpClass().

        # Act
        first_element = self.shared_data[0]

        # Assert
        self.assertEqual(first_element, 0)

    def test_data_last_element(self):
        """
        Тест: останній елемент shared_data.

        list(range(1000)) створює числа:
            0, 1, 2, ..., 999

        Тому останній елемент має бути 999.
        """

        # Arrange
        # Дані створено в setUpClass().

        # Act
        last_element = self.shared_data[-1]

        # Assert
        self.assertEqual(last_element, 999)


if __name__ == '__main__':
    unittest.main(verbosity=2)
