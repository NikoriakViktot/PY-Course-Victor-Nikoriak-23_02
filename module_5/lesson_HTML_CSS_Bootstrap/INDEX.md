# 🎓 Як використовувати цей курс — Гід для початківців

## Ти новачок у фронтенді?

Якщо HTML, CSS, і Django для тебе нові поняття — не хвилюйся. Цей курс побудований так, щоб ти міг розібратися з нуля.

### Ментальна модель курсу

Уяви, що будуєш будинок:

| Шар | Технологія | Аналогія |
|-----|-----------|---------|
| Фундамент + стіни | HTML | Структура будинку — де вікна, де двері |
| Фарба + оздоблення | CSS | Зовнішній вигляд — кольори, шрифти, відступи |
| Меблі IKEA | Bootstrap | Готові компоненти — не треба робити стіл з нуля |
| Архітектор | Django Templates | Генерує різні будинки за одним кресленням |
| Прораб-автоматник | Django Ninja | API — будинок може "розмовляти" з іншими системами |
| Нестандартні рішення | Advanced Templates | Складні системи для великих проектів |
| Управляючий | Django Admin | Інтерфейс для управління всім будинком |

### Три рівні розуміння

Для кожної теми є три рівні:

1. **"Що це і як використовувати"** — ти можеш написати код і він працює
2. **"Як це працює всередині"** — ти розумієш, що відбувається у браузері/Django
3. **"Архітектурні наслідки"** — ти знаєш, чому треба робити саме так, а не інакше

Мета цього курсу — довести тебе до рівня 2-3.

### Як браузер обробляє веб-сторінку (головний контекст)

Перш ніж розпочати, зрозумій цей загальний потік:

```
Ти вводиш URL у браузер
        ↓
DNS перекладає домен в IP-адресу
        ↓
HTTP запит летить на сервер
        ↓
Django отримує запит → urls.py → view функція
        ↓
View бере дані з бази даних
        ↓
Django Templates генерує HTML рядок (SSR)
        ↓
HTTP відповідь летить назад до браузера
        ↓
Браузер парсить HTML → будує DOM
        ↓
Браузер завантажує CSS → будує CSSOM
        ↓
DOM + CSSOM = Render Tree
        ↓
Layout: браузер вираховує розміри та позиції
        ↓
Paint: браузер малює пікселі
        ↓
Composite: GPU складає шари
        ↓
Ти бачиш сторінку! 🎉
```

### Де що може піти не так (і як дебажити)

| Симптом | Де шукати | Інструмент |
|---------|-----------|-----------|
| Сторінка пуста | HTML структура, Django view | F12 → Network → response |
| Стилі не застосовуються | CSS файл не завантажено, специфічність | F12 → Elements → Styles |
| Форма не відправляється | csrf_token відсутній, action неправильний | F12 → Network → POST request |
| Дані не відображаються | Контекст не переданий у шаблон | Django Debug Toolbar → Templates |
| Багато SQL запитів | N+1 проблема | Django Debug Toolbar → SQL |
| API не відповідає | Ninja endpoint не зареєстрований | /api/docs/ Swagger UI |

---

# HTML, CSS і Bootstrap — Система знань

> Продовження Django-архітектури. Від голого `HttpResponse("текст")`
> до Bootstrap 5 SaaS-інтерфейсів, custom template tags, HTMX і Unfold Admin.

**Попередній урок:** `lesson_Django_Network_Architecture` — MVT, ORM, HttpResponse
**Цей урок:** фронтенд + шаблонізація + production-архітектура Django

---

## Навігація по Модулю 5

