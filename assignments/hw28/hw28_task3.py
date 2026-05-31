import random
import time


def insertion_sort(arr, left, right):
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1

        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1

        arr[j + 1] = key


def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1

    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def hybrid_quick_sort(arr, low, high, limit):
    while low < high:
        if high - low + 1 < limit:
            insertion_sort(arr, low, high)
            break
        else:
            pi = partition(arr, low, high)

            # оптимізація (менша глибина стеку)
            if pi - low < high - pi:
                hybrid_quick_sort(arr, low, pi - 1, limit)
                low = pi + 1
            else:
                hybrid_quick_sort(arr, pi + 1, high, limit)
                high = pi - 1


# -------------------------------
# АНАЛІЗ
# -------------------------------
def test_performance(size, limit):
    arr = [random.randint(0, 100000) for _ in range(size)]

    start = time.time()
    hybrid_quick_sort(arr, 0, len(arr) - 1, limit)
    end = time.time()

    return end - start


# запуск тестів
sizes = [1000, 5000, 10000]
limits = [5, 10, 20, 50]

for size in sizes:
    print(f"\nSize: {size}")
    for limit in limits:
        t = test_performance(size, limit)
        print(f"limit={limit}: {t:.5f} sec")