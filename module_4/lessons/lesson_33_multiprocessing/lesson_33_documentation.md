# Урок 33 — Multiprocessing: Справжній Паралелізм та Executor Architecture

**Модуль:** 4 — Network & Concurrent Systems  
**Складність:** intermediate  
**Мова:** Українська  
**Попередній урок:** Урок 32 — Threading & Concurrency  
**Наступний урок:** Урок 34 — asyncio

---

## Про цей урок

Урок будується на 5 хибних уявленнях (misconceptions), які є найпоширенішими серед Python-розробників при роботі з `multiprocessing`. Кожна вправа провокує інтуїтивно неправильну відповідь, а потім пояснює реальну поведінку через призму OS-архітектури.

---

## Learning Objectives

### Conceptual Understanding
- Пояснити різницю між Thread та Process на рівні адресних просторів ОС
- Описати що відбувається коли Python викликає `fork()` vs `spawn()`
- Пояснити чому `multiprocessing` не вирішує проблему спільної пам'яті
- Описати механізм IPC (Inter-Process Communication) через OS Pipe
- Пояснити коли `multiprocessing` уповільнює програму

### Debugging Skills
- Передбачити вивід коду з ізоляцією пам'яті
- Визначити коли `pickle` призводить до `TypeError`
- Розпізнати Zombie Process та CPU Oversubscription
- Знайти причину `RuntimeError` при запуску на Windows

### Production Skills
- Правильно використовувати `ProcessPoolExecutor` для CPU-bound задач
- Використовувати `ThreadPoolExecutor` для I/O-bound задач
- Розуміти `Future` об'єкти та `as_completed()`
- Писати безпечний код з `if __name__ == '__main__':` guard

---

## Ключові концепції

### 1. Ізоляція пам'яті (Memory Isolation)

Це найважливіша концепція уроку. Коли Python викликає `multiprocessing.Process`, операційна система виконує `fork()` (Unix) або `spawn()` (Windows):

**fork() (Unix/macOS):**
- ОС миттєво дублює весь адресний простір батьківського процесу (Copy-on-Write)
- Дочірній процес отримує повну копію всіх змінних
- Зміни в дочірньому процесі НЕ видимі батьківському

**spawn() (Windows):**
- ОС запускає новий Python-інтерпретатор "з нуля"
- Імпортує target-скрипт
- Через pickle передає функцію та аргументи

**Наслідок:** глобальні змінні, змінені в дочірньому процесі, не впливають на батьківський.

### 2. GIL та CPU-bound задачі

**GIL (Global Interpreter Lock)** — м'ютекс CPython, що захищає reference counting.

Для CPU-bound задач:
- `threading` — потоки по черзі захоплюють GIL → overhead від context switch → програма **повільніша**
- `multiprocessing` — кожен процес має власний GIL → справжній паралелізм → **вдвічі швидше**

### 3. IPC та вартість серіалізації (pickle)

Оскільки процеси ізольовані, вони обмінюються даними через OS Pipe:
1. `pickle.dumps(obj)` — Python-об'єкт → байтовий потік
2. Байти записуються в OS Pipe (Kernel Space)
3. Дочірній процес отримує байти з pipe
4. `pickle.loads(bytes)` — байти → Python-об'єкт

**Критичне правило:** якщо вартість pickle+IPC перевищує вартість обчислень → `multiprocessing` ПОВІЛЬНІШИЙ.

### 4. Executor Architecture (concurrent.futures)

`concurrent.futures` надає єдиний інтерфейс для threading та multiprocessing:

```python
# Однаковий код, різна реалізація:
with ThreadPoolExecutor(max_workers=4) as executor:   # потоки
    results = list(executor.map(task, data))

with ProcessPoolExecutor(max_workers=4) as executor:  # процеси
    results = list(executor.map(task, data))
```

**Executor lifecycle:**
1. `with` відкривається → ОС створює N worker-потоків/процесів
2. `submit(task)` → задача в чергу, повертає `Future` негайно
3. Worker бере задачу, виконує
4. `with` закривається → `shutdown(wait=True)` → чекає всіх workers
5. Всі завершились → пул знищено

