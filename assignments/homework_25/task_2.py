class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedStack:
    def __init__(self):
        self._top = None  # Верхівка стека (head списку)
        self._size = 0  # Зберігаємо розмір для швидкого доступу за O(1)

    def is_empty(self):
        """Перевіряє, чи порожній стек. Складність: O(1)"""
        return self._top is None

    def size(self):
        """Повертає кількість елементів у стеку. Складність: O(1)"""
        return self._size

    def push(self, item):
        """Додає елемент на верхівку стека. Складність: O(1)"""
        new_node = Node(item)
        new_node.next = self._top  # Новий вузол посилається на стару верхівку
        self._top = new_node  # Тепер новий вузол стає верхівкою
        self._size += 1

    def pop(self):
        """Видаляє та повертає елемент з верхівки стека. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("pop from empty stack")

        popped_node = self._top  # Запам'ятовуємо поточну верхівку
        self._top = self._top.next  # Зміщуємо верхівку на наступний елемент
        self._size -= 1
        return popped_node.data  # Повертаємо дані видаленого вузла

    def peek(self):
        """Повертає елемент на верхівці стека без його видалення. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._top.data

    def __str__(self):
        """Допоміжний метод для візуалізації стека (від верхівки до низу)."""
        elements = []
        current = self._top
        while current is not None:
            elements.append(str(current.data))
            current = current.next
        return " -> ".join(elements) + " -> None" if elements else "Stack is empty"
