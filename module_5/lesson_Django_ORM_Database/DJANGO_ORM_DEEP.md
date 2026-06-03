# Django ORM — глибока механіка

> Цей файл пояснює **як Django ORM працює зсередини**.
> Не просто "використовуй `.filter()`" — а ЧОМУ це lazy, як це транслюється в SQL,
> чому N+1 — катастрофа і як F() рятує від race condition.

---

> 🔬 **Інтерактивна лабораторія:** [`notes_project/hello_app/orm_laboratory.ipynb`](notes_project/hello_app/orm_laboratory.ipynb)
>
> Виконай клітинки у ноутбуку і побач SQL живцем для кожної концепції:
>
> | Секція цього файлу | Розділ ноутбука |
> |-------------------|-----------------|
> | Django ORM Object Model | `## 0. 🧱 Що таке object в Django ORM?` |
> | Lazy Evaluation / QuerySet AST | `## 1. 🧠 ORM Mental Model` |
> | `all()`, `filter()`, `exclude()`, `get()` | `## 2. 🔍 Lazy Methods` |
> | Field lookups (`__icontains`, `__gte`, `__in`) | `## 3. 🔎 Field Lookups` |
> | Relationship traversal via `__` | `## 4. 🔗 Relationship Traversal` |
> | `Q()` objects — OR / AND / NOT | `## 5. 🎯 Q() Objects` |
> | `F()` expressions — порівняння полів | `## 6. 📐 F() Expressions` |
> | `annotate()` / `aggregate()` / `values()` | `## 7. 📊 Aggregation & Annotation` |
> | N+1 Problem → `select_related` / `prefetch_related` | `## 8. ⚡ N+1 Problem & Optimization` |
> | `Exists()` subquery | `## 8.1 🔎 Exists() Subquery` |
> | `only()` / `defer()` | `## 9. 🎛️ only() і defer()` |
> | Custom Managers & QuerySets | `## 10. 🏗️ Custom Managers` |
> | SQL Inspection (`.query`, `explain(analyze=True)`) | `## 11. 🔬 SQL Inspection` |
> | `DoesNotExist`, `MultipleObjectsReturned`, `distinct()` | `## 12. 💥 Edge Cases` |
> | `transaction.atomic()` | `## 13. 🔒 Транзакції` |
> | Raw SQL / `cursor.execute()` | `## 14. 🧪 Raw SQL` |
> | `bulk_create()` / `bulk_update()` | `## 15. 📋 Bulk операції` |
> | QuerySet Lifecycle (фінальний огляд) | `## 16. 🗂️ QuerySet Lifecycle` |



> **🧠 Ментальна модель:** Django ORM — це **перекладач**. Він перекладає Python-вирази (`Note.objects.filter(status='published')`) у SQL (`SELECT * FROM notes_note WHERE status='published'`). Але, на відміну від простого перекладача — він **розумний**: він не виконує переклад поки не потрібно (Lazy Evaluation), він кешує результат (QuerySet cache), він може об'єднати кілька операцій в один SQL-запит.
>
> **📚 Чому ORM а не сирий SQL:** Без ORM: ти пишеш SQL вручну, вставляєш значення через f-string (SQL injection!), вручну маппиш рядки на Python-об'єкти, вручну обробляєш різницю між SQLite і PostgreSQL. ORM вирішує всі ці проблеми. `Note.objects.filter(user=request.user)` — автоматично захищений від injection, працює однаково на SQLite і PostgreSQL.
>
> **🌐 Як Django обробляє запит:** `Note.objects.filter(...)` → створює `QuerySet` об'єкт → при виконанні `SQLCompiler.as_sql()` → генерує SQL → передає в `DatabaseWrapper` (psycopg2 для PostgreSQL) → отримує рядки → `ModelIterable` перетворює на Python об'єкти.
>
> **❌ Типова помилка початківця:** Думати що `qs = Note.objects.filter(status='published')` — це вже запит до БД. **Ні.** Це тільки опис запиту. SQL виконається пізніше — при `list(qs)`, `for note in qs`, `qs[0]`, `len(qs)` або `qs.count()`.

---

## 1. Models та Managers

---
> **🧠 Ментальна модель:** `Model` — це **клас = таблиця + інтерфейс**. Кожен атрибут-поле (`CharField`, `IntegerField`) описує один стовпець. Кожен екземпляр класу — це один рядок у таблиці. `Manager` — це шлюз між Python та базою даних.
>
> **📚 Чому `objects` це Manager:** `Note.objects` — це `Manager` об'єкт. Він надає доступ до всіх QuerySet методів. `objects.all()`, `objects.filter(...)`, `objects.create(...)` — це методи Manager. Ти можеш написати **Custom Manager** з власною логікою: `Note.published.all()` → автоматично фільтрує `status='published'`.
>
> **🌐 Як Manager генерує SQL:** `Note.objects.filter(status='published')` → `Manager.__get__` → `QuerySet.__init__` → зберігає фільтр → при виконанні `SQLCompiler` перетворює на `WHERE status = 'published'`.
>
> **❌ Типова помилка:** Не використовувати Custom Manager для повторюваних фільтрів. Якщо ти скрізь пишеш `Note.objects.filter(status='published', is_deleted=False)` — зроби `Note.published.all()`. Один раз описав логіку → використовуєш всюди.
---

