class CustomIterable:
    def __init__(self, data):
        self._data = list(data)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._data):
            raise StopIteration
        val = self._data[self._index]
        self._index += 1
        return val

    def __getitem__(self, index):
        return self._data[index]

# Приклад використання
ci = CustomIterable(["a", "b", "c"])

# for-in loop
for item in ci:
    print(item)

# Доступ по індексу
print(ci[0])  # a
print(ci[2])  # c