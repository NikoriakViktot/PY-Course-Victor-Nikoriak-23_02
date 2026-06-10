class CustomIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.items):
            raise StopIteration

        item = self.items[self.index]
        self.index += 1
        return item


class CustomIterable:
    def __init__(self, items):
        self.items = list(items)

    def __iter__(self):
        return CustomIterator(self.items)

    def __getitem__(self, index):
        return self.items[index]


numbers = CustomIterable([10, 20, 30, 40])

assert numbers[0] == 10
assert numbers[2] == 30
assert list(numbers) == [10, 20, 30, 40]

for number in numbers:
    print(number)

print("All assertions passed")
