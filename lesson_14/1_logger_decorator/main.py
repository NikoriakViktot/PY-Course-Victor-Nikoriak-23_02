from functools import wraps


def logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        arguments = [str(arg) for arg in args]
        arguments.extend(f"{key}={value}" for key, value in kwargs.items())

        print(f"{func.__name__} called with {', '.join(arguments)}")

        return func(*args, **kwargs)

    return wrapper


@logger
def add(x, y):
    return x + y


@logger
def square_all(*args):
    return [arg ** 2 for arg in args]


add(4, 5)
square_all(1, 2, 3, 4)
