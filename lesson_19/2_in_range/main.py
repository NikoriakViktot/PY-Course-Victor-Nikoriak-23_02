def in_range(start, end, step=1):
    if step == 0:
        raise ValueError("Step must not be zero")

    current = start

    if step > 0:
        while current < end:
            yield current
            current += step
    else:
        while current > end:
            yield current
            current += step


assert list(in_range(1, 5)) == [1, 2, 3, 4]
assert list(in_range(1, 10, 2)) == [1, 3, 5, 7, 9]
assert list(in_range(5, 1, -1)) == [5, 4, 3, 2]
assert list(in_range(5, 1, 1)) == []

for number in in_range(1, 5):
    print(number)

print("All assertions passed")
