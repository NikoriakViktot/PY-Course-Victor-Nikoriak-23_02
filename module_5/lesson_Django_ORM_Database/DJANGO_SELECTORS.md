# Django Selectors — Шар читання даних

> `selectors.py` — це окремий файл у кожному Django app,
> де живуть усі ORM-запити для ЧИТАННЯ даних.
> Selector — це **іменований, перевикористовуваний запит**.

---

## Проблема без Selectors

У будь-якому Django-проєкті дуже швидко з'являється такий код:

```python
# views.py
Post.objects.filter(is_active=True, published_at__lte=timezone.now())

# tasks.py
Post.objects.filter(is_active=True, published_at__lte=timezone.now())

# admin.py
Post.objects.filter(is_active=True, published_at__lte=timezone.now())

# services.py
Post.objects.filter(is_active=True, published_at__lte=timezone.now())
```

Один і той самий запит скопійований у 20 місцях.

**Що відбувається далі:**
- Змінилась бізнес-логіка (додали нове поле `is_deleted`) — потрібно оновити 20 місць
- Кожен розробник пише запит трохи по-іншому — розбіжності в поведінці
- Не зрозуміло, де централізовано оптимізувати `select_related`
- Код читається як SQL, а не як бізнес-домен

---

## Рішення: Selector

```python
# apps/blog/selectors.py

from django.utils import timezone
from apps.blog.models import Post


def get_published_posts():
    return Post.objects.filter(
        is_active=True,
        published_at__lte=timezone.now()
    )
```

Тепер усюди:

```python
# views.py
from apps.blog.selectors import get_published_posts

posts = get_published_posts()

# tasks.py
posts = get_published_posts()

# services.py
posts = get_published_posts()
```

Логіка в одному місці. Зміна — в одному місці.

---

## Що таке Selector архітектурно

Selector — це **абстракція над наміром запиту**.

| Рівень | Що відповідає | Приклад |
|--------|---------------|---------|
| PostgreSQL | Зберігає дані | `SELECT ... WHERE ...` |
| ORM | Як отримати дані | `Post.objects.filter(...)` |
| **Selector** | **ЩО ми хочемо (бізнес-мова)** | `get_published_posts()` |
| View / Service | Оркестрація | `posts = get_published_posts()` |

Selector ховає ORM і повертає **доменне ім'я**:

```python
# ORM — технічна мова
Post.objects.filter(Q(author=user) | Q(is_public=True)).select_related('author')

# Selector — доменна мова
get_visible_posts_for_user(user=user)
```

---

## CQRS-light: Reads vs Writes

В архітектурі Django бізнес-шар ділиться на дві чіткі ролі:

```
services.py   →   WRITE / Зміна стану
selectors.py  →   READ  / Читання стану
```

Це спрощений варіант патерну **CQRS** (Command Query Responsibility Segregation):

| | **Services** | **Selectors** |
|-|--------------|---------------|
| Роль | Command — змінює стан | Query — читає стан |
| Операції | CREATE, UPDATE, DELETE | SELECT |
| Транзакції | `@transaction.atomic` | Ні |
| Side effects | Так (email, Celery) | Ніколи |
| Повертає | Доменний об'єкт після змін | QuerySet або дані |

> **Головне правило:** Selector **ніколи** не змінює дані.

```python
# ПОГАНО — selector що мутує дані
def get_or_create_user(email):
    user, _ = User.objects.get_or_create(email=email)  # CREATE — це не selector
    return user

# ДОБРЕ — розділити
# selectors.py
def get_user_by_email(*, email: str):
    return User.objects.filter(email=email).first()

# services.py
def user_create(*, email: str, name: str) -> User:
    user = User(email=email, name=name)
    user.full_clean()
    user.save()
    return user
```

---

## Анатомія Selector

### Базові правила (ті самі що й для Services)

- Живе в `<app_name>/selectors.py`
- Stateless Python функція (не клас)
- Keyword-only аргументи (`*`) — захист від помилок порядку
- Строгі type annotations
- Не знає HTTP, не імпортує DRF

