# Django Tasks — Celery та Асинхронні Задачі

> `tasks.py` — це транспортний шар для фонових операцій.
> Task не містить бізнес-логіки. Він лише ставить роботу у чергу
> і делегує виконання в Service.

---

## Навігація

| Розділ | Що всередині |
|--------|--------------|
| [Навіщо Celery](#навіщо-celery) | Проблема блокуючих операцій |
| [Архітектура](#архітектура-celery--django) | Broker, Worker, Backend |
| [Анатомія Task](#анатомія-task) | Базова структура, правила |
| [Task = Transport Layer](#task--transport-layer) | Чому логіка не в task |
| [on_commit](#on_commit--безпечний-запуск-task) | Гарантія цілісності з БД |
| [Retry та помилки](#retry-та-обробка-помилок) | `autoretry_for`, `max_retries`, `countdown` |
| [Ідемпотентність](#ідемпотентність) | Задачі безпечні для повторного запуску |
| [Типові патерни](#типові-патерни) | Chains, Groups, Chords |
| [Конфігурація](#конфігурація) | Налаштування Celery у Django |
| [Антипатерни](#антипатерни) | Що не робити і чому |
| [Шаблон](#шаблон) | Copy-paste шаблон для нової task |

---

## Навіщо Celery

### Проблема блокуючих операцій

HTTP-запит має вкластись у ~200–500 мс. Деякі операції набагато довші:

| Операція | Час | Проблема |
|----------|-----|---------|
| Відправка email | 1–3 с | Клієнт чекає |
| Обробка DEM-файлу | 30–120 с | Timeout у Nginx/клієнта |
| ICESat-2 запит до SlideRule | 10–60 с | Воркер заблоковано |
| ML inference | 5–30 с | Клієнт чекає |
| Генерація PDF-звіту | 3–10 с | Клієнт чекає |

### Рішення: асинхронна черга

```
HTTP Request
    │
    ▼
View → ставить задачу в чергу → одразу повертає 202 Accepted
    │
    ▼ (незалежно, у фоні)
Celery Worker → виконує задачу → зберігає результат
```

Клієнт не чекає. Воркер не блокує HTTP-запити.

---

## Архітектура Celery + Django

```
Django App
    │
    │  task.delay(args)   ← ставить задачу у чергу
    ▼
Redis (Broker)            ← черга повідомлень
    │
    │  отримує задачу
    ▼
Celery Worker             ← окремий процес, виконує задачу
    │
    │  результат (optional)
    ▼
Redis / PostgreSQL (Backend)   ← зберігає результат якщо потрібно
```

| Компонент | Роль |
|-----------|------|
| **Broker** | Черга повідомлень (зазвичай Redis або RabbitMQ) |
| **Worker** | Окремий Python-процес що виконує задачі |
| **Backend** | Сховище результатів (Redis, PostgreSQL) — опційно |
| **Beat** | Планувальник для periodic tasks (аналог cron) |

---

## Анатомія Task

### Базова структура

```python
# apps/flood/tasks.py

from celery import shared_task


@shared_task
def notify_emergency_services_task(event_id: int) -> None:
    from apps.flood.selectors import flood_event_get_by_id
    from apps.flood.services import flood_event_notify

    event = flood_event_get_by_id(event_id=event_id)
    flood_event_notify(event=event)
```

### Чому імпорти всередині функції

Імпорти на рівні модуля можуть спричинити циклічні залежності при старті Celery worker. Локальні імпорти всередині task функції — безпечний патерн.

```python
# НЕБЕЗПЕЧНО — циклічний імпорт при старті worker
from apps.flood.services import flood_event_notify

@shared_task
def notify_task(event_id):
    ...

# БЕЗПЕЧНО — імпорт тільки при виконанні task
@shared_task
def notify_task(event_id):
    from apps.flood.services import flood_event_notify
    ...
```

### Передача аргументів

```python
# ДОБРЕ — передавати прості типи: int, str, list, dict
@shared_task
def process_flood_task(event_id: int) -> None:
    ...

# Виклик
process_flood_task.delay(event_id=42)


# ПОГАНО — передавати Python-об'єкти (не серіалізуються надійно)
@shared_task
def process_flood_task(event: FloodEvent) -> None:   # ❌
    ...
```

Celery серіалізує аргументи через JSON. Передавай ID, рядки, числа — не ORM-об'єкти.

---

## Task = Transport Layer

Task — це черга доставки виклику, не місце для логіки.

### Антипатерн: логіка в task

```python
# ПОГАНО — вся логіка у task
@shared_task
def process_flood_task(event_id: int):
    event = FloodEvent.objects.get(id=event_id)
    event.status = 'processing'
    event.save()

    # ML pipeline
    result = run_ml_model(event.geometry)
    event.risk_level = result['risk']
    event.status = 'done'
    event.save()

    # Email
    send_mail(
        subject='Flood processed',
        message=f'Event {event_id} done',
        from_email='system@example.com',
        recipient_list=[event.created_by.email],
    )
```

**Проблеми:**
- Логіку не можна викликати з View або CLI без Celery
- Не можна протестувати без запуску worker
- При retry — весь pipeline запускається знову

### Правильно: task делегує в service

```python
# ДОБРЕ — task тільки транспортує виклик
@shared_task
def process_flood_task(event_id: int) -> None:
    from apps.flood.selectors import flood_event_get_by_id
    from apps.flood.services import flood_event_process

    event = flood_event_get_by_id(event_id=event_id)
    flood_event_process(event=event)   # вся логіка у service
```

```python
# services.py — логіка тут, незалежно від Celery
@transaction.atomic
def flood_event_process(*, event: FloodEvent) -> FloodEvent:
    event.status = 'processing'
    event.save(update_fields=['status'])

    result = run_ml_model(event.geometry)
    event.risk_level = result['risk']
    event.status = 'done'
    event.save(update_fields=['risk_level', 'status'])

    transaction.on_commit(
        lambda: send_flood_report_task.delay(event.id)
    )

    return event
```

Ту саму `flood_event_process` можна викликати з View, management command, тесту — без Celery.

---

## `on_commit` — Безпечний запуск Task

### Проблема без `on_commit`

```python
@transaction.atomic
def flood_event_create(*, region_name: str, ...) -> FloodEvent:
    event = FloodEvent(...)
    event.save()

    # ❌ НЕБЕЗПЕЧНО:
    # Celery worker може запуститись ДО того як транзакція закрилась.
    # Worker робить SELECT — запис ще не з'явився в БД.
    # Task падає з DoesNotExist.
    process_flood_task.delay(event.id)

    return event
```

### Рішення

```python
@transaction.atomic
def flood_event_create(*, region_name: str, ...) -> FloodEvent:
    event = FloodEvent(...)
    event.save()

    # ✅ БЕЗПЕЧНО:
    # Task ставиться в чергу ТІЛЬКИ після успішного commit.
    # Якщо транзакція відкотиться — task не запуститься взагалі.
    transaction.on_commit(
        lambda: process_flood_task.delay(event.id)
    )

    return event
```

> **Правило:** будь-який `task.delay()` всередині `@transaction.atomic` — завжди через `on_commit`.

---

## Retry та обробка помилок

### `autoretry_for` — автоматичний retry при винятках

```python
import httpx
from celery import shared_task


@shared_task(
    autoretry_for=(httpx.HTTPError, ConnectionError),  # при яких помилках повторювати
    max_retries=3,                                      # максимум спроб
    countdown=60,                                       # затримка між спробами (секунди)
    retry_backoff=True,                                 # експоненційне збільшення затримки
)
def fetch_sliderule_data_task(job_id: int) -> None:
    from apps.satellite.services import icesat2_job_fetch

    icesat2_job_fetch(job_id=job_id)
```

З `retry_backoff=True` затримки будуть: 60с → 120с → 240с.

### Ручний retry

```python
@shared_task(bind=True, max_retries=5)
def process_dem_task(self, dem_id: int) -> None:
    from apps.dem.services import dem_process

    try:
        dem_process(dem_id=dem_id)
    except TemporaryProcessingError as exc:
        # Ручний retry з кастомною затримкою
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
```

`bind=True` дає доступ до `self` — поточного екземпляра task з метаданими.

### Обробка після всіх спроб

```python
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    max_retries=3,
    countdown=60,
)
def critical_processing_task(job_id: int) -> None:
    from apps.flood.services import flood_job_process, flood_job_mark_failed

    try:
        flood_job_process(job_id=job_id)
    except Exception as exc:
        logger.error(f"Task failed for job_id={job_id}: {exc}")
        flood_job_mark_failed(job_id=job_id)
        raise   # дає Celery знати що task впав → retry або FAILURE
```

---

## Ідемпотентність

Task може запуститись кілька разів (мережева помилка, retry, дублікат повідомлення). Кожен task повинен бути **ідемпотентним** — повторний запуск з тими самими аргументами не повинен зламати систему.

### Неідемпотентний (небезпечний)

```python
@shared_task
def send_welcome_email_task(user_id: int) -> None:
    user = User.objects.get(id=user_id)
    send_mail(subject='Ласкаво просимо!', ...)
    # При retry — email відправиться вдруге
```

### Ідемпотентний (безпечний)

```python
@shared_task
def send_welcome_email_task(user_id: int) -> None:
    user = User.objects.get(id=user_id)

    if user.welcome_email_sent:   # перевірка перед відправкою
        return

    send_mail(subject='Ласкаво просимо!', ...)

    User.objects.filter(id=user_id).update(welcome_email_sent=True)
```

---

## Типові патерни

### Простий delay — запустити і забути

```python
# Запуск task у фоні
process_flood_task.delay(event_id=42)

# З keyword arguments
process_flood_task.apply_async(kwargs={'event_id': 42})
```

### apply_async — розширені опції

```python
from datetime import timedelta
from django.utils import timezone

# Затримати виконання на 10 хвилин
process_flood_task.apply_async(
    kwargs={'event_id': 42},
    countdown=600,
)

# Виконати в конкретний час
process_flood_task.apply_async(
    kwargs={'event_id': 42},
    eta=timezone.now() + timedelta(hours=1),
)

# Поставити у специфічну чергу
process_flood_task.apply_async(
    kwargs={'event_id': 42},
    queue='high_priority',
)
```

### Chain — послідовне виконання

```python
from celery import chain

# Task 2 запускається тільки після успішного завершення Task 1
pipeline = chain(
    fetch_sliderule_data_task.s(job_id=42),
    process_icesat2_points_task.s(job_id=42),
    finalize_icesat2_job_task.s(job_id=42),
)
pipeline.delay()
```

### Group — паралельне виконання

```python
from celery import group

# Всі tasks запускаються паралельно
parallel_jobs = group(
    process_dem_task.s(dem_id=1),
    process_dem_task.s(dem_id=2),
    process_dem_task.s(dem_id=3),
)
parallel_jobs.delay()
```

### Periodic Tasks (Celery Beat)

```python
# config/celery.py

from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'apps.flood.tasks.cleanup_old_jobs_task',
        'schedule': crontab(hour=3, minute=0),   # щодня о 3:00
    },
    'sync-satellite-data': {
        'task': 'apps.satellite.tasks.sync_icesat2_data_task',
        'schedule': crontab(minute='*/30'),       # кожні 30 хвилин
    },
}
```

---

## Конфігурація

### `config/celery.py`

```python
# config/celery.py

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматичне виявлення tasks.py у всіх INSTALLED_APPS
app.autodiscover_tasks()
```

### `config/__init__.py`

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### `settings.py`

```python
# settings.py

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Важливо: завжди підтверджувати задачу ПІСЛЯ виконання
# (не після отримання — захист від втрати при падінні worker)
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

### Запуск worker

```bash
# Базовий запуск
celery -A config worker --loglevel=info

# З кількома чергами і concurrency
celery -A config worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=default,high_priority

# Celery Beat (periodic tasks)
celery -A config beat --loglevel=info
```

---

## Антипатерни

### Бізнес-логіка в task

```python
# ПОГАНО
@shared_task
def process_task(event_id):
    event = FloodEvent.objects.get(id=event_id)
    event.status = 'done'   # логіка тут
    event.save()

# ДОБРЕ
@shared_task
def process_task(event_id):
    from apps.flood.services import flood_event_complete
    event = flood_event_get_by_id(event_id=event_id)
    flood_event_complete(event=event)
```

### Передача ORM-об'єкта в task

```python
# ПОГАНО — об'єкт серіалізується через pickle, нестабільно
process_task.delay(event=flood_event_object)

# ДОБРЕ — передавати тільки ID
process_task.delay(event_id=flood_event_object.id)
```

### `task.delay()` без `on_commit` всередині транзакції

```python
# ПОГАНО — race condition з БД
@transaction.atomic
def create_event():
    event = FloodEvent.objects.create(...)
    process_task.delay(event.id)   # worker може не знайти запис

# ДОБРЕ
@transaction.atomic
def create_event():
    event = FloodEvent.objects.create(...)
    transaction.on_commit(lambda: process_task.delay(event.id))
```

### Синхронний виклик task у View

```python
# ПОГАНО — блокує HTTP-відповідь
result = process_task(event_id=42)   # виконується синхронно

# ДОБРЕ — ставить у чергу і повертає одразу
process_task.delay(event_id=42)
return Response({'status': 'queued'}, status=202)
```

---

## Таблиця: що task повинен і не повинен

| Дія | Повинен? |
|-----|----------|
| Отримувати прості аргументи (int, str) | ✅ |
| Виконувати SELECT для отримання об'єкта | ✅ (через selector) |
| Делегувати в service | ✅ |
| Логувати помилки | ✅ |
| Бути ідемпотентним | ✅ |
| Містити бізнес-логіку | ❌ |
| Отримувати ORM-об'єкти як аргументи | ❌ |
| Відкривати `@transaction.atomic` | ❌ (це роль service) |
| Повертати `Response` | ❌ |
| Знати про HTTP | ❌ |

---

## Шаблон

```python
# apps/<app>/tasks.py

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    max_retries=3,
    countdown=60,
    retry_backoff=True,
)
def <model>_<action>_task(<model>_id: int) -> None:
    from apps.<app>.selectors import <model>_get_by_id
    from apps.<app>.services import <model>_<action>

    logger.info(f"Starting <action> for <model>_id={<model>_id}")

    obj = <model>_get_by_id(<model>_id=<model>_id)
    <model>_<action>(obj=obj)

    logger.info(f"Completed <action> for <model>_id={<model>_id}")
```

```python
# Виклик із service через on_commit
@transaction.atomic
def <model>_create(*, <field>: <type>) -> <Model>:
    obj = <Model>(<field>=<field>)
    obj.full_clean()
    obj.save()

    transaction.on_commit(
        lambda: <model>_<action>_task.delay(<model>_id=obj.id)
    )

    return obj
```

---

## Зв'язок з рештою документації

| Тема | Файл |
|------|------|
| Services (`on_commit`, бізнес-логіка якій делегує task) | [DJANGO_SERVICES.md](DJANGO_SERVICES.md) |
| Selectors (читання даних всередині task) | [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) |
| Повна картина бізнес-шару | [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) |
| Структура проєкту (`infrastructure/celery/`) | [DJANGO_PROJECT_STRUCTURE.md](DJANGO_PROJECT_STRUCTURE.md) |
