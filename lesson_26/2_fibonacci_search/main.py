def fibonacci_search(numbers, target):
    size = len(numbers)
    fib_previous_previous = 0
    fib_previous = 1
    fib_current = fib_previous + fib_previous_previous

    while fib_current < size:
        fib_previous_previous = fib_previous
        fib_previous = fib_current
        fib_current = fib_previous + fib_previous_previous

    offset = -1

    while fib_current > 1:
        index = min(offset + fib_previous_previous, size - 1)

        if numbers[index] < target:
            fib_current = fib_previous
            fib_previous = fib_previous_previous
            fib_previous_previous = fib_current - fib_previous
            offset = index
        elif numbers[index] > target:
            fib_current = fib_previous_previous
            fib_previous = fib_previous - fib_previous_previous
            fib_previous_previous = fib_current - fib_previous
        else:
            return index

    if fib_previous and offset + 1 < size and numbers[offset + 1] == target:
        return offset + 1

    return -1


numbers = [1, 3, 5, 7, 9, 11, 13, 15]

assert fibonacci_search(numbers, 1) == 0
assert fibonacci_search(numbers, 9) == 4
assert fibonacci_search(numbers, 15) == 7
assert fibonacci_search(numbers, 8) == -1

print("All assertions passed")
