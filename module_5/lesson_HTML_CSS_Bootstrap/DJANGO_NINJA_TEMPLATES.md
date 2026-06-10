# Django Ninja + Rendering Architecture

> Django Ninja — швидкий API-фреймворк поверх Django з Python type hints.
> Незважаючи на API-орієнтованість, він повністю використовує Django rendering engine
> для HTML-відповідей — той самий `render()`, `TemplateResponse`, DTL, Jinja2.

---

---
- **🧠 Ментальна модель:** Django Ninja — це як FastAPI, вбудований всередину Django. Він бере найкраще з обох світів: потужну екосистему Django (ORM, auth, адмінка, шаблони) і сучасний API-стиль FastAPI (type hints, Pydantic, автодокументація). Уявіть, що у вас є Ferrari (FastAPI), але він їздить по зрілій міській інфраструктурі Django.
- **📚 Чому це існує:** До Ninja, Django-розробники обирали між "повним Django" (views, forms, HTML — але складно будувати API) або "чистим DRF" (JSON API — але багато бойлерплейту і конфігурації). Ninja заповнив цю нішу: простий API + повна підтримка Django.
- **🌐 Що відбувається під капотом:** Ninja реєструється як звичайний Django URL маршрут. Django не знає, що всередині — Ninja. Ninja отримує request, запускає свій власний роутер, виконує Pydantic-валідацію, викликає вашу функцію, і серіалізує відповідь. Для Django це просто ще один view.
- **❌ Типова помилка початківця:** Думати, що Ninja "замінює" Django views. Ні! Ninja і Django views живуть разом. HTML-сторінки — через Django views, JSON API — через Ninja. Разом вони утворюють повноцінний застосунок.
---

## 0. Що таке Django Ninja

> Перш ніж вивчати синтаксис, критично важливо зрозуміти, ЧОМУ існують три різні способи будувати відповіді в Django-екосистемі і коли обирати кожен з них.

**Django Views = "все в одному"**
Традиційні Django views обробляють HTML-форми, redirect-и, повідомлення (messages framework), сесії — все це вбудовано і зручно. Ідеальні для класичних веб-застосунків, де сервер формує повну HTML-сторінку і браузер просто відображає її. Якщо ви будуєте блог, CMS, або будь-який сайт без мобільного додатку — Django views це правильний вибір.

**DRF (Django REST Framework) = "чистий API"**
DRF поставляється з потужним serializers-механізмом, browsable API, детальними правами доступу, ViewSets і Routers. Призначений для великих команд, де фронтенд (React/Vue) повністю відокремлений від бекенду. Велика кількість конфігурації — це плата за гнучкість. Якщо у вас окрема команда фронтендерів і бекендерів — DRF це зрілий вибір.

**Django Ninja = "API з суперсилами"**
Ninja використовує Python type hints напряму. Немає `serializers.py` — є просто Pydantic-класи. Немає `APIView.get()` — є просто функція. Автоматична валідація, автоматична документація, висока продуктивність. Ідеальний для гібридних застосунків, де є і HTML-сторінки (через Django templates), і JSON API (для мобільного додатку або HTMX). **Саме цю архітектуру ми вивчаємо.**

**Коли використовувати Ninja РАЗОМ з шаблонами?**
Уявіть застосунок нотаток: веб-браузер отримує повні HTML-сторінки через Django views, мобільний додаток отримує JSON через Ninja API, а HTMX-запити отримують HTML-фрагменти через Ninja endpoints з `response=None`. Один бекенд, один Django ORM, один набір моделей — три "вікна" в дані.

### Порівняння з Django REST Framework

| | Django (views) | Django Ninja | Django REST Framework |
|-|----------------|-------------|----------------------|
| **Формат відповіді** | HTML (SSR) | JSON + HTML | JSON |
| **Валідація** | Django Forms | Pydantic v2 | DRF Serializers |
| **Документація API** | Немає | OpenAPI/Swagger (авто) | Немає (потребує drf-spectacular) |
| **Type hints** | Немає | Повна підтримка | Часткова |
| **Продуктивність** | Середня | Висока | Середня |
| **HTML шаблони** | Так | Так (через Django engine) | Рідко |

### Архітектурна позиція Django Ninja

> Ця діаграма показує найважливішу концепцію: той самий Django-сервер може одночасно відповідати HTML-сторінками (SSR), JSON (API) і HTML-фрагментами (HTMX). Кожен тип запиту іде своїм маршрутом, але всі вони звертаються до одних і тих самих Django-моделей і бізнес-логіки.

```
Браузер/Клієнт
    │
    ├── GET /notes/          →  Django View → render() → HTML (SSR)
    ├── GET /api/notes/      →  Ninja Router → Pydantic → JSON (API)
    ├── POST /api/notes/     →  Ninja Router → Pydantic validation → JSON
    └── GET /notes/42/partial →  Django View → TemplateResponse → HTML фрагмент (HTMX)
```

---

---
- **🧠 Ментальна модель:** NinjaAPI — це "головний диспетчер", а Router — це "відділ". Ви реєструєте відділи (роутери) в диспетчері, і він знає, куди направляти запити. Django взагалі нічого не знає про Ninja — він бачить тільки `api.get_urls()` як звичайний список URL-патернів.
- **📚 Чому це існує:** Ninja має власну систему маршрутизації, незалежну від Django URL patterns. Це дозволяє йому додавати middleware для валідації, автоматично збирати OpenAPI-специфікацію, і виконувати Pydantic-перевірку до того, як запит дійде до вашого коду. Django отримує вже оброблений запит.
- **🌐 Що відбувається під капотом:** `api.get_urls()` повертає звичайний Django URLconf список. Всередині кожного URL — Ninja's view function, яка запускає роутер, виконує валідацію параметрів через Pydantic, викликає вашу функцію і серіалізує результат.
- **❌ Типова помилка початківця:** Намагатися додати Ninja endpoints прямо в `urls.py` як звичайні Django views. Ninja endpoints ПОВИННІ бути зареєстровані через `router.get()` / `router.post()` і підключені до `NinjaAPI` через `api.add_router()`.
---

## 1. Встановлення та базова конфігурація

