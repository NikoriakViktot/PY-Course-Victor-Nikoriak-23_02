class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.items:
            return None
        return self.items.pop()

    def is_empty(self):
        return len(self.items) == 0


def reverse_string(text: str) -> str:
    stack = Stack()

    for char in text:
        stack.push(char)

    reversed_text = ""

    while not stack.is_empty():
        reversed_text += stack.pop()

    return reversed_text


# Example
if __name__ == "__main__":
    s = input("Enter string: ")
    print("Reversed:", reverse_string(s))