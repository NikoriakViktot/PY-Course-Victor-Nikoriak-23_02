#Task1

import random
number = random.randint(1, 10)
user_input = input("введите число")
if user_input.isdigit():
    guess = int(user_input)
    if 1 <= guess <= 10:
        if guess == number:
            print("Юху вы угадали")
        elif guess < number:
            print (f"число больше = {number}")
        elif guess > number:
            print (f"число меньше = {number}")
        else:
            print(f"ошибка числа = {number}")
    else:
        print("введите число от 1 до 10")
else:
    print("немного не так, без пробела")

#Task2

name = input("введите ваше имя:")
age = int(input("введите ваш возраст:"))
new_age = age + 1
print(f"Привет {name} в следующем году тебе будет {new_age}")