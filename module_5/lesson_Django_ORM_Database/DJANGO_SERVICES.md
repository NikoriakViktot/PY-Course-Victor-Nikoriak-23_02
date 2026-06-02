# Django Services — Шар бізнес-логіки

> `services.py` — це окремий файл у кожному Django app,
> де живе вся бізнес-логіка.
> Service — це **transport-агностична функція, що описує що система робить**.

---

## Проблема без Services

У типовому Django-проєкті бізнес-логіка поступово осідає у View:

```python
# views.py — "Fat View" антипатерн
class RegisterUserView(APIView):

    def post(self, request):
        # валідація
        if User.objects.filter(email=request.data['email']).exists():
            return Response({'error': 'Email вже зайнятий'}, status=400)

        # хешування пароля
        password = make_password(request.data['password'])

        # збереження
        user = User.objects.create(
            email=request.data['email'],
            password=password,
        )

        # відправка email
        send_welcome_email(user.email)

        # відповідь
        return Response({'id': user.id}, status=201)
```

**Що ламається:**
- Цю логіку не можна перевикористати з Celery task
- Не можна викликати з management command
- Не можна протестувати без HTTP request
- Логіка дублюється якщо реєстрація потрібна у двох місцях

---

## Рішення: Service

```python
# apps/users/services.py

def user_create(*, email: str, password: str) -> User:
    user = User(email=email)
    user.set_password(password)
    user.full_clean()
    user.save()
    send_welcome_email(user.email)
    return user
```

```python
# views.py — тонка, без логіки
class RegisterUserView(APIView):

    def post(self, request):
        serializer = UserRegisterInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = user_create(**serializer.validated_data)

        return Response({'id': user.id}, status=201)
```

Та сама логіка тепер доступна звідусіль:

```python
# З Celery task
user_create(email='bot@example.com', password='secret')

# З management command
user_create(email='admin@example.com', password='admin123')

# З тесту
user = user_create(email='test@example.com', password='pass')
assert user.id is not None
```

---

## Що таке Service архітектурно

Service — це **шар між HTTP-транспортом і базою даних**, що описує бізнес-домен.

```
Transport Layer     views.py, tasks.py, management commands
        │
        │  validated_data / параметри
        ▼
Application Layer   services.py          ← ТУТ ЖИВЕ ЛОГІКА
        │
        │  domain objects
        ▼
Data Layer          selectors.py, models.py, ORM
        │
        ▼
     PostgreSQL
```

| Шар | Відповідає на питання |
|-----|-----------------------|
| View | Як прийшов запит? HTTP, WebSocket, CLI? |
| **Service** | **Що система робить з цими даними?** |
| Selector | Як отримати потрібні дані з БД? |
| ORM | Як сформулювати SQL? |

---

## Анатомія Service

### Базові правила

- Живе в `<app_name>/services.py`
- Stateless Python функція (не клас, якщо немає складного стану)
- Keyword-only аргументи (`*`) — захист від помилок порядку при рефакторингу
- Строгі type annotations
- Не знає HTTP — не імпортує `request`, не повертає `Response`
- Повертає доменний об'єкт або None

```python
# apps/flood/services.py

from django.db import transaction
from apps.flood.models import FloodEvent


def flood_event_create(
    *,
    region_name: str,
    severity_level: str,
    detected_at,
    created_by,
) -> FloodEvent:
    event = FloodEvent(
        region_name=region_name,
        severity_level=severity_level,
        detected_at=detected_at,
        created_by=created_by,
    )
    event.full_clean()   # Django-валідація на рівні домену
    event.save()
    return event


def flood_event_update(
    *,
    event: FloodEvent,
    severity_level: str,
) -> FloodEvent:
    event.severity_level = severity_level
    event.full_clean()
    event.save(update_fields=['severity_level'])
    return event


def flood_event_delete(*, event: FloodEvent) -> None:
    event.delete()
```

> `*` перед аргументами — Python-синтаксис для keyword-only параметрів.
> Викликати можна тільки так: `flood_event_create(region_name="Kyiv", ...)`.
> Порядок аргументів не має значення — немає ризику переплутати.

---

## Транзакції

Service відповідає за межі транзакцій. Якщо кілька операцій мають бути атомарними — вся функція обгортається в `@transaction.atomic`.

