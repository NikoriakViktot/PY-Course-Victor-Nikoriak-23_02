# Django ORM та Бази даних — Система знань

> Цей файл — головна карта навчання. Починай тут.
> Матеріал організований від фундаменту реляційних БД до глибоких ORM-патернів Django.

---

## Карта навчання

```
РІВЕНЬ 1: Реляційний фундамент
    → Чому існують бази даних
    → Таблиці, рядки, стовпці, типи
    → Primary Key, Foreign Key, Constraints
    → Нормалізація (1NF, 2NF, 3NF)

РІВЕНЬ 2: Архітектурне мислення для БД
    → Проектування схеми: translating domains to relations
    → ACID властивості та CAP теорема
    → Системи відносин (1:1, 1:N, M:N, Referential Integrity)

РІВЕНЬ 3: SQL як мова запитів
    → SELECT, WHERE, JOIN (INNER/LEFT/RIGHT/FULL)
    → GROUP BY, Aggregations
    → Як БД виконує запит (Parsing → Planning → Execution)

РІВЕНЬ 4: Django ORM — внутрішня механіка
    → Models, Managers, QuerySets
    → Ліниве обчислення (Lazy Evaluation)
    → SQL-генерація та traversal через __

РІВЕНЬ 5: Система міграцій
    → makemigrations → граф залежностей → migrate
    → Schema version control

РІВЕНЬ 6: Архітектура моделей Django
    → Field System і lifecycle об'єкта
    → SQLite vs PostgreSQL

РІВЕНЬ 7: Дебаг та продуктивність
    → N+1 Query Problem
    → select_related vs prefetch_related
    → QuerySet.query інтроспекція

РІВЕНЬ 8: Django Forms — кордон довіри (Trust Boundary)
    → request.POST → QueryDict → is_valid() → cleaned_data
    → Validation Pipeline: to_python → validate → run_validators → clean_<field> → clean
    → ModelForm + save(commit=False) + M:N транзакції
    → Widget архітектура + Bootstrap CSS injection
    → CSRF захист + PRG патерн

РІВЕНЬ 9: Реальний Django-проєкт
    → notes_project/ — 9 моделей (User, Notebook, Note, Tag, Reminder,
                        TodoList, TodoItem, ShoppingList, ShopItem)
    → Services/Selectors архітектура
    → QuerySet API: select_related, prefetch_related, F(), atomic()
```

---

## Файли документації

| Файл | Рівні | Що дає |
|------|-------|--------|
| [RELATIONAL_DB_FOUNDATIONS.md](RELATIONAL_DB_FOUNDATIONS.md) | 1–3 | Фундамент реляційних БД: таблиці, ключі, нормалізація, SQL, Query Execution Flow, Predicate Pushdown, JOIN алгоритми, **SQL Injection + Trust Boundary Architecture** |
| [DJANGO_ORM_DEEP.md](DJANGO_ORM_DEEP.md) | 4–7 | Django ORM: QuerySets, Lazy Evaluation, Migrations, Field System, N+1, select_related, prefetch_related, F(), atomic() |
| [DJANGO_FORMS.md](DJANGO_FORMS.md) | 8 | Форми: Trust Boundary, Validation Pipeline, ModelForm, Widget/Bootstrap CSS injection, CSRF, PRG патерн, Crispy Forms |
| [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) | 9 | **Повна архітектура бізнес-шару:** View→InputSerializer→Service→Selector→ORM→OutputSerializer. Data flow, антипатерни, таблиця відповідальностей. Serializers як transport layer. |
| [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) | 9 | **Selector — шар читання:** CQRS-light (Reads vs Writes), централізація N+1, QuerySet vs evaluated list, selector + django-filter без витоку ORM, naming convention, шаблон |
| [DJANGO_SERVICES.md](DJANGO_SERVICES.md) | 9 | **Service — шар бізнес-логіки:** stateless функції, keyword-only args, @transaction.atomic, side effects через on_commit(), Celery task як transport layer, маппінг помилок домену → HTTP |
| [POSTGRESQL_ADVANCED.md](POSTGRESQL_ADVANCED.md) | — | PostgreSQL архітектура (MVCC, WAL, Process Model), Docker підключення, PostgreSQL-специфічні поля, PgBouncer, production stack |
| [INDEXING_DEEP.md](INDEXING_DEEP.md) | — | Фізика B-Tree, composite/covering/GIN/Trigram indexes, EXPLAIN ANALYZE |
| [TRANSACTIONS_CONCURRENCY.md](TRANSACTIONS_CONCURRENCY.md) | — | Транзакції, row locking, deadlocks, race conditions, select_for_update(), on_commit() |
| [ORM_MERMAID.md](ORM_MERMAID.md) | Всі | 20+ Mermaid-схем: ER-діаграми, ORM Flow, Migration Lifecycle, N+1, B-Tree, Deadlock, Transaction timelines, Services/Selectors |

