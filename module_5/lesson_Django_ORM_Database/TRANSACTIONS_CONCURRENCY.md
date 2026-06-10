# Транзакції, Блокування та Конкурентність в Django + PostgreSQL

> Цей документ для backend-розробників що хочуть розуміти
> як підтримується цілісність даних у конкурентних системах.
> Тут: MVCC deepdive, select_for_update(), race conditions, deadlocks та їх вирішення.

---

> 🔬 **Живі приклади транзакцій:**
> [`notes_project/hello_app/orm_laboratory.ipynb`](notes_project/hello_app/orm_laboratory.ipynb)
>
> | Концепція | Розділ ноутбука |
> |-----------|-----------------|
> | `transaction.atomic()` — BEGIN / COMMIT / ROLLBACK | `## 13. 🔒 Транзакції` |
> | `F()` expressions — race-condition safe | `## 6. 📐 F() Expressions` |
> | `select_for_update()` — row locking | `## 13. 🔒 Транзакції` |
> | Duplicate query detection | `## 11. 🔬 SQL Inspection` — `connection.queries` |



> **🧠 Ментальна модель:** Сервер обробляє тисячі запитів одночасно. Кожен запит може читати і змінювати дані. Без правильного управління конкурентністю — дані псуються: рахунки підвищуються неправильно, товари продаються двічі, важливі операції виконуються частково. Транзакції, MVCC і блокування — це механізми що запобігають цьому хаосу.
>
> **📚 Чому це важливо для звичайного Django-проекту:** Навіть проста сторінка перегляду товарів може стати проблемою при 1000 concurrent покупців. `note.views_count += 1` в циклі при 1000 паралельних запитах = race condition = зникнення 999 переглядів. Розуміти транзакції = писати надійний код.
>
> **🌐 Де в Django:** `transaction.atomic()`, `select_for_update()`, `F()`, `on_commit()` — це Python API для управління PostgreSQL транзакціями і блокуваннями.
>
> **❌ Типова помилка:** Думати що `save()` вже "атомарний". `Note.objects.create()` + `NoteRevision.objects.create()` — це ДВА окремих INSERT, дві окремі транзакції. Якщо між ними exception → Note збережена, Revision — ні → corrupted state. Потрібен `transaction.atomic()`.

---

## 1. MVCC в деталях

---
> **🧠 Ментальна модель:** MVCC = Multi-Version Concurrency Control. Уяви Google Docs: кілька людей відкрили документ одночасно. Кожен бачить версію на момент відкриття. Хтось зберіг зміни — інші ще не бачать (або бачать залежно від refresh). PostgreSQL робить те саме: кожна транзакція бачить snapshot стану БД.
>
> **📚 Читачі не блокують письменників:** Це ключова відмінність PostgreSQL від MySQL InnoDB (де читачі теж можуть блокуватись). В PostgreSQL `SELECT` ніколи не блокує `INSERT/UPDATE/DELETE` і навпаки. Вони бачать різні версії рядків (MVCC).
>
> **🌐 Isolation levels:** `READ COMMITTED` — кожен запит в транзакції бачить свіжі закомічені дані. `REPEATABLE READ` — snapshot фіксується на початку транзакції. `SERIALIZABLE` — транзакції виконуються ніби послідовно (найбезпечніше, найповільніше).
>
> **❌ Типова помилка:** Думати що `READ COMMITTED` дає "точний" результат при двох запитах в одній транзакції. `READ COMMITTED` = кожен запит бачить нові закомічені дані. Якщо хтось закомітив між твоїми двома SELECT — другий SELECT бачить нові дані. Для "frozen snapshot" → `REPEATABLE READ`.
---

