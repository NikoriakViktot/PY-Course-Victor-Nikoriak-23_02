# Діаграми — Урок 24: Структури Даних — Список як Архітектурне Рішення

---

## 1. Архітектура пам'яті: Масив проти Зв'язного Списку

```mermaid
graph TD
    subgraph ARRAY["Python list (Динамічний масив)"]
        direction LR
        B0["ptr[0]→42"] --- B1["ptr[1]→'hi'"] --- B2["ptr[2]→True"] --- B3["ptr[3]→[...]"]
        style ARRAY fill:#e8f4fd,stroke:#2196F3
    end

    subgraph LINKED["Зв'язний список (Вузли в RAM)"]
        direction LR
        N1["Node\ndata=10\nnext→"] --> N2["Node\ndata=20\nnext→"] --> N3["Node\ndata=30\nnext=None"]
        style LINKED fill:#fef3e2,stroke:#FF9800
    end

    ARRAY --- |"O(1) доступ\nO(n) insert"| A_LABEL[" "]
    LINKED --- |"O(n) доступ\nO(1) insert"| L_LABEL[" "]
```

**Де використовується:**
- Масив: читання даних, довільний доступ, ітерація, binary search
- Зв'язний список: часті вставки/видалення на початку, черги, undo-стеки

---

## 2. Алгоритм: Вставка у Зв'язний Список (O(1))

```mermaid
flowchart LR
    subgraph BEFORE["До вставки"]
        A1["Node A\nnext→"] --> B1["Node B\nnext=None"]
    end

    subgraph AFTER["Після вставки X між A і B"]
        A2["Node A\nnext→"] --> X2["Node X\nnext→"] --> B2["Node B\nnext=None"]
        style X2 fill:#c8e6c9,stroke:#4CAF50
    end

    BEFORE -->|"1. new_node = Node(X)\n2. new_node.next = B\n3. A.next = new_node"| AFTER
```

**Де використовується:**
- Планувальники задач (вставка з пріоритетом)
- Текстові редактори (вставка символів у середину)
- Операційні системи (управління процесами)

---

## 3. Алгоритм: Видалення з Зв'язного Списку (O(1) при наявності вказівника)

```mermaid
flowchart TD
    subgraph BEFORE["До видалення вузла B"]
        A1["Node A\nnext→"] --> B1["Node B ❌\nnext→"] --> C1["Node C\nnext=None"]
    end

    subgraph AFTER["Після видалення B"]
        A2["Node A\nnext→"] --> C2["Node C\nnext=None"]
        B2["Node B 🗑️\n(ізольований → GC)"]
        style B2 fill:#ffcdd2,stroke:#f44336
    end

    BEFORE -->|"A.next = C\n(обхідний шлях)"| AFTER
```

**Де використовується:**
- LRU-кеш (видалення найстарішого елемента)
- Doubly linked list (O(1) без пошуку попередника)
- Черга принтера (скасування завдання)

---

## 4. ADT: Контракт проти Реалізації

```mermaid
graph TB
    CLIENT["👤 Клієнтський код"]

    subgraph CONTRACT["🔒 Публічний інтерфейс (Контракт)"]
        I1["append(data)"]
        I2["remove(key)"]
        I3["__len__()"]
        I4["__iter__()"]
        I5["__contains__(item)"]
    end

    subgraph SECRET["🔐 Реалізація (Секрет)"]
        S1["_head: Node | None"]
        S2["_size: int"]
        S3["class _Node:\n  data\n  next"]
        S4["while current.next:\n  current = current.next"]
    end

    CLIENT -->|"використовує"| CONTRACT
    CONTRACT -->|"делегує до"| SECRET
    CLIENT -.->|"❌ НЕ ЗНАЄ"| SECRET

    style CONTRACT fill:#e8f5e9,stroke:#4CAF50
    style SECRET fill:#ffebee,stroke:#f44336
```

**Принцип:** Змінити реалізацію (масив → дерево → хеш) — клієнтський код не зламається.

---

## 5. Паттерн Ітератор: Механізм `yield`

