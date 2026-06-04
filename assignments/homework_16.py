# Task 1
# Школа
# Створіть у Python структуру класів, що відображає учнів та вчителів у школі. Створіть базовий
# клас Person, клас Student та клас Teacher. Спробуйте визначити якомога більше методів та
# атрибутів, що належать до різних класів, і зверніть увагу на те, які з них є спільними, а
# які — ні. Наприклад, ім’я має бути атрибутом класу Person, тоді як зарплата має бути доступною
# лише для класу Teacher.
class Person:
    """Базовий клас для всіх людей у школі."""
    def __init__(self, first_name: str, last_name: str, age: int):
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
    @property
    def full_name(self) -> str:
        """Повертає повне ім'я людини."""
        return f"{self.first_name} {self.last_name}"
    def introduce(self) -> str:
        """Загальне привітання."""
        return f"Вітаю, мене звати {self.full_name}, мені {self.age} років."
class Student(Person):
    """Підклас для учнів, що наслідує Person."""
    def __init__(self, first_name: str, last_name: str, age: int, school_class: str):
        # Виклик конструктора базового класу
        super().__init__(first_name, last_name, age)
        self.school_class = school_class
        self.grades = {}  # Словник для оцінок: {"Математика": [10, 12, 11]}
    def add_grade(self, subject: str, grade: int):
        """Додає оцінку з певного предмета."""
        if subject not in self.grades:
            self.grades[subject] = []
        self.grades[subject].append(grade)
    def get_average_grade(self) -> float:
        """Рахує середній бал учня по всім предметам."""
        if not self.grades:
            return 0.0
        all_grades = [g for grades_list in self.grades.values() for g in grades_list]
        return round(sum(all_grades) / len(all_grades), 2)
    def introduce(self) -> str:
        """Перевизначений метод привітання для учня."""
        base_intro = super().introduce()
        return f"{base_intro} Я навчаюся в {self.school_class} класі."
class Teacher(Person):
    """Підклас для вчителів, що наслідує Person."""
    def __init__(self, first_name: str, last_name: str, age: int, salary: float):
        super().__init__(first_name, last_name, age)
        self.salary = salary
        self.subjects = []  # Список предметів, які викладає вчитель
    def add_subject(self, subject: str):
        """Додає новий предмет до списку викладання."""
        if subject not in self.subjects:
            self.subjects.append(subject)
    def raise_salary(self, percent: float):
        """Збільшує зарплату вчителя на певний відсоток."""
        self.salary += self.salary * (percent / 100)
    def introduce(self) -> str:
        """Перевизначений метод привітання для вчителя."""
        base_intro = super().introduce()
        subjects_str = ", ".join(self.subjects) if self.subjects else "поки немає"
        return f"{base_intro} Я викладаю такі предмети: {subjects_str}."

# ==========================================
# Демонстрація роботи програми:
# ==========================================

# Створюємо вчителя
teacher = Teacher("Марія", "Іванівна", 42, 15000.0)
teacher.add_subject("Математика")
teacher.add_subject("Геометрія")
# Створюємо учня
student = Student("Олексій", "Петров", 15, "10-А")
student.add_grade("Математика", 11)
student.add_grade("Математика", 12)
student.add_grade("Геометрія", 9)
# Перевірка методів та атрибутів
print(teacher.introduce())
# Виведе: Вітаю, мене звати Марія Іванівна, мені 42 років. Я викладаю такі предмети:
# Математика, Геометрія.
print(student.introduce())
# Виведе: Вітаю, мене звати Олексій Петров, мені 15 років. Я навчаюся в 10-А класі.
print(f"Середній бал учня: {student.get_average_grade()}")  # Виведе: 10.67
# Підвищуємо зарплату вчителю на 10%
teacher.raise_salary(10)
print(f"Нова зарплата вчителя: {teacher.salary} грн")  # Виведе: 16500 грн