```python
# Демонстрація MVCC та isolation levels:

from django.db import transaction, connection

# READ COMMITTED (за замовчуванням):
with transaction.atomic():
    count1 = Note.objects.filter(user=user).count()  # → 100
    # Інший процес: Note.objects.create(user=user, ...)
    count2 = Note.objects.filter(user=user).count()  # → 101 (бачить нову нотатку!)
    # READ COMMITTED: кожен SELECT бачить нові закомічені дані

# REPEATABLE READ:
with transaction.atomic():
    connection.cursor().execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
    count1 = Note.objects.filter(user=user).count()  # → 100
    # Інший процес: Note.objects.create(user=user, ...)
    count2 = Note.objects.filter(user=user).count()  # → 100 (snapshot frozen!)
    # REPEATABLE READ: snapshot зафіксований на початку транзакції
```

```
Ізоляційні рівні PostgreSQL:

Рівень            | Dirty Read | Non-Repeatable | Phantom Read
──────────────────┼────────────┼────────────────┼─────────────
READ UNCOMMITTED  | Можливо¹   | Можливо        | Можливо
READ COMMITTED    | ✅ Захист   | Можливо        | Можливо
REPEATABLE READ   | ✅ Захист   | ✅ Захист       | ✅ Захист²
SERIALIZABLE      | ✅ Захист   | ✅ Захист       | ✅ Захист

¹ PostgreSQL завжди використовує READ COMMITTED як мінімум
² PostgreSQL REPEATABLE READ захищає від phantoms (відміна від SQL стандарту)
```

---

## 2. transaction.atomic() — повна механіка

---
> **🧠 Ментальна модель:** `with transaction.atomic():` — це "бульбашка безпеки". Все що відбувається всередині — або виконується ПОВНІСТЮ, або скасовується ПОВНІСТЮ. Немає "половини операції" або "частково збережених даних". Банківський переказ: знімаємо з A, додаємо до B — або обидві операції, або жодна.
>
> **📚 SQL lifecycle:** `transaction.atomic()` → SQL `BEGIN` (якщо ще не в транзакції) або `SAVEPOINT` (якщо вже в транзакції). При успіху → `COMMIT` або `RELEASE SAVEPOINT`. При exception → `ROLLBACK` або `ROLLBACK TO SAVEPOINT`.
>
> **🌐 Вкладені atomic():** Django реалізує їх через **Savepoints**. Зовнішній `atomic()` = `BEGIN`. Внутрішній `atomic()` = `SAVEPOINT sp_1`. Якщо внутрішній кидає exception → `ROLLBACK TO SAVEPOINT sp_1` (тільки внутрішній скасовується). Зовнішній продовжує.
>
> **❌ КРИТИЧНА помилка:** `try/except` всередині `atomic()`. Якщо перехопити exception всередині транзакції — Django не знає що транзакція зламана. Транзакція в "aborted" стані. Наступний `Note.objects.create()` кине `TransactionManagementError: You can't execute queries until the end of the 'atomic' block.` Catch ЗОВНІ atomic, ніколи всередині!
---

