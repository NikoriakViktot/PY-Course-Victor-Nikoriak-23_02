from functools import wraps


class TypeDecorators:
    @staticmethod
    def to_int(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return int(func(*args, **kwargs))

        return wrapper

    @staticmethod
    def to_str(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return str(func(*args, **kwargs))

        return wrapper

    @staticmethod
    def to_bool(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if isinstance(result, str):
                return result.lower() in ("true", "1", "yes")

            return bool(result)

        return wrapper

    @staticmethod
    def to_float(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return float(func(*args, **kwargs))

        return wrapper


@TypeDecorators.to_int
def do_nothing(string: str):
    return string


@TypeDecorators.to_bool
def do_something(string: str):
    return string


@TypeDecorators.to_str
def get_number():
    return 100


@TypeDecorators.to_float
def get_float_number():
    return "15.5"


assert do_nothing("25") == 25
assert do_something("True") is True
assert get_number() == "100"
assert get_float_number() == 15.5

print("All assertions passed")
