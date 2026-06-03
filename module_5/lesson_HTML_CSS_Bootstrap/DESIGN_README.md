# DESIGN_README — Дизайн Django-застосунку від нуля

> **Цей туторіал** веде тебе від порожнього `<html>` до повноцінного SaaS Dashboard
> з темною темою, sidebar-навігацією та картками нотаток — крок за кроком.
>
> Мова: **CrispyNotes** (`crispy_notes_project`) — реальний проєкт курсу.
> Кожен приклад коду — це **живий рядок** з файлів проєкту.

---

## Зміст

1. [Як підключити Bootstrap до Django](#1--як-підключити-bootstrap-до-django)
2. [Bootstrap 5 Dark Mode](#2--bootstrap-5-dark-mode)
3. [Статичні файли Django](#3--статичні-файли-django)
4. [CSS Custom Properties — дизайн-токени](#4--css-custom-properties--дизайн-токени)
5. [Layout: SaaS Dashboard з Flexbox](#5--layout-saas-dashboard-з-flexbox)
6. [Sidebar: стилі, hover, active state](#6--sidebar-стилі-hover-active-state)
7. [Картки та типографіка](#7--картки-та-типографіка)
8. [Bootstrap vs Custom CSS — що де](#8--bootstrap-vs-custom-css--що-де)
9. [Документація курсу](#9--документація-курсу)

---

## 1 · Як підключити Bootstrap до Django

> **Bootstrap** — бібліотека готових CSS-класів і JavaScript-компонентів.
> Замість писати `button { background: blue; padding: 8px 16px; border-radius: 4px; ... }`
> ти просто пишеш `class="btn btn-primary"` — і стиль вже є.

### Два способи: CDN vs npm

| | CDN (для навчання) | npm/Vite (для production) |
|--|-------------------|--------------------------|
| Встановлення | Копіюєш два рядки у HTML | `npm install bootstrap` + збірка |
| Швидкість старту | Миттєво | ~30 хвилин налаштування |
| Кастомізація | Обмежена (тільки CSS-змінні) | Повна (Sass-змінні) |
| Офлайн-робота | ❌ Потребує інтернет | ✅ |
| Розмір файлу | CDN кешується браузером | Тільки потрібний код (tree-shaking) |

**Для навчальних проєктів — завжди CDN.** Мета вчитися Django, не збірці.

### Що копіювати у `<head>`

```html
<!-- Bootstrap 5 CSS — ОБОВ'ЯЗКОВО у <head> -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
      rel="stylesheet"
      integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
      crossorigin="anonymous">

<!-- Bootstrap Icons — окрема бібліотека іконок (bi-journal-text, bi-trash...) -->
<link rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
```

```html
<!-- Bootstrap JS — ПЕРЕД </body>, не у <head> -->
<!-- Потрібен для: Dropdown, Modal, Collapse, Carousel... -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```

> **Чому JS перед `</body>`, а не в `<head>`?**
> HTML завантажується зверху вниз. JS в `<head>` блокує відображення сторінки —
> користувач бачить білий екран поки JS завантажується. JS перед `</body>` —
> спочатку відображається HTML, потім додається інтерактивність.

### Де це в нашому проєкті

**Файл:** `crispy_notes_project/templates/base.html`

```html
<!DOCTYPE html>
<html lang="uk" data-bs-theme="dark">   <!-- ← dark mode тут -->
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Notes{% endblock %} — CrispyNotes</title>

  <!-- 1. Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        rel="stylesheet" integrity="sha384-..." crossorigin="anonymous">

  <!-- 2. Bootstrap Icons -->
  <link rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

  <!-- 3. Наш кастомний CSS (поверх Bootstrap) -->
  {% load static %}
  <link rel="stylesheet" href="{% static 'hello_app/css/app.css' %}">

  {% block extra_css %}{% endblock %}   <!-- ← слот для CSS конкретних сторінок -->
</head>
<body>
  {% block body %}{% endblock %}

  <!-- Bootstrap JS (перед </body>) -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  {% block extra_js %}{% endblock %}   <!-- ← слот для JS конкретних сторінок -->
</body>
</html>
```

> **Порядок CSS важливий:** Bootstrap CSS → потім наш CSS.
> Наш `app.css` перевизначає Bootstrap-стилі де потрібно.
> Якщо підключити навпаки — Bootstrap перетре наші стилі.

### Bootstrap Icons — як використовувати

```html
<!-- Іконка додається через тег <i> з класом bi-* -->
<i class="bi bi-journal-text"></i>         <!-- нотатки -->
<i class="bi bi-trash me-1"></i>Видалити   <!-- + відступ me-1 праворуч -->
<i class="bi bi-plus-lg fs-5"></i>          <!-- більший розмір fs-5 -->
<i class="bi bi-person-circle text-primary"></i>  <!-- з кольором Bootstrap -->
```

Повний список іконок: **https://icons.getbootstrap.com/** — пошук по назві.

---

## 2 · Bootstrap 5 Dark Mode

> Bootstrap 5.3+ має **вбудовану** темну тему. Не потрібно писати жодного CSS —
> один атрибут на `<html>` вмикає темний режим для ВСІХ Bootstrap-компонентів.

### Увімкнути темну тему

```html
<!-- Замість: -->
<html lang="uk">

<!-- Пишемо: -->
<html lang="uk" data-bs-theme="dark">
```

**Що змінюється автоматично:**

| Компонент | Світла тема | Темна тема |
|-----------|-------------|-----------|
| `<body>` | білий `#fff` | темно-сірий `#212529` |
| `.card` | білий фон | сірий `#2b2d31` |
| `.form-control` | білий input | темний input |
| `.btn-outline-*` | кольорова рамка | та сама рамка + темний фон |
| `.dropdown-menu` | білий | темний |
| `.nav-link` | темний текст | світлий текст |
| `<hr>` | сірий | напівпрозорий білий |

### Перемикач темна/світла (JavaScript)

```html
<!-- Кнопка-перемикач -->
<button id="themeToggle" class="btn btn-sm btn-outline-secondary">
  <i class="bi bi-moon-stars"></i>
</button>

<script>
  document.getElementById('themeToggle').addEventListener('click', () => {
    const html = document.documentElement;
    const current = html.getAttribute('data-bs-theme');
    html.setAttribute('data-bs-theme', current === 'dark' ? 'light' : 'dark');
  });
</script>
```

### Наш проєкт — зафіксована темна тема

У CrispyNotes тема **зафіксована** на dark (`base.html` рядок 2).
Додатково ми перевизначаємо Bootstrap-кольори своєю палітрою через `app.css` (розділ 4).

---

## 3 · Статичні файли Django

> **Статичні файли** — CSS, JavaScript, зображення. Django не "розуміє" їх як шаблони —
> він просто роздає їх браузеру. Але Django треба знати **де їх шукати**.

### Два місця для static файлів

```
crispy_notes_project/
│
├── static/                          ← PROJECT-LEVEL static (STATICFILES_DIRS)
│   └── css/
│       └── project.css              ← глобальні змінні (--sidebar-width: 260px)
│
└── hello_app/
    └── static/
        └── hello_app/               ← APP-LEVEL static (APP_DIRS=True)
            └── css/
                └── app.css          ← головний CSS нашого застосунку ★
```

### settings.py — конфігурація

```python
# settings.py

STATIC_URL = '/static/'

# Project-level static (додатково до app/static/)
STATICFILES_DIRS = [
    BASE_DIR / 'static',   # ← папка crispy_notes_project/static/
]

# При APP_DIRS=True Django автоматично знаходить hello_app/static/
# Не треба додавати кожен app окремо
```

### У шаблоні: `{% load static %}`

```html
{% load static %}   <!-- ← ОБОВ'ЯЗКОВО на початку шаблону (або у base.html) -->

<!-- Підключення CSS -->
<link rel="stylesheet" href="{% static 'hello_app/css/app.css' %}">
<!--                                   ↑ шлях відносно hello_app/static/ -->

<!-- Підключення зображення -->
<img src="{% static 'hello_app/img/logo.png' %}" alt="Logo">
```

### `collectstatic` — для production

```bash
# Збирає всі static файли у STATIC_ROOT для Nginx/Apache
python manage.py collectstatic
```

У development (`DEBUG=True`) Django роздає static файли сам.
У production (`DEBUG=False`) — статику має роздавати Nginx, а не Django.

> **Навіщо два рівні static (project vs app)?**
> App-level static — кожен app відповідає за свої файли. При виносі app у інший проєкт —
> static їде разом. Project-level — для загальних файлів (favicon, шрифти, загальна палітра).

---

## 4 · CSS Custom Properties — дизайн-токени

> **CSS Custom Properties** (або CSS-змінні) — це іменовані значення у CSS,
> які можна перевикористовувати по всьому коду.
>
> **Дизайн-токен** — один "іменований колір" замість десятків hex-кодів по всьому CSS.
> Хочеш змінити колір sidebar? Правиш одну змінну — змінюється всюди.

### Синтаксис

```css
/* Оголошення — у :root{} (глобальний scope) */
:root {
  --accent: #7c6efa;          /* назва починається з -- */
  --text-primary: #e2e8f0;
  --card-bg: #1e1e2e;
}

/* Використання — функція var() */
.card {
  background: var(--card-bg);      /* підставить #1e1e2e */
  color: var(--text-primary);      /* підставить #e2e8f0 */
}

.btn-accent {
  background: var(--accent);       /* #7c6efa */
}

/* Fallback (запасне значення) */
color: var(--text-primary, #ffffff);  /* якщо змінна не оголошена → #ffffff */
```

### Всі токени нашого проєкту

**Файл:** `hello_app/static/hello_app/css/app.css`

```css
:root {
  /* ── SIDEBAR ───────────────────────────────── */
  --sidebar-bg:          #16161e;   /* фон sidebar (найтемніший) */
  --sidebar-hover:       rgba(255,255,255,0.06);  /* hover підсвітка nav-link */
  --sidebar-border:      rgba(255,255,255,0.07);  /* тонкі розділювачі */
  --sidebar-label:       #6060a0;   /* колір НОТАТКИ / ЗАДАЧІ / ТЕГИ заголовків */
  --sidebar-accent:      #7c6efa;   /* акцентний фіолетовий (не використовується напряму) */
  --sidebar-active-bg:   rgba(124,110,250,0.15);  /* фон активного nav-link */

  /* ── LAYOUT ────────────────────────────────── */
  --topbar-bg:           #0f0f18;   /* фон topbar (найтемніший з усіх) */
  --main-bg:             #1a1a27;   /* фон основного контенту */
  --card-bg:             #1e1e2e;   /* фон карток нотаток */

  /* ── BORDERS ───────────────────────────────── */
  --card-border:         rgba(255,255,255,0.08);  /* тонка рамка картки у спокої */
  --card-hover-border:   rgba(124,110,250,0.55);  /* рамка картки при hover */

  /* ── ТЕКСТ ─────────────────────────────────── */
  --text-primary:        #e2e8f0;   /* основний текст (заголовки, контент) */
  --text-secondary:      #9a9ac0;   /* другорядний текст (дата, підказки) */
                                    /* WCAG 4.5:1 на #1e1e2e — доступний контраст */

  /* ── ІНТЕРАКТИВНІСТЬ ───────────────────────── */
  --accent:              #7c6efa;   /* основний акцентний колір (кнопки, посилання) */
  --focus-ring:          0 0 0 3px rgba(124,110,250,0.35);  /* outline при фокусі */
}
```

**Файл:** `static/css/project.css` (project-level)

```css
:root {
  --sidebar-width:  260px;  /* ширина sidebar */
  --topbar-height:  56px;   /* висота topbar */
}
```

### Навіщо ділити на два файли?

`project.css` — структурні значення (розміри, відступи). Рідко змінюються.
`app.css` — кольорові токени. Якщо змінити тему — правиш тільки `app.css`.

### Bootstrap теж використовує CSS-змінні

Bootstrap має свої змінні `--bs-*`:

```css
/* Bootstrap генерує при завантаженні */
:root {
  --bs-primary: #0d6efd;
  --bs-secondary: #6c757d;
  --bs-body-bg: #212529;    /* у dark mode */
  --bs-body-color: #dee2e6;
}
```

Ти можеш **перевизначити** Bootstrap-змінні у своєму CSS:

```css
:root {
  --bs-primary: #7c6efa;   /* тепер btn-primary буде фіолетовим */
}
```

---

## 5 · Layout: SaaS Dashboard з Flexbox

> **SaaS Dashboard** — UI-паттерн: фіксований sidebar зліва + scrollable контент праворуч.
> Notion, Gmail, Linear, Figma — всі побудовані так.

### Структура HTML (3 рівні)

```
base.html                  ← Bootstrap CDN, app.css
└── layouts/dashboard.html ← Sidebar + Topbar
    └── note_list.html      ← Контент сторінки
```

### Повна HTML-структура dashboard

**Файл:** `templates/layouts/dashboard.html`

```html
<!-- Рівень 1: Зовнішня обгортка — весь viewport -->
<div class="d-flex vh-100 overflow-hidden">
  <!--
    d-flex        — display: flex (горизонтальне розміщення sidebar + main)
    vh-100        — height: 100vh (займає весь екран по висоті)
    overflow-hidden — щоб скрол був всередині, а не на body
  -->

  <!-- Рівень 2a: SIDEBAR — фіксована ширина зліва -->
  <nav id="sidebar"
       class="sidebar d-flex flex-column p-3"
       style="width: 260px; min-height: 100vh;">
    <!--
      sidebar       — наш CSS клас (background, border-right)
      d-flex        — flex-контейнер для вертикального стека
      flex-column   — flex-direction: column (дочірні елементи складаються зверху вниз)
      p-3           — padding: 1rem з усіх боків
      width:260px   — фіксована ширина (токен --sidebar-width)
      min-height    — розтягується на всю висоту навіть якщо контент короткий
    -->

    <!-- Бренд, навігація, теги... -->
  </nav>

  <!-- Рівень 2b: MAIN — займає решту ширини -->
  <div class="d-flex flex-column flex-grow-1 overflow-auto">
    <!--
      d-flex        — flex-контейнер для вертикального стека (topbar + content)
      flex-column   — topbar зверху, контент знизу
      flex-grow-1   — займає всю доступну ширину (100% - 260px sidebar)
      overflow-auto — скрол тут, а не на всій сторінці
    -->

    <!-- Рівень 3a: TOPBAR — фіксована висота зверху -->
    <header class="topbar d-flex align-items-center px-4 py-2">
      <!--
        topbar            — наш CSS клас (background, border-bottom)
        d-flex            — горизонтальний flex (заголовок | пошук | юзер)
        align-items-center — вертикальне центрування
        px-4              — горизонтальний padding 1.5rem
        py-2              — вертикальний padding 0.5rem
      -->

      <h6 class="mb-0 me-auto fw-semibold">
        <!--
          me-auto — margin-right: auto → відтискає все інше вправо
          fw-semibold — font-weight: 600
        -->
        {% block topbar_title %}Нотатки{% endblock %}
      </h6>

      <!-- Пошук: me-3 = margin-right 1rem, відступ від юзер-dropdown -->
      <form class="d-flex me-3" method="get">...</form>

      <!-- Юзер dropdown: останній елемент — прилипає до правого краю -->
      <div class="dropdown">...</div>
    </header>

    <!-- Рівень 3b: PAGE CONTENT — скролиться -->
    <main class="flex-grow-1 p-4 overflow-auto">
      {% block content %}{% endblock %}
      <!--
        flex-grow-1   — займає всю висоту (100% - topbar висота)
        p-4           — padding 1.5rem (відступ від країв)
        overflow-auto — скрол якщо контент не влізає
      -->
    </main>

  </div>
</div>
```

### Візуалізація Flexbox

```
┌─ d-flex vh-100 overflow-hidden ──────────────────────────────────┐
│                                                                    │
│  ┌─ sidebar ──────┐  ┌─ flex-grow-1 flex-column ────────────────┐│
│  │  width: 260px  │  │                                           ││
│  │  flex-shrink:0 │  │  ┌─ topbar ──────────────────────────┐   ││
│  │                │  │  │  min-height: 56px                  │   ││
│  │  НОТАТКИ       │  │  │  h6 me-auto | пошук | dropdown     │   ││
│  │  ЗАДАЧІ        │  │  └────────────────────────────────────┘   ││
│  │  ТЕГИ          │  │                                           ││
│  │                │  │  ┌─ main flex-grow-1 overflow-auto ───┐   ││
│  │                │  │  │  p-4                               │   ││
│  │                │  │  │  {% block content %}               │   ││
│  │                │  │  │                                    │   ││
│  └────────────────┘  │  └────────────────────────────────────┘   ││
│                       └───────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
```

### Чому Flexbox, а не Grid?

| Flexbox | CSS Grid |
|---------|---------|
| Одновимірний (рядок АБО колонка) | Двовимірний (рядки І колонки) |
| Sidebar + main → **Flexbox** | Складна сітка карток → **Grid** |
| `d-flex`, `flex-grow-1` | `row`, `col-md-4` |

У Bootstrap `d-flex` = Flexbox, `row/col-*` = Grid.

---

## 6 · Sidebar: стилі, hover, active state

### CSS класи sidebar (з app.css)

```css
/* Фон і рамка sidebar */
.sidebar {
    background: var(--sidebar-bg) !important;  /* #16161e */
    border-right: 1px solid var(--sidebar-border);  /* тонка лінія справа */
    flex-shrink: 0;  /* не стискається при зменшенні вікна */
}
```

### Section labels (НОТАТКИ / ЗАДАЧІ / ТЕГИ)

```css
.sidebar-label {
    font-size: 0.7rem;       /* дрібно — не конкурує з посиланнями */
    font-weight: 700;        /* жирний */
    letter-spacing: 0.08em;  /* розріджені букви — класичний uppercase стиль */
    color: var(--sidebar-label) !important;  /* #6060a0 — приглушений фіолетовий */
}
```

У HTML (dashboard.html):
```html
<p class="sidebar-label text-uppercase fw-semibold mb-1 px-2">Нотатки</p>
<!--
  sidebar-label  — наш CSS клас (font-size, letter-spacing, color)
  text-uppercase — Bootstrap: text-transform: uppercase
  fw-semibold    — Bootstrap: font-weight: 600
  mb-1           — Bootstrap: margin-bottom: 0.25rem
  px-2           — Bootstrap: padding-left/right: 0.5rem
-->
```

### Nav-links: hover та active

```css
/* Стан спокою */
.sidebar .nav-link {
    color: #9898c8 !important;   /* приглушений фіолетово-сірий */
    padding: 0.42rem 1rem;
    border-radius: 5px;
    margin: 1px 6px;
    transition: background 0.12s, color 0.12s;  /* плавний hover */
    font-size: 0.875rem;  /* 14px — трохи менше від основного тексту */
}

/* Hover */
.sidebar .nav-link:hover {
    background: var(--sidebar-hover);  /* rgba(255,255,255,0.06) — ледь помітно */
    color: #d8d8f8;  /* стає світліше */
}

/* Активний (поточна сторінка) */
.sidebar .nav-link.active {
    background: var(--sidebar-active-bg) !important;  /* rgba(124,110,250,0.15) */
    color: var(--accent) !important;  /* #7c6efa — яскравий фіолетовий */
    border-left: 3px solid var(--accent);  /* акцентна смуга зліва ← */
    padding-left: calc(1rem - 3px);  /* компенсуємо 3px border */
}
```

### Active state через Django

```html
<!-- dashboard.html — активний пункт визначається через URL -->
<a href="{% url 'hello_app:note_list' %}"
   class="nav-link {% if request.resolver_match.url_name == 'note_list' %}active{% endif %}">
  <i class="bi bi-journal-text me-2"></i>Всі нотатки
</a>
```

`request.resolver_match.url_name` — Django повертає **ім'я поточного URL**:
- На `/notes/` → `'note_list'` → клас `active` додається
- На `/notes/new/` → `'note_create'` → клас `active` НЕ додається для "Всі нотатки"

Для перевірки по **частині** імені (наприклад, всі todo-сторінки):
```html
class="nav-link {% if 'todo' in request.resolver_match.url_name %}active{% endif %}"
<!-- todo_list, todo_create, todo_detail — всі підсвітяться -->
```

### Bootstrap nav-pills

```html
<ul class="nav nav-pills flex-column mb-3">
<!--
  nav         — Bootstrap: base nav стилі (прибирає bullet points)
  nav-pills   — Bootstrap: таблетки (pill-форма активного пункту)
  flex-column — Bootstrap: вертикальний flex (список зверху вниз)
  mb-3        — Bootstrap: margin-bottom: 1rem (відступ між секціями)
-->
  <li class="nav-item">
    <a href="..." class="nav-link">...</a>
  </li>
</ul>
```

### Separator та розділювачі

```html
<hr>
<!-- .sidebar hr у CSS: -->
/* border-color: var(--sidebar-border); margin: 0.4rem 0; */
```

---

## 7 · Картки та типографіка

### Note Cards — анімація при hover

```css
/* Стан спокою */
.note-card {
    background: var(--card-bg) !important;         /* #1e1e2e */
    border: 1px solid var(--card-border) !important;  /* rgba(255,255,255,0.08) */
    border-radius: 10px;
    /* transition — що анімується і як швидко */
    transition: transform 0.18s ease,
                border-color 0.18s ease,
                box-shadow 0.18s ease;
}

/* При hover */
.note-card:hover {
    transform: translateY(-2px);  /* підіймається на 2px вгору */
    border-color: var(--card-hover-border) !important;  /* фіолетова рамка */
    box-shadow: 0 6px 24px rgba(124,110,250,0.15) !important;  /* тінь */
}
```

> **Чому `translateY(-2px)`?**
> Невелике підняття без зміни розміру — картка "відривається" від поверхні.
> `transform` не впливає на layout (не зсуває сусідні елементи).

### Типографіка — 3 рівні тексту

```css
/* Заголовок сторінки (h5 у note_list.html) */
.page-title {
    font-size: 1.2rem;    /* 19.2px */
    font-weight: 600;
    color: var(--text-primary);  /* #e2e8f0 — яскравий */
}

/* Заголовок картки */
.note-card .card-title a {
    font-size: 0.95rem;      /* 15.2px */
    font-weight: 600;
    letter-spacing: -0.01em; /* трохи ущільнено — виглядає сучасно */
    color: var(--text-primary);
}
.note-card .card-title a:hover {
    color: var(--accent);    /* фіолетовий при hover */
}

/* Превью тексту нотатки */
.note-card .card-text {
    color: var(--text-secondary) !important;  /* #9a9ac0 — приглушений */
    font-size: 0.85rem;   /* 13.6px */
    line-height: 1.55;
}
```

### WCAG — доступний контраст

```
--text-primary  #e2e8f0  на  --card-bg  #1e1e2e  → контраст 11.5:1  ✅ (норма 4.5:1)
--text-secondary #9a9ac0 на  --card-bg  #1e1e2e  → контраст ~4.5:1  ✅ (норма 4.5:1)
```

> **WCAG** — Web Content Accessibility Guidelines. Мінімальний контраст 4.5:1 між текстом
> і фоном. Якщо контраст менший — люди з порушеннями зору не зможуть читати.
> Перевірити: **https://webaim.org/resources/contrastchecker/**

### Bootstrap Badges

```html
<!-- У sidebar (лічильник задач) -->
<span class="badge bg-primary rounded-pill">{{ sidebar_todo_count }}</span>
<!--
  badge         — Bootstrap: base badge стилі (padding, font-size)
  bg-primary    — Bootstrap: синій фон (#0d6efd у light, аналог у dark)
  rounded-pill  — Bootstrap: border-radius: 50rem (таблетка)
-->

<!-- У note_list.html (кількість нотаток) -->
<span class="badge rounded-pill bg-primary bg-opacity-10 text-primary"
      style="font-size: 0.72rem;">{{ notes|length }}</span>
<!--
  bg-opacity-10 — Bootstrap: opacity 10% → дуже прозорий фон
  text-primary  — Bootstrap: синій текст
  Разом: "ghost badge" — тільки колір, без яскравого фону
-->
```

### Crispy Forms — стилізація fieldset

```css
/* app.css — стилізація <fieldset><legend> що генерує crispy */
fieldset legend {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid var(--card-border);  /* тонка лінія під секцією */
    margin-bottom: 1rem;
}
```

Crispy генерує `<fieldset><legend>Основна інформація</legend>` —
наш CSS автоматично стилізує їх у вигляді розділювача секцій.

### Custom Scrollbar

```css
/* Тонкий кастомний scrollbar для Webkit (Chrome, Edge, Safari) */
::-webkit-scrollbar       { width: 6px; }  /* тонша за стандартну */
::-webkit-scrollbar-track { background: transparent; }  /* прозорий трек */
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.12);  /* напівпрозорий */
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.2);  /* стає помітніше */
}
```

Firefox: `scrollbar-width: thin;` (без кастомізації кольору).

### Focus Ring — доступність

```css
/* Замість стандартного синього outline браузера */
:focus-visible {
    outline: none;
    box-shadow: var(--focus-ring);  /* 0 0 0 3px rgba(124,110,250,0.35) */
    border-radius: 4px;
}
```

`:focus-visible` — спрацьовує тільки при навігації клавіатурою (Tab),
не при кліку мишею. Важливо для доступності.

---

## 8 · Bootstrap vs Custom CSS — що де

> Bootstrap — це **фундамент**, наш CSS — **кастомізація**.
> Bootstrap дає структуру та компоненти, ми додаємо бренд і деталі.

### Таблиця розподілу відповідальності

| Що Bootstrap надає | Що пишемо у app.css |
|--------------------|---------------------|
| `d-flex`, `vh-100`, `flex-grow-1` | `.sidebar`, `.topbar`, `.note-card` |
| `data-bs-theme="dark"` (базова темна тема) | CSS-токени (`--sidebar-bg`, `--accent`...) |
| `btn`, `btn-primary`, `btn-sm` | Hover анімації `.note-card:hover` |
| `card`, `card-body`, `card-footer` | Active state `border-left: 3px solid accent` |
| `nav`, `nav-pills`, `nav-link` | `.sidebar-label` (section headers) |
| `badge`, `rounded-pill` | Custom scrollbar `::-webkit-scrollbar` |
| `dropdown`, `dropdown-menu-dark` | `fieldset legend` стилі для crispy |
| `p-4`, `me-3`, `px-2`, `mb-3` | `:focus-visible` ring |
| Bootstrap Icons (`bi-*`) | `--focus-ring`, `--card-hover-border` |
| `form-control`, `form-select` | `transition` анімації |
| `alert`, `alert-dismissible` | Типографіка `.page-title`, `.card-text` |

### Де знаходяться ці класи в проєкті

```
templates/base.html
├── data-bs-theme="dark"         ← Bootstrap dark mode
├── bootstrap.min.css CDN        ← всі Bootstrap класи
├── bootstrap-icons CDN          ← bi-* іконки
└── {% static 'app.css' %}       ← наш custom CSS

hello_app/static/hello_app/css/app.css
├── :root {}                     ← CSS токени (--accent, --card-bg...)
├── body                         ← base font, antialiasing
├── .sidebar                     ← sidebar background
├── .sidebar-label               ← section headers
├── .sidebar .nav-link           ← hover + transition
├── .sidebar .nav-link.active    ← active state + border-left
├── .topbar                      ← topbar background
├── .note-card                   ← card styles + hover animation
└── fieldset legend              ← crispy form sections

static/css/project.css
└── :root {}                     ← --sidebar-width, --topbar-height

templates/layouts/dashboard.html
├── d-flex vh-100 overflow-hidden ← layout wrapper
├── nav.sidebar d-flex flex-column ← sidebar container
├── header.topbar d-flex align-items-center ← topbar
└── main flex-grow-1 p-4         ← content area
```

---

## 9 · Документація курсу

> Повна навчальна база для цього модуля. Читай в порядку зліва направо.

| Файл | Рівень | Що всередині |
|------|--------|-------------|
| [`HTML_BASICS.md`](HTML_BASICS.md) | Початківець | HTML5 теги, семантика, структура документу |
| [`CSS_BASICS.md`](CSS_BASICS.md) | Початківець | Селектори, box model, flexbox, grid, media queries |
| [`BOOTSTRAP_5.md`](BOOTSTRAP_5.md) | Початківець+ | Grid, Flexbox utilities, компоненти, теми |
| [`DESIGN_FOUNDATIONS.md`](DESIGN_FOUNDATIONS.md) | Середній | UX/UI принципи, CRAP, типографіка, дизайн-системи |
| [`DJANGO_TEMPLATES_BOOTSTRAP.md`](DJANGO_TEMPLATES_BOOTSTRAP.md) | Середній | Django шаблони + Bootstrap — інтеграція та паттерни |
| [`ADVANCED_TEMPLATES.md`](ADVANCED_TEMPLATES.md) | Середній+ | Context Processors, Dashboard Architecture, Crispy Forms |
| [`CRISPY_FORMS.md`](CRISPY_FORMS.md) | Середній+ | FormHelper, Layout, Bootstrap 5 pack — повний довідник |
| [`DJANGO_NINJA_TEMPLATES.md`](DJANGO_NINJA_TEMPLATES.md) | Просунутий | Django Ninja REST API + шаблони, HTMX |
| [`DJANGO_ADMIN_UNFOLD.md`](DJANGO_ADMIN_UNFOLD.md) | Просунутий | Кастомізація Django Admin через Unfold |

### Де що шукати — швидкий довідник

| Питання | Файл |
|---------|------|
| Як підключити Bootstrap? | **цей файл** розділ 1 |
| Що таке CDN/npm? | **цей файл** розділ 1 |
| Як вмикається dark mode? | **цей файл** розділ 2 |
| Що таке CSS-змінні? | **цей файл** розділ 4 |
| Як будується sidebar? | **цей файл** розділ 6 |
| Які класи Bootstrap використовуємо? | **цей файл** розділ 8 |
| Принципи UX, CRAP | [`DESIGN_FOUNDATIONS.md`](DESIGN_FOUNDATIONS.md) §1-2 |
| Bootstrap Grid детально | [`BOOTSTRAP_5.md`](BOOTSTRAP_5.md) |
| FormHelper + Layout | [`CRISPY_FORMS.md`](CRISPY_FORMS.md) |
| Django template inheritance | [`ADVANCED_TEMPLATES.md`](ADVANCED_TEMPLATES.md) §2 |
| Context Processor | [`ADVANCED_TEMPLATES.md`](ADVANCED_TEMPLATES.md) §3 |

---

## Підсумок

```
Щоб побудувати CrispyNotes Dashboard:

1. base.html
   └── Bootstrap CDN (CSS + Icons + JS)
   └── data-bs-theme="dark"
   └── {% static 'app.css' %}

2. app.css
   └── :root {} → CSS токени (кольори, spacing)
   └── .sidebar, .topbar, .note-card → custom компоненти
   └── transitions, hover effects, scrollbar

3. dashboard.html
   └── d-flex vh-100            → повноекранний layout
   └── nav.sidebar 260px        → фіксована колонка
   └── flex-grow-1              → main займає решту
   └── nav-pills flex-column    → вертикальне меню
   └── request.resolver_match   → active state без JS

4. Сторінки
   └── {% extends 'layouts/dashboard.html' %}
   └── Тільки {% block content %} — sidebar/topbar безкоштовно
```

> **Ключова ідея:** Bootstrap дає ~80% готового — Grid, кнопки, форми, dark mode.
> Решта 20% — CSS-токени та кілька кастомних класів — і проєкт виглядає як product.
