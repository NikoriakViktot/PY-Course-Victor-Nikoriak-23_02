
## Task 1: Розширення `UnsortedList`

Припустимо, що базовий `UnsortedList` має стандартний вузол `Node` та зберігає посилання на `head` (голову списку). Додамо методи `append`, `index`, `pop`, `insert` та `slice`.

Python

```
class Node:
    def __init__(self, init_data):
        self.data = init_data
        self.next = None

class UnsortedList:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return self.head is None

    def add(self, item):
        """Додає елемент на початок списку (O(1))."""
        temp = Node(item)
        temp.next = self.head
        self.head = temp

    def size(self):
        current = self.head
        count = 0
        while current is not None:
            count += 1
            current = current.next
        return count

    # --- Твоє завдання починається тут ---

    def append(self, item):
        """Додає елемент у кінець списку. Складність: O(n)"""
        new_node = Node(item)
        if self.is_empty():
            self.head = new_node
            return
        
        current = self.head
        while current.next is not None:
            current = current.next
        current.next = new_node

    def index(self, item):
        """Повертає індекс елемента. Якщо не знайдено — ValueError."""
        current = self.head
        idx = 0
        while current is not None:
            if current.data == item:
                return idx
            current = current.next
            idx += 1
        raise ValueError(f"{item} is not in list")

    def pop(self, pos=None):
        """Видаляє та повертає елемент за індексом. 
        За замовчуванням видаляє останній елемент.
        """
        if self.is_empty():
            raise IndexError("pop from empty list")
            
        size = self.size()
        if pos is None:
            pos = size - 1
            
        if pos < 0 or pos >= size:
            raise IndexError("list index out of range")

        current = self.head
        previous = None
        idx = 0

        # Якщо видаляємо перший елемент (head)
        if pos == 0:
            data = self.head.data
            self.head = self.head.next
            return data

        # Шукаємо потрібну позицію
        while idx < pos:
            previous = current
            current = current.next
            idx += 1

        data = current.data
        previous.next = current.next
        return data

    def insert(self, pos, item):
        """Вставляє елемент на вказану позицію."""
        size = self.size()
        if pos < 0 or pos > size:
            raise IndexError("list index out of range")

        if pos == 0:
            self.add(item)
            return

        new_node = Node(item)
        current = self.head
        previous = None
        idx = 0

        while idx < pos:
            previous = current
            current = current.next
            idx += 1

        new_node.next = current
        previous.next = new_node

    def slice(self, start, stop):
        """Повертає копію зрізу списку від start (включно) до stop (не включно)."""
        size = self.size()
        # Базова валідація меж
        if start < 0 or stop > size or start > stop:
            raise IndexError("Invalid slice indices")

        new_list = UnsortedList()
        current = self.head
        idx = 0

        # Масив для тимчасового збереження елементів зрізу
        # (щоб зберегти правильний порядок при додаванні через .add чи .append)
        temp_data = []

        while current is not None and idx < stop:
            if idx >= start:
                temp_data.append(current.data)
            current = current.next
            idx += 1

        # Заповнюємо новий список у правильному порядку
        for item in reversed(temp_data):
            new_list.add(item) # або можна використати новий append

        return new_list

    def __str__(self):
        """Для зручного дебагу."""
        res = []
        curr = self.head
        while curr:
            res.append(str(curr.data))
            curr = curr.next
        return "[" + " -> ".join(res) + "]"
```

## Task 2: Реалізація Stack через Singly Linked List

У стеку діє принцип **LIFO** (Last In, First Out). Щоб операції `push` та `pop` виконувалися за блискавичні **O(1)**, ми будемо додавати та видаляти елементи з **голови (head)** зв'язаного списку.

Python

```
class StackNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class StackLinkedList:
    def __init__(self) -> None:
        self.head = None
        self._size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def push(self, item) -> None:
        """Додає елемент на вершину стеку. Складність: O(1)"""
        new_node = StackNode(item)
        new_node.next = self.head
        self.head = new_node
        self._size += 1

    def pop(self):
        """Видаляє та повертає елемент з вершини стеку. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        
        popped_node = self.head
        self.head = self.head.next
        self._size -= 1
        return popped_node.data

    def peek(self):
        """Повертає верхній елемент без його видалення. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.head.data

    def size(self) -> int:
        return self._size
```

## Task 3: Реалізація Queue через Singly Linked List

В черзі діє принцип **FIFO** (First In, First Out). Щоб і додавання (`enqueue`), і видалення (`dequeue`) працювали за **O(1)**, нам потрібно зберігати посилання як на початок списку (`head`), так і на його кінець (`tail`).

- **Enqueue** робимо в хвіст (`tail`).
    
- **Dequeue** забираємо з голови (`head`).
    

Python

```
class QueueNode:
    def __init__(self, data):
        self.data = data
        self.next = None

class QueueLinkedList:
    def __init__(self) -> None:
        self.head = None
        self.tail = None
        self._size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def enqueue(self, item) -> None:
        """Додає елемент у кінець черги. Складність: O(1)"""
        new_node = QueueNode(item)
        if self.is_empty():
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1

    def dequeue(self):
        """Видаляє та повертає елемент з початку черги. Складність: O(1)"""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        
        dequeued_node = self.head
        self.head = self.head.next
        
        # Якщо після видалення черга стала порожньою
        if self.head is None:
            self.tail = None
            
        self._size -= 1
        return dequeued_node.data

    def size(self) -> int:
        return self._size
```