> Зверніть увагу на різницю між `NinjaAPI` (головний об'єкт) і `Router` (модульний роутер для окремих ресурсів). `NinjaAPI` — один на проект, `Router` — один на "bounded context" або ресурс (notes, users, tags тощо). Це забезпечує масштабованість: кожен розробник у команді працює зі своїм роутером.

> Паттерн `api.get_urls()` — ключовий момент інтеграції. Ви не додаєте Ninja views по одному в `urlpatterns`. Натомість, ви передаєте Django весь список Ninja URLs одним викликом. Чому окремі роутери на кожну фічу? Тому що це "bounded contexts" — кожен роутер відповідає за одну предметну область і може бути в окремому файлі, тестуватися незалежно, і вимикатися без впливу на інші.

```bash
pip install django-ninja
```

> Нижче — мінімальна конфігурація підключення Ninja до Django-проекту. Зверніть увагу: `path('api/', api.urls)` передає Django не один URL, а цілий список URLs (все, що ви зареєстрували в Ninja роутерах). Рядок `include_in_schema=False` у деяких endpoints пізніше означатиме "не показувати в Swagger" — корисно для HTML-endpoints, які не призначені для API-клієнтів.

```python
# hello_project/urls.py
from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI

# Створюємо API instance
api = NinjaAPI(
    title="Notes API",
    version="1.0.0",
    description="API для управління нотатками",
)

# Підключаємо роутери (з окремих файлів)
from hello_app.api import router as notes_router
api.add_router("/notes/", notes_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hello_app.urls')),       # ← HTML views (SSR)
    path('api/', api.urls),                     # ← Ninja API (/api/docs/ — Swagger)
]
```

---

----
- **🧠 Ментальна модель:** `render()` — це мікрохвильовка: ви кладете їжу (context), натискаєте кнопку, отримуєте готову страву (HTML) одразу. `TemplateResponse` — це розумний термостат: він запам'ятовує інструкції (template + context), але виконує їх пізніше, дозволяючи комусь по дорозі змінити налаштування.
- **📚 Чому це існує:** `TemplateResponse` існує для того, щоб middleware міг модифікувати дані ПЕРЕД рендерингом. Context processors (які додають `request.user`, `MEDIA_URL` тощо в кожен шаблон) реалізовані саме через цю механіку відкладеного рендерингу.
- **🌐 Що відбувається під капотом:** Коли Django отримує `TemplateResponse` від view, він перевіряє `response.is_rendered`. Якщо `False` — запускає `response.render()`, який викликає `template.render(context)`. Весь middleware-стек виконується до цього моменту.
- **❌ Типова помилка початківця:** Думати, що `TemplateResponse` "краще" за `render()` завжди. Для більшості views `render()` простіший і правильніший. `TemplateResponse` потрібен тільки тоді, коли middleware або post-render callbacks повинні отримати доступ до незрендерованого context.
---

## 2. HTML Response Pipeline — як Django Ninja повертає HTML

> Перш ніж дивитися на код, розберемо критичну різницю між двома способами повернути HTML. Це не просто стилістична відмінність — це архітектурна різниця в тому, КОЛИ відбувається компіляція шаблону.

```
The CRITICAL difference:

render() = EAGER (негайний) — як мікрохвильовка
  1. Отримує template файл
  2. Компілює його у Node tree
  3. Рендерить з context (замінює {{ }}, {% %})
  4. Повертає HttpResponse (готово, HTML це вже рядок)
  Тільки після всіх 4 кроків response об'єкт створено

TemplateResponse = LAZY (відкладений) — як розумний термостат
  1. Створює TemplateResponse об'єкт (швидко, без рендерингу!)
  2. Зберігає template_name і context_data як атрибути
  3. Повертає TemplateResponse (template ЩЕ не скомпільовано)
  4. Django викликає response.render() ПІЗНІШЕ (в middleware стеку)
  5. Тепер template компілюється

ЧОМУ це важливо?
  Middleware отримує шанс ЗМІНИТИ context ДО рендерингу:

  render()         → response.content = b"<html>..." (вже HTML рядок)
  TemplateResponse → response.context_data = {...} (ще словник!)

  Тому з TemplateResponse:
    ваш GlobalContextMiddleware може додати {'user_count': 42} в context
    І цей user_count буде доступний в шаблоні через {{ user_count }}
    БЕЗ жодних змін у view коді

  З render(): запізно — HTML вже є рядком байтів.
```

> Зверніть на рядок `response=None` у Ninja decorators. Це говорить Ninja: "не намагайся серіалізувати відповідь через Pydantic, я поверну HttpResponse сам". Без `response=None` Ninja спробує серіалізувати ваш HttpResponse об'єкт у JSON і зламається.

```python
# hello_app/api.py
from ninja import Router
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Note

router = Router()
```

#### Шлях 1: `HttpResponse` з `render()` — негайна компіляція

> Цей endpoint — найпростіший спосіб повернути HTML з Ninja. `render()` виконує всю роботу: знаходить шаблон, компілює його, замінює `{{ notes }}` реальними даними, і повертає готовий HTML рядок. Зверніть на коментар `Content-Type: text/html` — браузер знає, що це HTML, а не JSON, завдяки цьому заголовку.

```python
@router.get("/html/", response=None)
def note_list_html(request):
    """
    Повертає повну HTML-сторінку.
    render() негайно компілює шаблон і повертає готовий HTML-рядок.
    """
    notes = Note.objects.all().order_by('-created_at')
    context = {'notes': notes}

    # render() = load template → compile → render with context → HttpResponse
    return render(request, 'hello_app/note_list.html', context)
    # Content-Type: text/html; charset=utf-8
```

#### Шлях 2: `TemplateResponse` — відкладена компіляція

> Цей endpoint робить те саме, але по-іншому. `TemplateResponse` НЕ компілює шаблон одразу. Він зберігає `template_name` і `context` як атрибути об'єкту відповіді. Django middleware стек отримує цей об'єкт і може додати дані (наприклад, `response.context_data['global_settings'] = ...`) перед тим, як шаблон буде скомпільовано. Для розуміння — додайте `print(response.is_rendered)` до і після `get_response(request)` в middleware і побачите `False` → `True`.

```python
@router.get("/html/lazy/", response=None)
def note_list_lazy(request):
    """
    TemplateResponse відкладає фінальну компіляцію.
    Template + Context зберігаються окремо до самого кінця pipeline.
    Middleware може модифікувати context перед рендерингом.
    """
    notes = Note.objects.all()
    context = {'notes': notes}

    # TemplateResponse НЕ компілює одразу
    # content_type за замовчуванням: text/html; charset=utf-8
    return TemplateResponse(request, 'hello_app/note_list.html', context)
```

### `render()` vs `TemplateResponse` — різниця під капотом

> Ця діаграма — найважливіше для розуміння. Зосередьтеся на стрілці "Middleware стек": саме тут `TemplateResponse` дає middleware можливість втрутитися. Context processors в Django (ті, що додають `request`, `user`, `messages` в кожен шаблон) — це і є ця механіка.

```
render():
─────────
View → render(request, 'tmpl.html', context)
              │
              ├── 1. get_template('tmpl.html')  → читає файл з диску (або кеш)
              ├── 2. template.render(context)    → компілює → HTML string
              └── 3. return HttpResponse(html)   → відповідь готова ЗАРАЗ

TemplateResponse():
───────────────────
View → TemplateResponse(request, 'tmpl.html', context)
              │
              ├── 1. Зберігає template_name і context (НЕ компілює!)
              │
              → Middleware стек (може змінити response.context_data)
              │
              ├── 2. render()  ← викликається автоматично наприкінці
              └── 3. return HttpResponse(html)

Перевага TemplateResponse:
middleware може додати дані в context (наприклад, глобальні налаштування,
A/B тести, аналітику) — без зміни view коду.
```

---

---
- **🧠 Ментальна модель:** SSR (Server-Side Rendering) — це як замовити готову піцу (HTML), а не купити інгредієнти (JSON) і готувати вдома (JavaScript). Ninja додає до цього процесу "охоронця на вході": Pydantic-валідацію, яка перевіряє запит ще до того, як ваш код взагалі виконується.
- **📚 Чому це існує:** MVT (Model-View-Template) — архітектурний патерн Django. Model знає про дані, View знає про бізнес-логіку, Template знає про відображення. Ninja вписується в цю схему як "розумний диспетчер" перед View — він обробляє валідацію, щоб View міг зосередитися тільки на бізнес-логіці.
- **🌐 Що відбувається під капотом:** Кожен крок у lifecycle — окремий модуль Django. Middleware — ланцюжок WSGI-обгорток. URL Dispatcher — `RegexURLResolver`. Template Engine — окремий модуль з власним кешем. Розуміння цього pipeline допоможе вам правильно розміщувати логіку.
- **❌ Типова помилка початківця:** Розміщувати бізнес-логіку в шаблоні (через template tags або методи моделі, що роблять запити). Вся логіка — у View. Шаблон тільки відображає готові дані.
---

## 3. SSR Architecture — модель MVT у Django Ninja

> Ключова відмінність від звичайних Django views: Ninja додає **крок 4a** — Pydantic-валідацію параметрів запиту **до** виконання вашої функції. Якщо в URL написано `/api/notes/abc/` (рядок замість числа), Ninja поверне `422 Unprocessable Entity` автоматично — ваша функція навіть не почне виконуватися. Це як мати охоронця на вході в клуб: без відповідного ID (правильного типу даних) — не заходиш.

> Крок 6 (Template Engine) особливо важливий для розуміння продуктивності. "Compile: HTML text → Node tree (кешується після першого разу)" — це означає, що Django розбирає `{% for %}`, `{% if %}`, `{{ var }}` тільки один раз на запуск сервера (у production з cached.Loader). При наступних запитах — використовується вже готовий Node tree з пам'яті.

### Request Lifecycle — повний шлях

```
1. Browser: HTTP GET /api/notes/html/
            │
2. Django Middleware Stack (SecurityMiddleware, SessionMiddleware, ...)
            │
3. URL Dispatcher: path('api/', api.urls)
            │
4. Ninja Router: GET "/notes/html/" → note_list_html(request)
            │
5. View (Ninja endpoint):
   ├── ORM: Note.objects.all()  → SQL → Python objects
   ├── context = {'notes': queryset, 'user': request.user}
   └── render(request, 'note_list.html', context)
            │
6. Template Engine:
   ├── Locate: APP_DIRS=True → hello_app/templates/hello_app/note_list.html
   ├── Load: читає файл з диску
   ├── Compile: HTML text → Node tree (кешується після першого разу)
   ├── Render: замінює {{ notes }}, {% for %}, {% url %} → HTML string
   └── Inherit: {% extends 'base.html' %} → рекурсивна компіляція
            │
7. HttpResponse(html_string)
   Content-Type: text/html; charset=utf-8
   Status: 200 OK
            │
8. Middleware Stack (відповідь назад)
            │
9. Browser:
   ├── Parse HTML → DOM Tree
   ├── Parse CSS → CSSOM Tree
   ├── Render Tree → Layout → Paint
   └── Request static assets (CSS, JS)
```

### Архітектурна межа — де Python "вмирає"

> Ця концепція — одна з найважливіших в веб-розробці. Python-об'єкти існують тільки на сервері, в оперативній пам'яті, під час обробки запиту. Після `render()` вони перетворюються в рядок символів (HTML). Браузер ніколи не бачить Python-об'єкт — він бачить тільки текст. Якщо вам потрібно передати "живі" дані в браузер (для JavaScript), потрібен або JSON API, або вбудований JSON у HTML (через `{{ data|json_script }}`).

```python
# View (Python World)
note = Note.objects.get(pk=1)   # Python object з методами
notes = Note.objects.all()       # QuerySet з ORM методами

# Після render() ця межа перетинається:
# Python object → "{{ note.title }}" → "Моя перша нотатка"
# QuerySet      → "{% for n in notes %}" → HTML рядки

# Браузер отримує тільки:
# <h1>Моя перша нотатка</h1>
# Python об'єктів більше не існує в контексті відповіді
```

---

---
- **🧠 Ментальна модель:** Той самий Django-model, два "об'єктиви". JSON endpoint — це мікроскоп для машин (структуровані дані, точні типи). HTML endpoint — це вітрина для людей (гарний інтерфейс, навігація, стилі). Сама "колекція" (база даних) одна.
- **📚 Чому це існує:** Content negotiation — концепція, де один ресурс може бути поданий у різних форматах залежно від того, хто запитує. В деяких фреймворках (наприклад DRF) один endpoint може повертати і HTML і JSON залежно від заголовку `Accept`. Ninja свідомо розділяє їх на окремі endpoints — це чистіше, простіше для тестування, і менш магічно.
- **🌐 Що відбувається під капотом:** Коли Ninja endpoint повертає `Note.objects.all()` (QuerySet), Ninja викликає Pydantic `NoteOut.from_orm(note)` для кожного об'єкту, потім `json.dumps()` для всього списку. Content-Type автоматично встановлюється в `application/json`.
- **❌ Типова помилка початківця:** Забути `response=None` для HTML endpoints. Без нього Ninja намагається серіалізувати `HttpResponse` об'єкт у JSON — і отримує помилку або порожній відповідь. `response=None` каже Ninja: "довіряю тобі, поверну HttpResponse сам".
---

## 4. JSON API vs HTML Endpoints — порівняння

> Зверніть на ключову архітектурну ідею: мобільний додаток і веб-браузер звертаються до однієї бази даних, через одні Django-моделі, але отримують різні "вікна" в дані. Мобільний додаток отримує чистий JSON і будує свій UI (Swift/Kotlin). Браузер отримує готовий HTML. Обидва endpoints можуть жити в одному файлі `api.py` і ділити спільну бізнес-логіку.

> Поняття "content negotiation" тут важливе: в деяких системах той самий URL повертає JSON або HTML залежно від заголовку `Accept: application/json` vs `Accept: text/html`. Ninja свідомо не робить цього — кожен endpoint має свій URL. Це explicit замість implicit: зрозуміліше при відлагодженні.

### Той самий ресурс, два формати

> Нижче — найважливіший приклад розділу. Зверніть, що обидва endpoints (`note_list_json` і `note_list_html`) звертаються до одних і тих самих `Note.objects.all()` — одна бізнес-логіка. Але `note_list_json` повертає `List[NoteOut]` (Pydantic серіалізує у JSON), а `note_list_html` повертає `render(...)` (Django Template Engine формує HTML). Це і є суть гібридної архітектури.

```python
# hello_app/api.py
from ninja import Router, Schema
from typing import List
from datetime import datetime

router = Router()

# Schema — Pydantic модель для JSON серіалізації
class NoteOut(Schema):
    id: int
    title: str
    content: str
    created_at: datetime

class NoteIn(Schema):
    title: str
    content: str = ""


# ─── JSON API endpoint ────────────────────────────────────────────
@router.get("/", response=List[NoteOut])
def note_list_json(request):
    """
    JSON API: повертає структуровані дані.
    Pydantic автоматично серіалізує QuerySet → JSON.
    Swagger доступний на /api/docs/
    """
    return Note.objects.all().order_by('-created_at')
    # Response: [{"id": 1, "title": "...", "content": "...", "created_at": "..."}]
    # Content-Type: application/json


@router.get("/{note_id}/", response=NoteOut)
def note_detail_json(request, note_id: int):
    """Path parameter — автоматична валідація (int, not string)"""
    note = get_object_or_404(Note, pk=note_id)
    return note


@router.post("/", response=NoteOut)
def note_create_json(request, data: NoteIn):
    """
    POST з Pydantic валідацією.
    data.title, data.content — вже валідовані і типізовані.
    """
    note = Note.objects.create(
        title=data.title,
        content=data.content,
    )
    return note  # → автоматично серіалізується через NoteOut


# ─── HTML endpoint ────────────────────────────────────────────────
@router.get("/html/", response=None)
def note_list_html(request):
    """HTML endpoint — повертає повну сторінку для браузера"""
    notes = Note.objects.all().order_by('-created_at')
    return render(request, 'hello_app/note_list.html', {'notes': notes})
```

### Порівняльна таблиця

| | JSON API | HTML (SSR) |
|-|----------|-----------|
| **Content-Type** | `application/json` | `text/html` |
| **Хто рендерить UI** | JavaScript (React/Vue/HTMX) | Django Template Engine |
| **Навігація** | AJAX (без перезавантаження) | Повне перезавантаження сторінки |
| **SEO** | Погано (JS не виконується краулерами) | Відмінно (готовий HTML) |
| **First Contentful Paint** | Повільніший (JS потрібен) | Швидший |
| **Інтерактивність** | Висока (SPA) | Обмежена (без JS) |
| **Кешування** | CDN легко кешує JSON | CDN кешує HTML |
| **Для мобільних** | Економить трафік | Більший payload |

---

---
- **🧠 Ментальна модель:** HTMX — це "телепортація HTML фрагментів". Замість того, щоб JavaScript запитував дані (JSON) і будував DOM вручну, HTMX просить сервер "дай мені готовий HTML шматок" і вставляє його на місце. Ви пишете Python + Django шаблони, а інтерактивність додається HTML-атрибутами, без жодного JS-коду.
- **📚 Чому це існує:** Традиційний підхід до інтерактивності вимагає: вивчити JavaScript, вивчити React/Vue, налаштувати збірку (webpack/vite), підтримувати синхронізацію стану між фронтендом і бекендом. HTMX пропонує альтернативу: якщо ваш сервер вже рендерить HTML (Django templates), нехай він рендерить і фрагменти для динамічних оновлень. Значно менше складності.
- **🌐 Що відбувається під капотом:** HTMX — це 14KB JavaScript-бібліотека, яка слухає HTML-атрибути (`hx-get`, `hx-post`, `hx-target`, `hx-trigger`) і виконує AJAX-запити від вашого імені. Отримавши HTML у відповідь, вона замінює DOM-вузол, вказаний у `hx-target`.
- **❌ Типова помилка початківця:** Повертати повну HTML-сторінку (з `<!DOCTYPE html>`, `<head>`, `<body>`) у відповідь на HTMX-запит. HTMX очікує тільки фрагмент — частину DOM, яку треба вставити. Повна сторінка у відповідь призведе до "HTML всередині HTML" і зламає вигляд.
---

## 5. Гібридна архітектура — SSR + API + HTMX

> Розберемо ключовий ментальний зсув від традиційного AJAX до HTMX:

```
Традиційний AJAX (без HTMX):
  Крок 1: Користувач вводить текст
  Крок 2: JavaScript слухає подію 'input'
  Крок 3: JS виконує fetch('/api/notes/search/?q=...') 
  Крок 4: Отримує JSON: [{"id":1, "title":"..."}, ...]
  Крок 5: JS будує HTML: '<div class="card">...' + noteData.title + '...'
  Крок 6: JS вставляє: document.getElementById('results').innerHTML = html
  Проблема: JavaScript знає про структуру даних (поля JSON) і структуру UI (як будувати HTML)
            → два місця, де потрібні зміни при оновленні дизайну

HTMX підхід:
  Крок 1: Користувач вводить текст
  Крок 2: hx-trigger="input changed delay:300ms" спрацьовує автоматично
  Крок 3: HTMX виконує GET /api/notes/search/?q=...
  Крок 4: Django Ninja view запускається, рендерить шаблон note_grid.html
  Крок 5: Отримує готовий HTML фрагмент: '<div class="card">...'
  Крок 6: HTMX вставляє в hx-target="#notes-container"
  Перевага: JavaScript (HTMX) нічого не знає про структуру. Весь UI — в Python templates.
```

> Потік живого пошуку — покроково:
```
Користувач вводить "Django" у поле пошуку
       ↓ hx-trigger="input changed delay:300ms" (debounce 300мс — не кожна клавіша)
       ↓ HTMX формує GET /api/notes/search/?q=Django
       ↓ Django Ninja router отримує запит
       ↓ Pydantic валідує: q: str = "" (завжди рядок, навіть якщо пустий)
       ↓ note_search() виконується: Note.objects.filter(title__icontains='Django')
       ↓ render(request, 'components/note_grid.html', {'notes': results})
       ↓ Django Template Engine рендерить ТІЛЬКИ фрагмент (без <html>, <head>)
       ↓ Повертає HTML: '<div class="row">...<h5>Django notes</h5>...</div>'
       ↓ hx-target="#notes-container" → HTMX замінює innerHTML цього div
Користувач бачить оновлені результати БЕЗ перезавантаження сторінки
```

> Чому це важливо для Django-розробників: ваші Python-шаблони вже є "компонентною системою". `{% include 'components/note_card.html' %}` — це і є компонент. Додавши HTMX, ці компоненти стають інтерактивними без написання жодного рядка JavaScript.

### Концепція

```
Повна сторінка (перший запит):
    Browser → /notes/ → Django View → render() → повний HTML

Часткове оновлення (після взаємодії):
    Browser → /api/notes/partial/ → Ninja → render(fragment.html) → HTML фрагмент

JavaScript (HTMX або fetch) підмінює тільки потрібний DOM-вузол:
    document.getElementById('notes-list').innerHTML = fragment
```

### HTMX — мінімальний JavaScript, максимальна інтерактивність

> Зверніть на HTML-атрибути HTMX: `hx-get` (куди відправляти запит), `hx-target` (який DOM-елемент замінити результатом), `hx-swap` (як замінити: `innerHTML`, `outerHTML`, `beforeend` тощо), `hx-trigger` (коли запускати). Атрибут `delay:300ms` в `hx-trigger="input changed delay:300ms"` — це debounce: HTMX чекає 300мс після останньої зміни, перш ніж відправити запит. Без цього кожна клавіша відправляла б запит на сервер.

```html
{# note_list.html — з HTMX #}
{% extends 'hello_app/base.html' %}

{% block extra_css %}
<!-- HTMX — 14KB, без build step -->
<script src="https://unpkg.com/htmx.org@1.9.12"></script>
{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3">Нотатки</h1>
    <button
        class="btn btn-primary"
        hx-get="{% url 'hello_app:note_create_partial' %}"
        hx-target="#modal-container"
        hx-swap="innerHTML"
    >
        + Нова нотатка
    </button>
</div>

{# Пошук — живий пошук без перезавантаження #}
<input
    type="search"
    class="form-control mb-4"
    name="q"
    placeholder="Пошук нотаток..."
    hx-get="/api/notes/search/"
    hx-trigger="input changed delay:300ms"
    hx-target="#notes-container"
    hx-swap="innerHTML"
>

{# Список нотаток — замінюється при пошуку #}
<div id="notes-container">
    {% include 'hello_app/components/note_grid.html' %}
</div>

{# Контейнер для динамічного modal #}
<div id="modal-container"></div>
{% endblock %}
```

### Ninja endpoint для HTMX (повертає HTML фрагмент)

> Зверніть на ключову відмінність: `render(request, 'hello_app/components/note_grid.html', ...)` — тут шаблон є **фрагментом**, не повною сторінкою. У `note_grid.html` немає `{% extends %}`, немає `<html>`, немає `<head>` — тільки `<div>` з картками нотаток. Це те, що HTMX вставить у `#notes-container`.

```python
# hello_app/api.py

@router.get("/search/", response=None)
def note_search(request, q: str = ""):
    """
    HTMX endpoint — повертає тільки HTML фрагмент (не повну сторінку).
    HTMX підмінить innerHTML в #notes-container.
    """
    notes = Note.objects.filter(title__icontains=q).order_by('-created_at')
    return render(
        request,
        'hello_app/components/note_grid.html',  # ← фрагмент, не повна сторінка
        {'notes': notes, 'query': q}
    )


@router.get("/partial/{note_id}/", response=None)
def note_partial(request, note_id: int):
    """Повертає HTML картку нотатки для динамічного оновлення"""
    note = get_object_or_404(Note, pk=note_id)
    return render(
        request,
        'hello_app/components/note_card.html',
        {'note': note}
    )
```

> Шаблон-фрагмент нижче — це "компонент" в Django-стилі. Він нічого не знає про те, де буде вставлений. `hx-trigger="revealed"` на картці означає: "коли ця картка з'явиться у viewport (видима область), виконай GET-запит і онови себе через `hx-swap="outerHTML"`". Це lazy-loading компонентів без JavaScript.

```html
{# hello_app/components/note_grid.html — ФРАГМЕНТ (без <!DOCTYPE>, без <html>) #}
{% if notes %}
<div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    {% for note in notes %}
    <div class="col">
        <div class="card h-100 border-0 shadow-sm"
             id="note-{{ note.pk }}"
             hx-get="/api/notes/partial/{{ note.pk }}/"
             hx-trigger="revealed"
             hx-swap="outerHTML">
            <div class="card-body">
                <h5 class="card-title">
                    {% if query %}
                    {# Підсвічуємо знайдений текст #}
                    {{ note.title }}
                    {% else %}
                    {{ note.title }}
                    {% endif %}
                </h5>
                <p class="card-text text-muted">{{ note.content|truncatewords:20 }}</p>
            </div>
            <div class="card-footer bg-transparent border-0">
                <small class="text-muted">{{ note.created_at|date:"d.m.Y" }}</small>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="text-center py-5 text-muted">
    {% if query %}
    <p>За запитом "{{ query }}" нічого не знайдено.</p>
    {% else %}
    <p>Нотаток ще немає.</p>
    {% endif %}
</div>
{% endif %}
```

---

---
- **🧠 Ментальна модель:** DTL (Django Template Language) — це "безпечні ножиці" (обмежені, але не можна порізатись). Jinja2 — це "швейцарський ніж" (потужний, але потребує обережності). DTL навмисно забороняє виклики функцій з аргументами, щоб розробники не писали бізнес-логіку в шаблонах. Jinja2 цю межу не встановлює.
- **📚 Чому це існує:** Django розроблявся з ідеєю "logic-less templates" — шаблони мають відображати дані, не обробляти їх. DTL реалізує цю ідею через обмеження. Jinja2 прийшов з іншої філософії (Flask) — повна потужність Python у шаблонах. Django підтримує обидва backends з Django 1.8.
- **🌐 Що відбувається під капотом:** Django перевіряє розширення файлу і директорію шаблону, щоб вирішити, який backend використовувати. `.html` → DTL (з `templates/`), `.html.j2` → Jinja2 (з `jinja2/`). Можна мати обидва в одному проекті без конфліктів.
- **❌ Типова помилка початківця:** Намагатися використовувати Jinja2 для django-admin шаблонів. Admin вимагає DTL — він використовує специфічні DTL template tags (`{% admin_list_filter %}` тощо), які не існують в Jinja2. Jinja2 використовуйте тільки для своїх templates, не для адмінки.
---

## 6. Jinja2 — альтернативний шаблонізатор

> Перш ніж обирати між DTL і Jinja2, запитайте себе: "Чи вимагає мій шаблон складної логіки?" Якщо відповідь "так" — це сигнал, що логіка знаходиться не в тому місці. Правильне рішення — перенести логіку у View, а не перейти на Jinja2. Якщо ж вам дійсно потрібні макроси, groupby-фільтри, або продуктивність має критичне значення — тоді Jinja2 виправданий.

> Коли обирати **Jinja2**:
> - Складна логіка шаблонів (макроси, loops з Python-функціями, `{{ items|groupby('category') }}`)
> - Критична продуктивність (Jinja2 компілює у Python bytecode — швидший рендеринг складних шаблонів)
> - Команда вже знайома з Jinja2 (Flask, FastAPI background)
>
> Коли залишатися на **DTL**:
> - django-admin (ЗАВЖДИ DTL — ніколи не використовуйте Jinja2 для admin templates)
> - Прості застосунки, де обмеження DTL не заважають
> - Коли важливі гарантії "без бізнес-логіки в шаблонах"
> - Коли ви хочете максимальну сумісність з django сторонніми пакетами (більшість пишуть DTL templates)

### DTL vs Jinja2 — порівняння

| | Django Template Language (DTL) | Jinja2 |
|-|-------------------------------|--------|
| **Синтаксис** | `{% for %}`, `{{ var\|filter }}` | `{% for %}`, `{{ var\|filter }}` (схожий) |
| **Виклики функцій** | Заборонені з аргументами | Дозволені: `{{ my_func(arg) }}` |
| **Продуктивність** | Стандартна | Вища (компілює у Python bytecode) |
| **Autoescape** | Так (за замовчуванням) | Так (треба увімкнути) |
| **Тести** | `{% if val %}` | `{% if val is defined %}` |
| **Макроси** | `{% include %}` | `{% macro %}` (потужніший) |
| **Фільтри** | Вбудовані + custom | Вбудовані + custom |
| **Коли обирати** | Стандарт Django, команда знає DTL | Висока продуктивність, складні шаблони |

### Як Django вирішує який backend використовувати

Перш ніж дивитись на конфігурацію — зрозумій алгоритм вибору backend:

```
render(request, 'hello_app/note_list.html', context)
         ↓
Django перебирає TEMPLATES список (порядок важливий!):
         ↓
Backend 1 (DjangoTemplates):
  Шукає 'hello_app/note_list.html' у templates/ директоріях
  → Знайшов? → Рендерить DTL → СТОП
  → Не знайшов? → Переходить до Backend 2

Backend 2 (Jinja2):
  Шукає 'hello_app/note_list.html' у jinja2/ директоріях
  → Знайшов? → Рендерить Jinja2 → СТОП
  → Не знайшов? → TemplateDoesNotExist помилка
```

**Конвенція .html.j2 vs .html:** Технічно ти можеш назвати Jinja2 шаблон `.html` — якщо він у `jinja2/` директорії, Django знайде його правильним backend. Але `.html.j2` розширення допомагає: редактори (PyCharm, VS Code) розуміють що це Jinja2 і вмикають правильне підсвічування синтаксису.

### Підключення Jinja2 у Django

> Зверніть на конфігурацію нижче: в `TEMPLATES` — **два** backends одночасно. Перший (DTL) обслуговує `templates/` директорії. Другий (Jinja2) обслуговує `jinja2/` директорії. `environment` вказує на вашу функцію ініціалізації Jinja2 Environment, де ви підключаєте `static()` і `url()` — без цього Jinja2 не знав би про Django-специфічні функції.

```bash
pip install jinja2
```

```python
# settings.py
TEMPLATES = [
    {
        # 1. Стандартний Django Template Language (залишаємо)
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # шукає в app/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    {
        # 2. Jinja2 (додатковий backend)
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [BASE_DIR / 'jinja2'],  # шукає в /jinja2/ папці
        'APP_DIRS': True,               # шукає в app/jinja2/
        'OPTIONS': {
            'environment': 'hello_app.jinja2_env.environment',
        },
    },
]
```

> Файл `jinja2_env.py` — це "міст" між Django і Jinja2. Django знає про `staticfiles` і `reverse()` (url-резолвер). Jinja2 — ні. Тут ви явно реєструєте ці функції в Jinja2 `globals`, щоб шаблони могли використовувати `{{ static('path') }}` і `{{ url('name') }}` так само, як і в DTL.

```python
# hello_app/jinja2_env.py
from jinja2 import Environment
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse

def environment(**options):
    env = Environment(**options)

    # Додаємо Django функції в Jinja2
    env.globals.update({
        'static': staticfiles_storage.url,   # {% static('path') %} → url
        'url': reverse,                        # {% url('name') %} → url
    })

    # Autoescape для HTML (захист від XSS)
    env.autoescape = True

    return env
```

### Структура файлів Jinja2

> Ця структура директорій критично важлива. Django визначає, який backend використовувати, виходячи з ТОГО, де знаходиться файл. Файл у `templates/` → DTL. Файл у `jinja2/` → Jinja2. Розширення `.html.j2` — це конвенція (не обов'язкова), яка допомагає редакторам коду правильно підсвічувати синтаксис.

```
hello_app/
├── templates/           ← DTL шаблони (*.html)
│   └── hello_app/
│       ├── base.html
│       └── note_list.html
└── jinja2/              ← Jinja2 шаблони (окрема папка!)
    └── hello_app/
        ├── base.html.j2
        └── note_list.html.j2
```

> **Jinja2 синтаксис, макроси, `Environment`, bytecode cache і streaming** розібрані детально
> в [ADVANCED_TEMPLATES.md §6](ADVANCED_TEMPLATES.md) — Jinja2 Deep Dive.

### Ninja + Jinja2 endpoint

> Зверніть: `render()` один і той самий. Django сам вирішує, який backend використовувати, виходячи з імені файлу і конфігурації. Ваш Ninja endpoint не знає і не повинен знати, DTL це чи Jinja2 — це деталь конфігурації, прихована від бізнес-логіки.

```python
# hello_app/api.py

@router.get("/jinja/", response=None)
def note_list_jinja(request):
    """
    Django автоматично вибирає правильний backend:
    - template.html     → DTL (django.template.backends.django)
    - template.html.j2  → Jinja2 (django.template.backends.jinja2)
    """
    notes = Note.objects.all()
    # render() шукає шаблон у всіх налаштованих backends
    return render(request, 'hello_app/note_list.html.j2', {'notes': notes})
```

---

---
- **🧠 Ментальна модель:** Middleware з `TemplateResponse` — це конвеєр трансформерів. Кожен middleware — це робоча станція на конвеєрі, яка може додати щось до "напівфабрикату" (незрендерованого TemplateResponse) перед тим, як він стане готовим продуктом (HTML рядком).
- **📚 Чому це існує:** Context processors в Django (той механізм, що автоматично додає `user`, `messages`, `MEDIA_URL` в кожен шаблон) реалізований через цей самий принцип відкладеного рендерингу. Без `TemplateResponse` довелося б вручну додавати ці дані в кожен виклик `render()`.
- **🌐 Що відбувається під капотом:** Патерн "відкладений рендеринг" є фундаментом для: context processors (додають у context перед render), template caching (кешують скомпільований HTML, не TemplateResponse), A/B testing (модифікують context залежно від сегменту користувача перед рендерингом), analytics injection (middleware додає tracking дані в кожну сторінку).
- **❌ Типова помилка початківця:** Викликати `response.render()` вручну у view або намагатися змінити `response.context_data` ПІСЛЯ того, як `response.render()` вже викликано. Після рендерингу `response.is_rendered = True` і зміни в context вже не впливають на HTML.
---

## 7. TemplateResponse — відкладений рендеринг

> Розглянемо реальний use case: middleware, що додає глобальні дані в КОЖНУ сторінку без зміни жодного view. Це класичний приклад Cross-Cutting Concern — логіки, що стосується всіх сторінок, і яку неправильно дублювати в кожному view. Middleware + TemplateResponse = елегантне рішення.

> Зверніть на перевірку `if hasattr(response, 'context_data')`. Це важливо: не кожна відповідь є `TemplateResponse`. JSON API endpoints, redirect-и, статичні файли — вони повертають звичайні `HttpResponse` без `context_data`. Перевірка `hasattr` захищає від AttributeError.

### Коли TemplateResponse критично важливий

```python
# Сценарій: middleware що додає глобальний context

# hello_project/middleware.py
class GlobalContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # TemplateResponse ЩЕ НЕ скомпільований → можна змінити context!
        if hasattr(response, 'context_data'):
            response.context_data['site_name'] = 'MySite'
            response.context_data['nav_items'] = get_nav_items()
            # Тепер шаблон має доступ до {{ site_name }} і {{ nav_items }}

        return response

# З HttpResponse це НЕМОЖЛИВО — HTML вже скомпільований у view
```

> Post-render callbacks — це ще одна потужна особливість `TemplateResponse`. Callback виконується ПІСЛЯ того, як шаблон скомпільований у HTML рядок. Це ідеальне місце для кешування готового HTML, логування розміру відповіді, або стиснення HTML. Зверніть: `response.content` у callback — вже `bytes`, не рядок.

```python
# views.py
from django.template.response import TemplateResponse

def note_list(request):
    notes = Note.objects.all()
    context = {'notes': notes}

    # TemplateResponse — middleware може додати в context_data
    response = TemplateResponse(request, 'hello_app/note_list.html', context)

    # Можна додавати callbacks що виконуються після render()
    def post_render_callback(response):
        # response.content — вже скомпільований HTML string
        # Зручно для кешування або логування
        cache.set(f'page_{request.path}', response.content, timeout=300)

    response.add_post_render_callback(post_render_callback)

    return response
```

### `render()` vs `TemplateResponse` — підсумок

> Практичне правило: починайте з `render()`. Переходьте на `TemplateResponse` тільки якщо вам потрібна одна з двох речей: (1) middleware повинен модифікувати context, або (2) вам потрібні post-render callbacks. Для 90% views `render()` — правильний вибір.

```python
# render() — найпростіший, для більшості випадків
return render(request, 'template.html', context)
# ✓ Простий код   ✓ Негайна компіляція   ✗ Middleware не може змінити context

# TemplateResponse — для складних middleware pipelines
return TemplateResponse(request, 'template.html', context)
# ✓ Middleware може змінювати context   ✓ Post-render callbacks   ✗ Складніший код
```

---

---
- **🧠 Ментальна модель:** Production налаштування — це різниця між "їздити на тест-драйві" (development) і "їздити на гоночному треку" (production). В development зручність важливіша за швидкість (бачимо зміни одразу). В production швидкість критична (тисячі запитів на секунду).
- **📚 Чому це існує:** Django за замовчуванням налаштований для зручності розробки: `DEBUG=True`, шаблони читаються з диску при кожному запиті, Swagger відкритий для всіх. Для production кожне з цих налаштувань небезпечне або неефективне.
- **🌐 Що відбувається під капотом:** `cached.Loader` зберігає скомпільований "Node tree" шаблону в словнику в пам'яті процесу. Ключ — ім'я файлу шаблону. При запиті Django перевіряє словник спочатку і тільки за відсутності читає файл з диску. У production сервер зазвичай не перезапускається між запитами, тому кеш живе весь час роботи сервера.
- **❌ Типова помилка початківця:** Увімкнути `cached.Loader` в development. Тоді зміни в шаблонах не будуть видні без перезапуску сервера — дуже незручно при розробці. `cached.Loader` — ТІЛЬКИ для production.
---

## 8. Production Patterns

> Дві найважливіші production оптимізації: **cached.Loader** (для HTML) і **select_related** (для SQL). Перша усуває повторне читання файлів з диску. Друга усуває проблему N+1 запитів. Без них навіть простий список нотаток може генерувати сотні SQL-запитів і сотні читань з диску при кожному HTTP-запиті.

> Проблема N+1 в API контексті — це особливо небезпечно, тому що Ninja endpoint виглядає "чистим":
> ```
> Ninja endpoint повертає 100 нотаток з іменами авторів:
> Без оптимізації:
>   1 SQL: SELECT * FROM notes (100 рядків)
>   100 SQL: SELECT * FROM users WHERE id=X (для кожної нотатки)
>   = 101 SQL-запит для ОДНОГО API-відклику!
> З select_related:
>   1 SQL: SELECT notes.*, users.* FROM notes JOIN users ON notes.user_id = users.id
>   = 1 SQL-запит!
> ```
> Це не помилка Python — це правильна поведінка Django ORM. QuerySet ледачий: `note.user` виконує окремий SQL при першому зверненні. `select_related` говорить ORM зробити JOIN заздалегідь.

### 1. Cached Template Loader — найважливіша оптимізація

> Ця конфігурація — найчастіша різниця між "повільний сайт" і "швидкий сайт" для Django в production. Зверніть: `APP_DIRS=False` при використанні `loaders` вручну — ці дві опції несумісні. При `APP_DIRS=True` Django вже додає `app_directories.Loader`, і дублювання в `loaders` викличе помилку.

```python
# settings.py — DEVELOPMENT
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,   # читає шаблон з диску при КОЖНОМУ запиті
    ...
}]

# settings.py — PRODUCTION
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': False,  # вимикаємо APP_DIRS якщо використовуємо loaders вручну
    'OPTIONS': {
        'loaders': [
            # cached.Loader кешує компільований Node tree в пам'яті
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
        'context_processors': [...],
    },
}]
```

**Що відбувається з cached.Loader:**

```
Без кешу (development):
  Запит 1: диск → читання → парсинг → Node tree → рендеринг  (повільно)
  Запит 2: диск → читання → парсинг → Node tree → рендеринг  (повільно)
  Запит N: диск → читання → парсинг → Node tree → рендеринг  (повільно)

З cached.Loader (production):
  Запит 1: диск → читання → парсинг → Node tree → кеш RAM → рендеринг
  Запит 2: кеш RAM → рендеринг  (швидко, без диску і парсингу!)
  Запит N: кеш RAM → рендеринг  (швидко)
```

### 2. Налаштування Production середовища

> `docs_url=None if not settings.DEBUG else '/docs/'` — це захист від небезпечного відкритого Swagger. У production Swagger UI — це детальна карта всіх ваших API endpoints з прикладами запитів і відповідей. Зловмисник може використати її для розуміння структури API і пошуку вразливостей. Вимикайте в production або захищайте через nginx IP-restriction чи Django `login_required`.

```python
# settings/production.py
import os

DEBUG = False

# Cached template loader
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Django Ninja — вимкнути Swagger у production (опціонально)
NINJA_PAGINATION_PER_PAGE = 20
```

```python
# hello_project/urls.py — production config
from ninja import NinjaAPI

api = NinjaAPI(
    title="Notes API",
    docs_url=None if not settings.DEBUG else '/docs/',   # ← вимкнути Swagger
)
```

### 3. Query Optimization — виконувати в View, не в шаблоні

> N+1 проблема — найпоширеніша проблема продуктивності в Django-проектах. Вона невидима при розробці (3-5 нотаток у тестовій базі → 4-6 запитів, непомітно). Але в production (1000 нотаток → 1001 SQL-запит на один HTTP-запит!) вона вбиває сервер. Завжди `select_related` для ForeignKey, `prefetch_related` для ManyToMany, `annotate` для агрегацій.

```python
# ❌ ПОГАНО: N+1 через lazy QuerySet у шаблоні
def note_list(request):
    notes = Note.objects.all()   # QuerySet ще не виконано
    return render(request, 'note_list.html', {'notes': notes})
# Шаблон: {% for note in notes %} → {{ note.user.username }} ← N+1!

# ✅ ДОБРЕ: select_related перед передачею в шаблон
def note_list(request):
    notes = Note.objects.select_related('user').order_by('-created_at')
    return render(request, 'note_list.html', {'notes': notes})
# Один SQL JOIN замість N окремих запитів

# ✅ ДОБРЕ: prefetch_related для ManyToMany
def note_list(request):
    notes = (
        Note.objects
        .select_related('user')
        .prefetch_related('tags')
        .annotate(comment_count=Count('comments'))
        .order_by('-created_at')
    )
    return render(request, 'note_list.html', {'notes': notes})
```

### 4. Ninja API — кешування JSON відповідей

> Кешування API відповідей критичне для read-heavy endpoints (список нотаток читається набагато частіше, ніж оновлюється). `cache_key` включає `request.user.id` — різні користувачі бачать різні нотатки, тому їхні кеші повинні бути ізольовані. `timeout=60` — 60 секунд актуальності. При оновленні нотатки потрібно також очистити кеш: `cache.delete(cache_key)`.

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from ninja import Router

router = Router()

# Кешування через Django cache framework
@router.get("/", response=List[NoteOut])
def note_list_cached(request):
    from django.core.cache import cache

    cache_key = f'notes_list_user_{request.user.id}'
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    notes = list(Note.objects.all().values('id', 'title', 'content', 'created_at'))
    cache.set(cache_key, notes, timeout=60)  # 60 секунд
    return notes
```

---

---
- **🧠 Ментальна модель:** Pydantic Schema — це "контракт для даних". Як Django Form перевіряє HTML-форми, Pydantic Schema перевіряє JSON. Але Pydantic робить це автоматично, через type hints, без написання `clean_` методів.
- **📚 Чому це існує:** "Mass assignment vulnerability" — класична атака: якщо API приймає JSON і напряму оновлює поля моделі (`Note.objects.create(**data)`), зловмисник може передати `{"is_admin": true}` і стати адміністратором. Input Schema вирішує це: ви явно вказуєте, які поля ДОЗВОЛЕНО отримувати від користувача. Output Schema вирішує проблему "витоку даних": ви явно вказуєте, які поля ДОЗВОЛЕНО відправляти.
- **🌐 Що відбувається під капотом:** Ninja отримує JSON body запиту, передає його в Pydantic `NoteCreateSchema(**json_data)`. Pydantic перевіряє типи, викликає validators, і або повертає валідний об'єкт, або кидає `ValidationError`. Ninja перехоплює `ValidationError` і повертає `422 Unprocessable Entity` з деталями помилок. Ваша функція навіть не запускається при помилці валідації.
- **❌ Типова помилка початківця:** Використовувати `ModelSchema` з `fields = '__all__'` для вхідних даних. Це автоматично додає ВСІ поля моделі у Input Schema — включаючи `is_staff`, `is_superuser`, `password_hash`. Завжди явно вказуйте поля або використовуйте окремі `CreateSchema` і `OutSchema`.
---

## 9. Ninja Schemas — валідація та серіалізація

> Патерн "окремі схеми для input і output" — це не просто стиль коду, це архітектурна безпека. `NoteCreateSchema` визначає "що користувач може НАДІСЛАТИ" (мінімум полів, без системних). `NoteOutSchema` визначає "що API ПОКАЗУЄ назовні" (може включати обчислювані поля, але не секрети як хеші паролів). Розділення цих двох концепцій захищає від цілого класу вразливостей.

> Чому `ModelSchema` не завжди краще за звичайну `Schema`: `ModelSchema` генерує схему автоматично з Django model. Зручно — але небезпечно для Input schemas. Якщо модель має поле `is_admin: bool = False`, `ModelSchema` дозволить користувачу надіслати `{"is_admin": true}` у запиті. Явна `Schema` з тільки потрібними полями — безпечніша за зручну `ModelSchema`.

### Pydantic Schemas для вхідних і вихідних даних

> Зверніть на `@validator('title')` — це Pydantic v1 синтаксис (Pydantic v2 використовує `@field_validator`). У Django Ninja 1.x підтримуються обидва. Validator автоматично викликається при валідації і або повертає очищене значення, або кидає `ValueError` з людськозрозумілим повідомленням. Це повідомлення потрапить у `422` відповідь автоматично.

```python
# hello_app/schemas.py
from ninja import Schema, ModelSchema
from typing import Optional, List
from datetime import datetime
from .models import Note


# Input schema — валідація вхідних даних
class NoteCreateSchema(Schema):
    title: str
    content: str = ""

    @validator('title')
    def title_min_length(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Мінімум 3 символи')
        return v.strip()


class NoteUpdateSchema(Schema):
    title: Optional[str] = None
    content: Optional[str] = None


# Output schema — серіалізація вихідних даних
class NoteOutSchema(Schema):
    id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2: читати з ORM об'єктів


# ModelSchema — автоматично з Django Model
class NoteModelSchema(ModelSchema):
    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'created_at']
        # або: fields = '__all__'
        # або: exclude = ['user']
```

### Архітектурна схема CRUD Router

Перш ніж читати код — зрозумій загальну картину. Один `Router` об'єкт обробляє всі п'ять HTTP операцій для одного ресурсу. Це REST-архітектура в чистому вигляді:

```
HTTP Method + URL Pattern → Дія           → SQL
─────────────────────────────────────────────────────
GET    /api/notes/          → список       → SELECT *
GET    /api/notes/{id}/     → деталі       → SELECT WHERE id=X
POST   /api/notes/          → створити     → INSERT
PUT    /api/notes/{id}/     → оновити      → UPDATE WHERE id=X
DELETE /api/notes/{id}/     → видалити     → DELETE WHERE id=X
```

Кожен endpoint у Ninja — це звичайна Python-функція з декоратором. Pydantic Schema (`NoteOutSchema`) вказує що повернути, `NoteCreateSchema` — що прийняти. Ninja сам виконує: десеріалізацію JSON → валідацію Pydantic → передачу в функцію → серіалізацію відповіді.

**Зверни увагу на `data.dict(exclude_unset=True)` в `note_update`** — це ключ до "часткового оновлення" (PATCH-like behavior). Якщо клієнт надіслав тільки `{"title": "Новий заголовок"}` — оновлюється тільки `title`, `content` не чіпається. Без `exclude_unset=True` — Pydantic підставив би default значення `content=None` і перезатер існуючий content.

### Повний CRUD Router

> Цей CRUD router демонструє всі основні HTTP методи. Зверніть на `data.dict(exclude_unset=True)` у `note_update` — це ключова деталь для PATCH-like поведінки: `exclude_unset=True` включає тільки поля, які РЕАЛЬНО надіслав клієнт, не всі поля схеми з default значеннями. Це дозволяє оновити тільки `title`, не чіпаючи `content`.

```python
# hello_app/api.py
from ninja import Router
from django.shortcuts import get_object_or_404
from typing import List
from .models import Note
from .schemas import NoteCreateSchema, NoteUpdateSchema, NoteOutSchema

router = Router(tags=["Notes"])

@router.get("/", response=List[NoteOutSchema], summary="Список нотаток")
def note_list(request):
    return Note.objects.all().order_by('-created_at')


@router.get("/{note_id}/", response=NoteOutSchema, summary="Деталі нотатки")
def note_detail(request, note_id: int):
    return get_object_or_404(Note, pk=note_id)


@router.post("/", response=NoteOutSchema, summary="Створити нотатку")
def note_create(request, data: NoteCreateSchema):
    note = Note.objects.create(**data.dict())
    return note


@router.put("/{note_id}/", response=NoteOutSchema, summary="Оновити нотатку")
def note_update(request, note_id: int, data: NoteUpdateSchema):
    note = get_object_or_404(Note, pk=note_id)
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(note, attr, value)
    note.save()
    return note


@router.delete("/{note_id}/", summary="Видалити нотатку")
def note_delete(request, note_id: int):
    note = get_object_or_404(Note, pk=note_id)
    note.delete()
    return {"success": True}


# HTML endpoint для браузера
@router.get("/html/", response=None, include_in_schema=False)
def note_list_html(request):
    from django.shortcuts import render
    notes = Note.objects.all().order_by('-created_at')
    return render(request, 'hello_app/note_list.html', {'notes': notes})
```

---

---
- **🧠 Ментальна модель:** Swagger UI — це безкоштовний "Postman", що генерується автоматично прямо з вашого коду. Ви написали Pydantic schemas і Ninja endpoints — Swagger вже знає, які поля приймає кожен endpoint, які відповіді повертає, і може протестувати їх у браузері.
- **📚 Чому це існує:** OpenAPI (раніше Swagger) — це стандарт опису REST API. Ninja генерує `openapi.json` специфікацію автоматично з type hints і schemas. Swagger UI читає цю специфікацію і рендерить інтерактивний інтерфейс. Сторонні інструменти (Postman, код-генератори для mobile SDK, API gateway) також можуть читати цю специфікацію.
- **🌐 Що відбувається під капотом:** При старті Django, Ninja інтроспектує всі зареєстровані endpoints і schemas. Збирає `openapi.json` специфікацію в пам'яті. При запиті `/api/docs/` — повертає Swagger UI HTML з embedded посиланням на `/api/openapi.json`. Swagger UI (JavaScript) завантажує spec і рендерить інтерактивні форми.
- **❌ Типова помилка початківця:** Залишати Swagger відкритим у production. Swagger UI показує назви всіх endpoints, типи параметрів, приклади запитів — це детальна карта API для зловмисника. Додатково: Swagger дозволяє виконувати реальні запити до API прямо з браузера — без будь-якої авторизації.
---

## 10. Swagger UI — автоматична документація

> Два URL, які Ninja генерує автоматично, вирішують різні проблеми: `/api/docs/` — для розробників (інтерактивний тест), `/api/openapi.json` — для інструментів (Postman, мобільні SDK генератори, API Gateway). Жоден рядок конфігурації не потрібен — тільки type hints і Pydantic schemas.

> Захист Swagger у production — не опціональна рекомендація, а вимога безпеки. Варіанти захисту:
> 1. `docs_url=None` — повністю вимкнути
> 2. Nginx `allow 192.168.1.0/24; deny all;` перед `/api/docs/` — тільки для офісної мережі
> 3. Django `@login_required` декоратор на docs URL — тільки для авторизованих
> 4. Custom `auth` в NinjaAPI — документація тільки після API-авторизації

**Як читати автоматичну документацію:** Ninja збирає інформацію про кожен endpoint з трьох джерел: (1) HTTP метод і шлях (`@router.get("/{note_id}/")`), (2) Pydantic schemas (`response=NoteOutSchema`, `data: NoteCreateSchema`), (3) Python docstring і `summary=` параметр. З цього генерується OpenAPI специфікація — стандартний JSON-формат опису API.

```
Як Swagger UI з'являється автоматично:
  Твій код: @router.get("/", response=List[NoteOutSchema])
       ↓
  Ninja: інтроспекція → OpenAPI spec JSON
       ↓
  GET /api/openapi.json → {"paths": {"/api/notes/": {"get": {...}}}}
       ↓
  GET /api/docs/ → Swagger UI HTML з embedded посиланням на openapi.json
       ↓
  Браузер: Swagger UI (JavaScript) завантажує spec → рендерить форми
```

Django Ninja автоматично генерує Swagger UI:

```
http://localhost:8000/api/docs/
→ Інтерактивна документація
→ Можна тестувати endpoints прямо з браузера
→ Автоматично з NoteOutSchema, NoteCreateSchema

http://localhost:8000/api/openapi.json
→ OpenAPI JSON специфікація (для Postman, код-генераторів)
```

> `description` підтримує Markdown — заголовки `##`, списки `- item`, жирний текст `**bold**`. Використовуйте це для структурованої документації прямо в коді. Версіонування `version="2.0.0"` відображається в Swagger UI і дозволяє клієнтам знати, з якою версією API вони працюють.

```python
# Кастомізація Swagger
api = NinjaAPI(
    title="Notes API",
    version="2.0.0",
    description="""
    ## Система нотаток

    API для управління нотатками.

    ### Автентифікація
    Використовується Bearer Token.
    """,
    docs_url="/docs/",
)
```

---

---
- **🧠 Ментальна модель:** Це порівняння показує еволюцію одного і того ж функціоналу. Обидва підходи правильні — вони оптимізовані для різних контекстів. Як молоток і викрутка: обидва інструменти, кожен для свого завдання.
- **📚 Чому це існує:** Django Class-Based Views (ListView, DetailView) — це "батарейки в комплекті". Вони реалізують 80% типових patterns (pagination, queryset, context) за вас. Ninja endpoints — це "чистий аркуш" з явним контролем. CBV менше коду для типових випадків. Ninja endpoint — більше гнучкості і контролю.
- **🌐 Що відбувається під капотом:** Django CBV `ListView` за кульісами робить те саме, що ваш Ninja endpoint вручну: `paginator = Paginator(queryset, paginate_by)`, `page_obj = paginator.get_page(page)`, `context = {'object_list': page_obj, ...}`, `return TemplateResponse(request, template_name, context)`. Ninja endpoint робить це явно — ви бачите кожен крок.
- **❌ Типова помилка початківця:** Думати, що Ninja endpoints "заміняють" Django views або що CBV "застарілі". Вибір залежить від завдання: CBV відмінні для CRUD з HTML, Ninja відмінний для JSON API і гібридних HTML+JSON endpoints.
---

## 11. Порівняння: Django View vs Ninja Endpoint для HTML

> Обидва підходи нижче роблять те саме: пагінований список нотаток. Але вони оптимізовані для різних сценаріїв. CBV `ListView` — менше коду, більше "магії" (Django робить pagination за вас). Ninja endpoint — більше коду, але повний контроль і можливість мати поряд JSON endpoint з тією ж логікою. Читаючи код нижче — зверніть, що Ninja endpoint явно показує кожен крок, тоді як CBV приховує їх.

```python
# ── DJANGO VIEW (традиційний) ──────────────────────────────────────
# hello_app/views.py
from django.views.generic import ListView

class NoteListView(ListView):
    model = Note
    template_name = 'hello_app/note_list.html'
    context_object_name = 'notes'
    ordering = ['-created_at']
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мої нотатки'
        return context


# hello_app/urls.py
urlpatterns = [
    path('notes/', NoteListView.as_view(), name='note_list'),
]


# ── NINJA ENDPOINT (API-стиль) ─────────────────────────────────────
# hello_app/api.py
@router.get("/html/", response=None, include_in_schema=False)
def note_list_html(request, page: int = 1, per_page: int = 12):
    from django.core.paginator import Paginator

    notes_all = Note.objects.all().order_by('-created_at')
    paginator = Paginator(notes_all, per_page)
    page_obj = paginator.get_page(page)

    return render(request, 'hello_app/note_list.html', {
        'notes': page_obj,
        'title': 'Мої нотатки',
        'page_obj': page_obj,
    })

# Перевага Ninja HTML endpoint:
# Той самий router може мати і JSON (/api/notes/) і HTML (/api/notes/html/)
# Єдина точка для бізнес-логіки
```

---

## 12. Анти-патерни

> Анти-патерни нижче — це найпоширеніші помилки, які роблять Django проекти складними для підтримки, повільними, або небезпечними. Кожен з них виглядає "зручно" на перший погляд і стає проблемою при масштабуванні.

```python
# ❌ HTML в Python коді (руйнує MVT)
@router.get("/bad/", response=None)
def bad_view(request):
    return HttpResponse("<h1>Hello</h1><ul>" +
                        "".join(f"<li>{n.title}</li>" for n in Note.objects.all()) +
                        "</ul>")

# ✅ Завжди через шаблон
@router.get("/good/", response=None)
def good_view(request):
    return render(request, 'hello_app/note_list.html', {'notes': Note.objects.all()})


# ❌ Запити в шаблоні (через Template Tag або методи)
# note_list.html: {{ note.user.profile.avatar.url }}
# → 1 запит на profile для кожної нотатки = N+1

# ✅ Оптимізація в View
notes = Note.objects.select_related('user__profile').all()


# ❌ Hardcoded URL в шаблоні
<a href="/notes/{{ note.pk }}/">...</a>

# ✅ Named URL
<a href="{% url 'hello_app:note_detail' pk=note.pk %}">...</a>


# ❌ Static URL hardcode
<img src="/static/hello_app/img/logo.png">

# ✅ {% static %}
{% load static %}
<img src="{% static 'hello_app/img/logo.png' %}">


# ❌ Swagger у production без захисту
api = NinjaAPI(docs_url='/docs/')  # Відкритий для всіх

# ✅ Swagger тільки в DEBUG або за паролем
api = NinjaAPI(docs_url='/docs/' if settings.DEBUG else None)
```

---

## 13. Питання для самоперевірки

1. Яка ключова різниця між `render()` і `TemplateResponse()`? Коли використовувати кожен?
2. Django Ninja endpoint повертає `Note.objects.all()`. Що автоматично відбувається з цим QuerySet?
3. Чому `cached.Loader` критичний для production і непотрібний для development?
4. Jinja2 дозволяє `{{ my_list.append('item') }}` у шаблоні. DTL — ні. Чому DTL навмисно обмежує це?
5. Ninja endpoint повертає `HttpResponse` з HTML. Swagger `/api/docs/` показуватиме цей endpoint? Як сховати?
6. В чому перевага HTMX підходу перед традиційним SSR для живого пошуку?
7. `TemplateResponse` дозволяє middleware змінити context. Як це пов'язано з post_render_callback?
8. Ninja Schema `NoteOutSchema` має поле `created_at: datetime`. Як воно серіалізується в JSON?
9. Чому для production потрібно вимкнути `APP_DIRS=True` при використанні `cached.Loader`?
10. HTMX-запит повертає HTML фрагмент без `<!DOCTYPE html>`. Чому це правильно і коли це проблема?
