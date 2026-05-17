def merge_sort(arr):
    # Допоміжний масив потрібен для тимчасового зберігання при злитті
    # Створюємо його один раз, щоб не виділяти пам'ять на кожному кроці
    temp_arr = [0] * len(arr)
    _merge_sort_recursive(arr, temp_arr, 0, len(arr) - 1)
    return arr


def _merge_sort_recursive(arr, temp_arr, left, right):
    if left < right:
        mid = (left + right) // 2

        _merge_sort_recursive(arr, temp_arr, left, mid)
        _merge_sort_recursive(arr, temp_arr, mid + 1, right)
        _merge(arr, temp_arr, left, mid, right)

def _merge(arr, temp_arr, left, mid, right):
    i = left
    j = mid + 1
    k = left

    while i <= mid and j <= right:
        if arr[i] <= arr[j]:
            temp_arr[k] = arr[i]
            i += 1
        else:
            temp_arr[k] = arr[j]
            j += 1
        k += 1

    while i <= mid:
        temp_arr[k] = arr[i]
        i += 1
        k += 1

    while j <= right:
        temp_arr[k] = arr[j]
        j += 1
        k += 1

    for idx in range(left, right + 1):
        arr[idx] = temp_arr[idx]


# Перевірка
data = [38, 27, 43, 3, 9, 82, 10]
print(f"Sorted array: {merge_sort(data)}")