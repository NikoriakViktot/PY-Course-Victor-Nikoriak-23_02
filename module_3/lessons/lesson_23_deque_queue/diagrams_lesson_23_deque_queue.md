# Урок 23 — Діаграми: Stack, Queue, Deque

Мermaid-схеми для візуалізації потоку даних у стеках, чергах та двосторонніх чергах.

---

## 1. Stack (LIFO) — Потік «Переривання»

```mermaid
flowchart TB
    subgraph stack["🗂 Stack (LIFO — Last-In, First-Out)"]
        direction TB
        T3["[TOP] Task C: ТЕРМІНОВО 🔴"]
        T2["      Task B: виправити баг"]
        T1["[BOT] Task A: написати тести"]
    end

    PUSH["append(item)"] -->|"O(1) — додаємо зверху"| T3
    T3 -->|"O(1) — знімаємо зверху"| POP["pop() → Task C"]

    style T3 fill:#FF6B6B,color:#fff
    style T2 fill:#FFB347,color:#000
    style T1 fill:#98D8C8,color:#000
    style PUSH fill:#4ECDC4,color:#fff
    style POP  fill:#FF6B6B,color:#fff
```

---

## 2. Queue (FIFO) — Потік «Справедливість»

```mermaid
flowchart LR
    IN["append(item)\nO(1)"]

    subgraph queue["🚶 Queue (FIFO — First-In, First-Out)"]
        direction LR
        R1["Request-001\n(найстаріший)"]
        R2["Request-002"]
        R3["Request-003"]
        R4["Request-004\n(найновіший)"]
        R1 --- R2 --- R3 --- R4
    end

    OUT["popleft()\nO(1) → Request-001"]

    IN -->|"ENQUEUE\n(в кінець)"| R4
    R1 -->|"DEQUEUE\n(з початку)"| OUT

    style R1 fill:#4ECDC4,color:#000
    style R4 fill:#FFB347,color:#000
    style IN  fill:#4ECDC4,color:#fff
    style OUT fill:#FF6B6B,color:#fff
```

---

## 3. Деградація list при використанні як черга

```mermaid
flowchart LR
    subgraph before["Список до pop(0): 1M елементів"]
        direction LR
        E0["[0]\nFirst"]:::highlight
        E1["[1]"]
        E2["[2]"]
        EN["...\n[999999]"]
        E0 --- E1 --- E2 --- EN
    end

    subgraph after["Після pop(0): потрібно зсунути 999999 елементів!"]
        direction LR
        A0["[0]\n← shift"]
        A1["[1]\n← shift"]
        AN["...\n← shift"]
        A0 --- A1 --- AN
    end

    before -->|"❌ O(n) зсув усіх елементів"| after

    classDef highlight fill:#FF6B6B,color:#fff
    style before fill:#fff5f5
    style after  fill:#fff5f5
```

### Рішення: `deque.popleft()` — O(1)

```mermaid
flowchart LR
    subgraph deque_mem["deque: doubly-linked list"]
        direction LR
        HEAD["HEAD\nvказівник"]
        N1["Node\nFirst\n⟷"]:::highlight
        N2["Node\n..."]
        N3["Node\nLast"]
        TAIL["TAIL\nvказівник"]
        HEAD -->|ptr| N1
        N1 -->|next| N2
        N2 -->|next| N3
        N3 -->|ptr| TAIL
    end

    OUT["popleft()\n→ First"]

    N1 -->|"✅ лише переключити HEAD ptr\nO(1)"| OUT

    classDef highlight fill:#4ECDC4,color:#000
    style OUT fill:#4ECDC4,color:#fff
```

---

## 4. Deque — Двосторонній Потік

```mermaid
flowchart LR
    AL["appendleft(x)\nO(1)"] -->|"← лівий кінець"| LEFT

    subgraph deque["🃏 deque (Double-Ended Queue)"]
        direction LR
        LEFT["[LEFT]\nelem_1"]
        E2["elem_2"]
        E3["elem_3"]
        RIGHT["[RIGHT]\nelem_N"]
        LEFT --- E2 --- E3 --- RIGHT
    end

    RIGHT -->|"правий кінець →"| AR["append(x)\nO(1)"]
    LEFT  -->|"← лівий кінець"| PL["popleft()\nO(1)"]
    RIGHT -->|"правий кінець →"| PR["pop()\nO(1)"]

    style LEFT  fill:#4ECDC4,color:#000
    style RIGHT fill:#FFB347,color:#000
    style AL fill:#4ECDC4,color:#fff
    style PL fill:#4ECDC4,color:#fff
    style AR fill:#FFB347,color:#000
    style PR fill:#FFB347,color:#000
```

---

## 5. Circular Buffer (maxlen=5)

