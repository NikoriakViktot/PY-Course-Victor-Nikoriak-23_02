def arg_rules(type_: type, max_length: int, contains: list):
    def decorator(func):
        def wrapper(arg):
            # перевірка типу
            if not isinstance(arg, type_):
                print("Invalid type")
                return False

            # перевірка довжини
            if len(arg) > max_length:
                print("Too long")
                return False

            # перевірка наявності підрядків
            for item in contains:
                if item not in arg:
                    print(f"Missing required substring: {item}")
                    return False

            return func(arg)
        return wrapper
    return decorator


@arg_rules(type_=str, max_length=15, contains=['05', '@'])
def create_slogan(name: str) -> str:
    return f"{name} drinks pepsi in his brand new BMW!"


# тести
assert create_slogan('johndoe05@gmail.com') is False
assert create_slogan('S@SH05') == 'S@SH05 drinks pepsi in his brand new BMW!'

print(create_slogan('S@SH05'))