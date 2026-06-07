# CrispyNotes — Django Автентифікація та Безпека

> Цей туторіал проводить тебе через **повний стек безпеки Django-застосунку**:
> login/logout → password reset → захист об'єктів → групи для спільного доступу.
>
> Проєкт — **той самий менеджер нотаток** з попереднього уроку (crispy forms + SaaS Dashboard).
> У цьому уроці ми додаємо шари безпеки поверх готового застосунку.
> Ти побачиш як безпека "вплітається" в реальний код, а не існує окремо.

---

## Зміст

**Архітектурний фундамент** _(читати перед кодом)_
- [01 · AUTH BASICS — Автентифікація vs Авторизація](#01--auth-basics)
- [02 · SESSIONS — Як Django пам'ятає юзера](#02--sessions)
- [03 · PASSWORD SECURITY — Скидання і зміна пароля](#03--password-security)
- [04 · OBJECT-LEVEL PERMISSIONS — Захист від IDOR](#04--object-level-permissions)
- [05 · GROUP SHARING — Спільний доступ через Django Groups](#05--group-sharing)
- [06 · SECURITY SETTINGS — Що і навіщо](#06--security-settings)

**Покрокова реалізація**
1. [Крок 0 — Запуск проєкту](#крок-0--запуск)
2. [Крок 1 — Settings: auth + security](#крок-1--settings)
3. [Крок 2 — URLs: підключення вбудованих auth views](#крок-2--urls)
4. [Крок 3 — Login / Register templates](#крок-3--login--register)
5. [Крок 4 — Password Reset Flow (5 шаблонів)](#крок-4--password-reset)
6. [Крок 5 — Password Change](#крок-5--password-change)
7. [Крок 6 — Object-Level Permissions у views.py](#крок-6--object-level-permissions)
8. [Крок 7 — Models: Group FK](#крок-7--models-group-fk)
9. [Крок 8 — Selectors: Q-filter для групового доступу](#крок-8--selectors)
10. [Крок 9 — Services: Group CRUD](#крок-9--services)
11. [Крок 10 — Group Views + URLs](#крок-10--group-views)
12. [Крок 11 — Group Templates](#крок-11--group-templates)
13. [Структура файлів проєкту](#структура-файлів)

---

## 01 · AUTH BASICS

> **Головне питання:** Хто ти і що тобі можна?
>
> Ці два питання — основа будь-якої системи безпеки.
> Django відповідає на них через дві різні системи.

### Аналогія — паспорт і квиток на концерт

- **Паспорт** = **Аутентифікація (AuthN)**: "Хто ти?" — підтверджує особу.
  Охоронець перевіряє документ і переконується що він справжній.
- **Квиток** = **Авторизація (AuthZ)**: "Куди тобі можна?" — визначає права.
  Касир перевіряє квиток і вирішує де ти можеш сидіти (VIP чи партер).

У аеропорту: охорона перевіряє паспорт (AuthN), потім посадковий талон (AuthZ).
Паспорт без квитка — не пустять. Квиток без паспорта — теж.

### Таблиця: AuthN vs AuthZ

| | Аутентифікація (AuthN) | Авторизація (AuthZ) |
|--|------------------------|---------------------|
| **Питання** | Хто ти? | Що тобі можна? |
| **Відповідь** | Перевірка пароля | Перевірка прав |
| **Django інструмент** | `authenticate()`, `login()` | `@login_required`, `get_object_or_404` |
| **Де перевіряється** | `AuthenticationMiddleware` | У кожному view окремо |
| **Що якщо не пройшов** | Форма з помилкою | 302 Redirect або 404/403 |

### Компоненти Django Auth

```python
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# 1. Перевірити credentials (AuthN):
user = authenticate(request, username='alice', password='secret')
# → Django: шукає User з username='alice'
# → Перевіряє PBKDF2 хеш пароля в БД
# → Повертає User object якщо збігається, або None

# 2. Запустити сесію після успішного входу:
if user is not None:
    login(request, user)   # ← створює session_id у БД + cookie у браузері
    # Тепер request.user = alice у всіх наступних запитах

# 3. Завершити сесію:
logout(request)   # ← видаляє запис сесії з БД + примусово стирає cookie
```

### Middleware chain: хто встановлює `request.user`

```
Кожен запит проходить через ВЕСЬ ланцюг middleware:

1. SecurityMiddleware       — HTTPS редирект, HTTP заголовки безпеки
2. SessionMiddleware        — читає Cookie: sessionid=... → завантажує сесію з БД
3. CommonMiddleware         — trailing slash, Content-Type
4. CsrfViewMiddleware       — перевіряє csrfmiddlewaretoken у POST
5. AuthenticationMiddleware — читає session → встановлює request.user
   │                          Якщо session є → request.user = User(id=42)
   │                          Якщо немає    → request.user = AnonymousUser
6. MessageMiddleware        — Django messages flash framework
7. XFrameOptionsMiddleware  — X-Frame-Options: DENY заголовок
   │
   ▼
View функція (request.user вже встановлено!)
```

### `@login_required` — що робить і де живе

```python
# hello_app/views.py
from django.contrib.auth.decorators import login_required

@login_required   # ← декоратор, перевіряє request.user.is_authenticated
def note_list(request):
    # Якщо request.user = AnonymousUser:
    #   → redirect до LOGIN_URL (settings.py) + ?next=/notes/
    #   → 302 /accounts/login/?next=/notes/
    # Якщо request.user = User(id=42):
    #   → виконує view нормально
    notes = selectors.get_user_notes(request.user)
    return render(request, 'hello_app/note_list.html', {'notes': notes})
```

```python
# settings.py — куди перенаправляти незалогінених:
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/notes/'         # куди ПІСЛЯ успішного входу
LOGOUT_REDIRECT_URL = '/accounts/login/'  # куди ПІСЛЯ виходу
```

> **Важливо:** `@login_required` — це тільки AuthN ("ти залогінений?").
> Він НЕ перевіряє чи ця конкретна нотатка належить тобі.
> Для цього потрібен окремий AuthZ крок у view.

---

## 02 · SESSIONS

> **Проблема:** HTTP — протокол без стану (stateless). Кожен запит ніби "перший".
> Сервер не знає хто ти, якщо ти не надіслав докази.

### Аналогія — клубна карта в кафе

Уяви кафе де за кожну каву нараховують бали. Без картки — офіціант забуває тебе
після кожного відвідування. З карткою — бали накопичуються.

**Session cookie = клубна картка**: браузер зберігає і автоматично пред'являє при кожному запиті.

### Покроковий flow: Login → Cookie → Наступний запит

```
КРОК 1: Аліса натискає "Увійти"
─────────────────────────────────────────────────────────────────
Браузер:  POST /accounts/login/  {username: 'alice', password: 'secret'}
Django:   authenticate('alice', 'secret') → User(id=42) ✓
          login(request, user)
            → INSERT INTO django_session (session_key='xK9mPq', user_id=42, expire=...)
          Відповідь: 302 /notes/
          Header:    Set-Cookie: sessionid=xK9mPq; HttpOnly; SameSite=Lax; Path=/

КРОК 2: Браузер зберігає cookie. Аліса бачить /notes/
─────────────────────────────────────────────────────────────────
Браузер зберігає: sessionid=xK9mPq (у захищеному сховищі)

КРОК 3: Наступний запит Аліси (/notes/)
─────────────────────────────────────────────────────────────────
Браузер:  GET /notes/
Header:   Cookie: sessionid=xK9mPq   ← автоматично!
          Django SessionMiddleware:
            SELECT * FROM django_session WHERE session_key='xK9mPq'
            → user_id = 42
          Django AuthenticationMiddleware:
            SELECT * FROM auth_user WHERE id=42
            → request.user = User(id=42, username='alice')
View:     request.user.is_authenticated → True ✓
          notes = Note.objects.filter(user=request.user)

КРОК 4: Вихід (Logout)
─────────────────────────────────────────────────────────────────
Браузер:  POST /accounts/logout/  (з CSRF токеном)
Django:   logout(request)
            → DELETE FROM django_session WHERE session_key='xK9mPq'
          Відповідь: 302 /accounts/login/
          Header:    Set-Cookie: sessionid=; expires=Thu, 01 Jan 1970...
Браузер:  Видаляє cookie. request.user → AnonymousUser.
```

### Cookie налаштування в settings.py

```python
# settings.py:

SESSION_COOKIE_HTTPONLY = True
# ↑ JS не може прочитати sessionid через document.cookie
#   Захист від XSS-атак що намагаються вкрасти cookie

SESSION_COOKIE_SAMESITE = "Lax"
# ↑ "Lax": cookie надсилається тільки з того самого сайту
#   Захист від CSRF (evil.com не може надіслати запит з твоїм cookie)
#   "Strict" — строгіше, але може ламати OAuth flows
#   "None" — небезпечно без Secure прапора

CSRF_COOKIE_HTTPONLY = False
# ↑ False: JS може читати csrftoken (потрібно для fetch/axios запитів)
#   Якщо не використовуєш JS для форм → True для строгого захисту

# Production HTTPS (розкоментуй коли є SSL-сертифікат):
# SESSION_COOKIE_SECURE = True   # cookie тільки по HTTPS
# CSRF_COOKIE_SECURE = True
```

---

## 03 · PASSWORD SECURITY

> Django надає **повну систему управління паролями "з коробки"** через `django.contrib.auth`.
> Не треба писати жодного view для login, logout, password reset або change.

### Що `include('django.contrib.auth.urls')` підключає

```python
# hello_project/urls.py:
path("accounts/", include("django.contrib.auth.urls")),
```

Це автоматично реєструє такі URL:

| URL | View | Назва | Шаблон (треба створити) |
|-----|------|-------|------------------------|
| `/accounts/login/` | `LoginView` | `login` | `registration/login.html` |
| `/accounts/logout/` | `LogoutView` | `logout` | (редирект) |
| `/accounts/password_change/` | `PasswordChangeView` | `password_change` | `registration/password_change_form.html` |
| `/accounts/password_change/done/` | `PasswordChangeDoneView` | `password_change_done` | `registration/password_change_done.html` |
| `/accounts/password_reset/` | `PasswordResetView` | `password_reset` | `registration/password_reset_form.html` |
| `/accounts/password_reset/done/` | `PasswordResetDoneView` | `password_reset_done` | `registration/password_reset_done.html` |
| `/accounts/reset/<uidb64>/<token>/` | `PasswordResetConfirmView` | `password_reset_confirm` | `registration/password_reset_confirm.html` |
| `/accounts/reset/done/` | `PasswordResetCompleteView` | `password_reset_complete` | `registration/password_reset_complete.html` |

**Висновок:** 8 URL + 7 views = написати тільки шаблони!

### Password Reset Flow — 5 кроків

```
Крок 1: /accounts/password_reset/
─────────────────────────────────────────────────────────────────
Аліса забула пароль → вводить email у форму
→ password_reset_form.html

Крок 2: Django обробляє POST
─────────────────────────────────────────────────────────────────
Django шукає User з таким email
Генерує унікальний токен: sha1(user_pk + timestamp + SECRET_KEY)
Надсилає email з посиланням:
  /accounts/reset/<uidb64>/<token>/

[DEV: email → консоль (EMAIL_BACKEND = console)]
[PROD: email → SMTP сервер]

Крок 3: /accounts/password_reset/done/
─────────────────────────────────────────────────────────────────
Django показує: "Перевірте пошту"
→ password_reset_done.html

Крок 4: /accounts/reset/<uidb64>/<token>/
─────────────────────────────────────────────────────────────────
Аліса переходить за посиланням з email
Django: перевіряє токен (дійсний? 72 год, одноразовий?)
Якщо OK → форма для нового пароля
→ password_reset_confirm.html

Крок 5: Успіх → /accounts/reset/done/
─────────────────────────────────────────────────────────────────
Пароль збережено (хешований PBKDF2) → сесії скинуто
→ password_reset_complete.html
```

### Password Validators — Django захищає від слабких паролів

```python
# settings.py — 4 вбудовані валідатори:
AUTH_PASSWORD_VALIDATORS = [
    # Пароль схожий на username / email / ім'я?
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # Мінімум 8 символів (за замовчуванням):
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # Є у списку 20 000 найпоширеніших паролів? ("password", "123456"...)
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # Складається тільки з цифр?
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
```

---

## 04 · OBJECT-LEVEL PERMISSIONS

> **Найпоширеніша вразливість у вебзастосунках (OWASP A01):**
> Broken Access Control — юзер отримує доступ до чужих даних.

### Що таке IDOR (Insecure Direct Object Reference)

```
Аліса зареєстрована. Вона бачить URL своєї нотатки: /notes/42/edit/
Вона думає: "А що буде якщо змінити 42 на 43?"
Аліса переходить на: /notes/43/edit/
Якщо view не перевіряє власника → Аліса редагує нотатку БОБА!
```

Це атака **IDOR** — пряме звернення до об'єкта за ID без перевірки прав.

### Різниця між AuthN і AuthZ (на прикладі)

```python
# ПРОБЛЕМА: @login_required — тільки AuthN, не AuthZ!
@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk)   # ← IDOR вразливість!
    # Аліса залогінена → @login_required пропускає
    # Але note 43 належить Бобу → Аліса редагує чужі дані!

# РІШЕННЯ: додай user= до get_object_or_404
@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)   # ← AuthZ ✓
    # pk=43 + user=Alice → Django шукає Note WHERE pk=43 AND user_id=Alice.id
    # Такого запису немає (43 належить Бобу) → 404 для Аліси
```

**Золоте правило:**
```
@login_required        = "ти залогінений?"        (AuthN)
get_object_or_404(     = "цей об'єкт — твій?"     (AuthZ)
    Note, pk=pk,
    user=request.user
)
```

### Патерн для власних об'єктів

```python
# Застосовується до: note_edit, note_delete, note_detail,
# notebook_edit, notebook_delete, shopping_edit, shopping_delete, тощо

@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    #      ↑ Якщо note.user != request.user → 404 (не 403, щоб не розкривати факт існування)
    if request.method == 'POST':
        note.delete()
        messages.warning(request, 'Нотатку видалено.')
        return redirect('hello_app:note_list')
    return render(request, 'hello_app/note_confirm_delete.html', {'note': note})
```

### Патерн для спільних об'єктів (власник АБО член групи)

```python
# Для нотаток з групою — більш складна перевірка:
from django.core.exceptions import PermissionDenied
from django.db.models import Q

@login_required
def note_detail(request, pk):
    user_groups = request.user.groups.all()
    note = get_object_or_404(
        Note.objects.filter(
            Q(user=request.user) | Q(group__in=user_groups)
        ),
        pk=pk
    )
    # Аліса бачить нотатку якщо:
    #   note.user == Alice (особиста)
    #   АБО note.group in Alice.groups.all() (групова)
    return render(request, 'hello_app/note_detail.html', {'note': note})
```

### Таблиця захищених views у проєкті

| View | Захист | Як |
|------|--------|----|
| `note_list` | `@login_required` | Показує тільки свої + групові (selector) |
| `note_edit` | `@login_required` + owner check | `get_object_or_404(Note, pk=pk, user=request.user)` |
| `note_delete` | `@login_required` + owner check | Те саме |
| `group_detail` | `@login_required` + membership | `get_group_with_members(pk, request.user)` → None якщо не член |
| `group_delete` | `@login_required` + membership | `group.user_set.filter(pk=request.user.pk).exists()` |

---

## 05 · GROUP SHARING

> **Ідея:** Аліса хоче ділитись нотатками з родиною.
> Вона створює групу "Сімя" і додає туди Боба.
> Нотатки позначені цією групою бачать обидва.

### Django вбудована модель Group

Django вже має готову модель `Group` у `django.contrib.auth`:

```python
from django.contrib.auth.models import Group

# Кожна Group має:
#   id       — PK
#   name     — назва ('Сімя', 'Команда', 'Клас')
#   users    — M2N зв'язок з User (через django_auth_user_groups)
#   permissions — M2N зв'язок з Permission (для role-based access — НЕ наш випадок)

# У нашому проєкті ми використовуємо Group для ШЕРИНГУ ДАНИХ,
# а не для Django Permission System.
```

### ER-Діаграма: User, Group, Note

```
┌─────────────┐        ┌──────────────────┐        ┌─────────────┐
│    User     │        │auth_user_groups  │        │    Group    │
│─────────────│        │──────────────────│        │─────────────│
│ id (PK)     │◄──────►│ user_id (FK)     │◄──────►│ id (PK)     │
│ username    │  M:N   │ group_id (FK)    │  M:N   │ name        │
│ password    │        └──────────────────┘        └──────┬──────┘
│ email       │                                           │
└──────┬──────┘                                           │ 1:N
       │ 1:N                                              │
       ▼                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                             Note                                 │
│─────────────────────────────────────────────────────────────────│
│ id (PK)                                                         │
│ title                                                           │
│ content                                                         │
│ user_id  (FK → User, CASCADE)    ← обов'язковий, власник        │
│ group_id (FK → Group, SET_NULL)  ← необов'язковий, шерінг       │
└─────────────────────────────────────────────────────────────────┘

Якщо group_id = NULL  → особиста нотатка (тільки user_id бачить)
Якщо group_id = 5     → групова нотатка (всі члени групи 5 бачать)
```

### Q-filter: "мої або групові"

```python
# selectors.py — хитрий запит:
from django.db.models import Q

def get_user_notes(user, *, archived=False, ...):
    user_groups = user.groups.all()   # всі групи Аліси
    qs = Note.objects.filter(
        Q(user=user) |               # власні нотатки АБО
        Q(group__in=user_groups),    # нотатки груп де Аліса є членом
        is_archived=archived,
    ).select_related('notebook', 'group').prefetch_related('tags')
    return qs.order_by('-is_pinned', '-priority', '-updated_at')
```

```
Аліса є в групах: [Сімя(id=1), Робота(id=3)]

SQL (спрощено):
  SELECT * FROM note
  WHERE (user_id = 42)                          -- особисті Аліси
     OR (group_id IN (1, 3))                    -- нотатки її груп
  AND is_archived = FALSE
  ORDER BY is_pinned DESC, priority DESC, updated_at DESC
```

### Порівняння підходів до шерингу

| | M2M `shared_with` (попередній урок) | Group FK (цей урок) |
|--|-------------------------------------|---------------------|
| **Де** | `TodoList.shared_with = ManyToManyField(User)` | `Note.group = ForeignKey(Group)` |
| **Кому шерити** | Конкретним юзерам (список осіб) | Всім членам групи |
| **Управління** | Через `/todo/<pk>/share/` | Через `/groups/<pk>/` |
| **Коли підходить** | "Поділитись з Бобом і Карою" | "Поділитись з усією родиною" |
| **Видалення** | ManyToMany join видаляється | `SET_NULL` → нотатка стає особистою |

---

## 06 · SECURITY SETTINGS

> Django має безліч security налаштувань. Більшість з них "вимкнені" за замовчуванням
> щоб не ламати localhost розробку. У production їх треба увімкнути.

### Таблиця: кожна настройка і що захищає

| Настройка | Значення | Від чого захищає |
|-----------|----------|-----------------|
| `SESSION_COOKIE_HTTPONLY = True` | JS не читає cookie | XSS-атаки на session hijacking |
| `SESSION_COOKIE_SAMESITE = "Lax"` | Cookie тільки з того ж сайту | CSRF через крос-сайтові форми |
| `CSRF_COOKIE_HTTPONLY = False` | JS читає csrftoken | (False = для fetch/axios) |
| `X_FRAME_OPTIONS = "DENY"` | Заборона `<iframe>` | Clickjacking атаки |
| `SECURE_CONTENT_TYPE_NOSNIFF = True` | Не "вгадувати" MIME | XSS через підроблені файли |
| `DEBUG = False` | Ховає stack traces | Витік SECRET_KEY та коду |
| `ALLOWED_HOSTS = ['mysite.com']` | Тільки цей домен | HTTP Host header attacks |

### Що витікає при `DEBUG = True` в production

```
Помилка сервера при DEBUG=True показує:
  ✗ Повний stack trace (шляхи до файлів, назви функцій)
  ✗ Значення ВСІХ локальних змінних у момент помилки
  ✗ SECRET_KEY (витік = будь-хто може підробити session cookies!)
  ✗ Всі SQL-запити зберігаються в пам'яті → memory leak
  ✗ INSTALLED_APPS, DATABASES, MIDDLEWARE — вся конфіга видима

Правило: DEBUG = False ЗАВЖДИ в production.
```

### Production HTTPS (розкоментувати на сервері)

```python
# settings.py — закоментовано у dev, увімкни у production:

# SESSION_COOKIE_SECURE = True
# ↑ Cookie надсилається ТІЛЬКИ по HTTPS (не по HTTP)
# Без цього атакер "в середині" може перехопити sessionid

# CSRF_COOKIE_SECURE = True
# ↑ Те саме для CSRF cookie

# SECURE_SSL_REDIRECT = True
# ↑ Будь-який HTTP запит → 301 Moved Permanently → HTTPS

# SECURE_HSTS_SECONDS = 31536000  # 1 рік
# ↑ Браузер запам'ятовує: цей сайт ТІЛЬКИ HTTPS, ніколи HTTP
# (Strict-Transport-Security заголовок)
```

---

## Крок 0 — Запуск

```bash
# 1. Перейти до папки проєкту
cd module_5/lesson_Django_authentication_and_security/crispy_notes_project

# 2. Встановити залежності
pip install -r requirements.txt
# Django>=5.2, django-crispy-forms>=2.3, crispy-bootstrap5, django-debug-toolbar

# 3. Застосувати міграції (включаючи 0003 — Group FK)
python manage.py migrate

# 4. Створити суперюзера для /admin/
python manage.py createsuperuser

# 5. Запустити сервер
python manage.py runserver
```

### Що дивитись у браузері

| URL | Що показує |
|-----|-----------|
| `http://127.0.0.1:8000/accounts/login/` | Login форма з "Забули пароль?" |
| `http://127.0.0.1:8000/register/` | Реєстрація нового акаунту |
| `http://127.0.0.1:8000/accounts/password_reset/` | Форма відновлення пароля |
| `http://127.0.0.1:8000/accounts/password_change/` | Зміна пароля (після входу) |
| `http://127.0.0.1:8000/notes/` | Список нотаток (тільки залогінені) |
| `http://127.0.0.1:8000/groups/` | Мої групи |
| `http://127.0.0.1:8000/groups/new/` | Створити групу |
| `http://127.0.0.1:8000/admin/` | Django Admin |

---

## Крок 1 — Settings

**Місце:** `hello_project/settings.py`

```python
# ── Auth redirects ─────────────────────────────────────────────────────────────
LOGIN_URL = '/accounts/login/'           # куди перенаправляти @login_required
LOGIN_REDIRECT_URL = '/notes/'           # куди ПІСЛЯ успішного входу
LOGOUT_REDIRECT_URL = '/accounts/login/' # куди ПІСЛЯ виходу

# ── Password Validators ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Email (password reset) ─────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# ↑ DEV: email виводиться в термінал (runserver), не надсилається реально
# PROD: замінити на:
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
# EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']

# ── Web Security ──────────────────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True     # JS не читає sessionid (XSS захист)
CSRF_COOKIE_HTTPONLY = False       # JS читає csrftoken (для fetch/axios)
SESSION_COOKIE_SAMESITE = "Lax"   # CSRF захист для cookies
X_FRAME_OPTIONS = "DENY"          # Clickjacking захист
SECURE_CONTENT_TYPE_NOSNIFF = True # MIME sniffing захист

# Production HTTPS (розкоментуй на сервері):
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
# SECURE_HSTS_SECONDS = 31536000

# ── Messages → Bootstrap alert variants ────────────────────────────────────────
from django.contrib.messages import constants as messages_constants
MESSAGE_TAGS = {
    messages_constants.DEBUG:   'secondary',
    messages_constants.INFO:    'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR:   'danger',
}
```

---

## Крок 2 — URLs

**Місце:** `hello_project/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path("admin/", admin.site.urls),

    # Django built-in auth: login, logout, password change, password reset
    # Реєструє 8 URL одним рядком!
    path("accounts/", include("django.contrib.auth.urls")),

    # Наш застосунок: нотатки, групи, реєстрація
    path("", include("hello_app.urls", namespace="hello_app")),
] + debug_toolbar_urls()
```

`hello_app/urls.py` — кастомні URL (реєстрація і групи):

```python
urlpatterns = [
    # ... notes, notebooks, todo, shopping ...

    # Реєстрація (Django не надає — пишемо самі)
    path('register/', views.register, name='register'),

    # Groups — 4 URL для CRUD груп
    path('groups/',                  views.group_list,    name='group_list'),
    path('groups/new/',              views.group_create,  name='group_create'),
    path('groups/<int:pk>/',         views.group_detail,  name='group_detail'),
    path('groups/<int:pk>/delete/',  views.group_delete,  name='group_delete'),
]
```

---

## Крок 3 — Login / Register

**Місце:** `templates/registration/login.html`

Django шукає шаблон `registration/login.html` автоматично для `LoginView`.

```html
{% extends 'base.html' %}

{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
  <div class="card shadow-sm" style="width: 380px;">
    <div class="card-body p-4">

      <!-- Бренд -->
      <div class="text-center mb-4">
        <i class="bi bi-journal-text display-4 text-primary"></i>
        <h5 class="fw-bold mt-2 mb-0">CrispyNotes</h5>
        <p class="text-muted small">Увійди до свого акаунту</p>
      </div>

      <!-- Помилка входу -->
      {% if form.errors %}
      <div class="alert alert-danger py-2 small">
        Невірний логін або пароль.
      </div>
      {% endif %}

      <!-- Форма входу (CSRF токен обов'язковий!) -->
      <form method="post">
        {% csrf_token %}   {# ← ОБОВ'ЯЗКОВО! без нього Django відхилить POST #}
        <div class="mb-3">
          <label class="form-label fw-semibold">Логін</label>
          <input type="text" name="{{ form.username.html_name }}"
                 class="form-control" autofocus>
        </div>
        <div class="mb-4">
          <label class="form-label fw-semibold">Пароль</label>
          <input type="password" name="{{ form.password.html_name }}"
                 class="form-control">
        </div>
        <input type="hidden" name="next" value="{{ next }}">
        {# ↑ next: куди повернутись після входу (наприклад /notes/42/) #}
        <button type="submit" class="btn btn-primary w-100">Увійти</button>
      </form>

      <hr class="my-3">
      <p class="text-center text-muted small mb-1">
        Немає акаунту? <a href="{% url 'hello_app:register' %}">Зареєструватись</a>
      </p>
      <p class="text-center text-muted small mb-0">
        <a href="{% url 'password_reset' %}">Забули пароль?</a>
        {# ↑ 'password_reset' — вбудована URL з django.contrib.auth.urls #}
      </p>
    </div>
  </div>
</div>
{% endblock %}
```

---

## Крок 4 — Password Reset

Django надає 4 views для password reset. Треба написати тільки шаблони.

### password_reset_form.html — форма email

```html
{% extends 'base.html' %}

{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
  <div class="card shadow-sm" style="width: 420px;">
    <div class="card-body p-4">
      <h5 class="fw-bold mb-1">Відновлення паролю</h5>
      <p class="text-muted small mb-3">
        Введіть ваш email — надішлемо посилання для скидання пароля.
      </p>
      <form method="post">
        {% csrf_token %}
        <div class="mb-3">
          <label class="form-label fw-semibold">Email</label>
          <input type="email" name="email" class="form-control" autofocus>
        </div>
        <button type="submit" class="btn btn-primary w-100">
          Надіслати посилання
        </button>
      </form>
      <div class="text-center mt-3">
        <a href="{% url 'login' %}" class="text-muted small">← Назад до входу</a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### password_reset_done.html — "перевір пошту"

```html
{% extends 'base.html' %}
{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
  <div class="card shadow-sm" style="width: 420px;">
    <div class="card-body p-4 text-center">
      <i class="bi bi-envelope-check display-4 text-success mb-3"></i>
      <h5 class="fw-bold">Посилання надіслано!</h5>
      <p class="text-muted">Перевірте вашу пошту і перейдіть за посиланням.</p>
      <div class="alert alert-info text-start small mt-3">
        <strong>DEV режим:</strong> Лист не надсилається на пошту.
        Відкрийте термінал з <code>runserver</code> — там буде текст листа.
        Скопіюйте <code>/accounts/reset/...</code> URL і відкрийте у браузері.
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### password_reset_confirm.html — нова форма пароля

```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
  <div class="card shadow-sm" style="width: 420px;">
    <div class="card-body p-4">

      {% if validlink %}
        <h5 class="fw-bold mb-3">Новий пароль</h5>
        <form method="post">
          {% csrf_token %}
          {{ form|crispy }}
          <button type="submit" class="btn btn-primary w-100 mt-2">
            Зберегти пароль
          </button>
        </form>
      {% else %}
        {# Токен недійсний (прострочений або вже використаний) #}
        <div class="text-center py-3">
          <i class="bi bi-exclamation-triangle display-4 text-danger mb-3"></i>
          <h5>Посилання недійсне</h5>
          <p class="text-muted small">Термін дії посилання вийшов або воно вже використано.</p>
          <a href="{% url 'password_reset' %}" class="btn btn-outline-primary">
            Запросити нове посилання
          </a>
        </div>
      {% endif %}

    </div>
  </div>
</div>
{% endblock %}
```

### password_reset_complete.html

```html
{% extends 'base.html' %}
{% block body %}
<div class="min-vh-100 d-flex align-items-center justify-content-center">
  <div class="card shadow-sm" style="width: 380px;">
    <div class="card-body p-4 text-center">
      <i class="bi bi-check-circle display-4 text-success mb-3"></i>
      <h5 class="fw-bold">Пароль змінено!</h5>
      <p class="text-muted">Тепер ви можете увійти з новим паролем.</p>
      <a href="{% url 'login' %}" class="btn btn-primary mt-2">Увійти</a>
    </div>
  </div>
</div>
{% endblock %}
```

### password_reset_email.html — текст листа

```html
{# Це текстовий email — без HTML тегів! #}
Привіт!

Ви запросили скидання пароля для акаунту на CrispyNotes.
Перейдіть за посиланням щоб встановити новий пароль:

{{ protocol }}://{{ domain }}{% url 'password_reset_confirm' uidb64=uid token=token %}

Посилання дійсне 72 години.

Якщо ви не запитували скидання пароля — просто проігноруйте цей лист.

— CrispyNotes
```

### Як знайти посилання в консолі (dev)

```bash
# Після надсилання форми password_reset — дивись в термінал:

Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: ...
...

Привіт!

Ви запросили скидання пароля...
http://127.0.0.1:8000/accounts/reset/Mg/abc123token456/   ← скопіюй цей URL!
```

---

## Крок 5 — Password Change

Password change вимагає що юзер **вже залогінений** (на відміну від password reset).

### password_change_form.html

```html
{% extends 'layouts/dashboard.html' %}
{% load crispy_forms_tags %}

{% block topbar_title %}Зміна пароля{% endblock %}

{% block content %}
<div class="row">
  <div class="col-md-6">
    <div class="card shadow-sm">
      <div class="card-header py-3">
        <h6 class="mb-0 fw-semibold">
          <i class="bi bi-key me-2"></i>Зміна пароля
        </h6>
      </div>
      <div class="card-body">
        <form method="post">
          {% csrf_token %}
          {{ form|crispy }}
          {# Форма автоматично містить: old_password, new_password1, new_password2 #}
          <hr>
          <button type="submit" class="btn btn-primary">Змінити пароль</button>
          <a href="{% url 'hello_app:note_list' %}" class="btn btn-outline-secondary ms-2">
            Скасувати
          </a>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Посилання у dropdown (dashboard.html)

```html
{# templates/layouts/dashboard.html — dropdown юзера: #}
<ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end shadow">
  <li><a class="dropdown-item" href="{% url 'hello_app:group_list' %}">
    <i class="bi bi-people me-2"></i>Мої групи
  </a></li>
  <li><a class="dropdown-item" href="{% url 'password_change' %}">
    <i class="bi bi-key me-2"></i>Змінити пароль
  </a></li>
  <li><hr class="dropdown-divider"></li>
  <li>
    <form method="post" action="{% url 'logout' %}">
      {% csrf_token %}
      <button type="submit" class="dropdown-item text-danger">Вийти</button>
    </form>
  </li>
</ul>
```

---

## Крок 6 — Object-Level Permissions

Патерн застосовується **у кожному view** що приймає `pk` параметр.

```python
# hello_app/views.py — загальний патерн для ВЛАСНИХ об'єктів:

@login_required
def note_edit(request, pk):
    # get_object_or_404 з user=request.user:
    #   1. Шукає Note WHERE pk=<pk> AND user_id=<request.user.id>
    #   2. Якщо не знайдено → 404 (не 403! — не розкриваємо що об'єкт існує)
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            services.update_note(note, **form.cleaned_data_for_service())
            messages.success(request, 'Нотатку оновлено.')
            return redirect('hello_app:note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note, user=request.user)

    return render(request, 'hello_app/note_form.html', {
        'form': form, 'title': 'Редагування нотатки',
    })
```

```python
# До (вразливо до IDOR):
note = get_object_or_404(Note, pk=pk)   # ← будь-який pk!

# Після (захищено):
note = get_object_or_404(Note, pk=pk, user=request.user)  # ← тільки свій pk!
```

---

## Крок 7 — Models: Group FK

**Місце:** `hello_app/models.py`

```python
from django.contrib.auth.models import User, Group

class Note(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notes'
    )
    # ── Group FK (новий у цьому уроці) ─────────────────────────────────────
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,  # ← якщо групу видалено → нотатка стає особистою
        null=True,                   # ← NULL = особиста нотатка (за замовчуванням)
        blank=True,                  # ← у формі поле необов'язкове
        related_name='notes',
    )
    # ── решта полів ─────────────────────────────────────────────────────────
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(default=1)
    # ...
```

### Чому `SET_NULL`, а не `CASCADE`?

```
CASCADE: видалення групи → видаляються ВСІ нотатки групи
         → Аліса видаляє групу → Боб втрачає всі спільні нотатки!

SET_NULL: видалення групи → нотатки залишаються, але стають особистими (group=NULL)
          → Аліса видаляє групу → нотатки переходять до особистого простору власника
          → Боб бачить що спільних нотаток більше немає, але оригінальні власники зберегли свої
```

### Міграція 0003

```python
# hello_app/migrations/0003_note_group_shoppinglist_group.py

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),  # ← Group з auth
        ('hello_app', '0002_shoppinglist_shared_with_todolist_shared_with'),
    ]
    operations = [
        migrations.AddField(
            model_name='note',
            name='group',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='notes',
                to='auth.group',
            ),
        ),
        migrations.AddField(
            model_name='shoppinglist',
            name='group',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='shopping_lists',
                to='auth.group',
            ),
        ),
    ]
```

---

## Крок 8 — Selectors

**Місце:** `hello_app/selectors.py`

```python
from django.db.models import Q, Count
from django.contrib.auth.models import Group


def get_user_notes(user, *, archived=False, notebook=None, tag=None, search=None):
    """Повертає нотатки юзера + нотатки груп де він є членом."""
    user_groups = user.groups.all()
    qs = Note.objects.filter(
        Q(user=user) | Q(group__in=user_groups),   # ← ключовий Q-фільтр
        is_archived=archived,
    ).select_related('notebook', 'group').prefetch_related('tags')

    if notebook is not None:
        qs = qs.filter(notebook=notebook)
    if tag is not None:
        qs = qs.filter(tags=tag)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

    return qs.order_by('-is_pinned', '-priority', '-updated_at')


def get_user_groups(user):
    """Групи юзера з кількістю учасників (для відображення на group_list)."""
    return user.groups.annotate(
        member_count=Count('user')   # ← annotate = додаємо поле member_count до queryset
    ).order_by('name')


def get_group_with_members(group_id, user):
    """Повертає групу з учасниками ТІЛЬКИ якщо юзер є її членом."""
    try:
        group = Group.objects.prefetch_related('user_set').get(pk=group_id)
        # Перевірка membership — якщо юзер не в групі → повертаємо None
        if not group.user_set.filter(pk=user.pk).exists():
            return None
        return group
    except Group.DoesNotExist:
        return None
```

---

## Крок 9 — Services

**Місце:** `hello_app/services.py`

```python
from django.contrib.auth.models import Group, User


def create_group(*, name, creator):
    """Створює групу і автоматично додає creator як першого учасника."""
    group = Group.objects.create(name=name)
    group.user_set.add(creator)   # ← creator стає першим членом
    return group


def add_user_to_group(group, username):
    """Додає юзера до групи за username. Повертає (True, '') або (False, 'повідомлення')."""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return False, f'Користувача «{username}» не знайдено.'

    if group.user_set.filter(pk=user.pk).exists():
        return False, f'«{username}» вже є членом цієї групи.'

    group.user_set.add(user)
    return True, ''


def remove_user_from_group(group, user):
    """Видаляє юзера з групи."""
    group.user_set.remove(user)


def delete_group(group):
    """Видаляє групу. Нотатки групи стають особистими (group=NULL через SET_NULL)."""
    group.delete()
    # Django автоматично виконує SET_NULL для Note.group і ShoppingList.group
```

---

## Крок 10 — Group Views

**Місце:** `hello_app/views.py`

```python
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from . import selectors, services
from .forms import GroupCreateForm, GroupAddMemberForm


@login_required
def group_list(request):
    """Список груп до яких належить поточний юзер."""
    groups = selectors.get_user_groups(request.user)
    return render(request, 'hello_app/group_list.html', {'groups': groups})


@login_required
def group_create(request):
    """Створення нової групи. Creator автоматично стає першим учасником."""
    if request.method == 'POST':
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group = services.create_group(
                name=form.cleaned_data['name'],
                creator=request.user,       # ← request.user = перший учасник
            )
            messages.success(request, f'Групу «{group.name}» створено!')
            return redirect('hello_app:group_detail', pk=group.pk)
    else:
        form = GroupCreateForm()
    return render(request, 'hello_app/group_form.html', {
        'form': form, 'title': 'Нова група',
    })


@login_required
def group_detail(request, pk):
    """Перегляд групи: учасники, додати/видалити, покинути."""
    group = selectors.get_group_with_members(pk, request.user)
    if group is None:
        raise Http404('Групу не знайдено або у вас немає доступу.')
    # ↑ Якщо юзер не є членом → Http404 (не 403, щоб не розкривати існування групи)

    add_form = GroupAddMemberForm()
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')   # 'add' / 'remove' / 'leave'

        if action == 'add':
            add_form = GroupAddMemberForm(request.POST)
            if add_form.is_valid():
                ok, msg = services.add_user_to_group(
                    group, add_form.cleaned_data['username']
                )
                if ok:
                    messages.success(request, 'Користувача додано до групи.')
                    return redirect('hello_app:group_detail', pk=pk)
                else:
                    error = msg   # ← "Не знайдено" або "вже є членом"

        elif action == 'remove':
            remove_pk = request.POST.get('user_pk')
            try:
                target = User.objects.get(pk=remove_pk)
                services.remove_user_from_group(group, target)
                messages.success(request, f'«{target.username}» видалено.')
            except User.DoesNotExist:
                pass
            return redirect('hello_app:group_detail', pk=pk)

        elif action == 'leave':
            services.remove_user_from_group(group, request.user)
            messages.info(request, f'Ви покинули групу «{group.name}».')
            return redirect('hello_app:group_list')

    return render(request, 'hello_app/group_detail.html', {
        'group': group,
        'members': group.user_set.all(),
        'add_form': add_form,
        'error': error,
    })


@login_required
def group_delete(request, pk):
    """Видалення групи (тільки якщо юзер є членом)."""
    group = get_object_or_404(Group, pk=pk)
    if not group.user_set.filter(pk=request.user.pk).exists():
        raise PermissionDenied   # ← 403 (знаємо що група існує, але юзер не член)
    if request.method == 'POST':
        name = group.name
        services.delete_group(group)
        messages.warning(request, f'Групу «{name}» видалено. Спільні нотатки стали особистими.')
        return redirect('hello_app:group_list')
    return render(request, 'hello_app/group_confirm_delete.html', {'group': group})
```

**Ключовий патерн у `group_detail`:**

```
Один view — три дії через один POST:

action = request.POST.get('action')

'add'    → додати учасника за username
'remove' → видалити конкретного учасника (по user_pk)
'leave'  → поточний юзер покидає групу

Навіщо один view? Вся логіка групи в одному місці — легше читати і підтримувати.
```

---

## Крок 11 — Group Templates

**Місце:** `hello_app/templates/hello_app/`

### group_list.html — картки груп

```html
{% extends 'layouts/dashboard.html' %}
{% block topbar_title %}Мої групи{% endblock %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-4">
  <h5 class="fw-semibold mb-0">Мої групи</h5>
  <a href="{% url 'hello_app:group_create' %}" class="btn btn-primary btn-sm">
    <i class="bi bi-person-plus me-1"></i>Нова група
  </a>
</div>

{% if groups %}
<div class="row row-cols-1 row-cols-md-3 g-3">
  {% for group in groups %}
  <div class="col">
    <div class="card h-100 shadow-sm">
      <div class="card-body">
        <h6 class="fw-semibold">{{ group.name }}</h6>
        <p class="text-muted small">{{ group.member_count }} учасників</p>
        {# member_count — annotate з get_user_groups selector #}
      </div>
      <div class="card-footer">
        <a href="{% url 'hello_app:group_detail' group.pk %}"
           class="btn btn-outline-primary btn-sm">Відкрити</a>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
{% else %}
  {# Немає груп — empty state #}
  {% include 'components/empty_state.html' with icon="bi-people" message="Груп ще немає" %}
{% endif %}

{% endblock %}
```

### group_detail.html — учасники і дії

```html
{% extends 'layouts/dashboard.html' %}
{% load crispy_forms_tags %}
{% block topbar_title %}Група: {{ group.name }}{% endblock %}
{% block content %}

<div class="row g-4">
  <!-- Список учасників -->
  <div class="col-md-6">
    <div class="card shadow-sm">
      <div class="card-header">
        <h6 class="mb-0">Учасники ({{ members.count }})</h6>
      </div>
      <ul class="list-group list-group-flush">
        {% for member in members %}
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <span>
            {{ member.username }}
            {% if member == request.user %}
              <span class="badge bg-success ms-1">Ти</span>
            {% endif %}
          </span>
          {% if member != request.user %}
          <!-- Видалити учасника (action=remove) -->
          <form method="post">
            {% csrf_token %}
            <input type="hidden" name="action" value="remove">
            <input type="hidden" name="user_pk" value="{{ member.pk }}">
            <button type="submit" class="btn btn-outline-danger btn-sm">
              <i class="bi bi-x"></i>
            </button>
          </form>
          {% endif %}
        </li>
        {% endfor %}
      </ul>
    </div>
  </div>

  <!-- Дії: додати учасника, покинути, видалити -->
  <div class="col-md-6">
    <!-- Додати учасника (action=add) -->
    <div class="card shadow-sm mb-3">
      <div class="card-header"><h6 class="mb-0">Додати учасника</h6></div>
      <div class="card-body">
        {% if error %}<div class="alert alert-danger small">{{ error }}</div>{% endif %}
        <form method="post">
          {% csrf_token %}
          <input type="hidden" name="action" value="add">
          {% crispy add_form %}
        </form>
      </div>
    </div>

    <!-- Небезпечна зона: покинути або видалити -->
    <div class="card border-danger shadow-sm">
      <div class="card-body">
        <h6 class="text-danger mb-3">Небезпечна зона</h6>
        <!-- Покинути групу (action=leave) -->
        <form method="post" class="d-inline">
          {% csrf_token %}
          <input type="hidden" name="action" value="leave">
          <button type="submit" class="btn btn-outline-danger btn-sm me-2"
                  onclick="return confirm('Покинути групу?')">
            Покинути групу
          </button>
        </form>
        <!-- Видалити групу (окремий URL) -->
        <a href="{% url 'hello_app:group_delete' group.pk %}"
           class="btn btn-danger btn-sm">
          Видалити групу
        </a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### group_confirm_delete.html

```html
{% extends 'layouts/dashboard.html' %}
{% block content %}
<div class="card border-danger shadow-sm" style="max-width: 480px;">
  <div class="card-header bg-danger text-white">
    <h6 class="mb-0">Видалення групи «{{ group.name }}»</h6>
  </div>
  <div class="card-body">
    <div class="alert alert-warning">
      <strong>Увага!</strong> Після видалення:
      <ul class="mb-0 mt-2">
        <li>Група та список учасників видаляться назавжди.</li>
        <li>Нотатки і списки покупок <strong>НЕ видаляються</strong> —
            вони стають особистими (group = NULL через <code>SET_NULL</code>).</li>
      </ul>
    </div>
    <form method="post">
      {% csrf_token %}
      <button type="submit" class="btn btn-danger me-2">Так, видалити</button>
      <a href="{% url 'hello_app:group_detail' group.pk %}"
         class="btn btn-outline-secondary">Скасувати</a>
    </form>
  </div>
</div>
{% endblock %}
```

---

## Структура файлів

```
crispy_notes_project/
│
├── requirements.txt               ← Django>=5.2, crispy-forms, crispy-bootstrap5
│
├── hello_project/
│   ├── settings.py                ← ★ LOGIN_URL, EMAIL_BACKEND, security block
│   └── urls.py                    ← include('django.contrib.auth.urls') + hello_app
│
├── hello_app/
│   ├── models.py                  ← Note.group FK, ShoppingList.group FK  ★ НОВЕ
│   ├── forms.py                   ← GroupCreateForm, GroupAddMemberForm    ★ НОВЕ
│   ├── services.py                ← create_group, add_user_to_group,       ★ НОВЕ
│   │                                 remove_user_from_group, delete_group
│   ├── selectors.py               ← get_user_notes (Q filter), get_user_groups ★ НОВЕ
│   ├── views.py                   ← group_list, group_create,              ★ НОВЕ
│   │                                 group_detail, group_delete
│   ├── urls.py                    ← /groups/ URL patterns                  ★ НОВЕ
│   ├── context_processors.py      ← sidebar_context (без змін)
│   ├── admin.py                   ← реєстрація всіх моделей
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   ├── 0002_shoppinglist_shared_with_todolist_shared_with.py  ← M2M
│   │   └── 0003_note_group_shoppinglist_group.py                  ★ НОВЕ
│   └── templates/hello_app/
│       ├── note_list.html         ← без змін
│       ├── note_form.html         ← + group поле у формі   ★ НОВЕ
│       ├── group_list.html        ←                         ★ НОВЕ
│       ├── group_form.html        ← {% crispy form %}        ★ НОВЕ
│       ├── group_detail.html      ← учасники, action=add/remove/leave ★ НОВЕ
│       └── group_confirm_delete.html ← SET_NULL пояснення   ★ НОВЕ
│
└── templates/                     ← глобальні шаблони
    ├── base.html                      ← Bootstrap CDN (без змін)
    ├── layouts/
    │   └── dashboard.html             ← + "Групи" у sidebar, "Змінити пароль" dropdown ★
    ├── registration/
    │   ├── login.html                 ← + "Забули пароль?" посилання  ★ ОНОВЛЕНО
    │   ├── register.html              ← реєстрація (без змін)
    │   ├── password_reset_form.html   ← email форма             ★ НОВЕ
    │   ├── password_reset_done.html   ← "перевір пошту"         ★ НОВЕ
    │   ├── password_reset_confirm.html← нова форма пароля       ★ НОВЕ
    │   ├── password_reset_complete.html← успіх                  ★ НОВЕ
    │   ├── password_reset_email.html  ← текст листа             ★ НОВЕ
    │   ├── password_change_form.html  ← зміна пароля            ★ НОВЕ
    │   └── password_change_done.html  ← успіх                   ★ НОВЕ
    └── components/
        ├── empty_state.html       ← без змін
        ├── pagination.html        ← без змін
        └── confirm_modal.html     ← без змін
```

---

## Підсумок: що і де вчити

| Концепція | Де дивитись у коді |
|-----------|-------------------|
| **AuthN vs AuthZ** | `views.py` — `@login_required` + `get_object_or_404(Note, pk=pk, user=request.user)` |
| **Session flow** | `settings.py` — `SESSION_COOKIE_*` + `django.contrib.sessions` |
| **Login/Logout** | `templates/registration/login.html` + `urls.py` auth.urls include |
| **Password Reset** | `templates/registration/password_reset_*.html` (5 файлів) |
| **Password Change** | `templates/registration/password_change_*.html` + `dashboard.html` dropdown |
| **IDOR захист** | `views.py` — всі `get_object_or_404` з `user=request.user` |
| **Group model** | `models.py` — `Note.group FK(Group, SET_NULL)` |
| **Q-filter** | `selectors.py` — `get_user_notes` + `Q(user=user) | Q(group__in=user_groups)` |
| **Group CRUD** | `services.py` — `create_group`, `add_user_to_group`, `delete_group` |
| **Group views** | `views.py` — `group_list`, `group_create`, `group_detail`, `group_delete` |
| **3-action POST** | `views.py group_detail` — один view обробляє 'add'/'remove'/'leave' |
| **SET_NULL pattern** | `models.py` + `group_confirm_delete.html` — пояснення behavior |
| **Security settings** | `settings.py` — блок Web Security (HTTPONLY, SAMESITE, X_FRAME_OPTIONS) |
| **EMAIL_BACKEND** | `settings.py` — `console.EmailBackend` для dev |

---

## Документація уроку

| Файл | Тема |
|------|------|
| [`../AUTH_BASICS.md`](../AUTH_BASICS.md) | authenticate(), @login_required, middleware — детально |
| [`../SESSIONS_FLOW.md`](../SESSIONS_FLOW.md) | cookies, sessions, login/logout, password reset |
| [`../PERMISSIONS.md`](../PERMISSIONS.md) | IDOR, object-level permissions, Q-filter для груп |
| [`../SECURITY_FOUNDATIONS.md`](../SECURITY_FOUNDATIONS.md) | CIA Triad, Trust Boundary, хешування паролів, CSRF |
| [`../SECURITY_MISCONCEPTIONS.md`](../SECURITY_MISCONCEPTIONS.md) | 6 типових помилок безпеки |
| [`../DJANGO_ADMIN.md`](../DJANGO_ADMIN.md) | is_staff, is_superuser, ModelAdmin |
| [`../DJANGO_SECURITY_ARCHITECTURE.md`](../DJANGO_SECURITY_ARCHITECTURE.md) | middleware pipeline, ORM, CSRF/XSS |
| [`../OWASP_TOP_10.md`](../OWASP_TOP_10.md) | 10 вразливостей та Django захист |
| [`../ZERO_TRUST.md`](../ZERO_TRUST.md) | Zero Trust архітектура з Django кодом |
| [`../SIEM.md`](../SIEM.md) | логування, rsyslog, ELK Stack |
| [`../INDEX.md`](../INDEX.md) | навігація по всіх файлах |
