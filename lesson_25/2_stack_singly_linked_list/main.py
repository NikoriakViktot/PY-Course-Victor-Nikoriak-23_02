class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Stack:
    def __init__(self):
        self.top = None
        self._size = 0

    def is_empty(self):
        return self.top is None

    def push(self, item):
        node = Node(item)
        node.next = self.top
        self.top = node
        self._size += 1

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")

        item = self.top.data
        self.top = self.top.next
        self._size -= 1

        return item

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")

        return self.top.data

    def size(self):
        return self._size

    def to_list(self):
        result = []
        current = self.top

        while current is not None:
            result.append(current.data)
            current = current.next

        return result

    def __repr__(self):
        return f"Stack({self.to_list()})"


stack = Stack()

assert stack.is_empty() is True

stack.push("first")
stack.push("second")
stack.push("third")

assert stack.is_empty() is False
assert stack.size() == 3
assert stack.peek() == "third"
assert stack.pop() == "third"
assert stack.pop() == "second"
assert stack.pop() == "first"
assert stack.is_empty() is True

try:
    stack.pop()
except IndexError as error:
    print(error)

print("All assertions passed")
