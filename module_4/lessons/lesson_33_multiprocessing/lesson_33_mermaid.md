# Урок 33 — Mermaid Діаграми

## Діаграма 1: fork() — Клітинний поділ пам'яті

```mermaid
flowchart TD
    A["🐍 Python Process\ncounter = 0\nGIL\nHeap"] -->|"fork()"| B
    A -->|"fork()"| C

    B["👨 Parent Process\nPID: 1000\nCPU Core 1\ncounter = 0\nGIL (original)\nHeap (original)"]
    C["👶 Child Process\nPID: 1001\nCPU Core 2\ncounter = 0\nGIL (copy!)\nHeap (ISOLATED!)"]

    C -->|"counter += 1"| D["Child: counter = 1\n(лише у своїй пам'яті)"]
    D -->|"Process завершується"| E["Пам'ять дитини знищена"]
    B -->|"p.join() завершено"| F["Parent: counter = 0\n(незмінний!)"]

    style A fill:#4A90D9,color:#fff
    style B fill:#27AE60,color:#fff
    style C fill:#E67E22,color:#fff
    style D fill:#E67E22,color:#fff
    style E fill:#E74C3C,color:#fff
    style F fill:#27AE60,color:#fff
```

---

## Діаграма 2: GIL та CPU Cores

```mermaid
flowchart LR

    classDef thread fill:#FFE0B2,stroke:#FB8C00,color:#000
    classDef process fill:#E8F5E9,stroke:#43A047,color:#000
    classDef gil fill:#FFCDD2,stroke:#E53935,color:#000
    classDef result fill:#E3F2FD,stroke:#1E88E5,color:#000

    %% ===== THREADING =====
    subgraph THREADING["🧵 Threading"]
        direction TB

        T1["Thread 1"]:::thread
        T2["Thread 2"]:::thread

        GIL["🔒 One Global GIL"]:::gil

        T1 <--> GIL
        T2 <--> GIL
    end

    %% ===== MULTIPROCESSING =====
    subgraph MULTIPROC["⚙️ Multiprocessing"]
        direction TB

        P1["Process 1\nOwn GIL\nCPU Core 1"]:::process

        P2["Process 2\nOwn GIL\nCPU Core 2"]:::process
    end

    THREADING -->|"CPU-bound\ncontext switching"| O1["⚠️ Limited Parallelism"]:::result

    MULTIPROC -->|"True Parallel CPU Execution"| O2["✅ Real Parallelism"]:::result
```

---

## Діаграма 3: IPC Pipeline — Як дані подорожують між процесами

```mermaid
sequenceDiagram
    participant P as Producer Process<br/>(User Space)
    participant K as OS Kernel Space<br/>(Pipe Buffer)
    participant C as Consumer Process<br/>(User Space)

    Note over P: data = {"task_id": 42}
    P->>P: pickle.dumps(data)<br/>→ 0x80 0x03 0x7D...
    P->>K: write(bytes) → OS Pipe
    Note over K: ~80 KB bytes buffered

    Note over C: q.get() → blocking I/O
    C->>K: read() [process SLEEPS]
    K-->>C: bytes повернуто
    C->>C: pickle.loads(bytes)<br/>→ {"task_id": 42}
    Note over C: Об'єкт відновлено<br/>в новій адресній зоні
```

---

## Діаграма 4: ProcessPoolExecutor Lifecycle

```mermaid
sequenceDiagram
    participant M as Main Process
    participant OS as OS Scheduler
    participant W1 as Worker 1
    participant W2 as Worker 2
    participant W3 as Worker 3
    participant W4 as Worker 4

    M->>OS: ProcessPoolExecutor(max_workers=4)
    OS->>W1: fork() / spawn()
    OS->>W2: fork() / spawn()
    OS->>W3: fork() / spawn()
    OS->>W4: fork() / spawn()
    Note over W1,W4: while True: wait(pipe)

    M->>W1: pickle(task_0) → pipe
    M->>W2: pickle(task_1) → pipe
    M->>W3: pickle(task_2) → pipe
    M->>W4: pickle(task_3) → pipe

    W1-->>M: pickle(result_0) ← pipe
    W2-->>M: pickle(result_1) ← pipe
    W3-->>M: pickle(result_2) ← pipe
    W4-->>M: pickle(result_3) ← pipe

    Note over M: exit 'with' block
    M->>W1: "poison pill" → pipe
    M->>W2: "poison pill" → pipe
    M->>W3: "poison pill" → pipe
    M->>W4: "poison pill" → pipe

    W1->>OS: exit() voluntarily
    W2->>OS: exit() voluntarily
    W3->>OS: exit() voluntarily
    W4->>OS: exit() voluntarily
    OS->>M: All children reaped ✓
```

