# Індекси PostgreSQL — Глибока механіка

> Індекси існують щоб запобігти читанню кожного рядка на диску.
> Цей документ пояснює ЧОМУ індекси такі ефективні (B-Tree, GIN),
> коли їх додавати, коли не додавати, і як перевіряти ефективність через EXPLAIN ANALYZE.

---

> 🔬 **Побачити EXPLAIN ANALYZE у дії:**
> [`notes_project/hello_app/orm_laboratory.ipynb`](notes_project/hello_app/orm_laboratory.ipynb)
>
> | Концепція | Розділ ноутбука |
> |-----------|-----------------|
> | `queryset.explain(analyze=True)` — Index Scan vs Seq Scan | `## 11. 🔬 SQL Inspection` |
> | `.query` — перегляд згенерованого SQL | `## 11. 🔬 SQL Inspection` |
> | `connection.queries` — всі SQL запити сесії | `## 11. 🔬 SQL Inspection` |
> | N+1 → індекси вирішують частину проблеми | `## 8. ⚡ N+1 Problem` |



> **🧠 Ментальна модель:** База даних БЕЗ індексу — як бібліотека без каталогу. Щоб знайти книгу "Django ORM" — потрібно переглянути кожну полицю по порядку. З індексом — підходиш до картотеки, знаходиш "Django ORM" → "стелаж 7, ряд 3, місце 42". Секунди замість годин.
>
> **📚 Чому індекси не "безкоштовні":** Індекс = окрема структура даних на диску. При кожному INSERT/UPDATE/DELETE → PostgreSQL оновлює і таблицю, і всі індекси на ній. 10 індексів на таблиці = кожен запис обходиться в 11 операцій запису (1 таблиця + 10 індексів). Занадто багато індексів → повільні записи.
>
> **🌐 Як PostgreSQL обирає використовувати індекс:** Query Planner рахує cost: sequential scan (читати всю таблицю) vs index scan (B-Tree traversal + heap fetch). Якщо SELECT повертає >5-10% рядків таблиці → sequential scan може бути дешевшим! Planner знає статистику таблиці і обирає оптимальний план.
>
> **❌ Типова помилка початківця:** "Додам індекс на кожне поле — буде швидше". Насправді зайвий індекс: уповільнює INSERT/UPDATE/DELETE, займає місце на диску, і може не використовуватись Planner-ом якщо умова не вибіркова. Індекси — стратегічне рішення, не "завжди більше = краще".

---

## 1. Sequential Scan vs Index Scan — фізика

---
> **🧠 Ментальна модель:** Sequential Scan = читати книгу з першої сторінки до останньої щоб знайти один абзац. Index Scan = спочатку дивишся на зміст → знаходиш номер сторінки → відкриваєш одразу. Різниця: O(N) vs O(log N).
>
> **📚 Фізичний рівень:** Таблиця PostgreSQL зберігається у "сторінках" по 8KB. Sequential Scan = читати всі сторінки підряд. 1 мільйон рядків × 8KB/10rows = ~800MB прочитати. З індексом: B-Tree traversal (3-4 диск-I/O) → отримати heap tuple pointer → 1 читання heap. Всього: 4-5 I/O операцій замість мільйона.
>
> **🌐 Коли Planner обирає Sequential Scan замість індексу:** Якщо WHERE clause повертає >10-15% рядків — sequential scan буде ефективнішим (один прохід по диску vs багато випадкових I/O через індекс). Planner враховує це.
>
> **❌ Типова помилка:** Додати індекс і дивуватись що він не використовується. `WHERE status = 'published'` на таблиці де 80% рядків = 'published' → Planner правильно обирає Sequential Scan. Індекс корисний коли умова **вибіркова** (повертає малий % рядків).
---

```
Sequential Scan (O(N)):
Таблиця notes_note: 1,000,000 рядків

Диск: [ Page 1 ][ Page 2 ][ Page 3 ] ... [ Page 100,000 ]
          ↑──────────────────────────────────────────────────
          Читаємо ВСЕ щоб знайти WHERE user_id=5

Операцій: 100,000 читань сторінок (800MB!)
Час: ~500ms - 2s залежно від диску та кешу
```

```
Index Scan (O(log N)):
B-Tree індекс на user_id:

                    [Root: 500]
                   /            \
          [250]                    [750]
         /     \                  /     \
    [125]      [375]          [625]      [875]
     / \        / \            / \        / \
  [100][150] [300][400]    [600][650] [800][900]
   ↑
   Leaf: [5] → pointer to heap page 42, slot 7

Операцій: log₂(1,000,000) ≈ 20 порівнянь → 3-4 disk I/O
Час: ~0.05ms - 1ms
```

