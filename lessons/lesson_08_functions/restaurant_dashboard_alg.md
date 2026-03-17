# Алгоритмічне мислення у Python — Урок 8

## Завдання

Власник ресторану хоче **інтерактивний дашборд**:
фільтрує чеки в реальному часі й одразу бачить KPI, графіки, таблиці.

**Проблема, яку вирішуємо:**
Аналітичний код з урока 7 — один великий блок.
Щоб змінити фільтр, треба переписувати весь цикл.
Щоб підключити UI — неможливо, код не розбитий на частини.

**Рішення — функціональна декомпозиція:**

```
Монолітний блок 200 рядків
        ↓
Чисті функції:  предикати + трансформери + редьюсери
        ↓
Pipeline: apply_filters → enrich_all → calc_kpis → ...
        ↓
Dash callback викликає pipeline при кожній зміні UI
```

**Що виконує алгоритм:**
Будь-яка комбінація фільтрів (день, зміна, стать, курці, гості, сума) → повний перерахунок KPI, шести графіків і двох таблиць — за один виклик `run_pipeline()`.

---

# 1. Архітектура: структури даних

```mermaid
graph TD

A[seaborn tips dataset]
A --> B[DataFrame]
B --> C[List of Order — NamedTuple]

C --> D[Order]
D --> D1[total_bill: float]
D --> D2[tip: float]
D --> D3[sex: str]
D --> D4[smoker: str]
D --> D5[day: str]
D --> D6[time: str]
D --> D7[size: int]

C --> E[apply_filters]

E --> F[List of RichOrder — NamedTuple]
F --> G[RichOrder]
G --> G1[всі поля Order]
G --> G2[tip_pct: float]
G --> G3[bill_per_person: float]
G --> G4[day_ua: str]
G --> G5[time_ua: str]

F --> H1[calc_kpis]
F --> H2[group_by_day]
F --> H3[group_by_time]
F --> H4[group_by_size]
F --> H5[group_by_sex]
F --> H6[top_by_tip_pct]

H1 --> Z[dict KPI]
H2 --> Z2[list of dict]
H3 --> Z3[list of dict]
H4 --> Z4[list of dict]
H5 --> Z5[list of dict]
H6 --> Z6[list of RichOrder]
```

```
Order      = сирий чек (7 полів)
RichOrder  = збагачений чек (11 полів, незмінний)
Різниця:   enrich_order() додає tip_pct, bill_per_person, day_ua, time_ua
```

---

# 2. load_orders() — Трансформер завантаження

**Задача:** перетворити DataFrame на `List[Order]` один раз при старті.
Після цього pandas більше не потрібен — тільки чистий Python.

```mermaid
flowchart TD

A[sns.load_dataset tips] --> B[DataFrame 244 рядки]

B --> C[list comprehension]
C --> D[для кожного row]
D --> E[Order total_bill tip sex smoker day time size]
E --> F{ще рядки?}
F -->|Так| D
F -->|Ні| G[ALL_ORDERS — 244 Order]

G --> H[зберігається у пам'яті раз і назавжди]
```

```python
ALL_ORDERS: list[Order] = load_orders()
# викликається один раз при імпорті модуля
```

```
DataFrame рядок → Order(total_bill=..., tip=..., ...)
float(row[...]) → гарантує правильний тип
```

---

# 3. Предикати (Predicates)

**Задача:** вирішити для кожного чека — потрапляє він у вибірку чи ні.
Предикат → чиста функція → завжди `True` або `False`.

```mermaid
graph TD

A[Order] --> P1[pred_day]
A --> P2[pred_time]
A --> P3[pred_smoker]
A --> P4[pred_sex]
A --> P5[pred_size]
A --> P6[pred_bill]

P1 --> R1{order.day in days?}
R1 -->|Так| T1[True]
R1 -->|Ні| F1[False]

P2 --> R2{order.time in times?}
R2 -->|Так| T2[True]
R2 -->|Ні| F2[False]

P3 --> R3{order.smoker in smoker?}
P4 --> R4{order.sex in sexes?}
P5 --> R5{lo <= order.size <= hi?}
P6 --> R6{lo <= order.total_bill <= hi?}
```

```python
pred_day(order, ["Sat", "Sun"])         # True якщо субота або неділя
pred_size(order, lo=2, hi=4)            # True якщо стіл 2–4 особи
pred_bill(order, lo=10.0, hi=30.0)      # True якщо чек $10–$30
pred_sex(order, ["Female"])             # True якщо клієнтка
```

