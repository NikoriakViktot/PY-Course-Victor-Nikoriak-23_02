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


def is_balanced(sequence):
    stack = Stack()
    opening_brackets = "({["
    closing_brackets = ")}]"
    brackets = {
        ")": "(",
        "}": "{",
        "]": "[",
    }

    for char in sequence:
        if char in opening_brackets:
            stack.push(char)
        elif char in closing_brackets:
            if stack.is_empty():
                return False

            if stack.pop() != brackets[char]:
                return False

    return stack.is_empty()


if __name__ == "__main__":
    user_input = input("Enter a sequence of characters: ")

    if is_balanced(user_input):
        print("Balanced")
    else:
        print("Not balanced")
