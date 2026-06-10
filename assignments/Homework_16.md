## Task 1: School (Ієрархія класів та успадкування)

Тут ми використовуємо базовий клас `Person` для спільних атрибутів (ім'я, вік, email) та методів. Класи `Student` та `Teacher` успадковують його за допомогою `super().__init__()` та додають свою специфіку (оцінки, предмети, зарплату).

Python

```
class Person:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email

    def get_info(self) -> str:
        return f"{self.name}, {self.age} років. Email: {self.email}"

    def Greet(self) -> str:
        return f"Привіт, мене звати {self.name}!"


class Student(Person):
    def __init__(self, name: str, age: int, email: str, student_id: str):
        super().__init__(name, age, email)
        self.student_id = student_id
        self.grades = []  # Список оцінок

    def add_grade(self, grade: int):
        if 1 <= grade <= 12:
            self.grades.append(grade)
        else:
            raise ValueError("Оцінка повинна бути від 1 до 12")

    def get_average_grade(self) -> float:
        if not self.grades:
            return 0.0
        return sum(self.grades) / len(self.grades)

    # Перевизначення (Polymorphism)
    def get_info(self) -> str:
        base_info = super().get_info()
        return f"[Студент] {base_info}, ID: {self.student_id}, Сер. бал: {self.get_average_grade():.2f}"


class Teacher(Person):
    def __init__(self, name: str, age: int, email: str, subject: str, salary: float):
        super().__init__(name, age, email)
        self.subject = subject
        self.salary = salary

    def raise_salary(self, percent: float):
        self.salary += self.salary * (percent / 100)

    # Перевизначення (Polymorphism)
    def get_info(self) -> str:
        base_info = super().get_info()
        return f"[Вчитель] {base_info}, Предмет: {self.subject}, Зарплата: {self.salary} грн"


# Перевірка роботи:
student = Student("Олексій", 19, "alex@school.com", "ST-2026")
student.add_grade(11)
student.add_grade(12)

teacher = Teacher("Марія Іванівна", 45, "maria@school.com", "Математика", 25000)

print(student.get_info())
print(teacher.get_info())
```

## Task 2: Mathematician (Утилітарний клас)

Цей клас не зберігає стан (не має `__init__`), а просто обробляє списки. Для фільтрації високосних років використано стандартне правило: рік ділиться на 4, але не ділиться на 100, або ж ділиться на 400.

Python

```
class Mathematician:
    def square_nums(self, nums: list[int]) -> list[int]:
        return [num ** 2 for num in nums]

    def remove_positives(self, nums: list[int]) -> list[int]:
        # Повертає тільки від'ємні числа та нуль
        return [num for num in nums if num <= 0]

    def filter_leaps(self, years: list[int]) -> list[int]:
        # Високосний рік: (ділиться на 4 І НЕ ділиться на 100) АБО ділиться на 400
        return [y for y in years if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)]


# Перевірка через assert:
m = Mathematician()
assert m.square_nums([7, 11, 5, 4]) == [49, 121, 25, 16]
assert m.remove_positives([26, -11, -8, 13, -90]) == [-11, -8, -90]
assert m.filter_leaps([2001, 1884, 1995, 2003, 2020]) == [1884, 2020]
print("Task 2: Всі тести пройдено успішно!")
```

## Task 3: Product Store (Агрегація та бізнес-логіка)

Для реалізації цього завдання найкраще зберігати продукти всередині магазину у вигляді словника, де ключем буде назва продукту (або сам об'єкт), а значенням — внутрішня інформація: об'єкт продукту, його ціна з націнкою та поточна кількість.

Python

```
class Product:
    def __init__(self, product_type: str, name: str, price: float):
        self.type = product_type
        self.name = name
        self.price = price


class ProductStore:
    def __init__(self):
        # Структура: { 'Назва_продукту': {'product': obj, 'store_price': float, 'amount': int} }
        self.inventory = {}
        self.income = 0.0

    def add(self, product: Product, amount: int):
        if amount <= 0:
            raise ValueError("Кількість товару для додавання має бути більшою за 0")
        
        # Якщо товар новий, додаємо його з націнкою 30%
        if product.name not in self.inventory:
            store_price = product.price * 1.30
            self.inventory[product.name] = {
                'product': product,
                'store_price': store_price,
                'amount': amount
            }
        else:
            self.inventory[product.name]['amount'] += amount

    def set_discount(self, identifier: str, percent: float, identifier_type: str = 'name'):
        if not (0 <= percent <= 100):
            raise ValueError("Знижка повинна бути в межах від 0 до 100 відсотків")
        
        found = False
        for item in self.inventory.values():
            prod = item['product']
            
            # Перевіряємо тип ідентифікатора
            if identifier_type == 'name' and prod.name == identifier:
                item['store_price'] -= item['store_price'] * (percent / 100)
                found = True
            elif identifier_type == 'type' and prod.type == identifier:
                item['store_price'] -= item['store_price'] * (percent / 100)
                found = True
                
        if not found:
            raise ValueError(f"Товар за ідентифікатором '{identifier}' типу '{identifier_type}' не знайдено")

    def sell_product(self, product_name: str, amount: int):
        if product_name not in self.inventory:
            raise ValueError(f"Товару з назвою '{product_name}' немає в асортименті магазину")
        
        item = self.inventory[product_name]
        if item['amount'] < amount:
            raise ValueError(f"Недостатньо товару '{product_name}'. В наявності: {item['amount']}, запитувано: {amount}")
        
        # Продаж
        item['amount'] -= amount
        self.income += item['store_price'] * amount

    def get_income(self) -> float:
        return self.income

    def get_all_products(self) -> list[str]:
        info_list = []
        for name, item in self.inventory.items():
            prod = item['product']
            info_list.append(f"Тип: {prod.type}, Назва: {name}, Ціна: {item['store_price']:.2f}, Кількість: {item['amount']}")
        return info_list

    def get_product_info(self, product_name: str) -> tuple[str, int]:
        if product_name not in self.inventory:
            raise ValueError(f"Товару '{product_name}' немає в магазині")
        return product_name, self.inventory[product_name]['amount']


# Перевірка через assert:
p = Product('Sport', 'Football T-Shirt', 100)
p2 = Product('Food', 'Ramen', 1.5)

s = ProductStore()
s.add(p, 10)
s.add(p2, 300)

s.sell_product('Ramen', 10)

assert s.get_product_info('Ramen') == ('Ramen', 290)
print("Task 3: Всі тести пройдено успішно!")
```

## Task 4: Custom exception (Кастомна помилка та логування)

При створенні винятку ми перевизначаємо метод `__init__`. Спочатку викликаємо конструктор базового класу `Exception`, щоб зберегти стандартну поведінку помилок, а потім дописуємо логіку запису тексту помилки у файл `logs.txt` (у режимі `"a"` — append, щоб дописувати в кінець файлу).

Python

```
class CustomException(Exception):
    def __init__(self, msg: str):
        # Викликаємо конструктор базового класу Exception
        super().__init__(msg)
        
        # Логуємо повідомлення у файл logs.txt
        try:
            with open("logs.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"Помилка: {msg}\n")
        except IOError as e:
            print(f"Не вдалося записати лог у файл: {e}")


# Демонстрація роботи:
try:
    raise CustomException("Щось пішло не так у коді!")
except CustomException as e:
    print(f"Зловлено кастомне виключення: {e}")
    print("Повідомлення успішно записано в 'logs.txt'")
```