# Task 1
# Алгоритм сортування «бульбашкою» можна модифікувати так, щоб «бульбашки» рухалися в обох
# напрямках. Під час першого проходу сортування відбувається «вгору» по списку, а під час
# другого — «вниз». Ця почергова схема триває доти, доки не буде потрібно більше проходів.
# Реалізуйте цей варіант і опишіть, за яких обставин його застосування може бути доречним.
def cocktail_shaker_sort(arr):
    n = len(arr)
    left = 0
    right = n - 1
    swapped = True
    while swapped:
        swapped = False
        # Прохід зліва направо (найбільший елемент стає в кінець)
        for i in range(left, right):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True
        # Якщо не було замін, масив відсортований
        if not swapped:
            break
        swapped = False
        right -= 1  # Зменшуємо праву межу
        # Прохід справа наліво (найменший елемент стає на початок)
        for i in range(right, left, -1):
            if arr[i] < arr[i - 1]:
                arr[i], arr[i - 1] = arr[i - 1], arr[i]
                swapped = True
        left += 1  # Збільшуємо ліву межу
    return arr
# 1. Частково відсортовані дані: Якщо масив уже майже впорядкований, кількість проходів зменшується
# 2. У класичному сортуванні великі елементи «спливають» швидко, але дрібні елементи, що знаходяться
# в кінці масиву (черепахи), пересуваються на початок дуже повільно (по одному кроку за прохід).
# Двонапрямний рух розв'язує цю проблему.

# Task 2
# Реалізуйте функцію mergeSort без використання оператора slice.
def merge_sort(arr, left=0, right=None):
    # При першому виклику встановлюємо праву межу на кінець масиву
    if right is None:
        right = len(arr) - 1
    # Базовий випадок: якщо підмасив має 1 або 0 елементів, він уже відсортований
    if left >= right:
        return arr
    # Знаходимо середній індекс без ризику переповнення пам'яті
    mid = left + (right - left) // 2
    # Рекурсивно ділимо ліву та праву частини за індексами
    merge_sort(arr, left, mid)
    merge_sort(arr, mid + 1, right)
    # Зливаємо дві відсортовані частини в одну
    merge(arr, left, mid, right)
    return arr
def merge(arr, left, mid, right):
    # Створюємо тимчасовий список для злиття поточного діапазону
    temp = []
    i = left  # Вказівник для лівої частини [left ... mid]
    j = mid + 1  # Вказівник для правої частини [mid + 1 ... right]
    # Порівнюємо елементи та додаємо менший у тимчасовий список
    while i <= mid and j <= right:
        if arr[i] <= arr[j]:
            temp.append(arr[i])
            i += 1
        else:
            temp.append(arr[j])
            j += 1
    # Якщо залишилися елементи у лівій частині — копіюємо їх
    while i <= mid:
        temp.append(arr[i])
        i += 1
    # Якщо залишилися елементи у правій частині — копіюємо їх
    while j <= right:
        temp.append(arr[j])
        j += 1
    # Переносимо відсортовані елементи з тимчасового списку назад в оригінальний
    for k in range(len(temp)):
        arr[left + k] = temp[k]
# Приклад використання:
if __name__ == "__main__":
    my_list = [38, 27, 43, 3, 9, 82, 10]
    print("До сортування:   ", my_list)
    merge_sort(my_list)
    print("Після сортування:", my_list)

# Task 3
# Один із способів поліпшити швидке сортування полягає у використанні сортування вставкою для
# списків невеликої довжини (назвемо це «межею поділу»). Чому це доцільно? Перепишіть алгоритм
# швидкого сортування та використайте його для сортування випадкового списку цілих чисел.
# Проведіть аналіз, використовуючи різні розміри списків для межі поділу.
import random
import time
def insertion_sort(arr, left, right):
    """Сортування вставкою для певного діапазону індексів."""
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
def partition(arr, left, right):
    """Розбиття масиву навколо опорного елемента (Lomuto partition)."""
    pivot = arr[right]
    i = left - 1
    for j in range(left, right):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[right] = arr[right], arr[i + 1]
    return i + 1
def hybrid_quick_sort(arr, left=0, right=None, threshold=10):
    """Гібридне швидке сортування із лімітом поділу."""
    if right is None:
        right = len(arr) - 1
    if left < right:
        # Якщо розмір поточного підсписку менший або рівний порогу
        if (right - left + 1) <= threshold:
            insertion_sort(arr, left, right)
        else:
            # Інакше продовжуємо стандартне швидке сортування
            pivot_index = partition(arr, left, right)
            hybrid_quick_sort(arr, left, pivot_index - 1, threshold)
            hybrid_quick_sort(arr, pivot_index + 1, right, threshold)
