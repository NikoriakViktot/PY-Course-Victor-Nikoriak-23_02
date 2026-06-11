import random
import time


def insertion_sort(items, left, right):
    for index in range(left + 1, right + 1):
        current_value = items[index]
        position = index - 1

        while position >= left and items[position] > current_value:
            items[position + 1] = items[position]
            position -= 1

        items[position + 1] = current_value


def partition(items, left, right):
    middle = (left + right) // 2
    items[middle], items[right] = items[right], items[middle]

    pivot = items[right]
    smaller_index = left - 1

    for current_index in range(left, right):
        if items[current_index] <= pivot:
            smaller_index += 1
            items[smaller_index], items[current_index] = items[current_index], items[smaller_index]

    items[smaller_index + 1], items[right] = items[right], items[smaller_index + 1]
    return smaller_index + 1


def quicksort(items, partition_limit=10):
    items = list(items)

    def sort(left, right):
        if left >= right:
            return

        if right - left + 1 <= partition_limit:
            insertion_sort(items, left, right)
            return

        pivot_index = partition(items, left, right)
        sort(left, pivot_index - 1)
        sort(pivot_index + 1, right)

    sort(0, len(items) - 1)
    return items


def run_analysis():
    random.seed(10)
    list_sizes = [100, 1000, 3000]
    partition_limits = [0, 5, 10, 20, 50]

    for size in list_sizes:
        numbers = [random.randint(1, 10000) for _ in range(size)]
        print(f"List size: {size}")

        for limit in partition_limits:
            start_time = time.perf_counter()
            sorted_numbers = quicksort(numbers, partition_limit=limit)
            end_time = time.perf_counter()

            assert sorted_numbers == sorted(numbers)
            print(f"Partition limit {limit}: {end_time - start_time:.6f} seconds")

        print()


numbers = [8, 3, 1, 7, 0, 10, 2]

assert quicksort(numbers, partition_limit=0) == [0, 1, 2, 3, 7, 8, 10]
assert quicksort(numbers, partition_limit=10) == [0, 1, 2, 3, 7, 8, 10]
assert quicksort([]) == []
assert quicksort([1]) == [1]

run_analysis()
print("All assertions passed")
