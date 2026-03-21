# Task 1

import random
numbers = []
i = 0
while i < 10:
    num = random.randint(1, 100)
    numbers.append(num)
    i += 1
largest = numbers[0]
i = 0
while i < len(numbers):
    if numbers[i] > largest:
        largest = numbers[i]
    i += 1
print("Numbers:", numbers)
print("Largest number:", largest)

# Task 2

import random
list1 = []
list2 = []
i = 0
while i < 10:
    list1.append(random.randint(1, 10))
    list2.append(random.randint(1, 10))
    i += 1
common = []
i = 0
while i < len(list1):
    j = 0
    while j < len(list2):
        if list1[i] == list2[j] and list1[i] not in common:
            common.append(list1[i])
        j += 1
    i += 1
print("List 1:", list1)
print("List 2:", list2)
print("Common numbers:", common)

# Task 3

numbers = []
i = 1
while i <= 100:
    numbers.append(i)
    i += 1
result = []
i = 0
while i < len(numbers):
    if numbers[i] % 7 == 0 and numbers[i] % 5 != 0:
        result.append(numbers[i])
    i += 1
print(result)