```
Предикат:
  вхід  → Order + параметри фільтра
  вихід → True (пропускаємо) або False (відкидаємо)
  ефект → жодного (чиста функція)
```

---

# 4. apply_filters() — Комбінований фільтр

**Задача:** застосувати всі шість предикатів одночасно (логічне AND).
Залишити тільки ті чеки, що пройшли всі перевірки.

```mermaid
flowchart TD

A[ALL_ORDERS — 244 чеки] --> B[List Comprehension]

B --> C[Взяти order]

C --> D{pred_day?}
D -->|False| X[пропустити]
D -->|True| E{pred_time?}

E -->|False| X
E -->|True| F{pred_smoker?}

F -->|False| X
F -->|True| G{pred_sex?}

G -->|False| X
G -->|True| H{pred_size?}

H -->|False| X
H -->|True| I{pred_bill?}

I -->|False| X
I -->|True| J[додати до результату]

J --> K{ще чеки?}
X --> K
K -->|Так| C
K -->|Ні| L[filtered — List of Order N чеків]
```

```python
return [
    o for o in orders
    if pred_day(o, days)
    and pred_time(o, times)
    and pred_smoker(o, smoker)
    and pred_sex(o, sexes)
    and pred_size(o, lo_s, hi_s)
    and pred_bill(o, lo_b, hi_b)
]
```

```
244 чеків → apply_filters() → N чеків (N ≤ 244)
AND-ланцюг: якщо хоча б один предикат False → чек відкидається
```

---

# 5. enrich_order() — Трансформер збагачення

**Задача:** перетворити `Order` на `RichOrder` — додати обчислені поля.
Кількість елементів не змінюється. Оригінал не змінюється (immutable).

```mermaid
flowchart LR

A[Order] --> B[enrich_order]

B --> C[RichOrder]

C --> C1[всі 7 полів Order]
C --> C2["tip_pct = round tip / total_bill * 100, 1"]
C --> C3["bill_per_person = round total_bill / size, 2"]
C --> C4["day_ua = _DAY_UA.get day"]
C --> C5["time_ua = _TIME_UA.get time"]
```

```python
# Маппінги для перекладу
_DAY_UA  = {"Thur": "Четвер", "Fri": "П'ятниця", "Sat": "Субота", "Sun": "Неділя"}
_TIME_UA = {"Lunch": "Обід", "Dinner": "Вечеря"}
```

```
Order(23.68, 3.31, ..., "Sun", "Dinner", 2)
        ↓  enrich_order()
RichOrder(23.68, 3.31, ..., "Sun", "Dinner", 2,
          tip_pct=14.0, bill_per_person=11.84,
          day_ua="Неділя", time_ua="Вечеря")
```

---

# 6. enrich_all() — Map Pattern

**Задача:** застосувати `enrich_order` до кожного чека у списку.
Класичний map: `len(input) == len(output)`.

```mermaid
flowchart LR

A["List[Order] — N чеків"] --> B[enrich_all]

B --> C["List[RichOrder] — N чеків"]

B --> B1[enrich_order o1 → RichOrder]
B --> B2[enrich_order o2 → RichOrder]
B --> B3[enrich_order o3 → RichOrder]
B --> B4[...]
```

```python
def enrich_all(orders):
    return [enrich_order(o) for o in orders]
```

```
Map Pattern:
  [transform(x) for x in data]
  Кількість не змінюється — тільки форма
```

---

# 7. calc_kpis() — Редьюсер KPI

**Задача:** зменшити список до словника з шістьма числовими показниками.
Вбудовані редьюсери: `sum()`, `len()`, `max()`.

```mermaid
flowchart TD

A["List[RichOrder] — N чеків"] --> B[calc_kpis]

B --> C1["bills = [o.total_bill for o in orders]"]
B --> C2["tips  = [o.tip for o in orders]"]
B --> C3["sizes = [o.size for o in orders]"]
B --> C4["pcts  = [o.tip_pct for o in orders]"]

C1 --> D1["revenue = sum(bills)"]
C1 --> D2["avg_bill = sum(bills) / len(bills)"]
C2 --> D3["tips = sum(tips)"]
C4 --> D4["avg_tip_pct = sum(pcts) / len(pcts)"]
C3 --> D5["avg_size = sum(sizes) / len(sizes)"]
A  --> D6["count = len(orders)"]

D1 --> E[dict KPI]
D2 --> E
D3 --> E
D4 --> E
D5 --> E
D6 --> E
```