```python
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


# ✅ ПРАВИЛЬНО: atomic() → всі операції або всі виконуються, або жодна
def transfer_note(note_id, from_notebook, to_notebook, user):
    """
    Перемістити нотатку між записниками.
    Атомарна операція: або обидва UPDATE виконуються, або жоден.
    """
    with transaction.atomic():
        note = Note.objects.select_for_update().get(id=note_id, user=user)
        note.notebook = to_notebook
        note.save(update_fields=['notebook'])
        
        # Логуємо переміщення (якщо це впаде → note теж відкотиться)
        NoteActivity.objects.create(
            note=note,
            action='moved',
            from_notebook=from_notebook,
            to_notebook=to_notebook,
        )
    # COMMIT тільки тут — після успішного виходу з блоку


# ❌ НЕПРАВИЛЬНО: catch всередині atomic()
def wrong_create_note(title, user):
    with transaction.atomic():
        note = Note.objects.create(title=title, user=user)
        try:
            # Якщо це кине exception — транзакція "зламана"!
            send_notification(user)  # припустимо, тут exception
        except Exception:
            pass  # ← КАТАСТРОФА!
            # Django тепер не знає: транзакція в aborted стані
            # Наступна операція: TransactionManagementError!
    # Якщо дійшли сюди — тільки якщо exception НЕ відбувся
    # (але тоді pass спрацював і ми таки дійшли → TransactionManagementError!)


# ✅ ПРАВИЛЬНО: catch ЗОВНІ atomic()
def correct_create_note(title, user):
    try:
        with transaction.atomic():
            note = Note.objects.create(title=title, user=user)
            send_notification(user)  # якщо впаде → ROLLBACK Note
    except Exception as e:
        logger.error(f"create_note failed: {e}")
        return None
    return note  # дійшли сюди тільки якщо все ОК


# Вкладені atomic() — Savepoints:
def create_note_with_optional_revision(title, content, user):
    with transaction.atomic():              # BEGIN
        note = Note.objects.create(
            title=title, content=content, user=user
        )                                    # INSERT note

        try:
            with transaction.atomic():      # SAVEPOINT sp_1
                NoteRevision.objects.create(
                    note=note, content=content, version=1
                )                           # INSERT revision
        except Exception:
            pass
            # ROLLBACK TO SAVEPOINT sp_1 (тільки revision відкотилась)
            # Note залишається!

    # COMMIT — note збережена, revision — можливо ні (залежно від exception)
```

---

## 3. Savepoints — вкладені транзакції

---
> **🧠 Ментальна модель:** Savepoint — це "контрольна точка" всередині транзакції. Як в грі: `SAVEPOINT` = зберегти прогрес на рівні. Якщо помер → `ROLLBACK TO SAVEPOINT` = повернутись до контрольної точки, не починаючи гру спочатку.
>
> **📚 Django і Savepoints:** Кожен вкладений `with transaction.atomic():` автоматично стає Savepoint якщо ми вже в транзакції. Ти не пишеш SQL напряму — Django сам вирішує: `BEGIN` або `SAVEPOINT`.
>
> **🌐 Де це корисно:** Операції з "опціональними" частинами. Основна операція обов'язкова. Додаткова — бажана але не критична. Якщо додаткова кидає exception → відкати тільки вона. Основна зберігається.
---

```
Sequence Diagram — Savepoints:

Django                  PostgreSQL
  │                         │
  │  with transaction.atomic():
  │ ────BEGIN──────────────► │
  │                          │
  │  Note.objects.create()  │
  │ ────INSERT note─────────► │
  │                          │
  │  with transaction.atomic():  (вкладений!)
  │ ────SAVEPOINT sp_1──────► │
  │                          │
  │  NoteRevision.create()   │
  │ ────INSERT revision─────► │
  │                          │
  │  (якщо exception):       │
  │ ────ROLLBACK TO sp_1────► │  (тільки revision відкатилась)
  │  (якщо успіх):           │
  │ ────RELEASE sp_1────────► │  (savepoint знятий)
  │                          │
  │ ────COMMIT───────────────► │  (note збережена)
```

---

## 4. select_for_update() — рядкові блокування

---
> **🧠 Ментальна модель:** `select_for_update()` — це "зайнято" табличка на ресурсі. Коли T1 виконує `SELECT FOR UPDATE` — PostgreSQL ставить lock на рядок. T2 намагається виконати `SELECT FOR UPDATE` на той самий рядок → чекає поки T1 зробить COMMIT або ROLLBACK.
>
> **📚 Навіщо потрібно:** Без lock: T1 і T2 обидва прочитали `stock=1`, обидва вирахували `1-1=0`, обидва записали `stock=0`. Товар продали двічі. З `SELECT FOR UPDATE`: T1 заблокував рядок, T2 чекає. T1 записав `stock=0` і COMMIT → T2 читає `stock=0` → не продає (stock пустий).
>
> **🌐 Варіанти:** `nowait=True` — кидає помилку замість очікування. `skip_locked=True` — пропускає заблоковані рядки (для task queue). `of=('table',)` — блокувати тільки конкретну таблицю при JOIN.
>
> **❌ Типова помилка:** `select_for_update()` БЕЗ `transaction.atomic()`. Lock знімається тільки при COMMIT або ROLLBACK. Без atomic Django в autocommit режимі — кожен запит = свій COMMIT → lock знімається одразу після SELECT. Сенс від lock зникає.
---