| Урок | Ключові концепції | Практичний проєкт |
|------|------------------|-------------------|
| [lesson_Django_Network_Architecture](../lesson_Django_Network_Architecture/) | MVT, URL routing, HttpResponse, прості view | simple_django_project, news_portal |
| [lesson_Django_ORM_Database](../lesson_Django_ORM_Database/) | ORM, Services/Selectors, FBV, Bootstrap5-форми вручну | notes_project, notes_project_cbv |
| **lesson_HTML_CSS_Bootstrap** (цей урок) | HTML/CSS/Bootstrap, Advanced Templates, Crispy Forms, Design Foundations | django_bootstrap_project, crispy_notes_project |

---

## Навігація по файлах

> **Як читати цю таблицю:** Рівень 1 = абсолютний початківець, Рівень 3 = впевнений junior. Порядок важливий — файли залежать один від одного.

## Файли уроку

| Файл | Рядків | Рівень | Тема |
|------|--------|--------|------|
| [DESIGN_FOUNDATIONS.md](DESIGN_FOUNDATIONS.md) | ~650 | 0 | UX, CRAP, IA, Bootstrap-філософія, Django Template Architecture, Crispy Forms, Tailwind vs Bootstrap, Static Files, React+Django |
| [CRISPY_FORMS.md](CRISPY_FORMS.md) | ~300 | 3 | django-crispy-forms довідник: FormHelper, всі Layout-компоненти, template tags, приклади |
| [HTML_BASICS.md](HTML_BASICS.md) | 1038 | 1 | DOM pipeline, теги, форми, семантика, a11y, DevTools |
| [CSS_BASICS.md](CSS_BASICS.md) | 1124 | 2 | Rendering Pipeline, Box Model, Flexbox, Grid, Holy Grail, Debugging |
| [BOOTSTRAP_5.md](BOOTSTRAP_5.md) | 1388 | 3 | Grid, Breakpoints, Navbar, Card, Modal, Forms, JS API, Accessibility |
| [DJANGO_TEMPLATES_BOOTSTRAP.md](DJANGO_TEMPLATES_BOOTSTRAP.md) | 1015 | 4 | SSR lifecycle, DTL, Template Inheritance, Static Files, Bootstrap Forms |
| [DJANGO_NINJA_TEMPLATES.md](DJANGO_NINJA_TEMPLATES.md) | 960 | 5 | Django Ninja, TemplateResponse, Jinja2 intro, HTMX intro, Swagger |
| [ADVANCED_TEMPLATES.md](ADVANCED_TEMPLATES.md) | 1506 | 6 | Context Processors, Custom Tags, crispy-forms, Vite, SaaS Dashboard, Jinja2 Deep Dive, HTMX lifecycle |
| [DJANGO_ADMIN_UNFOLD.md](DJANGO_ADMIN_UNFOLD.md) | 2171 | 7 | Django Admin + Unfold: AdminSite, ModelAdmin, Dashboard, Widgets, Filters, Caching |

**Практичні проєкти:**
- [django_bootstrap_project/README.md](django_bootstrap_project/README.md) — CRUD-нотатки: Navbar, Card Grid, Forms, Messages, Debug Toolbar
- [crispy_notes_project/README.md](crispy_notes_project/README.md) — Notes CRUD з `django-crispy-forms` FormHelper+Layout, SaaS Dashboard (`layouts/` + `components/`), порівняння 3 рівнів рендерингу форм

---

## Карта секцій

### HTML_BASICS.md
| § | Тема |
|---|------|
| 0 | Браузер і HTML: DOM pipeline, Error Recovery, Design Principles |
| 1–2 | Анатомія документа і тегу |
| 3–6 | Заголовки, посилання, списки, таблиці |
| 7 | Форми — inputs, select, textarea, label, fieldset |
| 8–9 | Семантика HTML5: article, section, nav, aside, header, footer |
| 10–11 | id/class атрибути, meta-теги, SEO, Open Graph |
| 12 | Типові помилки початківців |
| 13 | Block vs Inline — модель потоку документа |
| 14 | Accessibility (ARIA, role, alt, tabindex, skip-link) |
| 15 | Data-атрибути — `data-*` |
| 16 | DevTools — source vs live DOM |
| 17 | Повний приклад — семантична сторінка нотаток |
| 18 | 10 питань для самоперевірки |

