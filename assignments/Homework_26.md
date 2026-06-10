
### 1. Рекурсивний бінарний пошук (Binary Search)

Бінарний пошук працює **тільки на відсортованих масивах**. Ідея полягає в тому, щоб постійно ділити масив навпіл, порівнюючи серединний елемент із шуканим.

Python

```
def binary_search_recursive(arr, low, high, target):
    # Базовий випадок: якщо межі перетнулися, елемента немає в масиві
    if low > high:
        return -1
    
    mid = (low + high) // 2
    
    # Якщо знайшли елемент
    if arr[mid] == target:
        return mid
    # Якщо елемент менший за серединний, шукаємо в лівій половині
    elif arr[mid] > target:
        return binary_search_recursive(arr, low, mid - 1, target)
    # Якщо елемент більший за серединний, шукаємо в правій половині
    else:
        return binary_search_recursive(arr, mid + 1, high, target)

# Приклад використання:
arr = [1, 3, 5, 7, 9, 11, 13, 15]
target = 7
result = binary_search_recursive(arr, 0, len(arr) - 1, target)
print(f"Елемент {target} знайдено на індексі: {result}") # Виведе: 3
```

### 2. Пошук Фібоначчі (Fibonacci Search)

Пошук Фібоначчі — це ще один алгоритм для **відсортованих масивів**. На відміну від бінарного пошуку, який ділить масив на дві рівні частини ($1/2$ та $1/2$), пошук Фібоначчі ділить масив за допомогою чисел Фібоначчі (на нерівні частини, приблизно у пропорції Золотого перетину).

**Плюс цього алгоритму:** він використовує лише операції додавання та віднімання для розрахунку індексів, тоді як бінарний пошук вимагає ділення (`// 2`), яке на деяких архітектурах процесорів (або мікроконтролерах) може бути повільнішим.

Python

```
def fibonacci_search(arr, target):
    n = len(arr)
    
    # Ініціалізуємо числа Фібоначчі
    fib_m_minus_2 = 0  # (m-2)-ге число
    fib_m_minus_1 = 1  # (m-1)-ше число
    fib_m = fib_m_minus_2 + fib_m_minus_1  # m-те число
    
    # Знаходимо найменше число Фібоначчі, яке більше або дорівнює n
    while fib_m < n:
        fib_m_minus_2 = fib_m_minus_1
        fib_m_minus_1 = fib_m
        fib_m = fib_m_minus_2 + fib_m_minus_1
        
    # Зсув, який показує відкинуту ліву частину масиву
    offset = -1
    
    while fib_m > 1:
        # Перевіряємо, чи є індекс валідним
        i = min(offset + fib_m_minus_2, n - 1)
        
        # Якщо шукане значення більше, зсуваємо масив вправо
        if arr[i] < target:
            fib_m = fib_m_minus_1
            fib_m_minus_1 = fib_m_minus_2
            fib_m_minus_2 = fib_m - fib_m_minus_1
            offset = i
        # Якщо шукане значення менше, відкидаємо праву частину
        elif arr[i] > target:
            fib_m = fib_m_minus_2
            fib_m_minus_1 = fib_m_minus_1 - fib_m_minus_2
            fib_m_minus_2 = fib_m - fib_m_minus_1
        # Елемент знайдено
        else:
            return i
            
    # Перевірка останнього елемента
    if fib_m_minus_1 and offset + 1 < n and arr[offset + 1] == target:
        return offset + 1
        
    return -1

# Приклад використання:
arr = [10, 22, 35, 40, 45, 50, 80, 82, 85, 90, 100]
target = 85
result = fibonacci_search(arr, target)
print(f"Елемент {target} знайдено на індексі: {result}") # Виведе: 8
```