---

## Практичні проєкти

| Проєкт | Папка | Що всередині |
|--------|-------|--------------|
| [Notes Platform — FBV](notes_project/README.md) | `notes_project/` | Платформа нотаток: 9 моделей (UserProfile, Notebook, Tag, Note, Reminder, TodoList, TodoItem, ShoppingList, ShopItem). Services/Selectors архітектура. Всі типи зв'язків. QuerySet API. SQLite→PostgreSQL міграція. |
| [Notes Platform — CBV](notes_project_cbv/README.md) | `notes_project_cbv/` | Та сама платформа, але `views.py` і `urls.py` переписані на Class-Based Views: `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`, `LoginRequiredMixin`, `UserQuerySetMixin`. |

### Рекомендований порядок проєктів

```
notes_project/     ← спочатку: FBV, ORM, Services/Selectors, PostgreSQL
      ↓
notes_project_cbv/ ← потім: ті самі моделі/сервіси, але views → CBV
```

### Ключові файли notes_project (FBV)

| Файл | Що робить | Де в туторіалі |
|------|-----------|----------------|
| [`hello_app/orm_laboratory.ipynb`](notes_project/hello_app/orm_laboratory.ipynb) | 🔬 **Інтерактивна лабораторія** — 48 клітинок: QuerySet laziness, field lookups, Q()/F(), aggregation, N+1, select_related, prefetch_related, bulk ops, raw SQL, транзакції, SQL inspection | Рівні 4–7 |
| `hello_app/models.py` | 9 моделей з усіма зв'язками + Meta.indexes + constraints | Кроки 3–5 README |
| `hello_app/selectors.py` | SELECT шар — всі QuerySets з оптимізацією | Крок 7 README |
| `hello_app/services.py` | Бізнес-логіка — CREATE/UPDATE/DELETE в транзакціях | Крок 7 README |
| `hello_app/views.py` | Тонкий HTTP шар — тільки request/response | Крок 8 README |
| `hello_app/forms.py` | Форми з Trust Boundary + user-filtered QuerySets | Крок 8 README |
| `hello_app/admin.py` | Admin з select_related, TabularInline, annotate | — |
| `hello_app/migrations/` | Автогенерований граф міграцій | Крок 5 README |

### Ключові файли notes_project_cbv (CBV)

| Файл | Що змінилось |
|------|--------------|
| [`hello_app/views.py`](notes_project_cbv/hello_app/views.py) | ★ Переписано на CBV: `LoginRequiredMixin`, `UserQuerySetMixin`, `ListView`/`DetailView`/`CreateView`/`UpdateView`/`DeleteView` |
| [`hello_app/urls.py`](notes_project_cbv/hello_app/urls.py) | ★ `.as_view()` у кожному `path()` замість функцій |
| [`hello_app/views_fbv_backup.py`](notes_project_cbv/hello_app/views_fbv_backup.py) | FBV оригінал для порівняння (з CBV-еквівалентами у кожній функції) |
| [`hello_app/forms_views_laboratory.ipynb`](notes_project_cbv/hello_app/forms_views_laboratory.ipynb) | 🔬 **Інтерактивна лабораторія** — 45 клітинок: Trust Boundary, Validation Pipeline, user= queryset, instance= edit, Widget HTML, RequestFactory, django.test.Client, reverse(), CSRF |
| Всі інші файли | Без змін — ті самі models, forms, selectors, services, templates |

---

## Ключові концепції — швидкий довідник

### Реляційний фундамент
- **Primary Key** — унікальний ідентифікатор рядка (не може повторюватись)
- **Foreign Key** — стовпець що зберігає PK іншої таблиці (link між таблицями)
- **1NF** — всі атрибути атомарні; **2NF** — залежать від PK; **3NF** — без транзитивних залежностей
- **ACID** — Atomicity, Consistency, Isolation, Durability (PostgreSQL гарантує це)
- **CAP** — Consistency, Availability, Partition Tolerance (можна тільки 2 з 3 у distributed)