```python
from django.db import transaction

# ЗАВЖДИ в transaction.atomic()!

# Базовий select_for_update:
def book_ticket(event_id, user):
    """Купівля квитка — класичний race condition сценарій."""
    with transaction.atomic():
        # SELECT ... FOR UPDATE → блокує рядок event
        event = Event.objects.select_for_update().get(id=event_id)
        
        if event.available_tickets <= 0:
            raise ValueError("Квитки закінчились")
        
        # Тут тільки ОДИН process виконує цей код одночасно (lock!)
        event.available_tickets -= 1
        event.save(update_fields=['available_tickets'])
        
        Ticket.objects.create(event=event, user=user)
    # COMMIT → lock знімається → наступний process може читати


# nowait=True — кинути помилку якщо рядок вже заблокований
def try_process_note(note_id, user):
    """Якщо нотатка вже обробляється — відмовити (не чекати)."""
    try:
        with transaction.atomic():
            note = Note.objects.select_for_update(nowait=True).get(
                id=note_id, user=user
            )
            # Швидка операція без очікування
            note.status = 'processing'
            note.save(update_fields=['status'])
    except Exception as e:
        if 'could not obtain lock' in str(e):
            return {'error': 'Нотатка вже обробляється, спробуйте пізніше'}
        raise


# skip_locked=True — для task queue (пропустити зайняті рядки)
def process_pending_tasks():
    """
    Celery-подібний pattern для обробки черги.
    skip_locked=True: якщо рядок заблокований іншим worker-ом → пропустити.
    Не чекати (це уповільнить queue).
    """
    with transaction.atomic():
        tasks = Task.objects.select_for_update(
            skip_locked=True
        ).filter(status='pending')[:10]  # беремо 10 за раз
        
        for task in tasks:
            task.status = 'processing'
            task.save(update_fields=['status'])
        
        return list(tasks)
```

---

## 5. Race Condition — Lost Update

---
> **🧠 Ментальна модель:** Race condition = "гонка" між двома процесами. Обидва читають одне значення, обидва "виграють" змагання першим записати → другий перезаписує перший. "Втрачене оновлення" (Lost Update).
>
> **📚 Класичний приклад:** Лічильник переглядів. 1000 паралельних запитів, всі читають `views=100`, всі записують `views=101`. Замість `views=1100` маємо `views=101`. 999 переглядів "загублено".
>
> **🌐 Рішення F():** `Note.objects.filter(pk=42).update(views=F('views')+1)` → `UPDATE notes SET views = views + 1 WHERE id=42` → атомарна операція на рівні PostgreSQL, race condition неможливий.
>
> **❌ Типова помилка:** `note = Note.objects.get(pk=42); note.views += 1; note.save()` — classic lost update pattern. Завжди використовуй `F()` для лічильників.
---

```
Race Condition — Lost Update (без F()):

Час   | Process A               | Process B
─────────────────────────────────────────────
T=1   | SELECT views=100        |
T=2   |                         | SELECT views=100
T=3   | views = 100 + 1 = 101   |
T=4   |                         | views = 100 + 1 = 101
T=5   | UPDATE views=101        |
T=6   |                         | UPDATE views=101  ← перезаписав A!
Результат: views=101 замість 102. При 1000 процесів → views=101 замість 1100!
```

