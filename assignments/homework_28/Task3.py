import random
import time

def insertion_sort(arr, low, high):
    for i in range(low + 1, high + 1):
        key = arr[i]
        j = i - 1
        while j >= low and arr[j] > key:
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


def quicksort_optimized(arr, low, high, limit):
    while low < high:
        if (high - low + 1) < limit:
            insertion_sort(arr, low, high)
            break
        else:
            pivot_index = partition(arr, low, high)

            if pivot_index - low < high - pivot_index:
                quicksort_optimized(arr, low, pivot_index - 1, limit)
                low = pivot_index + 1
            else:
                quicksort_optimized(arr, pivot_index + 1, high, limit)
                high = pivot_index - 1


def run_test(size, limit):
    data = [random.randint(0, 100000) for _ in range(size)]
    start = time.time()
    quicksort_optimized(data, 0, len(data) - 1, limit)
    return time.time() - start