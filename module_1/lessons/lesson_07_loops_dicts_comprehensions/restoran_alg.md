# Алгоритмічне мислення у Python — Урок 7

## Сценарій: власник ресторану хоче аналітику

До нас прийшов власник ресторану з реальними даними чеків (seaborn tips dataset).
Він хоче відповіді на питання:

* Коли найприбутковіші дні?
* Обід чи вечеря приносить більше?
* Скільки людей в середньому за столом?
* Який відсоток чайових?

Наш інструмент: `NamedTuple`, `for`, `dict`, `list`, `set`, `comprehensions`.

---

# 1. Архітектура даних

Де і як зберігаються дані на кожному кроці.

```mermaid
graph TD

A[seaborn tips dataset]

A --> B[DataFrame]

B --> C[List of Order]

C --> D[Order — NamedTuple]

D --> D1[total_bill: float]
D --> D2[tip: float]
D --> D3[sex: str]
D --> D4[smoker: str]
D --> D5[day: str]
D --> D6[time: str]
D --> D7[size: int]

C --> E[Dict агрегати]
C --> F[Set унікальні значення]
C --> G[List comprehension]
```

```
реальні дані → NamedTuple → алгоритми → аналітика
```

---

# 2. NamedTuple: структура чеку

Чому NamedTuple краще за звичайний tuple.

```mermaid
graph LR

A[Один чек з ресторану]

A --> B[Звичайний tuple]
A --> C[NamedTuple Order]

B --> B1["order[0] — що це?"]
B --> B2["order[4] — незрозуміло"]
B --> B3[треба рахувати індекси]

C --> C1[order.total_bill — зрозуміло]
C --> C2[order.day — зрозуміло]
C --> C3[order.size — зрозуміло]
C --> C4[immutable — незмінний]
C --> C5[це справжній tuple]
```

```
order[0]          → незрозуміло
order.total_bill  → одразу ясно
```

Розрахунки — прості вирази у коді, не методи:

```python
tip_percent     = (order.tip / order.total_bill) * 100
bill_per_person = order.total_bill / order.size
is_large_table  = order.size >= 5
```

---

# 3. Завантаження даних: DataFrame → List[Order]

Два способи перетворити DataFrame на список Python-об'єктів.

```mermaid
flowchart TD

A[tips_df — DataFrame] --> B1[Варіант 1: for loop + append]
A --> B2[Варіант 2: list comprehension]

B1 --> C1[for row in iterrows]
C1 --> C2[Створити Order з полів row]
C2 --> C3[orders.append]
C3 --> C4{Ще рядки?}
C4 -->|Так| C1
C4 -->|Ні| C5[orders готовий]

B2 --> D1["[Order... for _, row in iterrows]"]
D1 --> D2[orders готовий]

C5 --> E[List of 244 Order]
D2 --> E
```

```
DataFrame → for loop або list comp → List[Order]
Після цього pandas більше не потрібен
```

---

# 4. For Loop: обробка потоку подій

Кожна ітерація — це один клієнт, який заплатив рахунок.

```mermaid
flowchart TD

A[Початок]

B[orders — список всіх чеків]

C[Взяти наступний order]

D[Читаємо поля: order.day, order.total_bill...]

E[Обробляємо: рахуємо, агрегуємо, фільтруємо]

F{Ще є чеки?}

G[Кінець — результат готовий]

A --> B
B --> C
C --> D
D --> E
E --> F

F -->|Так| C
F -->|Ні| G
```

```
for loop = event processor
кожна ітерація = один клієнт заплатив
```

---

# 5. Dict: Counting Pattern

Найважливіший патерн уроку.

```mermaid
flowchart TD

A["Початок: revenue_by_day = {}"]

B[Взяти order]

C[day = order.day]
D[bill = order.total_bill]

E{day вже є у dict?}

F["повертає існуюче значення + bill"]
G["повертає 0 + bill"]

H[записує результат у dict]

I{Ще чеки?}

J[revenue_by_day готовий]

A --> B
B --> C
C --> D
D --> E

E -->|Так| F
E -->|Ні| G

F --> H
G --> H

H --> I

I -->|Так| B
I -->|Ні| J
```

Код цього алгоритму:

```python
revenue_by_day[day] = revenue_by_day.get(day, 0) + bill
```

```
.get(key, 0) → шукаємо коробку у шафі:
  є   → беремо значення
  нема → повертаємо 0
```

---

# 6. Три словники за один цикл

За один прохід по даних рахуємо одразу три метрики.

```mermaid
flowchart LR

A[for order in orders]

A --> B[day = order.day]

B --> C["revenue_by_day[day] += total_bill"]
B --> D["orders_by_day[day] += 1"]
B --> E["guests_by_day[day] += size"]

C --> F[Дохід по днях]
D --> G[Кількість чеків]
E --> H[Кількість гостей]
```

