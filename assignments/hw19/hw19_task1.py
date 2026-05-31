def with_index(iterable, start=0):
    idx = start
    for item in iterable:
        yield idx, item
        idx += 1

# Приклад використання
items = ["apple", "banana", "cherry"]
for i, val in with_index(items, 1):
    print(i, val)

# Output:
# 1 apple
# 2 banana
# 3 cherry