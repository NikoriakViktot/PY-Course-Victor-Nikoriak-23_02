import random
import time


def insertion_sort_slice(arr: list, left: int, right: int):
    """Сортування вставками для певного діапазону масиву."""
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


def hybrid_quick_sort(arr: list, threshold: int = 10) -> list:
    """
    Гібридне швидке сортування.
    threshold — межа довжини підсписку для переходу на сортування вставками.
    """

    def _quick_sort(left: int, right: int):
        if left >= right:
            return

        # Якщо розмір підмасиву менший або рівний межі -> сортуємо вставками
        if (right - left + 1) <= threshold:
            insertion_sort_slice(arr, left, right)
            return

        # Логіка Quick Sort (схема розділення Ломуто)
        pivot = arr[right]
        i = left - 1
        for j in range(left, right):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]

        arr[i + 1], arr[right] = arr[right], arr[i + 1]
        pivot_idx = i + 1

        # Рекурсивні виклики
        _quick_sort(left, pivot_idx - 1)
        _quick_sort(pivot_idx + 1, right)

    _quick_sort(0, len(arr) - 1)
    return arr


def run_analysis():
    print("=== Задача 3: Аналіз гібридного сортування ===")

    # Генеруємо великий випадковий список
    ARRAY_SIZE = 20000
    random.seed(42)  # Фіксуємо seed для чесного порівняння
    source_array = [random.randint(1, 100000) for _ in range(ARRAY_SIZE)]

    # Різні значення межі поділу для аналізу
    thresholds = [0, 5, 10, 15, 25, 50, 100]

    print(f"Розмір тестового масиву: {ARRAY_SIZE} елементів\n")
    print(f"{'Межа (Threshold)':<18} | {'Час виконання (сек)':<20}")
    print("-" * 43)

    for t in thresholds:
        # Робимо копію оригінального масиву для кожного тесту
        test_arr = source_array.copy()

        start_time = time.perf_counter()
        hybrid_quick_sort(test_arr, threshold=t)
        end_time = time.perf_counter()

        execution_time = end_time - start_time

        label = "Чистий Quick Sort" if t == 0 else f"Threshold = {t}"
        print(f"{label:<18} | {execution_time:.5f}")


run_analysis()


'''
=== Задача 3: Аналіз гібридного сортування ===
Розмір тестового масиву: 20000 елементів

Межа (Threshold)   | Час виконання (сек) 
-------------------------------------------
Чистий Quick Sort  | 0.01967
Threshold = 5      | 0.01928
Threshold = 10     | 0.01721
Threshold = 15     | 0.01635
Threshold = 25     | 0.01711
Threshold = 50     | 0.01955
Threshold = 100    | 0.02623

'''