# Діаграми — Урок 26: Дерева та алгоритми дерев

---

## 1. Бінарне дерево: термінологія та структура

```mermaid
graph TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;

    R["4<br>Корінь · Глибина 0"]
    L["2<br>Внутрішній · Глибина 1"]
    Ri["6<br>Внутрішній · Глибина 1"]
    LL["1<br>Листок · Глибина 2"]
    LR["3<br>Листок · Глибина 2"]
    RL["5<br>Листок · Глибина 2"]
    RR["7<br>Листок · Глибина 2"]

    T1["Висота = 2 · Висота = max глибина"]
    T2["Листок: left=None, right=None"]
    T3["Вузол: value + left + right"]

    R --> L & Ri
    L --> LL & LR
    Ri --> RL & RR

    class R warning
    class L,Ri step
    class LL,LR,RL,RR success
    class T1,T2,T3 decision
```

**Інваріант BST:** ліве піддерево < вузол < праве піддерево — глобально для всього дерева!

---

## 2. Інваріант BST: локальний vs глобальний

```mermaid
graph TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    subgraph VALID["Валідне BST"]
        V10["10"] --> V5["5"] & V15["15"]
        V5 --> V3["3"] & V7["7"]
    end

    subgraph INVALID["Невалідне BST — локально OK, глобально НІ"]
        I10["10"] --> I5["5"] & I15["15"]
        I5 --> I3["3"] & I12["12 — порушення!<br>12 > 10, але в лівому піддереві"]
    end

    TRAP["Типова пастка:<br>node.left &lt; node &lt; node.right — недостатньо!<br>Треба передавати min/max у рекурсії"]

    class V10,V5,V15,V3,V7 success
    class I10,I5,I15,I3 step
    class I12 error
    class TRAP warning
```

---

## 3. Три варіанти DFS: Pre-order, In-order, Post-order

```mermaid
graph TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;

    subgraph TREE["Дерево [4, 2, 6, 1, 3, 5, 7]"]
        R2["4"] --> L2["2"] & RI2["6"]
        L2 --> LL2["1"] & LR2["3"]
        RI2 --> RL2["5"] & RR2["7"]
    end

    PRE["Pre-order: Корінь → Лів → Прав<br>4 2 1 3 6 5 7<br>Застосування: копіювання, серіалізація"]
    IN["In-order: Лів → Корінь → Прав<br>1 2 3 4 5 6 7 — завжди відсортовано!<br>Застосування: отримання sorted з BST"]
    POST["Post-order: Лів → Прав → Корінь<br>1 3 2 5 7 6 4<br>Застосування: видалення, розміри директорій"]

    TREE --> PRE & IN & POST

    class R2,L2,RI2,LL2,LR2,RL2,RR2 step
    class IN success
    class POST warning
    class PRE decision
```

---

## 4. BFS vs DFS: Черга проти Стеку

```mermaid
graph LR
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    CHOICE["Яка стратегія?"]

    subgraph DFS["DFS — Стек LIFO"]
        DS1["Правого кладемо першим<br>потім лівого"]
        DS2["LIFO → лівий обробляється першим"]
        DS3["Порядок: 4 2 1 3 6 5 7<br>Pre-order"]
        DS1 --> DS2 --> DS3
    end

    subgraph BFS["BFS — Черга FIFO"]
        BQ1["Лівого, потім правого"]
        BQ2["FIFO → обробляємо у порядку вставки"]
        BQ3["Порядок: 4 2 6 1 3 5 7<br>рівень за рівнем"]
        BQ1 --> BQ2 --> BQ3
    end

    CHOICE -->|"глибина / Stack"| DFS
    CHOICE -->|"ширина / Queue"| BFS

    class CHOICE warning
    class DS1,DS2,DS3 decision
    class BQ1,BQ2,BQ3 success
```

---

## 5. BFS покроково: Queue (FIFO)