```python
{
    "revenue":     4827.77,   # ← sum(bills)
    "tips":         731.58,   # ← sum(tips)
    "avg_bill":      19.79,   # ← sum / len
    "avg_tip_pct":   16.1,    # ← sum / len
    "count":           244,   # ← len
    "avg_size":        2.6,   # ← sum / len
}
```

```
Reducer Pattern:
  List[RichOrder] → одне значення або агрегат
  Багато → одне (список 244 → 6 чисел)
```

---

# 8. group_by_day() — Редьюсер з групуванням

**Задача:** порахувати виручку, чайові, кількість чеків по кожному дню.
Той самий Counting Pattern з урока 7, але тепер у функції.

```mermaid
flowchart TD

A["List[RichOrder]"] --> B[for o in orders]

B --> C["rev[o.day]  += o.total_bill"]
B --> D["tips[o.day] += o.tip"]
B --> E["cnt[o.day]  += 1"]

C --> F[defaultdict float]
D --> F
E --> G[defaultdict int]

F --> H[List Comprehension]
G --> H

H --> I["[{day, day_ua, revenue, tips, orders, avg_bill} for d in rev]"]

I --> J["sorted key=revenue reverse=True"]

J --> K["list of dict — відсортований за виручкою"]
```

```python
# Counting Pattern (урок 7) → тепер у функції (урок 8)
rev[o.day]  += o.total_bill   # defaultdict(float)
cnt[o.day]  += 1              # defaultdict(int)
```

```
group_by_day повертає:
  [{"day": "Sat", "day_ua": "Субота", "revenue": 1778.40, ...},
   {"day": "Sun", "day_ua": "Неділя", "revenue": 1627.16, ...}, ...]
```

---

# 9. group_by_time() — Редьюсер Lunch vs Dinner

**Задача:** порівняти середній tip% і середній чек для обіду і вечері.
Зберігаємо списки значень, потім рахуємо середнє.

```mermaid
flowchart TD

A["List[RichOrder]"] --> B[for o in orders]

B --> C["tip_pcts[o.time].append(o.tip_pct)"]
B --> D["bills[o.time].append(o.total_bill)"]

C --> E["defaultdict(list)"]
D --> E

E --> F[для кожного time]
F --> G["avg_tip_pct = sum(p) / len(p)"]
F --> H["avg_bill    = sum(b) / len(b)"]
F --> I["orders      = len(p)"]

G --> J[list of dict]
H --> J
I --> J
```

```
Grouping Pattern (урок 7) → агрегат списків
tip_pcts["Dinner"] = [14.0, 16.1, 5.9, ...]  → середнє
```

---

# 10. group_by_size() — Редьюсер по розміру столу

**Задача:** показати як розмір столу впливає на виручку і tip%.

```mermaid
flowchart LR

A["List[RichOrder]"] --> B[for o in orders]

B --> C["rev[o.size]  += o.total_bill"]
B --> D["pcts[o.size].append(o.tip_pct)"]
B --> E["cnt[o.size]  += 1"]

C --> F[dict int → float]
D --> G[dict int → list]
E --> H[dict int → int]

F --> I[sorted by size]
G --> I
H --> I

I --> J["[{size, size_label, revenue, avg_tip_pct, orders}]"]
```

```python
# size_label — локалізована назва
f"{s} {'особа' if s == 1 else 'особи' if s <= 4 else 'осіб'}"
# 1 → "1 особа",  2 → "2 особи",  6 → "6 осіб"
```

---

# 11. group_by_sex() — Редьюсер статі

**Задача:** порівняти виручку і tip% між Male і Female для pie chart.

```mermaid
flowchart LR

A["List[RichOrder]"] --> B[for o in orders]

B --> C["rev[o.sex]  += o.total_bill"]
B --> D["pcts[o.sex].append(o.tip_pct)"]
B --> E["cnt[o.sex]  += 1"]

C --> F["rev  — defaultdict(float)"]
D --> G["pcts — defaultdict(list)"]
E --> H["cnt  — defaultdict(int)"]

F --> I["list of dict: sex, revenue, avg_tip_pct, orders"]
G --> I
H --> I
```

```
Повертає:
  [{"sex": "Male",   "revenue": 3256.61, "avg_tip_pct": 15.8, "orders": 157},
   {"sex": "Female", "revenue": 1571.16, "avg_tip_pct": 16.6, "orders": 87}]
```

---

# 12. top_by_tip_pct() — Редьюсер топ-N

**Задача:** знайти N чеків з найвищим відсотком чайових.

