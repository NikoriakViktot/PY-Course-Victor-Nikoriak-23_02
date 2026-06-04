# Task 1
# Перевизначення методів.
# Створіть базовий клас Animal з методом talk, а потім створіть два підкласи: Dog і Cat, і
# зробіть їх реалізацію методу talk різною. Наприклад, для класу Dog це може бути виведення
# «woof woof», а для класу Cat — «meow».
# Також створіть просту генеричну функцію, яка приймає як вхідні дані екземпляр класу Cat або
# Dog і виконує метод talk на вхідному параметрі.
class Animal:
    """Базовий клас для всіх тварин."""
    def talk(self):
        # Базовий метод, який підкласи мають перевизначити
        raise NotImplementedError("Підкласи повинні реалізувати цей метод!")
class Dog(Animal):
    """Підклас Собака."""
    def talk(self):
        return "woof woof"
class Cat(Animal):
    """Підклас Кіт."""
    def talk(self):
        return "meow"
# Генерична функція для роботи з будь-якими тваринами
def make_animal_talk(animal_obj):
    """
    Приймає об'єкт тварини і викликає її унікальний метод talk().
    Завдяки поліморфізму, функція не перевіряє тип об'єкта (кіт чи собака),
    а просто виконує доступний інтерфейс.
    """
    print(animal_obj.talk())
# ==========================================
# Демонстрація роботи програми:
# ==========================================
# Створюємо екземпляри класів
my_dog = Dog()
my_cat = Cat()
# Викликаємо генеричну функцію для кожного об'єкта
make_animal_talk(my_dog)  # Виведе: woof woof
make_animal_talk(my_cat)  # Виведе: meow

# Task 2
# Бібліотека
# Створіть структуру класів, що реалізує бібліотеку. Класи:
# 1) Library — name, books = [], authors = []
# 2) Book — name, year, author (author має бути екземпляром класу Author)
# 3) Author — name, country, birthday, books = []
# Клас Library
# Методи:
# - new_book(name: str, year: int, author: Author) — повертає екземпляр класу Book і додає книгу до списку книг поточної бібліотеки.
# - group_by_author(author: Author) — повертає список усіх книг, згрупованих за вказаним автором
# - group_by_year(year: int) — повертає список усіх книг, згрупованих за вказаним роком
# Усі 3 класи повинні мати читабельні методи __repr__ та __str__.#
# Також клас book повинен мати змінну класу, яка зберігає кількість усіх існуючих книг
# class Library:
#     pass#
# class Book:
#     pass
# class Author:
#     pass
#  Усі класи мають методи __str__ та __repr__, а клас Book відстежує загальну кількість створених
#  книг за допомогою змінної класу total_books_count.
class Author:
    def __init__(self, name: str, country: str, birthday: str):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.books = []  # Список об'єктів Book цього автора
    def __str__(self):
        return f"{self.name} ({self.country}, нар. {self.birthday})"
    def __repr__(self):
        return f"Author(name='{self.name}', country='{self.country}', birthday='{self.birthday}')"
class Book:
    # Змінна класу для відстеження загальної кількості існуючих книг
    total_books_count = 0
    def __init__(self, name: str, year: int, author: Author):
        self.name = name
        self.year = year
        self.author = author
        # Збільшуємо лічильник при створенні кожної нової книги
        Book.total_books_count += 1
    def __str__(self):
        return f"«{self.name}» ({self.year}) — {self.author.name}"
    def __repr__(self):
        return f"Book(name='{self.name}', year={self.year}, author={repr(self.author)})"
class Library:
    def __init__(self, name: str):
        self.name = name
        self.books = []  # Список об'єктів Book у цій бібліотеці
        self.authors = []  # Список об'єктів Author у цій бібліотеці
    def new_book(self, name: str, year: int, author: Author) -> Book:
        """Створює нову книгу, додає її до бібліотеки та до списку книг автора."""
        book = Book(name, year, author)
        # Додаємо книгу до списку книг бібліотеки
        self.books.append(book)
        # Якщо цього автора ще немає в списку авторів бібліотеки, додаємо його
        if author not in self.authors:
            self.authors.append(author)
        # Додаємо книгу до власного списку книг автора (якщо її там ще немає)
        if book not in author.books:
            author.books.append(book)
        return book
    def group_by_author(self, author: Author) -> list:
        """Повертає список усіх книг бібліотеки, написаних вказаним автором."""
        return [book for book in self.books if book.author == author]
    def group_by_year(self, year: int) -> list:
        """Повертає список усіх книг бібліотеки, опублікованих у вказаному році."""
        return [book for book in self.books if book.year == year]
    def __str__(self):
        return f"Бібліотека '{self.name}' (Книг: {len(self.books)}, Авторів: {len(self.authors)})"
    def __repr__(self):
        return f"Library(name='{self.name}', books={self.books}, authors={self.authors})"
