# PostgreSQL — Архітектура, Схеми та Документація

> Урок 30 | Модуль 3 | Python Course  
> Підключення: `host=localhost port=5432 user=student password=python2024 dbname=course_db`

---

## 1. PostgreSQL як система — загальна архітектура

```mermaid
graph TB
    CLIENT["🖥️ Клієнт (Python / psycopg2)"]

    subgraph POSTGRES["PostgreSQL Server (course-postgres)"]
        PARSER["Parser\n(синтаксичний аналіз SQL)"]
        PLANNER["Query Planner\n(cost-based optimizer)"]
        EXECUTOR["Executor\n(виконавець плану)"]

        subgraph MEMORY["Shared Memory (RAM)"]
            BUFCACHE["Buffer Cache\n(кешовані Pages з диску)"]
            WALBUF["WAL Buffer\n(буфер журналу)"]
        end

        subgraph DISK["Disk Storage"]
            HEAP["Heap Files\n(таблиці — pages з tuples)"]
            INDEXES["Index Files\n(B-Tree / GIN / GiST)"]
            WALFILE["WAL Files\n(Write-Ahead Log)"]
        end

        BGWRITER["bgwriter\n(скидає dirty pages)"]
        VACUUM["autovacuum\n(прибирає мертві tuples)"]
        CHECKPOINT["checkpointer\n(WAL → tables sync)"]
    end

    CLIENT -->|"TCP (port 5432)"| PARSER
    PARSER --> PLANNER
    PLANNER -->|"EXPLAIN план"| EXECUTOR
    EXECUTOR <--> BUFCACHE
    BUFCACHE <-->|"Page in/out"| HEAP
    BUFCACHE <--> INDEXES
    EXECUTOR -->|"кожна мутація"| WALBUF
    WALBUF -->|"fsync (durability)"| WALFILE
    BGWRITER -->|"write dirty pages"| HEAP
    VACUUM -->|"clean dead tuples"| HEAP
    CHECKPOINT -->|"WAL → Heap sync"| HEAP

    style MEMORY fill:#E3F2FD
    style DISK fill:#FFF3E0
```

---

## 2. Фізичне зберігання: Heap Files → Pages → Tuples

```mermaid
block-beta
    columns 1

    block:FILE["Heap File (таблиця на диску)"]
        columns 3
        PAGE0["Page 0\n(8 KB блок)"] PAGE1["Page 1\n(8 KB блок)"] PAGEDOTS["Page N\n..."]
    end

    block:PAGE_DETAIL["Структура однієї Page (Slotted Page)"]
        columns 1
        HDR["Page Header\n(LSN, checksums, free space info)"]
        SLOTS["Item ID Array (слоти)\n[slot1→offset] [slot2→offset] [slot3→offset]\n↓ росте вниз"]
        FREE["Вільний простір"]
        TUPLES["Tuples (рядки) з фіксованими + змінними полями\n↑ росте вгору"]
    end

    block:TUPLE_DETAIL["Структура Tuple (рядка)"]
        columns 3
        THDR["Tuple Header\nxmin, xmax\n(MVCC visibility)"] FIXED["Поля фіксованої\nдовжини\n(INT, BOOL)"] VAR["Поля змінної\nдовжини\n(TEXT, JSONB)\n→ TOAST якщо >~2KB"]
    end
```

### Ключові механізми зберігання

| Концепція | Деталь |
|-----------|--------|
| **Page (Блок)** | 8 KB за замовчуванням; мінімальна одиниця диск↔RAM I/O |
| **Slotted Pages** | Масив слотів-покажчиків на початку page → рядки ростуть з кінця назустріч |
| **Buffer Cache** | Кешує hot pages в RAM; LRU витіснення; `shared_buffers = 25% RAM` |
| **TOAST** | `The Oversized-Attribute Storage Technique` — великі значення (>~2 KB) виносяться в окрему таблицю з посиланням |
| **Alignment** | Padding між полями для вирівнювання по 4/8 байт (процесорна вимога) |