```python
# Базова модель з усіма типами Manager

class PublishedNoteManager(models.Manager):
    """Custom Manager — повертає тільки опубліковані нотатки."""
    def get_queryset(self):
        # Базовий QuerySet із фільтром
        return super().get_queryset().filter(
            status='published',
            is_deleted=False
        )
    
    def recent(self):
        """Опубліковані, відсортовані по даті (зручний shortcut)."""
        return self.get_queryset().order_by('-created_at')[:10]


class Note(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Чернетка'),
        (STATUS_PUBLISHED, 'Опубліковано'),
        (STATUS_ARCHIVED, 'Архів'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Два Manager-а:
    objects = models.Manager()         # стандартний: Note.objects.all()
    published = PublishedNoteManager() # custom: Note.published.all()

# Використання:
Note.objects.all()           # всі нотатки (будь-який статус)
Note.published.all()         # тільки status='published' AND is_deleted=False
Note.published.recent()      # останні 10 опублікованих
```

---

## 2. QuerySets та Lazy Evaluation

---
> **🧠 Ментальна модель:** QuerySet — це як **рецепт страви**, а не сама страва. Рецепт описує що приготувати, але не готує поки не попросиш. Можна модифікувати рецепт (додати спеції = додати `.filter()`) скільки завгодно — реальна робота починається тільки коли подаєш страву на стіл (= ітеруєш або перетворюєш на список).
>
> **📚 Чому Lazy (ліниве) обчислення:** Ти можеш будувати складний QuerySet поступово: додавати фільтри, сортування, анотації — і в кінці це все транслюється в **один ефективний SQL-запит**. Якщо б SQL виконувався при кожному `.filter()` — це була б катастрофа: десятки запитів замість одного.
>
> **🌐 Що тригерить виконання SQL:** `list()`, `len()`, `bool()`, ітерація в `for`, зріз `qs[0]`, `qs.first()`, `qs.count()`, серіалізація (`json.dumps(list(qs))`).
>
> **❌ Типова помилка:** Двічі ітерувати один і той самий QuerySet в циклі. Перша ітерація — виконує SQL і **кешує результат** в `qs._result_cache`. Друга ітерація — використовує кеш, **нового SQL немає**. Але якщо між ітераціями дані змінились у БД — ти бачиш старі дані.
---

### Тригери виконання SQL

```
QuerySet Life Cycle:

      qs = Note.objects.filter(status='published')
                │
                │  ← ЦЕ ТІЛЬКИ PYTHON ОБ'ЄКТ, ЖОДНОГО SQL
                │
      qs = qs.select_related('user')
                │
                │  ← ЩЕ НІЧОГО НЕ СТАЛОСЬ
                │
      qs = qs.order_by('-created_at')
                │
                │  ← ДОСІ НІЧОГО
                ▼
    ┌──────────────────────────────────────────────────────────┐
    │  ТРИГЕРИ виконання SQL (qs._result_cache заповнюється)   │
    │                                                          │
    │  for note in qs: ...        ← ітерація                  │
    │  list(qs)                   ← явне перетворення          │
    │  note = qs[0]               ← перший елемент             │
    │  note = qs.first()          ← LIMIT 1                   │
    │  count = qs.count()         ← COUNT(*) (без кешу!)      │
    │  if qs: ...                 ← bool() перевірка          │
    │  len(qs)                    ← виконує і кешує           │
    └──────────────────────────────────────────────────────────┘
```

```python
# Демонстрація лінивості

# Крок 1: Будуємо QuerySet — НІЧОГО не виконується в БД
qs = Note.objects.filter(status='published')
qs = qs.select_related('user', 'category')
qs = qs.order_by('-created_at')
qs = qs.filter(views_count__gte=10)

# Крок 2: Тільки тут Django генерує і виконує SQL
notes = list(qs)  # ← ТРИГЕР

# Весь QuerySet транслюється в ОДИН SQL:
# SELECT notes_note.*, auth_user.*, notes_category.*
# FROM notes_note
# LEFT JOIN auth_user ON notes_note.user_id = auth_user.id
# LEFT JOIN notes_category ON notes_note.category_id = notes_category.id
# WHERE status = 'published' AND views_count >= 10
# ORDER BY created_at DESC

# Перегляд генерованого SQL — завжди корисно при дебагу!
print(qs.query)
```

