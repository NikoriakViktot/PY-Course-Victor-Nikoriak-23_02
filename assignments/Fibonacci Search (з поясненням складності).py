from typing import List

def fibonacci_search(arr: List[int], x: int) -> int:
    n = len(arr)

    fib2 = 0
    fib1 = 1
    fib = fib1 + fib2

    while fib < n:
        fib2 = fib1
        fib1 = fib
        fib = fib1 + fib2

    offset = -1

    while fib > 1:
        i = min(offset + fib2, n - 1)

        if arr[i] < x:
            fib = fib1
            fib1 = fib2
            fib2 = fib - fib1
            offset = i

        elif arr[i] > x:
            fib = fib2
            fib1 = fib1 - fib2
            fib2 = fib - fib1

        else:
            return i

    if fib1 and offset + 1 < n and arr[offset + 1] == x:
        return offset + 1

    return -1


# Example
if __name__ == "__main__":
    data = [1, 3, 5, 7, 9, 11, 13]
    print(fibonacci_search(data, 9))