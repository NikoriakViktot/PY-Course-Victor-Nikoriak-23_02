# Діаграми — Урок 28: Теорія Графів та Neo4j

---

## 1. Що таке граф? Основна анатомія

```mermaid
graph LR
    classDef node fill:#1a3a5c,stroke:#4fc3f7,color:#ffffff;
    classDef edge_label fill:#263238,stroke:#90a4ae,color:#cfd8dc;

    A["🏙️ Вузол A\n(Node / Vertex)"]
    B["🏙️ Вузол B"]
    C["🏙️ Вузол C"]
    D["🏙️ Вузол D"]
    E["🏙️ Вузол E"]

    A -->|"Ребро (Edge)"| B
    A -->|"Ребро"| C
    B -->|"Ребро"| D
    C -->|"Ребро"| D
    D -->|"Ребро"| E

    class A,B,C,D,E node
```

**Граф G = (V, E)**, де:
- **V** — множина вузлів (vertices): `{A, B, C, D, E}`
- **E** — множина ребер (edges): `{(A,B), (A,C), (B,D), (C,D), (D,E)}`

> **Ключова ідея:** вузол — це сутність, ребро — це зв'язок.
> Граф зберігає реальність такою, якою вона є, не спотворюючи її у таблиці.

---

## 2. Спрямований vs. Неспрямований граф

```mermaid
graph LR
    subgraph НЕСПРЯМОВАНИЙ
        U1["👤 Аліса"] --- U2["👤 Боб"]
        U2 --- U3["👤 Катя"]
        U1 --- U3
    end

    subgraph СПРЯМОВАНИЙ
        D1["👤 Аліса"] --> D2["👤 Боб"]
        D3["👤 Катя"] --> D2
        D2 --> D3
    end
```

| Властивість | Неспрямований | Спрямований |
|-------------|---------------|-------------|
| Ребро | `{u, v}` — симетричне | `(u, v)` — від u до v |
| Приклад | Facebook-дружба, дорога (2-смугова) | Twitter-підписка, одностороння вулиця |
| In/Out degree | Немає різниці | `in-degree` ≠ `out-degree` |
| Алгоритми | BFS, DFS без перевірки напрямку | Топологічне сортування, Dijkstra |

---

## 3. Зважений граф — реальні «витрати» на ребрах

```mermaid
graph LR
    classDef city fill:#1a3a5c,stroke:#4fc3f7,color:#ffffff;
    classDef weight fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    NYC["🗽 NYC\nзона 132"] 
    JFK["✈️ JFK\nзона 132→138"]
    BK["🏢 Brooklyn\nзона 11"]
    QNS["🏡 Queens\nзона 92"]
    BX["🌉 Bronx\nзона 3"]

    NYC -->|"⚡ 2.1 miles"| JFK
    NYC -->|"🚗 4.7 miles"| BK
    NYC -->|"🚕 8.3 miles"| QNS
    NYC -->|"🚖 12.6 miles"| BX
    BK -->|"3.4 miles"| QNS

    class NYC,JFK,BK,QNS,BX city
```

**Навіщо потрібні ваги:**
- Без ваги: BFS знаходить шлях з мінімальною кількістю переходів (хопів)
- З вагою: Dijkstra / A\* знаходить шлях з **мінімальною вартістю** (дистанція, час, $)
- Для пріоритетної черги вагового пошуку: складність `O((V + E) log V)`

---

## 4. Дерево vs. Граф — ієрархія проти мережі

```mermaid
graph TB
    %% ===== TREE =====
    subgraph Tree["🌳 ДЕРЕВО"]
        T_CEO["👔 CEO"]
        T_VP1["👔 VP Sales"] 
        T_VP2["👔 VP Tech"]
        T_M1["👨 Manager 1"]
        T_M2["👨 Manager 2"]
        T_M3["👨 Manager 3"]

        T_CEO --> T_VP1
        T_CEO --> T_VP2
        T_VP1 --> T_M1
        T_VP1 --> T_M2
        T_VP2 --> T_M3
    end

    %% ===== NETWORK =====
    subgraph Network["🕸️ ГРАФ-МЕРЕЖА"]
        N_A["🏢 A"]
        N_B["🏢 B"]
        N_C["🏢 C"]
        N_D["🏢 D"]

        N_A -->|"40%"| N_B
        N_B -->|"25%"| N_C
        N_C -->|"15%"| N_A
        N_A -->|"60%"| N_D
        N_D -->|"30%"| N_B
    end

    
```

