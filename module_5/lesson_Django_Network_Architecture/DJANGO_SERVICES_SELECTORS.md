# Django Services, Selectors & Serializers — Шар бізнес-логіки

> Цей документ описує production-архітектуру бізнес-шару Django:
> де живе логіка, хто читає дані, хто пише, і як HTTP ніколи не потрапляє в домен.

---

## Навігація

| Розділ | Що всередині |
|--------|--------------|
| [Архітектурна карта](#архітектурна-карта) | Де живе кожен шар |
| [Серіалайзери](#серіалайзери--transport-layer) | InputSerializer, OutputSerializer, validate() |
| [Services](#services--шар-бізнес-логіки) | Stateless функції, транзакції, side effects |
| [Selectors](#selectors--шар-читання-даних) | CQRS-light, N+1, query abstraction |
| [Повний data flow](#повний-data-flow) | HTTP → View → Serializer → Service → Selector → DB |
| [Антипатерни](#антипатерни) | Що не роби і чому |
| [Таблиця відповідальностей](#таблиця-відповідальностей) | Хто що робить / не робить |

---

## Архітектурна карта

```
HTTP Request
    │
    ▼
┌─────────────────────────────┐
│  View (views.py)            │  ← Тонкий HTTP-оркестратор
│  Отримує запит              │
│  Викликає серіалайзер       │
│  Передає в Service          │
│  Повертає Response          │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  InputSerializer            │  ← Валідація + трансформація
│  (serializers.py)           │     вхідних даних
└────────────┬────────────────┘
             │ validated_data
             ▼
┌─────────────────────────────┐
│  Service (services.py)      │  ← Бізнес-логіка + транзакція
│  Оркеструє операції         │     + side effects
│  Не знає HTTP               │
│  Викликає Selector          │
└────────────┬────────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌──────────┐   ┌──────────────────────┐
│ Selector │   │  Infrastructure      │
│(selectors│   │  (email, S3, Celery) │
│  .py)    │   └──────────────────────┘
│  Читання │
│  даних   │
└────┬─────┘
     │
     ▼
┌─────────────────────────────┐
│  ORM (models.py)            │  ← Схема БД, відносини
└────────────┬────────────────┘
             │
             ▼
         PostgreSQL
             │
             ▼
┌─────────────────────────────┐
│  OutputSerializer           │  ← Форматування відповіді
│  (serializers.py)           │
└────────────┬────────────────┘
             │
             ▼
         HTTP Response
```

---

## Серіалайзери — Transport Layer

### Основний принцип

Серіалайзер — це **межа між HTTP і доменом**. Він не знає бізнес-логіки. Він лише:
- приймає сирі HTTP дані → валідує → повертає `validated_data`
- приймає доменні об'єкти → форматує → повертає JSON

### Антипатерн: ModelSerializer як єдина точка входу

```python
# ПОГАНО — ModelSerializer тісно прив'язує HTTP до схеми БД
class FloodEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloodEvent
        fields = '__all__'
```

Проблема: зміна в моделі → зміна API. Бізнес-правила в `save()`. Немає явного контракту.

### Правильно: InputSerializer + OutputSerializer

```python
# serializers.py

class FloodEventInputSerializer(serializers.Serializer):
    """Контракт вхідних даних — незалежний від моделі."""
    region_name = serializers.CharField(max_length=200)
    severity_level = serializers.ChoiceField(choices=['low', 'medium', 'high'])
    detected_at = serializers.DateTimeField()


class FloodEventOutputSerializer(serializers.Serializer):
    """Контракт вихідних даних — що клієнт бачить у відповіді."""
    id = serializers.IntegerField()
    region_name = serializers.CharField()
    severity_level = serializers.CharField()
    detected_at = serializers.DateTimeField()
    created_by_email = serializers.EmailField(source='created_by.email')
```

### Метод validate() — Перехоплення перед validated_data

`validate(self, data)` — точка для крос-польової валідації та трансформації.

```python
class FloodEventInputSerializer(serializers.Serializer):
    region_name = serializers.CharField()
    # slug генерується сервером — read_only щоб DRF не вимагав його у запиті
    slug = serializers.SlugField(read_only=True)

    def validate(self, data: dict) -> dict:
        # Автогенерація поля до validated_data
        data['slug'] = slugify(data['region_name'])
        return data
```

> **Важливо:** поля, що генеруються сервером, мають бути `read_only=True` в `Meta.read_only_fields`, інакше серіалайзер упаде на валідації ще до виклику `validate()`.

### Складна серіалізація — Pure Python функція

Коли структура відповіді надто складна для `OutputSerializer`:

```python
# selectors.py або окремий модуль

def flood_feed_serialize(events: list) -> list[dict]:
    """
    Обходить обмеження OutputSerializer для складних joined структур.
    Будує відповідь через Python після оптимізованого SQL-запиту.
    """
    region_cache = {}  # in-memory кеш для повторних значень

    result = []
    for event in events:
        region_id = event.region_id
        if region_id not in region_cache:
            region_cache[region_id] = event.region.display_name

        result.append({
            'id': event.id,
            'region': region_cache[region_id],
            'severity': event.severity_level,
            'detected_at': event.detected_at.isoformat(),
        })
    return result
```

Перевага: повний контроль над SQL footprint, немає N+1 від вкладених серіалайзерів.

---

### Маппінг помилок домену → HTTP

Domain-код кидає `django.core.exceptions.ValidationError`.
DRF очікує `rest_framework.exceptions.ValidationError`.

Рішення — кастомний exception handler:

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

---

## Services — Шар бізнес-логіки

### Принцип

Service — це **transport-агностична бізнес-функція**. Вона не знає HTTP, не повертає `Response`, не імпортує DRF. Один і той самий Service викликається з:

- REST API View
- Celery Task
- Django Management Command
- WebSocket consumer
- Pytest тест

### Анатомія stateless service

```python
# apps/flood/services.py

from django.db import transaction
from apps.flood.models import FloodEvent
from apps.flood.tasks import notify_emergency_services_task


def flood_event_create(
    *,                              # keyword-only — захист від помилок порядку аргументів
    region_name: str,
    severity_level: str,
    detected_at,
    created_by,
) -> FloodEvent:
    """
    Єдине місце де живе логіка створення FloodEvent.
    Не повертає Response — повертає доменний об'єкт.
    """
    event = FloodEvent(
        region_name=region_name,
        severity_level=severity_level,
        detected_at=detected_at,
        created_by=created_by,
    )
    event.full_clean()   # Django-валідація на рівні домену
    event.save()

    return event
```

> `*` перед аргументами — це Python-синтаксис для keyword-only параметрів.
> `flood_event_create(region_name="Kyiv", severity_level="high", ...)` — явно, безпечно під час рефакторингу.

### Транзакції та Side Effects

Критичне правило: **side effects (email, Celery task) запускаються лише після успішного commit**.

```python
# apps/flood/services.py

@transaction.atomic
def flood_event_complete_processing(*, event: FloodEvent) -> FloodEvent:
    # 1. Мутація БД
    event.status = 'processed'
    event.save(update_fields=['status'])

    # 2. Side effect — запускається ТІЛЬКИ якщо транзакція закрилась без помилки
    transaction.on_commit(
        lambda: notify_emergency_services_task.delay(event.id)
    )

    return event
```

Якщо написати `notify_emergency_services_task.delay(event.id)` без `on_commit` — Celery може отримати task до того, як запис з'явиться в БД.

### Celery Task — теж transport layer

```python
# apps/flood/tasks.py

@shared_task
def notify_emergency_services_task(event_id: int):
    """Task — це черга доставки, не місце для логіки."""
    from apps.flood.selectors import flood_event_get_by_id
    from apps.flood.services import flood_event_notify

    event = flood_event_get_by_id(event_id=event_id)
    flood_event_notify(event=event)   # логіка — в сервісі
```

### Повний приклад View + Service

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

View: 6 рядків. Вся логіка — у сервісі.

---

## Selectors — Шар читання даних

### Принцип (CQRS-light)

Архітектура розрізняє дві принципово різні операції:

| | **Services** | **Selectors** |
|-|--------------|---------------|
| Що роблять | Мутують дані, оркеструють бізнес | Читають дані |
| Тип операцій | CREATE, UPDATE, DELETE, side effects | SELECT |
| Транзакції | `@transaction.atomic` | Ні |
| Паралельне навантаження | Вертикальне масштабування | Горизонтальне (replica читання) |

### Чому не model property?

```python
# ПОГАНО — прихований запит у Python-циклі → N+1
class FloodEvent(models.Model):
    @property
    def region_display(self):
        return self.region.display_name  # SELECT кожного разу в циклі
```

```python
# ДОБРЕ — оптимізований запит у selector
def flood_events_get_list(*, user) -> QuerySet:
    return (
        FloodEvent.objects
        .filter(created_by=user)
        .select_related('region')      # один JOIN замість N запитів
        .prefetch_related('tags')      # batched prefetch для M2M
        .annotate(
            comment_count=Count('comments')
        )
        .order_by('-detected_at')
    )
```

### Анатомія selector

```python
# apps/flood/selectors.py

def flood_event_get_by_id(*, event_id: int) -> FloodEvent:
    """Базовий selector — повертає об'єкт або кидає 404."""
    try:
        return FloodEvent.objects.get(id=event_id)
    except FloodEvent.DoesNotExist:
        raise FloodEvent.DoesNotExist(f"FloodEvent {event_id} не знайдено")


def flood_events_get_visible_for(*, user) -> QuerySet:
    """
    Ховає SQL-деталі за доменним іменем.
    Повертає QuerySet — View може додати пагінацію або фільтрацію.
    """
    return (
        FloodEvent.objects
        .filter(
            Q(created_by=user) | Q(is_public=True)
        )
        .select_related('region', 'created_by')
        .order_by('-detected_at')
    )
```

### QuerySet vs evaluated list

Selectors можуть повертати:

| Повертає | Коли використовувати |
|----------|----------------------|
| `QuerySet` | View може додати `.filter()`, пагінацію, `django_filters` |
| `list[dict]` | Коли потрібна складна Python-оптимізація перед поверненням |

```python
# Selector що повертає QuerySet — View додає пагінацію
def flood_events_get_list() -> QuerySet:
    return FloodEvent.objects.all().select_related('region')

# У View:
queryset = flood_events_get_list()
page = self.paginate_queryset(queryset)   # DRF пагінація — безпечно
```

### Selector + django-filter без витоку ORM у View

```python
# apps/flood/filters.py

import django_filters
from apps.flood.models import FloodEvent

class FloodEventFilter(django_filters.FilterSet):
    severity = django_filters.ChoiceFilter(choices=FloodEvent.SEVERITY_CHOICES)
    after = django_filters.DateTimeFilter(field_name='detected_at', lookup_expr='gte')

    class Meta:
        model = FloodEvent
        fields = ['severity', 'after']
```

```python
# apps/flood/views.py

class FloodEventListAPIView(ListAPIView):

    def get_queryset(self):
        qs = flood_events_get_visible_for(user=self.request.user)  # selector
        return FloodEventFilter(self.request.GET, queryset=qs).qs  # фільтрація
```

View не знає SQL. Selector не знає фільтрів запиту. Filter не знає бізнес-правил.

---

## Повний Data Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1. HTTP POST /api/flood/events/                                │
│    body: {"region_name": "Kyiv", "severity_level": "high"}    │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. FloodEventCreateAPIView.post()                              │
│    Тонка View — лише HTTP-оркестрація                         │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. FloodEventInputSerializer(data=request.data)                │
│    .is_valid(raise_exception=True)                             │
│    → validated_data = {"region_name": "Kyiv", ...}            │
└───────────────────────┬────────────────────────────────────────┘
                        │ validated_data
                        ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. flood_event_create(**validated_data, created_by=user)       │
│    @transaction.atomic                                         │
│    event.full_clean() → event.save()                           │
│    transaction.on_commit(→ Celery task)                        │
│    return FloodEvent instance                                  │
└───────────────────────┬────────────────────────────────────────┘
                        │ FloodEvent object
                        ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. FloodEventOutputSerializer(event)                           │
│    Форматує доменний об'єкт у JSON                             │
└───────────────────────┬────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────┐
│ 6. Response(output.data, status=201)                           │
└────────────────────────────────────────────────────────────────┘
```

---

## Антипатерни

### Бізнес-логіка в serializer.save()

```python
# ПОГАНО
class FloodEventSerializer(serializers.ModelSerializer):
    def save(self):
        self.instance.notify_emergency_services()  # бізнес-логіка в серіалайзері
        super().save()
```

```python
# ДОБРЕ
# View → Service → окремий виклик notification
event = flood_event_create(**validated_data)
flood_event_notify(event=event)
```

### HTTP об'єкти в service

```python
# ПОГАНО
def process_flood(request):
    user = request.user       # Service знає про HTTP request
    data = request.data
```

```python
# ДОБРЕ
def flood_event_create(*, region_name: str, created_by):
    pass   # Service отримує вже розпарсені дані
```

### ORM в View

```python
# ПОГАНО
class FloodListView(APIView):
    def get(self, request):
        events = FloodEvent.objects.filter(
            created_by=request.user
        ).select_related('region')   # ORM прямо у View
```

```python
# ДОБРЕ
class FloodListView(APIView):
    def get(self, request):
        events = flood_events_get_visible_for(user=request.user)  # Selector
```

### Business logic в Celery task

```python
# ПОГАНО
@shared_task
def process_flood_task(event_id):
    event = FloodEvent.objects.get(id=event_id)
    event.status = 'processed'
    event.save()
    send_email(event.created_by.email, ...)   # логіка прямо в task
```

```python
# ДОБРЕ
@shared_task
def process_flood_task(event_id):
    event = flood_event_get_by_id(event_id=event_id)
    flood_event_complete_processing(event=event)   # делегація в service
```

---

## Таблиця відповідальностей

| Шар | Повинен | НЕ повинен |
|-----|---------|------------|
| **View** | Обробляти HTTP, викликати серіалайзер і service, повертати Response | Знати SQL, містити бізнес-логіку, робити ORM-запити |
| **InputSerializer** | Валідувати типи і формати, трансформувати дані, повертати `validated_data` | Зберігати в БД, містити бізнес-правила |
| **OutputSerializer** | Форматувати доменний об'єкт у JSON-структуру | Робити запити до БД, містити логіку |
| **Service** | Оркеструвати бізнес-операції, відкривати транзакції, запускати side effects | Знати HTTP, імпортувати DRF, повертати Response |
| **Selector** | Читати дані з БД, оптимізувати запити (`select_related`, `annotate`) | Мутувати дані, містити бізнес-логіку |
| **ORM / Model** | Описувати схему БД і відносини | Містити бізнес-оркестрацію, знати HTTP |
| **Celery Task** | Транспортувати виклик у чергу, делегувати в service | Містити бізнес-логіку |

---

## Структура файлів у app

```
apps/flood/
    ├── models.py          ← Схема БД
    ├── selectors.py       ← Читання даних (SELECT + оптимізація)
    ├── services.py        ← Бізнес-логіка (CREATE / UPDATE / DELETE + side effects)
    ├── serializers.py     ← Input/Output контракти (HTTP ↔ domain)
    ├── views.py           ← Тонкий HTTP-оркестратор
    ├── urls.py            ← URL маршрути
    ├── tasks.py           ← Celery tasks (транспорт, не логіка)
    ├── filters.py         ← django-filter
    ├── permissions.py     ← DRF permissions
    ├── admin.py           ← Адмін-конфігурація
    ├── tests/
    └── migrations/
```

---

## Ментальна модель: три межі

```
┌─────────────────────────────────────────────────────┐
│  TRANSPORT LAYER                                    │
│  views.py + serializers.py + tasks.py               │
│  "Як дані приходять і куди йдуть"                   │
├─────────────────────────────────────────────────────┤
│  APPLICATION LAYER                                  │
│  services.py                                        │
│  "ЩО система робить"                               │
├─────────────────────────────────────────────────────┤
│  DATA LAYER                                         │
│  selectors.py + models.py + ORM                     │
│  "Звідки і як беруться дані"                        │
└─────────────────────────────────────────────────────┘
```

Правило: **кожен шар знає лише про шар безпосередньо під ним**.
View → Service → Selector → ORM. Ніяких стрибків через шари.

---

## Зв'язок з рештою документації

| Тема | Файл |
|------|------|
| Загальна архітектура Django | [django_architecture.md](django_architecture.md) |
| ORM, QuerySet, N+1, транзакції | [Django_ORM.md](Django_ORM.md) |
| Views: FBV, CBV, Generic | [Django_Views.md](Django_Views.md) |
| Архітектурні схеми (Mermaid) | [django_mermaid.md](django_mermaid.md) |
| Структура проєкту | [DJANGO_PROJECT_STRUCTURE.md](DJANGO_PROJECT_STRUCTURE.md) |
