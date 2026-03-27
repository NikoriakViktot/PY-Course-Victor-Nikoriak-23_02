def logger(func):
    def wrapper(*args, **kwargs):
        args_str = ", ".join(str(arg) for arg in args)
        print(f"{func.__name__} called with {args_str}")
        return func(*args, **kwargs)
    return wrapper


@logger
def add(x, y):
    return x + y


@logger
def square_all(*args):
    return [arg ** 2 for arg in args]


# тест
add(4, 5)
square_all(1, 2, 3)