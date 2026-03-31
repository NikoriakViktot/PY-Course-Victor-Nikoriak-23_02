import functools

def decorator(func):
    @functools.wraps(func)
    def wrapper(*args):
        func(*args)
        return print(f"{func.__name__}{tuple(args)}")
    return wrapper

@decorator
def our_function(x, y):
    return x + y

our_function(4,5)