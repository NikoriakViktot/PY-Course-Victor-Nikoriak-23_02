from functools import wraps

def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        arguments_str = ", ".join(map(str, args))
        print(f"{func.__name__} called with {arguments_str}")
        return func(*args, **kwargs)
    return wrapper


@logger
def add(x, y):
    return x + y


@logger
def square_all(*args):
    return [arg ** 2 for arg in args]


# Перевірка:
add(4, 5)  # Виведе: add called with 4, 5
square_all(1, 2, 3)  # Виведе: square_all called with 1, 2, 3