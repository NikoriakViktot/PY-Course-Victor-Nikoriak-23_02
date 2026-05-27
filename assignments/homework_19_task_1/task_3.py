class MyIterator:

    def __init__(self, *args):
        self.iterable = list(args)
        self.index = 0

    def __getitem__(self, index):
        return self.iterable[index]

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.iterable):
            result = self.iterable[self.index]
            self.index += 1
            return result
        raise StopIteration


my_collection = MyIterator('Картопля', 'Яблуко', 'Банан', 'Томат')

for item in my_collection:
    print(item)


print(my_collection[3])
print(my_collection[1])