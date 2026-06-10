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

    def get_from_stack(self, element):
        temp_stack = Stack()
        found_element = None

        while not self.is_empty():
            current_element = self.pop()

            if current_element == element:
                found_element = current_element
                break

            temp_stack.push(current_element)

        while not temp_stack.is_empty():
            self.push(temp_stack.pop())

        if found_element is None:
            raise ValueError(f"Element {element} was not found in stack")

        return found_element

    def __repr__(self):
        return f"Stack({self.items})"


class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Cannot dequeue from an empty queue")

        return self.items.pop(0)

    def is_empty(self):
        return len(self.items) == 0

    def get_from_stack(self, element):
        found_element = None
        original_length = len(self.items)

        for _ in range(original_length):
            current_element = self.dequeue()

            if current_element == element and found_element is None:
                found_element = current_element
            else:
                self.enqueue(current_element)

        if found_element is None:
            raise ValueError(f"Element {element} was not found in queue")

        return found_element

    def __repr__(self):
        return f"Queue({self.items})"


stack = Stack()
stack.push(1)
stack.push(2)
stack.push(3)
stack.push(4)

assert stack.get_from_stack(3) == 3
assert stack.items == [1, 2, 4]

queue = Queue()
queue.enqueue(1)
queue.enqueue(2)
queue.enqueue(3)
queue.enqueue(4)

assert queue.get_from_stack(3) == 3
assert queue.items == [1, 2, 4]

print(stack)
print(queue)
print("All assertions passed")
