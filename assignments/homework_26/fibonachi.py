def fibonacci_search(arr, target):
    n = len(arr)

    # 1. Ініціалізуємо перші числа Фібоначчі
    fib_m2 = 0  # (m-2)-ге число
    fib_m1 = 1  # (m-1)-ше число
    fib_m = fib_m2 + fib_m1  # m-те число Фібоначчі

    # Знаходимо найменше число Фібоначчі, яке >= n
    while fib_m < n:
        fib_m2 = fib_m1
        fib_m1 = fib_m
        fib_m = fib_m2 + fib_m1

    # Маркер зміщення (елементи, які ми вже відкинули зліва)
    offset = -1

    # 2. Основний цикл пошуку
    while fib_m > 1:
        # Перевіряємо валідність індексу (вибираємо мінімум, щоб не вийти за межі)
        i = min(offset + fib_m2, n - 1)

        # Якщо елемент більший за target, відкидаємо праву частину масиву
        if arr[i] > target:
            fib_m = fib_m2
            fib_m1 = fib_m1 - fib_m2
            fib_m2 = fib_m - fib_m1

        # Якщо елемент менший за target, відкидаємо ліву частину масиву
        elif arr[i] < target:
            fib_m = fib_m1
            fib_m1 = fib_m2
            fib_m2 = fib_m - fib_m1
            offset = i  # Зміщуємо ліву межу до поточного індексу

        # Елемент знайдено
        else:
            return i

    # Перевірка останнього елемента (якщо масив закінчився на fib_m1)
    if fib_m1 and offset + 1 < n and arr[offset + 1] == target:
        return offset + 1

    # Елемент не знайдено
    return -1