# Task 2
# Математик
# Реалізуйте клас Mathematician, який є допоміжним класом для виконання математичних операцій
# зі списками
# Цей клас не має атрибутів і містить лише методи:
# square_nums (приймає список цілих чисел і повертає список квадратів)
# remove_positives (приймає список цілих чисел і повертає його без додатних чисел
# filter_leaps (приймає список дат (цілих чисел) і видаляє ті, що не є «високосними роками»
# class Mathematician:
#     pass
# m = Mathematician()
# assert m.square_nums([7, 11, 5, 4]) == [49, 121, 25, 16]
# assert m.remove_positives([26, -11, -8, 13, -90]) == [-11, -8, -90]
# assert m.filter_leaps([2001, 1884, 1995, 2003, 2020]) == [1884, 2020]

class Mathematician:
    @staticmethod
    def square_nums(nums):
        """Приймає список чисел і повертає список їхніх квадратів."""
        return [num ** 2 for num in nums]
    @staticmethod
    def remove_positives(nums):
        """Приймає список чисел і повертає його без додатних чисел."""
        return [num for num in nums if num <= 0]
    @staticmethod
    def filter_leaps(years):
        """Приймає список років і повертає лише високосні роки."""
        return [year for year in years if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)]
# Перевірка роботи коду напряму через клас (без створення об'єкта):
assert Mathematician.square_nums([7, 11, 5, 4]) == [49, 121, 25, 16]
assert Mathematician.remove_positives([26, -11, -8, 13, -90]) == [-11, -8, -90]
assert Mathematician.filter_leaps([2001, 1884, 1995, 2003, 2020]) == [1884, 2020]
print("Всі перевірки через staticmethod пройдено успішно!")

# Task 3
# Магазин товарів
# Напишіть клас Product, який має три атрибути:
# type, name, price
# Потім створіть клас ProductStore, який міститиме кілька об’єктів Product і буде працювати з
# усіма товарами в магазині. Усі методи, якщо вони не можуть виконати свою дію, повинні
# генерувати ValueError із відповідною інформацією про помилку.#
# Поради: Використовуйте концепції агрегації/композиції під час реалізації класу ProductStore.
# Ви також можете реалізувати додаткові класи для роботи з певним типом товару тощо.
# Крім того, клас ProductStore повинен мати такі методи:
# add(product, amount) — додає вказану кількість одного товару з попередньо визначеною надбавкою
# до ціни для вашого магазину (30 відсотків)
# set_discount(identifier, percent, identifier_type=’name’) — додає знижку для всіх товарів,
# зазначених за ідентифікаторами введення (тип або назва). Знижка повинна бути вказана у відсотках
# sell_product(product_name, amount) — видаляє певну кількість товарів із магазину, якщо вони є
# в наявності, в іншому випадку генерує помилку. Також збільшує дохід, якщо метод sell_product
# виконано успішно.
# get_income() — повертає суму, зароблену екземпляром ProductStore.
# get_all_products() — повертає інформацію про всі товари, доступні в магазині.
# get_product_info(product_name) — повертає кортеж із назвою товару та кількістю одиниць у
# магазині.
# class Product:
#     pass
# class ProductStore:
# pass
# p = Product(“Sport”, “Football T-Shirt”, 100)
# p2 = Product(“Food”, “Ramen”, 1.5)
# s = ProductStore()
# s.add(p, 10)
# s.add(p2, 300)
# s.sell_product('Ramen', 10)
# assert s.get_product_info('Ramen') == ('Ramen', 290)
class Product:
    def __init__(self, product_type: str, name: str, price: float):
        self.type = product_type
        self.name = name
        self.price = price