```mermaid
sequenceDiagram
    participant CLIENT as 👤 for x in my_list
    participant ITER as ⚙️ __iter__() генератор
    participant NODE as 🔗 _Node (прихований)

    CLIENT->>ITER: iter(my_list) → генераторний об'єкт
    loop Кожна ітерація
        CLIENT->>ITER: next()
        ITER->>NODE: current = current.next
        NODE-->>ITER: current.data
        ITER-->>CLIENT: yield current.data
    end
    ITER-->>CLIENT: StopIteration (current = None)
```

**Де використовується:**
- Обхід будь-якої кастомної структури даних
- Lazy evaluation (генерація елементів по одному)
- Паттерн Observer, pipeline-обробка даних

---

## 6. Node-based Stack: Алгоритм Push/Pop (LIFO)

```mermaid
flowchart TD
    subgraph PUSH["push(X) — O(1)"]
        direction LR
        P1["1. new = Node(X)"]
        P2["2. new.next = top"]
        P3["3. top = new"]
        P1 --> P2 --> P3
    end

    subgraph STACK_STATE["Стан стека після push(A), push(B), push(C)"]
        direction TB
        TOP["⬆️ top"] --> NC["Node C\nnext→"] --> NB["Node B\nnext→"] --> NA["Node A\nnext=None"]
        style NC fill:#c8e6c9,stroke:#4CAF50
    end

    subgraph POP["pop() — O(1)"]
        direction LR
        Q1["1. data = top.data"]
        Q2["2. top = top.next"]
        Q3["3. return data"]
        Q1 --> Q2 --> Q3
    end
```

**Де використовується:** рекурсія, DFS, undo/redo, перевірка дужок, call stack

---

## 7. Node-based Queue: Алгоритм Enqueue/Dequeue (FIFO)

```mermaid
flowchart LR
    subgraph QUEUE_STATE["Стан черги: head → [A] → [B] → [C] ← tail"]
        H["🔼 head"] --> QA["Node A\nnext→"] --> QB["Node B\nnext→"] --> QC["Node C\nnext=None"]
        T["🔽 tail"] --> QC
    end

    subgraph ENQUEUE["enqueue(D) — O(1)"]
        E1["1. new = Node(D)"]
        E2["2. tail.next = new"]
        E3["3. tail = new"]
        E1 --> E2 --> E3
    end

    subgraph DEQUEUE["dequeue() — O(1)"]
        D1["1. data = head.data"]
        D2["2. head = head.next"]
        D3["3. return data"]
        D1 --> D2 --> D3
    end
```

**Де використовується:** HTTP request queue, BFS, принтер, планувальник ОС, Celery tasks

---

## 8. Doubly Linked List: Архітектура з Sentinel-вузлами

```mermaid
graph LR
    SH["🛡️ sentinel\n_head\n(dummy)"]
    N1["Node A\nprev→SH\nnext→"]
    N2["Node B\nprev→A\nnext→"]
    N3["Node C\nprev→B\nnext→ST"]
    ST["🛡️ sentinel\n_tail\n(dummy)"]

    SH -->|next| N1
    N1 -->|next| N2
    N2 -->|next| N3
    N3 -->|next| ST

    ST -->|prev| N3
    N3 -->|prev| N2
    N2 -->|prev| N1
    N1 -->|prev| SH

    style SH fill:#eeeeee,stroke:#9E9E9E
    style ST fill:#eeeeee,stroke:#9E9E9E
```

**Sentinel (dummy) усуває граничні випадки:**
- Порожній список: `SH.next = ST`, `ST.prev = SH`
- Вставка/видалення: завжди однаковий код, без `if head is None`

---

## 9. Складність Операцій: Повна Таблиця

