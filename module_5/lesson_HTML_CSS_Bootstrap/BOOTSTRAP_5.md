# Bootstrap 5 — Архітектура та Компоненти

> Bootstrap — це шар абстракції, який перетворює веб-дизайн із "написання сирого CSS"
> на "композицію готових архітектурних блоків".
> Для backend-розробника Bootstrap — це те ж саме що Django Admin:
> готовий, перевірений інструмент, щоб не будувати з нуля.

---

---

- 🧠 Ментальна модель: **Bootstrap** — це готовий набір LEGO. Без нього ти ліпиш деталі з глини (сирий CSS). З ним — клацаєш готові блоки разом.
- 📚 Чому це існує: **До Bootstrap (2011)** кожна команда будувала власну сітку, власні кнопки, власні модальні вікна — всі трохи різні, всі з багами. Twitter Bootstrap з'явився щоб стандартизувати UI-розробку.
- 🌐 Що Bootstrap робить під капотом: **Bootstrap** — це один великий CSS-файл (~190KB до мінімізації) з тисячами готових класів + один JS-файл що додає поведінку до компонентів (Modal, Dropdown, Tooltip тощо). Ти просто підключаєш їх і використовуєш класи.
- ❌ Типова помилка початківця: **Думати що Bootstrap — це "просто стилі"**. Bootstrap також надає JavaScript-поведінку (hamburger-меню, модальні вікна, тобтаб), систему сітки та доступність з коробки.
 
---

**Контекст для Django-розробників:** Ти пишеш Python/Django views — твоя сила у backend. Bootstrap дозволяє створити професійний UI без того, щоб бути CSS-експертом. Замість того щоб витрачати 10 годин на написання адаптивної навігації, ти пишеш 20 рядків HTML з Bootstrap-класами і отримуєш готовий результат.

**Історичний контекст:** До 2011 року кожна веб-команда будувала CSS з нуля. Кнопки виглядали по-різному на кожному сайті. Internet Explorer 6, 7, 8 мали різні баги — і кожен розробник писав власні "хаки" для сумісності. Bootstrap вирішив цю проблему: один стабільний, протестований CSS що працює скрізь.

## 0. Навіщо існують CSS-фреймворки

### Фундаментальна проблема без Bootstrap

```
Кожен проєкт → власний CSS для кнопок, карток, навігації
             → кросбраузерні баги
             → нестандартизований UI
             → нова команда — заново вивчати структуру
```

### Що Bootstrap вирішує

| Проблема | Рішення Bootstrap |
|----------|-------------------|
| Написання CSS для кожної кнопки | Готові класи: `.btn`, `.btn-primary` |
| Кросбраузерні баги | `Reboot` — нормалізація стилів під всі браузери |
| Адаптивність — окремі версії | 12-колонкова сітка + breakpoints |
| Нестандартний UI | Єдина система дизайну через класи |
| Modal/Dropdown логіка з нуля | Data API: `data-bs-toggle="modal"` |

### Bootstrap vs Tailwind — філософська різниця

| | Bootstrap | Tailwind |
|-|-----------|----------|
| **Підхід** | Component-First | Utility-First |
| **Готові компоненти** | Так (Navbar, Card, Modal) | Ні (будуєш сам) |
| **Кастомізація** | Sass-змінні, override | Атомарні утиліти |
| **Швидкість старту** | Дуже висока | Середня |
| **Кастомний дизайн** | Потребує зусиль | Нативний |
| **Для Django** | Ідеально | Потребує збірника |

> **Ментальна модель Bootstrap:** Конструктор LEGO для UI.
> Ти не виготовляєш деталі (сирий CSS) — ти збираєш з готових.

---

---
- **🧠 Ментальна модель:** CDN — це як стримінг музики (файл на сервері, ти слухаєш). Local — це як скачати трек (файл у тебе, завжди доступний). CDN швидше для старту, Local надійніше для продакшну.
- **📚 Чому це існує:** Підключення Bootstrap через CDN дозволяє розпочати роботу за 30 секунд без налаштування. Для навчальних проєктів це ідеально. Для продакшну часто використовують npm + bundler щоб включати тільки ті частини Bootstrap що реально потрібні.
- **🌐 Що Bootstrap робить під капотом:** При завантаженні CSS Bootstrap браузер парсить ~10,000 CSS-правил і будує CSSOM (CSS Object Model). Це відбувається блокуючи рендеринг — ось чому CSS іде в `<head>`, а JS — перед `</body>`.
- **❌ Типова помилка початківця:** Підключати Bootstrap JS перед Bootstrap CSS, або підключати власні стилі ДО Bootstrap CSS. Порядок критично важливий.
---

**CDN vs Local — коли що використовувати:**

CDN (Content Delivery Network) означає що файл Bootstrap живе на віддаленому сервері (cdn.jsdelivr.net). Браузер завантажує його звідти. Переваги: швидко, просто, не потрібно нічого встановлювати. Недолік: потрібен інтернет, і ти залежиш від зовнішнього сервера.

Local означає що ти завантажуєш Bootstrap і подаєш його зі свого сервера. Переваги: працює офлайн, не залежиш від зовнішніх сервісів. Недолік: треба налаштовувати.

**Порядок підключення — чому він важливий:**

Bootstrap CSS ОБОВ'ЯЗКОВО іде перед твоїм власним CSS — тоді твої стилі можуть перевизначити Bootstrap. Bootstrap JS ОБОВ'ЯЗКОВО іде перед `</body>` — тому що JS маніпулює DOM, і DOM повинен бути вже побудований. JS у `<head>` блокує рендеринг сторінки.

**Атрибут `integrity` — безпека через криптографію:**

`integrity="sha384-..."` — це SHA-384 хеш файлу. Браузер завантажує файл, обчислює його хеш і порівнює з вказаним. Якщо CDN-сервер був зламаний і файл підмінений — хеш не збіжиться і браузер ВІДМОВИТЬСЯ виконувати скрипт. Це захищає від атак на ланцюг постачання (supply chain attacks).

## 1. Підключення Bootstrap 5

### CDN (найшвидший спосіб — для навчання)

Цей HTML-шаблон є мінімально необхідним для роботи Bootstrap. Зверни увагу на `<meta name="viewport">` — без нього мобільні браузери рендерять сторінку як десктопну і масштабують її вниз, ламаючи адаптивність. Bootstrap CSS іде в `<head>` (потрібен до рендерингу), JS — перед `</body>` (не блокує відображення).

```html
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bootstrap 5</title>

    <!-- Bootstrap CSS — в <head> (блокує рендеринг поки не завантажиться) -->
    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        rel="stylesheet"
        integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH"
        crossorigin="anonymous"
    >
</head>
<body>
    <!-- Вміст -->

    <!-- Bootstrap JS + Popper — перед </body> (не блокує рендеринг) -->
    <script
        src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-YvpcrYf0tY3lHB60NNkmXc4s9bIOgUxi8T/jzmxfkOHv9y4m/sPyFG5p5TtVQOS"
        crossorigin="anonymous"
    ></script>
</body>
</html>
```

### У Django Templates

У Django-проєкті Bootstrap підключається у `base.html` — базовому шаблоні від якого успадковуються всі інші. Зверни на блоки `{% block extra_css %}` і `{% block extra_js %}` — вони дозволяють дочірнім шаблонам додавати сторінко-специфічні стилі та скрипти, не дублюючи базову структуру. Власні стилі (`custom.css`) підключені ПІСЛЯ Bootstrap — це дозволяє перевизначати Bootstrap-стилі.

```html
{# base.html #}
{% load static %}
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Сайт{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">

    <!-- Власні стилі — ПІСЛЯ Bootstrap (перевизначають) -->
    <link rel="stylesheet" href="{% static 'css/custom.css' %}">

    {% block extra_css %}{% endblock %}
</head>
<body>

    {% block content %}{% endblock %}

    <!-- Bootstrap JS Bundle (включає Popper.js) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### За допомогою django-bootstrap5

`django-bootstrap5` — це пакет що надає Django template tags для Bootstrap. Тег `{% bootstrap_form form %}` автоматично рендерить всі поля Django-форми з правильними Bootstrap-класами (`form-control`, `form-label`, `invalid-feedback`). Це економить десятки рядків HTML для кожної форми.

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_bootstrap5',
]
```

```html
{# У шаблоні #}
{% load django_bootstrap5 %}
{% bootstrap_css %}
{% bootstrap_javascript %}

<form method="post">
    {% csrf_token %}
    {% bootstrap_form form %}
    {% bootstrap_button "Зберегти" button_type="submit" button_class="btn-primary" %}
</form>
```

---

---
- **🧠 Ментальна модель:** Grid — це тривимірна матрьошка. Контейнер — зовнішня лялька (встановлює максимальну ширину). Row — середня (flex-контейнер). Col — внутрішня (реальний контент з відступами).
- **📚 Чому це існує:** До Grid-систем розробники використовували таблиці (`<table>`) для верстки сторінок — і це було жахливо. Bootstrap Grid вирішив проблему адаптивного макету через flexbox і математику 12 колонок.
- **🌐 Що Bootstrap робить під капотом:** Bootstrap генерує CSS з `flex: 0 0 X%` для кожної колонки, де X = (N/12)*100. `col-6` → `flex: 0 0 50%; max-width: 50%`. Row отримує `display: flex; flex-wrap: wrap; margin: 0 -12px` щоб компенсувати padding контейнера.
- **❌ Типова помилка початківця:** Писати контент напряму у `.row` без `.col`, або вкладати `.container` у `.container`. Обидва варіанти ламають математику відступів.
---

