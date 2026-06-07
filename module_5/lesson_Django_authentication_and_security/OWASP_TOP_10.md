# OWASP Top 10 — 10 Найнебезпечніших Вразливостей

> **OWASP** (Open Web Application Security Project) — некомерційна організація, що щороку публікує список
> 10 найпоширеніших вразливостей у вебзастосунках. Це "чорний список" атак, які ти **зобов'язаний** знати.
>
> **Аналогія:** OWASP Top 10 — це як ТОП-10 способів пограбування банку. Охоронці банку зобов'язані знати
> всі ці способи щоб їх запобігти.

---

## A01 — Broken Access Control (Порушений Контроль Доступу)

**Найпоширеніша вразливість** у 2021-2023 рр.

**Що це:** Юзер може виконати дії або отримати дані, до яких не повинен мати доступу.

**Приклади:**
- Аліса змінює URL `/notes/42/edit/` на `/notes/43/edit/` і редагує нотатку Боба
- URL `/admin/` доступний без перевірки `is_staff`
- API повертає список всіх юзерів замість тільки свого профілю

**Django захист:**
```python
# ПОГАНО:
note = get_object_or_404(Note, pk=pk)  # будь-хто може отримати будь-яку нотатку

# ДОБРЕ:
note = get_object_or_404(Note, pk=pk, user=request.user)  # тільки свої
```

**У нашому проєкті:**
- `@login_required` на всіх views
- `get_object_or_404(..., user=request.user)` у note_edit, note_delete тощо
- Групи: `Q(user=user) | Q(group__in=user_groups)` — видно тільки своє і групове

---

## A02 — Cryptographic Failures (Криптографічні Помилки)

**Що це:** Збереження або передача чутливих даних без належного шифрування.

**Приклади:**
- Пароль зберігається у відкритому вигляді: `password = "secret123"` у БД
- HTTP замість HTTPS → паролі передаються відкритим текстом
- Слабкий алгоритм хешування (MD5, SHA-1) для паролів

**Django захист:**
```python
# Django автоматично хешує паролі через PBKDF2:
user.set_password("new_password")
# → pbkdf2_sha256$720000$salt$hash  (зберігається у БД)

# Ніколи не зберігай:
user.raw_password = "secret"    # НІКОЛИ!
Note.objects.create(content=request.POST['secret'])  # без шифрування — погано
```

**Production налаштування:**
```python
# settings.py (розкоментуй у production):
SESSION_COOKIE_SECURE = True   # cookie тільки по HTTPS
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True     # HTTP → автоматичний редирект на HTTPS
```

---

## A03 — Injection (Ін'єкція)

**Що це:** Атакер вставляє шкідливий код у запит, який виконується на сервері.

**Типи:**
- **SQL Injection** — шкідливий SQL у запиті
- **XSS** — шкідливий JavaScript у HTML
- **Command Injection** — виконання системних команд

### SQL Injection

```python
# НЕБЕЗПЕЧНО — конкатенація рядків:
user_input = "'; DROP TABLE notes; --"
query = f"SELECT * FROM notes WHERE title = '{user_input}'"
# ↑ Цей код ВИДАЛЯЄ всю таблицю notes!

# БЕЗПЕЧНО — Django ORM параметризує запити автоматично:
notes = Note.objects.filter(title=user_input)
# → SQL: SELECT * FROM notes WHERE title = %s  (з escaped параметром)
```

### XSS (Cross-Site Scripting)

```html
<!-- НЕБЕЗПЕЧНО — без екранування: -->
<div>{{ note.content|safe }}</div>
<!-- Якщо content = "<script>document.cookie</script>" → виконається у браузері -->

<!-- БЕЗПЕЧНО — Django екранує HTML автоматично: -->
<div>{{ note.content }}</div>
<!-- Виведе: &lt;script&gt;document.cookie&lt;/script&gt; (безпечно) -->
```

**Django захист від XSS:**
- Шаблонний рушій `{{ variable }}` екранує все автоматично
- Використовуй `|safe` **тільки** якщо ВПЕВНЕНИЙ що контент безпечний (не user input!)

---

## A04 — Insecure Design (Небезпечне Проєктування)

**Що це:** Архітектурні рішення з вбудованими вразливостями.

**Приклади:**
- Форма реєстрації не має захисту від bot-реєстрацій (потрібна CAPTCHA або rate limiting)
- Password reset надсилає пароль відкритим текстом у листі (замість токена)
- Немає обмеження на кількість спроб входу (можливий brute-force)

**Django рішення:**
```python
# Rate limiting (обмеження кількості запитів):
# pip install django-axes

# settings.py:
INSTALLED_APPS += ['axes']
AXES_FAILURE_LIMIT = 5    # 5 невдалих спроб → блокування
AXES_COOLOFF_TIME = 1     # блокування на 1 годину

# Або: django-ratelimit
from ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    ...
```

---

## A05 — Security Misconfiguration (Неправильна Конфігурація Безпеки)

**Що це:** Небезпечні налаштування залишені за замовчуванням або встановлені помилково.

