# Діаграми — Урок 27: Алгоритми сортування

---

## 1. Bubble Sort — «бульбашки» спливають вгору

```mermaid
graph LR
    classDef unsorted fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef swapped fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef sorted fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef pivot fill:#4e1f1f,stroke:#f44336,color:#ffffff;

    subgraph Pass1["Прохід 1: 8 «спливає» в кінець"]
        A1["5"] --> B1["2"] --> C1["1"] --> D1["8"] --> E1["4"]
        A2["2"] --> B2["5"] --> C2["1"] --> D2["4"] --> E2["8"]
    end

    subgraph Pass2["Прохід 2: 5 займає місце"]
        A3["2"] --> B3["1"] --> C3["4"] --> D3["5"] --> E3["8"]
    end

    subgraph Pass3["Прохід 3: фінал"]
        A4["1"] --> B4["2"] --> C4["4"] --> D4["5"] --> E4["8"]
    end

    class A1,B1,C1,D1,E1 unsorted
    class A2,B2,C2,D2 unsorted
    class E2 sorted
    class A3,B3,C3,D3 unsorted
    class E3,D4,E4 sorted
    class A4,B4,C4 sorted
```

**Головна проблема:** кожен swap = 3 операції запису в пам'ять (через Python tuple unpacking). Для $n=10^4$ до $10^8$ swap → **несумісно з продакшеном**.

---

## 2. Selection Sort — завжди рівно n-1 swap

```mermaid
graph LR
    classDef unsorted fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef min_elem fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef sorted fill:#1b5e20,stroke:#4CAF50,color:#ffffff;

    subgraph Step1["Крок 1: мін=3, swap(0,2)"]
        s1_12["12"] -.->|swap| s1_3["3"]
        s1_8["8"] 
        s1_20["20"]
        s1_11["11"]
    end

    subgraph Step2["Крок 2: мін=8, вже на місці"]
        s2_3["3 ✓"] 
        s2_8["8"] 
        s2_12["12"]
        s2_20["20"]
        s2_11["11"]
    end

    subgraph Step3["Крок 3: мін=11, swap(2,4)"]
        s3_3["3 ✓"]
        s3_8["8 ✓"]
        s3_12["12"] -.->|swap| s3_11["11"]
        s3_20["20"]
    end

    subgraph Result["Результат: [3, 8, 11, 12, 20]"]
        r1["3 ✓"] --> r2["8 ✓"] --> r3["11 ✓"] --> r4["12 ✓"] --> r5["20 ✓"]
    end

    class s1_12,s1_8,s1_20,s1_11 unsorted
    class s1_3 min_elem
    class s2_3,s2_8 sorted
    class s2_12,s2_20,s2_11 unsorted
    class s3_3,s3_8 sorted
    class s3_12,s3_11 min_elem
    class s3_20 unsorted
    class r1,r2,r3,r4,r5 sorted
```