### Ланцюжок методів (method chaining)

Всі ці методи повертають **новий** QuerySet, не змінюючи оригінальний:

```python
# filter / exclude / Q objects
Note.objects.filter(status='published')
Note.objects.exclude(status='draft')
Note.objects.filter(Q(status='published') | Q(views_count__gt=100))

# Складні lookups через __ (double underscore)
Note.objects.filter(user__username='alice')        # JOIN + WHERE
Note.objects.filter(category__name__icontains='py')# JOIN + LIKE
Note.objects.filter(created_at__year=2024)         # DATE extraction
Note.objects.filter(tags__name='python')           # M:N JOIN

# Сортування
Note.objects.order_by('created_at')   # ASC
Note.objects.order_by('-created_at')  # DESC
Note.objects.order_by('category__name', '-created_at')  # кілька полів

# Видалення дублікатів
Note.objects.filter(tags__name='python').distinct()  # M:N може давати дублі

# Обмеження (LIMIT / OFFSET)
Note.objects.all()[:10]              # LIMIT 10
Note.objects.all()[10:20]            # LIMIT 10 OFFSET 10
```

### Lookup таблиця — __ (double underscore)

```python
# Значення
field__exact = 'val'        # WHERE field = 'val' (за замовчуванням)
field__iexact = 'val'       # WHERE LOWER(field) = LOWER('val')
field__contains = 'val'     # WHERE field LIKE '%val%'
field__icontains = 'val'    # WHERE LOWER(field) LIKE LOWER('%val%')
field__startswith = 'val'   # WHERE field LIKE 'val%'
field__in = [1, 2, 3]       # WHERE field IN (1, 2, 3)
field__range = (1, 10)      # WHERE field BETWEEN 1 AND 10

# Числові порівняння
field__gt = 5               # WHERE field > 5
field__gte = 5              # WHERE field >= 5
field__lt = 5               # WHERE field < 5
field__lte = 5              # WHERE field <= 5

# NULL перевірки
field__isnull = True        # WHERE field IS NULL
field__isnull = False       # WHERE field IS NOT NULL

# Дати
field__year = 2024          # WHERE EXTRACT(YEAR FROM field) = 2024
field__month = 1            # WHERE EXTRACT(MONTH FROM field) = 1
field__date = date(2024,1,1)# WHERE DATE(field) = '2024-01-01'

# Traversal через FK (Django JOIN автоматично)
note__user__username = 'alice'     # notes → users → username
note__category__name = 'Tech'      # notes → categories → name
```

---

## 3. N+1 Query Problem

---
> **🧠 Ментальна модель:** N+1 — це як їхати в магазин за кожним продуктом окремо. Маєш список з 10 продуктів → їдеш 10 разів. Або можна поїхати раз з повним списком. "1" — це запит за списком (100 нотаток). "N" — це 100 окремих запитів за авторами кожної нотатки. Разом: 101 запит замість 2.
>
> **📚 Чому це так часто виникає:** Django ORM лінивий — він не завантажує пов'язані об'єкти до тих пір поки їх не попросять. В шаблоні пишеш `{{ note.user.username }}` — Django виконує `SELECT FROM auth_user WHERE id=X` для кожної нотатки в циклі.
>
> **🌐 Як виявити N+1:** Django Debug Toolbar (кількість запитів на сторінці). `django-silk` для профілювання. Або `connection.queries` — список всіх SQL запитів у поточному запиті.
>
> **❌ Типова помилка:** Не думати про SELECT при написанні шаблонів. Цикл `{% for note in notes %}{{ note.user.username }}{% endfor %}` — виглядає нешкідливо, але якщо `notes` — QuerySet без `select_related('user')` → N запитів.
---