**Глибоке розуміння Grid перед кодом:**

Bootstrap Grid побудований на 3 вкладених концепціях:

```
Container  → встановлює max-width і центрує все
  └── Row  → створює flex-контейнер, використовує від'ємний margin для компенсації gutter
       └── Col → кожна колонка має padding (той самий "gutter")
```

**Чому саме 12 колонок?** 12 ділиться на 1, 2, 3, 4, 6, 12 — максимальна гнучкість. Тобі не потрібно писати дроби — ти просто кажеш "3 колонки" (col-4 × 3 = 12) або "4 колонки" (col-3 × 4 = 12).

**Математика сітки — детально:**

```
Container: max-width: 960px
  padding: 0 12px ← компенсує від'ємний margin Row
    ↓
  Row: margin: 0 -12px  ← "з'їдає" padding контейнера
    display: flex; flex-wrap: wrap;
    ↓
    Col-6: flex: 0 0 50%; padding: 0 12px ← "gutter" (проміжок між колонками)
    Col-6: flex: 0 0 50%; padding: 0 12px

Результат: дві рівні колонки з 24px загального проміжку між ними
(12px padding справа від першої + 12px padding зліва від другої)
```

Від'ємний margin на Row — це не баг, це математичний трюк: без нього перша і остання колонки мали б подвійний відступ від країв контейнера.

## 2. Grid System — Архітектура сітки

### Ієрархія: Container → Row → Column → Content

Наступний блок показує ПРАВИЛЬНУ і НЕПРАВИЛЬНУ ієрархію Grid. Запам'ятай: контент завжди іде всередину `.col`, ніколи напряму у `.row`. Вкладені контейнери також заборонені — вони подвоюють padding і ламають математику.

```
❌ НЕПРАВИЛЬНО:
<div class="row">
    <p>Контент напряму в row</p>   ← ламає margin/padding математику
</div>

❌ НЕПРАВИЛЬНО:
<div class="container">
    <div class="container">       ← вкладені контейнери
        ...
    </div>
</div>

✅ ПРАВИЛЬНО:
<div class="container">
    <div class="row">
        <div class="col-12 col-md-6">Контент</div>
        <div class="col-12 col-md-6">Контент</div>
    </div>
</div>
```

### Діаграма математики сітки

Ця діаграма показує як Bootstrap Grid працює зсередини. Зверни увагу на `margin: 0 -12px` у Row — це ключовий трюк що вирівнює колонки по краях контейнера. Padding у Col — це "gutter" (проміжок між колонками).

```
Container (.container)
│ max-width: 960px (на lg)
│ padding: 0 12px  ← компенсує negative margin row
│
└── Row (.row)
    │ display: flex; flex-wrap: wrap;
    │ margin: 0 -12px  ← від'ємний margin "забирає" padding контейнера
    │
    ├── Column (.col-md-6)
    │   │ flex: 0 0 50%; max-width: 50%
    │   │ padding: 0 12px  ← gutter (відстань між колонками)
    │   │
    │   └── [Контент тут]  ← padding захищає від країв
    │
    └── Column (.col-md-6)
        │ padding: 0 12px
        └── [Контент тут]
```

**Чому від'ємний margin?**
Row отримує `margin: 0 -12px` щоб компенсувати padding контейнера.
Це гарантує що перша і остання колонки вирівняні по краях контейнера.

### Типи контейнерів

Вибір типу контейнера залежить від дизайну. `.container` — для більшості сторінок (контент не розтягується до країв на великих екранах). `.container-fluid` — для повноекранних секцій (hero, карти, дашборди). `.container-md` — гібрид: мобільні повна ширина, планшети та більше — фіксована.

```html
<!-- Фіксована максимальна ширина на кожному breakpoint -->
<div class="container">...</div>

<!-- Завжди 100% ширини viewport -->
<div class="container-fluid">...</div>

<!-- 100% до md, потім фіксована -->
<div class="container-md">...</div>

<!-- 100% до lg, потім фіксована -->
<div class="container-lg">...</div>
```

| Клас | xs | sm | md | lg | xl | xxl |
|------|----|----|----|----|----|----|
| `.container` | 100% | 540px | 720px | 960px | 1140px | 1320px |
| `.container-fluid` | 100% | 100% | 100% | 100% | 100% | 100% |
| `.container-md` | 100% | 100% | 720px | 960px | 1140px | 1320px |

### Колонки — математика 12 одиниць

Ці приклади демонструють різні способи задати ширину колонок. `.col` (без числа) автоматично розподіляє доступний простір порівну між усіма колонками. Явні числа дають точний контроль. Якщо сума > 12 — flex-wrap переносить колонки на наступний рядок.

```html
<!-- Рівні колонки -->
<div class="row">
    <div class="col">Авто</div>     <!-- 1/N від доступної ширини -->
    <div class="col">Авто</div>
    <div class="col">Авто</div>
</div>

<!-- Явна ширина (сума в рядку = 12) -->
<div class="row">
    <div class="col-8">8/12 = 66.7%</div>
    <div class="col-4">4/12 = 33.3%</div>
</div>

<!-- Якщо сума > 12 → flex-wrap переносить на новий рядок -->
<div class="row">
    <div class="col-7">7/12</div>
    <div class="col-7">7/12 → переноситься (7+7=14 > 12)</div>
</div>

<!-- Вирівнювання по вертикалі -->
<div class="row align-items-center">    <!-- center | start | end | stretch -->
    <div class="col">...</div>
</div>

<!-- Вирівнювання по горизонталі -->
<div class="row justify-content-center"> <!-- start | end | center | between | around -->
    <div class="col-6">Центрована колонка</div>
</div>
```

### Вкладені сітки

Вкладені сітки — потужний патерн для складних макетів. Кожна колонка може містити свою власну Row з 12-колонковою математикою. Важливо: внутрішня 12 — це 12 від ширини батьківської колонки, а не від всього контейнера.

```html
<!-- Колонку можна розбити на власну 12-колонкову сітку -->
<div class="row">
    <div class="col-8">
        Основна колонка (8/12)
        <!-- Вкладена сітка — нова математика з нуля -->
        <div class="row">
            <div class="col-6">Вкладена 1 (6/12 від col-8)</div>
            <div class="col-6">Вкладена 2</div>
        </div>
    </div>
    <div class="col-4">Бічна колонка (4/12)</div>
</div>
```

---

---
- **🧠 Ментальна модель:** Breakpoints — це "пороги" — МОМЕНТ коли макет перемикається з телефонного на планшетний. Уяви термостат: нижче 20° — обігрів, вище 20° — кондиціонер. Breakpoints — це твоя температура.
- **📚 Чому це існує:** Один HTML-код повинен добре виглядати на екранах від 320px (малий телефон) до 2560px (великий монітор). Breakpoints дозволяють задати різну сіткову поведінку для різних розмірів без дублювання HTML.
- **🌐 Що Bootstrap робить під капотом:** Bootstrap CSS написаний з `min-width` media queries. `col-md-6` генерує: `@media (min-width: 768px) { .col-md-6 { flex: 0 0 50%; } }`. Правила для більших екранів оголошені пізніше у файлі, тому вони перемагають по CSS-каскаду.
- **❌ Типова помилка початківця:** Думати що `col-md-6` означає "тільки на md". Насправді це "від md і більше". Bootstrap Mobile First — правила нашаровуються зверху донизу, а не замінюють одне одне.
---

**Mobile First — чому Bootstrap так влаштований:**

Bootstrap використовує `min-width` media queries. Це означає: спочатку описуєш для найменшого екрана, потім додаєш правила для більших. Це "Mobile First" підхід.

Механіка каскаду:
- `col-12` — застосовується від 0px (немає media query, завжди активний)
- `col-md-6` — застосовується від 768px (є `@media (min-width: 768px)`)
- На екрані 800px ОБИДВА правила активні, але `col-md-6` оголошено ПІЗНІШЕ у файлі → він перемагає

Чому саме пізніше? CSS каскад: при однаковій специфічності правило що стоїть нижче у файлі перемагає. Bootstrap організує свої media queries від меншого до більшого — тому більший breakpoint завжди перемагає менший.

## 3. Breakpoints і Mobile First

### Таблиця breakpoints Bootstrap 5

Запам'ятай цю таблицю — вона є основою всієї адаптивної верстки Bootstrap. Prefix (`sm`, `md`, `lg` тощо) додається до будь-якого utility-класу щоб зробити його залежним від розміру екрана.

| Prefix | Назва | min-width | Типовий пристрій |
|--------|-------|-----------|------------------|
| *(none)* | Extra small | 0 | Телефон (портрет) |
| `sm` | Small | 576px | Телефон (альбом) |
| `md` | Medium | 768px | Планшет |
| `lg` | Large | 992px | Десктоп |
| `xl` | X-Large | 1200px | Великий монітор |
| `xxl` | XX-Large | 1400px | Дуже великий екран |

### Як читати клас: Mobile First = зліва → направо

Цей код показує як один елемент змінює поведінку на 4 різних розмірах екрана. Читай класи зліва направо — від найменшого екрана до найбільшого. Перший клас без prefix — базовий (мобільний), кожен наступний додає правило для більшого екрана.

```html
<div class="col-12 col-sm-6 col-md-4 col-lg-3">Елемент</div>
```

