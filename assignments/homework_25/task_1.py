class Node:
    def __init__(self, init_data):
        self.data = init_data
        self.next = None

    def get_data(self):
        return self.data

    def get_next(self):
        return self.next

    def set_data(self, new_data):
        self.data = new_data

    def set_next(self, new_next):
        self.next = new_next


class UnsortedList:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return self.head is None

    def add(self, item):
        """Додає елемент у початок списку (O(1))."""
        temp = Node(item)
        temp.set_next(self.head)
        self.head = temp

    def size(self):
        current = self.head
        count = 0
        while current is not None:
            count += 1
            current = current.get_next()
        return count

    def search(self, item):
        current = self.head
        found = False
        while current is not None and not found:
            if current.get_data() == item:
                found = True
            else:
                current = current.get_next()
        return found

    def remove(self, item):
        current = self.head
        previous = None
        found = False
        while not found and current is not None:
            if current.get_data() == item:
                found = True
            else:
                previous = current
                current = current.get_next()

        if found:
            if previous is None:
                self.head = current.get_next()
            else:
                previous.set_next(current.get_next())

    # --- НОВІ МЕТОДИ ---

    def append(self, item):
        """Додає елемент у кінець списку (O(n))."""
        new_node = Node(item)
        if self.is_empty():
            self.head = new_node
            return

        current = self.head
        while current.get_next() is not None:
            current = current.get_next()
        current.set_next(new_node)

    def index(self, item):
        """Повертає індекс першого знайденого елемента.
        Якщо елемента немає, піднімає ValueError."""
        current = self.head
        position = 0
        while current is not None:
            if current.get_data() == item:
                return position
            current = current.get_next()
            position += 1
        raise ValueError(f"{item} is not in list")

    def pop(self, pos=None):
        """Видаляє та повертає елемент із позиції pos.
        Якщо pos не вказано, видаляє останній елемент."""
        if self.is_empty():
            raise IndexError("pop from empty list")

        size = self.size()
        if pos is None:
            pos = size - 1

        if pos < 0 or pos >= size:
            raise IndexError("Index out of range")

        current = self.head
        previous = None
        current_pos = 0

        while current_pos < pos:
            previous = current
            current = current.get_next()
            current_pos += 1

        if previous is None:
            self.head = current.get_next()
        else:
            previous.set_next(current.get_next())

        return current.get_data()

    def insert(self, pos, item):
        """Вставляє елемент item на позицію pos."""
        size = self.size()
        if pos < 0 or pos > size:
            raise IndexError("Index out of range")

        if pos == 0:
            self.add(item)
            return

        new_node = Node(item)
        current = self.head
        previous = None
        current_pos = 0

        while current_pos < pos:
            previous = current
            current = current.get_next()
            current_pos += 1

        previous.set_next(new_node)
        new_node.set_next(current)

    def slice(self, start, stop):
        """Повертає новий UnsortedList, що містить копію елементів
        від start (включно) до stop (не включно)."""
        new_list = UnsortedList()
        if start >= stop or self.is_empty():
            return new_list

        current = self.head
        current_pos = 0

        # Спочатку доходимо до стартової позиції
        while current is not None and current_pos < start:
            current = current.get_next()
            current_pos += 1

        # Збираємо елементи для зрізу
        # Щоб зберегти правильний порядок при додаванні через append:
        while current is not None and current_pos < stop:
            new_list.append(current.get_data())
            current = current.get_next()
            current_pos += 1

        return new_list

    def __str__(self):
        """Допоміжний метод для зручного виведення списку на екран."""
        elements = []
        current = self.head
        while current is not None:
            elements.append(str(current.get_data()))
            current = current.get_next()
        return "[" + ", ".join(elements) + "]"
