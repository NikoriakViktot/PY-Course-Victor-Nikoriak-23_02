# Мій перший Django-проєкт — Hello, Django!

Покрокова інструкція для абсолютних початківців.
Ми створимо мінімальний сайт який показує текст **"Hello, Django!"** у браузері
та має повноцінну **адмін-панель**.

 **Сумісність Python і Django:**
> | Python | Django |
> |--------|--------|
> | 3.10 – 3.13 | 5.1.x або 5.2.x |
> | **3.14** | **тільки 5.2+** (5.1 не підтримує Python 3.14) |
>
> Перевір версію: `python --version`
> Якщо у тебе Python 3.14 — `requirements.txt` вже налаштований правильно (`Django>=5.2`).

---

## Що ти отримаєш в результаті

```
http://localhost:8000/        →  Hello, Django!
http://localhost:8000/about/  →  Це моя перша сторінка на Django!
http://localhost:8000/admin/  →  Адмін-панель (логін superuser)
```

---

## Кінцева структура проєкту

```
simple_django_project/        ← ти зараз тут
├── venv/                     ← virtual environment (не чіпай цю папку)
├── db.sqlite3                ← база даних SQLite (з'явиться після migrate)
├── hello_project/            ← пакет налаштувань Django (settings, urls)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hello_app/                ← наш додаток (views, urls)
│   ├── __init__.py
│   ├── views.py              ← ТУТ пишемо функції-обробники
│   └── urls.py               ← ТУТ прописуємо маршрути додатку
├── manage.py                 ← CLI оркестратор
└── requirements.txt          ← цей файл вже є
```

---

## Покрокові інструкції

> **Усі команди виконуються з папки `simple_django_project/`**
>
> Перевір де ти знаходишся: команда `pwd` (Linux/Mac) або `cd` (Windows)

---

### Крок 1 — Відкрий термінал у цій папці

**PyCharm:**
`View → Tool Windows → Terminal` — відкриє термінал вже в папці проєкту.

**Звичайний термінал** (з кореня репозиторію `PY-Course-Victor-Nikoriak-23_02`):
```
cd module_5\lesson_Django_Network_Architecture\simple_django_project
```

---

### Крок 2 — Створи virtual environment

Virtual environment — ізольоване Python-середовище.
Пакети які ти встановлюєш сюди не впливають на інші проєкти.

```bash
python -m venv venv
```

Після цього з'явиться папка `venv/`.

---

### Крок 3 — Активуй virtual environment

> Активувати потрібно **кожного разу** коли відкриваєш новий термінал!

**Windows (Command Prompt):**
```
venv\Scripts\activate
```

**Windows (PowerShell):**
```
venv\Scripts\Activate.ps1
```

**Linux / Mac:**
```bash
source venv/bin/activate
```

Після активації в рядку терміналу з'явиться `(venv)`:
```
(venv) C:\...\simple_django_project>
```

---

### Крок 4 — Встанови Django

upgrade pip
```bash
python -m pip install --upgrade pip
```
встановити залежності
```bash
pip install -r requirements.txt
```
або

```bash
python -m pip install -r requirements.txt
```


Перевір що Django встановився:
```bash
python -m django --version
```
Має показати: `5.2.x` (якщо Python 3.14) або `5.1.x` / `5.2.x` (якщо Python 3.10–3.13)

Якщо Django вже встановлений і потрібно **оновити** до 5.2:
```bash
pip install -r requirements.txt --upgrade
```

---

### Крок 5 — Створи Django-проєкт

```bash
django-admin startproject hello_project .
```

> **Крапка `.` наприкінці — обов'язкова!**
> Вона означає "створити в поточній папці".
> Без крапки Django створить зайву вкладену директорію.

Після цієї команди з'являться:
```
simple_django_project/
├── hello_project/    ← новий пакет налаштувань
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── manage.py         ← новий файл
```

### Крок 5.1 — Перевір що сервер запускається

```bash
python manage.py runserver
```

---

### Крок 6 — Застосуй міграції (створи таблиці в БД)

```bash
python manage.py migrate
```

> **Що це робить?**
> Django включає вбудовані додатки (`django.contrib.auth`, `django.contrib.admin` тощо).
> Кожен з них має свої таблиці в базі даних.
> `migrate` створює ці таблиці у файлі `db.sqlite3`.
>
> **БЕЗ цього кроку адмін-панель впаде з помилкою:**
> `OperationalError: no such table: auth_user`

