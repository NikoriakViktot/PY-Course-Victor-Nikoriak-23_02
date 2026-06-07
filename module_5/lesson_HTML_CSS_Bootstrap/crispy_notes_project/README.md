# CrispyNotes — Django Templates + Crispy Forms

> Цей туторіал проводить тебе через **еволюцію Django-форм**:
> HTML вручну → widget attrs → FormHelper + Layout.
>
> Проєкт — **менеджер нотаток з SaaS Dashboard**: та сама модель `Note` що в `notes_project`,
> але рендеринг форм переведений на `django-crispy-forms`.
> Три рівні рендерингу форм — від `{{ form.as_p }}` до `{% crispy form %}` — показують **чому** crispy.

---

## Зміст

**Архітектурний фундамент** _(читати перед кодом)_
- [01 · TEMPLATE SOUP — проблема дублювання HTML](#01--template-soup)
- [02 · TEMPLATE INHERITANCE — 3-рівнева ієрархія](#02--template-inheritance)
- [03 · FORMS EVOLUTION — 3 рівні рендерингу](#03--forms-evolution)
- [04 · FORMHELPER + LAYOUT — архітектура crispy](#04--formhelper--layout)
- [05 · DASHBOARD ARCHITECTURE — sidebar, topbar, context](#05--dashboard-architecture)

**Покрокова реалізація**
1. [Крок 0 — Запуск проєкту](#крок-0--запуск)
2. [Крок 1 — Settings: підключення crispy](#крок-1--settings)
3. [Крок 2 — Рівень 1: base.html (HTML-оболонка)](#крок-2--basehtml)
4. [Крок 3 — Рівень 2: layouts/dashboard.html (Sidebar + Topbar)](#крок-3--layoutsdashboardhtml)
5. [Крок 4 — Рівень 3: Сторінки (note_list, note_form...)](#крок-4--сторінки)
6. [Крок 5 — Forms Tier 1: form.as_p (Raw Django)](#крок-5--tier-1-raw)
7. [Крок 6 — Forms Tier 2: Manual Bootstrap HTML](#крок-6--tier-2-manual)
8. [Крок 7 — Forms Tier 3: FormHelper + Layout (Crispy)](#крок-7--tier-3-crispy)
9. [Крок 8 — Sidebar Context Processor](#крок-8--context-processor)
10. [Крок 9 — Components (pagination, empty_state, modal)](#крок-9--components)
11. [Структура файлів проєкту](#структура-файлів)

---

## 01 · TEMPLATE SOUP

> **"Template Soup"** — коли шаблони містять повторювані блоки HTML:
> `<nav>`, `<header>`, Bootstrap CDN — скопійовані в кожному файлі.
> При зміні навігації → правиш 20 файлів.

### Проблема: дублювання на рівні шаблонів

```html
<!-- notes_form.html — 80 рядків для 5 полів -->
<div class="mb-3">
  <label for="id_title" class="form-label fw-semibold">
    Заголовок
    <span class="text-danger">*</span>
  </label>
  <input type="text"
         name="title"
         id="id_title"
         class="form-control {% if form.title.errors %}is-invalid{% endif %}"
         autofocus>
  {% if form.title.errors %}
    {% for error in form.title.errors %}
    <div class="invalid-feedback">{{ error }}</div>
    {% endfor %}
  {% endif %}
</div>

<!-- ... повторити для кожного поля ... -->
```

Це **Tier 2** — ручний Bootstrap HTML. Проблеми:

| Проблема | Приклад |
|----------|---------|
| Дублювання | 15 рядків на поле × 6 полів = 90 рядків тільки для форми |
| Зміна класу | Хочеш `form-control-lg` → правиш кожен `<input>` у кожному шаблоні |
| Синхронізація | Додав поле у `models.py` → не забудь оновити шаблон |
| Немає системи | Кожен розробник пише "трошки по-своєму" |

### Рішення: розподіл відповідальності

```
БУЛО (Tier 2):
  forms.py:    поля + widget attrs + validation
  template:    label + input + error + help_text   ← 80 рядків HTML

СТАЛО (Tier 3):
  forms.py:    поля + FormHelper + Layout           ← опис структури Python-кодом
  template:    {% crispy form %}                    ← 1 рядок
```

> **Ключова ідея:** Форма — це **Python об'єкт**. Її структура описується Python-кодом (Layout),
> а не HTML у шаблоні. Шаблон стає тонким — тільки вказує де рендерити.

---

## 02 · TEMPLATE INHERITANCE

> **"Не повторюй HTML — успадковуй."**
> Django дозволяє будувати шаблони як дерево: батько визначає структуру, дитина — контент.

### 3-рівнева ієрархія (SaaS Dashboard паттерн)

```
base.html                          ← Рівень 1: HTML-оболонка
│  Bootstrap CDN, meta, <body>
│  {% block body %}
│
└── layouts/dashboard.html        ← Рівень 2: Макет застосунку
       Sidebar + Topbar
       Django Messages
       {% block content %}
       {% block topbar_title %}
       │
       ├── hello_app/note_list.html       ← Рівень 3: Контент сторінки
       ├── hello_app/note_form.html
       ├── hello_app/notebook_list.html
       └── hello_app/tag_form.html
```

### Як це виглядає в коді

**`base.html`** — тільки HTML-скелет:
```html
<!DOCTYPE html>
<html>
<head>
  <!-- Bootstrap CDN, CSS -->
</head>
<body>
  {% block body %}{% endblock %}   ← весь застосунок тут
</body>
</html>
```

**`layouts/dashboard.html`** — макет (extends base):
```html
{% extends 'base.html' %}
{% block body %}
  <div class="d-flex vh-100">
    <nav><!-- Sidebar --></nav>
    <div class="flex-grow-1">
      <header>{% block topbar_title %}{% endblock %}</header>
      <main>{% block content %}{% endblock %}</main>
    </div>
  </div>
{% endblock %}
```

**`note_list.html`** — сторінка (extends dashboard):
```html
{% extends 'layouts/dashboard.html' %}
{% block topbar_title %}Мої нотатки{% endblock %}
{% block content %}
  <!-- тільки контент, sidebar/topbar вже є з батька -->
{% endblock %}
```

### Потік наслідування

```
Запит /notes/
     │
     ▼
views.note_list()
  └─► render('hello_app/note_list.html', context)
           │
           ▼
      Django Template Engine
           │
      note_list.html extends dashboard.html
           │
      dashboard.html extends base.html
           │
      base.html — кореневий шаблон
           │
           ▼
      Зборка: base → dashboard → note_list → HTML
           │
           ▼
      200 OK  ·  повна HTML сторінка
```

> **Переваги:**
> - Зміна навігації → тільки `dashboard.html`, всі сторінки оновились
> - Нова сторінка → тільки пишеш `{% block content %}`, решта безкоштовно
> - Немає дублювання Bootstrap CDN у кожному файлі

### Порівняння: з наслідуванням vs без

| | Без наслідування | З 3-рівневою ієрархією |
|--|-----------------|----------------------|
| Нова сторінка | Скопіювати весь HTML | 5 рядків `{% extends %}` + content |
| Зміна навігації | Правити всі файли | Тільки `dashboard.html` |
| Bootstrap CDN | Кожен файл | Тільки `base.html` |
| Sidebar | Копіювати у кожен файл | Один раз у `dashboard.html` |

---

## 03 · FORMS EVOLUTION

> Три рівні еволюції форм — від "просто працює" до "красиво і без дублювання".

### Таблиця порівняння

| Tier | Де дивитись | Метод | HTML у шаблоні | Де Bootstrap-класи |
|------|-------------|-------|----------------|--------------------|
| **1 — Raw** | [`notes_project/forms.py`](../../lesson_Django_ORM_Database/notes_project/hello_app/forms.py) | `{{ form.as_p }}` | ~5 рядків | Ніде (немає стилів) |
| **2 — Manual** | [`django_bootstrap_project/`](../django_bootstrap_project/) | Ручний HTML | ~80 рядків | У шаблоні вручну |
| **3 — Crispy** | **цей проєкт** `/notes/new/` | `{% crispy form %}` | **1 рядок** | У `forms.py` через Layout |

Всі три підходи передають **ту саму** `NoteForm`. Різниця — тільки спосіб рендерингу.

---

### Tier 1: Raw Django — `{{ form.as_p }}`

```python
# views.py — нічого особливого
def note_create_raw(request):
    form = NoteForm(user=request.user)
    return render(request, 'hello_app/note_form_raw.html', {'form': form})
```

```html
<!-- note_form_raw.html -->
<form method="post">
  {% csrf_token %}
  {{ form.as_p }}      ← Django генерує <p><label><input></p> без класів
  <button type="submit">Зберегти</button>
</form>
```

**Що генерується:**
```html
<p>
  <label for="id_title">Заголовок:</label>
  <input type="text" name="title" id="id_title" required>
</p>
```

Жодного `class="form-control"`, жодних Bootstrap-стилів.
Валідація **працює**, але виглядає погано.

> **Коли використовувати:** тільки для debug. Ніколи в production.

---

### Tier 2: Manual Bootstrap HTML

```python
# forms.py — вказуємо Bootstrap-класи через widget attrs
class NoteFormManual(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['content'].widget.attrs.update({'class': 'form-control', 'rows': 8})
        self.fields['priority'].widget.attrs.update({'class': 'form-select'})
        # ... повторити для кожного поля
```

```html
<!-- note_form_manual.html — ~80 рядків HTML для 5 полів -->
<form method="post">
  {% csrf_token %}

  <!-- Поле: title -->
  <div class="mb-3">
    <label for="{{ form.title.id_for_label }}" class="form-label fw-semibold">
      {{ form.title.label }}
      {% if form.title.field.required %}<span class="text-danger">*</span>{% endif %}
    </label>
    <input type="text"
           name="{{ form.title.html_name }}"
           id="{{ form.title.id_for_label }}"
           value="{{ form.title.value|default:'' }}"
           class="form-control {% if form.title.errors %}is-invalid{% endif %}"
           autofocus>
    {% if form.title.errors %}
      {% for error in form.title.errors %}<div class="invalid-feedback">{{ error }}</div>{% endfor %}
    {% endif %}
  </div>

  <!-- ... ще ~60 рядків для priority, notebook, content, tags, is_pinned ... -->
</form>
```

**Проблеми Tier 2:**
- 80 рядків HTML тільки для форми
- При додаванні поля в `models.py` → вручну дописати у шаблон
- При зміні Bootstrap-версії → правити кожен шаблон
- 10 форм у застосунку = 800 рядків дублювання

> **Де цей підхід:** у `notes_project` (попередній урок) — саме так там написані форми.
> Це нормальний підхід для невеликих проєктів. Crispy — це upgrade для scale.

---

### Tier 3: Crispy Forms — `{% crispy form %}`

```python
# forms.py — ВСЯ Bootstrap-розмітка описана тут, Python-кодом
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, Submit, Field

class NoteForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset('Основна інформація',
                Field('title', placeholder='Назва нотатки...', autofocus=True),
                Row(Column('priority', css_class='col-md-4'),
                    Column('notebook', css_class='col-md-8')),
            ),
            Fieldset('Зміст нотатки',
                Field('content', rows=8, placeholder='Текст нотатки...'),
            ),
            Submit('submit', 'Зберегти нотатку', css_class='btn btn-primary me-2'),
        )
```

```html
<!-- note_form.html — 1 рядок замість 80 -->
{% load crispy_forms_tags %}
{% crispy form %}
```

**Що генерується автоматично:**
- `<form method="post">` + CSRF токен
- `<div class="mb-3">` для кожного поля
- `<label class="form-label">` з required-зірочкою
- `<input class="form-control">` або `<select class="form-select">`
- `<div class="invalid-feedback">` для помилок
- `<div class="form-text">` для help_text
- `<fieldset>` з `<legend>` для Fieldset
- `<div class="row">` для Row, `<div class="col-md-4">` для Column

---

## 04 · FORMHELPER + LAYOUT

> **FormHelper** — об'єкт, прикріплений до форми, що описує:
> - Атрибути `<form>` тегу (method, action, id, class)
> - Поведінку рендерингу
> - Layout — структуру та порядок полів

### Архітектура FormHelper

```
NoteForm
│
├── fields (Django стандарт)
│   ├── title     CharField
│   ├── content   TextField
│   └── ...
│
└── helper = FormHelper()          ← crispy додає сюди
    ├── form_method = 'post'       ← <form method="post">
    ├── form_id = 'note-form'      ← <form id="note-form">
    ├── form_tag = True            ← рендерити <form>...</form>
    └── layout = Layout(...)       ← структура полів
        ├── Fieldset(...)          ← <fieldset><legend>
        │   ├── Field('title')     ← окреме поле з attrs
        │   └── Row(...)           ← <div class="row">
        │       ├── Column(...)    ← <div class="col-md-4">
        │       └── Column(...)    ← <div class="col-md-8">
        ├── Submit(...)            ← <button type="submit">
        └── HTML('<hr>')           ← довільний HTML
```

### Конвеєр рендерингу

```
{% crispy form %}
     │
     ▼
crispy_forms templatetag
     │  Знаходить form.helper
     │  Знаходить form.helper.layout
     ▼
Layout.render(form, context)
     │
     ├── Fieldset.render()
     │   ├── Field('title').render()  → field.html template
     │   └── Row.render()
     │       └── Column.render()
     ├── Submit.render()              → baseinput.html template
     └── HTML.render()               → direct string
     │
     ▼
Bootstrap 5 HTML
(form-control, mb-3, row, col-md-4, invalid-feedback...)
```

### Атрибути Layout об'єктів

```python
# kwargs → HTML атрибути
Field('title', placeholder='Підказка')   # placeholder="Підказка"
Field('title', autofocus=True)           # autofocus
Field('title', data_custom="val")        # data-custom="val" (підкреслення → дефіс)
Field('title', css_class="extra")        # додатковий CSS клас
Field('title', type="hidden")            # прихований input

# Обгортаючий div
Field('title', wrapper_class="mt-3")     # клас для <div class="mb-3 mt-3">
```

### Де crispy vs де ручний HTML — правило

| Ситуація | Підхід |
|----------|--------|
| Форма займає цілу сторінку | `{% crispy form %}` — повний контроль через Layout |
| Швидкий прототип | `{{ form\|crispy }}` — без FormHelper, просто Bootstrap-стилі |
| Одне поле вбудоване в сторінку | `{{ form.title\|as_crispy_field }}` |
| Форма без Bootstrap (API, email) | `{{ form.as_p }}` або `form.cleaned_data` напряму |

---

## 05 · DASHBOARD ARCHITECTURE

> **SaaS Dashboard** — UI-паттерн для застосунків:
> фіксований sidebar зліва, topbar зверху, scrollable контент по центру.
> Gmail, Notion, Linear — всі побудовані на цьому паттерні.

### Структура Dashboard

```
┌──────────┬───────────────────────────────────────────────────┐
│          │  Topbar: заголовок / пошук / юзер-dropdown        │
│ Sidebar  ├───────────────────────────────────────────────────┤
│          │                                                   │
│ Бренд    │  ← {% block content %}                            │
│ ─────    │                                                   │
│ НОТАТКИ  │  Нотатки / Форма / Записники / Задачі...         │
│  Записн. │                                                   │
│  Всі     │                                                   │
│  + Нова  │                                                   │
│ ЗАДАЧІ   │                                                   │
│  Справи  │                                                   │
│  Покупки │                                                   │
│ ─────    │                                                   │
│ [Запис.] │  (якщо є)                                         │
│ ТЕГИ     │                                                   │
│  + Новий │                                                   │
└──────────┴───────────────────────────────────────────────────┘
```

### Sidebar Context Processor

Sidebar показує **записники** і **теги** — вони потрібні на КОЖНІЙ сторінці.
Але передавати їх з кожного view вручну — це дублювання:

```python
# ❌ Погано — дублювання у кожному view
def note_list(request):
    notes = selectors.get_user_notes(request.user)
    notebooks = selectors.get_user_notebooks(request.user)  # дублювання
    tags = selectors.get_user_tags(request.user)            # дублювання
    return render(request, '...', {'notes': notes, 'notebooks': notebooks, 'tags': tags})

def note_create(request):
    notebooks = selectors.get_user_notebooks(request.user)  # дублювання знову
    tags = selectors.get_user_tags(request.user)            # дублювання знову
    ...
```

**Рішення** — `context_processors.py`:

```python
# ✅ Добре — один раз, автоматично для всіх views
def sidebar_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'sidebar_notebooks': selectors.get_user_notebooks(request.user),
        'sidebar_tags': selectors.get_user_tags(request.user),
    }
```

```python
# settings.py — реєструємо процесор
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            ...
            'hello_app.context_processors.sidebar_context',  # ← тут
        ]
    }
}]
```

Тепер `{{ sidebar_notebooks }}` і `{{ sidebar_tags }}` доступні **в кожному шаблоні** автоматично.

### Active State у навігації

```html
<!-- Підсвічуємо активний пункт меню через request.resolver_match -->
<a href="{% url 'hello_app:note_list' %}"
   class="nav-link text-white {% if request.resolver_match.url_name == 'note_list' %}active{% endif %}">
  Всі нотатки
</a>
```

`request.resolver_match.url_name` повертає ім'я поточного URL — без додаткових змінних у View.

---

## Крок 0 — Запуск

```bash
# 1. Переходимо до папки
cd module_5/lesson_HTML_CSS_Bootstrap/crispy_notes_project

# 2. Встановлюємо залежності
pip install -r requirements.txt

# 3. Застосовуємо міграції
python manage.py migrate

# 4. Створюємо суперюзера
python manage.py createsuperuser

# 5. Запускаємо сервер
python manage.py runserver
```

### Що дивитись у браузері

| URL | Що показує |
|-----|-----------|
| `http://127.0.0.1:8000/notes/` | Dashboard: список нотаток + sidebar |
| `http://127.0.0.1:8000/notes/new/` | **Tier 3**: `{% crispy form %}` — Bootstrap форма з Layout |
| `http://127.0.0.1:8000/notebooks/` | Список записників |
| `http://127.0.0.1:8000/todo/` | Списки справ (ЗАДАЧІ секція) |
| `http://127.0.0.1:8000/shopping/` | Списки покупок |
| `http://127.0.0.1:8000/register/` | Реєстрація нового користувача |
| `http://127.0.0.1:8000/admin/` | Django Admin |

> **Tier 1 і Tier 2 як код для порівняння** (не як живі URL):
> - Tier 1 (`form.as_p`): [`notes_project/hello_app/forms.py`](../../lesson_Django_ORM_Database/notes_project/hello_app/forms.py)
> - Tier 2 (manual Bootstrap): [`django_bootstrap_project/`](../django_bootstrap_project/)

---

## Крок 1 — Settings

```python
# hello_project/settings.py

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'crispy_forms',        # ← 1. базовий пакет
    'crispy_bootstrap5',   # ← 2. template pack для Bootstrap 5
    'debug_toolbar',
    'hello_app',
]

# Налаштовуємо crispy
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
```

```python
# Де шукати шаблони — критично для 3-рівневої ієрархії
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],   # ← глобальні шаблони (base.html, layouts/)
    'APP_DIRS': True,                   # ← шаблони у hello_app/templates/hello_app/
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',  # ← для request.user, request.resolver_match
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'hello_app.context_processors.sidebar_context', # ← sidebar notebooks/tags
        ],
    },
}]

# Django Messages → Bootstrap alert класи
from django.contrib.messages import constants as messages_constants
MESSAGE_TAGS = {
    messages_constants.DEBUG: 'secondary',
    messages_constants.INFO: 'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR: 'danger',  # ← Bootstrap: alert-danger (не alert-error!)
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/notes/'
```

> **Чому `'DIRS': [BASE_DIR / 'templates']`?**
> `base.html` і `layouts/dashboard.html` — глобальні шаблони, не прив'язані до app.
> Django шукає шаблони у двох місцях: `DIRS` (глобальні) і `APP_DIRS` (у кожному app).

---

## Крок 2 — base.html

**Місце:** `crispy_notes_project/templates/base.html`

`base.html` — HTML-скелет. Тут ТІЛЬКИ:
- DOCTYPE, `<head>`, `<body>`
- Bootstrap 5 CDN
- Bootstrap Icons CDN
- Глобальний CSS
- Один `{% block body %}` — весь застосунок йде сюди

```html
<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CrispyNotes</title>

  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
</head>
<body>

  {% block body %}{% endblock %}    ← весь застосунок тут

  <!-- Bootstrap JS -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

> **Правило:** base.html не знає нічого про sidebar, навігацію або контент.
> Він відповідає тільки за: "я правильний HTML5 документ з Bootstrap".

---

## Крок 3 — layouts/dashboard.html

**Місце:** `crispy_notes_project/templates/layouts/dashboard.html`

Рівень 2 ієрархії. Він:
- Extends `base.html`
- Заповнює `{% block body %}` повною Dashboard-розміткою
- Надає два слоти для дочірніх шаблонів:
  - `{% block topbar_title %}` — заголовок у topbar
  - `{% block content %}` — основний контент сторінки

```html
{% extends 'base.html' %}
{% load static %}

{% block body %}
<div class="d-flex vh-100 overflow-hidden">

  <!-- ════════════════════ SIDEBAR ════════════════════ -->
  <nav id="sidebar" class="sidebar d-flex flex-column p-3 text-bg-dark" style="width: 260px;">

    <!-- Бренд -->
    <a href="{% url 'hello_app:note_list' %}" class="d-flex align-items-center text-white mb-3">
      <i class="bi bi-journal-text fs-4 me-2"></i>
      <span class="fs-5 fw-semibold">CrispyNotes</span>
    </a>
    <hr>

    <!-- НОТАТКИ section -->
    <p class="sidebar-label text-uppercase fw-semibold mb-1 px-2">Нотатки</p>
    <ul class="nav nav-pills flex-column mb-3">
      <li>
        <a href="{% url 'hello_app:notebook_list' %}"
           class="nav-link {% if 'notebook' in request.resolver_match.url_name %}active{% endif %}">
          <i class="bi bi-collection me-2"></i>Записники
        </a>
      </li>
      <li>
        <a href="{% url 'hello_app:note_list' %}"
           class="nav-link {% if request.resolver_match.url_name == 'note_list' %}active{% endif %}">
          <i class="bi bi-journal-text me-2"></i>Всі нотатки
        </a>
      </li>
      <li>
        <a href="{% url 'hello_app:note_create' %}"
           class="nav-link {% if request.resolver_match.url_name == 'note_create' %}active{% endif %}">
          <i class="bi bi-plus-circle me-2"></i>Нова нотатка
        </a>
      </li>
    </ul>

    <!-- ЗАДАЧІ section -->
    <p class="sidebar-label text-uppercase fw-semibold mb-1 px-2">Задачі</p>
    <ul class="nav nav-pills flex-column mb-3">
      <li>
        <a href="{% url 'hello_app:todo_list' %}"
           class="nav-link d-flex justify-content-between {% if 'todo' in request.resolver_match.url_name %}active{% endif %}">
          <span><i class="bi bi-check2-square me-2"></i>Список справ</span>
          {% if sidebar_todo_count %}
          <span class="badge bg-primary rounded-pill">{{ sidebar_todo_count }}</span>
          {% endif %}
        </a>
      </li>
      <li>
        <a href="{% url 'hello_app:shopping_list' %}"
           class="nav-link d-flex justify-content-between {% if 'shopping' in request.resolver_match.url_name %}active{% endif %}">
          <span><i class="bi bi-cart me-2"></i>Покупки</span>
          {% if sidebar_shopping_count %}
          <span class="badge bg-secondary rounded-pill">{{ sidebar_shopping_count }}</span>
          {% endif %}
        </a>
      </li>
    </ul>
    <hr>

    <!-- Записники (список, з sidebar_context — context processor!) -->
    {% if sidebar_notebooks %}
    <p class="sidebar-label text-uppercase fw-semibold mb-1 px-2">Записники</p>
    <ul class="nav nav-pills flex-column mb-3">
      {% for nb in sidebar_notebooks %}
      <li>
        <a href="{% url 'hello_app:note_list' %}?notebook={{ nb.pk }}"
           class="nav-link py-1 d-flex justify-content-between">
          <span><span style="color: {{ nb.color }};">●</span> {{ nb.title|truncatechars:18 }}</span>
          <span class="badge bg-secondary">{{ nb.note_count }}</span>
        </a>
      </li>
      {% endfor %}
    </ul>
    {% endif %}

    <!-- ТЕГИ section (завжди видимий header) -->
    <p class="sidebar-label text-uppercase fw-semibold mb-1 px-2">Теги</p>
    {% if sidebar_tags %}
    <div class="px-2 mb-2 d-flex flex-wrap gap-1">
      {% for tag in sidebar_tags %}
      <a href="{% url 'hello_app:note_list' %}?tag={{ tag.pk }}"
         class="badge text-decoration-none"
         style="background-color: {{ tag.color }}; color: white;">
        #{{ tag.name }}
      </a>
      {% endfor %}
    </div>
    {% endif %}
    <ul class="nav nav-pills flex-column mb-3">
      <li>
        <a href="{% url 'hello_app:tag_create' %}" class="nav-link">
          <i class="bi bi-tags me-2"></i>Новий тег
        </a>
      </li>
    </ul>
  </nav>
  <!-- /SIDEBAR -->

  <!-- ════════════════════ MAIN ════════════════════ -->
  <div class="d-flex flex-column flex-grow-1 overflow-auto">

    <!-- TOPBAR: заголовок | пошук | юзер-dropdown -->
    <header class="topbar d-flex align-items-center px-4 py-2">
      <h6 class="mb-0 me-auto fw-semibold">
        {% block topbar_title %}Нотатки{% endblock %}   ← дочірні шаблони підставляють заголовок
      </h6>
      <form class="d-flex me-3" method="get" action="{% url 'hello_app:note_list' %}">
        <input type="search" name="q" class="form-control form-control-sm" placeholder="Пошук нотаток...">
        <button class="btn btn-sm btn-outline-secondary ms-1" type="submit">
          <i class="bi bi-search"></i>
        </button>
      </form>
      <!-- Профіль / Вихід (dropdown праворуч) -->
      <div class="dropdown">
        <a href="#" class="d-flex align-items-center text-decoration-none dropdown-toggle"
           data-bs-toggle="dropdown">
          <i class="bi bi-person-circle fs-5 me-1"></i>
          <span class="small fw-semibold">{{ request.user.username }}</span>
        </a>
        <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow">
          <li><a class="dropdown-item" href="{% url 'hello_app:notebook_list' %}">Мої записники</a></li>
          <li><hr class="dropdown-divider"></li>
          <li>
            <form method="post" action="{% url 'logout' %}">
              {% csrf_token %}
              <button type="submit" class="dropdown-item text-danger">Вийти</button>
            </form>
          </li>
        </ul>
      </div>
    </header>

    <!-- Django Messages → Bootstrap Alerts -->
    {% if messages %}
    <div class="px-4 pt-3">
      {% for message in messages %}
      <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <!-- PAGE CONTENT -->
    <main class="flex-grow-1 p-4">
      {% block content %}{% endblock %}   ← дочірні шаблони підставляють контент
    </main>

  </div>
  <!-- /MAIN -->

</div>
{% endblock %}
```

---

## Крок 4 — Сторінки

**Місце:** `hello_app/templates/hello_app/`

Дочірні шаблони (рівень 3) пишуть **тільки контент**. Sidebar, topbar, Bootstrap — безкоштовно.

**Приклад `note_list.html`:**

```html
{% extends 'layouts/dashboard.html' %}

{% block topbar_title %}Мої нотатки{% endblock %}    ← тільки заголовок

{% block content %}
{# Тільки контент сторінки — sidebar/topbar вже є #}

{% if notes %}
<div class="row row-cols-1 row-cols-md-2 g-3">
  {% for note in notes %}
  <div class="col">
    <div class="card h-100">
      ...
    </div>
  </div>
  {% endfor %}
</div>
{% else %}
  {% include 'components/empty_state.html' with icon="bi-journal" message="Ще немає нотаток" %}
{% endif %}

{% endblock %}
```

---

## Крок 5 — Tier 1: Raw

**Мета:** показати що є у Django "з коробки", без жодних стилів.

> Tier 1 реалізовано у [`notes_project`](../../lesson_Django_ORM_Database/notes_project/) — там форми без crispy.
> Код нижче — для порівняння концепцій.

```python
# views.py
@login_required
def note_create_raw(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            # той самий service що і в Tier 3
            note = services.create_note(
                user=request.user,
                **form.cleaned_data_for_service(),
            )
            return redirect('hello_app:note_detail', pk=note.pk)
    else:
        form = NoteForm(user=request.user)

    return render(request, 'hello_app/note_form_raw.html', {
        'form': form,
        'title': 'Нова нотатка (Raw)',
        'current_tier': 'raw',
    })
```

```html
<!-- note_form_raw.html -->
{% extends 'layouts/dashboard.html' %}
{% block content %}

<form method="post">
  {% csrf_token %}
  {{ form.as_p }}    ← Django генерує <p><label><input></p> для кожного поля
  <button type="submit" class="btn btn-warning">Зберегти</button>
</form>

{% endblock %}
```

**Що `as_p` генерує для `title`:**
```html
<p>
  <label for="id_title">Заголовок:</label>
  <input type="text" name="title" maxlength="200" required id="id_title">
</p>
```

Немає `class="form-control"`. Немає Bootstrap. Виглядає погано, але **функціонує коректно**.

---

## Крок 6 — Tier 2: Manual

**Мета:** показати повний Bootstrap HTML — щоб зрозуміти від чого рятує Tier 3.

> Tier 2 реалізовано у [`django_bootstrap_project`](../django_bootstrap_project/) — там форми з ручним Bootstrap HTML.
> Код нижче — для порівняння концепцій.

```html
<!-- note_form_manual.html — дивись скільки коду для ОДНОГО поля -->
<form method="post">
  {% csrf_token %}

  <!-- Поле: title  ← 14 рядків HTML тільки для одного поля -->
  <div class="mb-3">
    <label for="{{ form.title.id_for_label }}" class="form-label fw-semibold">
      {{ form.title.label }}
      {% if form.title.field.required %}<span class="text-danger">*</span>{% endif %}
    </label>
    <input type="text"
           name="{{ form.title.html_name }}"
           id="{{ form.title.id_for_label }}"
           value="{{ form.title.value|default:'' }}"
           placeholder="Назва нотатки..."
           class="form-control {% if form.title.errors %}is-invalid{% endif %}"
           autofocus>
    {% if form.title.errors %}
      {% for error in form.title.errors %}
      <div class="invalid-feedback">{{ error }}</div>
      {% endfor %}
    {% endif %}
  </div>

  <!-- ... ще ~65 рядків для priority, notebook, content, tags, is_pinned ... -->

  <button type="submit" class="btn btn-secondary">Зберегти</button>
</form>
```

**Підрахунок рядків:**
```
title:     14 рядків
priority:  12 рядків (select)
notebook:  14 рядків (select + queryset)
content:   12 рядків (textarea)
tags:      14 рядків (multiple select)
is_pinned: 10 рядків (checkbox)
buttons:    3 рядки
─────────────────
ВСЬОГО:   ~80 рядків HTML тільки для форми
```

> Помнож на 5 форм у застосунку → **400 рядків дублювання**.
> Змінив Bootstrap-версію → правиш 400 рядків.

---

## Крок 7 — Tier 3: Crispy

**Мета:** замінити 80 рядків HTML на 10 рядків Python.

### forms.py — повний код `NoteForm`

```python
# hello_app/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout, Submit, Row, Column,
    Fieldset, HTML, Div, Field
)
from .models import Note, Notebook, Tag


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'priority', 'notebook', 'tags', 'is_pinned']
        # ↑ НІ ЖОДНИХ widget attrs — crispy додає Bootstrap-класи автоматично!

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Security: фільтруємо FK по поточному user
        if user is not None:
            self.fields['notebook'].queryset = Notebook.objects.filter(user=user)
            self.fields['tags'].queryset = Tag.objects.filter(user=user)

        # FormHelper — описуємо форму Python-кодом
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'note-form'

        # Layout — структура полів
        self.helper.layout = Layout(
            # Секція 1: основна інформація
            Fieldset('Основна інформація',
                Field('title', placeholder='Назва нотатки...', autofocus=True),
                Row(
                    Column('priority', css_class='col-md-4'),
                    Column('notebook', css_class='col-md-8'),
                ),
            ),
            # Секція 2: зміст
            Fieldset('Зміст нотатки',
                Field('content', rows=8, placeholder='Текст нотатки...'),
            ),
            # Секція 3: теги та опції
            Fieldset('Теги та параметри',
                'tags',
                Div(Field('is_pinned'), css_class='form-check mt-2'),
            ),
            # Розділювач
            HTML('<hr class="my-4">'),
            # Кнопки
            Submit('submit', 'Зберегти нотатку', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-outline-secondary">Скасувати</a>'),
        )
```

### note_form.html — весь шаблон

```html
{% extends 'layouts/dashboard.html' %}
{% load crispy_forms_tags %}

{% block topbar_title %}{{ title }}{% endblock %}

{% block content %}
<div class="row">
  <div class="col-lg-8">
    <div class="card shadow-sm">
      <div class="card-header bg-primary text-white">
        <h6 class="mb-0"><i class="bi bi-journal-plus me-2"></i>{{ title }}</h6>
      </div>
      <div class="card-body">

        {% crispy form %}

        {# ↑ Один тег замість 80 рядків HTML.
           FormHelper + Layout у forms.py описують ВСЮ Bootstrap-розмітку. #}

      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Що робить `{% crispy form %}` покроково

```
1. {% load crispy_forms_tags %} — реєструє тег

2. {% crispy form %} — викликає do_uni_form() в crispy_forms_tags.py

3. Знаходить form.helper — наш FormHelper з Layout

4. Рендерить form.helper.layout:
   ├── Fieldset('Основна інформація', ...) →
   │     <fieldset>
   │       <legend>Основна інформація</legend>
   │       ...поля...
   │     </fieldset>
   │
   ├── Field('title', placeholder='...') →
   │     <div class="mb-3">
   │       <label for="id_title" class="form-label">Заголовок *</label>
   │       <input type="text" name="title" id="id_title"
   │              class="form-control" placeholder="Назва нотатки..."
   │              autofocus>
   │     </div>
   │
   ├── Row(Column('priority', css_class='col-md-4'), ...) →
   │     <div class="row">
   │       <div class="col-md-4">...priority field...</div>
   │       <div class="col-md-8">...notebook field...</div>
   │     </div>
   │
   └── Submit('submit', 'Зберегти') →
         <input type="submit" value="Зберегти" class="btn btn-primary me-2">

5. Додає <form method="post"> та {% csrf_token %} автоматично
```

### Порівняння views для Tier 3

```python
# views.py — view для Tier 3 нічим особливим не відрізняється від Tier 2!
# Crispy — це виключно рівень PRESENTATION, не бізнес-логіки.

@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            note = services.create_note(
                user=request.user,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                priority=form.cleaned_data['priority'],
                notebook=form.cleaned_data.get('notebook'),
                tag_ids=[t.pk for t in form.cleaned_data.get('tags', [])],
                is_pinned=form.cleaned_data.get('is_pinned', False),
            )
            messages.success(request, f'Нотатку "{note.title}" створено!')
            return redirect('hello_app:note_detail', pk=note.pk)
    else:
        form = NoteForm(user=request.user)

    return render(request, 'hello_app/note_form.html', {
        'form': form,
        'title': 'Нова нотатка',
        'current_tier': 'crispy',
    })
```

> **Висновок:** `services.create_note()` — та сама функція з `notes_project`.
> Crispy не змінює бізнес-логіку. Він змінює тільки те як форма **виглядає**.

### Патерн: `form_tag = False` — вбудовані форми

Іноді форма є **частиною більшої сторінки**, а не окремою сторінкою.
Наприклад: список завдань + inline-форма для додавання нового завдання на тій самій сторінці.

**Проблема:** якщо у шаблоні вже є `<form action="/todo/5/items/add/">`, а crispy теж рендерить
`<form>` — виходить nested `<form>` — **невалідний HTML**, браузери ігнорують внутрішній `<form>`.

**Рішення:** `self.helper.form_tag = False` — crispy рендерить тільки поля та кнопки,
але **не** `<form>...</form>` обгортку. Шаблон сам надає тег форми.

```python
# forms.py — TodoItemForm: вбудовується всередині <form> що є в шаблоні
class TodoItemForm(forms.Form):
    text = forms.CharField(max_length=500, label='Завдання')
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False          # ← не рендерити <form>...</form>
        self.helper.form_show_labels = False  # ← без label (компактний вигляд)
        self.helper.layout = Layout(
            Row(
                Column(Field('text', placeholder='Нове завдання...'), css_class='col-md-7'),
                Column(Field('due_date'), css_class='col-md-3'),
                Column(Submit('submit', '+ Додати', css_class='btn btn-primary w-100'),
                       css_class='col-md-2'),
            ),
        )
```

```html
<!-- todo_detail.html — шаблон надає <form> тег, crispy — тільки поля -->
<form method="post" action="{% url 'hello_app:todo_item_add' list.pk %}">
  {% csrf_token %}
  {% crispy item_form %}   ← рендерить Row з полями та кнопкою, але БЕЗ <form>
</form>
```

| Сценарій | `form_tag` |
|----------|-----------|
| Форма займає окрему сторінку (note_create, note_edit) | `True` (за замовчуванням) |
| Форма вбудована у сторінку (inline add item) | `False` |

---

## Крок 8 — Context Processor

```python
# hello_app/context_processors.py
from django.db import OperationalError
from django.db.models import Q
from .models import TodoList, ShoppingList
from . import selectors


def sidebar_context(request):
    """
    Автоматично додає sidebar_notebooks, sidebar_tags і лічильники задач у кожен шаблон.
    Виконується при кожному запиті для автентифікованих користувачів.
    """
    if not request.user.is_authenticated:
        return {
            'sidebar_notebooks': [], 'sidebar_tags': [],
            'sidebar_todo_count': 0, 'sidebar_shopping_count': 0,
        }

    user = request.user

    # try/except — захист якщо міграція ще не застосована (нові M2M таблиці)
    try:
        todo_count = TodoList.objects.filter(
            Q(user=user) | Q(shared_with=user), is_completed=False
        ).distinct().count()
        shopping_count = ShoppingList.objects.filter(
            Q(user=user) | Q(shared_with=user)
        ).distinct().count()
    except OperationalError:
        todo_count = 0
        shopping_count = 0

    return {
        'sidebar_notebooks': selectors.get_user_notebooks(user),
        'sidebar_tags': selectors.get_user_tags(user),
        'sidebar_todo_count': todo_count,       # ← badge у "Список справ"
        'sidebar_shopping_count': shopping_count,  # ← badge у "Покупки"
    }
```

> **Навіщо `try/except OperationalError`?**
> Context processor виконується при **кожному** запиті. Якщо міграція для нової таблиці
> ще не застосована (наприклад, під час розробки після `git pull`), QuerySet впаде з
> `OperationalError: no such table`. Guard дозволяє серверу продовжити роботу — лічильники
> просто повернуть 0 замість 500 помилки.

**Реєстрація у settings.py:**
```python
'context_processors': [
    'django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'hello_app.context_processors.sidebar_context',   # ← наш
],
```

**Використання у будь-якому шаблоні (без передачі з View):**
```html
{% for nb in sidebar_notebooks %}
  <a href="?notebook={{ nb.pk }}">{{ nb.title }}</a>
{% endfor %}
```

> **Важливо:** Context processor виконується при **кожному** HTTP запиті.
> Тому selector повинен бути ефективним — `select_related`, `annotate`, не N+1.

---

## Крок 9 — Components

**Місце:** `crispy_notes_project/templates/components/`

Компоненти — повторювані блоки UI, що використовуються через `{% include %}`.

### `components/empty_state.html`

```html
{# Порожній стан — "у вас ще немає нотаток" #}
<div class="text-center py-5">
  <i class="bi {{ icon|default:'bi-inbox' }} display-1 text-muted"></i>
  <p class="text-muted mt-3">{{ message }}</p>
  {% if action_url %}
  <a href="{{ action_url }}" class="btn btn-primary">{{ action_label }}</a>
  {% endif %}
</div>
```

**Використання:**
```html
{% if not notes %}
  {% include 'components/empty_state.html' with
     icon="bi-journal"
     message="Ще немає нотаток"
     action_url=note_create_url
     action_label="Створити першу" %}
{% endif %}
```

### `components/pagination.html`

```html
{# Bootstrap Pagination #}
{% if page_obj.has_other_pages %}
<nav>
  <ul class="pagination justify-content-center">
    {% if page_obj.has_previous %}
    <li class="page-item">
      <a class="page-link" href="?page={{ page_obj.previous_page_number }}">←</a>
    </li>
    {% endif %}

    {% for num in page_obj.paginator.page_range %}
    <li class="page-item {% if page_obj.number == num %}active{% endif %}">
      <a class="page-link" href="?page={{ num }}">{{ num }}</a>
    </li>
    {% endfor %}

    {% if page_obj.has_next %}
    <li class="page-item">
      <a class="page-link" href="?page={{ page_obj.next_page_number }}">→</a>
    </li>
    {% endif %}
  </ul>
</nav>
{% endif %}
```

### `components/confirm_modal.html`

```html
{# Bootstrap Modal для підтвердження видалення #}
<div class="modal fade" id="confirmModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header bg-danger text-white">
        <h5 class="modal-title">Підтвердити видалення</h5>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        Ви впевнені що хочете видалити <strong id="deleteItemName"></strong>?
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Скасувати</button>
        <form id="deleteForm" method="post">
          {% csrf_token %}
          <button type="submit" class="btn btn-danger">Видалити</button>
        </form>
      </div>
    </div>
  </div>
</div>
```

---

## Структура файлів

```
crispy_notes_project/
│
├── requirements.txt              ← django-crispy-forms, crispy-bootstrap5, debug-toolbar
│
├── hello_project/
│   ├── settings.py               ← CRISPY_TEMPLATE_PACK, context_processors, MESSAGE_TAGS
│   └── urls.py                   ← accounts/ (login/logout) + hello_app/ + debug_toolbar
│
├── hello_app/
│   ├── models.py                 ← Note, Notebook, Tag, TodoList, TodoItem,
│   │                                ShoppingList, ShopItem, Reminder
│   ├── services.py               ← create/update/delete для всіх моделей
│   ├── selectors.py              ← get_user_notes, get_user_notebooks, get_user_tags,
│   │                                get_todo_lists, get_shopping_lists...
│   ├── context_processors.py     ← sidebar_context → notebooks, tags,
│   │                                todo_count, shopping_count (+ OperationalError guard)
│   ├── forms.py                  ← ★ NoteForm, NotebookForm, TagForm,
│   │                                TodoListForm, TodoItemForm (form_tag=False),
│   │                                ShoppingListForm, ShopItemForm (form_tag=False),
│   │                                ReminderForm, ShareForm
│   ├── views.py                  ← note CRUD + todo CRUD + shopping CRUD + reminders + register
│   ├── urls.py
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_shoppinglist_shared_with_todolist_shared_with.py  ← M2M shared_with
│   └── templates/hello_app/
│       ├── note_list.html            ← extends layouts/dashboard.html
│       ├── note_detail.html          ← з inline ReminderForm (form_action у view)
│       ├── note_form.html            ← Tier 3: {% crispy form %}  ★
│       ├── note_confirm_delete.html
│       ├── notebook_list.html
│       ├── notebook_form.html        ← {% crispy form %}
│       ├── tag_form.html             ← {% crispy form %}
│       ├── todo_list.html            ← мої + спільні списки справ
│       ├── todo_detail.html          ← inline TodoItemForm (form_tag=False)
│       ├── todo_form.html            ← {% crispy form %}
│       ├── todo_confirm_delete.html
│       ├── shopping_list.html
│       ├── shopping_detail.html      ← inline ShopItemForm (form_tag=False)
│       ├── shopping_form.html        ← {% crispy form %}
│       ├── shopping_confirm_delete.html
│       └── share_form.html           ← ShareForm (додати юзера до shared_with)
│
└── templates/                    ← ГЛОБАЛЬНІ шаблони (DIRS в settings)
    ├── base.html                      ← Рівень 1: HTML5 + Bootstrap CDN
    ├── layouts/
    │   └── dashboard.html             ← Рівень 2: Sidebar (НОТАТКИ/ЗАДАЧІ/ТЕГИ) + Topbar
    ├── registration/
    │   ├── login.html                 ← Bootstrap card, посилання на register
    │   └── register.html             ← реєстрація нового користувача
    └── components/
        ├── pagination.html            ← Bootstrap pagination
        ├── empty_state.html           ← "немає даних" placeholder
        └── confirm_modal.html         ← Bootstrap modal для delete
```

---

## Підсумок: що і де вчити

| Концепція | Де дивитись у коді |
|-----------|-------------------|
| **Template Inheritance** | `base.html` → `layouts/dashboard.html` → `note_list.html` |
| **FormHelper + Layout** | `hello_app/forms.py` — `NoteForm.__init__` |
| **3 рівні форм** | `notes_project` (Tier 1) · `django_bootstrap_project` (Tier 2) · `/notes/new/` (Tier 3) |
| **form_tag = False** | `forms.py` — `TodoItemForm`, `ShopItemForm` (inline forms) |
| **Context Processor** | `hello_app/context_processors.py` + `settings.py TEMPLATES` |
| **OperationalError guard** | `context_processors.py` — `try/except` для нових таблиць |
| **Active nav state** | `dashboard.html` — `request.resolver_match.url_name` |
| **Sidebar секції** | `dashboard.html` — НОТАТКИ / ЗАДАЧІ / ТЕГИ з `sidebar-label` |
| **M2M shared_with** | `models.py` `TodoList.shared_with` + міграція 0002 |
| **Django Messages** | `dashboard.html` блок `{% if messages %}` + `settings.py MESSAGE_TAGS` |
| **Components** | `templates/components/` + `{% include %}` у сторінках |
| **Services/Selectors** | `services.py` / `selectors.py` (детально у `notes_project/README.md`) |

---

## Документація

| Файл | Опис |
|------|------|
| [`../DESIGN_FOUNDATIONS.md`](../DESIGN_FOUNDATIONS.md) | UX, CRAP, Bootstrap, ієрархія шаблонів, Crispy — теорія |
| [`../CRISPY_FORMS.md`](../CRISPY_FORMS.md) | Повний довідник: FormHelper, Layout, Bootstrap компоненти, Dynamic API |
| [`../ADVANCED_TEMPLATES.md §3`](../ADVANCED_TEMPLATES.md) | FormHelper + Layout — деталі |
| [`../ADVANCED_TEMPLATES.md §5`](../ADVANCED_TEMPLATES.md) | SaaS Dashboard Architecture |
| [`../../lesson_Django_ORM_Database/notes_project/README.md`](../../lesson_Django_ORM_Database/notes_project/README.md) | ORM, Services/Selectors, міграції — фундамент цього проєкту |