### 5. Future об'єкти

`Future` — проксі-об'єкт для обчислення, що не завершилось:
- `future.done()` — чи завершено
- `future.result()` — отримати результат (БЛОКУЄ main thread!)
- `future.cancel()` — скасувати (тільки якщо ще в черзі)
- `concurrent.futures.as_completed(futures)` — ітерувати по мірі готовності

**Небезпека:** Exception "заморожується" всередині Future. Якщо не викликати `future.result()` — помилка зникає назавжди.

---

## 5 Типових помилок

### Помилка 1: Missing `__name__` guard (Windows)
```python
# НЕПРАВИЛЬНО
p = Process(target=worker)
p.start()  # RuntimeError на Windows!

# ПРАВИЛЬНО
if __name__ == '__main__':
    p = Process(target=worker)
    p.start()
    p.join()
```

### Помилка 2: Pickle Error
```python
# Не можна передати в Process:
# - socket objects
# - lambda functions
# - generators
# - open file handles

# Перевірка:
import pickle
pickle.dumps(my_obj)  # якщо падає -> Process не прийме
```

### Помилка 3: Zombie Processes
```python
# НЕПРАВИЛЬНО
for i in range(100):
    p = Process(target=task)
    p.start()
    # Забули join() -> 100 zombies!

# ПРАВИЛЬНО
processes = [Process(target=task) for _ in range(100)]
for p in processes: p.start()
for p in processes: p.join()  # ОС прибирає записи
```

### Помилка 4: JoinableQueue Deadlock
```python
# НЕПРАВИЛЬНО
def worker(q):
    item = q.get()
    process(item)
    # Забули: q.task_done() -> q.join() зависне!

# ПРАВИЛЬНО
def worker(q):
    item = q.get()
    try:
        process(item)
    finally:
        q.task_done()  # Гарантовано навіть при exception
```

### Помилка 5: CPU Oversubscription
```python
# НЕПРАВИЛЬНО: 1000 процесів на 4 cores
with ProcessPoolExecutor(max_workers=1000) as ex:
    results = ex.map(cpu_task, data)

# ПРАВИЛЬНО
import os
with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
    results = ex.map(cpu_task, data)
```

---

## Дерево рішень

```
Задача паралельна?
        |
    Так |
        +-- I/O-bound (мережа, файли, БД)?
        |         +--> ThreadPoolExecutor
        |              (GIL відпускається під час I/O)
        |
        +-- CPU-bound (математика, ML, обробка)?
                  +--> ProcessPoolExecutor
                       (власний GIL на кожен core)
                            |
                            +-- Дані прості (int, str)?  -> OK
                            +-- Дані складні (socket, lambda)? -> PickleError!
```

---

## 5 Золотих правил

1. Завжди `if __name__ == '__main__':` для multiprocessing на Windows
2. Ніколи не передавай socket/lambda/відкриті файли в Process — лише прості типи
3. Завжди `p.join()` або context manager (запобігає zombie-процесам)
4. `max_workers` для CPU-bound ≤ `os.cpu_count()`
5. Передавай мінімум даних через IPC — id замість цілого об'єкта

---

## Технологічний стек

| Модуль | Призначення |
|--------|-------------|
| `multiprocessing` | Низькорівнева робота з процесами |
| `multiprocessing.Queue` | IPC через OS Pipe |
| `multiprocessing.Value` + `Lock` | Спільна пам'ять між процесами |
| `concurrent.futures.ThreadPoolExecutor` | I/O-bound задачі |
| `concurrent.futures.ProcessPoolExecutor` | CPU-bound задачі |
| `concurrent.futures.as_completed` | Обробка результатів по мірі готовності |
| `pickle` | Серіалізація Python-об'єктів для IPC |
| `os.cpu_count()` | Визначення оптимальної кількості workers |

---

## Зв'язки з іншими уроками