Після виконання з'явиться файл `db.sqlite3` і в терміналі побачиш:
```
Applying auth.0001_initial... OK
Applying admin.0001_initial... OK
...
```

---

### Крок 7 — Створи облікові дані адміністратора

```bash
python manage.py createsuperuser
```

Django запитає:
```
Username: admin
Email address: (можна залишити порожнім, натисни Enter)
Password: ****
Password (again): ****
Superuser created successfully.
```

> Цей логін/пароль використовується для входу в адмін-панель
> на `http://localhost:8000/admin/`

---

### Крок 8 — Перевір що сервер і адмін запускаються

```bash
python manage.py runserver
```

Відкрий браузер:
- **http://localhost:8000/** → стартова сторінка Django (ракета)
- **http://localhost:8000/admin/** → адмін-панель, введи логін з Кроку 7

якщо є проблеми перевр чи не зайняти 8000 порт на твоїй машині іншими додатками.

Зупини сервер: `Ctrl + C`

---

### Крок 9 — Створи додаток

Django-проєкт складається з одного або кількох **додатків** (apps).
Кожен додаток відповідає за певну частину функціональності.

```bash
python manage.py startapp hello_app
```

З'явиться папка `hello_app/` з автоматично згенерованими файлами.

---

### Крок 10 — Зареєструй додаток у settings.py

Відкрий файл `hello_project/settings.py`.

Знайди список `INSTALLED_APPS` і додай `'hello_app'` в кінець:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hello_app',    # ← ДОДАЙ ЦЮ СТРОКУ
]
```

> **Чому це важливо?**
> Django знає про додаток тільки якщо він є в `INSTALLED_APPS`.
> Без цього Django не буде шукати views, templates і команди в `hello_app/`.

---

### Крок 11 — Напиши перші view-функції

Відкрий файл `hello_app/views.py`.

Замість вмісту який там є, напиши:

```python
from django.http import HttpResponse


def index(request):
    """Головна сторінка — повертає просте текстове повідомлення."""
    return HttpResponse("Hello, Django!")


def about(request):
    """Сторінка 'Про нас'."""
    return HttpResponse("Це моя перша сторінка на Django!")
```

> **Що таке view-функція?**
> - Приймає `request` (HTTP-запит від браузера)
> - Виконує якусь логіку
> - Повертає `HttpResponse` (відповідь браузеру)
>
> `HttpResponse("текст")` — найпростіша відповідь: просто текст.

---

### Крок 12 — Створи URL-маршрути для додатку

Створи **новий файл** `hello_app/urls.py` і напиши в нього:

```python
from django.urls import path
from . import views

# app_name — обов'язково якщо в головному urls.py вказано namespace=
# Дозволяє звертатись до маршрутів як: 'hello_app:index', 'hello_app:about'
app_name = "hello_app"

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
]
```

> **Що тут відбувається?**
> - `app_name = "hello_app"` — ім'я простору імен (namespace) цього додатку
> - `path('', views.index)` — запит на `/` → виклик `views.index`
> - `path('about/', views.about)` — запит на `/about/` → виклик `views.about`
> - `name='index'` — ім'я маршруту всередині namespace

---

### Крок 13 — Підключи маршрути до головного urls.py

Відкрий `hello_project/urls.py`.

Він зараз виглядає так:
```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
```

Замінити на:
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hello_app.urls', namespace='hello_app')),  # ← ДОДАЙ ЦЮ СТРОКУ
]
```

> **Що таке `include()`?**
> `include('hello_app.urls')` — говорить Django:
> "для цього URL-префіксу читай маршрути з файлу `hello_app/urls.py`".
>
> `namespace='hello_app'` — ізолює імена маршрутів цього додатку.
> **Вимагає** `app_name = "hello_app"` у `hello_app/urls.py` — інакше Django падає з `ImproperlyConfigured`.

---

### Крок 14 — Запусти сервер і перевір результат

```bash
python manage.py runserver
```

Відкрий браузер:

| URL | Результат |
|-----|-----------|
| http://localhost:8000/ | `Hello, Django!` |
| http://localhost:8000/about/ | `Це моя перша сторінка на Django!` |
| http://localhost:8000/admin/ | Адмін-панель — введи логін з Кроку 7 |

**Вітаємо! Твій перший Django-сайт з адмін-панеллю працює!** 🎉

---

## Адмін-панель Django — повне пояснення

### Що це таке

