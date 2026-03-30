import random

numbers = []
i = 0

while i < 10:
    num = random.randint(1, 100)
    numbers.append(num)
    i += 1

print("Generated numbers:", numbers)

largest = numbers[0]
i = 1

while i < len(numbers):
    if numbers[i] > largest:
        largest = numbers[i]
    i += 1

print("Largest number:", largest)