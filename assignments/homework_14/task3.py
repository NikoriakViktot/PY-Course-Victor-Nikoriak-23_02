from functools import wraps

def arg_rules(type_: type, max_length: int, contains: list):
    def decorator(func):
        @wraps(func)
        def wrapper(arg):
            if not isinstance(arg, type_):
                print('Invalid type')
                return False
            if len(arg) > max_length:
                print('Too long')
                return False
            for symbol in contains:
                if symbol not in arg:
                    print(f'Missing symbol: {symbol}')
                    return False
            return func(arg)
        return wrapper
    return decorator

@arg_rules(type_=str, max_length=15, contains=['05', '@'])
def create_slogan(name: str) -> str:
    return f'{name} drinks pepsi in his brand new BMW!'

assert create_slogan('johndoe05@gmail.com') is False
assert create_slogan('S@SH05') == 'S@SH05 drinks pepsi in his brand new BMW!'