```mermaid
flowchart TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    S0["Queue = [4]"]
    S1["Дістаємо 4 → додаємо 2, 6<br>Queue = [2, 6]"]
    S2["Дістаємо 2 → додаємо 1, 3<br>Queue = [6, 1, 3]"]
    S3["Дістаємо 6 → додаємо 5, 7<br>Queue = [1, 3, 5, 7]"]
    S4["Вузли 1 3 5 7 — листки<br>черга порожніє"]
    S5["Результат: 4 2 6 1 3 5 7"]

    BAD["list.pop(0) → O(n) зсув пам'яті<br>Весь алгоритм деградує до O(n²)!"]
    GOOD["deque.popleft() → O(1)<br>Завжди використовувати deque!"]

    S0 --> S1 --> S2 --> S3 --> S4 --> S5
    S5 --> BAD
    S5 --> GOOD

    class S0,S1,S2,S3,S4 step
    class S5,GOOD success
    class BAD error
```

---

## 6. DFS Pre-order покроково: Stack (LIFO)

```mermaid
flowchart TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    D0["Stack = [4]"]
    D1["pop 4 → push right=6, left=2<br>Stack = [6, 2]  — 2 на вершині!"]
    D2["pop 2 → push right=3, left=1<br>Stack = [6, 3, 1]"]
    D3["pop 1 — листок<br>Stack = [6, 3]"]
    D4["pop 3 — листок<br>Stack = [6]"]
    D5["pop 6 → push right=7, left=5<br>Stack = [7, 5]"]
    D6["pop 5, pop 7 — листки<br>Stack = []"]
    D7["Результат: 4 2 1 3 6 5 7"]
    KEY["Правого кладемо ПЕРШИМ<br>→ лівий на вершині LIFO → обробляється першим"]

    D0 --> D1 --> D2 --> D3 --> D4 --> D5 --> D6 --> D7
    D7 --> KEY

    class D0,D1,D2,D3,D4,D5,D6 step
    class D7 success
    class KEY warning
```

---

## 7. Рекурсія vs Ітерація: де зберігається стан

```mermaid
graph LR
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    subgraph RECURSIVE["Рекурсія"]
        RC1["Стан → Call Stack системи"]
        RC2["Ліміт: ~1000 кадрів"]
        RC3["Глибоке дерево → RecursionError"]
        RC1 --> RC2 --> RC3
    end

    subgraph ITERATIVE["Ітерація з явним стеком"]
        IT1["Стан → явний list у Heap"]
        IT2["Heap: обмежений лише RAM"]
        IT3["Будь-яка глибина — безпечно"]
        IT1 --> IT2 --> IT3
    end

    NOTE["BFS реалізується ТІЛЬКИ ітеративно<br>системного аналогу черги не існує"]

    class RC1,RC2 step
    class RC3 error
    class IT1,IT2,IT3 success
    class NOTE warning
```

---

## 8. Збалансоване vs Вироджене дерево

```mermaid
graph TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    subgraph BALANCED["Збалансоване BST — випадкова вставка"]
        B5["5"] --> B3["3"] & B7["7"]
        B3 --> B1["1"] & B4["4"]
        B7 --> B6["6"] & B8["8"]
        BH["Висота ≈ log₂(7) ≈ 3<br>Пошук: O(log n)"]
    end

    subgraph SKEWED["Вироджене BST — вставка 1 2 3 4 5"]
        S1["1"] --> S2["2"] --> S3["3"] --> S4["4"] --> S5["5"]
        SH["Висота = n - 1 = 4<br>Пошук: O(n) — повільно!"]
    end

    FIX["Рішення: AVL або Червоно-чорні дерева<br>автоматичні ротації → гарантія O(log n)"]

    class B5,B3,B7,B1,B4,B6,B8 success
    class BH success
    class S1,S2,S3,S4,S5 error
    class SH error
    class FIX warning
```

---

## 9. BST vs Хеш-таблиця: порівняння

```mermaid
graph TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef error fill:#4e1f1f,stroke:#f44336,color:#ffffff;

    subgraph HASH["dict / set — Хеш-таблиця"]
        H1["Точний пошук: O(1)"]
        H2["Вставка: O(1)"]
        H3["Діапазонний запит: O(n)<br>повний перебір усіх ключів"]
        H4["Відсортована ітерація: O(n log n)"]
        H5["Мін / Макс: O(n)"]
    end

    subgraph BST_BOX["BST — збалансоване"]
        B1["Точний пошук: O(log n)"]
        B2["Вставка: O(log n)"]
        B3["Діапазонний запит: O(log n + k)"]
        B4["Відсортована ітерація: O(n)<br>In-order обхід"]
        B5["Мін / Макс: O(log n)<br>крайній лівий / правий вузол"]
    end

    RULE["Точний пошук, кешування → dict/set<br>Діапазони, порядок, min/max → BST"]

    class H1,H2 success
    class H3,H4,H5 error
    class B1,B2 decision
    class B3,B4,B5 success
    class RULE warning
```