> **Корпоративна власність утворює цикли** — класичне дерево не може це представити.
> Граф — може. Саме тому Neo4j застосовується для Anti-Money Laundering (AML) аналізу.

---

## 5. BFS — обхід у ширину (хвиля)

```mermaid
graph TB
    classDef start fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef level1 fill:#1a3a5c,stroke:#4fc3f7,color:#ffffff;
    classDef level2 fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef level3 fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef queue fill:#263238,stroke:#546e7a,color:#90a4ae;

    S["🚀 Старт (S)\nЧерга: [S]"]
    A["A — Рівень 1"]
    B["B — Рівень 1"]
    C["C — Рівень 1"]
    D["D — Рівень 2"]
    E["E — Рівень 2"]
    F["F — Рівень 3"]

    S --> A
    S --> B
    S --> C
    A --> D
    B --> D
    C --> E
    D --> F
    E --> F

    Q1["📦 Черга (FIFO Queue)\nКрок 1: [S]\nКрок 2: [A, B, C]\nКрок 3: [D, E]\nКрок 4: [F]"]

    class S start
    class A,B,C level1
    class D,E level2
    class F level3
    class Q1 queue
```

**BFS Гарантія:** перший раз коли алгоритм знаходить цільовий вузол — це **найкоротший шлях** (мінімум хопів).

**Складність:**
- Час: `O(V + E)`
- Пам'ять: `O(V)` — у найгіршому випадку черга містить усі вузли одного рівня

---

## 6. DFS — обхід у глибину (занурення)

```mermaid
graph LR
    classDef visited fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef backtrack fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef current fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    subgraph DFS_Path["DFS: занурюємось по одному шляху"]
        direction LR
        S2["🚀 S"] -->|"1️⃣ йдемо"| A2["A"]
        A2 -->|"2️⃣ йдемо"| D2["D"]
        D2 -->|"3️⃣ глухий кут"| A2
        A2 -->|"4️⃣ інший шлях"| E2["E"]
        E2 -->|"5️⃣ йдемо"| G2["🎯 Ціль!"]
    end

    %% spacer
    SPACE[" "]:::hidden

    subgraph Stack["📚 Стек (LIFO)"]
        ST["S → A → E → G"]
    end

    classDef hidden fill:transparent,stroke:transparent

    class S2,A2,E2 visited
    class D2 backtrack
    class G2 current
```

**DFS застосування:**
- Пошук зв'язних компонент (окремих острівців у мережі)
- Топологічне сортування (порядок компіляції файлів)
- Пошук циклів у графі (виявлення fraud rings)
- Розв'язання лабіринтів

---

## 7. Алгоритм Дейкстри — найдешевший маршрут

```mermaid
graph LR
    classDef unvisited fill:#263238,stroke:#546e7a,color:#90a4ae;
    classDef settled fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef current fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    subgraph Dijkstra["Dijkstra від вузла S до T"]
        S3["🚀 S\ndist=0"] -->|"4"| A3["A\ndist=4"]
        S3 -->|"7"| B3["B\ndist=7"]
        A3 -->|"2"| C3["C\ndist=6"]
        A3 -->|"5"| B3
        B3 -->|"3"| T3["🎯 T\ndist=9"]
        C3 -->|"3"| T3
    end

    subgraph Steps["Кроки алгоритму"]
        ST2["Крок 1: обрати S (dist=0)\nОновити: A=4, B=7"]
        ST3["Крок 2: обрати A (dist=4) — найменший\nОновити: C=6, B=min(7, 4+5)=7"]
        ST4["Крок 3: обрати C (dist=6)\nОновити: T=min(∞, 6+3)=9"]
        ST5["Крок 4: обрати B (dist=7)\nОновити: T=min(9, 7+3)=9 (не змінилось)"]
        ST6["✅ Результат: S→A→C→T, вартість=9"]
    end

    class S3 settled
    class A3,C3 settled
    class B3 current
    class T3 unvisited
```

