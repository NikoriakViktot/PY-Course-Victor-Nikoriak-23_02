class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self.is_empty():
            return self._items.pop()
        return None

    def is_empty(self):
        return len(self._items) == 0


def reverse_string(input_str):
    stack = Stack()

    for char in input_str:
        stack.push(char)

    reversed_str = ""
    while not stack.is_empty():
        reversed_str += stack.pop()

    return reversed_str


# Приклад використання:
sequence = input("Введіть послідовність символів: ")
print("Результат:", reverse_string(sequence))