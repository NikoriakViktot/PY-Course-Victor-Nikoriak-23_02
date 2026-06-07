# Django Serializers — Transport Layer

> `serializers.py` — це межа між HTTP і доменом.
> Serializer не знає бізнес-логіки. Він лише:
> приймає сирі HTTP-дані → валідує → повертає `validated_data`,
> або приймає доменний об'єкт → форматує → повертає JSON.

---

## Що таке Serializer архітектурно

```
HTTP Request
    │  {"region_name": "Kyiv", "severity": "high"}
    ▼
InputSerializer.is_valid()
    │  validated_data = {"region_name": "Kyiv", "severity": "high"}
    ▼
Service
    │  FloodEvent object
    ▼
OutputSerializer(event)
    │  {"id": 1, "region_name": "Kyiv", ...}
    ▼
HTTP Response
```

Serializer — це **охоронець на вході та форматувальник на виході**.

| Клас | Напрям | Роль |
|------|--------|------|
| `InputSerializer` | HTTP → Domain | Валідація типів, форматів, cross-field правил |
| `OutputSerializer` | Domain → HTTP | Форматування відповіді, вибір полів |

---

## Проблема: ModelSerializer антипатерн

`ModelSerializer` — це зручний клас, що автоматично генерує поля з моделі.

```python
# ПОГАНО — ModelSerializer тісно прив'язаний до схеми БД
class FloodEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloodEvent
        fields = '__all__'
```

**Що ламається:**
- Зміна моделі → автоматична зміна API (несподівано для клієнтів)
- Один серіалайзер для читання І запису → неявний контракт
- Бізнес-поля (наприклад, `created_by` як ForeignKey) протікають у відповідь як ID
- Логіка в `serializer.save()` — бізнес-логіка у transport layer

### Коли ModelSerializer прийнятний

`ModelSerializer` підходить для простих CRUD-ендпоінтів де модель і API збігаються. Для складних workflow — явні `InputSerializer` і `OutputSerializer`.

---

## InputSerializer — Валідація вхідних даних

### Основа: `serializers.Serializer`

```python
# apps/flood/serializers.py

class FloodEventInputSerializer(serializers.Serializer):
    region_name    = serializers.CharField(max_length=200)
    severity_level = serializers.ChoiceField(choices=['low', 'medium', 'high'])
    detected_at    = serializers.DateTimeField()
```

Базовий `Serializer` (не `ModelSerializer`) дає явний контракт:
- Поля не залежать від схеми БД
- Зміна моделі не змінює API автоматично
- Одразу зрозуміло що очікується від клієнта

### Використання у View

```python
# apps/flood/views.py

class FloodEventCreateAPIView(APIView):

    def post(self, request):
        serializer = FloodEventInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # validated_data — гарантовано чисті, перевірені дані
        event = flood_event_create(**serializer.validated_data, created_by=request.user)

        output = FloodEventOutputSerializer(event)
        return Response(output.data, status=status.HTTP_201_CREATED)
```

`raise_exception=True` — якщо валідація не пройшла, DRF автоматично повертає HTTP 400 з описом помилок. Без зайвого `if not serializer.is_valid(): return Response(...)`.

---

## OutputSerializer — Форматування відповіді

```python
class FloodEventOutputSerializer(serializers.Serializer):
    id             = serializers.IntegerField()
    region_name    = serializers.CharField()
    severity_level = serializers.CharField()
    detected_at    = serializers.DateTimeField()
    created_by     = serializers.EmailField(source='created_by.email')
    created_at     = serializers.DateTimeField()
```

`source='created_by.email'` — замість того щоб повертати `created_by: 42` (ID), повертаємо email. Клієнт отримує що потрібно, не внутрішні деталі БД.

### Список об'єктів

```python
# many=True — серіалізація QuerySet або list
events = flood_events_get_list()
output = FloodEventOutputSerializer(events, many=True)
return Response(output.data)
```

### Вкладені об'єкти

```python
class RegionOutputSerializer(serializers.Serializer):
    id           = serializers.IntegerField()
    display_name = serializers.CharField()


class FloodEventOutputSerializer(serializers.Serializer):
    id             = serializers.IntegerField()
    region         = RegionOutputSerializer()   # вкладений об'єкт
    severity_level = serializers.CharField()
```

> Якщо вкладені серіалайзери провокують N+1 запити — переходь на pure Python функцію (див. розділ нижче).

---

## Поля серіалайзера — довідник

### Базові типи

| Поле | Python тип | Приклад |
|------|-----------|---------|
| `CharField` | `str` | назви, описи |
| `IntegerField` | `int` | ID, кількості |
| `FloatField` | `float` | координати, числа |
| `BooleanField` | `bool` | прапорці |
| `DateTimeField` | `datetime` | мітки часу |
| `DateField` | `date` | дати без часу |
| `EmailField` | `str` (з валідацією email) | адреси |
| `URLField` | `str` (з валідацією URL) | посилання |
| `UUIDField` | `UUID` | унікальні ідентифікатори |

