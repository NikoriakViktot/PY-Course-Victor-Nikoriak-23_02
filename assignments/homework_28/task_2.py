def merge_sort(arr: list) -> list:

    if not arr:
        return arr

    temp = [0] * len(arr)

    def _merge_sort_recursive(left: int, right: int):
        # Базовий випадок: якщо в підмасиві один або нуль елементів
        if left >= right:
            return

        # Знаходимо середину без використання ділення з рухомою комою
        mid = left + (right - left) // 2

        # Рекурсивно ділимо ліву та праву частини
        _merge_sort_recursive(left, mid)
        _merge_sort_recursive(mid + 1, right)

        # Зливаємо відсортовані частини
        _merge(left, mid, right)

    def _merge(left: int, mid: int, right: int):
        # Копіюємо елементи поточного діапазону в допоміжний масив
        for i in range(left, right + 1):
            temp[i] = arr[i]

        i = left  # Вказівник для лівої частини (від left до mid)
        j = mid + 1  # Вказівник для правої частини (від mid+1 до right)
        k = left  # Вказівник для запису в оригінальний масив

        # Злиття елементів у правильному порядку
        while i <= mid and j <= right:
            if temp[i] <= temp[j]:
                arr[k] = temp[i]
                i += 1
            else:
                arr[k] = temp[j]
                j += 1
            k += 1

        while i <= mid:
            arr[k] = temp[i]
            i += 1
            k += 1

        while j <= right:
            arr[k] = temp[j]
            j += 1
            k += 1

    _merge_sort_recursive(0, len(arr) - 1)
    return arr