---

## 3. MVCC — Багатоверсійне управління конкурентністю

```mermaid
sequenceDiagram
    participant T1 as Транзакція T1 (Reader)
    participant T2 as Транзакція T2 (Writer)
    participant DB as PostgreSQL (Pages)

    T1->>DB: BEGIN (xid=100)
    T2->>DB: BEGIN (xid=101)

    T1->>DB: SELECT balance WHERE id=5
    DB-->>T1: Tuple v1 (xmin=50, xmax=NULL) → balance=1000 ✓

    T2->>DB: UPDATE balance=900 WHERE id=5
    Note over DB: НЕ перезаписує tuple v1!<br/>Створює НОВИЙ tuple v2:<br/>v1: xmin=50, xmax=101 (помічено як "dead для T1")<br/>v2: xmin=101, xmax=NULL, balance=900

    T2->>DB: COMMIT (xid=101)
    Note over DB: v2 тепер committed

    T1->>DB: SELECT balance WHERE id=5 (ще в транзакції!)
    Note over DB: READ COMMITTED: бачить v2 (нові committed дані)<br/>REPEATABLE READ: бачить snapshot від START → v1
    DB-->>T1: balance=900 (READ COMMITTED) або 1000 (REPEATABLE READ)

    T1->>DB: COMMIT
    Note over DB: autovacuum потім видалить мертвий tuple v1
```

### Правило MVCC

> **Читачі не блокують письменників, письменники не блокують читачів.**
> 
> Блокування на рівні рядків відбувається ТІЛЬКИ коли два процеси намагаються **змінити один рядок одночасно**.

---

## 4. WAL (Write-Ahead Log) — гарантія Durability

```mermaid
flowchart LR
    TX["BEGIN ... UPDATE ... COMMIT"]

    TX --> WALB["WAL Buffer\n(RAM)\nзапис опису змін"]
    WALB -->|"fsync() при COMMIT"| WALF["WAL Files on Disk\n(pg_wal/)"]
    WALB -->|"асинхронно"| DIRTY["Dirty Pages\nу Buffer Cache (RAM)"]
    DIRTY -->|"bgwriter / checkpointer"| HEAP["Heap Files on Disk\n(actual tables)"]

    CRASH["💥 Server Crash?"] -->|"після перезапуску"| REPLAY
    WALF --> REPLAY["WAL Replay\n(Recovery Manager)"]
    REPLAY -->|"відновлює committed стани"| HEAP

    style WALF fill:#FFE0B2
    style HEAP fill:#C8E6C9
    style CRASH fill:#FFCDD2
```

### WAL = гарантія без жертви продуктивністю

| Без WAL | З WAL |
|---------|-------|
| Кожен COMMIT → fsync основних файлів таблиць (повільно) | COMMIT → fsync лише WAL (швидкий sequential I/O) |
| Crash → невідомий стан | Crash → WAL Replay відновлює точний стан |
| Random I/O по таблицях | Sequential I/O в WAL log (набагато швидше) |

---

## 5. Query Planner — вибір плану виконання

```mermaid
flowchart TD
    SQL["SQL запит\nSELECT ... FROM ... WHERE ... JOIN ..."]

    SQL --> PARSE["Parser\n(синтаксис + семантика)"]
    PARSE --> REWRITE["Rewriter\n(розкрити views, правила)"]
    REWRITE --> PLAN["Query Planner\n(cost-based optimizer)"]

    PLAN --> STATS["Системна статистика\npg_statistic\n(кардинальність, розподіл значень)"]
    STATS --> PLAN

    PLAN --> SCAN{"Спосіб читання\nданих?"}
    SCAN -->|"мала вибірка\n(selective query)"| ISCAN["Index Scan\nO(log N)"]
    SCAN -->|"багато рядків\n(> 5-10% таблиці)"| SEQSCAN["Sequential Scan\nO(N)"]
    SCAN -->|"кілька індексів"| BITMAP["Bitmap Index Scan\nIN-memory bitmap + sequential fetch"]

    PLAN --> JOIN{"Алгоритм\nJOIN?"}
    JOIN -->|"мала outer таблиця\n+ індекс на inner"| NL["Nested Loop\nO(N × log M)"]
    JOIN -->|"різні розміри\nбез сортування"| HASH["Hash Join\nO(N + M)"]
    JOIN -->|"приблизно рівні\nабо відсортовані"| MERGE["Merge Join\nO(N + M)"]

    ISCAN --> EXEC["Executor\n(виконання плану)"]
    SEQSCAN --> EXEC
    BITMAP --> EXEC
    NL --> EXEC
    HASH --> EXEC
    MERGE --> EXEC

    EXEC -->|"результат"| CLIENT["Клієнт"]
```

