# Task 1

def oops():
    raise IndexError("This is an IndexError")

def handle_error():
    try:
        oops()
    except IndexError:
        print("Caught an IndexError!")

handle_error()

# Task 2

def calculate():
    try:
        a = float(input("Enter number a: "))
        b = float(input("Enter number b: "))

        result = (a ** 2) / b
        print("Result:", result)

    except ValueError:
        print("Error: please enter valid numbers")

    except ZeroDivisionError:
        print("Error: division by zero is not allowed")


calculate()