Django Admin — це **автоматично згенерований веб-інтерфейс** для управління даними в базі даних.
Він вбудований у Django і доступний одразу після `migrate` + `createsuperuser`.

Це не "окремий проєкт" — це звичайний Django-додаток `django.contrib.admin`
зі своїми моделями, views і шаблонами. Він підключений у `INSTALLED_APPS` у `settings.py`.

```
http://127.0.0.1:8000/admin/               ← головна сторінка (список розділів)
http://127.0.0.1:8000/admin/auth/user/     ← список користувачів
http://127.0.0.1:8000/admin/auth/user/add/ ← створити нового користувача
http://127.0.0.1:8000/admin/auth/group/    ← список груп (ролей)
```

---

### Де зберігаються дані

У сирому Django (без налаштування PostgreSQL) дані зберігаються у файлі **`db.sqlite3`**.

```
simple_django_project/
└── db.sqlite3    ← це і є вся база даних (один файл!)
```

SQLite — вбудована база даних, не потребує окремого серверу.
Файл створюється автоматично командою `python manage.py migrate`.

**Таблиці які Django створює в db.sqlite3:**

| Таблиця | Що зберігає |
|---------|-------------|
| `auth_user` | Користувачі: username, password (хеш), email, is_staff, is_superuser |
| `auth_group` | Групи/ролі: назва групи |
| `auth_permission` | Дозволи: назва + до якої моделі відноситься |
| `auth_user_groups` | Зв'язок: який користувач у якій групі |
| `auth_user_user_permissions` | Зв'язок: індивідуальні дозволи користувача |
| `django_session` | Сесії: хто залогінений (cookie → запис у БД) |
| `django_admin_log` | Журнал дій в адмін-панелі (хто що змінив) |
| `django_content_type` | Реєстр типів контенту (для системи дозволів) |
| `django_migrations` | Які міграції вже застосовані |

Переглянути сирі дані можна будь-яким SQLite-оглядачем (наприклад DB Browser for SQLite).

---

### Розділ Users — http://127.0.0.1:8000/admin/auth/user/

Список всіх користувачів системи. Кожен користувач має:

| Поле | Що означає |
|------|------------|
| **Username** | Логін для входу |
| **Email** | Email адреса (необов'язковий) |
| **Password** | Зберігається як хеш (PBKDF2+SHA256) — ніколи не зберігається у відкритому вигляді |
| **First/Last name** | Ім'я та прізвище |
| **Active** | Чи може логінитись (False = заблокований) |
| **Staff status** | Чи має доступ до `/admin/` |
| **Superuser status** | Чи має ВСІ права (обходить перевірку дозволів) |
| **Groups** | Які групи (ролі) призначено |
| **User permissions** | Індивідуальні дозволи (зверх групових) |

**Типи користувачів:**

```
Superuser  → is_superuser=True → всі права, без обмежень
Staff user → is_staff=True     → вхід в /admin/, але тільки ті права що призначені
Regular    → обидва False       → немає доступу до /admin/
```

Ти створив superuser командою `python manage.py createsuperuser` — він має всі права.

---

### Розділ Groups — http://127.0.0.1:8000/admin/auth/group/

**Група = набір дозволів з назвою (роль).**

Замість того щоб призначати дозволи кожному користувачу окремо —
створюєш групу "Редактори" з потрібними правами і додаєш туди людей.

**Приклад реального використання:**

```
Група "Редактори новин"
    ✅ news.add_article    ← може створювати статті
    ✅ news.change_article ← може редагувати статті
    ❌ news.delete_article ← НЕ може видаляти
    ❌ news.view_user      ← НЕ бачить користувачів

Група "Модератори"
    ✅ news.delete_article ← може видаляти
    ✅ auth.view_user      ← бачить список користувачів
```

Коли додаєш користувача в групу — він автоматично отримує всі її дозволи.

**Формат дозволів Django:** `<app>.<action>_<model>`

```
news.add_article      ← додавати статті
news.change_article   ← редагувати статті
news.delete_article   ← видаляти статті
news.view_article     ← переглядати статті
auth.add_user         ← додавати користувачів
```

Django автоматично генерує 4 дозволи для **кожної** моделі (`add`, `change`, `delete`, `view`).

---

### Журнал дій (django_admin_log)

Кожна дія в адмін-панелі автоматично логується:

```
http://127.0.0.1:8000/admin/ → Recent actions (права колонка)
```

Зберігається в таблиці `django_admin_log`:
- хто зробив дію (user)
- що зробив (added / changed / deleted)
- який об'єкт (content_type + object_id)
- коли (action_time)

---

### Як додати свої моделі в адмін

Щоб твої моделі (наприклад `Article`) з'явились в адмін-панелі,
потрібно зареєструвати їх у `hello_app/admin.py`:

```python
from django.contrib import admin
from .models import Article  # імпортуємо модель

# Простий варіант — одним рядком
admin.site.register(Article)
```

Після цього з'явиться розділ `/admin/hello_app/article/` з автоматичним CRUD.

---

### SQLite vs PostgreSQL

| | SQLite (за замовчуванням) | PostgreSQL |
|-|--------------------------|-----------|
| **Запуск** | Нічого не потрібно, файл | Окремий сервер |
| **Де файл** | `db.sqlite3` в папці проєкту | На сервері БД |
| **Підходить для** | Розробка, навчання, прототипи | Продакшн |
| **Одночасні записи** | Блокує файл | Повна конкурентність |
| **Налаштування в settings.py** | `'ENGINE': 'django.db.backends.sqlite3'` | `'ENGINE': 'django.db.backends.postgresql'` |

У `news_portal/` проєкті вже налаштований PostgreSQL через Docker.

---

## Підсумок: всі команди по порядку

```bash
# 1. Перейти в папку
cd module_5\lesson_Django_Network_Architecture\simple_django_project

# 2. Створити і активувати venv
python -m venv venv
venv\Scripts\activate

# 3. Встановити Django
pip install -r requirements.txt

# 4. Створити проєкт
django-admin startproject hello_project .

# 5. Застосувати міграції (створює db.sqlite3 з таблицями)
python manage.py migrate

# 6. Створити адміністратора
python manage.py createsuperuser

# 7. Перевірити адмін-панель
python manage.py runserver
# → http://localhost:8000/admin/

# 8. Створити додаток
python manage.py startapp hello_app
# (далі редагуємо файли вручну — кроки 10–13)

# 9. Фінальний запуск
python manage.py runserver
```

---

## Що ти зробив (зміни у файлах)

| Файл | Що ти зробив |
|------|-------------|
| `hello_project/settings.py` | Додав `'hello_app'` в `INSTALLED_APPS` |
| `hello_app/views.py` | Написав функції `index()` і `about()` |
| `hello_app/urls.py` | Створив файл з `app_name` і маршрутами |
| `hello_project/urls.py` | Підключив маршрути через `include()` |

---

## Часті помилки початківців

| Помилка | Причина | Рішення |
|---------|---------|---------|
| `AttributeError: 'super' object has no attribute 'dicts'` | Python 3.14 несумісний з Django 5.1 | `pip install -r requirements.txt --upgrade` (встановить Django 5.2+) |
| `OperationalError: no such table: auth_user` | Міграції не запускались | `python manage.py migrate` |
| `ModuleNotFoundError: No module named 'django'` | venv не активований або Django не встановлений | Активуй venv → `pip install -r requirements.txt` |
| `Page not found (404)` | Маршрут не зареєстрований | Перевір `urls.py` в обох файлах |
| `ImproperlyConfigured: Specifying a namespace...` | `namespace=` є в `include()`, але `app_name` відсутній у `hello_app/urls.py` | Додай `app_name = "hello_app"` у `hello_app/urls.py` |
| `NameError: name 'Note' is not defined` | `views.py` не імпортує модель | Додай `from .models import Note` у `views.py` |
| `ImportError` в urls.py | Помилка в `from . import views` | Перевір що `views.py` існує в `hello_app/` |
| Django не бачить `hello_app` | Не додано в `INSTALLED_APPS` | Додай `'hello_app'` у `settings.py` |
| Не зупиняється сервер | — | Натисни `Ctrl + C` у терміналі |

---

## Наступні кроки

Цей проєкт використовує найпростіший варіант: `HttpResponse` з текстом.
Реальний Django-проєкт використовує **шаблони** (HTML-файли):

```python
# Замість HttpResponse("текст")
return render(request, 'hello_app/index.html', {'name': 'Дмитро'})
```

Повна архітектура з шаблонами, моделями і базою даних — у проєкті `news_portal/`.

---

## Бонус: створи свою першу модель

Додамо просту модель `Note` (нотатки) — щоб зрозуміти як Django ORM пов'язує
Python-клас з таблицею в базі даних.

### Що отримаємо

```
http://127.0.0.1:8000/admin/hello_app/note/     ← список нотаток
http://127.0.0.1:8000/admin/hello_app/note/add/ ← створити нотатку
```

---

### Крок Б1 — Опиши модель у models.py

Відкрий `hello_app/models.py` і напиши:

```python
from django.db import models


class Note(models.Model):
    """
    Модель = Python-клас що описує таблицю в базі даних.

    Django ORM автоматично:
        - створює таблицю 'hello_app_note' в db.sqlite3
        - генерує поле id (PRIMARY KEY AUTOINCREMENT) автоматично
        - дає API: Note.objects.all(), Note.objects.create(...) тощо
    """

    # CharField → VARCHAR в SQL, обмежена довжина рядка
    title = models.CharField(
        max_length=200,          # максимум 200 символів
        verbose_name='Заголовок' # назва поля в адмін-панелі
    )

    # TextField → TEXT в SQL, необмежений текст
    content = models.TextField(
        blank=True,              # поле необов'язкове у формі
        verbose_name='Текст'
    )

    # DateTimeField з auto_now_add=True → TIMESTAMP
    # автоматично записує час створення запису
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Створено'
    )

    def __str__(self):
        # Це рядкове представлення об'єкта.
        # Відображається в адмін-панелі замість "Note object (1)"
        return self.title

    class Meta:
        verbose_name = 'Нотатка'
        verbose_name_plural = 'Нотатки'
        ordering = ['-created_at']  # нові нотатки — першими
```

---

### Крок Б2 — Зареєструй модель в адмін-панелі

Відкрий `hello_app/admin.py` і напиши:

```python
from django.contrib import admin
from .models import Note  # імпортуємо нашу модель


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    # Які колонки показувати в таблиці списку
    list_display = ('title', 'created_at')

    # Поля для рядка пошуку
    search_fields = ('title', 'content')
```

---

### Крок Б3 — Згенеруй міграцію

```bash
python manage.py makemigrations
```

Django порівнює `models.py` з поточним станом БД і генерує файл зі змінами:

```
Migrations for 'hello_app':
  hello_app/migrations/0001_initial.py
    + Create model Note
```

> **Що створилось?**
> Файл `hello_app/migrations/0001_initial.py` — це Python-скрипт
> який описує SQL що потрібно виконати.
> Він автоматично згенерований і не потребує редагування.

---

### Крок Б4 — Застосуй міграцію до бази даних

```bash
python manage.py migrate
```

```
Applying hello_app.0001_initial... OK
```

Тепер в `db.sqlite3` з'явилась таблиця `hello_app_note`:

```sql
-- Що Django виконав за тебе:
CREATE TABLE "hello_app_note" (
    "id"         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "title"      VARCHAR(200) NOT NULL,
    "content"    TEXT NOT NULL,
    "created_at" DATETIME NOT NULL
);
```

---

### Крок Б5 — Перевір у браузері

```bash
python manage.py runserver
```

Відкрий `http://127.0.0.1:8000/admin/` — з'явився новий розділ **"Нотатки"**.

1. Натисни **"Add note"** / **"Додати нотатку"**
2. Введи заголовок і текст
3. Натисни **Save**
4. Нотатка збережена в `db.sqlite3` → таблиця `hello_app_note`

---

### Що відбулось під капотом

```
models.py (Python клас)
    ↓  python manage.py makemigrations
hello_app/migrations/0001_initial.py  (план змін)
    ↓  python manage.py migrate
db.sqlite3 → таблиця hello_app_note  (реальна БД)
    ↓  admin.site.register(Note)
http://127.0.0.1:8000/admin/hello_app/note/  (веб-інтерфейс)
```

**Правило:** після будь-якої зміни `models.py` — завжди два кроки:
```bash
python manage.py makemigrations   # зафіксувати план
python manage.py migrate          # застосувати до БД
```

---

### Django ORM — базові запити до моделі

Після створення моделі Django дає повний API для роботи з даними.
Спробуй у Django shell:

```bash
python manage.py shell
```

```python
from hello_app.models import Note

# Створити нотатку
Note.objects.create(title="Перша нотатка", content="Привіт Django!")

# Отримати всі нотатки
Note.objects.all()
# → <QuerySet [<Note: Перша нотатка>]>

# Фільтрувати
Note.objects.filter(title="Перша нотатка")

# Кількість
Note.objects.count()
# → 1

# Отримати одну
note = Note.objects.get(id=1)
note.title
# → 'Перша нотатка'

# Видалити
note.delete()

# Вийти з shell
exit()
```

> Django shell — це звичайний Python інтерпретатор але з завантаженим Django.
> Дуже зручно для швидкого тестування запитів до БД.

---

## Бонус 2: виводимо нотатки на сторінці сайту

Адмін — тільки для персоналу. Тепер зробимо публічну сторінку
де відвідувачі бачать список нотаток.

**Маршрут:** `http://127.0.0.1:8000/notes/` → список всіх нотаток

Повний шлях запиту:
```
Браузер GET /notes/
    ↓ urls.py знаходить маршрут
    ↓ views.py отримує дані з БД через ORM
    ↓ templates/hello_app/note_list.html рендерить HTML
    ↓ HttpResponse → браузер
```

---

### Крок В1 — Створи папку для шаблонів

Django шукає шаблони в папці `<app>/templates/<app>/`.
Таке подвоєння (`hello_app/templates/hello_app/`) потрібно щоб уникнути
конфліктів назв між різними додатками.

Структура яку потрібно створити:

```
hello_app/
└── templates/
    └── hello_app/
        └── note_list.html    ← цей файл створимо нижче
```

**Команда для створення папок:**

```bash
# Windows PowerShell
mkdir hello_app\templates\hello_app
```
```bash
# Linux / Mac
mkdir -p hello_app/templates/hello_app
```
---

### Крок В2 — Створи шаблон note_list.html

Створи файл `hello_app/templates/hello_app/note_list.html`:
```text
note_list.html
```

```html
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Мої нотатки</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; }
        .note { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .date { color: #888; font-size: 0.85em; }
    </style>
</head>
<body>

    <h1>Нотатки</h1>

    {# if notes — перевіряємо чи є нотатки в списку #}
    {# 'notes' — це ім'я змінної яку передає view (context['notes']) #}
    {% if notes %}

        {# for note in notes — цикл по кожній нотатці зі списку #}
        {# Django рендерить цей блок для кожного об'єкта #}
        {% for note in notes %}
        <div class="note">
            <!-- {{ note.title }} — виводить значення поля title об'єкта note -->
            <h2>{{ note.title }}</h2>

            <!--
                {{ note.content }} — текст нотатки.
                Якщо content порожній — нічого не виведеться.
            -->
            {% if note.content %}
                <p>{{ note.content }}</p>
            {% endif %}

            <!--
                {{ note.created_at|date:"d.m.Y H:i" }}
                |date:"формат" — фільтр для форматування дати
            -->
            <p class="date">{{ note.created_at|date:"d.m.Y H:i" }}</p>
        </div>
        {% endfor %}

    {% else %}
        <!-- Показуємо якщо нотаток немає -->
        <p>Нотаток поки немає.
           <a href="/admin/hello_app/note/add/">Додати в адмін-панелі →</a>
        </p>
    {% endif %}

    <hr>
    <a href="/admin/">← Адмін-панель</a>

</body>
</html>
```

---

### Крок В3 — Додай view функцію у views.py

Відкрий `hello_app/views.py` і **додай** нову функцію (не замінюй існуючі):

```python
from django.http import HttpResponse
from django.shortcuts import render   # ← додай render до імпорту
from .models import Note              # ← імпортуємо модель


def index(request):
    """Головна сторінка."""
    return HttpResponse("Hello, Django!")


def about(request):
    """Сторінка 'Про нас'."""
    return HttpResponse("Це моя перша сторінка на Django!")

def note_list(request):
    """
    Сторінка зі списком нотаток.

    Що відбувається:
    1. Note.objects.all() — робить SELECT * FROM hello_app_note ORDER BY created_at DESC
       (порядок DESC заданий в class Meta: ordering = ['-created_at'])
    2. render() — бере шаблон, підставляє дані (context) і повертає HTML
    """

    # ORM запит: отримати всі нотатки з БД
    # Результат — QuerySet: лінивий список об'єктів Note
    notes = Note.objects.all()

    # context — словник даних які передаємо в шаблон
    # Ключ 'notes' → в шаблоні: {{ notes }}, {% for note in notes %}
    context = {
        'notes': notes,
    }

    # render(request, 'шлях/до/шаблону', context)
    # Django шукає шаблон в hello_app/templates/hello_app/note_list.html
    return render(request, 'hello_app/note_list.html', context)
```


---

### Крок В4 — Додай URL маршрут у hello_app/urls.py

Відкрий `hello_app/urls.py` і додай новий маршрут:

```python
from django.urls import path
from . import views

app_name = "hello_app"

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('notes/', views.note_list, name='note_list'),   # ← ДОДАЙ ЦЮ СТРОКУ
]
```
```python
    path('notes/', views.note_list, name='note_list'),
```


> `path('notes/', views.note_list)` — запит на `/notes/` → виклик `views.note_list`

---

### Крок В5 — Перевір у браузері

```bash
python manage.py runserver
```

| URL | Результат |
|-----|-----------|
| http://127.0.0.1:8000/notes/ | Список нотаток зі стилями |
| http://127.0.0.1:8000/admin/hello_app/note/add/ | Додати нотатку через адмін |

**Додай кілька нотаток через адмін → оновлюй `/notes/` — вони з'являться на сторінці.**

---

### Кінцева структура після всіх бонусів

```
simple_django_project/
├── db.sqlite3
├── manage.py
├── requirements.txt
├── hello_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── hello_app/
    ├── models.py          ← Note модель
    ├── views.py           ← index, about, note_list
    ├── urls.py            ← /, /about/, /notes/
    ├── admin.py           ← NoteAdmin
    ├── migrations/
    │   └── 0001_initial.py
    └── templates/
        └── hello_app/
            └── note_list.html
```

---

### Повний шлях запиту GET /notes/ крок за кроком

```
1. Браузер: GET http://127.0.0.1:8000/notes/

2. Django: читає ROOT_URLCONF = 'hello_project.urls'
           hello_project/urls.py → include('hello_app.urls')
           hello_app/urls.py → path('notes/', views.note_list)

3. views.note_list(request) викликається:
           Note.objects.all()
           → SQL: SELECT * FROM hello_app_note ORDER BY created_at DESC
           → повертає QuerySet [<Note: ...>, ...]

4. render(request, 'hello_app/note_list.html', {'notes': queryset})
           Django знаходить шаблон: hello_app/templates/hello_app/note_list.html
           Підставляє дані: {% for note in notes %} → HTML рядки

5. HttpResponse(HTML) → браузер рендерить сторінку
```

Це і є **MVT архітектура** Django:
- **M** (Model) — `Note` у `models.py` — зберігає дані
- **V** (View) — `note_list` у `views.py` — отримує дані, вирішує що показати
- **T** (Template) — `note_list.html` — рендерить HTML


---


## Бонус 3:  Django Debug Toolbar — Runtime Introspection для Django ORM

### Що таке Django Debug Toolbar

`django-debug-toolbar` — це middleware-based debugging system для Django,
який дозволяє бачити:

- SQL queries
- ORM performance
- timings
- middleware execution
- template rendering
- cache usage
- headers
- signals
- profiling information

Toolbar додається прямо у браузер як floating debug panel.

---

### Архітектурна ідея

Django Debug Toolbar — це:

```text
Runtime Introspection Layer
```

Тобто система яка:

- перехоплює request/response lifecycle
- слухає ORM queries
- вимірює performance
- показує внутрішній стан Django runtime

---

### Workflow

```text
Browser Request
    ↓
Django Middleware Stack
    ↓
DebugToolbarMiddleware
    ↓
Intercept:
    - SQL
    - Templates
    - Cache
    - Signals
    - Headers
    - Timings
    ↓
Browser Debug Panel
```

---

### Чому це дуже важливо

ORM в Django є "lazy".

Наприклад:

```python
posts = Post.objects.all()
```

SQL ще НЕ виконується.

Toolbar дозволяє побачити:

- коли SQL реально виконався
- скільки queries було
- які joins були
- де виникає N+1 problem

---

### ORM → SQL Visibility

Без toolbar:

```python
posts = Post.objects.all()
```

виглядає як "магія".

---

### З toolbar

Ти бачиш реальний SQL:

```sql
SELECT * FROM posts;
```

---

### N+1 Problem

Наприклад:

```python
for post in posts:
    print(post.author.name)
```

Toolbar покаже:

```text
101 queries executed
```

---

### Це означає

ORM робить:

```sql
SELECT * FROM author WHERE id=...
```

для кожного post окремо.

---

### Solution

```python
Post.objects.select_related("author")
```

---

### Це вже ORM optimization engineering

Toolbar фактично навчає:

- select_related()
- prefetch_related()
- annotate()
- lazy evaluation
- query planning

---

### Installation

#### 1. Install package

```bash
pip install django-debug-toolbar
```

---

#### 2. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    "debug_toolbar",
]
```

---

#### 3. Add middleware

```python
MIDDLEWARE = [
    ...
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]
```

---

#### Middleware Order Important

Toolbar middleware потрібно ставити:

- максимально рано
- але ПІСЛЯ middleware які змінюють response encoding

Наприклад:

```python
GZipMiddleware
↓
DebugToolbarMiddleware
```

---

#### 4. Add URLs

```python
from django.urls import include, path
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    ...
] + debug_toolbar_urls()
```

---

#### Toolbar Routes

By default:

```text
/__debug__/
```

---

#### 5. INTERNAL_IPS

Toolbar показується тільки для internal IP.

```python
INTERNAL_IPS = [
    "127.0.0.1",
]
```

---
### Що показує Toolbar

#### SQL Panel

Показує:

- всі SQL queries
- execution time
- duplicated queries
- stack traces

---

#### Templates Panel

Показує:

- які templates рендерились
- inheritance chain
- context variables

---

#### Cache Panel

Показує:

- cache hits
- cache misses

---

#### Headers Panel

Показує:

- request headers
- response headers

---

#### Signals Panel

Показує Django signals.

---

### Найважливіша панель

#### SQL Panel

Саме вона робить ORM "видимим".

---

#### Lazy QuerySets

```python
posts = Post.objects.all()
```

SQL ще не виконується.

---

### SQL trigger

SQL виконується тільки коли:

```python
list(posts)