```
0px    → col-12    → 12/12 = 100%   (1 в рядку)
576px  → col-sm-6  →  6/12 = 50%   (2 в рядку)
768px  → col-md-4  →  4/12 = 33%   (3 в рядку)
992px  → col-lg-3  →  3/12 = 25%   (4 в рядку)
```

**Механіка:** Кожен наступний prefix має вищий `min-width` → CSS-правило з більшим `min-width`
оголошено пізніше в файлі → перемагає по каскаду.

### Prediction Quiz — відповідь

Перевір своє розуміння: скільки блоків буде в рядку на різних екранах? Порахуй: для кожного viewport активний тільки ОДИН клас (найбільший що ще застосовується). Сума колонок у рядку визначає кількість елементів.

```html
<div class="row">
    <div class="col-12 col-md-6 col-lg-4">Блок</div>  × 3
</div>
```

| Viewport | Активний клас | Ширина | Блоків у рядку |
|----------|--------------|--------|----------------|
| 480px | `col-12` | 100% | 1 |
| 800px | `col-md-6` | 50% | **2** (6+6=12) |
| 1200px | `col-lg-4` | 33% | **3** (4+4+4=12) |

**Відповідь: Б** — Планшет: 2 блоки, Монітор: 3 блоки.

---

---
- **🧠 Ментальна модель:** Bootstrap utilities — це як Tailwind, але менш гранулярний. `mt-3` = `margin-top: 1rem` (16px). Замість того щоб писати CSS, ти компонуєш з класів прямо в HTML. Це atomic CSS підхід.
- **📚 Чому це існує:** Замість того щоб відкривати CSS-файл для кожного дрібного відступу, Bootstrap дозволяє писати `mb-3` прямо в HTML. Це прискорює розробку і тримає "дрібні" стилі поряд з HTML-структурою де їм і місце.
- **🌐 Що Bootstrap робить під капотом:** `mt-3` генерує `margin-top: 1rem !important`. Зверни увагу на `!important` — це гарантує що utility-клас перемагає будь-який інший CSS. Це навмисно: utilities мають найвищий пріоритет.
- **❌ Типова помилка початківця:** Писати власний CSS `style="margin-top: 16px"` замість використання `mt-3`. Або не знати що `mx-auto` центрує блоковий елемент (margin: 0 auto).
---

**Шкала відступів — запам'ятай раз і назавжди:**

Bootstrap використовує шкалу де базова одиниця = `$spacer = 1rem = 16px`. Кожен рівень множить або ділить базову одиницю:
- `mt-1` = 4px (0.25rem)
- `mt-2` = 8px (0.5rem)
- `mt-3` = 16px (1rem) ← базова одиниця
- `mt-4` = 24px (1.5rem)
- `mt-5` = 48px (3rem)

Вивчи цю шкалу і ти більше ніколи не будеш писати `margin-top: 16px` вручну.

**Адаптивні utilities — дуже поширений патерн:**

`d-none d-md-block` = прихований на мобільних, видимий на планшетах+. Це один з найчастіших патернів у Bootstrap. Протилежне: `d-block d-md-none` = видимий тільки на мобільних.

## 4. Утиліти Bootstrap

### Відступи — spacing scale

Bootstrap використовує шкалу від 0 до 5, де 1 одиниця = 4px (`$spacer * 0.25`):

| Клас | Значення |
|------|---------|
| `*-0` | 0 |
| `*-1` | 4px (0.25rem) |
| `*-2` | 8px (0.5rem) |
| `*-3` | 16px (1rem) |
| `*-4` | 24px (1.5rem) |
| `*-5` | 48px (3rem) |
| `*-auto` | auto |

Наступний код демонструє всю систему скорочень для відступів. `m` = margin, `p` = padding. Напрямки: `t` (top), `b` (bottom), `s` (start/left), `e` (end/right), `x` (горизонталь), `y` (вертикаль). Адаптивні варіанти дозволяють задавати різні відступи для різних екранів.

```html
<!-- Margin: m = margin, p = padding -->
<!-- t=top, b=bottom, s=start(left), e=end(right), x=horizontal, y=vertical -->

<div class="mt-3">margin-top: 16px</div>
<div class="mb-2">margin-bottom: 8px</div>
<div class="mx-auto">margin-left: auto; margin-right: auto (центрування)</div>
<div class="p-4">padding: всі сторони 24px</div>
<div class="py-2 px-4">padding vertical 8px, horizontal 24px</div>

<!-- Адаптивні відступи -->
<div class="mt-3 mt-md-0">margin-top: 16px на мобільних, 0 на планшетах+</div>
<div class="p-2 p-lg-5">padding: 8px на мобільних, 48px на великих</div>
```

### Кольори і теми

Bootstrap надає семантичну систему кольорів через теми: `primary`, `secondary`, `success`, `danger`, `warning`, `info`, `light`, `dark`. Та сама тема (`success`) застосовується до тексту (`text-success`), фону (`bg-success`), кнопок (`btn-success`) і алертів (`alert-success`) — консистентна система.

```html
<!-- Текст -->
<p class="text-primary">Синій (primary)</p>
<p class="text-secondary">Сірий (secondary)</p>
<p class="text-success">Зелений (success)</p>
<p class="text-danger">Червоний (danger)</p>
<p class="text-warning">Жовтий (warning)</p>
<p class="text-info">Блакитний (info)</p>
<p class="text-light">Світлий</p>
<p class="text-dark">Темний</p>
<p class="text-muted">Сірий (приглушений)</p>
<p class="text-white bg-dark">Білий текст на темному фоні</p>

<!-- Фон -->
<div class="bg-primary text-white">Синій фон</div>
<div class="bg-light">Світло-сірий фон</div>
<div class="bg-transparent">Прозорий фон</div>

<!-- Кнопки з темами -->
<button class="btn btn-primary">Primary</button>
<button class="btn btn-outline-secondary">Outline Secondary</button>
<button class="btn btn-danger btn-sm">Маленька червона</button>
<button class="btn btn-success btn-lg">Велика зелена</button>
```

### Display та Flexbox утиліти

Display utilities дозволяють керувати видимістю і типом відображення елементів прямо в HTML. Адаптивні варіанти (`d-none d-md-block`) — один з найпоширеніших патернів у Bootstrap. Flex utilities (`justify-content-between`, `align-items-center`) дублюють CSS flexbox властивості у вигляді класів.

```html
<!-- Display -->
<div class="d-none">Прихований</div>
<div class="d-block">Block</div>
<div class="d-inline">Inline</div>
<div class="d-inline-block">Inline-block</div>
<div class="d-flex">Flex-контейнер</div>
<div class="d-grid">Grid-контейнер</div>

<!-- Адаптивне відображення -->
<div class="d-none d-md-block">Тільки від планшету</div>
<div class="d-block d-md-none">Тільки мобільний</div>
<div class="d-none d-lg-block d-xl-none">Тільки lg</div>

<!-- Flex утиліти (на flex-контейнері) -->
<div class="d-flex justify-content-between align-items-center">
    <span>Ліво</span>
    <span>Право</span>
</div>

<div class="d-flex flex-column flex-md-row gap-3">
    <!-- Вертикально на мобільних, горизонтально на планшетах -->
    <div>Елемент 1</div>
    <div>Елемент 2</div>
</div>

<!-- flex-wrap: wrap для переносу -->
<div class="d-flex flex-wrap gap-2">
    <div class="p-2 bg-light">Тег 1</div>
    <div class="p-2 bg-light">Тег 2</div>
    <div class="p-2 bg-light">Тег 3</div>
</div>
```

### Типографіка утиліти

Bootstrap надає типографічні utilities для розміру, вирівнювання, трансформації і ваги тексту. `display-1` до `display-6` — великі декоративні заголовки. `lead` — збільшений вступний абзац. `text-truncate` — обрізає текст з "..." (потребує фіксованої ширини).

```html
<h1 class="display-1">Великий заголовок (72px)</h1>
<h2 class="display-4">Менший display (36px)</h2>

<p class="lead">Вступний абзац (більший шрифт)</p>

<p class="text-center">По центру</p>
<p class="text-start">Зліва</p>
<p class="text-end">Справа</p>
<p class="text-md-center">По центру від md+</p>

<p class="text-uppercase">Великі літери</p>
<p class="text-lowercase">малі літери</p>
<p class="text-capitalize">Перша Велика</p>

<p class="fw-bold">Жирний</p>
<p class="fw-normal">Нормальний</p>
<p class="fst-italic">Курсив</p>

<p class="text-truncate" style="max-width: 200px">Довгий текст обрізається...</p>

<!-- Списки без стилів -->
<ul class="list-unstyled">
    <li>Без крапки</li>
    <li>Без відступу</li>
</ul>

<!-- Рядковий список -->
<ul class="list-inline">
    <li class="list-inline-item">Тег 1</li>
    <li class="list-inline-item">Тег 2</li>
</ul>
```

### Borders та Shadows

Border і shadow utilities дозволяють додавати рамки, заокруглення і тіні без написання CSS. `rounded-pill` — популярний для тегів і бейджів. `shadow-sm` — ледь помітна тінь, часто використовується на картках. `rounded-circle` разом з фіксованим розміром — патерн для аватарів.

