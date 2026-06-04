# Advanced Django Templates — Архітектура Production-рівня

> Продовження `DJANGO_TEMPLATES_BOOTSTRAP.md` і `DJANGO_NINJA_TEMPLATES.md`.
> Тут — Context Processors, Custom Template Tags, crispy-forms,
> Vite asset pipeline, SaaS Dashboard Architecture.

---


## Зміст

- [1. Context Processors — глобальний контекст](#1-context-processors--глобальний-контекст)
- [2. Custom Template Tags — simple_tag, inclusion_tag, filter](#2-custom-template-tags--simple_tag-inclusion_tag-filter)
- [3. crispy-forms — Python-лейаут форм](#3-crispy-forms--python-лейаут-форм)
- [4. Vite + ManifestStaticFilesStorage — сучасний asset pipeline](#4-vite--manifeststaticfilesstorage--сучасний-asset-pipeline)
- [5. SaaS Dashboard Architecture — sidebar, CRUD, reusable components](#5-saas-dashboard-architecture--sidebar-crud-reusable-components)
- [6. Jinja2 Deep Dive — macros, Environment, bytecode cache](#6-jinja2-deep-dive--macros-environment-bytecode-cache)
- [7. HTMX Architecture — повний lifecycle, Server-Driven UI](#7-htmx-architecture--повний-lifecycle-server-driven-ui)
- [8. Питання для самоперевірки](#8-питання-для-самоперевірки)
---

---
- **🧠 Ментальна модель:** Context Processors — це "глобальні змінні" для шаблонів. Уяви, що є дані, які потрібні КОЖНОМУ шаблону у твоєму проєкті — ім'я сайту, кількість сповіщень, поточний користувач. Без context processors ти мусиш передавати ці дані вручну в кожному view. Context processors автоматично "вводять" ці дані в кожен шаблон, як ніби вони завжди там були.
- **📚 Чому це існує:** Django навмисно розділяє логіку (views) від представлення (templates). Context processors — це офіційний механізм передачі "ambient" даних (даних навколишнього середовища) у шаблони без зв'язування кожного view вручну.
- **🌐 Що відбувається під капотом:** При кожному виклику `render(request, template, context)` Django збирає всі зареєстровані context processors, викликає кожен з них, передаючи `request`, отримує dict від кожного, потім ЗЛИВАЄ всі ці dicts разом з context, який ти передав з view. Тільки після цього шаблон рендериться з об'єднаним контекстом.
- **❌ Типова помилка початківця:** Забути зареєструвати кастомний context processor у `settings.py` → змінна в шаблоні просто порожня, без помилок. Ще гірше — робити важкий DB-запит у context processor без кешування. Він виконується на КОЖЕН HTTP-запит.
---

## §1. Context Processors — глобальний контекст

Context processors вирішують класичну проблему DRY (Don't Repeat Yourself) у Django views. Розглянемо спочатку, що відбувається БЕЗ них — і чому це погано.

Уяви, що кожен view мусить вручну збирати дані, потрібні кожному шаблону:

```python
# ❌ Без context processors: кожен view мусить це робити:
def notes_view(request):
    return render(request, 'notes.html', {
        'user': request.user,
        'site_name': settings.SITE_NAME,
        'notifications_count': Notification.objects.filter(user=request.user).count(),
        # ... кожен view мусить повторювати це
    })

def dashboard_view(request):
    return render(request, 'dashboard.html', {
        'user': request.user,           # ← копія
        'site_name': settings.SITE_NAME, # ← копія
        'notifications_count': ...,      # ← копія
    })
```

Context processors вирішують це: вони запускаються ОДИН РАЗ за запит і автоматично додають дані до КОЖНОГО шаблону. Ось як виглядає ланцюг виклику:

```
Request arrives
     ↓
Django calls each context processor in CONTEXT_PROCESSORS list
     ↓
Each processor returns a dict
     ↓
All dicts are MERGED into the template context
     ↓
Template renders with merged context
```

Зверни увагу: вбудований `django.contrib.auth.context_processors.auth` додає `{{ user }}` і `{{ perms }}` до КОЖНОГО шаблону — саме тому ти можеш використовувати `{{ user.username }}` у будь-якому шаблоні без додавання цього в кожен view.

### Проблема без Context Processors

Нижче — конкретна демонстрація проблеми: два звичайних view, які вимушені повторювати один і той самий код збору даних контексту:

```python
# ❌ Повторюємо в кожному view
def notes_list(request):
    return render(request, 'notes/list.html', {
        'user': request.user,
        'site_name': 'MyApp',
        'unread_count': Notification.objects.filter(user=request.user, read=False).count(),
    })

def notes_detail(request, pk):
    return render(request, 'notes/detail.html', {
        'user': request.user,           # ← знову
        'site_name': 'MyApp',           # ← знову
        'unread_count': ...,            # ← знову
    })
```

### Вбудовані Context Processors

Django постачається з набором вбудованих context processors. Ці рядки у `settings.py` визначають, які з них активні. Кожен процесор — це Python-функція, що приймає `request` і повертає dict:

```python
# settings.py — TEMPLATES → OPTIONS → context_processors
'context_processors': [
    'django.template.context_processors.debug',      # {{ debug }}
    'django.template.context_processors.request',    # {{ request }}
    'django.contrib.auth.context_processors.auth',   # {{ user }}, {{ perms }}
    'django.contrib.messages.context_processors.messages',  # {{ messages }}
],
```

| Процесор | Що додає в контекст | Коли використовувати |
|----------|---------------------|----------------------|
| `debug` | `{{ debug }}` — True/False | Умовне відображення debug-блоків |
| `request` | `{{ request.user }}`, `{{ request.path }}` | Navbar з поточним URL, breadcrumbs |
| `auth` | `{{ user }}`, `{{ perms.app.permission }}` | Auth check у шаблонах |
| `messages` | `{% for msg in messages %}` | Django Messages → Bootstrap Alert |

### Кастомний Context Processor

Тут ми пишемо власний context processor. Зверни увагу на структуру: це звичайна Python-функція, яка приймає `request` і повертає dict. Django сам турбується про виклик цієї функції та злиття результату з контекстом шаблону:

```python
# hello_app/context_processors.py

from .models import Notification

def global_context(request):
    """Дані для всіх шаблонів додатку."""
    context = {
        'site_name': 'Bootstrap Notes',
        'site_version': '2.0',
    }
    
    # Тільки для авторизованих
    if request.user.is_authenticated:
        context['unread_notifications'] = (
            Notification.objects
            .filter(user=request.user, read=False)
            .count()
        )
    
    return context
```

Після написання функції її треба зареєструвати в `settings.py`. Django не "знаходить" context processors автоматично — кожен треба додати вручну:

```python
# settings.py — реєстрація
'context_processors': [
    ...
    'hello_app.context_processors.global_context',  # ← додати
],
```

Після реєстрації змінна `unread_notifications` стає доступною у БУДЬ-ЯКОМУ шаблоні проєкту — без жодного рядка коду у view:

```html
{# base.html — тепер доступно скрізь без передачі з view #}
<span class="badge bg-danger">{{ unread_notifications }}</span>
```

### Ланцюг виклику Context Processors

Ця діаграма показує точний порядок, в якому Django збирає контекст перед рендерингом шаблону. Важливо: context view ПЕРЕКРИВАЄ однакові ключі з context processors — view завжди має пріоритет:

```
RequestFactory
    ↓ request
    ↓
Context Processors (всі викликаються для кожного render())
    ↓ merged dict
    ↓
View context (перекриває однакові ключі)
    ↓
Template Engine
```

> **Правило:** Context Processor не повинен робити важких запитів без кешування.
> Він виконується для **кожного** HTTP request.

### Кешування у Context Processor

Це критично важливий патерн для production. Оскільки context processor виконується на КОЖЕН запит, DB-запит у ньому без кешування може спричинити сотні зайвих запитів на секунду. Тут показано правильний підхід з Redis/Memcached кешем через Django cache framework:

```python
from django.core.cache import cache

def global_context(request):
    if request.user.is_authenticated:
        cache_key = f'unread_count_{request.user.pk}'
        count = cache.get(cache_key)
        if count is None:
            count = Notification.objects.filter(
                user=request.user, read=False
            ).count()
            cache.set(cache_key, count, timeout=60)  # 1 хвилина
        return {'unread_notifications': count}
    return {}
```

---

---
- **🧠 Ментальна модель:** Custom Template Tags — це Python-функції, які можна викликати ПРЯМО З ШАБЛОНІВ. Django Template Language (DTL) навмисно обмежений: ти не можеш викликати довільні Python-функції у шаблоні. Custom tags — це офіційний "безпечний міст" між шаблоном і Python-логікою.
- **📚 Чому це існує:** Розділення відповідальності: шаблони відповідають за відображення, Python — за логіку. Але іноді потрібна "легка логіка" прямо при рендерингу (форматування Badge, перевірка прав, підрахунок). Custom tags забезпечують це безпечно, не порушуючи архітектуру.
- **🌐 Що відбувається під капотом:** `{% load hello_tags %}` змушує Django знайти модуль `hello_tags.py` у будь-якій папці `templatetags/` у встановлених додатках. Django AUTO-DISCOVERS `templatetags/` папки — якщо додаток є в `INSTALLED_APPS`, Django сканує його `templatetags/`. `register = template.Library()` реєструє функції як теги. Під час рендерингу Django викликає зареєстровану Python-функцію і підставляє результат у HTML.
- **❌ Типова помилка початківця:** Забути `{% load hello_tags %}` на початку шаблону — тег просто не спрацює. Або зробити DB-запит у `simple_tag`, який викликається у циклі по 100 елементах — це класичне N+1 джерело.
---

## §2. Custom Template Tags

### Навіщо Custom Tags?

DTL навмисно обмежений — немає виклику функцій, немає складної логіки.
Custom Tags дозволяють розширити DTL безпечно: логіка в Python, відображення в шаблоні.

Django Template Language не дозволяє: `{{ Note.objects.count() }}` — це синтаксична помилка. Але що робити, якщо потрібно показати кількість нотаток у sidebar? Custom tags — це відповідь.

Існує три типи custom tags, кожен для своєї задачі:

```
simple_tag   → Python функція → повертає ЗНАЧЕННЯ (число, рядок)
inclusion_tag → Python функція → повертає КОНТЕКСТ → рендерить ШАБЛОН
filter       → Python функція → трансформує ЗНАЧЕННЯ → повертає трансформоване ЗНАЧЕННЯ
```

Папка `templatetags/` — обов'язкова назва. Django автоматично знаходить `templatetags/` папки у всіх встановлених додатках. `__init__.py` робить папку Python-пакетом:

### Структура

```
hello_app/
├── templatetags/          ← обов'язкова назва директорії
│   ├── __init__.py        ← порожній файл
│   └── hello_tags.py      ← ваші теги
```

`register = template.Library()` — це реєстр тегів. Декоратори `@register.simple_tag`, `@register.inclusion_tag`, `@register.filter` реєструють Python-функції як теги DTL:

```python
# hello_app/templatetags/hello_tags.py
from django import template
from django.utils.html import format_html
from hello_app.models import Note

register = template.Library()
```

---
- **🧠 Ментальна модель:** `simple_tag` = функція → значення. Думай про нього як про `{{ variable }}`, але де значення обчислюється Python-функцією у момент рендерингу, а не передається з view.
- **📚 Чому це існує:** Іноді значення залежить від параметрів шаблону або потребує легкого обчислення. Наприклад: `{% multiply price quantity %}` — зрозуміліше і безпечніше ніж передавати передраховані дані з кожного view.
- **🌐 Що відбувається під капотом:** При зустрічі `{% multiply 6 7 %}` Django парсить аргументи, знаходить зареєстровану функцію `multiply`, викликає `multiply(6, 7)`, і підставляє повернуте значення у HTML. `takes_context=True` передає весь поточний контекст шаблону першим аргументом — так можна отримати `request`, `user` та все інше.
- **❌ Типова помилка початківця:** Робити DB-запит у `simple_tag` який викликається у циклі `{% for note in notes %}{% notes_count request.user %}{% endfor %}` — це 100+ DB-запитів замість одного. Завжди рахуй, скільки разів викликається тег.
---

### simple_tag — повертає значення

`simple_tag` — найпростіший тип. Функція приймає аргументи і повертає значення, яке підставляється у HTML. `takes_context=True` дає доступ до всього контексту шаблону, включаючи `request`:

```python
@register.simple_tag
def multiply(a, b):
    return a * b

@register.simple_tag(takes_context=True)
def current_user_name(context):
    user = context['request'].user
    return user.get_full_name() or user.username

@register.simple_tag
def notes_count(user=None):
    qs = Note.objects.all()
    if user:
        qs = qs.filter(author=user)
    return qs.count()
```

Зверни на синтаксис виклику: `{% tag_name arg1 arg2 %}`. Конструкція `as my_count` зберігає результат у змінну контексту замість виводу — так можна використати значення кілька разів:

```html
{% load hello_tags %}

{# Базовий виклик #}
{% multiply 6 7 %}           {# → 42 #}

{# Зберегти в змінну #}
{% notes_count request.user as my_count %}
<span>Твоїх нотаток: {{ my_count }}</span>

{# З контекстом #}
{% current_user_name %}      {# → "Victor Nikoriak" #}
```

---
- **🧠 Ментальна модель:** `inclusion_tag` = міні-view у шаблоні. Функція повертає КОНТЕКСТ (dict), а Django рендерить окремий HTML-шаблон з цим контекстом і вставляє результат у поточний шаблон. Це найближче до "компонентної системи" у DTL.
- **📚 Чому це існує:** Для реюзабельних UI-компонентів, які мають власну логіку. Наприклад: notification badge потрібен у navbar кожної сторінки, але у нього є власна логіка (підрахунок, перевірка авторизації). Виносити цю логіку у кожен view — порушення DRY.
- **🌐 Що відбувається під капотом:** `@register.inclusion_tag('partial.html', takes_context=True)` каже Django: "виклич цю функцію, отримай dict, відрендери `partial.html` з цим dict як контекстом, і вставте HTML-результат у батьківський шаблон".
- **❌ Типова помилка початківця:** Передавати повний контекст батьківського шаблону (`return context`) замість мінімального контексту для під-шаблону. Це може призвести до несподіваних змінних і важкого debugging.
---

### inclusion_tag — рендерить під-шаблон

`inclusion_tag` повертає dict, який стає контекстом для окремого HTML-шаблону. Це потужний механізм для реюзабельних компонентів: badge, аватар, breadcrumbs, навігація. Реальні use cases: notification badge у navbar, user avatar з іменем, breadcrumb навігація:

```python
@register.inclusion_tag('hello_app/partials/notification_badge.html',
                         takes_context=True)
def notification_badge(context):
    request = context['request']
    if not request.user.is_authenticated:
        return {'count': 0}
    
    count = Notification.objects.filter(
        user=request.user, read=False
    ).count()
    return {'count': count, 'user': request.user}
```

Цей шаблон рендериться ОКРЕМО від батьківського, з власним контекстом. Він нічого не знає про батьківський шаблон — лише про те, що повернула функція:

```html
{# hello_app/partials/notification_badge.html #}
{% if count %}
<a href="{% url 'notifications' %}" class="btn position-relative">
    <i class="bi bi-bell"></i>
    <span class="position-absolute top-0 start-100 translate-middle
                 badge rounded-pill bg-danger">
        {{ count }}
    </span>
</a>
{% endif %}
```

Виклик тегу у шаблоні виглядає як будь-який інший тег. Django сам знаходить Python-функцію, викликає її, рендерить під-шаблон і вставляє результат на місце тегу:

```html
{# base.html — використання #}
{% load hello_tags %}
<nav class="navbar navbar-dark bg-dark">
    ...
    {% notification_badge %}   {# ← вставляє notification_badge.html #}
</nav>
```

---
- **🧠 Ментальна модель:** `filter` = перетворення значення у конвеєрі. `{{ value|my_filter:arg }}` читається як "візьми `value`, передай через `my_filter` з аргументом `arg`, виведи результат". Це Unix pipe для шаблонних значень.
- **📚 Чому це існує:** Для трансформацій, які тісно пов'язані з відображенням (форматування дати, скорочення тексту, конвертація статусу в колір). Фільтри — це "словниковий запас" для твоїх шаблонів.
- **🌐 Що відбувається під капотом:** Django auto-escapes весь вивід шаблонів для захисту від XSS. `format_html()` — ПРАВИЛЬНИЙ спосіб створювати HTML рядки в Python: він екранує змінні (захист від XSS), але зберігає твою HTML-структуру. НІКОЛИ не використовуй конкатенацію рядків або `mark_safe` для user-provided контенту — це XSS-вразливість.
- **❌ Типова помилка початківця:** Писати `return f'<span class="badge bg-{color}">{status}</span>'` замість `format_html(...)`. Якщо `status` містить `<script>alert('XSS')</script>`, перший варіант виконає скрипт у браузері. `format_html` автоматично екранує всі змінні.
---

### filter — трансформація значення

Django автоматично екранує весь вивід шаблонів для захисту від XSS. `format_html` — це ПРАВИЛЬНИЙ спосіб будувати HTML рядки у Python: він екранує змінні, але зберігає твою HTML-структуру. НІКОЛИ не використовуй конкатенацію рядків або `mark_safe` для user-provided контенту — це XSS-вразливість.

Перший фільтр `truncate_words` — безпечний: він повертає звичайний текст без HTML. Другий `status_badge` — повертає HTML, тому `format_html` обов'язковий:

```python
@register.filter(name='truncate_words')
def truncate_words(value, num_words):
    words = str(value).split()
    if len(words) <= num_words:
        return value
    return ' '.join(words[:num_words]) + '...'

@register.filter
def status_badge(status):
    """Note status → Bootstrap badge HTML."""
    colors = {
        'draft': 'secondary',
        'published': 'success',
        'archived': 'warning',
    }
    color = colors.get(status, 'primary')
    return format_html(
        '<span class="badge bg-{}">{}</span>',
        color,
        status.capitalize()
    )
```

Синтаксис фільтрів у шаблоні: `{{ value|filter_name:argument }}`. Фільтри ланцюгуються: `{{ value|filter1|filter2:arg }}`:

```html
{% load hello_tags %}

{{ note.body|truncate_words:20 }}
{{ note.status|status_badge }}
```

### Порівняння типів Template Tags

| Тип | Синтаксис у шаблоні | Повертає | Коли використовувати |
|-----|---------------------|----------|----------------------|
| `simple_tag` | `{% my_tag arg %}` | Значення | Обчислення, запити в БД |
| `inclusion_tag` | `{% my_tag %}` | Рендерить HTML | Реюзабельні компоненти (badge, card) |
| `filter` | `{{ value\|my_filter }}` | Трансформоване значення | Форматування рядків, кольори |
| `block tag` | `{% my_tag %}...{% end_my_tag %}` | HTML-блок | Складні обгортки (permission check, cache) |

---

---
- **🧠 Ментальна модель:** crispy-forms = Django forms + Bootstrap/Tailwind стилізація, через Pythonic Layout API замість HTML-шаблонів. Думай про це так: замість того, щоб писати Bootstrap HTML вручну для кожного поля форми, ти описуєш СТРУКТУРУ форми на Python, а crispy-forms генерує Bootstrap HTML автоматично.
- **📚 Чому це існує:** Django forms генерують мінімальний HTML (`<input>`, `<label>`) без Bootstrap класів. Для кожного Bootstrap поля треба написати `<div class="mb-3"><label class="form-label">...</label><input class="form-control">...`. crispy-forms автоматизує цей шаблонний код і дозволяє описувати layout форми на Python.
- **🌐 Що відбувається під капотом:** `FormHelper` не змінює валідацію форми — він ТІЛЬКИ змінює спосіб рендерингу у HTML. `Layout` — це дерево Python-об'єктів, що описує структуру: `Row(Column('field1'), Column('field2'))` = Bootstrap 2-колонковий layout. При рендерингу crispy-forms обходить це дерево і генерує відповідний Bootstrap HTML для кожного вузла.
- **❌ Типова помилка початківця:** Думати, що crispy-forms впливає на валідацію або поведінку форми. Він впливає ТІЛЬКИ на HTML-вигляд. Також: використовувати `{{ form.as_p }}` і `{{ form|crispy }}` одночасно — обирай один підхід.
---

## §3. crispy-forms — Python-лейаут форм

Ось конкретна демонстрація проблеми: той HTML, який треба писати ВРУЧНУ для кожної Bootstrap-форми без crispy-forms. Зверни увагу на кількість рядків лише для кількох полів:

### Проблема звичайних форм Django

```html
{# ❌ Шаблон перевантажений HTML-логікою форм #}
<form method="post">
    {% csrf_token %}
    {% for field in form %}
        <div class="mb-3">
            <label for="{{ field.id_for_label }}" class="form-label">
                {{ field.label }}
                {% if field.field.required %}<span class="text-danger">*</span>{% endif %}
            </label>
            {{ field }}
            {% if field.errors %}
                {% for error in field.errors %}
                    <div class="invalid-feedback d-block">{{ error }}</div>
                {% endfor %}
            {% endif %}
        </div>
    {% endfor %}
    <button type="submit" class="btn btn-primary">Зберегти</button>
</form>
```

### crispy-forms + crispy-bootstrap5

Встановлення двох пакетів: `django-crispy-forms` — основний пакет, `crispy-bootstrap5` — темплейт-пак для Bootstrap 5. Вони розділені, щоб підтримувати різні CSS фреймворки (Tailwind, Bootstrap 4/5):

```bash
pip install django-crispy-forms crispy-bootstrap5
```

`CRISPY_TEMPLATE_PACK` каже crispy-forms, який HTML генерувати. Для Bootstrap 5 він знає правильні класи, структуру, атрибути:

```python
# settings.py
INSTALLED_APPS = [
    ...
    'crispy_forms',
    'crispy_bootstrap5',
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
```

#### Варіант 1 — швидкий (template tag)

Найпростіший варіант: фільтр `|crispy` трансформує звичайний Django form у Bootstrap-стилізований HTML автоматично. Це "режим швидкого старту" — нуль конфігурації:

```html
{% load crispy_forms_tags %}

<form method="post">
    {% csrf_token %}
    {{ form|crispy }}
    <button type="submit" class="btn btn-primary">Зберегти</button>
</form>
```

#### Варіант 2 — FormHelper (Python-лейаут)

`FormHelper` визначається прямо у класі форми — це важливо. Логіка layout живе там само, де живе форма, а не розкидана по шаблонах. `Layout` — це Python-дерево, що описує структуру: `Fieldset` → `Row` → `Column` → поля. `{% crispy form %}` рендерить весь `<form>` тег, включаючи `action`, `method`, `id` з `FormHelper`:

```python
# hello_app/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout, Submit, Row, Column, Fieldset, HTML, Div
)
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'body', 'category', 'tags', 'is_public']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'note-form'
        
        self.helper.layout = Layout(
            Fieldset(
                'Основна інформація',
                'title',
                Row(
                    Column('category', css_class='col-md-6'),
                    Column('tags', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                'Зміст',
                'body',
            ),
            Div(
                'is_public',
                css_class='form-check mb-3',
            ),
            HTML("""
                <hr>
                <p class="text-muted">
                    <i class="bi bi-info-circle"></i>
                    Публічні нотатки видні всім користувачам.
                </p>
            """),
            Submit('submit', 'Зберегти нотатку', css_class='btn btn-primary'),
        )
```

`{% crispy form %}` — це все що потрібно у шаблоні. Весь Bootstrap HTML генерується автоматично на основі `FormHelper` і `Layout`, визначених у класі форми:

```html
{% load crispy_forms_tags %}

{% crispy form %}   {# ← рендерить весь form з helper, включно з тегом <form> #}
```

### FormHelper атрибути

Повний довідник атрибутів `FormHelper`. `form_tag = False` — корисно коли потрібно обернути форму у власний `<form>` тег (наприклад, для HTMX або multi-step forms). `error_text_inline = True` — помилки показуються поруч з полем, а не зверху форми:

```python
helper = FormHelper()

helper.form_method = 'post'           # GET або POST
helper.form_action = '/notes/create/' # action=""
helper.form_id = 'my-form'
helper.form_class = 'needs-validation' # Bootstrap validation class
helper.attrs = {'novalidate': ''}     # HTML атрибути

helper.form_tag = False               # Не рендерити <form> тег
helper.include_media = True           # Включати {{ form.media }}
helper.error_text_inline = True       # Помилки поруч з полем
helper.label_class = 'fw-bold'        # CSS для всіх label
helper.field_class = 'col-lg-10'      # CSS для всіх полів
```

### Layout елементи

Ці класи — будівельні блоки Layout. `Row`/`Column` генерують Bootstrap grid. `Field` дозволяє додавати HTML атрибути до конкретного поля. `HTML` вставляє довільний HTML без змін — корисно для роздільників, підказок, іконок:

```python
from crispy_forms.layout import (
    Layout,      # Кореневий контейнер
    Div,         # <div css_class="">
    Row,         # Bootstrap Row
    Column,      # Bootstrap Column
    Fieldset,    # <fieldset><legend>title</legend>...</fieldset>
    HTML,        # Довільний HTML рядок
    Field,       # Поле з кастомними атрибутами
    Submit,      # <button type="submit">
    Reset,       # <button type="reset">
    Hidden,      # <input type="hidden">
    MultiField,  # Кілька полів в одному рядку
)

# Field з атрибутами
Layout(
    Field('title', placeholder='Введіть назву', autofocus=True),
    Field('body', rows=5, css_class='font-monospace'),
)
```

---

---
- **🧠 Ментальна модель:** Vite — це "будівельна система" для frontend активів. Він бере твої SOURCE файли (TypeScript, SCSS, ES-модулі) і виробляє ОПТИМІЗОВАНІ output файли для production. Думай про нього як про `python manage.py collectstatic`, але для JavaScript і CSS — тільки набагато потужніший.
- **📚 Чому це існує:** Сучасний frontend неможливо просто "зв'язати" через `<script>` теги. SCSS треба компілювати у CSS. TypeScript у JavaScript. ES-модулі треба bundlувати. Файли треба мінімізувати і "content-хешувати" для cache busting. Vite вирішує всі ці задачі разом.
- **🌐 Що відбувається під капотом:** Development: Vite запускає dev-сервер на порту 5173 з Hot Module Replacement (HMR) — зміна CSS оновлює браузер БЕЗ перезавантаження. Production: `npm run build` генерує `dist/` папку з `manifest.json`. Manifest містить маппінг: `{"src/main.js": {"file": "assets/main-a4b3c2.js"}}`. Django читає цей manifest і `{% vite_asset 'src/main.js' %}` перетворює у правильний URL з хешем.
- **❌ Типова помилка початківця:** Запускати `npm run build` у development замість `npm run dev`. Або забути додати `static_dist/` до `STATICFILES_DIRS` у `settings.py` — Django не буде знати де шукати Vite output.
---

## §4. Vite + ManifestStaticFilesStorage — сучасний asset pipeline

Чому не просто `{% load static %}` і посилання на файли напряму? Ось чому:
- Сучасний CSS: Sass/SCSS треба компілювати у звичайний CSS
- Сучасний JS: TypeScript треба компілювати, ES-модулі треба bundlувати
- Production оптимізація: мінімізація, code splitting, content hashing (cache busting)

Asset pipeline виглядає так:

```
Development:
  Vite dev сервер на порту 5173
  Hot Module Replacement (HMR): зміна CSS → браузер оновлюється миттєво (без reload!)
  Django templates → {% vite_asset 'main.js' %} → URL Vite dev server

Production:
  npm run build → генерує dist/ папку
  dist/manifest.json: { "main.js": "assets/main-a4b3c2.js" }
  python manage.py collectstatic → копіює dist/ у STATIC_ROOT
  Django templates → {% vite_asset 'main.js' %} → /static/assets/main-a4b3c2.js
```

Content hashing = cache busting: `main-a4b3c2.js` містить хеш вмісту файлу. Якщо змінити файл — хеш змінюється, браузер завантажує свіжу копію. Якщо файл не змінився — браузер використовує кешовану версію.

### Чому Vite замість webpack?

| | webpack | Vite |
|-|---------|------|
| Cold start | ~30-60 сек | <1 сек (ESM native) |
| HMR | Повна перекомпіляція | Точковий апдейт |
| Production build | Добре | Добре (Rollup) |
| Django інтеграція | `django-webpack-loader` | `django-vite` |

### Структура проєкту

Зверни на розділення: `frontend/` містить весь JavaScript/CSS source code і npm-залежності. `static_dist/` — це Vite output, він потрапляє до Git лише якщо немає CI/CD. У production цю папку генерує Docker build stage:

```
django_bootstrap_project/
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js           ← entry point
│       ├── main.scss         ← Bootstrap + custom CSS
│       └── components/       ← JS компоненти
├── hello_app/
│   └── static/               ← Django static (legacy)
├── static_dist/              ← Vite output (collectstatic source)
└── manage.py
```

### vite.config.js

`base: '/static/'` — критично! Vite використовує цей шлях для генерації URL у HTML. Він має збігатись з Django `STATIC_URL`. `manifest: true` — генерує `manifest.json`, без якого Django не знатиме справжніх імен хешованих файлів:

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
    base: '/static/',          // Django STATIC_URL

    build: {
        outDir: '../static_dist',
        manifest: true,        // ← генерує manifest.json (потрібен Django)
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'src/main.js'),
            }
        }
    },

    server: {
        origin: 'http://localhost:5173',  // Vite dev server
        port: 5173,
    }
})
```

### main.js — Bootstrap через npm

Замість CDN Bootstrap — тепер через npm. Перевага: tree-shaking — імпортуємо тільки ті Bootstrap компоненти, які використовуємо, а не весь Bootstrap. Це зменшує розмір фінального bundle:

```javascript
// frontend/src/main.js

// Bootstrap JS (вибірково — тільки те що потрібно)
import { Modal, Toast, Tooltip } from 'bootstrap'

// Bootstrap CSS через SCSS
import './main.scss'

// Ваші компоненти
import './components/search'
import './components/delete-confirm'

// Ініціалізація Tooltips
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new Tooltip(el)
})
```

`:root` CSS змінні, визначені ДО `@import 'bootstrap'`, перевизначають Bootstrap дефолти — це офіційний спосіб брендування Bootstrap без форків:

```scss
// frontend/src/main.scss

// Кастомні CSS змінні ПЕРЕД Bootstrap
:root {
    --bs-primary: #2563eb;      // Перевизначення Bootstrap кольору
    --bs-border-radius: 0.5rem;
}

// Можна вибірково підключати Bootstrap модулі
@import 'bootstrap/scss/bootstrap';

// Ваші стилі
.note-card {
    transition: transform .2s ease;
    &:hover {
        transform: translateY(-4px);
    }
}
```

### settings.py — ManifestStaticFilesStorage

`ManifestStaticFilesStorage` читає `staticfiles.json` (аналог Vite `manifest.json`, але для Django) і автоматично перетворює `{% static 'main.js' %}` → `/static/main.abc123.js`. Це відбувається під час `collectstatic`:

```python
# settings.py

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic destination

# Vite build output — Django шукає тут
STATICFILES_DIRS = [
    BASE_DIR / 'static_dist',
]

# Production: файли з hash (main.abc123.js)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
# → генерує staticfiles.json з маппінгом main.js → main.abc123.js
# → {% static 'main.js' %} → /static/main.abc123.js
```

### django-vite інтеграція (dev режим)

`django-vite` забезпечує seamless перемикання між dev і production режимами. У dev — підключається до Vite HMR сервера (живе оновлення). У production — читає manifest.json і генерує правильні хешовані URL. `DJANGO_VITE_DEV_MODE = DEBUG` — автоматичне перемикання:

```bash
pip install django-vite
```

```python
# settings.py
INSTALLED_APPS = ['django_vite', ...]

DJANGO_VITE_ASSETS_PATH = BASE_DIR / 'static_dist'
DJANGO_VITE_DEV_MODE = DEBUG  # True в dev, False в prod
DJANGO_VITE_DEV_SERVER_URL = 'http://localhost:5173'
```

`{% vite_hmr_client %}` вставляє Vite HMR client script — він дозволяє Hot Module Replacement. `{% vite_asset 'src/main.js' %}` у dev генерує URL до Vite сервера, у prod — хешований URL до зібраного файлу:

```html
{# base.html #}
{% load django_vite %}

<head>
    {% if debug %}
        {# Dev: підключення через Vite dev server з HMR #}
        {% vite_hmr_client %}
        {% vite_asset 'src/main.js' %}
    {% else %}
        {# Production: Vite manifest → hash-файли #}
        {% vite_asset 'src/main.js' %}
    {% endif %}
</head>
```

### Multi-stage Dockerfile з Vite

Multi-stage build — ключова патерн для production. Stage 1 (Node.js) збирає frontend активи. Stage 2 (Python) збирає Django. `COPY --from=frontend-builder` копіює тільки Vite output між стейджами — Node.js модулі (сотні МБ) не потрапляють у фінальний образ:

```dockerfile
# Dockerfile

# Stage 1: Build frontend assets
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build   # → ../static_dist/

# Stage 2: Django production image
FROM python:3.12-slim AS django
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Django project
COPY . .

# Copy Vite output from frontend-builder
COPY --from=frontend-builder /static_dist/ ./static_dist/

# collectstatic
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "hello_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Production asset pipeline

Ця діаграма показує повний шлях від source code до браузера: dev режим (прямо через Vite HMR) і production режим (через хешовані файли на nginx):

```
Frontend Dev                    Production
─────────────                   ─────────────
npm run dev                     npm run build
    ↓                               ↓
Vite HMR server             static_dist/
(port 5173)                     ├── main.abc123.js
    ↓                           ├── main.def456.css
Browser JS modules              └── manifest.json
(no bundling)                       ↓
                            python manage.py collectstatic
                                    ↓
                            staticfiles/
                                    ↓
                            nginx /static/ → hash files
```

---

---
- **🧠 Ментальна модель:** SaaS Dashboard архітектура — це 3-рівневе дерево спадкування шаблонів. `base.html` (HTML-скелет) → `layouts/dashboard.html` (sidebar + topbar) → `notes/list.html` (контент сторінки). Кожен рівень додає свій шар, не повторюючи батьківський.
- **📚 Чому це існує:** Щоб зміна ONE рядка поширювалась на ВСІ сторінки. Зміна sidebar: редагуєш `layouts/dashboard.html` один раз — всі сторінки дашборду оновлюються. Зміна HTML-скелету: редагуєш `base.html` — весь сайт оновлюється.
- **🌐 Що відбувається під капотом:** Django template inheritance — це compile-time операція. При першому рендерингу Django компілює шаблон у дерево вузлів, де кожен `{% block %}` є точкою розширення. Дочірній шаблон "вставляє" свій контент у батьківські блоки.
- **❌ Типова помилка початківця:** Дублювати navbar або sidebar у кожному шаблоні замість виносити у `layouts/`. Або робити занадто плоску ієрархію (всі шаблони напряму extend `base.html`) — тоді sidebar треба копіювати у кожен layout.
---

## §5. SaaS Dashboard Architecture

Три рівні ієрархії шаблонів — це як inheritance tree. Корінний рівень визначає скелет, проміжні рівні визначають секції, листові шаблони визначають контент.

Чому ця архітектура масштабується:
- Додати нову сторінку: просто створи новий leaf шаблон, extend `layouts/dashboard.html`
- Змінити sidebar: відредагуй `layouts/dashboard.html` один раз — ВСІ сторінки оновляться
- Змінити HTML-скелет: відредагуй `base.html` один раз — КОЖНА сторінка оновиться

Компонентна філософія: sidebar, topbar, pagination, empty_state, confirm_modal — це КОМПОНЕНТИ, винесені у include-файли. Кожен має єдину відповідальність.

### Типова ієрархія шаблонів SaaS

```
templates/
├── base.html                   ← HTML5 shell, Bootstrap CDN/Vite
├── layouts/
│   ├── dashboard.html          ← base + sidebar + topbar
│   ├── auth.html               ← base + centered card (login/register)
│   └── landing.html            ← base + marketing nav
├── components/
│   ├── sidebar.html            ← inclusion_tag компонент
│   ├── topbar.html             ← з notification_badge
│   ├── breadcrumb.html         ← динамічний breadcrumb
│   ├── pagination.html         ← Bootstrap pagination
│   ├── empty_state.html        ← "No items yet" заглушка
│   └── confirm_modal.html      ← Delete confirmation modal
└── notes/
    ├── list.html               ← extends layouts/dashboard.html
    ├── detail.html
    ├── create.html
    └── edit.html
```

### base.html — HTML shell

`base.html` — це HTML5-скелет без жодного контенту. Всі `{% block %}` — точки розширення для дочірніх шаблонів. `data-bs-theme` — Bootstrap 5.3+ dark mode підтримка через CSS змінну, якою керує дочірній шаблон:

```html
{# templates/base.html #}
<!DOCTYPE html>
<html lang="uk" data-bs-theme="{% block theme %}light{% endblock %}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{% block meta_description %}Bootstrap Notes{% endblock %}">
    <title>{% block title %}Bootstrap Notes{% endblock %} — {{ site_name }}</title>

    {# Bootstrap CSS через CDN або Vite #}
    {% block css %}
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    {% endblock %}

    {% block extra_css %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">

    {% block body %}{% endblock %}

    {# Bootstrap JS #}
    {% block js %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
            defer></script>
    {% endblock %}

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### layouts/dashboard.html — sidebar layout

`layouts/dashboard.html` extends `base.html` і додає sidebar + topbar layout. Зверни на `request.resolver_match.url_name` — це динамічна підсвітка активного пункту меню. `resolver_match` доступний завдяки вбудованому `context_processors.request`:

```html
{# templates/layouts/dashboard.html #}
{% extends 'base.html' %}
{% load hello_tags static %}

{% block body_class %}bg-light{% endblock %}

{% block body %}
<div class="d-flex" style="min-height: 100vh;">

    {# ===== SIDEBAR ===== #}
    <nav id="sidebar"
         class="d-flex flex-column flex-shrink-0 bg-dark text-white"
         style="width: 260px;">

        {# Brand #}
        <a href="{% url 'hello_app:dashboard' %}"
           class="d-flex align-items-center p-3 text-white text-decoration-none border-bottom border-secondary">
            <i class="bi bi-journal-text fs-4 me-2"></i>
            <span class="fs-5 fw-bold">{{ site_name }}</span>
        </a>

        {# Navigation links #}
        <ul class="nav nav-pills flex-column mb-auto p-3">
            <li class="nav-item mb-1">
                <a href="{% url 'hello_app:note_list' %}"
                   class="nav-link text-white {% if request.resolver_match.url_name == 'note_list' %}active{% endif %}">
                    <i class="bi bi-file-text me-2"></i>Мої нотатки
                </a>
            </li>
            <li class="nav-item mb-1">
                <a href="{% url 'hello_app:note_create' %}"
                   class="nav-link text-white {% if request.resolver_match.url_name == 'note_create' %}active{% endif %}">
                    <i class="bi bi-plus-circle me-2"></i>Нова нотатка
                </a>
            </li>
            <li class="nav-item mb-1">
                <a href="{% url 'hello_app:category_list' %}"
                   class="nav-link text-white">
                    <i class="bi bi-tags me-2"></i>Категорії
                </a>
            </li>
        </ul>

        {# User section #}
        <div class="p-3 border-top border-secondary">
            <div class="d-flex align-items-center">
                <div class="flex-shrink-0">
                    <div class="rounded-circle bg-primary d-flex align-items-center
                                justify-content-center text-white"
                         style="width:36px; height:36px;">
                        {{ user.username|first|upper }}
                    </div>
                </div>
                <div class="flex-grow-1 ms-2 overflow-hidden">
                    <div class="fw-semibold text-truncate">{{ user.get_full_name|default:user.username }}</div>
                    <small class="text-muted">{{ user.email|truncatechars:20 }}</small>
                </div>
                <a href="{% url 'logout' %}" class="btn btn-sm btn-outline-secondary ms-1"
                   title="Вийти">
                    <i class="bi bi-box-arrow-right"></i>
                </a>
            </div>
        </div>
    </nav>

    {# ===== MAIN CONTENT ===== #}
    <div class="flex-grow-1 d-flex flex-column">

        {# Top bar #}
        <header class="navbar navbar-light bg-white border-bottom shadow-sm px-4 py-2">
            <div class="d-flex align-items-center gap-3">
                {# Mobile sidebar toggle #}
                <button class="btn btn-sm btn-outline-secondary d-lg-none"
                        data-bs-toggle="offcanvas" data-bs-target="#mobileSidebar">
                    <i class="bi bi-list"></i>
                </button>

                {# Breadcrumb #}
                <nav aria-label="breadcrumb">
                    <ol class="breadcrumb mb-0 small">
                        {% block breadcrumb %}
                        <li class="breadcrumb-item">
                            <a href="{% url 'hello_app:dashboard' %}">Головна</a>
                        </li>
                        {% endblock %}
                    </ol>
                </nav>
            </div>

            <div class="d-flex align-items-center gap-2">
                {# Search form #}
                <form class="d-flex" method="get" action="{% url 'hello_app:search' %}">
                    <div class="input-group input-group-sm">
                        <input type="search" name="q" class="form-control"
                               placeholder="Пошук..." value="{{ request.GET.q }}"
                               aria-label="Пошук нотаток">
                        <button class="btn btn-outline-secondary" type="submit">
                            <i class="bi bi-search"></i>
                        </button>
                    </div>
                </form>

                {# Notifications #}
                {% notification_badge %}
            </div>
        </header>

        {# Messages (Context Processor) #}
        {% if messages %}
        <div class="px-4 pt-3">
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"
                        aria-label="Закрити"></button>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        {# Page content #}
        <main class="flex-grow-1 p-4">
            {% block content %}{% endblock %}
        </main>

        {# Footer #}
        <footer class="text-center text-muted small py-3 border-top">
            {{ site_name }} v{{ site_version }} &copy; {% now "Y" %}
        </footer>
    </div>

</div>
{% endblock %}
```

### notes/list.html — CRUD Interface

Цей шаблон extends `layouts/dashboard.html` і визначає лише КОНТЕНТ сторінки. Зверни: тут немає ні HTML-скелету, ні sidebar — вони успадковуються автоматично. `{{ note.status|status_badge }}` — наш custom filter із §2. `{% include 'components/...' %}` — компонентна архітектура:

```html
{# templates/notes/list.html #}
{% extends 'layouts/dashboard.html' %}
{% load hello_tags %}

{% block title %}Мої нотатки{% endblock %}

{% block breadcrumb %}
<li class="breadcrumb-item active">Нотатки</li>
{% endblock %}

{% block content %}

{# Page header #}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h1 class="h3 mb-0">Мої нотатки</h1>
        <small class="text-muted">{{ notes.paginator.count }} нотаток</small>
    </div>
    <a href="{% url 'hello_app:note_create' %}" class="btn btn-primary">
        <i class="bi bi-plus-lg me-1"></i>Нова нотатка
    </a>
</div>

{# Filters #}
<div class="card mb-4">
    <div class="card-body py-2">
        <form method="get" class="row g-2 align-items-center">
            <div class="col-auto">
                <select name="category" class="form-select form-select-sm">
                    <option value="">Всі категорії</option>
                    {% for cat in categories %}
                    <option value="{{ cat.pk }}"
                            {% if request.GET.category == cat.pk|stringformat:"s" %}selected{% endif %}>
                        {{ cat.name }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-auto">
                <select name="sort" class="form-select form-select-sm">
                    <option value="-created_at">Спочатку нові</option>
                    <option value="created_at" {% if request.GET.sort == "created_at" %}selected{% endif %}>
                        Спочатку старі
                    </option>
                    <option value="title" {% if request.GET.sort == "title" %}selected{% endif %}>
                        За назвою
                    </option>
                </select>
            </div>
            <div class="col-auto">
                <button type="submit" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-funnel"></i> Застосувати
                </button>
            </div>
            {% if request.GET.category or request.GET.sort %}
            <div class="col-auto">
                <a href="{% url 'hello_app:note_list' %}" class="btn btn-sm btn-outline-secondary">
                    <i class="bi bi-x"></i> Скинути
                </a>
            </div>
            {% endif %}
        </form>
    </div>
</div>

{# Notes Grid #}
{% if notes %}
<div class="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
    {% for note in notes %}
    <div class="col">
        <div class="card h-100 shadow-sm">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title mb-0">
                        <a href="{% url 'hello_app:note_detail' pk=note.pk %}"
                           class="text-decoration-none text-dark stretched-link">
                            {{ note.title }}
                        </a>
                    </h5>
                    {{ note.status|status_badge }}
                </div>
                <p class="card-text text-muted small">
                    {{ note.body|truncate_words:25 }}
                </p>
            </div>
            <div class="card-footer bg-transparent d-flex justify-content-between align-items-center">
                <small class="text-muted">
                    <i class="bi bi-clock me-1"></i>{{ note.created_at|timesince }} тому
                </small>
                <div class="btn-group btn-group-sm position-relative">
                    <a href="{% url 'hello_app:note_edit' pk=note.pk %}"
                       class="btn btn-outline-secondary" title="Редагувати">
                        <i class="bi bi-pencil"></i>
                    </a>
                    <button type="button" class="btn btn-outline-danger"
                            data-bs-toggle="modal"
                            data-bs-target="#deleteModal"
                            data-note-id="{{ note.pk }}"
                            data-note-title="{{ note.title }}"
                            title="Видалити">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{# Pagination #}
{% include 'components/pagination.html' with page_obj=notes %}

{% else %}
{# Empty State #}
{% include 'components/empty_state.html' with
    icon='bi-journal-x'
    title='Ще немає нотаток'
    message='Створіть першу нотатку і вона з\'явиться тут.'
    action_url='hello_app:note_create'
    action_text='Створити нотатку'
%}
{% endif %}

{# Delete Confirmation Modal #}
{% include 'components/confirm_modal.html' %}

{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModal');
    deleteModal.addEventListener('show.bs.modal', function(e) {
        const btn = e.relatedTarget;
        document.getElementById('noteToDelete').textContent = btn.dataset.noteTitle;
        document.getElementById('deleteForm').action =
            `/notes/${btn.dataset.noteId}/delete/`;
    });
});
</script>
{% endblock %}
```

### components/pagination.html

Цей компонент — реюзабельний Bootstrap pagination, який приймає `page_obj` (Django Paginator об'єкт) через `{% include ... with page_obj=notes %}`. Логіка "показувати лише ±3 сторінки від поточної" робить pagination чистим навіть при сотнях сторінок:

```html
{# templates/components/pagination.html #}
{% if page_obj.has_other_pages %}
<nav aria-label="Навігація по сторінках" class="mt-4">
    <ul class="pagination justify-content-center">

        {# Previous #}
        <li class="page-item {% if not page_obj.has_previous %}disabled{% endif %}">
            <a class="page-link"
               href="?page={{ page_obj.previous_page_number }}"
               {% if not page_obj.has_previous %}aria-disabled="true"{% endif %}>
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>

        {# Page numbers #}
        {% for num in page_obj.paginator.page_range %}
            {% if page_obj.number == num %}
            <li class="page-item active" aria-current="page">
                <span class="page-link">{{ num }}</span>
            </li>
            {% elif num > page_obj.number|add:'-3' and num < page_obj.number|add:'3' %}
            <li class="page-item">
                <a class="page-link" href="?page={{ num }}">{{ num }}</a>
            </li>
            {% endif %}
        {% endfor %}

        {# Next #}
        <li class="page-item {% if not page_obj.has_next %}disabled{% endif %}">
            <a class="page-link"
               href="?page={{ page_obj.next_page_number }}"
               {% if not page_obj.has_next %}aria-disabled="true"{% endif %}>
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>

    </ul>
    <p class="text-center text-muted small">
        Сторінка {{ page_obj.number }} з {{ page_obj.paginator.num_pages }}
        ({{ page_obj.paginator.count }} елементів)
    </p>
</nav>
{% endif %}
```

### components/empty_state.html

"Empty state" — стандартний UX патерн. Замість порожнього екрану показуємо іконку, пояснення і CTA-кнопку. Параметри передаються через `{% include ... with icon=... title=... %}`:

```html
{# templates/components/empty_state.html #}
<div class="text-center py-5">
    <i class="bi {{ icon }} display-1 text-muted d-block mb-3"></i>
    <h4 class="text-muted">{{ title }}</h4>
    <p class="text-muted">{{ message }}</p>
    {% if action_url %}
    <a href="{% url action_url %}" class="btn btn-primary mt-2">
        <i class="bi bi-plus-lg me-1"></i>{{ action_text }}
    </a>
    {% endif %}
</div>
```

### components/confirm_modal.html

Bootstrap Modal для підтвердження видалення. JavaScript у `notes/list.html` (блок `extra_js`) динамічно заповнює назву нотатки і action URL перед показом модального вікна — через `data-note-id` і `data-note-title` атрибути кнопки:

```html
{# templates/components/confirm_modal.html #}
<div class="modal fade" id="deleteModal" tabindex="-1"
     aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header border-0">
                <h5 class="modal-title text-danger" id="deleteModalLabel">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Підтвердіть видалення
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"
                        aria-label="Скасувати"></button>
            </div>
            <div class="modal-body">
                Ви справді хочете видалити
                <strong>"<span id="noteToDelete"></span>"</strong>?
                Цю дію не можна скасувати.
            </div>
            <div class="modal-footer border-0">
                <button type="button" class="btn btn-secondary"
                        data-bs-dismiss="modal">Скасувати</button>
                <form id="deleteForm" method="post">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">
                        <i class="bi bi-trash me-1"></i>Видалити
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
```

---

---
- **🧠 Ментальна модель:** Jinja2 — це "розкута" версія Django Template Language. Там де DTL навмисно обмежений (немає виклику функцій, немає складних виразів), Jinja2 дозволяє майже все. Jinja2 — це потужність, DTL — це безпечність.
- **📚 Чому це існує:** Jinja2 — окремий template engine, значно потужніший за DTL. Django підтримує обидва через pluggable backend систему. Jinja2 обирають для: складних шаблонів з макросами, high-performance rendering, і коли треба більше гнучкості ніж дозволяє DTL.
- **🌐 Що відбувається під капотом:** `environment()` фабрика — еквівалент Django template engine конфігурації. Тут реєструються globals (функції доступні у всіх шаблонах) і filters. Jinja2 компілює шаблони у Python bytecode — кешування цього bytecode економить повторну компіляцію на кожен запит. Для дуже великих HTML документів streaming відправляє перші байти у браузер поки Python ще генерує решту — користувач бачить контент швидше.
- **❌ Типова помилка початківця:** Змішувати DTL і Jinja2 в одному шаблоні — вони несумісні. `{% load %}` — DTL-тег, у Jinja2 його немає. Також: `{{ csrf_token }}` у Jinja2 не працює — треба `{{ csrf_input }}` (це `<input type="hidden">` елемент).
---

## §6. Jinja2 Deep Dive

Ключові концепції перед кодом:
- `environment()` фабрика — еквівалент Django template engine конфігурації. Реєструй globals (функції доступні у всіх шаблонах) і filters тут.
- Макроси — потужна функція Jinja2. Macro — це реюзабельна HTML-функція з параметрами, визначена прямо у шаблоні. Схожа на `inclusion_tag`, але без Python коду.
- Bytecode cache — Jinja2 компілює шаблони у Python bytecode. Кешування цього bytecode економить повторну компіляцію на кожен запит — значний performance gain у production.
- Streaming — для дуже великих HTML документів (звіти, exports) streaming відправляє перші байти у браузер поки Python ще генерує решту. Користувач бачить контент швидше.

### Jinja2 Environment — конфігурація рушія

`environment()` — це фабрична функція, що конфігурує Jinja2 для Django. `env.globals.update()` реєструє Python-функції як глобальні змінні шаблону — вони доступні у ВСІХ шаблонах без import. Зверни: у Jinja2 можна викликати `len(notes)` і `range(10)` — це недоступно у DTL:

```python
# hello_app/jinja2_env.py

from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    """Фабрика Jinja2 Environment для Django."""
    env = Environment(**options)

    # Глобальні функції (доступні без import у шаблоні)
    env.globals.update({
        'static': static,           # {{ static('css/main.css') }}
        'url': reverse,             # {{ url('note_list') }}
        'len': len,                 # {{ len(notes) }}
        'range': range,             # {% for i in range(10) %}
        'zip': zip,                 # {% for a, b in zip(list1, list2) %}
    })

    # Кастомні фільтри
    env.filters['truncate_words'] = lambda s, n: ' '.join(str(s).split()[:n]) + '...'

    # Тести (is ... у шаблонах)
    env.tests['divisibleby'] = lambda n, d: n % d == 0

    return env
```

Django підтримує КІЛЬКА template backends одночасно. Перший backend у списку шукається першим. DTL обробляє шаблони у `templates/`, Jinja2 — у `templates/jinja2/`. `auto_reload: DEBUG` — у production шаблони не перечитуються з диску — тільки з cache:

```python
# settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'templates' / 'jinja2'],
        'APP_DIRS': False,
        'OPTIONS': {
            'environment': 'hello_app.jinja2_env.environment',
            'auto_reload': DEBUG,       # False у prod (bytecode cache)
            'undefined': 'jinja2.Undefined',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [...]},
    },
]
```

### Макроси — Jinja2 super-feature

Macro у Jinja2 — це як `inclusion_tag`, але визначений прямо у шаблоні, без Python. `{% macro input_field(field, label=None, help_text=None) %}` — функція з параметрами і default значеннями. `{% from 'macros/forms.html' import input_field %}` — import конкретних макросів з файлу:

```jinja2
{# templates/jinja2/macros/forms.html #}
{% macro input_field(field, label=None, help_text=None) %}
<div class="mb-3">
    <label for="{{ field.id_for_label }}" class="form-label fw-semibold">
        {{ label or field.label }}
        {% if field.field.required %}<span class="text-danger ms-1">*</span>{% endif %}
    </label>
    {{ field }}
    {% if help_text %}
        <div class="form-text text-muted">{{ help_text }}</div>
    {% endif %}
    {% if field.errors %}
        {% for error in field.errors %}
        <div class="invalid-feedback d-block">{{ error }}</div>
        {% endfor %}
    {% endif %}
</div>
{% endmacro %}

{% macro submit_btn(label='Зберегти', css_class='btn-primary') %}
<div class="d-grid gap-2 d-md-flex justify-content-md-end mt-4">
    <button type="submit" class="btn {{ css_class }}">
        <i class="bi bi-check-lg me-1"></i>{{ label }}
    </button>
</div>
{% endmacro %}
```

Зверни на ключову відмінність від DTL: `{{ Note.objects.count() }}` — це валідний Jinja2 синтаксис. У DTL це б призвело до помилки. `{{ csrf_input }}` замість `{% csrf_token %}` — специфіка Jinja2 у Django:

```jinja2
{# templates/jinja2/notes/create.html #}
{% from 'macros/forms.html' import input_field, submit_btn %}
{% extends 'jinja2/layouts/dashboard.html' %}

{% block content %}
<div class="card shadow-sm">
    <div class="card-body">
        <form method="post">
            {{ csrf_input }}   {# Jinja2 — не тег, а змінна #}

            {{ input_field(form.title, help_text='Коротка описова назва') }}
            {{ input_field(form.body) }}
            {{ input_field(form.category) }}

            {# Виклик функції — в Jinja2 це нормально, в DTL — заборонено #}
            <p>Всього нотаток: {{ Note.objects.count() }}</p>

            {{ submit_btn('Створити нотатку') }}
        </form>
    </div>
</div>
{% endblock %}
```

### Jinja2 успадкування з `{{ super() }}`

`{{ super() }}` — це Jinja2 еквівалент DTL `{{ block.super }}`. Він вставляє ВМІСТ батьківського блоку, а потім дозволяє дочірньому шаблону додати своє. Корисно для CSS/JS blocks — додаємо свої стилі поверх батьківських, не замінюючи їх:

```jinja2
{# templates/jinja2/base.html #}
{% block css %}
<link rel="stylesheet" href="{{ static('css/bootstrap.min.css') }}">
{% endblock %}
```

```jinja2
{# templates/jinja2/notes/create.html #}
{% block css %}
{{ super() }}   {# ← включає CSS батька #}
<link rel="stylesheet" href="{{ static('css/codemirror.min.css') }}">
{% endblock %}
```

> В DTL `{{ block.super }}` — схожа концепція.

### Bytecode Cache — Jinja2 production

Bytecode cache зберігає скомпільовані шаблони на диску. При наступному запиті Jinja2 завантажує bytecode замість повторної компіляції шаблону. Важливо: якщо очистити cache вручну після зміни шаблону у production без `auto_reload` — Django завантажить свіжий шаблон:

```python
# settings.py — Jinja2 bytecode cache

from jinja2 import FileSystemBytecodeCache

JINJA2_BYTECODE_CACHE = FileSystemBytecodeCache(
    directory='/tmp/jinja2_cache/',
    pattern='__jinja2_%s.cache',
)

# hello_app/jinja2_env.py
from django.conf import settings

def environment(**options):
    if not settings.DEBUG and hasattr(settings, 'JINJA2_BYTECODE_CACHE'):
        options['bytecode_cache'] = settings.JINJA2_BYTECODE_CACHE
    env = Environment(**options)
    ...
    return env
```

### Jinja2 Streaming — для великих відповідей

`StreamingHttpResponse` відправляє HTTP-відповідь по частинах. `template.stream()` генерує HTML поступово. `Note.objects.iterator()` читає QuerySet рядок за рядком без завантаження всього у RAM. Ідеально для великих звітів, CSV/HTML exports де дані можуть бути сотнями МБ:

```python
# views.py

from jinja2 import Environment
from django.http import StreamingHttpResponse

def large_export(request):
    """Потокова відповідь — не буферизує весь HTML у пам'яті."""
    env = Environment(loader=...)
    template = env.get_template('export.html')

    notes = Note.objects.iterator()  # Django QuerySet iterator

    def generate():
        stream = template.stream({'notes': notes})
        stream.enable_buffering(5)  # буфер 5 KB
        yield from stream

    return StreamingHttpResponse(generate(), content_type='text/html')
```

---

---
- **🧠 Ментальна модель:** HTMX — це "Ajax для HTML". Він додає HTTP-суперсилу будь-якому HTML елементу — не тільки `<a>` і `<form>`. Замість JavaScript-коду для fetch/update DOM, ти пишеш HTML атрибути.
- **📚 Чому це існує:** Класичний підхід: HTML статичний, JavaScript робить його динамічним — потребує окремого JS фреймворку (React/Vue), окремого API (JSON), окремого build toolchain. HTMX підхід: HTML сам IS API. HTML-фрагменти IS зміни стану. Ти залишаєшся у Python/Django шаблонах — без context-switching у JavaScript.
- **🌐 Що відбувається під капотом:** HTMX перехоплює DOM-події (click, submit, keyup), надсилає HTTP запит з спеціальними заголовками (`HX-Request: true`, `HX-Target`, `HX-Trigger`), Django view виявляє HTMX запит через заголовок, повертає HTML-фрагмент (не повну сторінку), HTMX вставляє цей фрагмент у DOM відповідно до `hx-swap` стратегії. Перезавантаження сторінки не відбувається.
- **❌ Типова помилка початківця:** Повертати повний HTML (з `base.html`) на HTMX-запит замість тільки фрагменту. Результат: sidebar вставляється всередину sidebar, повна сторінка з'являється у маленькому div. Завжди перевіряй `request.headers.get('HX-Request')`.
---

## §7. HTMX Architecture — повний lifecycle

Філософський зсув, який пояснює HTMX:

```
Традиційний підхід: HTML СТАТИЧНИЙ, JavaScript робить його ДИНАМІЧНИМ
HTMX підхід: HTML сам IS API. HTML фрагменти IS зміни стану.
```

Чому це революційно для Django розробників:
- Ти залишаєшся у Python/Django шаблонах — без context-switching у JavaScript
- Твої Django view повертають HTML фрагменти замість JSON
- Ніякого JavaScript фреймворку вчити, ніякої build системи не потрібно

Повний HTMX request lifecycle:

```
1. Користувач взаємодіє з елементом що має hx-* атрибути
2. HTMX перехоплює подію (click, submit, keyup, etc.)
3. HTMX надсилає HTTP запит (GET/POST/PUT/DELETE)
4. Запит має спеціальні заголовки: HX-Request: true, HX-Target: results, etc.
5. Django view отримує запит
6. Перевіряє HX-Request заголовок
7. Якщо HTMX запит → повертає HTML фрагмент (тільки змінену частину)
8. Якщо звичайний запит → повертає повну сторінку
9. HTMX отримує HTML фрагмент
10. HTMX вставляє фрагмент у target елемент
11. Перезавантаження сторінки не відбувається
```

### HTMX Philosophy

```
Traditional SPA                 HTMX Server-Driven UI
─────────────────               ─────────────────────
Client renders HTML             Server renders HTML
JavaScript heavy               JavaScript minimal
Full JSON API needed           HTML fragments from server
State in JS (Redux, Zustand)   State on server / database
Complex build setup (webpack)  Zero build tooling
```

### Атрибути HTMX

| Атрибут | Що робить |
|---------|-----------|
| `hx-get="/path/"` | GET запит до `/path/` |
| `hx-post="/path/"` | POST з даними форми |
| `hx-trigger="click"` | Тригер: `click`, `change`, `keyup delay:300ms`, `load`, `revealed` |
| `hx-target="#id"` | Куди вставити відповідь (CSS selector) |
| `hx-swap="innerHTML"` | Як вставити: `innerHTML`, `outerHTML`, `beforeend`, `afterend`, `delete` |
| `hx-include="#form-id"` | Включити дані іншого елемента |
| `hx-push-url="true"` | Оновити URL у браузері |
| `hx-indicator="#spinner"` | Показати spinner під час запиту |
| `hx-confirm="Ви впевнені?"` | Діалог підтвердження перед запитом |

### HTMX Request Lifecycle

```
1. User triggers event (click, keyup, etc.)
        ↓
2. HTMX reads attributes (hx-get, hx-target, hx-swap)
        ↓
3. htmx:configRequest event fired
   → можна модифікувати заголовки через JS
        ↓
4. HTTP Request (з HTMX заголовками):
   HX-Request: true
   HX-Current-URL: http://localhost:8000/notes/
   HX-Target: note-list-container
   HX-Trigger: search-input
        ↓
5. Django View отримує запит
   → Перевіряє HX-Request заголовок
   → Повертає HTML фрагмент (не повну сторінку)
        ↓
6. htmx:beforeSwap event
   → Можна перехопити і скасувати
        ↓
7. DOM оновлення (hx-swap стратегія)
        ↓
8. htmx:afterSwap → запустити scripts, init Bootstrap
        ↓
9. htmx:afterSettle → анімації завершені
```

### Django View — перевірка HTMX

Це ключовий патерн: один view обробляє ОБА типи запитів. Звичайний запит → повна сторінка. HTMX запит → тільки фрагмент. Це забезпечує progressive enhancement: сторінка працює без JavaScript (повне завантаження), і з HTMX (динамічне оновлення):

```python
# views.py

def note_list(request):
    query = request.GET.get('q', '')
    notes = Note.objects.filter(author=request.user)
    if query:
        notes = notes.filter(title__icontains=query)

    # Якщо HTMX запит — повертаємо тільки фрагмент
    if request.headers.get('HX-Request'):
        return render(request, 'notes/partials/note_cards.html', {'notes': notes})

    # Звичайний запит — повна сторінка
    return render(request, 'notes/list.html', {'notes': notes, 'query': query})
```

`django-htmx` пакет додає `request.htmx` — зручний інтерфейс замість ручної перевірки заголовків. Також надає `request.htmx.target`, `request.htmx.trigger` та інші атрибути:

```python
# Або через django-htmx (pip install django-htmx)
def note_list(request):
    notes = Note.objects.filter(author=request.user)
    if request.htmx:
        return render(request, 'notes/partials/note_cards.html', {'notes': notes})
    return render(request, 'notes/list.html', {'notes': notes})
```

### Живий пошук — повний приклад

`hx-trigger="keyup changed delay:300ms"` — розберемо кожну частину:
- `keyup` — подія яка тригерує запит
- `changed` — тільки якщо значення ЗМІНИЛОСЬ (без цього запит надсилається навіть при натисканні Shift)
- `delay:300ms` — debounce: чекає 300мс після останнього натискання. Без цього — кожна літера = окремий запит. З debounce — запит надсилається лише коли користувач перестав друкувати

`hx-target="#note-list-container"` — вказує який елемент оновити. Значення — CSS selector.
`hx-swap="innerHTML"` — замінити тільки ВМІСТ target (не сам контейнер). `htmx-indicator` — Bootstrap spinner, видимий автоматично під час HTMX запиту:

```html
{# notes/list.html — пошуковий input #}
<input type="search" name="q"
       class="form-control"
       placeholder="Пошук нотаток..."
       hx-get="{% url 'hello_app:note_list' %}"
       hx-trigger="keyup changed delay:300ms, search"
       hx-target="#note-list-container"
       hx-swap="innerHTML"
       hx-indicator="#search-spinner"
       aria-label="Живий пошук">

{# Spinner — видимий тільки під час HTMX запиту #}
<span id="search-spinner"
      class="spinner-border spinner-border-sm text-primary htmx-indicator"
      role="status" aria-hidden="true"></span>

{# Контейнер для результатів #}
<div id="note-list-container">
    {% include 'notes/partials/note_cards.html' %}
</div>
```

Partial шаблон `note_cards.html` рендерить ТІЛЬКИ картки — без `{% extends %}`, без `{% block %}`. Він повністю ізольований і може використовуватись як у повній сторінці (через `{% include %}`), так і повертатись на HTMX-запити:

```html
{# notes/partials/note_cards.html — тільки картки, без base.html #}
{% if notes %}
    {% for note in notes %}
    <div class="col">
        {# ... card ... #}
    </div>
    {% endfor %}
{% else %}
<div class="col-12">
    <p class="text-center text-muted py-4">Нотаток не знайдено.</p>
</div>
{% endif %}
```

### Infinite Scroll з HTMX

`hx-trigger="revealed"` спрацьовує коли елемент стає ВИДИМИМ у viewport (при скролі). Це стандартний infinite scroll патерн: останній елемент видимий → завантажити наступну сторінку. Набагато простіше ніж JavaScript `IntersectionObserver` реалізації.

`hx-swap="outerHTML"` — замінює SAM елемент-тригер на новий контент (наступні картки). Якщо більше сторінок немає — Django view повертає порожній рядок або "кінець списку" повідомлення, і тригер зникає:

```html
{# Останній елемент списку — тригер підвантаження #}
{% if page_obj.has_next %}
<div hx-get="{% url 'note_list' %}?page={{ page_obj.next_page_number }}"
     hx-trigger="revealed"        {# ← спрацьовує коли елемент з'являється у viewport #}
     hx-target="this"
     hx-swap="outerHTML"          {# ← замінює сам себе наступними картками #}
     class="text-center py-3">
    <span class="spinner-border text-primary htmx-indicator" role="status"></span>
    <span class="htmx-indicator-hide">Прокрутіть для завантаження...</span>
</div>
{% endif %}
```

### Optimistic UI з HTMX

Optimistic UI = припускаємо успіх ДО підтвердження сервера. Інтерфейс здається миттєвим. Ризик: що якщо сервер повертає помилку? HTMX замінює елемент відповіддю сервера (яка містить стан помилки). Тобто "rollback" відбувається автоматично через server response.

`hx-swap="outerHTML"` — замінює ВЕСЬ елемент (включаючи кнопку) на оновлену версію картки від сервера. Якщо статус змінився — відображається нова картка без кнопки "виконати":

```html
{# Відмітка як виконане — без перезавантаження сторінки #}
<button hx-post="{% url 'note_complete' pk=note.pk %}"
        hx-target="closest .note-card"
        hx-swap="outerHTML"          {# ← замінює картку оновленою версією #}
        hx-confirm="Відмітити як виконане?"
        class="btn btn-sm btn-outline-success">
    <i class="bi bi-check2"></i>
</button>
```

View повертає ТІЛЬКИ HTML картки, не повну сторінку. HTMX замінює стару картку цією новою відповіддю. Якщо виникла помилка — view може повернути картку з error state — HTMX вставить її автоматично:

```python
# views.py
@require_POST
def note_complete(request, pk):
    note = get_object_or_404(Note, pk=pk, author=request.user)
    note.status = 'completed'
    note.save()
    # Повертаємо тільки оновлену картку
    return render(request, 'notes/partials/note_card.html', {'note': note})
```

### HTMX + Bootstrap Modal (server-rendered)

Динамічний Modal: контент завантажується з сервера при відкритті. Не потрібно заздалегідь рендерити форми для всіх нотаток — тільки для тієї, яку відкрили. Це значно зменшує HTML розмір початкової сторінки:

```html
{# Кнопка — відкриває і завантажує вміст #}
<button hx-get="{% url 'note_edit_modal' pk=note.pk %}"
        hx-target="#modal-container"
        hx-swap="innerHTML"
        data-bs-toggle="modal"
        data-bs-target="#dynamicModal"
        class="btn btn-sm btn-outline-primary">
    <i class="bi bi-pencil"></i>
</button>

{# Контейнер для динамічного вмісту Modal #}
<div id="modal-container"></div>
<div class="modal fade" id="dynamicModal" tabindex="-1"></div>
```

```python
# views.py
def note_edit_modal(request, pk):
    note = get_object_or_404(Note, pk=pk, author=request.user)
    form = NoteForm(instance=note)
    # Повертаємо тільки modal-dialog HTML
    return render(request, 'notes/partials/edit_modal_body.html', {
        'note': note, 'form': form
    })
```

### HTMX Response Headers

HTMX Response Headers дозволяють серверу керувати HTMX поведінкою після відповіді. `HX-Redirect` — перенаправлення без повного page reload. `HX-Trigger` — надсилання custom JS events з сервера для синхронізації інших частин UI. Різниця між `HX-Redirect` і звичайним `redirect()`: HTMX перехоплює перенаправлення і виконує його як HTMX navigation, а не як повне перезавантаження сторінки:

```python
# views.py — управління HTMX поведінкою через заголовки відповіді

from django.http import HttpResponse

def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.save()

            response = HttpResponse(status=204)  # No Content
            # Перенаправити HTMX на список нотаток
            response['HX-Redirect'] = reverse('hello_app:note_list')
            # Або оновити тільки певний елемент
            response['HX-Trigger'] = 'noteCreated'  # JS event
            return response

        return render(request, 'notes/partials/create_form.html', {'form': form})
```

`HX-Trigger: noteCreated` надсилає custom DOM event. JavaScript на сторінці може слухати цей event і виконувати додаткові дії — наприклад, оновити лічильник нотаток у sidebar без перезавантаження:

```javascript
// Слухаємо server-side event
document.addEventListener('noteCreated', function() {
    // Оновити лічильник нотаток
    htmx.trigger('#notes-count', 'refresh');
});
```

---

## §8. Питання для самоперевірки

1. Context Processor виконує запит до БД (підрахунок повідомлень). На сторінці 50 запитів — скільки разів виконується Context Processor? Як оптимізувати?
2. `@register.inclusion_tag` отримує `takes_context=True`. Яку змінну шаблону він автоматично отримає? Для чого це потрібно?
3. crispy-forms `FormHelper` має `form_tag = False`. Коли це корисно?
4. Vite генерує `manifest.json`. Навіщо він потрібен Django? Що в ньому зберігається?
5. `ManifestStaticFilesStorage` додає hash до файлів (`main.abc123.js`). Навіщо? Що це дає браузеру?
6. В SaaS Dashboard `{% if request.resolver_match.url_name == 'note_list' %}active{% endif %}` — що таке `resolver_match`? Де він доступний?
7. Jinja2 `FileSystemBytecodeCache` зберігає скомпільовані шаблони. Що станеться якщо шаблон змінився, але кеш не очистився?
8. HTMX `hx-trigger="keyup changed delay:300ms"` — що означає `changed`? Навіщо `delay`?
9. HTMX view повертає `HttpResponse(status=204)` з заголовком `HX-Redirect`. Яка різниця з `redirect()`?
10. В якому порядку Django шукає шаблони якщо є і DTL і Jinja2 backend? Як контролювати який backend використовується?