```python
# ❌ ПРОБЛЕМА — N+1 queries
def notes_list_view(request):
    notes = Note.objects.filter(status='published')[:50]
    # До цього моменту: 1 запит (SELECT FROM notes_note WHERE ... LIMIT 50)
    
    for note in notes:
        # ТУТ для КОЖНОЇ нотатки виконується:
        # SELECT * FROM auth_user WHERE id = ?
        # SELECT * FROM notes_category WHERE id = ?
        print(note.user.username)    # ← ЗАПИТ #1 (author)
        print(note.category.name)   # ← ЗАПИТ #2 (category)
    
    # Підсумок: 1 + 50*2 = 101 SQL-запит!
    # При 1000 нотатках → 2001 запитів → таймаут

# ✅ РІШЕННЯ — select_related (для ForeignKey, OneToOne)
def notes_list_view(request):
    notes = Note.objects.select_related(
        'user',          # JOIN auth_user
        'category'       # JOIN notes_category
    ).filter(status='published')[:50]
    # 1 SQL-запит:
    # SELECT n.*, u.*, c.* FROM notes_note n
    # LEFT JOIN auth_user u ON n.user_id = u.id
    # LEFT JOIN notes_category c ON n.category_id = c.id
    # WHERE n.status = 'published' LIMIT 50
    
    for note in notes:
        print(note.user.username)   # ← з кешу, 0 SQL!
        print(note.category.name)  # ← з кешу, 0 SQL!
    
    # Підсумок: 1 запит. Завжди.


# ✅ РІШЕННЯ — prefetch_related (для ManyToMany, reverse FK)
def notes_with_tags_view(request):
    notes = Note.objects.prefetch_related(
        'tags',           # M:N через junction table (2 запити)
        'comments',       # reverse FK (2 запити)
    ).filter(status='published')[:50]
    # Запит 1: SELECT * FROM notes_note WHERE ... LIMIT 50
    # Запит 2: SELECT tags.*, nt.note_id FROM tags
    #          INNER JOIN note_tags nt WHERE nt.note_id IN (1,2,...,50)
    # Запит 3: SELECT * FROM comments WHERE note_id IN (1,2,...,50)
    # Підсумок: 3 запити замість 1 + 50*2 = 101

    for note in notes:
        for tag in note.tags.all():       # ← з кешу!
            print(tag.name)
        for comment in note.comments.all(): # ← з кешу!
            print(comment.body)
```

### select_related vs prefetch_related — коли що використовувати

```
select_related — для ОДИНИЧНИХ зв'язків:
  ✓ ForeignKey:    note.user, note.category
  ✓ OneToOne:      user.profile
  ✗ ManyToMany:    note.tags.all() — НЕ МОЖНА
  ✗ Reverse FK:    note.comments.all() — НЕ МОЖНА

  Механізм: SQL JOIN → 1 запит з більшими рядками

prefetch_related — для КОЛЕКЦІЙ:
  ✓ ManyToMany:    note.tags.all()
  ✓ Reverse FK:    note.comments.all()
  ✓ ForeignKey:    теж працює (але select_related ефективніший)

  Механізм: 2 окремих SQL + Python join у пам'яті

Правило:
  ForeignKey / OneToOne → select_related
  ManyToMany / reverse FK → prefetch_related
  Складні вкладені зв'язки → можна комбінувати обидва
```

```python
# Комбінований приклад
notes = Note.objects.select_related(
    'user',            # FK → JOIN
    'user__profile',   # через FK до OneToOne → ще один JOIN
    'category'         # FK → JOIN
).prefetch_related(
    'tags',            # M:N → окремий запит
    'comments__author' # Reverse FK + FK → prefetch + prefetch
).filter(status='published')
```

---

## 4. F() Expressions — операції на рівні БД

---
> **🧠 Ментальна модель:** `F('field')` — це посилання на значення стовпця **на рівні бази даних**. Замість "прочитай значення в Python, зміни, запиши назад" → "накажи БД змінити прямо там". Це як різниця між "принеси мені цифру з сейфу, я помножу і покладу назад" (Python-read) проти "помнож значення в сейфі не виймаючи" (F() expression).
>
> **📚 Чому F() рятує від race condition:** Без F(): `note.views_count += 1; note.save()` → прочитав 100, збільшив до 101, зберіг 101. Але що якщо 1000 concurrent запитів прочитали **одночасно** 100, всі збільшили до 101 і зберегли 101? Всі 1000 переглядів втрачені! З F(): `Note.objects.filter(id=1).update(views_count=F('views_count')+1)` → `UPDATE notes_note SET views_count = views_count + 1 WHERE id=1` → атомарна операція на рівні БД, race condition неможливий.
>
> **🌐 Як PostgreSQL виконує F():** `UPDATE notes_note SET views_count = views_count + 1 WHERE id=1` — це один атомарний SQL. PostgreSQL виконує read-modify-write внутрішньо в рамках однієї транзакції, блокуючи рядок на час UPDATE.
>
> **❌ Типова помилка:** Після `.update(views_count=F('views_count')+1)` очікувати що `note.views_count` оновиться. **Ні.** Python-об'єкт не знає про зміну в БД. Потрібно `note.refresh_from_db()`.
---

