# Діаграми — Урок 25: Алгоритми пошуку та хешування

---

## 1. Дві Фундаментальні Стратегії Пошуку

```mermaid
flowchart TD

    INPUT["Ключ пошуку"]

    subgraph NAV["Стратегія A: навігація по даних"]
        direction LR
        L1["Лінійний<br>O(n)"]
        L2["Бінарний<br>O(log n)"]
        L1 -->|"Покращення: сортуємо"| L2
    end

    subgraph TELE["Стратегія B: хешування"]
        H1["Хешування<br>O(1)"]
    end

    RESULT["Результат ✓"]

    INPUT --> NAV
    INPUT --> TELE

    NAV -->|"Порівняння елементів"| RESULT
    TELE -->|"Обчислюємо адресу"| RESULT

    %% ---- STYLE SYSTEM ----
    classDef nav fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef hash fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef io fill:#263238,stroke:#90a4ae,color:#ffffff;

    class INPUT,RESULT io;
    class NAV,L1,L2 nav;
    class TELE,H1 hash;
```

**Де використовується:**
- Лінійний: невідсортовані списки, малі об'єми
- Бінарний: відсортовані колекції, `bisect` модуль
- Хешування: `dict`, `set` — будь-який ключ → миттєво

---

## 2. Лінійний Пошук: Алгоритм O(n)

```mermaid
flowchart LR
    subgraph ARRAY["Масив: [10, 42, 7, 99, 55]<br>ціль = 99"]
        E0["10"] --> E1["42"] --> E2["7"] --> E3["99 ✓"] --> E4["55"]
    end

    subgraph STEPS["Кроки пошуку"]
        S1["10 == 99? → ні"]
        S2["42 == 99? → ні"]
        S3["7 == 99? → ні"]
        S4["99 == 99? → так → індекс = 3"]
        S1 --> S2 --> S3 --> S4
    end

    %% ---- STYLE SYSTEM ----
    classDef node fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    class E0,E1,E2,E4,S1,S2,S3 node;
    class E3,S4 success;
    class STEPS warning;
```

**Складність:** O(n) — у найгіршому випадку перевіряємо всі елементи

---

## 3. Бінарний Пошук: «Поділяй і Володарюй» O(log n)

```mermaid
flowchart TD
    START["Відсортований масив [2, 5, 8, 12, 16, 23, 38, 42, 56, 72, 91]\n target = 23\n low=0, high=10"]

    S1["mid=5 → 23<br>23 == 23 → FOUND ✓"]

    START --> S1

    %% ---- STYLE SYSTEM ----
    classDef info fill:#263238,stroke:#64b5f6,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;

    class START info;
    class S1 success;
```

```mermaid
flowchart TD
    START2["target = 16\n[2,5,8,12,16,23,38,42,56,72,91]\nlow=0, high=10"]

    ST1["mid=5 → 23\n16 < 23 → high=4"]
    ST2["mid=2 → 8\n16 > 8 → low=3"]
    ST3["mid=3 → 12\n16 > 12 → low=4"]
    ST4["mid=4 → 16\nFOUND ✓"]

    START2 --> ST1 --> ST2 --> ST3 --> ST4

    %% ---- STYLE SYSTEM ----
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;

    class START2,ST1,ST2,ST3 step;
    class ST4 success;
```
```mermaid
flowchart TD
    START["Start\nlow=0, high=n-1"]

    CHECK{"low ≤ high?"}
    MID["mid = (low+high)//2"]

    COMPARE{"arr[mid] ? target"}

    LEFT["target < arr[mid]\nhigh = mid - 1"]
    RIGHT["target > arr[mid]\nlow = mid + 1"]

    FOUND["FOUND ✓"]
    NOTFOUND["NOT FOUND"]

    START --> CHECK
    CHECK -->|yes| MID --> COMPARE
    CHECK -->|no| NOTFOUND

    COMPARE -->|==| FOUND
    COMPARE -->|<| LEFT --> CHECK
    COMPARE -->|>| RIGHT --> CHECK

    %% STYLE
    classDef step fill:#263238,stroke:#90a4ae,color:#fff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#fff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#fff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#fff;

    class START,MID,LEFT,RIGHT step;
    class CHECK,COMPARE decision;
    class FOUND success;
    class NOTFOUND error;
```


**Математика O(log n):**
```
n = 1 024 → максимум 10 кроків  (log₂(1024) = 10)
n = 1 000 000 → максимум 20 кроків
n = 1 000 000 000 → максимум 30 кроків
```

---

## 4. Архітектура Хеш-Таблиці

```mermaid
graph LR
    subgraph KEYS["Ключі"]
        K1["'apple'"]
        K2["'banana'"]
        K3["'grape'"]
    end

    subgraph HASH["Хеш-функція hash()"]
        HF["hash(key) % capacity\n→ bucket index"]
    end

    subgraph TABLE["Розріджений масив buckets"]
        B0["[0] None"]
        B1["[1] None"]
        B2["[2] ('apple', 5)"]
        B3["[3] ('banana', 3)"]
        B4["[4] None"]
        B5["[5] None"]
        B6["[6] ('grape', 12)"]
        B7["[7] None"]
    end

    K1 --> HASH --> B2
    K2 --> HASH --> B3
    K3 --> HASH --> B6

    classDef panel fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef hash fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef empty fill:#111827,stroke:#64b5f6,color:#ffffff;
    classDef filled fill:#1b5e20,stroke:#4CAF50,color:#ffffff;

    class KEYS,TABLE panel;
    class HASH,HF hash;
    class B0,B1,B4,B5,B7 empty;
    class B2,B3,B6 filled;
```

