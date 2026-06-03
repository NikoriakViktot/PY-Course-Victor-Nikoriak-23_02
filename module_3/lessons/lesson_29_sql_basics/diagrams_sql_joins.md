# SQL Joins та Підзапити — Схеми та Документація

> Урок 29 | Модуль 3 | Python Course

---

## 1. Архітектура SQL: П'ять підмов

```mermaid
mindmap
  root((SQL))
    DDL
      CREATE
      ALTER
      DROP
      TRUNCATE
    DML
      INSERT
      UPDATE
      DELETE
      MERGE
    DQL
      SELECT
    DCL
      GRANT
      REVOKE
    TCL
      BEGIN
      COMMIT
      ROLLBACK
      SAVEPOINT
```

---

## 2. Таблиця всіх SQL команд

| Категорія | Роль | Команда | Призначення | Ефект на стан БД |
|-----------|------|---------|-------------|------------------|
| **DDL** | Архітектор | `CREATE` | Створює нові об'єкти БД | Додає нову структуру в словник даних |
| | | `ALTER` | Змінює існуючий об'єкт | Мутує схему, не знищуючи об'єкт |
| | | `DROP` | Видаляє об'єкт повністю | Знищує схему та всі дані всередині |
| | | `TRUNCATE` | Швидко очищує таблицю | Миттєво видаляє всі рядки, структура залишається |
| **DML** | Оператор стану | `INSERT` | Додає нові рядки | Розширює поточний стан новими фактами |
| | | `UPDATE` | Змінює існуючі значення | Мутує конкретні значення за умовою |
| | | `DELETE` | Видаляє рядки | Зменшує стан, видаляючи факти за умовою |
| **DQL** | Спостерігач | `SELECT` | Читає та фільтрує дані | Читає стан без його зміни |
| **DCL** | Охоронець | `GRANT` | Надає привілеї | Розширює матрицю доступу |
| | | `REVOKE` | Відкликає привілеї | Звужує матрицю доступу |
| **TCL** | Синхронізатор | `BEGIN` | Відкриває транзакцію | Ізолює зміни від інших сесій |
| | | `COMMIT` | Зберігає зміни | Назавжди записує стан на диск |
| | | `ROLLBACK` | Скасовує зміни | Повертає до попереднього стану |
| | | `SAVEPOINT` | Проміжна точка | Дозволяє частковий відкат |

---

## 3. Типи зв'язків між таблицями

```mermaid
erDiagram
    DEPARTMENTS {
        int dept_id PK
        string dept_name
        string location
        real budget
    }

    EMPLOYEES {
        int emp_id PK
        string first_name
        string last_name
        real salary
        int dept_id FK
    }

    PROJECTS {
        int proj_id PK
        string proj_name
        string deadline
    }

    EMPLOYEE_PROJECTS {
        int emp_id FK
        int proj_id FK
        string role
    }

    DEPARTMENTS ||--o{ EMPLOYEES : "1:M (один відділ — багато співробітників)"
    EMPLOYEES }o--o{ PROJECTS : "M:N через junction table"
    EMPLOYEES ||--o{ EMPLOYEE_PROJECTS : "реалізація M:N"
    PROJECTS ||--o{ EMPLOYEE_PROJECTS : "реалізація M:N"
```

---

## 4. SQL JOIN операції — Діаграма Венна

```mermaid
graph LR
    subgraph "INNER JOIN — перетин"
        direction LR
        A1["Таблиця A"] -.-> INT1["✓ тільки збіги ✓"]
        B1["Таблиця B"] -.-> INT1
    end

    subgraph "LEFT JOIN — вся ліва + збіги"
        direction LR
        A2["Таблиця A ✓"] --> INT2["✓ збіги ✓"]
        B2["Таблиця B"] -.-> INT2
        A2 --> LEFT2["тільки A (NULL для B)"]
    end

    subgraph "RIGHT JOIN — вся права + збіги"
        direction LR
        A3["Таблиця A"] -.-> INT3["✓ збіги ✓"]
        B3["Таблиця B ✓"] --> INT3
        B3 --> RIGHT3["тільки B (NULL для A)"]
    end

    subgraph "FULL OUTER JOIN — всі рядки"
        direction LR
        A4["Таблиця A ✓"] --> INT4["✓ збіги ✓"]
        B4["Таблиця B ✓"] --> INT4
        A4 --> ONLYA["тільки A (NULL для B)"]
        B4 --> ONLYB["тільки B (NULL для A)"]
    end
```

---

## 5. Детальна схема JOIN типів

