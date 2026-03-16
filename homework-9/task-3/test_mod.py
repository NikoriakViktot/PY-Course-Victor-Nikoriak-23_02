def make_operation (operator, *args):
    if operator == '+':
        return sum(args)
    elif operator == '-':
        num_oper = args[0]
        for num in args[1:]:
            num_oper -= num
        return num_oper

    else:
        return('Error')

import mymod
mymod.test("mymod.py")