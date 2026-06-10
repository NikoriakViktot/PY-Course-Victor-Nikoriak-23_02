# Task 1

# Створюємо 2 файли module1.py, module2.py

# Створюємо функцію в фійлі module1.py
def greet(name):
   return f"Hello, {name}!"

# Імпортуємо і використовуємо
from module1 import greet

name = input("Enter your name: ")
message = greet(name)

print(message)

# Task 2

import sys

print("Before:", sys.path)

sys.path.append("C:/my_modules")  # додаємо новий шлях

print("After:", sys.path)

# Task 3

# Створюємо файл mymod.py

# Функція підрахунку рядків
def count_lines(name):
    file = open(name, "r")
    lines = file.readlines()
    file.close()
    return len(lines)

# Функція підрахунку символів
def count_chars(name):
    file = open(name, "r")
    text = file.read()
    file.close()
    return len(text)

# Тестова функція
def test(name):
    lines = count_lines(name)
    chars = count_chars(name)

    print("Lines:", lines)
    print("Characters:", chars)

# Використання (в іншому файлі або внизу)
import mymod
mymod.test("mymod.py")