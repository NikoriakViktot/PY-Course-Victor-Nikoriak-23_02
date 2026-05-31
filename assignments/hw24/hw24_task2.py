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


def is_balanced(sequence: str) -> bool:
    stack = Stack()
    pairs = {')': '(', ']': '[', '}': '{'}

    for char in sequence:
        if char in "([{":
            stack.push(char)
        elif char in ")]}":
            if stack.is_empty():
                return False
            if stack.pop() != pairs[char]:
                return False

    return stack.is_empty()


# Example
if __name__ == "__main__":
    s = input("Enter sequence: ")
    print("Balanced:", is_balanced(s))