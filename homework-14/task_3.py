def arg_rules(type_: type, max_length: int, contains: list):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for arg in args:
                if not isinstance(arg, type_):
                    print(f'Аргумент {arg} має бути типу {type_.__name__}!')
                    return False

                if len(arg) > max_length:
                    print(f'Аргумент {arg} довший за {max_length} символів!')
                    return False

                if not all(c in arg for c in contains):
                    print(f'Аргумент {arg} не містить усіх символів {contains}!')
                    return False
            return func(*args, **kwargs)
        return wrapper
    return decorator


@arg_rules(type_=str, max_length=15, contains=['05', '@'])
def create_slogan(name: str) -> str:
    return f"{name} drinks pepsi in his brand new BMW!"


assert create_slogan('johndoe05@gmail.com') is False

assert create_slogan('S@SH05') == 'S@SH05 drinks pepsi in his brand new BMW!'