**Переваги:** Мінімум swap — рівно $n-1$ незалежно від вхідних даних. Корисно коли операція **swap дорога** (наприклад, запис великих об'єктів на диск).

---

## 3. Insertion Sort — вставка «картки в руці»

```mermaid
graph TD
    classDef sorted fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef current fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef shifting fill:#263238,stroke:#90a4ae,color:#ffffff;

    subgraph Start["Початок: [9, 1, 15, 28, 6]"]
        i0["9 | 1 · 15 · 28 · 6"]
    end

    subgraph Step1["i=1: current=1, 1 < 9 → зсув 9 вправо"]
        i1["→ [1, 9, 15, 28, 6]"]
    end

    subgraph Step2["i=2: current=15, 15 > 9 → вже на місці"]
        i2["→ [1, 9, 15, 28, 6]"]
    end

    subgraph Step3["i=3: current=28, 28 > 15 → вже на місці"]
        i3["→ [1, 9, 15, 28, 6]"]
    end

    subgraph Step4["i=4: current=6, зсуваємо 28→15→9→зупиняємось"]
        i4["→ [1, 6, 9, 15, 28]"]
    end

    Start --> Step1 --> Step2 --> Step3 --> Step4
```

**Головна перевага:** `while` loop переривається миттєво на відсортованих ділянках → $O(n)$ для майже відсортованих даних. Саме тому Timsort використовує його для малих run'ів.

---

## 4. Merge Sort — дерево рекурсії

```mermaid
graph TD
    classDef split fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef merge fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef leaf fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    A["[120, 45, 68, 250, 176]"]
    B["[120, 45]"]
    C["[68, 250, 176]"]
    D["[120]"]
    E["[45]"]
    F["[68]"]
    G["[250, 176]"]
    H["[250]"]
    I["[176]"]

    M1["MERGE → [45, 120]"]
    M2["MERGE → [176, 250]"]
    M3["MERGE → [68, 176, 250]"]
    M4["MERGE → [45, 68, 120, 176, 250]"]

    A -->|"DIVIDE mid=2"| B
    A -->|"DIVIDE mid=2"| C
    B --> D
    B --> E
    C --> F
    C --> G
    G --> H
    G --> I

    D --> M1
    E --> M1
    H --> M2
    I --> M2
    F --> M3
    M2 --> M3
    M1 --> M4
    M3 --> M4

    class A,B,C split
    class D,E,F,H,I leaf
    class M1,M2,M3,M4 merge
    class G split
```

**Складність:** $\log_2 n$ рівнів × $O(n)$ на злиття кожного рівня = $O(n \log n)$.  
**Проблема:** Кожен `MERGE` виділяє новий масив → $O(n)$ пам'яті → cache pressure.

---

## 5. Heap Sort — Max-Heap у плоскому масиві

```mermaid
graph TD
    classDef root fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef internal fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef leaf fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef formula fill:#37474f,stroke:#64b5f6,color:#ffffff;

    subgraph MaxHeap["Max-Heap: [51, 12, 43, 8, 35]"]
        R["51<br/>idx=0 (корінь)"]
        L["12<br/>idx=1"]
        Ri["43<br/>idx=2"]
        LL["8<br/>idx=3"]
        LR["35<br/>idx=4"]

        R --> L
        R --> Ri
        L --> LL
        L --> LR
    end

    subgraph Formulas["Формули індексів"]
        F1["left = 2*i + 1"]
        F2["right = 2*i + 2"]
        F3["parent = (i-1) // 2"]
    end

    subgraph Phase2["Фаза 2: виймаємо максимум"]
        P1["swap(0, last) → 51 в кінець"]
        P2["heapify → 43 стає коренем"]
        P3["swap(0, last-1) → 43 на місце"]
        P4["... n разів → відсортовано!"]
        P1 --> P2 --> P3 --> P4
    end

    class R root
    class L,Ri internal
    class LL,LR leaf
    class F1,F2,F3 formula
```

**Чому повільніше Quicksort:** індекси `2i+1` і `2i+2` — це **стрибки** по масиву. Для великих $n$ ці стрибки виходять за межі L1/L2 cache → cache miss → звернення до RAM → 100+ нс затримка.

---

## 6. Quick Sort — партиція та рекурсія

```mermaid
graph TD
    classDef pivot fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef left fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef right fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef done fill:#37474f,stroke:#64b5f6,color:#ffffff;

    subgraph Partition["Partition(pivot=18): [22, 5, 1, 18, 99]"]
        direction LR
        I["i→"] ~~~ J["←j"]
        A1["22"] ~~~ A2["5"] ~~~ A3["1"] ~~~ A4["18*"] ~~~ A5["99"]
        B1["Після partition:"] ~~~ B2["[5, 1, 18, 22, 99]"]
    end

    subgraph Recurse["Рекурсія"]
        L["[5, 1]<br/>pivot=1"] --> LL["[1, 5] ✓"]
        R["[22, 99]<br/>pivot=99"] --> RR["[22, 99] ✓"]
    end

    subgraph Final["Результат"]
        F["[1, 5, 18, 22, 99] ✓"]
    end

    Partition --> Recurse --> Final

    class A4 pivot
    class B2 done
```

**Чому найшвидший:** партиція сканує масив **лінійно** двома вказівниками → CPU cache line 64 байти = 16 int32 завантажується за 1 RAM-запит, наступні 15 операцій — безкоштовно з кешу!

---

## 7. Timsort — гібридна архітектура

```mermaid
graph LR
    classDef run fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef ins fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef merge fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef input fill:#37474f,stroke:#64b5f6,color:#ffffff;

    INPUT["Реальні дані<br/>[3,5,8,2,4,9,1,7,6]"]

    subgraph Scan["Крок 1: Знайти runs"]
        R1["run1: [3,5,8]<br/>вже відсортовано!"]
        R2["run2: [2,4,9]<br/>вже відсортовано!"]
        R3["run3: [1,7,6]<br/>≥ MIN_RUN?"]
    end

    subgraph InsSort["Крок 2: Insertion Sort для коротких runs"]
        IS["[1,6,7] ← O(n) без рекурсії!"]
    end

    subgraph MergePhase["Крок 3: Merge runs попарно"]
        M1["Merge([3,5,8],[2,4,9])<br/>→ [2,3,4,5,8,9]"]
        M2["Merge([2,3,4,5,8,9],[1,6,7])<br/>→ [1,2,3,4,5,6,7,8,9]"]
    end

    INPUT --> Scan
    R1 --> M1
    R2 --> M1
    R3 --> InsSort --> M2
    M1 --> M2

    class INPUT input
    class R1,R2,R3 run
    class IS ins
    class M1,M2 merge
```

**Стабільний + O(n) для реальних даних** = ідеальний вибір для мови загального призначення.

---

## 8. Ієрархія пам'яті та Cache Locality

```mermaid
graph TD
    classDef fast fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef medium fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef slow fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef very_slow fill:#4e1f1f,stroke:#f44336,color:#ffffff;

    REG["CPU Registers<br/>~0.25 нс · 1x<br/>≈ 64 біта"]
    L1["L1 Cache<br/>~1 нс · 4x<br/>32 KB"]
    L2["L2 Cache<br/>~5 нс · 20x<br/>256 KB"]
    L3["L3 Cache<br/>~20 нс · 80x<br/>8 MB"]
    RAM["RAM (DRAM)<br/>~100 нс · 400x<br/>16+ GB"]
    SSD["NVMe SSD<br/>~100 мкс · 400,000x<br/>TB"]

    REG --> L1 --> L2 --> L3 --> RAM --> SSD

    class REG,L1 fast
    class L2,L3 medium
    class RAM slow
    class SSD very_slow
```

**Висновок:** Алгоритм, що читає **послідовно** (Quicksort partition, Insertion Sort) — майже завжди в L1/L2 кеші. Алгоритм, що «стрибає» (Heap Sort, деякі Merge операції) — постійні cache miss → звернення до RAM → 400x повільніше!

---

## 9. Порівняння Big-O: кількість кроків при різних n

```mermaid
xychart-beta
    title "Кроки алгоритмів залежно від n (логарифмічна шкала)"
    x-axis ["n=10", "n=100", "n=1000", "n=10000"]
    y-axis "Кроки (відносні)" 0 --> 100000000
    bar [100, 10000, 1000000, 100000000]
    bar [33, 664, 9966, 132877]
    bar [10, 100, 1000, 10000]
```

| n | $O(n^2)$ | $O(n \log n)$ | $O(n)$ |
|---|---------|--------------|--------|
| 100 | 10,000 | 664 | 100 |
| 1,000 | 1,000,000 | 9,966 | 1,000 |
| 10,000 | 100,000,000 | 132,877 | 10,000 |
| 1,000,000 | 10¹² | 19,931,568 | 1,000,000 |

При $n=10^6$: $O(n^2)$ = **10¹² операцій** ≈ **кілька днів**. $O(n \log n)$ ≈ **частки секунди**.

---

## 10. Алгоритм вибору сортування

```mermaid
flowchart TD
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef action fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    START["Потрібно сортувати дані"] --> Q1{"Мова / рівень?"}

    Q1 -->|"Python"| PYTHON["list.sort() або sorted()<br/>Timsort — завжди!"]
    Q1 -->|"C / системний"| Q2{"Гарантія O(n²)?"}

    Q2 -->|"Потрібна"| Q3{"Обмежена пам'ять?"}
    Q2 -->|"Не потрібна"| QS["Quick Sort<br/>Найшвидший на практиці"]

    Q3 -->|"O(1)"| HS["Heap Sort<br/>Linux планувальник, embedded"]
    Q3 -->|"O(n)"| MS["Merge Sort<br/>Зовнішнє сортування"]

    Q1 -->|"Спеціальний"| Q4{"Тип даних?"}
    Q4 -->|"Linked List"| MS2["Merge Sort<br/>O(1) злиття вказівниками"]
    Q4 -->|"Малий масив < 20"| IS["Insertion Sort<br/>Відсутність overhead"]
    Q4 -->|"Майже відсортований"| TS["Timsort / Insertion Sort<br/>O(n) best case"]

    class START decision
    class Q1,Q2,Q3,Q4 decision
    class PYTHON,QS,HS,MS,MS2,IS,TS action
```

---

## 11. Стабільність vs Нестабільність: практичний вплив

```mermaid
graph LR
    classDef stable fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef unstable fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef data fill:#263238,stroke:#90a4ae,color:#ffffff;

    subgraph Input["Вхід: logs відсортовані за time"]
        D1["500 | 10:00 | 'first 500'"]
        D2["200 | 10:05 | 'ok'"]
        D3["500 | 10:10 | 'second 500'"]
        D4["404 | 10:15 | 'not found'"]
    end

    subgraph StableSort["Стабільний (Timsort) — сортування за code"]
        S1["200 | 10:05"]
        S2["404 | 10:15"]
        S3["500 | 10:00 ← перший!"]
        S4["500 | 10:10 ← другий!"]
        S5["Часовий порядок збережено ✓"]
    end

    subgraph UnstableSort["Нестабільний (Quick Sort) — може дати"]
        U1["200 | 10:05"]
        U2["404 | 10:15"]
        U3["500 | 10:10 ← може бути першим!"]
        U4["500 | 10:00 ← може бути другим!"]
        U5["Часовий порядок НЕ гарантований ✗"]
    end

    Input --> StableSort
    Input --> UnstableSort

    class S1,S2,S3,S4 stable
    class S5 stable
    class U1,U2,U3,U4 unstable
    class U5 unstable
    class D1,D2,D3,D4 data
```

**Правило:** Якщо ви сортуєте об'єкти за **кількома ключами послідовно** — завжди використовуйте стабільний алгоритм або `key=` з tuple.