```html
<!-- Рамки -->
<div class="border">Всі сторони</div>
<div class="border-top border-primary">Верхня синя рамка</div>
<div class="border-0">Без рамки</div>

<!-- Заокруглення -->
<div class="rounded">4px radius</div>
<div class="rounded-3">Більше (8px)</div>
<div class="rounded-pill">Пілюля (50rem)</div>
<div class="rounded-circle">Круг</div>
<img class="rounded-circle" src="..." style="width: 100px">

<!-- Тіні -->
<div class="shadow-sm">Маленька тінь</div>
<div class="shadow">Середня</div>
<div class="shadow-lg">Велика</div>
<div class="shadow-none">Без тіні</div>
```

---

---
- **🧠 Ментальна модель:** Navbar — це адаптивний flex-контейнер з вбудованою collapse-поведінкою. На великих екранах — горизонтальне меню. На малих — кнопка-гамбургер що розгортає вертикальне меню.
- **📚 Чому це існує:** Адаптивна навігація — одна з найскладніших задач у CSS. Bootstrap Navbar вирішує її одним компонентом: відстежує розмір екрана, ховає/показує елементи, анімує collapse, додає ARIA атрибути.
- **🌐 Що Bootstrap робить під капотом:** `navbar-expand-lg` генерує `@media (min-width: 992px) { .navbar-expand-lg .navbar-collapse { display: flex !important; } }`. На малих екранах `.collapse` = `display: none`. Bootstrap JS додає/прибирає клас `show` коли клікають гамбургер.
- **❌ Типова помилка початківця:** Забути `data-bs-target="#navbarMenu"` на кнопці або `id="navbarMenu"` на collapse-div — вони ПОВИННІ співпадати, інакше гамбургер не працює.
---

**Що означає `navbar-expand-lg`:**

"Розгорнути (показати повне меню) на LG-екранах і більше. Згорнути (гамбургер) нижче LG." Тобто ти вибираєш ТОЧКУ переходу між мобільним і десктопним виглядом навігації. Можеш замінити на `navbar-expand-md` або `navbar-expand-sm`.

**Механізм гамбургера — крок за кроком:**

```
На мобільному: .collapse div → display: none (меню приховане)
Клік на гамбургер → Bootstrap JS отримує data-bs-target="#navbarMenu"
                  → Знаходить #navbarMenu у DOM
                  → Додає клас "show" → CSS: display: block → анімація
                  → Одночасно: aria-expanded змінюється з "false" на "true"
```

**Чому ARIA атрибути на кнопці-гамбургері:** Користувачі скрінрідерів не можуть "побачити" що меню відкрилось. `aria-expanded="false/true"` дозволяє скрінрідеру ОГОЛОСИТИ стан кнопки. `aria-controls="navbarMenu"` вказує ЯКИЙ елемент вона контролює.

## 5. Компоненти — Navbar

### Базова структура Navbar

