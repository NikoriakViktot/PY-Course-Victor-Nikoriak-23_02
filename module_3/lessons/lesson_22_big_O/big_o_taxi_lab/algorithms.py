"""
algorithms.py — Реалізації Big-O алгоритмів для Taxi Big-O Lab.

Кожна функція є чистою Python-функцією (без Streamlit, без I/O).
Повертає (result_value, op_count: int) — для автоматичного витягу
лічильника операцій у metrics.time_measure().

Розділи
-------
1. O(n)      — linear_scan + альтернативні реалізації
2. O(1)      — hash_index (build + lookup) + альтернативи
3. O(log n)  — binary_search + ручна ітеративна
4. O(n²)     — nested_loop + while-версія + оптимізація через set
5. Pandas / DuckDB допоміжні функції
6. Dataclass-и для метаданих (Implementation, AntiPattern, GoodPattern, MemoryInfo)
7. AlgoMeta  — розширений клас метаданих
8. ALGO_META — реєстр усіх алгоритмів з повним навчальним контентом
9. Оцінка памʼяті
"""
from __future__ import annotations

import bisect
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

import duckdb
import pandas as pd

# ---------------------------------------------------------------------------
# 0. Загальні псевдоніми типів
# ---------------------------------------------------------------------------

PaymentIndex = dict[str, list[int]]
SortedDistances = list[float]


# ===========================================================================
# 1. O(n) — Лінійний пошук (кілька реалізацій)
# ===========================================================================

def linear_scan(df: pd.DataFrame, target: str = "Cash") -> tuple[int, int]:
    """O(n): for loop — базова реалізація. Відвідує кожен елемент рівно раз."""
    count: int = 0
    ops: int = 0
    payment_col: list[str] = df["payment_type"].tolist()
    for val in payment_col:
        ops += 1
        if val == target:
            count += 1
    return count, ops


def linear_scan_while(df: pd.DataFrame, target: str = "Cash") -> tuple[int, int]:
    """O(n): while loop — аналогічно for, але явний індекс."""
    values = df["payment_type"].tolist()
    count, ops, i = 0, 0, 0
    while i < len(values):
        ops += 1
        if values[i] == target:
            count += 1
        i += 1
    return count, ops


def linear_scan_comprehension(df: pd.DataFrame, target: str = "Cash") -> tuple[int, int]:
    """O(n): list comprehension — синтаксичний цукор, все одно O(n) і витрачає O(n) памʼяті."""
    result = [1 for val in df["payment_type"] if val == target]
    return sum(result), len(df)


def linear_scan_generator(df: pd.DataFrame, target: str = "Cash") -> tuple[int, int]:
    """O(n): generator — O(1) додаткова памʼять (ліниво генерує значення)."""
    gen = (1 for val in df["payment_type"] if val == target)
    return sum(gen), len(df)


# ===========================================================================
# 2. O(1) — Хеш-таблиця (build + lookup + альтернативи)
# ===========================================================================

def build_hash_index(df: pd.DataFrame) -> tuple[PaymentIndex, int]:
    """O(n): будує dict payment_type → [row_indices]. Одноразова O(n) вартість."""
    index: PaymentIndex = {}
    ops: int = 0
    for i, val in enumerate(df["payment_type"].tolist()):
        ops += 1
        if val not in index:
            index[val] = []
        index[val].append(i)
    return index, ops


def build_hash_index_defaultdict(df: pd.DataFrame) -> tuple[PaymentIndex, int]:
    """O(n): те саме через defaultdict — чистіший код, та сама складність."""
    index: defaultdict[str, list[int]] = defaultdict(list)
    ops = 0
    for i, val in enumerate(df["payment_type"].tolist()):
        ops += 1
        index[val].append(i)
    return dict(index), ops


def build_hash_counter(df: pd.DataFrame) -> tuple[Counter, int]:
    """O(n): Counter — вбудований підрахунок частот. Найчистіша реалізація."""
    return Counter(df["payment_type"].tolist()), len(df)


def hash_index_lookup(index: PaymentIndex, key: str = "Cash") -> tuple[int, int]:
    """O(1): dict.get() — hash(key) → слот → значення. Завжди 1 операція."""
    result = index.get(key, [])
    return len(result), 1


def hash_set_membership(df: pd.DataFrame, target: str = "Cash") -> tuple[bool, int]:
    """O(1) lookup: set для перевірки наявності елемента."""
    unique: set[str] = set(df["payment_type"].unique())
    return (target in unique), 1


# ===========================================================================
# 3. O(log n) — Бінарний пошук (3 реалізації)
# ===========================================================================

def prepare_sorted_distances(df: pd.DataFrame) -> tuple[SortedDistances, int]:
    """O(n log n): сортує trip_distance. Одноразовий підготовчий крок."""
    distances = df["trip_distance"].tolist()
    distances.sort()   # Timsort: O(n log n)
    return distances, len(distances)


def binary_search(
    sorted_distances: SortedDistances,
    threshold: float = 3.0,
) -> tuple[int, int]:
    """O(log n): bisect_right — stdlib C-рівень. Підраховує елементи > threshold."""
    n = len(sorted_distances)
    if n == 0:
        return 0, 0
    idx = bisect.bisect_right(sorted_distances, threshold)
    count = n - idx
    max_steps = max(1, math.ceil(math.log2(n))) if n > 1 else 1
    return count, max_steps