- **Урок 32 (Threading):** GIL, race conditions, Lock — base для розуміння чому multiprocessing потрібен
- **Урок 34 (asyncio):** кооперативна конкурентність для I/O-bound — альтернатива threading
- **Урок 31 (HTTP Requests):** `requests.get()` блокує — ThreadPool вирішує цю проблему

---

## Keywords

`multiprocessing`, `threading`, `GIL`, `IPC`, `pickle`, `ProcessPoolExecutor`,
`ThreadPoolExecutor`, `concurrent.futures`, `Future`, `zombie-process`, `fork`,
`spawn`, `cpu-bound`, `io-bound`, `context-switch`, `OS-pipe`, `serialization`

---

# Mermaid Діаграми

## Діаграма 1: fork() — Клітинний поділ пам'яті

```mermaid
flowchart TD
    A["Python Process\ncounter = 0\nGIL\nHeap"] -->|"fork()"| B
    A -->|"fork()"| C

    B["Parent Process\nPID: 1000\nCPU Core 1\ncounter = 0\nGIL (original)\nHeap (original)"]
    C["Child Process\nPID: 1001\nCPU Core 2\ncounter = 0\nGIL (copy!)\nHeap (ISOLATED!)"]

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

## Діаграма 2: GIL та CPU Cores — Threading vs Multiprocessing

```mermaid
flowchart LR
    subgraph threading["Threading (один GIL)"]
        direction TB
        T1["Thread 1\n(чекає GIL)"]
        T2["Thread 2\n(чекає GIL)"]
        GIL["GIL (єдиний)"]
        T1 <-->|"захоплення/звільнення"| GIL
        T2 <-->|"захоплення/звільнення"| GIL
    end

    subgraph mp["Multiprocessing (кожен має GIL)"]
        direction TB
        P1["Process 1\nCore 1\nGIL₁ (власний)"]
        P2["Process 2\nCore 2\nGIL₂ (власний)"]
    end

    threading -.->|"CPU-bound: overhead"| R1["Повільніше!"]
    mp -.->|"Справжній паралелізм"| R2["Швидше!"]

    style threading fill:#FFE0B2
    style mp fill:#E8F5E9
    style R1 fill:#FFCDD2
    style R2 fill:#C8E6C9
```

---

## Діаграма 3: IPC Pipeline — Як дані подорожують між процесами

```mermaid
sequenceDiagram
    participant P as Producer Process (User Space)
    participant K as OS Kernel Space (Pipe Buffer)
    participant C as Consumer Process (User Space)

    Note over P: data = {"task_id": 42}
    P->>P: pickle.dumps(data) -> bytes
    P->>K: write(bytes) -> OS Pipe
    Note over K: bytes buffered

    Note over C: q.get() -> blocking I/O
    C->>K: read() [process SLEEPS]
    K-->>C: bytes повернуто
    C->>C: pickle.loads(bytes) -> dict
    Note over C: Об'єкт відновлено в новій адресній зоні
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

    M->>W1: pickle(task_0) pipe
    M->>W2: pickle(task_1) pipe
    M->>W3: pickle(task_2) pipe
    M->>W4: pickle(task_3) pipe

    W1-->>M: pickle(result_0)
    W2-->>M: pickle(result_1)
    W3-->>M: pickle(result_2)
    W4-->>M: pickle(result_3)

    Note over M: exit 'with' block
    M->>W1: poison pill
    M->>W2: poison pill
    M->>W3: poison pill
    M->>W4: poison pill

    W1->>OS: exit() voluntarily
    W2->>OS: exit() voluntarily
    W3->>OS: exit() voluntarily
    W4->>OS: exit() voluntarily
    OS->>M: All children reaped
```

---

## Діаграма 5: Future — State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING : executor.submit(task)
    PENDING --> RUNNING : Worker вибирає задачу
    PENDING --> CANCELLED : future.cancel() (тільки з черги)
    RUNNING --> FINISHED : task повернув результат
    RUNNING --> FINISHED_ERROR : task кинув exception
    CANCELLED --> [*]
    FINISHED --> [*] : future.result() повертає значення
    FINISHED_ERROR --> [*] : future.result() кидає exception
```