**Приклади:**
- `DEBUG = True` в production → витік SECRET_KEY, стектрейсів, SQL-запитів
- Адмін-панель `/admin/` за стандартним URL (легко знайти)
- Стандартні паролі БД (admin/admin)

**Django налаштування:**
```python
# settings.py — обов'язково в production:
DEBUG = False                          # ← НІКОЛИ True в production!
SECRET_KEY = os.environ['SECRET_KEY']  # ← зберігай у .env, не в коді!
ALLOWED_HOSTS = ['mysite.com']         # ← конкретні домени, не '*'

X_FRAME_OPTIONS = "DENY"              # захист від clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True    # браузер не "вгадує" тип файлу
SESSION_COOKIE_HTTPONLY = True        # JS не читає sessionid
```

---

## A06 — Vulnerable and Outdated Components (Застарілі Компоненти)

**Що це:** Використання бібліотек з відомими вразливостями.

**Перевірка Django:**
```bash
# Перевірити вразливості у залежностях:
pip install pip-audit
pip-audit

# Або через safety:
pip install safety
safety check

# Результат:
# Found vulnerability in Django 3.2.0: CVE-2021-XXXXX
# Upgrade to: Django 3.2.14
```

**Правило:**
> Регулярно оновлюй Django та всі бібліотеки. Слідкуй за security releases на djangoproject.com.

---

## A07 — Identification and Authentication Failures

**Що це:** Слабка аутентифікація — легкі паролі, відсутність MFA, незахищений password reset.

**Приклади:**
- Дозволений пароль "123456" або "password"
- Відсутнє обмеження спроб входу → brute-force атака
- Password reset токен дійсний безстроково

**Django захист:**
```python
# settings.py — валідатори паролів:
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
# ↑ Django вже має всі ці валідатори, просто не видаляй їх!
```

**Password Reset токен у Django:**
- Токен одноразовий (після першого використання інвалідується)
- Діє 72 години за замовчуванням (`PASSWORD_RESET_TIMEOUT = 259200`)

---

## A08 — Software and Data Integrity Failures

**Що це:** Довіра до даних або коду без перевірки їх цілісності.

**Приклади:**
- Завантаження JavaScript бібліотек без перевірки хешу (CDN підміна)
- Django `pickle` серіалізація у сесіях (вразлива до RCE)

**Django захист:**
```html
<!-- SRI (Subresource Integrity) — перевірка хешу при завантаженні з CDN: -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>
```

---

## A09 — Security Logging and Monitoring Failures

**Що це:** Відсутність логів або моніторингу безпекових подій.

**Що треба логувати:**
- Невдалі спроби входу (brute-force детекція)
- Спроби доступу до чужих об'єктів (IDOR спроби)
- Зміна прав доступу (хто і кому призначив права)
- Видалення даних (хто видалив)

**Django логування:**
```python
# settings.py:
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}

# views.py — логування підозрілих дій:
import logging
logger = logging.getLogger('django.security')

def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    logger.warning(f"User {request.user.pk} deleted note {pk}")
    note.delete()
```

---

## A10 — Server-Side Request Forgery (SSRF)

**Що це:** Атакер змушує сервер робити запити до внутрішніх ресурсів.

**Приклад:**
```python
# Небезпечна функція "завантажити аватар з URL":
def upload_avatar(request):
    url = request.POST.get('avatar_url')
    response = requests.get(url)      # SSRF!
    # Атакер надсилає: url = "http://169.254.169.254/latest/meta-data/"
    # → сервер робить запит до AWS metadata API → витік AWS credentials!
```

**Захист:**
```python
from urllib.parse import urlparse

ALLOWED_HOSTS_FOR_FETCH = ['i.imgur.com', 'avatars.githubusercontent.com']

def is_safe_url(url):
    parsed = urlparse(url)
    return parsed.hostname in ALLOWED_HOSTS_FOR_FETCH

def upload_avatar(request):
    url = request.POST.get('avatar_url')
    if not is_safe_url(url):
        raise PermissionDenied
    response = requests.get(url)
```

---

## Підсумок: Django vs OWASP Top 10

| # | Вразливість | Django захист |
|---|-------------|---------------|
| A01 | Broken Access Control | `@login_required` + `get_object_or_404(..., user=request.user)` |
| A02 | Cryptographic Failures | `set_password()` (PBKDF2), HTTPS settings |
| A03 | Injection | ORM (SQL), `{{ var }}` автоекранування (XSS) |
| A04 | Insecure Design | `django-axes` (rate limiting), правильна архітектура |
| A05 | Security Misconfiguration | `DEBUG=False`, security settings у settings.py |
| A06 | Vulnerable Components | `pip-audit`, регулярні оновлення |
| A07 | Auth Failures | `AUTH_PASSWORD_VALIDATORS`, `@login_required`, MFA |
| A08 | Integrity Failures | SRI для CDN ресурсів |
| A09 | Logging Failures | `django.security` logger, структуровані логи |
| A10 | SSRF | Whitelist дозволених URL для зовнішніх запитів |
