# Task 3

def make_operation(operator, *numbers):

    if operator == "+":
        return sum(numbers)

    elif operator == "-":
        result = numbers[0]
        for num in numbers[1:]:
            result -= num
        return result

    elif operator == "*":
        result = 1
        for num in numbers:
            result *= num
        return result


# examples
print(make_operation("+", 7, 7, 2))        # 16
print(make_operation("-", 5, 5, -10, -20)) # 30
print(make_operation("*", 7, 6))           # 42