```mermaid
flowchart TD
    Q["Який тип JOIN мені потрібен?"]

    Q --> Q1{"Потрібні лише рядки,\nде є збіг в обох\nтаблицях?"}
    Q1 -->|ТАК| INNER["INNER JOIN\nПовертає: тільки збіги\nБез збігу — рядок відсутній"]

    Q1 -->|НІ| Q2{"Потрібні ВСІ рядки\nлівої таблиці?"}
    Q2 -->|ТАК| LEFT["LEFT JOIN\nПовертає: всі з лівої\n+ збіги правої (NULL якщо немає)"]

    Q2 -->|НІ| Q3{"Потрібні ВСІ рядки\nправої таблиці?"}
    Q3 -->|ТАК| RIGHT["RIGHT JOIN\nПовертає: всі з правої\n+ збіги лівої (NULL якщо немає)"]

    Q3 -->|НІ| FULL["FULL OUTER JOIN\nПовертає: всі рядки обох таблиць\nNULL для незбіглих сторін"]

    INNER --> EX1["SELECT e.name, d.dept_name\nFROM employees e\nINNER JOIN departments d\nON e.dept_id = d.dept_id"]

    LEFT --> EX2["SELECT d.dept_name, COUNT(e.emp_id)\nFROM departments d\nLEFT JOIN employees e\nON d.dept_id = e.dept_id\nGROUP BY d.dept_id"]

    LEFT --> TRICK["Трюк: знайти рядки БЕЗ пари\nWHERE e.emp_id IS NULL"]
```

---

## 6. Візуалізація результатів JOIN

```mermaid
block-beta
    columns 5
    space:1 H1["A.id"] H2["A.val"] H3["B.id"] H4["B.val"]

    space:5

    space:1 IH["INNER JOIN результат:"]
    space:4

    space:1 R1A["1"] R1B["apple"] R1C["1"] R1D["red"]
    space:1 R2A["2"] R2B["banana"] R2C["2"] R2D["yellow"]

    space:5

    space:1 LH["LEFT JOIN результат:"]
    space:4

    space:1 L1A["1"] L1B["apple"] L1C["1"] L1D["red"]
    space:1 L2A["2"] L2B["banana"] L2C["2"] L2D["yellow"]
    space:1 L3A["3"] L3B["cherry"] L3C["NULL"] L3D["NULL"]
```

---

## 7. Алгоритми виконання JOIN (під капотом)

```mermaid
flowchart TD
    J["JOIN запит\nSELECT ... FROM A JOIN B ON A.id = B.a_id"]

    J --> QP["Query Planner\n(аналізує статистику таблиць)"]

    QP --> C1{"Таблиця A\nмаленька?"}
    C1 -->|ТАК| NL["Nested Loop Join\nO(N × log M) з індексом\nO(N × M) без індексу"]
    C1 -->|НІ| C2{"Обидві таблиці\nвідсортовані\nпо ключу?"}
    C2 -->|ТАК| MJ["Merge Join\nO(N + M)\nЕфективний для великих відсортованих"]
    C2 -->|НІ| HJ["Hash Join\nO(N + M)\nСтворює хеш-таблицю меншої"]

    NL --> IDX{"Є індекс\nна FK колонці?"}
    IDX -->|ТАК| FAST["✓ O(N × log M)\nМілісекунди"]
    IDX -->|НІ| SLOW["✗ O(N × M)\nМожуть бути хвилини!"]

    style FAST fill:#90EE90
    style SLOW fill:#FFB6C1
```

---

## 8. Підзапити (Subqueries)

### Типи підзапитів

```mermaid
mindmap
  root((Підзапити))
    За розташуванням
      WHERE
        Scalar повертає 1 значення
        IN повертає список
        EXISTS перевіряє наявність
      FROM
        Inline view похідна таблиця
      SELECT
        Correlated для кожного рядка
    За залежністю
      Незалежний
        Виконується один раз
        Не залежить від зовнішнього
      Корельований
        Виконується для кожного рядка
        Посилається на зовнішній запит
        Небезпечний O N²
```

### JOIN vs Підзапит — коли що використовувати

```mermaid
flowchart LR
    Q["Обрати JOIN чи підзапит?"]

    Q --> Q1{"Потрібні колонки\nз кількох таблиць\nв результаті?"}
    Q1 -->|ТАК| JOIN["Використовуй JOIN\nКраща продуктивність\nChain: A JOIN B JOIN C"]

    Q1 -->|НІ| Q2{"Фільтрація за\nагрегованим\nрезультатом?"}
    Q2 -->|ТАК| SUB["Підзапит у WHERE\nSELECT ... WHERE salary >\n  (SELECT AVG(salary) FROM ...)"]

    Q2 -->|НІ| Q3{"Перевірка наявності\nрядків у іншій таблиці?"}
    Q3 -->|ТАК| EXISTS["EXISTS підзапит\nSELECT ... WHERE EXISTS\n  (SELECT 1 FROM orders ...)"]

    Q3 -->|НІ| CTE["Common Table Expression\nWITH cte AS (...)\nSELECT * FROM cte"]
```

