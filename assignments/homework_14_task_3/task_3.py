import functools

def arg_rules(type_: type, max_length: int, contains: list):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(arg):
            if type_ != type(arg):
                return print("False! Type is wrong!")
            elif len(arg) > max_length:
                return print("False! Length is wrong!")
            else:
                for i in contains:
                    if i not in arg:
                        return print(f"False! element - {i}  missing!")
            return print(func(arg))
        return wrapper
    return decorator

@arg_rules(type_=str, max_length=15, contains=["@", "05"])
def create_slogan(name: str) -> str:
    return f"{name} drinks pepsi in his brand new BMW!"

create_slogan("@fhjdk05")