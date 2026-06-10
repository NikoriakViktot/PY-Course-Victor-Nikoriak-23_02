class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class UnsortedList:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return self.head is None

    def add(self, item):
        node = Node(item)
        node.next = self.head
        self.head = node

    def length(self):
        current = self.head
        count = 0

        while current is not None:
            count += 1
            current = current.next

        return count

    def search(self, item):
        current = self.head

        while current is not None:
            if current.data == item:
                return True

            current = current.next

        return False

    def remove(self, item):
        current = self.head
        previous = None

        while current is not None:
            if current.data == item:
                if previous is None:
                    self.head = current.next
                else:
                    previous.next = current.next

                return

            previous = current
            current = current.next

        raise ValueError(f"{item} is not in list")

    def append(self, item):
        node = Node(item)

        if self.is_empty():
            self.head = node
            return

        current = self.head

        while current.next is not None:
            current = current.next

        current.next = node

    def index(self, item):
        current = self.head
        position = 0

        while current is not None:
            if current.data == item:
                return position

            position += 1
            current = current.next

        raise ValueError(f"{item} is not in list")

    def pop(self, position=None):
        if self.is_empty():
            raise IndexError("pop from empty list")

        list_length = self.length()

        if position is None:
            position = list_length - 1

        if position < 0:
            position += list_length

        if position < 0 or position >= list_length:
            raise IndexError("pop index out of range")

        current = self.head
        previous = None
        current_position = 0

        while current_position < position:
            previous = current
            current = current.next
            current_position += 1

        if previous is None:
            self.head = current.next
        else:
            previous.next = current.next

        return current.data

    def insert(self, position, item):
        list_length = self.length()

        if position < 0:
            position = 0

        if position > list_length:
            position = list_length

        node = Node(item)

        if position == 0:
            node.next = self.head
            self.head = node
            return

        current = self.head
        previous = None
        current_position = 0

        while current_position < position:
            previous = current
            current = current.next
            current_position += 1

        previous.next = node
        node.next = current

    def slice(self, start, stop):
        result = UnsortedList()
        current = self.head
        position = 0

        while current is not None:
            if start <= position < stop:
                result.append(current.data)

            if position >= stop:
                break

            position += 1
            current = current.next

        return result

    def to_list(self):
        result = []
        current = self.head

        while current is not None:
            result.append(current.data)
            current = current.next

        return result

    def __repr__(self):
        return f"UnsortedList({self.to_list()})"


linked_list = UnsortedList()

linked_list.append(10)
linked_list.append(20)
linked_list.append(30)

assert linked_list.to_list() == [10, 20, 30]
assert linked_list.index(20) == 1

linked_list.insert(1, 15)
assert linked_list.to_list() == [10, 15, 20, 30]

assert linked_list.pop() == 30
assert linked_list.pop(0) == 10
assert linked_list.to_list() == [15, 20]

sliced_list = linked_list.slice(0, 2)
assert sliced_list.to_list() == [15, 20]

try:
    linked_list.index(100)
except ValueError as error:
    print(error)

print(linked_list)
print(sliced_list)
print("All assertions passed")