---

## 2. B-Tree Index — внутрішня структура

---
> **🧠 Ментальна модель:** B-Tree (Balanced Tree) — це впорядкована деревоподібна структура де пошук, вставка і видалення — O(log N). "Balanced" означає: всі листки на однаковій глибині. Для таблиці з 1 мільярдом рядків глибина B-Tree ≈ log₂(1,000,000,000) ≈ 30 рівнів. 30 порівнянь замість мільярда!
>
> **📚 Як B-Tree зберігається на диску:** Кожен вузол = одна сторінка (8KB). Кожна сторінка вміщає ~200-400 записів. Root → Branch nodes → Leaf nodes. Leaf nodes: зберігають значення + TID (tuple identifier = pointer на heap сторінку + offset). Sequential reads по leaf nodes = ефективна range scan.
>
> **🌐 B-Tree для Django:** `db_index=True`, `unique=True`, стандартний `models.Index(fields=[...])` — всі створюють B-Tree. Ефективний для: `=`, `>`, `<`, `>=`, `<=`, `BETWEEN`, `ORDER BY`, `LIKE 'prefix%'`. НЕ ефективний для: `LIKE '%suffix'`, `LOWER()`, `UPPER()` (якщо немає functional index).
>
> **❌ Типова помилка:** `LIKE '%python%'` і очікувати що індекс спрацює. B-Tree індекс не може шукати "містить підрядок" ефективно (тільки "починається з"). Для `icontains` → потрібен trigram індекс (GIN з pg_trgm).
---

```
B-Tree структура для index on notes_note(user_id):

                        ┌──────────────┐
                        │  Root Node   │
                        │   [250,500]  │
                        └──────────────┘
                        /       │       \
              ┌────────┐   ┌────────┐   ┌────────┐
              │ Branch │   │ Branch │   │ Branch │
              │ [5,50] │   │[251,350]│  │[501,750]│
              └────────┘   └────────┘   └────────┘
              /       \         ...         ...
      ┌──────┐   ┌──────┐
      │ Leaf │ ↔ │ Leaf │   ← листки ДВОЗВ'ЯЗНО з'єднані!
      │ [1,2,│   │[6,7, │   (ефективно для range scan: ORDER BY)
      │  3,4]│   │ 8,9] │
      │  TIDs│   │ TIDs │   TID = (page_number, slot_number) → pointer в heap
      └──────┘   └──────┘

Пошук user_id=5:
  Root: 5 < 250 → іди ліво
  Branch: 5 ≤ 50 → іди до першого листка
  Leaf: знаходимо 5 → TID = (42, 7)
  Heap: читаємо page 42, slot 7 → повертаємо рядок

Всього: 3-4 I/O операцій для мільярда рядків.
```

---

## 3. Composite Index — "leading column" правило

---
> **🧠 Ментальна модель:** Composite index (складений) — це як телефонна книга відсортована по **прізвищу, потім імені**. Шукати по прізвищу "Шевченко" → ефективно. Шукати по імені "Тарас" → доведеться читати всю книгу (прізвище не вказане → невідомо де шукати).
>
> **📚 Leading column правило:** Composite index `(A, B, C)` ефективний для: `WHERE A=`, `WHERE A= AND B=`, `WHERE A= AND B= AND C=`, `ORDER BY A, B`. НЕ ефективний для: `WHERE B=` (A не вказано), `WHERE C=` (A і B не вказані). Завжди починай з найселективнішого або найчастіше використовуваного поля.
>
> **🌐 Як це в Django:** `models.Index(fields=['user', '-updated_at'])` → `CREATE INDEX ON notes_note (user_id, updated_at DESC)`. Ефективно для `filter(user=X).order_by('-updated_at')` — типовий запит для списку нотаток.
>
> **❌ Типова помилка:** Покладатись на composite index де leading column не використовується. `Index(fields=['status', 'user'])` → `WHERE user=5` без `WHERE status=` → індекс НЕ використовується (не leading column!). Потрібен окремий `Index(fields=['user'])`.
---

