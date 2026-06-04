# Task 1
# Створіть метод класу з назвою `validate`, який повинен викликатися з методу `__init__` для
# перевірки параметра email, переданого в конструктор. Логіка всередині методу `validate` може
# полягати у перевірці того, чи є переданий параметр email дійсним рядком електронної адреси.
# Перевірка електронної адреси:
# Valid email address format #
# Email address
# pip install pdfkit
import re
class User:
    # Базовий регулярний вираз для перевірки загального формату email (local-part@domain.tld)
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    def __init__(self, username: str, email: str):
        # Викликаємо метод класу для валідації до того, як зберегти атрибут
        User.validate(email)
        self.username = username
        self.email = email
    @classmethod
    def validate(cls, email: str):
        """Метод класу для перевірки коректності формату email."""
        if not isinstance(email, str):
            raise ValueError("Email повинен бути рядком (str).")
        # re.fullmatch перевіряє весь рядок від початку до кінця
        if not re.fullmatch(cls.EMAIL_REGEX, email):
            raise ValueError(f"Некоректний формат електронної адреси: '{email}'")
        return True
# ==========================================
# Демонстрація роботи програми:
# ==========================================
# 1. Спроба створити користувача з коректним email
try:
    user1 = User("ivan_tech", "ivan.doe@example.com")
    print(f"Користувача створено успішно! Його email: {user1.email}")
except ValueError as e:
    print(f"Помилка: {e}")
# 2. Спроба створити користувача з помилкою у форматі (немає крапки в домені)
try:
    user2 = User("olga_qa", "olga@invalid_domain")
except ValueError as e:
    print(f"Перехоплено очікувану помилку валідації: {e}")
# 3. Виклик методу класу без створення об'єкта
print(f"Чи валідний 'test@mail.com'? -> {User.validate('test@mail.com')}")

# Task 2
# Реалізуйте 2 класи: перший — Boss, другий — Worker.
# Клас Worker має властивість «boss», значення якої має бути екземпляром класу Boss.
# Ви можете перепризначити це значення, але перед цим слід перевірити, чи є нове значення
# екземпляром класу Boss. Кожен екземпляр класу Boss має список своїх підлеглих. Вам потрібно
# реалізувати метод, який дозволить додавати підлеглих до екземпляра класу Boss. Не дозволяється
# додавати екземпляри класу Boss до списку працівників безпосередньо через доступ до атрибуту,
# замість цього використовуйте геттери та сеттери!
# Ви можете рефакторувати існуючий код.
# id_ - це просто випадкове унікальне ціле число
# class Boss:
#     def __init__(self, id_: int, name: str, company: str):
#         self.id = id_
#         self.name = name
#         self.company = company
#         self.workers = []
# class Worker:
#     def __init__(self, id_: int, name: str, company: str, boss: Boss):
#         self.id = id_
#         self.name = name
#         self.company = company
#         self.boss = boss
class Boss:
    def __init__(self, id_: int, name: str, company: str):
        self.id = id_
        self.name = name
        self.company = company
        self._workers = []  # Захищений список підлеглих
    @property
    def workers(self) -> list:
        """Геттер для отримання списку працівників."""
        return self._workers
    def add_worker(self, worker):
        """Метод для додавання працівника до списку боса."""
        if not isinstance(worker, Worker):
            raise ValueError("Додати можна лише об'єкт класу Worker.")
        if worker not in self._workers:
            self._workers.append(worker)
            # Синхронізуємо зв'язок: оновлюємо боса всередині самого працівника,
            # використовуючи його сеттер (уникаючи зациклення)
            if worker._boss != self:
                worker.boss = self
    def remove_worker(self, worker):
        """Внутрішній метод для видалення працівника зі списку боса."""
        if worker in self._workers:
            self._workers.remove(worker)
    def __str__(self):
        return f"Boss: {self.name} (ID: {self.id}, Підлеглих: {len(self._workers)})"
    def __repr__(self):
        return f"Boss(id_={self.id}, name='{self.name}', company='{self.company}')"