**Чому O(1)?** Ми **обчислюємо** індекс, а не **шукаємо** — один стрибок в пам'яті.

---

## 5. Внутрішній Процес Пошуку у Python `dict` (5 кроків)

```mermaid
flowchart TD
    START["my_dict[key]"]
    
    S1["Крок 1: hash_val = hash(key)"]
    S2["Крок 2: idx = hash_val & mask"]
    S3{"Крок 3: bucket[idx]?"}
    
    EMPTY["None (порожньо)"]
    MATCH["Key збігається"]
    COLLISION["Інший key (колізія)"]
    
    KEYERROR["KeyError або вставка"]
    RETURN["return value ✓"]
    
    S4["Probing:\nnew_idx = (5*idx + perturb + 1) % size"]

    START --> S1 --> S2 --> S3
    S3 --> EMPTY --> KEYERROR
    S3 --> MATCH --> RETURN
    S3 --> COLLISION --> S4
    S4 -->|"repeat"| S3

    %% ---- DESIGN SYSTEM ----
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    class START,S1,S2 step;
    class S3 decision;
    class RETURN success;
    class KEYERROR error;
    class S4 warning;
```

---

## 6. Колізії: Chaining vs Open Addressing

```mermaid
flowchart TD

    COLLISION["Колізія<br>hash('Alice') % 4 = 0<br>hash('Bob') % 4 = 0"]

    subgraph CHAIN["Метод ланцюжків (Chaining)<br>Java, Ruby"]
        CB0["bucket[0]: None"]
        CB2["bucket[2]: Alice → Bob → None"]
        CB4["bucket[4]: Carol → None"]
    end

    subgraph OPEN["Відкрита адресація<br>Python dict ✓"]
        OB0["bucket[0]: Alice"]
        OB1["bucket[1]: Bob (зсув через колізію)"]
        OB2["bucket[2]: None"]
        OB3["bucket[3]: Carol"]
    end

    COLLISION --> CHAIN
    COLLISION --> OPEN

    %% ---- STYLE SYSTEM ----
    classDef base fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef method fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef highlight fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    class COLLISION highlight;
    class CHAIN,OPEN method;
    class CB0,CB2,CB4,OB0,OB2,OB3 base;
    class OB1 highlight;
```

**Чому Python вибрав Open Addressing?**
- Немає накладних витрат на вказівники зв'язного списку
- Всі дані в одному суцільному масиві → CPU cache locality
- Псевдовипадкове зондування рівномірно розподіляє елементи

---

## 7. Hashable: Контракт `__hash__` + `__eq__`

```mermaid
graph TB
    subgraph CONTRACT["Контракт Hashable об'єкта"]
        R1["1. __hash__() → int\nЗначення НІКОЛИ не змінюється"]
        R2["2. __eq__() → bool\nКоректне порівняння"]
        R3["3. Золоте правило:\nякщо a == b → hash(a) == hash(b) ОБОВ'ЯЗКОВО"]
    end

    subgraph LOOKUP["Двоетапний пошук у dict"]
        L1["Крок 1: hash(key) → знаходимо bucket (O(1))"]
        L2["Крок 2: key == found_key (через __eq__) → вирішуємо колізії"]
        L1 --> L2
    end

    subgraph IMMUTABLE["Чому незмінність критична"]
        M1["my_list = [1, 2]\nd[my_list] = 'val'  → bucket #42"]
        M2["my_list.append(3)  → hash змінився!"]
        M3["d[my_list]  → шукає в bucket #99\n'val' назавжди загублено в bucket #42 ❌"]
        M1 --> M2 --> M3
        style M3 fill:#2a2a2a,stroke:#ff9800,color:#fff
    end

    CONTRACT --> LOOKUP
    CONTRACT --> IMMUTABLE
```

---

## 8. Компроміс: Пам'ять проти Швидкості

```mermaid
graph LR
    subgraph LIST["list (масив вказівників)"]
        LA["n=1000\n~8 KB"]
        LB["Пошук: O(n)"]
        LC["Вставка O(1) в кінець"]
    end

    subgraph DICT["dict (хеш-таблиця)"]
        DA["n=1000\n~36 KB (≈4.5x більше)"]
        DB["Пошук: O(1)"]
        DC["≥1/3 bucket порожні ЗАВЖДИ"]
    end

    TRADEOFF["⚖️ Компроміс:\nПам'ять ↑↑ → Час ↓↓"]

    LIST --- TRADEOFF
    DICT --- TRADEOFF

    classDef listStyle fill:#e3f2fd,stroke:#2196F3,color:#000;
    classDef dictStyle fill:#e8f5e9,stroke:#4CAF50,color:#000;

    class LIST listStyle;
    class DICT dictStyle;
```

