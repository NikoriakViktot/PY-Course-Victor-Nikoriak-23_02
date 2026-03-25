try:
    def func():
        a = int(input('Please enter the first number '))
        b = int(input('Please enter the second number '))
        return a**2 / b
    print(f"Calculation result: {func()}")
except ValueError:
    print('This is not a number')
except ZeroDivisionError:
    print('This is zero')