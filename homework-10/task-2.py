def numbers():
    a = int(input('Введи число a: '))
    b = int(input('Введи число b: '))
    result = (a**2)/b
    return result

try:
    print(numbers())
except ZeroDivisionError:
    print('На 0 ділити не можна')
except ValueError:
    print('Треба ввести число')