**Dijkstra vs BFS:**

| | BFS | Dijkstra |
|--|-----|---------|
| Граф | Незважений | Зважений |
| Структура | FIFO черга | Пріоритетна черга (min-heap) |
| Складність | `O(V + E)` | `O((V + E) log V)` |
| Гарантія | Мін. кількість хопів | Мін. вартість шляху |

---

## 8. SQL JOIN vs. Graph Traversal — проблема глибини

```mermaid
graph TB
    subgraph SQL_Problem["🐌 SQL: друзі друзів — 4 рівні глибини"]
        SQL1["SELECT * FROM users u1\nJOIN friendships f1 ON u1.id = f1.user_id\nJOIN users u2 ON f1.friend_id = u2.id\nJOIN friendships f2 ON u2.id = f2.user_id\n... (ще 2 JOINs)\n\n⏱️ 1500 секунд при 1M користувачів"]
        SQL_WARN["⚠️ Проблема: кожен JOIN\nгенерує Cartesian Product\nПродуктивність деградує\nЕКСПОНЕНЦІАЛЬНО"]
    end

    subgraph Neo4j_Solution["⚡ Neo4j: та сама задача"]
        CYP["MATCH (p:Person {name: 'Alice'})\n-[:FRIENDS_WITH*1..4]->(friend:Person)\nRETURN friend.name\n\n⏱️ 1.3 секунди — та сама кількість даних!"]
        NEO_WHY["✅ Чому швидко:\nIndex-Free Adjacency\nКожен вузол = прямий pointer\nна сусідів на диску\nO(1) замість O(log N) для JOINs"]
    end

    SQL_Problem -->|"Та сама задача"| Neo4j_Solution
```

---

## 9. Neo4j Index-Free Adjacency — архітектура зберігання

```mermaid
graph LR
    classDef node_block fill:#1a3a5c,stroke:#4fc3f7,color:#ffffff;
    classDef rel_block fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef prop_block fill:#263238,stroke:#546e7a,color:#90a4ae;

    subgraph NodeRecord["📦 Запис вузла (фіксований розмір)"]
        NR["Node Record\n├─ in_use: bool\n├─ first_rel_id: → R1 (pointer!)\n├─ first_prop_id: → P1\n└─ labels: Person"]
    end

    subgraph RelRecord["🔗 Запис ребра (relationship)"]
        R1["Rel Record R1\n├─ type: FRIENDS_WITH\n├─ start_node: → Alice\n├─ end_node: → Bob\n├─ next_rel_start: → R2\n└─ next_rel_end: → R5"]
    end

    subgraph PropRecord["📝 Запис властивості"]
        P1["Prop Record P1\n├─ key: name\n├─ value: 'Alice'\n└─ next_prop: → P2"]
    end

    NR -->|"O(1) pointer"| R1
    NR -->|"O(1) pointer"| P1

    class NR node_block
    class R1 rel_block
    class P1 prop_block
```

> **Секрет Neo4j:** обхід ребра — це просто **chase pointer** (слідувати по вказівнику).
> Не потрібно сканувати жодний глобальний індекс. Час: **O(1)**, незалежно від розміру БД.

---

## 10. NYC Taxi Zone Graph — наш сценарій

```mermaid
graph LR
    classDef manhattan fill:#1a3a5c,stroke:#4fc3f7,color:#ffffff;
    classDef brooklyn fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef queens fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef bronx fill:#4e1f1f,stroke:#f44336,color:#ffffff;

    Z132["🗽 Zone 132\nMidtown\n(багато поїздок)"]
    Z138["✈️ Zone 138\nJFK Airport"]
    Z236["🏢 Zone 236\nUpper West Side"]
    Z11["🌉 Zone 11\nBrooklyn Heights"]
    Z92["🏡 Zone 92\nJackson Heights\nQueens"]
    Z3["🌆 Zone 3\nBronx"]

    Z132 -->|"avg 4.2 mi\n$18.5"| Z138
    Z132 -->|"avg 2.1 mi\n$12.3"| Z236
    Z132 -->|"avg 6.7 mi\n$24.1"| Z11
    Z236 -->|"avg 8.3 mi\n$28.7"| Z92
    Z11 -->|"avg 3.4 mi\n$15.2"| Z92
    Z92 -->|"avg 5.1 mi\n$19.8"| Z3
    Z3 -->|"avg 14.2 mi\n$45.3"| Z138

    class Z132,Z236 manhattan
    class Z11 brooklyn
    class Z92 queens
    class Z3 bronx
    class Z138 manhattan
```

