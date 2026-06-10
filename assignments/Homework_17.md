## Task 1: Polymorphism & Duck Typing (Animal, Dog, Cat)

Python

```
class Animal:
    def talk(self):
        # Базовий метод, який можна перевизначити
        raise NotImplementedError("Subclasses must implement this method")

class Dog(Animal):
    def talk(self):
        print("woof woof")

class Cat(Animal):
    def talk(self):
        print("meow")

# Універсальна (generic) функція
def make_animal_talk(animal_instance: Animal):
    """Приймає об'єкт класу Animal (або його нащадків) і викликає метод talk."""
    animal_instance.talk()

# Перевірка роботи Task 1
if __name__ == "__main__":
    dog = Dog()
    cat = Cat()
    
    make_animal_talk(dog)  # Виведе: woof woof
    make_animal_talk(cat)  # Виведе: meow
```

## Task 2: Library Structure

Тут реалізовано зв'язок між трьома класами, підрахунок кількості книг через змінну класу (`total_books`), а також методи фільтрації та красиве відображення через `__str__` та `__repr__`.

Python

```
class Author:
    def __init__(self, name: str, country: str, birthday: str):
        self.name = name
        self.country = country
        self.birthday = birthday
        self.books = []  # Список об'єктів класу Book

    def __str__(self):
        return f"{self.name} ({self.country})"

    def __repr__(self):
        return f"Author(name='{self.name}', country='{self.country}')"


class Book:
    # Змінна класу для підрахунку всіх створених книг
    total_books = 0

    def __init__(self, name: str, year: int, author: Author):
        self.name = name
        self.year = year
        self.author = author
        
        # Автоматично збільшуємо лічильник при створенні екземпляра
        Book.total_books += 1
        # Автоматично додаємо книгу автору, якщо її там ще немає
        if self not in author.books:
            author.books.append(self)

    def __str__(self):
        return f"'{self.name}' by {self.author.name} ({self.year})"

    def __repr__(self):
        return f"Book(name='{self.name}', year={self.year}, author='{self.author.name}')"


class Library:
    def __init__(self, name: str):
        self.name = name
        self.books = []    # Список усіх книг у бібліотеці
        self.authors = []  # Список усіх авторів у бібліотеці

    def new_book(self, name: str, year: int, author: Author) -> Book:
        """Створює нову книгу, додає її в бібліотеку та повертає її екземпляр."""
        book = Book(name, year, author)
        self.books.append(book)
        
        if author not in self.authors:
            self.authors.append(author)
            
        return book

    def group_by_author(self, author: Author) -> list:
        """Повертає список книг конкретного автора, які є в цій бібліотеці."""
        return [book for book in self.books if book.author == author]

    def group_by_year(self, year: int) -> list:
        """Повертає список книг за певний рік."""
        return [book for book in self.books if book.year == year]

    def __str__(self):
        return f"Library '{self.name}' with {len(self.books)} books"

    def __repr__(self):
        return f"Library(name='{self.name}', books_count={len(self.books)})"


# Перевірка роботи Task 2
if __name__ == "__main__":
    library = Library("Центральна Бібліотека")
    
    author1 = Author("Тарас Шевченко", "Україна", "09-03-1814")
    author2 = Author("Стівен Кінг", "США", "21-09-1947")
    
    book1 = library.new_book("Кобзар", 1840, author1)
    book2 = library.new_book("Воно", 1986, author2)
    book3 = library.new_book("Сяйво", 1977, author2)
    
    print(f"Всього книг створено взагалі: {Book.total_books}")
    print(f"Книги Кінга в бібліотеці: {library.group_by_author(author2)}")
    print(f"Книги 1840 року: {library.group_by_year(1840)}")
    print(library)
```

## Task 3: Fraction Class (Кастомні Дроби)

Для правильного додавання, віднімання та порівняння дробів використовується пошук **найменшого спільного знаменника** або просте перемноження знаменників із подальшим скороченням дробу за допомогою функції **НСД (Найбільший спільний дільник)** з модуля `math`.

Python

```
import math

class Fraction:
    def __init__(self, numerator: int, denominator: int):
        if not isinstance(numerator, int) or not isinstance(denominator, int):
            raise TypeError("Чисельник і знаменник мають бути цілими числами (int).")
        if denominator == 0:
            raise ValueError("Знаменник не може дорівнювати нулю.")
        
        # Обробка знаку: якщо знаменник від'ємний, переносимо мінус в чисельник
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
            
        self.numerator = numerator
        self.denominator = denominator
        self._reduce()  # Автоматично скорочуємо дріб при створенні

    def _reduce(self):
        """Внутрішній метод для скорочення дробу."""
        gcd = math.gcd(self.numerator, self.denominator)
        self.numerator //= gcd
        self.denominator //= gcd

    # --- Магічні методи арифметики ---

    def __add__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        new_num = self.numerator * other.denominator + other.numerator * self.denominator
        new_den = self.denominator * other.denominator
        return Fraction(new_num, new_den)

    def __sub__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        new_num = self.numerator * other.denominator - other.numerator * self.denominator
        new_den = self.denominator * other.denominator
        return Fraction(new_num, new_den)

    def __mul__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        return Fraction(self.numerator * other.numerator, self.denominator * other.denominator)

    def __truediv__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        if other.numerator == 0:
            raise ZeroDivisionError("Ділення на дріб із нульовим чисельником (ділення на нуль).")
        return Fraction(self.numerator * other.denominator, self.denominator * other.numerator)

    # --- Магічні методи порівняння ---

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

    def __gt__(self, other):
        if not isinstance(other, Fraction):
            return NotImplemented
        return self.numerator * other.denominator > other.numerator * self.denominator

    def __ge__(self, other):
        return self > other or self == other

    # --- Відображення ---

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"

    def __repr__(self):
        return f"Fraction({self.numerator}, {self.denominator})"


# Перевірка роботи Task 3 (включаючи твій тест-кейс)
if __name__ == "__main__":
    x = Fraction(1, 2)
    y = Fraction(1, 4)
    
    # Твій тест-кейс з умови:
    print("Результат x + y == Fraction(3, 4):", x + y == Fraction(3, 4))  # Має бути True
    
    # Додаткові перевірки:
    print(f"{x} + {y} = {x + y}")   # 3/4
    print(f"{x} - {y} = {x - y}")   # 1/4
    print(f"{x} * {y} = {x * y}")   # 1/8
    print(f"{x} / {y} = {x / y}")   # 2/1
    print(f"Чи {x} > {y}?: {x > y}") # True
```