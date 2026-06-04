# Task 1
# Напишіть програму, яка зчитує послідовність символів і виводить їх у зворотному порядку,
# використовуючи вашу реалізацію стека.
class Stack:
    def __init__(self):
        # Використовуємо список як внутрішнє сховище для стека
        self._items = []
    def push(self, item):
        """Додає елемент на вершину стека."""
        self._items.append(item)
    def pop(self):
        """Видаляє та повертає елемент з вершини стека."""
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()
    def peek(self):
        """Дозволяє переглянути верхній елемент без його видалення."""
        if self.is_empty():
            return None
        return self._items[-1]
    def is_empty(self):
        """Перевіряє, чи порожній стек."""
        return len(self._items) == 0
    def size(self):
        """Повертає поточну кількість елементів у стеку."""
        return len(self._items)
def reverse_string_with_stack(text: str) -> str:
    """Функція, яка розгортає рядок за допомогою стека."""
    stack = Stack()
    # 1. ENQUEUE / PUSH: Заштовхуємо кожен символ рядка в стек
    for char in text:
        stack.push(char)
    # Оскільки стек працює за принципом LIFO (останній зайшов — перший вийшов),
    # символи з кінця рядка опиняться на самому верху стека.
    reversed_text = ""
    # 2. POP: Витягуємо символи зі стека по одному, доки він не спорожніє
    while not stack.is_empty():
        reversed_text += stack.pop()
    return reversed_text
# --- Демонстрація роботи програми ---
if __name__ == "__main__":
    # Користувач вводить послідовність символів
    user_input = input("Введіть рядок тексту: ")
    # Отримуємо розгорнутий рядок
    result = reverse_string_with_stack(user_input)
    # Виводимо результат
    print(f"Результат у зворотному порядку: {result}")

# Task 2
# Напишіть програму, яка зчитує послідовність символів і визначає, чи «збалансовані» дужки,
# фігурні дужки та фігурні дужки.
class Stack:
    def __init__(self):
        self._items = []
    def push(self, item):
        self._items.append(item)
    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()
    def is_empty(self):
        return len(self._items) == 0
def is_balanced(text: str) -> bool:
    """
    Перевіряє, чи є дужки (), [], {} у рядку збалансованими.
    Повертає True, якщо все правильно, і False, якщо є помилка.
    """
    stack = Stack()
    # Відповідність закриваючих дужок відкриваючим
    matching_brackets = {
        ')': '(',
        ']': '[',
        '}': '{'
    }
    # Множини для швидкої перевірки типу дужки
    opening_brackets = set(matching_brackets.values())
    closing_brackets = set(matching_brackets.keys())
    for char in text:
        # 1. Якщо бачимо відкриваючу дужку, кладемо її на вершину стека
        if char in opening_brackets:
            stack.push(char)
        # 2. Якщо бачимо закриваючу дужку
        elif char in closing_brackets:
            # Якщо стек порожній, значить для закриваючої дужки немає відкриваючої
            if stack.is_empty():
                return False
            # Витягуємо останню відкриту дужку зі стека
            last_opened = stack.pop()
            # Перевіряємо, чи підходить вона до поточної закриваючої
            if last_opened != matching_brackets[char]:
                return False
    # 3. Якщо після перевірки всього рядка стек порожній — все збалансовано.
    # Якщо в стеку щось залишилось (наприклад, "((("), то балансу немає.
    return stack.is_empty()
# --- Демонстрація роботи програми ---
if __name__ == "__main__":
    # Списки тестів для перевірки
    test_strings = [
        "()[{}](())",  # Збалансовано (True)
        "{[()]}",  # Збалансовано (True)
        "print(list[0])",  # Збалансовано (True, текст ігнорується)
        "([)]",  # Небаланс (False - неправильний порядок)
        "((()",  # Небаланс (False - не всі закриті)
        "())"  # Небаланс (False - зайва закриваюча)
    ]
    print("--- Автоматичні тести ---")
    for s in test_strings:
        status = "Збалансовано" if is_balanced(s) else "НЕ збалансовано"
        print(f"Рядок: {s:15} -> {status}")
    print("\n--- Ручний ввід ---")
    user_input = input("Введіть свій вираз для перевірки: ")
    if is_balanced(user_input):
        print("✅ Чудово! Дужки у виразі повністю збалансовані.")
    else:
        print("❌ Помилка! Дужки розставлені невірно.")

# Task 3
# Розширте стек, додавши метод get_from_stack, який шукає та повертає елемент e зі стека.
# Усі інші елементи повинні залишатися на стеку, зберігаючи свій порядок. У разі, якщо
# елемент не знайдено, слід викликати виняток ValueError із відповідним повідомленням

