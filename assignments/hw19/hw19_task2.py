def in_range(start, end, step=1):
    if step == 0:
        raise ValueError("step argument must not be zero")
    current = start
    if step > 0:
        while current < end:
            yield current
            current += step
    else:
        while current > end:
            yield current
            current += step  # step negative

# Приклад використання
for i in in_range(1, 5):
    print(i)  # 1 2 3 4

for i in in_range(5, 0, -1):
    print(i)  # 5 4 3 2 1