---

## 6. Типи індексів PostgreSQL

```mermaid
mindmap
  root((PostgreSQL Indexes))
    B-Tree
      За замовчуванням
      Збалансоване дерево
      O log N пошук
      Equality =
      Range < > BETWEEN
      LIKE 'prefix%'
      Числа Рядки Дати
    GIN Generalized Inverted Index
      Інвертована структура
      Елемент → рядки
      JSONB @> ? #>
      ARRAY @>
      Full-Text Search @@
      Маса елементів у колонці
    GiST Generalized Search Tree
      Балансоване дерево
      Для невпорядкованих даних
      PostGIS точки полігони
      Nearest-neighbor k-NN
      OVERLAPS перетин інтервалів
    Hash
      Тільки equality =
      Менше ніж B-Tree
    SP-GiST
      Незбалансоване дерево
      Quad-tree prefix-tree
      Текстові префікси
      Просторове розбиття
    BRIN
      Block Range INdex
      Мінімальний розмір
      Для монотонних даних
      timestamp sequence
```

### Коли який індекс використовувати

| Задача | Індекс | SQL приклад |
|--------|--------|-------------|
| Пошук по первинному ключу | B-Tree (автоматично) | `WHERE id = 5` |
| Сортування, BETWEEN | B-Tree | `WHERE age BETWEEN 20 AND 30` |
| JSONB полів | GIN | `WHERE data @> '{"status":"active"}'` |
| Full-Text Search | GIN | `WHERE ts_vec @@ to_tsquery('term')` |
| Масиви | GIN | `WHERE tags @> ARRAY['python']` |
| Геопросторові | GiST (PostGIS) | `WHERE ST_DWithin(point, center, 1000)` |
| Лише equality (= ) | Hash | `WHERE status = 'active'` |
| Великі монотонні таблиці | BRIN | `WHERE created_at > '2024-01-01'` |

### Трейдофи індексів

```mermaid
graph LR
    subgraph HELPS["✅ Індекс ПРИСКОРЮЄ"]
        H1["High cardinality\n(UUID, email, PK)"]
        H2["Selective queries\n(< 5-10% рядків)"]
        H3["FK у JOIN"]
        H4["ORDER BY / LIMIT"]
    end

    subgraph HURTS["❌ Індекс ГАЛЬМУЄ"]
        U1["Write amplification\n(кожен INSERT/UPDATE\nоновлює всі індекси)"]
        U2["Low cardinality\n(boolean, enum з 3 значень)"]
        U3["Disk bloat\n(займає місце + RAM)"]
        U4["Full table scans\n(планувальник ігнорує)"]
    end
```

---

## 7. Рівні ізоляції та аномалії