### CSS_BASICS.md
| § | Тема |
|---|------|
| 0 | Rendering Pipeline: DOM+CSSOM → Render Tree → Layout → Paint; Layout Thrashing |
| 1–3 | Підключення CSS, анатомія правила, селектори |
| 4 | Специфічність: (0,0,0,0) алгоритм + prediction quiz |
| 5 | Box Model: margin/border/padding/content, `box-sizing` |
| 6 | Одиниці: px, em, rem, %, vh/vw |
| 7 | `display`: block, inline, inline-block, none |
| 8 | Flexbox: `flex-direction`, `justify-content`, `align-items`, `flex-wrap` |
| 9 | CSS Grid: `grid-template-columns`, `fr`, `grid-area`, named areas |
| 10 | Позиціонування: static, relative, absolute, fixed, sticky |
| 11 | Media Queries + Mobile First концепція (min-width vs max-width) |
| 11b | Bootstrap Breakpoints: таблиця xs–xxl, quiz `col-12 col-md-6 col-lg-4` → [BOOTSTRAP_5.md §3] |
| 12 | CSS-змінні `--var`, `:root` |
| 13 | Типографіка |
| 14 | Holy Grail Layout: Grid macro + Flexbox micro |
| 15 | Практичні патерни |
| 16 | Debugging CSS: margin collapse, stacking context, DevTools |
| 17 | CSS Performance: will-change, layer promotion |
| 18 | 10 питань для самоперевірки |

### BOOTSTRAP_5.md
| § | Тема |
|---|------|
| 0 | Навіщо Bootstrap; Bootstrap vs Tailwind — філософська різниця |
| 1 | CDN підключення; django-bootstrap5; Bootstrap у Django Templates |
| 2 | Grid System: Container → Row → Column, математика 12 одиниць, вкладені сітки |
| 3 | Breakpoints: xs/sm/md/lg/xl/xxl таблиця; Mobile First читання класів; quiz відповідь |
| 4 | Утиліти: spacing scale, кольори, display/flexbox, типографіка, borders/shadows |
| 5 | Navbar: `navbar-expand-lg`, collapse, toggler, ARIA |
| 6 | Card: anatomy, `row-cols-*`, `h-100`, hover effect |
| 7 | Форми: `form-control`, Bootstrap validation, `was-validated` |
| 8 | Alerts: `alert-{variant}`, dismissible, Django Messages → Bootstrap |
| 9 | Modal: архітектура, data-bs API, JS Event Lifecycle (`show.bs.modal`, `shown.bs.modal`) |
| 10 | Bootstrap JS: Data API vs JavaScript API, Popper.js, Event Lifecycle |
| 11 | Accessibility: ARIA у компонентах, `visually-hidden`, focus management |
| 12 | Anti-patterns: overriding Bootstrap, JS conflicts, CDN у production |
| 13 | Повний Django приклад: base.html + note_list.html з усіма компонентами |
| 14 | 10 питань для самоперевірки |

### DJANGO_TEMPLATES_BOOTSTRAP.md
| § | Тема |
|---|------|
| 0 | Server-Side Rendering lifecycle: HTTP → View → Template Engine → HTTP Response → Browser |
| 1 | `render()` internals: Template.render(), RequestContext, context processors |
| 2 | Context і Dot-Lookup: dict → attribute → method → index (порядок пошуку) |
| 3 | DTL синтаксис: `{{ }}`, `{% %}`, `\|filter`; if/elif/else, for+forloop, url, csrf_token, with, comment |
| 4 | Template Inheritance: `{% extends %}`, `{% block %}`, `{{ block.super }}`, 3-рівнева ієрархія |
| 5 | Static Files: `{% load static %}`, `{% static 'path' %}`, `collectstatic`, `ManifestStaticFilesStorage` |
| 6 | HttpRequest атрибути; HTTP структура запиту/відповіді |
| 7 | Bootstrap Forms: ручний рендеринг, Widget attrs, django-bootstrap5 `{% bootstrap_form %}` |
| 8 | Django Debug Toolbar: SQL Panel (N+1), Templates Panel; PRG паттерн; CSRF; XSS та `\|safe` |
| 9 | Anti-patterns: HTML у Python, hardcoded URL/static, пропущений csrf_token |
| 10 | 10 питань для самоперевірки |

