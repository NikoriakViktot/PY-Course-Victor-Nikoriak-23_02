# Новинний Портал — Навчальний Django-проєкт

Практичний проєкт для вивчення Django-архітектури.
Новини парсяться з [rbc.ua](https://www.rbc.ua) і відображаються на сайті.
Адміністратор модерує і публікує статті через Django Admin.

---

## Архітектура проєкту

```
Браузер
  │ HTTP запит
  ▼
Gunicorn (WSGI сервер)
  │ Python dict
  ▼
Django (news_portal/wsgi.py)
  │ Middleware → urls.py
  ▼
views.py (ArticleListView / ArticleDetailView)
  │ QuerySet API
  ▼
models.py (Article, Category) → PostgreSQL
  │ дані
  ▼
templates/news/*.html → HTML відповідь
```

```
news_portal/               ← корінь проєкту
├── manage.py              ← CLI оркестратор
├── requirements.txt       ← залежності
├── .env.example           ← шаблон змінних оточення
├── Dockerfile             ← образ Docker
├── docker-compose.yml     ← PostgreSQL + Django
│
├── news_portal/           ← пакет конфігурації
│   ├── settings.py        ← центральні налаштування
│   ├── urls.py            ← головний маршрутизатор
│   ├── wsgi.py            ← синхронний шлюз
│   └── asgi.py            ← асинхронний шлюз
│
├── news/                  ← додаток новин
│   ├── models.py          ← Category, Article (ORM → PostgreSQL)
│   ├── views.py           ← ArticleListView, DetailView, CategoryView
│   ├── urls.py            ← маршрути /article/<pk>/ тощо
│   ├── admin.py           ← кастомна адмін-панель
│   └── management/
│       └── commands/
│           └── parse_rbc.py  ← парсер rbc.ua
│
├── templates/
│   ├── base.html          ← базовий шаблон (nav + footer)
│   └── news/
│       ├── article_list.html   ← список новин
│       └── article_detail.html ← одна стаття
│
└── static/
    └── css/style.css      ← кастомні стилі
```

---

## Запуск через Docker (рекомендовано)

### 1. Клонуй або перейди в директорію проєкту
```bash
cd module_5/lesson_Django_Network_Architecture/news_portal/

```
### 2. Запусти PostgreSQL + Django
```bash
docker compose up --build
```
### 3. В новому терміналі: застосуй міграції
#### перейди в директорію проєкту
```bash
cd module_5/lesson_Django_Network_Architecture/news_portal/
```
####  застосуй міграції
```bash
docker compose exec web python manage.py migrate
```
### 4. Створи адміністратора

```bash
docker compose exec web python manage.py createsuperuser

```
### 5. Спарси новини (--publish = одразу опублікувати)
```bash
  docker compose exec web python manage.py makemigrations news
```
```bash
  docker compose exec web python manage.py migrate

```
```bash
docker compose exec web python manage.py parse_rbc --publish

```

### 6. Відкрий у браузері
#### Сайт:     http://localhost:8000/
#### Адмінка:  http://localhost:8000/admin/

____

## Запуск локально (без Docker)

```bash
# 1. Створи virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Встанови залежності
pip install -r requirements.txt

# 3. Налаштуй змінні оточення
cp .env.example .env
# Відредагуй .env: вкажи DB_HOST=localhost і реальні паролі БД

# 4. Запусти PostgreSQL (або вкажи SQLite для прототипу — зміни settings.py)

# 5. Застосуй міграції
python manage.py migrate

# 6. Створи адміна
python manage.py createsuperuser

# 7. Спарси новини
python manage.py parse_rbc --limit 50 --publish

# 8. Запусти сервер
python manage.py runserver
# → http://localhost:8000/
```

---

## Команда парсера

### Спарсити 100 новин (чернетки, потрібна ручна публікація в адмінці)

```bash
python manage.py parse_rbc
```
### Спарсити 50 новин і одразу опублікувати

```bash
python manage.py parse_rbc --limit 50 --publish
```
### Довідка

```bash
python manage.py parse_rbc --help
```

---

## URL-схема

| URL | View | Опис |
|-----|------|------|
| `/` | ArticleListView | Список всіх опублікованих новин |
| `/article/<pk>/` | ArticleDetailView | Повна стаття |
| `/category/<slug>/` | CategoryArticleListView | Новини категорії |
| `/admin/` | Django Admin | Панель адміністратора |

---

## Моделі БД

```
Category                    Article
─────────────────────────   ──────────────────────────────────────
id          BigInt (PK)     id           BigInt (PK)
name        VARCHAR(100)    title        VARCHAR(300)
slug        VARCHAR(100)    content      TEXT
created_at  TIMESTAMP       source_url   VARCHAR(500) UNIQUE
                            source_name  VARCHAR(100)
                            pub_date     TIMESTAMP
                            is_published BOOLEAN
                            created_at   TIMESTAMP
                            updated_at   TIMESTAMP
                            category_id  BigInt (FK → Category)
```

---

## Ключові концепції Django в цьому проєкті

| Концепція | Де реалізована |
|-----------|----------------|
| Models (ORM) | `news/models.py` — Category, Article |
| Migrations | `news/migrations/` |
| Views (CBV) | `news/views.py` — ListView, DetailView |
| URL Routing | `news/urls.py`, `news_portal/urls.py` |
| Templates (DTL) | `templates/` — extends, for, url, block |
| Admin panel | `news/admin.py` — list_display, actions |
| Management commands | `news/management/commands/parse_rbc.py` |
| Settings | `news_portal/settings.py` |
| WSGI | `news_portal/wsgi.py` |
| select_related | `views.py` — N+1 оптимізація |
| get_or_create | `parse_rbc.py` — атомарне отримання/створення |
| transaction.atomic | `parse_rbc.py` — транзакція при імпорті |
