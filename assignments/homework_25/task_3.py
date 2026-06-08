class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedQueue:
    def __init__(self):
        self._head = None  # Початок черги (звідси видаляємо елементи)
        self._tail = None  # Кінець черги (сюди додаємо елементи)
        self._size = 0  # Зберігаємо розмір черги

    def is_empty(self):
        """Перевіряє, чи порожня черга. Складність: O(1)"""
        return self._head is None

    def size(self):
        """Повертає кількість елементів у черзі. Складність: O(1)"""
        return self._size

    def enqueue(self, item):
        """Додає елемент у кінець черги. Складність: O(1)"""
        new_node = Node(item)
        if self.is_empty():
            self._head = new_node  # Якщо черга порожня, новий вузол стає і початком,
            self._tail = new_node  # і кінцем черги.
        else:
            self._tail.next = new_node  # Прив'язуємо новий вузол після поточного хвоста
            self._tail = new_node  # Оновлюємо вказівник хвоста на новий вузол
        self._size += 1

    def dequeue(self):
        """Видаляє та повертає елемент з початку черги. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")

        removed_node = self._head  # Запам'ятовуємо перший вузол
        self._head = self._head.next  # Зміщуємо голову черги на наступний елемент

        # Якщо після видалення черга стала порожньою, занулюємо і tail
        if self._head is None:
            self._tail = None

        self._size -= 1
        return removed_node.data  # Повертаємо дані видаленого вузла

    def peek(self):
        """Повертає перший елемент у черзі без його видалення. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("peek from empty queue")
        return self._head.data

    def __str__(self):
        """Допоміжний метод для візуалізації черги (від голови до хвоста)."""
        elements = []
        current = self._head
        while current is not None:
            elements.append(str(current.data))
            current = current.next
        return "Head -> " + " -> ".join(elements) + " -> Tail" if elements else "Queue is empty"