```mermaid
graph TD
    subgraph LEVELS["Рівні ізоляції PostgreSQL"]
        RC["READ COMMITTED\n(за замовчуванням)\nCURI: бачить нові committed дані\nперформанс: ⭐⭐⭐⭐⭐"]
        RR["REPEATABLE READ\nСнімок від початку транзакції\nперформанс: ⭐⭐⭐⭐"]
        SER["SERIALIZABLE (SSI)\nАбсолютна ізоляція\nперформанс: ⭐⭐⭐"]
    end

    subgraph ANOMALIES["Аномалії"]
        DR["Dirty Read\n(читати незакомічені дані)"]
        NRR["Non-repeatable Read\n(2 SELECT = різні рядки)"]
        PR["Phantom Read\n(2 SELECT = різні кількості)"]
        SA["Serialization Anomaly\n(паралельні → неправильний стан)"]
    end

    RC -->|"захищає від"| DR
    RC -.->|"не захищає від"| NRR
    RC -.->|"не захищає від"| PR

    RR -->|"захищає від"| DR
    RR -->|"захищає від"| NRR
    RR -.->|"не захищає від"| SA

    SER -->|"захищає від ВСЬОГО"| DR
    SER -->|"захищає від ВСЬОГО"| NRR
    SER -->|"захищає від ВСЬОГО"| PR
    SER -->|"захищає від ВСЬОГО"| SA
```

---

## 8. Lifecycle транзакції в psycopg2

```mermaid
stateDiagram-v2
    [*] --> IDLE : psycopg2.connect()

    IDLE --> TX_OPEN : будь-який DML / DDL\n(psycopg2 автоматично починає транзакцію)

    TX_OPEN --> TX_OPEN : DML операції\n(INSERT / UPDATE / DELETE)

    TX_OPEN --> COMMITTED : conn.commit()
    TX_OPEN --> ROLLEDBACK : conn.rollback()
    TX_OPEN --> ROLLEDBACK : виключення Python

    COMMITTED --> IDLE : транзакція закрита
    ROLLEDBACK --> IDLE : транзакція скасована

    IDLE --> AUTOCOMMIT : conn.autocommit = True\n(кожен запит = окрема транзакція)
    AUTOCOMMIT --> AUTOCOMMIT : DDL / DML без BEGIN/COMMIT
```

### psycopg2 — ключові відмінності від sqlite3

| | SQLite (sqlite3) | PostgreSQL (psycopg2) |
|--|------------------|-----------------------|
| Параметри | `?` | `%s` |
| Dict результати | `conn.row_factory = Row` | `cursor_factory=RealDictCursor` |
| JSON | `json.dumps()` вручну | `Json()` адаптер |
| Autocommit | Немає | `conn.autocommit = True` |
| Isolation level | Обмежений | `BEGIN ISOLATION LEVEL ...` |
| RETURNING | Немає | `INSERT ... RETURNING id` |

---

## 9. OLTP vs OLAP — PostgreSQL vs Колонкові БД

```mermaid
graph LR
    subgraph ROW["PostgreSQL (Row Store)\nOLTP"]
        RS[("Рядок:\nid=1, name=Alice, age=30, email=...\nid=2, name=Bob,   age=25, email=...\nid=3, name=Carol, age=28, email=...")]
    end

    subgraph COL["DuckDB / ClickHouse (Column Store)\nOLAP"]
        CS[("Колонка age:\n30, 25, 28, ...\n\nКолонка name:\nAlice, Bob, Carol, ...")]
    end

    Q1["SELECT AVG(age) FROM users"]
    Q2["SELECT * FROM users WHERE id = 5"]

    Q1 -->|"❌ читає ВСІ колонки\n(зайвий I/O)"| ROW
    Q1 -->|"✅ читає ТІЛЬКИ age\n(компресія, SIMD)"| COL

    Q2 -->|"✅ 1 рядок = 1 disk read"| ROW
    Q2 -->|"❌ збирає по одній\nколонці = повільно"| COL
```

### Коли PostgreSQL, коли DuckDB/ClickHouse?

| Сценарій | PostgreSQL | DuckDB / ClickHouse |
|----------|------------|---------------------|
| CRUD операції | ✅ Ідеально | ❌ |
| Багато паралельних users | ✅ MVCC | ❌ |
| ACL / ролі / безпека | ✅ DCL | ❌ |
| Реплікація / HA | ✅ Streaming | ❌ |
| Агрегати по мільярдах рядків | ❌ Повільно | ✅ 10-100x швидше |
| Аналітичні дашборди | ❌ | ✅ |
| Embedded (без сервера) | ❌ | ✅ DuckDB |

