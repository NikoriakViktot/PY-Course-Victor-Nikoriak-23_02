## Базова реалізація Stack та Queue

Для початку створимо стандартні класи `Stack` та `Queue`, на основі яких будемо виконувати завдання. Зазвичай для стеку використовують звичайний список Python (`list`), а для черги — `collections.deque`, оскільки видалення з початку списку в Python є повільним ($O(N)$), а в `deque` воно оптимізоване ($O(1)$).

Python

```
from collections import deque
from typing import Any

class Stack:
    def __init__(self):
        self._items = []

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def push(self, item: Any) -> None:
        self._items.append(item)

    def pop(self) -> Any:
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> Any:
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def size(self) -> int:
        return len(self._items)


class Queue:
    def __init__(self):
        self._items = deque()

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def enqueue(self, item: Any) -> None:
        self._items.append(item)

    def dequeue(self) -> Any:
        if self.is_empty():
            raise IndexError("dequeue from empty queue")
        return self._items.popleft()

    def size(self) -> int:
        return len(self._items)
```

## Task 1: Реверс рядка за допомогою Stack

Оскільки стек повертає елементи у зворотному порядку від того, як вони додавалися (останній зайшов — першим вийшов), ми можемо просто "заштовхнути" всі символи туди, а потім діставати їх один за одним.

Python

```
def reverse_string(text: str) -> str:
    stack = Stack()
    # Додаємо всі символи у стек
    for char in text:
        stack.push(char)
    
    # Дістаємо їх — вони автоматично будуть йти у зворотному порядку
    reversed_text = ""
    while not stack.is_empty():
        reversed_text += stack.pop()
        
    return reversed_text

# Перевірка:
print(reverse_string("Hello World"))  # Виведе: dlroW olleH
```

## Task 2: Перевірка балансу дужок

Це класична задача для стеку. Коли ми зустрічаємо **відкриту** дужку, ми кладемо її в стек. Коли зустрічаємо **закриту** — перевіряємо, чи відповідає вона тій відкритій, що лежить на вершині стеку (найновішій).

Python

```
def is_balanced(expression: str) -> bool:
    stack = Stack()
    # Словник відповідностей закритих дужок до відкритих
    matching_brackets = {')': '(', '}': '{', ']': '['}
    
    for char in expression:
        # Якщо дужка відкрита — штовхаємо в стек
        if char in matching_brackets.values():
            stack.push(char)
        # Якщо закрита
        elif char in matching_brackets:
            # Якщо стек порожній, а закрита дужка вже є — балансу немає
            if stack.is_empty():
                return False
            # Якщо верхня дужка в стеку не відповідає поточному типу
            if stack.pop() != matching_brackets[char]:
                return False
                
    # Якщо в кінці стек порожній — все збалансовано
    return stack.is_empty()

# Перевірка:
print(is_balanced("{[()]}"))  # True
print(is_balanced("{[(])}"))  # False (неправильний порядок)
print(is_balanced("((())"))   # False (зайва відкрита)
```

## Task 3: Розширення функціоналу Stack та Queue

Головна умова цього завдання — **зберегти початковий порядок інших елементів** після пошуку та вилучення шуканого `e`.

### 1. Розширюємо Stack

Щоб дістатися до елемента всередині стеку, нам доведеться знімати (`pop`) елементи зверху. Щоб не загубити їх, ми тимчасово складатимемо їх в інший, допоміжний стек, а потім повернемо назад.

Python

```
class ExtendedStack(Stack):
    def get_from_stack(self, e: Any) -> Any:
        temp_stack = Stack()
        found = False

        # Шукаємо елемент, перекладаючи верхні елементи в temp_stack
        while not self.is_empty():
            current = self.pop()
            if current == e:
                found = True
                break  # Знайшли елемент, зупиняємо пошук
            else:
                temp_stack.push(current)

        # Повертаємо всі елементи з допоміжного стеку назад
        while not temp_stack.is_empty():
            self.push(temp_stack.pop())

        # Якщо елемент не знайшли — кидаємо помилку
        if not found:
            raise ValueError(f"Element '{e}' was not found in the stack.")
            
        return e

# Перевірка Stack:
ex_stack = ExtendedStack()
for x in [10, 20, 30, 40]: ex_stack.push(x)

print(ex_stack.get_from_stack(20))  # Поверне 20
print(ex_stack._items)              # Залишилось: [10, 30, 40] (порядок збережено!)
# print(ex_stack.get_from_stack(99)) # Викличе ValueError
```

### 2. Розширюємо Queue

_(Примітка: в умові завдання для черги метод теж названо `get_from_stack`, проте логічніше назвати його `get_from_queue`. Реалізуємо за умовою, але з правильним алгоритмом для черги)._

Для черги алгоритм простіший: ми можемо просто прокрутити чергу "по колу". Дістаємо елемент з початку (`dequeue`), якщо це не він — одразу відправляємо в кінець (`enqueue`). Робимо так рівно стільки разів, скільки елементів у черзі.

Python

```
class ExtendedQueue(Queue):
    def get_from_stack(self, e: Any) -> Any:  # назва за умовою таски
        size = self.size()
        found = False

        for _ in range(size):
            current = self.dequeue()
            if current == e and not found:
                found = True
                # Не робимо enqueue, тобто вилучаємо його з черги
                continue  
            else:
                # Всі інші елементи прокручуємо назад у хвіст черги
                self.enqueue(current)

        if not found:
            raise ValueError(f"Element '{e}' was not found in the queue.")
            
        return e

# Перевірка Queue:
ex_queue = ExtendedQueue()
for x in ['a', 'b', 'c', 'd']: ex_queue.enqueue(x)

print(ex_queue.get_from_stack('b'))  # Поверне 'b'
print(list(ex_queue._items))          # Залишилось: ['a', 'c'
```