```python
# apps/flood/selectors.py

from django.db.models import QuerySet, Count
from apps.flood.models import FloodEvent, Region


def flood_event_get_by_id(*, event_id: int) -> FloodEvent:
    """Повертає один об'єкт або кидає DoesNotExist."""
    return FloodEvent.objects.get(id=event_id)


def flood_events_get_for_region(*, region_id: int) -> QuerySet:
    """Всі події для регіону з оптимізованими JOIN-ами."""
    return (
        FloodEvent.objects
        .filter(region_id=region_id)
        .select_related('region', 'created_by')
        .prefetch_related('satellite_images')
        .order_by('-detected_at')
    )


def flood_events_get_visible_for(*, user) -> QuerySet:
    """
    Ховає складну Q-логіку за доменним іменем.
    Клієнт не знає деталей фільтрації.
    """
    from django.db.models import Q
    return (
        FloodEvent.objects
        .filter(Q(created_by=user) | Q(is_public=True))
        .select_related('region')
        .annotate(image_count=Count('satellite_images'))
        .order_by('-detected_at')
    )
```

---

## Централізація ORM-оптимізацій

Головна технічна перевага Selector — **N+1 вирішується в одному місці**.

### Проблема: query у model property

```python
# ПОГАНО — прихований запит при кожному зверненні
class FloodEvent(models.Model):

    @property
    def region_name(self):
        return self.region.display_name   # SELECT кожного разу

# У шаблоні або серіалайзері:
for event in events:           # 1 запит
    print(event.region_name)   # + N запитів → N+1 катастрофа
```

### Рішення: select_related в Selector

```python
# ДОБРЕ — один JOIN на рівні SQL
def flood_events_get_list() -> QuerySet:
    return (
        FloodEvent.objects
        .all()
        .select_related('region')          # JOIN для ForeignKey
        .prefetch_related('tags')          # batched SELECT для M2M
        .annotate(
            comment_count=Count('comments')  # обчислюється в SQL, не Python
        )
    )

# Тепер у циклі — НУЛЬ додаткових запитів
for event in flood_events_get_list():
    print(event.region.display_name)   # вже є в пам'яті
    print(event.comment_count)         # вже є з annotate
```

### Коли що використовувати

| ORM метод | Коли | Тип зв'язку |
|-----------|------|-------------|
| `select_related()` | ForeignKey, OneToOne | JOIN на рівні SQL |
| `prefetch_related()` | ManyToMany, зворотній FK | Окремий SELECT + Python join |
| `annotate()` | Агрегати, обчислення | SQL GROUP BY / підзапит |
| `only(*fields)` | Величезні моделі, потрібно 2-3 поля | Часткова SELECT |
| `defer(*fields)` | Виключити важкі поля (напр. TextField) | Часткова SELECT |

---

## QuerySet vs evaluated результат

Selector може повертати два типи:

### QuerySet (не виконаний запит)

```python
def flood_events_get_list() -> QuerySet:
    return FloodEvent.objects.filter(is_active=True).select_related('region')
```

**Коли:** View може безпечно додати пагінацію, `django_filters`, `.count()`.

```python
# View
queryset = flood_events_get_list()

# DRF пагінація — safe, QuerySet ще не виконаний
page = self.paginate_queryset(queryset)
```

### Evaluated list / dict

```python
def flood_events_get_summary(*, user) -> list[dict]:
    """Складна структура — будуємо через Python після одного SQL."""
    events = (
        FloodEvent.objects
        .filter(created_by=user)
        .select_related('region')
        .values('id', 'region__display_name', 'severity_level', 'detected_at')
    )

    return [
        {
            'id': e['id'],
            'region': e['region__display_name'],
            'severity': e['severity_level'],
            'detected_at': e['detected_at'].isoformat(),
        }
        for e in events
    ]
```

**Коли:** Складна трансформація даних, in-memory кеш, обходимо обмеження вкладених серіалайзерів.

---

## Selector + django-filter (без витоку ORM у View)