### Вибір зі списку

```python
severity = serializers.ChoiceField(choices=['low', 'medium', 'high'])

# Або через константи з моделі
severity = serializers.ChoiceField(choices=FloodEvent.SEVERITY_CHOICES)
```

### Опціональні та дефолтні поля

```python
# Поле не обов'язкове — якщо не передано, буде None
description = serializers.CharField(required=False, allow_null=True)

# Поле не обов'язкове — якщо не передано, буде дефолтне значення
page_size = serializers.IntegerField(required=False, default=20)
```

### Тільки для читання / тільки для запису

```python
# read_only — поле є у відповіді, але не приймається у запиті
id         = serializers.IntegerField(read_only=True)
created_at = serializers.DateTimeField(read_only=True)

# write_only — поле приймається у запиті, але не повертається у відповіді
password   = serializers.CharField(write_only=True)
```

### SerializerMethodField — обчислювані поля

```python
class FloodEventOutputSerializer(serializers.Serializer):
    id             = serializers.IntegerField()
    severity_label = serializers.SerializerMethodField()

    def get_severity_label(self, obj) -> str:
        labels = {'low': 'Низький', 'medium': 'Середній', 'high': 'Високий'}
        return labels.get(obj.severity_level, obj.severity_level)
```

---

## validate() — Крос-польова валідація

`validate(self, data)` виконується після того як всі окремі поля перевірено. Це точка для:
- валідації залежностей між полями
- автогенерації значень (slug, token)
- трансформації даних перед `validated_data`

```python
class EventRangeInputSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date   = serializers.DateField()

    def validate(self, data: dict) -> dict:
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError(
                "end_date не може бути раніше ніж start_date"
            )
        return data
```

### Автогенерація поля в validate()

```python
class FloodEventInputSerializer(serializers.Serializer):
    region_name = serializers.CharField()
    slug        = serializers.SlugField(read_only=True)  # генерується сервером

    def validate(self, data: dict) -> dict:
        data['slug'] = slugify(data['region_name'])
        return data
```

> `read_only=True` обов'язково — інакше DRF вимагатиме `slug` у запиті і впаде до виклику `validate()`.

### validate_`<field>`() — Валідація одного поля

```python
class UserRegisterInputSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email вже зареєстрований")
        return value.lower()   # трансформація — нормалізуємо до нижнього регістру

    def validate_password(self, value: str) -> str:
        if len(value) < 8:
            raise serializers.ValidationError("Мінімум 8 символів")
        return value
```

---

## Порядок виконання валідації

```
1. Парсинг тіла запиту (JSON → Python dict)
        │
        ▼
2. Перевірка кожного поля окремо
   CharField(max_length=200)? → перевіряє
   ChoiceField(choices=[...])? → перевіряє
        │
        ▼
3. validate_<field>() для кожного поля
   validate_email() → перевіряє унікальність
        │
        ▼
4. validate() → крос-польова валідація
   end_date > start_date?
        │
        ▼
5. validated_data — гарантовано чисті дані
        │
        ▼
6. View передає validated_data у Service
```

Якщо будь-який крок кидає `ValidationError` — подальші кроки не виконуються, клієнт отримує HTTP 400.

---

## Маппінг помилок домену на HTTP

Service викликає `full_clean()` і кидає `django.core.exceptions.ValidationError`.
DRF очікує `rest_framework.exceptions.ValidationError`.

Без налаштування Django поверне HTML-сторінку 500 замість JSON 400.

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

Після цього: `full_clean()` у будь-якому Service → автоматично JSON 400.

---

## Складна серіалізація — Pure Python функція

Коли OutputSerializer провокує N+1 або структура відповіді занадто складна:

```python
# apps/flood/serializers.py  (або selectors.py)

def flood_feed_serialize(events) -> list[dict]:
    """
    Замість вкладеного OutputSerializer — Python функція
    після одного оптимізованого SQL-запиту.
    """
    region_cache: dict[int, str] = {}

    result = []
    for event in events:
        region_id = event.region_id
        if region_id not in region_cache:
            region_cache[region_id] = event.region.display_name  # вже в select_related

        result.append({
            'id': event.id,
            'region': region_cache[region_id],
            'severity': event.severity_level,
            'detected_at': event.detected_at.isoformat(),
            'image_count': event.image_count,  # з annotate()
        })

    return result
```

```python
# views.py
events = flood_events_get_list()   # selector: select_related + annotate
data   = flood_feed_serialize(events)
return Response(data)
```

Перевага: повний контроль над SQL footprint. Selector робить один оптимізований запит, Python будує структуру — без прихованих запитів від вкладених серіалайзерів.

---

## Повний приклад: CRUD endpoint