### DJANGO_NINJA_TEMPLATES.md
| § | Тема |
|---|------|
| 0–1 | Django Ninja vs DRF vs Views; встановлення, NinjaAPI, Router |
| 2 | HTML Response Pipeline: `render()` vs `TemplateResponse` під капотом |
| 3 | SSR Architecture у Ninja: повний Request Lifecycle ASCII-діаграма |
| 4 | JSON API vs HTML Endpoints: той самий ресурс, два формати |
| 5 | Гібридна архітектура: SSR + Ninja API + HTMX живий пошук (intro) → [ADVANCED_TEMPLATES.md §7] |
| 6 | Jinja2 intro: DTL vs Jinja2 таблиця, Settings dual-backend, `jinja2_env.py`, Ninja+Jinja2 endpoint → [ADVANCED_TEMPLATES.md §6] |
| 7 | TemplateResponse: deferred rendering, `post_render_callback`, middleware interception |
| 8 | Production Patterns: `cached.Loader`, production settings, Query Optimization у View, Ninja кешування |
| 9 | Ninja Schemas: Pydantic in/out, ModelSchema, повний CRUD Router |
| 10 | Swagger UI: `/api/docs/`, захист у production |
| 11 | Django View vs Ninja Endpoint — порівняльна таблиця |
| 12 | Anti-patterns |
| 13 | 10 питань для самоперевірки |

### ADVANCED_TEMPLATES.md
| § | Тема |
|---|------|
| 1 | Context Processors: вбудовані (`auth`, `request`, `messages`), кастомний з кешуванням |
| 2 | Custom Template Tags: `simple_tag`, `inclusion_tag`, `filter`; структура `templatetags/` |
| 3 | crispy-forms: `FormHelper`, `Layout`, `Row/Column/Fieldset/HTML/Submit` |
| 4 | Vite: `vite.config.js`, Bootstrap через npm/SCSS, `ManifestStaticFilesStorage`, multi-stage Dockerfile |
| 5 | SaaS Dashboard: `base.html` → `layouts/dashboard.html` → `notes/list.html`; sidebar, topbar, pagination, empty_state, confirm_modal |
| 6 | Jinja2 Deep Dive: `Environment` factory, макроси `{% macro %}`, `{{ super() }}`, `FileSystemBytecodeCache`, streaming |
| 7 | HTMX lifecycle: request lifecycle діаграма, живий пошук, infinite scroll, optimistic UI, Modal server-rendered, `HX-Redirect` response header |
| 8 | 10 питань для самоперевірки |

