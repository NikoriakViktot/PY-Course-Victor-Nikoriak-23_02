#Task1

import random #импортируем модуль random

number = [] # создаем пустой список
i = 0
while i < 10: # создаем цикл while
    number.append(random.randint(0, 10)) #генерируем 10 случайных чисел
    i += 1
max_number = number[0] # создаем новый список и берем первое число из списка
j = 1 # берем новую переменную и берем 1 вместо 0 для избежания проверки одного и того числа
while j < len(number): # проходимся по всей длине списка
    if number[j] > max_number:
        max_number = number[j]
    j += 1
print(number)
print(max_number)


#Task2

import random
number1 = [] # создаем пустой список №1
number2 = [] # создаем пустой список №2
i = 0
while i < 10:
    number1.append(random.randint(1,10)) # генерируем случайные числа для списка №1
    number2.append(random.randint(1,10)) # генерируем случайные числа для списка №2
    i += 1
number3 = [] # # создаем пустой список№
j = 0
while j < len(number1): # циклом while проходимся по длине списка №1
    if number1[j] in number2 and number1[j] not in number3: # проверяем списки на наличие дубликатов
        number3.append(number1[j]) # добавляем проверенные числа в список 3
    j += 1 #добавляем переменную для того чтоб цикл не вошел в бесконечный цикл (извините за тавтологию)
print(number1)
print(number2)
print(number3)