### Django ORM
- **QuerySet** — **лінивий**: SQL виконується лише при ітерації/slice/len/list()
- **select_related** — JOIN на рівні SQL (для ForeignKey, OneToOne) → 1 запит
- **prefetch_related** — окремий запит + Python join (для ManyToMany, reverse FK) → 2 запити
- **N+1 проблема** — 1 запит на список + N запитів у циклі = катастрофа
- **F()** — операції на рівні БД (без race condition)
- **transaction.atomic()** — атомарні блоки: або все, або нічого

### Типи зв'язків в Django
| Зв'язок | Django поле | SQL механізм |
|---------|-------------|--------------|
| 1:N | `ForeignKey` | FK у таблиці "багатьох" |
| 1:1 | `OneToOneField` | FK + UNIQUE constraint |
| M:N | `ManyToManyField` | Junction table автоматично |

---

## Типові помилки

| Помилка | Наслідок | Рішення |
|---------|----------|---------|
| N+1 запити | 1000+ SQL на одну сторінку | `select_related`, `prefetch_related` |
| `save()` замість `F()` при інкременті | Race condition: втрата даних | `F('views_count') + 1` |
| `atomic()` exception trap | `TransactionManagementError` | Catch виключень ЗОВНІ блоку |
| `DecimalField` замість `FloatField` для грошей | Округлення помилки | Завжди `DecimalField` для валюти |
| Без `select_related` в ListView | N+1 при рендері шаблону | Завжди `select_related` для FK |
| `cursor.execute(f"...{user_input}...")` | SQL ін'єкція | `cursor.execute("...%s", [user_input])` |
| `Note.objects.filter(...)` прямо у View | Порушення Services/Selectors | Всі QuerySets → у `selectors.py` |
| `request.POST[key]` прямо в ORM | Trust boundary violation | Через `form.cleaned_data` після `is_valid()` |

---

## Рекомендований порядок читання

```
 1. RELATIONAL_DB_FOUNDATIONS.md      ← Розумієш реляційну модель, SQL, execution flow
 2. ORM_MERMAID.md (ER-діаграми)      ← Бачиш зв'язки візуально перед кодом
 3. DJANGO_ORM_DEEP.md                ← ORM: QuerySets, lazy eval, N+1, F(), atomic()
 4. DJANGO_FORMS.md                   ← Форми: Trust Boundary, Validation Pipeline, PRG
 5. POSTGRESQL_ADVANCED.md            ← MVCC, WAL, Docker підключення, prod стек
 6. INDEXING_DEEP.md                  ← B-Tree, GIN, EXPLAIN ANALYZE
 7. TRANSACTIONS_CONCURRENCY.md       ← Deadlocks, race conditions, select_for_update()
 8. ORM_MERMAID.md (всі схеми)        ← Закріплюєш всю архітектуру
 9. DJANGO_SERVICES_SELECTORS.md      ← Повна архітектура: View→Service→Selector→ORM, data flow, антипатерни
10. DJANGO_SELECTORS.md               ← Глибоко: CQRS-light, N+1 в одному місці, naming convention
11. DJANGO_SERVICES.md                ← Глибоко: stateless, atomic, on_commit, Celery як transport
12. notes_project/README.md           ← Покроковий туторіал: проєктування → PostgreSQL
13. notes_project/hello_app/models.py    ← Читай як навчальний матеріал з коментарями
14. notes_project/hello_app/selectors.py ← SELECT шар: N+1 рішення, Prefetch, annotate
15. notes_project/hello_app/services.py  ← Бізнес-логіка: atomic(), F(), select_for_update()
16. notes_project/hello_app/forms.py     ← Trust Boundary у практиці: user-filtered FK/M:N
17. notes_project/hello_app/orm_laboratory.ipynb ← Інтерактивна лабораторія: виконай кожну клітинку і подивись SQL
18. notes_project_cbv/README.md          ← CBV туторіал: as_view(), dispatch(), Generic Views, Mixins
19. notes_project_cbv/hello_app/views.py ← CBV код: порівняй кожен клас з FBV оригіналом
20. notes_project_cbv/hello_app/forms_views_laboratory.ipynb ← Forms & Views лабораторія: Trust Boundary, RequestFactory, Client
```

> Після цього шляху ти розумієш не просто "як писати QuerySet",
> а *чому* Django ORM працює саме так, як форми захищають від XSS/CSRF,
> як MVCC гарантує ізоляцію, чому deadlocks виникають і як їх уникати у production.