```python
class Note(models.Model):
    user = models.ForeignKey(User, ...)
    status = models.CharField(max_length=20, ...)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            # ✅ Індекс для типового запиту: нотатки юзера, відсортовані по даті
            # Ефективний для: filter(user=X).order_by('-updated_at')
            models.Index(
                fields=['user', '-updated_at'],
                name='note_user_updated_idx'
            ),

            # ✅ Для: filter(user=X, status='published')
            models.Index(
                fields=['user', 'status'],
                name='note_user_status_idx'
            ),

            # ✅ Для аналітики: топ по переглядах
            models.Index(
                fields=['-views_count'],
                name='note_views_desc_idx'
            ),
        ]
```

```
Таблиця використання composite index (user_id, updated_at):

Запит                                    | Індекс?
─────────────────────────────────────────┼─────────
filter(user=X).order_by('-updated_at')   | ✅ Так
filter(user=X)                           | ✅ Так (leading column)
filter(user=X, status='pub')             | ✅ Частково (тільки user_id частина)
filter(status='pub').order_by('-updated_at') | ❌ Ні (status не є leading!)
order_by('-updated_at')                  | ❌ Ні (user_id не вказано)
```

---

## 4. Covering Index — Index-Only Scan

---
> **🧠 Ментальна модель:** Покриваючий індекс — це каталог де є не тільки номер "стелажу" але й сама інформація. Замість: каталог → "стелаж 42, місце 7" → йти до стелажу → читати книгу. Тепер: каталог → вже є вся потрібна інформація → нікуди не йти.
>
> **📚 Index-Only Scan:** Якщо всі поля у SELECT і WHERE є в індексі — PostgreSQL читає тільки індекс, без heap (основних даних таблиці). Це `Index Only Scan` в EXPLAIN — дуже ефективно для агрегацій та аналітики.
>
> **🌐 `include` parameter в Django:** `Index(fields=['user', 'status'], include=['title', 'updated_at'])` → PostgreSQL INCLUDE синтаксис. Поля в `include` є в листках індексу але не є ключем сортування. SELECT title, updated_at WHERE user=X AND status='pub' → Index Only Scan.
>
> **❌ Типова помилка:** Покривати занадто багато полів. Широкий covering index займає більше місця і уповільнює записи. Покривай тільки поля що ТОЧНО потрібні для конкретного "гарячого" запиту.
---

```python
# Covering index: включаємо поля що часто SELECTуються але не в WHERE
class Note(models.Model):
    class Meta:
        indexes = [
            # index (user_id, status) INCLUDE (title, updated_at)
            # SELECT title, updated_at WHERE user_id=X AND status='published'
            # → Index Only Scan (не читає heap!)
            models.Index(
                fields=['user', 'status'],
                include=['title', 'updated_at'],  # PostgreSQL 11+ синтаксис
                name='note_user_status_cover_idx'
            ),
        ]
```

```sql
-- EXPLAIN ANALYZE покаже різницю:

-- БЕЗ covering index:
Seq Scan / Index Scan on notes_note
  + Heap Fetch (reading data pages)
  → 2 I/O операції: індекс + heap

-- З covering index:
Index Only Scan using note_user_status_cover_idx
  → 1 I/O операція: тільки індекс
  (heap ще відвідується для "visibility check" але набагато рідше)
```

---

## 5. GIN Index — для JSON та масивів

---
> **🧠 Ментальна модель:** B-Tree ефективний для порівняння одного значення з іншим (`user_id = 5`). GIN (Generalized Inverted Index) ефективний для "містить" (`tags @> ['python']`, `metadata ? 'word_count'`). GIN — це як індекс у кінці книги: "python → сторінки 5, 42, 100". Один запис в індексі може вказувати на ТИСЯЧІ рядків.
>
> **📚 Як GIN працює:** GIN розбирає кожне значення на "елементи" (ключі JSON, елементи масиву, слова тексту) і для кожного елементу зберігає список TID (pointer на рядки що містять цей елемент). Пошук `WHERE tags @> ['python']` → знайти 'python' в GIN → отримати список TID → повернути рядки.
>
> **🌐 GIN в Django:** `GinIndex(fields=['tags'])` для ArrayField, `GinIndex(fields=['metadata'])` для JSONField. Для повнотекстового пошуку: `GinIndex(fields=['content'], opclasses=['gin_trgm_ops'])` потребує розширення `pg_trgm`.
>
> **❌ Типова помилка:** Не додавати GIN індекс для JSONField і фільтрувати по JSON полях. `Note.objects.filter(metadata__language='uk')` без GIN → sequential scan на мільярдах рядків. З GIN → millісекунди.
---

