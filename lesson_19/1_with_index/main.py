def with_index(iterable, start=0):
    index = start

    for item in iterable:
        yield index, item
        index += 1


colors = ["red", "green", "blue"]

assert list(with_index(colors)) == [(0, "red"), (1, "green"), (2, "blue")]
assert list(with_index(colors, start=5)) == [(5, "red"), (6, "green"), (7, "blue")]

for index, color in with_index(colors, start=1):
    print(index, color)

print("All assertions passed")
