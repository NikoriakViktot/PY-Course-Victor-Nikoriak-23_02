class Stack:
    def __init__(self):
        self._items = []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop() if not self.is_empty() else None

    def is_empty(self):
        return len(self._items) == 0

    def get_from_stack(self, e):
        temp_stack = []
        found_element = None

        while not self.is_empty():
            current = self.pop()
            if current == e:
                found_element = current
                break
            temp_stack.append(current)

        while temp_stack:
            self.push(temp_stack.pop())

        if found_element is None:
            raise ValueError(f"Елемент '{e}' не знайдено у стеку")
        return found_element


class Queue:
    def __init__(self):
        self._items = []

    def enqueue(self, item):
        self._items.insert(0, item)

    def dequeue(self):
        return self._items.pop() if not self.is_empty() else None

    def is_empty(self):
        return len(self._items) == 0

    def size(self):
        return len(self._items)

    def get_from_queue(self, e):
        found_element = None
        for _ in range(self.size()):
            current = self.dequeue()
            if current == e:
                found_element = current
            else:
                self.enqueue(current)

        if found_element is None:
            raise ValueError(f"Елемент '{e}' не знайдено у черзі")
        return found_element


# Перевірка
if __name__ == "__main__":
    # Перевірка Стека
    s = Stack()
    for x in [10, 20, 30, 40]: s.push(x)
    print(f"Знайдено у стеку: {s.get_from_stack(20)}")

    # Перевірка Черги
    q = Queue()
    for x in ["A", "B", "C"]: q.enqueue(x)
    print(f"Знайдено у черзі: {q.get_from_queue('B')}")