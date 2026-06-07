# Django Network Architecture — Система знань

> Цей файл — головна карта навчання. Починай тут.
> Матеріал організований від фундаменту мережі до продакшен-архітектури Django.

---

## Карта навчання

```
РІВЕНЬ 1: Мережевий фундамент
    → Що таке Інтернет
    → IP, DNS, TCP, HTTP, HTTPS
    → Sockets, Ports, Client/Server

РІВЕНЬ 2: Як запит доходить до Python
    → Nginx → WSGI/ASGI → Django
    → Повний stack trace запиту

РІВЕНЬ 3: Django як система
    → Структура проєкту
    → MVT архітектура
    → Request Lifecycle

РІВЕНЬ 4: Компоненти Django
    → URL Routing
    → Views (FBV/CBV)
    → Templates (DTL)
    → ORM + Migrations

РІВЕНЬ 5: Продакшн архітектура
    → Nginx + Gunicorn + Docker
    → PostgreSQL + Redis + Celery
    → Scaling, Security, Deployment
```

---

## Частина 1 — Мережевий фундамент

### Обов'язково прочитати перед Django

| Файл | Що дає |
|------|--------|
| [network_foundation.md](network_foundation.md) | Системне розуміння Інтернету: IP, DNS, TCP, HTTP, HTTPS, REST API |
| [network_mermaid.md](network_mermaid.md) | Візуальні схеми: DNS resolving, TCP handshake, TLS, повний Browser→Server lifecycle |

### Ключові концепції

- **IP-адреса** — унікальний ідентифікатор комп'ютера в мережі
- **DNS** — перекладає `github.com` в `140.82.121.4`
- **TCP** — гарантована доставка пакетів (handshake, порядкові номери)
- **Port** — вказує до якої *програми* йде трафік (80→Nginx, 5432→PostgreSQL)
- **HTTP** — текстовий протокол: метод + шлях + заголовки + тіло
- **HTTPS** — HTTP + TLS шифрування
- **Stateless** — HTTP не пам'ятає між запитами → Cookies + Sessions
- **Socket** — двонаправлена точка з'єднання між програмами

---

## Частина 2 — Як запит доходить до Python

### Повний шлях HTTP-запиту

```
Браузер
  │
  │ DNS: example.com → 203.0.113.10
  │ TCP + TLS Handshake
  │ HTTP GET /products/
  ▼
Nginx (Reverse Proxy :443)
  │ Статичний файл? → роздає з диску (CSS, JS, PNG)
  │ Динамічний запит? → forwarding
  ▼
Gunicorn (Process Manager)
  │ Управляє Python-воркерами
  ▼
Uvicorn Worker (ASGI) або uWSGI (WSGI)
  │ HTTP байти → Python dict (environ)
  ▼
Django Application
  │ Middleware → URL Dispatcher → View → ORM → Template
  ▼
PostgreSQL / Redis
  │ SQL запит → дані
  ▼
HTTP Response → Gunicorn → Nginx → Браузер
```

### Документація

| Файл | Що дає |
|------|--------|
| [django_architecture.md](django_architecture.md) | Загальний огляд Django як системи — MVT, middleware, ORM, WSGI/ASGI, production stack |
| [django_mermaid.md](django_mermaid.md) | 15 архітектурних схем: lifecycle, middleware chain, ORM, production deployment |

---

## Частина 3 — Структура Django-проєкту

| Файл | Що дає |
|------|--------|
| [DJANGO_PROJECT_STRUCTURE.md](DJANGO_PROJECT_STRUCTURE.md) | Кожен файл Django з точною роллю, помилками і ментальними моделями |

### Швидка карта файлів

| Файл | Роль | Рівень |
|------|------|--------|
| `manage.py` | CLI оркестратор | Системний |
| `settings.py` | Центральна конфігурація | Системний |
| `wsgi.py` / `asgi.py` | Точка входу для серверів | Системний |
| `urls.py` | Маршрутизатор запитів | Логіка |
| `views.py` | Бізнес-логіка (контролер) | Логіка |
| `apps.py` | Реєстрація модуля | Логіка |
| `models.py` | Схема БД (ORM) | Дані |
| `migrations/` | Версії схеми БД | Дані |
| `admin.py` | Адмін-інтерфейс | Дані |
| `templates/` | HTML-шаблони | Презентація |
| `static/` | CSS, JS, зображення | Презентація |

