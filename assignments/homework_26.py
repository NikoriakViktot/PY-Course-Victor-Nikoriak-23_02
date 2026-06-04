# Реалізувати алгоритм бінарного пошуку за допомогою рекурсії.
# Прочитати про Fibonacci search та імплементуйте його за допомогою Python. Визначте складність
# алгоритму та порівняйте його з бінарним пошуком
def binary_search_recursive(arr, target, low, high):
    # Базовий випадок: елемент не знайдено
    if low > high:
        return -1
    mid = (low + high) // 2
    # Елемент знайдено
    if arr[mid] == target:
        return mid
    # Шукаємо у лівій половині
    elif arr[mid] > target:
        return binary_search_recursive(arr, target, low, mid - 1)
    # Шукаємо у правій половині
    else:
        return binary_search_recursive(arr, target, mid + 1, high)
# Приклад використання:
# Масив ОБОВ'ЯЗКОВО має бути відсортованим
numbers = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
target_num = 23
result = binary_search_recursive(numbers, target_num, 0, len(numbers) - 1)
print(f"Елемент {target_num} знайдено на індексі: {result}")  # Виведе 5


def fibonacci_search(arr, target):
    n = len(arr)
    # Ініціалізуємо числа Фібоначчі
    fib_m_minus_2 = 0  # (m-2)-ге число Фібоначчі
    fib_m_minus_1 = 1  # (m-1)-ше число Фібоначчі
    fib_m = fib_m_minus_2 + fib_m_minus_1  # m-те число Фібоначчі
    # Знаходимо найменше число Фібоначчі, яке більше або дорівнює n
    while fib_m < n:
        fib_m_minus_2 = fib_m_minus_1
        fib_m_minus_1 = fib_m
        fib_m = fib_m_minus_2 + fib_m_minus_1
    # Зсув визначає відкинуту ліву частину масиву
    offset = -1
    while fib_m > 1:
        # Перевіряємо, чи є індекс у межах масиву
        i = min(offset + fib_m_minus_2, n - 1)
        # Якщо елемент більший за target, зсуваємо підмасив вліво
        if arr[i] > target:
            fib_m = fib_m_minus_2
            fib_m_minus_1 = fib_m_minus_1 - fib_m_minus_2
            fib_m_minus_2 = fib_m - fib_m_minus_1
        # Якщо елемент менший за target, зсуваємо підмасив вправо
        elif arr[i] < target:
            fib_m = fib_m_minus_1
            fib_m_minus_1 = fib_m_minus_2
            fib_m_minus_2 = fib_m - fib_m_minus_1
            offset = i
        # Елемент знайдено!
        else:
            return i
    # Перевірка останнього елемента
    if fib_m_minus_1 and arr[offset + 1] == target:
        return offset + 1
    return -1
# Приклад використання:
print("Пошук Фібоначчі для 56:", fibonacci_search(numbers, 56))  # Виведе 7

# Перевага Фібоначчі:
# Він використовує лише додавання та віднімання для розрахунку індексів.
# Бінарний пошук використовує ділення навпіл (// 2). На старих архітектурах мікропроцесорів
# ділення займало значно більше тактів, тому пошук Фібоначчі був швидшим.

# Перевага Бінарного:
# Він ділить масив чітко навпіл, тому в середньому вимагає трохи менше операцій порівняння,
# ніж пошук Фібоначчі на великих масивах, що розташовані у швидкій оперативній пам'яті.
# Також Фібоначчі ефективніший, якщо масив настільки великий, що не поміщається в CPU Cache
# (він краще оптимізує локальність даних).

# Реалізувати in (__contains__) та len (__len__) методи для HashTable
class HashTable:
    def __init__(self, size=10):
        self.size = size
        # Створюємо бакети (списки списків для вирішення колізій)
        self.slots = [[] for _ in range(self.size)]
        self._count = 0  # Приватний лічильник для швидкого O(1) отримання довжини
    def _hash(self, key):
        """Внутрішня хеш-функція для отримання індексу слота"""
        return hash(key) % self.size
    def put(self, key, value):
        """Додає або оновлює пару ключ-значення"""
        slot_index = self._hash(key)
        bucket = self.slots[slot_index]
        # Якщо ключ вже є в бакеті, оновлюємо значення
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        # Якщо ключа немає, додаємо новий запис
        bucket.append((key, value))
        self._count += 1
    # === МЕТОДИ ЗА УМОВОЮ ЗАВДАННЯ ===
    def __len__(self):
        """Дозволяє використовувати функцію len(hash_table) за O(1)"""
        return self._count
    def __contains__(self, key):
        """Дозволяє використовувати оператор 'in': key in hash_table"""
        slot_index = self._hash(key)
        bucket = self.slots[slot_index]
        # Шукаємо лінійно всередині конкретного бакета
        for k, v in bucket:
            if k == key:
                return True
        return False

if __name__ == "__main__":
    ht = HashTable(size=5)
    # Додаємо дані
    ht.put("apple", 100)
    ht.put("banana", 250)
    ht.put("orange", 150)
    # 1. Перевірка методу __len__
    print(f"Кількість елементів у хеш-таблиці: {len(ht)}")  # Виведе 3
    # 2. Перевірка методу __contains__ за допомогою оператора 'in'
    print("Чи є 'apple' в таблиці?", "apple" in ht)  # Виведе True
    print("Чи є 'grape' в таблиці?", "grape" in ht)  # Виведе False