def binary_search_manual(
    sorted_list: list[float],
    target: float,
) -> tuple[int, int]:
    """O(log n): ручна ітеративна реалізація — показує кожен крок явно."""
    left, right = 0, len(sorted_list) - 1
    steps = 0
    while left <= right:
        steps += 1
        mid = (left + right) // 2
        if sorted_list[mid] == target:
            return mid, steps
        elif sorted_list[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1, steps


# ===========================================================================
# 4. O(n²) — Вкладені цикли (for, while, оптимізована через set)
# ===========================================================================

MAX_N_QUADRATIC = 3_000   # Жорстке обмеження — поза ним O(n²) не використовується


def nested_loop(df: pd.DataFrame, max_n: int = MAX_N_QUADRATIC) -> tuple[int, int]:
    """O(n²): подвійний for loop — n × n порівнянь."""
    actual_n = min(len(df), max_n)
    pickup  = df["PULocationID"].tolist()[:actual_n]
    dropoff = df["DOLocationID"].tolist()[:actual_n]
    match_count, ops = 0, 0
    for i in range(actual_n):
        for j in range(actual_n):
            ops += 1
            if i != j and pickup[i] == dropoff[j]:
                match_count += 1
    return match_count, ops


def nested_loop_while(df: pd.DataFrame, max_n: int = MAX_N_QUADRATIC) -> tuple[int, int]:
    """O(n²): подвійний while loop — та сама складність, явний контроль індексів."""
    actual_n = min(len(df), max_n)
    pickup  = df["PULocationID"].tolist()[:actual_n]
    dropoff = df["DOLocationID"].tolist()[:actual_n]
    match_count, ops = 0, 0
    i = 0
    while i < actual_n:
        j = 0
        while j < actual_n:
            ops += 1
            if i != j and pickup[i] == dropoff[j]:
                match_count += 1
            j += 1
        i += 1
    return match_count, ops


def nested_optimized_set(df: pd.DataFrame, max_n: int = MAX_N_QUADRATIC) -> tuple[int, int]:
    """O(n): та сама задача, але через set — демонструє як усунути O(n²)."""
    actual_n = min(len(df), max_n)
    pickup  = df["PULocationID"].tolist()[:actual_n]
    dropoff = df["DOLocationID"].tolist()[:actual_n]
    dropoff_set = set(dropoff)           # O(n) — одна побудова hash-таблиці
    ops = actual_n                       # вартість побудови set
    matches = 0
    for pu in pickup:                    # O(n) — один прохід
        ops += 1
        if pu in dropoff_set:            # O(1) — хеш-пошук!
            matches += 1
    return matches, ops                  # Разом: O(n) + O(n) = O(n) !!!


# ===========================================================================
# 5. Pandas / DuckDB допоміжні функції
# ===========================================================================

def pandas_filter_count(df: pd.DataFrame, target: str = "Cash") -> tuple[int, int]:
    """O(n) векторизовано: NumPy boolean mask в C — без Python interpreter overhead."""
    count = int((df["payment_type"] == target).sum())
    return count, len(df)


def duckdb_sql_count(df: pd.DataFrame, target: str = "Cash") -> tuple[int, int]:
    """O(n) SQL-колонково: DuckDB компілює SQL у векторизований машинний код (AVX2)."""
    con = duckdb.connect(database=":memory:")
    con.register("trips", df)
    count = con.execute(
        f"SELECT COUNT(*) FROM trips WHERE payment_type = '{target}'"
    ).fetchone()[0]
    con.close()
    return int(count), len(df)


# ===========================================================================
# 6. Dataclass-и для навчальних метаданих
# ===========================================================================

@dataclass
class Implementation:
    """Одна конкретна реалізація алгоритму (для вкладки 🔬 Реалізації)."""
    name: str            # "for loop", "while loop", "generator"...
    code: str            # Python код для відображення
    description: str     # Пояснення українською
    complexity: str      # "O(n)", "O(1)"...
    is_recommended: bool = True


@dataclass
class AntiPattern:
    """❌ Антипатерн — як НЕ треба писати код."""
    title: str
    bad_code: str        # поганий код
    why_bad: str         # чому погано — пояснення українською
    fix_code: str        # виправлений код
    why_good: str        # чому краще — пояснення українською


@dataclass
class GoodPattern:
    """✅ Правильний патерн."""
    title: str
    code: str
    description: str     # пояснення українською
    complexity: str


@dataclass
class MemoryInfo:
    """💾 Інформація про використання памʼяті."""
    formula: str                    # "Memory(n) = n × 96 байт"
    breakdown: dict[str, int]       # {компонент: байт/елемент}
    explanation: str                # пояснення українською


# ===========================================================================
# 7. AlgoMeta — розширений клас (backward compatible)
# ===========================================================================

@dataclass
class AlgoMeta:
    """Метадані одного алгоритму для відображення в UI."""
    # --- Існуючі поля (backward compatible з app.py) ---
    key: str
    label: str
    notation: str
    color: str
    badge: str
    short_desc: str
    long_desc: str
    safe_max_n: int
    # --- Нові навчальні поля ---
    formula: str = ""                  # математична формула T(n)=...
    formula_explanation: str = ""      # чому саме така формула (Ukrainian)
    operation_formula: str = "n"       # "n", "n**2", "log2(n)" — для таблиці
    implementations: list[Implementation] = field(default_factory=list)
    anti_patterns: list[AntiPattern] = field(default_factory=list)
    good_patterns: list[GoodPattern] = field(default_factory=list)
    memory_info: Optional[MemoryInfo] = None
    internals_explanation: str = ""    # що відбувається під капотом Python


# ===========================================================================
# 8. ALGO_META — реєстр алгоритмів з повним навчальним контентом
# ===========================================================================

ALGO_META: dict[str, AlgoMeta] = {

    # -----------------------------------------------------------------------
    # O(n) — Лінійний пошук
    # -----------------------------------------------------------------------
    "linear": AlgoMeta(
        key="linear",
        label="O(n) — Linear Scan",
        notation="O(n)",
        color="#f59e0b",
        badge="🟡",
        short_desc="Перевіряє кожен рядок по черзі. Час зростає пропорційно до n.",
        long_desc=(
            "**Лінійний пошук** проходить по всіх n записах один раз. "
            "Подвоїти n → подвоїти кількість порівнянь. "
            "Python `for` loop відвідує кожен елемент — скорочення немає. "
            "Це базовий клас складності — все що швидше за O(n) вважається «ефективним»."
        ),
        safe_max_n=500_000,

        formula="T(n) = c · n",
        formula_explanation=(
            "Алгоритм виконує **рівно n порівнянь** — по одному на кожен елемент.\n\n"
            "- n = 100 → 100 операцій\n"
            "- n = 1,000 → 1,000 операцій\n"
            "- n = 10,000 → 10,000 операцій\n\n"
            "Залежність **лінійна**: графік T(n) — пряма лінія через нуль.\n"
            "Константа **c** визначається типом порівняння, CPU-кешем та "
            "Python interpreter overhead (~50 нс на ітерацію).\n\n"
            "**Big-O відкидає c** → залишається O(n).\n"
            "Тому O(n) охоплює і «1 прохід», і «3 проходи» (3n → O(n))."
        ),
        operation_formula="n",

        implementations=[
            Implementation(
                name="for loop (рекомендовано)",
                code="""\
def linear_scan_for(df, target="Cash"):
    count, ops = 0, 0
    for val in df["payment_type"].tolist():
        ops += 1          # ← одна операція на елемент
        if val == target:
            count += 1
    return count, ops
# n=10,000  →  10,000 операцій
# n=100,000 → 100,000 операцій  (×10)""",
                description=(
                    "Класичний for loop. Python оптимізований для ітерації по спискам — "
                    "читає вказівники послідовно з памʼяті (cache-friendly). "
                    "Найчитабельніший варіант O(n)."
                ),
                complexity="O(n)",
            ),
            Implementation(
                name="while loop",
                code="""\
def linear_scan_while(df, target="Cash"):
    values = df["payment_type"].tolist()
    count, ops, i = 0, 0, 0
    while i < len(values):
        ops += 1
        if values[i] == target:
            count += 1
        i += 1
    return count, ops
# Та сама складність O(n), але потрібен явний лічильник i""",
                description=(
                    "while loop еквівалентний for за складністю O(n), але вимагає "
                    "явного управління індексом. Корисний коли потрібно змінювати i "
                    "всередині циклу (пропуск елементів, крок ≠ 1)."
                ),
                complexity="O(n)",
            ),
            Implementation(
                name="list comprehension",
                code="""\
def linear_scan_comprehension(df, target="Cash"):
    # Будує новий список [1, 0, 1, 1, ...] у памʼяті!
    result = [1 for val in df["payment_type"] if val == target]
    return sum(result), len(df)
# O(n) час, O(n) памʼять — витрачає RAM на проміжний список""",
                description=(
                    "List comprehension — синтаксичний цукор над for loop. "
                    "Час O(n), але будує **проміжний список у памʼяті** → O(n) RAM. "
                    "Для великих n краще використовувати generator."
                ),
                complexity="O(n)",
                is_recommended=False,
            ),
            Implementation(
                name="generator (оптимально по памʼяті)",
                code="""\
def linear_scan_generator(df, target="Cash"):
    # generator НЕ будує список — ліниво генерує по одному значенню
    gen = (1 for val in df["payment_type"] if val == target)
    return sum(gen), len(df)
# O(n) час, O(1) памʼять — ідеально для великих n!""",
                description=(
                    "Generator expression — лінива обробка: в памʼяті одночасно "
                    "тільки **один елемент**. Час O(n) як і for loop, але памʼять O(1). "
                    "Найкращий вибір для великих наборів даних."
                ),
                complexity="O(n)",
            ),
        ],

        anti_patterns=[
            AntiPattern(
                title='`item in list` всередині циклу → прихована O(n²) бомба',
                bad_code="""\
# ❌ АНТИПАТЕРН: виглядає як O(n), але насправді O(n × m)!
cash_zones = [1, 5, 12, 33, 97, ...]   # список — O(m) lookup!

for zone in pickup_zones:              # O(n) — зовнішній цикл
    if zone in cash_zones:             # O(m) — list сканує з початку кожного разу!
        result.append(zone)

# n=10,000 і m=10,000 → 100,000,000 порівнянь 💥""",
                why_bad=(
                    "Оператор `in` на **списку** виконує лінійне сканування O(m). "
                    "Всередині зовнішнього циклу O(n) це дає O(n × m). "
                    "При n=m=10,000: 100 мільйонів операцій замість 20,000!"
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: конвертуємо список у set ОДИН РАЗ
cash_set = set(cash_zones)             # O(m) — будуємо hash-таблицю один раз

for zone in pickup_zones:              # O(n)
    if zone in cash_set:               # O(1) — хеш-пошук!
        result.append(zone)

# n=10,000 і m=10,000 → 20,000 операцій (замість 100,000,000) 🚀""",
                why_good=(
                    "Set (`in set`) виконує хеш-пошук за O(1). "
                    "Одноразова вартість побудови set: O(m). "
                    "Загальна складність: O(n + m) замість O(n × m). "
                    "Прискорення: 100,000,000 / 20,000 = **5,000×**."
                ),
            ),
            AntiPattern(
                title="Перезапуск ітерації при умові → O(n²) у гіршому випадку",
                bad_code="""\
# ❌ АНТИПАТЕРН: i = 0 всередині while → перезапуск!
i = 0
while i < len(data):
    if data[i] < 0:
        data[i] = 0
        i = 0        # ← ПОМИЛКА: перезапуск циклу → O(n²)!
    i += 1

# Якщо data = [-1, -1, -1, ..., -1] (всі від'ємні):
# кожен елемент перезапускає цикл → n × n = n² ітерацій""",
                why_bad=(
                    "Перезапуск ітерації (`i = 0`) у гіршому випадку призводить до O(n²). "
                    "Python не оптимізує такі конструкції автоматично — "
                    "це класична помилка початківців."
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: один прохід — завжди O(n)
for i in range(len(data)):
    if data[i] < 0:
        data[i] = 0
# Завжди рівно n ітерацій — незалежно від вмісту даних""",
                why_good=(
                    "Один прохід for loop гарантує рівно n ітерацій — "
                    "незалежно від значень елементів. O(n) без виключень."
                ),
            ),
        ],

        good_patterns=[
            GoodPattern(
                title="for val in iterable",
                code='for val in df["payment_type"]:\n    if val == target: count += 1',
                description="Прямолінійний, cache-friendly, читабельний. Базовий шаблон O(n).",
                complexity="O(n)",
            ),
            GoodPattern(
                title="Generator expression (O(1) памʼять)",
                code='total = sum(1 for val in df["payment_type"] if val == target)',
                description="Ліниво обчислює — в памʼяті одночасно 1 елемент. Ідеально для великих n.",
                complexity="O(n)",
            ),
            GoodPattern(
                title="Pandas vectorized (10-100× швидше)",
                code='count = (df["payment_type"] == target).sum()',
                description=(
                    "NumPy boolean mask у C-коді. Той самий O(n) але без Python interpreter "
                    "overhead — у 10-100× швидше ніж Python for loop."
                ),
                complexity="O(n)",
            ),
        ],

        memory_info=MemoryInfo(
            formula="Memory(n) ≈ n × 154 байт",
            breakdown={
                "DataFrame (4 колонки)": 96,
                "Python list (tolist)": 8,
                "str objects у heap": 50,
            },
            explanation=(
                "**DataFrame** зберігає дані в NumPy-масивах: ~96 байт/рядок.\n\n"
                "**tolist()** створює Python list з n вказівниками: +8 байт/елемент.\n\n"
                "**str об'єкти** ('Cash', 'Card') займають ~50 байт у heap кожен, "
                "але CPython **інтернує** короткі рядки — тобто всі 'Cash' у списку "
                "вказують на **один** об'єкт у памʼяті, не n копій.\n\n"
                "**Для n=100,000:** ~15 MB\n"
                "**Для n=1,000,000:** ~150 MB"
            ),
        ),

        internals_explanation=(
            "### Python list — масив вказівників\n\n"
            "```\n"
            "list = [ptr_0][ptr_1][ptr_2]...[ptr_n-1]  ← масив у C heap\n"
            "         ↓       ↓       ↓\n"
            '       "Cash" "Card" "Cash"               ← str об\'єкти\n'
            "```\n\n"
            "Python list — це **dynamic array** (масив PyObject\\*). "
            "Ітерація читає вказівники послідовно → **cache-friendly** "
            "(процесор prefetch-ує наступні адреси автоматично).\n\n"
            "### Байт-код одної ітерації for loop\n\n"
            "```\n"
            "FOR_ITER    → наступний PyObject* зі списку\n"
            "LOAD_FAST   → target на стек\n"
            "COMPARE_OP  → PyUnicode_RichCompare('Cash', 'Cash')\n"
            "  └─ якщо id(a)==id(b): True миттєво (string interning!)\n"
            "  └─ інакше: довжина → хеш → посимвольне порівняння\n"
            "JUMP_IF_FALSE → пропустити count+=1\n"
            "INPLACE_ADD → count += 1\n"
            "```\n\n"
            "### Чому Python for повільніше pandas\n\n"
            "**Python for:** ~50-100 нс на ітерацію (interpreter overhead)\n\n"
            "**NumPy (pandas):** AVX2 SIMD — порівнює 8 int32 за **одну CPU-інструкцію**. "
            "Без Python interpreter. У 10-100× швидше при тих самих n операціях.\n\n"
            "### String interning (оптимізація CPython)\n\n"
            "Короткі рядки ('Cash', 'Card') CPython **інтернує** — всі однакові рядки "
            "вказують на один об'єкт. Порівняння `id(a)==id(b)` → True миттєво (O(1) "
            "замість посимвольного порівняння)."
        ),
    ),

    # -----------------------------------------------------------------------
    # O(1) — Хеш-таблиця
    # -----------------------------------------------------------------------
    "hash": AlgoMeta(
        key="hash",
        label="O(1) — Hash Index Lookup",
        notation="O(1)",
        color="#10b981",
        badge="🟢",
        short_desc="Попередньо побудований словник. Пошук миттєвий незалежно від n.",
        long_desc=(
            "**Хеш-індекс** відображає кожен payment_type на список індексів рядків. "
            "Побудова індексу: O(n) — один раз. "
            "Кожен наступний пошук: `dict.get(key)` обчислює `hash(key)` і "
            "стрибає прямо в комірку памʼяті — без сканування, без циклу. "
            "Саме тому Python dict/set — найпотужніший інструмент архітектора."
        ),
        safe_max_n=500_000,

        formula="T(n) = c (константа)",
        formula_explanation=(
            "Python dict реалізований як **хеш-таблиця**. При виклику `dict[key]`:\n\n"
            "1. `hash(key)` → 64-бітне хеш-значення (~5 нс)\n"
            "2. `hash % table_size` → індекс слоту (~1 нс)\n"
            "3. Перевірка слоту → значення (1 звернення до памʼяті)\n\n"
            "Ці **3 кроки виконуються незалежно від розміру dict**:\n\n"
            "- dict з 10 елементів → **1 операція**\n"
            "- dict з 10,000 елементів → **1 операція**\n"
            "- dict з 10,000,000 елементів → **1 операція**\n\n"
            "**T(n) = c** — константна функція. Big-O: **O(1)**.\n\n"
            "⚠️ Нюанс: при **collision** (два ключі в одному слоті) "
            "може знадобитися 2-3 проби → O(1) амортизовано."
        ),
        operation_formula="1",

        implementations=[
            Implementation(
                name="dict.get() — базова (рекомендовано)",
                code="""\
# КРОК 1: O(n) — будуємо index ОДИН РАЗ
def build_hash_index(df):
    index = {}
    for i, val in enumerate(df["payment_type"]):
        if val not in index:
            index[val] = []
        index[val].append(i)
    return index

# КРОК 2: O(1) — пошук завжди 1 операція
def hash_index_lookup(index, key="Cash"):
    return len(index.get(key, [])), 1  # ops = 1 ЗАВЖДИ!
    # hash("Cash") → 0x4f73... → slot_12 → [0,3,7,...]""",
                description=(
                    "dict.get(key, default) — безпечний O(1) доступ без KeyError. "
                    "Побудова індексу O(n) виконується **один раз**, потім "
                    "**необмежена кількість O(1) запитів**."
                ),
                complexity="O(1) lookup / O(n) build",
            ),
            Implementation(
                name="defaultdict (чистіший код)",
                code="""\
from collections import defaultdict

def build_with_defaultdict(df):
    index = defaultdict(list)   # автоматично створює [] для нових ключів
    for i, val in enumerate(df["payment_type"]):
        index[val].append(i)    # немає if-перевірки → чистіший код
    return dict(index)

# defaultdict vs dict: та сама O(n) build, O(1) lookup
# Перевага: index["new_key"] не кидає KeyError — повертає []""",
                description=(
                    "defaultdict автоматично ініціалізує відсутні ключі — "
                    "усуває шаблонний if/else код. Та сама O(n) побудова і O(1) lookup."
                ),
                complexity="O(1) lookup / O(n) build",
            ),
            Implementation(
                name="Counter (найчистіше для підрахунку)",
                code="""\
from collections import Counter

def count_with_counter(df):
    counts = Counter(df["payment_type"])  # O(n) — оптимізовано у C
    return counts["Cash"], 1              # O(1) — dict lookup
    # Counter — це dict підклас: Counter({"Cash": 512, "Card": 488})

# Найчистіша реалізація для задачі "підрахунок частот"
# Вбудована в stdlib — без зовнішніх залежностей""",
                description=(
                    "Counter — спеціалізований dict для підрахунку частот. "
                    "O(n) побудова в C-коді, O(1) query. "
                    "Найкращий вибір коли потрібні тільки кількості."
                ),
                complexity="O(1) lookup / O(n) build",
            ),
            Implementation(
                name="set (перевірка членства)",
                code="""\
def check_with_set(df, target="Cash"):
    unique = set(df["payment_type"].unique())  # O(k) де k — унікальні
    return (target in unique), 1               # O(1) — hash membership
    # set = dict без values — лише хеші ключів
    # "Cash" in {"Cash", "Card"} → hash("Cash") → slot → True""",
                description=(
                    "Set для O(1) перевірки наявності елемента. "
                    "set = dict без values → менше RAM. "
                    "Ідеально коли потрібно лише 'чи існує?', без count."
                ),
                complexity="O(1)",
            ),
        ],

        anti_patterns=[
            AntiPattern(
                title="Перебудова індексу при кожному запиті",
                bad_code="""\
# ❌ АНТИПАТЕРН: O(n) при КОЖНОМУ виклику!
def lookup_payment(df, key):
    index = {}                              # будуємо знову!
    for i, val in enumerate(df["payment_type"]):
        index.setdefault(val, []).append(i)
    return len(index.get(key, []))

# 100 запитів → 100 × O(n) = O(100n) замість O(n) + 100×O(1)
# При n=100,000 і 100 запитах: 10,000,000 зайвих операцій""",
                why_bad=(
                    "Кожен виклик будує хеш-таблицю з нуля — O(n) замість O(1). "
                    "Вся перевага хешування втрачена. "
                    "100 запитів = 100 × O(n) = O(n) за результатом але без переваги."
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: будуємо index ОДИН РАЗ, зберігаємо
index = build_hash_index(df)        # O(n) — один раз!

# Потім будь-яка кількість O(1) запитів:
count_cash = hash_index_lookup(index, "Cash")   # O(1)
count_card = hash_index_lookup(index, "Card")   # O(1)
# 100 запитів → O(n) + 100×O(1) = O(n) + O(100) ≈ O(n)""",
                why_good=(
                    "Побудова один раз = O(n). Кожен наступний запит = O(1). "
                    "При k запитах: O(n + k) замість O(n×k). "
                    "Зберігай індекс у змінній або st.session_state."
                ),
            ),
            AntiPattern(
                title="list замість dict/set для lookup",
                bad_code="""\
# ❌ АНТИПАТЕРН: list.index() — O(n), не O(1)!
payment_types = ["Cash", "Card", "Unknown"]
pos = payment_types.index("Cash")   # O(n) — сканує весь список!

# ❌ АНТИПАТЕРН: list.count() — O(n) кожного разу
all_payments = df["payment_type"].tolist()
n_cash = all_payments.count("Cash")   # O(n) при КОЖНОМУ виклику!

# Обидва виглядають як 1 рядок, але виконують n операцій""",
                why_bad=(
                    "`list.index()` і `list.count()` сканують весь список. "
                    "Для 100 запитів: 100 × O(n) = O(100n). "
                    "Виглядає як 1 рядок коду але ховає дорогу операцію."
                ),
                fix_code="""\
# ✅ dict → O(1) lookup
counts = {"Cash": 0, "Card": 0}
for val in df["payment_type"]:
    counts[val] = counts.get(val, 0) + 1
n_cash = counts["Cash"]   # O(1)

# ✅ Counter → ще чистіше
from collections import Counter
counts = Counter(df["payment_type"])   # O(n) build
n_cash = counts["Cash"]               # O(1) lookup, будь-яка кількість разів""",
                why_good=(
                    "Counter будується один раз O(n), "
                    "кожен наступний `counts[key]` — O(1). "
                    "100 запитів: O(n) + 100×O(1) замість 100×O(n)."
                ),
            ),
        ],

        good_patterns=[
            GoodPattern(
                title="dict.get(key, default)",
                code='count = index.get("Cash", [])  # O(1), без KeyError',
                description="Безпечний O(1) доступ. Повертає default якщо ключ відсутній.",
                complexity="O(1)",
            ),
            GoodPattern(
                title="collections.Counter",
                code='counts = Counter(df["payment_type"])  # O(n)\nn = counts["Cash"]              # O(1)',
                description="Вбудований підрахунок частот. O(n) build, O(1) запити.",
                complexity="O(1) lookup",
            ),
            GoodPattern(
                title="set для membership test",
                code='valid = {"Cash", "Card"}\nif payment in valid:  # O(1) — не O(n)!',
                description="set у 30× менше RAM ніж dict (без values). O(1) `in` перевірка.",
                complexity="O(1)",
            ),
        ],

        memory_info=MemoryInfo(
            formula="Memory(n) ≈ n × 240 байт (dict entry overhead)",
            breakdown={
                "DataFrame": 96,
                "dict indices array": 8,
                "dict entries (hash+key+value ptr)": 24,
                "list of indices (values)": 8,
                "Python object overhead": 104,
            },
            explanation=(
                "### dict vs list — порівняння памʼяті\n\n"
                "**list (масив вказівників):**\n"
                "- n × 8 байт (PyObject\\* per element)\n"
                "- Дуже компактний!\n\n"
                "**dict (хеш-таблиця CPython):**\n"
                "- indices array: `2^k` × 1-8 байт (k = ceil(log2(n×1.5)))\n"
                "- entries array: n × 24 байт (hash64 + key_ptr + value_ptr)\n"
                "- Load factor: rehash при > 2/3 заповненні\n"
                "- Разом: ~n × 240 байт (з Python overhead)\n\n"
                "**dict у ~30× важчий ніж list** за тих самих n елементів.\n"
                "Але дає O(1) lookup замість O(n) — класичний trade-off памʼять↔швидкість.\n\n"
                "**set:** аналогічно dict, але без values → ~20% легший."
            ),
        ),

        internals_explanation=(
            "### CPython dict — compact dict (Python 3.6+)\n\n"
            "```\n"
            "┌─────────────────────────────────────────────────────┐\n"
            "│ indices:  [-1, 0, -1, 2, -1, 1, -1, -1]            │\n"
            "│           (масив int8/int16/int32/int64, size=2^k)  │\n"
            "├─────────────────────────────────────────────────────┤\n"
            "│ entries:  [(h0,k0,v0), (h1,k1,v1), (h2,k2,v2)]     │\n"
            "│           (лише реальні елементи, компактно)        │\n"
            "└─────────────────────────────────────────────────────┘\n"
            "```\n\n"
            "### Lookup покроково: `index.get('Cash')`\n\n"
            "```\n"
            "1. h = hash('Cash')           → 0x4f73a2b1... (64-bit int)\n"
            "2. slot = h % len(indices)    → наприклад, 3\n"
            "3. entry_i = indices[3]       → 0 (або -1 = not found)\n"
            "4. entry = entries[0]         → (h0, 'Cash', [0,3,7,...])\n"
            "5. entry.hash==h and entry.key=='Cash'  → True → return value\n"
            "```\n\n"
            "### Collision (зіткнення)\n\n"
            "Якщо два ключі дають однаковий слот:\n"
            "```\n"
            "probe = (5*slot + h + 1) % len(indices)  ← probe sequence\n"
            "```\n"
            "Статистично: при load factor < 2/3 середня кількість проб < 1.5.\n\n"
            "### Rehashing — амортизований O(1)\n\n"
            "При заповненні > 2/3 → розмір таблиці ×4 + rehash всіх елементів.\n"
            "Це O(n) one-time cost. Але трапляється log₄(n) разів → "
            "амортизована вартість O(1) на insert.\n\n"
            "### Чому set → O(1) membership\n\n"
            "set = dict де values = `<dummy>` (NULL). Ідентична структура "
            "→ ідентична O(1) складність. Менший розмір (немає values ptr)."
        ),
    ),

    # -----------------------------------------------------------------------
    # O(log n) — Бінарний пошук
    # -----------------------------------------------------------------------
    "binary": AlgoMeta(
        key="binary",
        label="O(log n) — Binary Search",
        notation="O(log n)",
        color="#3b82f6",
        badge="🔵",
        short_desc="Кожен крок відкидає половину. 1B рядків → ~30 порівнянь.",
        long_desc=(
            "**Бінарний пошук** вимагає відсортованого списку. "
            "На кожному кроці він стрибає до середини і відкидає половину, "
            "яка не може містити відповідь. "
            "Для n=1,000,000 — максимум 20 порівнянь. "
            "Для n=1,000,000,000 — лише 30. "
            "Ми використовуємо Python stdlib `bisect` (реалізований у C)."
        ),
        safe_max_n=500_000,

        formula="T(n) = ⌈log₂(n)⌉",
        formula_explanation=(
            "### Вивід формули\n\n"
            "Кожен крок відкидає **половину** простору пошуку:\n\n"
            "- Після 1-го кроку: n/2 елементів залишилось\n"
            "- Після 2-го кроку: n/4\n"
            "- Після k-го кроку: n/2^k\n\n"
            "Зупиняємось коли залишився 1 елемент:\n"
            "```\n"
            "n / 2^k = 1  →  k = log₂(n)\n"
            "```\n\n"
            "### Порівняння з O(n)\n\n"
            "| n | O(n) кроків | O(log n) кроків |\n"
            "|---|---|---|\n"
            "| 1,000 | 1,000 | **~10** |\n"
            "| 100,000 | 100,000 | **~17** |\n"
            "| 1,000,000 | 1,000,000 | **~20** |\n"
            "| 1,000,000,000 | 1,000,000,000 | **~30** |\n\n"
            "⚠️ **Умова:** список **обовʼязково** має бути відсортований. "
            "Без сортування алгоритм не працює коректно."
        ),
        operation_formula="ceil(log2(n))",

        implementations=[
            Implementation(
                name="bisect (stdlib, рекомендовано)",
                code="""\
import bisect, math

# КРОК 1: O(n log n) — сортуємо ОДИН РАЗ
sorted_d = sorted(df["trip_distance"])   # Timsort

# КРОК 2: O(log n) — бінарний пошук
def binary_search_bisect(sorted_d, threshold=3.0):
    # bisect_right → позиція ПІСЛЯ всіх елементів ≤ threshold
    idx   = bisect.bisect_right(sorted_d, threshold)
    count = len(sorted_d) - idx         # елементів > threshold
    steps = math.ceil(math.log2(len(sorted_d)))
    return count, steps

# n=1,000,000 → max 20 кроків!""",
                description=(
                    "bisect реалізований у C (bisectmodule.c у CPython). "
                    "Без Python interpreter overhead на кожному кроці. "
                    "Найшвидша реалізація O(log n) у Python."
                ),
                complexity="O(log n)",
            ),
            Implementation(
                name="ручна ітеративна (показує логіку)",
                code="""\
def binary_search_manual(sorted_list, target):
    left, right = 0, len(sorted_list) - 1
    steps = 0
    while left <= right:
        steps += 1
        mid = (left + right) // 2    # середина поточного вікна
        if sorted_list[mid] == target:
            return mid, steps        # знайдено!
        elif sorted_list[mid] < target:
            left  = mid + 1          # відкидаємо ліву половину
        else:
            right = mid - 1          # відкидаємо праву половину
    return -1, steps                 # не знайдено

# n=1000: steps ≤ 10 (log₂(1000) ≈ 10)
# n=1000000: steps ≤ 20""",
                description=(
                    "Явна реалізація ітеративного бінарного пошуку. "
                    "Ідеально для розуміння алгоритму. "
                    "Показує кожен крок звуження вікна [left, right]."
                ),
                complexity="O(log n)",
            ),
        ],

        anti_patterns=[
            AntiPattern(
                title="Лінійний пошук на відсортованому списку",
                bad_code="""\
# ❌ АНТИПАТЕРН: ігнорує переваги сортування!
sorted_data = sorted(distances)    # O(n log n) — витратили ресурси...

def count_above_SLOW(sorted_data, threshold):
    count = 0
    for val in sorted_data:        # O(n) — не використовує порядок!
        if val > threshold:
            count += 1
    return count

# Потратили O(n log n) на сортування — і все одно O(n) на пошук!
# Разом: O(n log n + n) ≈ O(n log n) замість O(n log n + log n)""",
                why_bad=(
                    "Після сортування ми ЗНАЄМО що елементи впорядковані. "
                    "Лінійний пошук ігнорує цю інформацію і сканує все. "
                    "Це все одно що шукати слово в словнику, "
                    "читаючи кожну сторінку з початку."
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: bisect використовує порядок → O(log n)
sorted_data = sorted(distances)    # O(n log n) — один раз

def count_above_FAST(sorted_data, threshold):
    idx = bisect.bisect_right(sorted_data, threshold)  # O(log n)!
    return len(sorted_data) - idx
# Разом: O(n log n + log n) ≈ O(n log n) → але пошук у log n разів швидший""",
                why_good=(
                    "bisect_right стрибає до середини і відкидає половини — "
                    "log₂(1,000,000) = 20 порівнянь замість 1,000,000."
                ),
            ),
            AntiPattern(
                title="Сортування перед кожним запитом",
                bad_code="""\
# ❌ АНТИПАТЕРН: O(n log n) при КОЖНОМУ виклику!
def search_each_time(data, threshold):
    sorted_data = sorted(data)                 # O(n log n) знову!
    idx = bisect.bisect_right(sorted_data, threshold)
    return len(sorted_data) - idx

# 100 запитів = 100 × O(n log n) 😱
# При n=100,000 і 100 запитах: ~170,000,000 зайвих операцій""",
                why_bad=(
                    "sorted() при кожному виклику — O(n log n) зайвих операцій. "
                    "При k запитах: O(k × n log n) замість O(n log n + k log n). "
                    "Різниця при k=100, n=100,000: в 5,000× більше роботи."
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: сортуємо ОДИН РАЗ, кешуємо
sorted_data = sorted(data)    # O(n log n) — один раз назавжди

# 100 запитів → 100 × O(log n) = O(100 log n) — майже безкоштовно
for threshold in thresholds:
    idx = bisect.bisect_right(sorted_data, threshold)  # O(log n)""",
                why_good=(
                    "Sort once, search many times. "
                    "O(n log n) + k × O(log n) vs k × O(n log n). "
                    "Зберігай відсортований список у змінній або st.session_state."
                ),
            ),
        ],

        good_patterns=[
            GoodPattern(
                title="bisect.bisect_right / bisect_left",
                code="idx = bisect.bisect_right(sorted_list, threshold)",
                description="C-рівень реалізація. Найшвидший O(log n) пошук у Python. Для range queries.",
                complexity="O(log n)",
            ),
            GoodPattern(
                title="Sort once, search many",
                code="sorted_d = sorted(data)  # O(n log n) раз\nfor t in thresholds:\n    bisect.bisect_right(sorted_d, t)  # O(log n) кожен",
                description="Одноразове сортування + множинні бінарні пошуки — класичний шаблон.",
                complexity="O(n log n + k·log n)",
            ),
        ],

        memory_info=MemoryInfo(
            formula="Memory(n) = n × 8 байт (sorted list float64)",
            breakdown={
                "DataFrame": 96,
                "sorted list (float64 ptr)": 8,
                "float objects у heap": 24,
            },
            explanation=(
                "**sorted list** у Python — масив PyObject\\* на float об'єкти: "
                "8 байт/елемент (вказівник) + 24 байт/float об'єкт у heap.\n\n"
                "**NumPy array (якби використовували):** 8 байт/float64 без overhead — "
                "у 4× компактніше ніж Python list of floats.\n\n"
                "**Порівняння з dict:** sorted list у ~30× легший ніж dict з тими ж ключами. "
                "Але дає O(log n) замість O(1). Trade-off: памʼять↔швидкість lookup."
            ),
        ),

        internals_explanation=(
            "### bisect — C-реалізація у CPython\n\n"
            "bisect модуль (`Lib/bisect.py` + `Modules/_bisectmodule.c`) — "
            "ітеративний while loop у C:\n\n"
            "```c\n"
            "// Спрощено (bisectmodule.c)\n"
            "while (lo < hi) {\n"
            "    mid = ((size_t)lo + hi) / 2;\n"
            "    if (cmp(list[mid], item) < 0)\n"
            "        lo = mid + 1;\n"
            "    else\n"
            "        hi = mid;\n"
            "}\n"
            "return lo;\n"
            "```\n\n"
            "Без Python interpreter overhead на кожному кроці → дуже швидко.\n\n"
            "### Python list → O(1) random access\n\n"
            "```\n"
            "list = [ptr_0, ptr_1, ..., ptr_n]  ← C-масив у пам'яті\n"
            "list[mid] = *(array + mid * sizeof(PyObject*))  ← O(1)!\n"
            "```\n\n"
            "Random access за індексом — O(1) через пряму адресацію пам'яті. "
            "Це критично для бінарного пошуку: `sorted_list[mid]` → миттєво.\n\n"
            "### Тайм-схема бінарного пошуку (n=1,000,000)\n\n"
            "```\n"
            "Крок 1: вікно [0, 1,000,000] → перевіряємо [500,000]\n"
            "Крок 2: вікно [500,001, 1,000,000] → перевіряємо [750,000]\n"
            "Крок 3: вікно [500,001, 750,000] → перевіряємо [625,000]\n"
            "...20 кроків пізніше → знайдено!\n"
            "```\n\n"
            "### Чому не dict для range queries\n\n"
            "dict дає O(1) для **точного** пошуку (`key == value`). "
            "Але для **range query** (`value > threshold`) dict потребує "
            "перебору всіх ключів → O(n). Відсортований список + bisect → O(log n)."
        ),
    ),

    # -----------------------------------------------------------------------
    # O(n²) — Вкладені цикли
    # -----------------------------------------------------------------------
    "quadratic": AlgoMeta(
        key="quadratic",
        label="O(n²) — Nested Loops",
        notation="O(n²)",
        color="#ef4444",
        badge="🔴",
        short_desc="Кожен рядок порівнюється з кожним. n×10 → час×100!",
        long_desc=(
            "**Вкладені цикли** — найпоширеніший антипатерн продуктивності. "
            "Зовнішній цикл: n ітерацій. Внутрішній: n ітерацій кожного разу. "
            "Разом: n² ітерацій. "
            "n=1,000 → 1,000,000 ops. n=3,000 → 9,000,000 ops. "
            "Перетворення внутрішнього списку на set (O(1) lookup) — "
            "найпоширеніша оптимізація в кодовій базі."
        ),
        safe_max_n=MAX_N_QUADRATIC,

        formula="T(n) = n × n = n²",
        formula_explanation=(
            "### Вивід формули\n\n"
            "Зовнішній цикл виконується **n разів**.\n"
            "Для **кожної** ітерації зовнішнього → внутрішній виконується **n разів**.\n\n"
            "```\n"
            "T(n) = n (зовнішній) × n (внутрішній) = n²\n"
            "```\n\n"
            "### Зростання n² — квадратична парабола\n\n"
            "| n | операцій | відносно n=10 |\n"
            "|---|---|---|\n"
            "| 10 | 100 | 1× |\n"
            "| 100 | 10,000 | **100×** |\n"
            "| 1,000 | 1,000,000 | **10,000×** |\n"
            "| 10,000 | 100,000,000 | **1,000,000×** |\n\n"
            "**n × 10 → час × 100.** Це квадратична залежність — парабола вгору.\n\n"
            "### Чому O(n²) катастрофічно на великих даних\n\n"
            "n=100,000 → 10¹⁰ операцій → при 1 ГГц (~10⁹ ops/сек) → **10 секунд**.\n"
            "n=1,000,000 → 10¹² операцій → **~16 хвилин**. Неприйнятно для production.\n\n"
            "**Рішення:** замінити внутрішній цикл на O(1) lookup (set/dict) → O(n) total."
        ),
        operation_formula="n**2",

        implementations=[
            Implementation(
                name="for/for (базова, показує O(n²))",
                code="""\
def nested_loop(df, max_n=3000):
    actual_n = min(len(df), max_n)   # ← ОБОВ'ЯЗКОВИЙ CAP!
    pickup  = df["PULocationID"].tolist()[:actual_n]
    dropoff = df["DOLocationID"].tolist()[:actual_n]
    matches, ops = 0, 0

    for i in range(actual_n):        # ← зовнішній: n ітерацій
        for j in range(actual_n):    # ← внутрішній: n ітерацій КОЖЕН РАЗ
            ops += 1                 #   разом: n × n = n² !
            if i != j and pickup[i] == dropoff[j]:
                matches += 1

    return matches, ops

# n=500  →     250,000 операцій
# n=1000 →   1,000,000 операцій  (×4 при n×2)
# n=3000 →   9,000,000 операцій  (×36 при n×6)""",
                description=(
                    "Класичний O(n²) — подвійний for loop. "
                    "Обовʼязковий cap max_n=3000 запобігає зависанню UI. "
                    "Корисний лише для демонстрації проблеми."
                ),
                complexity="O(n²)",
                is_recommended=False,
            ),
            Implementation(
                name="while/while (явний контроль індексів)",
                code="""\
def nested_loop_while(df, max_n=3000):
    actual_n = min(len(df), max_n)
    pickup  = df["PULocationID"].tolist()[:actual_n]
    dropoff = df["DOLocationID"].tolist()[:actual_n]
    matches, ops = 0, 0
    i = 0
    while i < actual_n:
        j = 0
        while j < actual_n:
            ops += 1
            if i != j and pickup[i] == dropoff[j]:
                matches += 1
            j += 1
        i += 1
    return matches, ops
# Та сама O(n²) складність — while vs for не змінює Big-O""",
                description=(
                    "while/while — явний контроль i, j. "
                    "Корисний коли потрібно нестандартне оновлення індексів "
                    "(наприклад, j = i+1 для унікальних пар). "
                    "O(n²) та сама."
                ),
                complexity="O(n²)",
                is_recommended=False,
            ),
            Implementation(
                name="✅ Оптимізація через set — O(n) замість O(n²)!",
                code="""\
def nested_optimized_set(df, max_n=3000):
    actual_n = min(len(df), max_n)
    pickup  = df["PULocationID"].tolist()[:actual_n]
    dropoff = df["DOLocationID"].tolist()[:actual_n]

    # O(n) — будуємо хеш-таблицю ОДИН РАЗ
    dropoff_set = set(dropoff)
    ops = actual_n

    # O(n) — один прохід з O(1) lookup всередині
    matches = 0
    for pu in pickup:
        ops += 1
        if pu in dropoff_set:   # O(1) — хеш-пошук!
            matches += 1

    return matches, ops
# n=3000 → 6,000 операцій замість 9,000,000 → у 1,500× швидше!""",
                description=(
                    "Замінюємо внутрішній O(n) цикл на O(1) set lookup. "
                    "Загальна складність: O(n) + O(n) = O(n). "
                    "При n=3000: 6,000 ops замість 9,000,000 → **1,500× швидше**!"
                ),
                complexity="O(n)",
            ),
        ],

        anti_patterns=[
            AntiPattern(
                title="Подвійний цикл для перевірки дублікатів",
                bad_code="""\
# ❌ АНТИПАТЕРН: O(n²) для пошуку дублікатів
def has_duplicate_SLOW(data):
    n = len(data)
    for i in range(n):              # O(n)
        for j in range(i + 1, n):  # O(n) для кожного i → O(n²)
            if data[i] == data[j]:
                return True
    return False

# n=10,000 → ~50,000,000 порівнянь 💥
# n=100,000 → ~5,000,000,000 порівнянь 💥💥""",
                why_bad=(
                    "Кожен елемент порівнюється з усіма наступними: n×(n-1)/2 ≈ n²/2 операцій. "
                    "При n=10,000: 50 мільйонів порівнянь — катастрофа."
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: O(n) через set
def has_duplicate_FAST(data):
    seen = set()                   # хеш-таблиця: O(1) per op
    for item in data:              # O(n) — один прохід
        if item in seen:           # O(1) — хеш-пошук
            return True
        seen.add(item)             # O(1) — вставка
    return False

# n=10,000 → 10,000 операцій замість 50,000,000 → 5,000× швидше!""",
                why_good=(
                    "Один прохід: O(n). set lookup: O(1). "
                    "Загалом O(n) — незалежно від того чи є дублікат на початку чи в кінці."
                ),
            ),
            AntiPattern(
                title="list.index() всередині циклу",
                bad_code="""\
# ❌ АНТИПАТЕРН: list.index() — O(n) всередині O(n) циклу
zones = df["DOLocationID"].tolist()  # список
targets = df["PULocationID"].tolist()

positions = []
for target in targets:              # O(n)
    try:
        pos = zones.index(target)   # O(n) — сканує весь zones!
        positions.append(pos)
    except ValueError:
        pass
# Разом: O(n × n) = O(n²)""",
                why_bad=(
                    "list.index() завжди сканує список з початку до знаходження — O(n). "
                    "Всередині зовнішнього O(n) циклу → O(n²). "
                    "Виглядає як 1 виклик функції але ховає O(n) операцій."
                ),
                fix_code="""\
# ✅ ВИПРАВЛЕННЯ: побудувати index dict ОДИН РАЗ
zones = df["DOLocationID"].tolist()
targets = df["PULocationID"].tolist()

# O(n) — один раз
zone_index = {val: i for i, val in enumerate(zones)}

# O(n) — один прохід з O(1) lookup
positions = [zone_index[t] for t in targets if t in zone_index]
# Разом: O(n) замість O(n²)""",
                why_good=(
                    "dict comprehension будує індекс за O(n). "
                    "Кожен dict lookup — O(1). "
                    "n lookups = O(n). Total: O(n) + O(n) = O(n)."
                ),
            ),
        ],

        good_patterns=[
            GoodPattern(
                title="set для O(1) lookup всередині циклу",
                code="inner_set = set(inner_list)  # O(n)\nfor item in outer:           # O(n)\n    if item in inner_set:    # O(1)!",
                description="Перетворення внутрішнього списку в set — найпоширеніша O(n²)→O(n) оптимізація.",
                complexity="O(n)",
            ),
            GoodPattern(
                title="dict comprehension для індексу",
                code="index = {v: i for i, v in enumerate(data)}  # O(n)\npos = index.get(target, -1)                # O(1)",
                description="Замість list.index() всередині циклу — O(n²) → O(n).",
                complexity="O(n)",
            ),
            GoodPattern(
                title="pandas merge/join замість nested loops",
                code="result = df1.merge(df2, left_on='PU', right_on='DO')  # O(n log n)",
                description="SQL-style join — O(n log n) на великих DataFrame замість O(n²) Python loops.",
                complexity="O(n log n)",
            ),
        ],

        memory_info=MemoryInfo(
            formula="Memory(n) = O(1) — лише лічильники і змінні циклу",
            breakdown={
                "DataFrame": 96,
                "pickup list": 8,
                "dropoff list": 8,
                "match_count, ops, i, j": 4,
            },
            explanation=(
                "O(n²) витрачає **O(1) додаткової памʼяті** — лише цілочисельні "
                "лічильники та ітераційні змінні.\n\n"
                "**Парадокс:** O(n²) за часом, але O(1) за памʼяттю! "
                "Це «просторово-ефективний» алгоритм — просто катастрофічно повільний.\n\n"
                "**Оптимізована версія через set:** додаткові O(n) байт "
                "(для set dropoff_set) — але час O(n) замість O(n²).\n\n"
                "Класичний trade-off: **час ↔ памʼять**."
            ),
        ),

        internals_explanation=(
            "### Чому O(n²) такий повільний у Python\n\n"
            "Python не компілює вкладені цикли. Кожна ітерація:\n\n"
            "```\n"
            "FOR_ITER (outer)    → ~10 байт-кодових інструкцій\n"
            "  FOR_ITER (inner)  → ~10 байт-кодових інструкцій\n"
            "    COMPARE_OP      → PyObject_RichCompare → ~5 нс\n"
            "    INPLACE_ADD     → ops += 1 → ~3 нс\n"
            "```\n\n"
            "n=3,000: **9,000,000 ітерацій** × ~20 нс = **~180 мс** у Python.\n"
            "Той самий алгоритм у C або NumPy: ~2 мс (SIMD, без interpreter).\n\n"
            "### Dynamic array — чому list[i] O(1)\n\n"
            "```\n"
            "pickup = [ptr_0, ptr_1, ..., ptr_n]  ← C-масив\n"
            "pickup[i] = *(base_addr + i * 8)     ← O(1) адресна арифметика\n"
            "```\n\n"
            "Random access за індексом — O(1). Тому `pickup[i]` і `dropoff[j]` "
            "миттєві — вузьке місце не доступ до памʼяті, а **кількість ітерацій**.\n\n"
            "### Чому set вирішує проблему\n\n"
            "```\n"
            "# Замість O(n) внутрішнього циклу:\n"
            "for j in range(n):              # n ітерацій кожного разу\n"
            "    if pickup[i] == dropoff[j]: # O(n) загалом\n\n"
            "# set lookup:\n"
            "if pickup[i] in dropoff_set:    # hash → slot → O(1)!\n"
            "```\n\n"
            "Замінюємо **n порівнянь** на **1 хеш-операцію**. "
            "n разів O(n) → n разів O(1) = O(n) total.\n\n"
            "### Append під час O(n²) — append() O(1) амортизовано\n\n"
            "```\n"
            "list.append(x):\n"
            "  - Якщо є місце (len < capacity): O(1) — просто записуємо\n"
            "  - Якщо capacity вичерпана: resize! (×2 поточного розміру)\n"
            "    → копіюємо всі елементи: O(n) one-time\n"
            "  - Амортизовано за n append(): O(1) per append\n"
            "```\n\n"
            "Послідовність розмірів при resize: 0→4→8→16→25→35→46→58→72→88→106..."
        ),
    ),
}

ALL_ALGO_LABELS: list[str] = [m.label for m in ALGO_META.values()]


# ===========================================================================
# 9. Оцінка памʼяті
# ===========================================================================

_DF_BYTES_PER_ROW: int = 96


def estimate_algo_memory_gb(algo_key: str, n: int) -> float:
    """Груба оцінка RAM (у GB) для запуску algo_key на n рядках."""
    df_gb = n * _DF_BYTES_PER_ROW / (1_024 ** 3)
    extra_bytes_per_row: dict[str, int] = {
        "linear":    0,
        "hash":      100,
        "binary":    8,
        "quadratic": 0,
    }
    extra_gb = n * extra_bytes_per_row.get(algo_key, 0) / (1_024 ** 3)
    return df_gb + extra_gb


def estimate_memory_bytes(algo_key: str, n: int) -> dict[str, int]:
    """Детальна оцінка памʼяті з розбивкою по компонентах."""
    df_mem = n * _DF_BYTES_PER_ROW
    breakdowns: dict[str, dict[str, int]] = {
        "linear": {
            "DataFrame (4 колонки)": df_mem,
            "Python list (tolist)": n * 8,
            "Лічильники (count, ops)": 32,
        },
        "hash": {
            "DataFrame (4 колонки)": df_mem,
            "dict indices array": max(64, n * 8),
            "dict entries (hash+key+val)": n * 24,
            "list of indices (values)": n * 8,
        },
        "binary": {
            "DataFrame (4 колонки)": df_mem,
            "sorted list (ptr array)": n * 8,
            "float objects у heap": n * 24,
        },
        "quadratic": {
            "DataFrame (4 колонки)": df_mem,
            "pickup list": n * 8,
            "dropoff list": n * 8,
            "Лічильники (match, ops, i, j)": 64,
        },
    }
    return breakdowns.get(algo_key, {"DataFrame": df_mem})