```python
from django.db.models import F

# ❌ НЕБЕЗПЕЧНО — race condition при конкурентних запитах
def increment_views_UNSAFE(note_id):
    note = Note.objects.get(id=note_id)
    note.views_count += 1  # читаємо в Python
    note.save()             # записуємо назад
    # 2 SQL-запити + window of vulnerability між ними

# ✅ БЕЗПЕЧНО — атомарна операція на рівні БД
def increment_views_SAFE(note_id):
    Note.objects.filter(id=note_id).update(
        views_count=F('views_count') + 1
    )
    # 1 SQL: UPDATE notes_note SET views_count = views_count + 1 WHERE id=?
    # Атомарно, без race condition

# F() для порівняння двох стовпців
# Знайти нотатки де likes > views (популярні серед незначної кількості читачів)
Note.objects.filter(likes_count__gt=F('views_count'))
# WHERE likes_count > views_count (порівняння між СТОВПЦЯМИ, не значеннями)

# F() з арифметикою
Note.objects.update(
    views_count=F('views_count') * 2,    # подвоїти всі перегляди
    likes_count=F('likes_count') + 10,   # дати +10 лайків всім
)
# UPDATE notes_note SET views_count = views_count * 2, likes_count = likes_count + 10

# F() в annotate (розрахункові поля)
from django.db.models import ExpressionWrapper, FloatField
Note.objects.annotate(
    engagement_rate=ExpressionWrapper(
        F('likes_count') * 100.0 / F('views_count'),
        output_field=FloatField()
    )
).filter(engagement_rate__gt=5.0)
# Розраховує відсоток залученості безпосередньо в SQL
```

---

## 5. transaction.atomic() — атомарність

---
> **🧠 Ментальна модель:** `transaction.atomic()` — це "все або нічого" для групи операцій. Уяви банківський переказ: знімаєш 500 UAH з рахунку А, додаєш до рахунку Б. Якщо після зняття сервер падає — гроші зникли з А, але не з'явились в Б. `atomic()` гарантує: або ОБИДВІ операції відбуваються, або ЖОДНА.
>
> **📚 Що відбувається в SQL:** `with transaction.atomic():` → `BEGIN` → операції → `COMMIT`. Якщо exception → `ROLLBACK`. PostgreSQL скасовує всі зміни в рамках транзакції.
>
> **🌐 Вкладені atomic блоки:** Django використовує **Savepoints** для вкладених `atomic()`. `SAVEPOINT sp_1` → вкладений блок → якщо failure → `ROLLBACK TO SAVEPOINT sp_1` (тільки вкладений відкочується, зовнішній продовжує). Якщо success → `RELEASE SAVEPOINT sp_1`.
>
> **❌ КРИТИЧНА помилка:** `try/except` ВСЕРЕДИНІ `atomic()` — ніколи! Якщо перехоплюєш exception всередині atomic → транзакція "зламана" (aborted state), але не rollback'd. Django кине `TransactionManagementError` при спробі будь-якої наступної операції. Exception треба перехоплювати ЗОВНІ atomic.
---

```python
from django.db import transaction

# ✅ ПРАВИЛЬНО — atomic для пов'язаних операцій
def create_note_with_revision(user, title, content):
    """
    Якщо NoteRevision не створиться → Note теж не збережеться.
    Цілісність даних гарантована.
    """
    with transaction.atomic():
        note = Note.objects.create(
            title=title,
            content=content,
            user=user,
            status='draft'
        )
        # Якщо тут Exception → Note теж rollback
        revision = NoteRevision.objects.create(
            note=note,
            content=content,
            author=user,
            version=1
        )
    # Після виходу з блоку: COMMIT (якщо не було exception)
    return note

# ❌ НЕПРАВИЛЬНО — exception catch всередині atomic
def wrong_approach():
    with transaction.atomic():
        note = Note.objects.create(title='Test', user=user)
        try:
            revision = NoteRevision.objects.create(...)
        except Exception:
            pass  # ЦЕ ЗЛАМАЄ ТРАНЗАКЦІЮ!
            # Транзакція тепер у "aborted" стані
            # Наступний Note.objects.filter(...) кине TransactionManagementError!

# ✅ ПРАВИЛЬНО — exception catch ЗОВНІ atomic
def correct_approach():
    try:
        with transaction.atomic():
            note = Note.objects.create(title='Test', user=user)
            revision = NoteRevision.objects.create(...)
    except Exception as e:
        # ROLLBACK вже відбувся, тут просто логуємо
        logger.error(f"Failed to create note: {e}")
        return None
    return note

# Вкладені atomic (Savepoints)
def complex_operation():
    with transaction.atomic():   # BEGIN
        note = Note.objects.create(...)   # INSERT note
        
        with transaction.atomic():   # SAVEPOINT sp_1
            # Якщо це впаде — тільки comment відкочується
            Comment.objects.create(note=note, ...)
        
        # Note зберігається навіть якщо Comment впав
```

### on_commit — виконати після commit

