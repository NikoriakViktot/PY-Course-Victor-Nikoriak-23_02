# Django — Система команд та операційний lifecycle

> Django — це повноцінний конвеєр бекенд-системи. Дані проходять через послідовність:
> запит → URL dispatcher → View → Model (БД) → Template → HTTP відповідь.
> Цей файл описує всі команди та повний lifecycle проєкту від нуля до продакшену.

---

## Швидка довідка — Таблиця всіх команд

| Команда | Синтаксис | Коли виконувати |
|---------|-----------|-----------------|
| Створити проєкт | `django-admin startproject myproject` | Один раз на початку |
| Створити додаток | `python manage.py startapp myapp` | При додаванні нового модуля |
| Запустити сервер | `python manage.py runserver` | Під час розробки |
| Запустити на порту | `python manage.py runserver 0.0.0.0:8080` | При потребі іншого порту |
| Генерація міграцій | `python manage.py makemigrations` | Після зміни `models.py` |
| Застосування міграцій | `python manage.py migrate` | Після `makemigrations` |
| Перегляд SQL міграції | `python manage.py sqlmigrate myapp 0001` | Для відлагодження |
| Статус міграцій | `python manage.py showmigrations` | Для аудиту стану БД |
| Скасувати міграцію | `python manage.py migrate myapp 0001` | Відкат до версії |
| Створити суперюзера | `python manage.py createsuperuser` | Після першої міграції |
| Зібрати статику | `python manage.py collectstatic` | Перед деплоєм |
| Python shell | `python manage.py shell` | Для тестування ORM |
| SQL shell | `python manage.py dbshell` | Для прямих SQL-запитів |
| Запустити тести | `python manage.py test` | Перед деплоєм |
| Запустити тести (app) | `python manage.py test myapp` | Тести одного додатку |
| Перевірити проєкт | `python manage.py check` | Перевірка конфігурації |
| Перевірити деплой | `python manage.py check --deploy` | Аудит безпеки |
| Dump даних | `python manage.py dumpdata myapp` | Бекап даних |
| Load даних | `python manage.py loaddata fixture.json` | Відновлення / seeds |
| Власна команда | `python manage.py my_command` | Автоматизовані задачі |

---

## Частина 1: Основні команди — як вони працюють

### 1. `startproject` — Ініціалізація системи

**Основний механізм:** Створює абсолютно нове Django-середовище — генерує основні конфігураційні файли.

**Потік виконання:**
- Генерується кореневий каталог з `manage.py` (оркестратор проєкту)
- Внутрішній каталог містить `settings.py`, `urls.py`, `asgi.py`, `wsgi.py`

```bash
django-admin startproject myproject
cd myproject
```

Результат:
```
myproject/
├── manage.py
└── myproject/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── asgi.py
    └── wsgi.py
```

**Аналогія:** `startproject` — це купівля земельної ділянки, закладання фундаменту та проведення комунікацій. Жодної кімнати ще немає, але інфраструктура готова.

**Реальне застосування:** Згенеровані `wsgi.py` або `asgi.py` — це точки підключення, які використовують Gunicorn або Uvicorn для роздачі бекенду в Інтернет.

> **Типова помилка:** Не називай проєкт іменами вбудованих модулів Python (`test`, `django`) — це спричиняє фатальні конфлікти імен.

---

### 2. `startapp` — Створення модуля

**Основний механізм:** Створює модульний Python-пакет для окремої функції або домену проєкту.

```bash
python manage.py startapp myapp
```

Результат:
```
myapp/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── views.py
├── tests.py
└── migrations/
    └── __init__.py
```

**Після створення — обов'язково зареєструвати в `settings.py`:**

```python
INSTALLED_APPS = [
    ...
    'myapp.apps.MyappConfig',   # або просто 'myapp'
]
```

**Аналогія:** Якщо проєкт — фундамент будинку, то `startapp` — будівництво конкретної кімнати. Але будинок не знатиме про неї, доки не під'єднаєш до комунікацій (`INSTALLED_APPS`).

> **Типова помилка:** Забути зареєструвати додаток у `settings.py` — Django мовчки ігноруватиме твої моделі та міграції.

---

### 3. `makemigrations` — Фіксація змін схеми

**Основний механізм:** Сканує `models.py`, порівнює з поточним станом схеми БД і генерує Python-скрипти (міграції).

```bash
python manage.py makemigrations
python manage.py makemigrations myapp          # для конкретного додатку
python manage.py makemigrations --name add_isbn  # з іменем
```