class Worker:
    def __init__(self, id_: int, name: str, company: str, boss: Boss):
        self.id = id_
        self.name = name
        self.company = company
        self._boss = None  # Ініціалізуємо внутрішній атрибут
        # Використовуємо сеттер для перевірки та встановлення боса при створенні
        self.boss = boss
    @property
    def boss(self) -> Boss:
        """Геттер для отримання поточного боса працівника."""
        return self._boss
    @boss.setter
    def boss(self, new_boss: Boss):
        """Сеттер для зміни боса з обов'язковою перевіркою типу та синхронізацією."""
        if not isinstance(new_boss, Boss):
            raise ValueError("Нове значення 'boss' має бути екземпляром класу Boss.")
        # Якщо бос змінюється, видаляємо працівника зі списку старого боса
        if self._boss is not None and self._boss != new_boss:
            self._boss.remove_worker(self)
        # Встановлюємо нового боса
        self._boss = new_boss
        # Автоматично додаємо цього працівника до списку нового боса
        if self not in new_boss.workers:
            new_boss.add_worker(self)
    def __str__(self):
        boss_name = self._boss.name if self._boss else "Немає"
        return f"Worker: {self.name} (ID: {self.id}, Бос: {boss_name})"
    def __repr__(self):
        return f"Worker(id_={self.id}, name='{self.name}', company='{self.company}')"
# ==========================================
# Демонстрація роботи програми:
# ==========================================
# 1. Створюємо двох босів
boss_a = Boss(1, "Олександр", "TechCorp")
boss_b = Boss(2, "Дмитро", "InnovateLtd")
# 2. Створюємо працівника і відразу призначаємо йома першого боса
worker1 = Worker(101, "Анна", "TechCorp", boss_a)
# Перевіряємо взаємний зв'язок
print("--- Після створення worker1 ---")
print(worker1)  # Бос: Олександр
print(f"Підлеглі boss_a: {[w.name for w in boss_a.workers]}")  # ['Анна']
# 3. Додаємо другого працівника безпосередньо через метод боса
worker2 = Worker(102, "Сергій", "TechCorp", boss_a)
print(f"Підлеглі boss_a після додавання Сергія: {[w.name for w in boss_a.workers]}")
# ['Анна', 'Сергій']
# 4. Перепризначаємо боса для Анни через сеттер
worker1.boss = boss_b
print("\n--- Після зміни боса для worker1 ---")
print(worker1)  # Тепер бос: Дмитро
print(f"Підлеглі старого boss_a: {[w.name for w in boss_a.workers]}")  # Залишився тільки ['Сергій']
print(f"Підлеглі нового boss_b: {[w.name for w in boss_b.workers]}")  # З'явилася ['Анна']
# 5. Перевірка валідації (спроба призначити неправильний тип)
print("\n--- Перевірка помилок валідації ---")
try:
    worker1.boss = "Просто рядок замість об'єкта Boss"
except ValueError as e:
    print(f"Перехоплено помилку: {e}")

# Task 3
# Напишіть клас TypeDecorators, який містить кілька методів для перетворення результатів
# функцій у вказаний тип (якщо це можливо):
# методи:
# to_int
# to_str
# to_bool
# to_float
# Не забудьте використати @wraps
# class TypeDecorators:
#     pass
# @TypeDecorators.to_int
# def do_nothing(string: str):
#     return string
# @TypeDecorators.to_bool
# def do_something(string: str):
#     return string
# assert do_nothing(“25”) == 25
# assert do_something(“True”) is True
from functools import wraps
class TypeDecorators:
    @staticmethod
    def to_int(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                return int(result)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Неможливо перетворити '{result}' у тип int: {e}")
        return wrapper
    @staticmethod
    def to_str(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return str(result)
        return wrapper
    @staticmethod
    def to_bool(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Додатково обробляємо текстові значення для логічного типу
            if isinstance(result, str):
                if result.strip().lower() in ['true', '1', 'yes', 'y']:
                    return True
                if result.strip().lower() in ['false', '0', 'no', 'n', '']:
                    return False
            return bool(result)
        return wrapper
    @staticmethod
    def to_float(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            try:
                return float(result)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Неможливо перетворити '{result}' у тип float: {e}")
        return wrapper
# ==========================================
# Перевірка роботи коду з вашої умови:
# ==========================================
@TypeDecorators.to_int
def do_nothing(string: str):
    return string
@TypeDecorators.to_bool
def do_something(string: str):
    return string
# Перевірки через assert
assert do_nothing("25") == 25
assert do_something("True") is True
print("Всі перевірки (assert) пройдено успішно!")