Цей код — повна адаптивна навігація для Django-проєкту. Зверни на 3 ключові частини: 1) `navbar-brand` — лого/назва сайту. 2) `navbar-toggler` — кнопка-гамбургер для мобільних (з'являється тільки на малих екранах). 3) `collapse navbar-collapse` — блок меню що ховається на мобільних. Всі три повинні бути присутні для коректної роботи.

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container">

        <!-- Лого/Назва -->
        <a class="navbar-brand" href="{% url 'hello_app:index' %}">
            МійСайт
        </a>

        <!-- Кнопка-гамбургер (для мобільних) -->
        <button
            class="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarMenu"
            aria-controls="navbarMenu"
            aria-expanded="false"
            aria-label="Перемкнути навігацію"
        >
            <span class="navbar-toggler-icon"></span>
        </button>

        <!-- Меню (collapse на мобільних) -->
        <div class="collapse navbar-collapse" id="navbarMenu">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                    <a class="nav-link active" aria-current="page"
                       href="{% url 'hello_app:index' %}">
                        Головна
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link"
                       href="{% url 'hello_app:note_list' %}">
                        Нотатки
                    </a>
                </li>
                <!-- Dropdown -->
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#"
                       data-bs-toggle="dropdown" aria-expanded="false">
                        Ще
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="#">Про нас</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="#">Контакти</a></li>
                    </ul>
                </li>
            </ul>

            <!-- Права частина: пошук або кнопки -->
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                    <span class="navbar-text">{{ user.username }}</span>
                    <a href="{% url 'logout' %}" class="btn btn-outline-light btn-sm">
                        Вийти
                    </a>
                {% else %}
                    <a href="{% url 'login' %}" class="btn btn-outline-light btn-sm">
                        Увійти
                    </a>
                {% endif %}
            </div>
        </div>
    </div>
</nav>
```

### Теми Navbar

Теми Navbar контролюються двома класами: `navbar-dark/navbar-light` (колір тексту і іконок всередині) і `bg-*` (колір фону). Прозора navbar для hero-секцій потребує `position: absolute` щоб "плавати" над контентом — але тоді контент під нею потрібно зсунути вниз.

```html
<!-- Темна тема -->
<nav class="navbar navbar-dark bg-dark">

<!-- Світла тема -->
<nav class="navbar navbar-light bg-light">

<!-- Кольорова -->
<nav class="navbar navbar-dark bg-primary">
<nav class="navbar navbar-dark bg-success">

<!-- Прозора (для hero секцій) -->
<nav class="navbar navbar-dark" style="background: transparent; position: absolute; width: 100%;">
```

---

---
- **🧠 Ментальна модель:** Card — це прямокутна коробка з необов'язковими заголовком, тілом і підвалом. Думай про неї як про фізичну картку з інформацією — вона самодостатня і може стояти поряд з іншими.
- **📚 Чому це існує:** Card — найуніверсальніший UI-патерн. Продукти в магазині, пости в блозі, профілі користувачів, нотатки — всі вони природно відображаються у вигляді карток.
- **🌐 Що Bootstrap робить під капотом:** `.card` = `position: relative; display: flex; flex-direction: column; background-color: #fff; border: 1px solid rgba(0,0,0,.125); border-radius: .375rem`. Flexbox всередині карткі дозволяє `.card-footer` завжди бути внизу через `margin-top: auto`.
- **❌ Типова помилка початківця:** Не додавати `h-100` до карток у сітці. Без нього картки з різним вмістом мають різну висоту — сітка виглядає "рваною". ЗАВЖДИ використовуй `h-100` у card-сітках.
---

**Чому `h-100` — обов'язковий у card-сітках:**

У сітці карток (`row-cols-3`) кожна картка у рядку має власну висоту що залежить від вмісту. Картка з коротким текстом буде низькою, з довгим — високою. Це виглядає хаотично.

`h-100` = `height: 100%` робить кожну картку такою ж високою як її колонка. А колонка автоматично має висоту найвисокішої картки у рядку (flexbox align-items: stretch). Результат: всі картки однієї висоти.

**Клас `g-4` — gutter між картками:**

`g-4` = `gap: 24px` між картками у сітці. Bootstrap використовує CSS `gap` на flex/grid контейнері. Без `g-4` картки торкаються одна одної — немає дихання. `g-0` = без проміжків, `g-5` = великий проміжок.

## 6. Компоненти — Card

### Анатомія Card

Ця структура показує всі можливі елементи картки. Більшість з них необов'язкові: можна мати тільки `card-body`. Зверни на `.card-img-top` — він не потребує `border-radius`, Bootstrap автоматично заокруглює верхні кути зображення щоб вони збігались з `border-radius` картки.

```html
<div class="card">                          <!-- обгортка -->
    <img src="..." class="card-img-top" alt="...">  <!-- зображення зверху -->
    <div class="card-header">Заголовок</div>         <!-- шапка (необов'язково) -->
    <div class="card-body">                 <!-- основний вміст + padding -->
        <h5 class="card-title">Назва</h5>
        <h6 class="card-subtitle mb-2 text-muted">Підзаголовок</h6>
        <p class="card-text">Опис картки...</p>
        <a href="#" class="btn btn-primary">Детальніше</a>
    </div>
    <div class="card-footer text-muted">   <!-- підвал (необов'язково) -->
        <small>Оновлено: 21.05.2026</small>
    </div>
</div>
```

### Сітка карток — row-cols

`row-cols-*` — спрощений спосіб задати скільки карток у рядку. `row-cols-1 row-cols-md-2 row-cols-lg-3` = 1 картка на мобільному, 2 на планшеті, 3 на десктопі. Django шаблонний тег `{% empty %}` обробляє випадок коли список порожній — завжди додавай його до Django-шаблонів зі списками.

```html
<!-- row-cols-* → скільки карток у рядку -->
<div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    {% for note in notes %}
    <div class="col">
        <div class="card h-100">    <!-- h-100 — рівна висота всіх карток -->
            <div class="card-body">
                <h5 class="card-title">{{ note.title }}</h5>
                <p class="card-text">{{ note.content|truncatewords:20 }}</p>
            </div>
            <div class="card-footer">
                <small class="text-muted">
                    {{ note.created_at|date:"d.m.Y" }}
                </small>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="col-12">
        <div class="alert alert-info">Нотаток ще немає.</div>
    </div>
    {% endfor %}
</div>
```

**`g-4` → gap: 24px** між картками (gutter). `g-0`, `g-1`, ..., `g-5`.

### Card + Hover effect

Hover-ефект для карток — популярний патерн що дає відчуття інтерактивності. CSS `transition` забезпечує плавну анімацію. `translateY(-4px)` піднімає картку на 4px вгору. `box-shadow` посилює ефект "підняття". Зверни: клас `card-hover` написаний у власному CSS (`custom.css`), а не через Bootstrap-utilities — це правильний підхід для кастомних ефектів.

```html
<style>
.card-hover {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card-hover:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}
</style>

<div class="card card-hover border-0 shadow-sm">...</div>
```

---

----
- **🧠 Ментальна модель:** Bootstrap form-класи стилізують HTML-інпути — вони не змінюють ЯК форми працюють, тільки ЯК вони виглядають. Логіка форм (валідація, збереження) — все ще у Django.
- **📚 Чому це існує:** Нативні HTML-інпути без стилів виглядають по-різному у кожному браузері. `form-control` уніфікує вигляд: однаковий padding, border, border-radius, focus-ring у всіх браузерах.
- **🌐 Що Bootstrap робить під капотом:** `form-control` генерує: `display: block; width: 100%; padding: .375rem .75rem; border: 1px solid #ced4da; border-radius: .375rem; transition: border-color .15s ease-in-out, box-shadow .15s ease-in-out`. При фокусі додається синя тінь через `box-shadow`.
- **❌ Типова помилка початківця:** Покладатися ТІЛЬКИ на клієнтську валідацію браузера (`required`, `type="email"`). Вона може бути обійдена. Django-валідація у `views.py` або `forms.py` — це ЄДИНА надійна валідація.
---

**Клієнтська vs серверна валідація — критично важливо:**

```
Клієнтська (браузер): швидка, миттєва зворотня інформація, але МОЖЕ БУТИ ОБІЙДЕНА
  (будь-хто може відключити JS або відправити запит через curl/Postman)

Серверна (Django): завжди виконується, НЕМОЖЛИВО обійти — це РЕАЛЬНА валідація
  form.is_valid() у views.py перевіряє всі Django-валідатори

Bootstrap's .is-invalid class: тільки ВІЗУАЛЬНО показує Django помилки валідації
  Django передає помилки у form.errors → шаблон рендерить їх з Bootstrap-стилями
```

Правило: завжди валідуй на сервері (Django). Клієнтська валідація — це лише UX-покращення.

## 7. Компоненти — Форми

### Bootstrap Forms з django-bootstrap5

Цей шаблон показує повну Bootstrap-форму з усіма типами полів. Зверни на `needs-validation` і `novalidate` — це вмикає кастомну Bootstrap-валідацію замість нативної браузерної. `.valid-feedback` і `.invalid-feedback` показуються тільки коли форма має клас `was-validated` (додається через JS). Для Django-проєктів часто простіше використовувати `django-bootstrap5` пакет.

```html
<!-- Стандартне підключення -->
<form method="post" class="needs-validation" novalidate>
    {% csrf_token %}

    <!-- Група поля -->
    <div class="mb-3">
        <label for="id_title" class="form-label">Заголовок <span class="text-danger">*</span></label>
        <input
            type="text"
            class="form-control"
            id="id_title"
            name="title"
            placeholder="Введіть заголовок"
            required
        >
        <div class="valid-feedback">Відмінно!</div>
        <div class="invalid-feedback">Заповніть це поле.</div>
    </div>

    <!-- Textarea -->
    <div class="mb-3">
        <label for="id_content" class="form-label">Текст</label>
        <textarea
            class="form-control"
            id="id_content"
            name="content"
            rows="5"
            placeholder="Текст нотатки..."
        ></textarea>
        <div class="form-text">Необов'язкове поле.</div>
    </div>

    <!-- Select -->
    <div class="mb-3">
        <label for="id_category" class="form-label">Категорія</label>
        <select class="form-select" id="id_category" name="category">
            <option value="">Оберіть...</option>
            <option value="work">Робота</option>
            <option value="personal">Особисте</option>
        </select>
    </div>

    <!-- Checkbox -->
    <div class="mb-3 form-check">
        <input type="checkbox" class="form-check-input" id="id_public" name="public">
        <label class="form-check-label" for="id_public">Публічна нотатка</label>
    </div>

    <!-- Inline форма -->
    <div class="row g-2 align-items-center">
        <div class="col-auto">
            <input type="text" class="form-control" placeholder="Пошук...">
        </div>
        <div class="col-auto">
            <button type="submit" class="btn btn-primary">Знайти</button>
        </div>
    </div>

    <!-- Кнопки -->
    <div class="d-flex gap-2 mt-4">
        <button type="submit" class="btn btn-primary">Зберегти</button>
        <a href="{% url 'hello_app:note_list' %}" class="btn btn-outline-secondary">
            Скасувати
        </a>
    </div>
</form>
```

### Відображення Django форми через django-bootstrap5

`django-bootstrap5` — найпростіший спосіб підключити Bootstrap до Django-форм. `NoteForm.Meta.widgets` дозволяє додати Bootstrap-класи до нативних Django-віджетів. Альтернатива: використовувати `{% bootstrap_form form %}` і пакет автоматично додасть всі потрібні класи.

```python
# views.py
from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок нотатки'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5
            }),
        }
```

Тег `{% bootstrap_form form %}` автоматично рендерить всі поля з правильними Bootstrap-класами, включаючи помилки валідації. Це заощаджує десятки рядків ручного HTML для кожної форми.

```html
{# Шаблон з django-bootstrap5 #}
{% load django_bootstrap5 %}

<form method="post">
    {% csrf_token %}
    {% bootstrap_form form %}
    {% bootstrap_button "Зберегти" button_type="submit" button_class="btn-primary" %}
</form>
```

---

---
- **🧠 Ментальна модель:** Alert — це тимчасове повідомлення що говорить користувачу що щойно сталось. Зелений = добре. Червоний = погано. Жовтий = увага. Синій = інформація.
- **📚 Чому це існує:** Користувачі потребують зворотного зв'язку після дій. Зберіг нотатку? Скажи "Збережено!". Виникла помилка? Скажи "Щось пішло не так". Без alerts користувачі не знають чи їхня дія спрацювала.
- **🌐 Що Bootstrap робить під капотом:** `alert-success` = зелений фон через CSS змінні Bootstrap. `alert-dismissible` додає padding справа для кнопки закриття. `fade show` — CSS transition: opacity 0.15s. Клас `show` = opacity: 1. Без нього alert невидимий (opacity: 0).
- **❌ Типова помилка початківця:** Не налаштувати `MESSAGE_TAGS` у `settings.py`. Django за замовчуванням використовує теги `error`, але Bootstrap очікує `danger`. Без маппінгу `alert-error` не є валідним Bootstrap-класом.
---

**Django Messages → Bootstrap Alerts — як це працює:**

```
Python view: messages.success(request, 'Збережено!')
     ↓ Django Messages Framework зберігає у сесії (cookie або DB)
Template: {% for message in messages %}
     ↓ Django Messages Framework зчитує з сесії і передає у шаблон
HTML: <div class="alert alert-success">Збережено!</div>
     ↓ Браузер рендерить
Користувач бачить: зелений банер з текстом "Збережено!"
     ↓ Після прочитання — messages видаляються з сесії (one-time flash)
```

Ключове: messages — це одноразові повідомлення. Після відображення вони зникають. Якщо оновити сторінку — banner не з'явиться знову.

## 8. Компоненти — Alerts та Flash-повідомлення

### Django messages → Bootstrap alerts

Наступний Python-код показує як додати flash-повідомлення у Django view. `messages.success()`, `messages.error()` тощо зберігають повідомлення в сесії. Вони відображаються у base.html після redirect — класичний "Post-Redirect-Get" патерн.

```python
# views.py
from django.contrib import messages

def note_create(request):
    if form.is_valid():
        form.save()
        messages.success(request, 'Нотатку успішно збережено!')
        return redirect('hello_app:note_list')
    messages.error(request, 'Помилка. Перевірте форму.')
```

Цей HTML-фрагмент показує як рендерити Django messages з Bootstrap-стилями. `alert-{{ message.tags }}` підставляє Django-тег як Bootstrap-клас (`alert-success`, `alert-danger` тощо). `alert-dismissible` + `btn-close` дозволяє користувачу закрити повідомлення кліком. `fade show` — плавна анімація появи.

```html
{# base.html — відображення flash повідомлень #}
{% if messages %}
<div class="container mt-2">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close"
                data-bs-dismiss="alert"
                aria-label="Закрити">
        </button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

**Маппінг Django tags → Bootstrap classes:**

`MESSAGE_TAGS` у `settings.py` перекладає Django теги в Bootstrap-класи. Без цього налаштування `messages.error()` генерує тег `error`, але Bootstrap очікує клас `alert-danger` — і алерт не матиме правильного стилю.

```python
# settings.py
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}
```

### Статичні алерти

Статичні алерти — для постійних повідомлень (не flash). `role="alert"` — важливий ARIA атрибут: він сигналізує скрінрідеру що вміст важливий і повинен бути оголошений негайно. `alert-link` — спеціальний клас для посилань всередині alertів.

```html
<div class="alert alert-primary" role="alert">Інформація</div>
<div class="alert alert-success" role="alert">Успіх!</div>
<div class="alert alert-warning" role="alert">Увага!</div>
<div class="alert alert-danger" role="alert">Помилка!</div>

<!-- З посиланням -->
<div class="alert alert-info">
    Не знайшли нотатку?
    <a href="#" class="alert-link">Спробуй пошук</a>