```mermaid
graph TD
    subgraph COMPLEXITY["Порівняльна складність операцій"]
        direction TB

        subgraph ARRAY_COL["Python list (масив)"]
            A_READ["Читання list[i]: O(1) ✅"]
            A_APPEND["append(): O(1) амортизовано ✅"]
            A_INSERT0["insert(0, x): O(n) ❌"]
            A_DELETE0["pop(0): O(n) ❌"]
            A_SEARCH["in оператор: O(n)"]
        end

        subgraph LL_COL["Linked List (вузли)"]
            L_READ["Читання [i]: O(n) ❌"]
            L_PREPEND["prepend(): O(1) ✅"]
            L_INSERT["insert (з вказівником): O(1) ✅"]
            L_DELETE["delete (з вказівником): O(1) ✅"]
            L_SEARCH["search(): O(n)"]
        end

        subgraph DEQUE_COL["collections.deque"]
            D_LEFT["appendleft/popleft: O(1) ✅"]
            D_RIGHT["append/pop: O(1) ✅"]
            D_MIDDLE["deque[i] середина: O(n) ❌"]
        end
    end
```

---

## 10. Паттерни ООП у Структурах Даних

```mermaid
graph TB
    subgraph ADAPTER["Паттерн Адаптер (Stack)"]
        CLI1["Клієнт: push(x), pop()"] --> ADAPT["Stack обгортка"] --> LST["list._data.append/pop"]
        CLI1 -.->|"❌ заблоковано"| HIDDEN["insert(0,x), del[i]"]
    end

    subgraph VISITOR["Паттерн Відвідувач (Tree)"]
        TREE["TreeNode\n(лише дані + зв'язки)"] -->|"accept"| VIS["NodeVisitor\n(бізнес-логіка)"]
        VIS --> SV["SizeVisitor"]
        VIS --> PV["PrintVisitor"]
        VIS --> XV["XMLVisitor"]
    end

    subgraph ITERATOR["Паттерн Ітератор"]
        STRUCT["Структура даних\n__iter__()"] -->|"yield data"| GEN["Генератор\n(приховує Node)"] -->|"next()"| CL["for x in obj"]
    end

    style ADAPTER fill:#e8f5e9,stroke:#4CAF50
    style VISITOR fill:#e8eaf6,stroke:#3F51B5
    style ITERATOR fill:#fff3e0,stroke:#FF9800
```

---

## 11. Де Застосовуються Зв'язні Списки: Реальні Приклади

```mermaid
mindmap
  root((Linked List\nу реальному світі))
    OS / Системи
      Управління процесами ОС
      Файлова система FAT
      Управління пам'яттю heap
    Python stdlib
      collections.deque
      queue.Queue
      asyncio event loop
    Алгоритми
      LRU Cache
      DFS via explicit stack
      BFS via queue
      Граф adjacency list
    Веб / Бек
      Черга HTTP-запитів
      Celery task queue
      Redis list
    Апаратне забезпечення
      Буфер клавіатури
      DMA scatter-gather
      Network packet queue
```

---

## 12. Еволюція Структур: Від Лінійних до Ієрархічних

```mermaid
flowchart TD
    NODE["🔷 Node\n(data + pointer)"]

    NODE -->|"+next"| SLL["Singly Linked List\n→→→"]
    NODE -->|"+next +prev"| DLL["Doubly Linked List\n←→←→"]
    NODE -->|"+left +right"| BST["Binary Search Tree\n(наступний урок)"]
    NODE -->|"+children[]"| TREE["N-арне Дерево"]
    NODE -->|"+neighbors{}"| GRAPH["Граф"]

    SLL -->|"maxlen="| CIRC["Кільцевий буфер\ncollections.deque(maxlen=N)"]
    DLL -->|"optimized in C"| DEQUE["collections.deque"]

    style NODE fill:#fff9c4,stroke:#FFC107,stroke-width:2px
    style BST fill:#fce4ec,stroke:#E91E63
    style DEQUE fill:#e8f5e9,stroke:#4CAF50
```

**Головний інсайт:** Розуміння Node → розуміння будь-якої нелінійної структури даних.
Дерева, графи, хеш-таблиці з chaining — всі побудовані на тому самому принципі вузлів і вказівників.

---

*Урок 24 · Module 3 · Python Advanced · Viktor Nikoriak*