```python
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

class Note(models.Model):
    tags = models.ManyToManyField(Tag, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    quick_labels = ArrayField(
        models.CharField(max_length=50), blank=True, default=list
    )

    class Meta:
        indexes = [
            # GIN для ArrayField — пошук по елементах масиву
            GinIndex(
                fields=['quick_labels'],
                name='note_labels_gin_idx'
            ),
            # GIN для JSONField — пошук по JSON ключах та значеннях
            GinIndex(
                fields=['metadata'],
                name='note_metadata_gin_idx'
            ),
        ]

# Ефективні запити з GIN індексом:
Note.objects.filter(quick_labels__contains=['python'])
# WHERE quick_labels @> ARRAY['python']  → GIN O(log N)

Note.objects.filter(metadata__language='uk')
# WHERE metadata @> '{"language": "uk"}'  → GIN O(log N)

Note.objects.filter(metadata__has_key='word_count')
# WHERE metadata ? 'word_count'  → GIN O(log N)
```

---

## 6. Trigram Index — fuzzy пошук

---
> **🧠 Ментальна модель:** Trigram — розбивка тексту на групи по 3 символи. "Django" → ["Dja", "jan", "ang", "ngo"]. Trigram GIN індекс зберігає кожен trigram → список рядків що його містять. `LIKE '%django%'` → знайти всі рядки де є трайграми "dja", "jan", "ang", "ngo" → перетин списків → результат. Без trigram: sequential scan.
>
> **📚 Підключення pg_trgm:** `CREATE EXTENSION IF NOT EXISTS pg_trgm;` — або через Django міграцію: `BtreeGinExtension()` або `TrigramExtension()`.
>
> **🌐 icontains з trigram:** `Note.objects.filter(title__icontains='python')` без trigram → `LIKE '%python%'` → sequential scan. З trigram GIN → O(log N) пошук по трайграмах.
>
> **❌ Типова помилка:** Очікувати що `db_index=True` + `icontains` = швидкий пошук. Звичайний B-Tree НЕ допомагає для `%contains%`. Тільки trigram GIN.
---

```python
# Спочатку потрібно активувати розширення pg_trgm:

# migrations/0010_trigram_extension.py
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):
    operations = [
        TrigramExtension(),  # CREATE EXTENSION pg_trgm
    ]


# Потім додаємо trigram індекс:
from django.contrib.postgres.indexes import GinIndex

class Note(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)

    class Meta:
        indexes = [
            # GIN trigram для title — швидкий LIKE '%...%'
            GinIndex(
                fields=['title'],
                opclasses=['gin_trgm_ops'],  # trigram operator class
                name='note_title_trgm_idx'
            ),
            # GIN trigram для content (великий текст — корисно)
            GinIndex(
                fields=['content'],
                opclasses=['gin_trgm_ops'],
                name='note_content_trgm_idx'
            ),
        ]

# Тепер ці запити використовуватимуть trigram GIN:
Note.objects.filter(title__icontains='python')
# WHERE title ILIKE '%python%' → trigram GIN O(log N)

Note.objects.filter(
    Q(title__icontains='django') | Q(content__icontains='django')
)
```

---

## 7. AddIndexConcurrently — без downtime на production

---
> **🧠 Ментальна модель:** Звичайний `CREATE INDEX` блокує таблицю на весь час побудови індексу. На таблиці з 50 мільйонами рядків — це 10-30 хвилин без можливості вставляти або оновлювати дані. `CREATE INDEX CONCURRENTLY` будує індекс не блокуючи таблицю — за рахунок двох проходів та трохи повільнішого побудови.
>
> **📚 Як CONCURRENT працює:** Два скани таблиці: перший збирає snapshot, другий вловлює зміни що відбулись під час першого. Між сканами — таблиця залишається доступною для читання і запису. Час побудови: трохи довший. Блокування: мінімальне (тільки кілька Share Update Exclusive Lock на мілісекунди).
>
> **🌐 В Django:** `migrations.AddIndexConcurrently` (в `django.contrib.postgres.operations`). Потрібен `atomic = False` у міграції (CONCURRENT не може бути в транзакції).
>
> **❌ Типова помилка:** Додавати великий індекс через звичайний `migrations.AddIndex` на production таблиці з мільйонами рядків. 10-30 хвилин downtime. Завжди використовуй `AddIndexConcurrently` на production.
---

