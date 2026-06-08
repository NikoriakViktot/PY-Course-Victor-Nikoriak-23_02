def binary_search_recursive(arr, key, left=0, right=None):
    if right is None:
        right = len(arr) - 1

    if left > right:
        return -1  # елемент не знайдено

    mid = (left + right) // 2
    if arr[mid] == key:
        return mid
    elif arr[mid] > key:
        return binary_search_recursive(arr, key, left, mid - 1)
    else:
        return binary_search_recursive(arr, key, mid + 1, right)


# приклад
arr = [1, 3, 5, 7, 9, 11]
print(binary_search_recursive(arr, 7))   
print(binary_search_recursive(arr, 4))   



def fibonacci_search(arr, key):
    n = len(arr)

    # створюємо числа Фібоначчі
    fibMMm2 = 0   # (m-2)'те число
    fibMMm1 = 1   # (m-1)'ше число
    fibM = fibMMm2 + fibMMm1  # m'те число

    while fibM < n:
        fibMMm2, fibMMm1 = fibMMm1, fibM
        fibM = fibMMm2 + fibMMm1

    offset = -1

    while fibM > 1:
        i = min(offset + fibMMm2, n - 1)

        if arr[i] < key:
            fibM = fibMMm1
            fibMMm1 = fibMMm2
            fibMMm2 = fibM - fibMMm1
            offset = i
        elif arr[i] > key:
            fibM = fibMMm2
            fibMMm1 = fibMMm1 - fibMMm2
            fibMMm2 = fibM - fibMMm1
        else:
            return i

    if fibMMm1 and arr[offset + 1] == key:
        return offset + 1

    return -1


# приклад
arr = [1, 3, 5, 7, 9, 11]
print(fibonacci_search(arr, 7))   
print(fibonacci_search(arr, 4))   



class HashTable:
    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]  # ланцюжки для колізій

    def _hash(self, key):
        return hash(key) % self.size

    def insert(self, key, value):
        h = self._hash(key)
        for i, (k, v) in enumerate(self.table[h]):
            if k == key:
                self.table[h][i] = (key, value)
                return
        self.table[h].append((key, value))

    def __contains__(self, key):
        h = self._hash(key)
        return any(k == key for k, v in self.table[h])

    def __len__(self):
        return sum(len(bucket) for bucket in self.table)


# приклад
ht = HashTable()
ht.insert("name", "Svitlana")
ht.insert("lang", "Python")

print("name" in ht)   
print("age" in ht)    
print(len(ht))        
