class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.items:
            return None
        return self.items.pop()

    def get_from_stack(self, value):
        temp = Stack()
        found = None

        while self.items:
            item = self.pop()
            if item == value and found is None:
                found = item
                break
            temp.push(item)

        while not temp.is_empty():
            self.push(temp.pop())

        if found is None:
            raise ValueError(f"{value} not found in stack")

        return found


class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.items:
            return None
        return self.items.pop(0)

    def get_from_stack(self, value):
        size = len(self.items)
        found = None

        for _ in range(size):
            item = self.dequeue()
            if item == value and found is None:
                found = item
            self.enqueue(item)

        if found is None:
            raise ValueError(f"{value} not found in queue")

        return found


# Example
if __name__ == "__main__":
    s = Stack()
    s.push(1)
    s.push(2)
    s.push(3)

    print("Found in stack:", s.get_from_stack(2))

    q = Queue()
    q.enqueue(10)
    q.enqueue(20)
    q.enqueue(30)

    print("Found in queue:", q.get_from_stack(20))