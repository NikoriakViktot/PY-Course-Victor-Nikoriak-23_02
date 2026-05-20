from functools import wraps


class TypeDecorators:

    @staticmethod
    def to_int(func):
        @wraps(func)
        def wrapper(arg):
            result = func(arg)
            try:
                return int(result)
            except (ValueError, TypeError):
                return result

        return wrapper

    @staticmethod
    def to_str(func):
        @wraps(func)
        def wrapper(arg):
            result = func(arg)
            return str(result)

        return wrapper

    @staticmethod
    def to_bool(func):
        @wraps(func)
        def wrapper(arg):
            result = func(arg)
            if result.lower() in ('false', '', '0'):
                return False
            return bool(result)

        return wrapper

    @staticmethod
    def to_float(func):
        @wraps(func)
        def wrapper(arg):
            result = func(arg)
            try:
                return float(result)
            except (ValueError, TypeError):
                return result

        return wrapper



@TypeDecorators.to_int
def do_nothing(string: str):
    return string


@TypeDecorators.to_bool
def do_something(string: str):
    return string

try:
    assert do_nothing('25') == 25
except AssertionError:
    print('Функція do_nothing провалила тестування!')

try:
    assert do_something('True') is True
except AssertionError:
    print('Функція do_something провалила тестування!')

print("Тест завершено!")

    