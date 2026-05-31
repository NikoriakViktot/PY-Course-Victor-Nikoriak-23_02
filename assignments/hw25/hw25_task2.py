class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Stack:
    def __init__(self):
        self.head = None

    def push(self, item):
        new_node = Node(item)
        new_node.next = self.head
        self.head = new_node

    def pop(self):
        if not self.head:
            return None
        value = self.head.data
        self.head = self.head.next
        return value

    def peek(self):
        if not self.head:
            return None
        return self.head.data

    def is_empty(self):
        return self.head is None


# Example
if __name__ == "__main__":
    s = Stack()
    s.push(10)
    s.push(20)
    s.push(30)

    print(s.pop())
    print(s.peek())