class ProductStore:
    def __init__(self):
        # Зберігаємо товари у вигляді:
        # { 'Назва товару': {'product': об'єкт_Product, 'amount': кількість, 'store_price': ціна_з_надбавкою} }
        self.stock = {}
        self.income = 0.0
    def add(self, product: Product, amount: int):
        """Додає товар у магазин із надбавкою 30%."""
        if amount <= 0:
            raise ValueError("Кількість товару для додавання має бути більшою за 0.")
        # Обчислюємо ціну з 30% надбавкою
        store_price = product.price * 1.3
        if product.name in self.stock:
            self.stock[product.name]['amount'] += amount
            # Якщо товар уже був, оновлюємо ціну на випадок, якщо вона змінилася у нового об'єкта
            self.stock[product.name]['store_price'] = store_price
        else:
            self.stock[product.name] = {
                'product': product,
                'amount': amount,
                'store_price': store_price
            }
    def set_discount(self, identifier: str, percent: float, identifier_type: str = 'name'):
        """Встановлює знижку у відсотках за назвою (name) або типом (type) товару."""
        if not (0 <= percent <= 100):
            raise ValueError("Знижка повинна бути в межах від 0 до 100 відсотків.")
        if identifier_type not in ['name', 'type']:
            raise ValueError("identifier_type повинен бути або 'name', або 'type'.")
        found = False
        for item in self.stock.values():
            product = item['product']
            if (identifier_type == 'name' and product.name == identifier) or \
                    (identifier_type == 'type' and product.type == identifier):
                # Застосовуємо знижку до базової ціни магазину (яка вже з надбавкою 30%)
                base_store_price = product.price * 1.3
                item['store_price'] = base_store_price * (1 - percent / 100)
                found = True
        if not found:
            raise ValueError(f"Товарів за ідентифікатором '{identifier}' з типом '{identifier_type}' не знайдено.")
    def sell_product(self, product_name: str, amount: int):
        """Продає товар, зменшує залишок та збільшує дохід."""
        if product_name not in self.stock:
            raise ValueError(f"Товар '{product_name}' відсутній у магазині.")
        if amount <= 0:
            raise ValueError("Кількість для продажу має бути більшою за 0.")
        if self.stock[product_name]['amount'] < amount:
            raise ValueError(
                f"Недостатньо товару '{product_name}' на складі. Доступно: {self.stock[product_name]['amount']}.")
        # Зменшуємо кількість та додаємо гроші до доходу
        self.stock[product_name]['amount'] -= amount
        self.income += self.stock[product_name]['store_price'] * amount
    def get_income(self) -> float:
        """Повертає суму, зароблену магазином."""
        return round(self.income, 2)
    def get_all_products(self) -> list:
        """Повертає список інформації про всі наявні товари."""
        return [
            {
                "type": item['product'].type,
                "name": name,
                "price": round(item['store_price'], 2),
                "amount": item['amount']
            }
            for name, item in self.stock.items()
        ]
    def get_product_info(self, product_name: str) -> tuple:
        """Повертає кортеж із назвою товару та кількістю одиниць у магазині."""
        if product_name not in self.stock:
            raise ValueError(f"Товар '{product_name}' не знайдено в базі магазину.")
        return product_name, self.stock[product_name]['amount']
# ==========================================
# Перевірка роботи коду:
# ==========================================
p = Product("Sport", "Football T-Shirt", 100)
p2 = Product("Food", "Ramen", 1.5)
s = ProductStore()
s.add(p, 10)
s.add(p2, 300)
# Продаємо 10 одиниць Ramen
s.sell_product('Ramen', 10)
# Перевірка через assert з умови завдання
assert s.get_product_info('Ramen') == ('Ramen', 290)
# Додаткова перевірка доходу:
# 10 одиниць Ramen за ціною (1.5 * 1.3) = 1.95 за штуку. Разом: 19.5
print(f"Поточний дохід магазину: {s.get_income()} грн")  # Виведе: 19.5
# Встановлюємо знижку 10% на категорію Sport
s.set_discount("Sport", 10, identifier_type="type")
print(f"Усі товари після знижки: {s.get_all_products()}")
print("Всі перевірки пройдено успішно!")

# Task 4
# Виняток, визначений користувачем#
# Створіть власний виняток із назвою «CustomException». Ви можете успадкувати його від базового
# класу Exception, але розширити його функціональність, щоб записувати кожне повідомлення про
# помилку у файл із назвою «logs.txt». Порада: скористайтеся методом __init__, щоб розширити
# функціональність для збереження повідомлень у файл#
# class CustomException(Exception):
# def __init__(self, msg):
from datetime import datetime
class CustomException(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg
        self._log_to_file()
    def _log_to_file(self):
        """Внутрішній метод для запису помилки у файл логів."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{current_time}] ERROR: {self.msg}\n"
        with open("logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
# ==========================================
# Перевірка роботи коду:
# ==========================================
try:
    raise CustomException("Тестова помилка")
except CustomException as e:
    print(f"Перехоплено: {e}")
with open("logs.txt", "r", encoding="utf-8") as current_file:
    print("\nВміст файлу logs.txt:")
    print(current_file.read())