```python
from django.db.models import F

# ❌ RACE CONDITION (при конкурентних запитах):
def increment_views_UNSAFE(note_id):
    note = Note.objects.get(id=note_id)  # SELECT: reads views=100
    note.views_count += 1                # Python: 100+1=101
    note.save()                          # UPDATE: sets views=101
    # 2 операції, race condition між ними!

# ✅ SAFE — атомарний UPDATE на рівні PostgreSQL:
def increment_views_SAFE(note_id):
    Note.objects.filter(id=note_id).update(
        views_count=F('views_count') + 1
    )
    # 1 SQL: UPDATE notes SET views_count = views_count + 1 WHERE id=?
    # PostgreSQL виконує read+write атомарно — race condition неможливий

# ✅ SAFE — для складнішої логіки (select_for_update):
def increment_with_cap(note_id, max_views=10000):
    """Збільшити але не більше ніж max_views."""
    with transaction.atomic():
        note = Note.objects.select_for_update().get(id=note_id)
        if note.views_count < max_views:
            note.views_count += 1
            note.save(update_fields=['views_count'])
```

---

## 6. Race Condition — Double Submit

---
> **🧠 Ментальна модель:** Подвійне відправлення: користувач натиснув "Купити" двічі (або подвійний клік, або мережева затримка). Два HTTP POST запити летять одночасно. Без захисту — два ідентичних замовлення. Idempotency key — унікальний токен що дозволяє "повторні" запити не створювати дублікат.
>
> **📚 Idempotency Key:** Клієнт генерує UUID і відправляє з кожним запитом. Сервер зберігає idempotency_key в БД. При другому запиті з тим самим ключем → повертає той самий результат, не створює новий. UniqueConstraint на idempotency_key гарантує це на рівні БД.
>
> **🌐 Django реалізація:** `IntegrityError` при спробі INSERT з дублікатом idempotency_key → у View ловимо → повертаємо існуючий результат.
---

```python
import uuid
from django.db import IntegrityError

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    # Idempotency key — унікальний токен від клієнта
    idempotency_key = models.UUIDField(unique=True, default=uuid.uuid4)
    # UniqueConstraint гарантує: один key → одне замовлення (навіть при race condition)


def create_order_idempotent(user, cart, idempotency_key):
    """
    Ідемпотентне створення замовлення.
    Два паралельних запити з тим самим key → тільки одне замовлення.
    """
    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                total_price=cart.total,
                idempotency_key=idempotency_key,
            )
            # Подальша логіка...
            return order, 'created'
    except IntegrityError:
        # Другий запит з тим самим key → UNIQUE violation → повертаємо існуюче
        existing = Order.objects.get(idempotency_key=idempotency_key)
        return existing, 'already_exists'
```

---

## 7. Deadlock — взаємне блокування

---
> **🧠 Ментальна модель:** Deadlock = дві транзакції чекають одна одну. T1 заблокувала рядок A і чекає B. T2 заблокувала рядок B і чекає A. Обидві чекають вічно. PostgreSQL виявляє deadlock і автоматично вбиває одну (кидає `DeadlockDetected` exception).
>
> **📚 Коли виникає:** При різному порядку блокування. T1: `lock(note_1) → lock(note_2)`. T2: `lock(note_2) → lock(note_1)`. Якщо T1 заблокувала note_1 і T2 заблокувала note_2 одночасно → deadlock.
>
> **🌐 Профілактика:** Завжди блокувати в одному **стабільному порядку** (наприклад, по id ASC). Якщо T1 і T2 завжди беруть lock спочатку по меншому id → T1 бере note_1, T2 чекає note_1 → T1 бере note_2 → COMMIT → T2 отримує note_1 → бере note_2 → COMMIT. Deadlock неможливий!
>
> **❌ Типова помилка:** Різний порядок блокування в різних views. View A: `lock(user) → lock(note)`. View B: `lock(note) → lock(user)`. При одночасних запитах → deadlock.
---

