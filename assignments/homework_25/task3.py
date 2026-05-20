class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedQueue:
    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def enqueue(self, item):
        new_node = Node(item)
        if self.is_empty():
            self._head = new_node
        else:
            self._tail.next = new_node
        self._tail = new_node
        self._size += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("dequeue from empty queue")

        popped_data = self._head.data
        self._head = self._head.next

        if self._head is None:
            self._tail = None

        self._size -= 1
        return popped_data

    def is_empty(self):
        return self._head is None

    def size(self):
        return self._size


# Перевірка
if __name__ == "__main__":
    queue = LinkedQueue()
    queue.enqueue("User1")
    queue.enqueue("User2")
    queue.enqueue("User3")

    print(f"Перший у черзі: {queue.dequeue()}")  # User1
    print(f"Наступний у черзі: {queue.dequeue()}")  # User2
    print(f"Розмір черги: {queue.size()}")  # 1