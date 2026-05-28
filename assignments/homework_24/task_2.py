class Stack:

    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def is_empty(self):
        return len(self.items) == 0


def brackets_balanced():
    string_with_brackets = input("Введіть строку з дужками: ")
    stack = Stack()
    dict_balanced = {')': '(', ']': '[', '}': '{'}
    for char in string_with_brackets:
        if char in '([{':
            stack.push(char)
        elif char in ')]}':
            if stack.is_empty():
                return False
            elif stack.pop() != dict_balanced[char]:
                return False

    return stack.is_empty()

if __name__ == '__main__':
    if brackets_balanced():
        print('Дужки збалансовані!')
    else:
        print('Помилка! Дужки не збалансовані!')
