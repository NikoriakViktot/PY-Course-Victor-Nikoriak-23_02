def get_squared_a_divided_by_b():
    try:
        a = float(input("Enter a: "))
        b = float(input("Enter b: "))
        return a ** 2 / b
    except ValueError:
        print("Values must be numbers")
    except ZeroDivisionError:
        print("Cannot divide by zero")


result = get_squared_a_divided_by_b()

if result is not None:
    print(result)
