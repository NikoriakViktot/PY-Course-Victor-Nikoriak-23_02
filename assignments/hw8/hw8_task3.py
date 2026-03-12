# Task 3: Simple Calculator

def make_operation(operator, *args):
    """Perform a simple arithmetic operation ('+', '-', '*') on all numbers."""
    if operator == "+":
        result = sum(args)
    elif operator == "-":
        # Віднімаємо всі аргументи послідовно: a - b - c - d ...
        result = args[0]
        for num in args[1:]:
            result -= num
    elif operator == "*":
        result = 1
        for num in args:
            result *= num
    else:
        raise ValueError("Unsupported operator. Use '+', '-', or '*'.")
    return result

# Приклади викликів
print(make_operation("+", 7, 7, 2))        # 16
print(make_operation("-", 5, 5, -10, -20)) # 30
print(make_operation("*", 7, 6))           # 42