</div>
```

---

---
- **🧠 Ментальна модель:** Modal — це діалогове вікно що з'являється ПОВЕРХ сторінки. Сторінка стає некліковою (backdrop). Користувач зосереджується на одній задачі — підтвердити, заповнити форму, переглянути деталі.
- **📚 Чому це існує:** Модальні вікна дозволяють виконати дію без переходу на нову сторінку. "Ти впевнений що хочеш видалити?" — не потрібна окрема сторінка підтвердження, достатньо modal.
- **🌐 Що Bootstrap робить під капотом:** Bootstrap JS додає modal-backdrop (темне накладення) прямо у `<body>`, встановлює `overflow: hidden` на `<body>` (scrollbar зникає), керує z-index щоб modal завжди був поверх всього, і відстежує клік за межами modal щоб закрити його.
- **❌ Типова помилка початківця:** Розміщувати Modal всередині `.container`, `.card` або будь-якого елемента з `overflow: hidden` або `position: relative`. Modal буде обрізаний або матиме проблеми з z-index. ЗАВЖДИ перед `</body>`.
---

**Чому Modal ОБОВ'ЯЗКОВО на верхньому рівні DOM:**

```
Якщо Modal знаходиться всередині:
.container → overflow: hidden → Modal ОБРІЗАЄТЬСЯ!
.card → z-index проблеми → Modal з'являється ЗА іншими елементами!
position: relative батько → Modal позиціонується відносно батька, не viewport!

Рішення: ЗАВЖДИ розміщуй Modal як прямого нащадка <body>
```

**Lifecycle Modal — від кліку до відображення:**

```
data-bs-toggle="modal" клікнуто
     ↓
Bootstrap JS знаходить data-bs-target="#deleteModal"
     ↓
Запускається подія show.bs.modal (можна скасувати через e.preventDefault())
     ↓
Bootstrap додає клас 'show' → CSS transition починається (opacity: 0 → 1)
     ↓
Bootstrap додає modal-backdrop у <body>
     ↓
Bootstrap встановлює body { overflow: hidden } (scrollbar зникає)
     ↓
Bootstrap запускає подію shown.bs.modal (transition ЗАВЕРШЕНО)
     ↓
Користувач бачить modal, сторінка покрита напівпрозорим backdrop
```

## 9. Компоненти — Modal

### Архітектура Modal

Структура Modal з 3 шарів: `modal` (зовнішня обгортка, позиціонування), `modal-dialog` (центрування, розмір), `modal-content` (реальний вигляд — білий прямокутник). Ця 3-рівнева структура необхідна для правильного центрування і анімації.

```
Modal ЗАВЖДИ розміщується на верхньому рівні DOM (прямо перед </body>)
→ уникає конфліктів z-index та overflow: hidden від батьків
→ Bootstrap підтримує лише ОДИН активний modal одночасно
→ При відкритті: body отримує overflow: hidden (scrollbar зникає)
```

Наступний код показує повну структуру Modal з шапкою, тілом і підвалом. Зверни на `data-bs-toggle="modal"` і `data-bs-target="#deleteModal"` на кнопці — вони повинні точно відповідати `id="deleteModal"` на Modal-обгортці.

```html
<!-- Кнопка що відкриває modal -->
<button
    type="button"
    class="btn btn-danger"
    data-bs-toggle="modal"
    data-bs-target="#deleteModal"
>
    Видалити нотатку
</button>

<!-- Modal — розміщуємо перед </body> -->
<div
    class="modal fade"
    id="deleteModal"
    tabindex="-1"
    aria-labelledby="deleteModalLabel"
    aria-hidden="true"
>
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">

            <!-- Шапка -->
            <div class="modal-header">
                <h5 class="modal-title" id="deleteModalLabel">
                    Підтвердження видалення
                </h5>
                <button type="button" class="btn-close"
                        data-bs-dismiss="modal"
                        aria-label="Закрити">
                </button>
            </div>

            <!-- Тіло -->
            <div class="modal-body">
                <p>Ви впевнені що хочете видалити нотатку
                   <strong id="noteTitle"></strong>?
                </p>
                <p class="text-muted">Цю дію неможливо скасувати.</p>
            </div>

            <!-- Підвал -->
            <div class="modal-footer">
                <button type="button"
                        class="btn btn-secondary"
                        data-bs-dismiss="modal">
                    Скасувати
                </button>
                <form method="post" id="deleteForm">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">
                        Так, видалити
                    </button>
                </form>
            </div>

        </div>
    </div>
</div>
```

### Modal з динамічними даними через JS

Одна Modal для багатьох елементів — поширений патерн. Замість того щоб створювати окремий Modal для кожної нотатки, ми маємо один Modal і динамічно наповнюємо його даними через JavaScript. Подія `show.bs.modal` надає `event.relatedTarget` — кнопку що відкрила Modal, і ми зчитуємо з неї `data-*` атрибути.

```javascript
// Передаємо дані з кнопки в modal
const deleteModal = document.getElementById('deleteModal');
deleteModal.addEventListener('show.bs.modal', function(event) {
    // event.relatedTarget — кнопка що відкрила modal
    const button = event.relatedTarget;
    const noteId = button.getAttribute('data-note-id');
    const noteTitle = button.getAttribute('data-note-title');

    // Оновлюємо вміст modal
    document.getElementById('noteTitle').textContent = noteTitle;
    document.getElementById('deleteForm').action = `/notes/${noteId}/delete/`;
});
```

Кнопки зберігають ID і назву нотатки у `data-*` атрибутах. Коли будь-яка кнопка відкриває Modal — JavaScript зчитує ці дані і наповнює Modal правильною інформацією.

```html
<!-- Кнопки у списку нотаток -->
{% for note in notes %}
<button
    type="button"
    class="btn btn-danger btn-sm"
    data-bs-toggle="modal"
    data-bs-target="#deleteModal"
    data-note-id="{{ note.pk }}"
    data-note-title="{{ note.title }}"
>
    Видалити
</button>
{% endfor %}
```

### Розміри Modal

Bootstrap надає 7 розмірів Modal і 2 модифікатори поведінки. `modal-dialog-centered` — вертикальне центрування (без нього Modal прив'язаний до верху). `modal-dialog-scrollable` — корисно коли вміст Modal може бути довгим (прокрутка всередині Modal, а не сторінки).

```html
<div class="modal-dialog modal-sm">        <!-- Малий -->
<div class="modal-dialog">                 <!-- Стандартний -->
<div class="modal-dialog modal-lg">        <!-- Великий -->
<div class="modal-dialog modal-xl">        <!-- Дуже великий -->
<div class="modal-dialog modal-fullscreen"> <!-- На весь екран -->
<div class="modal-dialog modal-dialog-centered">  <!-- По центру вертикально -->
<div class="modal-dialog modal-dialog-scrollable"> <!-- Прокрутка всередині -->
```

---

---
- **🧠 Ментальна модель:** Bootstrap JS має ДВА API — декларативний (HTML атрибути) і програматичний (JavaScript). Декларативний = "опиши що хочеш у HTML". Програматичний = "керуй поведінкою через код".
- **📚 Чому це існує:** Декларативний API (data-bs-*) — для простих випадків без JS. Програматичний JS API — для динамічних сценаріїв де поведінку потрібно контролювати з коду (відкрити Modal після завантаження AJAX, закрити після успішного submit тощо).
- **🌐 Що Bootstrap робить під капотом:** При завантаженні сторінки Bootstrap JS читає весь DOM і автоматично ініціалізує компоненти з `data-bs-*` атрибутами. Це відбувається через `DOMContentLoaded` listener. Tooltip і Popover — виняток: вони потребують явної ініціалізації через JS.
- **❌ Типова помилка початківця:** Використовувати `data-bs-toggle="tooltip"` без JavaScript-ініціалізації. На відміну від Modal і Collapse, Tooltip і Popover ОБОВ'ЯЗКОВО потребують виклику `new bootstrap.Tooltip(element)`.
---

**Data API = HTML-керований підхід:**

Пиши HTML атрибути, Bootstrap JS читає їх і автоматично додає поведінку. Не потрібно писати JS. Це підхід "convention over configuration": Bootstrap знає стандартні патерни і бере всю роботу на себе.

**JS API = програмний підхід:**

Створюй instances і викликай методи програматично. Потрібно коли:
- Поведінка залежить від стану застосунку (відкрити Modal після AJAX-запиту)
- Треба відреагувати на lifecycle events (`shown.bs.modal`)
- Потрібно знищити instance і уникнути memory leaks (`modal.dispose()`)

## 10. Bootstrap JavaScript — Data API та Event Lifecycle

### Декларативний підхід — Data API

Bootstrap керується прямо в HTML через `data-bs-*` атрибути — **без написання JS**:

Наступний блок показує всі основні `data-bs-*` атрибути. Зверни: Tooltip і Popover відмічені як такі що "потребують JS ініціалізації" — це єдиний виняток з правила "data attributes автоматично ініціалізуються".

```html
<!-- Modal -->
<button data-bs-toggle="modal" data-bs-target="#myModal">Відкрити</button>

<!-- Collapse (акордеон) -->
<button data-bs-toggle="collapse" data-bs-target="#collapseContent">Розгорнути</button>
<div class="collapse" id="collapseContent">Прихований вміст</div>

<!-- Dropdown -->
<button class="btn dropdown-toggle" data-bs-toggle="dropdown">Меню ▼</button>

<!-- Dismiss (закрити alert/modal) -->
<button data-bs-dismiss="alert" class="btn-close"></button>

<!-- Tooltip (потребує JS ініціалізації!) -->
<button data-bs-toggle="tooltip" data-bs-placement="top" title="Підказка">
    Hover me
</button>

<!-- Popover (потребує JS ініціалізації!) -->
<button data-bs-toggle="popover" data-bs-content="Вміст поповера">
    Клікни
</button>