---

## Діаграма 5: Future — State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING : executor.submit(task)
    PENDING --> RUNNING : Worker вибирає задачу
    PENDING --> CANCELLED : future.cancel() (тільки з черги!)
    RUNNING --> FINISHED : task повернув результат
    RUNNING --> FINISHED_ERROR : task кинув exception
    CANCELLED --> [*]
    FINISHED --> [*] : future.result() повертає значення
    FINISHED_ERROR --> [*] : future.result() кидає exception\n(або зникає якщо не викликали)

    note right of FINISHED_ERROR
        Небезпека: exception "заморожений"
        всередині Future об'єкта.
        Якщо result() не викликати —
        помилка зникає назавжди!
    end note
```

---

## Діаграма 6: Дерево рішень — Threading vs Multiprocessing

```mermaid
flowchart TD
    Start["Задача вимагає паралелізму?"]

    Start -->|Так| IOorCPU{"Тип задачі?"}
    Start -->|Ні| Sequential["sequential\n(звичайний цикл)"]

    IOorCPU -->|"I/O-bound\n(мережа, файли, БД)"| ThreadPool["ThreadPoolExecutor\nmax_workers = 10-50\nGIL відпускається під час I/O"]

    IOorCPU -->|"CPU-bound\n(математика, ML)"| DataSize{"Розмір даних?"}

    DataSize -->|"Маленький\n(< 1 MB на задачу)"| ProcessPool["ProcessPoolExecutor\nmax_workers = os.cpu_count()\nВласний GIL на core"]

    DataSize -->|"Великий\n(> 10 MB на задачу)"| SerializationCheck{"Вартість pickle\n< вартості обчислень?"}

    SerializationCheck -->|"Так"| ProcessPool
    SerializationCheck -->|"Ні (обчислення швидкі)"| ThreadPool2["ThreadPoolExecutor\n(або Sequential!)"]

    ThreadPool --> Verify1["✅ timeout= у кожному запиті\n✅ try/except на future.result()"]
    ProcessPool --> Verify2["✅ if __name__ == main\n✅ лише прості типи в IPC\n✅ join() для всіх процесів"]

    style Sequential fill:#95A5A6,color:#fff
    style ThreadPool fill:#3498DB,color:#fff
    style ThreadPool2 fill:#3498DB,color:#fff
    style ProcessPool fill:#27AE60,color:#fff
    style Verify1 fill:#D5E8D4
    style Verify2 fill:#D5E8D4
```

---

## Діаграма 7: Серіалізація vs Обчислення (Коли ProcessPool програє)

```mermaid
xychart-beta
    title "Час виконання: ThreadPool vs ProcessPool"
    x-axis ["simple sum\n(tiny)", "sum(range 10K)", "sum(range 100K)", "ML inference\n(heavy)"]
    y-axis "Відносний час (1.0 = sequential)" 0 --> 3
    bar [1.2, 0.9, 0.5, 0.25]
    line [0.15, 0.4, 0.8, 1.8]
```

> **Синя лінія** = ProcessPool (pickle overhead домінує на простих задачах)  
> **Зелені стовпці** = ThreadPool (стабільно для I/O-bound)  
> Точка перетину: ProcessPool виграє тільки коли обчислення складні

---

## Діаграма 8: Windows Spawn Bomb (без `__name__` guard)

```mermaid
flowchart TD
    A["Запускаємо script.py\n(Parent Process)"] -->|"spawn()"| B["New Python Interpreter\nimports script.py..."]
    B -->|"module-level код\nProcess().start()"| C["spawn() знову!"]
    C -->|"spawn()"| D["New Python Interpreter\nimports script.py..."]
    D -->|"Process().start()"| E["spawn() знову!"]
    E --> F["... нескінченно ..."]

    style A fill:#27AE60,color:#fff
    style B fill:#E67E22,color:#fff
    style C fill:#E74C3C,color:#fff
    style D fill:#E74C3C,color:#fff
    style E fill:#E74C3C,color:#fff
    style F fill:#C0392B,color:#fff

    G["ВИПРАВЛЕННЯ:\nif __name__ == '__main__':\n    Process().start()"] -->|"тільки оригінальний\nbатьківський процес\nвиконує цей блок"| H["✅ Одна ітерація,\nнемає рекурсії"]

    style G fill:#2ECC71,color:#fff
    style H fill:#27AE60,color:#fff
```
