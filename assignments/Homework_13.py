# Task 1

def count_local_vars(func):
    # Повертаємо кількість локальних змінних функції
    return func.__code__.co_nlocals


# Приклад для перевірки:
def my_function():
    a = 1
    b = "Привіт"
    c = [1, 2, 3]
    d = 4  # Загалом 4 локальні змінні


print(
    f"Кількість локальних змінних: {count_local_vars(my_function)}"
)  # Виведе: 4

# Task 2


def outer_function(msg):
    # Створюємо внутрішню функцію
    def inner_function():
        return f"Повідомлення зсередини: {msg}"

    # Повертаємо саму функцію як об'єкт (БЕЗ дужок!)
    return inner_function


# Отримуємо доступ до внутрішньої функції
my_func_access = outer_function("Привіт, світе!")

# Тепер змінна my_func_access зберігає в собі inner_function, і ми можемо її викликати
print(my_func_access())  # Виведе: Повідомлення зсередини: Привіт, світе!


# Task 3

def choose_func(nums: list, func1, func2):
    # Перевіряємо, чи всі числа в списку є додатними (> 0)
    if all(num > 0 for num in nums):
        return func1(nums)
    else:
        return func2(nums)


# --- Перевірка працездатності (Твій код із завдання) ---

nums1 = [1, 2, 3, 4, 5]
nums2 = [1, -2, 3, -4, 5]


def square_nums(nums):
    return [num**2 for num in nums]


def remove_negatives(nums):
    return [num for num in nums if num > 0]


# Запуск асертів (якщо все правильно, код виконається без помилок)
assert choose_func(nums1, square_nums, remove_negatives) == [1, 4, 9, 16, 25]
assert choose_func(nums2, square_nums, remove_negatives) == [1, 3, 5]

print("Усі перевірки (asserts) успішно пройдено!")