from functools import wraps


def arg_rules(type_: type, max_length: int, contains: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            arguments = list(args) + list(kwargs.values())

            for argument in arguments:
                if not isinstance(argument, type_):
                    print(f"Argument must be {type_.__name__}")
                    return False

                if len(argument) > max_length:
                    print(f"Argument length must be less than or equal to {max_length}")
                    return False

                for symbol in contains:
                    if symbol not in argument:
                        print(f"Argument must contain '{symbol}'")
                        return False

            return func(*args, **kwargs)

        return wrapper

    return decorator


@arg_rules(type_=str, max_length=15, contains=["05", "@"])
def create_slogan(name: str) -> str:
    return f"{name} drinks pepsi in his brand new BMW!"


assert create_slogan("johndoe05@gmail.com") is False
assert create_slogan("S@SH05") == "S@SH05 drinks pepsi in his brand new BMW!"

print("All assertions passed")
