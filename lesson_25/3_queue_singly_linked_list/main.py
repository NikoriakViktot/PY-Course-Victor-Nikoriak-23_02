class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Queue:
    def __init__(self):
        self.front = None
        self.rear = None
        self._size = 0

    def is_empty(self):
        return self.front is None

    def enqueue(self, item):
        node = Node(item)

        if self.is_empty():
            self.front = node
            self.rear = node
        else:
            self.rear.next = node
            self.rear = node

        self._size += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("dequeue from empty queue")

        item = self.front.data
        self.front = self.front.next
        self._size -= 1

        if self.front is None:
            self.rear = None

        return item

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty queue")

        return self.front.data

    def size(self):
        return self._size

    def to_list(self):
        result = []
        current = self.front

        while current is not None:
            result.append(current.data)
            current = current.next

        return result

    def __repr__(self):
        return f"Queue({self.to_list()})"


queue = Queue()

assert queue.is_empty() is True

queue.enqueue("first")
queue.enqueue("second")
queue.enqueue("third")

assert queue.is_empty() is False
assert queue.size() == 3
assert queue.peek() == "first"
assert queue.dequeue() == "first"
assert queue.dequeue() == "second"
assert queue.dequeue() == "third"
assert queue.is_empty() is True

try:
    queue.dequeue()
except IndexError as error:
    print(error)

print("All assertions passed")