```python
from django.db import transaction

def create_note(request):
    with transaction.atomic():
        note = Note.objects.create(...)
        
        # on_commit виконується ТІЛЬКИ якщо COMMIT успішний
        # Ідеально для: відправки email, Celery task, Webhook
        transaction.on_commit(
            lambda: send_notification_email.delay(note.id)
        )
        # Якщо транзакція rollback'd → email НЕ відправиться
        # Якщо commit успішний → Celery task буде виконано
```

---

## 6. Sistema міграцій Django

---
> **🧠 Ментальна модель:** Міграції — це **git для схеми бази даних**. Кожна міграційна файл — це "коміт" що описує зміни схеми: `CREATE TABLE`, `ALTER TABLE`, `ADD COLUMN`. Django відстежує які міграції вже виконані (таблиця `django_migrations`). `migrate` виконує тільки нові (ще не застосовані) міграції.
>
> **📚 Чому не можна просто редагувати таблицю вручну:** На production є дані. Якщо вручну додати стовпець — Django не знає про це. Якщо потім запустити `makemigrations` і `migrate` — Django спробує додати стовпець що вже існує → помилка. Завжди використовуй міграції.
>
> **🌐 Граф залежностей міграцій:** Кожна міграція знає про свої `dependencies` (попередні міграції). Django будує DAG (Directed Acyclic Graph) і виконує міграції в правильному порядку. Якщо міграція A залежить від B — B виконується першою.
>
> **❌ Типова помилка:** Редагувати вже застосовану міграцію. Якщо міграція вже застосована на production і ти її редагуєш — production і development більше не синхронні. Django порівнює по **hash файлу**. Зміна застосованої міграції = катастрофа. Якщо потрібна зміна → нова міграція.
---

### Workflow міграцій

```
Крок 1: Змінюємо models.py
        (додаємо поле, нову модель, constraint, index)
           │
           ▼
Крок 2: makemigrations
        Django порівнює поточний стан models.py
        з останнім станом міграцій
        → генерує файл 0003_add_views_count.py
           │
           ▼
Крок 3: Перевіряємо файл міграції
        (обов'язково! особливо для backward compatibility)
           │
           ▼
Крок 4: migrate
        Django читає django_migrations таблицю
        → знаходить невиконані міграції
        → виконує по порядку залежностей
        → записує в django_migrations
           │
           ▼
Крок 5: БД оновлена, models.py і схема синхронні
```

```bash
# Основні команди

# Показати стан всіх міграцій
python manage.py showmigrations

# Згенерувати міграцію
python manage.py makemigrations

# Згенерувати з ім'ям (рекомендовано)
python manage.py makemigrations --name add_views_count_to_note

# Застосувати всі міграції
python manage.py migrate

# Застосувати міграції тільки для одного додатку
python manage.py migrate hello_app

# Переглянути SQL без виконання (корисно для code review)
python manage.py sqlmigrate hello_app 0002

# Відкотити до певної міграції (НЕБЕЗПЕЧНО — втрата даних!)
python manage.py migrate hello_app 0001
```

### Приклад файлу міграції

```python
# hello_app/migrations/0003_add_views_count.py

from django.db import migrations, models

class Migration(migrations.Migration):
    
    # Ця міграція залежить від попередньої
    # Django не виконає 0003 поки не виконана 0002
    dependencies = [
        ('hello_app', '0002_extended_models'),
    ]
    
    operations = [
        # Додаємо стовпець
        migrations.AddField(
            model_name='note',
            name='views_count',
            field=models.PositiveIntegerField(default=0),
        ),
        
        # Додаємо індекс
        migrations.AddIndex(
            model_name='note',
            index=models.Index(fields=['views_count'], name='note_views_idx'),
        ),
    ]
```

### Типи операцій у міграціях

```python
# Модель
migrations.CreateModel(name='Tag', fields=[...])
migrations.DeleteModel(name='Tag')
migrations.RenameModel(old_name='Tag', new_name='Label')

# Поля
migrations.AddField(model_name='note', name='views_count', field=...)
migrations.RemoveField(model_name='note', name='old_field')
migrations.AlterField(model_name='note', name='title', field=...)
migrations.RenameField(model_name='note', old_name='body', new_name='content')

# Схема
migrations.AddConstraint(model_name='note', constraint=...)
migrations.RemoveConstraint(model_name='note', name='...')
migrations.AddIndex(model_name='note', index=...)
migrations.RemoveIndex(model_name='note', name='...')

# Довільний SQL (для складних міграцій)
migrations.RunSQL(
    sql="UPDATE notes_note SET status = 'published' WHERE is_published = TRUE",
    reverse_sql="UPDATE notes_note SET is_published = TRUE WHERE status = 'published'"
)

# Python код (для трансформації даних)
def populate_slugs(apps, schema_editor):
    Note = apps.get_model('hello_app', 'Note')
    for note in Note.objects.all():
        note.slug = slugify(note.title)
        note.save()

migrations.RunPython(populate_slugs, reverse_code=migrations.RunPython.noop)
```