---

## 9. Lifecycle транзакції (TCL)

```mermaid
stateDiagram-v2
    [*] --> Active : BEGIN / START TRANSACTION

    Active --> Active : DML операції\n(INSERT / UPDATE / DELETE)

    Active --> Committed : COMMIT\n(зміни збережені назавжди)
    Active --> RolledBack : ROLLBACK\n(всі зміни скасовано)

    Active --> Savepoint : SAVEPOINT sp1\n(проміжна точка)
    Savepoint --> Active : продовжуємо\nDML операції
    Savepoint --> Active : ROLLBACK TO sp1\n(скасуємо лише від sp1)
    Savepoint --> Committed : COMMIT\n(всі зміни з початку)

    Committed --> [*] : блокування знято\nресурси звільнено
    RolledBack --> [*] : БД повернута\nдо попереднього стану
```

---

## 10. ACID властивості

```mermaid
graph TD
    ACID["ACID Гарантії"]

    ACID --> A["**Atomicity (Атомарність)**\nАбо ВСІ операції — або ЖОДНА\nПриклад: переказ грошей: дебет + кредит разом"]
    ACID --> C["**Consistency (Узгодженість)**\nТранзакція веде від одного\nкоректного стану до іншого\nПриклад: NOT NULL, FOREIGN KEY не порушені"]
    ACID --> I["**Isolation (Ізоляція)**\nПаралельні транзакції\nне бачать незавершені зміни\nодна одної"]
    ACID --> D["**Durability (Надійність)**\nПісля COMMIT — дані на диску\nнавіть при збої сервера\nМеханізм: Write-Ahead Log (WAL)"]

    I --> IL["Рівні ізоляції:\n1. Read Uncommitted (найслабший)\n2. Read Committed (за замовч.)\n3. Repeatable Read\n4. Serializable (найсильніший)"]
```

---

## 11. SQLite vs PostgreSQL — відмінності

| Особливість | SQLite | PostgreSQL |
|-------------|--------|------------|
| Foreign keys | Потрібно `PRAGMA foreign_keys = ON` | Увімкнені за замовч. |
| RIGHT JOIN | Підтримується (v3.39+) | Так |
| FULL OUTER JOIN | ❌ Не підтримується | Так |
| TRUNCATE | ❌ Немає (використовуй `DELETE FROM`) | Так |
| DCL (GRANT/REVOKE) | ❌ Немає (файлова БД) | Так |
| MERGE / Upsert | `INSERT OR REPLACE`, `INSERT OR IGNORE` | `INSERT ... ON CONFLICT DO UPDATE` |
| MVCC | Ні (WAL mode наближений) | Повноцінний MVCC |
| Concurrency | 1 writer / багато readers | Повна підтримка |
| Розмір | Файл до 281 TB | Необмежено |

---

## 12. Шпаргалка: Типові патерни

### Знайти рядки БЕЗ пари (LEFT JOIN + NULL)
```sql
-- Книги, які жодного разу не позичали
SELECT b.title
FROM books b
    LEFT JOIN borrows br ON b.book_id = br.book_id
WHERE br.borrow_id IS NULL;
```

### Агрегація через GROUP BY + HAVING
```sql
-- Автори, у яких більше 2 книг
SELECT author_id, COUNT(*) AS books_count
FROM books
GROUP BY author_id
HAVING COUNT(*) > 2;
```

### Upsert в SQLite
```sql
-- Вставити або оновити якщо вже є (по email)
INSERT INTO members (email, full_name)
VALUES ('test@ua.com', 'Тест Тестов')
ON CONFLICT(email)
DO UPDATE SET full_name = excluded.full_name;
```

### Підзапит vs JOIN (еквіваленти)
```sql
-- Підзапит: співробітники відділу 'IT'
SELECT * FROM employees
WHERE dept_id = (SELECT dept_id FROM departments WHERE dept_name = 'IT');

-- Еквівалент через JOIN:
SELECT e.* FROM employees e
    INNER JOIN departments d ON e.dept_id = d.dept_id
WHERE d.dept_name = 'IT';
```

### Транзакція з обробкою помилок (Python)
```python
try:
    conn.execute("BEGIN")
    conn.execute("UPDATE accounts SET balance = balance - 500 WHERE id = 1")
    conn.execute("UPDATE accounts SET balance = balance + 500 WHERE id = 2")
    conn.commit()
    print("Переказ успішний!")
except Exception as e:
    conn.rollback()
    print(f"Помилка: {e} — ROLLBACK!")
```

---

*Урок 29 | Модуль 3 | Python Course*