---

## Діаграма 6: Дерево рішень

```mermaid
flowchart TD
    Start["Задача вимагає паралелізму?"]

    Start -->|Так| IOorCPU{"Тип задачі?"}
    Start -->|Ні| Sequential["sequential\n(звичайний цикл)"]

    IOorCPU -->|"I/O-bound\n(мережа, файли, БД)"| ThreadPool["ThreadPoolExecutor\nmax_workers = 10-50\nGIL відпускається під час I/O"]

    IOorCPU -->|"CPU-bound\n(математика, ML)"| DataSize{"Розмір переданих даних?"}

    DataSize -->|"Малий (< 1 MB)"| ProcessPool["ProcessPoolExecutor\nmax_workers = os.cpu_count()\nВласний GIL на core"]

    DataSize -->|"Великий (> 10 MB)"| SerCheck{"Вартість pickle\n< вартості обчислень?"}

    SerCheck -->|"Так"| ProcessPool
    SerCheck -->|"Ні"| ThreadPool2["ThreadPoolExecutor\n(або Sequential)"]

    ThreadPool --> V1["timeout= у запитах\ntry/except на result()"]
    ProcessPool --> V2["if __name__ guard\nтільки прості типи в IPC\njoin() для всіх процесів"]

    style Sequential fill:#95A5A6,color:#fff
    style ThreadPool fill:#3498DB,color:#fff
    style ThreadPool2 fill:#3498DB,color:#fff
    style ProcessPool fill:#27AE60,color:#fff
    style V1 fill:#D5E8D4
    style V2 fill:#D5E8D4
```

---

## Діаграма 7: Flood Response Hybrid Pipeline Architecture

```mermaid
flowchart LR
    subgraph input["Input: 500 Sentinel-1 Tiles"]
        T1["Tile 001"] 
        T2["Tile 002"]
        TN["Tile 500"]
    end

    subgraph stage1["Stage 1: Download\nThreadPoolExecutor(10)\nI/O-bound"]
        DL["HTTP requests\nCopernicus Hub"]
    end

    subgraph stage2["Stage 2: SAR Analysis\nProcessPoolExecutor(4)\nCPU-bound"]
        P1["Core 1\nWorker"]
        P2["Core 2\nWorker"]
        P3["Core 3\nWorker"]
        P4["Core 4\nWorker"]
    end

    subgraph stage3["Stage 3: Save\nThreadPoolExecutor(5)\nI/O-bound"]
        DB["PostGIS\nINSERT"]
    end

    output["Flood Map\nDSNS Alert"]

    input --> stage1 --> stage2 --> stage3 --> output

    style stage1 fill:#E3F2FD
    style stage2 fill:#E8F5E9
    style stage3 fill:#E3F2FD
    style output fill:#FFCDD2
```

---

## Діаграма 8: Windows Spawn Bomb

```mermaid
flowchart TD
    A["Запускаємо script.py\n(Parent Process)"] -->|"spawn()"| B["New Python Interpreter\nimports script.py..."]
    B -->|"module-level: Process().start()"| C["spawn() знову!"]
    C -->|"spawn()"| D["New Python Interpreter\nimports script.py..."]
    D -->|"Process().start()"| E["spawn() знову!"]
    E --> F["нескінченно..."]

    style A fill:#27AE60,color:#fff
    style B fill:#E67E22,color:#fff
    style C fill:#E74C3C,color:#fff
    style D fill:#E74C3C,color:#fff
    style E fill:#E74C3C,color:#fff
    style F fill:#C0392B,color:#fff

    G["ВИПРАВЛЕННЯ:\nif __name__ == main:\n    Process().start()"] -->|"тільки батьківський\nпроцес виконує блок"| H["Одна ітерація — OK"]

    style G fill:#2ECC71,color:#fff
    style H fill:#27AE60,color:#fff
```
