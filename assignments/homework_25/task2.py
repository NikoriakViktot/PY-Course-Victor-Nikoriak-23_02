class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedStack:
    def __init__(self):
        self._head = None
        self._size = 0

    def push(self, item):
        new_node = Node(item)
        new_node.next = self._head
        self._head = new_node
        self._size += 1

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")

        popped_node = self._head
        self._head = self._head.next
        self._size -= 1
        return popped_node.data

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._head.data

    def is_empty(self):
        return self._head is None

    def size(self):
        return self._size


# Перевірка
if __name__ == "__main__":
    stack = LinkedStack()
    stack.push("Data1")
    stack.push("Data2")

    print(f"Верхній елемент (peek): {stack.peek()}")  # Data2
    print(f"Видалили (pop): {stack.pop()}")  # Data2
    print(f"Нова вершина: {stack.peek()}")  # Data1