```python
# ❌ DEADLOCK ПОТЕНЦІАЛ:
def transfer_A_to_B(note_a_id, note_b_id, user):
    with transaction.atomic():
        a = Note.objects.select_for_update().get(id=note_a_id)  # lock A
        b = Note.objects.select_for_update().get(id=note_b_id)  # чекає B
        ...

def transfer_B_to_A(note_a_id, note_b_id, user):
    with transaction.atomic():
        b = Note.objects.select_for_update().get(id=note_b_id)  # lock B
        a = Note.objects.select_for_update().get(id=note_a_id)  # чекає A ← DEADLOCK!
        ...


# ✅ РІШЕННЯ: завжди блокувати в стабільному порядку (по id ASC):
def transfer_notes_safe(note_a_id, note_b_id, user):
    with transaction.atomic():
        # ЗАВЖДИ блокуємо в порядку зростання id
        notes = Note.objects.select_for_update().filter(
            id__in=[note_a_id, note_b_id]
        ).order_by('id')  # ← СТАБІЛЬНИЙ ПОРЯДОК!

        note_map = {n.id: n for n in notes}
        note_a = note_map[note_a_id]
        note_b = note_map[note_b_id]
        # Логіка...


# ✅ RETRY при Deadlock (для складних систем):
import time
import random
from django.db import OperationalError

def with_deadlock_retry(func, max_retries=3, base_delay=0.1):
    """
    Декоратор: повторює операцію при deadlock.
    Exponential backoff + jitter (випадкова затримка).
    """
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            if 'deadlock detected' in str(e).lower() and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                time.sleep(delay)
                continue
            raise

# Використання:
with_deadlock_retry(lambda: transfer_notes_safe(a_id, b_id, user))
```

---

## 8. on_commit() — дії після успішного commit

---
> **🧠 Ментальна модель:** `on_commit()` — це "відправ email **тільки якщо** замовлення успішно збережено". Якщо транзакція відкатилась → email не відправляється. Якщо commit успішний → email відправляється. Ніколи не відправляй Celery task або email всередині `atomic()` — транзакція ще не закінчена, може відкотитись!
>
> **📚 Типова помилка без on_commit:** `celery_task.delay(note.id)` всередині `transaction.atomic()`. Celery task запускається негайно. Task намагається прочитати note → він ще не в БД (транзакція ще не завершена). Task падає або бачить неправильний стан.
>
> **🌐 Як працює:** Django накопичує `on_commit` callbacks. Після успішного `COMMIT` — виконує всі callbacks в порядку реєстрації. Якщо `ROLLBACK` — callbacks НЕ виконуються.
---

```python
from django.db import transaction

def create_note_with_notification(user, title, content):
    with transaction.atomic():
        note = Note.objects.create(
            title=title, content=content, user=user
        )
        
        # ❌ НЕПРАВИЛЬНО: email може відправитись навіть якщо транзакція відкатилась!
        # send_notification_email.delay(note.id)
        
        # ✅ ПРАВИЛЬНО: відправляємо тільки після успішного COMMIT
        transaction.on_commit(
            lambda: send_notification_email.delay(note.id)
        )
        
        # ✅ Можна реєструвати кілька callbacks:
        transaction.on_commit(
            lambda: update_search_index.delay(note.id)
        )
        transaction.on_commit(
            lambda: send_webhook.delay('note_created', note.id)
        )
    
    # Після цього рядка: COMMIT виконаний
    # on_commit callbacks виконуються в порядку реєстрації
    # Якщо між on_commit(email) і on_commit(webhook) виникає проблема —
    # email вже відправлено (callback виконується незалежно)
    
    return note
```

---

## 9. Isolation Levels та рішення для кожного сценарію