```python
# apps/flood/serializers.py

class FloodEventInputSerializer(serializers.Serializer):
    region_name    = serializers.CharField(max_length=200)
    severity_level = serializers.ChoiceField(choices=['low', 'medium', 'high'])
    detected_at    = serializers.DateTimeField()

    def validate_region_name(self, value: str) -> str:
        return value.strip().title()


class FloodEventUpdateInputSerializer(serializers.Serializer):
    severity_level = serializers.ChoiceField(choices=['low', 'medium', 'high'])
    detected_at    = serializers.DateTimeField(required=False)


class FloodEventOutputSerializer(serializers.Serializer):
    id             = serializers.IntegerField()
    region_name    = serializers.CharField()
    severity_level = serializers.CharField()
    detected_at    = serializers.DateTimeField()
    created_by     = serializers.EmailField(source='created_by.email')
    created_at     = serializers.DateTimeField()
```

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

        return Response(
            FloodEventOutputSerializer(event).data,
            status=status.HTTP_201_CREATED,
        )


class FloodEventDetailAPIView(APIView):

    def get(self, request, event_id: int):
        event = flood_event_get_by_id(event_id=event_id)
        return Response(FloodEventOutputSerializer(event).data)

    def patch(self, request, event_id: int):
        event = flood_event_get_by_id(event_id=event_id)

        serializer = FloodEventUpdateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = flood_event_update(event=event, **serializer.validated_data)

        return Response(FloodEventOutputSerializer(event).data)
```

---

## Типові помилки

### Логіка в `save()`

```python
# ПОГАНО — бізнес-логіка у transport layer
class FloodEventSerializer(serializers.ModelSerializer):
    def save(self):
        instance = super().save()
        send_notification_email(instance)   # side effect у серіалайзері
        return instance
```

```python
# ДОБРЕ — логіка у Service
event = flood_event_create(**serializer.validated_data)
# Service відповідає за notification через on_commit + Celery
```

### Прямий `queryset` у серіалайзері

```python
# ПОГАНО — серіалайзер робить запити до БД
class FloodEventOutputSerializer(serializers.Serializer):
    related_events = serializers.SerializerMethodField()

    def get_related_events(self, obj):
        return FloodEvent.objects.filter(region=obj.region).count()  # N+1
```

```python
# ДОБРЕ — annotate у Selector, передати в серіалайзер
class FloodEventOutputSerializer(serializers.Serializer):
    related_count = serializers.IntegerField()  # з annotate() у selector
```

### Один серіалайзер для запису і читання

```python
# ПОГАНО — невиразний контракт
class FloodEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloodEvent
        fields = ['id', 'region_name', 'severity_level', 'created_by']
        # id — тільки для читання, created_by — тільки для читання,
        # але це не очевидно з коду
```

```python
# ДОБРЕ — явні окремі класи
class FloodEventInputSerializer(serializers.Serializer):
    region_name    = serializers.CharField()
    severity_level = serializers.ChoiceField(choices=[...])

class FloodEventOutputSerializer(serializers.Serializer):
    id             = serializers.IntegerField()
    region_name    = serializers.CharField()
    severity_level = serializers.CharField()
    created_by     = serializers.EmailField(source='created_by.email')
```

---

## Таблиця: Serializer не повинен

| Дія | Чому ні |
|-----|---------|
| Зберігати у БД (`save()` з логікою) | Це Service |
| Робити ORM-запити у `SerializerMethodField` | N+1, це Selector |
| Містити бізнес-правила | Це Service або `full_clean()` на моделі |
| Знати про `transaction.atomic` | Це Service |
| Знати про Celery tasks | Це Service |
| Повертати `Response` | Це View |

---

## Швидка шпаргалка

```python
# serializers.py — шаблон

class <Model>InputSerializer(serializers.Serializer):
    """Контракт вхідних даних. Незалежний від моделі."""
    <field_1> = serializers.<FieldType>(...)
    <field_2> = serializers.<FieldType>(...)

    def validate_<field_1>(self, value):
        # Валідація одного поля
        return value

    def validate(self, data: dict) -> dict:
        # Крос-польова валідація або трансформація
        return data


class <Model>OutputSerializer(serializers.Serializer):
    """Контракт вихідних даних. Що клієнт бачить у відповіді."""
    id        = serializers.IntegerField()
    <field_1> = serializers.<FieldType>()
    <computed> = serializers.SerializerMethodField()

    def get_<computed>(self, obj):
        return ...
```

---

## Зв'язок з рештою документації

| Тема | Файл |
|------|------|
| Services (що робити з `validated_data`) | [DJANGO_SERVICES.md](DJANGO_SERVICES.md) |
| Selectors (як підготувати дані для OutputSerializer) | [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) |
| Services + Selectors + Serializers (повна картина) | [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) |
| Views: як поєднати все разом | [Django_Views.md](Django_Views.md) |