---

## Частина 4 — Команди та Lifecycle

| Файл | Що дає |
|------|--------|
| [DJANGO_COMMAND_SYSTEM.md](DJANGO_COMMAND_SYSTEM.md) | Таблиця всіх команд + покроковий lifecycle від нуля до деплою |
| [DJANGO_MIGRATIONS.md](DJANGO_MIGRATIONS.md) | Механіка міграцій, граф залежностей, CI/CD |

### Критичний порядок команд

```bash
# Новий проєкт
django-admin startproject myproject
python manage.py startapp myapp
# → реєструй в INSTALLED_APPS

# Цикл розробки
# (зміни models.py)
python manage.py makemigrations   # фіксує план
python manage.py migrate          # застосовує до БД

# Адмін
python manage.py createsuperuser

# Розробка
python manage.py runserver

# Перед деплоєм
python manage.py check --deploy
python manage.py collectstatic
```

---

## Частина 5 — Компоненти Django

### URL Routing

| Файл | Що дає |
|------|--------|
| [Django_URL_Routing.md](Django_URL_Routing.md) | URL Dispatcher, path converters, GET/POST params, Forms, ModelForms, CreateView |

**Ключові концепції:**
- Пошук маршруту — **зверху вниз**, зупиняється на **першому** збігу
- `include()` — розбиває маршрути на ізольовані модулі
- `<int:pk>`, `<str:username>` — захоплюють змінні з URL
- Статичні маршрути мають стояти **вище** динамічних

---

### Views

| Файл | Що дає |
|------|--------|
| [Django_Views.md](Django_Views.md) | FBV vs CBV, Generic Views (ListView, DetailView, CreateView), lifecycle |

**Ключові концепції:**
- View — центральний оркестратор: отримує запит → запитує БД → повертає відповідь
- FBV (Function-Based Views) — прості, явні, гнучкі
- CBV (Class-Based Views) — ООП, успадкування, менше дублювання
- Generic Views — `ListView`, `DetailView`, `CreateView` автоматизують CRUD

---

### Templates (DTL)

| Файл | Що дає |
|------|--------|
| [Django_Templates.md](Django_Templates.md) | DTL синтаксис, context system, security (XSS), template inheritance |

**Ключові концепції:**
- `{{ variable }}` — виведення змінних (з автоматичним HTML-екрануванням)
- `{% tag %}` — логіка: `for`, `if`, `extends`, `block`, `url`, `csrf_token`
- `{{ var|filter }}` — трансформація: `|date`, `|truncatewords`, `|lower`
- Template inheritance: `base.html` → дочірні шаблони через `{% extends %}`

---

### ORM та База даних

| Файл | Що дає |
|------|--------|
| [Django_ORM.md](Django_ORM.md) | QuerySet API, N+1 проблема, транзакції, MVCC, production пастки |

**Ключові концепції:**
- QuerySet — **лінивий**: SQL виконується лише при ітерації
- `select_related` — JOIN на рівні SQL (для ForeignKey)
- `prefetch_related` — окремий запит + Python join (для ManyToMany)
- N+1 проблема — 1 запит на список + N запитів у циклі → катастрофа
- `transaction.atomic()` — атомарні операції з БД
- MVCC — PostgreSQL зберігає версії рядків для ізоляції транзакцій

---

### Міграції

| Файл | Що дає |
|------|--------|
| [DJANGO_MIGRATIONS.md](DJANGO_MIGRATIONS.md) | Механіка міграцій, граф залежностей, типові проблеми |

---

### Services, Selectors & Serializers

