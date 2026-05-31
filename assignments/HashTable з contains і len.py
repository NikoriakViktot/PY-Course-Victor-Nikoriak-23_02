class HashTable:
    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]
        self.count = 0

    def _hash(self, key):
        return hash(key) % self.size

    def insert(self, key, value):
        index = self._hash(key)

        for item in self.table[index]:
            if item[0] == key:
                item[1] = value
                return

        self.table[index].append([key, value])
        self.count += 1

    def __contains__(self, key):
        index = self._hash(key)

        for item in self.table[index]:
            if item[0] == key:
                return True
        return False

    def __len__(self):
        return self.count

    def get(self, key):
        index = self._hash(key)

        for item in self.table[index]:
            if item[0] == key:
                return item[1]

        raise KeyError("Key not found")


# Example
if __name__ == "__main__":
    ht = HashTable()

    ht.insert("a", 1)
    ht.insert("b", 2)

    print("a" in ht)     # True
    print(len(ht))       # 2
    print(ht.get("b"))   # 2