---

## 10. Алгоритм вибору обходу

```mermaid
flowchart TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    Q1{"Яка задача?"}

    Q1 -->|"найкоротший шлях<br>або обхід по рівнях"| BFS_ANS["BFS<br>collections.deque<br>O(n) час · O(w) пам'ять"]

    Q1 -->|"глибинний обхід"| Q2{"Порядок обробки?"}

    Q2 -->|"батько перед дітьми<br>копіювання, серіалізація"| PRE_ANS["Pre-order DFS<br>Корінь → Лів → Прав"]

    Q2 -->|"відсортовані дані з BST"| IN_ANS["In-order DFS<br>Лів → Корінь → Прав"]

    Q2 -->|"батько після дітей<br>видалення, розміри"| POST_ANS["Post-order DFS<br>Лів → Прав → Корінь"]

    PRE_ANS & IN_ANS & POST_ANS --> Q3{"Глибина > 1000<br>або невідома?"}

    Q3 -->|"так"| ITER["Ітеративна реалізація<br>явний list як стек"]
    Q3 -->|"ні"| RECUR["Рекурсивна реалізація<br>коротший код"]

    class Q1,Q2,Q3 decision
    class BFS_ANS,IN_ANS success
    class PRE_ANS,POST_ANS,RECUR step
    class ITER warning
```

---

## 11. Серіалізація дерева через Pre-order

```mermaid
flowchart LR
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    subgraph ORIG["Оригінальне дерево"]
        T4["4"] --> T2["2"] & T6["6"]
        T2 --> T1["1"] & T3["3"]
        T6 --> T5["5"] & T7["7"]
    end

    SER["Pre-order серіалізація<br>None → '#'"]

    STR["'4,2,1,#,#,3,#,#,6,5,#,#,7,#,#'<br># = порожній вузол"]

    DES["Десеріалізація<br>iter() + рекурсія"]

    subgraph REST["Відновлене дерево"]
        R4["4"] --> R2["2"] & R6["6"]
        R2 --> R1["1"] & R3["3"]
        R6 --> R5["5"] & R7["7"]
    end

    ORIG --> SER --> STR --> DES --> REST

    class T4,T2,T6,T1,T3,T5,T7 step
    class SER,DES warning
    class STR decision
    class R4,R2,R6,R1,R3,R5,R7 success
```

---

## 12. Реальні застосування дерев

```mermaid
flowchart TD
    classDef step fill:#263238,stroke:#90a4ae,color:#ffffff;
    classDef success fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef decision fill:#37474f,stroke:#64b5f6,color:#ffffff;
    classDef warning fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    ROOT["Дерева у реальному світі"]

    ROOT --> FS["Файлова система"]
    ROOT --> DOM["HTML DOM"]
    ROOT --> DB["Бази даних"]
    ROOT --> COMP["Компілятори"]
    ROOT --> SEARCH["Пошукові системи"]

    FS --> FS1["Директорія = внутрішній вузол"]
    FS --> FS2["Файл = листок"]
    FS --> FS3["find / du = Post-order DFS"]

    DOM --> DOM1["html = корінь"]
    DOM --> DOM2["CSS-специфічність = LCA"]
    DOM --> DOM3["querySelector = DFS"]

    DB --> DB1["B-tree індекси PostgreSQL / MySQL"]
    DB --> DB2["O(log n) серед мільярдів рядків"]
    DB --> DB3["Вузол = сотні нащадків"]

    COMP --> COMP1["AST — абстрактне синтаксичне дерево"]
    COMP --> COMP2["2+3×4 → Post-order обчислення"]

    SEARCH --> SR1["Trie — автодоповнення"]
    SEARCH --> SR2["Prefix search O(L)"]

    class ROOT warning
    class FS,DOM,DB,COMP,SEARCH decision
    class FS1,FS2,DOM1,COMP1,SR1,DB1 step
    class FS3,DOM2,DOM3,DB2,DB3,COMP2,SR2 success
```

---

*Урок 26 · Module 3 · Python Advanced · Viktor Nikoriak*