| Файл | Що дає |
|------|--------|
| [DJANGO_SERVICES_SELECTORS.md](DJANGO_SERVICES_SELECTORS.md) | Бізнес-шар: Services (мутації), Selectors (читання), Serializers як transport boundary |
| [DJANGO_SERVICES.md](DJANGO_SERVICES.md) | Тільки `services.py`: stateless функції, транзакції, `on_commit`, side effects, шаблони |
| [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) | Тільки `selectors.py`: CQRS-light, named queries, N+1, ORM-оптимізації, шаблони |
| [DJANGO_SERIALIZERS.md](DJANGO_SERIALIZERS.md) | Тільки `serializers.py`: Input/Output, `validate()`, поля, pure Python функція, помилки |
| [DJANGO_TASKS.md](DJANGO_TASKS.md) | Тільки `tasks.py`: Celery, broker, retry, `on_commit`, ідемпотентність, шаблони |

**Ключові концепції:**
- `services.py` — business logic, `@transaction.atomic`, `on_commit` для side effects
- `selectors.py` — read-only ORM queries, `select_related`, `prefetch_related`, CQRS-light
- `InputSerializer` / `OutputSerializer` — явні контракти замість `ModelSerializer`
- Service не знає HTTP — викликається з View, Celery, CLI однаково
- N+1 централізується в Selector, а не розповзається по Views і Tasks

**Ключові концепції:**
- `makemigrations` — генерує Python-план змін (не змінює БД)
- `migrate` — виконує SQL (змінює БД)
- Граф залежностей — міграції виконуються в правильному порядку автоматично
- Файли міграцій — фіксуються в Git разом з кодом

---

## Частина 6 — Продакшн архітектура

### Стек технологій

| Компонент | Роль |
|-----------|------|
| **Nginx** | Reverse proxy, SSL, роздача static файлів |
| **Gunicorn** | Process manager для Python-воркерів |
| **Uvicorn** | ASGI-воркер з event loop (async) |
| **uWSGI** | WSGI-воркер (sync, traditional) |
| **PostgreSQL** | Основна реляційна база даних |
| **Redis** | Кеш, сесії, Celery broker |
| **Celery** | Фонові задачі (email, звіти, обробка) |
| **Docker** | Ізоляція та відтворюваність середовища |

### WSGI vs ASGI

| | WSGI | ASGI |
|-|------|------|
| **Синхронність** | Синхронний | Асинхронний |
| **Воркер** | 1 запит на воркер | Тисячі корутин на воркер |
| **Blocking** | Так — очікує БД | Ні — `await` звільняє воркер |
| **WebSockets** | Немає | Так |
| **Сервер** | Gunicorn + uWSGI | Uvicorn + Daphne |
| **Коли** | Традиційні сайти | API, real-time, high-load |

---

## Типові помилки — Зведена таблиця

| Помилка | Компонент | Наслідок | Рішення |
|---------|-----------|----------|---------|
| N+1 запити | ORM | Тисячі SQL запитів | `select_related`, `prefetch_related` |
| Блокуючий код у View | Views/WSGI | Заморожений воркер | `async def view` + `await` |
| Логіка в Templates | Templates | Неможливо тестувати | Перенести в View або Model |
| Auth перед Session у Middleware | Middleware | Порожній `request.user` | Правильний порядок Middleware |
| `runserver` у продакшні | Deployment | Crash при навантаженні | Gunicorn + Nginx |
| Без `collectstatic` | Deployment | 404 на статику | `collectstatic` + Nginx |
| `DEBUG=True` у продакшні | Security | Витік конфігурації | `DEBUG=False` |
| Race condition на `save()` | ORM | Втрата даних | `F()` expressions |
| `atomic()` exception trap | ORM/DB | `TransactionManagementError` | Catch ЗОВНІ atomic блоку |
| Мутабельна ціна в Order | DB Design | Зламана фінансова звітність | Зберігати `purchase_price` в OrderItem |

---

## Довідник для швидкого пошуку

