# Task 1

def favorite_movie(name):
    print(f"My favorite movie is named {name}")

# Приклад виклику
favorite_movie("Inception")

# Task 2

def make_country(name, capital):
    country = {"name": name, "capital": capital}
    print(country)

# Приклад виклику
make_country("Ukraine", "Kyiv")

# Task 3

def make_operation(operator, *args):
    if operator == '+':
        result = sum(args)
    elif operator == '-':
        result = 0
        for num in args:
            result -= -num if result == 0 else num  # щоб працювало як 5-5-(-10)-(-20)
        # або можна зробити так:
        # result = args[0]
        # for num in args[1:]:
        #     result -= num
    elif operator == '*':
        result = 1
        for num in args:
            result *= num
    else:
        return "Invalid operator"
    return result

# Приклади виклику
print(make_operation('+', 7, 7, 2))       # 16
print(make_operation('-', 5, 5, -10, -20)) # 30
print(make_operation('*', 7, 6))          # 42