---

## 10. PostgreSQL Extensions Ecosystem

```mermaid
mindmap
  root((PostgreSQL))
    Geospatial
      PostGIS
        ST_Distance
        ST_Within
        ST_Intersects
      pgRouting
        shortest path
    Time Series
      TimescaleDB
        time_bucket
        continuous aggregates
    Distributed
      Citus
        sharding
        MPP parallel queries
    Search
      pg_trgm
        ILIKE пришвидшення
        trigram similarity
      unaccent
        пошук без діакритики
    JSON / Document
      Built-in JSONB
      jsquery
    Cryptography
      pgcrypto
        AES encryption
        bcrypt
    ML / Vector
      pgvector
        cosine similarity
        nearest neighbor
        AI embeddings
```

---

## 11. Шпаргалка psycopg2

### Підключення та cursor

```python
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Підключення
conn = psycopg2.connect(
    host='localhost', port=5432,
    dbname='course_db', user='student', password='python2024'
)

# Cursor для dict-результатів
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Параметр: %s (не ?, не %d — завжди %s у psycopg2)
cursor.execute("SELECT * FROM users WHERE id = %s", (42,))
row = cursor.fetchone()        # один рядок
rows = cursor.fetchall()       # всі рядки
rows = cursor.fetchmany(100)   # N рядків

# Завжди закривай:
cursor.close()
conn.close()
```

### Транзакції

```python
try:
    conn.autocommit = False    # за замовчуванням
    cursor.execute("UPDATE accounts SET balance = balance - 500 WHERE id = 1")
    cursor.execute("UPDATE accounts SET balance = balance + 500 WHERE id = 2")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
```

### JSONB

```python
from psycopg2.extras import Json

# INSERT з JSONB
cursor.execute(
    "INSERT INTO customers (name, metadata) VALUES (%s, %s)",
    ("Alice", Json({"city": "Kyiv", "tier": "gold"}))
)

# Query JSONB
cursor.execute(
    "SELECT * FROM customers WHERE metadata @> %s",
    (Json({"tier": "gold"}),)
)
```

### RETURNING + UPSERT

```python
# RETURNING — отримати ID після INSERT
cursor.execute(
    "INSERT INTO orders (customer_id) VALUES (%s) RETURNING order_id",
    (customer_id,)
)
order_id = cursor.fetchone()['order_id']

# UPSERT — INSERT або UPDATE при конфлікті
cursor.execute("""
    INSERT INTO customers (email, name)
    VALUES (%s, %s)
    ON CONFLICT (email)
    DO UPDATE SET name = EXCLUDED.name
    RETURNING customer_id
""", (email, name))
```

### EXPLAIN

```python
cursor.execute("EXPLAIN (ANALYZE, FORMAT TEXT) SELECT * FROM products WHERE category = %s",
               ("phones",))
plan = '\n'.join(row[0] for row in cursor.fetchall())
conn.rollback()  # EXPLAIN відкриває транзакцію — закриваємо
print(plan)
```

---

## 12. Команди для роботи з Docker

```bash
# Запустити контейнер
docker compose up -d postgres

# Підключитись через psql всередині контейнера
docker exec -it course-postgres psql -U student -d course_db

# Перевірити статус
docker compose ps

# Переглянути логи
docker compose logs postgres

# Підключення з хоста (через psql)
psql -h localhost -p 5432 -U student -d course_db

# Корисні psql команди:
# \dt           — список таблиць
# \di           — список індексів
# \d tablename  — структура таблиці
# \timing       — увімкнути вимірювання часу запитів
# \x            — expanded output mode (по рядку на поле)
```

---

*Урок 30 | Модуль 3 | Python Course*