for p in posts

posts[0]
```

---

### Toolbar допомагає зрозуміти

```text
Python code
↓
ORM
↓
REAL SQL
↓
Database Cost
```

---

---

### Повна конфігурація — фінальний стан файлів

#### Крок 1 — Встанови пакет

```bash
pip install django-debug-toolbar
```

#### Крок 2 — `hello_project/settings.py` — три зміни

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'hello_app',
    "debug_toolbar",       # ← 1. ДОДАЙ
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",  # ← 2. ДОДАЙ ПЕРШИМ
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

INTERNAL_IPS = [           # ← 3. ДОДАЙ НОВИЙ БЛОК (в кінці файлу)
    "127.0.0.1",
]
```

#### Крок 3 — `hello_project/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls  # ← ДОДАЙ ІМПОРТ

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hello_app.urls', namespace='hello_app')),
] + debug_toolbar_urls()  # ← ДОДАЙ В КІНЦІ
```

#### Крок 4 — Запусти сервер

```bash
python manage.py runserver
```

Відкрий `http://127.0.0.1:8000/notes/` — справа з'явиться чорна панель **DJDT**.

> **Важливо:** toolbar показується лише на сторінках з повним HTML
> (тег `<body>`). Маршрути `/` і `/about/` повертають `HttpResponse("текст")` без `<body>` —
> там toolbar НЕ з'явиться. Перевіряй на `/notes/`.

