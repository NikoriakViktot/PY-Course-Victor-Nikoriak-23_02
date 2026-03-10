# Task 1
import random
numbers = []
i = 0
while i < 10:
    num = random.randint(1,100)
    numbers.append(num)
    i += 1

print(numbers)

max_number = numbers[0]
i = 1
while i < 10:
    if numbers[i] > max_number:
        max_number = numbers[i]
    i += 1

print(max_number)

#Task 2
import random
first_list = []
i = 0
while i < 10:
    first_list.append(random.randint(1,10))
    i += 1

print(first_list)

second_list = []
i = 0
while i < 10:
    second_list.append(random.randint(1,10))
    i += 1

print(second_list)

common_list = []
i = 0
while i < 10:
    if first_list[i] in second_list and first_list[i] not in common_list:
        common_list.append(first_list[i])
    i += 1

print(common_list)

#Task 3

numbers = []
i = 1
while i < 100:
    numbers.append(i)
    i += 1

result = []
i = 0
while i < len(numbers):
    if numbers[i] % 7  == 0 and numbers[i] % 5 != 0:
        result.append(numbers[i])
    i += 1

print(result)
