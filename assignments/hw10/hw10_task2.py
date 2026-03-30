def calculate():
    try:
        a = float(input("Enter a: "))
        b = float(input("Enter b: "))
        return (a ** 2) / b

    except ValueError:
        print("Error: invalid number input")
    except ZeroDivisionError:
        print("Error: division by zero")


result = calculate()
if result is not None:
    print("Result:", result)