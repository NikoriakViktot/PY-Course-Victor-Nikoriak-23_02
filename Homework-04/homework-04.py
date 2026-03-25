# Task1
def get_string_ends (s):
    if len(s) <2:
        return""
    return s[:2] + s[-2:]

print ("\n")

# Task2
def check_phone_number(phone):
    if len(phone) == 10 and phone.isdigit():
        print(f"Номер '{phone}' є правильним.")
    else:
        print(f"Номер '{phone}' не вірний. має бути 10 цифр без зайвих символів.")

test_numbers = []
for num in test_numbers:
    check_phone_number(num)

user_num = input ("\n Введіть номер телуфону для перевірки (10 цифр):")
check_phone_number(user_num)

print ("\n")

# Task3

import random
def math_quiz():
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)
    correct_answer = num1 + num2
    print("---Математична вікторина---")
    user_input = input(f"Скільки буде {num1} + {num2}?")

    if user_input.isdigit() or (user_input.startswith('-') and user_input[1:].isdigit()):
        user_answer = int(user_input)

        if user_answer == correct_answer:
            print("Вітаємо! Це правильна відповідь.")
        else:
            print (f"На жаль, це помилка. Правильна відповідь: {correct_answer}.")
    else:
        print("Будь ласка, вводьте числа")
math_quiz()

print ("\n")

# Task4

def check_name():
    my_name = "Sergiy"
    user_input = input("Як вас звати? ")

    if user_input.lower() == my_name:
        print("True (Імена збігаються)")
    else:
        print(f"False (Імена різні. Ви ввелт {user_input}, а необхідно: {my_name})")
check_name()

