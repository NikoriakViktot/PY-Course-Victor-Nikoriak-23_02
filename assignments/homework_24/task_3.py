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

    def get_from_stack(self, e):
        temp_stack = Stack()
        found_element = None

        while not self.is_empty():
            current = self.pop()
            if current == e:
                found_element = current
                break
            else:
                temp_stack.push(current)

        while not temp_stack.is_empty():
            self.push(temp_stack.pop())

        if found_element is None:
            raise ValueError(f"Елемент '{e}' не знайдено у стеку.")

        return found_element