```python
# Встановлення isolation level для конкретної транзакції:

from django.db import transaction, connection

def critical_report_generation(user_id):
    """
    Фінансовий звіт: потребує consistent snapshot.
    REPEATABLE READ: всі SELECT в транзакції бачать один snapshot.
    """
    with transaction.atomic():
        connection.cursor().execute(
            'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ'
        )
        
        total_notes = Note.objects.filter(user_id=user_id).count()
        published = Note.objects.filter(user_id=user_id, status='published').count()
        
        # Якщо хтось додасть нотатку між цими двома COUNT — ми не побачимо
        # (REPEATABLE READ: snapshot заморожений)
        
        return {'total': total_notes, 'published': published}


def book_last_seat(event_id, user_id):
    """
    Бронювання останнього місця: SERIALIZABLE для максимальної безпеки.
    """
    with transaction.atomic():
        connection.cursor().execute(
            'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE'
        )
        
        event = Event.objects.get(id=event_id)
        
        if event.seats_available <= 0:
            raise ValueError("Немає вільних місць")
        
        # SERIALIZABLE гарантує: якщо T1 і T2 обидва бачать seats=1,
        # одна з них отримає SerializationFailure і буде повторена
        event.seats_available -= 1
        event.save()
        
        Booking.objects.create(event=event, user_id=user_id)
```

---

## 10. Практична таблиця рішень

| Проблема | Рішення | Django API |
|----------|---------|------------|
| Лічильник (N+1 race) | Атомарний UPDATE | `F('count') + 1` |
| Часткова операція | Атомарна транзакція | `transaction.atomic()` |
| Конкурентне читання-запис | Рядкове блокування | `select_for_update()` |
| Double submit | Idempotency key | `UNIQUE` + catch `IntegrityError` |
| Deadlock | Стабільний порядок lock-ів | `order_by('id')` перед lock |
| Email після save | Після commit | `on_commit(lambda: task.delay(...))` |
| Consistent snapshot | REPEATABLE READ | `SET TRANSACTION ISOLATION LEVEL` |

---

## Prediction Exercises

### Exercise 1: F() vs save()

```python
# Варіант A:
note = Note.objects.get(pk=42)
note.likes += 1
note.save()

# Варіант B:
Note.objects.filter(pk=42).update(likes=F('likes') + 1)
```

**Питання:** При 1000 одночасних запитах на обидва варіанти — який результат?

> **Варіант A:** Всі 1000 читають `likes=0`, всі пишуть `likes=1`. Результат: `likes=1` (999 оновлень загублено!)
>
> **Варіант B:** Кожне UPDATE атомарно збільшує на 1. Результат: `likes=1000` (жодне оновлення не загублено!)

### Exercise 2: atomic() Exception

```python
with transaction.atomic():
    note = Note.objects.create(title='Test')
    try:
        raise ValueError("oops")
    except ValueError:
        pass
    note2 = Note.objects.create(title='Test2')  # що відбудеться тут?
```

**Питання:** Скільки нотаток буде створено?

> **Відповідь:** `TransactionManagementError` при спробі `create(title='Test2')`. Транзакція в "aborted" стані після `except ValueError: pass` (Python перехопив exception, але Django не знає — він думає транзакція зламана). **Жодна** нотатка не буде збережена. Потрібно catch ЗОВНІ atomic.

---

## Питання для самоперевірки

1. Чому не можна робити `try/except` всередині `transaction.atomic()`?
2. Що таке Savepoint і коли Django його використовує?
3. Яка різниця між `select_for_update(nowait=True)` і `select_for_update(skip_locked=True)`?
4. Що таке Lost Update і як F() його запобігає?
5. Що таке Deadlock і як його уникнути?
6. Навіщо `on_commit()` і чому не можна відправляти email/task всередині atomic()?
7. Яка різниця між READ COMMITTED і REPEATABLE READ?
8. Що таке idempotency key і для яких сценаріїв він потрібен?
9. Чому `select_for_update()` ЗАВЖДИ має бути в `transaction.atomic()`?
10. PostgreSQL виявив deadlock і вбив одну транзакцію. Яку? Що отримає вбита транзакція?
