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