# ==========================================
# Демонстрація роботи програми та перевірка:
# ==========================================
# 1. Створюємо авторів
author1 = Author("Тарас Шевченко", "Україна", "09.03.1814")
author2 = Author("Джордж Орвелл", "Велика Британія", "25.06.1903")
# 2. Створюємо бібліотеку
my_library = Library("Центральна Бібліотека")
# 3. Додаємо книги через метод new_book
b1 = my_library.new_book("Кобзар", 1840, author1)
b2 = my_library.new_book("Гайдамаки", 1841, author1)
b3 = my_library.new_book("1984", 1949, author2)
b4 = my_library.new_book("Колгосп тварин", 1945, author2)
print("--- Перевірка методів __str__ ---")
print(my_library)  # Виведе інформацію про бібліотеку
print(b1)  # Виведе інформацію про книгу
print(author1)  # Виведе інформацію про автора
print("\n--- Перевірка фільтрації за автором (Тарас Шевченко) ---")
shevchenko_books = my_library.group_by_author(author1)
print(shevchenko_books)
print("\n--- Перевірка фільтрації за роком (1949) ---")
books_1949 = my_library.group_by_year(1949)
print(books_1949)
print("\n--- Перевірка лічильника книг у класі Book ---")
print(f"Загальна кількість створених книг у системі: {Book.total_books_count}")  # Виведе: 4
# Task 3
# Fraction
# Створіть клас Fraction, який реалізує всі основні арифметичні операції з дробами (+, -, /, *) з відповідною перевіркою та обробкою помилок. Вам потрібно додати магічні методи для математичних операцій та операцій порівняння між об’єктами класу Fraction
# class Fraction:
#     pass
# if __name__ == “__main__”:
#     x = Fraction(1, 2)
#     y = Fraction(1, 4)
#     x + y == Fraction(3, 4)
import math
class Fraction:
    def __init__(self, numerator: int, denominator: int):
        if not isinstance(numerator, int) or not isinstance(denominator, int):
            raise TypeError("Чисельник і знаменник повинні бути цілими числами (int).")
        if denominator == 0:
            raise ValueError("Знаменник не може дорівнювати нулю.")
        # Слідкуємо за знаком: якщо знаменник від'ємний, переносимо мінус нагору
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        # Автоматично скорочуємо дріб при створенні
        common_divisor = math.gcd(numerator, denominator)
        self.numerator = numerator // common_divisor
        self.denominator = denominator // common_divisor
    # --- Магічні методи для виведення ---
    def __str__(self):
        return f"{self.numerator}/{self.denominator}"
    def __repr__(self):
        return f"Fraction({self.numerator}, {self.denominator})"
    # --- Магічні методи для порівняння ---
    def __eq__(self, other):
        if not isinstance(other, Fraction):
            return False
        return self.numerator == other.numerator and self.denominator == other.denominator
    def __lt__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        return self.numerator * other.denominator < other.numerator * self.denominator
    def __le__(self, other):
        return self < other or self == other
    # --- Магічні методи для арифметики ---
    def __add__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        # Формула: a/b + c/d = (a*d + c*b) / (b*d)
        new_num = self.numerator * other.denominator + other.numerator * self.denominator
        new_den = self.denominator * other.denominator
        return Fraction(new_num, new_den)
    def __sub__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        # Формула: a/b - c/d = (a*d - c*b) / (b*d)
        new_num = self.numerator * other.denominator - other.numerator * self.denominator
        new_den = self.denominator * other.denominator
        return Fraction(new_num, new_den)
    def __mul__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        # Формула: (a/b) * (c/d) = (a*c) / (b*d)
        return Fraction(self.numerator * other.numerator, self.denominator * other.denominator)
    def __truediv__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        # При діленні на нульовий дріб виникне ValueError всередині __init__
        # Формула: (a/b) / (c/d) = (a*d) / (b*c)
        return Fraction(self.numerator * other.denominator, self.denominator * other.numerator)
if __name__ == "__main__":
    x = Fraction(1, 2)
    y = Fraction(1, 4)
    # Перевірка з умови завдання
    print(f"Перевірка додавання: {x + y == Fraction(3, 4)}")  # True
    # Додаткові перевірки
    print(f"{x} + {y} = {x + y}")  # 1/2 + 1/4 = 3/4
    print(f"{x} - {y} = {x - y}")  # 1/2 - 1/4 = 1/4
    print(f"{x} * {y} = {x * y}")  # 1/2 * 1/4 = 1/8
    print(f"{x} / {y} = {x / y}")  # 1/2 / 1/4 = 2/1 (автоматично скорочено)
    # Перевірка порівнянь
    print(f"Чи рівні {x} та {y}? -> {x == y}")  # False
    print(f"Чи {y} менше за {x}? -> {y < x}")  # True
    # Перевірка обробки помилок
    try:
        invalid = Fraction(1, 0)
    except ValueError as e:
        print(f"\nПерехоплено помилку: {e}")