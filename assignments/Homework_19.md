## Task 1: Своя реалізація `enumerate` (`with_index`)

Функція `enumerate` в Python повертає ітератор, який видає кортежі, що складаються з індексу та самого елемента. Найпростіший і найелегантніший спосіб відтворити цю поведінку — використати **генератор** (ключове слово `yield`).

Python

```
from typing import Iterable, Any, Generator

def with_index(iterable: Iterable[Any], start: int = 0) -> Generator[tuple[int, Any], None, None]:
    """Власна реалізація вбудованої функції enumerate."""
    current = start
    for item in iterable:
        yield current, item
        current += 1

# Перевірка роботи Task 1
if __name__ == "__main__":
    fruits = ["apple", "banana", "cherry"]
    
    print("Тест з дефолтним start=0:")
    for index, fruit in with_index(fruits):
        print(f"Індекс: {index}, Елемент: {fruit}")
        
    print("\nТест зі start=10:")
    for index, fruit in with_index(fruits, start=10):
        print(f"Індекс: {index}, Елемент: {fruit}")
```

## Task 2: Своя реалізація `range` (`in_range`)

Вбудований `range` хитрий: якщо передати один аргумент, він вважається за `end` (а `start` стає `0`). Якщо два або три — перший стає `start`.

Реалізуємо функцію `in_range`, яка гнучко приймає аргументи, валідує `step` (він не може бути `0`) і працює як в пряму, так і в зворотну сторону (з від'ємним кроком).

Python

```
from typing import Generator

def in_range(*args) -> Generator[int, None, None]:
    """Власна реалізація функції range().
    
    Підтримує виклики:
    - in_range(end)
    - in_range(start, end)
    - in_range(start, end, step)
    """
    # Ініціалізуємо дефолтні значення
    start = 0
    step = 1
    
    # Розбираємо аргументи як у вбудованому range()
    if len(args) == 1:
        end = args[0]
    elif len(args) == 2:
        start, end = args
    elif len(args) == 3:
        start, end, step = args
    else:
        raise TypeError(f"in_range expected at most 3 arguments, got {len(args)}")
        
    if step == 0:
        raise ValueError("in_range() arg 3 must not be zero")
        
    current = start
    
    # Логіка для додатного кроку
    if step > 0:
        while current < end:
            yield current
            current += step
    # Логіка для від'ємного кроку
    else:
        while current > end:
            yield current
            current += step

# Перевірка роботи Task 2
if __name__ == "__main__":
    print("Один аргумент (end=5):", list(in_range(5)))
    print("Два аргументи (start=2, end=7):", list(in_range(2, 7)))
    print("Три аргументи з кроком (2, 10, 2):", list(in_range(2, 10, 2)))
    print("Зворотний крок (10, 2, -2):", list(in_range(10, 2, -2)))
```

## Task 3: Кастомний Iterable з доступом через `[]` (Square Brackets)

Щоб об'єкт підтримував цикл `for-in`, він має реалізувати метод `__iter__` (який повертає ітератор, тобто об'єкт з методом `__next__`). А щоб об'єкт підтримував синтаксис квадратних дужок `obj[index]`, йому потрібен метод `__getitem__`.

Створимо клас `CustomSequence`, який зберігає колекцію елементів. Ми зробимо його ітератором «самого себе» для простоти, а також навчимо `__getitem__` працювати не лише зі звичайними індексами, а й зі зрізами (`slices`).

Python

```
class CustomSequence:
    def __init__(self, data: list):
        self.data = list(data)  # Робимо копію списку даних
        self._cursor = 0        # Курсор для ітерації

    # --- Логіка Ітератора (for-in loop) ---
    def __iter__(self):
        # При кожному виклику iter() скидаємо курсор на початок, 
        # щоб об'єкт можна було ітерувати багаторазово
        self._cursor = 0
        return self

    def __next__(self):
        if self._cursor >= len(self.data):
            raise StopIteration  # Сигнал для циклу 'for', що елементи закінчилися
        
        result = self.data[self._cursor]
        self._cursor += 1
        return result

    # --- Логіка доступу через квадратні дужки [index] ---
    def __getitem__(self, item):
        """Дозволяє отримувати елементи як по індексу obj[0], так і через зрізи obj[1:3]."""
        if isinstance(item, (int, slice)):
            return self.data[item]
        raise TypeError(f"Sequence indices must be integers or slices, not {type(item).__name__}")


# Перевірка роботи Task 3
if __name__ == "__main__":
    # Створюємо нашу кастомну послідовність
    my_seq = CustomSequence(["Python", "Java", "C++", "Go", "Rust"])
    
    # 1. Перевірка роботи в циклі for-in
    print("Ітерація через for-in:")
    for lang in my_seq:
        print(f" -> {lang}")
        
    # 2. Перевірка доступу за індексом через квадратні дужки
    print("\nДоступ за індексами:")
    print("Перший елемент [0]:", my_seq[0])
    print("Останній елемент [-1]:", my_seq[-1])
    
    # 3. Перевірка підтримки зрізів (slices)
    print("\nРобота зі зрізами [1:4]:")
    print(my_seq[1:4])  # Виведе ['Java', 'C++', 'Go']
```