### DJANGO_ADMIN_UNFOLD.md
| § | Тема |
|---|------|
| 0 | Django Admin vs Unfold: архітектурна позиція, навіщо Unfold |
| 1 | AdminSite: синглтон, кілька AdminSite для різних ролей, `each_context()` |
| 2 | ModelAdmin: `list_display`, `list_filter`, `fieldsets`, `inlines`, custom columns (`format_html`), actions, custom URLs |
| 3 | Admin Request Lifecycle: Middleware → `change_view` → permissions → form → `save_model` → `response_change` |
| 4 | ChangeList: кастомний клас, `ShowFacets` (Django 5.0+) |
| 5 | Query Architecture: N+1 у `list_display`, `list_select_related`, `search_fields` префікси (`^`, `=`, `@`), `get_search_results()`, `prefetch_related` |
| 6 | Admin Rendering Pipeline: `TemplateResponse`, ієрархія шаблонів (глобал/app/model), `base_site.html` |
| 7 | Unfold setup: `INSTALLED_APPS` порядок, `UNFOLD` config, `COLORS`, `THEME`, `UnfoldModelAdmin` |
| 8 | Sidebar + Navigation: `SITE_DROPDOWN`, badge callbacks, `TABS` (static + dynamic callback) |
| 9 | Dashboard: `DASHBOARD_CALLBACK`, `templates/admin/index.html`, `unfold/layouts/base_simple.html` |
| 10 | Widget Systems: Card, Chart (line/bar), Tracker (heatmap), Cohort (retention table) |
| 11 | Information Hierarchy: Fieldset tabs, Conditional fields (Alpine.js), SortableStackedInline, Expandable Rows |
| 12 | Enterprise Patterns: паралельний `UnfoldAdminSite`, `InfinitePaginator`, crispy+Unfold, import/export, Command Palette |
| 13 | Anti-patterns: адмін як frontend, State Leakage, XSS via `mark_safe`, повільний search |
| 14 | 10 питань для самоперевірки |
| 15 | Advanced Filtering: `AutocompleteSelectFilter`, `RangeDateTimeFilter`, `TextFilter`, `list_filter_submit` |
| 16 | Bulk Actions + Dialog Actions: `BaseDialogForm`, row-level actions |
| 17 | Component Classes: `@register_component`, `get_context_data()` |
| 18 | Custom Pages: `UnfoldModelAdminViewMixin`, реєстрація в sidebar |
| 19 | Advanced Widgets: `WysiwygWidget`, `ArrayWidget`, `autocomplete_fields` |
| 20 | Performance: Redis caching, `{% cache %}`, `cached.Loader`, PostgreSQL Full-Text Search + GIN index |
| 21 | Datasets — вбудований ChangeList у ChangeForm |
| 22 | Production Checklist (22 пункти: безпека, продуктивність, архітектура, UX) |

---

---

## 🗺️ Шлях студента — Детальний гід

> **Як використовувати цей шлях:**
> - Проходь кроки в порядку — кожен крок спирається на попередній
> - Для кожного кроку: **прочитай** → **напиши код вручну** → **відкрий в браузері** → **покрути DevTools**
> - Не переходь до наступного кроку, поки не зможеш пояснити попередній "простими словами"

### Контрольне питання для кожного рівня

Перед тим як рухатися далі, запитай себе:

**Рівень HTML (кроки 0-4):** Чи можу я пояснити, як браузер перетворює HTML-текст на візуальний елемент?

**Рівень CSS (кроки 5-7):** Чи розумію я, чому `position: absolute` поводиться по-різному залежно від батьківського елемента?

**Рівень Bootstrap (кроки 8-10):** Чи можу я пояснити, чому Bootstrap використовує `min-width` (не `max-width`) у media queries?

**Рівень Django Templates (кроки 11-14):** Чи розумію я різницю між `{{ }}` та `{% %}`? Чи можу пояснити, коли вмираю Python і живе лише HTML?

**Рівень Advanced (кроки 15-22):** Чи розумію я, коли використовувати HTMX замість JavaScript, і чому?

## Шлях студента