**Rehashing (перебудова таблиці):**
```mermaid
flowchart LR
    A["load_factor > 0.67"] --> B["Виділяємо новий масив\n(capacity × 2)"]
    B --> C["Перехешовуємо ВСІ елементи\n(нові індекси через новий size)"]
    C --> D["Ітератори по старому масиву\nстають НЕВАЛІДНИМИ → RuntimeError"]
style D fill:#2a2a2a,stroke:#ff9800,color:#fff
```

---

## 9. Алгоритм Вибору Стратегії Пошуку

```mermaid
flowchart TD

    Q1{"Дані відсортовані?"}

    Q2{"Потрібна швидкість O(1)?"}
    Q3{"Часті повторні пошуки?"}
    Q4{"Ключі хешовані?"}

    R1["Лінійний пошук<br>list / in<br>O(n)"]
    R2["Бінарний пошук<br>bisect<br>O(log n)"]
    R3["dict / set<br>O(1) середнє"]

    Q1 -->|ні| Q2
    Q1 -->|так| Q3

    Q2 -->|ні| R1
    Q2 -->|так| Q4

    Q3 -->|ні| R1
    Q3 -->|так| R2

    Q4 -->|так| R3
    Q4 -->|ні| R2

    %% ---- STYLE SYSTEM ----
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef result1 fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef result2 fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef result3 fill:#1b5e20,stroke:#4CAF50,color:#ffffff;

    class Q1,Q2,Q3,Q4 decision;
    class R1 result1;
    class R2 result2;
    class R3 result3;
```

---

## 10. Порівняльна Складність: Повна Картина

```mermaid
graph TD
    subgraph COMPLEXITY["Складність операцій"]
        direction TB

        subgraph LINEAR["🟠 Лінійний пошук (list)"]
            LS1["Пошук: O(n)"]
            LS2["Пошук 1M елем: 1 000 000 кроків"]
        end

        subgraph BINARY["🟡 Бінарний пошук (bisect)"]
            BS1["Пошук: O(log n)"]
            BS2["Пошук 1M елем: ~20 кроків"]
            BS3["⚠️ Вимога: дані ВІДСОРТОВАНІ"]
        end

        subgraph HASH["🟢 Хешування (dict/set)"]
            HS1["Пошук: O(1) середнє"]
            HS2["Пошук 1M елем: ~1 крок"]
            HS3["⚠️ Ціна: пам'ять (sparse array)"]
            HS4["⚠️ Гірший випадок: O(n) (масові колізії)"]
        end
    end
```

---

## 11. Python `dict`: Порядок Вставки (CPython 3.7+)

```mermaid
graph LR

    subgraph OLD["До Python 3.6"]
        O1["Вставили:\n'banana', 'apple', 'cherry'"]
        O2["Ітерація:\n'apple', 'cherry', 'banana'\n(хаотичний порядок)"]
        O1 --> O2
    end

    subgraph NEW["Python 3.7+"]
        N1["Вставили:\n'banana', 'apple', 'cherry'"]
        N2["Ітерація:\n'banana', 'apple', 'cherry'\n(порядок збережено ✓)"]
        N1 --> N2
    end

    subgraph HOW["Як це працює (Compact Dict)"]
        H1["Index array:\n[None, 2, 0, 1, ...]"]
        H2["Data array:\n[('banana',3), ('apple',5), ('cherry',8)]"]
        H1 ---|"hash(key) → bucket → index → data"| H2
    end

    OLD --> HOW
    NEW --> HOW

    %% --- DESIGN SYSTEM ---
    classDef danger fill:#2a2a2a,stroke:#f44336,color:#fff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#fff;
    classDef neutral fill:#263238,stroke:#90a4ae,color:#fff;

    class OLD danger;
    class NEW success;
    class HOW neutral;
```

---

## 12. Реальні Застосування

```mermaid
graph TD
    ROOT["Пошук та Хешування\nу реальному світі"]

    ROOT --> BINARY["Бінарний пошук"]
    ROOT --> HASH["Хеш-таблиці"]
    ROOT --> LINEAR["Лінійний пошук"]
    ROOT --> COMBO["Комбінації"]

    BINARY --> B1["bisect"]
    BINARY --> B2["Відсортовані БД"]
    BINARY --> B3["Git blame/log"]
    BINARY --> B4["BST"]

    HASH --> H1["dict / set"]
    HASH --> H2["Кеш"]
    HASH --> H3["Індекс пошуку"]
    HASH --> H4["LRU"]
    HASH --> H5["DNS"]
    HASH --> H6["NLP частоти"]

    LINEAR --> L1["grep"]
    LINEAR --> L2["filter / find"]
    LINEAR --> L3["substring"]
    LINEAR --> L4["small data"]

    COMBO --> C1["hash + binary"]
    COMBO --> C2["LRU = dict + list"]
    COMBO --> C3["autocomplete"]
      
```

---

*Урок 25 · Module 3 · Python Advanced · Viktor Nikoriak*
