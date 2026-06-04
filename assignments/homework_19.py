# Task 1
# Створіть власну реалізацію вбудованої функції `enumerate` під назвою «with_index», яка
# приймає два параметри: «iterable» та «start» (за замовчуванням — 0). Поради: ознайомтеся
# з документацією до функції `enumerate`.
def with_index(iterable, start=0):
    current = start
    for item in iterable:
        yield current, item
        current += 1
# Список для тесту
fruits = ["яблуко", "банан", "груша"]
# Використання зі значенням start за замовчуванням (0)
for index, fruit in with_index(fruits):
    print(f"Індекс: {index}, Фрукт: {fruit}")
print("-" * 20)
# Використання зі зміненим значенням start (наприклад, з 1)
for index, fruit in with_index(fruits, start=1):
    print(f"№ {index}: {fruit}")

# Task 2
# Створіть власну реалізацію вбудованої функції range під назвою in_range(), яка приймає
# три параметри: «start», «end» та необов’язковий параметр step. Поради: ознайомтеся з
# документацією до функції «range»
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
# 1. Звичайний крок вперед
print("Крок 1:")
print(list(in_range(1, 5)))  # [1, 2, 3, 4]
# 2. Крок більше одиниці
print("\nКрок 2:")
print(list(in_range(2, 10, 2)))  # [2, 4, 6, 8]
# 3. Зворотний відлік (від'ємний крок)
print("\nЗворотний крок:")
print(list(in_range(5, 0, -1)))  # [5, 4, 3, 2, 1]

# Task 3
# Створіть власну реалізацію об'єкта, що підтримує ітерацію, який можна використовувати в
# циклі for-in. Також додайте логіку для отримання елементів за допомогою синтаксису
# квадратних дужок.
class CustomCollection:
    def __init__(self, data):
        # Зберігаємо дані (наприклад, список)
        self.data = list(data)
        # Індекс для відстеження поточної позиції під час ітерації
        self.current_index = 0
    # --- Логіка ітератора ---
    def __iter__(self):
        # Скидаємо індекс перед початком нового циклу for-in
        self.current_index = 0
        return self
    def __next__(self):
        if self.current_index < len(self.data):
            result = self.data[self.current_index]
            self.current_index += 1
            return result
        # Якщо елементи закінчилися, зупиняємо цикл
        raise StopIteration
    # --- Логіка доступу за індексом ---
    def __getitem__(self, index):
        # Дозволяє читати дані як collection[index]
        return self.data[index]
# Створюємо об'єкт
my_list = CustomCollection(["Python", "Java", "C++", "JavaScript"])
# 1. Перевірка доступу за індексом []
print("Елемент за індексом 1:", my_list[1])
print("Останній елемент:", my_list[-1])
print("\n--- Ітерація через for-in ---")
# 2. Перевірка роботи в циклі for-in
for language in my_list:
    print(language)