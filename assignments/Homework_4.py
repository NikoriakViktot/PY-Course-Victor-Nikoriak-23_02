# Task 1

a = "helloworld"

if len(a) < 2:
    result_1 = ""
else:
    result_1 = a[:2] + a[-2:]

print(result_1)

b = "my"

if len(b) < 2:
    result_2 = ""
else:
    result_2 = b[:2] + b[-2:]

print(result_2)

c = "x"

if len(c) < 2:
    result_3 = ""
else:
    result_3 = c[:2] + c[-2:]

print(result_3)

# Task 2

phone_num = "0508078344"

if len(phone_num) == 10 and phone_num.isdigit():
    print("Формат номеру коректний")
else:
    print("Некоректний формат номеру")

# Task 3

print("Який добуток 5 + 3?")
answer = input("Ваша відповідь: ")

if answer == "8":
    print("Чудово, ви молодець!!!")
else:
    print("Нажаль ні, Правильна відповідь 8")

# Task 4

username = "petro"

name_input = input("Введіть ваше ім'я: ")

if name_input.lower() == username:
    print(True)
else:
    print(False)