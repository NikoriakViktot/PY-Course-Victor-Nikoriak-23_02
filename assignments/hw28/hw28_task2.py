def merge(arr, left, mid, right):
    left_part = []
    right_part = []

    for i in range(left, mid + 1):
        left_part.append(arr[i])

    for i in range(mid + 1, right + 1):
        right_part.append(arr[i])

    i = j = 0
    k = left

    while i < len(left_part) and j < len(right_part):
        if left_part[i] <= right_part[j]:
            arr[k] = left_part[i]
            i += 1
        else:
            arr[k] = right_part[j]
            j += 1
        k += 1

    while i < len(left_part):
        arr[k] = left_part[i]
        i += 1
        k += 1

    while j < len(right_part):
        arr[k] = right_part[j]
        j += 1
        k += 1


def merge_sort(arr, left, right):
    if left < right:
        mid = (left + right) // 2

        merge_sort(arr, left, mid)
        merge_sort(arr, mid + 1, right)

        merge(arr, left, mid, right)


# тест
arr = [5, 2, 9, 1, 5, 6]
merge_sort(arr, 0, len(arr) - 1)
print(arr)