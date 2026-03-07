#Task_1

import random

rand_list = []

while len(rand_list) < 10:
    rand_list.append(random.randint(1,100))
print(rand_list)

i = 0
number_max = 0
while i < len(rand_list):
    if rand_list[i] > number_max:
        number_max = rand_list[i]
    i = i + 1

print(f'Найбільше число у списку: {number_max}')