```
1.  HTML_BASICS.md §0         ← DOM pipeline: bytes → parser → DOM → CSSOM → paint
2.  HTML_BASICS.md §1–12      ← теги, форми, семантика, атрибути, meta
3.  HTML_BASICS.md §13–18     ← Block/Inline, Accessibility, data-*, DevTools
    ↓
4.  CSS_BASICS.md §0          ← Rendering Pipeline: чому CSS блокує рендеринг
5.  CSS_BASICS.md §1–11       ← синтаксис, специфічність, Box Model, Flexbox, Grid
6.  CSS_BASICS.md §11b        ← Mobile First + Bootstrap quiz
7.  CSS_BASICS.md §14–18      ← Holy Grail Layout, Debugging, Performance
    ↓
8.  BOOTSTRAP_5.md §0–3       ← навіщо Bootstrap, CDN, Grid архітектура, Breakpoints
9.  BOOTSTRAP_5.md §4–7       ← утиліти, Navbar, Card, Forms
10. BOOTSTRAP_5.md §8–11      ← Modal, JS API, Event Lifecycle, Accessibility
11. BOOTSTRAP_5.md §12–13     ← Anti-patterns, повний Django приклад
    ↓
    [Практика: django_bootstrap_project/README.md — кроки 1–9]
    ↓
12. DJANGO_TEMPLATES_BOOTSTRAP.md §0–2  ← SSR lifecycle, render(), Context, Dot-Lookup
13. DJANGO_TEMPLATES_BOOTSTRAP.md §3–5  ← DTL синтаксис, Template Inheritance, Static
14. DJANGO_TEMPLATES_BOOTSTRAP.md §6–9  ← HttpRequest/Response, Bootstrap Forms, DjDT
    ↓
15. DJANGO_NINJA_TEMPLATES.md §0–4   ← Ninja API, HTML Pipeline, TemplateResponse
16. DJANGO_NINJA_TEMPLATES.md §5–8   ← HTMX intro, Jinja2 intro, Production Patterns
17. DJANGO_NINJA_TEMPLATES.md §9–13  ← Schemas, Swagger, anti-patterns
    ↓
18. ADVANCED_TEMPLATES.md §1–3  ← Context Processors, Custom Tags, crispy-forms
19. ADVANCED_TEMPLATES.md §4–5  ← Vite pipeline, SaaS Dashboard Architecture
20. ADVANCED_TEMPLATES.md §6–7  ← Jinja2 Deep Dive (macros, bytecode), HTMX lifecycle
    ↓
21. DJANGO_ADMIN_UNFOLD.md §0–6   ← Django Admin архітектура, Query Optimization
22. DJANGO_ADMIN_UNFOLD.md §7–14  ← Unfold setup, Sidebar, Dashboard, Widgets
23. DJANGO_ADMIN_UNFOLD.md §15–22 ← Filters, Actions, Component Classes, Production
```

---

## ⚡ Швидкий старт — для тих, хто поспішає

Якщо у тебе обмежений час:

### Мінімальний шлях (1 тиждень):
1. HTML_BASICS §0-§8 (структура, форми)
2. CSS_BASICS §5, §8 (Box Model, Flexbox)
3. BOOTSTRAP_5 §2-§4 (Grid, Breakpoints, Utilities)
4. DJANGO_TEMPLATES_BOOTSTRAP §0-§4 (SSR, render(), DTL, Inheritance)

Після цього ти зможеш будувати базові Django веб-сторінки.

### Повний шлях (3-4 тижні):
Всі 23 кроки зі "Шляху студента" вище.

Після цього ти зможеш будувати production-ready Django застосунки з modern UI.

---

## 🔧 Інструменти, які потрібні з першого дня

| Інструмент | Навіщо | Як відкрити |
|-----------|--------|------------|
| Chrome DevTools | Дебаг HTML/CSS, перегляд DOM | F12 або Ctrl+Shift+I |
| Django Debug Toolbar | SQL запити, контекст шаблону | Встановити в settings.py |
| Swagger UI | Тестувати Django Ninja API | /api/docs/ |
| VS Code + Emmet | Швидке написання HTML | вбудовано в VS Code |

---

## 📊 Карта залежностей між концепціями

> **Читай зліва направо:** якщо концепція зліва, ти маєш розуміти її, щоб зрозуміти концепцію справа.

