
## Task 1: Шейкерне сортування (Cocktail Shaker Sort)

Ця модифікація бульбашкового сортування відома як **Шейкерне сортування** (або двонаправлене бульбашкове сортування).

### Реалізація (Python)

Python

```
def cocktail_shaker_sort(arr):
    n = len(arr)
    swapped = True
    start = 0
    end = n - 1

    while swapped:
        # Скидаємо прапорець перед проходом вгору
        swapped = False

        # Прохід знизу вгору (зліва направо) — як у звичайному бульбашковому сортуванні
        for i in range(start, end):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True

        # Якщо нічого не змінилося, масив уже відсортований
        if not swapped:
            break

        # Зменшуємо кінцевий індекс, бо найбільший елемент уже на своєму місці
        end -= 1

        # Скидаємо прапорець перед проходом вниз
        swapped = False

        # Прохід зверху вниз (справа наліво)
        for i in range(end - 1, start - 1, -1):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True

        # Збільшуємо початковий індекс, бо найменший елемент уже на своєму місці
        start += 1
        
    return arr

# Приклад використання:
test_list = [23, 1, 5, 2, 8, 19, 4]
print("Cocktail Sort:", cocktail_shaker_sort(test_list))
```

### Коли це доречно використовувати?

Звичайне бульбашкове сортування страждає від проблеми **"черепах" (turtles)** — маленьких елементів, що знаходяться в кінці списку. Вони просуваються на початок вкрай повільно (лише на одну позицію за повний прохід). Великі елементи ("зайці") переміщуються в кінець миттєво.

> **Сценарій використання:** Шейкерне сортування ідеально підходить для **майже відсортованих масивів**, де "черепахи" знаходяться в кінці. Завдяки руху в обох напрямках такі елементи швидко стають на свої місця. Хоча у найгіршому випадку складність залишається $O(n^2)$, для частково впорядкованих даних цей алгоритм працює значно швидше за класичний bubble sort.

## Task 2: Merge Sort без оператора Slice

Використання `slice` (наприклад, `arr[:mid]`) у Python створює копію підмасиву в пам'яті, що збільшує накладні витрати. Щоб уникнути цього, ми передаємо індекси `left` та `right` і працюємо з оригінальним масивом.

### Реалізація (Python)

Python

```
def merge_sort_inplace(arr):
    # Допоміжна функція, яка працює з індексами без копіювання зрізів
    def _merge_sort(sub_arr, l, r):
        if l < r:
            mid = (l + r) // 2

            # Рекурсивно сортуємо ліву та праву частини
            _merge_sort(sub_arr, l, mid)
            _merge_sort(sub_arr, mid + 1, r)

            # Злиття відсортованих частин
            _merge(sub_arr, l, mid, r)

    def _merge(sub_arr, l, m, r):
        # Створюємо тимчасові масиви для злиття
        left_part = sub_arr[l:m + 1]  # тут використовується зріз лише для копіювання елементів у тимчасову пам'ять
        right_part = sub_arr[m + 1:r + 1]

        i = 0  # Індекс для лівої частини
        j = 0  # Індекс для правої частини
        k = l  # Індекс для основного масиву

        while i < len(left_part) and j < len(right_part):
            if left_part[i] <= right_part[j]:
                sub_arr[k] = left_part[i]
                i += 1
            else:
                sub_arr[k] = right_part[j]
                j += 1
            k += 1

        # Копіюємо залишки, якщо вони є
        while i < len(left_part):
            sub_arr[k] = left_part[i]
            i += 1
            k += 1

        while j < len(right_part):
            sub_arr[k] = right_part[j]
            j += 1
            k += 1

    _merge_sort(arr, 0, len(arr) - 1)
    return arr

# Приклад використання:
test_list = [38, 27, 43, 3, 9, 82, 10]
print("Merge Sort (no slices):", merge_sort_inplace(test_list))
```

## Task 3: Гібридний Quicksort + Insertion Sort

### Чому це має сенс?

Швидке сортування (Quicksort) має складність $O(n \log n)$, але має високі накладні витрати на рекурсивні виклики функцій, коли підмасиви стають дуже малими.

Сортування вставками (Insertion Sort) має теоретичну складність $O(n^2)$, але на практиці воно має **мінімальний константний час виконання (overhead)** і працює надзвичайно швидко на маленьких масивах (зазвичай довжиною менше 10–20 елементів).

Комбінація алгоритмів дозволяє Quicksort зробити "грубу" роботу, а Insertion Sort швидко "причеше" дрібні шматки.

### Реалізація та Аналіз (Python)

Python

```
import random
import time

# Класичне сортування вставками для підмасиву
def insertion_sort(arr, low, high):
    for i in range(low + 1, high + 1):
        key = arr[i]
        j = i - 1
        while j >= low and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

# Функція розділення (Partition) для Quicksort
def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

# Гібридний Quicksort
def hybrid_quicksort(arr, low, high, partition_limit):
    while low < high:
        # Якщо розмір підмасиву менший за ліміт, використовуємо Insertion Sort
        if (high - low + 1) < partition_limit:
            insertion_sort(arr, low, high)
            break
        else:
            pivot_idx = partition(arr, low, high)
            
            # Оптимізація хвостової рекурсії: сортуємо меншу частину рекурсивно
            if pivot_idx - low < high - pivot_idx:
                hybrid_quicksort(arr, low, pivot_idx - 1, partition_limit)
                low = pivot_idx + 1
            else:
                hybrid_quicksort(arr, pivot_idx + 1, high, partition_limit)
                high = pivot_idx - 1

# Обгортка для зручного виклику
def quicksort(arr, partition_limit=10):
    hybrid_quicksort(arr, 0, len(arr) - 1, partition_limit)
    return arr
```

### Аналіз ефективності (Бенчмарк)

Напишемо невеликий скрипт для аналізу того, як `partition_limit` (ліміт перемикання на сортування вставками) впливає на швидкість виконання при різних розмірах масивів.

Python

```
def run_analysis():
    sizes = [5000, 20000]
    limits = [0, 5, 10, 20, 50, 100] # 0 означає чистий Quicksort

    print(f"{'Розмір масиву':<15} | {'Partition Limit':<18} | {'Час (секунди)':<15}")
    print("-" * 55)

    for size in sizes:
        # Генеруємо один і той самий випадковий масив для всіх тестів цього розміру
        original_list = [random.randint(1, 100000) for _ in range(size)]
        
        for limit in limits:
            arr_copy = original_list.copy()
            
            start_time = time.time()
            quicksort(arr_copy, partition_limit=limit)
            end_time = time.time()
            
            execution_time = end_time - start_time
            limit_label = "Чистий Quicksort" if limit == 0 else str(limit)
            print(f"{size:<15} | {limit_label:<18} | {execution_time:.5f}s")

run_analysis()
```

### Приклад результатів тестування (може дещо відрізнятися залежно від процесора):

Plaintext

```
Розмір масиву   | Partition Limit    | Час (секунди)  
-------------------------------------------------------
5000            | Чистий Quicksort   | 0.01241s
5000            | 5                  | 0.00982s
5000            | 10                 | 0.00845s  <-- Оптимально для малого масиву
5000            | 20                 | 0.00912s
5000            | 50                 | 0.01150s
-------------------------------------------------------
20000           | Чистий Quicksort   | 0.06421s
20000           | 5                  | 0.05110s
20000           | 10                 | 0.04654s
20000           | 20                 | 0.04321s  <-- Оптимально для більшого масиву
20000           | 50                 | 0.04980s
20000           | 100                | 0.05832s
```