```python
def user_complete_onboarding(*, user: User) -> User:
    # Без atomic — якщо друга операція впаде,
    # перша вже виконалась і не відкотиться
    user.onboarding_completed = True
    user.save(update_fields=['onboarding_completed'])

    profile = UserProfile(user=user, bio='')
    profile.save()

    return user
```

```python
@transaction.atomic
def user_complete_onboarding(*, user: User) -> User:
    # З atomic — або все збереглось, або нічого
    user.onboarding_completed = True
    user.save(update_fields=['onboarding_completed'])

    profile = UserProfile(user=user, bio='')
    profile.save()

    return user
```

### Коли потрібно `@transaction.atomic`

| Ситуація | Atomic? |
|----------|---------|
| Один `save()` | Ні — Django сам по собі атомарний на рівні рядка |
| Два і більше `save()` | Так |
| `save()` + `delete()` | Так |
| Будь-які пов'язані операції що мають бути або всі, або жодна | Так |

---

## Side Effects і `on_commit`

**Side effect** — це дія поза межами основної транзакції: відправка email, Celery task, запис у зовнішній API.

### Проблема без `on_commit`

```python
@transaction.atomic
def flood_event_create(*, region_name: str, ...) -> FloodEvent:
    event = FloodEvent(...)
    event.save()

    # НЕБЕЗПЕЧНО — Celery отримає task до того,
    # як транзакція закрилась і запис з'явився в БД.
    # Воркер спробує знайти event — і не знайде.
    notify_emergency_task.delay(event.id)

    return event
```

### Рішення: `transaction.on_commit`

```python
@transaction.atomic
def flood_event_create(*, region_name: str, ...) -> FloodEvent:
    event = FloodEvent(...)
    event.save()

    # БЕЗПЕЧНО — task запускається ТІЛЬКИ після успішного commit.
    # Якщо транзакція відкотиться — task не запуститься взагалі.
    transaction.on_commit(
        lambda: notify_emergency_task.delay(event.id)
    )

    return event
```

### Правило

```
on_commit → гарантія того що side effect
            відбувається лише якщо дані реально збереглись у БД
```

---

## Celery Task — теж Transport Layer

Celery task — це черга доставки, не місце для логіки. Task делегує в Service.

```python
# apps/flood/tasks.py

# ПОГАНО — логіка прямо в task
@shared_task
def process_flood_task(event_id: int):
    event = FloodEvent.objects.get(id=event_id)
    event.status = 'processed'
    event.save()
    send_report_email(event.created_by.email)
```

```python
# ДОБРЕ — task тільки транспортує виклик
@shared_task
def process_flood_task(event_id: int):
    from apps.flood.selectors import flood_event_get_by_id
    from apps.flood.services import flood_event_mark_processed

    event = flood_event_get_by_id(event_id=event_id)
    flood_event_mark_processed(event=event)
```

Та сама `flood_event_mark_processed` може бути викликана з View, тесту або CLI — без зміни логіки.

---

## Маппінг доменних помилок на HTTP

Service не знає HTTP. Але якщо `full_clean()` кидає `django.core.exceptions.ValidationError` — DRF не знає як його відформатувати у 400-відповідь.

Рішення — кастомний exception handler (один раз у `settings.py`):

```python
# shared/exceptions/handlers.py

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.serializers import as_serializer_error


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=as_serializer_error(exc))

    return exception_handler(exc, context)
```

```python
# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'shared.exceptions.handlers.custom_exception_handler',
}
```

Тепер `full_clean()` у будь-якому Service автоматично повертає клієнту красивий JSON 400.

---

## Повний приклад: View → Service

### Модель

```python
# apps/flood/models.py

class FloodEvent(models.Model):
    SEVERITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    region_name    = models.CharField(max_length=200)
    severity_level = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    detected_at    = models.DateTimeField()
    created_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at     = models.DateTimeField(auto_now_add=True)
```

### Серіалайзер

```python
# apps/flood/serializers.py

class FloodEventInputSerializer(serializers.Serializer):
    region_name    = serializers.CharField(max_length=200)
    severity_level = serializers.ChoiceField(choices=['low', 'medium', 'high'])
    detected_at    = serializers.DateTimeField()


class FloodEventOutputSerializer(serializers.Serializer):
    id             = serializers.IntegerField()
    region_name    = serializers.CharField()
    severity_level = serializers.CharField()
    detected_at    = serializers.DateTimeField()
    created_by     = serializers.EmailField(source='created_by.email')
```

