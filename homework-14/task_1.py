from functools import wraps

def dec_func(func):
    @wraps(func)
    def wrapper(*args):
        print(f'{func.__name__}{args}')
        return func(*args)
    return wrapper

@dec_func
def test_func(*args):
    return args

test_func(5,8,2,5)