**Важливо:** Ця команда **не вносить змін до бази даних**. Вона лише створює план.

Приклад згенерованого файлу:
```python
# migrations/0002_book_isbn.py
class Migration(migrations.Migration):
    dependencies = [('myapp', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='book',
            name='isbn',
            field=models.CharField(max_length=13, blank=True),
        ),
    ]
```

**Аналогія:** Це як фіксація в Git. Ти реєструєш намір змінити базу, але будівельники ще не приступили до роботи.

> **Типова помилка:** Думати, що `makemigrations` оновлює базу даних. Вона лише створює інструкції.

---

### 4. `migrate` — Застосування міграцій

**Основний механізм:** Застосовує файли міграцій до бази даних, виконуючи SQL.

```bash
python manage.py migrate
python manage.py migrate myapp             # тільки один додаток
python manage.py migrate myapp 0001        # відкат до конкретної версії
```

**Потік виконання:**
1. Django підключається до БД
2. Перевіряє таблицю `django_migrations` — що вже застосовано
3. Виконує SQL для всіх нових міграцій
4. Записує кожну виконану міграцію в `django_migrations`

**Для відлагодження — переглянь SQL перед запуском:**
```bash
python manage.py sqlmigrate myapp 0002
# Виводить: ALTER TABLE myapp_book ADD COLUMN isbn VARCHAR(13) NOT NULL DEFAULT '';
```

**Аналогія:** Якщо `makemigrations` — архітектор, що малює креслення, то `migrate` — будівельна бригада, яка заливає бетон і зводить стіни.

> **Типова помилка:** Змінити `models.py` і забути запустити `makemigrations` та `migrate` — отримаєш помилки на рівні БД.

---

### 5. `runserver` — Сервер для розробки

**Основний механізм:** Легкий вбудований сервер виключно для локальної розробки.

```bash
python manage.py runserver               # localhost:8000
python manage.py runserver 0.0.0.0:8080  # доступний у мережі
python manage.py runserver --noreload    # без автоперезавантаження
```

**Що відбувається всередині:**
- Прив'язується до порту 8000
- Відстежує зміни у файлах (автоперезавантаження)
- Однопотоковий — обробляє 1 запит одночасно

**Аналогія:** Репетиційна сцена. Для тестування, не для глядачів.

> **Критична помилка:** Використовувати `runserver` у продакшні. Він однопотоковий, не перевіряє безпеку, не оптимізований для статичних файлів. **У продакшні — тільки Gunicorn + Nginx.**

---

### 6. `createsuperuser` — Адміністратор системи

```bash
python manage.py createsuperuser
```

**Потік виконання:**
1. Запитує ім'я користувача / email / пароль
2. Безпечно хешує пароль (PBKDF2 + SHA256)
3. Вставляє запис у таблицю `auth_user` з `is_superuser=True`, `is_staff=True`

Після цього доступна панель адміністратора: `http://localhost:8000/admin/`

> **Типова помилка:** Спроба зайти в адмін без попереднього `migrate` — таблиця `auth_user` не існуватиме.

---

### 7. `collectstatic` — Підготовка статики

```bash
python manage.py collectstatic
```

Збирає всі статичні файли (CSS, JS, зображення) з усіх додатків в одну папку `STATIC_ROOT`.

```python
# settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'  # куди збирати
STATIC_URL = '/static/'                 # URL-префікс
```

У продакшні Nginx роздає файли з `STATIC_ROOT` напряму, без участі Python.

> **Типова помилка:** Очікувати, що Django автоматично роздаватиме статику у продакшні (`DEBUG=False`). Це не так — потрібен Nginx.

---

### 8. `shell` — Інтерактивна Python-оболонка

```bash
python manage.py shell          # стандартний Python shell
python manage.py shell -i bpython  # з bpython (кращий UX)
```

Надає повний доступ до Django ORM в інтерактивному режимі:

```python
>>> from myapp.models import Book
>>> Book.objects.all()
>>> Book.objects.create(title="Django 5", price=29.99)
>>> Book.objects.filter(price__gt=20).count()
```

**Реальне застосування:** Тестування ORM-запитів, дебагінг даних, ручне виправлення помилкових записів.

---

### 9. `check` / `check --deploy` — Аудит конфігурації

```bash
python manage.py check             # загальна перевірка
python manage.py check --deploy    # перевірка безпеки для продакшну
```

`--deploy` перевіряє:
- `DEBUG = False`
- `SECRET_KEY` не дефолтний
- `ALLOWED_HOSTS` налаштовано
- HTTPS headers увімкнені
- Cookie параметри безпечні