### Service

```python
# apps/flood/services.py

@transaction.atomic
def flood_event_create(
    *,
    region_name: str,
    severity_level: str,
    detected_at,
    created_by,
) -> FloodEvent:
    event = FloodEvent(
        region_name=region_name,
        severity_level=severity_level,
        detected_at=detected_at,
        created_by=created_by,
    )
    event.full_clean()
    event.save()

    transaction.on_commit(
        lambda: notify_emergency_services_task.delay(event.id)
    )

    return event
```

### View

```python
# apps/flood/views.py

class FloodEventCreateAPIView(APIView):

    def post(self, request):
        serializer = FloodEventInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = flood_event_create(
            **serializer.validated_data,
            created_by=request.user,
        )

        output = FloodEventOutputSerializer(event)
        return Response(output.data, status=status.HTTP_201_CREATED)
```

View: 7 рядків. Вся логіка — у Service. View не знає що відбувається всередині.

---

## Service не знає звідки його викликають

Та сама функція:

```python
# З REST API View
event = flood_event_create(region_name="Kyiv", severity_level="high", ...)

# З Celery task
event = flood_event_create(region_name="Lviv", severity_level="medium", ...)

# З management command
event = flood_event_create(region_name="Odesa", severity_level="low", ...)

# З тесту
event = flood_event_create(region_name="Test", severity_level="high", ...)
```

Логіка виконується однаково незалежно від того як прийшов виклик.

---

## Naming Convention

```python
# Створення
user_create(*, email, password) -> User
flood_event_create(*, region_name, severity_level) -> FloodEvent

# Оновлення
user_update(*, user, name) -> User
flood_event_update(*, event, severity_level) -> FloodEvent

# Видалення
user_delete(*, user) -> None
flood_event_delete(*, event) -> None

# Складні workflow
user_complete_onboarding(*, user) -> User
flood_event_mark_processed(*, event) -> FloodEvent
payment_process(*, order, card_token) -> Payment
pipeline_run_dem_validation(*, dem_file) -> ValidationResult
```

Назва = **дія + що відбувається**. Не `process()`, не `handle()`, не `do_stuff()`.

---

## Чого НЕ повинен робити Service

| Дія | Чому ні |
|-----|---------|
| `return Response(...)` | Service не знає HTTP |
| `import request` або `self.request` | Service не знає про Views |
| Прямі SELECT без Selector | Читання — відповідальність Selector |
| Рендерити шаблони | Це рівень Template / View |
| Містити бізнес-логіку в Celery task | Task — це транспорт, не домен |
| Кидати HTTP-статус коди | Домен кидає `ValidationError`, не `400` |

---

## Швидка шпаргалка

```python
# services.py — шаблон

from django.db import transaction
from apps.<app>.models import <Model>


def <model>_create(
    *,
    <field_1>: <type>,
    <field_2>: <type>,
) -> <Model>:
    obj = <Model>(
        <field_1>=<field_1>,
        <field_2>=<field_2>,
    )
    obj.full_clean()
    obj.save()
    return obj


@transaction.atomic
def <model>_create_with_side_effect(
    *,
    <field>: <type>,
) -> <Model>:
    obj = <Model>(<field>=<field>)
    obj.full_clean()
    obj.save()

    transaction.on_commit(
        lambda: some_celery_task.delay(obj.id)
    )

    return obj


def <model>_update(
    *,
    obj: <Model>,
    <field>: <type>,
) -> <Model>:
    obj.<field> = <field>
    obj.full_clean()
    obj.save(update_fields=['<field>'])
    return obj


def <model>_delete(*, obj: <Model>) -> None:
    obj.delete()
```

---

## Зв'язок з рештою документації

| Тема | Файл |
|------|------|
| Selectors (читання даних) | [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) |
| Services + Selectors + Serializers (повна картина) | [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) |
| ORM: `full_clean`, `save`, транзакції | [DJANGO_ORM_DEEP.md](DJANGO_ORM_DEEP.md) |
| Views: як передати дані у Service | [notes_project/README.md](notes_project/README.md) — Крок 8 |
