# Task 1
# Розширити клас UnsortedList
# Реалізуйте методи append, index, pop та insert для класу UnsortedList. Також реалізуйте метод
# slice, який прийматиме два параметри «start» та «stop» і повертатиме копію списку, починаючи
# з позиції start і закінчуючи позицією stop (не включно).
class Node:
    def __init__(self, init_data):
        self.data = init_data
        self.next = None
class UnsortedList:
    def __init__(self):
        self.head = None
    def is_empty(self):
        return self.head is None
    def add(self, item):
        """Класичний метод додавання на початок списку за O(1)"""
        temp = Node(item)
        temp.next = self.head
        self.head = temp
    def size(self):
        """Повертає кількість елементів у списку"""
        current = self.head
        count = 0
        while current is not None:
            count += 1
            current = current.next
        return count
    # ==========================================
    # НОВІ МЕТОДИ ЗА УМОВОЮ ЗАВДАННЯ
    # ==========================================
    def append(self, item):
        """Додає новий елемент у самий кінець списку за O(n)"""
        new_node = Node(item)
        if self.is_empty():
            self.head = new_node
            return
        current = self.head
        # Йдемо до останнього вузла (у якого next є None)
        while current.next is not None:
            current = current.next
        current.next = new_node
    def index(self, item):
        """Повертає індекс першого знайденого елемента.
        Якщо елемента немає — викликає ValueError"""
        current = self.head
        pos = 0
        while current is not None:
            if current.data == item:
                return pos
            current = current.next
            pos += 1
        raise ValueError(f"'{item}' немає у списку")
    def pop(self, pos=None):
        """Видаляє та повертає елемент із вказаної позиції 'pos'.
        Якщо 'pos' не вказано, видаляє ОСТАННІЙ елемент списку."""
        if self.is_empty():
            raise IndexError("pop з порожнього списку")
        list_size = self.size()
        if pos is None:
            pos = list_size - 1
        if pos < 0 or pos >= list_size:
            raise IndexError("Індекс поза межами списку")
        current = self.head
        previous = None
        current_pos = 0
        # Шукаємо потрібний вузол та його попередника
        while current_pos < pos:
            previous = current
            current = current.next
            current_pos += 1
        # Якщо видаляємо перший елемент (head)
        if previous is None:
            self.head = current.next
        else:
            previous.next = current.next
        return current.data
    def insert(self, pos, item):
        """Вставляє новий елемент на вказану позицію 'pos'"""
        list_size = self.size()
        if pos < 0 or pos > list_size:
            raise IndexError("Індекс для вставки поза межами списку")
        # Якщо вставка на початок, використовуємо готовий метод add
        if pos == 0:
            self.add(item)
            return
        new_node = Node(item)
        current = self.head
        previous = None
        current_pos = 0
        # Шукаємо місце для вставки
        while current_pos < pos:
            previous = current
            current = current.next
            current_pos += 1
        previous.next = new_node
        new_node.next = current
    def slice(self, start, stop):
        """Повертає новий об'єкт UnsortedList, який є копією частини
        оригінального списку від 'start' до 'stop' (не включно)"""
        list_size = self.size()
        # Обробка меж
        if start < 0: start = 0
        if stop > list_size: stop = list_size
        new_list = UnsortedList()
        if start >= stop or self.is_empty():
            return new_list  # Повертаємо порожній список
        current = self.head
        pos = 0
        # Спочатку доходимо до індексу 'start'
        while current is not None and pos < start:
            current = current.next
            pos += 1
        # Копіюємо елементи до позиції 'stop'
        # Щоб зберегти правильний порядок при копіюванні, використовуємо метод append
        while current is not None and pos < stop:
            new_list.append(current.data)
            current = current.next
            pos += 1
        return new_list
    # --- Допоміжний метод для гарного виводу ---
    def __str__(self):
        items = []
        current = self.head
        while current is not None:
            items.append(str(current.data))
            current = current.next
        return "[" + " -> ".join(items) + "]"

if __name__ == "__main__":
    mylist = UnsortedList()
    # 1. Тест класичного add та нового append
    mylist.add(20)  # [20]
    mylist.add(10)  # [10 -> 20]
    mylist.append(30)  # [10 -> 20 -> 30]
    mylist.append(40)  # [10 -> 20 -> 30 -> 40]
    print("Початковий список:", mylist)
    # 2. Тест методу index
    print("Індекс елемента 30:", mylist.index(30))  # Виведе: 2
    # 3. Тест методу insert
    mylist.insert(2, 25)  # Вставляємо 25 на позицію 2
    print("Після вставки 25 на інд. 2:", mylist)  # [10 -> 20 -> 25 -> 30 -> 40]
    # 4. Тест методу pop (з позицією і без)
    print("Видалено останній (pop):", mylist.pop())  # Видалить 40
    print("Видалено за індексом 1 (pop(1)):", mylist.pop(1))  # Видалить 20
    print("Список після видалень:", mylist)  # [10 -> 25 -> 30]
    # 5. Тест методу slice
    mylist.append(35)
    mylist.append(50)
    print("Оновлений список перед зрізом:", mylist)  # [10 -> 25 -> 30 -> 35 -> 50]
    sub_list = mylist.slice(1, 4)  # Беремо індекси 1, 2, 3 (елементи 25, 30, 35)
    print("Отриманий зріз slice(1, 4):", sub_list)  # [25 -> 30 -> 35]

