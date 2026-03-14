#Task_3

def make_operation(parametr, *args):
    x = None
    for arg in args:
        if x is None:
            x = arg
        elif parametr == '-':
            x -= arg
        elif parametr == '+':
            x += arg
        elif parametr == '*':
            x *= arg
    print(x)


make_operation('*', 7, 6)
