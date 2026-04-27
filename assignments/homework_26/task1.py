def binary_search_rec(arr, low, high, x):
    if high >= low:
        mid = (high + low) // 2

        if arr[mid] == x:
            return mid
        elif arr[mid] > x:
            return binary_search_rec(arr, low, mid - 1, x)
        else:
            return binary_search_rec(arr, mid + 1, high, x)
    else:
        return -1

def fibonacci_search(arr, x):
    n = len(arr)
    fib2, fib1 = 0, 1
    fibM = fib2 + fib1

    while (fibM < n):
        fib2 = fib1
        fib1 = fibM
        fibM = fib2 + fib1

    offset = -1

    while (fibM > 1):
        i = min(offset + fib2, n - 1)
        if (arr[i] < x):
            fibM, fib1 = fib1, fib2
            fib2 = fibM - fib1
            offset = i
        elif (arr[i] > x):
            fibM = fib2
            fib1 = fib1 - fib2
            fib2 = fibM - fib1
        else:
            return i

    if (fib1 and offset < n - 1 and arr[offset + 1] == x):
        return offset + 1
    return -1

# Перевірка
if __name__ == "__main__":
    data = [2, 3, 4, 10, 40]
    target = 10

    print(f"Binary Search: Index of {target} is {binary_search_rec(data, 0, len(data) - 1, target)}")
    print(f"Fibonacci Search: Index of {target} is {fibonacci_search(data, target)}")
