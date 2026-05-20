class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class UnsortedList:
    def __init__(self):
        self.head = None

    def add(self, item):
        temp = Node(item)
        temp.next = self.head
        self.head = temp

    def append(self, item):
        temp = Node(item)
        if self.head is None:
            self.head = temp
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = temp

    def index(self, item):
        curr = self.head
        idx = 0
        while curr:
            if curr.data == item:
                return idx
            curr = curr.next
            idx += 1
        raise ValueError("Item not found")

    def pop(self, pos=None):
        if self.head is None: raise IndexError("List is empty")

        curr, prev, idx = self.head, None, 0
        target = pos if pos is not None else (self._get_size() - 1)

        while idx < target and curr:
            prev, curr = curr, curr.next
            idx += 1

        if prev is None:
            self.head = curr.next
        else:
            prev.next = curr.next
        return curr.data

    def insert(self, pos, item):
        if pos == 0:
            self.add(item)
        else:
            temp, curr, idx = Node(item), self.head, 0
            while idx < pos - 1:
                curr = curr.next
                idx += 1
            temp.next = curr.next
            curr.next = temp

    def slice(self, start, stop):
        new_list = UnsortedList()
        curr, idx = self.head, 0
        while curr and idx < stop:
            if idx >= start:
                new_list.append(curr.data)
            curr = curr.next
            idx += 1
        return new_list

    def _get_size(self):
        curr, count = self.head, 0
        while curr:
            count += 1
            curr = curr.next
        return count