```
HTML DOM
   ├──→ CSS Rendering Pipeline (CSSOM + DOM = Render Tree)
   │        └──→ Bootstrap Grid (використовує Flexbox/CSS)
   │                 └──→ Bootstrap Components (Card, Modal, Navbar)
   └──→ HTML Forms (method, action, enctype)
            └──→ Django Forms (request.POST, is_valid(), save())
                     └──→ crispy-forms (forms + Bootstrap styling)

Django Templates (DTL)
   ├──→ Template Inheritance ({% extends %}, {% block %})
   │        └──→ SaaS Dashboard Architecture (3-level hierarchy)
   ├──→ Context Processors (global template variables)
   ├──→ Custom Template Tags (Python functions in templates)
   └──→ Jinja2 (alternative template engine, macros)

Django Ninja
   ├──→ Pydantic Schemas (data validation)
   ├──→ render() vs TemplateResponse (SSR)
   └──→ HTMX (server-driven UI, HTML fragments)
            └──→ Infinite Scroll, Live Search, Optimistic UI

Django Admin
   ├──→ ModelAdmin (list_display, fieldsets)
   ├──→ N+1 Problem (select_related, list_select_related)
   ├──→ Unfold (modern UI framework for admin)
   └──→ Dashboard Widgets (Chart, Card, Tracker, Cohort)
```

---

## 🆘 Потрапив у глухий кут? Використовуй цей алгоритм

```
Проблема з HTML?
  → F12 → Elements → перевір DOM (не source! DOM може відрізнятися)
  → HTML_BASICS §12 (типові помилки), §16 (DevTools)

Проблема з CSS?
  → F12 → Elements → Styles (чи перекреслено правило?)
  → F12 → Elements → Computed (яке значення ФАКТИЧНО застосовано?)
  → CSS_BASICS §16 (алгоритм дебагу), §4 (специфічність)

Проблема з Bootstrap Grid?
  → Тимчасово додай: .row { background: rgba(255,0,0,0.1) }
  → BOOTSTRAP_5 §2 (математика Grid), §3 (breakpoints)

Проблема з Django Template?
  → Django Debug Toolbar → Templates → context
  → Перевір: чи передав контекст у render()?
  → DJANGO_TEMPLATES_BOOTSTRAP §2 (dot-lookup), §9 (anti-patterns)

Проблема з формою (CSRF)?
  → F12 → Network → POST request → headers → є csrfmiddlewaretoken?
  → DJANGO_TEMPLATES_BOOTSTRAP §3 (csrf_token)

Дуже багато SQL запитів?
  → Django Debug Toolbar → SQL panel
  → DJANGO_TEMPLATES_BOOTSTRAP §8, DJANGO_ADMIN_UNFOLD §5

HTMX не спрацьовує?
  → F12 → Network → чи летить запит при взаємодії?
  → F12 → Console → чи є JavaScript помилки?
  → ADVANCED_TEMPLATES §7

Django Admin повільний?
  → Django Debug Toolbar на список Admin → перевір SQL count
  → DJANGO_ADMIN_UNFOLD §5 (N+1), §12 (InfinitePaginator)
```

---

## Де що шукати

