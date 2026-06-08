def binary_search_recursive(arr, target, left=0, right=None):
    # При першому виклику встановлюємо праву межу на кінець списку
    if right is None:
        right = len(arr) - 1

    # Базовий випадок 1: межі перетнулися, елемент не знайдено
    if left > right:
        return -1  # або можна піднімати ValueError / повертати False

    # Знаходимо середній індекс
    mid = left + (right - left) // 2

    # Базовий випадок 2: елемент знайдено
    if arr[mid] == target:
        return mid

    # Рекурсивний випадок 1: елемент менший за середній -> шукаємо в лівій половині
    elif arr[mid] > target:
        return binary_search_recursive(arr, target, left, mid - 1)

    # Рекурсивний випадок 2: елемент більший за середній -> шукаємо в правій половині
    else:
        return binary_search_recursive(arr, target, mid + 1, right)
