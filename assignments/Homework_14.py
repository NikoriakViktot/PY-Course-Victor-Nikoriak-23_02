# Task 1

def logger(func):
    def wrapper(*args, **kwargs):
        # Перетворюємо всі позиційні аргументи на рядки для виведення
        args_str = ", ".join(map(str, args))

        # Виводимо назву функції та її аргументи за допомогою f-рядка
        print(f"{func.__name__} called with {args_str}")

        # Повертаємо результат виконання оригінальної функції
        return func(*args, **kwargs)

    return wrapper


# --- Перевірка роботи ---


@logger
def add(x, y):
    return x + y


@logger
def square_all(*args):
    return [arg**2 for arg in args]


# Виклик функцій (у терміналі з'являться принти логера)
res1 = add(4, 5)  # Виведе: add called with 4, 5
res2 = square_all(1, 2, 3)  # Виведе: square_all called with 1, 2, 3

# Task 2


def stop_words(words: list):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Спочатку отримуємо оригінальний рядок-результат від функції
            result = func(*args, **kwargs)

            # Проходимо по кожному стоп-слову і замінюємо його на зірочку
            for word in words:
                result = result.replace(word, "*")

            return result

        return wrapper

    return decorator


# --- Перевірка роботи за допомогою assert ---


@stop_words(["pepsi", "BMW"])
def create_slogan(name: str) -> str:
    return f"{name} drinks pepsi in his brand new BMW!"


# Перевіряємо, чи спрацювала заміна стоп-слів
assert create_slogan("Steve") == "Steve drinks * in his brand new *!"
print("Task 2: Успішно пройдено!")


# Task 3

def arg_rules(type_: type, max_length: int, contains: list):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Отримуємо цільовий аргумент (працює як для позиційних, так і для іменованих)
            arg = args[0] if args else list(kwargs.values())[0]

            # 1. Перевірка типу даних
            if not isinstance(arg, type_):
                print(f"Validation failed: Argument type must be {type_.__name__}")
                return False

            # 2. Перевірка максимальної довжини
            if len(arg) > max_length:
                print(
                    f"Validation failed: '{arg}' length ({len(arg)}) exceeds maximum of {max_length}"
                )
                return False

            # 3. Перевірка наявності обов'язкових підрядків/символів
            for symbol in contains:
                if symbol not in arg:
                    print(
                        f"Validation failed: Argument must contain '{symbol}'"
                    )
                    return False

            # Якщо всі перевірки пройдено, викликаємо оригінальну функцію
            return func(*args, **kwargs)

        return wrapper

    return decorator


# --- Перевірка роботи за допомогою assert ---


@arg_rules(type_=str, max_length=15, contains=["05", "@"])
def create_slogan(name: str) -> str:
    return f"{name} drinks pepsi in his brand new BMW!"


# 1. Повинно повернути False (довжина рядка > 15)
assert create_slogan("johndoe05@gmail.com") is False

# 2. Повинно успішно виконатись і повернути слоган
assert (
    create_slogan("S@SH05") == "S@SH05 drinks pepsi in his brand new BMW!"
)

print("Task 3: Успішно пройдено!")