---

## 7. annotate() та aggregate() — підрахунки і групування

---
> **🧠 Ментальна модель:** `annotate()` — це "додати розрахунковий стовпець до кожного рядка" (GROUP BY рівень кожного об'єкта). `aggregate()` — це "розрахувати одне значення для всього QuerySet" (одне число в відповідь). `annotate()` → список з новим полем. `aggregate()` → словник.
>
> **📚 Чому це важливо:** Без annotate: `for category in categories: count = Note.objects.filter(category=category).count()` → N+1! З annotate: `Category.objects.annotate(note_count=Count('notes'))` → 1 SQL з GROUP BY.
>
> **🌐 SQL генерується:** `annotate(note_count=Count('notes'))` → `SELECT *, COUNT(notes_note.id) AS note_count FROM categories LEFT JOIN notes_note ON ... GROUP BY categories.id`. Все в одному запиті.
>
> **❌ Типова помилка:** Рахувати агрегати в Python циклах замість SQL. Якщо можна описати підрахунок через `Count`, `Sum`, `Avg` — завжди використовуй `annotate()`.
---

```python
from django.db.models import Count, Sum, Avg, Max, Min, Q

# aggregate() — одне значення для всього QuerySet
result = Note.objects.aggregate(
    total=Count('id'),
    total_views=Sum('views_count'),
    avg_views=Avg('views_count'),
    max_views=Max('views_count'),
)
# result = {'total': 1250, 'total_views': 45000, 'avg_views': 36.0, 'max_views': 1200}
# SQL: SELECT COUNT(id), SUM(views_count), AVG(views_count), MAX(views_count)
#      FROM notes_note


# annotate() — розрахунковий стовпець для кожного об'єкта
categories = Category.objects.annotate(
    note_count=Count('notes'),                              # кількість нотаток
    published_count=Count('notes', filter=Q(notes__status='published')),
    avg_views=Avg('notes__views_count'),
).filter(note_count__gte=1).order_by('-note_count')
# SQL: SELECT categories.*, COUNT(notes.id) AS note_count, ...
#      FROM categories LEFT JOIN notes ON ...
#      GROUP BY categories.id HAVING COUNT(notes.id) >= 1

for cat in categories:
    print(f"{cat.name}: {cat.note_count} нотаток, avg {cat.avg_views:.1f} переглядів


# Annotate з умовою (conditional annotation)
from django.db.models import Case, When, IntegerField, Value

notes = Note.objects.annotate(
    engagement=Case(
        When(views_count__gte=1000, then=Value(3)),   # "viral"
        When(views_count__gte=100, then=Value(2)),    # "popular"
        When(views_count__gte=10, then=Value(1)),     # "growing"
        default=Value(0),                              # "new"
        output_field=IntegerField(),
    )
)
# Кожна нотатка тепер має поле `engagement` (0-3)
```

---

## 8. Field System та lifecycle об'єкта

---
> **🧠 Ментальна модель:** `save()` — це не просто "записати в БД". Це **5-кроковий процес**: pre_save сигнал → валідація → INSERT або UPDATE → post_save сигнал. `auto_now_add` і `auto_now` — це не Python логіка, це параметри поля що впливають на SQL генерацію.
>
> **📚 Різниця auto_now_add vs auto_now:** `auto_now_add=True` → встановлюється ОДИН РАЗ при створенні, ніколи не оновлюється. `auto_now=True` → оновлюється при кожному `save()`. Одночасно `auto_now=True` означає `editable=False` і `blank=True` — поле недоступне у формах.
>
> **🌐 Як Django вирішує INSERT vs UPDATE:** `save()` перевіряє: якщо `self.pk is None` → `INSERT`. Якщо `pk` вказано і запис існує → `UPDATE`. Якщо `force_insert=True` → завжди `INSERT` (навіть якщо pk вказано).
>
> **❌ Типова помилка:** `auto_now_add` і `default=timezone.now` — різні речі. `default` можна перевизначити при створенні: `Note(created_at=yesterday)`. `auto_now_add` — **ніколи** не перевизначити (editable=False).
---

```python
class Note(models.Model):
    title = models.CharField(
        max_length=200,           # VARCHAR(200) NOT NULL
        db_index=True             # CREATE INDEX ON title
    )
    content = models.TextField(
        blank=True,               # дозволяє порожній рядок у формі
        default=''                # DEFAULT '' в SQL
    )
    slug = models.SlugField(
        max_length=200,
        unique=True               # UNIQUE constraint
    )
    
    # Nullable field (потребує і null=True і blank=True для форм)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,    # NULL в SQL + blank в формі
        related_name='notes'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True         # SET ONCE на момент INSERT
    )
    updated_at = models.DateTimeField(
        auto_now=True             # UPDATE при кожному save()
    )
    
    views_count = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    
    def save(self, *args, **kwargs):
        """
        Перевизначення save() — auto-generate slug.
        """
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)  # Не забудь super()!
```

### Lifecycle об'єкта

```
Створення:
    note = Note(title='Test', user=user)
         │  ← Python об'єкт, note.id = None, ЖОДНОГО SQL
         ▼
    note.save()
    SQL: INSERT INTO notes_note (title, user_id, ...) VALUES ('Test', 5, ...)
    DB:  RETURNING id  → note.id = 42

Оновлення:
    note.title = 'Updated'
    note.save()
    SQL: UPDATE notes_note SET title='Updated', updated_at=NOW() WHERE id=42

    # Оновлення конкретних полів (більш ефективно):
    note.save(update_fields=['title', 'status'])
    # UPDATE notes_note SET title=..., status=... WHERE id=42

Видалення:
    note.delete()
    SQL: DELETE FROM notes_note WHERE id=42
    # Cascade: якщо comments ON DELETE CASCADE → видаляються в БД
```

---

## 9. Корисні патерни та best practices

```python
# get_or_create — CREATE якщо не існує
category, created = Category.objects.get_or_create(
    name='Python',
    defaults={'slug': 'python', 'description': 'Python programming'}
)
# Returns: (object, bool) — bool = True якщо СТВОРЕНО

# update_or_create — UPDATE якщо існує, CREATE якщо ні
profile, created = UserProfile.objects.update_or_create(
    user=request.user,
    defaults={'bio': new_bio, 'city': new_city}
)

# bulk_create — масове створення (1 SQL замість N)
tags = [Tag(name=name, slug=slugify(name)) for name in ['python', 'django', 'orm']]
Tag.objects.bulk_create(tags, ignore_conflicts=True)
# SQL: INSERT INTO notes_tag (name, slug) VALUES (...), (...), (...)

# bulk_update — масове оновлення (1 SQL)
notes = list(Note.objects.filter(status='draft'))
for note in notes:
    note.views_count = 0
Note.objects.bulk_update(notes, ['views_count'])

# .values() та .values_list() — dict/tuple замість Model об'єктів
Note.objects.values('id', 'title', 'status')
# → [{'id': 1, 'title': 'Django ORM', 'status': 'published'}, ...]

Note.objects.values_list('title', flat=True)
# → ['Django ORM', 'CSS Tips', ...]

# .only() / .defer() — відкладене завантаження полів
Note.objects.only('id', 'title', 'status')      # тільки ці поля
Note.objects.defer('content')                    # всі КРІМ content
```

---

## Prediction Exercises — перевір себе

### Exercise 1: Lazy Evaluation

```python
qs = Note.objects.filter(status='published')
qs = qs.order_by('-views_count')
qs = qs.select_related('user')
```

**Питання:** Скільки SQL-запитів виконалось після цих трьох рядків?

> Відповідь: **0 запитів**. QuerySet лінивий — SQL виконається тільки при `list(qs)`, `qs.first()`, ітерації тощо.

### Exercise 2: N+1 Detection

```python
notes = Note.objects.all()[:10]
for note in notes:
    print(note.user.username, note.category.name)
```

**Питання:** Скільки SQL-запитів виконається?

> Відповідь: **1 + 10 + 10 = 21 запит** (якщо в кожної нотатки різний user і category).
>
> Виправлення: `Note.objects.select_related('user', 'category').all()[:10]` → **1 запит**.

### Exercise 3: F() vs Python

```python
# Варіант A:
note = Note.objects.get(id=1)
note.views_count += 1
note.save()

# Варіант B:
Note.objects.filter(id=1).update(views_count=F('views_count') + 1)
```

**Питання:** В чому різниця?

> Відповідь: A — 2 запити + race condition. B — 1 атомарний SQL, без race condition. **B завжди краще для лічильників**.

---

## Питання для самоперевірки

1. Що таке Lazy Evaluation в Django ORM і коли SQL фактично виконується?
2. Яка різниця між `select_related` і `prefetch_related`? Для яких зв'язків кожен?
3. Що таке N+1 Query Problem і як його виявити?
4. Чому `F('views_count') + 1` безпечніший за `note.views_count + 1`?
5. Що відбувається якщо зробити `try/except` всередині `transaction.atomic()`?
6. Яка різниця між `annotate()` і `aggregate()`?
7. Що таке Django Migrations і навіщо вони потрібні?
8. Яка різниця між `auto_now_add` і `auto_now`?
9. Коли використовувати `bulk_create()` і яка перевага?
10. Як переглянути SQL що генерує QuerySet?