```python
# hello_app/migrations/0015_add_concurrent_index.py
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    # ОБОВ'ЯЗКОВО: atomic=False — CONCURRENT не можна в транзакції!
    atomic = False

    dependencies = [
        ('hello_app', '0014_previous_migration'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='note',
            index=models.Index(
                fields=['user', '-updated_at'],
                name='note_user_updated_concurrent_idx'
            ),
        ),
    ]

# SQL що виконується:
# CREATE INDEX CONCURRENTLY note_user_updated_concurrent_idx
# ON hello_app_note (user_id, updated_at DESC)
# (без блокування таблиці!)
```

---

## 8. Коли додавати індекс (і коли ні)

```
✅ ДОДАВАТИ ІНДЕКС:

  1. Поля в WHERE clause (фільтрація)
     filter(user=X) → індекс на user_id

  2. Поля в ORDER BY (сортування без sort операції)
     order_by('-updated_at') → індекс на updated_at DESC

  3. Foreign Key поля
     Django автоматично НЕ додає індекс на FK в деяких версіях.
     Явно: db_index=True або в Meta.indexes

  4. Поля у JOIN умовах
     JOIN ... ON note.user_id = user.id → індекс на user_id

  5. Поля у UNIQUE обмеженнях
     Django автоматично додає при unique=True

  6. JSON/Array поля що фільтруються
     GinIndex(fields=['metadata'])

❌ НЕ ДОДАВАТИ ІНДЕКС:

  1. Поля з низькою вибірковістю
     Boolean (тільки 2 значення)
     Status з 2-3 значеннями де 80% = одне значення
     Planner обере Sequential Scan (правильно!)

  2. Маленькі таблиці (< 1000 рядків)
     Sequential Scan ефективніший (все в кеші)

  3. Поля що рідко використовуються у WHERE/ORDER BY
     Тільки займає місце і уповільнює записи

  4. Поля що дуже часто оновлюються
     UPDATE → переписати індекс → overhead

  5. "Про всяк випадок" поля
     Кожен зайвий індекс = уповільнення INSERT/UPDATE/DELETE
```

---

## 9. REINDEX та обслуговування індексів

```sql
-- Перевірити розмір індексів
SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Bloat: скільки мертвих записів у індексі (після масових DELETE/UPDATE)
-- PostgreSQL VACUUM прибирає їх автоматично

-- REINDEX CONCURRENTLY (PostgreSQL 12+): відновити індекс без блокування
REINDEX INDEX CONCURRENTLY note_user_updated_idx;

-- Або через Django:
# python manage.py shell
# from django.db import connection
# connection.cursor().execute('REINDEX INDEX CONCURRENTLY note_user_updated_idx')
```

---

## Prediction Exercises

### Exercise 1: Вибірковість

```python
class Order(models.Model):
    status = models.CharField(max_length=20)  # 'pending', 'completed', 'cancelled'
    # Розподіл: 5% pending, 90% completed, 5% cancelled
```

**Питання:** Чи варто додавати `db_index=True` на `status`?

> Відповідь: **Залежить від запиту.** `filter(status='pending')` → 5% рядків → індекс корисний. `filter(status='completed')` → 90% рядків → Planner правильно обере Sequential Scan. Рішення: часткові індекси або залишити без індексу.

### Exercise 2: Composite index

```python
Index(fields=['user', 'status', 'updated_at'])
```

**Питання:** Для яких WHERE умов цей індекс буде ефективним?

> Відповідь: `filter(user=X)`, `filter(user=X, status='pub')`, `filter(user=X, status='pub', updated_at__gte=date)`. НЕ для: `filter(status='pub')`, `filter(updated_at__gte=date)`, `filter(status='pub', updated_at__gte=date)` — немає leading column `user`.

---

## Питання для самоперевірки

1. Що таке Sequential Scan і коли він краще Index Scan?
2. Як виглядає B-Tree і яка його асимптотична складність пошуку?
3. Що таке "leading column" у composite index і чому це важливо?
4. Коли потрібен GIN індекс а не B-Tree?
5. Чому `LIKE '%text%'` не використовує B-Tree індекс?
6. Що таке trigram і як він дозволяє ефективний fuzzy пошук?
7. Чим `AddIndexConcurrently` відрізняється від `AddIndex` і коли використовувати?
8. Як переглянути що конкретний запит використовує індекс?
9. Навіщо `include` у `models.Index` і що таке Index-Only Scan?
10. Чому занадто багато індексів уповільнює систему?