---

### Чеклист — чому toolbar не підключається

| # | Перевірка | Що перевірити |
|---|-----------|--------------|
| 1 | Пакет встановлений? | `pip show django-debug-toolbar` — має показати версію |
| 2 | `"debug_toolbar"` в `INSTALLED_APPS`? | settings.py |
| 3 | `DebugToolbarMiddleware` в `MIDDLEWARE`? | settings.py |
| 4 | `INTERNAL_IPS = ["127.0.0.1"]` є? | settings.py |
| 5 | `debug_toolbar_urls()` в urls.py? | hello_project/urls.py |
| 6 | Сторінка має `<body>` тег? | HttpResponse("текст") — не підходить, потрібен шаблон |
| 7 | `DEBUG = True`? | settings.py — toolbar показується лише в debug режимі |
| 8 | Windows: помилка MIME? | Додай в settings.py: `import mimetypes` + `mimetypes.add_type("application/javascript", ".js", True)` |

---

### Production Warning

Django Debug Toolbar — DEV TOOL.

НЕ використовувати в production.

---

### Для production використовують

- logging
- metrics
- tracing
- APM systems

Наприклад:

- Sentry
- Prometheus
- Grafana
- Jaeger

---

### django-silk

Альтернатива:

```text
django-silk
```

Більш profiling-oriented.

Показує:

- request history
- profiling
- timings
- SQL analysis

---

### Найважливіше

Toolbar вчить:

```text
ORM ≠ магія
```

а:

```text
Python
↓
ORM
↓
SQL
↓
Query Planner
↓
Database Cost
```

---