# Task 2
# Реалізуйте стек за допомогою однонаправленого списку.
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
class LinkedStack:
    def __init__(self):
        # head списку є вершиною (top) нашого стека
        self._head = None
        self._size = 0
    def push(self, item):
        """Додає елемент на вершину стека за O(1)"""
        new_node = Node(item)
        # Новий вузол посилається на поточну голову
        new_node.next = self._head
        # Новий вузол стає новою головою (вершиною)
        self._head = new_node
        self._size += 1
    def pop(self):
        """Видаляє та повертає елемент з вершини стека за O(1)"""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        # Запам'ятовуємо дані з вершини
        popped_data = self._head.data
        # Переміщуємо голову на наступний вузол
        self._head = self._head.next
        self._size -= 1
        return popped_data
    def peek(self):
        """Дозволяє переглянути верхній елемент без його видалення за O(1)"""
        if self.is_empty():
            return None
        return self._head.data
    def is_empty(self):
        """Перевіряє, чи порожній стек за O(1)"""
        return self._head is None
    def size(self):
        """Повертає поточну кількість елементів у стеку за O(1)"""
        return self._size
    # --- Допоміжний метод для красивого виводу ---
    def __str__(self):
        items = []
        current = self._head
        while current is not None:
            items.append(str(current.data))
            current = current.next
        return " -> ".join(items) + " (вершина)" if items else "Стек порожній"

if __name__ == "__main__":
    stack = LinkedStack()
    print("--- 1. Додавання елементів (Push) ---")
    stack.push("Книга А")
    stack.push("Книга Б")
    stack.push("Книга В")
    print("Поточний стек (зліва направо від вершини):")
    print(stack)  # Виведе: Книга В -> Книга Б -> Книга А (вершина)
    print("Розмір стека:", stack.size())  # 3
    print("\n--- 2. Перегляд вершини (Peek) ---")
    print("Елемент на вершині:", stack.peek())  # Книга В
    print("\n--- 3. Вилучення елементів (Pop) ---")
    print("Вилучено:", stack.pop())  # Книга В
    print("Вилучено:", stack.pop())  # Книга Б
    print("\nСтан стека після двох pop():")
    print(stack)  # Книга А (вершина)
    print("Розмір стека:", stack.size())  # 1
    print("\n--- 4. Перевірка на порожнечу ---")
    print("Стек порожній?", stack.is_empty())  # False
    stack.pop()
    print("Стек порожній після останнього pop()?", stack.is_empty())  # True

# Task 3
# Реалізуйте чергу за допомогою однонаправленого списку.
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
class LinkedQueue:
    def __init__(self):
        self._head = None  # Початок черги (звідси видаляємо)
        self._tail = None  # Кінець черги (сюди додаємо)
        self._size = 0  # Лічильник елементів
    def enqueue(self, item):
        """Додає новий елемент у кінець черги за O(1)"""
        new_node = Node(item)
        # Якщо черга порожня, новий вузол стає і головою, і хвостом
        if self.is_empty():
            self._head = new_node
            self._tail = new_node
        else:
            # Старий хвіст тепер посилається на новий вузол
            self._tail.next = new_node
            # Оновлюємо покажчик хвоста на новий вузол
            self._tail = new_node
        self._size += 1
    def dequeue(self):
        """Видаляє та повертає елемент із початку черги за O(1)"""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        # Запам'ятовуємо дані з голови черги
        data = self._head.data
        # Зміщуємо голову на наступний вузол
        self._head = self._head.next
        # Якщо після видалення черга стала порожньою, хвіст теж має стати None
        if self._head is None:
            self._tail = None
        self._size -= 1
        return data
    def peek(self):
        """Дозволяє переглянути перший елемент у черзі без видалення за O(1)"""
        if self.is_empty():
            return None
        return self._head.data
    def is_empty(self):
        """Перевіряє, чи порожня черга за O(1)"""
        return self._head is None
    def size(self):
        """Повертає поточну кількість елементів у черзі за O(1)"""
        return self._size
    # --- Допоміжний метод для зручного виведення стану черги ---
    def __str__(self):
        items = []
        current = self._head
        while current is not None:
            items.append(str(current.data))
            current = current.next
        return " -> ".join(items) if items else "Черга порожня"

if __name__ == "__main__":
    queue = LinkedQueue()
    print("--- 1. Додавання в чергу (Enqueue) ---")
    queue.enqueue("Клієнт 1")
    queue.enqueue("Клієнт 2")
    queue.enqueue("Клієнт 3")
    print("Поточна черга (від початку до кінця):")
    print(queue)  # Виведе: Клієнт 1 -> Клієнт 2 -> Клієнт 3
    print("Розмір черги:", queue.size())  # 3
    print("\n--- 2. Перегляд першого в черзі (Peek) ---")
    print("Наступний на обслуговування:", queue.peek())  # Клієнт 1
    print("\n--- 3. Вилучення з черги (Dequeue) ---")
    print("Обслуговано:", queue.dequeue())  # Клієнт 1
    print("Обслуговано:", queue.dequeue())  # Клієнт 2
    print("\nСтан черги після обслуговування двох клієнтів:")
    print(queue)  # Клієнт 3
    print("Розмір черги:", queue.size())  # 1
    print("\n--- 4. Перевірка на порожнечу ---")
    print("Черга порожня?", queue.is_empty())  # False
    queue.dequeue()
    print("Черга порожня тепер?", queue.is_empty())  # True