<!-- Carousel autoplay -->
<div id="myCarousel" class="carousel slide" data-bs-ride="carousel">
```

### Програматичний підхід — JS API

Програматичний API дозволяє повністю контролювати Bootstrap-компоненти з JavaScript. `new bootstrap.Modal(el)` — створює instance. `.show()`, `.hide()`, `.toggle()` — методи керування. `.dispose()` — ОБОВ'ЯЗКОВО викликай коли прибираєш елемент з DOM, щоб уникнути memory leak.

```javascript
// Ініціалізація (обов'язкова для Tooltip і Popover)
const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
tooltips.forEach(el => new bootstrap.Tooltip(el));

const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
popovers.forEach(el => new bootstrap.Popover(el));

// Керування modal програматично
const modal = new bootstrap.Modal(document.getElementById('myModal'));
modal.show();
modal.hide();
modal.toggle();
modal.dispose(); // очистити DOM, уникнути memory leak

// Керування collapse
const collapse = new bootstrap.Collapse(document.getElementById('myCollapse'));
collapse.show();
collapse.hide();
```

### Event Lifecycle — хуки подій

Bootstrap компоненти генерують події на кожному кроці свого lifecycle. Це дозволяє підключитись до будь-якого моменту і виконати кастомну логіку. `show.bs.modal` (без "n") = перед, `shown.bs.modal` (з "n") = після. Різниця критична: якщо потрібно зробити focus на input у Modal — роби це у `shown`, не у `show` (DOM ще не видимий).

```javascript
const modalEl = document.getElementById('myModal');

// show.bs.modal → спрацьовує одразу при виклику .show()
modalEl.addEventListener('show.bs.modal', function(e) {
    console.log('Modal починає відкриватись');
    // e.preventDefault() → скасує відкриття
});

// shown.bs.modal → спрацьовує ПІСЛЯ завершення анімації
modalEl.addEventListener('shown.bs.modal', function(e) {
    console.log('Modal повністю відкритий, анімація завершена');
    // Тут безпечно робити focus на input всередині modal
    document.getElementById('myInput').focus();
});

// hide.bs.modal → перед закриттям
modalEl.addEventListener('hide.bs.modal', function(e) {
    console.log('Modal починає закриватись');
});

// hidden.bs.modal → після закриття
modalEl.addEventListener('hidden.bs.modal', function(e) {
    console.log('Modal закритий');
    // Очистити форму всередині
    document.getElementById('myForm').reset();
});
```

**Таблиця подій для всіх компонентів:**

| Компонент | Prefix | Події |
|-----------|--------|-------|
| Modal | `modal` | `show`, `shown`, `hide`, `hidden`, `hidePrevented` |
| Collapse | `collapse` | `show`, `shown`, `hide`, `hidden` |
| Dropdown | `dropdown` | `show`, `shown`, `hide`, `hidden` |
| Tooltip | `tooltip` | `show`, `shown`, `hide`, `hidden`, `inserted` |
| Tab | `tab` | `show`, `shown`, `hide`, `hidden` |
| Carousel | `carousel` | `slide`, `slid` |
| Toast | `toast` | `show`, `shown`, `hide`, `hidden` |

### Popper.js — динамічне позиціонування

Bootstrap використовує **Popper.js** для Dropdown, Tooltip, Popover:

```
Без Popper: dropdown відкривається вниз → виходить за межі екрану
З Popper: автоматично розраховує куди "відкрити" щоб влізло у viewport
```

Popper.js вже включений у `bootstrap.bundle.min.js`. Якщо підключаєш Bootstrap окремо — потрібно додати Popper окремо перед Bootstrap JS.

```html
<!-- bootstrap.bundle.min.js вже включає Popper.js -->
<script src="bootstrap.bundle.min.js"></script>

<!-- АБО окремо: -->
<script src="popper.min.js"></script>
<script src="bootstrap.min.js"></script>
```

**Увага:** Dropdown у `.navbar` — Popper **не використовується**.
Статичне позиціонування достатнє всередині navbar.

---

---
- **🧠 Ментальна модель:** ARIA (Accessible Rich Internet Applications) — це "прихований шар" HTML, невидимий для очей але зрозумілий скрінрідерам. Уяви що скрінрідер — сліпий, але дуже розумний читач: він читає текст і ARIA-підказки щоб розповісти про структуру сторінки.
- **📚 Чому це існує:** Веб-сайти мають бути доступними для людей з обмеженими можливостями (близько 15% населення). Закони у багатьох країнах вимагають веб-доступності (WCAG стандарт). Bootstrap допомагає дотримуватись цих вимог з коробки.
- **🌐 Що Bootstrap робить під капотом:** Bootstrap JS автоматично керує ARIA атрибутами на динамічних компонентах. Наприклад, при відкритті Dropdown Bootstrap JS змінює `aria-expanded` з `false` на `true`. Ти описуєш початковий стан, Bootstrap підтримує актуальність.
- **❌ Типова помилка початківця:** Думати що достатньо просто зробити щоб виглядало добре. Кнопка з іконкою без тексту (`<button><svg/></button>`) — для скрінрідера це мовчання. ЗАВЖДИ додавай `aria-label` або `visually-hidden` текст.
---

**Чому Bootstrap включає ARIA:**

Недостатньо щоб сайт ВИГЛЯДАВ доступним. Скрінрідерам потрібні СЕМАНТИЧНІ підказки:
- `aria-current="page"` — яка сторінка зараз активна
- `aria-expanded="true/false"` — чи відкритий dropdown/collapse
- `aria-labelledby="id"` — що є заголовком цього блоку
- `aria-hidden="true"` — цей елемент декоративний, ігноруй

**Патерн `visually-hidden` — невидимий для очей, видимий для скрінрідерів:**

CSS позиціонує елемент за межами viewport (1×1 піксель, обрізаний) — він є в DOM і доступний для скрінрідерів, але невидимий користувачам. Це стандартний патерн для додавання контексту до іконкових кнопок.

## 11. Accessibility у Bootstrap

### ARIA стандарти — обов'язкові атрибути

Наступний блок показує всі ключові ARIA атрибути у Bootstrap-компонентах. Запам'ятай правило: кожен інтерактивний елемент (кнопка, посилання, форма) повинен мати зрозумілий текстовий опис для скрінрідерів — або видимий, або через `aria-label`/`visually-hidden`.

```html
<!-- Navbar: aria-current для активної сторінки -->
<a class="nav-link active" aria-current="page" href="/">Головна</a>
<!-- Тільки .active класу недостатньо — скрінрідер не побачить -->

<!-- Modal: aria-labelledby + aria-hidden -->
<div class="modal" aria-labelledby="modalTitle" aria-hidden="true">
    <h5 id="modalTitle">Заголовок Modal</h5>
</div>
<!-- aria-hidden="true" ховає від скрінрідера коли закрито -->

<!-- Dropdown: aria-expanded -->
<button data-bs-toggle="dropdown" aria-expanded="false">Меню</button>
<!-- Bootstrap автоматично змінює aria-expanded на true при відкритті -->

<!-- Кнопка-іконка: aria-label -->
<button class="btn-close" aria-label="Закрити"></button>
<button class="btn btn-primary">
    <i class="bi bi-heart" aria-hidden="true"></i>  <!-- іконка декоративна -->
    <span class="visually-hidden">Додати в обране</span>  <!-- текст для скрінрідера -->
</button>

<!-- Pagination: nav + aria-label -->
<nav aria-label="Пагінація">
    <ul class="pagination">
        <li class="page-item"><a class="page-link" href="#">1</a></li>
        <li class="page-item active">
            <a class="page-link" href="#" aria-current="page">2</a>
        </li>
    </ul>
</nav>

<!-- Alert: role="alert" для aria-live оголошення -->
<div class="alert alert-danger" role="alert">
    Помилка збереження!
</div>
```

### visually-hidden — текст тільки для скрінрідерів

Клас `visually-hidden` — стандартний спосіб додати контекст для скрінрідерів без зміни зовнішнього вигляду. Ключовий трюк: `position: absolute; width: 1px; height: 1px` — елемент займає місце в DOM але не видний на екрані. `clip: rect(0,0,0,0)` додатково обрізає будь-які можливі артефакти рендерингу.

```html
<!-- Кнопка з іконкою без видимого тексту -->
<button class="btn btn-danger">
    <svg aria-hidden="true">...</svg>
    <span class="visually-hidden">Видалити нотатку</span>
</button>

<!-- Заголовок секції що не потрібен візуально -->
<h2 class="visually-hidden">Список нотаток</h2>

<!-- CSS що стоїть за visually-hidden: -->
/* position: absolute; width: 1px; height: 1px;
   padding: 0; margin: -1px; overflow: hidden;
   clip: rect(0,0,0,0); white-space: nowrap; border: 0; */
```

---

## 12. Anti-patterns — Типові помилки

### Grid Anti-patterns

Ці антипатерни ламають Bootstrap Grid. Читай уважно — найпоширеніші помилки що зустрічаються у проєктах початківців.

```html
<!-- ❌ Контент напряму в .row -->
<div class="row">
    <p>Текст напряму в row</p>  ← ламає negative margin математику
</div>

<!-- ❌ Вкладені контейнери -->
<div class="container">
    <div class="container">    ← подвійний padding
    </div>
</div>

<!-- ❌ Дублювання HTML для мобільних/десктопів -->
<div class="d-block d-md-none"> <!-- мобільна версія -->
    <div class="card">...</div>
