class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class UnsortedList:
    def __init__(self):
        self.head = None

    def append(self, item):
        new_node = Node(item)
        if not self.head:
            self.head = new_node
            return

        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    def index(self, item):
        current = self.head
        i = 0
        while current:
            if current.data == item:
                return i
            current = current.next
            i += 1
        raise ValueError("Item not found")

    def pop(self, pos=None):
        if self.head is None:
            raise IndexError("Pop from empty list")

        current = self.head

        if pos is None:
            if not current.next:
                value = current.data
                self.head = None
                return value

            while current.next.next:
                current = current.next

            value = current.next.data
            current.next = None
            return value

        if pos == 0:
            value = self.head.data
            self.head = self.head.next
            return value

        prev = None
        i = 0
        while current and i < pos:
            prev = current
            current = current.next
            i += 1

        if current is None:
            raise IndexError("Index out of range")

        prev.next = current.next
        return current.data

    def insert(self, pos, item):
        new_node = Node(item)

        if pos == 0:
            new_node.next = self.head
            self.head = new_node
            return

        current = self.head
        i = 0

        while current and i < pos - 1:
            current = current.next
            i += 1

        if current is None:
            raise IndexError("Index out of range")

        new_node.next = current.next
        current.next = new_node

    def slice(self, start, stop):
        result = UnsortedList()

        current = self.head
        i = 0

        while current and i < start:
            current = current.next
            i += 1

        while current and i < stop:
            result.append(current.data)
            current = current.next
            i += 1

        return result

    def display(self):
        current = self.head
        while current:
            print(current.data, end=" -> ")
            current = current.next
        print("None")


# Example
if __name__ == "__main__":
    ul = UnsortedList()
    ul.append(1)
    ul.append(2)
    ul.append(3)
    ul.append(4)

    ul.display()

    print("Index of 3:", ul.index(3))

    ul.insert(2, 99)
    ul.display()

    ul.pop(1)
    ul.display()

    sliced = ul.slice(1, 3)
    sliced.display()