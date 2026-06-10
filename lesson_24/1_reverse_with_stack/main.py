class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("Cannot pop from an empty stack")

        return self.items.pop()

    def is_empty(self):
        return len(self.items) == 0


def reverse_sequence(sequence):
    stack = Stack()

    for char in sequence:
        stack.push(char)

    reversed_sequence = ""

    while not stack.is_empty():
        reversed_sequence += stack.pop()

    return reversed_sequence


if __name__ == "__main__":
    user_input = input("Enter a sequence of characters: ")
    print(reverse_sequence(user_input))
