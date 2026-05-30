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


def reverse():
    input_str = input('Введіть строку: ')
    stack = Stack()
    for char in input_str:
        stack.push(char)

    reversed_str = ""
    while not stack.is_empty():
        reversed_str += stack.pop()

    print("Відповідь: ", reversed_str)

if __name__ == '__main__':
    reverse()