**Задача лабораторії:**
1. Завантажити NYC Taxi дані через DuckDB (3M+ рядків)
2. Побудувати граф зон (adjacency list) з реальних поїздок
3. BFS: знайти найближчу зону за мін. кількістю переходів
4. Dijkstra: знайти найдешевший маршрут між зонами (за середньою вартістю)
5. Dispatch Optimizer: отримати запит — повернути ранжований список доступних таксі

---

## 11. Recommendation Engine — граф рекомендацій

```mermaid
graph LR
    classDef user fill:#1a3a5c,stroke:#4fc3f7,color:#ffffff;
    classDef product fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef rec fill:#4a3b00,stroke:#ff9800,color:#ffffff;

    UA["👤 User A\n(запит)"]
    UB["👤 User B\n(схожий)"]
    UC["👤 User C\n(схожий)"]

    P1["📦 Product 1\n(купив A і B)"]
    P2["📦 Product 2\n(купив B)"]
    P3["📦 Product 3\n(купив C)"]

    UA -->|"BOUGHT"| P1
    UB -->|"BOUGHT"| P1
    UB -->|"BOUGHT"| P2
    UC -->|"BOUGHT"| P1
    UC -->|"BOUGHT"| P3

    REC["💡 Рекомендації для A:\nProduct 2 (через B)\nProduct 3 (через C)"]

    P2 -.->|"RECOMMEND →"| REC
    P3 -.->|"RECOMMEND →"| REC

    class UA,UB,UC user
    class P1,P2,P3 product
    class REC rec
```

**Cypher запит (Neo4j):**
```cypher
MATCH (me:User {id: "A"})-[:BOUGHT]->(p:Product)<-[:BOUGHT]-(similar:User)
MATCH (similar)-[:BOUGHT]->(rec:Product)
WHERE NOT (me)-[:BOUGHT]->(rec)
RETURN rec.name, count(similar) AS score
ORDER BY score DESC
LIMIT 10
```

---

## 12. Fraud Detection — виявлення шахрайських кілець

```mermaid
graph LR
    classDef legit fill:#1b5e20,stroke:#4CAF50,color:#ffffff;
    classDef suspect fill:#4a3b00,stroke:#ff9800,color:#ffffff;
    classDef fraud fill:#4e1f1f,stroke:#f44336,color:#ffffff;
    classDef shared fill:#263238,stroke:#546e7a,color:#90a4ae;

    ACC1["💳 Account A\n(нова)"]
    ACC2["💳 Account B\n(нова)"]
    ACC3["💳 Account C\n(нова)"]
    KNOWN["☠️ Відомий\nшахрай"]

    PHONE["📱 Телефон\n+380XX-XXX"]
    IP["🌐 IP\n192.168.1.1"]
    DEVICE["💻 Device\nMAC:AA:BB"]

    ACC1 -->|"USES"| PHONE
    ACC2 -->|"USES"| PHONE
    ACC3 -->|"USES"| IP
    KNOWN -->|"USES"| IP
    ACC2 -->|"USES"| DEVICE
    KNOWN -->|"USES"| DEVICE

    WARNING["⚠️ Neo4j знаходить:\nACC1, ACC2, ACC3 пов'язані через\nспільні пристрої/IP з відомим шахраєм\nSQL не знайде це за 5 JOINs"]

    class ACC1,ACC2,ACC3 suspect
    class KNOWN fraud
    class PHONE,IP,DEVICE shared
    class WARNING fraud
```
