class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop() if not self.is_empty() else None

    def is_empty(self):
        return len(self._items) == 0


def is_balanced(sequence):
    stack = Stack()
    brackets = {')': '(', ']': '[', '}': '{'}

    for char in sequence:
        if char in "([{":
            stack.push(char)
        elif char in ")]}":
            if stack.is_empty() or stack.pop() != brackets[char]:
                return False

    return stack.is_empty()


# Тестування
test_cases = ["([]{})", "([)]", "{[()]}", "((("]

for tc in test_cases:
    status = "Збалансовано" if is_balanced(tc) else "Не збалансовано"
    print(f"{tc}: {status}")