</div>
<div class="d-none d-md-block"> <!-- десктопна версія -->
    <div class="card">...</div>
</div>
<!-- ✅ Правильно: один HTML, адаптивні класи -->
<div class="col-12 col-md-6">...</div>

<!-- ❌ Горизонтальний скрол через відсутній .container -->
<div class="row">  ← row без container → negative margin виходить за екран
    <div class="col-6">...</div>
</div>
<!-- ✅ Завжди огортай .row у .container -->
```

### Modal Anti-patterns

Ці антипатерни специфічні для Modal. Найважливіше правило: Modal завжди перед `</body>`. Другий поширений баг: два відкритих Modal одночасно — Bootstrap не підтримує це і поведінка непередбачувана.

```html
<!-- ❌ Modal всередині flex/overflow контейнера -->
<div style="overflow: hidden">
    <div class="modal">...</div>  ← modal буде обрізаний!
</div>

<!-- ✅ Modal перед </body> -->
<body>
    <div class="container">...</div>
    <!-- Modals завжди тут: -->
    <div class="modal" id="myModal">...</div>
    <script src="bootstrap.bundle.min.js"></script>
</body>

<!-- ❌ Два активних modals одночасно — Bootstrap не підтримує -->
<!-- ❌ Modal всередині Modal — UX і backdrop ламаються -->
```

### JavaScript Anti-patterns

Memory leaks і неправильна ініціалізація — найпоширеніші JS помилки з Bootstrap.

```javascript
// ❌ Не знищений Modal instance → memory leak
const modal = new bootstrap.Modal(el);
modal.show();
// ... видалили el з DOM але не викликали modal.dispose()

// ✅ Правильне знищення
modal.dispose();

// ❌ Tooltip/Popover без ініціалізації
// data-bs-toggle="tooltip" не спрацює без:
// new bootstrap.Tooltip(element)

// ❌ Dropdown у responsive table
// overflow-y: hidden від .table-responsive обріже dropdown menu!
```

---

---
- **🧠 Ментальна модель:** Цей повний приклад — як складальна лінія: `base.html` = каркас заводу (навігація, flash messages, footer), `note_list.html` = конкретна продукція (Grid карток + Modal). Кожна деталь яку ти вивчив — Grid, Navbar, Card, Modal, Flash Messages — збирається тут разом.
- **📚 Чому це існує:** Навчальні приклади часто показують компоненти окремо. Цей приклад показує як всі вони взаємодіють у реальному Django-проєкті: наслідування шаблонів, передача JS через блоки, один Modal для багатьох елементів.
- **🌐 Що Bootstrap робить під капотом:** `d-flex flex-column min-vh-100` на `<body>` + `flex-grow-1` на `<main>` = "sticky footer" патерн. Footer завжди внизу viewport навіть якщо контенту мало. `sticky-top` на navbar = navbar прикріплений до верху при прокрутці.
- **❌ Типова помилка початківця:** Не розуміти що `{% block extra_js %}{% endblock %}` у base.html дозволяє дочірнім шаблонам додавати сторінко-специфічний JavaScript. Без цього блоку JavaScript для Modal у `note_list.html` не буде включений у `base.html`.
---

**Як читати цей приклад:**

1. Починай з `base.html` — він визначає загальну структуру: navbar зверху, flash messages, main-контент у середині, footer внизу
2. `note_list.html` розширює (`{% extends %}`) `base.html` і заповнює `{% block content %}` своїм вмістом
3. Зверни на `{% block extra_js %}` в кінці `note_list.html` — це місце де сторінко-специфічний JavaScript передається у base-шаблон
4. Modal знаходиться всередині `{% block content %}` але Bootstrap JS знає як його правильно позиціонувати через z-index

## 13. Повний приклад — Django + Bootstrap 5

### Структура проєкту

```
django_bootstrap_project/
├── hello_project/
│   ├── settings.py    ← django-bootstrap5 в INSTALLED_APPS
│   └── urls.py
└── hello_app/
    ├── views.py
    ├── urls.py
    ├── models.py
    └── templates/
        └── hello_app/
            ├── base.html          ← Bootstrap navbar + структура
            ├── note_list.html     ← Grid сітка карток
            ├── note_detail.html   ← Одна нотатка
            └── note_form.html     ← Форма з Bootstrap
```

### base.html

`base.html` — фундамент всього Django-проєкту. Зверни на: 1) `d-flex flex-column min-vh-100` на body + `flex-grow-1` на main = footer завжди внизу. 2) `sticky-top` на navbar = navbar прикріплений при прокрутці. 3) Flash messages між navbar і main — їх завжди видно одразу після дії. 4) `{% block extra_js %}` перед `</body>` — для сторінко-специфічного JS.

```html
{% load static %}
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Нотатки{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
          rel="stylesheet">
    <link rel="stylesheet" href="{% static 'css/custom.css' %}">
</head>
<body class="d-flex flex-column min-vh-100">

    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="{% url 'hello_app:index' %}">
                📝 Нотатки
            </a>
            <button class="navbar-toggler" type="button"
                    data-bs-toggle="collapse" data-bs-target="#navMenu">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navMenu">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'index' %}active{% endif %}"
                           href="{% url 'hello_app:index' %}">Головна</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {% if request.resolver_match.url_name == 'note_list' %}active{% endif %}"
                           href="{% url 'hello_app:note_list' %}">Нотатки</a>
                    </li>
                </ul>
                <a href="{% url 'hello_app:note_create' %}" class="btn btn-outline-light btn-sm">
                    + Нова нотатка
                </a>
            </div>
        </div>
    </nav>

    <!-- Flash Messages -->
    {% if messages %}
    <div class="container mt-3">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Main content (flex: 1 → footer внизу) -->
    <main class="container py-4 flex-grow-1">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-dark text-light py-3 mt-auto">
        <div class="container text-center">
            <small>© 2026 Нотатки | Django + Bootstrap 5</small>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### note_list.html

`note_list.html` — дочірній шаблон що розширює `base.html`. Зверни: 1) Grid карток з `row-cols-*` і `h-100`. 2) `{% empty %}` — порожній стан. 3) Modal для підтвердження видалення — з динамічними даними через JS. 4) `{% block extra_js %}` з JavaScript що слухає `show.bs.modal` і заповнює Modal даними з кнопки.

```html
{% extends 'hello_app/base.html' %}

{% block title %}Мої нотатки{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 mb-0">Мої нотатки</h1>
    <a href="{% url 'hello_app:note_create' %}" class="btn btn-primary">
        + Нова нотатка
    </a>
</div>

{% if notes %}
<div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
    {% for note in notes %}
    <div class="col">
        <div class="card h-100 border-0 shadow-sm">
            <div class="card-body">
                <h5 class="card-title">
                    <a href="{% url 'hello_app:note_detail' pk=note.pk %}"
                       class="text-decoration-none text-dark">
                        {{ note.title }}
                    </a>
                </h5>
                {% if note.content %}
                <p class="card-text text-muted">
                    {{ note.content|truncatewords:20 }}
                </p>
                {% endif %}
            </div>
            <div class="card-footer bg-transparent border-0 d-flex justify-content-between align-items-center">
                <small class="text-muted">
                    <i class="bi bi-clock"></i>
                    {{ note.created_at|date:"d.m.Y" }}
                </small>
                <div class="d-flex gap-1">
                    <a href="{% url 'hello_app:note_detail' pk=note.pk %}"
                       class="btn btn-outline-primary btn-sm">
                        Читати
                    </a>
                    <button
                        type="button"
                        class="btn btn-outline-danger btn-sm"
                        data-bs-toggle="modal"
                        data-bs-target="#deleteModal"
                        data-note-id="{{ note.pk }}"
                        data-note-title="{{ note.title }}"
                    >
                        ✕
                    </button>
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% else %}
<div class="text-center py-5">
    <p class="lead text-muted">Нотаток ще немає.</p>
    <a href="{% url 'hello_app:note_create' %}" class="btn btn-primary btn-lg">
        Створити першу нотатку
    </a>
</div>
{% endif %}

<!-- Delete Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1"
     aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="deleteModalLabel">Видалення нотатки</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                Видалити нотатку <strong id="modalNoteTitle"></strong>?
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" data-bs-dismiss="modal">Скасувати</button>
                <form method="post" id="deleteForm">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">Видалити</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
const deleteModal = document.getElementById('deleteModal');
deleteModal.addEventListener('show.bs.modal', function(e) {
    const btn = e.relatedTarget;
    document.getElementById('modalNoteTitle').textContent = btn.dataset.noteTitle;
    document.getElementById('deleteForm').action = `/notes/${btn.dataset.noteId}/delete/`;
});
</script>
{% endblock %}
```

---

## 14. Питання для самоперевірки

1. Чому `<div class="row">` завжди має бути всередині `.container`?
2. Що означає `col-12 col-md-6 col-lg-4`? Опиши поведінку на 3 розмірах екрану.
3. Чому `.btn-danger` недостатньо для accessibility? Що треба додати?
4. Де в DOM треба розміщувати `<div class="modal">`? Чому?
5. `data-bs-toggle="tooltip"` не працює. Чому? Що треба зробити?
6. Яка різниця між `show.bs.modal` і `shown.bs.modal`?
7. Навіщо Bootstrap використовує від'ємний `margin` на `.row`?
8. Коли використовувати `container-fluid` замість `container`?
9. Що таке Layout Thrashing і як він пов'язаний з Bootstrap JS?
10. Чому Bootstrap Dropdown не відкривається по hover? Як це правильно?