---

### 10. Власні команди — Автоматизація бекенду

**Де створювати:**
```
myapp/
└── management/
    └── commands/
        ├── __init__.py
        └── send_reports.py
```

```python
# management/commands/send_reports.py
from django.core.management.base import BaseCommand
from myapp.tasks import generate_monthly_report

class Command(BaseCommand):
    help = 'Генерує та надсилає місячні звіти'

    def add_arguments(self, parser):
        parser.add_argument('--month', type=int, default=None)

    def handle(self, *args, **options):
        month = options['month']
        generate_monthly_report(month)
        self.stdout.write(self.style.SUCCESS('Звіти успішно надіслано'))
```

```bash
python manage.py send_reports --month 5
```

**Реальне застосування:** Нічні звіти, очищення прострочених сесій, масова розсилка email — усе через `cron` або `Celery Beat`.

---

## Частина 2: Повний операційний lifecycle

### Від нуля до продакшену — покроковий процес

```
Крок 1: Підготовка середовища
├── python -m venv env
├── source env/bin/activate  (Linux/Mac) або env\Scripts\activate (Windows)
└── pip install django psycopg2-binary gunicorn

Крок 2: Ініціалізація проєкту
├── django-admin startproject myproject
└── cd myproject

Крок 3: Перша перевірка
├── python manage.py runserver
└── Відкрий http://127.0.0.1:8000 — має бути стартова сторінка Django

Крок 4: Створення додатку
├── python manage.py startapp myapp
├── Додай 'myapp' до INSTALLED_APPS в settings.py
└── Налаштуй urls.py

Крок 5: Модель → Міграція → БД
├── Визнач класи в models.py
├── python manage.py makemigrations
└── python manage.py migrate

Крок 6: Адміністратор
├── python manage.py createsuperuser
└── Зареєструй моделі в admin.py

Крок 7: Views + Templates
├── Напиши функції або класи в views.py
├── Прив'яжи маршрути в urls.py
└── Створи HTML-шаблони в templates/

Крок 8: Підготовка до деплою
├── python manage.py check --deploy
├── python manage.py collectstatic
└── gunicorn myproject.wsgi:application --workers 4
```

---

## Шпаргалка: Найпоширеніші сценарії

### Додати нове поле до моделі

```bash
# 1. Зміни models.py
# 2. Створи міграцію
python manage.py makemigrations

# 3. Перевір SQL (необов'язково, але корисно)
python manage.py sqlmigrate myapp 0003

# 4. Застосуй
python manage.py migrate
```

### Відкотити міграцію

```bash
# Переглянь поточний стан
python manage.py showmigrations

# Відкот до попередньої версії (0001)
python manage.py migrate myapp 0001

# Видали файл 0002_*.py
# Зміни models.py назад
# Або тільки migrate назад якщо потрібно повторно застосувати
```

### Дебаг ORM-запиту

```bash
python manage.py shell
```

```python
>>> from myapp.models import Book
>>> qs = Book.objects.select_related('author').filter(is_active=True)
>>> print(qs.query)
# Виводить SQL: SELECT ... FROM myapp_book INNER JOIN ...
>>> qs.explain()
# Виводить EXPLAIN ANALYZE від PostgreSQL
```

### Скидання всіх міграцій (НЕБЕЗПЕЧНО — лише у dev)

```bash
# Тільки якщо БД можна знищити!
python manage.py migrate myapp zero     # скасовує всі міграції додатку
# Видали всі файли в migrations/ крім __init__.py
python manage.py makemigrations         # генерує свіжий 0001_initial.py
python manage.py migrate
```

---

## Типові помилки та як їх уникнути

| Помилка | Причина | Рішення |
|---------|---------|---------|
| `No module named 'myapp'` | Не в `INSTALLED_APPS` | Додай `'myapp'` до `INSTALLED_APPS` |
| `Table doesn't exist` | Не запустив `migrate` | `python manage.py migrate` |
| `InconsistentMigrationHistory` | Видалено файл міграції після `migrate` | Відновити файл або `migrate --fake` |
| `Address already in use` | Порт 8000 зайнятий | `python manage.py runserver 8001` |
| `Non-nullable field` | Додав поле без `default` | Додай `default=` або `null=True` |
| Admin `DoesNotExist` | Не запустив `migrate` перед `createsuperuser` | Спочатку `migrate` |
| Static files 404 у prod | `collectstatic` не запущено або Nginx не налаштований | `collectstatic` + налаштувати Nginx |
