def add(a,b):
    print(a+b)

def sub(a,b):
    print(a-b)

def mul(a,b):
    print(a*b)

def div(a,b):
    print(a/b)

def default(*args, **kwargs):
    print('Unknown command')

def calc(operator):
    command = {
        '+': add,
        '-': sub,
        '*': mul,
        '/': div
    }
    return command.get(operator, default)

calc('!')(6, 8)