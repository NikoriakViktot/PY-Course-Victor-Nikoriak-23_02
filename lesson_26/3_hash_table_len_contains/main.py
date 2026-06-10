class HashTable:
    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]
        self.length = 0

    def _get_index(self, key):
        return hash(key) % self.size

    def set(self, key, value):
        index = self._get_index(key)
        bucket = self.table[index]

        for item_index, item in enumerate(bucket):
            if item[0] == key:
                bucket[item_index] = (key, value)
                return

        bucket.append((key, value))
        self.length += 1

    def get(self, key):
        index = self._get_index(key)
        bucket = self.table[index]

        for item_key, item_value in bucket:
            if item_key == key:
                return item_value

        raise KeyError(f"Key {key} was not found")

    def delete(self, key):
        index = self._get_index(key)
        bucket = self.table[index]

        for item_index, item in enumerate(bucket):
            if item[0] == key:
                del bucket[item_index]
                self.length -= 1
                return

        raise KeyError(f"Key {key} was not found")

    def __contains__(self, key):
        index = self._get_index(key)
        bucket = self.table[index]

        for item_key, _ in bucket:
            if item_key == key:
                return True

        return False

    def __len__(self):
        return self.length


hash_table = HashTable()

hash_table.set("name", "John")
hash_table.set("age", 25)

assert "name" in hash_table
assert "age" in hash_table
assert "city" not in hash_table
assert len(hash_table) == 2

hash_table.set("name", "Bob")
assert len(hash_table) == 2
assert hash_table.get("name") == "Bob"

hash_table.delete("age")
assert "age" not in hash_table
assert len(hash_table) == 1

print("All assertions passed")