```python
revenue_by_day[day] = revenue_by_day.get(day, 0) + order.total_bill
orders_by_day[day]  = orders_by_day.get(day, 0)  + 1
guests_by_day[day]  = guests_by_day.get(day, 0)  + order.size
```

```
один цикл → три результати
```

---

# 7. Leader Algorithm

Знаходимо найприбутковіший день.

```mermaid
flowchart TD

A[Початок]

B[best_day = None]
C[best_revenue = 0]

D[Взяти наступний день і його дохід]

E{revenue > best_revenue?}

F[best_revenue = revenue]
G[best_day = day]

H{Ще дні є?}

I["Кінець: best_day = найкращий день"]

A --> B
B --> C
C --> D
D --> E

E -->|Так| F
F --> G
G --> H

E -->|Ні| H

H -->|Так| D
H -->|Ні| I
```

Або через вбудований Python:

```python
best_day = max(revenue_by_day, key=revenue_by_day.get)
```

```
ручний алгоритм → розуміємо логіку
max() → pythonic варіант
```

---

# 8. Set Pattern

Знаходимо унікальні дні, типи зміни, розміри столів.

```mermaid
flowchart TD

A["Початок: unique_days = set()"]

B[Взяти order]

C[unique_days.add order.day]

D{Значення вже є у set?}

E[Ігнорувати — дублікат]
F[Додати у set]

G{Ще чеки?}

H[unique_days — тільки унікальні]

A --> B
B --> C
C --> D

D -->|Так| E
D -->|Ні| F

E --> G
F --> G

G -->|Так| B
G -->|Ні| H
```

```
set автоматично прибирає дублікати
```

Set comprehension — компактніше:

```python
unique_days  = {order.day  for order in orders}
unique_times = {order.time for order in orders}
unique_sizes = {order.size for order in orders}
```

---

# 9. Grouping Pattern: dict of lists

Зберігаємо не суму, а список всіх чеків.

```mermaid
flowchart TD

A["Початок: orders_by_day = {}"]

B[Взяти order]

C[day = order.day]

D{day вже є у dict?}

E["створює порожній список []"]
F["orders_by_day[day].append(order)"]

G{Ще чеки?}

H["orders_by_day — dict of lists"]

A --> B
B --> C
C --> D

D -->|Ні| E
E --> F

D -->|Так| F

F --> G

G -->|Так| B
G -->|Ні| H
```

```python
orders_by_day.setdefault(day, []).append(order)
```

```
Counting:  {день: кількість}
Grouping:  {день: [order1, order2, order3...]}
```

---

# 10. defaultdict: еволюція коду

`defaultdict` робить те саме що `.get()` і `setdefault()`, але коротше.

```mermaid
graph TD

A[Патерн] --> B[dict варіант]
A --> C[defaultdict варіант]

B --> B1["d[k] = d.get(k, 0) + 1"]
B --> B2["d[k] = d.get(k, 0) + x"]
B --> B3["d.setdefault(k, []).append(x)"]

C --> C1["defaultdict(int) → d[k] += 1"]
C --> C2["defaultdict(float) → d[k] += x"]
C --> C3["defaultdict(list) → d[k].append(x)"]

B1 -.->|те саме| C1
B2 -.->|те саме| C2
B3 -.->|те саме| C3
```

```python
from collections import defaultdict

orders_count = defaultdict(int)
revenue      = defaultdict(float)
groups       = defaultdict(list)

for order in orders:
    orders_count[order.day] += 1
    revenue[order.day]      += order.total_bill
    groups[order.day].append(order)
```

```
спочатку вчимо .get() — розуміємо механіку
потім defaultdict — той самий алгоритм, чистіший синтаксис
```

---

# 11. List Comprehension

Три форми — filter, mapping, filter+transform.

```mermaid
flowchart LR

A[orders — всі чеки] --> B[for order in orders]

B --> C{if умова?}

C -->|Так| D[зберегти або трансформувати]
C -->|Ні| E[пропустити]

D --> F[новий список]
E --> F
```

```mermaid
graph TD

A[List Comprehension] --> B[тільки фільтр]
A --> C[тільки mapping]
A --> D[фільтр + mapping]

B --> B1["[o for o in orders if o.total_bill > 40]"]

C --> C1["[(o.tip / o.total_bill) * 100 for o in orders]"]

D --> D1["[o.total_bill for o in orders if o.time == 'Dinner']"]
```

```
[що_зберегти  for елемент in колекція  if умова]
   Transform       Iterate               Filter
```

Важливо:

```python
# Замість методу — простий вираз
(o.tip / o.total_bill) * 100   # tip%
o.total_bill / o.size          # чек на людину
o.size >= 5                    # великий стіл
```

---

# 12. Dict Comprehension

Будуємо словник з агрегатом в один рядок.