```python
# apps/flood/filters.py
import django_filters
from apps.flood.models import FloodEvent

class FloodEventFilter(django_filters.FilterSet):
    severity  = django_filters.ChoiceFilter(choices=FloodEvent.SEVERITY_CHOICES)
    after     = django_filters.DateTimeFilter(field_name='detected_at', lookup_expr='gte')

    class Meta:
        model  = FloodEvent
        fields = ['severity', 'after']
```

```python
# apps/flood/views.py
class FloodEventListAPIView(ListAPIView):

    def get_queryset(self):
        qs = flood_events_get_visible_for(user=self.request.user)  # selector
        return FloodEventFilter(self.request.GET, queryset=qs).qs  # фільтр
```

View не знає SQL. Selector не знає про query params. Filter не знає бізнес-правил.

---

## Повний workflow

```
HTTP GET /api/flood/events/?severity=high
        │
        ▼
┌──────────────────────────────────────┐
│  View                                │
│  Викликає selector                   │
│  Передає QuerySet у фільтр           │
│  Пагінує результат                   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  Selector                            │
│  flood_events_get_visible_for(user)  │
│  select_related('region')            │
│  annotate(image_count=Count(...))    │
│  Повертає QuerySet                   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  ORM                                 │
│  Компілює в оптимальний SQL          │
│  SELECT flood_event.*, region.*,     │
│         COUNT(images.id)             │
│  FROM flood_event                    │
│  JOIN region ON ...                  │
│  WHERE (created_by=$1 OR is_public)  │
│  AND severity='high'                 │
└──────────────┬───────────────────────┘
               │
               ▼
         PostgreSQL
               │
               ▼
    Один оптимізований запит
```

---

## Naming Convention

Selectors мають називатись так, щоб читались як бізнес-фрази:

```python
# Отримати один об'єкт
user_get_by_id(*, user_id: int) -> User
flood_event_get_by_id(*, event_id: int) -> FloodEvent

# Отримати список
flood_events_get_list() -> QuerySet
flood_events_get_visible_for(*, user) -> QuerySet
users_get_active() -> QuerySet

# Отримати з фільтром
papers_get_unvalidated() -> QuerySet
jobs_get_failed_since(*, since: datetime) -> QuerySet
dem_candidates_get_best_for_region(*, region_id: int) -> QuerySet
```

Назва говорить **ЩО** потрібно. ORM всередині — **ЯК** це отримати.

---

## Чого НЕ повинен робити Selector

| Дія | Чому ні |
|-----|---------|
| `obj.save()` | Це мутація — робота Service |
| `obj.delete()` | Це мутація — робота Service |
| `get_or_create()` | Мутує дані — це Service |
| Відкривати `@transaction.atomic` | Тільки Service відповідає за транзакції |
| Надсилати email або запускати Celery | Side effects — тільки Service |
| Знати про `request` або `Response` | Selector не знає HTTP |

---

## Швидка шпаргалка

```python
# selectors.py — шаблон

from apps.<app>.models import <Model>


def <model>_get_by_id(*, <model>_id: int) -> <Model>:
    return <Model>.objects.get(id=<model>_id)


def <model>s_get_list() -> QuerySet:
    return (
        <Model>.objects
        .all()
        .select_related('<fk_field>')
        .prefetch_related('<m2m_field>')
        .order_by('-created_at')
    )


def <model>s_get_for_<condition>(*, <param>) -> QuerySet:
    return (
        <Model>.objects
        .filter(<field>=<param>)
        .select_related('<fk_field>')
    )
```

---

## Зв'язок з рештою документації

| Тема | Файл |
|------|------|
| Services (бізнес-логіка, мутації, транзакції) | [DJANGO_SERVICES.md](DJANGO_SERVICES.md) |
| Services + Selectors + Serializers (повна картина) | [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) |
| ORM: QuerySet API, N+1, `select_related` | [DJANGO_ORM_DEEP.md](DJANGO_ORM_DEEP.md) |
| Views: як викликати Selector з View | [notes_project/README.md](notes_project/README.md) — Крок 8 |