```mermaid
flowchart LR
    subgraph full["Буфер повний (maxlen=5)"]
        direction LR
        B1["log_1\n(найстаріший)"]:::old
        B2["log_2"]
        B3["log_3"]
        B4["log_4"]
        B5["log_5\n(найновіший)"]
        B1 --- B2 --- B3 --- B4 --- B5
    end

    NEW["append(log_6)"]

    subgraph after["Після append(log_6)"]
        direction LR
        C2["log_2"]
        C3["log_3"]
        C4["log_4"]
        C5["log_5"]
        C6["log_6\n(новий)"]:::new
        C2 --- C3 --- C4 --- C5 --- C6
    end

    full -->|"log_1 автоматично\nвидаляється ✅ O(1)"| after
    NEW --> after

    classDef old fill:#FF6B6B,color:#fff
    classDef new fill:#4ECDC4,color:#000
```

---

## 6. Call Stack — Рекурсія fact(3)

```mermaid
sequenceDiagram
    participant Main
    participant fact3 as fact(3)
    participant fact2 as fact(2)
    participant fact1 as fact(1)

    Main->>fact3: виклик fact(3)
    Note over fact3: PUSH frame: n=3
    fact3->>fact2: виклик fact(2)
    Note over fact2: PUSH frame: n=2
    fact2->>fact1: виклик fact(1)
    Note over fact1: PUSH frame: n=1 (BASE CASE)
    fact1-->>fact2: return 1
    Note over fact2: POP frame → n=2, result=2*1=2
    fact2-->>fact3: return 2
    Note over fact3: POP frame → n=3, result=3*2=6
    fact3-->>Main: return 6
```

---

## 7. DFS vs BFS — Порядок обходу

```mermaid
flowchart TD
    A(("A"))
    B(("B"))
    C(("C"))
    D(("D"))
    E(("E"))
    F(("F"))
    G(("G"))

    A --- B
    A --- C
    B --- D
    B --- E
    C --- F
    C --- G

    subgraph DFS_order["DFS (Stack/LIFO) — занурення"]
        direction LR
        D1(("1\nA")):::dfs --- D2(("2\nB")):::dfs --- D3(("3\nD")):::dfs --- D4(("4\nE")):::dfs --- D5(("5\nC")):::dfs --- D6(("6\nF")):::dfs --- D7(("7\nG")):::dfs
    end

    subgraph BFS_order["BFS (Queue/FIFO) — рівні"]
        direction LR
        B1(("1\nA")):::bfs --- B2(("2\nB")):::bfs --- B3(("3\nC")):::bfs --- B4(("4\nD")):::bfs --- B5(("5\nE")):::bfs --- B6(("6\nF")):::bfs --- B7(("7\nG")):::bfs
    end

    classDef dfs fill:#FF6B6B,color:#fff
    classDef bfs fill:#4ECDC4,color:#000
```

---

## 8. Порівняльна таблиця: list vs deque vs queue.Queue

```mermaid
quadrantChart
    title Структури даних: Швидкість vs Безпека
    x-axis "Повільні кінцеві операції" --> "Швидкі кінцеві операції O(1)"
    y-axis "Однопотокова" --> "Багатопотокова (Thread-Safe)"
    quadrant-1 "черги у конкурентних системах"
    quadrant-2 "Безпечна але повільна"
    quadrant-3 "Повільна і небезпечна"
    quadrant-4 "Швидка, однопотокова"
    "list черга": [0.1, 0.15]
    deque: [0.85, 0.45]
    "queue.Queue": [0.65, 0.9]
    "list як стек": [0.9, 0.3]
```

---

## 9. Producer-Consumer з `queue.Queue`

```mermaid
sequenceDiagram
    participant P as Producer Thread
    participant Q as queue.Queue
    participant W1 as Worker-1 Thread
    participant W2 as Worker-2 Thread

    P->>Q: put("Task-01")
    P->>Q: put("Task-02")
    P->>Q: put("Task-03")

    Q-->>W1: get() → "Task-01" (блокує, якщо черга порожня)
    Q-->>W2: get() → "Task-02"

    Note over W1: Обробка Task-01
    Note over W2: Обробка Task-02

    W1->>Q: task_done()
    W2->>Q: task_done()

    Q-->>W1: get() → "Task-03"
    Note over W1: Обробка Task-03
    W1->>Q: task_done()
```

---

## 10. Архітектурне рішення: коли що використовувати

```mermaid
flowchart TD
    START([Вибір структури даних]) --> Q1{"Потрібен доступ за індексом data[i] часто?"}

    Q1 -->|Так| LIST["list: O(1) random access"]
    Q1 -->|Ні| Q2{"Операції тільки на одному кінці?"}

    Q2 -->|"Stack"| LIST_STACK["list як Stack: append/pop O(1)"]
    Q2 -->|"Deque"| Q3{"Фіксований розмір буфера?"}

    Q3 -->|Так| DEQUE_MAX["deque(maxlen=N): circular buffer"]
    Q3 -->|Ні| Q4{"Потрібна багатопоточність?"}

    Q4 -->|Ні| DEQUE["deque: append + popleft O(1)"]
    Q4 -->|Так| QUEUE_Q["queue.Queue: thread-safe"]

    style LIST fill:#4ECDC4,color:#000
    style LIST_STACK fill:#4ECDC4,color:#000
    style DEQUE fill:#4ECDC4,color:#000
    style DEQUE_MAX fill:#FFB347,color:#000
    style QUEUE_Q fill:#98D8C8,color:#000 fill:#98D8C8,color:#000
```