```mermaid
flowchart TD

A[revenue_by_day — вже є]
B[orders_count — вже є]

A --> C[Dict Comprehension]
B --> C

C --> D["{ day: revenue / count  for day in revenue_by_day }"]

D --> E[avg_bill_by_day]

E --> E1[Sun: середній чек]
E --> E2[Sat: середній чек]
E --> E3[Thur: середній чек]
E --> E4[Fri: середній чек]
```

```python
avg_bill_by_day = {
    day: revenue_by_day[day] / orders_count[day]
    for day in revenue_by_day
}

tip_pct_by_day = {
    day: sum((o.tip / o.total_bill) * 100 for o in groups[day]) / len(groups[day])
    for day in groups
}
```

---

# 13. Повний Pipeline аналітики

Як дані течуть від seaborn до відповіді для власника.

```mermaid
flowchart TD

A[seaborn tips dataset] --> B[DataFrame 244 рядки]

B --> C[List of Order — NamedTuple]

C --> D1[For Loop: counting/aggregation]
C --> D2[For Loop: grouping]
C --> D3[Set: унікальні]
C --> D4[List comp: фільтр і mapping]

D1 --> E1[revenue_by_day dict]
D1 --> E2[orders_by_day dict]
D1 --> E3[revenue_by_time dict]
D1 --> E4[guests_by_day dict]

D2 --> E5[orders_grouped dict of lists]

D3 --> E6[unique_days set]
D3 --> E7[unique_times set]
D3 --> E8[unique_sizes set]

D4 --> E9[big_orders list]
D4 --> E10[top10 list]
D4 --> E11[all_tip_percents list]

E1 --> F1[Leader Algorithm]
F1 --> G1[best_day]

E1 --> F2[Dict Comprehension]
E2 --> F2
F2 --> G2[avg_bill_by_day]

G1 --> Z[Звіт для власника]
E2 --> Z
E3 --> Z
E4 --> Z
G2 --> Z
E9 --> Z
E10 --> Z
```

---

# 14. Відповідь на питання власника

Від даних до рішення.

```mermaid
flowchart LR

Q1[Найприбутковіший день?] --> A1["revenue_by_day dict"]
A1 --> A2["max(d, key=d.get)"]
A2 --> R1[Sat — найкращий]

Q2[Обід чи вечеря?] --> B1["revenue_by_time dict"]
B1 --> B2[порівняння ключів]
B2 --> R2[Dinner переможець]

Q3[Скільки людей?] --> C1["guests_by_day / orders_by_day"]
C1 --> R3[середній стіл 2.6 осіб]

Q4[Середній tip%?] --> D1["(o.tip / o.total_bill) * 100 for o in orders"]
D1 --> D2[sum div len]
D2 --> R4[avg 16.1%]

Q5[Топ чеки?] --> E1["sorted(orders, key=lambda o: o.total_bill)[:10]"]
E1 --> R5[топ-10 список]
```

---

# 15. Чотири патерни мислення

Будь-яку задачу аналізу даних можна розкласти так:

```mermaid
graph TD

A[Нова задача аналізу] --> B{Який патерн?}

B --> C[ITERATION]
B --> D[MAPPING]
B --> E[AGGREGATION]
B --> F[COUNTING]

C --> C1["Пошук, перевірка умов"]
C --> C2["for order in orders: if ..."]

D --> D1["Трансформація кожного елементу"]
D --> D2["[(o.tip / o.total_bill) * 100 for o in orders]"]

E --> E1["Багато → одне число"]
E --> E2["total += order.total_bill"]

F --> F1["Частота по категоріях"]
F --> F2["d[key] = d.get(key, 0) + 1"]
```

---

# 16. Відповідність патернів і Python

| Патерн | Інструмент | Приклад |
|---|---|---|
| Iteration | `for` + `if` | пошук великих чеків |
| Mapping | `list comprehension` | `[(o.tip / o.total_bill) * 100 for o in orders]` |
| Aggregation | `+=` накопичувач | `total += order.total_bill` |
| Counting | `d.get(k, 0) + 1` | кількість чеків по днях |
| Aggregation dict | `d.get(k, 0) + x` | дохід по днях |
| Grouping | `setdefault + append` | всі чеки по днях |
| Leader | `max(d, key=d.get)` | найкращий день |
| Unique | `set` | унікальні дні |
| defaultdict | `defaultdict(int/float/list)` | те саме без `.get()` |

---

# Головна ідея уроку

```
NamedTuple  = tuple з іменами полів (незмінний)
for loop    = система обробки потоку подій
dict        = база даних аналітики
list comp   = конвеєр трансформацій
set         = індекс унікальних значень
defaultdict = dict без .get() і setdefault()
```

Три рядки, які пояснюють всю аналітику реального бізнесу:

```python
revenue_by_day[day] = revenue_by_day.get(day, 0) + bill        # counting
best_day = max(revenue_by_day, key=revenue_by_day.get)          # leader
tip_pcts = [(o.tip / o.total_bill) * 100 for o in orders]      # mapping
```

```
дані → NamedTuple → цикл → dict → аналітика → рішення
```
