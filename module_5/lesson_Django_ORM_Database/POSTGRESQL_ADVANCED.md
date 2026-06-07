# PostgreSQL Advanced — Архітектура, Docker та Production патерни

> Продовження після `DJANGO_ORM_DEEP.md`.
> Тут: внутрішня механіка PostgreSQL, чому він такий швидкий, як підключити через Docker,
> специфічні PostgreSQL поля та production-оптимізація.

---

> 🔬 **SQL інспекція в ноутбуку:**
> [`notes_project/hello_app/orm_laboratory.ipynb`](notes_project/hello_app/orm_laboratory.ipynb)
>
> | Концепція | Розділ ноутбука |
> |-----------|-----------------|
> | `queryset.explain(analyze=True)` — query plan | `## 11. 🔬 SQL Inspection` |
> | `connection.queries` — логування SQL | `## 11. 🔬 SQL Inspection` |
> | Raw SQL через `cursor.execute()` | `## 14. 🧪 Raw SQL` |



> **🧠 Ментальна модель:** PostgreSQL — не просто "місце для збереження". Це складна клієнт-серверна система з багатопроцесною архітектурою, власним менеджером пам'яті (Shared Buffers), механізмом ізоляції (MVCC) та журналом відмовостійкості (WAL). Розуміння цього = розуміння чому деякі запити швидкі, а деякі ні.
>
> **📚 Чому це важливо для Django-розробника:** Коли ти пишеш `Note.objects.filter(user=user)` — Django відправляє SQL в PostgreSQL, PostgreSQL вирішує де шукати дані (диск чи пам'ять, індекс чи sequential scan), виконує та повертає результат. Розуміючи цей процес — ти знаєш де bottleneck і як його усунути.
>
> **🌐 Практична цінність:** Кожен Django девелопер рано чи пізно стикається з "чому моя сторінка завантажується 5 секунд?" Відповідь завжди в PostgreSQL: немає індексу, N+1 запити, sequential scan на великій таблиці. `EXPLAIN ANALYZE` + знання архітектури = діагноз за 5 хвилин.
>
> **❌ Типова помилка:** Думати що PostgreSQL = "просто сховище". Насправді PostgreSQL — потужний сервер з планувальником запитів, кешем, транзакційним менеджером. Правильна конфігурація може дати 10-100x приріст продуктивності без зміни коду.

---

## 1. PostgreSQL vs SQLite — чому змінюємо на production

---
> **🧠 Ментальна модель:** SQLite — це "файл-база". Весь доступ через один файловий дескриптор. В один момент тільки ОДИН процес може писати. PostgreSQL — окремий сервер-процес. Сотні клієнтів одночасно → кожен отримує свій backend процес → MVCC забезпечує ізоляцію.
>
> **📚 Реальний сценарій:** Gunicorn з 4 воркерами → 4 паралельних Django запити → 4 одночасних INSERT. В SQLite: перший пише, три чекають. В PostgreSQL: всі 4 пишуть незалежно без блокування (через MVCC).
>
> **❌ Типова помилка:** Деплоїти production з SQLite. Django навіть документує: "SQLite is not suitable for production". Для реального трафіку (50+ concurrent users) — SQLite = bottleneck.
---

```
SQLite (Serverless):
  Django Process A ─────────────────┐
  Django Process B ─────────────────┤ → [db.sqlite3 file] ← ОДИН файл
  Django Process C ─────────────────┘   (write lock на весь файл)

  Проблема: Process A пише → B і C ЧЕКАЮТЬ

PostgreSQL (Client-Server):
  Django + psycopg2 ──TCP──► [postmaster :5432]
                                 │  ─ fork()  ─► [backend process 1] ─► [Shared Buffers]
                                 │  ─ fork()  ─► [backend process 2] ─► [Shared Buffers]
                                 │  ─ fork()  ─► [backend process 3] ─► [Shared Buffers]

  Всі три backend processes паралельно, кожен зі своєю транзакцією (MVCC).
```

| Характеристика | SQLite | PostgreSQL |
|----------------|--------|------------|
| **Архітектура** | Serverless, один файл | Client-server, окремий daemon |
| **Concurrent writes** | Database-level lock | MVCC: тисячі паралельних |
| **Розмір БД** | До ~1 TB практично | Необмежено (навіть петабайти) |
| **JSON/Arrays** | Базово | Повна підтримка + GIN індекси |
| **Full-text search** | Обмежено | GIN + tsvector, trigram |
| **Транзакції DDL** | Обмежено | Повна підтримка |
| **Підключення** | Direct file | TCP socket (або Unix socket) |
| **Для production** | ❌ Ніколи | ✅ Завжди |

---

## 2. PostgreSQL Process Model — як сервер обробляє запити

---
> **🧠 Ментальна модель:** Коли Django підключається до PostgreSQL — postmaster daemon fork()-ує новий процес спеціально для цього підключення. Цей backend process обслуговує ONE connection поки вона активна. Shared Buffers — це спільна пам'ять між усіма backend процесами: кеш даних.
>
> **📚 Чому fork() а не threads:** PostgreSQL використовує процеси (не threads) для ізоляції. Якщо backend process падає — він не вбиває весь сервер. Shared Buffers — спільна пам'ять (не копії): всі процеси бачать один і той самий кеш.
>
> **🌐 CONN_MAX_AGE в Django:** Кожен новий Python процес → нове підключення до PostgreSQL → fork() на боці PostgreSQL. Це дорого (10-100ms). `CONN_MAX_AGE=60` → тримати підключення між HTTP запитами → не vitko fork() щоразу → 5-10x менше overhead на DB connections.
>
> **❌ Типова помилка:** `CONN_MAX_AGE=None` (persistent) без PgBouncer. При 100 Gunicorn воркерах = 100 постійних підключень до PostgreSQL. PostgreSQL тримає 100 backend процесів. При `max_connections=100` → 101-й клієнт отримує "too many connections" помилку.
---

```
                ┌─────────────────────────────────────────────────────────┐
                │                 PostgreSQL Server                        │
                │                                                           │
  Django ────► │ Postmaster (порт 5432)                                   │
  psycopg2     │   │                                                        │
               │   ├─ fork() ──► Backend Process 1 (твій запит)           │
               │   │              │  ← Query Parser                        │
               │   │              │  ← Query Planner & Optimizer            │
               │   │              │  ← Execution Engine                    │
               │   │              │                                         │
               │   │              └──► Shared Buffers (8GB RAM кеш)       │
               │   │                     │                                  │
               │   │              WAL Writer ──► WAL Log (диск)           │
               │   │              Checkpointer ──► Data Files (диск)      │
               │   │                                                        │
               │   ├─ fork() ──► Backend Process 2 (інший клієнт)         │
               │   └─ fork() ──► Backend Process 3 (ще один)              │
               └─────────────────────────────────────────────────────────┘
```

---

## 3. MVCC — Multi-Version Concurrency Control

---
> **🧠 Ментальна модель:** Уяви що кожен рядок у таблиці має "версії". Коли ти починаєш транзакцію — ти бачиш snapshot стану БД на момент початку. Інші транзакції можуть паралельно змінювати ті самі рядки — ти їх не бачиш поки вони не закоммітили, і вони не бачать твоїх змін. Це як Google Docs: кілька людей редагують одночасно без конфліктів.
>
> **📚 Як PostgreSQL це реалізує:** Кожен рядок зберігає `xmin` (яка транзакція створила) та `xmax` (яка транзакція видалила або замінила). При SELECT PostgreSQL бачить тільки рядки де `xmin <= current_transaction` та `xmax` або NULL (не видалений) або `xmax > current_transaction` (видалений пізніше ніж твоя транзакція почалась).
>
> **🌐 Що це дає Django:** `READ COMMITTED` (за замовчуванням) — кожен запит в транзакції бачить свіжі закомічені дані. Жодного "dirty read" (читання незакомічених змін). Паралельні транзакції не блокують одна одну при читанні.
>
> **❌ Типова помилка:** Думати що PostgreSQL "блокує таблицю" при кожному SELECT. **Ні.** Читачі не блокують письменників, письменники не блокують читачів (MVCC). Блокування виникає тільки при `SELECT FOR UPDATE` або при конкурентних записах в один і той самий рядок.
---

```
MVCC — туплів версіонування:

таблиця notes_note (внутрішнє представлення):
┌─────┬───────────┬──────────┬───────────┬──────────────┐
│ id  │ title     │ xmin     │ xmax      │ Кому видимий │
├─────┼───────────┼──────────┼───────────┼──────────────┤
│  42 │ "Django"  │ txid=100 │ NULL      │ всім ≥ 100   │ ← активна версія
│  42 │ "Django!" │ txid=200 │ NULL      │ всім ≥ 200   │ ← нова версія (UPDATE)
│  42 │ "Django"  │ txid=100 │ txid=200  │ транзакціям  │ ← стара (xmax=200: видалена)
│     │           │          │           │  < 200       │
└─────┴───────────┴──────────┴───────────┴──────────────┘

Транзакція txid=150 (почалась між 100 і 200):
  → бачить рядок з xmin=100, xmax=NULL (стара версія)
  → НЕ бачить рядок з xmin=200 (ще не існував коли 150 почалась)

Транзакція txid=250 (почалась після 200):
  → бачить рядок з xmin=200 (нова версія)
  → стара версія (xmax=200) для неї "видалена"

VACUUM прибирає "мертві" тупліі (xmax != NULL і недоступні жодній активній транзакції)
```

---

## 4. WAL — Write-Ahead Logging

---
> **🧠 Ментальна модель:** WAL — це "чорний ящик літака" для бази даних. Перш ніж зробити будь-яку зміну в даних — PostgreSQL записує намір у WAL журнал. Якщо сервер впаде — при рестарті PostgreSQL читає WAL і відновлює всі підтверджені транзакції. Ніяких втрат даних після COMMIT.
>
> **📚 Чому "Write-Ahead":** "Write-Ahead" = "запиши журнал ПЕРЕД тим як змінити дані". Якщо питання: що важливіше зберегти — журнал або дані? Журнал! Журнал → можна відновити дані. Дані без журналу → не знаємо до якого стану відновлювати.
>
> **🌐 WAL і продуктивність:** PostgreSQL пише зміни спочатку в Shared Buffers (RAM) → потім WAL на диск. Checkpointer синхронізує dirty pages з диску. `synchronous_commit=on` (за замовчуванням) → COMMIT чекає запис WAL на диск. `synchronous_commit=off` → швидше але ризик втрати останніх транзакцій при збої. Для некритичних даних (логи, аналітика) — `off` може бути прийнятним.
>
> **❌ Типова помилка:** Запускати PostgreSQL з `fsync=off` "для прискорення розробки". Це ок для локальної розробки, але на production = гарантована корупція даних при збої. Ніколи на production.
---

```
Шлях даних від COMMIT до диску:

1. Django: session.commit()
           │
2. SQL: COMMIT
           │
3. PostgreSQL WAL Writer:
   ┌─ WAL Buffer (в RAM) ─────────────────────────────────┐
   │  LSN 0/1234ABC: BEGIN txid=200                        │
   │  LSN 0/1234DEF: INSERT notes_note (id=42, title=...)  │
   │  LSN 0/1235000: COMMIT txid=200                       │
   └──────────────────────────────────────────────────────┘
           │ fsync() — flush до диску
           ▼
   WAL файл: pg_wal/000000010000000000000001
   (Тепер навіть після збою — транзакцію можна відновити!)
           │
4. COMMIT повертається клієнту (Django отримує OK)
           │
5. Пізніше: Checkpointer записує dirty pages з Shared Buffers у Data Files
   (асинхронно, не затримує клієнта)
```

---

## 5. Підключення Django до PostgreSQL через Docker

---
> **🧠 Ментальна модель:** Docker для PostgreSQL — це "віртуальний сервер" що запускається за 5 секунд. Контейнер PostgreSQL = окремий network namespace → Django підключається через TCP на `localhost:5432` як ніби це справжній сервер.
>
> **📚 Чому Docker а не встановлювати PostgreSQL:** Версіонування (легко перемкнутись на postgres:15 або postgres:16), ізоляція (не засмічує систему), однакове середовище у всієї команди, легко очистити (`docker-compose down -v`).
>
> **🌐 docker-compose.yml для development:** `volumes: postgres_data` зберігає дані між рестартами контейнера. Без volume — перезапуск = нова порожня БД. `healthcheck` — Django не підключається поки PostgreSQL не готовий приймати з'єднання.
>
> **❌ Типова помилка:** Ставити порожні паролі або `POSTGRES_HOST_AUTH_METHOD=trust` в docker-compose. Для локальної розробки — ок. Але якщо порт 5432 відкритий назовні (наприклад, port forwarding в хмарі) — хтось може підключитись без пароля.
---

### Повний docker-compose.yml для розробки:

```yaml
# docker-compose.yml

version: '3.9'

services:

  # ── PostgreSQL ────────────────────────────────────────────────────────────
  db:
    image: postgres:16-alpine          # alpine = мінімальний образ (~25MB)
    restart: unless-stopped
    environment:
      POSTGRES_DB: notes_db            # назва бази даних
      POSTGRES_USER: notes_user        # ім'я користувача
      POSTGRES_PASSWORD: notes_pass    # пароль (у .env файлі на production!)
    volumes:
      - postgres_data:/var/lib/postgresql/data  # дані зберігаються між рестартами
    ports:
      - "5432:5432"                    # host:container
    healthcheck:
      # Django (app) не запуститься поки PostgreSQL не готовий
      test: ["CMD-SHELL", "pg_isready -U notes_user -d notes_db"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  # ── Django App (опційно) ──────────────────────────────────────────────────
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://notes_user:notes_pass@db:5432/notes_db
    depends_on:
      db:
        condition: service_healthy    # чекати поки db healthcheck = healthy
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"

volumes:
  postgres_data:     # named volume — дані зберігаються поза контейнером
```

```bash
# Команди для роботи:

# Запустити тільки PostgreSQL (для локальної розробки)
docker-compose up -d db

# Запустити весь стек
docker-compose up -d

# Перевірити що PostgreSQL запущений
docker-compose ps
docker-compose logs db

# Підключитись до psql консолі
docker-compose exec db psql -U notes_user -d notes_db

# Показати всі таблиці
docker-compose exec db psql -U notes_user -d notes_db -c "\dt hello_app*"

# Зупинити та зберегти дані
docker-compose stop

# Зупинити та ВИДАЛИТИ дані (повне очищення!)
docker-compose down -v
```

### Django settings.py для PostgreSQL:

```python
# settings.py

from decouple import config    # pip install python-decouple

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='notes_db'),
        'USER': config('DB_USER', default='notes_user'),
        'PASSWORD': config('DB_PASSWORD', default='notes_pass'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),

        # CONN_MAX_AGE: тримати з'єднання між HTTP запитами
        # None = persistent (не закривати ніколи)
        # 0 = завжди нове (за замовчуванням, неефективно)
        # 60 = тримати 60 секунд (рекомендовано для Gunicorn)
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=60, cast=int),

        # OPTIONS для production:
        'OPTIONS': {
            # 'connect_timeout': 5,      # таймаут з'єднання
            # 'options': '-c search_path=myschema',  # PostgreSQL search_path
        },
    }
}
```

```bash
# .env файл (НІКОЛИ не комітити в git!)
DB_NAME=notes_db
DB_USER=notes_user
DB_PASSWORD=notes_pass
DB_HOST=localhost
DB_PORT=5432
DB_CONN_MAX_AGE=60
```

```bash
# .gitignore
.env
db.sqlite3
*.pyc
__pycache__/
```

---

## 6. psycopg2 та PgBouncer

---
> **🧠 Ментальна модель:** psycopg2 — це "телефонна лінія" між Python і PostgreSQL. PgBouncer — це "АТС": замість того щоб кожен Django воркер тримав пряму лінію до PostgreSQL, вони підключаються через ATC яка переключає між обмеженою кількістю реальних ліній.
>
> **📚 Проблема без PgBouncer:** Gunicorn з 10 воркерами + 5 threads = 50 паралельних підключень. PostgreSQL fork()-ує 50 backend процесів. При 100 воркерах → 100 backend процесів → `max_connections=100` → 101-й отримає помилку. PgBouncer → 1000 Django підключень → 20 реальних з'єднань з PostgreSQL.
>
> **🌐 Режими PgBouncer:** Session pooling (1 з'єднання до PostgreSQL на Django session), Transaction pooling (1 реальне з'єднання з PostgreSQL на транзакцію — найефективніше), Statement pooling (найефективніше але не підтримує multi-statement transactions).
>
> **❌ Типова помилка:** Transaction pooling + `CONN_MAX_AGE` у Django. При Transaction pooling — кожна транзакція може йти через різне фізичне з'єднання. Persistent з'єднань з PostgreSQL тоді немає сенсу. З PgBouncer: `CONN_MAX_AGE=0`.
---

```
Без PgBouncer:
  Django w1 ──────────────────────────── TCP ──► PostgreSQL :5432
  Django w2 ──────────────────────────── TCP ──► PostgreSQL :5432
  Django w3 ──────────────────────────── TCP ──► PostgreSQL :5432
  ... (100 воркерів = 100 postgres backend processes)

З PgBouncer:
  Django w1 ──┐
  Django w2 ──┤── PgBouncer :6432 ──[ pool: 20 conns ]──► PostgreSQL :5432
  Django w3 ──┘  (100 Django з'єднань → 20 реальних)
```

```python
# settings.py з PgBouncer:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'notes_db',
        'USER': 'notes_user',
        'PASSWORD': 'notes_pass',
        'HOST': 'pgbouncer',  # хост PgBouncer, не PostgreSQL!
        'PORT': '6432',       # порт PgBouncer
        'CONN_MAX_AGE': 0,    # з PgBouncer persistent connections не потрібні
    }
}
```

---

## 7. PostgreSQL-специфічні поля Django

---
> **🧠 Ментальна модель:** PostgreSQL підтримує типи даних яких немає в SQLite або MySQL: масиви, JSONB, UUID, hstore, range types. Django надає поля для роботи з ними. Ці поля — тільки для PostgreSQL backend!
>
> **📚 JSONField vs окрема таблиця:** JSONField зберігає довільну структуру в одному стовпці. Коли використовувати: конфігурація, metadata, дані що часто змінюють структуру. Коли НЕ використовувати: дані по яких потрібні складні JOIN, часті оновлення окремих полів, строга схема.
>
> **🌐 GIN індекс для JSON і масивів:** Звичайний B-Tree індекс не може індексувати JSON або масив (багато значень в одному стовпці). GIN (Generalized Inverted Index) — індексує кожен елемент масиву або кожен ключ JSON. `GinIndex(fields=['metadata'])` → швидкий пошук по JSON ключах.
>
> **❌ Типова помилка:** Використовувати JSONField як "запасний" для непродуманої схеми. JSONField без GIN індексу + фільтрація `filter(metadata__key=val)` → sequential scan (повне сканування таблиці). Завжди додавай GIN індекс якщо фільтруєш по JSON.
---

### JSONField — структуровані дані в стовпці:

```python
from django.db import models

class Note(models.Model):
    # JSONField зберігає Python dict/list в PostgreSQL JSONB стовпці
    # JSONB = бінарний JSON → швидше ніж TEXT JSON
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Довільні метадані: word_count, reading_time, language тощо'
    )

# Заповнення:
note.metadata = {
    'word_count': 450,
    'reading_time_minutes': 3,
    'language': 'uk',
    'ai_tags': ['python', 'orm', 'database'],
    'last_spell_check': '2024-01-15'
}
note.save()

# Фільтрація по JSON полях:
Note.objects.filter(metadata__language='uk')
# WHERE metadata->>'language' = 'uk'

Note.objects.filter(metadata__word_count__gte=100)
# WHERE (metadata->>'word_count')::int >= 100

Note.objects.filter(metadata__ai_tags__contains=['python'])
# WHERE metadata->'ai_tags' @> '["python"]'

# Анотація з JSON полем:
from django.db.models import F
Note.objects.annotate(
    word_count=F('metadata__word_count')
).order_by('-word_count')
```

### ArrayField — масиви у PostgreSQL:

```python
from django.contrib.postgres.fields import ArrayField

class Note(models.Model):
    # Масив рядків — альтернатива M:N для простих тегів
    quick_labels = ArrayField(
        base_field=models.CharField(max_length=50),
        blank=True,
        default=list,
        help_text='Швидкі мітки (no FK, no junction table)'
    )

    # Масив IntegerField
    related_note_ids = ArrayField(
        base_field=models.IntegerField(),
        blank=True,
        default=list,
    )

# SQL: quick_labels TEXT[] DEFAULT '{}'

# Фільтрація:
Note.objects.filter(quick_labels__contains=['python'])
# WHERE quick_labels @> ARRAY['python']  (масив містить 'python')

Note.objects.filter(quick_labels__overlap=['python', 'django'])
# WHERE quick_labels && ARRAY['python', 'django']  (є хоча б один збіг)

Note.objects.filter(quick_labels__len=3)
# WHERE array_length(quick_labels, 1) = 3  (масив з 3 елементів)
```

### UniqueConstraint та CheckConstraint:

```python
class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=200)
    views_count = models.PositiveIntegerField(default=0)
    priority = models.PositiveSmallIntegerField(default=1)

    class Meta:
        constraints = [
            # СКЛАДЕНИЙ UNIQUE: slug унікальний в межах одного user
            # (alice може мати /notes/python/, bob теж може, але alice не може двічі)
            models.UniqueConstraint(
                fields=['user', 'slug'],
                name='unique_note_slug_per_user'
            ),

            # CHECK: views_count >= 0 (не може бути від'ємним)
            # Перевіряється навіть при прямому SQL INSERT (не тільки через Django)
            models.CheckConstraint(
                check=models.Q(views_count__gte=0),
                name='note_views_count_non_negative'
            ),

            # CHECK: priority від 1 до 4
            models.CheckConstraint(
                check=models.Q(priority__gte=1) & models.Q(priority__lte=4),
                name='note_priority_valid_range'
            ),
        ]
```

```sql
-- Що генерується в SQL:
ALTER TABLE notes_note
  ADD CONSTRAINT unique_note_slug_per_user UNIQUE (user_id, slug),
  ADD CONSTRAINT note_views_count_non_negative CHECK (views_count >= 0),
  ADD CONSTRAINT note_priority_valid_range CHECK (priority >= 1 AND priority <= 4);
```

---

## 8. EXPLAIN ANALYZE — діагностика запитів

---
> **🧠 Ментальна модель:** `EXPLAIN ANALYZE` — це MRI-скан для твого SQL запиту. Він показує: який план обрав Planner, скільки часу зайняв кожен крок, скільки рядків було оброблено. З цим — ти бачиш де bottleneck: немає індексу, занадто широкий JOIN, неоптимальне сортування.
>
> **📚 EXPLAIN vs EXPLAIN ANALYZE:** `EXPLAIN` — показує план без виконання (швидко). `EXPLAIN ANALYZE` — виконує запит і показує реальні метрики (повільно, але точно). На production завжди тестуй на копії, `EXPLAIN ANALYZE` реально виконує запит!
>
> **🌐 Як читати план:** `Seq Scan` = читає всю таблицю O(N). `Index Scan` = використовує B-Tree O(log N). `Index Only Scan` = покриваючий індекс (не читає heap). `Hash Join` = ефективний JOIN для великих таблиць. `Nested Loop Join` = ефективний для малих таблиць з індексом.
>
> **❌ Типова помилка:** Ігнорувати `Seq Scan` на великих таблицях. `Seq Scan on notes_note (cost=0.00..5000.00 rows=100000)` = читання мільйона рядків. Потрібен індекс на поле в WHERE clause.
---

```python
# Django: qs.explain(analyze=True) — відправляє EXPLAIN ANALYZE до PostgreSQL
from hello_app.models import Note

qs = Note.objects.filter(user_id=5, is_archived=False).order_by('-updated_at')
print(qs.explain(analyze=True))
```

```sql
-- Типовий вивід EXPLAIN ANALYZE:

-- ХОРОШИЙ запит (є індекс):
Index Scan using note_user_updated_idx on notes_note  (cost=0.29..8.31 rows=1 width=100)
                                                       (actual time=0.023..0.025 rows=1 loops=1)
  Index Cond: ((user_id = 5) AND (is_archived = false))
Planning Time: 0.150 ms
Execution Time: 0.045 ms   ← мілісекунди!

-- ПОГАНИЙ запит (Seq Scan без індексу):
Seq Scan on notes_note  (cost=0.00..25000.00 rows=500000 width=100)
                         (actual time=0.050..1500.000 rows=150 loops=1)
  Filter: ((user_id = 5) AND (is_archived = false))
  Rows Removed by Filter: 499850    ← 500K рядків проскановано щоб знайти 150!
Planning Time: 0.250 ms
Execution Time: 1500.000 ms   ← 1.5 секунди!
```

```sql
-- Читаємо план:
-- cost=0.00..8.31      → кошт: estimated start..total cost (в PostgreSQL units)
-- rows=1               → estimated кількість рядків
-- actual time=0.023..0.025 → реальний час: first row..last row (мс)
-- rows=1 loops=1       → реально повернуто рядків, кількість ітерацій

-- Операції:
-- Seq Scan            → ❌ повне сканування таблиці O(N)
-- Index Scan          → ✅ B-Tree індекс O(log N)
-- Index Only Scan     → ✅✅ покриваючий індекс (без heap читання)
-- Bitmap Index Scan   → ✅ для великої кількості рядків по індексу
-- Hash Join           → JOIN через hash table (ефективно для великих таблиць)
-- Nested Loop         → JOIN через цикл (ефективно коли є індекс на внутрішній таблиці)
-- Sort                → ORDER BY без індексу (може бути повільно)
```

---

## 9. CONN_MAX_AGE та Connection Pooling

---
> **🧠 Ментальна модель:** Підключення до PostgreSQL — дорога операція: TCP handshake, аутентифікація, fork() backend процесу — 5-50ms. `CONN_MAX_AGE` каже Django: "тримай підключення між HTTP запитами замість того щоб відкривати/закривати кожен раз".
>
> **📚 Як CONN_MAX_AGE працює з Gunicorn:** Кожен Gunicorn воркер = окремий процес = окреме підключення. При `CONN_MAX_AGE=60` — воркер тримає підключення 60 секунд після останнього запиту. При наступному HTTP запиті до цього воркера — підключення вже готове.
>
> **🌐 Правило для production:** Gunicorn + `CONN_MAX_AGE=60` + без PgBouncer: кількість підключень = кількість воркерів * потоків. 10 воркерів * 2 threads = 20 підключень max. Якщо `max_connections=100` — безпечно. Якщо воркерів більше — або зменшуй `CONN_MAX_AGE` або додавай PgBouncer.
>
> **❌ Типова помилка:** `CONN_MAX_AGE=None` (infinite). Підключення ніколи не закривається. При деплої нової версії старі підключення залишаються. З часом PostgreSQL накопичує "зависшие" підключення. Краще `CONN_MAX_AGE=60` або `300`.
---

```
З'єднання без CONN_MAX_AGE (CONN_MAX_AGE=0):

HTTP Request 1 → [open connection] → [SQL] → [close connection]   +50ms overhead
HTTP Request 2 → [open connection] → [SQL] → [close connection]   +50ms overhead
HTTP Request 3 → [open connection] → [SQL] → [close connection]   +50ms overhead

З'єднання з CONN_MAX_AGE=60:

HTTP Request 1 → [open connection] → [SQL] → [keep open]   +50ms (перший раз)
HTTP Request 2 → [reuse connection] → [SQL] → [keep open]  +0ms!
HTTP Request 3 → [reuse connection] → [SQL] → [keep open]  +0ms!
... (через 60 секунд без запитів → закривається)
```

---

## 10. Production стек

```
Internet
    │
    ▼
[nginx] (порт 443, SSL termination, static files)
    │
    ▼
[Gunicorn] (4-8 воркерів, Unix socket)
    │
    │  Django WSGI app
    │  CONN_MAX_AGE=60
    ▼
[PgBouncer] (порт 6432, transaction pooling)
    │
    │  pool_size=20
    ▼
[PostgreSQL 16] (порт 5432)
    │
    ├── Shared Buffers: 25% RAM
    ├── WAL: pg_wal/
    └── Data Files: /var/lib/postgresql/data/
```

```python
# settings/production.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='pgbouncer'),  # pgbouncer хост
        'PORT': config('DB_PORT', default='6432'),        # pgbouncer порт
        'CONN_MAX_AGE': 0,        # з PgBouncer не потрібен persistent conn
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c lock_timeout=3s',   # тайм-аут для lock-ів
        },
    }
}

# Логування повільних запитів у розробці
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',    # показує всі SQL запити
        },
    },
}
```

---

## Prediction Exercises

### Exercise 1: З'єднання

```python
# settings.py:
DATABASES = {'default': {'CONN_MAX_AGE': 0, ...}}
# Gunicorn: 4 воркери, кожен обробляє 100 запитів на хвилину
```

**Питання:** Скільки підключень до PostgreSQL відкривається за хвилину?

> Відповідь: **400 підключень** (100 req/хвилину × 4 воркери). Кожен запит = open + close. З `CONN_MAX_AGE=60` → **4 підключення** (по одному на воркер, тримаються 60 секунд).

### Exercise 2: MVCC

```
Транзакція T1 починається о 10:00:00
Транзакція T2 вставляє новий рядок і COMMIT о 10:00:01
T1 виконує SELECT о 10:00:02
```

**Питання:** Чи бачить T1 новий рядок T2?

> Відповідь (залежить від isolation level):
> - `READ COMMITTED` (за замовчуванням в PostgreSQL) → **ТАК** бачить. Кожен запит в T1 бачить свіжі закомічені дані.
> - `REPEATABLE READ` або `SERIALIZABLE` → **НЕ бачить**. Snapshot T1 зафіксований на момент START TRANSACTION.

---

## Питання для самоперевірки

1. Чому PostgreSQL не блокує таблицю при кожному SELECT (MVCC)?
2. Що таке WAL і навіщо він потрібен?
3. Що таке CONN_MAX_AGE і які значення рекомендовані?
4. Коли використовувати JSONField а коли окрему таблицю?
5. Чому потрібен GIN індекс для JSONField?
6. Що показує `Seq Scan` в EXPLAIN ANALYZE і коли це проблема?
7. Навіщо PgBouncer і коли він потрібен?
8. Яка різниця між `EXPLAIN` та `EXPLAIN ANALYZE`?
9. Що означає `xmin` і `xmax` у внутрішньому представленні PostgreSQL?
10. Чому `POSTGRES_HOST_AUTH_METHOD=trust` небезпечно на production?