| Питання | Де шукати |
|---------|-----------|
| Як налаштувати URL? | [Django_URL_Routing.md](Django_URL_Routing.md) |
| Як написати View? | [Django_Views.md](Django_Views.md) |
| Як написати Template? | [Django_Templates.md](Django_Templates.md) |
| Як написати Model? | [Django_ORM.md](Django_ORM.md) |
| Що таке міграція? | [DJANGO_MIGRATIONS.md](DJANGO_MIGRATIONS.md) |
| Яка команда що робить? | [DJANGO_COMMAND_SYSTEM.md](DJANGO_COMMAND_SYSTEM.md) |
| Що таке кожен файл? | [DJANGO_PROJECT_STRUCTURE.md](DJANGO_PROJECT_STRUCTURE.md) |
| Як працює DNS? | [network_foundation.md](network_foundation.md) |
| Що таке TCP? | [network_foundation.md](network_foundation.md) |
| Архітектурні схеми | [django_mermaid.md](django_mermaid.md) |
| Мережеві схеми | [network_mermaid.md](network_mermaid.md) |
| Де живе бізнес-логіка? | [DJANGO_SERVICES.md](DJANGO_SERVICES.md) |
| Що таке Service? | [DJANGO_SERVICES.md](DJANGO_SERVICES.md) |
| Що таке Selector? | [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) |
| Як не дублювати ORM-запити? | [DJANGO_SELECTORS.md](DJANGO_SELECTORS.md) |
| Як правильно відправити Celery task? | [DJANGO_TASKS.md](DJANGO_TASKS.md) |
| Що таке Celery broker і worker? | [DJANGO_TASKS.md](DJANGO_TASKS.md) |
| Як зробити task ідемпотентним? | [DJANGO_TASKS.md](DJANGO_TASKS.md) |
| Що таке InputSerializer / OutputSerializer? | [DJANGO_SERIALIZERS.md](DJANGO_SERIALIZERS.md) |
| Як валідувати вхідні дані? | [DJANGO_SERIALIZERS.md](DJANGO_SERIALIZERS.md) |

---

## Шлях студента — рекомендований порядок читання

```
1. network_foundation.md          ← Розумієш Інтернет
2. network_mermaid.md             ← Бачиш схеми
3. django_architecture.md         ← Розумієш Django як систему
4. DJANGO_PROJECT_STRUCTURE.md    ← Знаєш кожен файл
5. DJANGO_COMMAND_SYSTEM.md       ← Вмієш користуватись CLI
6. DJANGO_MIGRATIONS.md           ← Розумієш еволюцію БД
7. Django_ORM.md                  ← Пишеш запити до БД
8. Django_URL_Routing.md          ← Маршрутизуєш запити
9. Django_Views.md                ← Пишеш бізнес-логіку
10. Django_Templates.md           ← Рендериш HTML
11. django_mermaid.md             ← Бачиш повну архітектуру
12. DJANGO_SERVICES_SELECTORS.md  ← Архітектура бізнес-шару (Services, Selectors, Serializers)
13. DJANGO_SERVICES.md            ← Детально про services.py: транзакції, on_commit, side effects
14. DJANGO_SELECTORS.md           ← Детально про selectors.py: CQRS-light, named queries, N+1
15. DJANGO_SERIALIZERS.md         ← Детально про serializers.py: Input/Output, validate(), поля
16. DJANGO_TASKS.md               ← Детально про tasks.py: Celery, retry, on_commit, ідемпотентність
```

> Після цього шляху ти думаєш як backend engineer, а не просто "пишеш Django-код".

---

## Практичні проєкти

| Проєкт | Папка | Рівень | Що всередині |
|--------|-------|--------|--------------|
| [Hello, Django!](simple_django_project/README.md) | `simple_django_project/` | Початківець | Покрокова інструкція: venv → перша сторінка у браузері. Тільки README + requirements.txt |
| [Новинний портал](news_portal/README.md) | `news_portal/` | Базовий | Повноцінний сайт: моделі, вьюшки, шаблони, адмін-панель, парсер rbc.ua, Docker + PostgreSQL |

### Рекомендований порядок

```
Теорія (кроки 1–11 вище)
       ↓
simple_django_project/   ← перший запуск Django своїми руками
       ↓
news_portal/             ← реальна архітектура: ORM, CBV, Admin, management command
```