class Stack:
    def __init__(self):
        self._items = []
    def push(self, item):
        self._items.append(item)
    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()
    def is_empty(self):
        return len(self._items) == 0
    def size(self):
        return len(self._items)
    # --- Новий метод за умовою завдання ---
    def get_from_stack(self, e):
        """
        Шукає та повертає елемент 'e' зі стека.
        Усі інші елементи залишаються на стеку у своєму початковому порядку.
        Якщо елемент не знайдено, викликає ValueError.
        """
        temp_stack = Stack()
        found_item = None
        # 1. Послідовно знімаємо елементи з вершини основного стека
        # і перекладаємо в допоміжний, поки не знайдемо шуканий елемент
        while not self.is_empty():
            current = self.pop()
            if current == e:
                found_item = current
                break  # Елемент знайдено, зупиняємо пошук
            temp_stack.push(current)
        # 2. Повертаємо всі елементи з допоміжного стека назад в основний,
        # щоб повністю відновити початковий порядок решти елементів
        while not temp_stack.is_empty():
            self.push(temp_stack.pop())
        # 3. Якщо елемент так і не був знайдений в циклі, викликаємо виняток
        if found_item is None:
            raise ValueError(f"Елемент '{e}' не знайдено в стеку.")
        return found_item
# Створюємо стек та наповнюємо його
my_stack = Stack()
my_stack.push("книга 1")
my_stack.push("книга 2")
my_stack.push("книга 3")  # Це шуканий елемент
my_stack.push("книга 4")  # Лежить на самій вершині
print("Початковий розмір стека:", my_stack.size())
# 1. Успішний пошук елемента всередині стека
try:
    target = my_stack.get_from_stack("книга 3")
    print(f"✅ Знайдено елемент: '{target}'")
except ValueError as error:
    print(error)
print("Розмір стека після пошуку (має бути 4):", my_stack.size())
print("Елемент на вершині (має залишитися 'книга 4'):", my_stack._items[-1])
print("\n" + "-"*30 + "\n")
# 2. Спроба знайти елемент, якого немає в стеку
try:
    print("Шукаємо неіснуючий елемент...")
    my_stack.get_from_stack("книга 99")
except ValueError as error:
    print(f"❌ Перехоплено помилку: {error}")

# Розширте чергу, додавши метод get_from_stack, який шукає та повертає елемент e з черги.
# Усі інші елементи повинні залишатися в черзі, зберігаючи їхній порядок. Розгляньте випадок,
# коли елемент не знайдено — виведіть ValueError з відповідним повідомленням

class Queue:
    def __init__(self):
        # Використовуємо список як внутрішнє сховище для черги
        self._items = []
    def enqueue(self, item):
        """Додає елемент у кінець черги."""
        self._items.append(item)
    def dequeue(self):
        """Видаляє та повертає елемент із початку черги."""
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self._items.pop(0)
    def is_empty(self):
        """Перевіряє, чи порожня черга."""
        return len(self._items) == 0
    def size(self):
        """Повертає поточну кількість елементів у черзі."""
        return len(self._items)
    # --- Новий метод за умовою завдання ---
    def get_from_stack(self, e):
        """
        Шукає та повертає елемент 'e' з черги.
        Усі інші елементи залишаються в черзі та зберігають свій порядок.
        Якщо елемент не знайдено, викликає ValueError.
        """
        initial_size = self.size()
        found_item = None
        # Проходимо по черзі рівно стільки разів, скільки елементів у ній було спочатку
        for _ in range(initial_size):
            current = self.dequeue()
            # Якщо знайшли потрібний елемент і ми його ще не знаходили (перше входження)
            if current == e and found_item is None:
                found_item = current
                # Ми НЕ додаємо його назад у чергу, оскільки ми його вилучаємо
                continue
                # Усі інші елементи повертаємо назад у кінець черги
            self.enqueue(current)
        # Якщо елемент так і не був знайдений
        if found_item is None:
            raise ValueError(f"Елемент '{e}' не знайдено в черзі.")
        return found_item

# Створюємо чергу та наповнюємо її (перший зайшов — перший на вихід)
my_queue = Queue()
my_queue.enqueue("Абонент 1")  # На початку черги
my_queue.enqueue("Абонент 2")
my_queue.enqueue("Абонент 3")  # Шуканий елемент
my_queue.enqueue("Абонент 4")  # В кінці черги
print("Початкова черга:", my_queue._items)
print("Початковий розмір черги:", my_queue.size())
# 1. Успішний пошук та вилучення елемента
try:
    target = my_queue.get_from_stack("Абонент 3")
    print(f"\n✅ Знайдено та вилучено: '{target}'")
except ValueError as error:
    print(error)
print("Черга після пошуку:", my_queue._items)
print("Розмір черги (має бути 3):", my_queue.size())
print("\n" + "-" * 40 + "\n")
# 2. Спроба знайти елемент, якого немає в черзі
try:
    print("Шукаємо неіснуючого абонента...")
    my_queue.get_from_stack("Абонент 99")
except ValueError as error:
    print(f"❌ Перехоплено помилку: {error}")
print("Черга після невдалого пошуку (порядок не змінився):", my_queue._items)