```mermaid
flowchart TD

A["List[RichOrder]"] --> B["sorted key=lambda o: o.tip_pct reverse=True"]

B --> C[відсортований список — найвищий tip% першим]

C --> D["зріз [:n]"]

D --> E["List[RichOrder] — топ N чеків"]
```

```python
def top_by_tip_pct(orders, n=5):
    return sorted(orders, key=lambda o: o.tip_pct, reverse=True)[:n]
```

```
sorted() + зріз → Leader Algorithm для N кращих
```

---

# 13. run_pipeline() — Головний Pipeline

**Задача:** один виклик → повна аналітика для будь-якої комбінації фільтрів.
Оркеструє всі функції у правильному порядку.

```mermaid
flowchart TD

START["run_pipeline(days, times, smoker, sexes, size_range, bill_range)"]

START --> S1

subgraph S1["STEP 1 — FILTER"]
  F1["apply_filters(ALL_ORDERS, ...)"]
  F1 --> F2["List[Order] — N чеків"]
end

S1 --> S2

subgraph S2["STEP 2 — MAP / TRANSFORM"]
  T1["enrich_all(filtered)"]
  T1 --> T2["List[RichOrder] — N чеків"]
end

S2 --> S3

subgraph S3["STEP 3 — REDUCE"]
  R1["calc_kpis(enriched)    → dict"]
  R2["group_by_day(enriched) → list"]
  R3["group_by_time(enriched)→ list"]
  R4["group_by_size(enriched)→ list"]
  R5["group_by_sex(enriched) → list"]
  R6["top_by_tip_pct(enriched, n=5) → list"]
end

S3 --> RESULT["return dict з усіма результатами"]
```

```python
def run_pipeline(days, times, smoker, size_range, bill_range, sexes) -> dict:
    filtered = apply_filters(ALL_ORDERS, days, times, smoker, size_range, bill_range, sexes)
    enriched = enrich_all(filtered)
    return {
        "count":    len(enriched),
        "enriched": enriched,
        "kpis":     calc_kpis(enriched),
        "by_day":   group_by_day(enriched),
        "by_time":  group_by_time(enriched),
        "by_size":  group_by_size(enriched),
        "by_sex":   group_by_sex(enriched),
        "top_tips": top_by_tip_pct(enriched, n=5),
    }
```

```
Закон pipeline:
  вихід однієї функції = вхід наступної
  apply_filters → List[Order] → enrich_all → List[RichOrder] → редьюсери
```

---

# 14. Dash Callback — UI як обгортка навколо pipeline

**Задача:** при зміні будь-якого фільтра у sidebar перерахувати все і оновити UI.

```mermaid
flowchart TD

UI["Sidebar UI"]
UI --> I1["f-day    Checklist"]
UI --> I2["f-time   Checklist"]
UI --> I3["f-smoker Checklist"]
UI --> I4["f-sex    Checklist"]
UI --> I5["f-size   RangeSlider"]
UI --> I6["f-bill   RangeSlider"]

I1 --> CB["@app.callback  update()"]
I2 --> CB
I3 --> CB
I4 --> CB
I5 --> CB
I6 --> CB

CB --> PL["run_pipeline(days, times, smoker, sexes, size_range, bill_range)"]

PL --> O1["kpis → kpi-revenue, kpi-tips, kpi-avg, kpi-pct"]
PL --> O2["by_day   → ch-day   Figure"]
PL --> O3["by_time  → ch-time  Figure"]
PL --> O4["enriched → ch-scatter Figure"]
PL --> O5["by_size  → ch-size  Figure"]
PL --> O6["enriched → ch-dist  Figure"]
PL --> O7["by_sex   → ch-sex   Figure"]
PL --> O8["top_tips → top-table"]
PL --> O9["enriched → orders-table"]
```

```
Dash callback = обгортка навколо run_pipeline()
Кожна зміна фільтра → callback → pipeline → 14 Output-оновлень
```

---

# 15. Повний потік даних

Від сирих даних до кожного елемента UI.