| Питання | Файл | § |
|---------|------|---|
| Як браузер читає HTML? | HTML_BASICS.md | §0 |
| `<div>` vs `<section>` — різниця? | HTML_BASICS.md | §8 |
| ARIA і доступність | HTML_BASICS.md | §14 |
| Як відлагодити DOM у DevTools? | HTML_BASICS.md | §16 |
| Що таке Box Model? | CSS_BASICS.md | §5 |
| Flexbox vs Grid — коли що? | CSS_BASICS.md | §8–9 |
| Mobile First: min-width чи max-width? | CSS_BASICS.md | §11 |
| Bootstrap breakpoints таблиця | BOOTSTRAP_5.md | §3 |
| Bootstrap Grid — 3 колонки | BOOTSTRAP_5.md | §2–3 |
| Navbar з hamburger | BOOTSTRAP_5.md | §5 |
| Modal з динамічними даними | BOOTSTRAP_5.md | §9 |
| Django Messages → Bootstrap Alert | BOOTSTRAP_5.md | §8 |
| `{% extends %}` і `{% block %}` | DJANGO_TEMPLATES_BOOTSTRAP.md | §4 |
| Dot-Lookup `{{ user.profile.name }}` | DJANGO_TEMPLATES_BOOTSTRAP.md | §2 |
| Bootstrap Forms у Django | DJANGO_TEMPLATES_BOOTSTRAP.md | §7 |
| CSRF token — навіщо | DJANGO_TEMPLATES_BOOTSTRAP.md | §8 |
| Django Debug Toolbar SQL Panel | DJANGO_TEMPLATES_BOOTSTRAP.md | §8 |
| `render()` vs `TemplateResponse` | DJANGO_NINJA_TEMPLATES.md | §2, §7 |
| Django Ninja vs DRF | DJANGO_NINJA_TEMPLATES.md | §0 |
| HTMX hx-trigger, hx-target | ADVANCED_TEMPLATES.md | §7 |
| Context Processor — глобальний context | ADVANCED_TEMPLATES.md | §1 |
| `inclusion_tag` — reusable компонент | ADVANCED_TEMPLATES.md | §2 |
| crispy-forms FormHelper Python-лейаут | ADVANCED_TEMPLATES.md | §3 |
| Vite + Django налаштування | ADVANCED_TEMPLATES.md | §4 |
| SaaS sidebar layout | ADVANCED_TEMPLATES.md | §5 |
| Jinja2 macros і bytecode cache | ADVANCED_TEMPLATES.md | §6 |
| ModelAdmin `list_display`, actions | DJANGO_ADMIN_UNFOLD.md | §2 |
| N+1 у адмінці — `list_select_related` | DJANGO_ADMIN_UNFOLD.md | §5 |
| Unfold UNFOLD config у settings.py | DJANGO_ADMIN_UNFOLD.md | §7 |
| Unfold Dashboard + DASHBOARD_CALLBACK | DJANGO_ADMIN_UNFOLD.md | §9 |
| InfinitePaginator — без COUNT(*) | DJANGO_ADMIN_UNFOLD.md | §12 |
| Dialog Action з Bootstrap формою | DJANGO_ADMIN_UNFOLD.md | §16 |
| Full-text Search (PostgreSQL SearchVector) | DJANGO_ADMIN_UNFOLD.md | §20 |

---

## Зв'язок між файлами

```
HTML_BASICS ──────────────────► CSS_BASICS
(DOM tree)                       (CSSOM, Rendering Pipeline)
     │                                │
     └──────────┬─────────────────────┘
                ▼
           BOOTSTRAP_5
           (Grid, Navbar, Modal — побудовані на HTML+CSS)
                │
                ▼
     DJANGO_TEMPLATES_BOOTSTRAP
     (DTL рендерить Bootstrap HTML на сервері)
                │
                ├──► DJANGO_NINJA_TEMPLATES
                │    (API + Jinja2 + HTMX intro)
                │
                └──► ADVANCED_TEMPLATES
                     (Context Processors, Custom Tags,
                      crispy-forms, Vite, Jinja2 deep dive,
                      HTMX lifecycle)
                          │
                          ▼
                  DJANGO_ADMIN_UNFOLD
                  (внутрішні інструменти — окремий шар)
```

**Де є cross-references між файлами:**
- `CSS_BASICS.md §11b` → Bootstrap breakpoints таблиця детально у `BOOTSTRAP_5.md §3`
- `CSS_BASICS.md §11b` → Bootstrap utilities → `BOOTSTRAP_5.md §4`
- `DJANGO_NINJA_TEMPLATES.md §5` → HTMX повний lifecycle → `ADVANCED_TEMPLATES.md §7`
- `DJANGO_NINJA_TEMPLATES.md §6` → Jinja2 macros/bytecode → `ADVANCED_TEMPLATES.md §6`