```mermaid
flowchart TD

RAW[seaborn tips CSV] --> DF[DataFrame 244 x 7]
DF --> LOAD["load_orders()"]
LOAD --> ALL["ALL_ORDERS: List[Order] — 244 чеки у пам'яті"]

ALL --> FILT["apply_filters() — Predicates AND-ланцюг"]
FILT --> FLIST["filtered: List[Order] — N чеків"]

FLIST --> ENRICH["enrich_all() — Map"]
ENRICH --> ELIST["enriched: List[RichOrder] — N чеків"]

ELIST --> KPI["calc_kpis()"]
ELIST --> DAY["group_by_day()"]
ELIST --> TIME["group_by_time()"]
ELIST --> SIZE["group_by_size()"]
ELIST --> SEX["group_by_sex()"]
ELIST --> TOP["top_by_tip_pct()"]

KPI  --> UI1["4 KPI картки"]
DAY  --> UI2["Bar: виручка по днях"]
TIME --> UI3["Bar: Lunch vs Dinner"]
ELIST --> UI4["Scatter: рахунок vs чайові"]
SIZE --> UI5["Bar: розмір столу + colorbar"]
ELIST --> UI6["Histogram: розподіл Tip%"]
SEX  --> UI7["Pie: стать клієнтів"]
TOP  --> UI8["Таблиця топ-5 Tip%"]
ELIST --> UI9["Таблиця всіх чеків"]
```

---

# 16. Типи функцій у app.py

| Функція | Тип | Вхід | Вихід |
|---|---|---|---|
| `load_orders` | Трансформер | DataFrame | `List[Order]` |
| `pred_day` | Предикат | `Order`, `list[str]` | `bool` |
| `pred_time` | Предикат | `Order`, `list[str]` | `bool` |
| `pred_smoker` | Предикат | `Order`, `list[str]` | `bool` |
| `pred_sex` | Предикат | `Order`, `list[str]` | `bool` |
| `pred_size` | Предикат | `Order`, `int`, `int` | `bool` |
| `pred_bill` | Предикат | `Order`, `float`, `float` | `bool` |
| `apply_filters` | Комбінований фільтр | `List[Order]` + 6 параметрів | `List[Order]` |
| `enrich_order` | Трансформер | `Order` | `RichOrder` |
| `enrich_all` | Map | `List[Order]` | `List[RichOrder]` |
| `calc_kpis` | Редьюсер | `List[RichOrder]` | `dict` |
| `group_by_day` | Редьюсер | `List[RichOrder]` | `list[dict]` |
| `group_by_time` | Редьюсер | `List[RichOrder]` | `list[dict]` |
| `group_by_size` | Редьюсер | `List[RichOrder]` | `list[dict]` |
| `group_by_sex` | Редьюсер | `List[RichOrder]` | `list[dict]` |
| `top_by_tip_pct` | Редьюсер | `List[RichOrder]`, `int` | `List[RichOrder]` |
| `run_pipeline` | Оркестратор | 6 параметрів фільтрів | `dict` з усім |
| `update` | Dash callback | 6 Input | 14 Output |

---

# 17. Порівняння: Урок 7 vs Урок 8

```mermaid
graph LR

A[Урок 7] --> A1[for order in orders]
A --> A2[if order.day == day]
A --> A3[rev += order.total_bill]
A --> A4[cnt += 1]
A --> A5[Один великий блок]

B[Урок 8] --> B1["apply_filters()  — Предикати"]
B --> B2["enrich_all()     — Трансформер"]
B --> B3["calc_kpis()      — Редьюсер"]
B --> B4["run_pipeline()   — Оркестратор"]
B --> B5[Маленькі чисті функції]

A5 -.->|рефакторинг| B5
```

| | Урок 7 | Урок 8 |
|---|---|---|
| Код | Один великий for-блок | Маленькі функції |
| Зміна фільтра | Переписати весь цикл | Змінити параметр |
| Тестування | Важко — все разом | Кожна функція окремо |
| UI | Неможливо підключити | `run_pipeline()` → Dash callback |
| Читабельність | `rev += bill` | `calc_kpis(enriched)` |

---

# Головна ідея уроку

```
Чиста функція  = лише параметри → лише return, завжди той самий результат
Предикат       = (Order) → bool, фейсконтроль для кожного чека
Трансформер    = (Order) → RichOrder, форма змінюється, кількість — ні
Редьюсер       = List[RichOrder] → dict, багато → одне
Pipeline       = Filter → Map → Reduce
Dash callback  = UI-обгортка навколо pipeline
```

Три рядки, які пояснюють весь дашборд:

```python
filtered = apply_filters(ALL_ORDERS, days, times, ...)   # Predicate
enriched = enrich_all(filtered)                          # Transformer
kpis     = calc_kpis(enriched)                           # Reducer
```

```
сирі дані → предикати (хто входить?) → трансформер (яка форма?)
         → редьюсери (яка відповідь?) → UI (що показати?)
```
